# Omarchy PS4 contributor rules

## Product standard

- Treat this as a real distribution project, not a demo or a collection of
  one-off shell snippets.
- Prefer small, inspectable tools with clear inputs, progress, errors, and
  recovery instructions.
- Never claim hardware or software support without a recorded real-hardware
  test result.
- Do not hide uncertainty. Use the compatibility states defined in
  `docs/COMPATIBILITY.md`.
- Keep the known-good XFCE installation bootable while testing later layers.

## Test discipline

- Follow [`docs/DEVELOPMENT-MODE.md`](docs/DEVELOPMENT-MODE.md) for consequential
  PS4 hardware experiments. Keep continuous UART, but use one bounded session
  for a coherent objective rather than one session per operator action.
- Change one diagnostic variable per hardware experiment; group its necessary
  setup, observation, and cleanup steps.
- Record the console model, southbridge, firmware, kernel, package versions,
  commands, result, and relevant logs for acceptance or failure investigations,
  not for routine navigation with no diagnostic value.
- A failed experiment must have a documented rollback path.
- Do not promote a component to the root filesystem until its individual gate
  passes.
- Close the active entry in [`experiments/SESSIONS.md`](experiments/SESSIONS.md)
  before starting a different diagnostic branch.

## Agent collaboration

- Additional agents may perform bounded advice, independent audit, research,
  tests, or implementation work.
- Delegated conclusions must be verified by the primary agent. Agent agreement
  is not hardware evidence.
- Spawning an agent does not authorize console actions, destructive storage
  operations, public pushes/releases, or Git history rewrites.

## Local infrastructure and repository migration

- The active repository is `omarchy-psx`; this directory owns its PS4 platform.
  Read the root `AGENTS.md`, `README.md` and `docs/MIGRATION.md` first.
- Run setup from root `scripts/setup-workspace`; the platform wrapper delegates
  there. Root `manifests/development-sources.json` owns sibling pins and loader
  acquisition. Do not require an old `omarchy-ps4` or `linux-ps4-kernel` clone.
- Local package/profile paths resolve from this platform directory. Workspace
  siblings are three parents above this directory (`../../../linux-psx`,
  `../../../ps4-uart`), not siblings of the nested platform.
- macOS ARM64 uses OrbStack only. Before Docker work verify `orb status` is
  `Running` and `docker context show` is `orbstack`. Never start another runtime.
- Linux x86-64 kernel builds/source checks are native. The imported distro image
  wrappers still require the Mac OrbStack host; porting them needs separate work.
- Frozen FPKG profiles are historical exact-hash fixtures, not profiles for the
  new firmware-free Linux psX kernel. Preserve their hashes and require explicit
  historical input files. Do not relabel a new kernel as an accepted old build.
- Keep historical experiment qualifications, exclusions and local-only data
  boundaries visible. Raw UART captures, credentials, firmware and PKGs stay out
  of Git. Private debug provisioning requires an operator-supplied private config.
- Preserve local commits and uncommitted work during handoff. Recreate virtual
  environments; do not transfer active UART locks/PIDs/session state.
- Include full URLs for terminal links and absolute local artifact paths when useful.

## Safety

- Never assume a disk device name such as `/dev/sda` or `/dev/sdb`.
- Disk-writing tools must identify the target by stable metadata, show the
  resolved device, and require explicit confirmation.
- Do not ship default passwords or enable remote password login in release
  images.
- Keep downloaded artifacts out of Git. Track their source, version, size, and
  digest instead.

## Source policy

- Pin upstream commits used by builds and compatibility tests.
- Prefer upstream packages and patches when they work on PS4.
- Create a PS4-specific package or implementation only after a recorded test
  demonstrates that the upstream solution is missing or incompatible.
- Preserve license and source provenance for kernels, firmware handling,
  loaders, and patched packages.
