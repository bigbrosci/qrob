#!/usr/bin/env python3
"""
Compute center of mass from a VASP POSCAR/CONTCAR using ASE and print a DIPOL line.

VASP expects DIPOL in *direct lattice coordinates* (fractional).  See VASP wiki.  :contentReference[oaicite:1]{index=1}
"""

import argparse
import numpy as np
from ase.io import read


def com_cart_and_direct(atoms, wrap=True):
    # ASE returns center of mass in Cartesian coordinates (Å)
    com_cart = atoms.get_center_of_mass()

    # Convert Cartesian -> direct (fractional):
    # r_cart = s_direct @ cell  (cell vectors are rows in ASE)
    cell = atoms.cell.array
    com_direct = np.linalg.solve(cell.T, com_cart)

    if wrap:
        com_direct = com_direct % 1.0  # keep in [0,1)
    return com_cart, com_direct


def update_incar(incar_path, dipol_direct, out_path=None):
    dipol_line = f"DIPOL = {dipol_direct[0]:.10f} {dipol_direct[1]:.10f} {dipol_direct[2]:.10f}\n"

    with open(incar_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().upper().startswith("DIPOL"):
            new_lines.append(dipol_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(dipol_line)

    out_path = out_path or incar_path
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("poscar", nargs="?", default="POSCAR", help="POSCAR/CONTCAR path")
    p.add_argument("--wrap", action="store_true", help="Wrap direct coords into [0,1)")
    p.add_argument(
        "--idipol3",
        action="store_true",
        help="Common slab case (IDIPOL=3): set x=y=0.5, z from COM",
    )
    p.add_argument("--incar", help="If set, write/replace DIPOL line in this INCAR")
    p.add_argument("--out", help="Output INCAR path (default: overwrite --incar)")

    args = p.parse_args()

    atoms = read(args.poscar)
    com_cart, com_direct = com_cart_and_direct(atoms, wrap=args.wrap)

#    print(f"# COM (Cartesian, Å): {com_cart[0]:.6f} {com_cart[1]:.6f} {com_cart[2]:.6f}")
#    print(
#        f"# COM (direct/fractional): {com_direct[0]:.10f} {com_direct[1]:.10f} {com_direct[2]:.10f}"
#    )

    dipol = np.array([0.5, 0.5, com_direct[2]]) if args.idipol3 else com_direct
    print(f"DIPOL = {dipol[0]:.10f} {dipol[1]:.10f} {dipol[2]:.10f}")

    if args.incar:
        update_incar(args.incar, dipol, out_path=args.out)


if __name__ == "__main__":
    main()

