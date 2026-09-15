#!/usr/bin/env python3
"""Group POSCAR atoms by a user-specified element order."""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from actions_py.bootstrap import ensure_repo_root
ensure_repo_root()

from brain.poscar import sort_poscar


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=Path("POSCAR"))
    parser.add_argument(
        "elements",
        nargs="*",
        help="Element order, for example: Cu C H O N S",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("POSCAR_sorted"),
        help="Output POSCAR (default: POSCAR_sorted)",
    )
    args = parser.parse_args()
    sort_poscar(args.input, args.output, args.elements)
    order_text = " ".join(args.elements) if args.elements else "first appearance"
    print(f"Wrote sorted POSCAR to {args.output} (order: {order_text})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
