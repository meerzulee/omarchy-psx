# Owner provisioning package

This package installs the PS4-specific automatic root-expansion program,
first-boot owner program and their disabled-by-default systemd services.
Installing the package does not arm either flow.

An image builder arms it only after confirming the release image has no
default user or password. For an already installed development root, mount the
USB filesystem from another Linux environment and use the guarded preparation
command:

```bash
sudo omarchy-ps4-prepare-for-owner --check /mnt
sudo omarchy-ps4-prepare-for-owner /mnt
```

On a terminal, the second command shows the Omarchy confirmation screen. An
image pipeline can use the explicit non-interactive form instead:

```bash
sudo omarchy-ps4-prepare-for-owner \
  --confirm PREPARE-FOR-ANOTHER-OWNER /mnt
```

It refuses `/`, non-USB filesystems, the wrong label, and any existing human
account other than the known `ps4` development account. Preparation removes
that account, development sudo/SSH access, LightDM autologin, cloned machine
identity, and SSH host keys before arming storage expansion followed by owner
setup.

An image builder may stage validated public keys at
`/var/lib/omarchy-ps4/provisioning/authorized_keys`. Owner setup installs them
for the newly created user and enables OpenSSH with password, keyboard-
interactive, and root login disabled. The staged file is removed after a
successful handoff. Public release images must not contain a maintainer's
personal key. Without a staged unattended key, first-owner setup leaves SSH
disabled and never requires network access. After the desktop starts, the
owner can use Omarchy's normal security setup to configure SSH.

The whole-device release profile uses one ext4 filesystem and expands it
online after checking the label, filesystem, USB ancestry and recorded layout.
The private `partitioned-usb` development profile instead uses a 4 GiB FAT32
partition labelled `PS4BOOT`, followed by ext4 labelled `OMARCHY-PS4` using the
remaining space. It requires the matching private launcher and host installer.
Before owner setup, `omarchy-ps4-grow-root` validates that exact two-partition
layout and full-size ext4 without changing its geometry. Both profiles record
storage readiness only after verification. The program never edits a partition
table or accepts a device argument.

The program refuses any root that is not labelled `OMARCHY-PS4` and reached
through USB. It leaves `pending` in place after an error so setup can resume.
Before removing that marker it runs an offline PS4-owned user finalizer that
creates the Tokyo Night theme/background state, XDG directories, bookmarks,
application launchers, default browser associations, skill links, migration
markers, and the default keyring. It does not run upstream Mise downloads or
enable unaudited user services.
LightDM requires this owner unit and is ordered after it. The owner unit keeps
control of tty1 even when storage expansion or setup fails. Its clean terminal
surface centers the pinned green Omarchy ASCII logo and every interactive
prompt; raw service errors go to the journal instead of being painted through
the form. Timezone selection first offers every fixed whole-hour GMT offset
from GMT-12:00 through GMT+14:00. Labels use the familiar sign; the picker maps
them to tzdata internally and the final review shows the chosen GMT label.
Choose a city or region for daylight-saving rules or half/quarter-hour zones.
All lists scroll with Up/Down; they do not use a live filter that repaints
unreliably on the Linux virtual console. Selection is offline and does not
perform a location lookup. The final review and confirmation are centered; Yes remains Omarchy green and No
remains neutral gray. A branded `OWNER-SETUP` support screen replaces an empty
login prompt on failure. UART receives only lifecycle stages and storage
evidence; usernames, passwords and prompt input are never mirrored to it.

Flashable partitioned candidates use image-layout schema 2. They retain the
existing 4 GiB `PS4BOOT` geometry and authorize growing partition 2 and ext4 on
the first boot. The growth helper checks the running USB root, MBR, original
image length and device identity, saves the original MBR, changes only the
second partition's length, checks its read-back and kernel size, then permits
ext4 growth. A stopped attempt can resume before owner setup completes.
Historical schema-1 partitioned installations still require a full-size root
and never authorize a partition-table write. Their initramfs and boot-profile
hashes are unchanged. These new source paths require real-hardware acceptance.

After successful setup, the provisioner creates the PAM-required system
`autologin` group when absent and adds the owner to it. LightDM uses a
PS4-owned PAM service that admits only that group, plus an explicit per-owner
Omarchy session record, to persistently enter the desktop. The normal LightDM
password stack, `sudo`, and screen locking remain unchanged and still require
the password,
but the current unencrypted gift has no boot-time authentication boundary.
Anyone with physical access to the console or removable USB can reach the
desktop. A future accepted LUKS unlock flow may provide that boundary before
automatic desktop login.
It does not touch the PS4 loader, kernel, initramfs, internal disk, LUKS,
Limine, SDDM, Btrfs, or any partition table.
