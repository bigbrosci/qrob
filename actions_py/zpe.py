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

from brain.outcar import get_energy, get_frequencies


def extract_epot_from_outcar(path: str) -> float:
    return get_energy(path)


def extract_vib_energies_from_outcar(path: str) -> tuple[list[float], list[float]]:
    _, real_mev, imag, _ = get_frequencies(path)
    return [value / 1000.0 for value in real_mev], imag


def extract_zpe_mev_terms(path: str) -> list[float]:
    real, real_mev, _, _ = get_frequencies(path)
    return [energy for _, energy in dict.fromkeys(zip(real, real_mev))]


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

    real, real_mev, imag_freqs, _ = get_frequencies(outcar_path)
    zpe_terms = [energy for _, energy in dict.fromkeys(zip(real, real_mev))]
    vib_energies = [value / 1000.0 for value in real_mev]
    if not zpe_terms and not vib_energies:
        print("No vibrational information was parsed from OUTCAR.", file=sys.stderr)
        return 1

    e_zpe = sum(zpe_terms) / 2000.0

    print(f"ZPE: {e_zpe:.6f} eV")

    if args.temperature is not None:
        from ase.thermochemistry import HarmonicThermo

        thermo = HarmonicThermo(
            vib_energies=vib_energies,
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
