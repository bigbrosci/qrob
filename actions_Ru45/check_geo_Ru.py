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

from ase.io import read
#from ase.geometry import get_distances
import numpy as np

def find_ru_bonded_to_n(poscar_path, cutoff=2.7):
    # Read the POSCAR file
    structure = read(poscar_path)
    symbols = structure.symbols
    ru_indices = [idx for idx, symbol in enumerate(symbols) if symbol == 'Ru']
    try:
        n_index = [idx for idx, symbol in enumerate(symbols) if symbol == 'N'][0]
    except:
        n_index = [idx for idx, symbol in enumerate(symbols) if symbol == 'H'][0] # single H
    # Calculate distances from N to all Ru atoms
    distances = structure.get_distances(n_index, ru_indices, mic=True)
    short_distances = [dist for dist in distances if dist <= cutoff]
    # Find Ru atoms that are within the cutoff distance
    bonded_ru_indices = [idx  for idx, dist in enumerate(distances) if dist <= cutoff]

    # Sort the indices and format the output
    bonded_ru_indices.sort()
    formatted_indices = '_'.join(f'{idx + 1}' for idx in bonded_ru_indices)  # +1 to convert from 0-based to 1-based indexing

    return formatted_indices, short_distances  

# Example usage of the function
poscar_path = 'POSCAR'  # Specify the path to your POSCAR file
bonded_ru, short_distances  = find_ru_bonded_to_n(poscar_path)
#print("Bonded Ru atoms to N:", bonded_ru)
print(bonded_ru)#, short_distances)
