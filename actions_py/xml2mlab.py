#!/usr/bin/env python3
"""Convert VASP `vasprun.xml` outputs into an ML_AB-style training dataset."""

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

from brain.ml_ab import build_dataset, parse_vasprun_to_mlab_configurations


def resolve_input_paths(inputs: list[str], vasprun_name: str) -> list[Path]:
    if inputs:
        resolved: list[Path] = []
        for item in inputs:
            path = Path(item).resolve()
            if path.is_dir():
                resolved.append(path / vasprun_name)
            else:
                resolved.append(path)
        return resolved

    cwd = Path.cwd()
    local_vasprun = cwd / vasprun_name
    if local_vasprun.is_file():
        return [local_vasprun]

    subdir_vaspruns = sorted(
        path / vasprun_name for path in cwd.iterdir() if path.is_dir() and (path / vasprun_name).is_file()
    )
    if subdir_vaspruns:
        return subdir_vaspruns

    raise FileNotFoundError(f"No {vasprun_name} found in the current directory or its immediate subdirectories.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert one or more VASP XML runs into an ML_AB file.")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Directories containing vasprun.xml or explicit vasprun.xml paths. Default: current directory or all immediate subdirectories.",
    )
    parser.add_argument("--vasprun-name", default="vasprun.xml", help="Vasprun filename to look for (default: vasprun.xml)")
    parser.add_argument("--output", default="ML_AB", help="Output ML_AB filename (default: ML_AB)")
    parser.add_argument(
        "--ctifor",
        type=float,
        default=2.0e-2,
        help="CTIFOR value to write for every configuration (default: 2.0e-2)",
    )
    parser.add_argument(
        "--omit-ctifor",
        action="store_true",
        help="Omit the optional CTIFOR block entirely for all configurations",
    )
    args = parser.parse_args()

    vasprun_paths = resolve_input_paths(args.inputs, args.vasprun_name)

    merged_configurations = []
    for vasprun_path in vasprun_paths:
        try:
            ctifor = None if args.omit_ctifor else args.ctifor
            configurations = parse_vasprun_to_mlab_configurations(vasprun_path, ctifor=ctifor)
            merged_configurations.extend(configurations)
            print(f"Processed {vasprun_path}: {len(configurations)} configuration(s)")
        except Exception as exc:
            print(f"Error processing {vasprun_path}: {exc}", file=sys.stderr)

    if not merged_configurations:
        print("No configurations were converted.", file=sys.stderr)
        return 1

    dataset = build_dataset(merged_configurations)
    output_path = dataset.write_file(args.output)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
