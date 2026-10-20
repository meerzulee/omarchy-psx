# Seahorse flight: private UVD playback fixture

This source renders an original Mandelbrot zoom on the native Mac CPU. It follows
the seahorse valley at `-0.743643887037151 + 0.131825904205330i`, zooms about
1480 times, rotates gently, and moves through a midnight/lapis/turquoise/pearl/
amber/coral palette. Both explicit variants have 30 fps, 900 different frames,
and 30 seconds. There is no audio, caption, overlay, random seed, or external
image input. Dark interiors are iteration-limited; this is a visual fixture.

`render.c` uses double precision, a continuous escape-time palette, analytic
cardioid/bulb interior tests, a mild vignette, and 600–1200 iterations. Each
pixel is independent. Final renders use 1.5 times the output resolution in each
axis and Lanczos downsampling to soften subpixel detail. Quick previews render
at the selected output resolution directly. Thread scheduling does not change the image. Floating
point/library/encoder revisions can change bytes across hosts; use the saved
hashes to identify an exact fixture.

`generate.py` requires native macOS, Python 3, clang, FFmpeg with libx264, and
ffprobe. It does not install packages or use a VM/GPU. Pass a new private output
directory whose parent already exists; all outputs, executable, source snapshots,
versions, exact command arrays, diagnostics and failure state stay there.

| Variant | Video | Native RGB samples | H.264 level | VBV ceiling / buffer |
| --- | --- | --- | --- | --- |
| `720p30` (default) | 1280×720 | 1920×1080 | 3.1 | 10 Mbit/s / 10 Mbit |
| `1080p30` | 1920×1080 | 2880×1620 | 4.1 | 20 Mbit/s / 40 Mbit |

The completed private `render-03` 720p clip and its source snapshot remain the
canonical fixture for initial higher-resolution qualification. The 1080p clip
is a separate fixture; its SPS codes 1920×1088 and crops eight bottom rows to
1920×1080. Its creation does not establish hardware decoding support.

From the workspace root, for example:

```sh
mkdir -p lab/mesa-uvd-2026-10-20/fractal
python3 -B omarchy-psx/platforms/ps4/experiments/mesa-uvd/fractal/generate.py \
  --preview --output lab/mesa-uvd-2026-10-20/fractal/preview-01
python3 -B omarchy-psx/platforms/ps4/experiments/mesa-uvd/fractal/generate.py \
  --output lab/mesa-uvd-2026-10-20/fractal/render-01
python3 -B omarchy-psx/platforms/ps4/experiments/mesa-uvd/fractal/generate.py \
  --variant 1080p30 --output lab/mesa-uvd-2026-10-20/fractal/render-1080p-01
```

The MP4 uses x264 Constrained Baseline, 8-bit limited-range BT.709 4:2:0,
the selected level, one reference frame, CAVLC, no B pictures, no weighted
prediction, and fixed 60-frame I/P GOPs. Both use CRF 18 with the table's VBV
ceiling/buffer. MP4 sample PTS
and DTS start at zero, advance exactly 1/30 second, and place `moov` before
`mdat` for faststart. `check.py` verifies the actual parsed bitstream's profile,
picture types, pixel format, dimensions and all 900 packet/frame timestamps.
FFmpeg's `trace_headers` additionally checks actual SPS/PPS profile constraints,
level, coded/cropped geometry, single-reference limits and CAVLC; it copies compressed packets without
decoding or invoking hardware.
Filtering and x264 encoding use one thread each to avoid a threaded VBV
bitstream variation observed during the pilot runs. Pixel rendering still uses
eight independent row workers by default. The saved MP4 hash identifies the
exact encoded artifact; bitwise reproducibility across toolchains is not claimed.

The explicitly selected FFmpeg software H.264 decoder produces
`reference-nv12.framemd5` (one MD5 per complete NV12 frame) and
`reference-nv12.sha256` (SHA256 of all decoded bytes in order: 1,244,160,000
bytes for 720p, 2,799,360,000 for 1080p).
`RESULT.json` binds these outputs, media probes, contact sheet and exact recipe.
The final contact sheet shows frames 0, 180, 360, 540, 720 and 899, left to
right then top to bottom. The preview uses 0, 179, 358, 537, 716 and 895.
Three full-resolution decoded PNGs additionally show frames 0, 450 and 899.

An independent read-only structure/reference check is:

```sh
python3 -B omarchy-psx/platforms/ps4/experiments/mesa-uvd/fractal/check.py \
  lab/mesa-uvd-2026-10-20/fractal/render-01/seahorse-flight-720p30-baseline.mp4 \
  --framemd5 lab/mesa-uvd-2026-10-20/fractal/render-01/reference-nv12.framemd5 --decode
python3 -B omarchy-psx/platforms/ps4/experiments/mesa-uvd/fractal/check.py \
  lab/mesa-uvd-2026-10-20/fractal/render-1080p-01/seahorse-flight-1080p30-baseline.mp4 \
  --variant 1080p30 \
  --framemd5 lab/mesa-uvd-2026-10-20/fractal/render-1080p-01/reference-nv12.framemd5 --decode
```

For a future authorized PS4 test, the external player must force hardware
decoding and reject fallback. H.264 media cannot require hardware intrinsically.
The intended player invocation is:

```sh
mpv --no-config --load-scripts=no --hwdec=vaapi-copy \
  --hwdec-software-fallback=no --vo=wlshm --no-audio --fullscreen \
  --osc=no --osd-level=0 --osd-bar=no --input-conf=/dev/null \
  --input-default-bindings=no --input-builtin-bindings=no \
  --input-vo-keyboard=no --input-terminal=no --input-cursor=no \
  --input-gamepad=no --cursor-autohide=always --start=0 \
  --resume-playback=no --loop-file=no --keep-open=no -- /path/to/clip.mp4
```

Pin the actual player/version and confirm VAAPI selection in its diagnostic
output. The supplied tools never transfer/launch media or operate the console.
Hardware activation needs its own authorized bounded experiment and UART.
Player option reference:
https://mpv.io/manual/stable/

Software decode and a pleasant picture do not establish UVD correctness or
real-time performance. Future exact NV12 comparison should begin with the pinned
software reference; any hardware/software pixel differences need a documented
comparison policy and investigation before acceptance. No hardware result is
claimed here.
