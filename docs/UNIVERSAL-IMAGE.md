# Shared PS4 and PS5 image

Status on 2026-10-21: common source and desktop packages are practical now.
A USB image qualified on both consoles is not available. The first PS5 image
is a development build with no console acceptance; the deployed PS4 boot
contracts remain separate.

The next useful shared image would contain one Omarchy root filesystem and
two complete boot sets. Each console still selects its own kernel, matching
initramfs, command line and firmware policy. Modules live under their distinct
kernel releases. This does not require a universal kernel binary.

## What is shared now

`packages/omarchy-psx/` extracts the common Omarchy runtime, settings and offline
owner setup for the PS5 milestone. The existing PS4 packages and their deployed
identities are preserved. Migrating PS4 to those common packages is a separate
change, with its console-specific graphics settings retained in a PS4 profile.

The kernel repository already has independent PS4 and PS5 targets. Its
`docs/UNIVERSAL-KERNEL.md` records why combining the patch sets into one binary
needs additional work: both loaders use subarchitecture number 5, and some
PS5 quirks currently apply at compile time.

## Current image contracts differ

| Contract | PS4 partitioned USB builder | PS5 development builder |
| --- | --- | --- |
| Partition table | DOS/MBR | GPT |
| Boot filesystem | p1, FAT, 4 GiB from 1 MiB | p2, FAT32, 1–500 MiB |
| Root filesystem | p2, ext4, after boot | p1, ext4, from 500 MiB |
| Root label | `OMARCHY-PS4` | `OMARCHY-PS5` |
| Boot files | `bzImage`, `initramfs.cpio.gz`, `bootargs.txt`, `vram.txt` | `bzImage`, `initrd.img`, `cmdline.txt`, `vram.txt` |

Sources are `platforms/ps4/scripts/build-partitioned-usb-image`, the preserved
PS4 initramfs, and `scripts/build-ps5-image`. Concatenating the two outputs or
putting both kernels under the same `bzImage` path does not resolve these
contracts.

## Work needed for one image

1. Select a partition layout and labels that both external loaders can read.
   Prove their actual media paths on each console before choosing final paths.
2. Give the two boot sets disjoint paths and manifests. The console-specific
   loader must select the matching set without replacing the other one.
3. Pass an explicit platform identity from each boot profile. Select graphics,
   network, firmware and owner-provisioning settings at each boot; the current
   PS5 image writes a fixed PS5 platform configuration.
4. Install both complete module trees and keep update/rollback transactions
   coherent with the selected kernel and initramfs. Preserve PS4-specific Mesa
   requirements while checking the shared graphics userspace on PS5.
5. Test cold boots, owner setup, display, input, storage and recovery on both
   consoles, including moving the same media between them.

Finish and qualify the PS5 baseline first, then migrate PS4 to the common
packages and design the dual boot-set image. A shared kernel is a later,
independent milestone.
