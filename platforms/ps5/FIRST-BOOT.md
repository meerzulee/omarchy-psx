# PS5 Linux bring-up before the Omarchy desktop

Target: original PS5, system software 12.40. The owner's working jailbreak and
ELF delivery are assumed. Existing payload loaders can provide that entry point;
the firmware-specific hypervisor and Linux handoff remain separate work.

Research was refreshed on 2026-10-18. The selected upstream heads are unchanged:

| Reference | Commit | Purpose |
| --- | --- | --- |
| `ps5-linux/ps5-linux-patches` | `753c7936dcb079bfeaaa0bb19dfc495744266500` | PS5 kernel patch and configuration |
| `ps5-linux/ps5-linux-loader` | `64637c177eaed277fb6ccce394cbb29dd047b893` | Established Linux boot-file and handoff contract |
| `pLabs5/pLinux5-NG` | `978cfb3a1ff1dd5e6fc6e776c5aae3ed8c5770fd` | Experimental newer-firmware handoff reference |
| `ps5-linux/ps5-linux-image` | `52db0a42302e4a6b5420a11fa00a84841ea5db56` | Arch rootfs, mkinitcpio and firmware integration reference |

The established loader selects its own older-firmware hypervisor paths. It is
not a generic Linux entry point that gains 12.40 support by running Reborn first.
The reviewed newer loader also lacks a 12.40 environment entry. No payload is
selected or sent by this preparation. See [BOOT-DEPENDENCIES.md](BOOT-DEPENDENCIES.md).

## Local kernel candidate

Sibling `linux-psx` now has target `7.2-ps5`, release
`7.2.3-psx-ps5-dev1`, using Linux commit
`58e7295cfecaddec94629160386412e0f2b1e8fe`. The upstream patch is unchanged.
The derived config changes its release name and removes embedded firmware;
the original config and exact adaptation remain recorded in kernel provenance.

Build through `linux-psx/scripts/build-kernel-orbstack` on macOS ARM64, or
its native builder on Linux x86-64. Keep `bzImage`, the complete matching
module archive, resolved config and checksums together. This is a local
development artifact; release packaging and hardware qualification are separate.

The first local OrbStack build completed on 2026-10-18 with Debian GCC 14.2.0
and 519 matching modules. Its measured build identities are recorded in
`linux-psx/provenance/7.2-ps5.json`; this establishes compilation only.

## First boot question

The first experiment should establish that the selected loader enters this
kernel, reaches our `/init`, and provides a usable diagnostic console. A
RAM-only BusyBox initramfs keeps this question independent of Omarchy packages,
rootfs installation and desktop rendering. It can report the running release,
command line and enumerated devices, then offer a supervised shell.

The probe's startup must not mount block devices, install a rootfs, repair or
resize filesystems, bring up networking, or reboot automatically. Matching HID
modules are needed for USB keyboard input; including them is not evidence that
the keyboard works on this console. Manual commands entered into a root shell
remain consequential actions under the hardware experiment's scope.

## Assemble the diagnostic files locally

After the kernel build completes, run from the `omarchy-psx` root. The commands
only read explicitly selected files and create a new local output directory.
They do not install BusyBox, send a payload or access console storage.

```sh
python3 scripts/fetch-ps5-probe-userspace
python3 scripts/fetch-ps5-probe-userspace --check
python3 scripts/build-ps5-probe-initramfs \
  --kernel-output ../linux-psx/output/7.2-ps5 \
  --busybox cache/ps5-probe-userspace/busybox \
  --busybox-sha256 7ae95c260622412ceba6eb9f45d68f616cdc091a1d71d6c0a08b5875bb2c31dd \
  --busybox-notice cache/ps5-probe-userspace/copyright \
  --busybox-license cache/ps5-probe-userspace/GPL-2.txt \
  --output output/ps5-probe/7.2.3-psx-ps5-dev1
```

The builder requires host `zstd`, validates all six raw kernel outputs and
their checksums, verifies the PS5 configuration and kernel/module release,
checks the static x86-64 BusyBox executable, and constructs the archive as
data. It never runs the kernel, modules or BusyBox. A pre-existing output
directory is refused; choose a new one for a changed candidate.

The resulting directory contains `bzImage`, gzip-compressed `initrd.img`,
`cmdline.txt`, `vram.txt`, `receipt.json` and `SHA256SUMS`. The extra
`cmdline-uart.txt` is an explicit alternative for a later qualified capture
setup. Only the filename `cmdline.txt` is consumed by the reference loader.
The probe carries the complete exact module tree but automatically requests
only `hid_generic` and `usbhid`. The 512 MiB VRAM value follows the reference
default and is not a measured Omarchy sizing choice.

Debian's `busybox-static` package, full source inputs and copyright/license
notices are pinned in `manifests/ps5-probe-userspace.json`. They remain in local
ignored cache; the initramfs retains its notices. This is preparation for a
future experiment, not an installable 12.40 Linux payload or Omarchy rootfs.

The first diagnostic set is now assembled at
`output/ps5-probe/7.2.3-psx-ps5-dev1/`. Its `initrd.img` is 47,963,239 bytes,
with SHA256 `435bc67d5bf04c035e89f1e13082b43e5f91d5368f67adf805eea6fcaa8ce8c0`.
Its kernel SHA256 is
`64162b82cf3f7ac37cdb8b4fe8638b10a1d53907e1bfb1be48383b2c9726c822`.
The output checksums passed and an independent gzip/newc inspection compared
every module and metadata file against the complete installed kernel tree,
including all 519 modules. The pinned BusyBox, notices, `/init`, device nodes
and command-line files also passed. `receipt.json` records the exact inputs;
these ignored local outputs are not public release artifacts.

## Console and firmware requirements

The source config enables simple DRM and framebuffer console support, but the
reviewed loader does not populate `boot_params.screen_info`. Therefore a visible
HDMI shell is unqualified. The patched kernel also registers the built-in
Titania UART as `ttyTitania0`; a UART route requires actual PS5 wiring/capture
access, which has not been established here. PS4 UART evidence does not qualify
a PS5 capture setup. No console mode is accepted merely because its name exists
in source.

The later HDMI stage needs the matching AMDGPU module/dependencies and required
external firmware, or demonstrated framebuffer handoff. The upstream config
embeds `amdgpu/ps5_vcn.bin`; the new kernel leaves firmware external. No GPU or
Wi-Fi firmware is bundled in this probe.

The existing Linux loader itself writes extracted Wi-Fi firmware beside the
selected initrd. A RAM-only `/init` does not make the whole loader path
non-writing. That behavior must be included in any future experiment scope.

## From the shell to Omarchy

After the handoff and diagnostic console work, qualify USB input and the
intended USB/ext4 root device. Then assemble a fresh Arch root with the exact
kernel module tree, required firmware and a distinct PS5 root LABEL/UUID. Use
the upstream Arch recipe's explicit kernel selection and omit host-hardware
autodetection when generating its mkinitcpio image.

Next qualify AMDGPU, Mesa, HDMI and a Wayland session before adding Omarchy's
pinned desktop/packages. Ordinary Omarchy userspace can run on that Arch root;
the console-specific work belongs in the kernel, loader, early userspace and
hardware settings. Do not rename a PS4 image or inherit its PCI IDs, CIK workarounds,
boot labels, module tree, installation services or package exclusions.

The final loader-facing directory will contain `bzImage`, `initrd.img`,
`cmdline.txt` and `vram.txt`. Root selectors must agree with the actual rootfs
and `fstab`. Keep one complete boot set together because the reference loader
searches for each filename independently. Launcher packaging can follow once
this path works; it does not gate kernel or desktop development.

## Primary source locations

Kernel configuration and original patch:
https://github.com/ps5-linux/ps5-linux-patches/tree/753c7936dcb079bfeaaa0bb19dfc495744266500

Boot-file loading and firmware writer:
https://github.com/ps5-linux/ps5-linux-loader/blob/64637c177eaed277fb6ccce394cbb29dd047b893/source/loader.c
https://github.com/ps5-linux/ps5-linux-loader/blob/64637c177eaed277fb6ccce394cbb29dd047b893/source/firmware.c

Linux boot parameters:
https://github.com/ps5-linux/ps5-linux-loader/blob/64637c177eaed277fb6ccce394cbb29dd047b893/shellcode_hv/boot_linux.c

Arch recipe:
https://github.com/ps5-linux/ps5-linux-image/blob/52db0a42302e4a6b5420a11fa00a84841ea5db56/distros/arch/image.yaml
