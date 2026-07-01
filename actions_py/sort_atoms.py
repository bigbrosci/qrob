#!/usr/bin/env python3
"""
Sort atoms in a VASP POSCAR with one unified CLI.

Supported workflows:
- group atoms by element, optionally with a custom element order
- sort atoms globally by Cartesian z
- sort atoms by Cartesian z within each element group
- optionally mark atoms below a z cutoff as fixed in the output

Examples:
  python sort_atoms.py -i POSCAR --mode element
  python sort_atoms.py -i POSCAR --mode element --elements Fe C H O
  python sort_atoms.py -i POSCAR --mode z
  python sort_atoms.py -i POSCAR --mode z-within-element --elements Ni C H O
  python sort_atoms.py -i POSCAR --mode element --elements Ru O --fix-below 2.0
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.constraints import FixScaled
from ase.io import read, write

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def detect_input_file(path: str | None) -> str:
    if path is not None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input file not found: {path}")
        return path

    for candidate in ("POSCAR", "CONTCAR"):
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("Could not find POSCAR or CONTCAR in the current directory.")


def order_by_element(symbols: list[str], requested_order: list[str] | None) -> list[int]:
    present_order = unique_in_order(symbols)
    if requested_order:
        canonical_order = requested_order + [sym for sym in present_order if sym not in requested_order]
    else:
        canonical_order = sorted(present_order)

    indices: list[int] = []
    for element in canonical_order:
        indices.extend(i for i, symbol in enumerate(symbols) if symbol == element)
    return indices


def order_by_z(positions: np.ndarray) -> list[int]:
    return sorted(range(len(positions)), key=lambda idx: (positions[idx, 2], idx))


def order_by_z_within_element(symbols: list[str], positions: np.ndarray, requested_order: list[str] | None) -> list[int]:
    element_order = requested_order + [sym for sym in unique_in_order(symbols) if sym not in requested_order] if requested_order else unique_in_order(symbols)
    indices: list[int] = []
    for element in element_order:
        group = [i for i, symbol in enumerate(symbols) if symbol == element]
        group.sort(key=lambda idx: (positions[idx, 2], idx))
        indices.extend(group)
    return indices


def reorder_selective_dynamics(old_flags: np.ndarray | None, order: list[int], natoms: int) -> np.ndarray | None:
    if old_flags is None or old_flags.shape != (natoms, 3):
        return None
    return old_flags[order].copy()


def apply_fix_below(selective: np.ndarray | None, sorted_positions: np.ndarray, z_cut: float) -> np.ndarray:
    natoms = len(sorted_positions)
    if selective is None:
        selective = np.ones((natoms, 3), dtype=bool)

    for idx, pos in enumerate(sorted_positions):
        if pos[2] < z_cut:
            selective[idx, :] = False
    return selective


def _make_fix_scaled(idx: int, mask: tuple[bool, bool, bool]):
    try:
        return FixScaled([idx], mask=mask)
    except TypeError:
        return FixScaled(a=[idx], mask=mask)


def apply_selective_dynamics(atoms: Atoms, selective: np.ndarray | None) -> Atoms:
    if selective is None:
        return atoms.copy()

    constraints = []
    for idx in range(len(atoms)):
        mask = tuple(not bool(flag) for flag in selective[idx, :])
        if any(mask):
            constraints.append(_make_fix_scaled(idx, mask))

    updated_atoms = atoms.copy()
    if constraints:
        updated_atoms.set_constraint(constraints)
    else:
        updated_atoms.set_constraint([])
    return updated_atoms


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sort atoms in a VASP POSCAR by element order and/or Cartesian z.",
        epilog=(
            "Examples:\n"
            "  python sort_atoms.py -i POSCAR --mode element\n"
            "  python sort_atoms.py -i POSCAR --mode element --elements Fe C H O\n"
            "  python sort_atoms.py -i POSCAR --mode z\n"
            "  python sort_atoms.py -i POSCAR --mode z-within-element --elements Ni C H O\n"
            "  python sort_atoms.py -i POSCAR --mode element --elements Ru O --fix-below 2.0"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-i", "--input", help="Input POSCAR/CONTCAR file (default: POSCAR or CONTCAR in cwd)")
    parser.add_argument("-o", "--output", help="Output filename (default: <input>_sorted)")
    parser.add_argument(
        "--mode",
        choices=("element", "z", "z-within-element"),
        default="element",
        help="Sorting mode (default: element)",
    )
    parser.add_argument(
        "--elements",
        nargs="+",
        help="Custom element order for element-based modes, for example --elements Fe C H O",
    )
    parser.add_argument(
        "--fix-below",
        type=float,
        help="After sorting, mark atoms with Cartesian z smaller than this value as F F F",
    )
    parser.add_argument(
        "--cartesian",
        action="store_true",
        help="Write Cartesian coordinates instead of direct coordinates",
    )
    args = parser.parse_args(argv)

    infile = detect_input_file(args.input)
    atoms = read(infile, format="vasp")
    symbols = atoms.get_chemical_symbols()
    positions = atoms.get_positions()
    natoms = len(atoms)

    if args.mode == "element":
        order = order_by_element(symbols, args.elements)
    elif args.mode == "z":
        order = order_by_z(positions)
    else:
        order = order_by_z_within_element(symbols, positions, args.elements)

    sorted_atoms = atoms[order]

    old_selective = atoms.arrays.get("selective_dynamics")
    selective = reorder_selective_dynamics(old_selective, order, natoms)
    if args.fix_below is not None:
        selective = apply_fix_below(selective, sorted_atoms.get_positions(), args.fix_below)

    output = args.output if args.output else f"{infile}_sorted"
    output_atoms = apply_selective_dynamics(sorted_atoms, selective)
    write(
        output,
        output_atoms,
        format="vasp",
        direct=not args.cartesian,
        vasp5=True,
    )

    print(f"Input: {infile}")
    print(f"Output: {output}")
    print(f"Mode: {args.mode}")
    if args.elements:
        print(f"Element order: {' '.join(args.elements)}")
    if args.fix_below is not None:
        print(f"Applied F F F to atoms with z < {args.fix_below} A after sorting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
