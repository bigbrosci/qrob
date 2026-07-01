#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

"""Legacy wrapper for NEB plotting."""

import argparse

from brain.data_analysis import plot_neb_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot a NEB energy profile from image folders.")
    parser.add_argument("name", nargs="?", default="neb", help="Output name prefix (default: neb)")
    parser.add_argument("--dirs", help="Comma-separated image directories (default: auto-detect)")
    parser.add_argument("-o", "--output", help="Output figure name (default: <name>.png)")
    args = parser.parse_args()

    dirs = None
    if args.dirs:
        dirs = [entry.strip() for entry in args.dirs.split(",") if entry.strip()]

    out_name = plot_neb_profile(dirs=dirs, name=args.name, out=args.output)
    print(f"Wrote {out_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
