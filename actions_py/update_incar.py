#!/usr/bin/env python3
"""Build a magnetization database from VASP folders and refresh `brain/data.py`.

Workflow:
1. Find folders that contain `OUTCAR` plus `POSCAR` or `CONTCAR`.
2. For each folder, export `Magnetization.csv` with 0-based atom index,
   element symbol, and total per-atom magnetic moment.
3. Aggregate all per-atom CSVs by element and compute the mean moment.
4. Write the result into `brain/data.py` as `mag_value_database`.

If no database folders are found, the script still keeps the codebase usable by
writing an empty `mag_value_database = {}` block.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from ase.io import read as ase_read
except Exception:  # pragma: no cover - optional dependency
    ase_read = None


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "brain" / "data.py"
SUMMARY_CSV = REPO_ROOT / "mag_value_database_summary.csv"
CSV_NAME = "Magnetization.csv"


def read_symbols(structure_path: Path) -> List[str]:
    """Return chemical symbols in POSCAR order."""
    if ase_read is None:
        raise RuntimeError("ASE is required to read POSCAR/CONTCAR files")

    atoms = ase_read(str(structure_path), format="vasp")
    return atoms.get_chemical_symbols()


def extract_total_moments(outcar_path: Path) -> List[float]:
    """Extract the total moment column from the last magnetization block."""
    lines = outcar_path.read_text(errors="ignore").splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if "magnetization (x)" in line:
            header_idx = idx
    if header_idx is None:
        raise ValueError(f"magnetization block not found in {outcar_path}")

    start_idx = header_idx + 4
    totals: List[float] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            if totals:
                break
            continue
        if stripped.startswith("tot"):
            break
        parts = stripped.split()
        if not parts or not parts[0].isdigit():
            continue
        try:
            totals.append(float(parts[-1]))
        except ValueError:
            continue

    return totals


def locate_structure_file(folder: Path) -> Path | None:
    """Prefer CONTCAR, then POSCAR."""
    contcar = folder / "CONTCAR"
    poscar = folder / "POSCAR"
    if contcar.is_file():
        return contcar
    if poscar.is_file():
        return poscar
    return None


def write_case_csv(folder: Path, symbols: List[str], moments: List[float]) -> Path:
    """Write per-folder atom-level magnetization CSV."""
    out_path = folder / CSV_NAME
    rows = []
    n = min(len(symbols), len(moments))
    for idx in range(n):
        rows.append(
            {
                "index": idx,
                "element": symbols[idx],
                "magmom": moments[idx],
            }
        )

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["index", "element", "magmom"])
        writer.writeheader()
        writer.writerows(rows)

    return out_path


def collect_case_rows(csv_paths: Iterable[Path]) -> List[Tuple[str, float]]:
    """Read all per-folder CSVs and flatten them into (element, magmom) rows."""
    rows: List[Tuple[str, float]] = []
    for csv_path in csv_paths:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                element = (row.get("element") or "").strip()
                if not element:
                    continue
                try:
                    magmom = float(row.get("magmom", "0.0"))
                except ValueError:
                    continue
                rows.append((element, magmom))
    return rows


def summarize_by_element(rows: Iterable[Tuple[str, float]]) -> Dict[str, float]:
    """Average the magnetic moment for each element symbol."""
    totals: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)

    for element, magmom in rows:
        totals[element] += magmom
        counts[element] += 1

    summary = {
        element: totals[element] / counts[element]
        for element in sorted(totals.keys())
        if counts[element]
    }
    return summary


def render_mag_database(summary: Dict[str, float]) -> str:
    """Render the Python assignment used inside `brain/data.py`."""
    if not summary:
        return "mag_value_database = {}"

    body = ",\n".join(
        f"    {element!r}: {repr(float(value))}" for element, value in summary.items()
    )
    return "mag_value_database = {\n" + body + "\n}"


def update_data_py(summary: Dict[str, float]) -> None:
    """Replace the marked database block in `brain/data.py`."""
    text = DATA_PATH.read_text(encoding="utf-8")
    replacement = (
        "# BEGIN MAG_VALUE_DATABASE\n"
        f"{render_mag_database(summary)}\n"
        "# END MAG_VALUE_DATABASE"
    )

    pattern = re.compile(
        r"# BEGIN MAG_VALUE_DATABASE\nmag_value_database\s*=\s*\{.*?\}\n# END MAG_VALUE_DATABASE",
        re.S,
    )
    if not pattern.search(text):
        raise RuntimeError(
            "Could not find the MAG_VALUE_DATABASE marker block in brain/data.py"
        )

    DATA_PATH.write_text(pattern.sub(replacement, text), encoding="utf-8")


def maybe_write_summary_csv(summary: Dict[str, float], csv_paths: List[Path]) -> None:
    """Write a compact summary CSV for inspection."""
    fieldnames = ["element", "average_magmom", "atom_count", "source_csv_count"]
    atom_counts: Dict[str, int] = defaultdict(int)
    source_counts: Dict[str, int] = defaultdict(int)

    for csv_path in csv_paths:
        seen_in_file = set()
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                element = (row.get("element") or "").strip()
                if not element:
                    continue
                atom_counts[element] += 1
                seen_in_file.add(element)
        for element in seen_in_file:
            source_counts[element] += 1

    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for element in sorted(summary.keys()):
            writer.writerow(
                {
                    "element": element,
                    "average_magmom": summary[element],
                    "atom_count": atom_counts[element],
                    "source_csv_count": source_counts[element],
                }
            )


def scan_database_roots(roots: Iterable[Path]) -> List[Path]:
    """Find folders that contain an OUTCAR and a matching POSCAR/CONTCAR."""
    case_dirs = []
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        for outcar in root.rglob("OUTCAR"):
            folder = outcar.parent
            if folder in seen:
                continue
            if locate_structure_file(folder) is None:
                continue
            seen.add(folder)
            case_dirs.append(folder)
    return sorted(case_dirs)


def process_case(folder: Path) -> Path | None:
    """Generate the atom-level CSV for a single calculation folder."""
    outcar_path = folder / "OUTCAR"
    structure_path = locate_structure_file(folder)
    if structure_path is None or not outcar_path.is_file():
        return None

    symbols = read_symbols(structure_path)
    moments = extract_total_moments(outcar_path)
    if not symbols or not moments:
        return None

    if len(moments) < len(symbols):
        moments = moments + [0.0] * (len(symbols) - len(moments))

    return write_case_csv(folder, symbols, moments)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build per-folder magnetization CSVs and refresh brain/data.py"
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=["."],
        help="Database root directories to scan recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report but do not write data.py or the summary CSV",
    )
    return parser


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    roots = [Path(root).expanduser().resolve() for root in args.roots]

    case_dirs = scan_database_roots(roots)
    csv_paths: List[Path] = []

    for folder in case_dirs:
        csv_path = process_case(folder)
        if csv_path is not None:
            csv_paths.append(csv_path)

    rows = collect_case_rows(csv_paths)
    summary = summarize_by_element(rows)

    print(f"Scanned {len(case_dirs)} calculation folders.")
    print(f"Generated {len(csv_paths)} per-folder CSV files.")
    print(f"Elements in summary: {len(summary)}")

    if args.dry_run:
        print("Dry run requested; not updating brain/data.py.")
        return 0

    update_data_py(summary)
    maybe_write_summary_csv(summary, csv_paths)

    print(f"Updated {DATA_PATH}")
    print(f"Wrote summary CSV to {SUMMARY_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
