#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One pinned VAAPI decode into bounded per-frame MD5 and whole-NV12 SHA256 receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True

LOG_LIMIT = 2 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def pin(path, expected):
    require(re.fullmatch(r"[0-9a-f]{64}", expected), "Invalid SHA256 pin")
    require(stat.S_ISREG(path.stat().st_mode), f"Not a regular input: {path}")
    actual = sha(path)
    require(actual == expected, f"SHA256 mismatch: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def write_json(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def md5_rows(path, count, frame_bytes):
    require(0 < path.stat().st_size <= 65536 + count * 256, "Missing/oversized framemd5")
    rows = []
    for line in path.read_text(encoding="ascii").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = [v.strip() for v in line.split(",")]
        require(len(fields) == 6 and all(re.fullmatch(r"-?[0-9]+", v) for v in fields[:5]),
                "Malformed framemd5 row")
        require(int(fields[0]) == 0 and int(fields[4]) == frame_bytes and
                re.fullmatch(r"[0-9a-f]{32}", fields[5]), "Wrong stream/size/hash in framemd5")
        rows.append({"index": len(rows), "bytes": int(fields[4]), "md5": fields[5]})
        require(len(rows) <= count, "Extra decoded frame")
    require(len(rows) == count, f"Expected {count} complete frames, got {len(rows)}")
    return rows


def environment(driver):
    suffix = "_drv_video.so"
    require(driver.name.endswith(suffix), "Expected *_drv_video.so")
    return {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
            "LIBVA_DRIVER_NAME": driver.name[:-len(suffix)],
            "LIBVA_DRIVERS_PATH": str(driver.parent), "LIBVA_MESSAGING_LEVEL": "2"}


def command(ffmpeg, node, clip, hash_fd):
    # One rawvideo encoder feeds two checksum muxers after the same hwdownload.
    tee = f"[f=framemd5:hash=md5]pipe:1|[f=hash:hash=SHA256]pipe:{hash_fd}"
    return [str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "verbose", "-nostats",
            "-xerror", "-noauto_conversion_filters", "-err_detect", "explode",
            "-filter_threads", "1", "-hwaccel", "vaapi", "-hwaccel_device", str(node),
            "-hwaccel_output_format", "vaapi", "-c:v", "h264", "-threads", "1",
            "-i", str(clip), "-map", "0:v:0", "-an", "-sn", "-dn",
            "-vf", "hwdownload,format=nv12", "-fps_mode", "passthrough",
            "-c:v", "rawvideo", "-threads:v", "1", "-pix_fmt", "nv12", "-f", "tee", tee]


def query(ffmpeg, option, env):
    p = subprocess.Popen([str(ffmpeg), option], env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    data = bytearray()
    try:
        with selectors.DefaultSelector() as sel:
            sel.register(p.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 10
            while sel.get_map():
                require(time.monotonic() < deadline, "FFmpeg identity timeout")
                for key, _ in sel.select(0.1):
                    block = os.read(key.fd, 65536)
                    if not block:
                        sel.unregister(key.fileobj)
                    else:
                        require(len(data) + len(block) <= LOG_LIMIT, "FFmpeg identity log overflow")
                        data.extend(block)
            require(p.wait(timeout=max(0.1, deadline - time.monotonic())) == 0,
                    "FFmpeg identity query failed")
    finally:
        if p.poll() is None:
            p.kill()
            p.wait(timeout=5)
        p.stdout.close()
    return data.decode("utf-8", errors="replace")


def preflight(args):
    require(platform.system() == "Linux", "Runtime preflight requires Linux")
    require(platform.release() == args.release, "Kernel release mismatch")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    require(boot == str(uuid.UUID(args.boot_id)), "Boot ID mismatch")
    require(args.width == 1920 and args.height == 1080 and args.frames == 900,
            "This tool is fixed to1920x1080,900 frames")
    require(1 <= args.timeout <= 180, "Timeout must be1..180 seconds")
    require(re.fullmatch(r"[0-9a-f]{64}", args.total_nv12_sha256), "Invalid total NV12 SHA256")
    args.clip = args.clip.resolve(strict=True)
    args.framemd5 = args.framemd5.resolve(strict=True)
    args.ffmpeg = args.ffmpeg.resolve(strict=True)
    selected_driver = args.driver.absolute()
    driver = selected_driver.resolve(strict=True)
    args.render_node = args.render_node.resolve(strict=True)
    require(re.fullmatch(r"/dev/dri/renderD[0-9]+", str(args.render_node)) and
            stat.S_ISCHR(args.render_node.stat().st_mode) and
            os.access(args.render_node, os.R_OK | os.W_OK), "Inaccessible DRM render node")
    inputs = {"clip": pin(args.clip, args.clip_sha256),
              "framemd5": pin(args.framemd5, args.framemd5_sha256),
              "ffmpeg": pin(args.ffmpeg, args.ffmpeg_sha256),
              "driver": pin(driver, args.driver_sha256)}
    inputs["driver"]["selected_path"] = str(selected_driver)
    rows = md5_rows(args.framemd5, args.frames, args.width * args.height * 3 // 2)
    require(len({r["md5"] for r in rows}) > 1, "Expected moving fractal reference")
    env = environment(selected_driver)
    version = query(args.ffmpeg, "-version", env)
    hwaccels = query(args.ffmpeg, "-hwaccels", env)
    require("vaapi" in hwaccels.splitlines(), "FFmpeg lacks VAAPI")
    return rows, {"inputs": inputs, "kernel_release": platform.release(), "boot_id": boot,
                  "render_node": str(args.render_node), "environment": env,
                  "ffmpeg_version": version, "ffmpeg_hwaccels": hwaccels,
                  "command_template": command(args.ffmpeg, args.render_node, args.clip, "HASH_FD"),
                  "width": args.width, "height": args.height, "frames": args.frames,
                  "frame_bytes": args.width * args.height * 3 // 2,
                  "total_nv12_sha256": args.total_nv12_sha256}


def execute(args, identity, output):
    started = time.monotonic()
    read_fd, write_fd = os.pipe()
    cmd = command(args.ffmpeg, args.render_node, args.clip, write_fd)
    limits = {"frames.framemd5": 65536 + args.frames * 256,
              "total.sha256": 1024, "ffmpeg.stderr.txt": LOG_LIMIT}
    sizes = {k: 0 for k in limits}
    execution = {"command": cmd, "environment": identity["environment"], "limits": limits,
                 "timeout_seconds": args.timeout, "failure": None, "returncode": None}
    write_json(output / "COMMAND.json", execution)
    p = None
    try:
        p = subprocess.Popen(cmd, env=identity["environment"], stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(write_fd,))
        os.close(write_fd)
        write_fd = None
        with selectors.DefaultSelector() as sel:
            streams = [(p.stdout, "frames.framemd5"), (p.stderr, "ffmpeg.stderr.txt"), (read_fd, "total.sha256")]
            handles = {}
            try:
                for stream, name in streams:
                    handles[name] = (output / name).open("xb")
                    sel.register(stream, selectors.EVENT_READ, name)
                while sel.get_map():
                    require(time.monotonic() - started < args.timeout, "FFmpeg timeout")
                    for key, _ in sel.select(0.1):
                        block = os.read(key.fd, 65536)
                        if not block:
                            sel.unregister(key.fileobj)
                            continue
                        name = key.data
                        left = limits[name] - sizes[name]
                        handles[name].write(block[:left])
                        sizes[name] += min(left, len(block))
                        require(len(block) <= left, f"Output byte limit: {name}")
                execution["returncode"] = p.wait(timeout=max(0.1, args.timeout - (time.monotonic() - started)))
            finally:
                for f in handles.values():
                    f.close()
    except (Exception, KeyboardInterrupt) as exc:
        execution["failure"] = str(exc) or type(exc).__name__
    finally:
        if write_fd is not None:
            os.close(write_fd)
        os.close(read_fd)
        if p is not None:
            if p.poll() is None:
                p.kill()
            execution["returncode"] = p.wait(timeout=5)
            p.stdout.close()
            p.stderr.close()
        execution.update(elapsed_seconds=round(time.monotonic() - started, 6), retained_bytes=sizes)
    return execution


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("clip", "framemd5", "driver", "ffmpeg"):
        p.add_argument("--" + name, type=Path, required=True)
        p.add_argument("--" + name + "-sha256", required=True)
    p.add_argument("--total-nv12-sha256", required=True)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--frames", type=int, default=900)
    p.add_argument("--release", required=True)
    p.add_argument("--boot-id", required=True)
    p.add_argument("--render-node", type=Path, default=Path("/dev/dri/renderD128"))
    p.add_argument("--output", type=Path, required=True, help="New private result directory")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--run", action="store_true", help="Execute exactly one hardware decode")
    args = p.parse_args(argv)
    output = None
    created_output = False
    result = {"status": "FAIL_PREFLIGHT", "hardware_acceptance": False,
              "hardware_decode_invoked": False, "runner_sha256": sha(Path(__file__).resolve()),
              "argv": sys.argv if argv is None else argv}
    try:
        output = args.output.absolute()
        require(output.parent.is_dir() and output.parent.resolve() == output.parent,
                "Output requires an existing canonical parent")
        output.mkdir(mode=0o700)
        created_output = True
        expected, identity = preflight(args)
        result.update(status="PASS_PREFLIGHT", preflight=identity)
        write_json(output / "PREFLIGHT.json", result)
        if args.run:
            result.update(status="FAIL_DECODE", hardware_decode_invoked=True)
            execution = execute(args, identity, output)
            result["execution"] = execution
            write_json(output / "EXECUTION.json", execution)
            require(execution["returncode"] == 0 and execution["failure"] is None,
                    "FFmpeg decode failed; inspect execution/log")
            actual = md5_rows(output / "frames.framemd5", args.frames, identity["frame_bytes"])
            total = (output / "total.sha256").read_text(encoding="ascii").strip()
            require(re.fullmatch(r"SHA256=[0-9a-f]{64}", total), "Malformed total SHA256 output")
            mismatches = [i for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
            comparison = {"frames": args.frames, "frame_bytes": identity["frame_bytes"],
                          "total_bytes": args.frames * identity["frame_bytes"],
                          "frame_rows": actual, "mismatched_frames": mismatches,
                          "total_nv12_sha256": total.split("=", 1)[1],
                          "expected_total_nv12_sha256": args.total_nv12_sha256}
            write_json(output / "COMPARISON.json", comparison)
            require(not mismatches and comparison["total_nv12_sha256"] == args.total_nv12_sha256,
                    "Decoded NV12 differs from pinned oracle")
            _, after = preflight(args)
            require(after == identity, "Input/runtime identity changed during decode")
            result.update(status="PASS_EXACT_NV12_HASHES", inputs_unchanged=True,
                          comparison={k: v for k, v in comparison.items() if k != "frame_rows"})
        result["artifacts"] = {f.name: {"bytes": f.stat().st_size, "sha256": sha(f)}
                               for f in output.iterdir() if f.is_file()}
    except (Exception, KeyboardInterrupt) as exc:
        result["error"] = str(exc) or type(exc).__name__
    if created_output and not (output / "RESULT.json").exists():
        result["artifacts"] = {f.name: {"bytes": f.stat().st_size, "sha256": sha(f)}
                               for f in output.iterdir() if f.is_file()}
        write_json(output / "RESULT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in ("PASS_PREFLIGHT", "PASS_EXACT_NV12_HASHES") else 1


if __name__ == "__main__":
    sys.exit(main())
