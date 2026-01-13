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


def plot_workfunction(locpot_path: str, out: str | None = None, outcar_path: str = 'OUTCAR'):
    """Plot workfunction data.

    If `locpot_path` is a LOCPOT_Z-like two-column file (name contains '_Z' or
    filename endswith 'LOCPOT_Z'), use the simple two-column reader. Otherwise
    if the file looks like a LOCPOT file, try to use pymatgen Locpot to compute
    the planar average and extract vacuum level. `outcar_path` is used to
    extract the Fermi energy when using LOCPOT.
    """
    if not os.path.exists(locpot_path):
        raise FileNotFoundError(f"File not found: {locpot_path}")

    base = os.path.basename(locpot_path)
    is_locpot_z = ('_Z' in base) or base.upper().endswith('LOCPOT_Z')

    if is_locpot_z:
        # simple two-column format (wplot style)
        x = []
        y = []
        name_x = 'x'
        name_y = 'y'
        with open(locpot_path, 'r', errors='ignore') as fh:
            first = fh.readline().strip()
            parts = first.split()
            if len(parts) >= 3:
                name_x = parts[1]
                name_y = parts[2]
            for line in fh:
                cols = line.strip().split()
                if len(cols) < 2:
                    continue
                try:
                    xv = float(cols[0])
                    yv = float(cols[1])
                except ValueError:
                    continue
                x.append(xv)
                y.append(yv)

        if not x:
            raise RuntimeError(f'No data found in {locpot_path}')

        plt.figure()
        plt.plot(x, y)
        plt.xlabel(name_x)
        plt.ylabel(name_y)
        out_name = out or (os.path.splitext(os.path.basename(locpot_path))[0] + '.png')
        plt.tight_layout()
        plt.savefig(out_name, dpi=300)
        print(f'Wrote {out_name}')
        return

    # Otherwise treat as LOCPOT and use pymatgen
    try:
        from pymatgen.io.vasp.outputs import Locpot
    except Exception as e:
        raise RuntimeError('pymatgen is required to read LOCPOT; install pymatgen') from e

    locpot = Locpot.from_file(locpot_path)
    planar_average = locpot.get_average_along_axis(2)
    vacuum_level = float(max(planar_average))

    # Read Fermi from OUTCAR
    if not os.path.exists(outcar_path):
        raise FileNotFoundError(f'OUTCAR not found at {outcar_path}; required to get Fermi energy')
    fermi_energy = None
    with open(outcar_path, 'r', errors='ignore') as fh:
        for line in fh:
            if 'Fermi energy' in line or 'E-fermi' in line:
                parts = line.split()
                # try to find a float in the line
                for p in parts:
                    try:
                        fermi_energy = float(p)
                        break
                    except Exception:
                        continue
    if fermi_energy is None:
        raise RuntimeError('Fermi energy not found in OUTCAR')

    work_function = vacuum_level - fermi_energy

    z_length = locpot.structure.lattice.c
    num_z = len(planar_average)
    z_positions = np.linspace(0.0, z_length, num_z)

    plt.figure(figsize=(9, 7))
    plt.plot(z_positions, planar_average, linewidth=2, label='Planar Average')
    plt.axhline(y=vacuum_level, color='#fdbd00', linestyle=':', linewidth=2, label='Vacuum Level')
    plt.axhline(y=fermi_energy, color='#2da94f', linestyle='--', linewidth=2, label='Fermi Energy')
    plt.axhline(y=work_function, color='#ea4335', linestyle='-.', linewidth=2, label='Work Function')
    plt.xlabel('z (Å)', fontsize=12)
    plt.ylabel('Potential (eV)', fontsize=12)
    plt.legend()
    out_name = out or 'Pot_vs_Z.png'
    plt.tight_layout()
    plt.savefig(out_name, dpi=300)
    print(f'Wrote {out_name}  (vacuum={vacuum_level:.4f}, fermi={fermi_energy:.4f}, workfunction={work_function:.4f} eV)')


def main():
    parser = argparse.ArgumentParser(description='Plot DFT: linear, NEB or workfunction')
    parser.add_argument('--type', '-t', choices=['linear', 'neb', 'workfunction'], required=True, help='Plot type')
    parser.add_argument('-i', '--input', help='Input file: CSV for linear (De,Ea) or LOCPOT_Z for workfunction')
    parser.add_argument('--dirs', help='Comma-separated dirs for NEB (default: auto)')
    parser.add_argument('--name', default='neb', help='Name/label for NEB output')
    parser.add_argument('--outcar', default='OUTCAR', help='OUTCAR path (used for workfunction calculation with LOCPOT)')
    parser.add_argument('--out', help='Output filename (png)')
    args = parser.parse_args()

    if args.type == 'linear':
        if not args.input:
            parser.error('linear type requires -i/--input CSV file')
        plot_linear(args.input, out=args.out)
    elif args.type == 'neb':
        dirs = None
        if args.dirs:
            dirs = [d.strip() for d in args.dirs.split(',') if d.strip()]
        plot_neb(dirs=dirs, name=args.name, out=args.out)
    else:  # workfunction
        if not args.input:
            parser.error('workfunction type requires -i/--input LOCPOT or LOCPOT_Z file')
        plot_workfunction(args.input, out=args.out, outcar_path=args.outcar)


if __name__ == '__main__':
    main()
