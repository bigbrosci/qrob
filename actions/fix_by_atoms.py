#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fix selective-dynamics flags in a VASP POSCAR using ASE.

Usage examples:
  # fix atoms by zero-based index range 0-5 with flags (x,y,z) = F F F
  python fix_by_atoms.py POSCAR 0-5 FFF

  # fix all C atoms with flags T F F
  python fix_by_atoms.py POSCAR C TFF

  # fix atoms by indices and elements
  python fix_by_atoms.py POSCAR 0 2 5 O TTT

Notes:
- Indices are 0-based (first atom has index 0). This script prints a warning.
- Flags are three characters of T/F where T means movable ("T" in POSCAR selective dynamics),
  and F means fixed. Example: `TTF` allows x and y, fixes z.
"""

import sys
import os
import re
import numpy as np
from ase.io import read, write


def parse_selection(tokens, natoms, symbols):
    """Return list of atom indices selected by tokens.

    tokens: list of selection tokens, each either element symbol, integer index, or range start-end.
    natoms: number of atoms
    symbols: list of element symbols of length natoms
    """
    indices = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        # element symbol (letters)
        if re.fullmatch(r"[A-Za-z]+", tok):
            for i, s in enumerate(symbols):
                if s == tok:
                    indices.append(i)
            continue

        # range like 1-5
        m = re.fullmatch(r"(\d+)-(\d+)", tok)
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            if a > b:
                a, b = b, a
            for ii in range(a, b + 1):
                if 0 <= ii < natoms:
                    indices.append(ii)
            continue

        # single integer index
        if re.fullmatch(r"\d+", tok):
            ii = int(tok)
            if 0 <= ii < natoms:
                indices.append(ii)
            continue

        print(f"Warning: unrecognized selection token '{tok}' — ignoring")

    # preserve order and unique
    seen = set()
    out = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) < 2:
        print("Usage: fix_by_atoms.py POSCAR SELECTION [TFF|FFF|TTT]")
        print("Example: fix_by_atoms.py POSCAR 0-5 FFF")
        return 2

    file_in = argv[0]
    rest = argv[1:]

    # If last token matches three T/F letters, treat it as flags
    tf = 'FFF'
    if re.fullmatch(r"[TFtf]{3}", rest[-1]):
        tf = rest[-1].upper()
        selections = rest[:-1]
    else:
        selections = rest

    if not selections:
        print('No selection tokens provided. Nothing to do.')
        return 2

    print("Warning: selection indices are 0-based (first atom = index 0).")

    try:
        atoms = read(file_in, format='vasp')
    except Exception as e:
        print(f"Error: failed to read '{file_in}': {e}")
        return 3

    natoms = len(atoms)
    symbols = atoms.get_chemical_symbols()

    idxs = parse_selection(selections, natoms, symbols)
    if not idxs:
        print('No atoms matched the selection tokens. Nothing to do.')
        return 0

    # Build selective dynamics array: True = movable (T), False = fixed (F)
    mask_per_atom = np.zeros((natoms, 3), dtype=bool)
    # default: keep existing selective_dynamics if present, otherwise default to True (movable)
    if 'selective_dynamics' in atoms.arrays:
        existing = atoms.get_array('selective_dynamics')
        if existing.shape == (natoms, 3):
            mask_per_atom[:] = existing
        else:
            mask_per_atom[:] = True
    else:
        # default assume all movable, then we will apply provided flags to selected atoms
        mask_per_atom[:] = True

    tf_bool = [c == 'T' for c in tf]

    for i in idxs:
        mask_per_atom[i, :] = tf_bool

    atoms.set_array('selective_dynamics', mask_per_atom)

    out_name = f"{file_in}_fixed"
    try:
        write(out_name, atoms, format='vasp', vasp5=True)
    except Exception as e:
        print(f"Error writing output '{out_name}': {e}")
        return 4

    print(f"Wrote '{out_name}' with selective dynamics updated for {len(idxs)} atoms.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
