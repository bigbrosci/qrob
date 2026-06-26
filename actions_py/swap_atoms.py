#!/usr/bin/env python3
"""
Swap atom positions in one POSCAR or copy atom positions between two structures.

Modes:
- `within`: swap the Cartesian positions of atoms inside one structure
- `between`: replace selected atom positions in file A with positions from file B

Examples:
  python swap_atoms.py within 3 8
  python swap_atoms.py within 3 8 -i POSCAR -o POSCAR_swapped
  python swap_atoms.py between -A POSCAR_A -B POSCAR_B -s 1 2 -f 5 6
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse

import ase.io
import numpy as np


def swap_within(input_file: str, output_file: str, atom_a: int, atom_b: int) -> None:
    model = ase.io.read(input_file, format="vasp")
    positions = model.get_positions().copy()

    idx_a = atom_a - 1
    idx_b = atom_b - 1
    positions[[idx_a, idx_b]] = positions[[idx_b, idx_a]]

    model.positions = positions
    ase.io.write(output_file, model, format="vasp", vasp5=True)


def swap_between(file_a: str, file_b: str, atoms_a: list[int], atoms_b: list[int], output_file: str) -> None:
    if len(atoms_a) != len(atoms_b):
        raise ValueError("The number of source atoms and replacement atoms must match.")

    model_a = ase.io.read(file_a, format="vasp")
    model_b = ase.io.read(file_b, format="vasp")

    positions_a = model_a.get_positions()
    positions_b = model_b.get_positions()

    for idx_a, idx_b in zip(atoms_a, atoms_b):
        positions_a[idx_a - 1] = positions_b[idx_b - 1]

    model_a.positions = np.array(positions_a)
    ase.io.write(output_file, model_a, format="vasp", vasp5=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Swap atom positions within one POSCAR or between two files.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    within = subparsers.add_parser("within", help="Swap two atom positions inside one structure")
    within.add_argument("atom_a", type=int, help="First atom index (1-based)")
    within.add_argument("atom_b", type=int, help="Second atom index (1-based)")
    within.add_argument("-i", "--input", default="POSCAR", help="Input POSCAR file (default: POSCAR)")
    within.add_argument("-o", "--output", default="POSCAR_swapped", help="Output file (default: POSCAR_swapped)")

    between = subparsers.add_parser("between", help="Replace positions in file A using positions from file B")
    between.add_argument("-A", "--file-a", required=True, help="Atoms in file A will be replaced")
    between.add_argument("-B", "--file-b", required=True, help="Atoms in file B provide the replacement positions")
    between.add_argument("-s", "--source", nargs="+", required=True, type=int, help="1-based atom indices in file A")
    between.add_argument("-f", "--from-file-b", nargs="+", required=True, type=int, help="1-based atom indices in file B")
    between.add_argument("-o", "--output", default="POSCAR", help="Output file (default: POSCAR)")

    args = parser.parse_args()

    if args.mode == "within":
        swap_within(args.input, args.output, args.atom_a, args.atom_b)
        print(f"Wrote {args.output}")
    else:
        swap_between(args.file_a, args.file_b, args.source, args.from_file_b, args.output)
        print(f"Wrote {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
