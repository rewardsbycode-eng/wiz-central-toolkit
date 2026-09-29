#!/usr/bin/env python3
"""Sync public-compatible wizard files from wizard_central."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

WIZARD_MAPPING = {
    "banner-wizard": "bannerwiz",
    "read-wizard": "readwiz",
    "rust-wizard": "rustwiz",
    "python-wizard": "pythonwiz",
    "json-wizard": "jsonwiz",
    "diff-wizard": "diffwiz",
    "todo-wizard": "todowiz",
    "tmux-wizard": "tmuxwiz",
    "commandline-wizard": "commandlinewiz",
    "godfather-wizard": "godfatherwiz",
}

# Keep these markers specific. Do not use broad terms like CERTIFIED.
PRIVATE_MARKERS = (
    "Fleet_Laws",
    "Governor_Certification",
    "Sovereign_Fleet",
    "private_doctrine",
    "PRIVATE_DOCTRINE",
)

IGNORED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "reports",
}


def is_private(path: Path, content: str) -> bool:
    if path.name in {
        "Fleet_Laws",
        "Governor_Certifications",
        "private_doctrine",
    }:
        return True

    text = content.lower()
    return any(marker.lower() in text for marker in PRIVATE_MARKERS)


def sync_wizard(source: Path, destination: Path, dry_run: bool):
    copied = 0
    filtered = 0

    print(f"[SYNC] {source.name} -> {destination.relative_to(destination.parents[1])}")

    for source_file in sorted(source.rglob("*")):
        if not source_file.is_file():
            continue

        relative = source_file.relative_to(source)

        if any(part in IGNORED_PARTS for part in relative.parts):
            continue

        try:
            content = source_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"  [SKIP BINARY] {relative}")
            continue

        if is_private(source_file, content):
            print(f"  [FILTERED] {relative}")
            filtered += 1
            continue

        target = destination / relative

        if dry_run:
            print(f"  [WOULD COPY] {relative}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
            print(f"  [COPIED] {relative}")

        copied += 1

    return copied, filtered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    dest = args.dest.expanduser().resolve()

    if not source.is_dir():
        print(f"[ERROR] Source not found: {source}")
        return 1

    # Keep imported source separate from the live package.
    sync_root = dest / "synced"

    total_copied = 0
    total_filtered = 0
    skipped = 0

    for central_name, toolkit_name in WIZARD_MAPPING.items():
        source_wizard = source / central_name

        if not source_wizard.is_dir():
            print(f"[SKIP] {central_name} not found")
            skipped += 1
            continue

        destination_wizard = sync_root / toolkit_name
        copied, filtered = sync_wizard(
            source_wizard,
            destination_wizard,
            args.dry_run,
        )

        total_copied += copied
        total_filtered += filtered

    print("----------------------------------------")
    print(f"Files copied:   {total_copied}")
    print(f"Files filtered: {total_filtered}")
    print(f"Wizards skipped:{skipped}")
    print(f"Dry run:        {args.dry_run}")
    print(f"Timestamp:      {datetime.now(timezone.utc).isoformat()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
