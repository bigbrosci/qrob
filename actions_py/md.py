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

''' This script is used to 
1) check the steps that O--O bond breaks in the MD simulations of OOH on the metal surfaces
2) save the xy coordinates of the O atoms in trajectory.
3) vasprun.xml and POSCAR files will be read
# Written By Qiang on 9th-Jan-2019
'''
import sys, os
import numpy as np 
from ase.io import read

script, atom1, atom2 = sys.argv
vector = read('POSCAR', format='vasp').cell.array.T
inverse_vector = np.linalg.inv(vector)

def save_atoms(atom_list):
    atom_list = sorted(atom_list)
    file_out = []
    file_name = []
    break_steps = []
    for i in atom_list:
        out = 'file_out_' + str(i)
        file = 'data_' + str(i)
        file_out.append(out)  
        file_name.append(file)  
    for i in range(0,len(file_out)):
        file_out[i] = open(file_name[i], 'w')

    with open('vasprun.xml') as infile:
        count = 0
        for line in infile:
            if '<varray name="positions" >' not in line:
                continue
            count += 1
            selected = {}
            for atom_index, row in enumerate(infile, start=1):
                if '</varray>' in row:
                    break
                if atom_index in atom_list:
                    fractional = np.array([float(value) for value in row.replace("<v>", "").replace("</v>", "").split()[:3]])
                    selected[atom_index] = vector @ fractional
            xyz = []
            for num, atom in enumerate(atom_list):
                position = selected[atom]
                xyz.append(position)
                file_out[num].write('%s\t%s\t%s\n' % tuple(position))
            delta_fractional = inverse_vector @ (xyz[0] - xyz[1])
            delta_fractional -= np.round(delta_fractional)
            if np.linalg.norm(vector @ delta_fractional) > 1.7:
                break_steps.append(count)
    for i in file_out:
        i.close()
    if len(break_steps) >= 1:
        print(break_steps[0])
    else:
        print('No')
    
atoms_list = [int(atom1),int(atom2)]
save_atoms(atoms_list)
