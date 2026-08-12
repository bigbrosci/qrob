#!/usr/bin/env python3
"""Calculate thermochemistry for one species directory.

Usage:
    python get_GS.py XXX

``XXX`` must contain OUTCAR, OUTCAR_freq (or freq/OUTCAR), and CONTCAR or
POSCAR.  The result is written to ``XXX.csv`` in the current directory, where
XXX is the input directory's name.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from get_GS_species import PRESSURE, TEMPERATURE, thermochemistry


COLUMNS = [
    "path",
    "T_K",
    "E_DFT",
    "ZPE",
    "TS",
    "S_eV/K",
    "S_J/mol/K",
    "G",
]


def output_path_for(species_dir: Path) -> Path:
    """Return <species-folder-name>.csv in the current working directory."""
    return Path.cwd() / f"{species_dir.name}.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "species",
        type=Path,
        help="folder containing OUTCAR and OUTCAR_freq",
    )
    args = parser.parse_args()

    species_dir = args.species.expanduser().resolve()
    if not species_dir.is_dir():
        parser.error(f"species folder does not exist: {args.species}")
    if not (species_dir / "OUTCAR").is_file():
        parser.error(f"OUTCAR does not exist in: {args.species}")

    try:
        values = thermochemistry(species_dir)
    except Exception as exc:
        parser.exit(1, f"Error: could not process {args.species}: {exc}\n")

    output = output_path_for(species_dir)
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerow(
            [
                species_dir.name,
                f"{TEMPERATURE:.10f}",
                *(f"{value:.10f}" for value in values),
            ]
        )

    print(
        f"Wrote {output} at T={TEMPERATURE:g} K and P={PRESSURE:g} Pa."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
