<div align="center">
  <h1>Omarchy psX</h1>
  <p><strong>Omarchy, coming to PlayStation.</strong></p>
  <p>PS4 &middot; PS5 &middot; Future PlayStation consoles</p>
  <p>
    <a href="https://github.com/meerzulee/linux-psx">Powered by Linux psX</a>
    &middot;
    <a href="https://github.com/omacom/omarchy">Upstream Omarchy</a>
    &middot;
    <a href="https://github.com/meerzulee/omarchy-psx/issues">Ideas &amp; contributions</a>
  </p>
</div>

## The goal

We're bringing [Omarchy](https://github.com/omacom/omarchy) to
**PlayStation 4 and PlayStation 5**, with the long-term ambition of supporting
upcoming PlayStation consoles.

Omarchy psX brings our existing PS4 port and future console ports into one
distribution project: a shared desktop experience, with installation, boot and
hardware integration tailored to each console.

## Powered by Linux psX

**Our kernel foundation is
[Linux psX](https://github.com/meerzulee/linux-psx).**

Linux psX owns the console kernel patches, configurations, hardware enablement
and kernel builds. Omarchy psX will use those kernels and focus on the
distribution around them:

- Package profiles and system configuration.
- Desktop integration and console-specific defaults.
- Installation, first boot and recovery.
- Updates, release images and compatibility documentation.

Each console will use its own selected Linux psX kernel and matching modules.

## Console roadmap

| Console | Project status |
| --- | --- |
| **PlayStation 4** | Existing distribution source, pending Ethernet/partitioned-USB work and curated research migrated under `platforms/ps4/`. New psX boot sets require validation. |
| **PlayStation 5** | Planned port, using the Linux psX kernel foundation. |
| **Future PlayStation consoles** | Long-term exploration as hardware access and public research become available. |

## Start development

With Git and Python 3.10+ installed:

```sh
git clone https://github.com/meerzulee/omarchy-psx.git
cd omarchy-psx
./scripts/setup-workspace
make check
```

Setup obtains pinned sibling `linux-psx` and `ps4-uart` sources while preserving
existing work. Read [development hosts](docs/DEVELOPMENT-HOSTS.md) for
**macOS ARM64 with OrbStack** and **Linux x86-64 with native kernel builds**.
Full distribution image wrappers currently use the Mac/OrbStack host.

## Source map

| Location | Contents |
| --- | --- |
| [`platforms/ps4/`](platforms/ps4/README.md) | Complete imported PS4 distribution source: packages, profiles, rootfs, launcher/FPKG, installers, recovery tools and tests. |
| [`platforms/ps4/knowledge/`](platforms/ps4/knowledge/README.md) | Curated research and source references. |
| [`platforms/ps4/experiments/`](platforms/ps4/experiments/README.md) | Historical experiment ledger, with private identifiers redacted and raw captures excluded. |
| [`platforms/ps5/`](platforms/ps5/README.md) | Planned PS5 boundary and prerequisites. |
| [`docs/USING-LINUX-PSX.md`](docs/USING-LINUX-PSX.md) | Whole matching kernel/modules, optional boot profile and manual Ethernet adapter. |
| [`docs/INITRAMFS.md`](docs/INITRAMFS.md) | Existing BusyBox initramfs preservation and source reconstruction. |
| [`docs/MIGRATION.md`](docs/MIGRATION.md) | What moved, historical compatibility interfaces and remaining qualification. |
| [`manifests/`](manifests/development-sources.json) | Full source commit pins and external boot-input identities. |
| [`provenance/ps4-worktree-import.json`](provenance/ps4-worktree-import.json) | Per-file source/destination hashes, pending source and deliberate exclusions. |

The old `omarchy-ps4` checkout is preserved as history. Existing PS4 package
names, services, labels and exact-hash boot profiles remain compatibility
interfaces; a repository move does not change the installed system.

This is a **source migration**, not a new turnkey image or release. Historical
hardware results retain their original scope. New Linux psX boot sets and
unattended Ethernet startup need separate validation. PS5 and future-console
implementation remain planned.

## License

Original Omarchy psX code and documentation use the [MIT License](LICENSE).
The [Linux psX](https://github.com/meerzulee/linux-psx) kernel work remains
GPLv2, with existing per-file licenses preserved. Other bundled components
retain their own licenses and copyright notices.

---

Want to help with development, testing or documentation?
[Join the work](https://github.com/meerzulee/omarchy-psx/issues).
