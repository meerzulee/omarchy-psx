# Troubleshooting

Start with _PS4 > Compatibility status_ in the Omarchy menu (or `omarchy-ps4-status` in a terminal). It tells you which kernel is running and what the display, network, audio and storage are doing.

## Why does a command say "Unsupported on Omarchy PS4"?

That command is switched off on purpose, because it's unsafe or meaningless on the PS4. The message tells you why. See [What's Different on PS4](05-whats-different-on-ps4.md).

## Why does the clock say 1970?

The PS4 doesn't give Linux a working hardware clock. Connect to a network, and the time is set automatically.

## Why do I get a login screen instead of the desktop?

Persistent automatic login hasn't passed its reboot test yet. Sign in with your password.

## The screen stays black

Use a display that accepts 1920×1080 at 60 Hz, turn off VRR/FreeSync in its settings, and connect it before you boot. If you're testing a Linux psX kernel, make sure your initramfs carries the display firmware and EDID; see [Kernels and Firmware](08-kernels-and-firmware.md#firmware-lives-in-the-initramfs).

## Wi-Fi doesn't show up with a Linux psX kernel

Those kernels carry no firmware, so the Wi-Fi and Bluetooth firmware has to be added to the initramfs. See [Wi-Fi and Bluetooth firmware](08-kernels-and-firmware.md#wi-fi-and-bluetooth-firmware).

## Ethernet doesn't come up

Check `uname -r` first: built-in Ethernet needs a Linux psX kernel with native Ethernet, and the v0.31 launcher's kernel doesn't have it. Then check that NetworkManager isn't randomizing the wired MAC address, and that nothing on the kernel command line turns the driver off (`psx_mts_net.autoarm=0` or `modprobe.blacklist=psx_mts_net`).

After a terminal driver fault, power the console fully off before the next boot. Don't unload, reload or rearm the driver. The checks to run are in [Networking](06-networking.md#ethernet).

## Chromium shows dark rectangles or corrupted tiles

Chromium should be using software rendering on the PS4. Check, re-enable it if needed, and restart Chromium:

```bash
omarchy-ps4-chromium-software-rendering --check
omarchy-ps4-chromium-software-rendering --enable
```

## An app crashes the moment it starts

The PS4's Jaguar CPU doesn't have AVX2, BMI1, BMI2 or FMA, which programs built for the newer `x86-64-v3` level expect. Such a binary can crash with an illegal instruction even though the kernel and the rest of the system are fine. Use a build for baseline x86-64 instead. That's a property of the particular binary, not of every modern package.

## Where did night light go?

It's off on purpose. Changing the display's color tables blacked out the PS4's HDMI output.

## My USB stick doesn't show up in Files

Nothing mounts drives automatically on the PS4, because the automounter probes the internal drive too. Mount the stick yourself from a terminal.

## There's no sound from my TV

HDMI audio isn't working yet: the audio device appears, but no sound came out in our tests. A Bluetooth speaker has worked once on our test console.

## Boot pauses for a long time

If the internal drive isn't disabled on the kernel command line, Linux tries to read it, and those reads time out. The release boot profile disables it; the debug profile deliberately doesn't. See [Storage](07-storage.md#the-ps4s-internal-drive).

## Owner setup shows an `OWNER-SETUP` screen

Setup hit a problem and stopped safely. Launch Omarchy PS4 and boot again; setup stays pending until it finishes. See [First Boot](03-first-boot.md).

## The PS4 system crashed before Linux started

That happened before Linux started, so it's outside this project. Power the console fully off before you try again. See [Recovery](10-recovery.md#linux-didnt-start).

## Where are the logs?

`journalctl -b` shows the current boot. For problems that happen before the desktop, developers capture the console's UART output; see [Contributing](14-contributing.md). Before you share any log, remove serial numbers, MAC and IP addresses, and anything else that identifies your console.

---

For questions that aren't problems, see the [FAQ](12-faq.md).

<!-- manual-navigation -->

---

[← Previous](10-recovery.md) · [Contents](README.md) · [Next →](12-faq.md)
