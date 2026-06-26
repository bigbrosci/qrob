#!/usr/bin/env python3
"""
Read VTST Bader output files and report per-atom charge transfer values.

This unified helper reads `ACF.dat`, `POTCAR`, and `POSCAR`, computes
`ZVAL - Bader charge` for each atom, writes a CSV for all atoms, and can
optionally print only selected atoms by element symbol or atom index.

Examples:
  python get_bader.py
  python get_bader.py O
  python get_bader.py 0 3 5
  python get_bader.py O 0-5
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse
import os
import re
from typing import List, Tuple

from brain.poscar import parse_atom_targets


def read_acf(acf_file: str) -> List[float]:
    with open(acf_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    charges: List[float] = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            charges.append(float(parts[4]))
    return charges


def read_potcar_with_zval(potcar_file: str) -> Tuple[List[str], dict[str, float]]:
    ordered_elements: List[str] = []
    elements_zval: dict[str, float] = {}
    current_element = ""

    with open(potcar_file, "r", encoding="utf-8") as file:
        for line in file:
            if "VRHFIN" in line:
                current_element = line.split("=")[1].split(":")[0].strip()
                ordered_elements.append(current_element)
            elif "ZVAL" in line and current_element:
                try:
                    zval = float(line.split(";")[1].split("=")[1].strip().split()[0])
                except Exception:
                    parts = [p for p in line.replace("=", " ").split() if re.search(r"\d", p)]
                    zval = float(parts[-1])
                elements_zval[current_element] = zval

    # POTCAR blocks are repeated in some files; keep first-seen order unique.
    unique_order: List[str] = []
    for element in ordered_elements:
        if element not in unique_order:
            unique_order.append(element)
    return unique_order, elements_zval


def read_poscar_counts(poscar_file: str) -> List[int]:
    with open(poscar_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
    return [int(x) for x in lines[6].split()]


def calculate_bader_charge(acf_file: str, potcar_file: str, poscar_file: str) -> List[Tuple[int, str, float, float, float]]:
    bader_charges = read_acf(acf_file)
    element_order, elements_zval = read_potcar_with_zval(potcar_file)
    atom_counts = read_poscar_counts(poscar_file)

    output: List[Tuple[int, str, float, float, float]] = []
    atom_index = 1

    for i, count in enumerate(atom_counts):
        element = element_order[i]
        zval = elements_zval[element]
        for _ in range(count):
            bader_charge = bader_charges[atom_index - 1]
            charge_transfer = zval - bader_charge
            output.append((atom_index, element, bader_charge, zval, charge_transfer))
            atom_index += 1

    return output


def write_csv(all_data: List[Tuple[int, str, float, float, float]], out_file: str) -> None:
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write("Index,Element,BaderCharge,ZVAL,ChargeTransfer\n")
        for idx, elem, bader_charge, zval, charge_transfer in all_data:
            fh.write(f"{idx},{elem},{bader_charge},{zval},{charge_transfer}\n")


def write_dat(all_data: List[Tuple[int, str, float, float, float]], out_file: str) -> None:
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write("Element\tNo.\tCHARGE\tZVAL\tZVAL-CHARGE\n")
        for idx, elem, bader_charge, zval, charge_transfer in all_data:
            fh.write(f"{elem}\t{idx}\t{bader_charge:.4f}\t{zval}\t{charge_transfer:.4f}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print Bader charge-transfer values for selected atoms and save the full list."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Element symbols or 0-based atom indices/ranges. If omitted, all atoms are printed.",
    )
    parser.add_argument("--acf", default="./ACF.dat", help="Path to ACF.dat")
    parser.add_argument("--potcar", default="./POTCAR", help="Path to POTCAR")
    parser.add_argument("--poscar", default="./POSCAR", help="Path to POSCAR")
    parser.add_argument("--out", default="bader_all.csv", help="CSV output filename for all atoms")
    parser.add_argument(
        "--dat-out",
        default="bader_charges.dat",
        help="Legacy tab-delimited output filename for all atoms",
    )
    args = parser.parse_args()

    for path in (args.acf, args.potcar, args.poscar):
        if not os.path.exists(path):
            print(f"Error: required file '{path}' not found", file=sys.stderr)
            return 2

    all_data = calculate_bader_charge(args.acf, args.potcar, args.poscar)
    write_csv(all_data, args.out)
    write_dat(all_data, args.dat_out)

    if args.targets:
        try:
            idxs0 = parse_atom_targets(args.targets, args.poscar)
        except Exception as exc:
            print(f"Error parsing targets: {exc}", file=sys.stderr)
            return 4

        if not idxs0 and any("-" in target for target in args.targets):
            expanded: List[int] = []
            natoms = len(all_data)
            for target in args.targets:
                match = re.fullmatch(r"(\d+)-(\d+)", target)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2))
                    if start > end:
                        start, end = end, start
                    expanded.extend(i for i in range(start, end + 1) if 0 <= i < natoms)
            idxs0 = list(dict.fromkeys(expanded))

        wanted = set(i + 1 for i in idxs0)
        selected = [entry for entry in all_data if entry[0] in wanted]
    else:
        selected = all_data

    if not selected:
        print("No matching atoms found for the requested targets.", file=sys.stderr)
        return 0

    print("Index,Element,BaderCharge,ZVAL,ChargeTransfer")
    for idx, elem, bader_charge, zval, charge_transfer in selected:
        print(f"{idx},{elem},{bader_charge},{zval},{charge_transfer}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
