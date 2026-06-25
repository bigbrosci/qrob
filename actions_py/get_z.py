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

import os
from ase.io import read

def read_structure_and_analyze_z():
    # Check for CONTCAR in the current folder, else read POSCAR
    if os.path.exists('CONTCAR'):
        structure = read('CONTCAR')
        file_used = 'CONTCAR'
    elif os.path.exists('POSCAR'):
        structure = read('POSCAR')
        file_used = 'POSCAR'
    else:
        return "Neither CONTCAR nor POSCAR found in the current directory."

    # Extract positions of all atoms
    positions = structure.positions

    # Find the highest and lowest Z coordinates
    z_coords = positions[:, 2]  # All z-coordinates
    highest_z = max(z_coords)
    lowest_z = min(z_coords)

    # Get the box size in the z direction
    z_box_size = structure.cell.lengths()[2]

    return {
        'File Used': file_used,
        'Highest Z Coordination': highest_z,
        'Lowest Z Coordination': lowest_z,
        'Box Size in Z': z_box_size
    }

# Example usage of the function
result = read_structure_and_analyze_z()
print(result)
