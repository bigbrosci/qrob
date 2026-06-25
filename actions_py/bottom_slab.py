#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

"""Move the bottom atom of a POSCAR slab to z=0.1 A and reset c length."""

import argparse
from pathlib import Path

import numpy as np
from ase.io import read, write


BOTTOM_Z = 0.1
VACUUM_Z = 15.0
OUTPUT = "POSCAR_bot"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read a POSCAR, translate the slab so its lowest Cartesian z "
            "coordinate is 0.1 A, then set the cell c length to z_max + 15 A."
        )
    )
    parser.add_argument("poscar", help="Input POSCAR file")
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT,
        help=f"Output POSCAR file name, default: {OUTPUT}",
    )
    args = parser.parse_args()

    input_path = Path(args.poscar)
    atoms = read(input_path, format="vasp")

    positions = atoms.get_positions()
    z_min = positions[:, 2].min()
    z_shift = BOTTOM_Z - z_min
    atoms.translate((0.0, 0.0, z_shift))

    z_max = atoms.get_positions()[:, 2].max()
    new_c = z_max + VACUUM_Z

    cell = atoms.get_cell().array.copy()
    c_vector = cell[2]
    c_xy = np.linalg.norm(c_vector[:2])
    if c_xy > 1.0e-8:
        raise ValueError(
            "The third lattice vector is not aligned with Cartesian z. "
            "Please use a POSCAR with c vector along z."
        )

    cell[2] = (0.0, 0.0, new_c)
    atoms.set_cell(cell, scale_atoms=False)

    write(args.output, atoms, format="vasp", direct=True, sort=False, vasp5=True)

    bottom_index = int(atoms.get_positions()[:, 2].argmin())
    top_index = int(atoms.get_positions()[:, 2].argmax())
    print(f"Input: {input_path}")
    print(f"Lowest atom index: {bottom_index + 1}, z -> {BOTTOM_Z:.6f} A")
    print(f"Highest atom index: {top_index + 1}, z = {z_max:.6f} A")
    print(f"New c length: {new_c:.6f} A")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
