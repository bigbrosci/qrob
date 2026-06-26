#!/usr/bin/env python3
"""
Read vibrational information from OUTCAR and report zero-point energy.

By default this script prints the ZPE correction in eV. It can also report
the Helmholtz free-energy correction at a chosen temperature and list any
imaginary modes detected in the OUTCAR.

Examples:
  python zpe.py
  python zpe.py -i OUTCAR
  python zpe.py -i OUTCAR --temperature 298.15
  python zpe.py -i OUTCAR --show-imag
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
import re

import numpy as np
from ase.thermochemistry import HarmonicThermo


def extract_epot_from_outcar(path: str) -> float:
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    for line in reversed(lines):
        if "  without" in line:
            try:
                return float(line.strip().split()[-1])
            except ValueError:
                continue
    raise ValueError("Could not find the final energy line containing 'without' in OUTCAR.")


def extract_vib_energies_from_outcar(path: str) -> tuple[list[float], list[float]]:
    vib_energies: list[float] = []
    imag_freqs: list[float] = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if "f/i=" in line and "THz" in line:
                match = re.search(r"([-]?\d+\.\d+)\s+cm-1", line)
                if match:
                    imag_freqs.append(float(match.group(1)))
            elif "f  =" in line and "cm-1" in line:
                try:
                    energy_mev = float(line.strip().split()[-2])
                    vib_energies.append(energy_mev / 1000.0)
                except (IndexError, ValueError):
                    continue

    return vib_energies, imag_freqs


def extract_zpe_mev_terms(path: str) -> list[float]:
    zpe_terms: list[float] = []
    seen_pairs: set[tuple[float, float]] = set()

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if "f  =" not in line:
                continue
            parts = line.split()
            try:
                freq_cm = float(parts[7])
                zpe_mev = float(parts[9])
            except (IndexError, ValueError):
                continue
            pair = (freq_cm, zpe_mev)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                zpe_terms.append(zpe_mev)
    return zpe_terms


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report ZPE and optional thermochemistry corrections from OUTCAR."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="OUTCAR",
        help="OUTCAR file to read (default: OUTCAR)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Also report the Helmholtz free-energy correction at this temperature in K",
    )
    parser.add_argument(
        "--show-imag",
        action="store_true",
        help="Print any imaginary modes found in OUTCAR",
    )
    args = parser.parse_args(argv)

    outcar_path = args.input

    if not os.path.exists(outcar_path):
        print(f"OUTCAR not found: {outcar_path}", file=sys.stderr)
        return 1

    zpe_terms = extract_zpe_mev_terms(outcar_path)
    vib_energies, imag_freqs = extract_vib_energies_from_outcar(outcar_path)
    if not zpe_terms and not vib_energies:
        print("No vibrational information was parsed from OUTCAR.", file=sys.stderr)
        return 1

    if zpe_terms:
        e_zpe = sum(zpe_terms) / 2000.0
    else:
        thermo = HarmonicThermo(
            vib_energies=np.array(vib_energies),
            potentialenergy=extract_epot_from_outcar(outcar_path),
            ignore_imag_modes=True,
        )
        e_zpe = thermo.get_ZPE_correction()

    print(f"ZPE: {e_zpe:.6f} eV")

    if args.temperature is not None:
        thermo = HarmonicThermo(
            vib_energies=np.array(vib_energies),
            potentialenergy=extract_epot_from_outcar(outcar_path),
            ignore_imag_modes=True,
        )
        helmholtz = thermo.get_helmholtz_energy(args.temperature)
        print(f"Helmholtz correction @ {args.temperature:.2f} K: {helmholtz:.6f} eV")

    if args.show_imag and imag_freqs:
        print(f"Imaginary modes detected: {len(imag_freqs)}")
        for idx, freq in enumerate(imag_freqs, start=1):
            print(f"  {idx}. {freq:.2f} cm^-1")

    return 0


if __name__ == "__main__":
    sys.exit(main())
