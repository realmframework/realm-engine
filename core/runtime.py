"""Configurable runtime mode and local data root shared by launchers and stores."""

import os
from pathlib import Path
from typing import Literal

AppMode = Literal["local", "public"]


def data_root() -> Path:
    default = Path(__file__).resolve().parents[1] / "data"
    return Path(os.environ.get("REALM_DATA_DIR", default)).expanduser().resolve()


def app_mode() -> AppMode:
    return "public" if os.environ.get("REALM_MODE", "local").strip().lower() == "public" else "local"
