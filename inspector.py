"""Read-only paired-file integrity scanner adapted from a local import planner."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile


def stream_hash(handle):
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def identity(entries):
    """Preserve the import planner's extension/size/content identity."""
    payload = sorted((Path(entry["name"]).suffix.lower(), entry["size"], entry["sha256"])
                     for entry in entries)
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def add_pairs(entries, source, units, issues):
    groups = defaultdict(list)
    for entry in entries:
        groups[str(Path(entry["name"]).with_suffix("")).casefold()].append(entry)
    for stem, pair in sorted(groups.items()):
        extensions = [Path(entry["name"]).suffix.lower() for entry in pair]
        if sorted(extensions) != [".cdg", ".mp3"]:
            issues.append({"source": source, "item": stem, "reason": "incomplete or ambiguous pair"})
            continue
        if any(entry["size"] == 0 for entry in pair):
            issues.append({"source": source, "item": stem, "reason": "empty payload"})
            continue
        units.append({"source": source, "item": stem, "identity": identity(pair), "entries": pair})


def scan(root, max_archive_bytes=128 * 1024 * 1024):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Input must be a directory")
    units, issues, loose = [], [], []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        label = path.relative_to(root).as_posix()
        try:
            if path.suffix.lower() in {".mp3", ".cdg"}:
                with path.open("rb") as handle:
                    loose.append({"name": label, "size": path.stat().st_size,
                                  "sha256": stream_hash(handle)})
            elif path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path) as archive:
                    members = [m for m in archive.infolist()
                               if not m.is_dir() and Path(m.filename).suffix.lower() in {".mp3", ".cdg"}]
                    if sum(m.file_size for m in members) > max_archive_bytes:
                        raise ValueError("archive exceeds configured payload limit")
                    entries = []
                    for member in members:
                        with archive.open(member) as handle:
                            entries.append({"name": member.filename, "size": member.file_size,
                                            "sha256": stream_hash(handle)})
                    add_pairs(entries, label, units, issues)
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
            issues.append({"source": label, "reason": str(error)})
    add_pairs(loose, "loose files", units, issues)
    grouped = defaultdict(list)
    for unit in units:
        grouped[unit["identity"]].append({"source": unit["source"], "item": unit["item"]})
    duplicates = [copies for copies in grouped.values() if len(copies) > 1]
    return {"pairs": units, "duplicate_groups": duplicates, "issues": issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(scan(args.directory), indent=2) + "\n"
    if args.output:
        if args.output.exists():
            parser.error("Output already exists. Choose a new report filename.")
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
