#!/usr/bin/env python3
"""Move the lowest atom of a slab to a target z value and optionally reset the c vector."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from ase.io import read, write

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()


DEFAULT_Z_OFFSET = 0.1
DEFAULT_VACUUM = 15.0
DEFAULT_OUTPUT = "POSCAR_bottomed.vasp"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read a POSCAR/CONTCAR, translate the slab so its lowest Cartesian z "
            "coordinate is at a requested value, and optionally reset the c vector."
        )
    )
    parser.add_argument("poscar", nargs="?", help="Optional positional input POSCAR file")
    parser.add_argument("-i", "--input", default="POSCAR", help="Input POSCAR or CONTCAR file (default: POSCAR)")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output POSCAR file name, default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--z-offset",
        type=float,
        default=DEFAULT_Z_OFFSET,
        help=f"Desired z position for the lowest atom after bottoming (default: {DEFAULT_Z_OFFSET})",
    )
    parser.add_argument(
        "--set-c-vacuum",
        type=float,
        default=DEFAULT_VACUUM,
        metavar="ANGSTROM",
        help=f"Reset the c lattice vector to z_max + this vacuum amount after bottoming (default: {DEFAULT_VACUUM})",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Write direct coordinates instead of Cartesian coordinates",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.poscar if args.poscar is not None else args.input)
    if not input_path.exists():
        print(f"Error: input file '{input_path}' not found", file=sys.stderr)
        return 2

    atoms = read(input_path, format="vasp")

    positions = atoms.get_positions()
    z_min = float(np.min(positions[:, 2]))
    z_shift = args.z_offset - z_min
    atoms.translate((0.0, 0.0, z_shift))

    z_max = float(np.max(atoms.get_positions()[:, 2]))
    new_c = z_max + args.set_c_vacuum

    cell = atoms.get_cell().array.copy()
    c_vector = cell[2]
    if np.linalg.norm(c_vector[:2]) > 1.0e-8:
        raise ValueError(
            "The third lattice vector is not aligned with Cartesian z. "
            "Please use a POSCAR with c vector along z."
        )

    cell[2] = (0.0, 0.0, new_c)
    atoms.set_cell(cell, scale_atoms=False)

    output_path = Path(args.output)
    write(output_path, atoms, format="vasp", direct=args.direct, vasp5=True)

    bottom_index = int(atoms.get_positions()[:, 2].argmin())
    top_index = int(atoms.get_positions()[:, 2].argmax())
    print(f"Input: {input_path}")
    print(f"Lowest atom index: {bottom_index + 1}, z -> {args.z_offset:.6f} A")
    print(f"Highest atom index: {top_index + 1}, z = {z_max:.6f} A")
    print(f"New c length: {new_c:.6f} A")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
