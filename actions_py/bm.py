#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

#Get Lattice paramters from BM state equation
# Written by Qiang 
# To use it : python bm.py data

import sys 
from lattice import bm_fitting
data_file = sys.argv[1]

bm_fitting(data_file)
