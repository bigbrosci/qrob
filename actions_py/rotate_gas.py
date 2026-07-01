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


from gpm import * 
import sys 

file_in = sys.argv[1]
raw_infor = sys.argv[2:]

point_1, point_2 = [int(i) for i in raw_infor[0:2]]
atom_s = raw_infor[2:-1]   
coords = file_analyzer(file_in)
atom_list = get_atom_list_g09(coords, atom_s)
theta  = float(raw_infor[-1]) * math.pi / 180

if point_1 in atom_list:
    atom_list.remove(point_1)
if point_2 in atom_list:
    atom_list.remove(point_2)

coord_1 = get_coord_atom(coords, point_1)
coord_2 = get_coord_atom(coords, point_2)
    
name, lines = read_file(file_in)
coords      = get_coord_xyz(lines)
new_coords  = rotate_atoms(coords, coord_1, coord_2, atom_list, theta)
save_xyz(new_coords, 'rotated')
