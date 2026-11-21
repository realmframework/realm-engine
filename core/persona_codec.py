"""Pure Markdown/YAML frontmatter codec and prompt builder for agent persona.md files."""

import re

from core.agent_presets import BUILTIN_AGENT_MAP, AgentPersona

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def slugify_agent(name: str) -> str:
    return _SLUG_RE.sub("_", name.strip().lower()).strip("_")[:48]


def _one_line(value: str) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def render_persona_md(agent: AgentPersona) -> str:
    """Serialize an AgentPersona into human-editable persona.md with YAML frontmatter."""
    lines = [
        "---",
        f"id: {_one_line(agent.id)}",
        f"name: {_one_line(agent.name)}",
        f"role: {_one_line(agent.role)}",
        f"tagline: {_one_line(agent.tagline)}",
        f"palette: {_one_line(agent.palette or 'realm')}",
        f"default_format: {_one_line(agent.default_format)}",
        f"model_provider: {_one_line(agent.model_provider)}",
        f"model_name: {_one_line(agent.model_name)}",
        f"temperature: {round(float(agent.temperature), 2)}",
        "---",
        "",
        agent.instructions.strip(),
        "",
    ]
    return "\n".join(lines)


def parse_persona_md(raw: str, fallback_id: str, file_path: str = "") -> AgentPersona | None:
    """Parse a persona.md file safely without external YAML dependencies."""
    text = raw.replace("\r\n", "\n").strip()
    meta: dict[str, str] = {}
    body = text
    match = _FRONTMATTER_RE.match(text)
    if match:
        header, body = match.group(1), match.group(2).strip()
        for line in header.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    aid = slugify_agent(meta.get("id") or fallback_id)
    if not aid:
        return None
    name = (meta.get("name") or aid.title()).strip()[:40]
    role = (meta.get("role") or "Specialist").strip()[:64]
    tagline = (meta.get("tagline") or "").strip()[:160]
    palette = slugify_agent(meta.get("palette") or "realm") or "realm"
    default_format = slugify_agent(meta.get("default_format") or "")
    raw_prov = slugify_agent(meta.get("model_provider") or "")
    valid_provs = {"ollama", "openai", "kimi", "deepseek", "gemini", "xai", "mistral", "anthropic"}
    model_provider = raw_prov if raw_prov in valid_provs else ""
    model_name = _one_line(meta.get("model_name") or "")[:120] if model_provider else ""
    try:
        temp = max(0.0, min(1.0, float(meta.get("temperature") or "0.2")))
    except ValueError:
        temp = 0.2
    ref = BUILTIN_AGENT_MAP.get(aid)
    customized = bool(
        ref
        and (
            name != ref.name or role != ref.role or tagline != ref.tagline
            or palette != ref.palette or default_format != ref.default_format
            or model_provider != ref.model_provider or model_name != ref.model_name
            or abs(temp - ref.temperature) > 0.01 or body.strip() != ref.instructions.strip()
        )
    )
    return AgentPersona(
        id=aid, name=name or "Agent", role=role, tagline=tagline, palette=palette,
        default_format=default_format, model_provider=model_provider, model_name=model_name,
        temperature=temp, instructions=body[:3000],
        builtin=ref is not None, customized=customized, file_path=file_path,
    )


def build_persona_prompt(agent: AgentPersona | None) -> str:
    """Build a crisp analytical lens block injected below REALM grounding & safety rules."""
    if agent is None:
        return ""
    body = agent.instructions.strip()
    if not body and not agent.role:
        return ""
    header = f"[ACTIVE AGENT PERSONA: {agent.name} — {agent.role}]"
    guard = "Apply this analytical lens and communication style without breaking factual grounding, citations, or untrusted-document safety rules. Stay professional — never break into fictional cosplay."
    return f"{header}\n{guard}\n\n{body}".strip()
