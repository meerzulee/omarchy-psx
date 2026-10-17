# Using Linux psX with Omarchy

Linux psX is a distribution-independent kernel project. Omarchy psX owns the
distribution implementation and optional integration described here. The full
existing PS4 source now lives under `platforms/ps4/`: packages, rootfs and
initramfs builders, launcher/FPKG, installation/recovery tools, tests and curated
research. Root tools provide source handoff and initramfs preservation.
Generated root filesystems, initramfs archives and PKGs remain external. See
[MIGRATION.md](MIGRATION.md) for the source map and historical boot-profile
boundaries.

The kernel target is `6.18-ps4-baikal`, release
`6.18.44-psx-ps4-baikal2`, based on upstream Linux v6.18.44 commit
`1efe5d048a391de3ead2804b2e7f86376c356cc5`. Its 56 platform patches preserve
the existing PS4 Baikal work and add native Ethernet autoload. The CI build
has **not** been booted; the same patch set passed two boots as a local
build. Neither is hardware acceptance. PS5 is planned.

## Pinned source handoff: Mac ARM64 and Linux x86-64

Clone Omarchy psX on the development computer, then obtain the sibling kernel
from the full commit in `manifests/kernel-source.json`:

```sh
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
./scripts/setup-workspace
```

The script creates missing sibling `linux-psx` and `ps4-uart` sources at the
full commits in `manifests/development-sources.json`. It preserves existing
checkouts whose history contains the pins, including local edits, and never
resets, rebases, merges or discards work. `--check` is offline and read-only.
The kernel pin also appears in `manifests/kernel-source.json`.

For an exact separate kernel snapshot, the older `setup-kernel-workspace`
helper requires an unchanged checkout at the pin. Its `--revision` option
accepts a full 40-character SHA for an explicitly selected different snapshot;
record that choice. Missing or moving pins are refused. The complete host
setup is in [DEVELOPMENT-HOSTS.md](DEVELOPMENT-HOSTS.md).

On **macOS ARM64**, install/start OrbStack, verify its context and run the
kernel repository's x86-64 cross-builder:

```sh
orb status                    # Running
docker context show           # orbstack
cd ../linux-psx
./scripts/build-kernel-orbstack -t 6.18-ps4-baikal
```

Do not run the Linux kernel build directly on Darwin or start Docker Desktop,
Colima, Lima or another VM/container runtime for this workflow.

On **Linux x86-64** (including Arch/Omarchy), install the native prerequisites
documented by Linux psX and build natively:

```sh
cd ../linux-psx
make TARGET=6.18-ps4-baikal
```

No container is required for native Linux compilation. The kernel builder
fetches and checks its recorded upstream Linux source; do not copy a generated
Mac build tree, virtual environment or UART runtime state to the new device.
Expected outputs live in `output/6.18-ps4-baikal/`; consult Linux psX's own
README/build records for the final tooling and artifact contract:

https://github.com/meerzulee/linux-psx

No new Linux psX binary release is promised by this migration. Source builds
and CI artifacts must retain their source/config/compiler identities. Earlier
`linux-ps4` releases are historical references with different release strings;
they are not matching binaries for this target.

## Kernel artifacts and matching modules

Linux psX `artifacts.json` schema 1 records `target`, `platform`,
`kernel_release`, `kernel_config_sha256`, `kernel_sha256`,
`embedded_firmware`, `modules_archive.{path,sha256}` and
`module.{name,path,sha256,build_note_hex}`. Module paths are archive-relative
`lib/modules/<release>/...`; they do not encode a distribution's local `/usr`
layout. Consumers ignore additional source/upstream/acceptance metadata.

Verify published artifact checksums and the kernel/archive hashes in that
metadata **before** any installation.

Install the **whole** matching module tree beside the old release. Preserve
the old module tree and a complete boot-set backup on another machine. Never
overwrite an existing release directory or install only `psx_mts_net.ko`.
Inspect a verified archive before extracting it; it must contain only the new
`lib/modules/<release>/` tree and its parents. On Omarchy's merged-/usr layout:

```sh
release=6.18.44-psx-ps4-baikal2
tar --zstd -tf "modules-$release.tar.zst"
if [ -e "/usr/lib/modules/$release" ] || [ -L "/usr/lib/modules/$release" ]; then
  printf 'STOP: preserve the existing release and inspect it.\n' >&2
else
  sudo tar --zstd --extract --file "modules-$release.tar.zst" --directory / --no-same-owner &&
    sudo depmod -a "$release"
fi
```

These commands assume the running root filesystem is the intended external
PS4 Linux system. They do not select a disk, format storage, install an image
or alter console-internal files. An offline root requires its own explicit
mount/depmod-root procedure; do not run these against the development host.

## Optional existing Omarchy USB boot profile

`boot-profiles/ps4-baikal-partitioned-omarchy.example.txt` preserves the
previously used Omarchy command line: FAT boot files, ext4 root labelled
`OMARCHY-PS4`, existing partitioned-USB Omarchy initramfs, and VRAM setting
`1024`. It keeps internal SATA disabled. It is an **example for that existing
layout**, not a generic Linux boot requirement or validation of the new build.

Use your established compatible PS4 loader, initramfs and root filesystem.
The old setup used ps4-linux-loader v25 and a 1024 MB loader; its initramfs SHA256
was `31e793671aca8b595e130fa9d1ba5a93f0d777ee45843eb1aa3925294b0dc353`.
The binary archive is external; [INITRAMFS.md](INITRAMFS.md) supplies the exact
BusyBox identity, source/repacker, base hash and Mac/Linux generation command.
Check its compatibility and required
firmware before reuse. A kernel configured without embedded firmware may
need display EDID and built-in Wi-Fi firmware inside the initramfs, before
the root filesystem is available. Firmware licensing remains separate.

Place the matching `bzImage`, compatible `initramfs.cpio.gz` and your selected
`bootargs.txt`/`vram.txt` on external boot media using the reviewed existing
procedure. No new launcher PKG or internal boot-file replacement is implied.
For another distribution, use Linux psX's generic boot documentation instead
of this Omarchy profile. Back up first and retain a way to boot the old pair.

## Ethernet

From `6.18.44-psx-ps4-baikal2` the Baikal Ethernet driver starts by itself. udev
loads `psx_mts_net` from its PCI alias, the driver registers `psx0`, and the
network manager's first open publishes the interface. On Omarchy,
NetworkManager's default wired profile then handles carrier and DHCP, with the
cable connected at boot or plugged in later. No Omarchy package, service or
activation step is involved; the earlier MTS2 package and manual adapter were
removed. Keep recovery Wi-Fi or a local console available.

To keep Ethernet off for a boot, add `psx_mts_net.autoarm=0` (the module loads
but the first open waits for an explicit `allow_open` write) or
`modprobe.blacklist=psx_mts_net` to the kernel command line. Do not unload,
reset or rearm a published instance: its DMA, mappings and PCI references stay
retained until power-off, and a terminal fault needs a fresh boot.

Check a boot with:

```sh
uname -r
nmcli device status
ip -4 route get 1.1.1.1
ip -s link show dev psx0
sudo cat /sys/module/psx_mts_net/parameters/report
curl --interface psx0 --noproxy '*' --fail --max-time 30 https://example.com/ -o /dev/null
ip -s link show dev psx0
```

A wired route through `psx0`, the interface-bound HTTPS request and advancing
TX/RX counters show traffic; an address or carrier alone does not. The same
patch set passed two boots on one console (EXP-20261017-019 and -020 in the
PS4 experiment ledger). The CI-built release, `ip link` down/up under
NetworkManager, other network managers and other consoles are untested. Driver
details:
[Linux psX `docs/ETHERNET.md`](https://github.com/meerzulee/linux-psx/blob/master/docs/ETHERNET.md).
Redact private identifiers/logs before public reporting.

## Host tests

Run synthetic host tests without touching devices:

```sh
python3 -B -m unittest discover -s tests -v
```
