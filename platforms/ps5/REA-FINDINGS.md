# Supplied Byepervisor Reborn ELF: static findings

Inspected 2026-10-17 using the REA investigation workflow and the independently
configured IDA MCP on the development host. Target execution was not requested
or performed. This is a bounded compatibility investigation, not a complete
binary audit or a hardware test.

## Artifact identity

- Size: 177,256 bytes.
- SHA256: `a8fa2970f55cd29454211f618aa3145341da7959b4d15a60b8f665cd4a8b112d`.
- IDA identifies a 64-bit ELF and completed automatic analysis.
- Provider: IDA 9.4, Hex-Rays 9.4.0.260714, IDA MCP 3.1.4.
- Publisher, build source and reproducible build identity remain unverified.

The analysis used a hash-matched copy. The supplied original was unchanged.

## Question and evidence ledger

| Question | Finding | Evidence / limits |
| --- | --- | --- |
| Does this binary contain 12.40 firmware selection? | No 12.40 case exists in the complete named selectors `kdlsym`, `kgadget` and `rawoff`. Each selects only 13.00, 13.20 and 13.60, otherwise returning zero. | `IDA-RPC-0007`, observed static decompilation. This conclusion is scoped to these selectors. |
| Does the unsupported-firmware check exit? | The initial branch prints/notifies and then falls through to model detection; it contains no early return. | `IDA-RPC-0008` and `IDA-RPC-0010`, bounded disassembly and pseudocode. Notification behavior and runtime outcome were not tested. |
| Is this the supplied artifact? | The analysis input size and SHA256 match the supplied file. | `IDA-RPC-0006`, IDA input metadata plus local/remote hashing. |
| Is it byte-identical to an official build? | Unknown. The inspected behavior agrees with the reviewed official source, but this is not whole-binary equivalence. | No official release/build match established. |
| Does it boot Linux or work on the owner's console? | Unestablished; its missing 12.40 selector is an immediate compatibility blocker. | No payload execution, console operation or hardware acceptance. |

`IDA-RPC-*` identifiers belong to the local investigation ledger, not REA's
native `ev_*` namespace. Private raw RPC results, the focused evidence JSON,
report, checksums and saved IDA database are retained under the workspace's
`lab/ps5-12.40-rea-20261017/`. They are not bundled in this repository.

At the time of this binary pass, REA 6.4.0 connected but had no configured
Ghidra installation path or IDA adapter binding. Actual decompilation used the
working standalone IDA MCP. A subsequent Ghidra environment repair is a
separate provider-validation task; it must not retroactively be described as
Ghidra analysis of this artifact.

## Subsequent Ghidra provider repair

The development host already had Ghidra 12.1.3 and a full JDK 21 installed.
Fish login also lacked the required variables. Explicit `GHIDRA_INSTALL_DIR`
and `JAVA_HOME` entries were added to the existing REA MCP registration, with
a backup and every other parsed configuration value preserved. REA remains
pinned to 6.4.0; its provider accepts the installed Ghidra 12.1.x build.

A fresh process started from the saved registration successfully opened and
decompiled `/usr/bin/true` through Ghidra, then closed its own session. Probe
evidence: `ev_ad4cdc8cb81975d496b7decdcb96424686b38e46a6f8b34e7a0351b8c7da1dc2`.
This verifies the repaired provider; it is not another analysis of the supplied
ELF. Existing remote Codex/REA processes need a restart/reconnect to inherit
the repaired environment. Private configuration receipts and probe results are
in `lab/ps5-12.40-ghidra-setup-20261017/` at the workspace root.

## How the components relate

The source research describes an existing jailbreak providing the environment
in which an ELF payload can run. Byepervisor Reborn then uses a rest-resume
hypervisor boundary flaw, with firmware-specific code/data mappings. A Linux
loader still has to establish Linux's memory map, boot parameters and hardware
state before entering a compatible kernel and initramfs. A launcher UI is an
entry point for those external payloads; packaging the UI does not fill in
their missing firmware support.

```mermaid
flowchart LR
    A[Launcher UI] --> B[Existing ELF loader]
    B --> C[Firmware-compatible payload]
    C --> D[Linux boot handoff]
    D --> E[PS5 kernel and matching initramfs]
    E --> F[Omarchy root filesystem]
```

The inspected file cannot be promoted to a 12.40 candidate merely by assigning
it an Omarchy menu entry. The public-source dependency report remains blocked.

Source research:
https://github.com/PS5Dev/Byepervisor-Reborn/tree/ea04f7132b837087f552c57261cb800481a3a910
https://github.com/soniciso1/ps5-hv-writeups/blob/e4d8b98390754d7eba7c4ea307a168a7d2e9962d/s3-resume-startup_mp-ap-launch.md
