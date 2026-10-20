# PS4 Mesa graphics port

`0001-ps4-graphics-families.patch` targets the exact official Mesa 26.2.5
release archive. Apply with `patch -F0 -p1` from its extracted root.
The archive and patch digests, attribution, adaptations and checks are in
`ps4-graphics-provenance.json`; do not substitute a moving Mesa Git branch.

This is a port of the Liverpool/Gladius graphics changes in the pinned
DionKill repository patch (commit author: froyo). Existing Mesa/AMD
per-file MIT copyright and license notices remain unchanged; the source
repository's accompanying license is preserved in `LICENSE.ps4-mesa`.

https://github.com/DionKill/ps4-video-archlinux/blob/57e0f8ecc7a1df9b9664d682b19fadfe3e336f02/mesa-ps4/ps4-mesa.patch

The patch identifies the kernel's FAMILY_KV console revision ranges and
selects console raster layouts, names, compiler target, cache classification
and GS depth. New shared family IDs remain within the existing GFX7 range.
The unused private drm/radeon enum additions and unrelated CLC LLVM edit
were omitted. Build all selected Mesa components from the same patched
source; these internal enum values are not a system-library replacement API.

Graphics source and CPU contract checks passed. Full native Mesa compilation
and the separately owned UVD capability patch have their own receipts. No
installation or PS4 visual result is established by this directory. The
source mismatch is concrete; fixing the observed stripes remains a hardware
test question, including the separate XR30/EGL-format hypothesis.
