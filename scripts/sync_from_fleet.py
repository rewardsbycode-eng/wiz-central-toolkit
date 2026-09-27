#!/usr/bin/env python3
"""Sync public-compatible code from wizard_central sovereign fleet.

WARNING: This script extracts PUBLIC-ONLY code.
Do NOT sync private doctrine, Governor secrets, or certification gates.

Usage:
    python3 sync_from_fleet.py <source_dir> <dest_dir> --dry-run
    python3 sync_from_fleet.py ~/wizard_central ~/wiz-central-toolkit
"""

import argparse
import shutil
import os
from pathlib import Path
from datetime import datetime

# Public-compatible wizards (safe to sync)
PUBLIC_WIZARDS = frozenset([
    "bannerwiz",
    "readwiz",
    "rustwiz",
    "pythonwiz",
    "jsonwiz",
    "diffwiz",
    "todowiz",
    "tmuxwiz",
])

# Private doctrine (NEVER sync these)
PRIVATE_PATTERNS = frozenset([
    "Fleet_Laws",
    "Governor",
    "bootwiz",
    "CERTIFIED",
    "Sovereign_Fleet",
    "doctrine",
    "_secret_",
    "private_",
])


def is_private_content(content: str) -> bool:
    """Check if content contains private sovereign fleet markers."""
    for pattern in PRIVATE_PATTERNS:
        if pattern.lower() in content.lower():
            return True
    return False


def sync_wizard(src_wizard: Path, dest_wizard: Path, dry_run: bool):
    """Copy a wizard from source to destination with sanitization."""
    if not src_wizard.exists():
        print(f"[SKIP] {src_wizard.name} not found in source")
        return
    
    print(f"[SYNC] {src_wizard.name}")
    
    for root, dirs, files in os.walk(src_wizard):
        for file in files:
            src_file = Path(root) / file
            rel_path = src_file.relative_to(src_wizard)
            dest_file = dest_wizard / rel_path
            
            if file.endswith(".py"):
                # Sanitize Python files
                content = src_file.read_text(encoding="utf-8")
                if is_private_content(content):
                    print(f"  [BLOCKED] {rel_path} contains private markers")
                    continue
                
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                if not dry_run:
                    dest_file.write_text(content, encoding="utf-8")
                    print(f"  [COPIED] {rel_path}")
            else:
                # Copy non-Python files as-is
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                if not dry_run:
                    shutil.copy2(src_file, dest_file)
                    print(f"  [COPIED] {rel_path}")


def main():
    parser = argparse.ArgumentParser(description="Sync public code from sovereign fleet")
    parser.add_argument("source", help="Path to wizard_central directory")
    parser.add_argument("dest", help="Path to wiz-central-toolkit directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would sync")
    args = parser.parse_args()
    
    source = Path(args.source)
    dest = Path(args.dest)
    
    if not source.exists():
        print(f"[ERROR] Source not found: {source}")
        return 1
    
    if not dest.exists():
        print(f"[ERROR] Dest not found: {dest}")
        return 1
    
    print(f"Source: {source}")
    print(f"Dest: {dest}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 40)
    
    synced_count = 0
    blocked_count = 0
    
    for wizard_name in PUBLIC_WIZARDS:
        src_wizard = source / wizard_name
        dest_wizard = dest / wizard_name
        
        if src_wizard.exists():
            sync_wizard(src_wizard, dest_wizard, args.dry_run)
            if not args.dry_run:
                synced_count += 1
        else:
            print(f"[SKIP] {wizard_name} not in source")
    
    print("-" * 40)
    print(f"Synced: {synced_count} wizards")
    print(f"Blocked: {blocked_count} (private content filtered)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return 0


if __name__ == "__main__":
    exit(main())
