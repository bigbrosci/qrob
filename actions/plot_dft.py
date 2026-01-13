#!/usr/bin/env python3
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
import os
import sys
import numpy as np
import matplotlib.pyplot as plt


def plot_linear(csv_path: str, out: str = None):
    import pandas as pd
    from scipy import stats
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    data = pd.read_csv(csv_path)

    # support either De/Ea or IS/TS naming conventions
    if 'De' in data.columns and 'Ea' in data.columns:
        xcol, ycol = 'De', 'Ea'
    elif 'IS' in data.columns and 'TS' in data.columns:
        xcol, ycol = 'IS', 'TS'
    else:
        raise ValueError("CSV must contain either ('De','Ea') or ('IS','TS') columns")

    x = data[xcol].values.astype(float)
    y = data[ycol].values.astype(float)

    # use scipy.stats.linregress for slope/intercept/r
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    y_pred = slope * x + intercept

    mae = mean_absolute_error(y, y_pred)
    rmse = mean_squared_error(y, y_pred, squared=False)
    r2 = r_value ** 2

    equation = f'{ycol} = {slope:.2f} x + {intercept:.2f}'

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color='blue', label='DFT')
    # sort x for a nicer line plot
    order = np.argsort(x)
    plt.plot(x[order], y_pred[order], color='red', label='Reg.')

    textstr = f"{equation}\nMAE: {mae:.2f}\nRMSE: {rmse:.2f}\nR2: {r2:.2f}"
    plt.gca().text(0.65, 0.25, textstr, transform=plt.gca().transAxes,
                   fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0))
    plt.xlabel(f'{xcol}', fontsize=14)
    plt.ylabel(f'{ycol}', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc='upper left', frameon=False, fontsize=12)
    plt.tight_layout()

    out_name = out or (os.path.splitext(os.path.basename(csv_path))[0] + '.png')
    plt.savefig(out_name, dpi=300)
    print(f"Wrote {out_name}")


def plot_neb(dirs: list | None = None, name: str = 'neb', out: str | None = None):
    from scipy import interpolate

    if dirs is None:
        # pick subdirectories in cwd, ignoring files
        all_dirs = sorted([d for d in os.listdir('.') if os.path.isdir(d)])
        # try to select numeric directories first if present
        numeric = [d for d in all_dirs if d.isdigit()]
        use = numeric if numeric else all_dirs
        dirs = use

    if not dirs:
        raise RuntimeError('No directories found for NEB plotting')

    # Convert to ints where possible for ordering
    try:
        x = [int(d) for d in dirs]
    except Exception:
        # fallback: use enumeration
        x = list(range(len(dirs)))

    y = []
    used_dirs = []
    for d in dirs:
        outcar = os.path.join(d, 'OUTCAR')
        if not os.path.exists(outcar):
            print(f"Warning: OUTCAR not found in {d}, skipping", file=sys.stderr)
            continue
        E = None
        with open(outcar, 'r', errors='ignore') as fh:
            for line in fh:
                if '  without' in line:
                    E = line.rstrip().split()[-1]
        if E is None:
            print(f"Warning: energy line not found in {outcar}, skipping", file=sys.stderr)
            continue
        y.append(float(E))
        used_dirs.append(d)

    if not y:
        raise RuntimeError('No energies extracted for NEB')

    # Normalize to first
    y = [val - y[0] for val in y]

    # Use actual x values corresponding to used_dirs
    try:
        x_vals = [int(d) for d in used_dirs]
    except Exception:
        x_vals = list(range(len(used_dirs)))

    xnew = np.linspace(min(x_vals), max(x_vals), 600)
    xus = interpolate.InterpolatedUnivariateSpline(x_vals, y)
    ynew = xus(xnew)

    plt.figure()
    plt.plot(xnew, ynew)
    plt.plot(x_vals, y, 'o', alpha=0.6)
    plt.xlabel('Reaction Coordinates')
    plt.ylabel('Potential Energy / eV')
    out_name = out or f"{name}.png"
    plt.tight_layout()
    plt.savefig(out_name, dpi=300)
    print(f"Wrote {out_name}")


def main():
    parser = argparse.ArgumentParser(description='Plot DFT: linear regression or NEB profile')
    parser.add_argument('--type', '-t', choices=['linear', 'neb'], required=True, help='Plot type')
    parser.add_argument('-i', '--input', help='Input CSV for linear (De,Ea)')
    parser.add_argument('--dirs', help='Comma-separated dirs for NEB (default: auto)')
    parser.add_argument('--name', default='neb', help='Name/label for NEB output')
    parser.add_argument('--out', help='Output filename (png)')
    args = parser.parse_args()

    if args.type == 'linear':
        if not args.input:
            parser.error('linear type requires -i/--input CSV file')
        plot_linear(args.input, out=args.out)
    else:
        dirs = None
        if args.dirs:
            dirs = [d.strip() for d in args.dirs.split(',') if d.strip()]
        plot_neb(dirs=dirs, name=args.name, out=args.out)


if __name__ == '__main__':
    main()
