#!/usr/bin/env python3
"""
Set selective-dynamics flags in a VASP POSCAR using one unified CLI.

You can select atoms by any combination of:
- atom indices or ranges
- element symbols
- bottom N layers
- Cartesian z cutoff

Examples:
  python fix_atoms.py -i POSCAR --indices 0-5 --flags FFF
  python fix_atoms.py -i POSCAR --elements C O --flags TTF
  python fix_atoms.py -i POSCAR --layers 2 --layer-threshold 0.5 --flags FFF
  python fix_atoms.py -i POSCAR --z-below 8.0 --flags FFF
  python fix_atoms.py -i POSCAR --indices 0-3 10 --elements Ru --z-below 7.5 --flags FFF

Index notes:
- All atom indices are 0-based.
"""

from __future__ import annotations

import argparse
import os
import re
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


def detect_input_file(path: str | None) -> str:
    if path is not None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input file not found: {path}")
        return path

    for candidate in ("POSCAR", "CONTCAR"):
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("Could not find POSCAR or CONTCAR in the current directory.")


def parse_index_token(token: str, natoms: int) -> list[int]:
    token = token.strip()
    if not token:
        return []

    single_match = re.fullmatch(r"\d+", token)
    if single_match:
        idx = int(token)
        return [idx] if 0 <= idx < natoms else []

    range_match = re.fullmatch(r"(\d*)-(\d*)", token)
    if not range_match:
        raise ValueError(f"Unrecognized index token: {token}")

    start_s, end_s = range_match.groups()
    if not start_s and not end_s:
        raise ValueError("Range token '-' is ambiguous. Use forms like '1-4' or '5-'.")

    start = int(start_s) if start_s else 0
    end = int(end_s) if end_s else natoms - 1

    if start > end:
        start, end = end, start
    start = max(start, 0)
    end = min(end, natoms - 1)
    return list(range(start, end + 1))


def parse_indices(tokens: list[str], natoms: int) -> list[int]:
    indices: list[int] = []
    for token in tokens:
        indices.extend(parse_index_token(token, natoms))
    return unique(indices)


def parse_elements(elements: list[str], symbols: list[str]) -> list[int]:
    wanted = {element.lower() for element in elements}
    return [idx for idx, symbol in enumerate(symbols) if symbol.lower() in wanted]


def find_layers(z_coords: np.ndarray, threshold: float) -> list[list[int]]:
    if len(z_coords) == 0:
        return []

    idx_z = sorted(enumerate(z_coords), key=lambda pair: pair[1])
    layers: list[list[int]] = [[idx_z[0][0]]]
    prev_z = idx_z[0][1]

    for idx, z in idx_z[1:]:
        if z - prev_z > threshold:
            layers.append([idx])
        else:
            layers[-1].append(idx)
        prev_z = z
    return layers


def unique(values: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def build_selection(args: argparse.Namespace, atoms) -> tuple[list[int], list[str]]:
    natoms = len(atoms)
    symbols = atoms.get_chemical_symbols()
    positions = atoms.get_positions()

    selected: list[int] = []
    reasons: list[str] = []

    if args.indices:
        idxs = parse_indices(args.indices, natoms)
        selected.extend(idxs)
        reasons.append(f"indices (0-based): {' '.join(args.indices)}")

    if args.elements:
        idxs = parse_elements(args.elements, symbols)
        selected.extend(idxs)
        reasons.append(f"elements: {' '.join(args.elements)}")

    if args.layers is not None:
        layers = find_layers(positions[:, 2], args.layer_threshold)
        n_fix = min(args.layers, len(layers))
        idxs = [idx for layer in layers[:n_fix] for idx in layer]
        selected.extend(idxs)
        reasons.append(f"bottom layers: {n_fix} (threshold={args.layer_threshold})")

    if args.z_below is not None:
        idxs = [idx for idx, pos in enumerate(positions) if pos[2] < args.z_below]
        selected.extend(idxs)
        reasons.append(f"z < {args.z_below}")

    return unique(selected), reasons


def parse_flags(flags: str) -> list[bool]:
    if not re.fullmatch(r"[TFtf]{3}", flags):
        raise ValueError("Flags must be exactly three T/F characters, for example FFF or TTF.")
    return [char.upper() == "T" for char in flags]


def _make_fix_scaled(idx: int, mask: tuple[bool, bool, bool]):
    try:
        return FixScaled([idx], mask=mask)
    except TypeError:
        return FixScaled(a=[idx], mask=mask)


def apply_selective_dynamics(atoms: Atoms, selective: np.ndarray) -> Atoms:
    if selective.shape != (len(atoms), 3):
        raise ValueError("Selective-dynamics array must have shape (N, 3).")

    # ASE's VASP writer understands selective dynamics through constraints.
    # In this workflow, True means a T flag (free) and False means an F flag (fixed).
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
        description="Fix or relax atoms in a VASP POSCAR by indices, elements, layers, and/or z cutoff.",
        epilog=(
            "Examples:\n"
            "  python fix_atoms.py -i POSCAR --indices 0-5 --flags FFF\n"
            "  python fix_atoms.py -i POSCAR --elements C O --flags TTF\n"
            "  python fix_atoms.py -i POSCAR --layers 2 --layer-threshold 0.5 --flags FFF\n"
            "  python fix_atoms.py -i POSCAR --z-below 8.0 --flags FFF\n"
            "  python fix_atoms.py -i POSCAR --elements Ru --flags FFF\n"
            "  python fix_atoms.py -i POSCAR --indices 0-5 --flags TTT"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-i", "--input", help="Input POSCAR/CONTCAR file (default: POSCAR or CONTCAR in cwd)")
    parser.add_argument(
        "-o",
        "--output",
        help="Output filename (default: <input>_fixed)",
    )
    parser.add_argument(
        "--flags",
        default="FFF",
        help="Selective-dynamics flags applied to the selected atoms, e.g. FFF, TTF, TTT (default: FFF)",
    )
    parser.add_argument(
        "--indices",
        nargs="+",
        help="Atom indices or ranges such as 0 3 5-8 12- (0-based)",
    )
    parser.add_argument(
        "--elements",
        nargs="+",
        help="Element symbols to select, for example --elements Ru O",
    )
    parser.add_argument(
        "--layers",
        type=int,
        help="Fix the bottom N layers based on Cartesian z grouping",
    )
    parser.add_argument(
        "--layer-threshold",
        type=float,
        default=0.5,
        help="z-gap threshold in Angstrom used to separate layers (default: 0.5)",
    )
    parser.add_argument(
        "--z-below",
        type=float,
        help="Select atoms with Cartesian z smaller than this value in Angstrom",
    )
    parser.add_argument(
        "--cartesian",
        action="store_true",
        help="Write Cartesian coordinates instead of direct coordinates",
    )
    args = parser.parse_args(argv)

    if not any([args.indices, args.elements, args.layers is not None, args.z_below is not None]):
        parser.error("At least one selector is required: --indices, --elements, --layers, or --z-below.")

    infile = detect_input_file(args.input)
    atoms = read(infile, format="vasp")
    natoms = len(atoms)

    selected, reasons = build_selection(args, atoms)
    if not selected:
        print("No atoms matched the requested selectors. Nothing was written.")
        return 0

    if "selective_dynamics" in atoms.arrays and atoms.arrays["selective_dynamics"].shape == (natoms, 3):
        selective = atoms.arrays["selective_dynamics"].copy()
    else:
        selective = np.ones((natoms, 3), dtype=bool)

    flag_values = np.array(parse_flags(args.flags), dtype=bool)
    for idx in selected:
        selective[idx, :] = flag_values

    output = args.output if args.output else f"{infile}_fixed"
    output_atoms = apply_selective_dynamics(atoms, selective)
    write(
        output,
        output_atoms,
        format="vasp",
        direct=not args.cartesian,
        vasp5=True,
    )

    print(f"Input: {infile}")
    print(f"Output: {output}")
    print(f"Selected {len(selected)} atom(s) using: {', '.join(reasons)}")
    print(f"Applied selective-dynamics flags: {' '.join(flag.upper() for flag in args.flags)}")
    if args.indices:
        print("Index mode: 0-based")
    return 0


if __name__ == "__main__":
    sys.exit(main())
