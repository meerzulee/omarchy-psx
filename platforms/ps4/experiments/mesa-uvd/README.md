# PS4 Mesa integration

Mesa patches, pinned native builder and graphics/UVD test tools now live in Linux psX:

https://github.com/meerzulee/linux-psx/tree/master/userspace/mesa

In the sibling workspace use `linux-psx/userspace/mesa/`. This directory owns
Omarchy package installation and update policy. The curated hardware history
remains in the parent `SESSIONS.md`; moving source does not qualify an update.

## Current system trial and update policy

EXP-20261020-022 installed the exact tested26.2.5 dev2 files and rendered clean GL/WebGL,
but its Vulkan check stalled and the experimental UVD runtime timed out.
Both original signed26.1.7 packages and previous rendering settings were
restored. Stable system adoption remains withdrawn; consult the Linux psX
[Mesa test matrix](https://github.com/meerzulee/linux-psx/blob/master/docs/MESA-TESTING.md).

`package-arch.py` is a data-only native Arch packager for a hash-verified
candidate; it never installs, enables repositories or operates the GPU.
Its local build skips dependency installation; an actual installation must
resolve its dependencies and verify the complete package/stage identities.
The unsigned local package file is not a signed public release. Preserve
verified signed original packages before an authorized installation trial.

Normal Omarchy updates remain blocked by the existing profile. Keep offline
repository policy and signatures intact; never run upstream refresh/update
commands to install this candidate. `graphics-hold.conf` records the additional
Mesa/RADV IgnorePkg policy used on the test console. Include it under Pacman's
options only through an authorized configuration change. Holds do not replace
a complete matched-package qualification and rollback set.

## Owner's experimental default

EXP-20261021-023 installed the exact dev5 Mesa/RADV stage as local packages
`1:26.2.5-5.1`, following the owner's explicit request. All40 staged file and
symlink identities match; package integrity and database checks pass. This
CPU-only transaction preserved rendering settings (including `AMD_DEBUG=notiling`),
offline repositories, required signatures, graphics holds and the update guard.
Verified signed26.1.7 rollback packages remain saved on the console.

The package change did not restart the desktop or operate the GPU. The boot
was already terminal-faulted by CarChase and still needed full power-off.
EXP-20261021-025 subsequently verifies one fresh boot: all40 stage identities
match, Hyprland/Xwayland map installed Gallium26.2.5, and the owner confirms
normal desktop/mouse. This experimental default is not stable-image promotion;
CarChase remains unfixed and repeated boots/full graphics coverage remain open.

The separate [browser codec policy](../browser-codecs/README.md) selects
YouTube H.264 instead of unsupported AV1/VP9. EXP027's isolated Chromium VAAPI
attempt reaches5UVD completions, then CS rejection(-28) aborts its GPU process.
No terminal kernel fault is observed. Normal Chromium's software-rendering
workaround remains enabled; browser hardware decoding is not qualified.

## Package artifacts

Git contains the source, patches, pinned builder and this package recipe.
Distribute the matched `mesa` and `vulkan-radeon` packages together as artifacts,
with `PACKAGES.json`, `SHA256SUMS` and the exact packaging inputs. Keep generated
`src/` and `pkg/` work directories out of the distributed set. The candidate
archive includes its source pins, patches and license notices; full upstream
Mesa is fetched through Linux psX's pinned native builder.

On a native x86-64 Arch build host, after building and verifying the stage:

```sh
python3 package-arch.py \
  --archive /path/to/mesa-psx-candidate.tar.xz \
  --archive-sha256 5c397d86a769ed55dd35798c32bfcedea5c4e3ce6eee5147dd282a04c9385fe9 \
  --manifest-sha256 687af5a366d4bba5af1f72cf5b1a57c4e09d1cfef58257a898ee34da2c7e3964 \
  --mesa-source /path/to/linux-psx/userspace/mesa \
  --candidate ps4-mesa-26.2.5-fill-bounds-htile-dev5 \
  --pkgrel 5.1 --output /path/to/new-package-output
```

Package releases are distinct from candidate identities. Select both explicitly;
the recipe rejects a mismatched candidate and verifies every staged file before
packaging. Hashes identify bytes but do not replace package signatures. Current
local packages are unsigned experimental artifacts, not a signed public release.
A public release still needs reviewed corresponding source, qualification scope,
signing and an explicit publication step. No upstream refresh or automatic
Omarchy update is part of this packaging flow.
