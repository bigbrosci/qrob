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
import ase
from  ase.io import read
from  ase.io import write
import numpy as np


A, B = [int(i)-1  for i in sys.argv[1:3]]

model = ase.io.read('POSCAR', format='vasp')

positions = model.get_positions().tolist()

positions[A], positions[B] = positions[B], positions[A]

model.positions = np.array(positions)

ase.io.write('POSCAR_swaped', model, format='vasp', vasp5=True)
