#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""Extract per-atom magnetization from OUTCAR and print/save selections.

Usage:
  python3 get_mag.py [targets...]

Targets are element symbols or 0-based atom indices. If omitted, the script
writes the full magnetization CSV and prints all atoms.
"""

import sys
import os
import csv
import errno

# ensure repo root on sys.path so brain.poscar can be imported
script_dir = os.path.dirname(os.path.realpath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from brain.poscar import parse_atom_targets
from brain.outcar import get_mag

try:
    from ase.io import read
except Exception:
    read = None


def read_poscar_symbols(poscar_path='POSCAR'):
    if read is None:
        raise RuntimeError('ASE is required to read POSCAR')
    atoms = read(poscar_path, format='vasp')
    return atoms.get_chemical_symbols()


def main():
    args = sys.argv[1:]

    if not os.path.isfile('OUTCAR'):
        print('No OUTCAR in current path. Bye!', file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile('POSCAR') and not os.path.isfile('CONTCAR'):
        print('POSCAR or CONTCAR not found; required to map elements', file=sys.stderr)
        sys.exit(2)

    poscar_file = 'CONTCAR' if os.path.isfile('CONTCAR') else 'POSCAR'

    # parse atom selection (0-based indices)
    targets = args
    try:
        selected0 = parse_atom_targets(targets, poscar_file) if targets else []
    except Exception as e:
        print(f'Error parsing targets: {e}', file=sys.stderr)
        sys.exit(3)

    # get per-atom magnetization from OUTCAR (keys are 1-based indices)
    mag_dict = get_mag()

    # get element symbols from POSCAR/CONTCAR
    symbols = read_poscar_symbols(poscar_file)

    # write full CSV for all atoms
    out_csv = 'Magnetization.csv'
    header = ['Index', 'Element']
    # determine max length of mag entries
    maxlen = max((len(v) for v in mag_dict.values()), default=0)
    for i in range(maxlen):
        header.append(f'Mag_{i}')

    try:
        with open(out_csv, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            # iterate over atoms in POSCAR order (1-based)
            for idx0, elem in enumerate(symbols):
                idx1 = idx0 + 1
                mags = mag_dict.get(idx1, [])
                row = [idx1, elem] + mags + [''] * (maxlen - len(mags))
                writer.writerow(row)
    except OSError as e:
        if e.errno == errno.EACCES:
            print(f'Permission denied writing {out_csv}', file=sys.stderr)
        raise

    # print selected atoms if any, else print all
    if selected0:
        print('Index,Element,Magnetizations')
        for i0 in selected0:
            i1 = i0 + 1
            elem = symbols[i0] if 0 <= i0 < len(symbols) else 'N/A'
            mags = mag_dict.get(i1, [])
            print(f"{i1},{elem},{','.join(str(x) for x in mags)}")
    else:
        print('Index,Element,Magnetizations')
        for idx0, elem in enumerate(symbols):
            idx1 = idx0 + 1
            mags = mag_dict.get(idx1, [])
            print(f"{idx1},{elem},{','.join(str(x) for x in mags)}")


if __name__ == '__main__':
    main()


