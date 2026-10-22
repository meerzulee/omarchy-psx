"""Synthetic image checks, included by default unittest discovery; no devices."""
import importlib.machinery
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("ps5_image", str(ROOT / "scripts/build-ps5-image"))
spec = importlib.util.spec_from_loader(loader.name, loader)
image = importlib.util.module_from_spec(spec)
loader.exec_module(image)


class ImageContractTests(unittest.TestCase):
    def test_vram_file_uses_loader_hexadecimal_bytes(self):
        text = image.vram_text(512)
        self.assertEqual(text, "0x20000000\n")
        self.assertEqual(int(text, 16), 512 * 1024 * 1024)
        for invalid in (0, -1, "512", 512.0, True):
            with self.assertRaises(ValueError):
                image.vram_text(invalid)

    def fixture(self, path, swapped=False, aligned=False):
        size = 1024 ** 3
        last = size // 512 - 34
        entries = bytearray(128 * 128)
        end = (last + 1) // 2048 * 2048 - 1 if aligned else last
        bounds = [(500 * 1024 ** 2 // 512, end), (2048, 500 * 1024 ** 2 // 512 - 1)]
        if swapped:
            bounds.reverse()
        for i, pair in enumerate(bounds):
            struct.pack_into("<QQ", entries, i * 128 + 32, *pair)
        with path.open("wb") as f:
            f.truncate(size)
            for current, backup, entry_lba in [(1, size // 512 - 1, 2), (size // 512 - 1, 1, size // 512 - 33)]:
                h = bytearray(512)
                h[:8] = b"EFI PART"
                struct.pack_into("<IIII", h, 8, 0x10000, 92, 0, 0)
                struct.pack_into("<QQQQ", h, 24, current, backup, 34, last)
                struct.pack_into("<QIII", h, 72, entry_lba, 128, 128, zlib.crc32(entries))
                struct.pack_into("<I", h, 16, zlib.crc32(h[:92]))
                f.seek(current * 512); f.write(h)
                f.seek(entry_lba * 512); f.write(entries)

    def test_gpt_requires_root_on_p1_and_fat_before_it_on_p2(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "image"
            self.fixture(p)
            self.assertEqual(len(image.gpt_contract(p)), 2)
            self.fixture(p, aligned=True)
            headers = image.gpt_contract(p)
            self.assertLess(headers[0]["root_end"], headers[0]["last_usable"])
            self.fixture(p, swapped=True)
            with self.assertRaisesRegex(ValueError, "incorrect PS5"):
                image.gpt_contract(p)

    def test_gpt_corruption_is_detected_independently_of_parted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "image"
            self.fixture(p)
            with p.open("r+b") as f:
                f.seek(2 * 512 + 80); f.write(b"x")
            with self.assertRaisesRegex(ValueError, "entry CRC"):
                image.gpt_contract(p)

    def test_image_file_write_does_not_follow_absolute_file_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "root"; root.mkdir()
            outside = Path(d) / "outside"; outside.write_text("preserve")
            (root / "config").symlink_to(outside)
            image.write(root, "/config", "image-owned")
            self.assertEqual(outside.read_text(), "preserve")
            self.assertFalse((root / "config").is_symlink())
            (root / "parent").symlink_to(Path(d))
            with self.assertRaisesRegex(ValueError, "escaped root"):
                image.write(root, "/parent/other", "refuse")


if __name__ == "__main__":
    unittest.main()
