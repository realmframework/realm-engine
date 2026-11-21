"""Regression guards for WCAG 2.1 AA contrast, accessibility landmarks/labels, and EN/DE/ES i18n."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from features.ui.i18n_script import I18N_SCRIPT
from features.ui.markdown_script import MARKDOWN_SCRIPT
from features.ui.template import HTML_PAGE
from features.ui.theme_script import THEME_SCRIPT

UI_DIR = Path(__file__).resolve().parent


def _hex_rgb(h: str) -> tuple[float, float, float]:
    s = h.lstrip("#")
    return (int(s[0:2], 16) / 255.0, int(s[2:4], 16) / 255.0, int(s[4:6], 16) / 255.0)


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _contrast(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    la = 0.2126 * _lin(a[0]) + 0.7152 * _lin(a[1]) + 0.0722 * _lin(a[2])
    lb = 0.2126 * _lin(b[0]) + 0.7152 * _lin(b[1]) + 0.0722 * _lin(b[2])
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _mix_oklab(h1: str, pct1: float, h2: str) -> tuple[float, float, float]:
    def to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
        r, g, b = _lin(rgb[0]), _lin(rgb[1]), _lin(rgb[2])
        lv = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        mv = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        sv = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
        l_, m_, s_ = math.copysign(abs(lv) ** (1 / 3), lv), math.copysign(abs(mv) ** (1 / 3), mv), math.copysign(abs(sv) ** (1 / 3), sv)
        return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_, 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_, 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)

    l1, l2, t = to_lab(_hex_rgb(h1)), to_lab(_hex_rgb(h2)), pct1 / 100.0
    L, a, b = l1[0] * t + l2[0] * (1 - t), l1[1] * t + l2[1] * (1 - t), l1[2] * t + l2[2] * (1 - t)
    l_, m_, s_ = L + 0.3963377774 * a + 0.2158037573 * b, L - 0.1055613458 * a - 0.0638541728 * b, L - 0.0894841775 * a - 1.2914855480 * b
    lv, mv, sv = l_**3, m_**3, s_**3
    return (_srgb(4.0767416621 * lv - 3.3077115913 * mv + 0.2309699292 * sv), _srgb(-1.2684380046 * lv + 2.6097574011 * mv - 0.3413193965 * sv), _srgb(-0.0041960863 * lv - 0.7034186147 * mv + 1.7076147010 * sv))


def test_all_15_theme_presets_and_semantic_tokens_pass_wcag_aa_contrast() -> None:
    presets = re.findall(r'\baccent:\s*"(#[0-9A-Fa-f]{6})"', THEME_SCRIPT)
    assert len(presets) == 15
    for acc in presets:
        acc_l, bg_l, surf_l = _mix_oklab(acc, 50, "#04060F"), _mix_oklab("#F3F7FC", 92, acc), _mix_oklab("#FFFFFF", 96, acc)
        acc_d, surf_d = _mix_oklab(acc, 88, "#FFFFFF"), _mix_oklab("#0B1020", 90, acc)
        assert _contrast(acc_l, bg_l) >= 4.5 and _contrast(acc_l, surf_l) >= 4.5
        assert _contrast(acc_l, (1.0, 1.0, 1.0)) >= 4.5
        assert _contrast(acc_d, surf_d) >= 4.5 and _contrast(acc_d, _hex_rgb("#04060F")) >= 4.5
    for light_hex, dark_hex in (("#4B5563", "#8A99AE"), ("#1E293B", "#C8D4E6"), ("#047857", "#38D399"), ("#92400E", "#FCD34D"), ("#B91C1C", "#FCA5A5")):
        assert _contrast(_hex_rgb(light_hex), _hex_rgb("#F8FAFD")) >= 4.5
        assert _contrast(_hex_rgb(dark_hex), _hex_rgb("#0E162B")) >= 4.5
    assert _contrast(_hex_rgb("#DC2626"), (1.0, 1.0, 1.0)) >= 4.5


def test_i18n_full_parity_placeholders_aria_and_zero_hardcoded_confirms() -> None:
    dicts: dict[str, dict[str, str]] = {"en": {}, "de": {}, "es": {}}
    for m in re.finditer(r"  (en|de|es): \{([\s\S]*?)\n  \}[,\n]", I18N_SCRIPT):
        for k, v in re.findall(r'(?:^|,\s*|\n\s*)([a-z0-9_]+):\s*"((?:[^"\\]|\\.)*)"', m.group(2)):
            dicts[m.group(1)][k] = v
    assert len(dicts["en"]) >= 680 and set(dicts["en"]) == set(dicts["de"]) == set(dicts["es"])
    for key in dicts["en"]:
        ph_en = set(re.findall(r"\{[a-z0-9_]+\}", dicts["en"][key]))
        assert ph_en == set(re.findall(r"\{[a-z0-9_]+\}", dicts["de"][key])) == set(re.findall(r"\{[a-z0-9_]+\}", dicts["es"][key]))
    used = set(re.findall(r'data-i18n(?:|-span|-placeholder|-aria-label|-title)="([a-z0-9_]+)"', HTML_PAGE))
    used |= set(re.findall(r'\bt\("([a-z0-9_]+)"', HTML_PAGE))
    assert not (used - set(dicts["en"]))
    for path in sorted(UI_DIR.glob("*_script.py")):
        src = path.read_text(encoding="utf-8")
        assert not re.search(r'confirmDeletion\(\s*"', src), f"Hardcoded confirmDeletion in {path.name}"
    for name in ("comfort_script.py", "theme_script.py", "i18n_script.py"):
        assert "localStorage." not in (UI_DIR / name).read_text(encoding="utf-8")


class _FormLabelAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.label_for: set[str] = set()
        self.controls: list[tuple[str, dict[str, str | None], bool]] = []
        self.dialogs: list[dict[str, str | None]] = []
        self._in_label = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if tag == "label":
            self._in_label += 1
            if ad.get("for"):
                self.label_for.add(str(ad["for"]))
        elif tag == "dialog":
            self.dialogs.append(ad)
        elif tag in {"input", "select", "textarea"}:
            self.controls.append((tag, ad, self._in_label > 0))

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self._in_label > 0:
            self._in_label -= 1


def test_html_wcag_landmarks_labels_dialogs_and_reduced_motion() -> None:
    head_body = HTML_PAGE.split("<script>", 1)[0] + HTML_PAGE.split("</script>", 1)[-1]
    parser = _FormLabelAudit()
    parser.feed(head_body)
    assert len(parser.dialogs) >= 12
    for d in parser.dialogs:
        assert d.get("role") != "dialog" and "aria-modal" not in d
    unlabeled: list[str] = []
    for tag, ad, wrapped in parser.controls:
        if ad.get("type") == "hidden" or "hidden" in ad or ad.get("aria-hidden") == "true":
            continue
        cid = ad.get("id") or ""
        if not (wrapped or (cid and cid in parser.label_for) or ad.get("aria-label") or ad.get("aria-labelledby")):
            unlabeled.append(f"{tag}#{cid}")
    assert unlabeled == []
    for marker in ('href="#main-content"', '<main id="main-content"', 'id="app-live-status"', 'id="sidebar-backdrop"', '@media (max-width: 900px)', '<nav aria-label="Primary"', 'data-open-guide=', 'syncGraphMotion'):
        assert marker in HTML_PAGE
    assert "animation-duration: 0.01ms" not in HTML_PAGE
    assert "data-guide-idx='\" + idx + \"' tabindex='0'" not in HTML_PAGE


def test_markdown_lists_are_semantic_ul_ol_and_respect_heading_base() -> None:
    node = shutil.which("node")
    if not node:
        return
    prelude = 'function escapeHtml(v){return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/\'/g,"&#39;");}\n' + MARKDOWN_SCRIPT
    code = prelude + "\nconsole.log(JSON.stringify({ul:formatMarkdown('- One\\n- Two'),ol:formatMarkdown('1. First\\n2. Second'),h:formatMarkdown('# Top\\n## Sub',false,3)}));"
    out = json.loads(subprocess.run([node, "-"], input=code, capture_output=True, text=True, encoding="utf-8", check=True, timeout=5).stdout)
    assert "<ul role='list' class='md-list'>" in out["ul"] and "<li class='md-list-item'" in out["ul"] and "aria-hidden='true'" in out["ul"]
    assert "<ol role='list' class='md-list'>" in out["ol"] and "<li class='md-list-item'" in out["ol"]
    assert "<h3 " in out["h"] and "<h4 " in out["h"] and "<h1" not in out["h"]
