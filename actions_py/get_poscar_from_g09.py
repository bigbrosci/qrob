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
Created on Thu Mar 19 06:08:23 2020

@author: qli
"""
import sys
from lignin_ga import *

f_in = sys.argv[1]
save_poscar_from_g09(f_in)
