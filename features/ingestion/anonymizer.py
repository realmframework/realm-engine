"""DSGVO / GDPR PII anonymizer for scrubbing names, emails, IBANs, IPs, and phone numbers."""

import re
from pathlib import Path

from core.contracts import AnonymizationReport

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IBAN_RE = re.compile(
    r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b|\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"
)
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]+)\d{3,4}[\s.-]?\d{2,5}\b"
)
_DOB_RE = re.compile(r"\b\d{1,2}\.\d{1,2}\.(?:19|20)\d{2}\b")
_HEALTH_RE = re.compile(r"\b[A-Z]\d{9}\b")
_ADDRESS_RE = re.compile(r"\b\d{5}\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+\b|\b[A-ZÄÖÜ][a-zäöüß]+(?:straße|str\.|weg|platz|allee)\s+\d+[a-zA-Z]?\b")
PII_TYPES = ("EMAIL", "IBAN", "PHONE", "NAME", "IP", "DOB", "HEALTH_ID", "ADDRESS")
_CV_MARKERS = {"cv", "resume", "lebenslauf", "curriculum", "vitae", "bio", "profile"}
_DOC_STOPWORDS = {
    *_CV_MARKERS,
    "report", "guide", "doc", "docs", "document", "notes", "note", "study", "lecture",
    "spec", "architecture", "en", "de", "fr", "es", "it", "pt", "alt", "final", "draft",
    "new", "copy", "pdf", "docx", "txt", "md", "html", "overview", "summary", "handbook",
    "manual", "project", "test", "page", "section", "chapter", "part", "version", "file",
    "upload", "uploaded", "knowledge", "base", "system", "engine", "ai", "rag", "llm",
    "patient", "patients", "care", "healthcare", "health", "pflege", "medizin",
}


def extract_filename_names(filename: str) -> list[str]:
    """Extract proper-name tokens from a document filename while ignoring common document words."""
    if not filename:
        return []
    stem = Path(filename).stem
    tokens = [tok for tok in re.split(r"[^A-Za-zÀ-ÖØ-öø-ÿ]+", stem) if len(tok) >= 2]
    is_personal_doc = any(tok.lower() in _CV_MARKERS for tok in tokens)
    names: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if low in _DOC_STOPWORDS:
            continue
        if (tok[0].isupper() or is_personal_doc) and low not in [n.lower() for n in names]:
            names.append(tok)
    return names


def anonymize_slug(filename: str, fallback_stem: str) -> str:
    """Return a scrubbed filename stem with personal name tokens removed."""
    names = {n.lower() for n in extract_filename_names(filename)}
    if not names:
        return fallback_stem
    kept = [p for p in fallback_stem.split("_") if p and p.lower() not in names]
    return "_".join(kept) if kept else "anonymized_document"


def anonymize_text(text: str, filename: str = "") -> tuple[str, int]:
    """Apply exactly the same redaction rules as the visual inspection preview."""
    report = _inspection(text, filename)
    return report.scrubbed_text, report.total_redacted


def inspect_anonymization(text: str, filename: str = "") -> dict[str, object]:
    """Inspect PII without persistence; samples mask originals and scrub surrounding context."""
    return _inspection(text, filename).model_dump()


def collapse_redaction_tokens(text: str) -> str:
    """Coalesce identical adjacent tokens on a line without joining paragraphs."""
    return re.sub(r"(\[REDACTED_[A-Z_]+\])(?:[ \t_]+\1)+", r"\1", text)


def _masked_sample(value: str, category: str) -> str:
    if category == "EMAIL":
        local, domain = value.split("@", 1)
        return local[:1] + "***@" + domain
    return value[:1] + "***" if category == "NAME" else "***" + value[-2:]


def _inspection(text: str, filename: str) -> AnonymizationReport:
    patterns = [("EMAIL", _EMAIL_RE), ("IBAN", _IBAN_RE), ("IP", _IPV4_RE), ("DOB", _DOB_RE), ("HEALTH_ID", _HEALTH_RE), ("ADDRESS", _ADDRESS_RE), ("PHONE", _PHONE_RE)]
    patterns += [("NAME", re.compile(rf"\b{re.escape(n)}\b", re.IGNORECASE)) for n in extract_filename_names(filename)]
    matches: list[tuple[int, int, str]] = []
    occupied = bytearray(len(text))
    for category, pattern in patterns:
        for match in pattern.finditer(text):
            if not any(occupied[match.start():match.end()]):
                matches.append((match.start(), match.end(), category))
                occupied[match.start():match.end()] = b"\x01" * (match.end() - match.start())
    counts: dict[str, int] = dict.fromkeys(PII_TYPES, 0)
    parts: list[str] = []
    samples: list[dict[str, str]] = []
    offsets: list[int] = []
    cursor, output_size = 0, 0
    for start, end, category in sorted(matches):
        prefix, replacement = text[cursor:start], f"[REDACTED_{category}]"
        output_size += len(prefix)
        parts.extend((prefix, replacement))
        counts[category] += 1
        if len(samples) < 8:
            samples.append({"type": category, "original": _masked_sample(text[start:end], category), "replacement": replacement})
            offsets.append(output_size)
        output_size += len(replacement)
        cursor = end
    parts.append(text[cursor:])
    scrubbed = "".join(parts)
    for sample, offset in zip(samples, offsets, strict=True):
        sample["context"] = collapse_redaction_tokens("…" + scrubbed[max(0, offset - 35):offset + len(sample["replacement"]) + 35] + "…")
    return AnonymizationReport(scrubbed_text=collapse_redaction_tokens(scrubbed), total_redacted=sum(counts.values()), counts_by_type=counts, samples=samples)
