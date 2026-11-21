"""Structured rotating file logging with secret redaction and in-memory error ring buffer."""

import logging
import os
from collections import deque
from contextlib import suppress
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

from core.net_security import scrub_secrets
from core.runtime import data_root

MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
_RING_LOCK = Lock()
_RECENT_EVENTS: deque[dict[str, str]] = deque(maxlen=100)
_CONFIGURED_DIR: Path | None = None


class _SecretRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
            redacted = scrub_secrets(rendered)
            if redacted != rendered:
                record.msg = redacted
                record.args = ()
        except Exception:
            pass
        return True


class _RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.WARNING:
            return
        try:
            msg = scrub_secrets(record.getMessage())[:320]
        except Exception:
            msg = "Log formatting error"
        with _RING_LOCK:
            _RECENT_EVENTS.append({
                "ts": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": msg,
            })


class _PrivateRotatingFileHandler(RotatingFileHandler):
    def _open(self):  # type: ignore[override]
        stream = super()._open()
        if os.name != "nt":
            with suppress(OSError):
                os.chmod(self.baseFilename, 0o600)
        return stream


def log_file_path(root: Path | None = None) -> Path:
    """Return the active rotating log file location under ``<data_root>/logs/``."""
    return (root or data_root()).expanduser().resolve() / "logs" / "realm-engine.log"


def configure_logging(root: Path | None = None) -> logging.Logger:
    """Configure the ``realm`` logger once with 0600 rotating logs and warning/error ring buffer."""
    global _CONFIGURED_DIR
    logger = logging.getLogger("realm")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(isinstance(h, _RingBufferHandler) for h in logger.handlers):
        ring = _RingBufferHandler(level=logging.WARNING)
        ring.addFilter(_SecretRedactingFilter())
        logger.addHandler(ring)
    if os.environ.get("PYTEST_CURRENT_TEST") and root is None:
        return logger
    target_path = log_file_path(root)
    if _CONFIGURED_DIR == target_path.parent and any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        return logger
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.is_symlink() and not target_path.parent.is_symlink():
            for existing in list(logger.handlers):
                if isinstance(existing, RotatingFileHandler):
                    logger.removeHandler(existing)
                    with suppress(OSError):
                        existing.close()
            fh = _PrivateRotatingFileHandler(target_path, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
            fh.addFilter(_SecretRedactingFilter())
            logger.addHandler(fh)
            _CONFIGURED_DIR = target_path.parent
    except OSError:
        pass
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``realm`` namespace."""
    configure_logging()
    suffix = name.removeprefix("realm.")
    return logging.getLogger(f"realm.{suffix}" if suffix else "realm")


def recent_log_events(limit: int = 30) -> list[dict[str, str]]:
    """Return the newest sanitized warning/error entries from the in-memory ring buffer."""
    with _RING_LOCK:
        items = list(_RECENT_EVENTS)
    return items[-max(1, min(100, limit)) :]
