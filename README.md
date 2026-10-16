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
| **PlayStation 4** | Existing Omarchy PS4 port; integration into psX is planned. |
| **PlayStation 5** | Planned port, using the Linux psX kernel foundation. |
| **Future PlayStation consoles** | Long-term exploration as hardware access and public research become available. |

## Road ahead

1. Bring the existing PS4 distribution work into psX.
2. Integrate and validate a PS5 kernel and boot path.
3. Share distribution components while keeping console differences explicit.
4. Publish reproducible builds, installation guides and hardware test results.

## Current stage

**Project setup and documentation.** The existing
[Omarchy PS4 project](https://github.com/meerzulee/omarchy-ps4) remains the home
of the current PS4 implementation while integration is prepared.

Source, build instructions and releases will be added here as the work lands.
PS5 and future-console support are planned.

---

Want to help with development, testing or documentation?
[Join the work](https://github.com/meerzulee/omarchy-psx/issues).
