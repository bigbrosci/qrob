#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

"""
Created on Tue Jul 12 18:38:35 2022
https://janaf.nist.gov/tables/H-083.html #Database
@author: qli
"""
import numpy as np
from ase.io import read, write
from ase.thermochemistry import IdealGasThermo,HarmonicThermo
from scipy import constants as con

f = open('./OUTCAR', 'r')
energy = 0
for line in f.readlines():
    if '  without' in line:
        energy = float(line.rstrip().split()[-1])
    

vib_energies = []
with open('./freq/OUTCAR') as f_in:
    lines = f_in.readlines()
    for num, line in enumerate(lines):
        if 'cm-1' in line:
            vib_e = float(line.rstrip().split()[-2])
            vib_energies.append(vib_e)

## The list should be modified.
vib_energies = np.array(vib_energies)/1000 # For Gas, the last six are translation and rotation


thermo = HarmonicThermo(vib_energies=vib_energies,
                        potentialenergy=0)

zpe = thermo.get_ZPE_correction()
tem = 298.15
entropy = thermo.get_entropy(temperature=tem,verbose=False)
TS = tem * entropy

print(energy + zpe + TS)

