# Getting Started

Prepare Omarchy by flashing one compressed USB image on Windows, macOS or Linux, then launching it on your PS4 and completing the first-time setup:

**Download → Flash → Launch → Setup → Desktop.**

The image includes Omarchy, its applications, the selected [Linux psX](https://github.com/meerzulee/linux-psx) kernel and matching modules, plus the launcher package and startup files. **Flashing installs the system onto the USB drive**, where it runs and stores your personal files.

## What you need

- A **PS4 Slim with the Baikal B1 southbridge** is the recorded test hardware. Other Baikal revisions, Aeolia and Belize consoles, and the PS4 Pro have no local acceptance record.
- An **already working Linux boot environment**, with a compatible launcher or loader. Preparing console access is outside this manual.
- A **USB drive of 32 GB or more**; 64 GB is recommended. Flashing erases everything on it.
- An **HDMI display** that does 1920×1080 at 60 Hz, plus a **USB keyboard and mouse**. A controller is handy for the launcher.
- A Windows, macOS or Linux **computer** to flash the USB drive.

_Turn off VRR/FreeSync in your monitor's settings. The PS4's display path has a fixed 1080p60 mode, and adaptive sync isn't supported._

## Choose a complete, matching set

For an Omarchy installation, choose the **USB image and launcher from the same release**. The release must supply the matching kernel and modules together; you do not need to assemble them yourself. Linux psX supplies the kernel for the new development path.

There is no newly qualified public Omarchy image yet. The current local development image has been built and integrity checked; the final matching launcher and PS4 boot, storage expansion and owner-setup tests are still required. The flow below describes the intended public installation experience. Before using any candidate, check its release notes for the hardware, matching launcher and USB layout it has actually been tested with.

## Download and USB sizes

Downloads and release announcements:

https://t.me/omarchy_psx

Read the download post's hardware notes before flashing, and check whether it is marked as a development candidate or a tested release.

The current local development build measures:

| Item | Size or version |
| --- | --- |
| **Download** | **2.29 GB**, compressed as `.img.xz`. |
| **Image written to the USB** | **15 GiB**, expanded by the flasher. |
| **Linux kernel** | **6.18.44**, build `6.18.44-psx-ps4-baikal2`. |

These describe the current development build; check the published release for its own sizes and hardware status.

## What flashing creates

The new partitioned image contains:

| USB partition | Contents |
| --- | --- |
| **PS4BOOT — 4 GiB FAT32** | The kernel, startup files and matching launcher package. |
| **OMARCHY-PS4 — ext4** | Omarchy, applications and personal files. |

Etcher creates both partitions automatically. The first-boot expansion code is designed to keep FAT32 at **4 GiB** and grow the ext4 partition and filesystem into **all remaining USB space**. The same image is used on supported **64 GB and 128 GB drives**; filesystem metadata and reserved space reduce the capacity available for personal files. This new growth path still needs a PS4 hardware test.

## Install

This is the intended user flow for a matched partitioned image. Use a candidate only within its recorded test scope; a public download must identify its accepted hardware and boot set.

### On your computer

1. **Download the Omarchy PS4 image.** Open the [Omarchy psX downloads channel](https://t.me/omarchy_psx) and choose a matched release for your hardware. Read its release notes, download the `.img.xz` file and check its checksum. It contains the matching Linux psX kernel and modules. Back up files on the USB and keep your existing working boot set.
2. **Install and open [balenaEtcher](https://etcher.balena.io/).** Use the version for your computer: Windows, macOS or Linux. The USB image is the same on all three.
3. **Choose the image.** Click _Flash from file_ and select the downloaded `.img.xz`. Leave it compressed: Etcher expands it and creates the two partitions during flashing.
4. **Choose the USB.** Click _Select target_ and check the drive's model and capacity carefully. **Flashing erases everything on the selected drive.**
5. **Flash and verify.** Click _Flash!_ and wait for both writing and validation to finish. Keep the drive connected until Etcher reports completion.
6. **Safely eject the USB.** It now holds the installed Omarchy system. Windows and macOS can read the FAT32 boot partition. If the computer offers to format the Linux partition, **cancel that offer**.

Flasher download:

https://etcher.balena.io/

### On your PS4

1. **Connect the prepared USB.** Connect your display, USB keyboard and mouse, then start the PS4's normal system.
2. **Set up the matching launcher once.** The FAT32 partition contains `omarchy-ps4.pkg`. Install the supplied launcher using your already established console Linux environment. Open **Omarchy PS4**, review the displayed boot-set identity, and follow that release's initial boot-file preparation steps. Preparing console access is outside this manual.
3. **Choose _Boot Omarchy_.** Keep the console and USB powered while Linux starts and prepares the drive's remaining storage.
4. **Complete first-time setup.** Choose your keyboard layout, username, password, hostname and timezone, then enter the desktop. [First Boot](03-first-boot.md) explains these screens, including the GMT timezone choices.

Keep the USB connected while using Omarchy: it holds the running system and your files. Storage expansion and account setup are the intended first-boot behaviors; repeated acceptance on this rebuilt image is still pending.

## How long does flashing take?

Allow time for writing the image and then checking it. Writing the current **15 GiB image** takes about **3 minutes at 100 MB/s** or **13–14 minutes at 20 MB/s**, followed by verification. These are estimates from the image size, not measured results for a particular drive. Download time is separate.

A compressed download expands to the full image when flashed. The release should show both sizes. A larger USB drive does not mean writing its entire capacity: the flasher writes the image, and first-boot expansion uses the remaining space.

## Older boot sets

The **historical v0.31 launcher** uses a whole-drive ext4 filesystem with no FAT32 partition. Its profile pins `6.18.44-ps4-baikal` and exact boot-file hashes, predating native Baikal Ethernet. Its [release page](https://github.com/meerzulee/omarchy-ps4/releases/tag/v0.31-baikal-beta) is a historical download, and its layout is incompatible with the new partitioned image. See [Storage](07-storage.md) and [Building from Source](13-building-from-source.md) for the distinct development paths.

## How it boots

A PS4 does not use the normal PC UEFI boot path. In this setup, a cold boot starts the console's own system, and Linux starts from the established launcher environment:

```
PS4 system → Omarchy PS4 launcher → compatible Linux loader
           → Linux kernel and initramfs → Omarchy on the USB drive
```

After the first setup, use **PS4 system → Omarchy PS4 → Boot Omarchy → desktop** with the same USB connected. The console's normal boot path remains the route back to its own system; shutdown and reboot still need repeated hardware acceptance. See [Recovery](10-recovery.md).

## Help if you're stuck

Open an issue on [GitHub](https://github.com/meerzulee/omarchy-psx/issues) with your console model, what you did and what you saw. Leave out serial numbers, MAC and IP addresses, and anything that identifies your console.

<!-- manual-navigation -->

---

[← Previous](01-welcome-to-omarchy-psx.md) · [Contents](README.md) · [Next →](03-first-boot.md)
