import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

"""Legacy wrapper for linear-fit plotting."""

import argparse

from brain.data_analysis import plot_linear_fit


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot linear-fit data from a CSV file.")
    parser.add_argument("-i", "--input", default="data.csv", help="CSV file to read (default: data.csv)")
    parser.add_argument("--x-column", default="De", help="Column to use as x (default: De)")
    parser.add_argument("--y-column", default="Ea", help="Column to use as y (default: Ea)")
    parser.add_argument("-o", "--output", default="data.png", help="Output figure name (default: data.png)")
    args = parser.parse_args()

    out_name = plot_linear_fit(args.input, out=args.output, x_column=args.x_column, y_column=args.y_column)
    print(f"Wrote {out_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
