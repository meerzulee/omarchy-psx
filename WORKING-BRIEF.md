# Omarchy psX migration working brief

## Goal and current deliverable

Develop Omarchy and its independent Linux kernel for PS4, PS5 and future
consoles in `omarchy-psx` and `linux-psx`. This run migrates the existing PS4
implementation and curated knowledge, makes the psX repositories the development
entry points, and preserves the original checkouts. It does not implement or
claim a working PS5 port.

## Priorities

1. Preserve all useful PS4 source, including pending partitioned-USB and Ethernet
   work, with import provenance and a complete disposition inventory.
2. Keep PS4 runtime identities and qualified historical boot profiles intact;
   resolve workspace dependencies through the new repositories.
3. Carry forward readable research and verification while keeping raw captures,
   credentials, firmware, generated archives and machine state outside Git.

## Scope and constraints

The PS4 distribution implementation lives under `platforms/ps4/`, preserving
its internal layout. Root tooling provides console-neutral setup and handoff.
Kernel implementation belongs in `linux-psx`; PS5 has an explicit planned status.
Legacy package names and filesystem labels remain compatibility interfaces.
The original repositories, including their indexes and pending edits, must not
change. Mac infrastructure uses OrbStack; native Linux kernel development needs
no VM. Existing Omarchy image/launcher build constraints remain documented.

No console operation, media write, reboot, hardware acceptance or new binary
release is part of this source migration. Reconstructed boot inputs and the
new psX kernel require their own hardware qualification.

## Done when

- Every legacy source/knowledge input has an imported, superseded or excluded
  disposition, with source and resulting hashes for imported files.
- New-clone source setup uses pinned public repositories; active source tools
  do not require an old `omarchy-ps4` or `linux-ps4-kernel` checkout.
- Historical exact-hash boot profiles are distinguished from new candidates.
- Focused synthetic/host checks pass; unavailable generated-input and hardware
  checks are identified accurately.
- Documentation identifies the new ownership, host paths and remaining PS5 work.
- Original repository HEAD, index, status and pending bytes are preserved.

## Execution and evidence

Audit completed: the PS4 kernel's 55-patch build/CI stack is present in
`linux-psx`, but its historical knowledge coverage is incomplete. `omarchy-psx`
has only 20 integration files; the old distribution has 246 tracked files and
20 additional source files. Two tracked raw UART logs are excluded from public
migration. Initial kernel and integration CI passed before this broader import.

The PS4 source import now accounts for all 266 selected legacy paths: 260
imported files (200 unchanged, 60 adapted), two excluded raw UART logs and four
excluded vendor placeholders. Four new platform files document and verify the
handoff. Original source hashes, current hashes/modes, pending states and each
disposition are in `provenance/ps4-worktree-import.json`.

Nested workspace paths and pinned source setup are adapted. Public initramfs
seed acquisition was exercised and matched its recorded size/SHA256. Full
source reconstruction is available through the migrated OrbStack assembler;
it creates a new candidate and was not run during this source-only migration.
The exact historical repacker remains available separately.

Independent review checked package recipe digests, module layout and source
handoff. It exposed and corrected a frozen-beta/new-kernel module mismatch and
a missing archive digest check. The historical whole-device profile writer is
disabled before device probes until stable USB identity/confirmation is ported.

Measured host verification: root synthetic suite (34 tests, one optional
external-base skip), platform source/fixture checks (98 source programs syntax,
Git/ZIP setup fixtures, Ethernet/USB/profile/migration guards, five shell suites
and C++ manager/SHA-256 tests) passed. OS, generated-input and container tests
report explicit skips. Kernel `make check` passed six tests, 102 frozen input
hashes, all 55 active patches and 11 curated knowledge/test hashes. Its new
knowledge ledger accounts for 117 historical sources.

Both original checkouts' HEADs, indexes, statuses and pending file bytes were
checked unchanged. Current documentation links resolve; installed-context
workspace templates have separate path semantics. Privacy review removed
machine/network identifiers while preserving address relationships, hardware
IDs, exact artifact hashes and original historical acceptance limits.

Source publication and a fresh-clone handoff check complete this phase.
Image/FPKG builds, live storage writes, fresh boot acceptance, unattended
Ethernet startup and PS5 implementation remain outside this migration.

## Steering

2026-10-17: the owner explicitly requested moving everything useful from
`omarchy-ps4` into `omarchy-psx`, within the larger two-repository migration.
