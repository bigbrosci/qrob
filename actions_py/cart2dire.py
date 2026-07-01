#!/usr/bin/env python3
"""
Convert a VASP structure from Cartesian coordinates to direct coordinates using ASE.

This helper reads a POSCAR/CONTCAR-like file with ASE, keeps the same structure
and lattice, and writes the output in VASP direct-coordinate format. By default
it writes `<input>_direct` so the original file stays untouched.
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
import shutil

from ase.io import read, write


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Cartesian coordinates in a VASP file to direct coordinates using ASE."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="POSCAR",
        help="Input POSCAR/CONTCAR file (default: POSCAR)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file name (default: <input>_direct)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file after saving a <input>_back backup",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    atoms = read(input_path, format="vasp")

    if args.in_place:
        backup_path = input_path.with_name(f"{input_path.name}_back")
        shutil.copy2(input_path, backup_path)
        output_path = input_path
    else:
        output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.name}_direct")

    write(output_path, atoms, format="vasp", direct=True, vasp5=True)
    print(f"Wrote direct-coordinate structure to {output_path}")
    if args.in_place:
        print(f"Saved backup of the original file to {backup_path}")


if __name__ == "__main__":
    main()


# #!/usr/bin/env python3
# """
# Reference implementation showing the math behind Cartesian -> direct conversion.

# This file preserves the original hand-worked approach for learning purposes.
# The idea is:
# 1. Read the three lattice vectors from the POSCAR.
# 2. Compute lattice lengths and inter-vector angles.
# 3. Build the matrix that converts Cartesian coordinates into direct coordinates.
# 4. Multiply a Cartesian coordinate by that conversion matrix.

# For day-to-day use, prefer `cart2dire.py`, which performs the same task through
# ASE with a cleaner and safer CLI.
# """

# import sys
# from pathlib import Path

# repo_root = Path(__file__).resolve().parent.parent
# brain_root = repo_root / "brain"
# for candidate in (repo_root, brain_root):
#     if str(candidate) not in sys.path:
#         sys.path.insert(0, str(candidate))

# from actions_py.bootstrap import ensure_repo_root

# ensure_repo_root()

# import numpy as np
# from math import cos, sin, sqrt

# from lattice import get_abc, read_car


# def unit_vector(vector):
#     """Return the unit vector of an input vector."""

#     return vector / np.linalg.norm(vector)


# def get_angle(v1, v2):
#     """Return the angle in radians between two vectors."""

#     v1_u = unit_vector(v1)
#     v2_u = unit_vector(v2)
#     return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


# def get_vectors(lines):
#     """Read the three lattice vectors from POSCAR-style text lines."""

#     la1 = np.array([float(i) for i in lines[2].strip().split()])
#     la2 = np.array([float(i) for i in lines[3].strip().split()])
#     la3 = np.array([float(i) for i in lines[4].strip().split()])
#     return np.array([la1, la2, la3])


# def main() -> None:
#     lines = read_car("POSCAR")[0]
#     va, vb, vc = get_vectors(lines)
#     a, b, c = get_abc(lines)[0:3]
#     alpha = get_angle(vc, vb)
#     beta = get_angle(vc, va)
#     gamma = get_angle(va, vb)

#     omega = a * b * c * sqrt(
#         1
#         - cos(alpha) ** 2
#         - cos(beta) ** 2
#         - cos(gamma) ** 2
#         + 2 * cos(alpha) * cos(beta) * cos(gamma)
#     )

#     v_1 = [
#         1 / a,
#         -cos(gamma) / (a * sin(gamma)),
#         b * c * (cos(alpha) * cos(gamma) - cos(beta)) / (omega * sin(gamma)),
#     ]
#     v_2 = [
#         0,
#         1 / (b * sin(gamma)),
#         a * c * (cos(beta) * cos(gamma) - cos(alpha)) / (omega * sin(gamma)),
#     ]
#     v_3 = [0, 0, a * b * sin(gamma) / omega]

#     vector_direct = np.array([v_1, v_2, v_3])

#     # Example Cartesian coordinate from the original script.
#     coord = np.array([9.4940864321, 5.4814133571, 0.0000000000])
#     d, e, f = vector_direct * coord
#     print(sum(d), sum(e), sum(f))


# if __name__ == "__main__":
#     main()
