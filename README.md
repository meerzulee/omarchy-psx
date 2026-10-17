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

Omarchy psX will bring our existing PS4 port and future console ports into one
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
| **PlayStation 4** | Existing PS4 port; source handoff and experimental integration scaffolding now live here. |
| **PlayStation 5** | Planned port, using the Linux psX kernel foundation. |
| **Future PlayStation consoles** | Long-term exploration as hardware access and public research become available. |

## Road ahead

1. Bring the existing PS4 distribution work into psX.
2. Integrate and validate a PS5 kernel and boot path.
3. Share distribution components while keeping console differences explicit.
4. Publish reproducible builds, installation guides and hardware test results.

## Current stage

**Integration scaffolding.** This repository now holds a pinned kernel-source
handoff, host setup guidance, the existing Omarchy `/init` source and portable
data-only initramfs repacker, an optional USB boot profile and a manually invoked
experimental Ethernet adapter. Linux psX owns the kernel
and its distribution-independent build/artifact contract; Omarchy-specific
setup stays here.

Read [Using Linux psX with Omarchy](docs/USING-LINUX-PSX.md) for Mac ARM64
(OrbStack), Linux x86-64 native builds, whole matching modules and recovery.
The [handoff manifest](manifests/kernel-source.json) pins the published kernel
migration commit `b9bcf7234dff601ce41e141ca1403ea0a4525c1a`.
The [initramfs guide](docs/INITRAMFS.md) identifies the exact BusyBox archive,
external base requirement and Mac/Linux generation command. Its source import
is recorded in [initramfs provenance](provenance/initramfs-import.json).
[Integration provenance](provenance/integration-import.json) records the exact
source paths, hashes, adaptations and preserved notices for imported helpers
and the optional boot-profile example.

This is not a turnkey OS installer or a complete migration of the existing
[Omarchy PS4 implementation](https://github.com/meerzulee/omarchy-ps4).
No new Linux psX binary release or hardware acceptance is implied. PS5 and
future-console support remain planned.

## License

Original Omarchy psX code and documentation use the [MIT License](LICENSE).
The [Linux psX](https://github.com/meerzulee/linux-psx) kernel work remains
GPLv2, with existing per-file licenses preserved. Other bundled components
retain their own licenses and copyright notices.

---

Want to help with development, testing or documentation?
[Join the work](https://github.com/meerzulee/omarchy-psx/issues).
