"""Browser helpers for conversation Markdown export, library saving, and source navigation."""

CHAT_ACTIONS_SCRIPT: str = r"""
const chatActionsInFlight = new Set();
function chatActionsHeader() {
  if (!currentChatId || (!currentTurns.length && !activeAttachedNotes.length)) { return ""; }
  const busy = chatActionsInFlight.has(activeKnowledgeArea + "::" + currentChatId) || currentTurns.some(function (t) { return !t.created_at || t.loadingTutor; });
  const style = "px-2.5 py-1.5 rounded-lg border border-white/10 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5 focus-visible:outline focus-visible:outline-2 disabled:opacity-40 disabled:cursor-wait inline-flex items-center gap-1.5 transition";
  const pinned = typeof pinnedFormatObj === "function" ? pinnedFormatObj() : null;
  const fmtBtn = "<button id='chat-format-btn' type='button' class='px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/12 border border-[#4BB8E8]/35 text-xs font-medium text-[#4BB8E8] hover:bg-[#4BB8E8]/22 inline-flex items-center gap-1.5 transition'" + (busy ? " disabled" : "") + ">" + FORMAT_SVG + "<span>" + (pinned ? ("Format: " + escapeHtml(pinned.name)) : "Answer in Format…") + "</span></button>"
    + (pinned ? "<button id='chat-unpin-format-btn' type='button' title='Unpin format' class='px-1.5 py-1 rounded-lg border border-white/10 text-xs text-[#738196] hover:text-[#EEF2F8]'>✕</button>" : "");
  const freeBadge = freeChatMode ? "<span class='px-2.5 py-1 rounded-full bg-white/[0.05] border border-white/10 text-[11px] font-mono text-[#A0B0C8]'>Free Chat</span>" : "";
  const pdfBtn = "<button id='chat-pdf-btn' type='button' class='" + style + "'" + (busy ? " disabled" : "") + ">" + PDF_SVG + "<span>PDF</span></button>";
  return "<header class='flex flex-col gap-2 pt-6'><div class='flex items-center justify-between gap-2 flex-wrap' aria-label='Conversation actions'><div class='flex items-center gap-1.5 flex-wrap'>" + fmtBtn + freeBadge + "</div><div class='flex items-center gap-1.5 flex-wrap'>" + pdfBtn + "<button id='chat-export-btn' type='button' class='" + style + "'" + (busy ? " disabled" : "") + ">↓ .md</button><button id='chat-save-btn' type='button' class='" + style + "'" + (busy || freeChatMode ? " disabled" : "") + ">＋ Save</button></div></div><p id='chat-action-status' role='status' class='text-xs text-[#A0B0C8]'></p></header>";
}
function chatSlug(title) {
  return String(title || "conversation").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80) || "conversation";
}
function conversationMarkdown(session) {
  const title = String(session.title || "Conversation").replace(/[\r\n]+/g, " ");
  const lines = ["# " + title, "Tags: study-notes", "", "Created: " + (session.turns[0] ? session.turns[0].created_at : session.updated_at), "Updated: " + session.updated_at];
  const agentLbl = typeof activeAgentName === "function" ? activeAgentName() : "Saga";
  (session.turns || []).forEach(function (turn, index) {
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
async function runChatAction(saveToLibrary) {
  const version = areaVersion, actionKey = activeKnowledgeArea + "::" + currentChatId;
  const chatId = currentChatId, status = document.getElementById("chat-action-status"), buttons = Array.from(document.querySelectorAll("#chat-export-btn, #chat-save-btn"));
  if (!chatId || chatActionsInFlight.has(actionKey) || buttons.some(function (btn) { return btn.disabled; })) { return; }
  chatActionsInFlight.add(actionKey);
  buttons.forEach(function (btn) { btn.disabled = true; });
  status.textContent = saveToLibrary ? "Saving study notes..." : "Preparing Markdown...";
  try {
    const response = await areaFetch("/api/chats/" + encodeURIComponent(chatId) + (freeChatMode ? "?free_chat=true" : ""));
    if (!response.ok) { throw new Error("Conversation could not be loaded. Please try again."); }
    const session = await response.json(), markdown = conversationMarkdown(session), slug = chatSlug(session.title);
    if (currentChatId !== chatId || version !== areaVersion || !status.isConnected) { return; }
    if (saveToLibrary) {
      const filename = slug + "-study-notes-" + newChatId() + ".md";
      const upload = await areaFetch("/api/upload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: filename, content: markdown, tags: "study-notes" }) });
      const data = await upload.json(); if (version !== areaVersion) { return; }
      if (!upload.ok) { throw new Error(typeof data.detail === "string" ? data.detail : "Study notes could not be saved. Please try again."); }
      applyWorkspacePayload(data); await loadGuidesCatalog(null);
      status.textContent = "Saved to Library · study-notes" + (data.redacted_count ? " · " + data.redacted_count + " personal details redacted" : "");
    } else {
      const url = URL.createObjectURL(new Blob([markdown], { type: "text/markdown;charset=utf-8" })), link = document.createElement("a");
      link.href = url; link.download = slug + ".md"; document.body.appendChild(link); link.click(); link.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      status.textContent = "Markdown exported.";
    }
  } catch (error) { status.textContent = error.message || "Conversation action failed. Please try again."; }
  finally {
    chatActionsInFlight.delete(actionKey);
    if (currentChatId === chatId && version === areaVersion) {
      const liveStatus = document.getElementById("chat-action-status"); if (liveStatus) { liveStatus.textContent = status.textContent; }
      document.querySelectorAll("#chat-export-btn, #chat-save-btn").forEach(function (btn) { btn.disabled = currentTurns.some(function (t) { return !t.created_at || t.loadingTutor; }); });
    }
  }
}
function bindChatActions(stream) {
  const exportBtn = document.getElementById("chat-export-btn"), saveBtn = document.getElementById("chat-save-btn");
  const fmtBtn = document.getElementById("chat-format-btn"), unpinBtn = document.getElementById("chat-unpin-format-btn");
  const pdfBtn = document.getElementById("chat-pdf-btn");
  if (exportBtn) { exportBtn.addEventListener("click", function () { runChatAction(false); }); }
  if (saveBtn) { saveBtn.addEventListener("click", function () { runChatAction(true); }); }
  if (fmtBtn && typeof openFormatStudio === "function") { fmtBtn.addEventListener("click", function () { openFormatStudio("browse"); }); }
  if (unpinBtn && typeof pinFormat === "function") { unpinBtn.addEventListener("click", function () { pinFormat(null); }); }
  if (pdfBtn && typeof exportFullChatPdf === "function") { pdfBtn.addEventListener("click", exportFullChatPdf); }
  stream.querySelectorAll("[data-reader-turn]").forEach(function (link) {
    link.addEventListener("click", function (event) { event.preventDefault(); openCitationGuide(Number(link.dataset.readerTurn), Number(link.dataset.readerChunk)); });
  });
}
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
