"""Atomic, process-wide cloud reservations; estimates are not provider billing totals."""

import json
import math
import os
import time
from datetime import UTC, datetime
from threading import RLock

from core.runtime import data_root

BUDGET_FILE = data_root() / "budget_state.json"
LOCK = RLock()
MAX_REQUESTS_PER_MINUTE = 12
MAX_OUTPUT_TOKENS = 1024
ESTIMATE_USD_PER_MILLION_TOKENS = 10.0


def estimate_usage(text: str, output_tokens: int = MAX_OUTPUT_TOKENS, kind: str = "chat") -> tuple[int, float]:
    """Reserve UTF-8 bytes as a conservative token count, plus framing and bounded output."""
    tokens = len(text.encode("utf-8")) + (1024 if output_tokens else 0) + output_tokens
    if kind.endswith("_speech"):
        return tokens, round(len(text) * (0.000015 if kind == "openai_speech" else 0.0003), 8)
    return tokens, round(tokens * ESTIMATE_USD_PER_MILLION_TOKENS / 1_000_000, 8)


def _load(now: float) -> dict[str, object]:
    date = datetime.fromtimestamp(now, UTC).date().isoformat()
    state: dict[str, object] = {"date_str": date, "cloud_requests_today": 0, "estimated_tokens_today": 0, "estimated_cost_usd": 0.0, "minute_timestamps": []}
    if BUDGET_FILE.is_symlink() or BUDGET_FILE.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Budget storage cannot be a symbolic link")
    if BUDGET_FILE.exists():
        if BUDGET_FILE.stat().st_size > 16384:
            raise ValueError("Invalid budget state")
        raw = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("date_str"), str):
            raise ValueError("Invalid budget state")
        datetime.fromisoformat(raw["date_str"])
        for key in ("cloud_requests_today", "estimated_tokens_today"):
            if type(raw.get(key)) is not int or raw[key] < 0:
                raise ValueError("Invalid budget counter")
        cost = raw.get("estimated_cost_usd")
        timestamps = raw.get("minute_timestamps")
        if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0 or not isinstance(timestamps, list) or len(timestamps) > 12:
            raise ValueError("Invalid budget state")
        if any(type(t) not in (int, float) or not math.isfinite(t) for t in timestamps):
            raise ValueError("Invalid rate-limit state")
        if raw["date_str"] == date:
            state.update({key: raw[key] for key in state if key != "date_str"})
        state["minute_timestamps"] = [t for t in timestamps if t > now - 60]
    return state


def _save(state: dict[str, object]) -> None:
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = BUDGET_FILE.with_suffix(".json.tmp")
    if BUDGET_FILE.is_symlink() or temporary.is_symlink():
        raise ValueError("Budget storage cannot be a symbolic link")
    with temporary.open("w", encoding="utf-8") as handle:
        os.chmod(temporary, 0o600)
        json.dump(state, handle)
    temporary.replace(BUDGET_FILE)


def budget_snapshot(request_limit: int = 50, usd_limit: float = 1.0, now: float | None = None) -> dict[str, object]:
    with LOCK:
        try:
            state = _load(time.time() if now is None else now)
            timestamps = state.pop("minute_timestamps")
            state["requests_last_minute"] = len(timestamps) if isinstance(timestamps, list) else 0
            return {**state, "daily_cloud_request_limit": request_limit, "daily_budget_usd_limit": usd_limit, "max_requests_per_minute": 12, "state_error": None, "estimate_usd_per_million_tokens": ESTIMATE_USD_PER_MILLION_TOKENS}
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return {"state_error": "Cloud budget state is unavailable. Reset the counter or use Local Ollama.", "daily_cloud_request_limit": request_limit, "daily_budget_usd_limit": usd_limit, "detail": type(exc).__name__}


def check_and_record_budget(provider: str, estimated_tokens: int = MAX_OUTPUT_TOKENS, request_limit: int = 50, usd_limit: float = 1.0, estimated_cost_usd: float | None = None, now: float | None = None) -> str | None:
    if provider == "ollama":
        return None
    cost = estimated_tokens * ESTIMATE_USD_PER_MILLION_TOKENS / 1_000_000 if estimated_cost_usd is None else estimated_cost_usd
    with LOCK:
        try:
            if estimated_tokens < 0 or not math.isfinite(cost) or cost < 0:
                raise ValueError("Invalid reservation")
            state = _load(time.time() if now is None else now)
            raw_timestamps = state["minute_timestamps"]
            timestamps = raw_timestamps if isinstance(raw_timestamps, list) else []
            used, spent = int(str(state["cloud_requests_today"])), float(str(state["estimated_cost_usd"]))
            reason = "12 requests/minute rate limit reached" if len(timestamps) >= MAX_REQUESTS_PER_MINUTE else "Daily limit reached" if used >= request_limit or spent + cost > usd_limit else ""
            if reason:
                guidance = "Wait up to 60 seconds or switch to Local Ollama." if len(timestamps) >= MAX_REQUESTS_PER_MINUTE else "Increase your limit in Settings or switch to Local Ollama."
                return f"Cloud Budget Guardrail triggered: {reason} (${spent:.2f} / {used} requests; next estimate ${cost:.4f}). {guidance}"
            state.update(cloud_requests_today=used + 1, estimated_tokens_today=int(str(state["estimated_tokens_today"])) + estimated_tokens, estimated_cost_usd=round(spent + cost, 8), minute_timestamps=[*timestamps, time.time() if now is None else now])
            _save(state)
        except (OSError, ValueError, TypeError, KeyError):
            return "Cloud Budget Guardrail triggered: Usage state is unavailable. Reset the counter in Settings or switch to Local Ollama."
    return None


def reset_budget(now: float | None = None) -> None:
    with LOCK:
        timestamp = time.time() if now is None else now
        try:
            recent = _load(timestamp)["minute_timestamps"]
        except (ValueError, TypeError, KeyError):
            recent = []
        if BUDGET_FILE.is_symlink():
            raise ValueError("Budget storage cannot be a symbolic link")
        _save({"date_str": datetime.fromtimestamp(timestamp, UTC).date().isoformat(), "cloud_requests_today": 0, "estimated_tokens_today": 0, "estimated_cost_usd": 0.0, "minute_timestamps": recent})
