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
    parser = argparse.ArgumentParser(description='Bottom a POSCAR/CONTCAR file.')
    parser.add_argument('-i', '--input', default='POSCAR', help='Input POSCAR or CONTCAR (defaults to POSCAR)')
    parser.add_argument('--z-offset', type=float, default=0.1, help='Desired z position for the lowest atom after bottoming')
    parser.add_argument('--out-bottom', default='POSCAR_bottomed.vasp', help='Bottomed output filename')
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
    write(args.out_bottom, atoms, format='vasp', vasp5=True)
    print(f"Wrote bottomed structure to {args.out_bottom} (translated by dz={dz:.4f} Å)")



if __name__ == '__main__':
    main()
