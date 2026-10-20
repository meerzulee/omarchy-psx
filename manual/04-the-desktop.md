# The Desktop

What you get after first boot is Omarchy 4.0.0 (Quattro), pinned to an exact upstream commit: Hyprland under UWSM, the Quickshell bar and menus, Foot as the terminal and Neovim as the editor. All 22 Quattro themes ship on the drive, and Tokyo Night with its wallpaper is the default.

## Hotkeys and navigation are upstream's

Everything you'd do on a regular Omarchy machine works the same way here, from `Super + Enter` for a terminal to the Omarchy menu. Learn them from the upstream manual, as of the Omarchy commit this port is built from:

- [Navigation](https://github.com/omacom/omarchy/blob/f0020448ca87329199de7cb12f2015ebc4a3e5e7/manual/04-navigation.md)
- [The top bar](https://github.com/omacom/omarchy/blob/f0020448ca87329199de7cb12f2015ebc4a3e5e7/manual/05-the-top-bar.md)
- [Themes](https://github.com/omacom/omarchy/blob/f0020448ca87329199de7cb12f2015ebc4a3e5e7/manual/06-themes.md)
- [Hotkeys](https://github.com/omacom/omarchy/blob/f0020448ca87329199de7cb12f2015ebc4a3e5e7/manual/07-hotkeys.md)

Where the PS4 can't do something safely, the command or menu entry is switched off and tells you why. That's [What's Different on PS4](05-whats-different-on-ps4.md).

## One display mode: 1080p at 60 Hz

The PS4's HDMI output goes through a bridge chip, and the tested path is a fixed 1920×1080 at 60 Hz on `HDMI-A-1`, at scale 1. Other scales haven't been tested, and VRR/FreeSync stays off. The text preset is a readable 14 px, while the bar keeps its fixed geometry so its icons render cleanly.

An experimental 3440×1440 at 50 Hz ultrawide mode exists, but only with its own separately built test kernel. It hasn't been qualified, so treat it as a lab experiment.

## Lighter on the GPU

The PS4 GPU's display engine is old (AMD DCE 8), so the look is tuned to keep it happy:

- Window animations are off.
- Menu cards have no border, because that border renders broken on this display engine.
- `AMD_DEBUG=notiling` is set for the whole session to avoid tiled-buffer corruption.

Everything still looks like Omarchy. It just doesn't swoosh.

## The bar

The bar sits at the top with the Omarchy menu and workspaces on the left; indicators, the clock, keyboard layout and weather in the middle; and the tray, agents, network, Bluetooth and audio on the right. Battery, idle, monitor control, night light and power widgets are turned off: the PS4 has no battery, and the rest haven't passed their hardware tests.

The idle service is off too, so the screen won't blank or lock by itself after a few minutes. You can still lock the screen yourself any time.

## The PS4 menu

Open the Omarchy menu and you'll find a **PS4** section with _Compatibility status_. It runs `omarchy-ps4-status`, a quick report on the kernel, display, OpenGL, network, audio, Vulkan, video decoding, suspend, night light, internal storage and updates. It's the first thing to check when something seems off.

## Apps

You get the regular Omarchy apps, with a few swaps:

- **Files** opens Thunar instead of Nautilus. Nautilus pulls in disk services that probe the PS4's internal drive.
- **Chromium** uses software rendering, because its GPU path draws dark rectangles over pages on the PS4. Every other app keeps the GPU. More in [What's Different on PS4](05-whats-different-on-ps4.md#chromium-uses-software-rendering).

Installed doesn't always mean supported. Audio, screen recording, printing, Docker and gaming remain unqualified. A separate experimental stack has passed scoped H.264 hardware decoding and a bounded 1080p30 loop; it is not enabled or supported in the standard image. See [What Works](09-what-works.md).

## A recovery desktop, just in case

The image also carries an XFCE desktop as a recovery session, with a conservative display setup that has hardware acceleration switched off. It's there for when something in the Omarchy session goes wrong, not for daily use.

<!-- manual-navigation -->

---

[← Previous](03-first-boot.md) · [Contents](README.md) · [Next →](05-whats-different-on-ps4.md)
