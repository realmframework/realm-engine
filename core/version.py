"""Single source of truth for REALM Engine application version."""

import importlib.metadata
import tomllib
from pathlib import Path

_FALLBACK_VERSION = "0.10.0"


def _resolve_version() -> str:
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            with pyproject.open("rb") as handle:
                ver = str(tomllib.load(handle).get("project", {}).get("version") or "").strip()
            if ver:
                return ver
        except (OSError, ValueError):
            pass
    try:
        return importlib.metadata.version("realm-engine")
    except importlib.metadata.PackageNotFoundError:
        return _FALLBACK_VERSION


APP_VERSION = _resolve_version()
