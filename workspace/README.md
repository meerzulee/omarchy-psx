# psX Linux development workspace

This portable file is installed at the workspace root by `scripts/setup-workspace`;
relative links refer to that installed location. Keep the projects as siblings:

```text
psx/
  linux-psx/       # kernel patches, builds, modules and generic hardware evidence
  omarchy-psx/     # distribution; existing PS4 implementation under platforms/ps4
  ps4-uart/       # continuous capture and bounded experiment sessions
  payloads/       # optional locally acquired inputs
  backups/        # private recovery copies
  lab/            # private research and receipts
```

With Git and Python 3.10+ installed, start on another computer:

```sh
mkdir -p "$HOME/Work/psx"
cd "$HOME/Work/psx"
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
./scripts/setup-workspace
./scripts/setup-workspace --check
make check
```

The helper creates missing kernel/UART clones at recorded full commit pins,
verifies existing origins and pinned ancestry, and copies only missing
workspace instructions. Existing commits, dirty files and customized
instructions are preserved. The source map is
[`omarchy-psx/manifests/development-sources.json`](omarchy-psx/manifests/development-sources.json).

Read each project's `AGENTS.md` and the
[`development host guide`](omarchy-psx/docs/DEVELOPMENT-HOSTS.md).
On **macOS ARM64**, use OrbStack (`orb status`: `Running`; Docker context:
`orbstack`) and the kernel's `scripts/build-kernel-orbstack` helper. On
**Linux x86-64**, compile the kernel natively with
`make TARGET=6.18-ps4-baikal`; no VM is required. Full Omarchy image wrappers
still use the Mac/OrbStack build host. Python source/repack and C/C++ fixture
checks run on both hosts.

Kernel upstream is fetched by its builder. In `omarchy-psx`, use
`scripts/sync-omarchy-upstream`, `scripts/fetch-ps4-loader` and
`scripts/fetch-ps4-initramfs-seed` for recorded public inputs. Generated
images/PKGs/modules and firmware are external artifacts; preserve matching
identities and recovery sets. No private source archive or old source checkout
is required for development setup.

PS4 migration and current versus historical boot paths are described in
[`MIGRATION.md`](omarchy-psx/docs/MIGRATION.md). Curated PS4 evidence lives in
[`SESSIONS.md`](omarchy-psx/platforms/ps4/experiments/SESSIONS.md). PS5 remains
a planned port; successful source/build checks do not qualify new hardware.

The old `linux-ps4-kernel`, `omarchy-ps4`, `linux-ps4` and `linux-ps4-git`
checkouts are preserved historical references. Use the psX repositories for
new development. Recreate UART virtual environments and capture state on each
host; do not migrate active PID, lock or session files. Raw captures, keys,
console firmware and recovery data remain private.

Project URLs:

https://github.com/meerzulee/linux-psx

https://github.com/meerzulee/omarchy-psx

https://github.com/meerzulee/ps4-uart
