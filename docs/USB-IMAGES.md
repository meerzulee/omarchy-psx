# Flashable PS4 USB images

The new image path creates one compressed `.img.xz` containing a DOS/MBR
partition table, a 4 GiB FAT32 volume labelled `PS4BOOT`, and an ext4 volume
labelled `OMARCHY-PS4` occupying the rest of the initial image. Etcher can write
the same file on Windows, macOS and Linux. End users do not partition or format
the drive themselves.

This is a development candidate format, not an accepted public release. Keep
generated images, firmware and assembled boot archives out of Git. Creating an
image does not flash a USB or operate a console.

## Build inputs

Use the macOS OrbStack build host. The builder uses a native tools container
and regular files only; it does not require a Linux VM named `ubuntu`, a
privileged container, loop devices or mounted filesystems.

- An owner-ready rootfs built with provisioning `4.0.0-24` and its manifest.
- A complete boot directory with `release.json` and all four matching files.
- An explicit boot-profile record pinning the kernel and whole module tree.
- The matching launcher package and an explicitly expected SHA-256 digest.
- A distinct image release ID. Historical boot profiles and manifests stay
  unchanged; a new kernel requires its own measured profile.

If upstream package repositories have moved, `build-package-snapshot` can use
`--base-snapshot DIRECTORY` with a previously verified complete snapshot and
the newly built project packages. It checks the base hashes, upstream commit
and Arch snapshot date, disables network resolution, and records the base
fingerprint. Existing package archives are not modified.

For example, substitute actual verified paths and identities:

```sh
python3 platforms/ps4/scripts/build-partitioned-usb-image \
  --rootfs output/rootfs/candidate.tar.zst \
  --boot-set output/boot-set/candidate \
  --boot-profile output/boot-set/candidate/profile.env \
  --launcher output/launcher/candidate.pkg \
  --launcher-sha256 EXPECTED_64_CHARACTER_SHA256 \
  --release-id omarchy-psx-ps4-image-dev1 \
  --output output/usb-image/omarchy-psx-ps4-image-dev1.img.xz \
  --plan
```

`--plan` verifies the inputs and measures the archive without building or
writing storage. Remove it to build. An old rootfs may be measured for sizing,
but building refuses it until its growth scripts match the current package.

The completed build writes the image, a `.manifest` with sizes and checksums,
and a `.json` receipt with geometry, input identities, filesystem use and tool
versions. `--keep-raw` also retains the uncompressed `.img`. Existing outputs
are never overwritten.

An explicitly separate kernel experiment may use a schema-1 `usb-boot-set`
manifest with `boot_set.storage=usb-fat`, a profile recording
`launcher_base_release`, and `--allow-development-usb-override`. It must record
the exact base launcher's SHA-256 and `release_eligible=false`. This describes
the loader's USB-first development path; it does not claim the new kernel is
embedded in that older launcher. Such candidates cannot be promoted as a
matched public release without the corresponding launcher work and evidence.

## Size and verification

The default `--image-size-gib auto` rounds the measured payload, a metadata
allowance and at least 2 GiB of free root space to a whole GiB. A fixed size can
be requested, for example `--image-size-gib 16`. The FAT partition is included
in that total. The builder checks actual free ext4 space after construction.
The current boot contract requires 4 GiB FAT32; a 2 GiB variant needs a separate
initramfs/profile change and validation.

The compressed download size is measured after xz compression. The raw size is
the number of bytes written by a flasher. Neither is the final USB capacity:
on a larger supported drive, first boot extends partition 2 and then ext4.

Build verification checks both filesystems, both assembled partition byte
ranges, the complete MBR layout, and the full decompressed image against its
raw SHA-256. Ownership, hard links, ACLs and extended attributes are copied
from the extracted Linux root using `mke2fs -d`.

## First boot

The existing partitioned initramfs accepts this 4 GiB boot geometry without
changing its frozen source or hash. A schema-2 image-layout record authorizes
the current provisioning package to enlarge partition 2. It verifies the
running USB root, both partition identities and geometry, validates the MBR,
backs up its original sector, and changes only partition 2's length. The kernel
must report the enlarged size before ext4 is grown and owner setup proceeds.

An interrupted attempt remains pending. If the MBR was already extended, the
next attempt repeats the kernel size update and finishes filesystem expansion.
Historical schema-1 partitioned installations continue to require their exact
full-device geometry and do not authorize partition-table changes.

Synthetic host/container tests do not qualify a PS4 boot. The new image needs
bounded UART evidence for first-boot growth and owner setup, followed by the
active plan's repeated boot criteria before release promotion.
