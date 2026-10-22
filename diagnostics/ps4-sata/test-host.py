#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Meerzulee
"""Run /init root-discovery control flow against synthetic sysfs/block fixtures.

No host devices, sysfs, mounts or target binaries are used. Only the fixture
copy changes block-node tests into ordinary-file tests and replaces PID1's
holding loop with exit; production init remains unchanged.
"""

from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class InitFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ("commands", "proc", "sys/class/block", "dev", "run", "newroot/usr", "newroot/etc"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / "newroot/etc/os-release").write_text("ID=fixture\n")
        for name, content in {"cmdline": "root=LABEL=OMARCHY-PS4 rootfstype=ext4 omarchy.require_usb=1 omarchy.root_layout=partitioned-usb omarchy.sata_diag=1\n",
                              "uptime": "12.00 40.00\n", "interrupts": "1: 5 xhci\n", "diskstats": "8 0 sda 1 0 1 0\n"}.items():
            (self.root / "proc" / name).write_text(content)
        trace = shlex.quote(str(self.root / "commands.log"))
        self.command("mount", '#!/bin/sh\nprintf "mount %s\\n" "$*" >> ' + trace + "\n")
        self.command("sleep", "#!/bin/sh\nexit 0\n")
        self.command("readlink", "#!/usr/bin/env python3\nimport os,sys\np=sys.argv[-1]\n"
                     "if '-f' in sys.argv: print(os.path.realpath(p))\n"
                     "elif os.path.islink(p): print(os.readlink(p))\n"
                     "else: sys.exit(1)\n")
        self.command("blkid", '#!/bin/sh\nprintf "blkid %s\\n" "$*" >> ' + trace + "\n"
                     'case "$1" in\n'
                     '  *1) printf \'%s\\n\' "$1: LABEL=\\\"PS4BOOT\\\" TYPE=\\\"vfat\\\"" ;;\n'
                     '  *2) printf \'%s\\n\' "$1: LABEL=\\\"OMARCHY-PS4\\\" TYPE=\\\"ext4\\\"" ;;\n'
                     'esac\n')

    def command(self, name, content):
        path = self.root / "commands" / name
        path.write_text(content)
        path.chmod(0o755)

    def disk(self, name, usb=True, correct_geometry=True):
        controller = "pci/usb1/1-1" if usb else "pci/ata1/host0"
        base = self.root / "sys/devices" / controller / "block" / name
        base.mkdir(parents=True)
        for number in (1, 2):
            partition = base / (name + str(number))
            partition.mkdir()
            (partition / "partition").write_text(str(number))
            (partition / "size").write_text("8388608" if number == 1 else "9999999")
            start = 2048 if number == 1 else 8390656
            if not correct_geometry:
                start += 1
            (partition / "start").write_text(str(start))
            (self.root / "sys/class/block" / partition.name).symlink_to(partition)
            (self.root / "dev" / partition.name).touch()

    def run_init(self):
        source = (HERE / "init").read_text()
        original_hold = "hold() {\n  # Remain PID1. Never launch desktop, networking, a rescue shell or rootfs code.\n  while :; do sleep 30; done\n}"
        self.assertIn(original_hold, source)
        source = source.replace(original_hold, "hold() { exit 0; }")
        source = source.replace("PATH=/bin:/sbin:/usr/bin:/usr/sbin", "PATH=" + str(self.root / "commands") + ":/bin:/usr/bin")
        source = source.replace("[ -b ", "[ -f ")
        source = source.replace("> /dev/kmsg", ">> /dev/kmsg")
        for path in ("/newroot", "/proc", "/sys", "/dev", "/run"):
            source = source.replace(path, str(self.root) + path)
        script = self.root / "fixture-init"
        script.write_text(source)
        result = subprocess.run(["/bin/sh", str(script)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return (self.root / "commands.log").read_text(), (self.root / "dev/kmsg").read_text()

    def test_only_usb_candidates_are_probed_and_mounted(self):
        self.disk("sda", usb=True)
        # Identical labels/geometry on a synthetic ATA disk must never reach blkid.
        self.disk("sdb", usb=False)
        commands, markers = self.run_init()
        self.assertIn("phase=ready", markers)
        self.assertIn("phase=observation_complete", markers)
        self.assertIn("blkid " + str(self.root / "dev/sda2"), commands)
        self.assertIn("blkid " + str(self.root / "dev/sda1"), commands)
        self.assertNotIn("/dev/sdb", commands)
        self.assertIn("mount -t ext4 -o ro,noload,nodev,nosuid,noexec", commands)

    def test_ata_only_never_reaches_blkid_or_mount(self):
        self.disk("sda", usb=False)
        commands, markers = self.run_init()
        self.assertNotIn("blkid ", commands)
        self.assertNotIn("mount -t ext4", commands)
        self.assertIn("reason=usb_root_not_found", markers)

    def test_wrong_usb_geometry_is_rejected_before_blkid(self):
        self.disk("sda", correct_geometry=False)
        commands, markers = self.run_init()
        self.assertNotIn("blkid ", commands)
        self.assertIn("reason=usb_root_not_found", markers)

    def test_duplicate_usb_labels_do_not_choose_first_disk(self):
        self.disk("sda")
        self.disk("sdc")
        commands, markers = self.run_init()
        self.assertIn("reason=multiple_matching_usb_roots", markers)
        self.assertNotIn("mount -t ext4", commands)

    def test_opt_in_is_required(self):
        cmdline = self.root / "proc/cmdline"
        cmdline.write_text(cmdline.read_text().replace("omarchy.sata_diag=1", ""))
        commands, markers = self.run_init()
        self.assertIn("reason=diagnostic_opt_in_missing", markers)
        self.assertNotIn("blkid ", commands)


if __name__ == "__main__":
    unittest.main()
