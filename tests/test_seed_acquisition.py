# SPDX-License-Identifier: MIT
"""Synthetic cache acquisition; no network, firmware, devices or containers."""
import hashlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/fetch-ps4-initramfs-seed"
LOADER = importlib.machinery.SourceFileLoader("seed_acquisition", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)


class SeedAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination = Path(self.temp.name) / "cache/seed.cpio.gz"
        self.payload = b"synthetic external input"
        self.record = {"url": "https://example.invalid/pinned-input", "bytes": len(self.payload),
                       "sha256": hashlib.sha256(self.payload).hexdigest()}

    def test_only_exact_download_is_published_and_reused_offline(self):
        APP.fetch(self.record, self.destination, lambda *_a, **_k: io.BytesIO(self.payload))
        self.assertEqual(self.destination.read_bytes(), self.payload)
        before = self.destination.stat()
        def offline(*_a, **_k):
            self.fail("Cached verification must not access the network")
        APP.fetch(self.record, self.destination, offline)
        self.assertEqual(before.st_ino, self.destination.stat().st_ino)

    def test_wrong_hash_and_oversized_download_leave_no_output(self):
        for payload in (b"x" * len(self.payload), self.payload + b"x"):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    APP.fetch(self.record, self.destination, lambda *_a, **_k: io.BytesIO(payload))
                self.assertFalse(self.destination.exists())
                self.assertEqual(list(self.destination.parent.iterdir()), [])

    def test_existing_different_file_or_symlink_is_preserved(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"operator input")
        with self.assertRaises(ValueError):
            APP.fetch(self.record, self.destination)
        self.assertEqual(self.destination.read_bytes(), b"operator input")
        other = self.destination.parent / "other"
        other.write_bytes(self.payload)
        self.destination.unlink()
        self.destination.symlink_to(other)
        with self.assertRaises(ValueError):
            APP.fetch(self.record, self.destination)
        self.assertTrue(self.destination.is_symlink())
        self.assertEqual(other.read_bytes(), self.payload)

    def test_concurrent_destination_is_not_overwritten(self):
        def acquire(*_a, **_k):
            self.destination.write_bytes(b"operator created this during download")
            return io.BytesIO(self.payload)
        with self.assertRaises(FileExistsError):
            APP.fetch(self.record, self.destination, acquire)
        self.assertEqual(self.destination.read_bytes(), b"operator created this during download")
        self.assertEqual(list(self.destination.parent.glob(".ps4-seed-*")), [])
