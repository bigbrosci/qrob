"""
Central registry describing how each `actions_py/` script interacts with `brain` helpers.

This module exposes metadata (description, usage, dependencies, required files) and
allows other tools to discover which scripts rely on which brain APIs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, TypedDict

BASE_DIR = Path(__file__).resolve().parent


class ActionInfo(TypedDict):
    script: Path
    description: str
    usage: str
    category: str
    dependencies: List[str]
    brain_helpers: List[str]
    required_inputs: List[str]
    outputs: List[str]
    notes: str


ACTION_REGISTRY: Dict[str, ActionInfo] = {
    "delete_atoms": {
        "script": BASE_DIR / "delete_atoms.py",
        "description": "Remove atoms from a POSCAR by element symbol or 0-based index.",
        "usage": "python delete_atoms.py POSCAR C H 0 2 5",
        "category": "POSCAR editing",
        "dependencies": ["ase"],
        "brain_helpers": ["brain.poscar.parse_atom_targets"],
        "required_inputs": ["POSCAR"],
        "outputs": ["POSCAR_deleted", "atom_deleted"],
        "notes": "Also supports 1-based ranges with --one-based and H-cleanup mode via --delete-far-h.",
    },
    "fix_atoms": {
        "script": BASE_DIR / "fix_atoms.py",
        "description": "Update selective-dynamics flags by indices, elements, layers, and/or z cutoff.",
        "usage": "python fix_atoms.py -i POSCAR --layers 2 --flags FFF",
        "category": "POSCAR editing",
        "dependencies": ["ase", "numpy"],
        "brain_helpers": [],
        "required_inputs": ["POSCAR"],
        "outputs": ["POSCAR_fixed"],
        "notes": "Supports combining selectors such as --indices, --elements, --layers, and --z-below in one command.",
    },
    "bottom": {
        "script": BASE_DIR / "bottom.py",
        "description": "Translate a slab so its bottom sits at a target z-offset and optionally reset the c vector with added vacuum.",
        "usage": "python bottom.py -i POSCAR --z-offset 0.1 --set-c-vacuum 15",
        "category": "POSCAR editing",
        "dependencies": ["ase", "numpy"],
        "brain_helpers": [],
        "required_inputs": ["POSCAR"],
        "outputs": ["POSCAR_bottomed.vasp"],
        "notes": "Use --set-c-vacuum to reproduce the old bottom_slab.py behavior of resetting the c vector after bottoming.",
    },
    "get_mag": {
        "script": BASE_DIR / "get_mag.py",
        "description": "Extract per-atom magnetizations from OUTCAR and map them to POSCAR indices.",
        "usage": "python get_mag.py [targets...]",
        "category": "Analysis",
        "dependencies": ["ase"],
        "brain_helpers": ["brain.poscar.parse_atom_targets", "brain.outcar.get_mag"],
        "required_inputs": ["OUTCAR", "POSCAR or CONTCAR"],
        "outputs": ["Magnetization.csv"],
        "notes": "Targets default to all atoms if not provided; writes both CSV and console output.",
    },
    "get_bader": {
        "script": BASE_DIR / "get_bader.py",
        "description": "Compute Bader charges and optionally print details for selected atoms.",
        "usage": "python get_bader.py [targets...]",
        "category": "Analysis",
        "dependencies": ["ase"],
        "brain_helpers": ["brain.poscar.parse_atom_targets"],
        "required_inputs": ["ACF.dat", "POTCAR", "POSCAR"],
        "outputs": ["bader_all.csv"],
        "notes": "Selection targets use the same helper that maps elements/indices to 0-based lists.",
    },
    "pp": {
        "script": BASE_DIR / "pp.py",
        "description": "Concatenate POTCAR files based on POSCAR or a user-provided element list.",
        "usage": "python pp.py [element1 element2 ...]",
        "category": "POTCAR management",
        "dependencies": [],
        "brain_helpers": ["brain.potcar.concatenate", "brain.potcar.read_potcar"],
        "required_inputs": ["POSCAR (optional)", "POTCAR library under books/"],
        "outputs": ["POTCAR"],
        "notes": "If no elements are passed, it tries to infer the order from POSCAR.",
    },
}


def list_actions() -> List[str]:
    """Return the canonical action identifiers."""

    return sorted(ACTION_REGISTRY.keys())


def find_actions_by_helper(helper: str) -> List[str]:
    """List actions that declare a dependency on a specific brain helper."""

    return sorted(
        action for action, info in ACTION_REGISTRY.items() if helper in info["brain_helpers"]
    )


def get_action_info(action_id: str) -> ActionInfo | None:
    """Retrieve metadata for a given action identifier."""

    return ACTION_REGISTRY.get(action_id)


__all__ = ["ActionInfo", "ACTION_REGISTRY", "list_actions", "find_actions_by_helper", "get_action_info"]
