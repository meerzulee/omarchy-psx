# SPDX-License-Identifier: MIT
"""Synthetic firmware fetch and initramfs insertion; no network, firmware or devices."""
import contextlib
import gzip
import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(ROOT / "scripts" / name))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


FETCH = load("fetch-ps4-firmware")
ADD = load("add-ps4-initramfs-firmware")
PAYLOADS = {"vendor/a.bin": b"synthetic bluetooth", "b.bin": b"synthetic wifi"}


def record(name, source):
    data = PAYLOADS[name]
    return {"name": name, "source": source, "path": "fw/" + name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "git_blob": FETCH.git_blob(data)}


MANIFEST = {
    "initramfs_directory": "lib/firmware",
    "entry_mtime": 1792195200,
    "sources": {
        "plain": {"commit": "1" * 40, "url": "https://plain.invalid/{path}?id={commit}"},
        "github": {"commit": "2" * 40, "url": "https://raw.invalid/{commit}/{path}",
                   "api_url": "https://api.invalid/{path}?ref={commit}"},
    },
    "files": [record("vendor/a.bin", "plain"), record("b.bin", "github")],
}


class Opener:
    def __init__(self, responses):
        self.responses, self.requests = responses, []

    def __call__(self, request, timeout):
        self.requests.append(request)
        reply = self.responses[request.full_url]
        if isinstance(reply, int):
            raise urllib.error.HTTPError(request.full_url, reply, "synthetic", {}, None)
        return io.BytesIO(reply)


def urls(payloads=PAYLOADS):
    return {"https://plain.invalid/fw/vendor/a.bin?id=" + "1" * 40: payloads["vendor/a.bin"],
            "https://raw.invalid/" + "2" * 40 + "/fw/b.bin": payloads["b.bin"]}


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "cache"

    def fetch(self, opener, token=None):
        return FETCH.fetch(MANIFEST, self.output, token, opener, lambda _s: None, lambda _m: None)

    def test_pinned_files_are_saved_then_reused_offline(self):
        self.assertEqual(set(self.fetch(Opener(urls())).values()), {"fetched"})
        for name, data in PAYLOADS.items():
            self.assertEqual((self.output / name).read_bytes(), data)
        self.assertEqual(set(self.fetch(Opener({})).values()), {"verified"})

    def test_rate_limited_github_falls_back_to_the_api_with_token(self):
        responses = urls()
        responses["https://raw.invalid/" + "2" * 40 + "/fw/b.bin"] = 429
        responses["https://api.invalid/fw/b.bin?ref=" + "2" * 40] = PAYLOADS["b.bin"]
        opener = Opener(responses)
        self.fetch(opener, token="secret")
        api = [r for r in opener.requests if r.full_url.startswith("https://api.invalid/")]
        self.assertEqual(len([r for r in opener.requests if r.full_url.startswith("https://raw.invalid/")]), 3)
        self.assertEqual(api[0].get_header("Authorization"), "Bearer secret")
        self.assertEqual(api[0].get_header("Accept"), "application/vnd.github.raw")

    def test_wrong_bytes_are_never_saved(self):
        bad = dict(PAYLOADS, **{"b.bin": b"synthetic wifX"})
        with self.assertRaisesRegex(ValueError, "b.bin"):
            self.fetch(Opener(dict(urls(bad), **{"https://api.invalid/fw/b.bin?ref=" + "2" * 40: 404})))
        self.assertFalse((self.output / "b.bin").exists())
        self.assertEqual(sorted(p.name for p in self.output.iterdir()), ["vendor"])

    def test_existing_different_file_is_preserved(self):
        (self.output / "vendor").mkdir(parents=True)
        (self.output / "vendor/a.bin").write_bytes(b"operator copy")
        with self.assertRaises(ValueError):
            self.fetch(Opener(urls()))
        self.assertEqual((self.output / "vendor/a.bin").read_bytes(), b"operator copy")

    def test_unsafe_names_are_refused(self):
        for name in ("../x", "/etc/x", "a/../b", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                FETCH.safe_name(name)


def archive(names):
    body = b"".join(ADD.entry(i + 1, 0o040755 if n != "init" else 0o100755, 1, 0, n, b"#!/bin/sh\n" if n == "init" else b"")
                    for i, n in enumerate(names))
    body += ADD.entry(0, 0, 1, 0, ADD.TRAILER)
    return body + b"\0" * ((512 - len(body) % 512) % 512)


class InitramfsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.firmware_dir = Path(self.temp.name) / "fw"
        for name, data in PAYLOADS.items():
            (self.firmware_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (self.firmware_dir / name).write_bytes(data)

    def firmware(self):
        return ADD.load_firmware(MANIFEST, self.firmware_dir)

    def test_firmware_is_added_and_existing_entries_are_unchanged(self):
        base = archive([".", "init", "lib", "lib/firmware"])
        body, records = ADD.add_firmware(base, self.firmware(), 7)
        entries, trailer = ADD.parse(body)
        _, old_trailer = ADD.parse(base)
        self.assertEqual(body[:old_trailer], base[:old_trailer])
        self.assertEqual(len(body) % 512, 0)
        names = [e["name"] for e in entries]
        self.assertEqual(names[-4:], ["lib/firmware/vendor", "lib/firmware/vendor/a.bin", "lib/firmware/b.bin", ADD.TRAILER])
        by_name = {e["name"]: e for e in entries}
        for name, data in PAYLOADS.items():
            start, end = by_name["lib/firmware/" + name]["data"]
            self.assertEqual(body[start:end], data)
        self.assertEqual([r["path"] for r in records][0], "lib/firmware/vendor")

    def test_missing_parent_directories_are_created(self):
        body, _ = ADD.add_firmware(archive([".", "init"]), self.firmware(), 7)
        names = [e["name"] for e in ADD.parse(body)[0]]
        self.assertLess(names.index("lib"), names.index("lib/firmware"))
        self.assertLess(names.index("lib/firmware"), names.index("lib/firmware/vendor"))

    def test_clashes_non_initramfs_and_trailing_archives_are_refused(self):
        with self.assertRaisesRegex(ADD.ArchiveError, "already contains"):
            ADD.add_firmware(archive(["init", "lib", "lib/firmware", "lib/firmware/b.bin"]), self.firmware(), 7)
        with self.assertRaisesRegex(ADD.ArchiveError, "no /init"):
            ADD.add_firmware(archive(["lib"]), self.firmware(), 7)
        with self.assertRaisesRegex(ADD.ArchiveError, "concatenated"):
            ADD.add_firmware(archive(["init"]) + archive(["lib"]), self.firmware(), 7)

    def test_changed_or_missing_firmware_is_refused(self):
        (self.firmware_dir / "b.bin").write_bytes(b"synthetic wifX")
        with self.assertRaisesRegex(ADD.ArchiveError, "differs from its pin"):
            self.firmware()
        (self.firmware_dir / "b.bin").unlink()
        with self.assertRaisesRegex(ADD.ArchiveError, "fetch-ps4-firmware"):
            self.firmware()

    def test_command_writes_once_and_refuses_overwrite(self):
        base = Path(self.temp.name) / "base.cpio.gz"
        base.write_bytes(gzip.compress(archive([".", "init", "lib", "lib/firmware"]), mtime=0))
        manifest = dict(MANIFEST, cache_path="unused", tested={"experiment": "synthetic", "base_sha256": "0", "cpio_sha256": "0"})
        output = Path(self.temp.name) / "out/initramfs.cpio.gz"
        original = ADD.MANIFEST
        ADD.MANIFEST = Path(self.temp.name) / "manifest.json"
        ADD.MANIFEST.write_text(json.dumps(manifest))
        self.addCleanup(setattr, ADD, "MANIFEST", original)
        argv = ["--base", str(base), "--firmware", str(self.firmware_dir), "--output", str(output)]
        quiet = io.StringIO()
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            self.assertEqual(ADD.main(argv), 0)
            produced = output.read_bytes()
            self.assertEqual(ADD.main(argv), 1)
        self.assertIn(b"synthetic wifi", gzip.decompress(produced))
        self.assertEqual(output.read_bytes(), produced)


class ManifestTests(unittest.TestCase):
    def test_repository_manifest_pins_every_file(self):
        manifest = json.loads((ROOT / "manifests/ps4-firmware.json").read_text())
        names = [f["name"] for f in manifest["files"]]
        self.assertEqual(len(names), len(set(names)))
        for item in manifest["files"]:
            FETCH.safe_name(item["name"])
            self.assertIn(item["source"], manifest["sources"])
        self.assertTrue(manifest["cache_path"].startswith("cache/"))


if __name__ == "__main__":
    unittest.main()
