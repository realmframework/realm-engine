"""Prepare bounded text for local or explicitly permitted cloud speech."""

import re


def truncate_speech_text(text: str, max_chars: int = 4000) -> str:
    cleaned = re.sub(r"[*`#]+", "", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    window = cleaned[:max_chars]
    last_stop = max(window.rfind(". "), window.rfind("! "), window.rfind("? "), window.rfind("\n"))
    return window[: last_stop + 1].strip() if last_stop > max_chars // 2 else window.strip()
