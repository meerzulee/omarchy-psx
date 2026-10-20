#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Synthetic archive/identity tests; no console, devices or target execution."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/build-ps5-probe-initramfs"
API = runpy.run_path(str(TOOL))
ERROR = API["ProbeError"]
PARSE_NEWC = runpy.run_path(str(REPO / "scripts/repack-ps4-initramfs"))["parse_newc"]
RELEASE = "7.2.3-psx-ps5-dev1"
PREFIX = "lib/modules/" + RELEASE


def sha(data):
    return hashlib.sha256(data).hexdigest()


def busybox(interpreter=False, needed=False):
    # The bytes are an intentionally nonfunctional synthetic ELF fixture.
    data = bytearray(512)
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    count = 2 if interpreter or needed else 1
    struct.pack_into("<16sHHIQQQIHHHHHH", data, 0, ident, 2, 62, 1,
                     0x400100, 64, 0, 0, 64, 56, count, 0, 0, 0)
    struct.pack_into("<IIQQQQQQ", data, 64, 1, 5, 0, 0x400000, 0, 512, 512, 4096)
    if interpreter:
        struct.pack_into("<IIQQQQQQ", data, 120, 3, 4, 256, 0, 0, 8, 8, 1)
    if needed:
        struct.pack_into("<IIQQQQQQ", data, 120, 2, 4, 256, 0, 0, 32, 32, 8)
        struct.pack_into("<qQqQ", data, 256, 1, 0, 0, 0)
    return bytes(data)


def module(release=RELEASE):
    names = b"\0.shstrtab\0.modinfo\0"
    info = b"license=GPL\0vermagic=" + release.encode() + b" SMP preempt mod_unload\0"
    data = bytearray(256 + len(names) + len(info))
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    struct.pack_into("<16sHHIQQQIHHHHHH", data, 0, ident, 1, 62, 1,
                     0, 0, 64, 0, 64, 0, 0, 64, 3, 1)
    struct.pack_into("<IIQQQQIIQQ", data, 128, 1, 3, 0, 0, 256, len(names), 0, 0, 1, 0)
    struct.pack_into("<IIQQQQIIQQ", data, 192, 11, 1, 0, 0, 256 + len(names), len(info), 0, 0, 1, 0)
    data[256:256 + len(names)] = names
    data[256 + len(names):] = info
    return bytes(data)


def kernel_image(release=RELEASE):
    data = bytearray(4096)
    data[0x1f1] = 4
    data[0x1fe:0x200] = b"\x55\xaa"
    data[0x202:0x206] = b"HdrS"
    struct.pack_into("<I", data, 0x1f4, 96)
    struct.pack_into("<H", data, 0x206, 0x20f)
    struct.pack_into("<H", data, 0x20e, 0x50)
    struct.pack_into("<H", data, 0x236, 1)
    text = release.encode() + b" (synthetic fixture)\0"
    data[0x250:0x250 + len(text)] = text
    return bytes(data)


def members():
    directory = lambda name: (name, b"", tarfile.DIRTYPE)
    regular = lambda name, data: (PREFIX + "/" + name, data, tarfile.REGTYPE)
    return [directory("lib"), directory("lib/modules"), directory(PREFIX),
            directory(PREFIX + "/kernel"),
            regular("kernel/hid-generic.ko", module()), regular("kernel/usbhid.ko", module()),
            regular("modules.dep", b"kernel/hid-generic.ko:\nkernel/usbhid.ko: kernel/hid-generic.ko\n"),
            regular("modules.alias", b"alias usb:test usbhid\n"),
            regular("modules.builtin", b"kernel/builtin.ko\n"),
            regular("modules.order", b"kernel/hid-generic.ko\nkernel/usbhid.ko\n")]


def tar_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data, kind in entries:
            info = tarfile.TarInfo(name)
            info.type, info.mode, info.uid, info.gid, info.mtime = kind, 0o755, 42, 43, 1234567
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                info.linkname = "/outside"
            if kind == tarfile.REGTYPE:
                info.size = len(data)
            archive.addfile(info, io.BytesIO(data) if info.size else None)
    return output.getvalue()


def config():
    enabled = ["X86_64", "X86_PS5", "BLK_DEV_INITRD", "RD_GZIP", "BINFMT_ELF", "BINFMT_SCRIPT",
               "MODULES", "DEVTMPFS", "PROC_FS", "SYSFS"]
    return ("\n".join("CONFIG_" + key + "=y" for key in enabled)
            + '\nCONFIG_LOCALVERSION="-psx-ps5-dev1"\nCONFIG_EXTRA_FIRMWARE=""\n').encode()


def create_kernel(directory, archive=b"synthetic compressed input"):
    directory.mkdir()
    manifest = {"target": "7.2-ps5", "platform": "ps5", "kernel_release": RELEASE,
                "base_repo": "https://github.com/gregkh/linux.git", "base_ref": "v7.2.3",
                "base_commit": "a" * 40, "series_sha256": "b" * 64, "patchset_sha256": "c" * 64,
                "config_sha256": sha(config()), "active_patch_count": "1", "compiler": "fixture",
                "builder_image": "fixture", "builder_image_id": "fixture", "source_date_epoch": "0",
                "kbuild_identity": "fixture@fixture", "kbuild_version": "1", "embedded_firmware": "false"}
    files = {"bzImage": kernel_image(), "config": config(), "System.map": b"synthetic map\n",
             "version.txt": (RELEASE + "\n").encode(), f"modules-{RELEASE}.tar.zst": archive,
             "manifest.txt": "".join(f"{key}={value}\n" for key, value in manifest.items()).encode()}
    for name, data in files.items():
        (directory / name).write_bytes(data)
    reseal(directory)


def reseal(directory):
    (directory / "SHA256SUMS").write_text("".join(
        f"{sha(path.read_bytes())}  {path.name}\n" for path in sorted(directory.iterdir()) if path.name != "SHA256SUMS"))


class ProbeTests(unittest.TestCase):
    def test_static_busybox_rejects_interpreter_needed_wrong_arch_and_truncation(self):
        API["validate_busybox"](busybox())
        wrong_arch = bytearray(busybox())
        struct.pack_into("<H", wrong_arch, 18, 183)
        for data in (busybox(interpreter=True), busybox(needed=True), bytes(wrong_arch), busybox()[:70]):
            with self.subTest(data=data[:20]), self.assertRaises(ERROR):
                API["validate_busybox"](data)

    def test_raw_kernel_identity_hashes_config_and_boot_release_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            create_kernel(base / "good")
            API["validate_kernel"](base / "good")
            mutations = {
                "hash": ("System.map", b"changed", False),
                "ps4": ("config", config() + b"CONFIG_X86_PS4=y\n", True),
                "firmware": ("config", config().replace(b'CONFIG_EXTRA_FIRMWARE=""', b'CONFIG_EXTRA_FIRMWARE="vendor.bin"'), True),
                "elf-disabled": ("config", config().replace(b"CONFIG_BINFMT_ELF=y\n", b""), True),
                "script-disabled": ("config", config().replace(b"CONFIG_BINFMT_SCRIPT=y\n", b""), True),
                "image-release": ("bzImage", kernel_image("7.2.3-psx-ps4-dev1"), True),
                "identity": ("manifest.txt", (base / "good/manifest.txt").read_bytes().replace(b"platform=ps5", b"platform=ps4"), True),
                "manifest-release": ("manifest.txt", (base / "good/manifest.txt").read_bytes().replace(RELEASE.encode(), b"7.2.3-psx-ps5-other"), True),
                "manifest-missing": ("manifest.txt", b"target=7.2-ps5\n", True),
            }
            for name, (filename, content, seal) in mutations.items():
                folder = base / name
                shutil.copytree(base / "good", folder)
                (folder / filename).write_bytes(content)
                if filename == "config":
                    manifest = (folder / "manifest.txt").read_text().replace(sha(config()), sha(content))
                    (folder / "manifest.txt").write_text(manifest)
                if seal:
                    reseal(folder)
                with self.subTest(name=name), self.assertRaises(ERROR):
                    API["validate_kernel"](folder)

    def test_checksum_path_injection_duplicate_and_symlink_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "kernel"
            create_kernel(folder)
            original = (folder / "SHA256SUMS").read_text()
            for sums in (original + original.splitlines()[0] + "\n", original.replace("  config", "  ../config")):
                (folder / "SHA256SUMS").write_text(sums)
                with self.assertRaises(ERROR):
                    API["validate_kernel"](folder)
            (folder / "SHA256SUMS").write_text(original)
            (folder / "config").rename(folder / "real-config")
            (folder / "config").symlink_to(folder / "real-config")
            with self.assertRaises(OSError):
                API["validate_kernel"](folder)

    def test_complete_module_tree_is_preserved(self):
        result = API["read_module_tar"](io.BytesIO(tar_bytes(members())), RELEASE)
        for name, data, kind in members():
            self.assertIn(name, result)
            self.assertEqual(result[name][1], data)
            self.assertEqual(stat.S_ISDIR(result[name][0]), kind == tarfile.DIRTYPE)

    def test_module_paths_links_types_release_dependencies_and_size_rejected(self):
        bad = {
            "parent": members() + [("../escape", b"x", tarfile.REGTYPE)],
            "absolute": members() + [("/escape", b"x", tarfile.REGTYPE)],
            "wrong-release": members() + [("lib/modules/wrong/module.ko", module(), tarfile.REGTYPE)],
            "symlink": members() + [(PREFIX + "/link", b"", tarfile.SYMTYPE)],
            "hardlink": members() + [(PREFIX + "/hard", b"", tarfile.LNKTYPE)],
            "device": members() + [(PREFIX + "/node", b"", tarfile.CHRTYPE)],
            "duplicate": members() + [members()[-1]],
            "source": members() + [(PREFIX + "/source", b"", tarfile.DIRTYPE)],
            "compressed-module": members() + [(PREFIX + "/kernel/other.ko.zst", b"zstd", tarfile.REGTYPE)],
            "wrong-vermagic": [entry if not entry[0].endswith("usbhid.ko") else
                               (entry[0], module("wrong"), entry[2]) for entry in members()],
            "missing-dep": [entry for entry in members() if not entry[0].endswith("modules.dep")],
            "incomplete-dep": [(name, b"kernel/hid-generic.ko:\n", kind) if name.endswith("modules.dep") else
                               (name, data, kind) for name, data, kind in members()],
        }
        for name, entries in bad.items():
            with self.subTest(name=name), self.assertRaises(ERROR):
                API["read_module_tar"](io.BytesIO(tar_bytes(entries)), RELEASE)
        with mock.patch.dict(API["read_module_tar"].__globals__, MAX_MEMBER=16), self.assertRaises(ERROR):
            API["read_module_tar"](io.BytesIO(tar_bytes(members())), RELEASE)

    def test_newc_is_deterministic_with_real_device_metadata_and_notices(self):
        modules = API["read_module_tar"](io.BytesIO(tar_bytes(members())), RELEASE)
        init = (REPO / "platforms/ps5/rootfs/probe-init").read_bytes()
        first = API["make_initrd"](modules, busybox(), b"copyright", b"GPL text", init)
        self.assertEqual(first, API["make_initrd"](dict(reversed(list(modules.items()))), busybox(), b"copyright", b"GPL text", init))
        parsed, _ = PARSE_NEWC(gzip.decompress(first))
        entries = {entry.name.decode(): entry for entry in parsed}
        self.assertEqual(entries["init"].data, init)
        self.assertEqual(entries["bin/sh"].data, b"busybox")
        self.assertTrue(stat.S_ISLNK(entries["bin/sh"].mode))
        self.assertEqual(entries["usr/share/doc/busybox/LICENSE"].data, b"GPL text")
        for name, major, minor in (("dev/console", 5, 1), ("dev/tty", 5, 0), ("dev/null", 1, 3)):
            self.assertTrue(stat.S_ISCHR(entries[name].mode))
            header = entries[name].header
            self.assertEqual((int(header[78:86], 16), int(header[86:94], 16)), (major, minor))
        for name, (_, data) in modules.items():
            self.assertEqual(entries[name].data, data)

    @unittest.skipUnless(shutil.which("zstd"), "host zstd is required for the data-only CLI fixture")
    def test_cli_build_determinism_hash_rejection_and_output_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            compressed = subprocess.run([shutil.which("zstd"), "-q", "-c"], input=tar_bytes(members()), capture_output=True, check=True).stdout
            create_kernel(base / "kernel", compressed)
            (base / "busybox").write_bytes(busybox())
            (base / "copyright").write_bytes(b"synthetic attribution\n")
            (base / "LICENSE").write_bytes(b"synthetic license\n")
            common = [sys.executable, str(TOOL), "--kernel-output", str(base / "kernel"),
                      "--busybox", str(base / "busybox"), "--busybox-sha256", sha(busybox()),
                      "--busybox-notice", str(base / "copyright"), "--busybox-license", str(base / "LICENSE")]
            for output in (base / "first", base / "second"):
                result = subprocess.run(common + ["--output", str(output)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            first = {p.name: p.read_bytes() for p in (base / "first").iterdir()}
            second = {p.name: p.read_bytes() for p in (base / "second").iterdir()}
            self.assertEqual(first, second)
            self.assertEqual(first["bzImage"], kernel_image())
            self.assertNotIn(b"root=", first["cmdline.txt"])
            self.assertEqual(json.loads(first["receipt.json"])["module_count"], 2)
            again = subprocess.run(common + ["--output", str(base / "first")], text=True, capture_output=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(first, {p.name: p.read_bytes() for p in (base / "first").iterdir()})
            (base / "busybox").write_bytes(busybox() + b"changed")
            rejected = subprocess.run(common + ["--output", str(base / "bad")], text=True, capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("BusyBox SHA256", rejected.stderr)
            self.assertFalse((base / "bad").exists())


if __name__ == "__main__":
    unittest.main()
