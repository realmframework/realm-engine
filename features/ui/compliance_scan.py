"""Local Markdown token inventory and pattern inspection; never claims full PII coverage."""

import re
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile

CATEGORIES = ("NAME", "EMAIL", "PHONE", "IBAN", "DOB", "HEALTH_ID", "ADDRESS", "IP")
TOKEN = re.compile(r"\[REDACTED_([A-Z_]+)\]")


def scan_vault(base: Path, inspect: Callable[[str, str], dict[str, object]], scrub: bool = False) -> dict[str, object]:
    counts = dict.fromkeys(CATEGORIES, 0)
    warnings = errors = files = redacted = 0
    base_res = base.resolve()
    for path in sorted(p for p in base.rglob("*") if p.suffix.lower() == ".md"):
        if any(part.startswith(".") for part in path.relative_to(base).parts):
            continue
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base_res):
            continue
        temporary: Path | None = None
        try:
            text = path.read_text(encoding="utf-8")
            report = inspect(text, path.name)
            detected = int(str(report["total_redacted"]))
            if scrub and detected:
                text = str(report["scrubbed_text"])
                with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(text)
                temporary.replace(path)
                redacted += detected
            else:
                warnings += detected
            for category in TOKEN.findall(text):
                if category in counts:
                    counts[category] += 1
            files += 1
        except (OSError, UnicodeError, ValueError, KeyError):
            errors += 1
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
    return {"files_scanned": files, "counts_by_type": counts, "total_redacted_tokens": sum(counts.values()), "unredacted_warnings": warnings, "scan_errors": errors, "clean_vault": warnings == 0 and errors == 0, "redacted_now": redacted}
