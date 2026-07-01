#!/usr/bin/env python3
"""
Build an fcc, bcc, or hcp metal bulk structure with ASE.

Examples:
  python get_metal_bulk.py Pt fcc --a 3.92
  python get_metal_bulk.py Fe bcc --a 2.87
  python get_metal_bulk.py Ru hcp --a 2.706 --c 4.282
  python get_metal_bulk.py Co hcp --a 2.51 --c-over-a 1.62 --output Co_hcp.vasp
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse

from ase.build import bulk
from ase.io import write


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a metal bulk structure with ASE.")
    parser.add_argument("metal", help="Element symbol, for example Pt, Fe, or Ru")
    parser.add_argument("structure", choices=("fcc", "bcc", "hcp"), help="Crystal structure type")
    parser.add_argument("--a", type=float, required=True, help="Lattice parameter a in Angstrom")
    parser.add_argument("--c", type=float, help="Lattice parameter c in Angstrom (required for hcp unless --c-over-a is given)")
    parser.add_argument("--c-over-a", type=float, dest="c_over_a", help="c/a ratio for hcp")
    parser.add_argument("--output", default="POSCAR", help="Output filename (default: POSCAR)")
    parser.add_argument("--cubic", action="store_true", help="Use a cubic conventional cell for fcc/bcc")
    args = parser.parse_args()

    if args.structure == "hcp":
        if args.c is not None and args.c_over_a is not None:
            parser.error("Use either --c or --c-over-a for hcp, not both.")
        if args.c is None and args.c_over_a is None:
            parser.error("hcp requires either --c or --c-over-a.")
        c_value = args.c if args.c is not None else args.a * args.c_over_a
        atoms = bulk(args.metal, "hcp", a=args.a, c=c_value)
    else:
        atoms = bulk(args.metal, args.structure, a=args.a, cubic=args.cubic)

    write(args.output, atoms, format="vasp", vasp5=True)
    print(f"Wrote {args.output}")
    print(f"Metal: {args.metal}")
    print(f"Structure: {args.structure}")
    print(f"a = {args.a:.6f} A")
    if args.structure == "hcp":
        print(f"c = {c_value:.6f} A")
    return 0


if __name__ == "__main__":
    sys.exit(main())
