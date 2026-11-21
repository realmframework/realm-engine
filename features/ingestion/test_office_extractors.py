"""Tests for pure-Python CSV, TSV, Excel (.xlsx), and PowerPoint (.pptx) ingestion."""

import io
import zipfile
from pathlib import Path

from features.ingestion.converters import convert_bytes_to_markdown
from features.ingestion.service import ingest_directory


def _make_xlsx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "xl/workbook.xml",
            '<workbook><sheets><sheet name="Budget" sheetId="1"/></sheets></workbook>',
        )
        zf.writestr(
            "xl/sharedStrings.xml",
            "<sst><si><t>Category</t></si><si><t>Amount</t></si><si><t>Servers</t></si></sst>",
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet><sheetData>'
            '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
            '<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2"><v>420</v></c></row>'
            "</sheetData></worksheet>",
        )
    return buf.getvalue()


def _make_pptx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ppt/slides/slide1.xml", "<sld><p><t>Quarterly Roadmap</t></p><p><t>Ship desktop engine</t></p></sld>")
        zf.writestr("ppt/slides/slide2.xml", "<sld><p><t>Privacy First</t></p></sld>")
    return buf.getvalue()


def test_csv_tsv_xlsx_and_pptx_convert_to_structured_markdown() -> None:
    csv_md = convert_bytes_to_markdown("expenses.csv", b"Item,Cost\nCoffee,4\nBook,20\n")
    assert "# Expenses" in csv_md and "| Item | Cost |" in csv_md and "| Coffee | 4 |" in csv_md

    tsv_md = convert_bytes_to_markdown("notes.tsv", b"Key\tValue\nMode\tLocal\n")
    assert "| Key | Value |" in tsv_md and "| Mode | Local |" in tsv_md

    xlsx_md = convert_bytes_to_markdown("q1_plan.xlsx", _make_xlsx())
    assert "## Budget" in xlsx_md and "| Category | Amount |" in xlsx_md and "| Servers | 420 |" in xlsx_md

    pptx_md = convert_bytes_to_markdown("deck.pptx", _make_pptx())
    assert "## Slide 1" in pptx_md and "Quarterly Roadmap" in pptx_md and "## Slide 2" in pptx_md and "Privacy First" in pptx_md


def test_ingest_directory_recursively_indexes_office_files(tmp_path: Path) -> None:
    nested = tmp_path / "finance" / "2026"
    nested.mkdir(parents=True)
    (nested / "budget.xlsx").write_bytes(_make_xlsx())
    (nested / "slides.pptx").write_bytes(_make_pptx())
    (nested / "summary.csv").write_bytes(b"Metric,Score\nRecall,0.98\n")

    chunks = ingest_directory(tmp_path)
    doc_ids = {c.doc_id for c in chunks}
    assert {"finance/2026/budget", "finance/2026/slides", "finance/2026/summary"} <= doc_ids
