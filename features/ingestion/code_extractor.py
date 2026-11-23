"""Pure-Python source-code and config file chunker for RAG indexing."""

from __future__ import annotations

CODE_CHAR_TARGET = 1200
CODE_LINE_TARGET = 65


def extract_code(raw_text: str, filename: str, lang: str) -> tuple[str, list[tuple[str, str]]]:
    """Slice source code into line-numbered fenced Markdown sections."""
    lines = raw_text.replace("\r\n", "\n").splitlines()
    if not lines:
        return filename, [("Lines 1–1", f"```{lang}\n```")]
    sections: list[tuple[str, str]] = []
    chunk: list[str] = []
    start, char_len = 1, 0
    for idx, line in enumerate(lines, 1):
        if chunk and (char_len + len(line) > CODE_CHAR_TARGET or len(chunk) >= CODE_LINE_TARGET):
            sections.append((f"Lines {start}–{idx - 1}", f"```{lang}\n" + "\n".join(chunk) + "\n```"))
            chunk, start, char_len = [], idx, 0
        chunk.append(line)
        char_len += len(line) + 1
    if chunk:
        sections.append((f"Lines {start}–{len(lines)}", f"```{lang}\n" + "\n".join(chunk) + "\n```"))
    return filename, sections
