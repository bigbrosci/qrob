#!/usr/bin/env python3
"""
Sort atoms in a VASP POSCAR by element.

Usage:
    sort_atoms_by_ele.py FILE [ELE1 ELE2 ...]

If element order arguments are provided, atoms are grouped in that order.
If no element order is provided, atoms are grouped by element (alphabetical).

Output is written to `<input_basename>_sorted` in the same directory as the input.
"""
import sys
import os
from ase.io import read, write
from ase import Atoms


def main():
    if len(sys.argv) < 2:
        print("Usage: sort_atoms_by_ele.py FILE [ELE1 ELE2 ...]")
        sys.exit(1)

    infile = sys.argv[1]
    order_args = sys.argv[2:]

    if not os.path.exists(infile):
        print(f"Error: input file '{infile}' does not exist.")
        sys.exit(2)

    try:
        atoms = read(infile, format='vasp')
    except Exception as e:
        print(f"Error: failed to read '{infile}': {e}")
        sys.exit(3)

    symbols = atoms.get_chemical_symbols()

    # Default order: alphabetical unique element list
    unique_symbols = []
    for s in symbols:
        if s not in unique_symbols:
            unique_symbols.append(s)

    if order_args:
        order = order_args
    else:
        order = sorted(unique_symbols)

    # Build ordered list of atom indices
    l_total = []
    for ele in order:
        l_total.extend([i for i, a in enumerate(atoms) if a.symbol == ele])

    # Append any remaining atoms (elements not listed) in original order
    included = set(l_total)
    for i in range(len(atoms)):
        if i not in included:
            l_total.append(i)

    model_sorted = Atoms(cell=atoms.cell, pbc=True)
    for idx in l_total:
        model_sorted.append(atoms[idx])

    out_base = os.path.splitext(os.path.basename(infile))[0] + "_sorted"
    out_path = os.path.join(os.path.dirname(infile) or ".", out_base)

    write(out_path, model_sorted, format='vasp', vasp5=True)

    print('Output file is:\t', out_path)


if __name__ == '__main__':
    main()
