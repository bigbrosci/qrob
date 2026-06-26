#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""Plot DFT results: linear regression or NEB energy profile.

Usage examples:
  python3 plot_dft.py --type linear -i data.csv
  python3 plot_dft.py --type neb --name system_name

For `linear`, input CSV must contain columns `De` and `Ea`.
For `neb`, the script will look for subdirectories in the current folder
and read `OUTCAR` inside them to extract energies (same heuristic as
existing `plot_neb.py`). You can also pass `--dirs 00,01,02` to specify
which subdirectories to use.
"""

import argparse

from brain.data_analysis import plot_linear_fit, plot_neb_profile


def main():
    parser = argparse.ArgumentParser(description='Plot DFT: linear regression or NEB profile')
    parser.add_argument('--type', '-t', choices=['linear', 'neb'], required=True, help='Plot type')
    parser.add_argument('-i', '--input', help='Input file: CSV for linear plotting')
    parser.add_argument('--dirs', help='Comma-separated dirs for NEB (default: auto)')
    parser.add_argument('--name', default='neb', help='Name/label for NEB output')
    parser.add_argument('--out', help='Output filename (png)')
    args = parser.parse_args()

    if args.type == 'linear':
        if not args.input:
            parser.error('linear type requires -i/--input CSV file')
        out_name = plot_linear_fit(args.input, out=args.out)
        print(f"Wrote {out_name}")
    elif args.type == 'neb':
        dirs = None
        if args.dirs:
            dirs = [d.strip() for d in args.dirs.split(',') if d.strip()]
        out_name = plot_neb_profile(dirs=dirs, name=args.name, out=args.out)
        print(f"Wrote {out_name}")
if __name__ == '__main__':
    main()
