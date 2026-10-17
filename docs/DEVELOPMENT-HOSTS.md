# Develop on macOS ARM64 or Linux x86-64

Keep `omarchy-psx`, `linux-psx` and `ps4-uart` as siblings. Linux x86 here
means **x86-64** (`uname -m` must report `x86_64`). The console target remains
x86-64 regardless of the development computer's architecture.

## Start on another computer

Install Git and Python 3.10+, then:

```sh
mkdir -p "$HOME/Work/psx"
cd "$HOME/Work/psx"
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
./scripts/setup-workspace
./scripts/setup-workspace --check
```

The helper creates missing sibling checkouts at the full commits in
[`development-sources.json`](../manifests/development-sources.json). Existing
origins and pinned ancestry are checked before anything is created. Existing
branches, commits, dirty work and workspace instructions are preserved. An
incompatible checkout stops setup; `--check` is offline and read-only. New
clones start detached at their pins: create a development branch when ready.
The older `setup-kernel-workspace` is an exact-snapshot helper; the broader
`setup-workspace` also accepts newer development history containing the pin.

Read each repository's `AGENTS.md`. The old `linux-ps4-kernel` and
`omarchy-ps4` directories are historical references; they are not source
dependencies of the new workspace.

## Host capabilities

| Work | macOS ARM64 | Arch Linux x86-64 |
| --- | --- | --- |
| Source, Python checks and C/C++ fixture tests | Native | Native |
| Linux psX kernel | OrbStack ARM64 builder with x86-64 cross compiler | Native kernel build |
| Exact existing initramfs repack | Native Python | Native Python |
| Full Omarchy package/rootfs/initramfs/image builds | Migrated OrbStack wrappers | Use the Mac host; native image-builder port is pending |
| FPKG UI/transaction host tests | Native C++ | Native C++ |
| Complete OpenOrbis FPKG | Existing macOS path and external pinned inputs | Source path present; Linux packaging remains unqualified |
| UART | Explicit adapter or macOS discovery | Explicit stable serial path; qualify the adapter separately |

On macOS, install Xcode command-line tools and the host utilities:

```sh
xcode-select --install
brew install git bash python coreutils zstd xz ripgrep imagemagick llvm lld@20
orb status
docker context show
```

Before Docker work these must report `Running` and `orbstack`. Use OrbStack
exclusively for local containers/VMs. Do not run kernel compilation directly
on Darwin. Build from the sibling kernel checkout:

```sh
cd ../linux-psx
make check
./scripts/build-kernel-orbstack -t 6.18-ps4-baikal
```

On Arch, install native source/test/build dependencies. This updates the host;
it does not install the console kernel on the PC:

```sh
sudo pacman -Syu --needed base-devel git curl bc cpio pahole libelf openssl \
  kmod perl python python-pip rsync xz zstd ripgrep clang lld imagemagick
export PATH="/usr/bin/core_perl:$PATH"
cd ../linux-psx
make check
make TARGET=6.18-ps4-baikal
```

For other Linux distributions use the dependencies in the kernel build guide.
Native kernel builds need no VM. Their compiler may differ from the pinned
container compiler: preserve the produced manifest and whole matching modules.

## Inputs come from recorded sources

| Input | Source / acquisition |
| --- | --- |
| Kernel patches, configs, builder | Pinned sibling `linux-psx`, obtained by `setup-workspace` |
| Full upstream Linux | Fetched and commit-checked by the kernel builder |
| UART | Pinned sibling `ps4-uart`, obtained by `setup-workspace` |
| Omarchy source and logo | `./scripts/sync-omarchy-upstream`; platform `upstream/omarchy.lock` |
| Arch/Omarchy packages | Platform snapshot/build recipes and pinned package-source commit |
| PS4 loader | `./scripts/fetch-ps4-loader`; ZIP/member size and SHA checks in the development manifest |
| Original public initramfs seed | `./scripts/fetch-ps4-initramfs-seed`; immutable URL, size and SHA in its seed manifest |
| OpenOrbis SDK | Platform `fpkg/tools/build-ui-prototype`, pinned archive/digest |
| Rootfs, modules, complete boot sets | Build outputs or explicitly supplied matching historical artifacts; not source clones |
| Raw logs, keys and per-console firmware/recovery state | Private local inputs; not published source dependencies |

Acquisition downloads local inputs only. It does not flash storage or launch
anything on the PS4. The original public seed differs from the generated base
required by the exact historical repacker; see [INITRAMFS.md](INITRAMFS.md).

## Work on the distribution

Run host checks at the new root:

```sh
cd ../omarchy-psx
make check
```

The complete imported PS4 implementation has its own repository-local layout:

```sh
cd platforms/ps4
./scripts/sync-omarchy-upstream
# Read docs/BUILDING.md and the migration/input notes before image/FPKG builds.
make -C fpkg/ui-prototype host-test
```

Existing PS4 package names, services, boot labels and exact-hash FPKG profiles
remain compatibility interfaces. Historical profiles identify old artifacts;
they must not silently select a newly built psX kernel. See
[MIGRATION.md](MIGRATION.md) for current versus historical entry points.

## Recreate UART state

```sh
cd ../../../ps4-uart  # from omarchy-psx/platforms/ps4
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```

On Linux list `/dev/serial/by-id/` and choose the real adapter explicitly with
`./uart start --port /dev/serial/by-id/YOUR_ADAPTER`. On macOS use `./uart start`
or an explicit `/dev/cu.*` device. Resolve access through the adapter's owning
group rather than running capture as root. Do not copy PID, lock, port-pointer
or active-session files. A new device connection requires a new session.

The curated PS4 ledger is
[`platforms/ps4/experiments/SESSIONS.md`](../platforms/ps4/experiments/SESSIONS.md).
Source tests are not hardware acceptance. The new kernel/initramfs pairing
and PS5 port still require separate validation.
