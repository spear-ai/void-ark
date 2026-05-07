#!/usr/bin/env python3
"""
build-mirror.py

Pipeline: Cargo.toml → panamax sync → prune → trim index → [tarball]

Steps:
  1. Generate Cargo.lock from the given Cargo.toml  (cargo generate-lockfile)
  2. Parse Cargo.lock for registry crate dependencies
  3. Run panamax sync via Docker to pull the full crates + index  (skippable)
  4. Prune crates/ to only the packages listed in Cargo.lock
  5. Trim crates.io-index/ to only entries with a local .crate file,
     deleting empty index files and empty directories
  6. (optional) Package crates/ and crates.io-index/ into a .tar.gz
     When --output is omitted the trimmed mirrors/ directory is kept as-is.

Usage:
    python3 build-mirror.py --cargo-toml /path/to/Cargo.toml [options]

Options:
    --cargo-toml  <path>   Path to the Cargo.toml  (required)
    --mirrors-dir <path>   Path to the mirrors directory
                           (default: ./mirrors next to this script)
    --output      <file>   Output tarball path; when omitted no tarball is
                           created and the mirrors/ directory is left intact
    --skip-sync            Skip the panamax sync step (useful if already synced)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, **kwargs):
    """Run a command, streaming output, and raise on failure."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def crate_prefix(name):
    """Return the crates.io directory prefix for a crate name."""
    n = len(name)
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    if n == 3:
        return os.path.join("3", name[0])
    return os.path.join(name[0:2], name[2:4])


# ---------------------------------------------------------------------------
# Step 1 – generate Cargo.lock
# ---------------------------------------------------------------------------

def generate_lockfile(cargo_toml):
    """Run cargo generate-lockfile and return the path to the resulting Cargo.lock."""
    cargo_dir = os.path.dirname(cargo_toml)
    lock_path = os.path.join(cargo_dir, "Cargo.lock")
    print(f"\n[1/5] Generating Cargo.lock in {cargo_dir}")
    run(["cargo", "generate-lockfile", "--manifest-path", cargo_toml])
    return lock_path


# ---------------------------------------------------------------------------
# Step 2 – parse Cargo.lock
# ---------------------------------------------------------------------------

def parse_lockfile(lock_path):
    """
    Return a set of (name, version) tuples for all registry-sourced packages.
    Parses the TOML manually to avoid external dependencies.
    """
    with open(lock_path, "r", encoding="utf-8") as f:
        content = f.read()

    needed = set()
    # Split on [[package]] boundaries; first chunk is the header, skip it
    for block in re.split(r"\[\[package\]\]", content)[1:]:
        name_m = re.search(r'^name\s*=\s*"([^"]+)"', block, re.MULTILINE)
        vers_m = re.search(r'^version\s*=\s*"([^"]+)"', block, re.MULTILINE)
        src_m  = re.search(r'^source\s*=\s*"registry\+', block, re.MULTILINE)
        if name_m and vers_m and src_m:
            needed.add((name_m.group(1), vers_m.group(1)))

    print(f"  Found {len(needed)} registry crate version(s) in Cargo.lock")
    return needed


# ---------------------------------------------------------------------------
# Step 3 – panamax sync
# ---------------------------------------------------------------------------

def panamax_sync(mirrors_dir):
    """Pull the full crates.io index and crate files into mirrors_dir via Docker."""
    print(f"\n[2/5] Running panamax sync  (this may take a long time)")
    run([
        "docker", "run", "--rm",
        "-v", f"{mirrors_dir}:/mirror",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "panamaxrs/panamax", "sync", "/mirror",
    ])


# ---------------------------------------------------------------------------
# Step 4 – prune crates/
# ---------------------------------------------------------------------------

def prune_crates(crates_dir, needed):
    """
    Delete any .crate file whose (name, version) is not in `needed`.
    Then remove empty directories bottom-up.
    """
    print(f"\n[3/5] Pruning crates/ to Cargo.lock dependencies")

    # Regex to split a stem like "serde_json-1.0.140" into name + version.
    # Version always starts with a digit; name may contain hyphens and underscores.
    stem_re = re.compile(r"^(.+?)-(\d+\..+)$")

    removed = kept = 0
    for root, dirs, files in os.walk(crates_dir, topdown=False):
        for filename in files:
            if not filename.endswith(".crate"):
                continue
            stem = filename[:-6]  # strip .crate
            m = stem_re.match(stem)
            if not m:
                continue
            name, vers = m.group(1), m.group(2)
            if (name, vers) in needed:
                kept += 1
            else:
                os.remove(os.path.join(root, filename))
                removed += 1

        # Remove directory if now empty
        try:
            os.rmdir(root)
        except OSError:
            pass

    print(f"  Kept {kept}, removed {removed} .crate file(s)")


# ---------------------------------------------------------------------------
# Step 5 – trim crates.io-index
# ---------------------------------------------------------------------------

SKIP_INDEX_NAMES = {"config.json"}
SKIP_INDEX_DIRS  = {".git"}


def get_available_versions(crates_dir, prefix, crate_name):
    """Return the set of versions present on disk for a given crate."""
    crate_path = os.path.join(crates_dir, prefix, crate_name)
    if not os.path.isdir(crate_path):
        return set()
    versions = set()
    for version in os.listdir(crate_path):
        crate_file = os.path.join(crate_path, version, f"{crate_name}-{version}.crate")
        if os.path.isfile(crate_file):
            versions.add(version)
    return versions


def trim_index(mirrors_dir):
    """Remove index entries and empty files/dirs for crates not present in crates/."""
    print(f"\n[4/5] Trimming crates.io-index")
    index_dir  = os.path.join(mirrors_dir, "crates.io-index")
    crates_dir = os.path.join(mirrors_dir, "crates")

    total_kept = total_removed = deleted_files = deleted_dirs = 0

    for root, dirs, files in os.walk(index_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_INDEX_DIRS]
        rel_root = os.path.relpath(root, index_dir)

        for filename in files:
            if filename in SKIP_INDEX_NAMES:
                continue

            abs_path = os.path.join(root, filename)
            prefix   = "" if rel_root == "." else rel_root

            available = get_available_versions(crates_dir, prefix, filename)

            with open(abs_path, "r", encoding="utf-8") as f:
                raw_lines = f.readlines()

            kept = []
            removed = 0
            for line in raw_lines:
                stripped = line.strip()
                if not stripped:
                    kept.append(line)
                    continue
                try:
                    vers = json.loads(stripped).get("vers", "")
                except json.JSONDecodeError:
                    kept.append(line)
                    continue
                if vers in available:
                    kept.append(line)
                else:
                    removed += 1

            if removed == 0:
                total_kept += len(kept)
                continue

            has_content = any(l.strip() for l in kept)
            if not has_content:
                os.remove(abs_path)
                deleted_files += 1
                total_removed += removed
            else:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.writelines(kept)
                total_kept    += len(kept)
                total_removed += removed

    # Remove empty index directories bottom-up
    for root, dirs, files in os.walk(index_dir, topdown=False):
        if root == index_dir:
            continue
        try:
            os.rmdir(root)
            deleted_dirs += 1
        except OSError:
            pass

    print(
        f"  Kept {total_kept} version entries, removed {total_removed}. "
        f"Deleted {deleted_files} empty index file(s) and {deleted_dirs} empty dir(s)."
    )


# ---------------------------------------------------------------------------
# Step 6 – create tarball
# ---------------------------------------------------------------------------

def create_tarball(mirrors_dir, output_path):
    """Package crates/ and crates.io-index/ from mirrors_dir into a .tar.gz at output_path."""
    print(f"\n[5/5] Creating tarball: {output_path}")
    with tarfile.open(output_path, "w:gz") as tar:
        for name in ("crates", "crates.io-index"):
            path = os.path.join(mirrors_dir, name)
            if os.path.exists(path):
                tar.add(path, arcname=name)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Done. {size_mb:.1f} MB → {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Parse arguments and run the full mirror build pipeline."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser.add_argument("--cargo-toml",  default=os.path.join(script_dir, "Cargo.toml"),
                        help="Path to Cargo.toml (default: root Cargo.toml — full environment)")
    parser.add_argument("--mirrors-dir", default=os.path.join(script_dir, "mirrors"),
                        help="Path to the mirrors directory (default: ./mirrors)")
    parser.add_argument("--output",      default=None,
                        help="Output tarball path; omit to leave mirrors/ directory intact")
    parser.add_argument("--skip-sync",   action="store_true",
                        help="Skip panamax sync (use if mirrors/ is already up to date)")
    args = parser.parse_args()

    cargo_toml  = os.path.abspath(args.cargo_toml)
    mirrors_dir = os.path.abspath(args.mirrors_dir)
    output_path = os.path.abspath(args.output) if args.output else None

    if not os.path.isfile(cargo_toml):
        print(f"ERROR: Cargo.toml not found: {cargo_toml}", file=sys.stderr)
        sys.exit(1)

    for cmd, required_without_skip in [(["cargo", "--version"], True), (["docker", "--version"], not args.skip_sync)]:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            if required_without_skip:
                print(f"ERROR: {cmd[0]} not found or not working", file=sys.stderr)
                sys.exit(1)

    print(f"Cargo.toml  : {cargo_toml}")
    print(f"Mirrors dir : {mirrors_dir}")
    print(f"Output      : {output_path if output_path else '(none — mirrors/ kept as-is)'}")
    print(f"Panamax sync: {'skipped' if args.skip_sync else 'enabled'}")

    lock_path = generate_lockfile(cargo_toml)
    needed    = parse_lockfile(lock_path)

    if not args.skip_sync:
        panamax_sync(mirrors_dir)
    else:
        print("\n[2/5] Skipping panamax sync (--skip-sync)")
        for subdir in ("crates", "crates.io-index"):
            path = os.path.join(mirrors_dir, subdir)
            if not os.path.isdir(path):
                print(f"ERROR: required directory not found: {path}", file=sys.stderr)
                sys.exit(1)

    prune_crates(os.path.join(mirrors_dir, "crates"), needed)
    trim_index(mirrors_dir)

    if output_path:
        create_tarball(mirrors_dir, output_path)
    else:
        print(f"\n[5/5] Skipping tarball — trimmed mirrors/ directory kept at {mirrors_dir}")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
