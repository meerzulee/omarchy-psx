# PS5 12.40 boot dependencies

Research/preparation snapshot: 2026-10-18. Target: original retail PS5, firmware
12.40. Relapse jailbreak and arbitrary ELF delivery are working assumptions
supplied by the owner; the loader's exact version is not needed for this local
preparation. No console actions or hardware acceptance have occurred.

[Static analysis of the supplied ELF](REA-FINDINGS.md) now confirms that its
firmware selectors also omit 12.40. Its initial unsupported-firmware warning
does not return. This file is therefore not a 12.40 candidate; a local hash
match does not change that conclusion.

**There is no prepared 12.40 boot payload or bootable image.** The current
public references leave the hypervisor implementation and Linux handoff
unresolved. Version-selection edits or copied offsets from a nearby firmware
would not establish compatibility.

## Prepared files

- `manifests/ps5-dependencies.json`: full source pins, per-file SHA256/size,
  component status, evidence links and the upstream boot-input contract.
- `scripts/fetch-ps5-references`: acquire those exact text files into ignored
  `cache/ps5-references`. Existing different files are preserved and refused.
- `scripts/check-ps5-compatibility`: offline metadata/reference verification,
  compatibility report and optional local ELF fingerprint. No network or
  payload execution occurs in the checker.
- `tests/test_ps5_*.py`: synthetic integrity and negative readiness cases.

Cached upstream text remains external reference material under its original
terms. It is not imported or relicensed as Omarchy source. The kernel repository
now separately integrates the pinned PS5 patch and a firmware-free derived config
as target `7.2-ps5`. See [FIRST-BOOT.md](FIRST-BOOT.md) for this local build and
diagnostic-initramfs preparation; neither supplies a 12.40 handoff.

## Current dependency result

| Requirement | Result | Evidence and remaining work |
| --- | --- | --- |
| Jailbreak / ELF delivery | Assumed working | Owner report; no repetition requested. |
| Hypervisor implementation | Blocked | Official Reborn dispatch includes only 13.00, 13.20 and 13.60. The 12.40 author reports incomplete resume validation. |
| Linux handoff | Blocked | Established loader supports specified 3.00–7.61 versions. Reviewed pLinux5-NG has neither a Linux entry nor a fallback registry entry for 12.40. |
| PS5 kernel + modules | Built locally | `7.2.3-psx-ps5-dev1` compiled in OrbStack with 519 matching modules; measured identities are in `linux-psx/provenance/7.2-ps5.json`. No hardware acceptance. |
| Early userspace + rootfs | Diagnostic set built and verified | `output/ps5-probe/7.2.3-psx-ps5-dev1/` contains pinned BusyBox and the complete exact module tree. Graphics firmware, console qualification and the complete Omarchy rootfs remain pending. |
| Hardware acceptance | Pending | No PS5 Linux boot evidence. Host checks cannot provide this evidence. |

The source checker validates the **recorded snapshot**, not the behavior of a
payload or the truth of a future edited support claim. It does not automatically
infer compatibility from C code, monitor upstream or promote a firmware because
an ELF's name, header or hash matches. A valid manifest is allowed to describe
blocked work. Missing requirements and unknown firmware remain unsuccessful.

Official support reference:
https://github.com/PS5Dev/Byepervisor-Reborn/blob/ea04f7132b837087f552c57261cb800481a3a910/kdlsym.c

12.40 work-in-progress report:
https://github.com/PS5Dev/Byepervisor-Reborn/issues/5#issuecomment-6181127462

New loader reference (experimental):
https://github.com/pLabs5/pLinux5-NG/tree/978cfb3a1ff1dd5e6fc6e776c5aae3ed8c5770fd

## Linux boot-input contract

This contract is derived from the established loader at
`64637c177eaed277fb6ccce394cbb29dd047b893`. It is a preparation reference;
its memory layout and runtime hardware assumptions are not validated on 12.40.

| File | Contract |
| --- | --- |
| `bzImage` | Required PS5-enabled x86-64 Linux boot-protocol image. Record kernel release, source/config/patch pins and artifact identity. |
| `initrd.img` | Required external initramfs. Its format must be supported by the selected kernel; it must provide the drivers/firmware needed to discover and mount the agreed rootfs. |
| `cmdline.txt` | Optional upstream, but a future candidate should supply one explicit line. Upstream reads at most 2047 bytes and cuts at the first newline. Root LABEL/UUID must agree with actual storage and `fstab`. |
| `vram.txt` | Optional hexadecimal byte count. Upstream fallback is 512 MiB (`0x20000000`); no local sizing decision has been qualified. |
| Module tree | Complete modules for the exact kernel release; early modules belong in the matching initramfs. Never substitute a PS4 tree or isolated module. |

Each boot file is searched independently: USB roots 0–3, then `PS5/Linux/`
inside USB roots 0–3. Future staging should use one complete set in one chosen
directory; duplicate files on different drives could produce a mixed set.
No command here writes or formats media.

The loader owns Linux boot parameters, the physical memory map and reserved
regions, ACPI/model information and the runtime CPU/device handoff. Rootfs
configuration cannot supply missing firmware-specific loader support. PS4 and
PS5 both use subarchitecture identifier 5 in the reviewed loaders, so that
identifier alone is not sufficient to validate which console a kernel targets.

Source contract:
https://github.com/ps5-linux/ps5-linux-loader/blob/64637c177eaed277fb6ccce394cbb29dd047b893/source/loader.c

Kernel research remains owned by sibling `linux-psx`; distribution boot
integration belongs here. The existing PS4 kernel-source manifest and profiles
remain selected. There is no PS5 artifact substitution into those interfaces.

## Local use and next evidence

From the repository root:

```sh
python3 scripts/fetch-ps5-references
python3 scripts/check-ps5-compatibility --validate-manifest
python3 scripts/check-ps5-compatibility --sources cache/ps5-references --firmware 12.40 --json
```

Use `--elf /absolute/path/to/file.elf` only to add size and SHA256 to the local
report. It reads a bounded regular file and never executes it. A fingerprint
does not identify its build source, establish firmware support or clear any
other requirement. Keep reports containing private paths under ignored
`output/`, not in versioned metadata.

Exit codes: 0 = requested validation completed / all recorded requirements
ready; 1 = invalid input or integrity failure; 2 = unresolved dependencies.
Inspect the report even after exit 0; this tool is not a hardware acceptance
authority.

The next useful upstream evidence is a published, reviewable 12.40 hypervisor
implementation together with a compatible Linux handoff and original-model
boot evidence. Review those exact revisions before updating the snapshot.
Kernel/initramfs preparation proceeds independently as local work in the two
psX repositories. Hardware tests require their own task authority and an
agreed PS5 capture/rollback/acceptance plan under the workspace rules; PS4
capture history is not PS5 evidence.
