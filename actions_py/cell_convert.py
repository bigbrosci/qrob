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
import numpy as np

# 1. Read in your original structure from a VASP POSCAR
atoms = read('POSCAR', format='vasp')

# 2. Extract the original cell vectors
old_cell = atoms.get_cell()  # 3x3 matrix

# 3. Compute the lengths of each lattice vector
a_len = np.linalg.norm(old_cell[0])  # length of vector a
b_len = np.linalg.norm(old_cell[1])  # length of vector b
c_len = np.linalg.norm(old_cell[2])  # length of vector c

# 4. Construct a new cell with zero off-diagonal components
new_cell = np.array([[a_len,    0.0,     0.0],
                     [0.0,      b_len,   0.0],
                     [0.0,      0.0,     c_len]])

# 5. Decide how to place the atoms:
#    (a) Keep fractional coords the same => absolute positions will change
#    (b) Keep absolute (Cartesian) coords => fractional coords will change

# (a) Keep fractional coordinates the same:
atoms.set_cell(new_cell, scale_atoms=False)

# (b) If you instead want to keep absolute positions unchanged:
# atoms.set_cell(new_cell, scale_atoms=True)

# 6. Write out a new POSCAR
# Use "direct=True" if you want VASP to see the positions in fractional (direct) coords
write('POSCAR_new', atoms, format='vasp', direct=True)

