"""Privacy-preserving in-memory per-IP and global daily quota guard for REALM_MODE=public."""

import hashlib
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock

QuotaChecker = Callable[[str, float], str | None]
MAX_TRACKED_IPS = 4096


def hash_client_ip(client_ip: str, salt: str = "") -> str:
    """Hash visitor IPs before tracking so raw IP addresses are never stored."""
    effective_salt = salt or os.environ.get("REALM_IP_SALT") or "realm-public"
    return hashlib.sha256(f"{effective_salt}:{client_ip.strip() or 'unknown'}".encode()).hexdigest()[:24]


def create_memory_limiter(
    ip_rpm: int = 5,
    ip_daily: int = 25,
    global_daily: int = 300,
    global_usd: float = 1.0,
    clock: Callable[[], float] = time.time,
) -> QuotaChecker:
    """Atomic in-memory per-IP sliding window + UTC daily global budget guard."""
    lock = RLock()
    state: dict[str, object] = {"day": "", "global_count": 0, "global_usd": 0.0}
    ip_minutes: dict[str, list[float]] = {}
    ip_days: dict[str, int] = {}

    def check(client_ip: str, est_cost_usd: float) -> str | None:
        now = clock()
        today = datetime.fromtimestamp(now, UTC).date().isoformat()
        ip_key = hash_client_ip(client_ip)
        with lock:
            if state["day"] != today:
                state.update(day=today, global_count=0, global_usd=0.0)
                ip_days.clear()
            if len(ip_minutes) > MAX_TRACKED_IPS:
                stale = [k for k, ts in ip_minutes.items() if not any(t > now - 60 for t in ts)]
                for key in stale:
                    ip_minutes.pop(key, None)
            recent = [t for t in ip_minutes.get(ip_key, []) if t > now - 60]
            if len(recent) >= ip_rpm:
                return f"Rate limit reached ({ip_rpm} AI answers/minute). Instant search remains available."
            used_ip = ip_days.get(ip_key, 0)
            if used_ip >= ip_daily:
                return f"Daily visitor limit reached ({ip_daily} AI answers/day). Instant search remains available."
            g_count = int(str(state["global_count"]))
            g_usd = float(str(state["global_usd"]))
            if global_daily == 0 or g_count >= global_daily or g_usd + est_cost_usd > global_usd:
                return "Daily public AI budget reached. Showing instant search results instead."
            ip_minutes[ip_key] = [*recent, now]
            ip_days[ip_key] = used_ip + 1
            state["global_count"] = g_count + 1
            state["global_usd"] = round(g_usd + est_cost_usd, 8)
            return None

    return check


def build_public_limiter(settings: dict[str, object]) -> QuotaChecker:
    """Build the default zero-dependency in-memory quota guard from public settings."""
    return create_memory_limiter(
        ip_rpm=int(str(settings.get("ip_rpm", 5))),
        ip_daily=int(str(settings.get("ip_daily", 25))),
        global_daily=int(str(settings.get("global_daily", 300))),
        global_usd=float(str(settings.get("global_usd", 1.0))),
    )
