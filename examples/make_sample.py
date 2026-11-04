from pathlib import Path
import zipfile

root = Path(__file__).parent / "sample"
root.mkdir(exist_ok=True)
for stem in ("first", "duplicate"):
    (root / (stem + ".mp3")).write_bytes(b"synthetic audio payload")
    (root / (stem + ".cdg")).write_bytes(b"synthetic graphics payload")
(root / "orphan.mp3").write_bytes(b"unpaired payload")
with zipfile.ZipFile(root / "archive.zip", "w") as archive:
    archive.writestr("nested/track.mp3", b"unique synthetic audio")
    archive.writestr("nested/track.cdg", b"unique synthetic graphics")
