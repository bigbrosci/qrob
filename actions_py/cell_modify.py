import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import numpy as np
from ase.io import read, write

# 1. Read your original POSCAR
atoms = read('POSCAR', format='vasp')

# 2. Extract old cell vectors
old_cell = atoms.get_cell()  # This is a 3x3 array
a_old = np.array(old_cell[0])
b_old = np.array(old_cell[1])
c_old = np.array(old_cell[2])

# 3. Compute lengths
a_len = np.linalg.norm(a_old)
b_len = np.linalg.norm(b_old)
c_len = np.linalg.norm(c_old)

# 4. Angle between a_old and b_old
#    dot(a,b) = |a||b| cos(theta)
cos_theta = np.dot(a_old, b_old) / (a_len * b_len)
# Numerical issues can put cos_theta slightly out of [-1,1], so clip it:
cos_theta = max(min(cos_theta, 1.0), -1.0)
theta_ab = np.arccos(cos_theta)

# 5. Build a new 3x3 cell
#    a -> along x
#    b -> in xy-plane with angle theta_ab relative to a
#    c -> along z
new_cell = np.array([
    [a_len,                   0.0,                  0.0],
    [b_len*np.cos(theta_ab),  b_len*np.sin(theta_ab),  0.0],
    [0.0,                     0.0,                  c_len]
])

# 6. Update your ASE atoms object with the new cell.
#    Decide whether to 'scale' the atoms or not:
atoms.set_cell(new_cell, scale_atoms=False)

# 7. Write a new POSCAR
write('POSCAR_new', atoms, format='vasp', direct=True)

