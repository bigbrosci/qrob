#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
"""
Use ase to convert xyz files to POSCAR
"""

import sys
import os
import numpy as np
from ase.io import read, write
from ase import Atoms


def has_valid_cell(atoms: Atoms) -> bool:
    cell = np.asarray(atoms.get_cell())
    # consider cell valid if any diagonal element > 1e-6
    return not np.allclose(cell, 0.0)


def main():
    if len(sys.argv) < 2:
        print('Usage: xyz_to_poscar.py FILE.xyz [OUTPOSCAR]')
        sys.exit(2)

    xyz_in = sys.argv[1]
    out_poscar = sys.argv[2] if len(sys.argv) > 2 else 'POSCAR'

    if not os.path.exists(xyz_in):
        print(f"Error: '{xyz_in}' not found", file=sys.stderr)
        sys.exit(3)

    # Try reading with ASE. extxyz will be detected automatically if present.
    try:
        atoms = read(xyz_in)
    except Exception:
        # try explicit formats as fallback
        try:
            atoms = read(xyz_in, format='extxyz')
        except Exception:
            atoms = read(xyz_in, format='xyz')

    # If ASE returned a list/Trajectory, take the first frame
    try:
        from ase.io.trajectory import Trajectory
        if hasattr(atoms, '__len__') and not isinstance(atoms, Atoms):
            atoms = atoms[0]
    except Exception:
        pass

    # If the XYZ contains cell information (extended xyz), ASE should have set it.
    if has_valid_cell(atoms):
        atoms.set_pbc((True, True, True))
        print('Detected cell in XYZ: writing POSCAR with provided cell')
    else:
        # no cell present: use large vacuum box
        atoms.set_cell([(40.0, 0.0, 0.0), (0.0, 40.0, 0.0), (0.0, 0.0, 40.0)])
        atoms.set_pbc((True, True, True))
        print('No cell found in XYZ: using 40x40x40 Å cell')

    # Ensure positions wrapped into cell
    atoms.wrap()

    write(out_poscar, atoms, format='vasp', vasp5=True)
    print(f'Wrote POSCAR -> {out_poscar}')


if __name__ == '__main__':
    main()





