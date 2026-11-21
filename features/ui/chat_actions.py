"""Browser helpers for unified Export (PDF / Markdown / Text), library saving, and source links."""

CHAT_ACTIONS_SCRIPT: str = r"""
const chatActionsInFlight = new Set();
const EXPORT_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M12 3v12m0 0-4-4m4 4 4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2'/></svg>";
function exportMenuHtml(kind, idx, disabled, iconOnly) {
  const sumCls = iconOnly
    ? "turn-icon-btn list-none select-none"
    : "list-none cursor-pointer px-2.5 py-1.5 rounded-lg text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5 inline-flex items-center gap-1.5 transition select-none";
  if (disabled) {
    return "<span class='" + sumCls + " opacity-40 pointer-events-none'>" + EXPORT_SVG + (iconOnly ? "" : "<span>" + escapeHtml(t("chat_export")) + "</span>") + "</span>";
  }
  const attr = kind === "turn" ? ("data-export-turn='" + idx + "'") : "data-export-chat='1'";
  const posStyle = kind === "turn" ? "" : " style='top:calc(100% + 0.35rem);bottom:auto;left:auto;right:0'";
  const labelAttr = iconOnly ? (" title='" + escapeHtml(t("chat_export").replace(" ⌄", "")) + "' aria-label='" + escapeHtml(t("chat_export").replace(" ⌄", "")) + "'") : "";
  return "<details class='export-menu relative inline-block'><summary class='" + sumCls + "'" + labelAttr + ">" + EXPORT_SVG + (iconOnly ? "" : "<span>" + escapeHtml(t("chat_export")) + "</span>") + "</summary>"
    + "<div class='turn-popover-panel'" + posStyle + ">"
    + "<button type='button' " + attr + " data-export-fmt='pdf' class='turn-popover-item'>" + escapeHtml(t("chat_exp_pdf")) + "</button>"
    + "<button type='button' " + attr + " data-export-fmt='md' class='turn-popover-item'>" + escapeHtml(t("chat_exp_md")) + "</button>"
    + "<button type='button' " + attr + " data-export-fmt='txt' class='turn-popover-item'>" + escapeHtml(t("chat_exp_txt")) + "</button>"
    + "</div></details>";
}
function chatActionsHeader() {
  if (!currentChatId || (!currentTurns.length && !activeAttachedNotes.length)) { return ""; }
  const busy = chatActionsInFlight.has(activeKnowledgeArea + "::" + currentChatId) || currentTurns.some(function (t) { return !t.created_at || t.loadingTutor; });
  const style = "px-2.5 py-1.5 rounded-lg text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5 focus-visible:outline focus-visible:outline-2 disabled:opacity-40 disabled:cursor-wait inline-flex items-center gap-1.5 transition";
  const pinned = typeof pinnedFormatObj === "function" ? pinnedFormatObj() : null;
  const fmtBtn = pinned
    ? ("<button id='chat-format-btn' type='button' class='px-2.5 py-1 rounded-full bg-[#4BB8E8]/15 border border-[#4BB8E8]/35 text-xs font-medium text-[#4BB8E8] hover:bg-[#4BB8E8]/20 inline-flex items-center gap-1.5 transition'" + (busy ? " disabled" : "") + ">" + FORMAT_SVG + "<span>" + escapeHtml(t("chat_format_pinned", { name: pinned.name })) + "</span></button>"
      + "<button id='chat-unpin-format-btn' type='button' title='Unpin format' aria-label='Unpin format' class='px-1.5 py-1 rounded-full text-xs text-[#738196] hover:text-[#EEF2F8] hover:bg-white/5'>✕</button>")
    : "";
  const freeBadge = freeChatMode ? "<span class='px-2.5 py-1 rounded-full bg-white/[0.05] border border-white/10 text-[11px] font-mono text-[#A0B0C8]'>" + escapeHtml(t("free_chat_short")) + "</span>" : "";
  const saveBtn = freeChatMode ? "" : "<button id='chat-save-btn' type='button' class='" + style + "'" + (busy ? " disabled" : "") + ">" + escapeHtml(t("chat_save")) + "</button>";
  return "<header class='flex flex-col gap-1.5 pt-3'><h1 class='visually-hidden'>Conversation</h1><div role='toolbar' class='flex items-center justify-between gap-2 flex-wrap' aria-label='Conversation actions'><div class='flex items-center gap-1.5 flex-wrap'>" + fmtBtn + freeBadge + "</div><div class='flex items-center gap-1 flex-wrap'>" + exportMenuHtml("chat", 0, busy, false) + saveBtn + "</div></div><p id='chat-action-status' role='status' class='text-xs text-[#A0B0C8]'></p></header>";
}
function chatSlug(title) {
  return String(title || "conversation").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80) || "conversation";
}
function downloadBlobText(content, filename, mime) {
  const url = URL.createObjectURL(new Blob([content], { type: mime })), link = document.createElement("a");
  link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}
function stripMarkdownToText(md) {
  return String(md || "").replace(/```[^\n]*\n([\s\S]*?)```/g, "$1").replace(/^#{1,6}\s+/gm, "").replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)").replace(/[*_`]+/g, "").trim();
}
function conversationMarkdown(session) {
  const title = String(session.title || "Conversation").replace(/[\r\n]+/g, " ");
  const lines = ["# " + title, "Tags: study-notes", "", "Created: " + (session.turns[0] ? session.turns[0].created_at : session.updated_at), "Updated: " + session.updated_at];
  (session.turns || []).forEach(function (turn, index) {
    const agentLbl = typeof turnAuthorName === "function" ? turnAuthorName(turn) : (turn.agent_name || "Saga");
    lines.push("", "## Turn " + (index + 1), "", "Timestamp: " + turn.created_at, "", "### User Question", "", turn.query, "", "### " + agentLbl + " Answer", "", turn.tutor ? turn.tutor.answer : "Raw search only; no " + agentLbl + " answer.", "", "### Source Citations", "");
    const citations = Array.from(new Set((turn.tutor && turn.tutor.cited_titles) || []));
    citations.forEach(function (title, i) { lines.push((i + 1) + ". " + title); });
    (turn.results || []).forEach(function (item) {
      lines.push("", "- " + item.chunk.title, "  Source: " + item.chunk.file_path, "", item.chunk.content);
    });
    if (!citations.length && !(turn.results || []).length) { lines.push("No sources recorded."); }
  });
  return lines.join("\n") + "\n";
}
function exportSingleTurn(tIdx, fmt) {
  const turn = currentTurns[tIdx]; if (!turn || !turn.tutor) { return; }
  if (fmt === "pdf" && typeof exportTurnPdf === "function") { exportTurnPdf(tIdx); return; }
  const title = turn.format_name || turn.query.slice(0, 60) || "response", slug = chatSlug(title);
  const cited = Array.from(new Set(turn.tutor.cited_titles || []));
  const md = "# " + title + "\n\n" + turn.tutor.answer + (cited.length ? ("\n\n## Sources\n\n" + cited.map((c, i) => (i + 1) + ". " + c).join("\n")) : "") + "\n";
  if (fmt === "txt") { downloadBlobText(stripMarkdownToText(md) + "\n", slug + ".txt", "text/plain;charset=utf-8"); showToast(t("toast_exp_txt_ok")); }
  else { downloadBlobText(md, slug + ".md", "text/markdown;charset=utf-8"); showToast(t("toast_exp_md_ok")); }
}
async function runChatAction(saveToLibrary, format) {
  const version = areaVersion, actionKey = activeKnowledgeArea + "::" + currentChatId;
  const chatId = currentChatId, status = document.getElementById("chat-action-status"), saveBtn = document.getElementById("chat-save-btn");
  if (!chatId || chatActionsInFlight.has(actionKey)) { return; }
  if (!saveToLibrary && format === "pdf" && typeof exportFullChatPdf === "function") { exportFullChatPdf(); return; }
  chatActionsInFlight.add(actionKey);
  if (saveBtn) { saveBtn.disabled = true; }
  if (status) { status.textContent = saveToLibrary ? "Saving study notes..." : ("Preparing " + (format === "txt" ? "Text" : "Markdown") + "..."); }
  try {
    const response = await areaFetch("/api/chats/" + encodeURIComponent(chatId) + (freeChatMode ? "?free_chat=true" : ""));
    if (!response.ok) { throw new Error("Conversation could not be loaded. Please try again."); }
    const session = await response.json(), markdown = conversationMarkdown(session), slug = chatSlug(session.title);
    if (currentChatId !== chatId || version !== areaVersion) { return; }
    if (saveToLibrary) {
      const filename = slug + "-study-notes-" + newChatId() + ".md";
      const upload = await areaFetch("/api/upload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: filename, content: markdown, tags: "study-notes" }) });
      const data = await upload.json(); if (version !== areaVersion) { return; }
      if (!upload.ok) { throw new Error(typeof data.detail === "string" ? data.detail : "Study notes could not be saved. Please try again."); }
      applyWorkspacePayload(data); await loadGuidesCatalog(null);
      if (status && status.isConnected) { status.textContent = "Saved to Library · study-notes" + (data.redacted_count ? " · " + data.redacted_count + " personal details redacted" : ""); }
    } else if (format === "txt") {
      downloadBlobText(stripMarkdownToText(markdown) + "\n", slug + ".txt", "text/plain;charset=utf-8");
      if (status && status.isConnected) { status.textContent = "Plain text exported."; }
    } else {
      downloadBlobText(markdown, slug + ".md", "text/markdown;charset=utf-8");
      if (status && status.isConnected) { status.textContent = "Markdown exported."; }
    }
  } catch (error) { if (status && status.isConnected) { status.textContent = error.message || "Conversation action failed. Please try again."; } }
  finally {
    chatActionsInFlight.delete(actionKey);
    if (currentChatId === chatId && version === areaVersion && saveBtn && saveBtn.isConnected) {
      saveBtn.disabled = freeChatMode || currentTurns.some(function (t) { return !t.created_at || t.loadingTutor; });
    }
  }
}
function bindChatActions(stream) {
  const saveBtn = document.getElementById("chat-save-btn"), fmtBtn = document.getElementById("chat-format-btn"), unpinBtn = document.getElementById("chat-unpin-format-btn");
  if (saveBtn) { saveBtn.addEventListener("click", function () { runChatAction(true); }); }
  if (fmtBtn && typeof openFormatStudio === "function") { fmtBtn.addEventListener("click", function () { openFormatStudio("browse"); }); }
  if (unpinBtn && typeof pinFormat === "function") { unpinBtn.addEventListener("click", function () { pinFormat(null); }); }
  stream.querySelectorAll("[data-export-chat]").forEach(function (btn) {
    btn.addEventListener("click", function () { const d = btn.closest("details"); if (d) { d.open = false; } runChatAction(false, btn.dataset.exportFmt || "md"); });
  });
  stream.querySelectorAll("[data-export-turn]").forEach(function (btn) {
    btn.addEventListener("click", function () { const d = btn.closest("details"); if (d) { d.open = false; } exportSingleTurn(Number(btn.dataset.exportTurn || 0), btn.dataset.exportFmt || "pdf"); });
  });
  stream.querySelectorAll("[data-reader-turn]").forEach(function (link) {
    link.addEventListener("click", function (event) { event.preventDefault(); openCitationGuide(Number(link.dataset.readerTurn), Number(link.dataset.readerChunk)); });
  });
}
document.addEventListener("click", function (e) {
  document.querySelectorAll("details.export-menu[open], details.turn-more-menu[open]").forEach(function (d) { if (!d.contains(e.target)) { d.open = false; } });
});
async function openCitationGuide(turnIndex, chunkIndex) {
  const chunk = currentTurns[turnIndex] && currentTurns[turnIndex].results[chunkIndex] && currentTurns[turnIndex].results[chunkIndex].chunk;
  if (!chunk) { return; }
  const operation = ++currentScrollId, origin = document.getElementById("chat-action-status");
  try {
    const guides = await loadGuidesCatalog(null);
    if (operation !== currentScrollId || !origin || !origin.isConnected) { return; }
    const stem = chunk.file_path.replace(/\\/g, "/").split("/").pop().replace(/\.[^.]+$/, "");
    const candidates = guides.filter(function (g) { return g.doc_id === stem && chunk.title.startsWith(g.title + " — "); });
    const guide = guides.find(function (g) { return g.file_path === chunk.file_path; }) || (candidates.length === 1 ? candidates[0] : null);
    if (!guide) { throw new Error("This guide is no longer in the active Library."); }
    const section = chunk.title.slice((guide.title + " — ").length), index = guide.sections.findIndex(function (s) { return s.section_title === section; });
    if (index < 0) { throw new Error("This source section is no longer in the active guide."); }
    abortActiveRequest(); stopActiveAudio(); await renderGuideReader(guide, selectedTag, index);
  } catch (error) { if (origin && origin.isConnected) { origin.textContent = error.message || "Guide could not be opened. Please try again."; } }
}
"""
