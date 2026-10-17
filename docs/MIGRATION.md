# Moving development to psX

`omarchy-psx` is the distribution development repository; `linux-psx` owns
the independent console kernel. The existing PS4 implementation is preserved
under `platforms/ps4/`, so a PS5 port can use its own target without duplicating
the repository. PS5 implementation and hardware qualification remain planned.

## What moved

The source import includes the old checkout's pending work, not just its last
commit: packages/settings/provisioning/Ethernet, package profiles, rootfs and
initramfs source, launcher/FPKG source, installation/recovery tools, tests,
documentation, research and the curated experiment ledger. Source paths,
worktree states, hashes, file modes, changes and exclusions are recorded in
[`ps4-worktree-import.json`](../provenance/ps4-worktree-import.json).

Generated rootfs/images, kernel and module archives, PKGs, vendored SDK/loader
binaries, firmware, caches and raw UART captures remain external. Their absence
from Git does not discard the local originals. Private machine/network details
are redacted from the migrated public research record. The old checkouts and
all their staged, unstaged and untracked work are preserved.

## Find the implementation

| Work | New location |
| --- | --- |
| Distribution packages and runtime policy | `platforms/ps4/packages/`, `profiles/`, `inventory/` |
| Rootfs, splash, initramfs and installers | `platforms/ps4/rootfs/`, `scripts/` |
| PS4 launcher/FPKG and boot-set staging | `platforms/ps4/fpkg/` |
| Recovery and portable development | `platforms/ps4/gift-dev/`, `portable/` |
| Historical results and research | `platforms/ps4/docs/`, `knowledge/`, `experiments/SESSIONS.md` |
| Current Mac/Linux setup | `docs/DEVELOPMENT-HOSTS.md`, `scripts/setup-workspace` |
| New kernel adapter / exact initramfs preservation | Root `scripts/`, `rootfs/initramfs/init`, `docs/USING-LINUX-PSX.md`, `docs/INITRAMFS.md` |
| Kernel patches, builds and generic hardware evidence | Sibling `linux-psx` |
| PS5 distribution target | `platforms/ps5/README.md` (planned) |

Imported dated records explain the original experiments. Their absolute source
paths, old artifact identities and old repository links are history, not fresh
host instructions. Start from this guide and the root host guide. Historical
support claims do not transfer to a new config, compiler, firmware arrangement
or kernel/initramfs combination.

## Runtime compatibility and boot inputs

Keep deployed `omarchy-ps4` package/service names, `/etc/omarchy-ps4` settings,
`OMARCHY-PS4` root labels and launcher boot parameters until a separately tested
upgrade changes those interfaces. The repository name is independent of them.

Old FPKG boot profiles and manifests contain exact accepted artifact hashes.
They remain frozen. Supply their matching external boot inputs explicitly;
an old profile must reject a new psX kernel with a different identity. Building
the new kernel successfully is not sufficient to change an FPKG pin.
The old whole-device boot-profile writer is retained as archived source and
disabled before device access until its stable USB identification and explicit
confirmation checks are ported. Other storage tools retain their existing
operator confirmation gates; this migration runs none of them.

For a new boot candidate:

1. Build the selected Linux psX target and preserve its resolved config,
   artifact manifest and complete matching module tree.
2. Assemble compatible early userspace, supplying required firmware externally.
   The exact historical repack and source reconstruction are separate paths.
3. Define a distinct boot-set/profile identity with measured sizes and hashes;
   retain a complete known-good rollback set.
4. Use one bounded UART experiment for the coherent boot test, then record
   results and repeat acceptance according to the active plan.

This migration performs source/host verification only. It does not stage a new
console boot set, enable an Ethernet service or create a new binary release.
The imported MTS2 Ethernet package and the manual activation adapter were
removed on 2026-10-18: from `6.18.44-psx-ps4-baikal2` the kernel loads
`psx_mts_net` itself and NetworkManager's ordinary wired profile brings up
`psx0`. Their history remains in the experiment ledger and Git history.

## Kernel knowledge and remaining work

The kernel migration ledger and PS4 capability/history guides live in
`linux-psx/provenance/knowledge-migration.json` and
`linux-psx/platforms/ps4/docs/`. They distinguish measured Sony controller and
PHY identities from superseded DWMAC hypotheses and separate earlier private
build evidence from the new public firmware-free target.

The practical multi-console design is one repository per concern with separate
console targets. A common PS4/PS5 kernel binary needs additional runtime gating
and independent loader/hardware work; it is not implied by this source move.

Implementation progress and measured verification for this run are recorded in
[`WORKING-BRIEF.md`](../WORKING-BRIEF.md).
