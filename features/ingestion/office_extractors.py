"""Pure-Python extractors for CSV, TSV, Excel (.xlsx), and PowerPoint (.pptx) files."""

import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile

MAX_OFFICE_XML_BYTES = 20 * 1024 * 1024
ROWS_PER_SECTION = 40
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
    header = "| " + " | ".join(padded[0]) + " |"
    sep = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(r) + " |" for r in padded[1:]]
    return "\n".join([header, sep, *body])


def _read_zip_xml(archive: zipfile.ZipFile, member: str) -> ET.Element:
    with archive.open(member) as handle:
        raw = handle.read(MAX_OFFICE_XML_BYTES + 1)
    if len(raw) > MAX_OFFICE_XML_BYTES:
        raise ValueError("Office XML exceeds the 20 MiB decompression limit")
    return ET.fromstring(raw)


def _col_index(cell_ref: str) -> int:
    match = _COL_RE.match(cell_ref.upper())
    if not match:
        return 0
    idx = 0
    for ch in match.group(1):
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return max(0, idx - 1)


def extract_csv(raw_bytes: bytes, fallback_title: str, delimiter: str = ",") -> tuple[str, list[tuple[str, str]]]:
    """Convert CSV or TSV bytes into chunked Markdown table sections."""
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in row)]
    if not rows:
        return fallback_title, [("Overview", "No extractable tabular content.")]
    header, body = rows[0], rows[1:]
    if not body:
        return fallback_title, [("Overview", _rows_to_markdown([header]))]
    sections: list[tuple[str, str]] = []
    for start in range(0, len(body), ROWS_PER_SECTION):
        chunk_rows = [header, *body[start : start + ROWS_PER_SECTION]]
        label = "Overview" if len(body) <= ROWS_PER_SECTION else f"Rows {start + 1}-{min(len(body), start + ROWS_PER_SECTION)}"
        sections.append((label, _rows_to_markdown(chunk_rows)))
    return fallback_title, sections


def extract_xlsx(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    """Extract sheets from an .xlsx workbook as Markdown tables without external packages."""
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        names = set(archive.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            ss_root = _read_zip_xml(archive, "xl/sharedStrings.xml")
            for si in ss_root.iter():
                if si.tag.endswith("}si") or si.tag == "si":
                    shared.append("".join(t.text for t in si.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text))
        sheet_names: list[str] = []
        if "xl/workbook.xml" in names:
            wb_root = _read_zip_xml(archive, "xl/workbook.xml")
            sheet_names = [el.attrib["name"] for el in wb_root.iter() if (el.tag.endswith("}sheet") or el.tag == "sheet") and el.attrib.get("name")]
        sheet_files = sorted(
            (n for n in names if re.match(r"^xl/worksheets/sheet\d+\.xml$", n)),
            key=lambda p: int(re.findall(r"\d+", p)[-1]),
        )
        sections: list[tuple[str, str]] = []
        for idx, member in enumerate(sheet_files):
            sheet_root = _read_zip_xml(archive, member)
            rows: list[list[str]] = []
            for row_el in sheet_root.iter():
                if not (row_el.tag.endswith("}row") or row_el.tag == "row"):
                    continue
                row_map: dict[int, str] = {}
                for cell in row_el:
                    if not (cell.tag.endswith("}c") or cell.tag == "c"):
                        continue
                    col = _col_index(cell.attrib.get("r", "")) if cell.attrib.get("r") else len(row_map)
                    ctype = cell.attrib.get("t", "")
                    val = ""
                    if ctype == "inlineStr":
                        val = "".join(t.text for t in cell.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text)
                    else:
                        v_el = next((c for c in cell if c.tag.endswith("}v") or c.tag == "v"), None)
                        raw_v = (v_el.text or "").strip() if v_el is not None else ""
                        if ctype == "s" and raw_v.isdigit() and int(raw_v) < len(shared):
                            val = shared[int(raw_v)]
                        else:
                            val = raw_v
                    if val:
                        row_map[col] = val
                if row_map:
                    max_c = max(row_map)
                    rows.append([row_map.get(c, "") for c in range(max_c + 1)])
            if rows:
                title = sheet_names[idx] if idx < len(sheet_names) else f"Sheet {idx + 1}"
                sections.append((title, _rows_to_markdown(rows[:200])))
    return fallback_title, sections or [("Overview", "No extractable spreadsheet content.")]


def extract_pptx(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    """Extract slide text in presentation order from a .pptx archive."""
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        slide_files = sorted(
            (n for n in archive.namelist() if _SLIDE_NUM_RE.search(n) and n.startswith("ppt/slides/")),
            key=lambda p: int(_SLIDE_NUM_RE.search(p).group(1)),  # type: ignore[union-attr]
        )
        sections: list[tuple[str, str]] = []
        for idx, member in enumerate(slide_files):
            slide_root = _read_zip_xml(archive, member)
            lines: list[str] = []
            for para in slide_root.iter():
                if not (para.tag.endswith("}p") or para.tag == "p"):
                    continue
                line = "".join(t.text for t in para.iter() if (t.tag.endswith("}t") or t.tag == "t") and t.text).strip()
                if line:
                    lines.append(line)
            if lines:
                sections.append((f"Slide {idx + 1}", "\n\n".join(lines)))
    return fallback_title, sections or [("Slide 1", "No extractable presentation text.")]
