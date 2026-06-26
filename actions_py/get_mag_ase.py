#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""Read per-atom magnetization from OUTCAR using ASE only.

Usage:
  python get_mag.py [--outcar OUTCAR] [--index IDX] [--output FILE] [--format text|json] [selection...]

Selection tokens can be:
 - integer atom index (0-based)
 - range `start-end` or `start-` (to end)
 - element symbol like `C` to select all atoms of that element

If no selection is provided, all atoms are printed.
"""

import sys
import os
import re
import argparse
import json

try:
    from ase.io import read
except Exception:
    print('ASE is required for this script. Install with `pip install ase`.')
    sys.exit(1)


def parse_selection(tokens, symbols):
    """Return sorted unique 0-based atom indices matching tokens."""
    n = len(symbols)
    sel = []

    def add_idx(i):
        if 0 <= i < n and i not in sel:
            sel.append(i)

    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # single index
        if t.isdigit():
            add_idx(int(t))
            continue
        # range:  start-end  or start-
        m = re.match(r"^(\d+)-(\d*)$", t)
        if m:
            start = int(m.group(1))
            end_s = m.group(2)
            end = int(end_s) if end_s.isdigit() else n - 1
            for i in range(start, end + 1):
                add_idx(i)
            continue
        # element symbol (case-insensitive)
        if re.match(r'^[A-Za-z]+$', t):
            for i, s in enumerate(symbols):
                if s.upper() == t.upper():
                    add_idx(i)
            continue
        # unknown token -> ignore
    sel.sort()
    return sel


def parse_args(argv=None):
    p = argparse.ArgumentParser(description='Extract per-atom magnetization from OUTCAR using ASE')
    p.add_argument('--outcar', '-f', default='OUTCAR', help='Path to OUTCAR file (default: OUTCAR)')
    p.add_argument('--index', '-i', type=int, default=-1, help='ASE read index for OUTCAR (default: -1, last)')
    p.add_argument('--output', '-o', default='Magnetization.txt', help='Output file path')
    p.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    p.add_argument('selection', nargs='*', help='Selection tokens: 0-based indices, ranges (e.g. 0-4, 3-), or element symbols (e.g. Fe)')
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not os.path.isfile(args.outcar):
        print(f'OUTCAR not found: {args.outcar}')
        return 1

    # Read requested ionic step from OUTCAR
    try:
        atoms = read(args.outcar, index=args.index, format='vasp-out')
    except Exception:
        atoms = read(args.outcar, index=args.index)

    symbols = atoms.get_chemical_symbols()

    if not args.selection:
        atom_list = list(range(len(symbols)))
    else:
        atom_list = parse_selection(args.selection, symbols)

    # Try to obtain magnetic moments
    magmoms = None
    try:
        magmoms = atoms.get_magnetic_moments()
    except Exception:
        try:
            magmoms = atoms.get_initial_magnetic_moments()
        except Exception:
            magmoms = None

    if magmoms is None or len(magmoms) != len(symbols):
        print('No per-atom magnetic moments found in OUTCAR via ASE.')
        magmoms = [None] * len(symbols)

    # Prepare output structure
    out_dict = {}
    for i, (sym, m) in enumerate(zip(symbols, magmoms)):
        out_dict[i] = {'element': sym, 'magmom': None if m is None else float(m)}

    # Print selected atoms
    for idx in atom_list:
        item = out_dict.get(idx)
        if item is None:
            print(idx, '\t', 'N/A')
        else:
            m = item['magmom']
            m_str = 'N/A' if m is None else '{:.6f}'.format(m)
            print(idx, '\t', item['element'], '\t', m_str)

    # Write output file
    if args.format == 'text':
        with open(args.output, 'w') as f_out:
            for i in sorted(out_dict.keys()):
                item = out_dict[i]
                m_str = 'N/A' if item['magmom'] is None else '{:.6f}'.format(item['magmom'])
                f_out.write(f"{i}\t{item['element']}\t{m_str}\n")
    else:
        with open(args.output, 'w') as f_out:
            json.dump(out_dict, f_out, indent=2)

    return 0


if __name__ == '__main__':
    sys.exit(main())
