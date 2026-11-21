"""Pure-Python extractors for CSV, TSV, Excel (.xlsx), and PowerPoint (.pptx) files."""

import csv
import io
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

MAX_OFFICE_XML_BYTES = 20 * 1024 * 1024
MAX_CUMULATIVE_OFFICE_XML_BYTES = 40 * 1024 * 1024
MAX_XLSX_COLS, MAX_XLSX_ROWS, ROWS_PER_SECTION = 128, 2000, 40
_COL_RE = re.compile(r"^([A-Z]+)")
_SLIDE_NUM_RE = re.compile(r"slide(\d+)\.xml$", re.IGNORECASE)


def _escape_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value).replace("|", "\\|").strip()

def _rows_to_markdown(rows: list[list[str]]) -> str:
    cleaned = [[_escape_cell(c) for c in row] for row in rows if any(c.strip() for c in row)]
    if not cleaned:
        return "No tabular data."
    width = max(len(r) for r in cleaned)
    padded = [r + [""] * (width - len(r)) for r in cleaned]
    return "\n".join(["| " + " | ".join(padded[0]) + " |", "| " + " | ".join(["---"] * width) + " |", *("| " + " | ".join(r) + " |" for r in padded[1:])])

def _read_zip_xml(archive: zipfile.ZipFile, member: str, budget: list[int] | None = None) -> ET.Element:
    with archive.open(member) as handle:
        raw = handle.read(MAX_OFFICE_XML_BYTES + 1)
    if len(raw) > MAX_OFFICE_XML_BYTES:
        raise ValueError("Office XML exceeds the 20 MiB decompression limit")
    if budget is not None:
        budget[0] += len(raw)
        if budget[0] > MAX_CUMULATIVE_OFFICE_XML_BYTES:
            raise ValueError("Office archive exceeds cumulative 40 MiB XML decompression limit")
    return ET.fromstring(raw)

def _col_index(cell_ref: str) -> int:
    if not (match := _COL_RE.match(cell_ref.upper())):
        return 0
    idx = 0
    for ch in match.group(1):
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
        if idx > MAX_XLSX_COLS + 1:
            return MAX_XLSX_COLS
    return max(0, idx - 1)

def _chunk_table_sections(prefix: str, rows: list[list[str]]) -> list[tuple[str, str]]:
    header, body = rows[0], rows[1:]
    if not body or len(body) <= ROWS_PER_SECTION:
        return [(prefix, _rows_to_markdown(rows))]
    return [
        (f"{prefix} (Rows {s + 1}-{min(len(body), s + ROWS_PER_SECTION)})" if prefix != "Overview" else f"Rows {s + 1}-{min(len(body), s + ROWS_PER_SECTION)}",
         _rows_to_markdown([header, *body[s:min(len(body), s + ROWS_PER_SECTION)]]))
        for s in range(0, len(body), ROWS_PER_SECTION)
    ]


def extract_csv(raw_bytes: bytes, fallback_title: str, delimiter: str = ",") -> tuple[str, list[tuple[str, str]]]:
    """Convert CSV or TSV bytes into chunked Markdown table sections."""
    try:
        rows = [row for row in csv.reader(io.StringIO(raw_bytes.decode("utf-8-sig", errors="replace")), delimiter=delimiter) if any(c.strip() for c in row)]
    except csv.Error as exc:
        raise ValueError("Malformed CSV/TSV file or oversized field") from exc
    return fallback_title, _chunk_table_sections("Overview", rows[:MAX_XLSX_ROWS]) if rows else [("Overview", "No extractable tabular content.")]


def _resolve_xlsx_sheets(archive: zipfile.ZipFile, names: set[str]) -> list[tuple[str, str]]:
    rels: dict[str, str] = {}
    if "xl/_rels/workbook.xml.rels" in names:
        for rel in _read_zip_xml(archive, "xl/_rels/workbook.xml.rels").iter():
            if (rel.tag.endswith("}Relationship") or rel.tag == "Relationship") and (rid := rel.attrib.get("Id", "")) and (target := rel.attrib.get("Target", "")):
                rels[rid] = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target))
    ordered, wb_names = [], []
    if "xl/workbook.xml" in names:
        for el in _read_zip_xml(archive, "xl/workbook.xml").iter():
            if not (el.tag.endswith("}sheet") or el.tag == "sheet"):
                continue
            title = el.attrib.get("name") or f"Sheet {len(wb_names) + 1}"
            wb_names.append(title)
            rid = next((v for k, v in el.attrib.items() if k.endswith("}id") or k == "id"), "")
            member = rels.get(rid, "")
            if member in names and member.startswith("xl/worksheets/"):
                ordered.append((title, member))
    if ordered:
        return ordered
    files = sorted((n for n in names if re.match(r"^xl/worksheets/sheet\d+\.xml$", n)), key=lambda p: int(re.findall(r"\d+", p)[-1]))
    return [(wb_names[i] if i < len(wb_names) else f"Sheet {i + 1}", m) for i, m in enumerate(files)]


def extract_xlsx(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    """Extract sheets from an .xlsx workbook with bounded sparse columns & rel-mapped names."""
    budget = [0]
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        names = set(archive.namelist())
        shared = [
            "".join(t.text for t in si.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text)
            for si in (_read_zip_xml(archive, "xl/sharedStrings.xml", budget).iter() if "xl/sharedStrings.xml" in names else [])
            if si.tag.endswith("}si") or si.tag == "si"
        ]
        sections: list[tuple[str, str]] = []
        for title, member in _resolve_xlsx_sheets(archive, names):
            rows: list[list[str]] = []
            for row_el in _read_zip_xml(archive, member, budget).iter():
                if not (row_el.tag.endswith("}row") or row_el.tag == "row") or len(rows) >= MAX_XLSX_ROWS:
                    continue
                row_map, next_col = {}, 0
                for cell in row_el:
                    if not (cell.tag.endswith("}c") or cell.tag == "c"):
                        continue
                    col = _col_index(cell.attrib["r"]) if cell.attrib.get("r") else next_col
                    next_col = col + 1
                    if col >= MAX_XLSX_COLS:
                        continue
                    ctype = cell.attrib.get("t", "")
                    if ctype == "inlineStr":
                        val = "".join(t.text for t in cell.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text)
                    else:
                        v_el = next((c for c in cell if c.tag.endswith("}v") or c.tag == "v"), None)
                        raw_v = (v_el.text or "").strip() if v_el is not None else ""
                        val = shared[int(raw_v)] if (ctype == "s" and raw_v.isdigit() and int(raw_v) < len(shared)) else raw_v
                    if val:
                        row_map[col] = val
                if row_map:
                    rows.append([row_map.get(c, "") for c in range(min(MAX_XLSX_COLS - 1, max(row_map)) + 1)])
            if rows:
                sections.extend(_chunk_table_sections(title, rows))
    return fallback_title, sections or [("Overview", "No extractable spreadsheet content.")]


def extract_pptx(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    """Extract slide text in presentation order from a .pptx archive."""
    budget = [0]
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        slide_files = sorted(
            (n for n in archive.namelist() if _SLIDE_NUM_RE.search(n) and n.startswith("ppt/slides/")),
            key=lambda p: int(_SLIDE_NUM_RE.search(p).group(1)),  # type: ignore[union-attr]
        )
        sections: list[tuple[str, str]] = []
        for idx, member in enumerate(slide_files):
            lines = [
                line for para in _read_zip_xml(archive, member, budget).iter()
                if (para.tag.endswith("}p") or para.tag == "p")
                and (line := "".join(t.text for t in para.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text).strip())
            ]
            if lines:
                sections.append((f"Slide {idx + 1}", "\n\n".join(lines)))
    return fallback_title, sections or [("Slide 1", "No extractable presentation text.")]
