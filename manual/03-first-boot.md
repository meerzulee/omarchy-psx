# First Boot

An owner-ready image prepares the USB root and runs account setup on its first Linux boot. This chapter describes the current provisioning source; automatic login and network-time persistence still need a repeated boot test on a rebuilt image.

The new partitioned image is designed to grow its Linux partition and ext4 filesystem automatically after checking the target. This growth path still needs a PS4 hardware test. Account setup uses files already on the image and does not need a network connection.

```
Kernel and initramfs start
  → find the drive labelled OMARCHY-PS4
  → check that the USB root matches the selected image layout
  → mount the Omarchy system
  → expand the Linux partition and filesystem into the remaining USB space
  → set up the owner
  → start the Omarchy desktop
```

## Setting up the owner

There's no default user and no default password in the image. On the first boot, a full-screen Omarchy setup asks for:

- your keyboard layout,
- a username and password,
- a hostname,
- your timezone: choose a GMT offset such as **GMT+06:00**, or pick a city/region for daylight-saving rules and half/quarter-hour offsets.

The GMT list covers every whole-hour offset from GMT-12:00 to GMT+14:00. Use Up/Down to scroll beyond the visible rows. A fixed GMT choice stays at that offset throughout the year.

Review the summary, choose _Yes_, and Omarchy creates your account and starts the desktop. Your password is entered in Linux on the console itself. The setup flow is designed to keep it out of diagnostic logs and UART output.

If setup is interrupted, launch Omarchy PS4 and choose _Boot Omarchy_ again; setup stays pending until it has finished, so it simply runs again. If something goes wrong, you'll see an `OWNER-SETUP` support screen instead of an empty login prompt.

## Logging in

After setup, Omarchy takes you straight into the desktop. If you get a login screen instead, sign in with your password; persistent automatic login is still waiting for its reboot test.

_The USB drive isn't encrypted. Anyone with physical access to the console or the drive can reach your desktop. Your password still protects `sudo` and the lock screen, but treat the drive like an unlocked laptop._

## The clock starts in 1970

The PS4 doesn't give Linux a usable hardware clock. So if you boot offline, the date may read 1970 for a while. As soon as the network connects, the clock is set from the internet automatically. Setup never waits for the network and never asks you to type the date.

## SSH stays off

OpenSSH isn't running, and password logins over SSH are disabled. If you want remote access, set it up from the desktop like you would on any Omarchy machine, preferably with keys.

## Every boot after that

```
PS4 system → established launcher environment → Omarchy PS4 → Boot Omarchy
```

The launcher remembers its boot files, so after the first time it's a single button. The desktop is next: [The Desktop](04-the-desktop.md).

<!-- manual-navigation -->

---

[← Previous](02-getting-started.md) · [Contents](README.md) · [Next →](04-the-desktop.md)
