#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""Compatibility shim: import parse_atom_targets from brain.poscar.

The real implementation lives in `brain.poscar`. Keep this module so
existing imports like `from atom_selector import parse_atom_targets`
continue to work.
"""

from brain.poscar import parse_atom_targets

__all__ = ["parse_atom_targets"]
