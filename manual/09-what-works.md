# What Works

Here's the honest list, as of 2026-10-20. Everything below was observed on **one PS4 Slim with a Baikal B1 southbridge**, on specific recorded builds. It's what we've seen, not a promise for your console. [Linux psX's PS4 compatibility record](https://github.com/meerzulee/linux-psx/blob/master/platforms/ps4/README.md#hardware-compatibility) documents the kernel baseline. This chapter also identifies later, build-specific desktop observations; always check the build and experiment scope before comparing results.

## Observed on recorded boot sets

- **CPU and memory.** All eight cores come online, and about 6.8 GiB of RAM is usable with the tested VRAM setting.
- **Booting from USB.** The whole system runs from the external USB drive.
- **USB keyboard and mouse.**
- **HDMI at 1920×1080, 60 Hz.**
- **Wi-Fi.** Association, DHCP, SSH, DNS and HTTPS all worked. With Linux psX kernels, the firmware has to be in the initramfs; see [Kernels and Firmware](08-kernels-and-firmware.md#wi-fi-and-bluetooth-firmware).
- **Temperatures.** The CPU temperature sensor gives believable readings.
- **Boot logs over UART**, for anyone debugging with a serial adapter.

## Working, with limits

- **Accelerated graphics.** OpenGL 4.6 and Vulkan 1.3 rendered short tests. Long sessions, GPU resets and video codecs aren't qualified.
- **Built-in Ethernet.** Works on Linux psX kernels and passed two boots, including unplugging and replugging the cable. Repeated cold boots, other consoles and strict administrative up/down tests aren't qualified. See [Networking](06-networking.md#ethernet).
- **Bluetooth.** The controller comes up, and one Bluetooth speaker connected and played stereo audio on a Linux 7.2 development kernel. Reconnecting, staying paired across reboots and DualShock controllers are unverified.
- **HDMI audio.** The device and audio stream show up, but no sound came out in the recorded test.
- **Chromium.** Works with software rendering; its GPU path draws corrupted tiles. See [What's Different on PS4](05-whats-different-on-ps4.md#chromium-uses-software-rendering).
- **Ultrawide.** A 3440×1440 test kernel exists, but it isn't qualified.

## Not working yet

- **Fan control.** Linux has no way to read or set the fan.
- **Suspend and resume.** Not available.
- **Night light.** It blacked out the display, so it's switched off.
- **Hardware video decoding in the standard image.** Not enabled or supported. A separate [experimental Mesa/UVD stack](https://github.com/meerzulee/omarchy-psx/tree/master/platforms/ps4/experiments/mesa-uvd#recorded-hardware-results) passed exact AVC decoding and a bounded 1080p30 loop on one Liverpool boot; seeking and broader qualification remain open.
- **The internal drive.** Linux sees it, but reads time out and fail. It's disabled in the boot profile, and installing to it isn't supported.

## Not tested

- **Shutdown and reboot**, as a formal repeated test. In practice, restarting from Linux returns you to the PS4 system.
- **DualShock 4** controllers, over USB or Bluetooth.
- **Screen recording, printing, Docker and gaming.** None of it has passed a PS4 test, even where the software is installed.
- **Any other console**: other Baikal revisions, Aeolia and Belize consoles, and the PS4 Pro. The PS5 port is planned.

## How something moves up this list

Nothing becomes "working" because a package installs, a build compiles or a log looks clean. It takes a recorded hardware experiment on a real console, with a clear pass condition and a way back. If you want to help, read [Contributing](14-contributing.md).

<!-- manual-navigation -->

---

[← Previous](08-kernels-and-firmware.md) · [Contents](README.md) · [Next →](10-recovery.md)
