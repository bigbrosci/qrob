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
Created on Mon Sep 30 08:58:43 2019

@author: qli
"""
import sys 
from gpm import *

coords_file = sys.argv[1]

coords = file_analyzer(coords_file)
n_hbonds1 = calc_hbond_num1(coords)
n_hbonds2 = calc_hbond_num2(coords)
print(n_hbonds1, n_hbonds2)
