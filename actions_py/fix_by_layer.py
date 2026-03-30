#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""
Fix bottom N layers in a slab POSCAR using ASE.

Features:
1) Identify layers by clustering atomic Cartesian z positions
2) Apply FixAtoms constraint to atoms in bottom N layers
3) Write POSCAR with Selective Dynamics in Cartesian coordinates
"""

import argparse
import os
import sys

from ase.io import read
from ase.constraints import FixAtoms
from ase.io.vasp import write_vasp


# --------------------------------------------------
# Layer detection
# --------------------------------------------------
def find_layers(z_coords, threshold=0.5):
    """
    Group atoms into layers using a z-gap threshold.

    Parameters
    ----------
    z_coords : array-like
        Cartesian z coordinates (Å)
    threshold : float
        Gap (Å) above which a new layer is started

    Returns
    -------
    layers : list[list[int]]
        Atom indices for each layer, ordered bottom → top
    """
    idx_z = list(enumerate(z_coords))
    idx_z.sort(key=lambda x: x[1])

    layers = []
    current = [idx_z[0][0]]
    prev_z = idx_z[0][1]

    for idx, z in idx_z[1:]:
        if z - prev_z > threshold:
            layers.append(current)
            current = [idx]
        else:
            current.append(idx)
        prev_z = z

    layers.append(current)
    return layers


# --------------------------------------------------
# Main
# --------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fix bottom layers in a slab POSCAR using ASE"
    )
    parser.add_argument(
        "-i", "--input",
        default=None,
        help="Input POSCAR/CONTCAR (default: POSCAR or CONTCAR in cwd)"
    )
    parser.add_argument(
        "-s", "--fix-layers",
        type=int,
        required=True,
        help="Number of bottom layers to fix"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.5,
        help="z-gap threshold in Å for layer separation (default: 0.5)"
    )
    parser.add_argument(
        "-o", "--output",
        default="POSCAR_fixed",
        help="Output POSCAR filename"
    )
    args = parser.parse_args(argv)

    # --------------------------------------------------
    # Input file detection
    # --------------------------------------------------
    infile = args.input
    if infile is None:
        if os.path.isfile("POSCAR"):
            infile = "POSCAR"
        elif os.path.isfile("CONTCAR"):
            infile = "CONTCAR"
        else:
            sys.exit("Error: POSCAR or CONTCAR not found.")

    # --------------------------------------------------
    # Read structure
    # --------------------------------------------------
    atoms = read(infile, format="vasp")

    # --------------------------------------------------
    # Identify layers (Cartesian z)
    # --------------------------------------------------
    z_coords = atoms.get_positions()[:, 2]
    layers = find_layers(z_coords, threshold=args.threshold)

    if not layers:
        sys.exit("Error: no layers detected.")

    print(f"Detected {len(layers)} layers (bottom → top)")

    # --------------------------------------------------
    # Select layers to fix
    # --------------------------------------------------
    n_fix = min(args.fix_layers, len(layers))
    fixed_indices = [i for layer in layers[:n_fix] for i in layer]

    print(
        f"Fixing {n_fix} bottom layers "
        f"({len(fixed_indices)} atoms)"
    )

    # --------------------------------------------------
    # Apply ASE constraints
    # --------------------------------------------------
    atoms.set_constraint(FixAtoms(indices=fixed_indices))

    # --------------------------------------------------
    # Selective dynamics flags
    # True  = movable (T)
    # False = fixed   (F)
    # --------------------------------------------------
    selective_flags = [[True, True, True] for _ in range(len(atoms))]
    for i in fixed_indices:
        selective_flags[i] = [False, False, False]

    # --------------------------------------------------
    # Write POSCAR (Cartesian)
    # --------------------------------------------------
    write_vasp(
        args.output,
        atoms,
        direct=False,                 # Cartesian coordinates
        selective_dynamics=selective_flags,
        vasp5=True
    )

    print(f"Wrote Cartesian POSCAR with Selective Dynamics: {args.output}")


if __name__ == "__main__":
    main()
