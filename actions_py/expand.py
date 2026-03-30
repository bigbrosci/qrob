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
Created on Wed Oct  2 10:54:36 2019
expand the cell to a larger one
@author: qli
"""
import sys, os
import ase.io.vasp

file_read = sys.argv[1]
x,y,z     = [int(i) for i in sys.argv[2:5]]
try:
    cell = ase.io.vasp.read_vasp(file_read)
    ase.io.vasp.write_vasp("POSCARex",cell*(x, y, z), direct=True,sort=True)
except:
    print(os.getcwd())

