#!/usr/bin/env python3
"""Synthetic-host tests: no service/SSH/PCI action.
Derived from Omarchy PS4 tests under the MIT license:
MIT License

Copyright (c) 2026 Omarchy PS4 contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import gzip
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HELPER = Path(__file__).resolve().parents[1] / "scripts/activate-baikal-ethernet"
LOADER = importlib.machinery.SourceFileLoader("baikal_activate", str(HELPER))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)
APP.CANDIDATE = "/root/omarchy-psx/artifacts.json"
MODULE_PATH = f"/usr/lib/modules/{APP.RELEASE}/kernel/drivers/net/ethernet/{APP.NAME}.ko"
MAC = "b0:05:94:12:34:56"
FOREIGN_UUID = "570870e1-0876-43f8-a9b4-240fbe3ddc31"


class FakeSystem(APP.System):
    def __init__(self):
        self.events = []
        self.claimed = False
        self.loaded = False
        self.managed = "yes"
        self.auto = "yes"
        self.profile_loaded = False
        self.fail_command = None
        self.fail_gate = False
        self.foreign = False
        self.wrong_origin = False
        self.foreign_options = False
        self.open_result = "healthy"
        self.glue_bound = True
        self.config = b"CONFIG_PS4_MTS=m\n"
        self.module = b"exact synthetic module bytes"
        self.note = bytes(range(24))
        self.candidate = {"schema": 1, "target": "6.18-ps4-baikal", "platform": "ps4-baikal",
                          "kernel_release": APP.RELEASE, "kernel_config_sha256": APP.digest(self.config),
                          "kernel_sha256": "a" * 64, "embedded_firmware": False,
                          "modules_archive": {"path": "modules-" + APP.RELEASE + ".tar.zst", "sha256": "b" * 64},
                          "module": {"name": APP.NAME,
                                     "path": "lib/modules/" + APP.RELEASE + "/kernel/drivers/net/ethernet/" + APP.NAME + ".ko",
                                     "sha256": APP.digest(self.module), "build_note_hex": self.note.hex()}}
        self.files = {MODULE_PATH: self.module, "/proc/config.gz": gzip.compress(self.config),
                      "/sys/class/net/psx0/address": MAC.encode(),
                      "/sys/class/net/psx0/name_assign_type": b"2",
                      "/proc/sys/net/ipv6/conf/psx0/disable_ipv6": b"0",
                      "/sys/kernel/iommu_groups/0/type": b"identity"}
        self.modes = {APP.CANDIDATE: 0o600, MODULE_PATH: 0o644}
        self.owners = {}
        for base, device in ((APP.PCI, "0x90d8"), (APP.GLUE, "0x90db")):
            self.files.update({base + "/vendor": b"0x104d", base + "/device": device.encode(),
                               base + "/power_state": b"D0", base + "/config": b"0000\x46\x05"})
        self.files.update({APP.PCI + "/driver_override": b"(null)",
                           APP.PCI + "/dma_mask_bits": b"32", APP.PCI + "/consistent_dma_mask_bits": b"32",
                           APP.PCI + "/resource": b"00000000c2000000 00000000c2000fff 00000200",
                           APP.GLUE + "/resource": b"0 0 0\n0 0 0\n00000000c8800000 00000000c89fffff 00000200"})
        self.value = {"continuous": 1, "lease_seconds": 0, "bound": 1, "terminal_fault": 0,
                      "error": 0, "stop_error": 0, "drain_proven": False, "state": 1,
                      "allowed": 0, "attempted": 0, "published": 0, "self_pinned": 0,
                      "engine_live": 0, "admin_up": 0, "carrier": 0, "poll_enabled": 0,
                      "mac14": 0xb005, "mac18": 0x94123456,
                      "phy_id": 0x03a29441, "phy_page": 0, "bmcr": 0x1040,
                      "mmd147_before": 0x10, "mmd147_after": 0, "mac08": 0x0f597c00,
                      "mask": 0x7ffffa, "gate": 0,
                      "dma": [[0x1000000, 0x4000], [0x1004000, 0x4000],
                              [0x1100000, 0x60000], [0x1200000, 0x60000]]}

    def read(self, path):
        path = str(path)
        if path == APP.CANDIDATE:
            return json.dumps(self.candidate).encode()
        if path == "/proc/modules":
            return (APP.NAME + " 1 0 - Live\n").encode() if self.loaded else b""
        if path == APP.PARAMS + "/report":
            return json.dumps(self.value).encode()
        if path.endswith("/initstate"):
            return b"live"
        if path.endswith("/notes/.note.gnu.build-id"):
            return self.note
        if path.endswith("/refcnt"):
            return str(self.value["self_pinned"]).encode()
        return self.files[path]

    def sealed(self, path, mode=None):
        APP.require(self.owners.get(path, (0, 0)) == (0, 0), "Unsealed fake owner")
        actual_mode = self.modes.get(path, 0o644)
        APP.require(not actual_mode & 0o022 and (mode is None or actual_mode == mode), "Unsealed fake mode")
        return self.read(path)

    def exists(self, path):
        if path == APP.GLUE + "/driver":
            return self.glue_bound
        if path in ("/sys/module/" + APP.NAME, APP.PCI + "/driver"):
            return self.loaded
        return path in self.files

    def real(self, path):
        return {"/lib/modules/" + APP.RELEASE + "/kernel/drivers/net/ethernet/" + APP.NAME + ".ko": MODULE_PATH,
                APP.GLUE + "/driver": "/sys/bus/pci/drivers/baikal_pcie",
                APP.PCI + "/driver": "/sys/bus/pci/drivers/" + APP.NAME,
                APP.PCI + "/iommu_group": "/sys/kernel/iommu_groups/0",
                "/sys/class/net/psx0/device": APP.PCI}.get(path, path)

    def pci_command(self, path):
        return self.files[path + "/config"][4:6]

    def claim_attempt(self):
        if self.claimed:
            raise FileExistsError("This boot's activation attempt was already used")
        self.claimed = True
        self.events.append(("claim",))

    def create_profile(self, data):
        APP.require(APP.PROFILE not in self.files, "Would replace profile")
        self.events.append(("create", APP.PROFILE))
        self.files[APP.PROFILE] = data
        self.modes[APP.PROFILE] = 0o600

    def write(self, path, data):
        self.events.append(("write", path, data))
        if path == APP.PARAMS + "/allow_open":
            if self.fail_gate:
                raise OSError("uncertain gate write")
            self.value["allowed"] = 1
        else:
            self.files[path] = data

    def command(self, *args, timeout=5):
        self.events.append(("command", *args))
        if self.fail_command and self.fail_command(args):
            raise OSError("injected command failure")
        if args[:2] == ("/usr/bin/modinfo", "-n"):
            return MODULE_PATH
        if args[:3] == ("/usr/bin/modinfo", "-F", "vermagic"):
            return APP.RELEASE + " SMP preempt mod_unload"
        if args[:3] == ("/usr/bin/modinfo", "-F", "depends"):
            return ""
        if args[:2] == ("/usr/bin/modprobe", "--show-depends"):
            return "insmod " + MODULE_PATH + (" allow_open=1" if self.foreign_options else "")
        if args[:2] == ("/usr/bin/modprobe", "--ignore-install"):
            self.loaded = True
            return ""
        if args == ("/usr/bin/ip", "link", "set", "dev", "psx0", "up"):
            APP.require(self.managed == self.auto == "no" and self.value["allowed"] == 1 and
                        self.value["published"] == 0, "First open escaped blocked NM/gated preparation")
            if self.open_result == "timeout":
                raise APP.subprocess.TimeoutExpired(args, timeout)
            if self.open_result == "unpublished":
                return ""
            self.value.update(state=3, attempted=1, published=1, self_pinned=1,
                              engine_live=1, admin_up=1, poll_enabled=1)
            if self.open_result == "retained-fault":
                self.value.update(state=4, terminal_fault=1, error=-5,
                                  engine_live=0, admin_up=0, poll_enabled=0)
            return ""
        if args[0] == APP.NM:
            rest = args[1:]
            if rest[:3] == ("device", "set", "psx0"):
                for key, value in zip(rest[3::2], rest[4::2]):
                    if key == "managed":
                        self.managed = value
                    if key == "autoconnect":
                        self.auto = value
                return ""
            if rest[:2] == ("-g", "GENERAL.NM-MANAGED"):
                return self.managed
            if rest[:2] == ("-g", "GENERAL.AUTOCONNECT"):
                return self.auto
            if rest[:2] == ("connection", "load"):
                self.profile_loaded = True
                return ""
            if rest[:2] == ("-t", "-e"):
                lines = []
                if self.profile_loaded:
                    lines.append(APP.PROFILE_UUID + ":ethernet:" +
                                 ("/run/foreign.nmconnection" if self.wrong_origin else APP.PROFILE))
                if self.foreign:
                    lines.append(FOREIGN_UUID + ":ethernet:/etc/NetworkManager/system-connections/other")
                return "\n".join(lines)
            if rest[:3] == ("-e", "no", "-g"):
                return "psx0\n\nyes"
        raise AssertionError("Unexpected command " + repr(args))


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeSystem()
        self.root = mock.patch.object(APP.os, "geteuid", return_value=0).start()
        mock.patch.object(APP.os, "uname", return_value=SimpleNamespace(release=APP.RELEASE, machine="x86_64")).start()
        self.addCleanup(mock.patch.stopall)

    def assert_not_armed(self):
        self.assertFalse(any(event[:2] == ("write", APP.PARAMS + "/allow_open") for event in self.host.events))
        self.assertFalse(any(event[:5] == ("command", APP.NM, "device", "set", "psx0") and
                             "yes" in event[5:] for event in self.host.events))

    def test_unplugged_activation_loads_arms_opens_verifies_then_delegates_without_dhcp(self):
        result = APP.activate(self.host)
        self.assertIn("asynchronous", result)
        events = self.host.events
        load = events.index(("command", APP.NM, "connection", "load", APP.PROFILE))
        arm = events.index(("write", APP.PARAMS + "/allow_open", b"1\n"))
        opened = events.index(("command", "/usr/bin/ip", "link", "set", "dev", "psx0", "up"))
        manage = events.index(("command", APP.NM, "device", "set", "psx0", "managed", "yes", "autoconnect", "yes"))
        self.assertLess(load, arm)
        self.assertLess(arm, opened)
        self.assertLess(opened, manage)
        self.assertEqual(self.host.value["carrier"], 0)
        self.assertEqual(self.host.value["published"], 1)
        self.assertEqual(self.host.value["admin_up"], 1)
        self.assertFalse(any("unload" in event or "rmmod" in event or
                             event[:4] == ("command", APP.NM, "connection", "up") for event in events))
        self.assertTrue(all("wlan0" not in event for event in events))

    def test_wrong_kernel_config_module_and_seal_make_no_activation_call(self):
        for change in ("release", "config", "module", "mode", "owner", "options"):
            with self.subTest(change=change):
                self.host = FakeSystem()
                if change == "release":
                    self.host.candidate["kernel_release"] = "old-kernel"
                elif change == "config":
                    self.host.candidate["kernel_config_sha256"] = "0" * 64
                elif change == "module":
                    self.host.candidate["module"]["sha256"] = "0" * 64
                elif change == "mode":
                    self.host.modes[APP.CANDIDATE] = 0o644
                elif change == "owner":
                    self.host.owners[APP.CANDIDATE] = (1000, 1000)
                else:
                    self.host.foreign_options = True
                with self.assertRaises(RuntimeError):
                    APP.activate(self.host)
                self.assert_not_armed()
                self.assertFalse(self.host.loaded)
                self.assertFalse(any(event[:2] == ("command", APP.NM) for event in self.host.events))

    def test_profile_load_failure_and_foreign_profile_never_arm_or_edit_foreign(self):
        for failure in ("load", "competitor", "origin", "changed-own-profile"):
            with self.subTest(failure=failure):
                self.host = FakeSystem()
                if failure == "load":
                    self.host.fail_command = lambda args: args[:3] == (APP.NM, "connection", "load")
                elif failure == "competitor":
                    self.host.foreign = True
                elif failure == "origin":
                    self.host.wrong_origin = True
                else:
                    original = b"[connection]\nid=custom user work\n"
                    self.host.files[APP.PROFILE] = original
                    self.host.modes[APP.PROFILE] = 0o600
                with self.assertRaises((RuntimeError, OSError)):
                    APP.activate(self.host)
                self.assert_not_armed()
                self.assertEqual(self.host.managed, "no")
                self.assertFalse(any("modify" in event or "delete" in event or "-r" in event for event in self.host.events))
                if failure == "changed-own-profile":
                    self.assertEqual(self.host.files[APP.PROFILE], original)

    def make_published(self):
        self.host.loaded = True
        self.host.value.update({"state": 3, "attempted": 1, "published": 1, "self_pinned": 1,
                                "engine_live": 1, "poll_enabled": 1, "allowed": 1})
        self.host.files[APP.PROFILE] = APP.TEMPLATE.replace(b"@MAC@", MAC.encode())
        self.host.modes[APP.PROFILE] = 0o600

    def test_healthy_published_admin_down_is_idempotent_without_rearm_or_nm_change(self):
        self.make_published()
        self.host.files[APP.PROFILE] = self.host.files[APP.PROFILE].replace(MAC.encode(), MAC.upper().encode())
        result = APP.activate(self.host)
        self.assertIn("ALREADY INITIALIZED", result)
        self.assertFalse(any(event[0] in ("write", "create") for event in self.host.events))
        self.assertFalse(any(event[:2] == ("command", APP.NM) for event in self.host.events))

    def test_published_dma_overlap_or_terminal_fault_refused_without_cleanup(self):
        for failure in ("overlap", "terminal", "note"):
            with self.subTest(failure=failure):
                self.host = FakeSystem()
                self.make_published()
                if failure == "overlap":
                    self.host.value["dma"][3][0] = self.host.value["dma"][2][0] + 1
                elif failure == "terminal":
                    self.host.value["terminal_fault"] = 1
                else:
                    self.host.note = b"wrong note"
                with self.assertRaises(RuntimeError):
                    APP.activate(self.host)
                self.assertFalse(any(event[0] == "write" for event in self.host.events))
                self.assertFalse(any("-r" in event or "rmmod" in event for event in self.host.events))

    def test_uncertain_gate_and_postgate_nm_failure_never_unload_or_retry_gate(self):
        for failure in ("gate", "manage"):
            with self.subTest(failure=failure):
                self.host = FakeSystem()
                self.host.fail_gate = failure == "gate"
                if failure == "manage":
                    self.host.fail_command = lambda args: args == (APP.NM, "device", "set", "psx0",
                                                                    "managed", "yes", "autoconnect", "yes")
                with self.assertRaises(OSError):
                    APP.activate(self.host)
                arms = [event for event in self.host.events if event[:2] == ("write", APP.PARAMS + "/allow_open")]
                self.assertEqual(len(arms), 1)
                self.assertTrue(self.host.loaded)
                self.assertFalse(any("-r" in event or "rmmod" in event or "down" in event for event in self.host.events))

    def test_up_exit_zero_without_healthy_publication_or_timeout_never_hands_to_nm(self):
        for result in ("unpublished", "retained-fault", "timeout"):
            with self.subTest(result=result):
                self.host = FakeSystem()
                self.host.open_result = result
                with self.assertRaises((RuntimeError, APP.subprocess.TimeoutExpired)):
                    APP.activate(self.host)
                self.assertEqual(self.host.managed, "no")
                self.assertEqual(self.host.auto, "no")
                opens = [event for event in self.host.events if event ==
                         ("command", "/usr/bin/ip", "link", "set", "dev", "psx0", "up")]
                arms = [event for event in self.host.events if event[:2] == ("write", APP.PARAMS + "/allow_open")]
                self.assertEqual(len(opens), 1)
                self.assertEqual(len(arms), 1)
                self.assertTrue(self.host.loaded)
                self.assertFalse(any("-r" in event or "rmmod" in event or "down" in event for event in self.host.events))

    def test_glue_wait_is_bounded_before_module_load(self):
        self.host.glue_bound = False
        with mock.patch.object(APP.time, "monotonic", side_effect=[100, 111]):
            with self.assertRaisesRegex(RuntimeError, "within10 seconds"):
                APP.activate(self.host)
        self.assertFalse(self.host.loaded)
        self.assert_not_armed()

    def test_already_armed_unpublished_instance_is_not_automatically_rearmed(self):
        self.host.loaded = True
        self.host.value["allowed"] = 1
        with self.assertRaisesRegex(RuntimeError, "gated PROBED"):
            APP.activate(self.host)
        self.assert_not_armed()

    def test_known_nm_writer_roundtrip_defaults_alias_case_timestamp_remain_activatable(self):
        original = APP.TEMPLATE.replace(b"@MAC@", MAC.encode())
        rewritten = (original.replace(b"autoconnect=true\n", b"")
                     .replace(b"auto-negotiate=false\n", b"")
                     .replace(b"type=ethernet", b"type=802-3-ethernet")
                     .replace(b"[ethernet]", b"[802-3-ethernet]")
                     .replace(MAC.encode(), MAC.upper().encode())
                     .replace(b"[connection]\n", b"[connection]\ntimestamp=1792220000\n")
                     + b"\n[proxy]\n")
        self.host.files[APP.PROFILE] = rewritten
        self.host.modes[APP.PROFILE] = 0o600
        self.host.profile_loaded = True
        self.assertEqual(APP.parse_profile(original), APP.parse_profile(rewritten))
        self.assertIn("ENABLED", APP.activate(self.host))
        self.assertEqual(self.host.files[APP.PROFILE], rewritten)
        self.assertFalse(any(event[0] == "create" for event in self.host.events))
        for changed in (rewritten.replace(b"route-metric=100", b"route-metric=50"),
                        rewritten.replace(b"method=disabled", b"method=auto"),
                        rewritten.replace(b"cloned-mac-address=preserve", b"cloned-mac-address=random")):
            with self.subTest(changed=changed):
                self.host.files[APP.PROFILE] = changed
                with self.assertRaisesRegex(RuntimeError, "profile was changed"):
                    APP.profile_guard(self.host, MAC, create=False)

    def test_second_invocation_never_rearms_or_reopens(self):
        APP.activate(self.host)
        previous = len(self.host.events)
        with self.assertRaises(FileExistsError):
            APP.activate(self.host)
        later = self.host.events[previous:]
        self.assertFalse(any(event[0] in ("write", "create") for event in later))
        self.assertFalse(any(event[:2] == ("command", APP.NM) for event in later))
        self.assertFalse(any(event[:3] == ("command", "/usr/bin/modprobe", "--ignore-install") for event in later))
        self.assertFalse(any(event[:2] == ("command", "/usr/bin/ip") for event in later))

    def test_command_preserves_blank_nm_fields_for_unrelated_mac_profile(self):
        host = APP.System()
        with mock.patch.object(host, "resolve_tool", return_value=APP.NM), \
             mock.patch.object(APP.subprocess, "check_output", return_value="\n00:11:22:33:44:55\nyes\n"):
            text = host.command(APP.NM, "-g", "synthetic-fields")
        self.assertEqual(text.split("\n"), ["", "00:11:22:33:44:55", "yes"])

    def test_trusted_sbin_multicall_alias_resolves_and_preserves_argv0(self):
        host = APP.System()
        alias, canonical = "/usr/sbin/modprobe", "/usr/bin/kmod"
        def info(path):
            kind = stat.S_IFLNK | 0o777 if str(path) == alias else stat.S_IFDIR | 0o755
            return SimpleNamespace(st_uid=0, st_mode=kind)
        with mock.patch.object(host, "exists", side_effect=lambda path: path == alias), \
             mock.patch.object(host, "real", return_value=canonical), \
             mock.patch.object(host, "sealed", return_value=b"synthetic root-owned executable") as seal, \
             mock.patch.object(APP.Path, "lstat", info), \
             mock.patch.object(APP.os, "access", return_value=True), \
             mock.patch.object(APP.subprocess, "check_output", return_value="ok\n") as command:
            self.assertEqual(host.command("/usr/bin/modprobe", "--show-depends", APP.NAME), "ok")
            self.assertEqual(command.call_args.args[0], (alias, "--show-depends", APP.NAME))
            seal.assert_called_once_with(canonical)

    def test_untrusted_or_missing_system_tool_never_executes(self):
        for available in (False, True):
            with self.subTest(available=available):
                host = APP.System()
                with mock.patch.object(host, "exists", return_value=available), \
                     mock.patch.object(host, "real", return_value="/usr/bin/nmcli"), \
                     mock.patch.object(host, "sealed", return_value=b"fake"), \
                     mock.patch.object(APP.Path, "lstat", return_value=SimpleNamespace(st_uid=1000, st_mode=stat.S_IFREG | 0o755)), \
                     mock.patch.object(APP.subprocess, "check_output") as command:
                    with self.assertRaises(RuntimeError):
                        host.command(APP.NM, "device", "status")
                    command.assert_not_called()

    def test_generic_module_layout_resolves_without_usr_assumption(self):
        ordinary = "/" + self.host.candidate["module"]["path"]
        self.host.files[ordinary] = self.host.files[MODULE_PATH]
        original = self.host.real
        def real(path):
            return ordinary if path in (ordinary, MODULE_PATH) else original(path)
        with mock.patch.object(self.host, "real", side_effect=real):
            self.assertIn("ENABLED", APP.activate(self.host))

    def test_generic_metadata_extensions_allowed_but_path_and_firmware_policy_guarded(self):
        self.host.candidate["source_commit"] = "1" * 40
        self.host.candidate["hardware_acceptance"] = {"status": "not-tested"}
        self.assertIn("ENABLED", APP.activate(self.host))
        for failure in ("path", "firmware", "archive"):
            self.host = FakeSystem()
            if failure == "path":
                self.host.candidate["module"]["path"] = "lib/modules/other/../../foreign.ko"
            elif failure == "firmware":
                self.host.candidate["embedded_firmware"] = True
            else:
                self.host.candidate["modules_archive"]["path"] = "modules-other.tar.zst"
            with self.subTest(failure=failure):
                with self.assertRaises(RuntimeError):
                    APP.activate(self.host)
                self.assertFalse(self.host.claimed)
                self.assertFalse(self.host.loaded)
                self.assert_not_armed()


if __name__ == "__main__":
    unittest.main(verbosity=2)
