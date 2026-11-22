"""Atomic, process-wide cloud reservations; estimates are not provider billing totals."""

import json
import math
import time
from datetime import UTC, datetime
from threading import RLock

from core.db import atomic_write_text
from core.runtime import data_root

BUDGET_FILE = data_root() / "budget_state.json"
LOCK = RLock()
MAX_REQUESTS_PER_MINUTE = 12
MAX_OUTPUT_TOKENS = 1024
ESTIMATE_USD_PER_MILLION_TOKENS = 10.0
PROVIDER_TOKEN_RATES: dict[str, tuple[float, float]] = {
    "kimi": (0.60, 2.50),
    "deepseek": (0.30, 1.10),
    "gemini": (0.30, 2.50),
    "mistral": (0.40, 2.00),
    "openai": (1.50, 6.00),
    "xai": (2.00, 10.00),
    "anthropic": (3.00, 15.00),
}
DEFAULT_TOKEN_RATE = (1.50, 6.00)


def estimate_tokens_cost(input_tokens: int, output_tokens: int, provider: str = "") -> float:
    """Estimate USD spend from input/output token counts using realistic provider rates."""
    in_rate, out_rate = PROVIDER_TOKEN_RATES.get(provider.lower(), DEFAULT_TOKEN_RATE)
    return round((max(0, input_tokens) * in_rate + max(0, output_tokens) * out_rate) / 1_000_000, 8)


def estimate_usage(text: str, output_tokens: int = MAX_OUTPUT_TOKENS, kind: str = "chat", provider: str = "") -> tuple[int, float]:
    """Estimate realistic input + bounded output tokens and provider-aware USD reservation."""
    in_tokens = max(1, (len(text.encode("utf-8")) + 3) // 4)
    if kind.endswith("_speech"):
        return in_tokens, round(len(text) * (0.000015 if kind == "openai_speech" else 0.0003), 8)
    reserved_out = min(max(0, output_tokens), 512)
    return in_tokens + reserved_out, estimate_tokens_cost(in_tokens, reserved_out, provider)


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
        if not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0 or not isinstance(timestamps, list) or len(timestamps) > max(MAX_REQUESTS_PER_MINUTE, 60):
            raise ValueError("Invalid budget state")
        if any(type(t) not in (int, float) or not math.isfinite(t) for t in timestamps):
            raise ValueError("Invalid rate-limit state")
        if raw["date_str"] == date:
            state.update({key: raw[key] for key in state if key != "date_str"})
        state["minute_timestamps"] = [t for t in timestamps if t > now - 60]
    return state


def _save(state: dict[str, object]) -> None:
    if BUDGET_FILE.is_symlink() or BUDGET_FILE.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Budget storage cannot be a symbolic link")
    atomic_write_text(BUDGET_FILE, json.dumps(state), mode=0o600)


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
    if provider in {"ollama", "builtin"}:
        return None
    cost = estimated_tokens * ESTIMATE_USD_PER_MILLION_TOKENS / 1_000_000 if estimated_cost_usd is None else estimated_cost_usd
    with LOCK:
        try:
            if estimated_tokens < 0 or not math.isfinite(cost) or cost < 0:
                raise ValueError("Invalid reservation")
            ts = time.time() if now is None else now
            state = _load(ts)
            raw_timestamps = state["minute_timestamps"]
            timestamps = raw_timestamps if isinstance(raw_timestamps, list) else []
            used, spent = int(str(state["cloud_requests_today"])), float(str(state["estimated_cost_usd"]))
            reason = "12 requests/minute rate limit reached" if len(timestamps) >= MAX_REQUESTS_PER_MINUTE else "Daily limit reached" if used >= request_limit or spent + cost > usd_limit else ""
            if reason:
                guidance = "Wait up to 60 seconds or switch to Local Ollama." if len(timestamps) >= MAX_REQUESTS_PER_MINUTE else "Increase your limit in Settings or switch to Local Ollama."
                return f"Cloud Budget Guardrail triggered: {reason} (${spent:.2f} / {used} requests; next estimate ${cost:.4f}). {guidance}"
            state.update(cloud_requests_today=used + 1, estimated_tokens_today=int(str(state["estimated_tokens_today"])) + estimated_tokens, estimated_cost_usd=round(spent + cost, 8), minute_timestamps=[*timestamps, ts])
            _save(state)
        except (OSError, ValueError, TypeError, KeyError):
            return "Cloud Budget Guardrail triggered: Usage state is unavailable. Reset the counter in Settings or switch to Local Ollama."
    return None


def reconcile_budget(provider: str, reserved_tokens: int, reserved_cost: float, actual_tokens: int, actual_cost: float, now: float | None = None, refund_request: bool = False) -> None:
    """Adjust today's reserved tokens/cost to observed usage, or refund failed calls."""
    if provider == "ollama":
        return
    with LOCK:
        try:
            state = _load(time.time() if now is None else now)
            used = int(str(state["cloud_requests_today"]))
            toks = int(str(state["estimated_tokens_today"]))
            spent = float(str(state["estimated_cost_usd"]))
            state.update(
                cloud_requests_today=max(0, used - 1) if refund_request else used,
                estimated_tokens_today=max(0, toks + actual_tokens - reserved_tokens),
                estimated_cost_usd=round(max(0.0, spent + actual_cost - reserved_cost), 8),
            )
            _save(state)
        except (OSError, ValueError, TypeError, KeyError):
            return


def reset_budget(now: float | None = None) -> None:
    with LOCK:
        timestamp = time.time() if now is None else now
        try:
            recent = _load(timestamp)["minute_timestamps"]
        except (OSError, ValueError, TypeError, KeyError):
            recent = []
        if BUDGET_FILE.is_symlink():
            raise ValueError("Budget storage cannot be a symbolic link")
        _save({"date_str": datetime.fromtimestamp(timestamp, UTC).date().isoformat(), "cloud_requests_today": 0, "estimated_tokens_today": 0, "estimated_cost_usd": 0.0, "minute_timestamps": recent})
