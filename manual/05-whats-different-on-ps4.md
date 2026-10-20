# What's Different on PS4

Omarchy psX keeps upstream Omarchy as intact as it can. The differences are the places where the PS4's boot chain, display engine or storage would turn a normal PC feature into a bad day. Instead of pretending those features work, we switch them off and say why.

## Some commands say "Unsupported on Omarchy PS4"

Run one of the guarded commands and you'll get a message instead of an action:

```
Unsupported on Omarchy PS4: omarchy-toggle-nightlight
Reason: the legacy PS4 DCE8 color path can black out HDMI output.
The unmodified upstream script is retained under /usr/lib/omarchy-ps4/upstream-bin for audit.
```

The guarded groups, and why:

| Commands | Why they're off |
| --- | --- |
| Night light and Hyprsunset | Gamma programming on the PS4's display engine blacked out the HDMI output. |
| Limine, Plymouth, system/hardware apply, factory reset, drive password | The PS4 loader and our recovery tools own boot and storage. |
| Hibernation, power profiles, brightness | These power and display operations haven't passed a PS4 hardware safety test, or don't apply to the console. |
| Update channel, migrations, reinstall, `omarchy-update` and friends | Updates have to match the PS4 kernel and graphics stack. |
| Gaming installers for 32-bit GPU libraries and Xbox controllers | They assume stock PC graphics or kernel modules built on the machine. |

The unmodified upstream scripts stay on the system under `/usr/lib/omarchy-ps4/upstream-bin`, so you can read exactly what was switched off. The full list is in [`ps4-disabled-commands.txt`](../platforms/ps4/packages/omarchy-ps4/ps4-disabled-commands.txt).

The Omarchy menu hides the same things: suspend, hibernate, night light, the update channel, firmware updates and drive passwords don't appear.

## Updates come as releases, not rolling

On a PC, Omarchy updates itself and Arch packages roll forward continuously. On a PS4, the kernel, its modules, Mesa and the display path have to be tested together, so there are no rolling Arch updates. A new version arrives as a matching launcher and USB system. Stock Arch kernels are never installed: the PS4 boots its own kernel from the launcher.

## No system snapshots

Upstream Omarchy can roll back with Btrfs snapshots. The PS4 root filesystem is ext4 and the snapshot tools are left out, so there's no rollback inside Linux. Keep copies of anything that matters on another machine.

## No Plymouth boot screen

The PS4 boots through its own loader and initramfs, so instead of Plymouth you get a small framebuffer splash that draws the Omarchy logo while Linux starts.

## Chromium uses software rendering

Chromium's GPU path drew dark rectangular tiles inside pages on the PS4. Turning off Chromium's GPU use made them go away while everything else stayed the same, so Omarchy psX starts Chromium with `--disable-gpu`. The rest of the desktop still uses the GPU.

Check or restore the setting, then restart Chromium:

```bash
omarchy-ps4-chromium-software-rendering --check
omarchy-ps4-chromium-software-rendering --enable
```

Software rendering puts more work on the CPU, so heavy pages and video can feel slower. The details are in [the Chromium notes](../platforms/ps4/docs/CHROMIUM-GPU-COMPATIBILITY.md).

## Drives don't mount automatically

UDisks, udiskie and anything that pulls them in are left out, because probing disks caused I/O errors on the PS4's internal drive. That also means no Nautilus, GNOME Disks, Evince or network shares through GVfs. Files opens Thunar, and USB sticks need to be mounted by hand. The complete list, with a reason for each package, is in [`blocked-packages.txt`](../platforms/ps4/profiles/omarchy-full/blocked-packages.txt).

## LightDM instead of SDDM

The login screen is LightDM, which also keeps the XFCE recovery session available. SDDM stays out.

## No firewall

The PS4 kernels are built without netfilter, so there's no firewall. If you set up SSH with Omarchy's security setup, it stays key-only, but it skips the firewall rule and tells you that the machine doesn't filter network traffic. Firewall and container features that depend on netfilter would need a different, separately tested kernel configuration. Keep the console on a network you trust.

## Check what's working

Run _PS4 > Compatibility status_ from the Omarchy menu, or `omarchy-ps4-status` in a terminal, for a quick report on what this console is doing right now.

<!-- manual-navigation -->

---

[← Previous](04-the-desktop.md) · [Contents](README.md) · [Next →](06-networking.md)
