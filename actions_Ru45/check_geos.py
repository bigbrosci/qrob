#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()


def main() -> int:
    cwd = Path.cwd()
    for directory in sorted(p for p in cwd.iterdir() if p.is_dir() and "_" in p.name):
        result = subprocess.run(
            [str(Path(__file__).resolve().parent / "check_geo.py")],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        out = result.stdout.strip()
        if out and directory.name != out:
            print(f"{directory.name} {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
