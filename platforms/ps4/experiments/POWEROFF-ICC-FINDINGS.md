# Baikal power-off over ICC: findings

Recorded 2026-10-22. Reworded for publication 2026-11-10.

> This is an analysis note, not a hardware experiment. It adds no entry to
> `SESSIONS.md` and claims no hardware acceptance.

What this note says about the console's own software comes from studying how its
12.02 system software powers off, so that Linux can drive the same hardware. It
is written in our own words and reproduces no Sony code, symbols or strings.

## Question

Why did Linux `poweroff` hang on a Baikal PS4 while `reboot` returned to the
console's own OS?

## Result

The message Linux sends was already correct. The difference is how the last
command completes.

- The console's own software sends the final power command, service 4 minor 1,
  and does not wait for a reply.
- Linux sent the same command through `bpcie_icc_cmd()`, which waits up to 15
  seconds for a reply. If none comes, `icc_shutdown()` runs `mdelay(3000)` and
  `pm_power_off` returns, so the kernel reaches its halt loop with the power
  still on. This was a hypothesis when written. No UART log of the failing
  power-off was attached to the analysis.
- An ordinary `reboot` never reaches this code. It takes the x86 reset path and
  lands back in the console's boot flow, which says nothing about whether the
  Baikal ICC reboot command works. The Baikal `icc_reboot` is `static` and
  unused, and `machine_ops.emergency_restart` points at the Aeolia one. A
  Linux-to-Linux reboot is a separate boot-chain or kexec problem.

An earlier Linux shutdown reached `reboot: Power down` cleanly
(`EXP-20260810-001-A47`). That result shows the hardware can get there. It is
not acceptance for the 7.2 Baikal kernel.

## Later result

`platforms/ps4/patches/7.2-ps4-baikal/0200-ps4-drivers/0001-ps4-bpcie-icc-power-off-before-acpi.patch`
in `linux-psx` (PR #4, by suds-mcduff, 2026-10-31) found a blocker that comes
first. Linux ran the ACPI S5 handler before the ICC power-off, and on the tested
console that handler neither powered off nor returned, so `icc_shutdown()` was
never reached. The patch registers the ICC power-off ahead of ACPI and sends the
request without waiting for a reply. Its author reports that a PS4 Slim
CUH-2002A then powered off with a clean UART ending. Treat the 15-second wait
above as a second problem behind that one, and qualify each kernel on hardware.

## Order of the power requests

The console's own software uses service 4 in this order.

| When | Request | Waits for a reply |
|---|---|---|
| Start-up | minor 0, reads the last shutdown cause | yes |
| Start-up | minor 4, state 1 | yes |
| Late shutdown | minor 3, then minor 2 | yes |
| Final | minor 4, state 0, then the ICC channel is quiesced | yes |
| Final | minor 1, the power command | no |

The no-wait send exists only for service 4. The last write happens in the
kernel. User-space software only asks for the shutdown.

## Request layout

The request is a 12-byte ICC header plus the payload, padded to 32 bytes.

| Offset | Width | Shutdown | Reboot | Meaning |
|---|---:|---:|---:|---|
| `0x00` | 1 | `0x42` | `0x42` | magic |
| `0x01` | 1 | `4` | `4` | service (major) |
| `0x02` | 2 | `1` | `1` | minor |
| `0x04` | 2 | `0` | `0` | unknown or reserved |
| `0x06` | 2 | cookie | cookie | incremented per request |
| `0x08` | 2 | `32` | `32` | request length |
| `0x0a` | 2 | checksum | checksum | sum of the request bytes |
| `0x0c` | 2 | `0x0000` | `0x0100` | shutdown or reboot |
| `0x0e` | 1 | `2` | `2` | reason or state |
| `0x0f` | 1 | `0` | `0` | mode |
| `0x10` | 1 | `1` | `1` | flag |
| `0x11` | 2 | `0` | `0` | extra flag |
| `0x13..0x1f` | | `0` | `0` | padding |

The Linux payload at offset `0x0c` is `{0, 0, 2, 0, 1, 0}` for shutdown and
`{0, 1, 2, 0, 1, 0}` for reboot. `_bpcie_icc_cmd()` places it after the 12-byte
header and pads the request to 32 bytes, so the bytes on the wire match.

## Linux path at the time

In `drivers/ps4/ps4-bpcie-icc.c`:

- `icc_shutdown()` and `icc_reboot()` both send service 4 minor 1 through
  `bpcie_icc_cmd()` and `_bpcie_icc_cmd()`.
- `_bpcie_icc_cmd()` sets `reply_pending`, rings the doorbell, and waits for a
  reply or the fixed 15-second deadline.
- On timeout it logs `icc: interrupted or timeout: ret = ...`. `icc_shutdown()`
  then runs `mdelay(3000)` and `WARN_ON(1)`.
- `pm_power_off` is `icc_shutdown`.

The imported `0091-ps4-icc-use-msleep-instead-of-mdelay-in-shutdown-reb.patch`
changes the 3-second delay for Aeolia only. It does not touch the 15-second wait
or the Baikal driver.

## The no-wait candidate

The candidate was Linux-only and changed one thing. It added
`_bpcie_icc_cmd_nowait()` and `bpcie_icc_cmd_nowait()`, which build the same
header and payload, set `BUF_FULL`, ring the doorbell, leave `reply_pending`
clear and do not wait. `icc_shutdown()` used the new send. The unused
`icc_reboot()` was converted the same way for consistency, and that makes no
claim about reboot. The payload, flags, delay and `WARN_ON(1)` did not change.
The pending `0x70D` audio files were reverted so that a power test would not mix
in an audio variable.

It built as `7.2.11-psx-ps4-baikal-uvd-runtime-underscan-dev1-ps4-icc-nowait1`
and had not been booted when this was written.

If a no-wait send alone does not cut power, the next single variable is the
preparatory minor 4, state 0 request and the quiesce before the final request.
That is a separate protocol step, so it was left out of the first candidate.

## Reading the UART log

The no-wait reasoning only applies once shutdown reaches `pm_power_off`.

| UART shows | Meaning |
|---|---|
| `icc: interrupted or timeout` after about 15 seconds | The Linux wait path is confirmed, and a no-wait send addresses it. |
| `reboot: Power down`, then no power loss | `pm_power_off` returned. The command was refused, or the preparatory step is needed. |
| The log stops before `reboot: Power down` | The hang is earlier, in user space, unmounting or another driver. ICC is not the first suspect. |

## Hardware test boundary

A test needs one bounded UART session with:

- a stable `EXP-YYYYMMDD-NNN` identifier and the single objective "does the
  no-wait service 4 minor 1 request cut power?";
- expected evidence of the send being accepted, no 15-second timeout, the kernel
  line `reboot: Power down`, and the owner confirming the power LED and fan are
  off;
- a short timeout and a safe rollback to the accepted kernel if the console stays
  on;
- one power-off only, with no boot-file or storage change and no audio test
  combined with it.
