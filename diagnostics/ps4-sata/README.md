# PS4 SATA UART diagnostic early userspace

This is a separate diagnostic boot candidate, not an installer or a SATA fix.
It keeps the console in a minimal BusyBox initramfs and reports milestones to
the existing early UART bootconsole through `/dev/kmsg`. It never starts
systemd, the desktop, UVD applications, networking, SSH or a rescue shell.

The first comparison uses the same diagnostic kernel and initrd twice. Profile A
has `libata.force=1.00:disable`; profile B removes only that token. Keep all
instrumentation, graphics policy, USB layout and firmware identical between A
and B. This comparison locates the stall; it does not establish data integrity.

## Exact retained input

`build-initramfs` requires the 2,549,097-byte retained runtime initrd with SHA256
`cf2102f52b8b5d048538e1dd410b2c9b43ec81d2a567294d6204578aa83103f7`.
The private `EXP-20261020-006/installation/INSTALL.json` pins that input for the
running `7.2.11-psx-ps4-baikal-uvd-runtime-dev1` installation. Its `/init` is the
6,542-byte source pinned by `provenance/initramfs-import.json`, SHA256
`c0232dd418e9ea4916390f7d38a6903a5553cb8b3a5a32755b70d6a0f94ef894`.
That installation receipt is the identity basis; this preparation does not
claim a fresh measurement of the ramdisk currently loaded on the console.

From the repository root, using an explicitly supplied ordinary local file:

```sh
python3 -B diagnostics/ps4-sata/build-initramfs --base /path/to/retained/initramfs.cpio.gz --output-dir /path/to/new-local-artifact-directory
python3 -B diagnostics/ps4-sata/test-host.py -v
```

The data-only builder imports the strict `newc` parser from
`scripts/repack-ps4-initramfs`. It runs no target code, uses no container or root
privileges, and writes only a fresh output directory. It replaces `/init` data
while preserving its metadata and all 346 other entries byte-for-byte. Output
contains `initramfs.cpio.gz`, `receipt.json`, `original-init`, `diagnostic-init`
and `init.patch`. The original input has no modules; no modules are added or
loaded. Keep the whole matching module archive with the kernel handoff for
later work, without installing it for this initramfs-only test.

Existing BusyBox, firmware and other archive components retain their licenses
and notices. Generated initrds stay private and outside Git. Replacing the
diagnostic boot files with the complete preserved known-good boot set restores
the prior userspace; this tool performs neither staging nor restoration.

## Root discovery and evidence

Before any userspace block-device open, `/init` checks a candidate's canonical
USB sysfs ancestry, partition number and partition geometry. It then runs
`blkid` only against the two partitions of that USB candidate. It never performs
a global filesystem scan or selects a root by `/dev/sdX` ordering. Duplicate
matching USB roots fail closed. The retained contract is:

- Partition 1: FAT32 label `PS4BOOT`, start sector 2048, 8,388,608 sectors.
- Partition 2: ext4 label `OMARCHY-PS4`, start sector 8,390,656.

The verified USB root is mounted `ro,noload,nodev,nosuid,noexec` for an
`os-release`/directory check; its code is never run. `noload` prevents ext4
journal replay. No internal block device is opened by the diagnostic userspace.
An enabled kernel can itself issue IDENTIFY, capacity and partition reads before
`/init`; the userspace policy does not stop those automatic enumeration reads.

Look for `PS4_SATA_DIAG` records with these phases:

| Phase | Meaning |
| --- | --- |
| `init` | Kernel finished enough initialization to execute `/init`. |
| `root_scan` | USB-only root discovery started. |
| `usb_identity_begin` / `usb_identity_ok` | Exact USB identity probe boundaries. |
| `root_found` / `root_mount_begin` / `root_mount_ok` | USB mount timing. |
| `ready` | Minimal PID1 is alive; rootfs services have not started. |
| `snapshot` | Cached PCI masks, link/mode, IRQ and disk counters. |
| `heartbeat` | PID1 is making progress, every ten seconds. |
| `failed` | Userspace validation stopped; PID1 waits without automatic recovery. |

The retry limit is 60 one-second intervals, not a wall-clock guarantee for a
blocked I/O. The external UART experiment has a 180-second observation bound
from the Linux banner. The initramfs does not reset, reboot or power off at a
deadline. `observation_complete` follows twelve heartbeats after readiness and
then waits; the external observation bound still takes precedence.

## Boot arguments

Derive both profiles from the saved live command line. Keep the observed
`earlycon=uart8250,mmio32,0xC890E000,115200n8`, `console=null`, `keep_bootcon` and
`8250.nr_uarts=0`. A normal `ttyS0` is not available under that configuration.
Include in both profiles:

```text
root=LABEL=OMARCHY-PS4 rootfstype=ext4 omarchy.require_usb=1 omarchy.root_layout=partitioned-usb ro omarchy.splash=0 omarchy.sata_diag=1 ps4_sata_diag=1 amdgpu.modeset=0 amdgpu.ps4_uvd_ready=0 amdgpu.ps4_uvd_poll_state=0 amdgpu.ps4_uvd_runtime=0 printk.devkmsg=on loglevel=7 ignore_loglevel printk.time=1 log_buf_len=4M initcall_debug
```

Remove `quiet`, `splash`, `rw`, positive UVD enable flags and irrelevant
`systemd.*` parameters identically. Preserve other hardware parameters from the
observed boot. `ps4_sata_diag=1` enables the separately built kernel's bounded
instrumentation; `omarchy.sata_diag=1` is the early-userspace opt-in. Profile A
retains the exact `libata.force=1.00:disable` token. Profile B removes only it.
Do not combine NCQ, speed, DMA width or reset-policy changes into this baseline.

## Later hardware capture

Preparation performs no console, disk, boot-file or UART-session mutation. Use
the normal workspace hardware procedure before staging or launching a test:
one active experiment, a fresh console state, complete known-good rollback,
continuous UART and one bounded session per coherent hardware experiment.
The controlling agent assigns the next real experiment ID and coordinates
with other console work. On the logger host, reuse the existing collector:

```sh
./uart status
./uart session status
```

Require `READY` and resolve any existing active experiment first. The controlling
agent starts a bounded session with `./uart session start "EXP-YYYYMMDD-NNN ..."`
before consequential actions and finalizes it with `./uart session stop` after
observation and recovery. Do not open a second serial reader or restart a healthy
logger. Preserve UART through recovery; serial reconnect/restart invalidates
continuity. Stop additional actions on an oops/panic, USB-root failure or the
180-second bound. Do not automatically reboot at the first missing milestone.

Compare kernel instrumented command/completion/IRQ/DMA evidence before `init`
against the USB discovery phases after it. A stall before `init` cannot be fixed
by shortening userspace root discovery. An absence of errors or a single boot
does not qualify the HDD for writes or internal installation.

If a later normal Linux boot already has SSH, `collect-passive` prints cached
sysfs/proc topology and counters to stdout. It starts no process or service
other than itself, invokes no storage tools and opens no device nodes. Redirect
its output on the collecting host. It is not needed or installed in this
UART-only initramfs. Raw results and serial logs remain private.
