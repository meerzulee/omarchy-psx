#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile and exercise the actual patched Mesa caps source with a DRM query stub."""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import re
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=pathlib.Path, help="Patched official Mesa source directory")
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--cc", default="cc")
    args = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    source = args.source.resolve()
    common = source / "src/amd/common"
    source_files = [common / name for name in ("ac_video.c", "ac_video.h", "amd_family.h", "ac_gpu_info.h")]
    uapi = source / "include/drm-uapi/amdgpu_drm.h"
    for path in [*source_files, uapi, root / "caps_fixture.c"]:
        if not path.is_file():
            raise SystemExit(f"missing source input: {path}")
    args.out.mkdir(parents=True, exist_ok=False)
    args.out = args.out.resolve()
    tu = args.out / "input-snapshot"
    tu.mkdir()
    for name in ("ac_video.c", "ac_video.h", "amd_family.h"):
        shutil.copyfile(common / name, tu / name)
    shutil.copyfile(root / "caps_fixture.c", tu / "caps_fixture.c")
    (tu / "ac_surface.h").write_text("""/* SPDX-License-Identifier: MIT -- host-only dependency stub. */
#ifndef TEST_AC_SURFACE_H
#define TEST_AC_SURFACE_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "amd_family.h"
enum pipe_format { PIPE_FORMAT_TEST = 0 };
struct radeon_surf;
#define MIN2(a,b) ((a) < (b) ? (a) : (b))
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#endif
""")
    ip_structs = re.findall(r"struct amd_ip_info \{.*?\n\};", (common / "ac_gpu_info.h").read_text(), re.S)
    if len(ip_structs) != 1:
        raise SystemExit("actual amd_ip_info declaration missing or ambiguous")
    (tu / "ac_gpu_info.h").write_text("""/* SPDX-License-Identifier: MIT -- host-only dependency stub.
 * amd_ip_info is copied from the caller's actual Mesa header.
 * radeon_info contains only fields read by ac_video.c; no device ABI is modeled.
 */
#ifndef TEST_AC_GPU_INFO_H
#define TEST_AC_GPU_INFO_H
#include "ac_video.h"
""" + ip_structs[0] + """
struct radeon_info {
   enum radeon_family family;
   enum vcn_version vcn_ip_version;
   enum vpe_version vpe_ip_version;
   uint32_t vcn_dec_version, vcn_enc_minor_version, vcn_fw_revision, vce_fw_version, uvd_fw_version;
   struct amd_ip_info ip[AMD_NUM_IP_TYPES];
   struct ac_video_caps video_caps;
};
#endif
""")
    constants = []
    for name in ("DECODE", "ENCODE"):
        matches = re.findall(r"^\s*#define AMDGPU_INFO_VIDEO_CAPS_" + name + r"\s+\d+\s*$", uapi.read_text(), re.M)
        if len(matches) != 1:
            raise SystemExit(f"actual UAPI constant missing or ambiguous: {name}")
        constants.append(matches[0].strip())
    (tu / "ac_linux_drm.h").write_text("""/* SPDX-License-Identifier: MIT -- host-only query stub; values from caller's UAPI. */
#ifndef TEST_AC_LINUX_DRM_H
#define TEST_AC_LINUX_DRM_H
""" + "\n".join(constants) + """
struct ac_drm_device;
int ac_drm_query_video_caps_info(struct ac_drm_device *, unsigned, unsigned, void *);
#endif
""")
    cc = shutil.which(args.cc)
    if not cc:
        raise SystemExit("C compiler not found")
    receipt = {
        "scope": "CPU actual-source capability policy; DRM ioctl results stubbed; no GPU or hardware acceptance",
        "hardware_acceptance": False,
        "host": platform.platform(), "machine": platform.machine(),
        "compiler": cc, "compiler_sha256": sha(pathlib.Path(cc).resolve()),
        "script_sha256": sha(pathlib.Path(__file__).resolve()),
        "source": str(source),
        "source_files": {str(p.relative_to(source)): sha(p) for p in [*source_files, uapi]},
        "inputs": {str(p.relative_to(args.out)): sha(p) for p in sorted(tu.iterdir()) if p.is_file()},
        "checks": [], "result": "RUNNING",
    }

    def run(name, cmd, env=None):
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env, cwd=args.out)
        (args.out / (name + ".stdout")).write_text(result.stdout)
        (args.out / (name + ".stderr")).write_text(result.stderr)
        row = {"name": name, "command": cmd, "exit": result.returncode,
               "stdout_sha256": sha(args.out / (name + ".stdout")),
               "stderr_sha256": sha(args.out / (name + ".stderr"))}
        receipt["checks"].append(row)
        return result

    passed = False
    try:
        version = run("compiler-version", [cc, "--version"])
        if version.returncode:
            raise RuntimeError("compiler version query failed")
        flags = ["-std=c11", "-g", "-Wall", "-Wextra", "-Werror"]
        for mode, extra in (("o2", ["-O2"]), ("sanitizers", ["-O1", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"])):
            binary = args.out / ("caps-" + mode)
            build = run("build-" + mode, [cc, *flags, *extra, str(tu / "ac_video.c"), str(tu / "caps_fixture.c"), "-o", str(binary)])
            if build.returncode:
                raise RuntimeError(f"compile failed: {mode}")
            env = dict(os.environ)
            env["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=0"
            env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            run_args = [str(binary)] + (["--ps4-only"] if mode == "sanitizers" else [])
            result = run("run-" + mode, run_args, env)
            expected = "38 cases" if mode == "sanitizers" else "40 cases"
            if result.returncode or expected not in result.stdout:
                raise RuntimeError(f"capability fixture failed: {mode}")
            receipt["checks"][-1]["binary_sha256"] = sha(binary)
        original = (tu / "ac_video.c").read_text()
        query = """   if (ac_drm_query_video_caps_info(dev, AMDGPU_INFO_VIDEO_CAPS_DECODE, sizeof(dec_cap), dec_cap) ||
       ac_drm_query_video_caps_info(dev, AMDGPU_INFO_VIDEO_CAPS_ENCODE, sizeof(enc_cap), enc_cap))
      return;"""
        mutants = [
            ("ignore-query-errors", query, """   (void)ac_drm_query_video_caps_info(dev, AMDGPU_INFO_VIDEO_CAPS_DECODE, sizeof(dec_cap), dec_cap);
   (void)ac_drm_query_video_caps_info(dev, AMDGPU_INFO_VIDEO_CAPS_ENCODE, sizeof(enc_cap), enc_cap);"""),
            ("omit-gladius-gate", "info->family == CHIP_LIVERPOOL || info->family == CHIP_GLADIUS", "info->family == CHIP_LIVERPOOL"),
            ("remove-width-clamp", "uint32_t width = MIN2(dec_cap[avc].max_width, 1920);", "uint32_t width = dec_cap[avc].max_width;"),
            ("preserve-stale-caps", "   memset(&info->video_caps, 0, sizeof(info->video_caps));", "   /* injected: stale caps retained */"),
        ]
        for name, before, after in mutants:
            if original.count(before) != 1:
                raise RuntimeError(f"mutation target ambiguous: {name}")
            source = args.out / ("mutant-" + name + ".c")
            source.write_text(original.replace(before, after, 1))
            binary = args.out / ("mutant-" + name)
            build = run("build-mutant-" + name, [cc, *flags, "-O2", "-I", str(tu), str(source), str(tu / "caps_fixture.c"), "-o", str(binary)])
            if build.returncode:
                raise RuntimeError(f"mutation compile failed: {name}")
            result = run("run-mutant-" + name, [str(binary)])
            if result.returncode == 0:
                raise RuntimeError(f"mutation escaped fixture: {name}")
            receipt["checks"][-1]["expected_rejection"] = True
            receipt["checks"][-1]["mutant_source_sha256"] = sha(source)
        passed = True
    except Exception as exc:
        receipt["error"] = str(exc)
    finally:
        receipt["result"] = "PASS" if passed else "FAIL"
        (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"result": receipt["result"], "receipt": str(args.out / "receipt.json"), "error": receipt.get("error")}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
