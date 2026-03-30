from pathlib import Path
import sys


def ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


__all__ = ["ensure_repo_root"]
