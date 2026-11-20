"""Content topic inference and legacy metadata repair regressions."""

from pathlib import Path

from features.ingestion.anonymizer import anonymize_text
from features.ingestion.converters import convert_file_to_chunks, infer_document_tags
from features.ingestion.service import ingest_directory


def test_consecutive_redaction_tokens_collapse() -> None:
    for separator in (" ", "_", "  "):
        raw = separator.join(["[REDACTED_NAME]"] * 3)
        assert anonymize_text("CV " + raw)[0] == "CV [REDACTED_NAME]"
    assert anonymize_text("Alice Smith", "CV_Alice_Smith.pdf") == ("[REDACTED_NAME]", 2)
    assert anonymize_text("[REDACTED_NAME] [REDACTED_EMAIL]")[0] == "[REDACTED_NAME] [REDACTED_EMAIL]"


def test_infer_document_tags_uses_real_domain_content() -> None:
    text = "# Python Architecture\nTags: uploaded\n## Engineering\nPython architecture engineering finance recipes. "
    text += "Python architecture engineering finance recipes. The and this und der die eine [REDACTED_NAME] 2026 pdf docx txt uploaded."
    tags = infer_document_tags(text)
    assert len(tags) == 5 and {"python", "architecture", "engineering", "finance", "recipes"} == set(tags)
    assert tags == infer_document_tags(text)
    assert all(word.isalpha() and word.islower() and 4 <= len(word) <= 18 for word in tags)


def test_index_repairs_placeholder_tags_and_preserves_curated_topics(tmp_path: Path) -> None:
    document = tmp_path / "cv.md"
    content = "# Python Architecture\nTags: uploaded\n\n## Engineering\nPython engineering architecture finance finance.\n"
    document.write_text(content, encoding="utf-8")
    assert "uploaded" not in ingest_directory(tmp_path)[0].tags
    repaired = document.read_text(encoding="utf-8")
    assert "Tags: uploaded" not in repaired and "Python engineering architecture" in repaired
    assert ingest_directory(tmp_path)[0].tags == convert_file_to_chunks(document)[0].tags
    curated = content.replace("uploaded", "study-notes")
    document.write_text(curated, encoding="utf-8")
    assert ingest_directory(tmp_path)[0].tags == ["study-notes"] and document.read_text() == curated
