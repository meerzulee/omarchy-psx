# Orbis 12.02 ICC poweroff/reboot findings — 2026-10-22

> **Static-analysis note.** This document is not a hardware experiment and does
> not create or satisfy a `SESSIONS.md` acceptance entry. No console action,
> payload, boot-file change or power test is implied. The Linux candidate below
> has not been booted on hardware.

## Scope

The question was why Linux `poweroff` hangs on the Baikal PS4 while `reboot`
returns to Orbis. The investigation compared the Orbis 12.02 ICC power path,
recovered from the full-kernel IDA database, with the Linux Baikal
`ps4-bpcie-icc.c` implementation. The Orbis `SceSysCore` userland daemon was
also checked in Ghidra to identify the shutdown entry point.

Artifacts:

- `fullkernel1202.i64` — Orbis 12.02 full-kernel IDA database. Existing
  function objects are available in the `icc` and `icc_power` ranges.
- `SceSysCore.elf.decrypted` — Orbis 12.02 system daemon, 940,552 bytes,
  ELF `e_type=0xfe10` (`OS Specific`), entry `0x34f50`.
- Ghidra 12.1.3 raw import of the first `SceSysCore` `LOAD`: file offset
  `0x4000`, vaddr `0`, size `0xd1a18`. IDA 9.4.3 refuses this ELF with
  “Unsupported or unknown image type 65040 (0xFE10)”; Ghidra's raw import was
  used instead and therefore lacks dynamic-symbol names.

## Bottom line

The Linux shutdown **payload and ICC header are correct**. The defect is the
**completion mode**:

- Orbis sends the final service-4/minor-1 power command with
  `icc_query_nowait()` and never waits for a reply. The adjacent string says
  **“%s: use only to power off, reboot or suspend.”**
- Linux sends the same command through `bpcie_icc_cmd()`, which waits for a
  reply for up to 15 seconds. The Orbis path deliberately does not wait for
  one; if the firmware withholds it, `poweroff` spends 15 seconds in
  `_bpcie_icc_cmd()`, then runs `mdelay(3000)`, returns from `pm_power_off`,
  and the kernel reaches its halt loop without cutting power. This is the
  current failure hypothesis and matches an indefinite “poweroff hangs”
  symptom.
- Normal `reboot` does not exercise this path. The platform code assigns the
  global Aeolia `icc_reboot` to `machine_ops.emergency_restart`; the Baikal
  driver's `icc_reboot` is `static` and the compiler reports it as unused.
  An ordinary `reboot` uses the x86 reset path and lands back in the Orbis
  boot flow. That is expected and is not evidence that the Baikal ICC reboot
  command works; it needs separate wiring if that path is wanted. A
  Linux-to-Linux reboot is a separate boot-chain/kexec problem, not an ICC
  poweroff fix.

## Confirmed: Orbis ICC power module

The Orbis ICC source path embedded in the kernel is:

```
W:\Build\J02688428\sys\freebsd\sys\dev\scesb\icc\icc.c
W:\Build\J02688428\sys\freebsd\sys\dev\scesb\icc\icc_power.c
```

Relevant functions and handlers:

| Orbis symbol / address | Role |
|---|---|
| `sub_9D85C0` | `icc_power_shutdown_init`; registers `shutdown_pre_sync`, `shutdown_post_sync`, `shutdown_final`, `shutdown_force`, `icc_available`; sends major 4/minor 4 state 1 with the waiting query; registers the service-4 callback |
| `sub_9D8720` | `icc_power_shutdown_pre_sync`; calls `sub_EC82E0` |
| `sub_9D8750` | `icc_power_shutdown_post_sync`; sends major 4/minor 3 then minor 2 with the waiting query |
| `sub_9D8860` | `icc_power_shutdown_final`; sends major 4/minor 4 state 0, then the final major 4/minor 1 request through `sub_C47AD0` |
| `sub_9D8BD0` | `init_last_shutdown_cause`; major 4/minor 0 waiting query |
| `sub_9D8EB0` | service-4 notification callback (`system_power_state_change`) |
| `sub_C47050` | waiting ICC query; used for minor 4, 3, 2 and 0 |
| `sub_C47AD0` | `icc_query_nowait`; only accepts major 4; sends through `sub_C47C10`; does not wait for a reply |
| `sub_C47C10` | ICC request writer; sets magic/header/checksum, writes `BUF_FULL`, rings the doorbell |
| `sub_C47F90` | post-minor-4 quiesce/lock helper called before the final request |

The Orbis final handler also logs `ICC: Shutdown.`, `ICC: Reboot.`,
`ICC: Fatal shutdown.`, `ICC: Boot diagOS.` and `ICC: Boot alt CPU.`; those
strings are in `icc_power.c`.

## Recovered request layout

`sub_C47C10` sets byte 0 to magic `0x42`, so the caller-built buffer is a
complete ICC request. For the normal shutdown and reboot cases the layout is:

| Offset | Width | Shutdown | Reboot | Meaning |
|---|---:|---:|---:|---|
| `0x00` | 1 | `0x42` | `0x42` | magic, set by `sub_C47C10` |
| `0x01` | 1 | `4` | `4` | major |
| `0x02` | 2 | `1` | `1` | minor |
| `0x04` | 2 | `0` | `0` | unknown/reserved |
| `0x06` | 2 | cookie | cookie | incremented by `sub_C47C10` |
| `0x08` | 2 | `32` | `32` | request length |
| `0x0a` | 2 | checksum | checksum | sum of request bytes |
| `0x0c` | 2 | `0x0000` | `0x0100` | shutdown vs reboot |
| `0x0e` | 1 | `2` | `2` | reason/state default (`v4`) |
| `0x0f` | 1 | `0` | `0` | mode default (`v5`) |
| `0x10` | 1 | `1` | `1` | handoff/flag |
| `0x11` | 2 | `0` | `0` | extra flag |
| `0x13..0x1f` | — | `0` | `0` | zero padding |

The Linux `icc_shutdown()` payload at offset `0x0c` is
`{0, 0, 2, 0, 1, 0}`; the reboot payload is `{0, 1, 2, 0, 1, 0}`. Those are
byte-for-byte the default Orbis payload. Linux's `_bpcie_icc_cmd()` puts this
data after the 12-byte ICC header and pads the total length to `0x20`, so the
wire request is also correct.

The important difference is not the bytes but the call:

```c
/* Orbis: final power command */
sub_C47AD0(&request, ...);      /* icc_query_nowait(): return immediately */

/* Linux: current power command */
bpcie_icc_cmd(4, 1, command, sizeof(command), NULL, 0);
/* waits up to 15 s for a reply that the firmware does not send */
```

The project previously recorded a clean Linux shutdown that reached
`reboot: Power down` (`EXP-20260810-001-A47`), so the hardware is not
inherently unable to power off. That historical result must not be used as
acceptance for the current 7.2 Baikal kernel; it only shows why a regression
or a changed ICC completion path is the relevant question.

## Confirmed: Linux current path

From `drivers/ps4/ps4-bpcie-icc.c`:

- `icc_shutdown()` sends service 4/minor 1 with
  `{0, 0, 2, 0, 1, 0}`.
- `icc_reboot()` sends service 4/minor 1 with
  `{0, 1, 2, 0, 1, 0}`.
- Both use `bpcie_icc_cmd()` → `_bpcie_icc_cmd()`.
- `_bpcie_icc_cmd()` sets `reply_pending`, rings the doorbell, and polls or
  waits until a reply arrives or the hard-coded 15-second deadline expires.
- On timeout it logs `icc: interrupted or timeout: ret = ...`, then
  `icc_shutdown()` does `mdelay(3000)` and `WARN_ON(1)`.
- `pm_power_off` is `icc_shutdown`. The platform
  `machine_ops.emergency_restart` references the global Aeolia `icc_reboot`;
  the Baikal `icc_reboot` in this file is static and unused, so the Baikal
  emergency-reboot command is not currently wired.

The existing `0091-ps4-icc-use-msleep-instead-of-mdelay-in-shutdown-reb.patch`
changes the 3-second post-command delay for Aeolia, but it does not change the
15-second reply wait and is not applied to the Baikal driver.

## Ghidra: Orbis userland shutdown entry

The Ghidra raw-import pass on `SceSysCore.elf.decrypted` found:

| String / address | Ghidra result |
|---|---|
| `appSystemShutdown` at `0x971c5` | referenced from `FUN_00011b80` at `0x11b80` |
| `appSystemReboot` at `0x9727f` | present in the same daemon |
| `sceSystemReboot` at `0x94553` | referenced from `FUN_00004dc0` at `0x4dc0` |
| `SceSysCoreReboot` at `0xa919f` | referenced from `FUN_00031f30` at `0x31f30` |
| `[Syscore App] Start SystemShutdown` / `Start SystemReboot` | daemon shutdown/reboot logging |

`FUN_00011b80` calls `FUN_00004dc0`, which logs `sceSystemReboot` and invokes
the daemon's system reboot helper. This is a userland request path; the final
ICC service-4/minor-1 write is in the kernel `icc_power` module, not in
`SceSysCore`. The raw import has no dynamic-symbol table, so the `FUN_*` names
must be treated as structural addresses, not as confirmed export names.

A second IDA pass used a local copy of the same ELF with only the ELF header
`e_type` changed from `0xfe10` to `ET_EXEC` (`0x0002`); IDA 9.4.3 then loaded
the existing program headers and decompiled the daemon. In that pass:

- `sub_11B80` is `appSystemShutdown`; it logs
  `[Syscore App] System Shutdown %d`, computes
  `(reason << 27) | 0x4000`, and calls `sub_4DC0`.
- `sub_4DC0` is `umd::Manager::reboot(int)`; it logs
  `[Syscore Umd] sceUmdReboot(%#x)`, sets the `sceSystemReboot` tag, and calls
  `sub_33480(reason)`.
- `sub_33480` runs the reboot notification list, calls `sub_34EF0`, then calls
  `sub_31F30` (`SceSysCoreReboot`) and `sub_31FA0`.
- `sub_31F30` is the `SceSysCoreReboot` helper; it resolves
  `SceSysCoreReboot` and calls `sub_913D0`.

The final `sub_908A0`/`sub_913D0`/`sub_90DC0` targets appear in IDA as
unresolved `while (1);` thunks; the patched ELF has no usable import module
table. The exact `sceSystemReboot`/`sceKernelPower` wrapper therefore cannot be
named from this stripped daemon alone. The structural chain
(`appSystemShutdown` → `umd::Manager::reboot` → `SceSysCoreReboot`) is
confirmed; the final ICC service-4/minor-1 write remains the kernel
`icc_power` path analysed above.

## Candidate for a one-variable hardware test

A minimal Linux-only candidate is in
`lab/poweroff-nowait-20261022/0001-ps4-icc-use-nowait-for-final-power-command.patch`.
It:

1. adds `_bpcie_icc_cmd_nowait()` and `bpcie_icc_cmd_nowait()` to
   `drivers/ps4/ps4-bpcie-icc.c`;
2. builds the identical 12-byte header and payload, sets `BUF_FULL`, and rings
   the doorbell;
3. deliberately does not set `reply_pending` and does not wait for a reply;
4. changes `icc_shutdown()` to use the nowait send.

The patch also applies the same conversion to the file's static `icc_reboot()`
for consistency, but that function is currently unused and is not the normal
reboot path; it does not claim a reboot fix. The payload, flags, delay and
`WARN_ON(1)` are unchanged. The candidate is built from the pre-audio v2 base,
with the `dce_v8_0.c` and `atihdmi.c` audio experiment files reverted, so a
poweroff test does not mix in the pending `0x70D` audio variable.

If the nowait candidate still does not cut power, the next single variable is
the Orbis preparatory major 4/minor 4 state-0 query (and the `sub_C47F90`
quiesce) before the final request. It is intentionally not included in the
first candidate because it is a separate protocol step.

### Build result

The candidate built as:

```
7.2.11-psx-ps4-baikal-uvd-runtime-underscan-dev1-ps4-icc-nowait1
```

- `bzImage` SHA-256:
  `8ed182c0d6a08a5f2e3c083cf4bdf10ed12f9001814125291188be4317267e57`
- patched `ps4-bpcie-icc.c` SHA-256:
  `d6e9fb0f0b02d253c4fe7e48f5b1aab43e8a46fe7b5525be156b3c4a1b649edb`
- review artifact:
  `lab/poweroff-nowait-20261022/artifact/bzImage`
- remote modules root:
  `/home/meerzulee/Work/psx/lab/poweroff-nowait-20261022/artifact/modules-root`

The image is built but not staged or booted. This build result is not a
hardware acceptance entry.

## Diagnostic discriminator before the test

The nowait conclusion applies when the shutdown reaches `pm_power_off`
(`icc_shutdown`). The existing UART log should distinguish three cases:

- `icc: interrupted or timeout` after roughly 15 seconds: the Linux wait path
  is confirmed; the nowait candidate directly addresses it.
- `reboot: Power down` followed by no power loss: `pm_power_off` returned; the
  command was not accepted or the firmware needs the preparatory minor-4
  state-0 step.
- The log stops before `reboot: Power down`: the hang is earlier in userspace,
  unmount, or another driver; the ICC power command is not the first suspect.

No UART log from the current failing poweroff has been attached to this
static-analysis record.

## Hardware test boundary

A hardware test requires one bounded UART session with:

- a stable `EXP-YYYYMMDD-NNN` identifier and the single objective “does the
  nowait service-4/minor-1 request cut power?”;
- expected evidence: `icc` send accepted, no 15-second timeout, kernel
  `reboot: Power down`, and operator-confirmed power LED/fan off;
- a short timeout and a safe rollback to the accepted kernel if the console
  remains on;
- one poweroff action only, without changing boot files or storage and without
  combining the pending audio test.

No such session has been started, and no hardware acceptance is claimed here.
