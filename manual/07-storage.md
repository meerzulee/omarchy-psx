# Storage

The Linux system and personal files live on the USB drive. The new image uses a FAT32 boot partition and a separate ext4 system partition. Linux access to the console's internal SATA disk is disabled in normal profiles.

## The USB drive

The partitioned image creates a **4 GiB FAT32 partition labelled `PS4BOOT`** for boot files and the launcher package, followed by **ext4 labelled `OMARCHY-PS4`** for Linux and personal files. Linux finds its system by label rather than assuming a device name like `/dev/sda`.

The new first-boot source checks the running USB root, labels and partition geometry, then extends only the system partition and its ext4 filesystem to use the remaining drive. It keeps the boot partition and the system partition's starting point unchanged. A failed check stops setup. This path has synthetic host/container tests; PS4 hardware acceptance is still pending.

Windows and macOS can read `PS4BOOT`, but cannot normally read the ext4 system partition. Cancel any offer to format the Linux partition.

## The developer layout

The earlier private developer installer creates the same 4 GiB FAT32 boot partition followed by ext4, filling the selected drive during installation. It does not authorize automatic partition growth. The FAT partition holds the kernel, initramfs, boot arguments and VRAM setting, which is how development kernels get tested without rebuilding the launcher. Linux mounts it read-only at `/boot`.

Two things to know about it:

- The PS4 Linux loader looks for boot files on USB before the launcher's own copies. All four files on the FAT partition have to belong together, and you shouldn't attach a second boot drive.
- It isn't interchangeable with the historical whole-drive layout. The v0.31 launcher expects ext4 across the entire drive, with no partition table.

This layout hasn't passed hardware acceptance. Building and installing it is covered in [the partitioned USB guide](../platforms/ps4/docs/USB-PARTITIONED-DEVELOPMENT.md).

The new flashable image and its growth contract are described in [USB images](../docs/USB-IMAGES.md). Historical whole-device images grow only their ext4 filesystem and retain their own boot profile.

## The PS4's internal drive

Left alone, Linux sees the internal SATA disk, but reading it timed out and failed on our test console, and probing it with desktop disk tools caused more I/O errors. So:

- The normal boot profiles tell Linux to switch the internal disk off (`libata.force=1.00:disable`). The separate debug profile leaves it on.
- UDisks, automounters and disk utilities are left out of the image.
- The supported development workflow uses external Linux storage. Formatting, mounting or writing the console's system partitions is outside that workflow, and internal Linux installation is unsupported.

The launcher can retain an internal boot set in `/data/linux/boot`, along with its previous set. With the partitioned USB present, the loader searches its FAT boot files first. All USB boot files must belong to one matching set. The launcher does not write the Omarchy USB.

## Encryption

The USB drive isn't encrypted today. An "Encrypt USB" conversion to LUKS2 has worked on disposable images in a virtual machine, but unlocking at boot, interruption recovery and performance haven't been tested on a PS4, so it's not offered yet. Until then, anyone holding the drive can read it. Details are in [the LUKS notes](../platforms/ps4/docs/LUKS-POST-INSTALL.md).

## Backups

There are no system snapshots on the PS4 (see [What's Different on PS4](05-whats-different-on-ps4.md#no-system-snapshots)), and reflashing the drive erases it. Copy anything you care about to another machine.

<!-- manual-navigation -->

---

[← Previous](06-networking.md) · [Contents](README.md) · [Next →](08-kernels-and-firmware.md)
