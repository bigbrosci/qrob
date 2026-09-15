#!/usr/bin/env python3
"""Convert a MOL structure to a POSCAR using a slab template."""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from actions_py.bootstrap import ensure_repo_root
ensure_repo_root()

from brain.poscar import convert_mol_to_poscar


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mol_file", type=Path, help="Input MOL file")
    parser.add_argument("--slab", type=Path, default=Path("POSCAR_hollow"))
    parser.add_argument("--output", type=Path, default=Path("POSCAR_mol"))
    args = parser.parse_args()
    convert_mol_to_poscar(args.mol_file, args.slab, args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
