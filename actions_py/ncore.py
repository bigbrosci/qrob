#!/usr/bin/env python3
"""Update NCORE in INCAR unless the job is a frequency/phonon calculation."""

from __future__ import annotations

import re
import sys
from pathlib import Path


INCAR_PATH = Path("INCAR")
FREQ_IBRION_VALUES = {"5", "6", "7", "8"}


def read_incar_lines(path: Path) -> list[str]:
    if not path.exists():
        print(f"Error: {path} not found in current directory", file=sys.stderr)
        sys.exit(2)
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def get_ibrion_value(lines: list[str]) -> str | None:
    for line in lines:
        if re.match(r"^\s*IBRION\b", line, flags=re.IGNORECASE):
            match = re.search(r"=\s*([-\d]+)", line)
            if match:
                return match.group(1)
    return None


def has_ncore(lines: list[str]) -> bool:
    return any(re.match(r"^\s*NCORE\b", line, flags=re.IGNORECASE) for line in lines)


def replace_ncore(lines: list[str], value: str) -> list[str]:
    updated = []
    replaced = False
    for line in lines:
        if re.match(r"^\s*NCORE\b", line, flags=re.IGNORECASE):
            updated.append(f"NCORE = {value}\n")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(f"NCORE = {value}\n")
    return updated


def main() -> int:
    requested_value = sys.argv[1] if len(sys.argv) > 1 else "8"
    lines = read_incar_lines(INCAR_PATH)

    ibrion = get_ibrion_value(lines)
    if ibrion in FREQ_IBRION_VALUES:
        print(f"Skipped NCORE update because IBRION = {ibrion} indicates a frequency/phonon calculation.")
        return 0

    if len(sys.argv) > 1:
        new_lines = replace_ncore(lines, requested_value)
        INCAR_PATH.write_text("".join(new_lines), encoding="utf-8")
        print(f"Set NCORE = {requested_value} in {INCAR_PATH}")
        return 0

    if has_ncore(lines):
        print(f"NCORE already exists in {INCAR_PATH}. No change made.")
        return 0

    new_lines = replace_ncore(lines, requested_value)
    INCAR_PATH.write_text("".join(new_lines), encoding="utf-8")
    print(f"Added NCORE = {requested_value} to {INCAR_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
