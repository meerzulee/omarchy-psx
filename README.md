<div align="center">
  <h1>Omarchy psX</h1>
  <p><strong>Omarchy, coming to PlayStation.</strong></p>
  <p>PS4 &middot; PS5 &middot; Future PlayStation consoles</p>
  <p>
    <a href="manual/README.md">The manual</a>
    &middot;
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
| **PlayStation 4** | Existing distribution source, pending partitioned-USB work and curated research migrated under `platforms/ps4/`. Linux psX `6.18.44-psx-ps4-baikal2` adds native Baikal Ethernet. New psX boot sets require validation. |
| **PlayStation 5** | Planned port, using the Linux psX kernel foundation. |
| **Future PlayStation consoles** | Long-term exploration as hardware access and public research become available. |

## Experimental PS4 graphics and video

A process-local Mesa 26.2.5 candidate with PS4 graphics setup displayed clean
OpenGL reference pixels and worked with the experimental Liverpool UVD kernel.
The 1080p30 H.264 fractal passed exact decoding and five bounded zero-drop
playback loops. This is a separate engineering experiment, with system-wide
Mesa adoption and release qualification still pending. The normal image and
package profiles have not been switched to it.

See [Mesa source and test tools](platforms/ps4/experiments/mesa-uvd/README.md)
and the [curated experiment ledger](platforms/ps4/experiments/SESSIONS.md).
The kernel transport remains in the sibling Linux psX project.

## USB installation flow

The intended user experience is **Download → Flash → Launch → Setup → Desktop**.
Use one compressed USB image on Windows, macOS or Linux with balenaEtcher,
then connect the USB to the PS4 and start the matching Omarchy launcher. The
image includes its selected Linux psX kernel and matching modules. First boot
is designed to expand the Linux partition into the remaining USB space and
run account setup.

The current local candidate is a **2.29 GB download**, expanding to a **15 GiB
image** when flashed. A matching public launcher and PS4 validation are still
pending. Follow [Getting Started](manual/02-getting-started.md) for the complete
flow, drive preparation and current test scope.

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

## Web documentation

The documentation website follows the upstream Omarchy manual's chapter layout.
Its fifteen chapters live in [`manual/`](manual/README.md); [`website/`](website/README.md)
builds them into a static site with search, chapter navigation and a mobile menu.

With Node.js 22 or newer:

```sh
cd website
npm ci
npm run dev
```

The command prints a local preview URL. From the same directory, `npm run build`
writes the static site to `website/dist/` (relative to the repository root).
See the [website guide](website/README.md) for hosting under a path. Builds and previews do not publish anything.

## Source map

| Location | Contents |
| --- | --- |
| [`manual/`](manual/README.md) | The Omarchy psX manual: getting started, first boot, the desktop, networking, storage, recovery, troubleshooting, FAQ and the legal notice. |
| [`website/`](website/README.md) | Static web documentation generated from the manual. |
| [`platforms/ps4/`](platforms/ps4/README.md) | Complete imported PS4 distribution source: packages, profiles, rootfs, launcher/FPKG, installers, recovery tools and tests. |
| [`platforms/ps4/docs/`](platforms/ps4/docs/) | PS4 build, desktop, compatibility and recovery guides; dated records retain their historical scope. |
| [`platforms/ps4/experiments/`](platforms/ps4/experiments/README.md) | Historical experiment ledger, with private identifiers redacted and raw captures excluded. |
| [`platforms/ps5/`](platforms/ps5/README.md) | PS5 development image builder, shared console packages and boot prerequisites. |
| [`docs/UNIVERSAL-IMAGE.md`](docs/UNIVERSAL-IMAGE.md) | Shared rootfs design and remaining work for PS4/PS5 media. |
| [`docs/USING-LINUX-PSX.md`](docs/USING-LINUX-PSX.md) | Whole matching kernel/modules, optional boot profile and native Ethernet. |
| [`docs/INITRAMFS.md`](docs/INITRAMFS.md) | Existing BusyBox initramfs preservation, source reconstruction and Wi-Fi/Bluetooth firmware download. |
| [`docs/MIGRATION.md`](docs/MIGRATION.md) | What moved, historical compatibility interfaces and remaining qualification. |
| [`manifests/`](manifests/development-sources.json) | Full source commit pins and external boot-input identities. |
| [`provenance/ps4-worktree-import.json`](provenance/ps4-worktree-import.json) | Per-file source/destination hashes, pending source and deliberate exclusions. |

The old `omarchy-ps4` checkout is preserved as history. Existing PS4 package
names, services, labels and exact-hash boot profiles remain compatibility
interfaces; a repository move does not change the installed system.

The migrated source and native PS5 development builder do not establish a
turnkey release. Historical hardware results retain their original scope.
New Linux psX boot sets need separate validation; native PS4 Ethernet passed
two boots of its tested build. The PS5 desktop image and a combined PS4/PS5
image have no console acceptance. Future-console implementation remains planned.

## Legal

Omarchy psX is an independent community project. It is not affiliated with,
authorized, sponsored or endorsed by Sony Interactive Entertainment, and it is
not made or endorsed by the Omarchy project. "PlayStation", "PS4" and "PS5" are
trademarks of Sony Interactive Entertainment Inc., used only to identify the
hardware this software runs on.

The [manual](manual/README.md) begins with an established console Linux boot
environment and covers the distribution from that point. Reviewed findings
from private background work are described as private hardware research.
Device firmware and generated boot archives remain external build inputs.
See the [legal notice](manual/15-legal-notice.md) for licenses and attribution.

## License

Original Omarchy psX code and documentation use the [MIT License](LICENSE).
The [Linux psX](https://github.com/meerzulee/linux-psx) kernel work remains
GPLv2, with existing per-file licenses preserved. Other bundled components
retain their own licenses and copyright notices.

---

Want to help with development, testing or documentation?
[Join the work](https://github.com/meerzulee/omarchy-psx/issues).
