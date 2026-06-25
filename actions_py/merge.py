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
Created on Fri Jul  5 15:47:16 2019
@author: qiang
This script is used to merge the coordinates from different gjf or xyz files
"""

import sys 
from gpm import * 
files_in_list = sys.argv[1:]

coords = []
for file_in in files_in_list:
    coords_file_in = file_analyzer(file_in)
    coords += coords_file_in

save_xyz(coords, 'merged')    
