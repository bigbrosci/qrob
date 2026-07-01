#!/usr/bin/env python3
"""Run a simple linear regression on a CSV file."""

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

from brain.data_analysis import fit_linear_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a linear fit on two CSV columns.")
    parser.add_argument("file", help="CSV file to read")
    parser.add_argument("--x-column", default="IS", help="Column to use as x (default: IS)")
    parser.add_argument("--y-column", default="TS", help="Column to use as y (default: TS)")
    args = parser.parse_args()

    result = fit_linear_csv(args.file, x_column=args.x_column, y_column=args.y_column)
    print(result.slope, result.intercept, result.r_squared, result.mae, result.rmse)
    return 0


if __name__ == "__main__":
    sys.exit(main())
