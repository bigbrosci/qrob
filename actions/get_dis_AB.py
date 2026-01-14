#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 10:06:51 2022

@author: qli
"""

import numpy as np
from ase.io import read, write
import os, sys

'''
Important: Atom index starts from 0
'''
atom_A, atom_B = [int(i) for i in sys.argv[1:3]]
model = read('CONTCAR')
positions = model.get_positions()
dis_AB_1 = model.get_distance(atom_A, atom_B, mic=True)
dis_AB_2 = model.get_distance(atom_A, atom_B, mic=False)

print(dis_AB_1)
#print(round(dis_AB_1, 4), '\t',round(dis_AB_2,4))


