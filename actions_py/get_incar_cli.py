#!/usr/bin/env python3
"""Generate an INCAR via the shared brain/incar helper."""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

from brain import incar as brain_incar


def list_tasks() -> None:
    print("Supported INCAR tasks:")
    print(" ".join(sorted(brain_incar.tasks_recorded)))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Produce an INCAR file from brain/incar.py",
        epilog="Use --list to print available task keywords.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tasks", nargs="*", help="Task keywords such as dftu, neb, ispin")
    parser.add_argument("--list", "-l", action="store_true", help="List supported task keywords")
    args = parser.parse_args(argv)

    if args.list:
        list_tasks()
        return

    try:
        brain_incar.build_incar(args.tasks)
        task_msg = f" (tasks: {' '.join(args.tasks)})" if args.tasks else ''
        print(f"INCAR generated from brain/incar.py{task_msg}")
    except brain_incar.UnsupportedTasksError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
