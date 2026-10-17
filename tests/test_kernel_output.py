# SPDX-License-Identifier: MIT
"""Kernel input integrity fixtures; never load modules or open target disks."""
import hashlib
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "platforms/ps4/scripts/verify-kernel-output"
LOADER = importlib.machinery.SourceFileLoader("kernel_output_verifier", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)


class KernelInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = "6.18.44-psx-ps4-baikal1"
        self.module = f"modules-{self.release}.tar.zst"
        self.config = b"synthetic config\n"
        self.files = {"version.txt": (self.release + "\n").encode(),
                      "bzImage": b"synthetic kernel", self.module: b"synthetic whole modules",
                      "config": self.config,
                      "manifest.txt": (f"kernel_release={self.release}\nconfig_sha256=" +
                                       hashlib.sha256(self.config).hexdigest() + "\n").encode()}
        self.write_inputs()

    def write_inputs(self):
        for name, payload in self.files.items():
            (self.root / name).write_bytes(payload)
        self.checksums = {name: hashlib.sha256(payload).hexdigest() for name, payload in self.files.items()}
        (self.root / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in self.checksums.items()))

    def test_complete_set_and_explicit_historical_pins(self):
        self.assertEqual(APP.verify(self.root), self.release)
        APP.verify(self.root, self.release, self.checksums["bzImage"], self.checksums[self.module])
        for arguments in (("6.18.44-ps4-baikal", None, None),
                          (self.release, "0" * 64, None), (self.release, None, "0" * 64)):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                APP.verify(self.root, *arguments)

    def test_modified_archive_and_duplicate_checksum_are_rejected(self):
        (self.root / self.module).write_bytes(b"different modules")
        with self.assertRaisesRegex(ValueError, "checksum differs"):
            APP.verify(self.root)
        self.write_inputs()
        with (self.root / "SHA256SUMS").open("a") as output:
            output.write(f"{self.checksums[self.module]}  {self.module}\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            APP.verify(self.root)

    def test_consistently_hashed_but_mismatched_build_metadata_is_rejected(self):
        self.files["manifest.txt"] = b"kernel_release=6.18.44-other\nconfig_sha256=wrong\n"
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "manifest kernel release differs"):
            APP.verify(self.root)
        self.files["manifest.txt"] = f"kernel_release={self.release}\nconfig_sha256=wrong\n".encode()
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "config digest differs"):
            APP.verify(self.root)

    def test_path_release_and_symlink_inputs_are_refused(self):
        (self.root / "version.txt").write_text("../../outside")
        with self.assertRaisesRegex(ValueError, "invalid kernel release"):
            APP.verify(self.root)
        self.write_inputs()
        (self.root / self.module).unlink()
        (self.root / self.module).symlink_to(self.root / "bzImage")
        with self.assertRaisesRegex(ValueError, "regular"):
            APP.verify(self.root)
