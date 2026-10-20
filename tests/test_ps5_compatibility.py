# SPDX-License-Identifier: MIT
"""Synthetic PS5 dependency checks; no network, subprocess or console access."""
import copy
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / "scripts/check-ps5-compatibility"
LOADER = importlib.machinery.SourceFileLoader("ps5_compatibility", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
APP = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(APP)
COMMIT = "a" * 40
CONTENT = b"synthetic public source\n"


def fixture():
    return {"schema": 1, "researched_on": "2026-10-17",
            "target": {"console": "ps5", "model": "original", "firmware": "12.40",
                       "jailbreak": "working_user_report", "payload_delivery": "working_user_assumption"},
            "sources": [{"id": "loader", "repository": "https://github.com/example/loader", "commit": COMMIT,
                         "files": [{"path": "src/main.c", "url": f"https://raw.githubusercontent.com/example/loader/{COMMIT}/src/main.c",
                                    "bytes": len(CONTENT), "sha256": hashlib.sha256(CONTENT).hexdigest()}]}],
            "requirements": [{"id": name, "status": "blocked", "firmwares": [], "reason": "Unresolved fixture",
                              "evidence": ["https://github.com/example/loader/issues/1"]}
                             for name in sorted(APP.REQUIREMENTS)], "boot_contract": {}}


class PS5CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.manifest = self.base / "manifest.json"
        self.record = fixture()

    def invoke(self, *args):
        self.manifest.write_text(json.dumps(self.record))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = APP.main(["--manifest", str(self.manifest), *map(str, args)])
        return code, out.getvalue(), err.getvalue()

    def test_valid_manifest_does_not_imply_ready(self):
        code, out, _ = self.invoke("--validate-manifest", "--json")
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out)["requirements_recorded_ready"])
        code, out, _ = self.invoke("--json")
        self.assertEqual(code, 2)
        result = json.loads(out)
        self.assertEqual({item["id"] for item in result["requirements"]}, APP.REQUIREMENTS)
        self.assertTrue(all(not item["recorded_for_firmware"] for item in result["requirements"]))

    def test_exact_firmware_coverage_and_ready_status_are_both_required(self):
        for item in self.record["requirements"]:
            item.update(status="ready", firmwares=["12.40"])
        self.assertEqual(self.invoke()[0], 0)
        code, out, _ = self.invoke("--firmware", "12.41", "--json")
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out)["requirements_recorded_ready"])
        self.record["requirements"][0]["status"] = "pending"
        self.assertEqual(self.invoke()[0], 2)
        for value in ("", "12.4", "12.40-extra", "12x40", "12.40\n"):
            with self.subTest(firmware=value):
                self.assertEqual(self.invoke("--firmware", value)[0], 1)

    def test_malformed_pins_paths_fields_and_evidence_are_rejected(self):
        baseline = copy.deepcopy(self.record)
        changes = [lambda r: r.pop("boot_contract"),
                   lambda r: r.update(schema=True),
                   lambda r: r["target"].pop("payload_delivery"),
                   lambda r: r["sources"][0].update(commit="main"),
                   lambda r: r["sources"][0]["files"][0].update(url="https://raw.githubusercontent.com/example/loader/main/src/main.c"),
                   lambda r: r["sources"][0]["files"][0].update(url=f"https://raw.githubusercontent.com/other/loader/{COMMIT}/src/main.c"),
                   lambda r: r["sources"][0]["files"][0].update(path="../main.c"),
                   lambda r: r["sources"][0]["files"][0].update(path="/main.c"),
                   lambda r: r["sources"][0]["files"][0].update(path="src/%2e%2e/main.c"),
                   lambda r: r["sources"][0]["files"][0].update(path="src/main.c#other"),
                   lambda r: r["sources"][0]["files"][0].update(bytes=True),
                   lambda r: r["requirements"].pop(),
                   lambda r: r["requirements"].append(r["requirements"][0]),
                   lambda r: r["requirements"][0].update(evidence=["http://example.invalid"]),
                   lambda r: r["requirements"][0].update(evidence=["https://user:secret@example.invalid"]),
                   lambda r: r["requirements"][0].update(evidence=[])]
        for index, change in enumerate(changes):
            self.record = copy.deepcopy(baseline)
            change(self.record)
            with self.subTest(change=index):
                code, out, _ = self.invoke("--validate-manifest", "--json")
                self.assertEqual(code, 1)
                self.assertIn("error", json.loads(out))

    def test_local_source_identity_cannot_unblock_and_corruption_is_rejected(self):
        root = self.base / "sources"
        source = root / "loader/src/main.c"
        source.parent.mkdir(parents=True)
        source.write_bytes(CONTENT)
        code, out, _ = self.invoke("--sources", root, "--json")
        self.assertEqual(code, 2)
        result = json.loads(out)
        self.assertEqual(len(result["verified_source_files"]), 1)
        self.assertFalse(result["requirements_recorded_ready"])
        source.write_bytes(b"x" * len(CONTENT))
        code, _, err = self.invoke("--sources", root)
        self.assertEqual(code, 1)
        self.assertIn("SHA-256 differs", err)
        source.write_bytes(CONTENT + b"x")
        self.assertIn("size differs", self.invoke("--sources", root)[2])
        source.unlink()
        self.assertEqual(self.invoke("--sources", root)[0], 1)

    def test_source_symlink_escape_is_rejected(self):
        root = self.base / "sources"
        root.mkdir()
        external = self.base / "outside"
        (external / "src").mkdir(parents=True)
        (external / "src/main.c").write_bytes(CONTENT)
        (root / "loader").symlink_to(external, target_is_directory=True)
        code, _, err = self.invoke("--sources", root)
        self.assertEqual(code, 1)
        self.assertIn("escapes", err)

    def test_elf_identity_never_changes_readiness_or_file(self):
        payload = self.base / "payload.elf"
        content = b"\x7fELFsynthetic identity only"
        payload.write_bytes(content)
        before = payload.stat()
        code, out, _ = self.invoke("--elf", payload, "--json")
        self.assertEqual(code, 2)
        result = json.loads(out)
        self.assertEqual(result["elf_identity"]["sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(result["elf_identity"]["bytes"], len(content))
        self.assertFalse(result["requirements_recorded_ready"])
        self.assertEqual(payload.read_bytes(), content)
        self.assertEqual(payload.stat().st_mtime_ns, before.st_mtime_ns)

    def test_elf_symlink_directory_fifo_and_oversize_refused_before_open(self):
        regular = self.base / "regular"
        regular.write_bytes(b"fixture")
        link = self.base / "link"
        link.symlink_to(regular)
        fifo = self.base / "fifo"
        os.mkfifo(fifo)
        for path in (link, self.base, fifo):
            with self.subTest(path=path), patch.object(APP.os, "open", side_effect=AssertionError("must not open")):
                with self.assertRaisesRegex(ValueError, "regular nonsymlink"):
                    APP.read_identity(path)
        oversized = SimpleNamespace(st_mode=stat.S_IFREG, st_size=APP.MAX_BYTES + 1)
        with patch.object(APP.Path, "lstat", return_value=oversized), patch.object(APP.os, "open", side_effect=AssertionError("must not open")):
            with self.assertRaisesRegex(ValueError, "exceeds"):
                APP.read_identity(regular)

    def test_all_ready_output_remains_a_metadata_statement(self):
        for item in self.record["requirements"]:
            item.update(status="ready", firmwares=["12.40"])
        code, out, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn("All requirements recorded ready", out)
        self.assertIn("do not establish hardware acceptance", out)
        self.assertNotIn("ready to boot", out.lower())


if __name__ == "__main__":
    unittest.main()
