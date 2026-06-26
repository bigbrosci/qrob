#!/usr/bin/env python3
"""Merge one or more existing ML_AB files into a single output file."""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse

from brain.ml_ab import MLABDataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge multiple ML_AB files into one dataset.")
    parser.add_argument("inputs", nargs="+", help="Input ML_AB files to merge")
    parser.add_argument("--output", default="ML_AB_merged", help="Output filename (default: ML_AB_merged)")
    args = parser.parse_args()

    datasets = [MLABDataset.read_file(path) for path in args.inputs]
    merged = datasets[0]
    for dataset in datasets[1:]:
        merged = merged + dataset

    output_path = merged.write_file(args.output)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
