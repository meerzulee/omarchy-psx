# Building from Source

The source tree can build the parts of an Omarchy USB system. This is a development workflow: it involves several gigabytes of downloads, Linux containers for full image assembly, and explicit matching of kernel, modules, initramfs and launcher profiles.

## Pick a host

- **macOS on Apple silicon** with [OrbStack](https://orbstack.dev/). This is the host for the full Omarchy image builders today.
- **Linux on x86-64.** Kernel builds, source work and tests run natively, but the full image wrappers still expect the Mac/OrbStack host.

On macOS, use OrbStack and nothing else for containers: check that `orb status` says `Running` and `docker context show` says `orbstack`. Never build the kernel directly on macOS; use the kernel repository's OrbStack helper. The full setup is in [Development hosts](../docs/DEVELOPMENT-HOSTS.md).

## Set up the workspace

With Git and Python 3.10 or newer:

```bash
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
./scripts/setup-workspace
./scripts/setup-workspace --check
make check
```

`setup-workspace` clones the sibling `linux-psx` and `ps4-uart` repositories at the exact commits pinned in `manifests/development-sources.json`. It never resets, rebases or discards existing work. `make check` runs the host tests; they're synthetic and never touch a device.

## Build the kernel

From the sibling `linux-psx` checkout:

```bash
# macOS on Apple silicon
./scripts/build-kernel-orbstack -t 6.18-ps4-baikal

# Linux x86-64
make TARGET=6.18-ps4-baikal
```

The builder fetches upstream Linux at a pinned commit and applies the PS4 patches in order. Keep the whole output together: kernel, complete modules archive, config and checksums. See [Linux psX's build guide](https://github.com/meerzulee/linux-psx/blob/master/docs/BUILDING.md).

## Build the initramfs

The initramfs finds and checks the USB root, draws the splash and switches into Omarchy. [The initramfs guide](../docs/INITRAMFS.md) covers the exact repack of the existing archive, the full source rebuild and adding the Wi-Fi and Bluetooth firmware.

## Build the system

The PS4 platform keeps the complete distribution build under `platforms/ps4/`. The sequence, in [the PS4 build guide](../platforms/ps4/docs/BUILDING.md), goes:

1. Sync the pinned Omarchy source.
2. Build the matching kernel and modules.
3. Build the PS4 initramfs.
4. Check the PS4-safe package profile.
5. Build the Omarchy PS4 packages.
6. Resolve a complete offline package snapshot.
7. Compose the owner-ready root filesystem.
8. Build the flashable USB image.
9. Stage the launcher's boot set.
10. Build and audit the launcher.
11. Assemble and verify a release directory.

That guide is a historical build reference. Read [the migration guide](../docs/MIGRATION.md), [Using Linux psX](../docs/USING-LINUX-PSX.md), and [the initramfs guide](../docs/INITRAMFS.md) before adapting its commands. A freshly built psX kernel is not a replacement input for a frozen v0.31 launcher profile: its hashes, boot pairing and qualification differ.

For a flashable two-partition candidate, use the new [USB image builder](../docs/USB-IMAGES.md). It measures the rootfs, creates FAT32 and ext4 in regular files, verifies the assembled image and reports both the raw flash size and compressed download size. Building it does not write a USB device.

The earlier developer layout also has a guarded Linux installer, which previews by default and asks for an explicit wipe confirmation before it touches a drive. See [the partitioned USB guide](../platforms/ps4/docs/USB-PARTITIONED-DEVELOPMENT.md).

## Rules that keep builds honest

- The USB image, release and initramfs repack builders refuse to overwrite an existing output. Give every candidate a new name.
- Generated images, packages, initramfs archives and kernels stay out of Git.
- Never commit, upload or publish firmware. Downloaded firmware lives in the ignored `cache/`, and anything built with it stays on your machine.
- Old launcher profiles pin their exact kernel. A new kernel needs its own boot set and its own hardware test.

_A successful build is not a hardware test. Before you put anything on a console, read [Contributing](14-contributing.md)._

<!-- manual-navigation -->

---

[← Previous](12-faq.md) · [Contents](README.md) · [Next →](14-contributing.md)
