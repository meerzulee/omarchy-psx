> Imported PS4 history from `omarchy-ps4` on 2026-10-17. Paths and milestones below describe the original PS4 implementation and artifacts; they do not qualify a new Linux psX build or PS5. Use the [current migration guide](../../../docs/MIGRATION.md) for the active repository layout. Private network/host details are redacted.

# Private partitioned USB development profile

This profile is an unaccepted hardware experiment. The published v0.31
launcher and whole-device image contract are unchanged. Use private v0.32
only with its matching boot set and rootfs.

## Layout

The host installer creates a DOS/MBR table on an explicitly identified USB
disk with 512-byte logical sectors:

| Partition | Start sector | Size | Format | Label |
| --- | ---: | --- | --- | --- |
| 1, active, type `0c` | 2048 | 4 GiB | FAT32 | `PS4BOOT` |
| 2, type `83` | 8390656 | remaining disk | ext4 | `OMARCHY-PS4` |

The FAT volume holds the matching kernel, initramfs, boot arguments, VRAM file
and private launcher package. The pinned loader can select USB boot files
before internal files, so all four USB files must match the packaged boot set.
Do not mix files from different profiles or attach another boot USB.

The root filesystem mounts FAT at `/boot` read-only. Provisioning verifies
USB ancestry, both partitions, geometry, labels and ext4 capacity before
allowing owner setup. It does not resize partitions or filesystems in this
profile. The first-owner password is entered on the console; images contain
no default human account or password. An optional development public key may
be staged for key-only SSH; keep its private key on the development host.

Ext4 is the current root filesystem contract. Btrfs would require a separate
initramfs, mount, provisioning and recovery design, plus hardware acceptance.

## Build on macOS ARM64

Use the existing OrbStack environment and pinned source inputs. The kernel
and module output must be the accepted `6.18.44-ps4-baikal` pair.

```sh
scripts/build-omarchy-packages --output output/packages-partitioned
scripts/build-package-snapshot \
  --package-source output/packages-partitioned \
  --output output/snapshot-partitioned
scripts/build-gift-rootfs --layout partitioned-usb \
  --snapshot output/snapshot-partitioned \
  --output output/omarchy-ps4-partitioned-rootfs.tar.zst
fpkg/tools/repack-initramfs-init
fpkg/tools/build-ui-prototype --private-kernel-manager-partitioned
```

The data-only repacker requires the accepted base initramfs digest. It changes
only `/init`, preserving every other archive entry, including metadata. If
`/init` changes, review and update its resulting size/digest in the new private
profile's staging, compiled artifact table and manifest before building.
The v0.31 pins must stay intact.

The new manifest is explicitly release-ineligible, even when its placeholder
USB image metadata is later filled. Building and extracting the package does
not establish hardware acceptance.

## Install on Linux x86-64

Run the following with actual paths and the USB's recorded stable identity.
The default command checks inputs and shows a preview without disk writes.

```sh
scripts/install-partitioned-usb-linux \
  --device /dev/disk/by-id/usb-MODEL_SERIAL-0:0 --serial SERIAL \
  --rootfs /path/to/omarchy-ps4-partitioned-rootfs.tar.zst \
  --boot-set /path/to/internal-boot-partitioned \
  --launcher /path/to/private-v0.32.pkg
```

After explicit approval of the identified disk, use `sudo`, add `--apply`,
and enter the exact stable-path WIPE confirmation. Formatting destroys all
existing USB data. The installer checks host-root ancestry, active swap and
block holders, ensures its inputs are outside the target, verifies hashes and
partition geometry, installs the root and FAT files, checks both filesystems
and leaves both partitions unmounted. A failure stops the operation; preserve
its output before deciding whether a retry is appropriate.

The installer temporarily sets `UDISKS_IGNORE=1` for the exact USB serial so
desktop automounters cannot race formatting or copying. It checks that this
rule applied to every target node. Cleanup removes the temporary rule without
triggering another mount; normal automount resumes after unplug/replug. Other
devices and desktop services are unchanged.

If an attempt stopped after formatting but before extraction, a reviewed
resume can use the existing filesystems without partitioning or formatting:

```sh
sudo scripts/install-partitioned-usb-linux \
  --device /dev/disk/by-id/usb-MODEL_SERIAL-0:0 --serial SERIAL \
  --rootfs /path/to/omarchy-ps4-partitioned-rootfs.tar.zst \
  --boot-set /path/to/internal-boot-partitioned \
  --launcher /path/to/private-v0.32.pkg \
  --resume --expect-root-uuid RECORDED-ROOT-UUID \
  --expect-boot-uuid RECORDED-BOOT-UUID --apply
```

Resume requires the recorded UUIDs, original exact geometry, labels and types,
clean filesystem checks and empty FAT/ext4 filesystems. An empty ext4
`lost+found` directory is allowed. Existing files, recovered data and partial
installations are refused. Use a new bounded attempt only after recording why
the earlier one stopped and what changed.

## First hardware experiment

Keep continuous UART running. Use one bounded experiment for installation,
installing the matching private package in Orbis, launching once, and observing
owner setup and the desktop. Stop on UART loss, panic, root-layout errors or
the declared timeout. Return to Orbis through the recorded recovery path;
never initialize or repair the PS4's internal storage.

The previous v0.31 launcher requires its old whole-device root layout for
rollback. This new root is not a compatible substitute. The launcher's
transaction manager retains the previous internal boot set, but FAT files
can override it; remove the new USB before using an independent rollback set.

Built-in Baikal Ethernet is still unavailable in this kernel. This profile
does not install or enable an experimental MTS/sky2 driver. A successful
desktop boot and a working wired network are separate evidence requirements.

## Explicit kernel development override

The optional kernel target `6.18-baikal-mts` has a separate, private USB
override procedure for EXP-20261017-015. It retains this profile's initramfs,
boot arguments and VRAM file byte-for-byte, replaces only the FAT-root
kernel, and installs the entire matching module tree beside the old one.
This deliberately differs from the package's recorded kernel; preserve the
original `release.json`, launcher and console-internal boot set, and record
the candidate separately. Do not use installation/resume or package staging
tools to update an already populated USB.

Before writing, back up all four boot files and `release.json` off-device
and into a unique FAT recovery directory. Verify the identified USB, hashes
and read-only remount. The loader's independent USB-first file search makes
a complete four-file set mandatory. Restoring all four original files on an
unmounted USB is the rollback if the candidate cannot boot. Detailed driver
limits and the test sequence live in the sibling kernel's
`docs/BAIKAL-MTS-KERNEL-CANDIDATE.md`. EXP-20261017-015 passed the first bounded
candidate boot/modem-network test; the curated result is in
`experiments/SESSIONS.md`. This exception does not change the normal profile
or establish continuous Ethernet or release qualification.

The follow-up EXP016 uses target `6.18-baikal-mts2` and the same override
contract. The mts1 boot set is independently backed up on both development
hosts; both older module trees remain installed. The new kernel and complete
module tree were verified, and modem DHCP/IPv4 transport plus three NM profile
reconnects passed. The separate activation package0.1.1 fixes the observed
first-UP handoff gap and is installed for future boots. Its automatic startup
still needs a later boot. See [the Ethernet handoff](BAIKAL-ETHERNET.md) and
EXP016 for duration, cable and administrative-test qualifications. The
standard USB profile and original package metadata remain unchanged.
