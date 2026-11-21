"""Local CLI `ask` and `mcp` subcommand dispatcher (pure core, zero feature imports)."""

import argparse
import os
from collections.abc import Callable
from pathlib import Path

from core.mcp_bridge import (
    list_area_names,
    load_cfg,
    load_chunks_for_area,
    run_mcp_stdio,
)
from core.retrieval_xray import build_retrieval_xray


def run_cli_ask(root: Path, query: str, area: str = "", top_k: int = 5) -> str:
    """Query a local REALM workspace from the terminal and return grounded passages."""
    cfg = load_cfg(root)
    target = area or cfg.knowledge_dir
    if not target:
        found = list_area_names(root)
        if not found:
            return "No workspaces found. Create or link a workspace first."
        target = str(found[0]["name"])
    rows = build_retrieval_xray(query[:2000], load_chunks_for_area(root, target, cfg.excluded_subfolders.get(target, [])), top_k=top_k, retrieval_mode="lexical")
    if not rows:
        return f"No matching passages found in '{target}' for: {query}"
    lines = [f"REALM Search ({target}) — {len(rows)} matches for: {query}", ""]
    for idx, row in enumerate(rows, 1):
        lines.append(f"[{idx}] {row['title']} (doc_id={row['doc_id']}, bm25={row['bm25_score']})")
        lines.append(f"    {row['snippet']}")
    return "\n".join(lines)


def dispatch_cli_subcommand(raw_argv: list[str], resolve_root: Callable[[], Path]) -> bool:
    """Handle `ask` and `mcp` subcommands; return True when handled."""
    if not raw_argv or raw_argv[0] not in {"ask", "mcp"}:
        return False
    sub = argparse.ArgumentParser(prog=f"realm {raw_argv[0]}")
    sub.add_argument("--data-dir", type=Path)
    if raw_argv[0] == "ask":
        sub.add_argument("query")
        sub.add_argument("--area", default="")
        sub.add_argument("--top-k", type=int, default=5)
        ns = sub.parse_args(raw_argv[1:])
        if ns.data_dir:
            os.environ["REALM_DATA_DIR"] = str(ns.data_dir.expanduser().resolve())
        print(run_cli_ask(resolve_root(), ns.query, area=ns.area, top_k=ns.top_k))
        return True
    ns = sub.parse_args(raw_argv[1:])
    if ns.data_dir:
        os.environ["REALM_DATA_DIR"] = str(ns.data_dir.expanduser().resolve())
    run_mcp_stdio(resolve_root())
    return True
