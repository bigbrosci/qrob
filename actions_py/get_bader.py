#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse
import sys
import os
from typing import List, Tuple
from brain.poscar import parse_atom_targets
from ase.io import read
from collections import defaultdict


def read_acf(acf_file: str) -> List[float]:
    """Read ACF.dat file and extract Bader charges for each atom."""
    with open(acf_file, 'r') as file:
        lines = file.readlines()
        # typical ACF.dat has header lines; keep existing slicing
        charge_data = lines[2:-4]
        bader_charges = [float(line.split()[4]) for line in charge_data]
    return bader_charges


def read_potcar_with_zval(potcar_file: str):
    """Read POTCAR file and extract elements along with their ZVAL values."""
    elements_zval = {}
    with open(potcar_file, 'r') as file:
        current_element = ""
        for line in file:
            if 'VRHFIN' in line:
                current_element = line.split('=')[1].split(':')[0].strip()
            if 'ZVAL' in line:
                # Keep current parsing logic; POTCAR formatting can vary
                try:
                    zval = float(line.split(';')[1].split('=')[1].strip().split()[0])
                except Exception:
                    # fallback: try to extract last float in the line
                    parts = [p for p in line.replace('=', ' ').split() if any(ch.isdigit() for ch in p)]
                    zval = float(parts[-1])
                elements_zval[current_element] = zval
    return elements_zval


def read_poscar(poscar_file: str) -> List[int]:
    """Read POSCAR file and determine the number of each type of atom."""
    with open(poscar_file, 'r') as file:
        lines = file.readlines()
        atom_counts = [int(x) for x in lines[6].split()]
    return atom_counts


def calculate_bader_charge(acf_file: str, potcar_file: str, poscar_file: str) -> List[Tuple[int, str, float]]:
    """Calculate the Bader charge for each atom and return list of (index, element, charge)."""
    bader_charges_raw = read_acf(acf_file)
    elements_zval = read_potcar_with_zval(potcar_file)
    atom_counts = read_poscar(poscar_file)

    output: List[Tuple[int, str, float]] = []
    atom_index = 1
    element_list = list(elements_zval.keys())
    for i, count in enumerate(atom_counts):
        element = element_list[i]
        zval = elements_zval[element]
        for _ in range(count):
            adjusted_charge = zval - bader_charges_raw[atom_index - 1]
            output.append((atom_index, element, adjusted_charge))
            atom_index += 1

    return output


# Selection of atoms is handled by `atom_selector.parse_atom_targets`, which
# returns 0-based atom indices given element symbols or 0-based indices.


def write_csv(all_data: List[Tuple[int, str, float]], out_file: str):
    with open(out_file, 'w') as fh:
        fh.write('Index,Element,Charge\n')
        for idx, elem, ch in all_data:
            fh.write(f"{idx},{elem},{ch}\n")


def main():
    parser = argparse.ArgumentParser(description='Print Bader charges for specified atoms and save full list')
    parser.add_argument('targets', nargs='*', help="Element symbols or 0-based atom indices. If omitted, only full CSV is written.")
    parser.add_argument('--acf', default='./ACF.dat', help='Path to ACF.dat')
    parser.add_argument('--potcar', default='./POTCAR', help='Path to POTCAR')
    parser.add_argument('--poscar', default='./POSCAR', help='Path to POSCAR')
    parser.add_argument('--out', default='bader_all.csv', help='Output CSV filename for all atoms')
    args = parser.parse_args()

    for p in (args.acf, args.potcar, args.poscar):
        if not os.path.exists(p):
            print(f"Error: required file '{p}' not found", file=sys.stderr)
            sys.exit(2)

    all_data = calculate_bader_charge(args.acf, args.potcar, args.poscar)

    # Always write full CSV
    write_csv(all_data, args.out)

    # If targets given, use atom_selector to parse them (0-based indices)
    if args.targets:
        try:
            idxs0 = parse_atom_targets(args.targets, args.poscar)
        except Exception as e:
            print(f"Error parsing targets: {e}", file=sys.stderr)
            sys.exit(4)

        if not idxs0:
            print('No matching atoms found for given targets.', file=sys.stderr)
            sys.exit(0)

        # convert to 1-based indices used in `all_data`
        wanted = set(i + 1 for i in idxs0)
        sel = [entry for entry in all_data if entry[0] in wanted]
        if sel:
            print('Index,Element,Charge')
            for idx, elem, ch in sel:
                print(f"{idx},{elem},{ch}")
        else:
            print('No matching atoms found for given targets.', file=sys.stderr)
    else:
        # Print all
        print('Index,Element,Charge')
        for idx, elem, ch in all_data:
            print(f"{idx},{elem},{ch}")

    # ASE integration: read POSCAR and demonstrate ASE capabilities
    atoms = read(args.poscar, format='vasp')
    print(len(atoms))
    print(atoms.get_chemical_symbols())
    print(atoms.get_positions())         # cartesian
    print(atoms.get_scaled_positions())  # direct
    print(atoms.get_cell())

    # map element -> 1-based atom indices
    idxs = defaultdict(list)
    for i, s in enumerate(atoms.get_chemical_symbols(), start=1):
        idxs[s].append(i)
    print(idxs['O'])  # indices of all oxygens


if __name__ == '__main__':
    main()
