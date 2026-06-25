#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
# -*- coding: utf-8 -*-
'''Delete atoms from POSCAR using ASE'''
from pathlib import Path

from ase.io import read, write
from brain.poscar import parse_atom_targets

def get_atoms_to_delete(args, atoms, poscar_path):
    """Return set of 0-based atom indices to delete based on `args`.

    `args` may contain element symbols or 0-based atom indices. Uses
    `parse_atom_targets` from `brain.poscar` to perform parsing against the
    provided POSCAR file.
    """
    try:
        idxs0 = parse_atom_targets(args, poscar_path)
    except Exception as e:
        print(f"Error parsing targets: {e}", file=sys.stderr)
        sys.exit(2)

    return set(idxs0)


def delete_atoms_and_save(file_in, atoms_to_delete, atoms):
    """
    Delete the specified atoms and save the modified structure and deleted
    atom coordinates to new files.
    """
    deleted_indices = sorted(atoms_to_delete)

    deleted_out = Path(file_in).with_name("atom_deleted")
    with deleted_out.open("w", encoding="utf-8") as fh:
        fh.write("# index symbol x y z (Cartesian coordinates in Angstrom)\n")
        for idx in deleted_indices:
            symbol = atoms[idx].symbol
            x, y, z = atoms.positions[idx]
            fh.write(f"{idx} {symbol} {x:.10f} {y:.10f} {z:.10f}\n")

    # Remove atoms from the Atoms object
    atoms = atoms[[i for i in range(len(atoms)) if i not in atoms_to_delete]]

    # Write the modified atoms to a new file
    out_name = file_in.replace("POSCAR", "POSCAR_deleted")
    write(out_name, atoms)

    print(f'\nThe output files are: {out_name} and {deleted_out}')



if len(sys.argv) < 3:
    print('\nCommand Usage: delete_atoms.py POSCAR element_or_index1 element_or_index2 ...')
    print('Example: delete_atoms.py POSCAR C H O 0 2 5')
    print('This will delete all C, H, O atoms and the atoms with 0-based indices 0,2,5 from the POSCAR file')
    exit()

file_in = sys.argv[1]
args = sys.argv[2:]

# Read POSCAR file using ASE
try:
    atoms = read(file_in)
except Exception as e:
    print(f"Error: failed to read POSCAR '{file_in}': {e}", file=sys.stderr)
    sys.exit(3)

# Get atoms to delete based on the command-line arguments
atoms_to_delete = get_atoms_to_delete(args, atoms, file_in)

# Delete atoms and save the new POSCAR file
delete_atoms_and_save(file_in, atoms_to_delete, atoms)
