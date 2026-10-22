# PS5 Omarchy development image

The native Linux x86-64 builder consumes the complete Linux psX PS5 artifact
contract and an explicit offline package snapshot. It creates regular files in
a new marked workspace. It never formats a device or writes console storage.
The existing PS4 build and deployed package identities remain unchanged.

This first profile uses Linux `7.2.3-psx-ps5-dev1`, community patches at
`753c7936dcb079bfeaaa0bb19dfc495744266500`, Omarchy source
`f0020448ca87329199de7cb12f2015ebc4a3e5e7`, and Arch packages from
`2026/08/20`. See `manifests/ps5-image.json` for immutable external firmware
identities and the PS5 boot parameters. Firmware is acquired for the ignored
image output; it is neither embedded in Linux nor committed to this repository.

## Build on the native host

First build and package the sibling kernel, preserving its entire module set
and complete corresponding GPL source:

```sh
cd ../linux-psx
./build.sh --target 7.2-ps5 --jobs 12
python3 scripts/ci/package_release.py --target 7.2-ps5
```

The packaging command refuses an existing `dist/`. Keep prior outputs and use
an isolated checkout for a new build. Native dependencies are in the kernel
build guide. Use `/usr/bin:/bin` ahead of language-manager shims when selecting
the host toolchain; no workspace-wide configuration trust is needed.

Build the three shared console packages with native `makepkg`, Git and
ImageMagick. `--nodeps` avoids installing target desktop packages on the build
host; the image's Pacman transaction still checks their dependencies. Set
`PKGDEST` to a new output directory. `--holdver` retains the source cache's
recorded immutable commit; a new cache is still acquired from upstream.

```sh
cd ../omarchy-psx/packages/omarchy-psx
PKGDEST=/absolute/build/packages makepkg --holdver --nodeps --nocheck
```

Supply the verified snapshot produced by the existing PS4 package snapshot
tool, containing `RELEASE.env`, `SHA256SUMS`, `manifest/packages.lock` and its
complete repository. The PS5 builder consumes the pinned common package
closure and replaces all three PS4-specific packages with the new common
packages. It adds signed mkinitcpio, SDDM and mtools from the same Arch date.
The existing local development snapshot uses checksums instead of production
package signing; this output is a private development candidate.

```sh
cd /absolute/workspace/omarchy-psx
sudo /usr/bin/python3 scripts/build-ps5-image \
  --snapshot /absolute/build/snapshot \
  --packages /absolute/build/packages \
  --kernel /absolute/workspace/linux-psx/dist/runtime \
  --work /absolute/build/ps5-image-work \
  --output /absolute/build/output/omarchy-ps5-4.0.0-dev1.img.xz
```

The sibling `dist/source/` must contain the matching source archive named in
`artifacts.json`. No kernel modules are installed on the build host. The rootfs
runs in a native private mount namespace and chroot, with no container/VM
runtime. `--resume` accepts only a marked workspace with identical selected
inputs, builder, profile and output path.

## Boot and owner experience

The default uncompressed image is 16 GiB; use media with at least that many
bytes (a nominal 32 GB USB device is sufficient). GPT partition 1 is ext4
`OMARCHY-PS5` starting at 500 MiB; partition 2 is FAT32 `PS5BOOT` at 1–500 MiB.
The FAT root contains `bzImage`, `initrd.img`, `cmdline.txt` and `vram.txt`.
The last file contains `0x20000000`: the loader expects hexadecimal bytes
for the baseline 512 MiB VRAM allocation.
The label-based command line is essential: a loader fallback to `/dev/sda2`
does not describe this root-on-p1 layout. The selected external loader is
supplied separately; building an image does not qualify any console firmware.

The initramfs includes the matching amdgpu/storage modules, external PS5 VCN
firmware, and `options amdgpu dpm=0 gpu_recovery=0` from the community PS5
image policy. It uses no build-host autodetection, PC UKI/Limine hooks, PS4
`AMD_DEBUG=notiling`, or PS4 Chromium workaround.

First boot presents the shared centered owner form on tty1. Keyboard, account,
password, optional Git identity, hostname and timezone are chosen locally.
Offline theme finalization prepares the desktop before SDDM autologin. There
is no default owner/password; root is locked and SSH starts disabled. The
source extraction preserves the original PS4 implementation and records its
file identities in `provenance/ps5-image-import.json`.

## Current limits and qualification

The first candidate uses Ethernet and a USB keyboard. IW620 out-of-tree
modules/per-console firmware staging and the separately requested MediaTek
fixes are follow-up work. Screen modes, HDMI audio, DRM acceleration and the
actual Hyprland session still require console testing.

The root filesystem has fixed capacity in this candidate. GPT expansion,
coordinated system updates, boot-set rollback selection, reset, snapshots and
encryption are pending. PC boot/update commands return a clear unavailable
message. The image does not advertise those unfinished release features.

Host validation checks kernel/source/package hashes, module releases, both GPT
headers and entry CRCs, ext4 consistency, FAT boot-file readbacks and compressed
image integrity. The output includes an image manifest, installed package lock
and SHA256. Keep the matching kernel/source packages alongside the image.

Console qualification is separate: use the workspace's bounded hardware
experiment and rollback rules before any boot-file write or boot trial. No
media flashing or console launch is performed by the builder or its tests.

The proposed shared PS4/PS5 rootfs with separate boot sets is described in
[the universal image notes](../../docs/UNIVERSAL-IMAGE.md). This PS5 candidate
does not implement that combined media layout.
