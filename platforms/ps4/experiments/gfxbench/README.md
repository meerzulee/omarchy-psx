# CarChase shadow-cascade diagnostic

Private native preparation uses GFXBench5.1.5 source commit
`89aa956f43836798d1eaaab8ec32d3dc8b02eead`. Preserve upstream BSD-3-Clause
source notices and separate asset licenses. The existing isolated benchmark
also contains the recorded Wayland/window and modern Vulkan-loader build
adaptations; this patch does not reproduce those earlier preparations.

`shadow0.patch` instruments only the CarChase GL scene. Warmup remains
unchanged: motion-blur initialization already calls a complete scene Render
at animation time50224. With`PSX_CARCHASE_SHADOW0=1`, the diagnostic waits for
the first timed frame, finishes earlier GPU work, logs shadow setup/clear and
each direct/instanced draw with program, mesh/material, TES/GS and bound
buffer/framebuffer identities. Each marker is flushed and each draw is
followed by`glFinish()`; synchronization deliberately changes timing.

After shadow cascade0 it flushes`SHADOW0_COMPLETE_EXIT86` and calls`_Exit(86)`.
It cannot proceed to cascade1 or later timed-frame passes. This intentionally
skips normal GL cleanup and benchmark results; exit86 plus the marker is a
diagnostic cut, never a benchmark score. A hung glFinish still requires an
external process timeout and independent UART/kernel supervision.

Build the existing private CMake tree's`testfw_app` target with`--parallel16`;
the GL scene is in a static archive and the application must be relinked.
Native preparation builds successfully. Diagnostic executable SHA256:
`df37e2fab7ae9048733e2c89f969638db5a61186b819a492243732696a771d1a`.
Patch SHA256:
`65cdb7ffb5329fa10ee697e3011ad4f755017ab0e895f4cc4e8419038e067a33`.
The original console benchmark is preserved. EXP-20261021-028 subsequently
runs this diagnostic once: it faults during motion-blur TileMax warmup, before
any first-timed-frame marker or cascade0 cut. The controller stops after15.502s.
Kernel records VM writes and a terminal UVD guard closure; completed fences do
not establish recovery. The owner reports no intended scene on the monitor.
This is a failed initialization observation, not a shadow-stage result.

The earlier CarChase VM fault remains unresolved. Runtime GPU virtual-address
allocation records, the earliest retained UART fault and stage/draw markers
are needed to attribute it. A clean stage with added synchronization would
only narrow the next diagnostic variable; it would not qualify CarChase or
prove a family-specific workaround. No reset, rearm or full-scene retry.


## Next reduced shader oracle (built; not run)

`tilemax-probe.c` creates one surfaceless desktop GL4.3 context and uses the
unchanged external GFXBench`mb_tile_max_reduction.shader`, SHA256
`e4974c719479cb9aa80e35d184167c94933a3fc6f80086f03630af0ee58794a3`.
The shader belongs to the pinned upstream source and retains BSD-3-Clause
notices. The harness defines the observed WG64, K30, four-pass,64×36 dispatch
geometry, uses a constant RG8 velocity texture and checks4,608 output floats
plus both4KiB guards after200dispatches. Scene setup, tessellation and adaptive
workgroup selection are absent. Constant texture input and added guards make
this a reduced diagnostic, not an exact replay or performance benchmark.

Native build uses`cc -O2 -Wall -Wextra -Werror tilemax-probe.c -o tilemax-probe`
with`pkg-config --cflags --libs egl gl`and`-lm`; compilation passes. The current
private binary SHA256 is
`97e8575de3943aa42d13eb5f4adc490f5142ed6737a2e472deb96df9ab6c306b`.
No GPU execution has occurred. Run only after physical recovery, clean guard/
fence checks and a new bounded experiment with an external process timeout.
A pass would narrow the problem to omitted scene/state/input history; it
would not exonerate Mesa or qualify CarChase. A failure still needs shader/BO
and command-stream attribution before a fix.
