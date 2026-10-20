# Kernels and Firmware

The kernel comes from our sister project, [Linux psX](https://github.com/meerzulee/linux-psx). It holds the console patches, configurations and builds, and it doesn't depend on Omarchy. Omarchy psX pairs a selected kernel with its matching modules and a compatible boot set; each new combination needs its own test.

## Which kernel am I running?

Run `uname -r`:

- `6.18.44-ps4-baikal` is the kernel inside the v0.31 launcher. It's an earlier build from before the move to Linux psX, and it has no built-in Ethernet.
- `6.18.44-psx-ps4-baikal2` is the current Linux psX target: Linux 6.18.44 with 56 patches, including native Ethernet. The published CI build hasn't been boot-tested; the same patch set, built locally, passed two boots on our test console.
- `7.2.11-psx-ps4-baikal-native-dev1` is an experimental Linux 7.2 build. A local build passed one boot with short wired traffic; the published CI build hasn't been boot-tested.

Linux psX publishes its builds as experimental [pre-releases](https://github.com/meerzulee/linux-psx/releases), each with its complete corresponding source. Its [status page](https://github.com/meerzulee/linux-psx/blob/master/platforms/ps4/STATUS.md) says exactly what has and hasn't been tested.

## A kernel and its modules travel together

The kernel the launcher boots and the module tree on the USB drive must come from the same build. A matching version string isn't enough. So:

- Install the **whole** matching module tree for a new kernel, then run `depmod` for that release. Never copy in a single module, like just the Ethernet driver.
- Keep the previous kernel's modules, and keep a complete copy of the previous boot set — kernel, initramfs, boot arguments and VRAM setting — on another machine.
- Old launcher profiles pin their kernel by exact hash and must refuse a different one, so a new kernel needs its own boot set.

The exact steps, with safety checks, are in [Using Linux psX](../docs/USING-LINUX-PSX.md). New kernel and initramfs pairings need their own hardware test before anyone calls them working.

## Boot arguments

The launcher's tested boot profile tells Linux where everything is:

- `root=LABEL=OMARCHY-PS4` finds the USB root by its label.
- `pci=nocrs intremap=off` are platform settings for the PS4.
- `video=HDMI-A-1:1920x1080@60D` with a 1080p EDID pins the display mode.
- `libata.force=1.00:disable` keeps the internal SATA disk out of the way.
- `earlycon=uart8250,mmio32,0xC890E000,115200n8` sends early boot logs to the Baikal UART for debugging.
- `omarchy.*` options drive the splash and the USB layout checks.

The launcher also sets 1024 MB of VRAM. The profiles live in [`platforms/ps4/fpkg/bootargs/`](../platforms/ps4/fpkg/bootargs/README.md), with a verbose debug profile kept as the rollback. These values were measured on our one Baikal console; don't assume they suit other hardware.

## Firmware lives in the initramfs

Linux psX kernels embed no device firmware. Drivers built into the kernel can ask for firmware before Linux has mounted the USB drive, so the firmware has to be inside the initramfs. Omarchy psX doesn't store any firmware in its repository.

- **Display.** The Liverpool GPU firmware and the 1080p EDID come with the existing Omarchy PS4 initramfs, an external input that isn't stored in this repository. See [the initramfs notes](../docs/INITRAMFS.md).
- **Wi-Fi and Bluetooth.** The MediaTek MT7668 files are downloaded from their public sources onto your own machine, as described next.

## Wi-Fi and Bluetooth firmware

Run these from the **Omarchy psX repository root**, after preparing the compatible base described in [the initramfs guide](../docs/INITRAMFS.md). The example base path is a generated development output, not a file included in a clone:

```bash
python3 scripts/fetch-ps4-firmware
python3 scripts/add-ps4-initramfs-firmware \
  --base output/initramfs/ps4-baikal-partitioned/initramfs.cpio.gz
```

The first saves the files under the Git-ignored `cache/ps4-firmware/` and refuses any file whose hash doesn't match [`manifests/ps4-firmware.json`](../manifests/ps4-firmware.json). The second checks them again and writes a new initramfs under `output/initramfs/`; it refuses to overwrite an existing output.

_The result contains vendor firmware. Keep it on your own machines, and never commit, upload or share it._

One boot on our test console ran display, Wi-Fi and Bluetooth with a Linux psX kernel and an initramfs built this way. The PS4 system initializes the Wi-Fi chip before every launch, though, so whether Linux actually loaded these files wasn't witnessed.

## Using another distribution

The kernel doesn't need Omarchy. If you'd rather boot your own Linux root filesystem, follow [Linux psX's boot guide](https://github.com/meerzulee/linux-psx/blob/master/docs/BOOTING.md).

<!-- manual-navigation -->

---

[← Previous](07-storage.md) · [Contents](README.md) · [Next →](09-what-works.md)
