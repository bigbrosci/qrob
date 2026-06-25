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

'''Generate the k_add file to show how the KPOINTS are splitted in the line model.'''
from kpoints import *

lines_k, num_pairs = read_kpoints_band()
lines_k_add = get_k_add_lines(lines_k, num_pairs)

f_out = open('k_add', 'w')
f_out.writelines(lines_k_add)
f_out.close()
       
