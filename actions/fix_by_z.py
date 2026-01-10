#!/usr/bin/env python3
"""
Fix atoms by z coordinate using ASE.

Usage:
  python3 fix_by_z.py Z [FILE]

Arguments:
  Z     : z cutoff (Angstrom). All atoms with z < Z will be fixed, atoms with z >= Z will be relaxed.
  FILE  : optional input POSCAR filename (default: POSCAR)

Output:
  Writes <input>_fixed (e.g. POSCAR_fixed) with updated selective dynamics.
"""

import sys
import os
import math
from ase.io import read, write
import numpy as np


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) < 1:
        print("Usage: fix_by_z.py Z [FILE]")
        return 2

    try:
        z_cut = float(argv[0])
    except ValueError:
        print(f"Error: Z must be a number (got '{argv[0]}').")
        return 3

    infile = argv[1] if len(argv) > 1 else 'POSCAR'
    if not os.path.exists(infile):
        print(f"Error: input file '{infile}' not found.")
        return 4

    try:
        atoms = read(infile, format='vasp')
    except Exception as e:
        print(f"Error: failed to read '{infile}': {e}")
        return 5

    positions = atoms.get_positions()  # Cartesian
    natoms = len(atoms)

    # Prepare selective dynamics array: True = movable, False = fixed
    sel = np.ones((natoms, 3), dtype=bool)

    below = 0
    above = 0
    for i, pos in enumerate(positions):
        z = pos[2]
        if z < z_cut:
            sel[i, :] = False
            below += 1
        else:
            sel[i, :] = True
            above += 1

    atoms.set_array('selective_dynamics', sel)

    out_name = os.path.splitext(infile)[0] + '_fixed'
    try:
        write(out_name, atoms, format='vasp', vasp5=True)
    except Exception as e:
        print(f"Error: failed to write '{out_name}': {e}")
        return 6

    print(f"Wrote '{out_name}': fixed {below} atoms (z < {z_cut}), relaxed {above} atoms (z >= {z_cut}).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
