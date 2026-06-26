from pathlib import Path
import sys
import os

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
import argparse
from ase.io import read, write
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description='Bottom a POSCAR/CONTCAR file and optionally reset the c vector with added vacuum.'
    )
    parser.add_argument('-i', '--input', default='POSCAR', help='Input POSCAR or CONTCAR (defaults to POSCAR)')
    parser.add_argument('--z-offset', type=float, default=0.1, help='Desired z position for the lowest atom after bottoming')
    parser.add_argument('--out-bottom', default='POSCAR_bottomed.vasp', help='Bottomed output filename')
    parser.add_argument(
        '--set-c-vacuum',
        type=float,
        default=15.0,
        metavar='ANGSTROM',
        help='Reset the c lattice vector to z_max + this vacuum amount after bottoming (default: 15.0)',
    )
    parser.add_argument(
        '--direct',
        action='store_true',
        help='Write direct coordinates instead of Cartesian coordinates',
    )
    args = parser.parse_args()

    infile = args.input
    if not os.path.exists(infile):
        print(f"Error: input file '{infile}' not found", file=sys.stderr)
        sys.exit(2)

    atoms = read(infile, format='vasp')

    # Bottoming: translate so minimum z becomes z_offset
    positions = atoms.get_positions()
    lowest_z = float(np.min(positions[:, 2]))
    dz = args.z_offset - lowest_z
    atoms.translate([0.0, 0.0, dz])

    if args.set_c_vacuum is not None:
        z_max = float(np.max(atoms.get_positions()[:, 2]))
        new_c = z_max + args.set_c_vacuum
        cell = atoms.get_cell().array.copy()
        c_vector = cell[2]
        if np.linalg.norm(c_vector[:2]) > 1.0e-8:
            raise ValueError(
                'The third lattice vector is not aligned with Cartesian z. '
                'Please use a POSCAR with c vector along z.'
            )
        cell[2] = (0.0, 0.0, new_c)
        atoms.set_cell(cell, scale_atoms=False)

    write(args.out_bottom, atoms, format='vasp', direct=args.direct, vasp5=True)
    print(f"Wrote bottomed structure to {args.out_bottom} (translated by dz={dz:.4f} Å)")
    if args.set_c_vacuum is not None:
        print(f"Reset c lattice vector to z_max + {args.set_c_vacuum:.4f} Å vacuum")



if __name__ == '__main__':
    main()
