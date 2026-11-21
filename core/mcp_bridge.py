"""Zero-dependency stdio MCP server exposing REALM local vaults and agents (pure core)."""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from core import linked_vaults
from core.agent_personas import list_agents
from core.contracts import KnowledgeChunk, SearchQuery, WorkspaceConfig
from core.db import load_chunks
from core.retrieval_xray import build_retrieval_xray
from core.version import APP_VERSION

_RESERVED = {"agents", "core", "features", "src", "docs", "tests", "node_modules", "__pycache__", "build", "dist", "wheels"}

def load_cfg(root: Path) -> WorkspaceConfig:
    path = root / "workspace.json"
    if path.is_file() and not path.is_symlink():
        try:
            return WorkspaceConfig.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return WorkspaceConfig()

def resolve_area(root: Path, name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name) or name in _RESERVED:
        raise ValueError("Invalid workspace area name")
    if (allowed := _allowed_mcp_areas()) is not None and name not in allowed:
        raise ValueError("Workspace area is not permitted for MCP access")
    if (linked := linked_vaults.resolve_linked_path(name, root)) is not None:
        return linked
    cand = root.resolve() / name
    if cand.is_symlink() or cand.resolve().parent != root.resolve() or not cand.is_dir():
        raise ValueError(f"Workspace area not found: {name}")
    return cand

def _is_excluded(subfolder: str, excluded: list[str]) -> bool:
    sub = unicodedata.normalize("NFC", subfolder.strip().strip("/")).casefold()
    return bool(sub) and any(sub == ex or sub.startswith(ex + "/") for raw in excluded if (ex := unicodedata.normalize("NFC", raw.strip().strip("/")).casefold()))

def _allowed_mcp_areas() -> set[str] | None:
    raw = os.environ.get("REALM_MCP_AREAS", "").strip()
    return {a.strip() for a in raw.split(",") if a.strip()} if raw else None

def _safe_contained(base: Path, rel_parts: tuple[str, ...]) -> Path | None:
    if not rel_parts or any(p in {"", ".", ".."} or p.startswith(".") or "\\" in p or "\x00" in p for p in rel_parts):
        return None
    cur = base
    for part in rel_parts:
        cur = cur / part
        if cur.is_symlink():
            return None
    return cur if cur.resolve().is_relative_to(base.resolve()) else None

def list_area_names(root: Path) -> list[dict[str, object]]:
    linked = linked_vaults.load_linked_vaults(root)
    names = set(linked.keys())
    if root.is_dir():
        for child in root.iterdir():
            if child.is_dir() and not child.is_symlink() and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", child.name) and child.name not in _RESERVED and ((child / ".knowledge-area.json").is_file() or (child / "index.json").is_file() or child.name == "knowledge_base"):
                names.add(child.name)
    return [{"name": n, "linked": n in linked} for n in sorted(names)]

def load_chunks_for_area(root: Path, area_name: str, excluded: list[str] | None = None) -> list[KnowledgeChunk]:
    target, excl = resolve_area(root, area_name), excluded or []
    cache = linked_vaults.cache_index_for_dir(target, root)
    if cache.is_file() and not cache.is_symlink() and (cached := load_chunks(cache)):
        return [c for c in cached if not _is_excluded(c.subfolder, excl)] if excl else cached
    chunks: list[KnowledgeChunk] = []
    for md in sorted(target.rglob("*.md")):
        rel = md.relative_to(target)
        sub = "" if rel.parent == Path(".") else rel.parent.as_posix()
        if _safe_contained(target, rel.parts) is None or _is_excluded(sub, excl):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if text:
            doc_id = rel.with_suffix("").as_posix()
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("# ")), md.stem)
            chunks.append(KnowledgeChunk(id=f"{doc_id}-0", doc_id=doc_id, title=title, file_path=str(md), area=area_name, subfolder=sub, content=text[:4000], tags=[]))
    return chunks

MCP_TOOLS = [
    {"name": "realm_list_areas", "description": "List available local and linked REALM workspaces.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "realm_list_agents", "description": "List configured REALM persona.md agents.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "realm_search", "description": "Search a REALM workspace and return grounded passages.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "area": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]}},
    {"name": "realm_read_guide", "description": "Read a Markdown guide inside a REALM workspace.", "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string"}, "area": {"type": "string"}}, "required": ["doc_id"]}},
]
def _call_mcp_tool(name: str, args: dict[str, object], root: Path) -> str:
    cfg = load_cfg(root)
    if name == "realm_list_areas":
        return json.dumps(list_area_names(root), indent=2)
    if name == "realm_list_agents":
        return json.dumps([{"id": a.id, "name": a.name, "role": a.role, "tagline": a.tagline} for a in list_agents(root, cfg.agent_name)], indent=2)
    if name == "realm_search":
        q, area, top_k = str(args.get("query") or "").strip()[:2000], str(args.get("area") or cfg.knowledge_dir or "").strip(), max(1, min(15, int(str(args.get("top_k") or 5))))
        if not q or not area:
            return json.dumps({"error": "Provide a query and an existing workspace area"})
        _ = SearchQuery(query=q, top_k=top_k)
        return json.dumps(build_retrieval_xray(q, load_chunks_for_area(root, area, cfg.excluded_subfolders.get(area, [])), top_k=top_k, retrieval_mode="lexical"), indent=2)
    if name == "realm_read_guide":
        doc_id, area = str(args.get("doc_id") or "").strip().strip("/"), str(args.get("area") or cfg.knowledge_dir or "").strip()
        if not doc_id or not area:
            raise ValueError("Provide a valid doc_id and area")
        base, parts = resolve_area(root, area), tuple(f"{doc_id}.md".split("/"))
        path = _safe_contained(base, parts)
        if path is None or not path.is_file():
            raise ValueError("Guide not found")
        if _is_excluded("/".join(parts[:-1]), cfg.excluded_subfolders.get(area, [])):
            raise ValueError("Guide is inside an unloaded subfolder")
        with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(60_000)
    raise ValueError(f"Unknown tool: {name}")

def handle_mcp_request(req: dict[str, object], root: Path) -> dict[str, object] | None:
    method, req_id = str(req.get("method") or ""), req.get("id")
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "realm-engine", "version": APP_VERSION}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}
    if method == "tools/call":
        params = req.get("params") if isinstance(req.get("params"), dict) else {}
        raw_args = params.get("arguments") if isinstance(params, dict) else {}
        tool_args: dict[str, object] = {str(k): v for k, v in raw_args.items()} if isinstance(raw_args, dict) else {}
        try:
            tool_name = str(params.get("name") or "") if isinstance(params, dict) else ""
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": _call_mcp_tool(tool_name, tool_args, root)}]}}
        except ValueError as exc:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"isError": True, "content": [{"type": "text", "text": str(exc)}]}}
        except OSError:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"isError": True, "content": [{"type": "text", "text": "Could not read workspace resource"}]}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
def run_mcp_stdio(root: Path) -> None:
    while raw_line := sys.stdin.readline(262_144):
        if not (line := raw_line.strip()) or len(raw_line) >= 262_144:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if isinstance(msg, dict) and (resp := handle_mcp_request(msg, root)) is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
