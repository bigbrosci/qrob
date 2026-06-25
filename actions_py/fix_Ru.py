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

from ase.io import read, write
from ase.constraints import FixAtoms

# Load the POSCAR file
atoms = read('POSCAR')

# Identify Ru atoms
ru_indices = [atom.index for atom in atoms if atom.symbol == 'Ru']

# Apply the constraint to fix the Ru atoms
constraint = FixAtoms(indices=ru_indices)
atoms.set_constraint(constraint)

# Save the updated POSCAR with the constraints applied
write('POSCAR_relax', atoms, format='vasp')

print("Modified POSCAR with fixed Ru atoms saved as 'POSCAR_relax'.")

