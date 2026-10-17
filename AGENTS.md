# Omarchy psX contributor instructions

## Project boundaries

- This MIT-licensed repository owns optional Omarchy integration: host handoff,
  boot profiles, NetworkManager activation, distribution UX and recovery docs.
  Preserve existing copyright and license notices when importing adapters;
  record source commits, original/destination hashes and adaptations in
  `provenance/integration-import.json`.
- `https://github.com/meerzulee/linux-psx` owns the distribution-independent
  kernel, platform patches/configs, builder, generic artifact metadata and CI.
  Do not duplicate its kernel tree or add Omarchy/NM dependencies to it.
- This repository is integration scaffolding, not a complete migrated Omarchy
  distribution, OS image or installer. PS5 and future-console work is planned.
- Keep historical `omarchy-ps4` work and its dirty files intact. Do not import
  whole workspaces, firmware, raw UART/network logs, credentials, PKGs or private
  console artifacts. Fetch publicly recorded sources from their upstreams.

## Reproducible host handoff

- Read `README.md` and `docs/USING-LINUX-PSX.md`. The source handoff lives in
  `manifests/kernel-source.json`; use its full immutable kernel commit. A null
  revision means publication is pending, not permission to use moving `main`.
- `scripts/setup-kernel-workspace` creates a missing sibling `linux-psx` clone
  at that commit. It must never reset/rebase/merge or replace an existing clone,
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
- Run `python3 scripts/check-provenance` and the synthetic host suite. Real-base
  tests require explicit `OMARCHY_INITRAMFS_TEST_BASE`; never auto-probe disks.

## Hardware and activation

- Source inspection, host tests and builds do not operate the console. A build
  or agent agreement is not hardware acceptance; preserve the recorded scope.
- Boot-file writes, driver activation, reboot/power tests and acceptance claims
  require explicit task authority and continuous UART with one coherent bounded
  experiment: stable EXP ID, objective/evidence, timeout, rollback and stop
  conditions. Do not manufacture sessions for ordinary source work.
- Never format/partition media, mount or repair console-internal storage, write
  internal boot files, or install a PKG from these integration scripts.
- The explicit Ethernet adapter is optional, manual and once per boot. Preserve
  its kernel/config/module pins, PCI/glue guards, NM ownership barrier and
  positive publication check. Do not auto-enable a service or arm on import.
- Published MTS DMA/code/maps/references remain retained. Do not unload, reset,
  force cleanup, clear overrides or retry an uncertain arm/UP. Terminal faults
  need a fresh power-off/boot; ordinary healthy admin down/up uses one generation.
- Keep at most one hardware experiment active. Record new evidence before a
  retry; three identical failures without new evidence end that path.

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
