"""Package entrypoint delegating to the realm-engine launcher."""

import sys
from pathlib import Path


def main() -> None:
    root = str(Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)
    from main import main as run_launcher

    run_launcher()
