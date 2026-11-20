"""Automated architecture tests for the AI Engineering Knowledge Engine."""

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent
FEATURES_DIR = Path(__file__).resolve().parent.parent / "features"
SLICES = sorted(path for path in FEATURES_DIR.iterdir() if path.is_dir())
COMPOSITION_ROOT_EXCLUDED = {"app.py", "test_ui.py"}
MAX_LINES = 150
FRONTEND_MAX_LINES = 350
FRONTEND_TEMPLATES = {"template.py", "modals.py", "script.py", "chat_actions.py"}


def line_limit(path: Path) -> int:
    relative = path.relative_to(CORE_DIR.parent)
    frontend = relative.parts[:2] == ("features", "ui")
    if frontend and (path.name in FRONTEND_TEMPLATES or path.name.endswith("_script.py")):
        return FRONTEND_MAX_LINES
    if relative.parts[:3] == ("features", "ui", "static") and path.suffix in {".js", ".css"}:
        return FRONTEND_MAX_LINES
    return MAX_LINES


def _feature_imports(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("features."):
                    modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("features."):
            modules.add(node.module)
    return modules


def test_file_size_ceiling() -> None:
    """Backend sources stay within 150 lines; frontend templates/assets may use 350."""
    excluded = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "build", "dist"}
    sources = sorted(p for p in CORE_DIR.parent.rglob("*") if p.suffix in {".py", ".js", ".css"} and not excluded.intersection(p.parts))
    oversized = [f"{p}: limit {line_limit(p)}" for p in sources if len(p.read_text(encoding="utf-8").splitlines()) > line_limit(p)]
    assert oversized == []


def test_line_limits_distinguish_routes_from_templates() -> None:
    root = CORE_DIR.parent
    assert line_limit(root / "features/ui/graph_script.py") == 350
    assert line_limit(root / "features/ui/static/graph.js") == 350
    assert line_limit(root / "features/ui/document_routes.py") == 150
    assert line_limit(root / "features/ingestion/service.py") == 150


def test_vertical_slice_isolation() -> None:
    """Feature slices must not import from other feature slices."""
    violations: list[str] = []
    for slice_dir in SLICES:
        for py_file in sorted(slice_dir.rglob("*.py")):
            if slice_dir.name == "ui" and py_file.name in COMPOSITION_ROOT_EXCLUDED:
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for module in _feature_imports(tree):
                imported_slice = module.removeprefix("features.").split(".")[0]
                if imported_slice != slice_dir.name:
                    violations.append(f"{py_file} imports {module}")
    assert violations == []
