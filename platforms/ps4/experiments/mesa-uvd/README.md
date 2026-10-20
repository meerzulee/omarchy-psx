# PS4 Mesa / UVD candidate

Experimental Mesa 26.2.5 for Liverpool graphics and the experimental AVC-only
kernel transport. This directory owns distribution-side userspace changes;
the UVD kernel remains in the sibling `linux-psx` repository. It is not a
system package or supported release. Hardware results below have narrow scope.

## Why this candidate exists

EXP-20261020-006 downloaded 120 H264 frames through VAAPI, byte-exact against
software output. EXP008 showed a clean initial moving clip with `vo=wlshm`,
then a real decode error following interactive seeks. Seeking remains unresolved.

EXP009 reproduced the same stripes using saved NV12 with `hwdec=no` through
mpv OpenGL/Wayland-EGL. EXP010 reproduced them with a verified RGB8 EGL target.
The rendering fault therefore reproduces without a fresh H264 decode, and
automatic RGB10 output alone does not explain it. Wayland SHM still uses the
compositor; these tests do not establish that Wayland itself is faulty.

Source review found stock Mesa's Kaveri identity overrides Liverpool's reported
four render backends with two and selects raster `0x00000002`; the kernel uses
`0x2a00161a`. Patch 0001 ports the existing public PS4 family/raster fix to the
exact current stable release. This addresses a confirmed source mismatch. EXP011/012 subsequently showed
clean reference pixels and text, including owner monitor confirmation. The
upstream-version and PS4-patch changes were tested together; the exact causal
hunk has not been isolated.

Patch 0002 keeps console video capabilities on kernel-confirmed AVC/NV12,
with no encoding or inferred extra codecs. Family enum placement preserves
the legacy UVD stream/session/feedback/register branches. No serializer or
firmware bytes are imported. Liverpool UVD4.2 has no HEVC hardware decoding.

Official release and source:

https://docs.mesa3d.org/relnotes/26.2.5.html

https://archive.mesa3d.org/mesa-26.2.5.tar.xz

Original PS4 graphics patch:

https://github.com/DionKill/ps4-video-archlinux/blob/57e0f8ecc7a1df9b9664d682b19fadfe3e336f02/mesa-ps4/ps4-mesa.patch

## Isolated native build

Use Linux x86_64. The Mac can generate the video, but Linux libraries are
built on the native development host. Nothing installs to `/usr` on the host
or console. Python 3.12+ is needed for safe source extraction.

Create a private venv with Meson, Ninja, Mako, PyYAML, packaging and setuptools.
The first build uses Meson1.10.2, Ninja1.13.0, Mako1.3.10, PyYAML6.0.3,
packaging26.0 and setuptools80.9.0. Native dependencies include GCC/G++,
pkg-config, Bison/Flex, libdrm, libva, libglvnd, Wayland/protocols/scanner,
X11/XCB development files, libelf, zlib/zstd and SPIRV-Tools. No dependency
fallback downloads or global package installation are performed by the builder.

```sh
python3 build-candidate.py \
  --archive /path/to/mesa-26.2.5.tar.xz \
  --meson /path/to/venv/bin/meson \
  --work /path/to/new-build-directory --jobs 6
```

`sources.json` pins official source and ordered patches. The builder refuses
existing output directories, verifies inputs, records every source hash,
compiles with baseline x86_64 CPU flags, runs Mesa host tests, then stages
GL/EGL/GLX/GBM, RadeonSI/VAAPI and RADV into a private tree. ACO is used;
LLVM shared-library dependencies and LTO are disabled. Assertions remain
enabled. The native candidate passed all44 selected Mesa host tests. An
initial recipe incorrectly skipped non-default test helper builds; its failed
run was preserved before the corrected passing run. Only H264 decode is compiled into this bounded candidate; additional
video codecs and encoding require separate kernel work and qualification.

Outputs include `RESULT.json`, phase logs, the complete source manifest,
staged-file manifest and `mesa-psx-candidate.tar.xz`. Licenses, exact source
pins and patches accompany the staged libraries. Preserve these outputs.

## One-process comparison

After extraction into an isolated user-owned path:

```sh
python3 with-mesa.py --root /path/to/mesa-psx-candidate --verify-only
python3 with-mesa.py --root /path/to/mesa-psx-candidate --print-env
```

The wrapper verifies every staged file and symlink, selects absolute EGL and
Vulkan vendor manifests, and overrides the DRI/VA driver paths for one supplied
command. It does not restart or replace the compositor. No command runs with
`--verify-only` or `--print-env`.

GPU workloads on the console require a bounded UART experiment. The first
comparison reused EXP009's saved NV12 and OpenGL settings, changing selected
Mesa. Do not promote system libraries on a build or a single visual success.

## Recorded hardware results

All results use the same running Liverpool kernel/boot. The installed system
Mesa and compositor were not replaced. See the curated parent `SESSIONS.md`;
raw captures, generated videos and binary packages stay in private `lab/`.

- EXP011/012: saved reference NV12 through OpenGL is clean in the compositor
  screenshot and on the owner's monitor. Actual mapped EGL/GLX/Gallium/GBM
  hashes match the isolated candidate, renderer identifies Liverpool, and
  automatic RGB10/XR30 matches the formerly failing path. Normal player exit.
- EXP012: original canonical120-frame128×96H264 fixture decoded through the
  candidate VAAPI driver. Every2,211,840NV12 byte matches the software oracle.
  Post-exit INFO query is ready/idle and122 new UVD completions were observed.
- EXP013: native1920×1080p30 thirty-second fractal decoded all900frames through
  forced VAAPI/hwdownload. Every frame size/MD5 and the whole NV12 SHA256 match.
  The56.061952sec invocation includes CPU download and hashing; it is not a
  real-time playback benchmark. Its subsequent mpv initialization failed with
  CS rejection errno-28 and an abort; the recording loop did not run. Actual
  mpv logs requested four hardware threads despite vd-lavc-threads=1.
- EXP014: hwdec-threads=1, the hardware setting documented by pinned mpv0.41.0
  source, is confirmed in the actual log. Five completed1080p30 loops in the
  bounded prefix passed with zero display/decoder drops, measured PTS/wall
  speed0.997509x and5130 additional UVD completions. Captured picture/OSD are
  clean; owner confirmation of this moving clip remains pending. The same
  player was left looping for filming, with only the bounded prefix qualified.
  This fixes the configuration defect; the exact errno-28 guard in the earlier
  run remains unisolated. No kernel quota or clock change was made.

`decode-fractal.py` defaults to CPU-only input/CLI preflight. Explicit `--run`
performs exactly one forced VAAPI decode, fixed hwdownload to NV12 and bounded
per-frame/whole-stream hash capture, with no raw2.8GB output retained.

`demo.py` also defaults to preflight. Explicit `--run` launches a paused
forced-vaapi-copy player, verifies actual libraries/decoder/dimensions/thread
request, then unpauses once. It displays real decoder, source FPS, PTS/wall
speed, drop counters and UVD fence completions, and monitors the ongoing loop.
Three completed zero-drop passes are required for its READY record. Controls
are disabled; seeking remains a separate gate. Software fallback is disabled.
H264 can be decoded in software: hardware is required by the launcher and
verified execution, not intrinsically by the video file.

The native Mac fractal generator lives in `fractal/`, with deterministic
720p30 and1080p30 variants and independently checked software NV12 oracles.

## CPU-only demo guard checks

From the repository root:

```sh
python3 -B platforms/ps4/experiments/mesa-uvd/checks/demo_check.py
```

These portable checks exercise actual thread/log gates, IPC parsing, fence
parsing, loop progress and preflight with synthetic fixtures. They never
launch mpv or touch GPU/debugfs/live process state. The frozen controller
used in EXP014 passed62 checks; these do not establish hardware acceptance.

## Recovery and remaining gates

Normal exit restores application driver selection because it was process-local.
Do not reset/unload/rearm the experimental UVD kernel. On a terminal driver
fault, stop and use the preserved full-power-off/preparation recovery workflow.
Preserve the existing Linux boot while it remains usable.

Full desktop adoption, long-duration playback, supported resolutions/profiles,
controlled seeking, repeated sessions and at least three cold boots of a frozen
matching artifact set remain separate acceptance gates. Gladius is source-only.
This directory publishes experimental source only. Binary releases, firmware redistribution and system-wide adoption are outside this source package.
