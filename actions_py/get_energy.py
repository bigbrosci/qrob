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

import sys 
from gpm import *
'''Get infor from Gaussian log file'''
log_file = sys.argv[1]
dict_infor = get_infor_from_log(log_file)
for key, val in dict_infor.items():
    if isinstance(val, float):
#    if isinstance(val, (int, float)):
        print(key, val)
