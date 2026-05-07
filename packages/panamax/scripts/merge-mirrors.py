#!/usr/bin/env python3
"""
merge-mirrors.py

Merges a source mirrors directory into a destination mirrors directory:
  - Crate files (.crate): moved into the matching path under dst/crates/
  - Index files (crates.io-index): appended to the destination file if it
    exists (deduplicating by version), or copied in if it does not.

Usage:
    python3 merge-mirrors.py --src /path/to/src/mirrors --dst /path/to/dst/mirrors [--dry-run] [--copy]
"""

import argparse
import json
import os
import shutil
import sys


SKIP_NAMES = {"config.json"}
SKIP_DIRS = {".git"}


# ---------------------------------------------------------------------------
# Crates
# ---------------------------------------------------------------------------

def merge_crates(src_crates, dst_crates, dry_run, copy):
    """Move (or copy) .crate files from src into dst, skipping any that already exist."""
    moved = skipped = 0

    for root, dirs, files in os.walk(src_crates):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if not filename.endswith(".crate"):
                continue

            src_file = os.path.join(root, filename)
            rel = os.path.relpath(src_file, src_crates)
            dst_file = os.path.join(dst_crates, rel)

            if os.path.exists(dst_file):
                skipped += 1
                continue

            if not dry_run:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                if copy:
                    shutil.copy2(src_file, dst_file)
                else:
                    shutil.move(src_file, dst_file)

            action = "copy" if copy else "move"
            print(f"  [{action}] {rel}")
            moved += 1

    return moved, skipped


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

def load_versions(path):
    """Return an ordered list of (vers, raw_line) from an index file."""
    entries = []
    seen = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                vers = json.loads(stripped).get("vers", "")
            except json.JSONDecodeError:
                vers = ""
            if vers not in seen:
                seen.add(vers)
                entries.append((vers, line if line.endswith("\n") else line + "\n"))
    return entries


def merge_index(src_index, dst_index, dry_run):
    """Merge src index files into dst, appending new versions and deduplicating by version."""
    created = appended = skipped = 0

    for root, dirs, files in os.walk(src_index):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if filename in SKIP_NAMES:
                continue

            src_file = os.path.join(root, filename)
            rel = os.path.relpath(src_file, src_index)
            dst_file = os.path.join(dst_index, rel)

            if not os.path.exists(dst_file):
                # Destination doesn't exist — just copy the file in
                if not dry_run:
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                print(f"  [create] {rel}")
                created += 1
            else:
                # Destination exists — append versions not already present
                dst_entries = load_versions(dst_file)
                dst_vers = {v for v, _ in dst_entries}

                src_entries = load_versions(src_file)
                new_entries = [(v, line) for v, line in src_entries if v not in dst_vers]

                if not new_entries:
                    skipped += 1
                    continue

                if not dry_run:
                    with open(dst_file, "a", encoding="utf-8") as f:
                        for _, line in new_entries:
                            f.write(line)

                print(f"  [append] {rel}: +{len(new_entries)} version(s)")
                appended += 1

    return created, appended, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Parse arguments and merge a source mirrors directory into a destination."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--src", required=True, help="Source mirrors directory")
    parser.add_argument("--dst", required=True, help="Destination mirrors directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be done without modifying any files",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy crate files instead of moving them (default: move)",
    )
    args = parser.parse_args()

    src = os.path.abspath(args.src)
    dst = os.path.abspath(args.dst)

    src_crates = os.path.join(src, "crates")
    dst_crates = os.path.join(dst, "crates")
    src_index = os.path.join(src, "crates.io-index")
    dst_index = os.path.join(dst, "crates.io-index")

    for path, label in [(src_crates, "src/crates"), (src_index, "src/crates.io-index"),
                        (dst_crates, "dst/crates"), (dst_index, "dst/crates.io-index")]:
        if not os.path.isdir(path):
            print(f"ERROR: directory not found: {path} ({label})", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("DRY RUN — no files will be modified.\n")

    print("=== Crates ===")
    moved, crates_skipped = merge_crates(src_crates, dst_crates, args.dry_run, args.copy)

    print("\n=== Index ===")
    created, appended, index_skipped = merge_index(src_index, dst_index, args.dry_run)

    verb = "Would" if args.dry_run else "Did"
    crate_action = "copy" if args.copy else "move"
    print(f"""
Done.
  Crates : {verb.lower()} {crate_action} {moved}, skipped {crates_skipped} (already exist)
  Index  : {verb.lower()} create {created}, append {appended}, skipped {index_skipped} (no new versions)
""")


if __name__ == "__main__":
    main()
