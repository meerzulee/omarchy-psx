# PS4 source import notes

This is the PS4 implementation imported into `omarchy-psx/platforms/ps4`.
Original source is recorded per file in the root
[`provenance/ps4-worktree-import.json`](../../../provenance/ps4-worktree-import.json).
The source includes uncommitted work from the old checkout; its original HEAD
is context rather than a claim that those pending bytes exist in that commit.
Raw UART logs, ignored downloads, kernels, modules, firmware, PKGs and generated
images were excluded. Two already tracked raw UART logs are deliberately absent.
Curated experiment conclusions remain in `experiments/SESSIONS.md`; local LAN
addresses, MACs, owner home paths, key fingerprints and old credentials are
replaced by documentation examples. Machine/volume/boot UUIDs and USB serials
are pseudonyms too; distinct local IP relationships are preserved. Hardware PCI/PHY identities, hashes,
experiment IDs and observed failure limits remain intact.

## Running source tools

Run shared acquisition from the repository root:

```sh
python3 scripts/setup-workspace
python3 scripts/fetch-ps4-initramfs-seed
```

Run platform-specific commands from `platforms/ps4`. Local `output/`, `cache/`,
package/profile inputs and container mounts resolve from that directory. The
platform setup wrapper delegates to the root. The loader helper reads root
source pins and places its verified upstream input in the workspace, without
sending a payload. Kernel builds belong to the sibling `linux-psx` repository;
`build-gift-rootfs` defaults to its `output/6.18-ps4-baikal` and accepts an explicit
`--kernel-output DIRECTORY`. This source import and the new kernel pairing have
not produced a newly accepted distribution image. Image wrappers retain their
OrbStack requirement; native Linux image-builder work remains separate.

`build-xfce-initramfs` consumes the pinned public v26 seed from root
`cache/ps4/initramfs-v26-with-edid.cpio.gz` or `PS4_SOURCE_INITRAMFS`. It checks
the seed SHA-256, assembles the imported `/init` and splash/installer tools,
and preserves the GPU firmware/EDID files from that explicitly acquired input.
The seed is an earlier input, not the exact current Omarchy initramfs. Generated
archives and their firmware remain local. The current exact replacement-only
workflow lives at root `scripts/repack-ps4-initramfs` and `docs/INITRAMFS.md`.

## Frozen boot profiles

The existing `fpkg/boot-profiles`, release manifests and staging hashes describe
original PS4 builds. They remain unchanged to keep their evidence meaningful.
The new firmware-free Linux psX build has a different release/config and cannot
pass those hashes; do not remove hash gates or relabel it as an accepted image.

- `fpkg/tools/stage-internal-boot-set` and `stage-offline-bundle` require
  `PS4_HISTORICAL_KERNEL_IMAGE=/absolute/path/to/original/bzImage`.
- The internal boot-set helper also accepts `PS4_HISTORICAL_INITRAMFS` when the
  exact original archive is explicitly acquired elsewhere.
- `scripts/apply-usb-boot-profile-linux` is retained as archived source and
  refuses all writes before probing a device. Its old label-only identification
  predates the stable USB identity/explicit-confirmation contract. Port those
  checks before enabling it; a historical module archive alone is insufficient.
- The frozen `scripts/build-baikal-beta-release` requires
  `PS4_HISTORICAL_KERNEL_OUTPUT=/absolute/path/to/original/output`, verifies
  its exact kernel/module hashes, and passes that directory to the rootfs
  builder. It cannot pick up the new default psX kernel accidentally.

These variables select inputs, not exceptions to validation. Every original
size/hash gate remains active. Reproducing a historical profile may require
externally acquired artifacts that are neither published here nor silently
copied from an old checkout. Creating a new Linux psX FPKG/image profile requires
its own firmware/module integration, artifact manifest and hardware acceptance.
Source migration alone does not authorize storage writes or console operations.

The generic rootfs builder verifies actual kernel/module/version checksums
before opening a build container. Present config/build metadata must agree;
finding a filename in a checksum list alone is insufficient.

## Private development access

Release images keep root locked, defer owner creation and prohibit SSH password
login. There is no distributed development password. The private-only
`provision-debug-rootfs` tool now requires:

```sh
sudo ./scripts/provision-debug-rootfs --private-config /private/password-hash \
  /mounted/development-root /private/authorized-key.pub
```

The root-owned regular config must be mode `0600` and contain exactly one
SHA-512 crypt hash line, produced privately by the operator. It is parsed as data,
never sourced as shell code. Keep it outside the checkout. SSH remains key-only;
the supplied password is for the local development account. This tool still
modifies the identified mounted root and belongs in an authorized hardware
experiment, not an ordinary source test.

Temporary restricted recovery requires an explicit public-key fingerprint:

```sh
fingerprint=$(ssh-keygen -l -E sha256 -f /private/key.pub | awk '{ print $2 }')
# In the authorized experiment, pass the fingerprint explicitly through sudo:
sudo env OMARCHY_RECOVERY_KEY_FINGERPRINT="$fingerprint" \
  ./gift-dev/arm-recovery --check EXP-YYYYMMDD-NNN-A1
```

The operator must authorize and run `gift-dev/arm-recovery` in the established
bounded experiment. The helper compares the intended fingerprint with the
existing development key; it no longer embeds a project owner's identity.

## Compatibility boundary

Historical documents keep old repo/release names as evidence. Their opening
notices identify that scope. Old package names, labels (`OMARCHY-PS4`, `PS4BOOT`)
and `/data/linux` locations are deployed interfaces, not stale repository paths.
The optional imported `omarchy-ps4-ethernet` package targets the historical MTS2
kernel and has an unresolved unattended-startup acceptance gate; do not enable
it for a new Linux psX kernel. Root `scripts/activate-baikal-ethernet` is the
explicit new-kernel adapter, with its own version/metadata/once-per-boot guards.
PS5 remains a separate planned integration and has no hardware acceptance here.
