"""Single source of truth for supported document, code, and config file types & security ignore rules."""

from __future__ import annotations

from pathlib import Path

DOC_EXTENSIONS: tuple[str, ...] = (".md", ".txt", ".html", ".docx", ".pdf", ".csv", ".tsv", ".xlsx", ".pptx")
CODE_LANG_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".xml": "xml",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".dart": "dart",
    ".rb": "ruby",
    ".php": "php",
    ".r": "r",
    ".lua": "lua",
    ".graphql": "graphql",
    ".proto": "protobuf",
}
CODE_EXTENSIONS: tuple[str, ...] = tuple(CODE_LANG_BY_EXT.keys())
ALL_EXTENSIONS: tuple[str, ...] = (*DOC_EXTENSIONS, *CODE_EXTENSIONS)
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(ALL_EXTENSIONS)
EDITABLE_TEXT_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt", ".html", *CODE_EXTENSIONS})

IGNORED_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        "target",
        "vendor",
        "venv",
        "env",
        "coverage",
        "out",
        "bin",
        "obj",
        "pkg",
        "pods",
        "deriveddata",
    }
)
IGNORED_FILENAMES: frozenset[str] = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "uv.lock",
        "poetry.lock",
        "cargo.lock",
        "composer.lock",
        "gemfile.lock",
        "pipfile.lock",
    }
)
_SECRET_TOKENS: tuple[str, ...] = ("id_rsa", "id_ed25519", "id_ecdsa", ".pem", ".key", ".p12", ".pfx", ".secret", ".sqlite", ".db", "credentials.")
_SECRET_FILENAMES: frozenset[str] = frozenset({"credentials.json", "service-account.json", "client_secret.json"})
REALM_INTERNAL_ROOT_FILES: frozenset[str] = frozenset(
    {
        "index.json",
        "chats.json",
        "workspace.json",
        "study_deck.json",
        "study_progress.json",
        "work_board.json",
        "impact_ledger.json",
        "focus_engine.json",
        "workflows.json",
        "linked_vaults.json",
        "output_formats.json",
        "secrets.json",
        "budget_state.json",
        "local_ai_state.json",
    }
)


def is_ignored_relpath(rel_path: Path) -> bool:
    """Return True for hidden paths, build/dependency folders, lockfiles, REALM stores, or secrets."""
    parts = rel_path.parts
    if not parts:
        return True
    if any(p.startswith(".") for p in parts):
        return True
    if any(p.lower() in IGNORED_DIRS for p in parts):
        return True
    name = parts[-1].lower()
    if len(parts) == 1 and name in REALM_INTERNAL_ROOT_FILES:
        return True
    if name in IGNORED_FILENAMES or name in _SECRET_FILENAMES or name.startswith(".env"):
        return True
    return any(tok in name for tok in _SECRET_TOKENS)


def code_language_for(filename_or_ext: str) -> str:
    """Return a clean syntax language label for code/config files, or empty string for docs."""
    ext = filename_or_ext.lower() if filename_or_ext.startswith(".") else Path(filename_or_ext).suffix.lower()
    return CODE_LANG_BY_EXT.get(ext, "")
