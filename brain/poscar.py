#!/usr/bin/env python3
"""POSCAR helper utilities using ASE.

Contains `parse_atom_targets` which converts CLI-style targets (element
symbols or 0-based indices) into a list of 0-based atom indices.
"""

from io import StringIO
from typing import List
import sys
import os

try:
    from ase.io import read
except Exception:
    read = None


def _read_poscar_symbols(poscar_path: str) -> List[str]:
    """Return list of chemical symbols (in order) for the structure in POSCAR.

    Uses ASE when available. If ASE read fails due to malformed POSCAR
    (e.g. trailing blank lines), we try a simple cleanup: strip trailing
    whitespace-only lines and re-read from a StringIO.
    """
    if read is None:
        raise RuntimeError("ASE is required to read POSCAR; please install ase")

    try:
        atoms = read(poscar_path, format='vasp')
        return atoms.get_chemical_symbols()
    except Exception:
        # fallback: try stripping trailing blank lines and re-read
        with open(poscar_path, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        while lines and lines[-1].strip() == "":
            lines.pop()
        s = StringIO(''.join(lines))
        atoms = read(s, format='vasp')
        return atoms.get_chemical_symbols()


def parse_atom_targets(targets: List[str], poscar_path: str) -> List[int]:
    """Parse a list of target strings into 0-based atom indices.

    Args:
        targets: list of strings provided by user (element symbols or indices).
        poscar_path: path to POSCAR file used to map element names to indices.

    Returns:
        List of unique 0-based atom indices in the order they were first requested.

    Raises:
        FileNotFoundError: if `poscar_path` does not exist.
        RuntimeError: if ASE is not available.
    """
    if not os.path.exists(poscar_path):
        raise FileNotFoundError(f"POSCAR not found: {poscar_path}")

    symbols = _read_poscar_symbols(poscar_path)
    n = len(symbols)

    selected = []
    for t in targets:
        t = t.strip()
        if t == "":
            continue
        # try parse as integer (0-based index)
        try:
            idx = int(t)
            if idx < 0 or idx >= n:
                print(f"Warning: index {idx} out of range (0..{n-1})", file=sys.stderr)
            else:
                selected.append(idx)
            continue
        except ValueError:
            pass

        # otherwise treat as element symbol (case-insensitive exact match)
        sym = t.lower()
        matched = [i for i, s in enumerate(symbols) if s.lower() == sym]
        if not matched:
            print(f"Warning: element '{t}' not found in POSCAR", file=sys.stderr)
        else:
            selected.extend(matched)

    # remove duplicates while preserving order
    seen = set()
    uniq = []
    for i in selected:
        if i not in seen:
            uniq.append(i)
            seen.add(i)
    return uniq


if __name__ == '__main__':
    # small CLI for quick tests
    import argparse

    p = argparse.ArgumentParser(description='Parse atom selection targets using POSCAR')
    p.add_argument('targets', nargs='*', help='Element symbols or 0-based atom indices')
    p.add_argument('--poscar', default='POSCAR', help='POSCAR path')
    args = p.parse_args()

    try:
        idxs = parse_atom_targets(args.targets, args.poscar)
        print(idxs)
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        sys.exit(1)
