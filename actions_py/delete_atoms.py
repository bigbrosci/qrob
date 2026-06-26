#!/usr/bin/env python3
"""
Delete atoms from a POSCAR/CONTCAR using one unified CLI.

You can delete atoms by:
- element symbols
- atom indices or ranges
- hydrogen atoms farther than a cutoff from a reference element

Examples:
  python delete_atoms.py POSCAR C H O 0 2 5
  python delete_atoms.py POSCAR C 0-2
  python delete_atoms.py POSCAR --delete-far-h --anchor-element N --distance-cutoff 1.5
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse
import re

from ase.io import read, write
from brain.poscar import parse_atom_targets


def parse_index_range(token: str, natoms: int) -> list[int]:
    match = re.fullmatch(r"(\d*)-(\d*)", token)
    if not match:
        raise ValueError(f"Unrecognized range token: {token}")

    start_s, end_s = match.groups()
    if not start_s and not end_s:
        raise ValueError("Range token '-' is ambiguous.")

    start = int(start_s) if start_s else 0
    end = int(end_s) if end_s else natoms - 1

    if start > end:
        start, end = end, start
    start = max(start, 0)
    end = min(end, natoms - 1)
    return list(range(start, end + 1))


def parse_targets(tokens: list[str], poscar_path: str, natoms: int) -> set[int]:
    direct_tokens = [token for token in tokens if "-" not in token]
    selected = set(parse_atom_targets(direct_tokens, poscar_path)) if direct_tokens else set()

    for token in tokens:
        if "-" not in token:
            continue
        selected.update(parse_index_range(token, natoms))

    return selected


def far_h_indices(atoms, anchor_element: str, cutoff: float) -> set[int]:
    anchor_indices = [atom.index for atom in atoms if atom.symbol == anchor_element]
    if not anchor_indices:
        raise ValueError(f"No anchor element '{anchor_element}' found in structure.")
    if len(anchor_indices) > 1:
        raise ValueError(
            f"Expected one anchor element '{anchor_element}', found {len(anchor_indices)}. "
            "Please narrow the structure or adjust the script if multiple anchors are intended."
        )

    anchor_index = anchor_indices[0]
    delete_h: set[int] = set()
    for atom in atoms:
        if atom.symbol != "H":
            continue
        distance = atoms.get_distance(anchor_index, atom.index, mic=True)
        if distance > cutoff:
            delete_h.add(atom.index)
    return delete_h


def write_deleted_atoms_log(file_in: str, deleted_indices: list[int], atoms) -> Path:
    deleted_out = Path(file_in).with_name("atom_deleted")
    with deleted_out.open("w", encoding="utf-8") as fh:
        fh.write("# index symbol x y z (Cartesian coordinates in Angstrom)\n")
        for idx in deleted_indices:
            symbol = atoms[idx].symbol
            x, y, z = atoms.positions[idx]
            fh.write(f"{idx} {symbol} {x:.10f} {y:.10f} {z:.10f}\n")
    return deleted_out


def output_name(file_in: str) -> str:
    path = Path(file_in)
    if path.name in {"POSCAR", "CONTCAR"}:
        return str(path.with_name("POSCAR_deleted"))
    return str(path.with_name(path.name + "_deleted"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete atoms from a POSCAR/CONTCAR file.")
    parser.add_argument("file", help="Input POSCAR/CONTCAR file")
    parser.add_argument(
        "targets",
        nargs="*",
        help="Element symbols or atom indices/ranges to delete (0-based by default)",
    )
    parser.add_argument(
        "--delete-far-h",
        action="store_true",
        help="Delete H atoms farther than the cutoff from the anchor element",
    )
    parser.add_argument(
        "--anchor-element",
        default="N",
        help="Reference element used with --delete-far-h (default: N)",
    )
    parser.add_argument(
        "--distance-cutoff",
        type=float,
        default=1.5,
        help="Distance cutoff in Angstrom for --delete-far-h (default: 1.5)",
    )
    args = parser.parse_args()

    if not args.targets and not args.delete_far_h:
        parser.error("Provide deletion targets and/or --delete-far-h.")

    try:
        atoms = read(args.file, format="vasp")
    except Exception as exc:
        print(f"Error: failed to read '{args.file}': {exc}", file=sys.stderr)
        return 3

    atoms_to_delete: set[int] = set()
    if args.targets:
        try:
            atoms_to_delete.update(parse_targets(args.targets, args.file, len(atoms)))
        except Exception as exc:
            print(f"Error parsing targets: {exc}", file=sys.stderr)
            return 2

    if args.delete_far_h:
        try:
            atoms_to_delete.update(far_h_indices(atoms, args.anchor_element, args.distance_cutoff))
        except Exception as exc:
            print(f"Error in --delete-far-h mode: {exc}", file=sys.stderr)
            return 4

    if not atoms_to_delete:
        print("No atoms matched the requested deletion criteria.")
        return 0

    deleted_indices = sorted(atoms_to_delete)
    deleted_log = write_deleted_atoms_log(args.file, deleted_indices, atoms)
    kept_indices = [idx for idx in range(len(atoms)) if idx not in atoms_to_delete]
    new_atoms = atoms[kept_indices]

    out_name = output_name(args.file)
    write(out_name, new_atoms, format="vasp", vasp5=True)
    print(f"The output files are: {out_name} and {deleted_log}")
    print(f"Deleted {len(deleted_indices)} atom(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
