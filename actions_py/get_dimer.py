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
@author: qli
Created on Thu Jun  2 22:09:18 2022
Creat POSCAR for improved dimer calculations
1) run frequency calculation: 
IBRION = 5
POTIM = 0.015
NFREE = 2
NWRITE = 3 ### Must be 3
2) run this script:
get_dimer.py 
3) use the POSCAR for IDM calc.
NSW = 100           
Prec=Normal
IBRION=44           !  use the dimer method as optimization engine
EDIFFG=-0.05
POTIM = 0.05
    
"""

import numpy as np
from ase.io import read, write
import os
from sys import exit


# os.chdir('/home/win.udel.edu/qli/Desktop/freq/')

model = read('POSCAR_relax') ### POSCAR_relax is the POSCAR before freq calculations, that means the some atoms are not fixed.
model_positions = model.get_positions()

# print(model_positions)
# print(len(model))

from brain.outcar import get_imaginary_mode
try:
    vib_dis = get_imaginary_mode('OUTCAR', len(model), mass_weighted=True)
except ValueError as exc:
    print(f"{exc}. Check frequency results; NWRITE must be 3.")
    sys.exit(1)

model.write('POSCAR_dimer', vasp5=True)
pos_dimer = open('POSCAR_dimer', 'a')
pos_dimer.write('  ! Dimer Axis Block\n')

for displacement in vib_dis:
    pos_dimer.write(' '.join(displacement) + '\n')

pos_dimer.close()
print('''
      DONE!
      Output file is named as: POSCAR_dimer and can be used for dimer calculations.
      Don't forget to rename POSCAR_dimer to POSCAR before you run the dimer jobs.      
      ''')
