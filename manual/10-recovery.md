# Recovery

Keep a complete known-good boot set and a backup of your personal files before testing a candidate. Recovery has two separate parts: restoring the Linux boot components and repairing or replacing the USB root filesystem.

## Getting back to the PS4 system

The established console boot path starts the PS4 system before Linux. Returning through it has been observed, but clean shutdown and reboot still lack repeated acceptance for each exact Linux build.

Save work and use the normal shutdown controls when they respond. If the console is stuck, follow its documented power-off procedure; abrupt power loss can damage the USB filesystem. After an Ethernet terminal fault, the driver requires a full power-off and fresh boot.

## Linux didn't start

A blank screen alone does not tell you which layer failed. Check the launcher's message and, for development tests, the UART capture. If there is no new Linux version banner, a boot of the candidate has not been established. Record that boundary before changing any Linux files.

If Linux starts but never reaches the desktop, check that the Omarchy USB drive is plugged in and that its kernel modules match the launcher's kernel. A launcher and a USB drive from different releases don't belong together.

## The launcher's boot files

The launcher installs its boot set with a journal and keeps the previous set alongside the current one. In this beta, the manual _Restore previous set_ and _Export diagnostics_ actions are marked "coming soon", and the launcher tells you plainly: "Recovery is not available in this beta."

Use the matching launcher's explicit boot-file installation flow to repair its boot set. Do not assume that reinstalling an application package activates new boot files. A hash mismatch means the inputs need to be reconciled; do not bypass it. Repairing the boot set does not recover personal files on the USB drive.

## First-boot setup failed or was interrupted

Boot Omarchy again. Owner setup stays pending until it has finished, so it simply runs again. If it can't continue, it shows an `OWNER-SETUP` support screen with what went wrong.

## A login screen instead of the desktop

Sign in with your password. Persistent automatic login is still waiting for its reboot test; a greeter does not by itself establish a storage or kernel fault.

## The Omarchy session won't start

Pick the XFCE recovery session on the login screen. It uses a conservative display setup without acceleration, which is enough to fix configuration files, check logs or copy your data off.

## Ethernet stopped working

Don't unload, reload, reset or rearm the driver. A terminal fault retains the driver state until a full power-off and fresh boot. See [Networking](06-networking.md#ethernet).

## The USB drive is damaged

If the drive is readable, copy personal files to another machine before repair. Reflashing a verified matching image is a way to rebuild the system, but it erases the selected device. Identify the USB by stable device information before writing it.

## Testing development kernels

On the developer layout, the loader prefers the boot files on the USB drive. Before swapping a kernel, back up all four boot files — kernel, initramfs, boot arguments and VRAM setting — off the drive and keep the old module tree. To roll back, power the console fully off and use the development host to restore the verified four-file set together. Preserve the matching module tree, verify the restored hashes, flush writes, and unmount the filesystems before returning the drive to the console. The full procedure is in [the partitioned USB guide](../platforms/ps4/docs/USB-PARTITIONED-DEVELOPMENT.md#explicit-kernel-development-override).

<!-- manual-navigation -->

---

[← Previous](09-what-works.md) · [Contents](README.md) · [Next →](11-troubleshooting.md)
