#!/usr/bin/env python3
"""Compatibility shim: import parse_atom_targets from brain.poscar.

The real implementation lives in `brain.poscar`. Keep this module so
existing imports like `from atom_selector import parse_atom_targets`
continue to work.
"""

from brain.poscar import parse_atom_targets

__all__ = ["parse_atom_targets"]
