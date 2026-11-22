"""Live timer transitions, time/impact CRUD, and natural AI/offline Wirksamkeit drafting."""

import json
import re
from datetime import UTC, datetime

from core import impact_contracts as ic
from core.ai_stream import StreamMessagesFn, collect_stream_text
from core.contracts import TutorConfig
from core.json_store import validate_iso_date
from features.impact_ledger.store import new_id, today_iso, utc_now


def elapsed_timer_seconds(timer: ic.ActiveTimer, now: datetime | None = None) -> int:
    total = timer.accumulated_seconds
    if not timer.is_paused and timer.started_at:
        try:
            start = datetime.fromisoformat(timer.started_at)
            ref = now or datetime.now(UTC)
            total += max(0, int((ref - start).total_seconds()))
        except ValueError:
            pass
    return total


def start_timer(state: ic.ImpactLedgerState, label: str, project_id: str = "", task_id: str = "", category: str = "deep_work", hourly_rate: float = 0.0) -> tuple[ic.ImpactLedgerState, ic.ActiveTimer]:
    timer = ic.ActiveTimer(
        label=label.strip() or "Work Session", project_id=project_id.strip(), task_id=task_id.strip(),
        category=category.strip() or "deep_work", hourly_rate=max(0.0, float(hourly_rate)),
        started_at=utc_now(), accumulated_seconds=0, is_paused=False,
    )
    return state.model_copy(update={"active_timer": timer}), timer


def toggle_timer_pause(state: ic.ImpactLedgerState) -> tuple[ic.ImpactLedgerState, ic.ActiveTimer | None]:
    timer = state.active_timer
    if timer is None:
        return state, None
    if timer.is_paused:
        resumed = timer.model_copy(update={"is_paused": False, "started_at": utc_now()})
        return state.model_copy(update={"active_timer": resumed}), resumed
    acc = elapsed_timer_seconds(timer)
    paused = timer.model_copy(update={"is_paused": True, "accumulated_seconds": acc, "started_at": ""})
    return state.model_copy(update={"active_timer": paused}), paused


def stop_and_log_timer(state: ic.ImpactLedgerState, notes: str = "", min_minutes: float = 1.0) -> tuple[ic.ImpactLedgerState, ic.TimeEntry | None]:
    timer = state.active_timer
    if timer is None:
        return state, None
    mins = max(min_minutes, round(elapsed_timer_seconds(timer) / 60.0, 1))
    entry = ic.TimeEntry(
        id=new_id("tim"), label=timer.label, project_id=timer.project_id, task_id=timer.task_id,
        category=timer.category, date=today_iso(), duration_minutes=mins,
        hourly_rate=timer.hourly_rate or state.default_hourly_rate, billable=True,
        source="timer", notes=notes.strip(), created_at=utc_now(),
    )
    return state.model_copy(update={"active_timer": None, "time_entries": [entry, *state.time_entries]}), entry


def add_time_entry(state: ic.ImpactLedgerState, label: str, duration_minutes: float, date_str: str = "", project_id: str = "", task_id: str = "", category: str = "deep_work", hourly_rate: float = 0.0, source: ic.TimeSource = "manual", notes: str = "") -> tuple[ic.ImpactLedgerState, ic.TimeEntry]:
    safe_dt = validate_iso_date(date_str, allow_empty=True, field_name="date") or today_iso()
    entry = ic.TimeEntry(
        id=new_id("tim"), label=label.strip(), project_id=project_id.strip(), task_id=task_id.strip(),
        category=category.strip() or "deep_work", date=safe_dt,
        duration_minutes=round(float(duration_minutes), 1),
        hourly_rate=hourly_rate if hourly_rate > 0 else state.default_hourly_rate,
        billable=True, source=source, notes=notes.strip(), created_at=utc_now(),
    )
    return state.model_copy(update={"time_entries": [entry, *state.time_entries]}), entry


def remove_time_entry(state: ic.ImpactLedgerState, entry_id: str) -> tuple[ic.ImpactLedgerState, bool]:
    kept = [e for e in state.time_entries if e.id != entry_id]
    return (state.model_copy(update={"time_entries": kept}), True) if len(kept) != len(state.time_entries) else (state, False)


def add_impact_entry(state: ic.ImpactLedgerState, what_done: str, effect: str, date_str: str = "", project_id: str = "", evidence_notes: str = "", hours_invested: float = 0.0, direct_cost: float = 0.0, estimated_value: float = 0.0, time_saved_hours: float = 0.0, outcome_tag: ic.OutcomeTag = "quality", task_ids: list[str] | None = None) -> tuple[ic.ImpactLedgerState, ic.ImpactEntry]:
    safe_dt = validate_iso_date(date_str, allow_empty=True, field_name="date") or today_iso()
    entry = ic.ImpactEntry(
        id=new_id("imp"), date=safe_dt, project_id=project_id.strip(), task_ids=task_ids or [],
        what_done=what_done.strip(), effect=effect.strip(), evidence_notes=evidence_notes.strip(),
        hours_invested=max(0.0, float(hours_invested)), direct_cost=max(0.0, float(direct_cost)),
        estimated_value=max(0.0, float(estimated_value)), time_saved_hours=max(0.0, float(time_saved_hours)),
        outcome_tag=outcome_tag, created_at=utc_now(),
    )
    return state.model_copy(update={"impact_entries": [entry, *state.impact_entries]}), entry


def edit_impact_entry(state: ic.ImpactLedgerState, entry_id: str, updates: dict[str, object]) -> tuple[ic.ImpactLedgerState, ic.ImpactEntry | None]:
    clean = {k: (v.strip() if isinstance(v, str) else v) for k, v in updates.items() if v is not None}
    if "date" in clean:
        clean["date"] = validate_iso_date(str(clean["date"]), allow_empty=False, field_name="date")
    items, found = [], None
    for item in state.impact_entries:
        if item.id == entry_id:
            found = ic.ImpactEntry.model_validate({**item.model_dump(), **clean})
            items.append(found)
        else:
            items.append(item)
    return (state.model_copy(update={"impact_entries": items}), found) if found else (state, None)


def remove_impact_entry(state: ic.ImpactLedgerState, entry_id: str) -> tuple[ic.ImpactLedgerState, bool]:
    kept = [e for e in state.impact_entries if e.id != entry_id]
    return (state.model_copy(update={"impact_entries": kept}), True) if len(kept) != len(state.impact_entries) else (state, False)


async def draft_impact_entry(notes: str, hours: float, stream_messages: StreamMessagesFn | None, tutor_config: TutorConfig | None, *, language: str = "en") -> tuple[dict[str, object], str]:
    """Draft a clear, jargon-free Wirksamkeitsdokumentation entry (AI or deterministic offline)."""
    cleaned = notes.strip()[:5000]
    lines = [ln.strip(" -*•\t") for ln in cleaned.splitlines() if ln.strip()]
    fallback: dict[str, object] = {
        "what_done": (lines[0] if lines else "Completed focused project work")[:300],
        "effect": (" ; ".join(lines[1:3]) if len(lines) > 1 else "Advanced project milestones and improved clarity for stakeholders.")[:500],
        "evidence_notes": cleaned[:600],
        "hours_invested": round(max(0.0, hours), 2),
        "outcome_tag": "milestone",
    }
    if not cleaned or stream_messages is None or tutor_config is None:
        return fallback, "deterministic"
    lang_name = {"de": "German", "es": "Spanish"}.get(language, "English")
    sys_prompt = (
        f"You write concise, natural, jargon-free impact documentation (Wirksamkeitsdokumentation) in {lang_name}. "
        "Reply ONLY with JSON inside <impact_json>{...}</impact_json> containing keys: "
        'what_done (what was done), effect (tangible effect/outcome), evidence_notes (short supporting note), outcome_tag ("quality"|"time_saved"|"revenue"|"wellbeing"|"milestone").'
    )
    try:
        raw = await collect_stream_text(stream_messages, [{"role": "system", "content": sys_prompt}, {"role": "user", "content": cleaned}], tutor_config)
    except Exception:
        return fallback, "deterministic"
    m = re.search(r"<impact_json>\s*(\{.*?\})\s*</impact_json>", raw, re.DOTALL)
    try:
        parsed = json.loads(m.group(1) if m else raw[raw.find("{") : raw.rfind("}") + 1])
    except ValueError:
        return fallback, "deterministic"
    if not isinstance(parsed, dict) or not str(parsed.get("what_done") or "").strip():
        return fallback, "deterministic"
    tag = str(parsed.get("outcome_tag") or "quality")
    return {
        "what_done": str(parsed.get("what_done"))[:600],
        "effect": str(parsed.get("effect") or fallback["effect"])[:1000],
        "evidence_notes": str(parsed.get("evidence_notes") or fallback["evidence_notes"])[:1200],
        "hours_invested": round(max(0.0, hours), 2),
        "outcome_tag": tag if tag in {"quality", "time_saved", "revenue", "wellbeing", "milestone"} else "quality",
    }, "ai"
