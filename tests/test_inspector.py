from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import zlib
from inspector import scan


class InspectorTests(unittest.TestCase):
    def test_pairs_duplicates_partial_matches_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for stem, audio, lyrics in [("one", b"audio", b"graphics"),
                                        ("duplicate", b"audio", b"graphics"),
                                        ("changed", b"audio", b"different")]:
                (root / (stem + ".mp3")).write_bytes(audio)
                (root / (stem + ".cdg")).write_bytes(lyrics)
            (root / "partial.mp3").write_bytes(b"orphan")
            with zipfile.ZipFile(root / "bundle.zip", "w") as archive:
                archive.writestr("nested/alias.MP3", b"audio")
                archive.writestr("nested/alias.CDG", b"graphics")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = scan(root)
            self.assertEqual(len(result["pairs"]), 4)
            self.assertEqual(len(result["duplicate_groups"]), 1)
            self.assertEqual(len(result["duplicate_groups"][0]), 3)
            self.assertEqual(len(result["issues"]), 1)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_broken_and_oversized_archives_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "broken.zip").write_bytes(b"invalid zip")
            with zipfile.ZipFile(root / "large.zip", "w") as archive:
                archive.writestr("track.mp3", b"long")
            self.assertEqual(len(scan(root, max_archive_bytes=1)["issues"]), 2)

    def test_decompression_failure_does_not_abort_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "broken-payload.zip", "w") as archive:
                archive.writestr("track.mp3", b"payload")
            with patch("inspector.stream_hash", side_effect=zlib.error("bad stream")):
                self.assertEqual(len(scan(root)["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
