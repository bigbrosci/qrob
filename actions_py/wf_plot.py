#!/usr/bin/env python3
"""
Plot work-function related potentials from either `LOCPOT_Z` or raw VASP outputs.

Modes:
- `locpot-z`: plot the two-column `LOCPOT_Z` file written by `vtotav.py`
- `locpot`: read `LOCPOT` and `OUTCAR`, compute the planar-average potential,
  vacuum level, Fermi energy, and work function, then plot them together

Examples:
  python wplot.py
  python wplot.py --mode locpot-z --input LOCPOT_Z --output workfunction.pdf
  python wplot.py --mode locpot --locpot LOCPOT --outcar OUTCAR --output Pot_vs_Z.png
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np


def read_locpot_z(path: str) -> tuple[np.ndarray, np.ndarray, str, str]:
    x_vals = []
    y_vals = []
    with open(path, "r", encoding="utf-8") as handle:
        first_line = handle.readline()
        labels = first_line.split()
        x_label = labels[1] if len(labels) > 1 else "x"
        y_label = labels[2] if len(labels) > 2 else "y"
        for line in handle:
            parts = line.split()
            if len(parts) >= 2:
                x_vals.append(float(parts[0]))
                y_vals.append(float(parts[1]))
    return np.array(x_vals), np.array(y_vals), x_label, y_label


def extract_fermi_energy(outcar_path: str) -> float:
    with open(outcar_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if "E-fermi" in line:
                return float(line.split()[2])
            if "Fermi energy" in line:
                return float(line.split()[2])
    raise ValueError("Fermi energy not found in OUTCAR.")


def plot_locpot_z(input_path: str, output_path: str, show: bool) -> None:
    x_vals, y_vals, x_label, y_label = read_locpot_z(input_path)
    plt.figure()
    plt.plot(x_vals, y_vals)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.savefig(output_path, dpi=400)
    if show:
        plt.show()
    plt.close()


def plot_locpot(locpot_path: str, outcar_path: str, output_path: str, show: bool) -> None:
    try:
        from pymatgen.io.vasp.outputs import Locpot
    except ImportError as exc:
        raise ImportError("pymatgen is required for --mode locpot") from exc

    locpot = Locpot.from_file(locpot_path)
    planar_average = locpot.get_average_along_axis(2)
    vacuum_level = float(np.max(planar_average))
    fermi_energy = extract_fermi_energy(outcar_path)
    work_function = vacuum_level - fermi_energy

    z_length = locpot.structure.lattice.c
    z_positions = np.linspace(0, z_length, len(planar_average))

    plt.figure(figsize=(9, 7))
    plt.plot(z_positions, planar_average, linewidth=2, label="Planar average potential")
    plt.axhline(y=vacuum_level, color="#fdbd00", linestyle=":", linewidth=2, label="Vacuum level")
    plt.axhline(y=fermi_energy, color="#2da94f", linestyle=":", linewidth=2, label="Fermi energy")
    plt.axhline(y=work_function, color="#ea4335", linestyle=":", linewidth=2, label="Work function")
    plt.xlabel("z-direction (A)")
    plt.ylabel("Potential (eV)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=600)
    print(f"Vacuum level: {vacuum_level:.6f} eV")
    print(f"Fermi energy: {fermi_energy:.6f} eV")
    print(f"Work function: {work_function:.6f} eV")
    if show:
        plt.show()
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot work-function potential data from LOCPOT_Z or LOCPOT.")
    parser.add_argument(
        "--mode",
        choices=("locpot-z", "locpot"),
        default="locpot-z",
        help="Plot from LOCPOT_Z or compute directly from LOCPOT/OUTCAR (default: locpot-z)",
    )
    parser.add_argument(
        "--input",
        default="LOCPOT_Z",
        help="Input file for --mode locpot-z (default: LOCPOT_Z)",
    )
    parser.add_argument(
        "--locpot",
        default="LOCPOT",
        help="LOCPOT file for --mode locpot (default: LOCPOT)",
    )
    parser.add_argument(
        "--outcar",
        default="OUTCAR",
        help="OUTCAR file for --mode locpot (default: OUTCAR)",
    )
    parser.add_argument(
        "--output",
        help="Output figure filename",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save the figure without opening an interactive window",
    )
    args = parser.parse_args()

    if args.mode == "locpot-z":
        input_path = args.input
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}", file=sys.stderr)
            return 1
        output_path = args.output or "workfunction.pdf"
        plot_locpot_z(input_path, output_path, show=not args.no_show)
    else:
        if not os.path.exists(args.locpot):
            print(f"LOCPOT file not found: {args.locpot}", file=sys.stderr)
            return 1
        if not os.path.exists(args.outcar):
            print(f"OUTCAR file not found: {args.outcar}", file=sys.stderr)
            return 1
        output_path = args.output or "Pot_vs_Z.png"
        plot_locpot(args.locpot, args.outcar, output_path, show=not args.no_show)

    print(f"Saved plot to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
