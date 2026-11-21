"""Package entrypoint delegating to the realm-engine launcher."""

import sys
from pathlib import Path

from core.version import APP_VERSION

__version__ = APP_VERSION


def main() -> None:
    try:
        from main import main as run_launcher
    except ImportError:
        root = str(Path(__file__).resolve().parents[2])
        if root not in sys.path:
            sys.path.insert(0, root)
        from main import main as run_launcher

    run_launcher()
