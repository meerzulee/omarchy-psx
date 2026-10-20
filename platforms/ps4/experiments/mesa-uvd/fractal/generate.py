#!/usr/bin/env python3
"""Render a deterministic native-Mac fractal clip into a fresh private directory."""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import check


def encoder_options(variant="720p30"):
    spec = check.VARIANTS[variant]
    level = spec["level"]
    return [
        "-an", "-vf", f"scale={spec['width']}:{spec['height']}:flags=lanczos:in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=field_mode=prog:range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
        "-c:v", "libx264", "-preset", "medium", "-profile:v", "baseline", "-level:v", f"{level // 10}.{level % 10}",
        "-crf", "18", "-maxrate", spec["maxrate"], "-bufsize", spec["bufsize"], "-bf", "0", "-refs", "1",
        "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-coder:v", "cavlc",
        "-x264-params", "bframes=0:cabac=0:weightp=0:ref=1:keyint=60:min-keyint=60:scenecut=0:threads=1:lookahead-threads=1:force-cfr=1",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        "-video_track_timescale", "15360", "-movflags", "+faststart", "-map_metadata", "-1"]


def write_json(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New private output directory; must not exist")
    parser.add_argument("--variant", choices=check.VARIANTS, default="720p30")
    parser.add_argument("--render-threads", default=min(8, max(1, (os.cpu_count() or 2) - 2)), type=int)
    parser.add_argument("--preview", action="store_true", help="Only six full-resolution samples and a contact sheet")
    args = parser.parse_args()
    check.require(platform.system() == "Darwin", "This recipe requires native macOS")
    check.require(1 <= args.render_threads <= 32, "Render threads outside 1..32")
    spec = check.VARIANTS[args.variant]
    tools = {name: shutil.which(name) for name in ("clang", "ffmpeg", "ffprobe")}
    check.require(all(tools.values()), "clang, ffmpeg and ffprobe are required")
    output = args.output.absolute()
    output.mkdir(mode=0o700, parents=False)
    source = Path(__file__).resolve().parent
    (output / "source").mkdir()
    for name in ("render.c", "generate.py", "check.py", "README.md"):
        shutil.copyfile(source / name, output / "source" / name)
    started = time.monotonic()
    commands = []
    plan = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "host": {"system": platform.platform(), "machine": platform.machine(), "python": sys.version},
            "preview": args.preview, "variant": args.variant,
            "width": spec["width"], "height": spec["height"], "encoder_policy": spec,
            "fps": check.FPS, "frames": check.FRAMES, "duration_seconds": 30,
            "render_threads": args.render_threads,
            "render_size": [spec["width"], spec["height"]] if args.preview else [spec["render_width"], spec["render_height"]],
            "source_sha256": {p.name: check.sha256(p) for p in sorted((output / "source").iterdir())},
            "tool_versions": {}, "hardware_acceptance": False}
    for name, path in tools.items():
        argv = [path, "--version" if name == "clang" else "-version"]
        plan["tool_versions"][name] = {"path": path, "sha256": check.sha256(path), "argv": argv,
            "output": subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT)}
    write_json(output / "PLAN.json", plan)

    def run(argv, label):
        commands.append({"argv": argv, "stdout": label + ".stdout", "stderr": label + ".stderr"})
        with (output / (label + ".stdout")).open("xb") as stdout, (output / (label + ".stderr")).open("xb") as stderr:
            completed = subprocess.run(argv, stdout=stdout, stderr=stderr)
        commands[-1]["returncode"] = completed.returncode
        completed.check_returncode()

    try:
        renderer = output / "fractal-render"
        compile_argv = [tools["clang"], "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fno-fast-math", "-ffp-contract=off", "-pthread", str(output / "source" / "render.c"),
                        "-lm", "-o", str(renderer)]
        run(compile_argv, "compile")
        count, step = (6, 179) if args.preview else (900, 1)
        render_width, render_height = plan["render_size"]
        render_argv = [str(renderer), str(render_width), str(render_height), "0", str(count), str(step), "900", str(args.render_threads)]
        contact = output / "contact-sheet.png"
        video = output / f"seahorse-flight-{args.variant}-baseline.mp4"
        input_argv = [tools["ffmpeg"], "-nostdin", "-hide_banner", "-v", "info", "-n", "-filter_threads", "1", "-f", "rawvideo",
                      "-pixel_format", "rgb24", "-video_size", f"{render_width}x{render_height}", "-framerate", "30", "-i", "pipe:0"]
        if args.preview:
            encode_argv = input_argv + ["-vf", "scale=640:360:flags=lanczos,tile=3x2:padding=10:margin=10:color=0x080e22",
                                       "-frames:v", "1", str(contact)]
        else:
            encode_argv = input_argv + encoder_options(args.variant) + [str(video)]
        commands.append({"renderer_argv": render_argv, "encoder_argv": encode_argv,
                         "renderer_stderr": "render.stderr", "encoder_stdout": "encode.stdout", "encoder_stderr": "encode.stderr"})
        with (output / "render.stderr").open("xb") as render_log, (output / "encode.stdout").open("xb") as encode_out, (output / "encode.stderr").open("xb") as encode_log:
            renderer_process = subprocess.Popen(render_argv, stdout=subprocess.PIPE, stderr=render_log)
            try:
                encoder_process = subprocess.Popen(encode_argv, stdin=renderer_process.stdout, stdout=encode_out, stderr=encode_log)
                renderer_process.stdout.close()
                encoder_rc = encoder_process.wait()
                renderer_rc = renderer_process.wait()
            finally:
                if renderer_process.poll() is None:
                    renderer_process.terminate()
                    renderer_process.wait()
        commands[-1].update(renderer_returncode=renderer_rc, encoder_returncode=encoder_rc)
        check.require(renderer_rc == encoder_rc == 0, "Render or encoding failed; logs preserved")
        result = {"status": "PASS_PREVIEW" if args.preview else "PASS_FRACTAL_FIXTURE",
                  "wall_seconds": time.monotonic() - started,
                  "hardware_acceptance": False, "preview": args.preview, "variant": args.variant}
        if not args.preview:
            decoded = output / "reference-nv12.framemd5"
            decoded_hash = output / "reference-nv12.sha256"
            decode_argv = [tools["ffmpeg"], "-nostdin", "-hide_banner", "-v", "info", "-n", "-hwaccel", "none", "-c:v", "h264", "-i", str(video)]
            mapping = ["-map", "0:v:0", "-an", "-sn", "-dn", "-pix_fmt", "nv12", "-c:v", "rawvideo"]
            run(decode_argv + mapping + ["-f", "framemd5", str(decoded)] + mapping + ["-f", "hash", "-hash", "sha256", str(decoded_hash)], "software-reference")
            rows = check.frame_md5(decoded.read_text(), args.variant)
            probes = check.probe(video, tools["ffprobe"], tools["ffmpeg"])
            for label, data in probes.items():
                write_json(output / ("ffprobe-" + label + ".json"), data)
            result["media"] = check.validate_probe(probes, video, args.variant)
            result["software_reference"] = {"pixel_format": "nv12", "frame_bytes": check.frame_bytes(args.variant),
                "total_bytes": check.frame_bytes(args.variant) * len(rows), "unique_frames": len({row[5] for row in rows}),
                "total_sha256": decoded_hash.read_text().strip().removeprefix("SHA256=")}
            selection = "+".join(f"eq(n\\,{i})" for i in (0, 180, 360, 540, 720, 899))
            run([tools["ffmpeg"], "-nostdin", "-hide_banner", "-v", "error", "-n", "-hwaccel", "none", "-c:v", "h264", "-i", str(video),
                 "-vf", f"select={selection},scale=640:360:flags=lanczos,tile=3x2:padding=10:margin=10:color=0x080e22", "-frames:v", "1", str(contact)], "contact-sheet")
            result["contact_sheet_frames"] = [0, 180, 360, 540, 720, 899]
            run([tools["ffmpeg"], "-nostdin", "-hide_banner", "-v", "error", "-n", "-hwaccel", "none", "-c:v", "h264", "-i", str(video),
                 "-vf", "select=eq(n\\,0)+eq(n\\,450)+eq(n\\,899)", "-fps_mode", "passthrough",
                 str(output / "representative-%02d.png")], "representative-frames")
            result["representative_png_frames"] = [0, 450, 899]
        else:
            result["contact_sheet_frames"] = [0, 179, 358, 537, 716, 895]
        write_json(output / "COMMANDS.json", commands)
        result["wall_seconds"] = time.monotonic() - started
        result["files"] = {str(p.relative_to(output)): {"bytes": p.stat().st_size, "sha256": check.sha256(p)}
                           for p in sorted(output.rglob("*")) if p.is_file()}
        write_json(output / "RESULT.json", result)
        print(json.dumps({"status": result["status"], "output": str(output), "wall_seconds": result["wall_seconds"]}))
    except BaseException as error:
        if not (output / "COMMANDS.json").exists():
            write_json(output / "COMMANDS.json", commands)
        write_json(output / "FAILED.json", {"error_type": type(error).__name__, "error": str(error),
                   "outputs_preserved": True, "hardware_acceptance": False})
        raise


if __name__ == "__main__":
    main()
