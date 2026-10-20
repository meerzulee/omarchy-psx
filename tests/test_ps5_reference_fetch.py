# SPDX-License-Identifier: MIT
"""Synthetic downloads only; no network, payload or device access."""
import hashlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/fetch-ps5-references"
LOADER = importlib.machinery.SourceFileLoader("ps5_reference_fetch", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)


class ReferenceFetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination = Path(self.temp.name).resolve() / "references/README.md"
        self.payload = b"Synthetic text reference\n"
        self.record = {"url": "https://example.invalid/reference",
                       "bytes": len(self.payload),
                       "sha256": hashlib.sha256(self.payload).hexdigest()}

    def test_exact_download_and_offline_reuse(self):
        APP.fetch(self.record, self.destination, lambda *_a, **_k: io.BytesIO(self.payload))
        before = self.destination.stat()
        def offline(*_a, **_k):
            self.fail("Verified references must be reusable offline")
        APP.fetch(self.record, self.destination, offline)
        self.assertEqual(before.st_ino, self.destination.stat().st_ino)

    def test_bad_content_leaves_no_published_file(self):
        for data in (self.payload + b"x", b"x" * len(self.payload), self.payload[:-1]):
            with self.subTest(data=data), self.assertRaises(ValueError):
                APP.fetch(self.record, self.destination, lambda *_a, **_k: io.BytesIO(data))
            self.assertFalse(self.destination.exists())
            self.assertEqual(list(self.destination.parent.iterdir()), [])

    def test_existing_different_input_is_preserved(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"operator notes")
        with self.assertRaises(ValueError):
            APP.fetch(self.record, self.destination)
        self.assertEqual(self.destination.read_bytes(), b"operator notes")

    def test_symlink_parent_and_racing_file_are_not_overwritten(self):
        self.destination.parent.symlink_to(Path(self.temp.name).resolve(), target_is_directory=True)
        with self.assertRaises(ValueError):
            APP.fetch(self.record, self.destination)
        self.destination.parent.unlink()
        def race(*_a, **_k):
            self.destination.write_bytes(b"racing operator input")
            return io.BytesIO(self.payload)
        with self.assertRaises(FileExistsError):
            APP.fetch(self.record, self.destination, race)
        self.assertEqual(self.destination.read_bytes(), b"racing operator input")


if __name__ == "__main__":
    unittest.main()
