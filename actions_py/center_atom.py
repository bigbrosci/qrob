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

# Read the POSCAR file containing a cluster in a box
cluster = read('POSCAR', format='vasp')

# Center the cluster in the box
#cluster.center(about=(0.5, 0.5, 0.5))
cluster.center()

# Wrap atoms into the unit cell
cluster.wrap()

# Save the centered structure as 'POSCAR_centered'
write('POSCAR_centered', cluster, format='vasp', vasp5=True)
