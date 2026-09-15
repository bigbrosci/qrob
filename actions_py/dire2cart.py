#!/usr/bin/env python3
"""Convert a POSCAR to Cartesian coordinates and fix its bottom layers."""

import argparse
from io import StringIO
from pathlib import Path
import shutil
import sys

from ase.constraints import FixAtoms
from ase.io import read, write

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.fix_atoms import detect_input_file, find_layers


def get_infor(file_to_be_converted):
    return read(file_to_be_converted, format="vasp")


def convert(file_to_be_converted, fixedlayer=0, threshold=0.5):
    if fixedlayer < 0:
        raise ValueError("The number of fixed layers must be nonnegative.")
    if not 0 < threshold < float("inf"):
        raise ValueError("The layer threshold must be finite and positive.")

    atoms = get_infor(file_to_be_converted)
    layers = find_layers(atoms.get_positions()[:, 2], threshold)
    fixed = [index for layer in layers[:fixedlayer] for index in layer]
    # Replace existing flags, matching the command's bottom-layer selection.
    atoms.set_constraint(FixAtoms(indices=fixed))

    output = StringIO()
    write(output, atoms, format="vasp", direct=False, vasp5=True, sort=False)
    path = Path(file_to_be_converted)
    shutil.copyfile(path, str(path) + "_back")
    path.write_text(output.getvalue())
    print(f"Found {len(layers)} layers; fixed {len(fixed)} atoms.")
    print(f"{path} now has Cartesian coordinates.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", dest="file", help="Input file (default: POSCAR or CONTCAR)")
    parser.add_argument("-s", dest="selected", type=int, default=0,
                        help="Number of bottom layers to fix")
    parser.add_argument("-t", dest="threshold", type=float, default=0.5,
                        help="Maximum z spacing within a layer in angstroms (default: 0.5)")
    options = parser.parse_args(argv)
    try:
        convert(detect_input_file(options.file), options.selected, options.threshold)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
