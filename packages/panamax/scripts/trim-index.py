#!/usr/bin/env python3
"""
trim-index.py

Trims crates.io-index entries down to only the versions that exist
in the local crates/ directory.

For each index file, reads JSON lines (one per version) and removes
any line whose corresponding .crate file is not present in crates/.

Usage:
    python3 trim-index.py [--mirrors-dir /path/to/mirrors] [--dry-run]
"""

import argparse
import json
import os
import sys


SKIP_NAMES = {"config.json"}
SKIP_DIRS = {".git"}


def get_available_versions(crates_dir, prefix, crate_name):
    """Return a set of versions available on disk for a given crate."""
    crate_path = os.path.join(crates_dir, prefix, crate_name)
    if not os.path.isdir(crate_path):
        return set()
    versions = set()
    for version in os.listdir(crate_path):
        crate_file = os.path.join(crate_path, version, f"{crate_name}-{version}.crate")
        if os.path.isfile(crate_file):
            versions.add(version)
    return versions


def iter_index_files(index_dir):
    """Yield (absolute_path, prefix, crate_name) for every index entry file."""
    for root, dirs, files in os.walk(index_dir):
        # Skip hidden dirs like .git in-place so os.walk won't descend
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        rel_root = os.path.relpath(root, index_dir)

        for filename in files:
            if filename in SKIP_NAMES:
                continue

            abs_path = os.path.join(root, filename)
            crate_name = filename

            # Derive prefix: everything between index_dir and the filename
            if rel_root == ".":
                # Shouldn't happen for valid crates (they're always nested),
                # but handle gracefully
                prefix = ""
            else:
                prefix = rel_root

            yield abs_path, prefix, crate_name


def trim_index_file(abs_path, prefix, crate_name, crates_dir, dry_run, delete_empty):
    """
    Filter the index file to only keep lines whose .crate file exists.
    If delete_empty is True and no versions remain, delete the file.
    Returns (kept, removed, deleted) where deleted is bool.
    """
    with open(abs_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    available = get_available_versions(crates_dir, prefix, crate_name)

    kept = []
    removed_count = 0

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            # Preserve blank lines as-is
            kept.append(line)
            continue
        try:
            entry = json.loads(stripped)
            version = entry.get("vers", "")
        except json.JSONDecodeError:
            # Keep malformed lines rather than silently dropping them
            kept.append(line)
            continue

        if version in available:
            kept.append(line)
        else:
            removed_count += 1

    if removed_count == 0:
        return len(kept), 0, False

    # Check if any real (non-blank) content remains
    has_content = any(line.strip() for line in kept)

    if delete_empty and not has_content:
        if not dry_run:
            os.remove(abs_path)
        return 0, removed_count, True

    if not dry_run:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(kept)

    return len(kept), removed_count, False


def main():
    """Parse arguments and trim the crates.io-index to match local crates/."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--mirrors-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to the mirrors directory (default: directory containing this script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be changed without modifying any files",
    )
    parser.add_argument(
        "--delete-empty",
        action="store_true",
        help="Delete index files that have no remaining versions after trimming",
    )
    args = parser.parse_args()

    mirrors_dir = os.path.abspath(args.mirrors_dir)
    index_dir = os.path.join(mirrors_dir, "crates.io-index")
    crates_dir = os.path.join(mirrors_dir, "crates")

    if not os.path.isdir(index_dir):
        print(f"ERROR: index directory not found: {index_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(crates_dir):
        print(f"ERROR: crates directory not found: {crates_dir}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("DRY RUN — no files will be modified.\n")

    total_files = 0
    total_kept = 0
    total_removed = 0
    modified_files = 0
    deleted_files = 0

    for abs_path, prefix, crate_name in iter_index_files(index_dir):
        kept, removed, deleted = trim_index_file(
            abs_path, prefix, crate_name, crates_dir, args.dry_run, args.delete_empty
        )
        total_files += 1
        total_kept += kept
        total_removed += removed
        if removed:
            modified_files += 1
            rel = os.path.relpath(abs_path, mirrors_dir)
            if deleted:
                deleted_files += 1
                print(f"  {rel}: deleted (all {removed} version(s) missing)")
            else:
                print(f"  {rel}: kept {kept}, removed {removed} version(s)")

    # Remove empty directories bottom-up (leaves first)
    deleted_dirs = 0
    for root, dirs, files in os.walk(index_dir, topdown=False):
        if root == index_dir:
            continue
        try:
            os.rmdir(root)  # only succeeds if directory is empty
            deleted_dirs += 1
            if args.dry_run:
                rel = os.path.relpath(root, mirrors_dir)
                print(f"  {rel}: would delete empty dir")
        except OSError:
            pass  # not empty, leave it

    verb = "Would" if args.dry_run else "Did"
    print(
        f"\nDone. Scanned {total_files} index file(s). "
        f"{verb} modify {modified_files} file(s) "
        f"({verb.lower()} delete {deleted_files} empty file(s), "
        f"{deleted_dirs} empty dir(s)). "
        f"Kept {total_kept} version entries, removed {total_removed}."
    )


if __name__ == "__main__":
    main()
