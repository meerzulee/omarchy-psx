# Omarchy psX contributor instructions

## Project boundaries

- This MIT-licensed repository owns Omarchy distribution source: packages,
  desktop/rootfs policy, host handoff, boot profiles, optional NetworkManager
  activation, launcher/FPKG, installation, recovery and curated research.
  Preserve existing copyright and license notices when importing adapters;
  record source commits, original/destination hashes and adaptations in
  `provenance/integration-import.json`.
- `https://github.com/meerzulee/linux-psx` owns the distribution-independent
  kernel, platform patches/configs, builder, generic artifact metadata and CI.
  Do not duplicate its kernel tree or add Omarchy/NM dependencies to it.
- The PS4 implementation lives under `platforms/ps4/`; preserve its internal
  paths and deployed package/service/label identities. Root tooling owns
  workspace setup and cross-console entry points. `platforms/ps5/` is planned;
  a source migration does not establish a new image or hardware acceptance.
- Keep historical `omarchy-ps4` work and its dirty files intact. Do not import
  whole workspaces, firmware, raw UART/network logs, credentials, PKGs or private
  console artifacts. Fetch publicly recorded sources from their upstreams.

## Reproducible host handoff

- Read `README.md`, `docs/MIGRATION.md` and `docs/DEVELOPMENT-HOSTS.md`. Source
  handoff lives in `manifests/development-sources.json` and
  `manifests/kernel-source.json`; use their full immutable commits. A null
  revision means publication is pending, not permission to use moving `main`.
- `scripts/setup-workspace` creates missing sibling kernel/UART clones at their
  pins and accepts existing history containing those pins. The older
  `setup-kernel-workspace` checks an exact kernel snapshot. Neither may
  reset/rebase/merge or replace an existing clone,
  discard dirty work, or carry a virtual environment/runtime PID across hosts.
- On macOS ARM64 use OrbStack only; verify `orb status` is `Running` and
  `docker context show` is `orbstack` before container work. Do not run a kernel
  build directly on Darwin or start another container/VM runtime.
- On Linux x86-64 use the kernel repository's native build tools. No container
  is required for a native kernel build. Follow its pinned dependencies/config.
- Consume a whole matching kernel/module set plus its `artifacts.json`. Never
  install one Ethernet module as a replacement for the matching module tree.
- For initramfs work read `docs/INITRAMFS.md`, `manifests/ps4-initramfs.json`
  and `provenance/initramfs-import.json`. The exact legacy `/init` is preserved;
  changing it creates a new candidate and requires updated hashes/evidence.
- `scripts/repack-ps4-initramfs` is data-only, requires an explicit pinned
  external base and refuses existing outputs. Keep generated archives, seeds,
  BusyBox binaries and firmware out of Git; source provenance must distinguish
  the old checkout HEAD from its pending/untracked source bytes.
- `scripts/fetch-ps4-initramfs-seed` acquires the original public seed into
  ignored cache with full size/hash checks. It differs from the generated base
  required by the exact repacker. The migrated full assembler creates a new
  candidate; do not assume historical byte identity or change FPKG pins blindly.
- Preserve frozen old boot profiles. Supply their matching binaries explicitly;
  new psX boot sets need distinct measured manifests and hardware experiments.
- Imported dated records are historical, with current corrections/entry points
  in `docs/MIGRATION.md`. Record source/current hashes and adaptations for the
  full PS4 import in `provenance/ps4-worktree-import.json`.
- Run `python3 scripts/check-provenance` and the synthetic host suite. Real-base
  tests require explicit `OMARCHY_INITRAMFS_TEST_BASE`; never auto-probe disks.

## Hardware and activation

- Source inspection, host tests and builds do not operate the console. A build
  or agent agreement is not hardware acceptance; preserve the recorded scope.
- Boot-file writes, driver activation, reboot/power tests and acceptance claims
  require explicit task authority and continuous UART with one coherent bounded
  experiment: stable EXP ID, objective/evidence, timeout, rollback and stop
  conditions. Do not manufacture sessions for ordinary source work.
- Storage and launcher tools must never act during source setup or tests.
  Any authorized media write requires identifying the actual target and explicit
  confirmation. Console-internal storage/boot writes and PKG installation need
  their own explicit task authority and bounded experiment.
- Baikal Ethernet is native from Linux psX `6.18.44-psx-ps4-baikal2`: udev
  loads `psx_mts_net` and the network manager's first open publishes `psx0`.
  Do not add a userspace activation adapter, package or service. Boot with
  `psx_mts_net.autoarm=0` or `modprobe.blacklist=psx_mts_net` to keep it off.
- Published MTS DMA/code/maps/references remain retained. Do not unload, reset,
  force cleanup, clear overrides or retry an uncertain arm/UP. Terminal faults
  need a fresh power-off/boot; ordinary healthy admin down/up uses one generation.
- Keep at most one hardware experiment active. Record new evidence before a
  retry; three identical failures without new evidence end that path.
- The curated PS4 ledger is `platforms/ps4/experiments/SESSIONS.md`. Keep raw
  UART/packet captures local. Do not ship default passwords or enable password
  SSH in release images; private debug/recovery access requires explicit inputs.

## Collaboration and publication

- You are sharing a workspace. Preserve other agents' and users' edits; use
  assigned file ownership and verify delegated findings before adopting them.
- Commits, pushes, releases and storage/console actions need explicit task
  authority; do not infer it from successful tests. Existing session authority
  remains valid and should not be requested again.
- Run the focused host tests after adapter changes. Keep all tests synthetic;
  do not probe live sysfs, NetworkManager or storage from a test suite.
- Operational links should include a full raw URL for terminal users. Local
  handoffs should use repository-relative paths, never a particular user's home.
