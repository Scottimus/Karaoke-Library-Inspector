# Karaoke Library Inspector

A read-only scanner for MP3/CDG pairs and ZIP collections. It groups duplicates by both payloads' SHA256 hashes and sizes, so matching audio with changed graphics remains a distinct version. File names are excluded from the content identity.

```sh
python examples/make_sample.py
python inspector.py examples/sample
python -m unittest discover -s tests -v
```

The generated fixtures contain byte strings with media extensions. They exercise integrity checks and are not playable audio. The output lists complete pairs, byte-identical groups, and incomplete, empty, ambiguous, or damaged entries. Archive media payloads are limited to 128 MiB by default and are hashed without extraction.

Adapted from an existing local karaoke import planner. This release contains only inspection and report generation. Reports use relative filenames, which can still reveal library information. Review your own reports before sharing them.
