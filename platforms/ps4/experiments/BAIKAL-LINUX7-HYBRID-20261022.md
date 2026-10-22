# Baikal B1: Linux 7.2.11 Omarchy hybrid status

Date: 2026-10-22

Status: **one verified working hybrid boot**, not hardware acceptance.

Scope: PS4 Slim Baikal B1, Orbis 12.02, Linux 7.2.11, Omarchy/Arch root on
USB, internal SATA HDD used as writable test storage.

Private identifiers, key material, firmware, raw UART logs and internal
partition details are intentionally excluded from this document.

## Working configuration

| Component | Result |
| --- | --- |
| Kernel | `7.2.11-psx-ps4-baikal-sata-phy-dev1` |
| Kernel image | `5a900a…` (AHCI completion probe + PS4 audio clock handling) |
| Initramfs | `8c2d2f…` (Omarchy USB root + internal image mount) |
| Boot args | `d07342…` |
| Root | Omarchy ext4 on USB partition 2 |
| Internal storage | ext4 image in the Orbis user volume, mounted at `/mnt/internal` |
| Modules | 41 matching `7.2.11` modules |
| Desktop | Graphical target, no failed systemd units |
| Ethernet | `psx0` up, DHCP address, gateway reachable |
| Internal SATA | Toshiba 465.8 GB HDD detected and readable |
| HDMI audio | Clean at 44.1 kHz |
| UVD | Driver stack present; real playback validation still pending |

## Boot flow

The initramfs:

1. Finds the USB `OMARCHY-PS4` ext4 root and mounts it read-write.
2. Finds the internal user target by geometry, not by a fixed `sdX` name.
3. Opens the encrypted user volume using loader-injected key material. The key
   is never printed, copied into this document or committed.
4. Mounts the internal test image read-write at `/mnt/internal`.
5. Switches root into the Omarchy system.

The internal test volume is the only internal storage written. No Orbis system
partition is formatted, repaired or modified.

## Internal SATA and AHCI

The embedded AHCI controller completed the internal disk attach, partition
scan and normal I/O with the legacy unconditional 5 ms poll explicitly
disabled:

```text
ata1: ps4: completion probe enabled (5 ms), legacy poll 0 ms
```

A command-scoped completion probe runs while commands are outstanding and
services the normal `ahci_port_intr()` path. It does not complete a command
from elapsed time. The boot log showed probe recovery of internal-command
tags; the legacy timer was not responsible for those completions.

Open work remains:

- repeat cold/warm boots
- sustained read/write and flush testing
- SMART/error handling
- longer random I/O
- removal of diagnostic instrumentation after stability is established

## Audio

HDMI audio is clean at 44.1 kHz through the PipeWire graph. The working kernel
includes:

- DTO0 programming from the active pixel clock
- HDMI `DIGI_CONVERT_1` handling

Native 48 kHz still produces robotic audio and remains disabled. 44.1 kHz is a
verified workaround, not a fix for the native 48 kHz path.

## Ethernet

`psx0` is up with a DHCP address and a working default route. The PS4 Ethernet
driver does not expose speed/duplex through the usual sysfs attributes, so
operstate, carrier, address, route and RX/TX counters are the useful native
indicators.

## UVD and graphics

The Linux 7.2.11 kernel includes the PS4 UVD/amdgpu driver stack and the
Omarchy desktop starts. A real hardware-decode playback test is still needed
before calling UVD validated.

## Open work

1. Stabilize internal SATA under repeated boots and sustained writes.
2. Validate UVD with actual video playback and GPU/UVD accounting.
3. WiFi/Bluetooth: MT7668 firmware probe still times out; Ethernet remains the
   working network path.
4. Desktop polish: suspend/resume, fan/thermal behavior, controller/Bluetooth
   input and native 48 kHz audio.
5. Internal-root installation instead of USB-root hybrid boot. The loader still
   requires the USB boot set.
6. Blu-ray:
   - No optical device is currently detected.
   - The second Baikal SATA controller reports zero implemented ports.
   - The drive connection/power path must be identified before adding optical
     kernel support.
   - Data Blu-ray/UDF reading is a separate goal from commercial movie
     playback, which involves AACS/BD+ and region handling.

## What not to claim

- One successful boot is evidence, not hardware acceptance.
- UVD is present but not yet decode-validated.
- Native 48 kHz audio is not fixed.
- Blu-ray is not detected and is not supported yet.
- The internal-root path is not yet independent of the USB loader.

## Publication boundary

This note excludes:

- loader or disk key material
- raw UART captures
- private firmware files
- device serial numbers and USB identifiers
- private LAN addresses
- Orbis system-partition contents
