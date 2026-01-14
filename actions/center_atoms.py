#!/usr/bin/env python3 
# center the clusters or gas phase species in the box 

import sys
from ase.io import read, write

def wrap_atoms(filename):
    # Read the structure from the file
    atoms = read(filename)

    # Center the atoms in the unit cell
    #atoms.center(about=(0.5, 0.5, 0.5))
    atoms.center()

    # Wrap the atoms using the pbc (periodic boundary conditions) and cell
    atoms.wrap(pbc=True)

    filename_out = filename + '_centered'
    # Save the modified structure back to the file
    write(filename_out, atoms, format='vasp', vasp5=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 wrap_atoms.py POSCAR")
    else:
        wrap_atoms(sys.argv[1])

