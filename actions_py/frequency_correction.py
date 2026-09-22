#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import numpy as np
from ase.io import read, write
import os


## Read POSCAR
print('Read POSCAR >>>\t')
model = read('POSCAR')
model_positions = model.get_positions()
print('Read POSCAR DONE >>>\t')
#Read OUTCAR and get the line number of the largest imaginary frequency
print('Read OUTCAR >>>\t')
from brain.outcar import get_imaginary_mode
vib_dis = np.array(get_imaginary_mode('OUTCAR', len(model)), dtype=float)

print('Read OUTCAR DONE >>>\t')         

print("Start Correcting the xyz coordinates with a factor of 0.1")
# 0.3 is the displacement factor to add to the poscar.
new_positions = model_positions + vib_dis * 0.1 
model.positions = new_positions
write('POSCAR_corrected', model, vasp5=True)
print("Done! Output file is named as: POSCAR_corrected")
