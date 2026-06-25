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
Created on Wed Jul 17 15:06:37 2019
Calculate the dihedral angle 
@author: qiang
"""

from gpm import *
import sys 
file_in = sys.argv[1]
points = sys.argv[2:6]

coords = file_analyzer(file_in)

p = [get_coord_atom(coords, int(i)) for i in points]

dihedral = get_dihedral(p)

dihedral = abs(dihedral)
if dihedral > 90:
    dihedral = 180 - dihedral
    
print(dihedral)
