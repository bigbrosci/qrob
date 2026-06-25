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

from eigenval import *
write_band_energy()
