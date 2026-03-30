#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

from brain.lattice import *

try:
    lines = read_car('CONTCAR')[0]
except FileNotFoundError:
    lines = read_car('POSCAR')[0]
 
a, b, c, A, V = get_abc(lines)

print('Length_a\tLength_b\tLength_c\tArea/A^2\tVolume/A^3\t')
print('%5.4f\t%5.4f\t%5.4f\t%5.4f\t%5.4f\t' %(a, b, c, A, V))
