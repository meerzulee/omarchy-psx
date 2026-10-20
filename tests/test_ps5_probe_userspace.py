"""Synthetic acquisition tests; no packages execute and no network is used."""
import hashlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("probe_userspace", str(ROOT / "scripts/fetch-ps5-probe-userspace"))
spec = importlib.util.spec_from_loader(loader.name, loader)
fetch = importlib.util.module_from_spec(spec)
loader.exec_module(fetch)


def record(name, data, **extra):
    return dict(destination=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), **extra)


def ar_entry(name, data):
    fields = [(name + "/", 16), ("0", 12), ("0", 6), ("0", 6), ("100644", 8), (str(len(data)), 10)]
    return "".join(s.ljust(n) for s, n in fields).encode() + b"`\n" + data + (b"\n" if len(data) % 2 else b"")


def fixture(duplicate=False, symlink=False):
    data, out = b"synthetic executable bytes", io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:xz") as archive:
        for name in ["./different/busybox", "./usr/bin/busybox"] + (["./usr/bin/busybox"] if duplicate else []):
            member = tarfile.TarInfo(name)
            if symlink and name == "./usr/bin/busybox":
                member.type, member.linkname = tarfile.SYMTYPE, "/outside"
                archive.addfile(member)
            else:
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
    payload = out.getvalue()
    package = b"!<arch>\n" + ar_entry("debian-binary", b"2.0\n") + ar_entry("data.tar.xz", payload)
    manifest = {"schema": 1, "downloads": [record("test.deb", package, id="package", url="https://example.invalid/test.deb")],
                "members": [record("busybox", data, source_id="package", ar_member="data.tar.xz", member="./usr/bin/busybox")]}
    return package, manifest


class ProbeUserspaceTests(unittest.TestCase):
    def test_exact_member_and_offline_check(self):
        package, manifest = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "cache"
            fetch.acquire(manifest, destination, open_url=lambda *a, **k: io.BytesIO(package))
            self.assertEqual(sorted(p.name for p in destination.iterdir()), ["busybox", "test.deb"])
            fetch.acquire(manifest, destination, check=True, open_url=lambda *a, **k: self.fail("network used"))

    def test_duplicate_and_symlink_archive_members_refused(self):
        for options in ({"duplicate": True}, {"symlink": True}):
            with self.subTest(options=options):
                package, manifest = fixture(**options)
                with self.assertRaises(ValueError):
                    fetch.extract_member(package, manifest["members"][0])

    def test_duplicate_ar_and_truncation_refused(self):
        package, _ = fixture()
        for data in [package[:-20], package + ar_entry("data.tar.xz", b"duplicate")]:
            with self.assertRaises(ValueError):
                fetch.ar_member(data, "data.tar.xz")

    def test_different_existing_file_is_preserved(self):
        _, manifest = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / "busybox"
            path.write_bytes(b"user data")
            with self.assertRaises(ValueError):
                fetch.acquire(manifest, Path(tmp).resolve(), open_url=lambda *a, **k: self.fail("network used"))
            self.assertEqual(path.read_bytes(), b"user data")

    def test_bad_download_is_not_published(self):
        _, manifest = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "cache"
            with self.assertRaises(ValueError):
                fetch.acquire(manifest, destination, open_url=lambda *a, **k: io.BytesIO(b"wrong"))
            self.assertFalse(destination.exists())

    def test_offline_missing_does_not_create_cache(self):
        _, manifest = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "missing"
            with self.assertRaises(ValueError):
                fetch.acquire(manifest, destination, check=True, open_url=lambda *a, **k: self.fail("network used"))
            self.assertFalse(destination.exists())

    def test_destination_links_and_traversal_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "link").symlink_to(root, target_is_directory=True)
            for directory, name in [(root / "link", "busybox"), (root, "../busybox")]:
                with self.assertRaises(ValueError):
                    fetch.target(directory, name)


if __name__ == "__main__":
    unittest.main()
