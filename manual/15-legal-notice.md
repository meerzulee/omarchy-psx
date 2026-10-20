# Legal Notice

Omarchy psX is an independent community port. It is not affiliated with or endorsed by Sony Interactive Entertainment or the upstream Omarchy project. Console and project names identify the hardware and software discussed in this manual.

## Scope of this manual

The manual covers the Linux system: builds, external storage, desktop integration, hardware observations and recovery. It begins with an established console Linux boot environment.

Public hardware notes summarize reviewed findings. Where background work is private, it is described as **private hardware research**, without private repository links, tool names, dumps or access details.

## Licenses and attribution

| Component | License and source record |
| --- | --- |
| Original Omarchy psX code and documentation | [MIT License](../LICENSE). |
| Linux psX kernel work | GPLv2, with existing per-file notices preserved. See [kernel credits](https://github.com/meerzulee/linux-psx/blob/master/CREDITS.md). |
| Upstream Omarchy | Its upstream license and notices remain in effect; the selected source is pinned in [omarchy.lock](../platforms/ps4/upstream/omarchy.lock). |
| Website wordmark | Adapted from Omarchy's SVG logo and its Delta Corps Priest 1 lettering. The [upstream MIT notice](../website/assets/LICENSE-omarchy.txt) is retained; see the [branding source record](../website/BRANDING.md). |
| Launcher and third-party inputs | [Launcher credits](../platforms/ps4/fpkg/CREDITS.md) and [third-party notes](../platforms/ps4/fpkg/THIRD_PARTY.md). |
| Arch Linux packages | Each package retains its own license and notices. |

Public kernel binaries must be accompanied by complete corresponding source and the required notices. The [Linux psX artifact guide](https://github.com/meerzulee/linux-psx/blob/master/docs/ARTIFACTS.md) describes how source and runtime downloads are tied together.

## External inputs

Device firmware and generated boot archives are external build inputs, kept outside Git. The selected Linux psX kernels embed no device firmware. Some drivers need separately supplied firmware in the initramfs; see [Kernels and Firmware](08-kernels-and-firmware.md).

A public download location does not by itself establish redistribution permission. Follow the recorded license status for each input before sharing an assembled artifact.

## Development status

The project is provided under its license's warranty terms. Hardware observations apply to the recorded console and exact boot set. Keep personal backups and a complete recovery set before testing a different build.

Questions about source attribution or included material can be raised with the [maintainer](https://github.com/meerzulee) or in the [issue tracker](https://github.com/meerzulee/omarchy-psx/issues).

<!-- manual-navigation -->

---

[← Previous](14-contributing.md) · [Contents](README.md)
