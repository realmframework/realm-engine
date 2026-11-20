"""XSS-safe Markdown renderer with fenced code, tables, blockquotes, equations, and vault links."""

MARKDOWN_SCRIPT: str = r"""
function safeMarkdownHref(raw) {
  const url = String(raw || "").trim();
  if (!url || /^javascript:|^data:|^vbscript:/i.test(url)) { return null; }
  if (/^https?:\/\//i.test(url)) { return { kind: "external", href: url }; }
  if (/\.md(?:#[^#]*)?$/i.test(url) && !url.startsWith("/") && !url.startsWith("//")) { return { kind: "guide", href: url }; }
  return null;
}
function resolveRelativeGuideId(currentDocId, relativeHref) {
  const cleanHref = String(relativeHref || "").split("#")[0].replace(/\.md$/i, "");
  const parts = String(currentDocId || "").split("::").pop().split("/");
  parts.pop();
  for (const seg of cleanHref.split("/")) {
    if (!seg || seg === ".") { continue; }
    if (seg === "..") { parts.pop(); } else { parts.push(seg); }
  }
  const areaPrefix = String(currentDocId || "").includes("::") ? String(currentDocId).split("::")[0] + "::" : "";
  return areaPrefix + parts.join("/");
}
function formatInline(rawText) {
  const codeSpans = [];
  let text = String(rawText || "").replace(/`([^`\n]+)`/g, function (_m, code) {
    const idx = codeSpans.push("<code class='md-code-inline'>" + escapeHtml(code) + "</code>") - 1;
    return "\u0000C" + idx + "\u0000";
  });
  const linkSpans = [];
  text = text.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_m, label, href) {
    const safe = safeMarkdownHref(href);
    const renderedLabel = escapeHtml(label);
    if (!safe) { return renderedLabel; }
    const html = safe.kind === "external"
      ? "<a href='" + escapeHtml(safe.href) + "' target='_blank' rel='noopener noreferrer' class='md-link'>" + renderedLabel + " ↗</a>"
      : "<button type='button' data-md-doc='" + escapeHtml(safe.href) + "' class='md-link'>" + renderedLabel + "</button>";
    const idx = linkSpans.push(html) - 1;
    return "\u0000L" + idx + "\u0000";
  });
  let escaped = escapeHtml(text);
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong class='text-[#EEF2F8] font-semibold'>$1</strong>");
  escaped = escaped.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em class='text-[#EEF2F8]/90 italic'>$2</em>");
  escaped = escaped.replace(/(^|[\s(])_([^_\n]+)_(?=$|[\s.,;:!?)\]])/g, "$1<em class='text-[#EEF2F8]/90 italic'>$2</em>");
  escaped = escaped.replace(/\u0000L(\d+)\u0000/g, function (_m, i) { return linkSpans[Number(i)] || ""; });
  escaped = escaped.replace(/\u0000C(\d+)\u0000/g, function (_m, i) { return codeSpans[Number(i)] || ""; });
  return escaped;
}
function parseTableRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(function (cell) { return cell.trim(); });
}
function isTableSeparator(line) {
  const cells = parseTableRow(line);
  return cells.length > 0 && cells.every(function (c) { return /^:?-{3,}:?$/.test(c); });
}
function renderMarkdownTable(lines) {
  const headers = parseTableRow(lines[0]), rows = lines.slice(2).map(parseTableRow);
  const thead = "<thead><tr>" + headers.map(function (h) { return "<th>" + formatInline(h) + "</th>"; }).join("") + "</tr></thead>";
  const tbody = "<tbody>" + rows.map(function (r) {
    return "<tr>" + headers.map(function (_h, i) { return "<td>" + formatInline(r[i] || "") + "</td>"; }).join("") + "</tr>";
  }).join("") + "</tbody>";
  return "<div class='md-table-wrap'><table class='md-table'>" + thead + tbody + "</table></div>";
}
function formatMarkdown(raw) {
  const cleaned = String(raw || "").replace(/\r\n?/g, "\n").replace(/\n+\s*(?:\*\*|#{1,3}\s*)?(?:Sources|Cited Sources|References|Knowledge Gap)\s*(?:\*\*)?\s*:[\s\S]*$/i, "").trim();
  if (!cleaned) { return ""; }
  const lines = cleaned.split("\n"), out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i], trimmed = line.trim();
    if (!trimmed) { i++; continue; }
    if (/^```/.test(trimmed)) {
      const lang = trimmed.slice(3).trim(), buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i].trim())) { buf.push(lines[i]); i++; }
      if (i < lines.length) { i++; }
      const label = lang ? "<div class='md-pre-lang'>" + escapeHtml(lang) + "</div>" : "";
      out.push("<div class='md-pre-wrap'>" + label + "<pre class='md-pre'><code>" + escapeHtml(buf.join("\n")) + "</code></pre></div>");
      continue;
    }
    if (trimmed === "$$") {
      const buf = []; i++;
      while (i < lines.length && lines[i].trim() !== "$$") { buf.push(lines[i]); i++; }
      if (i < lines.length) { i++; }
      out.push("<div class='md-math'><code>" + escapeHtml(buf.join("\n").trim()) + "</code></div>");
      continue;
    }
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) { out.push("<hr class='md-hr'/>"); i++; continue; }
    const heading = trimmed.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length, cls = level <= 2 ? "text-lg font-semibold text-[#EEF2F8] mt-3 mb-1" : "text-base font-semibold text-[#EEF2F8] mt-3 mb-0.5";
      out.push("<h" + Math.min(4, level + 1) + " class='" + cls + "'>" + formatInline(heading[2]) + "</h" + Math.min(4, level + 1) + ">");
      i++; continue;
    }
    if (trimmed.startsWith(">")) {
      const qLines = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) { qLines.push(lines[i].trim().replace(/^>\s?/, "")); i++; }
      out.push("<blockquote class='md-quote'>" + qLines.map(formatInline).join("<br/>") + "</blockquote>");
      continue;
    }
    if (trimmed.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const tLines = [lines[i], lines[i + 1]]; i += 2;
      while (i < lines.length && lines[i].trim() && lines[i].includes("|")) { tLines.push(lines[i]); i++; }
      out.push(renderMarkdownTable(tLines));
      continue;
    }
    if (/^\s*(?:[-*+]|\d+\.)\s+/.test(line)) {
      const items = [];
      while (i < lines.length) {
        const cur = lines[i];
        if (!cur.trim()) {
          if (i + 1 < lines.length && /^\s*(?:[-*+]|\d+\.)\s+/.test(lines[i + 1])) { i++; continue; }
          break;
        }
        const m = cur.match(/^(\s*)(?:([-*+])|(\d+\.))\s+(.*)$/);
        if (!m) { break; }
        const depth = Math.min(3, Math.floor(m[1].length / 2)), marker = m[3] || "•";
        items.push("<div class='md-list-item' style='padding-inline-start:" + (depth * 1.1) + "rem'><span class='md-list-marker'>" + escapeHtml(marker) + "</span><span class='flex-1 leading-relaxed'>" + formatInline(m[4]) + "</span></div>");
        i++;
      }
      out.push("<div class='md-list'>" + items.join("") + "</div>");
      continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() && !/^(```|\$\$|#{1,4}\s|>|[-*+]\s|\d+\.\s|-{3,}$|\*{3,}$)/.test(lines[i].trim())) {
      if (lines[i].includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) { break; }
      para.push(lines[i].trim()); i++;
    }
    if (para.length) { out.push("<p class='md-p'>" + para.map(formatInline).join(" ") + "</p>"); }
    else { i++; }
  }
  return out.join("");
}
function bindMarkdownLinks(root, currentDocId, previousTag) {
  root.querySelectorAll("[data-md-doc]").forEach(function (button) {
    button.addEventListener("click", async function (event) {
      event.preventDefault(); event.stopPropagation();
      const targetId = resolveRelativeGuideId(currentDocId, button.getAttribute("data-md-doc") || "");
      const list = allGuides.length ? allGuides : await loadGuidesCatalog(null);
      const target = list.find(function (g) { return g.doc_id === targetId || g.doc_id.endsWith("/" + targetId); });
      if (target) { await renderGuideReader(target, previousTag); }
      else { showToast("Linked guide not found in this area: " + targetId); }
    });
  });
}
"""
