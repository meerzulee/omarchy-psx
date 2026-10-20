# FAQ

## Where are downloads?

The [Omarchy psX Telegram channel](https://t.me/omarchy_psx) carries downloads and release announcements. Read each download's hardware notes and status, and use its matching image and launcher. Development candidates still require the tests described in [Getting Started](02-getting-started.md).

## Is there a complete installation image in this repository?

The repository contains source and build tools. A usable installation needs a matching launcher or loader, kernel, initramfs, module tree and USB root. Start with [Getting Started](02-getting-started.md); the manual assumes a working console Linux boot environment.

## How do I prepare the USB on Windows, macOS or Linux?

The intended public installation uses one compressed `.img.xz` image on all three. Open balenaEtcher, choose _Flash from file_, select your USB with _Select target_, and choose _Flash!_. Wait for validation, safely eject the drive, then connect it to the PS4 and use the matching Omarchy launcher. Flashing erases the selected drive. Follow [Getting Started](02-getting-started.md#on-your-computer) for the complete flow and current development status.

## Do I download the Linux psX kernel separately?

For the complete Omarchy USB image, the selected Linux psX kernel and its matching modules are already included, together with the launcher package and startup files. Use the image and launcher from the same release. Separate kernel downloads are for custom installations and development.

## Will a 64 GB or 128 GB USB use its remaining space?

The same image is designed for both sizes. On first boot, the FAT32 boot partition stays at 4 GiB and the ext4 system partition expands into the remaining space. This automatic growth still needs a PS4 hardware test on the new image. See [Storage](07-storage.md).

## Will it mess with my PS4?

The Linux root and personal files live on the USB drive. Normal profiles disable Linux access to internal SATA; the launcher has its own application and boot files on the console. This is a development beta, so keep recovery copies before changing boot files or storage.

## Can I keep using my PS4 normally?

Yes. Every cold boot starts the PS4 system as usual. Omarchy only runs when you launch it.

## Which PS4 do I need?

Recorded hardware evidence comes from one PS4 Slim with the Baikal B1 southbridge. Other Baikal revisions, Aeolia and Belize consoles, and the PS4 Pro have no local acceptance record. See [Contributing](14-contributing.md) for useful hardware reports.

## What about the PS5?

A complete Omarchy desktop for PS5 is planned. Kernel and early-userspace development are separate candidates, with no local PS5 hardware acceptance. PS4 boot sets and observations do not qualify them.

## Can I play PS4 games in Omarchy?

Omarchy psX runs Linux applications. It does not provide a runtime for PlayStation games.

## Can I play PC games?

Not as a supported feature yet. Vulkan has only passed short smoke tests, some gaming installers are switched off because they assume a PC graphics stack, and games built for newer CPUs won't run on the PS4's Jaguar cores (see [Troubleshooting](11-troubleshooting.md#an-app-crashes-the-moment-it-starts)).

## Can I install Omarchy on the PS4's internal drive?

Internal Linux installation is unsupported. Reading the internal SATA disk from Linux was unreliable on the test console, so normal profiles disable it. The Linux root lives on external USB; the launcher's separate boot folder is described in [Storage](07-storage.md#the-ps4s-internal-drive).

## Why is the display stuck at 1080p?

The PS4 drives HDMI through a bridge chip, and 1920×1080 at 60 Hz is the mode that has been tested end to end. An ultrawide mode exists as an unqualified experiment.

## Why can't I suspend?

Suspend isn't available on the PS4 in Linux yet, so it's hidden from the menu.

## Can I update with `omarchy-update` or `pacman -Syu`?

Omarchy's update commands are switched off, and there are no rolling Arch updates on the PS4. The kernel, its modules and the graphics stack have to be tested together, so new versions come as matched releases. See [What's Different on PS4](05-whats-different-on-ps4.md#updates-come-as-releases-not-rolling).

## Is my data encrypted?

No, not yet. Anyone with the USB drive can read it. See [Storage](07-storage.md#encryption).

## Can I run a different Linux distribution?

Yes. The Linux psX kernel doesn't depend on Omarchy. Follow its [boot guide](https://github.com/meerzulee/linux-psx/blob/master/docs/BOOTING.md) with your own initramfs and root filesystem.

## Is this an official Omarchy or Sony project?

Neither. Omarchy psX is an unofficial community port. It isn't made or endorsed by the Omarchy project, and it isn't affiliated with Sony.

## Where's the source?

On GitHub: [Omarchy psX](https://github.com/meerzulee/omarchy-psx) under the MIT License, and [Linux psX](https://github.com/meerzulee/linux-psx) under GPLv2, with complete corresponding source published for its kernel builds.

---

For errors and broken bits, see [Troubleshooting](11-troubleshooting.md).

<!-- manual-navigation -->

---

[← Previous](11-troubleshooting.md) · [Contents](README.md) · [Next →](13-building-from-source.md)
