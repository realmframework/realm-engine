"""Deterministic content topics and repair of placeholder Markdown metadata."""

import re
from collections import Counter
from pathlib import Path

from features.ingestion.anonymizer import anonymize_text, collapse_redaction_tokens

INVALID_TAGS = {"uploaded", "upload", "pdf", "docx", "txt", "html", "markdown", "general"}
STOPWORD_TEXT = """
about above after again against also among another because before being below between
both could does doing down during each even every from further have having
here into itself just more most much must only other ours over same
should some such than that their theirs them then there these they this
those through under until very what when where which while whom will with
would your yours been were shall either neither whose once upon within without
aber alle allem allen aller alles also andere anderen anderer anderes auch beim
bereits beide beiden damit dann darf dazu dass dem den denn der deren
des diese diesem diesen dieser dieses doch dort durch eine einem einen einer
eines etwas fuer für ganz haben hatte heute hier ihre ihrem ihren ihrer
ihres immer kann keine keinem keinen keiner keines können machen mehr meine meinem
meinen meiner meines muss nach nicht noch oder ohne seine seinem seinen seiner
seines sein sehr sich sind sollte sowie über und unter viele vom von
vor waren weiter welche welchem welchen welcher welches wenn werden wurde wurden wird
zum zur zwischen dies wird tags title overview section chapter page document documents
notes note guide summary file files contact contacts personal details information curriculum vitae
lebenslauf resume redacted name email phone iban address unknown extractable content text date
dates
"""
STOPWORDS = set(STOPWORD_TEXT.split()) | INVALID_TAGS


def infer_document_tags(text: str) -> list[str]:
    """Rank 4–18 letter content words by heading presence and repeated occurrences."""
    clean = re.sub(r"\[REDACTED_[A-Z_]+\]|https?://\S+|\S+@\S+", " ", text)
    lines = [line for line in clean.splitlines() if not line.startswith("Tags:")]

    def words(value: str) -> list[str]:
        return [word for word in re.findall(r"[^\W\d_]+", value.casefold()) if 4 <= len(word) <= 18 and word not in STOPWORDS]

    counts = Counter(words("\n".join(lines)))
    headings = Counter(words("\n".join(line.lstrip("# ") for line in lines if line.startswith("#"))))
    ranked = sorted(counts, key=lambda word: (-(counts[word] + 3 * headings[word]), -counts[word], word))
    return ranked[:5] or ["knowledge"]


def normalize_document_tags(text: str, filename: str = "", tags: list[str] | None = None) -> str:
    """Keep curated domain tags, replace placeholders, and clean repeated redactions."""
    text = collapse_redaction_tokens(text)
    lines = text.splitlines()
    if lines and lines[0].strip() == "---" and any(line.strip() in {"---", "..."} for line in lines[1:]):
        return text if text.endswith("\n") else text + "\n"
    tag_index = 1 if len(lines) > 1 and lines[1].startswith("Tags:") else None
    existing = lines[1][5:].split(",") if tag_index is not None else []
    valid = list(dict.fromkeys(t.strip().lower() for t in (tags or existing) if t.strip() and t.strip().lower() not in INVALID_TAGS))
    content = "\n".join(line for i, line in enumerate(lines) if i != tag_index)
    chosen = valid or infer_document_tags(anonymize_text(content, filename)[0])
    if tag_index is None:
        lines.insert(1 if lines and lines[0].startswith("#") else 0, "Tags: " + ", ".join(chosen))
    else:
        lines[tag_index] = "Tags: " + ", ".join(chosen)
    return "\n".join(lines) + "\n"


def repair_directory_topics(directory: Path) -> None:
    """Repair legacy Markdown metadata without parsing unrelated binary documents."""
    for path in directory.rglob("*.md"):
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            continue
        text = path.read_text(encoding="utf-8")
        if has_placeholder_tags(text):
            path.write_text(normalize_document_tags(text, path.name), encoding="utf-8")


def has_placeholder_tags(text: str) -> bool:
    metadata = text.splitlines()[1:2]
    return bool(metadata and metadata[0].startswith("Tags:") and any(tag.strip().lower() in INVALID_TAGS for tag in metadata[0][5:].split(",")))
