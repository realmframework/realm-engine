"""File-first persona.md repository under <data_root>/agents/<id>/persona.md."""

import json
from pathlib import Path

from core import persona_codec
from core.agent_presets import BUILTIN_AGENT_MAP, BUILTIN_AGENTS, AgentPersona
from core.db import atomic_write_text


def agents_root(root: Path) -> Path:
    return root / "agents"


def _load_removed(root: Path) -> set[str]:
    path = agents_root(root) / ".removed.json"
    if not path.is_file() or path.is_symlink():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(x) for x in data} if isinstance(data, list) else set()
    except (OSError, ValueError):
        return set()


def _save_removed(root: Path, removed: set[str]) -> None:
    folder = agents_root(root)
    if folder.is_symlink():
        raise ValueError("Agents directory cannot be a symbolic link")
    folder.mkdir(parents=True, exist_ok=True)
    atomic_write_text(folder / ".removed.json", json.dumps(sorted(removed), indent=2))


def _write_persona(root: Path, agent: AgentPersona) -> Path:
    base = agents_root(root)
    if base.is_symlink():
        raise ValueError("Agents directory cannot be a symbolic link")
    folder = base / agent.id
    if folder.is_symlink():
        raise ValueError("Agent persona path cannot be a symbolic link")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "persona.md"
    atomic_write_text(target, persona_codec.render_persona_md(agent))
    return target


def seed_default_agents(root: Path) -> Path:
    folder = agents_root(root)
    folder.mkdir(parents=True, exist_ok=True)
    removed = _load_removed(root)
    for agent in BUILTIN_AGENTS:
        if agent.id not in removed and not (folder / agent.id / "persona.md").exists():
            _write_persona(root, agent)
    return folder


def list_agents(root: Path, saga_name_override: str = "") -> list[AgentPersona]:
    folder, loaded = seed_default_agents(root), {}
    for entry in sorted(folder.iterdir()):
        pfile = entry / "persona.md"
        if not entry.is_dir() or entry.is_symlink() or entry.name.startswith(".") or not pfile.is_file() or pfile.is_symlink():
            continue
        try:
            parsed = persona_codec.parse_persona_md(pfile.read_text(encoding="utf-8"), entry.name, str(pfile))
        except OSError:
            parsed = None
        if parsed is not None:
            loaded[parsed.id] = parsed
    override = saga_name_override.strip()[:40]
    if "saga" in loaded and override and not loaded["saga"].customized and override != "Saga":
        loaded["saga"] = loaded["saga"].model_copy(update={"name": override})
    ordered = [loaded[a.id] for a in BUILTIN_AGENTS if a.id in loaded]
    extras = sorted((a for aid, a in loaded.items() if aid not in BUILTIN_AGENT_MAP), key=lambda a: a.name.lower())
    return ordered + extras


def get_agent(root: Path, agent_id: str | None, saga_name_override: str = "") -> AgentPersona:
    agents = list_agents(root, saga_name_override=saga_name_override)
    wanted = persona_codec.slugify_agent(agent_id or "")
    return next((a for a in agents if a.id == wanted), agents[0] if agents else BUILTIN_AGENTS[0])


def save_agent(root: Path, *, name: str = "", role: str = "Specialist", tagline: str = "", palette: str = "realm", default_format: str = "", model_provider: str = "", model_name: str = "", temperature: float = 0.2, instructions: str = "", agent_id: str = "", raw_markdown: str = "") -> AgentPersona:
    seed_default_agents(root)
    if raw_markdown.strip():
        parsed = persona_codec.parse_persona_md(raw_markdown, persona_codec.slugify_agent(agent_id or name))
        if parsed is None:
            raise ValueError("Provide a valid agent id or name inside persona.md frontmatter")
        persona = parsed
    else:
        clean_name = name.strip()[:40]
        aid = persona_codec.slugify_agent(agent_id or clean_name)
        if not clean_name or not aid:
            raise ValueError("Provide an agent name with letters or numbers")
        prov = persona_codec.slugify_agent(model_provider or "")
        prov = prov if prov in {"ollama", "openai", "kimi", "deepseek", "gemini", "xai", "mistral", "anthropic"} else ""
        persona = AgentPersona(
            id=aid, name=clean_name, role=(role.strip() or "Specialist")[:64], tagline=tagline.strip()[:160],
            palette=persona_codec.slugify_agent(palette or "realm") or "realm", default_format=persona_codec.slugify_agent(default_format or ""),
            model_provider=prov, model_name=model_name.strip()[:120] if prov else "",
            temperature=max(0.0, min(1.0, float(temperature))), instructions=instructions.strip()[:3000],
            builtin=aid in BUILTIN_AGENT_MAP,
        )
    target = _write_persona(root, persona)
    removed = _load_removed(root)
    if persona.id in removed:
        removed.discard(persona.id)
        _save_removed(root, removed)
    return persona_codec.parse_persona_md(target.read_text(encoding="utf-8"), persona.id, str(target)) or persona


def delete_agent(root: Path, agent_id: str) -> bool:
    aid = persona_codec.slugify_agent(agent_id)
    if not aid:
        return False
    if len(list_agents(root)) <= 1:
        raise ValueError("Keep at least one active agent in your team.")
    base = agents_root(root)
    folder, pfile = base / aid, base / aid / "persona.md"
    if base.is_symlink() or folder.is_symlink() or pfile.is_symlink() or not pfile.is_file():
        return False
    pfile.unlink()
    if folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
    if aid in BUILTIN_AGENT_MAP:
        _save_removed(root, _load_removed(root) | {aid})
    return True


def reset_agent(root: Path, agent_id: str) -> AgentPersona:
    aid = persona_codec.slugify_agent(agent_id)
    builtin = BUILTIN_AGENT_MAP.get(aid)
    if builtin is None:
        raise ValueError("Only built-in agents can be reset to default")
    _save_removed(root, _load_removed(root) - {aid})
    return builtin.model_copy(update={"file_path": str(_write_persona(root, builtin)), "customized": False})


def restore_default_team(root: Path) -> list[AgentPersona]:
    _save_removed(root, set())
    for agent in BUILTIN_AGENTS:
        if not (agents_root(root) / agent.id / "persona.md").exists():
            _write_persona(root, agent)
    return list_agents(root)


def active_persona_prompt(root: Path, agent_id: str | None, saga_name_override: str = "") -> tuple[AgentPersona, str]:
    agent = get_agent(root, agent_id, saga_name_override=saga_name_override)
    return agent, persona_codec.build_persona_prompt(agent)
