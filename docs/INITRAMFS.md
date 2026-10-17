# Omarchy PS4 initramfs

The existing Omarchy PS4 boot set uses a custom **BusyBox-based x86-64
initramfs**: gzip-compressed `cpio newc`, with static BusyBox **1.28.3**
(build timestamp `2018-04-22 21:29:51 UTC`) and our `/init` script.
The archive is named `initramfs.cpio.gz`.

The PS4 loader passes it to Linux. `/init` mounts early virtual filesystems,
finds and validates the external USB root, optionally starts the Omarchy
framebuffer splash, then runs `switch_root` into `/sbin/init` on the real
root filesystem. It retains the existing `omarchy.*` boot parameters.

## Exact existing profile

The partitioned profile uses a 4 GiB FAT32 `PS4BOOT` partition followed by an
ext4 `OMARCHY-PS4` root. Geometry and USB ancestry checks are part of `/init`.
The optional profile is versioned in
[`boot-profiles/ps4-baikal-partitioned-omarchy.example.txt`](../boot-profiles/ps4-baikal-partitioned-omarchy.example.txt).
Other layouts need their own reviewed initramfs/profile.

| Input/output | Bytes | SHA256 |
| --- | ---: | --- |
| Existing whole-device base archive | 1,686,508 | `824530e22392376d5fc27994a9ccff97f0442b7a41681155f46e183f892365ae` |
| Our partitioned `/init` source | 6,542 | `c0232dd418e9ea4916390f7d38a6903a5553cb8b3a5a32755b70d6a0f94ef894` |
| Existing partitioned initramfs | 1,686,082 | `31e793671aca8b595e130fa9d1ba5a93f0d777ee45843eb1aa3925294b0dc353` |

The machine-readable contract and inspected firmware inventory are in
[`manifests/ps4-initramfs.json`](../manifests/ps4-initramfs.json).
Source origin, working-tree state and adaptations are in
[`provenance/initramfs-import.json`](../provenance/initramfs-import.json).
The selected original sources included pending/untracked work; their file
hashes identify the import, rather than claiming those bytes were already in
the old repository's recorded HEAD.

## Generate the existing initramfs on Mac or Linux

Python **3.10+** is sufficient on macOS ARM64 and Linux x86-64. This data-only
repacker needs no container, root privileges or target-code execution.

Supply a local copy of the **exact external base archive** identified above.
In the old workspace it was staged at
`omarchy-ps4/fpkg/vendor/internal-boot/initramfs.cpio.gz`. The source handoff
does not bundle or automatically fetch that archive. An existing partitioned
archive with hash `31e793…` is the result, not the required `824530…` base.

From the `omarchy-psx` checkout:

```sh
python3 scripts/repack-ps4-initramfs \
  --base /path/to/accepted-base/initramfs.cpio.gz
```

Output:

```text
output/initramfs/ps4-baikal-partitioned/initramfs.cpio.gz
```

The tool checks the base size/SHA256, reads the versioned
`rootfs/initramfs/init`, replaces only the `/init` data/size and preserves all
other entries and their metadata. It prints the input/source/output hashes.
The migrated source reproduced the existing `31e793…` result byte-for-byte
on the migration host. This preserves the existing userspace/firmware input;
it does not compile BusyBox or reconstruct all firmware from source.

An existing output is refused. Use `--output /path/to/new-candidate.cpio.gz`
for another result. `--init` explicitly selects another source; changes create
a new candidate with a new identity and require their own validation.
Compression-library differences can also change gzip bytes; compare the
reported digest rather than assuming identical output on every host.

## Reconstruct from the public historical seed

The complete assembler and its source are now under `platforms/ps4/`. A fresh
clone can acquire the original seed from an immutable public GitHub path:

```sh
./scripts/fetch-ps4-initramfs-seed
./scripts/sync-omarchy-upstream
cd platforms/ps4
./scripts/build-initramfs-tools
./scripts/build-xfce-initramfs
```

The last two commands use the existing Mac/OrbStack build path. The resulting
candidate is `platforms/ps4/output/xfce-baseline/initramfs.cpio.gz`. This uses
the migrated `/init`, `install-rootfs`, splash source and userspace tools. The
seed downloader verifies **4,082,183 bytes**, SHA256
`245df0d98133fd14efc09ab2c5a309b065f9668d5a07b0887bee4fcf1237f113`, against
[`ps4-initramfs-seed.json`](../manifests/ps4-initramfs-seed.json); an explicit
`PS4_SOURCE_INITRAMFS` override is subject to that seed contract too.

The original seed is **not** the `824530…` generated base or `31e793…` accepted
historical result. Historical Alpine/APK tool versions were not fully pinned;
reconstruction creates a new candidate unless its actual digest matches a
recorded accepted artifact. The exact historical repacker above deliberately
refuses arbitrary bases. No old sibling source checkout or private source
archive is needed to run the full source reconstruction path.

## Kernel and firmware boundary

This initramfs has **336 entries and no kernel module tree**. Matching kernel
modules, including `psx_mts_net`, belong in the real root's module tree and
use the separate reviewed post-boot activation path.

The inspected archive contains ten Liverpool AMDGPU firmware files and the
1080p EDID. It contains **no MT7668 Wi-Fi firmware**. The historical private
kernel embedded MT7668 payloads; the new Linux psX target deliberately embeds
none. Early Wi-Fi with that new kernel therefore needs a separate firmware
integration check. This repacker adds no firmware and does not establish a
compatible fallback Wi-Fi path.

No BusyBox binary, firmware blob, seed/initramfs archive or PKG is committed
or published by this source migration. Those components retain their own
source/provenance and licensing requirements. The local generated result is
ignored by Git.

Linux psX remains independent of this Omarchy root layout and initramfs.
Other distributions supply their own compatible early userspace. The unchanged
existing initramfs has historical boot evidence; pairing it with
`6.18.44-psx-ps4-baikal1` is **not boot-tested**. Source/repack tests do not
replace the bounded UART/hardware procedure before deployment.

## Host checks

Default tests use synthetic archives and never access devices or firmware:

```sh
python3 scripts/check-provenance
python3 -B -m unittest discover -s tests -v
```

To include the optional read-only preservation test against an explicitly
supplied local base:

```sh
OMARCHY_INITRAMFS_TEST_BASE=/path/to/accepted-base/initramfs.cpio.gz \
  python3 -B -m unittest discover -s tests -v
```
