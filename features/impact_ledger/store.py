"""Atomic local storage, zero-division-safe ROI math, and CSV export for Impact Ledger."""

import csv
import io
from datetime import date, timedelta
from pathlib import Path

from core.impact_contracts import ImpactLedgerState
from core.json_store import (
    area_store_path,
    load_model_json,
    new_id,
    save_model_json,
    store_lock,
    today_iso,
    utc_now,
)

__all__ = [
    "compute_roi_summary", "export_timesheet_csv", "ledger_path", "load_ledger",
    "new_id", "save_ledger", "store_lock", "today_iso", "utc_now",
]


def ledger_path(area: str, root: Path | None = None) -> Path:
    return area_store_path(area, "impact_ledger.json", root)


def load_ledger(path: Path) -> ImpactLedgerState:
    return load_model_json(path, ImpactLedgerState, ImpactLedgerState)


def save_ledger(state: ImpactLedgerState, path: Path) -> ImpactLedgerState:
    return save_model_json(state, path, ImpactLedgerState)


def compute_roi_summary(state: ImpactLedgerState, today: str | None = None) -> dict[str, object]:
    """Compute zero-division-safe ROI metrics, weekly rollup, and per-project attribution."""
    ref = date.fromisoformat(today) if today else date.today()
    week_start = (ref - timedelta(days=ref.weekday())).isoformat()
    month_prefix = ref.strftime("%Y-%m")
    rate_def = state.default_hourly_rate

    total_hours, week_hours, month_hours, time_cost = 0.0, 0.0, 0.0, 0.0
    by_project: dict[str, dict[str, float]] = {}

    def _bucket(pid: str) -> dict[str, float]:
        key = pid or "_general"
        if key not in by_project:
            by_project[key] = {"hours": 0.0, "cost": 0.0, "value": 0.0, "saved_hours": 0.0, "entries": 0.0}
        return by_project[key]

    for te in state.time_entries:
        hrs = round(te.duration_minutes / 60.0, 4)
        eff_rate = te.hourly_rate if te.hourly_rate > 0 else rate_def
        cost = hrs * eff_rate
        total_hours += hrs
        time_cost += cost
        if te.date >= week_start:
            week_hours += hrs
        if te.date.startswith(month_prefix):
            month_hours += hrs
        b = _bucket(te.project_id)
        b["hours"] += hrs
        b["cost"] += cost

    direct_cost, est_value, saved_hours, extra_impact_hours = 0.0, 0.0, 0.0, 0.0
    for imp in state.impact_entries:
        saved_val = imp.time_saved_hours * rate_def
        val = imp.estimated_value + saved_val
        imp_cost = imp.direct_cost + (imp.hours_invested * rate_def if total_hours == 0 else 0.0)
        direct_cost += imp.direct_cost
        extra_impact_hours += imp.hours_invested
        est_value += val
        saved_hours += imp.time_saved_hours
        b = _bucket(imp.project_id)
        b["cost"] += imp_cost
        b["value"] += val
        b["saved_hours"] += imp.time_saved_hours
        b["entries"] += 1.0

    logged_or_impact_hours = total_hours if total_hours > 0 else extra_impact_hours
    total_cost = round(time_cost + direct_cost + (extra_impact_hours * rate_def if total_hours == 0 else 0.0), 2)
    total_value = round(est_value, 2)
    net_impact = round(total_value - total_cost, 2)
    roi_pct = round(((total_value - total_cost) / total_cost) * 100.0, 1) if total_cost > 0 else None

    projects_out = []
    for pid, b in sorted(by_project.items(), key=lambda kv: (-kv[1]["value"], -kv[1]["hours"])):
        p_cost, p_val = round(b["cost"], 2), round(b["value"], 2)
        p_roi = round(((p_val - p_cost) / p_cost) * 100.0, 1) if p_cost > 0 else None
        projects_out.append({
            "project_id": "" if pid == "_general" else pid,
            "hours": round(b["hours"], 2),
            "cost": p_cost,
            "value": p_val,
            "net": round(p_val - p_cost, 2),
            "roi_pct": p_roi,
            "saved_hours": round(b["saved_hours"], 2),
            "impact_count": int(b["entries"]),
        })

    return {
        "currency": state.currency, "default_hourly_rate": state.default_hourly_rate,
        "total_hours": round(logged_or_impact_hours, 2), "week_hours": round(week_hours, 2), "month_hours": round(month_hours, 2),
        "total_cost": total_cost, "total_value": total_value, "time_saved_hours": round(saved_hours, 2),
        "net_impact": net_impact, "roi_pct": roi_pct, "impact_count": len(state.impact_entries),
        "time_count": len(state.time_entries), "by_project": projects_out,
    }


def _safe_csv_cell(val: object) -> str:
    txt = str(val)
    return "'" + txt if txt[:1] in ("=", "+", "-", "@", "\t", "\r") else txt


def export_timesheet_csv(state: ImpactLedgerState) -> str:
    """Export all logged work time entries as Excel-safe UTF-8 CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Label", "Category", "Project ID", "Duration (min)", "Duration (h)", "Rate", "Currency", "Source", "Notes"])
    for te in sorted(state.time_entries, key=lambda x: (x.date, x.created_at), reverse=True):
        rate = te.hourly_rate if te.hourly_rate > 0 else state.default_hourly_rate
        writer.writerow([
            te.date, _safe_csv_cell(te.label), _safe_csv_cell(te.category), _safe_csv_cell(te.project_id),
            f"{te.duration_minutes:.1f}", f"{te.duration_minutes / 60.0:.2f}", f"{rate:.2f}", state.currency, te.source, _safe_csv_cell(te.notes),
        ])
    return buf.getvalue()
