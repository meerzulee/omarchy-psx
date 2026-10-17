#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Meerzulee
# Adapted from omarchy-ps4/tests/initramfs-repack-test, local source
# SHA256:472bd7b9670e6cb53345bc2ceb30123e86f2ba26f8084686f837a235305a5a7e.
# MIT is applied by this repository; the original file had no per-file notice.
"""Host-only archive tests. No target code, mounts, devices or network access."""

import gzip
import hashlib
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/repack-ps4-initramfs"
API = runpy.run_path(str(TOOL))
ArchiveError = API["ArchiveError"]
parse_newc = API["parse_newc"]
replace_init = API["replace_init"]


def record(name, data=b"", mode=0o100755, nlink=1, ino=1):
    name = name.encode() + b"\0"
    fields = [ino, mode, 27, 42, nlink, 123456789, len(data), 7, 8, 0, 0, len(name), 0]
    result = b"070701" + b"".join(f"{value:08x}".encode() for value in fields) + name
    result += b"\0" * (-len(result) % 4)
    result += data
    return result + b"\0" * (-len(result) % 4)


def archive(*entries):
    result = b"".join(entries) + record("TRAILER!!!", mode=0, nlink=1)
    return result + b"\0" * (-len(result) % 512)


class RepackTests(unittest.TestCase):
    def test_only_init_data_and_filesize_change(self):
        original = archive(record(".", mode=0o40755), record("init", b"#!/bin/sh\nold\n"),
                           record("bin/busybox", b"binary\0bytes"),
                           record("bin/sh", b"busybox", mode=0o120777),
                           record("dev/console", mode=0o20600))
        replacement = b"#!/bin/sh\nreplacement with another size\n"
        result = replace_init(original, replacement)
        before, trailer_before = parse_newc(original)
        after, trailer_after = parse_newc(result)
        self.assertEqual(len(result) % 512, 0)
        self.assertEqual(len(before), len(after))
        self.assertTrue(trailer_after.startswith(trailer_before))
        for old, new in zip(before, after):
            if old.name == b"init":
                self.assertEqual(old.header[:54] + old.header[62:], new.header[:54] + new.header[62:])
                self.assertEqual(old.prefix[110:], new.prefix[110:])
                self.assertEqual(new.data, replacement)
                self.assertEqual(new.mode, 0o100755)
            else:
                self.assertEqual(old.raw, new.raw)

    def test_malformed_or_ambiguous_archives_fail(self):
        valid = archive(record("init", b"old"))
        malformed = {
            "truncated header": valid[:100],
            "wrong magic": b"070702" + valid[6:],
            "invalid hex": valid[:6] + b"xxxxxxxx" + valid[14:],
            "truncated data": record("init", b"old")[:-4],
            "missing trailer": record("init", b"old"),
            "trailing junk": valid + b"x",
            "missing init": archive(record("bin/busybox", b"binary")),
            "duplicate init": archive(record("init", b"old"), record("./init", b"other")),
            "hardlinked init": archive(record("init", b"old", nlink=2)),
            "symlink init": archive(record("init", b"bin/sh", mode=0o120777)),
            "nonexecutable init": archive(record("init", b"old", mode=0o100644)),
            "unsafe name": archive(record("../init", b"old")),
        }
        for description, candidate in malformed.items():
            with self.subTest(description=description), self.assertRaises(ArchiveError):
                replace_init(candidate, b"replacement")

    def test_cli_rejects_unpinned_base_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "base.gz"
            init = Path(directory) / "init"
            output = Path(directory) / "result.gz"
            base.write_bytes(gzip.compress(archive(record("init", b"old"))))
            init.write_bytes(b"#!/bin/sh\nnew\n")
            result = subprocess.run([sys.executable, str(TOOL), "--base", str(base), "--init", str(init),
                                     "--output", str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("size/SHA-256", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_requires_explicit_base_and_refuses_same_input_or_existing_output(self):
        missing = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("--base", missing.stderr)
        with tempfile.TemporaryDirectory() as directory:
            base, init, existing = (Path(directory) / name for name in ("base.gz", "init", "existing.gz"))
            base.write_bytes(b"preserve base")
            init.write_bytes(b"preserve init")
            existing.write_bytes(b"preserve output")
            for output in (base, init, existing):
                with self.subTest(output=output):
                    result = subprocess.run([sys.executable, str(TOOL), "--base", str(base),
                                             "--init", str(init), "--output", str(output)],
                                            capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
            self.assertEqual(base.read_bytes(), b"preserve base")
            self.assertEqual(init.read_bytes(), b"preserve init")
            self.assertEqual(existing.read_bytes(), b"preserve output")

    def test_atomic_output_create_never_overwrites_a_file_symlink_or_racing_destination(self):
        create = API["create_output"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "result.gz"
            create(output, b"complete result")
            self.assertEqual(output.read_bytes(), b"complete result")
            with self.assertRaises(ArchiveError):
                create(output, b"replacement")
            symlink = base / "symlink.gz"
            symlink.symlink_to(output)
            with self.assertRaises(ArchiveError):
                create(symlink, b"replacement")
            racing = base / "racing.gz"
            real_link = os.link
            def link(source, destination, **kwargs):
                Path(destination).write_bytes(b"another writer won")
                return real_link(source, destination, **kwargs)
            with mock.patch.object(os, "link", side_effect=link):
                with self.assertRaises(FileExistsError):
                    create(racing, b"must not replace")
            self.assertEqual(output.read_bytes(), b"complete result")
            self.assertEqual(racing.read_bytes(), b"another writer won")
            self.assertFalse(list(base.glob(".initramfs-*")))

    def test_synthetic_pinned_repack_is_deterministic_and_uses_repo_default_init(self):
        base = gzip.compress(archive(record("init", b"old"), record("bin/busybox", b"data only")), mtime=0)
        globals_ = API["main"].__globals__
        with tempfile.TemporaryDirectory() as directory:
            seed, output = (Path(directory) / name for name in ("synthetic.gz", "output.gz"))
            seed.write_bytes(base)
            with mock.patch.dict(globals_, BASE_SIZE=len(base), BASE_SHA256=hashlib.sha256(base).hexdigest()), \
                 mock.patch("builtins.print"):
                self.assertEqual(API["main"](["--base", str(seed), "--output", str(output)]), 0)
                expected = API["repack"](base, (REPO / "rootfs/initramfs/init").read_bytes())
                self.assertEqual(output.read_bytes(), expected)
                entries, _ = parse_newc(gzip.decompress(output.read_bytes()))
                self.assertEqual(next(entry.data for entry in entries if entry.name == b"init"),
                                 (REPO / "rootfs/initramfs/init").read_bytes())
                self.assertEqual(API["main"](["--base", str(seed), "--output", str(output)]), 1)
                self.assertEqual(output.read_bytes(), expected)

    def test_accepted_base_preserves_all_non_init_entries_and_is_deterministic(self):
        supplied = os.environ.get("OMARCHY_INITRAMFS_TEST_BASE")
        if not supplied:
            self.skipTest("set OMARCHY_INITRAMFS_TEST_BASE explicitly for the optional real-base test")
        base_path = Path(supplied)
        self.assertTrue(base_path.is_file(), "Explicit test base is not a regular file")
        base = base_path.read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(), API["BASE_SHA256"])
        replacement = b"#!/bin/sh\n# preservation test data only\n"
        first = API["repack"](base, replacement)
        self.assertEqual(first, API["repack"](base, replacement))
        before, _ = parse_newc(gzip.decompress(base))
        after, _ = parse_newc(gzip.decompress(first))
        self.assertEqual([entry.name for entry in before], [entry.name for entry in after])
        self.assertEqual([entry.raw for entry in before if entry.name != b"init"],
                         [entry.raw for entry in after if entry.name != b"init"])


if __name__ == "__main__":
    unittest.main()
