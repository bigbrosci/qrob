#!/usr/bin/env python3
"""
Normalize a VASP cell into a simpler orientation while preserving lattice lengths.

Modes:
- `ab-plane`: keep the original angle between `a` and `b`, place `a` on +x,
  keep `b` in the xy plane, and align `c` with +z.
- `diagonal`: replace the cell with an orthogonal box whose side lengths match
  the original `a`, `b`, and `c` magnitudes.

By default the script keeps Cartesian atom positions unchanged while updating
the lattice vectors. Use `--scale-atoms` if you want to preserve fractional
coordinates instead.
"""

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

import numpy as np
from ase.io import read, write


def build_diagonal_cell(old_cell: np.ndarray) -> np.ndarray:
    a_len = np.linalg.norm(old_cell[0])
    b_len = np.linalg.norm(old_cell[1])
    c_len = np.linalg.norm(old_cell[2])
    return np.array(
        [
            [a_len, 0.0, 0.0],
            [0.0, b_len, 0.0],
            [0.0, 0.0, c_len],
        ]
    )


def build_ab_plane_cell(old_cell: np.ndarray) -> np.ndarray:
    a_old = np.array(old_cell[0], dtype=float)
    b_old = np.array(old_cell[1], dtype=float)
    c_old = np.array(old_cell[2], dtype=float)

    a_len = np.linalg.norm(a_old)
    b_len = np.linalg.norm(b_old)
    c_len = np.linalg.norm(c_old)

    cos_theta = np.dot(a_old, b_old) / (a_len * b_len)
    cos_theta = float(np.clip(cos_theta, -1.0, 1.0))
    theta_ab = np.arccos(cos_theta)

    return np.array(
        [
            [a_len, 0.0, 0.0],
            [b_len * np.cos(theta_ab), b_len * np.sin(theta_ab), 0.0],
            [0.0, 0.0, c_len],
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize the orientation of a VASP cell.")
    parser.add_argument(
        "-i",
        "--input",
        default="POSCAR",
        help="Input POSCAR/CONTCAR file (default: POSCAR)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="POSCAR_new",
        help="Output filename (default: POSCAR_new)",
    )
    parser.add_argument(
        "--mode",
        choices=("ab-plane", "diagonal"),
        default="ab-plane",
        help="Cell normalization mode (default: ab-plane)",
    )
    parser.add_argument(
        "--scale-atoms",
        action="store_true",
        help="Preserve fractional coordinates instead of Cartesian positions",
    )
    parser.add_argument(
        "--cartesian",
        action="store_true",
        help="Write Cartesian coordinates instead of direct coordinates",
    )
    args = parser.parse_args()

    atoms = read(args.input, format="vasp")
    old_cell = atoms.get_cell().array

    if args.mode == "diagonal":
        new_cell = build_diagonal_cell(old_cell)
    else:
        new_cell = build_ab_plane_cell(old_cell)

    atoms.set_cell(new_cell, scale_atoms=args.scale_atoms)
    write(args.output, atoms, format="vasp", direct=not args.cartesian, vasp5=True)
    print(f"Wrote converted structure to {args.output} using mode={args.mode}")


if __name__ == "__main__":
    main()
