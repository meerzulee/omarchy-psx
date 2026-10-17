#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Synthetic source handoff: no network, Git process, device or mount access."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / "scripts/setup-kernel-workspace"
LOADER = importlib.machinery.SourceFileLoader("kernel_handoff", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)
SHA = "1234567890abcdef1234567890abcdef12345678"
REPO = "https://github.com/meerzulee/linux-psx.git"


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.manifest = self.base / "source.json"
        self.manifest.write_text(json.dumps({"schema": 1, "repository": REPO,
                                             "revision": SHA, "target": "6.18-ps4-baikal"}))
        self.destination = self.base / "linux-psx"
        self.patch = patch.object(APP, "MANIFEST", self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.temporary.cleanup)

    def test_pending_or_moving_ref_never_invokes_git(self):
        for revision in (None, "main", "v6.18.44", "abc123"):
            record = json.loads(self.manifest.read_text())
            record["revision"] = revision
            self.manifest.write_text(json.dumps(record))
            with self.subTest(revision=revision):
                with self.assertRaisesRegex(RuntimeError, "immutable"):
                    APP.setup(self.destination, invoke=lambda *_: self.fail("Unexpected Git operation"))
        self.assertFalse(self.destination.exists())

    def test_existing_dirty_or_different_checkout_is_never_modified(self):
        self.destination.mkdir()
        (self.destination / ".git").mkdir()
        work = self.destination / "my-local-work"
        work.write_text("preserve this")
        for actual, dirty in ((SHA, "?? my-local-work"), ("f" * 40, "")):
            calls = []
            def invoke(*args):
                calls.append(args)
                operation = args[2:]
                return {("remote", "get-url", "origin"): REPO,
                        ("rev-parse", "HEAD"): actual,
                        ("status", "--porcelain"): dirty}[operation]
            with self.subTest(actual=actual, dirty=dirty):
                with self.assertRaises(RuntimeError):
                    APP.setup(self.destination, invoke=invoke)
                self.assertEqual(work.read_text(), "preserve this")
                self.assertTrue(all(args[:2] == ("-C", self.destination) for args in calls))
                self.assertTrue(all(args[2] in ("remote", "rev-parse", "status") for args in calls))

    def test_missing_clone_fetches_exact_commit_and_renames_only_complete_tree(self):
        calls = []
        def invoke(*args):
            calls.append(args)
            if args[0] == "clone":
                temporary = Path(args[-1])
                (temporary / ".git").mkdir()
                (temporary / "targets").mkdir()
                (temporary / "targets/6.18-ps4-baikal.env").write_text("source fixture")
            if args[-2:] == ("rev-parse", "HEAD"):
                return SHA
            return ""
        self.assertIn("Created pinned", APP.setup(self.destination, invoke=invoke))
        self.assertTrue((self.destination / "targets/6.18-ps4-baikal.env").is_file())
        fetch = next(args for args in calls if "fetch" in args)
        self.assertEqual(fetch[-4:], ("fetch", "--depth=1", "origin", SHA))
        checkout = next(args for args in calls if "checkout" in args)
        self.assertEqual(checkout[-3:], ("checkout", "--detach", SHA))
        self.assertFalse(list(self.base.glob(".linux-psx-fetch-*")))


if __name__ == "__main__":
    unittest.main()
