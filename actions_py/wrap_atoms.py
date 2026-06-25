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

import sys
from ase.io import read, write

def wrap_atoms(filename):
    # Read the structure from the file
    atoms = read(filename)

    # Center the atoms in the unit cell
    atoms.center()

    # Wrap the atoms using the pbc (periodic boundary conditions) and cell
    atoms.wrap(pbc=True)

    # Save the modified structure back to the file
    write(filename, atoms)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 wrap_atoms.py POSCAR")
    else:
        wrap_atoms(sys.argv[1])


