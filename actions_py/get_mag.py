#!/usr/bin/env python3
"""Extract per-atom total magnetic moments from OUTCAR.

Usage:
  python3 get_mag.py [targets...]

Targets may be element symbols or 0-based atom indices. If omitted, the script
prints all atoms. The CSV output always uses the workflow format:
`index,element,magmom` with 0-based indices and total magnetic moment.
"""

from __future__ import annotations

import csv
import errno
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

from brain.outcar import get_mag
from brain.poscar import parse_atom_targets

try:
    from ase.io import read
except Exception:
    read = None


def read_poscar_symbols(poscar_path: str) -> list[str]:
    if read is None:
        raise RuntimeError("ASE is required to read POSCAR")
    atoms = read(poscar_path, format="vasp")
    return atoms.get_chemical_symbols()


def total_magmom(mag_values) -> float:
    """Sum the s/p/d magnetization components into a single moment."""
    return float(sum(float(x) for x in mag_values))


def write_csv(out_csv: str, symbols: list[str], mag_dict: dict[int, list[float]]) -> None:
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "element", "magmom"])
        for idx0, elem in enumerate(symbols):
            mag_values = mag_dict.get(idx0 + 1, [])
            writer.writerow([idx0, elem, total_magmom(mag_values)])


def print_rows(indices: list[int], symbols: list[str], mag_dict: dict[int, list[float]]) -> None:
    print("index,element,magmom")
    for idx0 in indices:
        elem = symbols[idx0] if 0 <= idx0 < len(symbols) else "N/A"
        mag_values = mag_dict.get(idx0 + 1, [])
        print(f"{idx0},{elem},{total_magmom(mag_values)}")


def main() -> int:
    args = sys.argv[1:]

    if not os.path.isfile("OUTCAR"):
        print("No OUTCAR in current path. Bye!", file=sys.stderr)
        return 1

    if not os.path.isfile("POSCAR") and not os.path.isfile("CONTCAR"):
        print("POSCAR or CONTCAR not found; required to map elements", file=sys.stderr)
        return 2

    poscar_file = "CONTCAR" if os.path.isfile("CONTCAR") else "POSCAR"

    try:
        selected0 = parse_atom_targets(args, poscar_file) if args else []
    except Exception as exc:
        print(f"Error parsing targets: {exc}", file=sys.stderr)
        return 3

    mag_dict = get_mag()
    symbols = read_poscar_symbols(poscar_file)

    out_csv = "Magnetization.csv"
    try:
        write_csv(out_csv, symbols, mag_dict)
    except OSError as exc:
        if exc.errno == errno.EACCES:
            print(f"Permission denied writing {out_csv}", file=sys.stderr)
        raise

    if selected0:
        print_rows(selected0, symbols, mag_dict)
    else:
        print_rows(list(range(len(symbols))), symbols, mag_dict)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
