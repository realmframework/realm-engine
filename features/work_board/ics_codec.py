"""Pure-Python RFC 5545 iCalendar (.ics) exporter and importer with zero external dependencies."""

import re
from datetime import UTC, date, datetime, timedelta

from core.work_contracts import CalendarEvent, WorkBoardState
from features.work_board.store import done_column_ids, new_id


def _ics_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def _ics_unescape(value: str) -> str:
    return value.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def _fold_line(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    out, current = [], ""
    for ch in line:
        cand = current + ch
        if len(cand.encode("utf-8")) > (75 if not out else 74):
            out.append(current)
            current = " " + ch
        else:
            current = cand
    if current:
        out.append(current)
    return "\r\n".join(out)


def _date_compact(iso_date: str) -> str:
    return iso_date.replace("-", "")


def _next_day_compact(iso_date: str) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=1)).strftime("%Y%m%d")


def _event_lines(uid: str, summary: str, date_iso: str, start_t: str, end_t: str, description: str, stamp: str, category: str) -> list[str]:
    lines = ["BEGIN:VEVENT", f"UID:{_ics_escape(uid)}", f"DTSTAMP:{stamp}", f"SUMMARY:{_ics_escape(summary)}"]
    if start_t:
        start_hhmm = start_t.replace(":", "") + "00"
        end_hhmm = (end_t.replace(":", "") + "00") if end_t else start_hhmm
        lines.append(f"DTSTART:{_date_compact(date_iso)}T{start_hhmm}")
        lines.append(f"DTEND:{_date_compact(date_iso)}T{end_hhmm}")
    else:
        lines.append(f"DTSTART;VALUE=DATE:{_date_compact(date_iso)}")
        lines.append(f"DTEND;VALUE=DATE:{_next_day_compact(date_iso)}")
    if description:
        lines.append(f"DESCRIPTION:{_ics_escape(description)}")
    if category:
        lines.append(f"CATEGORIES:{_ics_escape(category.upper())}")
    lines.append("END:VEVENT")
    return lines


def export_ics(state: WorkBoardState, calendar_name: str = "REALM Engine") -> str:
    """Serialize calendar events and open tasks with due dates to a valid RFC 5545 .ics string."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//REALM Engine//Solo Work OS//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_ics_escape(calendar_name)}",
    ]
    for ev in state.events:
        uid = ev.uid or f"{ev.id}@realm-engine.local"
        lines.extend(_event_lines(uid, ev.title, ev.date, ev.start_time, ev.end_time, ev.notes, stamp, ev.kind))
    done_cols = done_column_ids(state)
    for task in state.tasks:
        if not task.due_date or task.column_id in done_cols:
            continue
        uid = f"task-{task.id}@realm-engine.local"
        summary = f"[Task] {task.title}"
        lines.extend(_event_lines(uid, summary, task.due_date, task.scheduled_start, task.scheduled_end, task.description, stamp, "deadline"))
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold_line(line) for line in lines) + "\r\n"


def _unfold_ics(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    unfolded: list[str] = []
    for line in normalized.split("\n"):
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        elif line.strip():
            unfolded.append(line)
    return unfolded


def _parse_dt(raw_val: str) -> tuple[str, str]:
    val = raw_val.strip()
    m_dt = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})", val)
    if m_dt:
        y, mo, d, hh, mm = m_dt.groups()
        return f"{y}-{mo}-{d}", f"{hh}:{mm}"
    m_d = re.match(r"^(\d{4})(\d{2})(\d{2})$", val)
    if m_d:
        y, mo, d = m_d.groups()
        return f"{y}-{mo}-{d}", ""
    return "", ""


def import_ics(raw_text: str, existing_uids: set[str] | None = None) -> list[CalendarEvent]:
    """Parse VEVENT items from an RFC 5545 .ics file, skipping duplicate UIDs."""
    seen = set(existing_uids or set())
    events: list[CalendarEvent] = []
    block: dict[str, str] | None = None
    for line in _unfold_ics(raw_text):
        upper = line.upper()
        if upper == "BEGIN:VEVENT":
            block = {}
            continue
        if upper == "END:VEVENT" and block is not None:
            dt_date, start_t = _parse_dt(block.get("DTSTART", ""))
            _, end_t = _parse_dt(block.get("DTEND", ""))
            title = _ics_unescape(block.get("SUMMARY", "")).strip()[:200]
            uid = _ics_unescape(block.get("UID", "")).strip()[:180]
            if dt_date and title and (not uid or uid not in seen):
                if uid:
                    seen.add(uid)
                cat = block.get("CATEGORIES", "").upper()
                kind = "focus" if "FOCUS" in cat else ("milestone" if "MILESTONE" in cat else ("deadline" if "DEADLINE" in cat else "event"))
                events.append(CalendarEvent(id=new_id("evt"), title=title, notes=_ics_unescape(block.get("DESCRIPTION", "")).strip()[:2000], kind=kind, date=dt_date, start_time=start_t, end_time=end_t if start_t else "", uid=uid or f"{new_id('ics')}@import.local"))
            block = None
            continue
        if block is not None and ":" in line:
            key_part, val_part = line.split(":", 1)
            prop_name = key_part.split(";", 1)[0].strip().upper()
            if prop_name in {"SUMMARY", "DESCRIPTION", "DTSTART", "DTEND", "UID", "CATEGORIES"}:
                block[prop_name] = val_part
    return events
