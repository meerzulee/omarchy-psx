# Using Linux psX with Omarchy

Linux psX is a distribution-independent kernel project. Omarchy psX owns the
optional distribution integration described here. This repository currently
contains handoff documentation, a legacy boot-profile example and a manually
invoked NetworkManager adapter. It does **not** contain a complete migrated
Omarchy distribution, a root filesystem, an initramfs, an OS installer or PKG.

The kernel target is `6.18-ps4-baikal`, release
`6.18.44-psx-ps4-baikal1`, based on upstream Linux v6.18.44 commit
`1efe5d048a391de3ead2804b2e7f86376c356cc5`. Its 55 platform patches preserve
the existing PS4 Baikal work. The new names/build and this integration have
**not** acquired hardware acceptance through migration. PS5 is planned.

## Pinned source handoff: Mac ARM64 and Linux x86-64

Clone Omarchy psX on the development computer, then obtain the sibling kernel
from the full commit in `manifests/kernel-source.json`:

```sh
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
python3 scripts/setup-kernel-workspace
```

The script creates a missing sibling `linux-psx` at the immutable revision. It
refuses a different/dirty existing checkout and never resets, rebases, merges
or discards local work. The published migration pin is
`b9bcf7234dff601ce41e141ca1403ea0a4525c1a`. For an explicitly selected different
development commit, use `--revision` with its full 40-character SHA and record
that choice. Missing or non-immutable pins fail closed. Do not treat moving
`main` or a private source archive as a reproducible pin.

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
layout. Additional source/upstream/acceptance metadata does not change the
activation guards.

Verify published artifact checksums and the kernel/archive hashes in that
metadata **before** any installation. The activation adapter later checks the
running release/configuration and installed/loaded module; it does not hash
the live kernel image in memory.

Install the **whole** matching module tree beside the old release. Preserve
the old module tree and a complete boot-set backup on another machine. Never
overwrite an existing release directory or install only `psx_mts_net.ko`.
Inspect a verified archive before extracting it; it must contain only the new
`lib/modules/<release>/` tree and its parents. On Omarchy's merged-/usr layout:

```sh
release=6.18.44-psx-ps4-baikal1
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
That initramfs is not supplied here. Check its compatibility and required
firmware before reuse. A kernel configured without embedded firmware may
need display EDID and built-in Wi-Fi firmware inside the initramfs, before
the root filesystem is available. Firmware licensing remains separate.

Place the matching `bzImage`, compatible `initramfs.cpio.gz` and your selected
`bootargs.txt`/`vram.txt` on external boot media using the reviewed existing
procedure. No new launcher PKG or internal boot-file replacement is implied.
For another distribution, use Linux psX's generic boot documentation instead
of this Omarchy profile. Back up first and retain a way to boot the old pair.

## Optional experimental Ethernet activation

The kernel and its driver have no NetworkManager dependency. This repository's
MIT adapter is specifically for the optional Omarchy/NetworkManager layer;
other network managers need an equivalent reviewed first-publication path.
It requires Python 3, kmod, iproute2 and NetworkManager, resolving programs
only through root-controlled system directories. It supports canonical `/lib`
and merged-/usr module layouts.

After an authorized fresh boot into the new kernel, install the reviewed
adapter and matching generic metadata in root-owned locations:

```sh
sudo install -Dm755 scripts/activate-baikal-ethernet /usr/local/sbin/activate-baikal-ethernet
sudo install -Dm600 artifacts.json /root/omarchy-psx/artifacts.json
sudo /usr/local/sbin/activate-baikal-ethernet --activate \
  --artifacts /root/omarchy-psx/artifacts.json
```

It does not enable startup. It uses one attempt marker per boot, verifies
kernel/module/PCI/glue/DMA identity, blocks NM ownership before arming, creates
only `PSXEthernet.nmconnection`, performs exactly one explicit UP and validates
positive publication before NM handoff. The owned profile uses DHCPv4, metric
100, MTU 1500, IPv6 disabled and the inherited permanent MAC. A competing
automatic Ethernet profile causes refusal; unrelated profiles are never edited.
Carrier and DHCP remain asynchronous, including unplugged activation.

On error or uncertain completion, stop and preserve UART/report evidence. Do
not retry, unload, reset, clear overrides, rearm or load an old experiment
module. Published code, DMA, mappings and PCI references remain retained until
power-off; stop acknowledgement does not prove drain. Ordinary healthy admin
down/up preserves the same generation; a fatal terminal fault needs a fresh
power-off/boot. Keep recovery Wi-Fi or a local console available.

```sh
uname -r
nmcli device status
ip -4 route get 1.1.1.1
ip -s link show dev psx0
sudo cat /sys/module/psx_mts_net/parameters/report
curl --interface psx0 --noproxy '*' --fail --max-time 30 https://example.com/ -o /dev/null
ip -s link show dev psx0
```

A preferred wired route names `psx0`; the interface-bound HTTPS request plus
advancing TX/RX counters provides traffic evidence. An address/carrier alone
does not. Source review, successful compilation and old MTS2 observations do
not establish acceptance of this new build or adapter. Record hashes, UART
continuity, DHCP/routing, independent bidirectional transfer hashes, traffic
beyond 900 seconds, admin cycles, cable recovery and unchanged DMA generation.
Redact private identifiers/logs before public reporting.

Run synthetic host tests without touching devices:

```sh
python3 -B -m unittest discover -s tests -v
```
