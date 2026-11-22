"""Node execution handlers for all 8 native local workflow node kinds."""

import asyncio
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from core.agent_personas import list_agents
from core.contracts import TutorConfig, WorkspaceConfig
from core.runtime import data_root
from core.workflow_contracts import WorkflowNode

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]
VaultSearchFn = Callable[[str, int], str]
ExtractTasksFn = Callable[[str, str], int]
GenerateSlidesFn = Callable[[str, str, str], str]
SaveGuideFn = Callable[[str, str, str], str]
LogImpactFn = Callable[[str, str, str], str]
CloudGuardFn = Callable[[str, str, str], None]


def render_template(raw: str, user_input: str, prev_output: str) -> str:
    return raw.replace("{{input}}", user_input).replace("{{prev}}", prev_output)


def _agent_system_prompt(agent_id: str, root: Path | None) -> tuple[str, str]:
    agents = list_agents(root or data_root())
    found = next((a for a in agents if a.id == agent_id), None)
    if found is None and agents:
        found = agents[0]
    if found is None:
        return "Saga", "You are Saga, a precise local knowledge assistant."
    return found.name, f"You are {found.name} ({found.role}). {found.instructions}"


def _fallback_agent_text(agent_name: str, prompt: str, prev_output: str) -> str:
    base = (prev_output or prompt).strip()
    lines = [ln.strip() for ln in base.splitlines() if ln.strip()][:8]
    summary = "\n".join(f"- {ln[:180]}" for ln in lines) or "- Ready for review."
    return f"## {agent_name} Summary (Offline Draft)\n\n{summary}"


async def _run_agent_node(
    node: WorkflowNode,
    user_input: str,
    prev_output: str,
    cfg: WorkspaceConfig,
    tutor_cfg: TutorConfig,
    api_key: str | None,
    cancel_ev: asyncio.Event,
    stream_messages: StreamMessagesFn | None,
    cloud_guard: CloudGuardFn | None,
    root: Path | None,
) -> tuple[str, str]:
    if cfg.strict_local_only and tutor_cfg.provider != "ollama":
        raise ValueError(f"Local-Only Privacy Lock blocks cloud provider '{tutor_cfg.provider}'.")
    agent_id = str(node.config.get("agent_id") or "saga")
    agent_name, sys_prompt = _agent_system_prompt(agent_id, root)
    tmpl = str(node.config.get("prompt") or "Summarize and highlight key next steps:\n\n{{prev}}")
    user_msg = render_template(tmpl, user_input, prev_output or user_input).strip()
    if cloud_guard is not None:
        cloud_guard(tutor_cfg.provider, tutor_cfg.model, sys_prompt + "\n" + user_msg)
    if stream_messages is None:
        return _fallback_agent_text(agent_name, user_msg, prev_output), f"Agent: {agent_name} (offline)"
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
    chunks: list[str] = []
    try:
        async for ev in stream_messages(messages, tutor_cfg, api_key=api_key, local_only=cfg.strict_local_only):
            if cancel_ev.is_set():
                raise asyncio.CancelledError("Workflow cancelled")
            if ev.get("event") == "token" and isinstance(ev.get("text"), str):
                chunks.append(str(ev["text"]))
    except asyncio.CancelledError:
        raise
    except Exception:
        if not chunks:
            return _fallback_agent_text(agent_name, user_msg, prev_output), f"Agent: {agent_name} (offline fallback)"
    text = "".join(chunks).strip() or _fallback_agent_text(agent_name, user_msg, prev_output)
    return text, f"Agent: {agent_name} ({tutor_cfg.model})"


def evaluate_condition(node: WorkflowNode, text: str) -> bool:
    needle = str(node.config.get("contains") or "").strip().lower()
    mode = str(node.config.get("mode") or "contains").strip().lower()
    hay = text.lower()
    if mode == "not_empty":
        return bool(hay.strip())
    if mode == "not_contains":
        return bool(needle) and needle not in hay
    return bool(needle) and needle in hay


async def execute_node(
    node: WorkflowNode,
    user_input: str,
    prev_output: str,
    cfg: WorkspaceConfig,
    tutor_cfg: TutorConfig,
    api_key: str | None,
    cancel_ev: asyncio.Event,
    callbacks: dict[str, object],
    root: Path | None,
) -> tuple[str, str, bool | None]:
    """Execute one node, returning (output_text, artifact_note, condition_result)."""
    kind = node.kind
    if kind == "trigger":
        seed = user_input.strip() or str(node.config.get("default_input") or "Workspace overview")
        return seed, f"Trigger: {node.config.get('trigger_kind', 'manual')}", None
    if kind == "vault_search":
        q = render_template(str(node.config.get("query") or "{{input}}"), user_input, prev_output).strip() or "overview"
        top_k = max(1, min(12, int(node.config.get("top_k") or 5)))
        fn = callbacks.get("vault_search")
        text = fn(q, top_k) if callable(fn) else f"Search query: {q}"
        return str(text), f"Vault search ({top_k} passages)", None
    if kind == "run_agent":
        sm = callbacks.get("stream_messages")
        cg = callbacks.get("cloud_guard")
        out, note = await _run_agent_node(
            node, user_input, prev_output, cfg, tutor_cfg, api_key, cancel_ev,
            sm if callable(sm) else None, cg if callable(cg) else None, root,  # type: ignore[arg-type]
        )
        return out, note, None
    if kind == "condition":
        passed = evaluate_condition(node, prev_output or user_input)
        return prev_output or user_input, f"Condition -> {'TRUE' if passed else 'FALSE'}", passed
    if kind == "extract_tasks":
        fn = callbacks.get("extract_tasks")
        pid = str(node.config.get("project_id") or "")
        count = int(fn(prev_output or user_input, pid)) if callable(fn) else 0  # type: ignore[arg-type]
        return prev_output or user_input, f"Added {count} task(s) to Kanban Board", None
    if kind == "generate_slides":
        fn = callbacks.get("generate_slides")
        title = render_template(str(node.config.get("title") or "Workflow Presentation"), user_input, prev_output).strip()[:120]
        fmt = "pdf" if str(node.config.get("output_format") or "pptx").lower() == "pdf" else "pptx"
        saved = str(fn(title, prev_output or user_input, fmt)) if callable(fn) else f"slides.{fmt}"
        return prev_output or user_input, f"Saved deck: {saved}", None
    if kind == "save_guide":
        fn = callbacks.get("save_guide")
        title = render_template(str(node.config.get("title") or "Workflow Output"), user_input, prev_output).strip()[:120]
        sub = str(node.config.get("subfolder") or "workflows").strip()
        saved = str(fn(title, prev_output or user_input, sub)) if callable(fn) else f"{title}.md"
        return prev_output or user_input, f"Saved guide: {saved}", None
    fn = callbacks.get("log_impact")
    tag = str(node.config.get("outcome_tag") or "milestone")
    what = render_template(str(node.config.get("what_done") or "{{input}}"), user_input, prev_output).strip() or node.label
    saved = str(fn(what[:400], (prev_output or user_input)[:1200], tag)) if callable(fn) else "logged"
    return prev_output or user_input, f"Impact entry: {saved}", None
