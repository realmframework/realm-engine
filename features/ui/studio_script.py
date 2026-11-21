"""Format & Synthesis Studio, OpenCode Context Meter/Compaction, Inspector, Free Chat & PDF Export."""

STUDIO_SCRIPT: str = r"""
let freeChatMode = false, pinnedFormatId = null, availableFormats = [], lastContextUsage = null, activeAttachedNotes = [], inspectorOpen = false, uploadDestinationMode = "vault";
const PDF_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9ZM14 3v6h6M9 15h6m-6 3h4'/></svg>";
const FORMAT_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 12h6m-6 4h4'/></svg>";
const COMPRESS_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M4 14h6v6M20 10h-6V4m0 6 7-7M3 21l7-7'/></svg>";
function pinnedFormatObj() { return availableFormats.find(f => f.id === pinnedFormatId) || null; }
function fmtTokens(n) { const v = Number(n || 0); return v >= 1000 ? (v / 1000).toFixed(1) + "k" : String(v); }
function syncFreeChatUI() {
  const btn = document.getElementById("free-chat-mode-btn"), pill = document.getElementById("free-chat-pill");
  if (btn) { btn.setAttribute("aria-pressed", String(freeChatMode)); btn.classList.toggle("border-[#4BB8E8]", freeChatMode); }
  if (pill) { pill.textContent = freeChatMode ? "ON" : "OFF"; pill.className = "text-[10px] font-mono " + (freeChatMode ? "text-[#38D399]" : "text-[#738196]"); }
  if (freeChatMode) {
    const title = document.getElementById("brand-title"), dot = document.getElementById("workspace-color-dot");
    if (title) { title.textContent = t("free_chat_short"); title.style.fontSize = ""; }
    if (dot) { dot.innerHTML = "<span class='w-2.5 h-2.5 rounded-full border-2 border-[#4BB8E8] shrink-0'></span>"; }
  }
}
async function setFreeChatMode(on) {
  const next = Boolean(on);
  if (next === freeChatMode) { closeWorkspaceMenu(); return; }
  freeChatMode = next; closeWorkspaceMenu();
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation(); resetHome();
  activeAttachedNotes = []; lastContextUsage = null;
  if (freeChatMode) { syncFreeChatUI(); showToast("Free Chat active — chat freely without an area, or attach files/area anytime."); }
  else { renderKnowledgeAreas(); }
  await loadRecentChats();
}
function setUploadDestinationMode(mode) {
  uploadDestinationMode = mode === "chat" ? "chat" : "vault";
  const vBtn = document.getElementById("upload-mode-vault-btn"), cBtn = document.getElementById("upload-mode-chat-btn");
  const confirmBtn = document.getElementById("confirm-upload-btn"), subRow = document.getElementById("upload-subfolder") && document.getElementById("upload-subfolder").closest(".flex.flex-col");
  const isChat = uploadDestinationMode === "chat";
  if (vBtn) { vBtn.setAttribute("aria-pressed", String(!isChat)); vBtn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (!isChat ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (cBtn) { cBtn.setAttribute("aria-pressed", String(isChat)); cBtn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (isChat ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (confirmBtn) { confirmBtn.textContent = isChat ? "Attach to Chat" : "Upload & Index"; }
  if (subRow) { subRow.hidden = isChat; }
}
async function attachFilesToCurrentChat(files) {
  const statusEl = document.getElementById("upload-status"), btn = document.getElementById("confirm-upload-btn");
  if (!files || !files.length) { if (statusEl) { statusEl.textContent = "Select one or more files first."; } return; }
  if (!currentChatId) { currentChatId = newChatId(); }
  if (btn) { btn.disabled = true; }
  if (statusEl) { statusEl.textContent = "Extracting & attaching to chat…"; }
  try {
    const fd = new FormData();
    for (const f of files) { fd.append("files", f); }
    fd.append("free_chat", String(freeChatMode));
    const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/attach", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.detail || "Could not attach file to chat."); }
    activeAttachedNotes = data.attached_notes || [];
    if (data.context_usage) { lastContextUsage = data.context_usage; }
    uploadModal.close(); stageUploadFiles([]); document.getElementById("upload-file-input").value = "";
    showToast("Attached " + files.length + (files.length === 1 ? " file" : " files") + " to this chat — ready for questions & Format Synthesis.");
    if (currentTurns.length) { renderChatStream(); }
  } catch (err) { if (statusEl) { statusEl.textContent = err.message || "Attachment failed."; } }
  finally { if (btn) { btn.disabled = false; } }
}
async function detachChatNote(idx) {
  if (!currentChatId) { return; }
  const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/attach/" + idx + "?free_chat=" + String(freeChatMode), { method: "DELETE" });
  if (res.ok) { const d = await res.json(); activeAttachedNotes = d.attached_notes || []; lastContextUsage = d.context_usage || lastContextUsage; renderChatStream(); }
}
async function attachVaultToActiveChat(areaName) {
  if (!currentChatId || !freeChatMode) { return; }
  const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/attach-vault", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ area: areaName || activeKnowledgeArea }) });
  const data = await res.json();
  if (!res.ok) { showToast(data.detail || "Could not connect knowledge area."); return; }
  freeChatMode = false;
  if (data.area && data.area !== activeKnowledgeArea) {
    const wsRes = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { knowledge_dir: data.area, active_dirs: [data.area] })) });
    if (wsRes.ok) { activeKnowledgeArea = null; applyWorkspacePayload(await wsRes.json()); }
  } else { renderKnowledgeAreas(); }
  syncFreeChatUI(); await loadRecentChats(); renderChatStream();
  showToast("Connected “" + areaTitle(data.area) + "” to this chat — your next turn will search it.");
}
async function loadOutputFormats() {
  try {
    const res = await fetch("/api/formats");
    if (res.ok) { const d = await res.json(); availableFormats = Array.isArray(d.formats) ? d.formats : []; }
  } catch (_e) {}
}
function setFormatStudioTab(tab) {
  const isCustom = tab === "custom", bBtn = document.getElementById("format-tab-browse"), cBtn = document.getElementById("format-tab-custom");
  const bPane = document.getElementById("format-browse-pane"), cForm = document.getElementById("custom-format-form");
  if (bBtn) { bBtn.setAttribute("aria-selected", String(!isCustom)); bBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (!isCustom ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (cBtn) { cBtn.setAttribute("aria-selected", String(isCustom)); cBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (isCustom ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (bPane) { bPane.hidden = isCustom; }
  if (cForm) { cForm.hidden = !isCustom; }
}
function renderFormatStudio() {
  const grid = document.getElementById("format-cards-grid"), pinInd = document.getElementById("format-pinned-indicator"), sideBadge = document.getElementById("sidebar-format-badge");
  const pinned = pinnedFormatObj(), canSynth = Boolean(currentChatId && (currentTurns.length || activeAttachedNotes.length));
  if (pinInd) { pinInd.textContent = pinned ? ("Pinned: " + pinned.name) : "No format pinned (free conversation)"; }
  if (sideBadge) { sideBadge.textContent = pinned ? "Pinned" : "Studio"; sideBadge.className = "text-xs font-mono " + (pinned ? "text-[#4BB8E8]" : "text-[#738196]"); }
  if (!grid) { return; }
  grid.innerHTML = availableFormats.map(function (f) {
    const isPin = f.id === pinnedFormatId;
    const secs = (f.sections || []).slice(0, 4).map(s => "<span class='px-2 py-0.5 rounded bg-white/[0.04] text-[11px] text-[#A0B0C8] truncate max-w-full'>" + escapeHtml(s) + "</span>").join("");
    const delBtn = !f.builtin ? "<button type='button' data-del-format='" + escapeHtml(f.id) + "' title='Delete custom format' class='text-[#738196] hover:text-[#EF4444] text-xs px-1'>✕</button>" : "";
    return "<article class='rounded-xl bg-[#04060F] border " + (isPin ? "border-[#4BB8E8]" : "border-white/10") + " p-3.5 flex flex-col gap-2.5'>"
      + "<div class='flex items-start justify-between gap-2'><div class='min-w-0'><span class='text-[10px] font-mono uppercase tracking-wider text-[#4BB8E8]'>" + escapeHtml(f.category || "Format") + "</span><h3 class='text-sm font-semibold text-[#EEF2F8] mt-0.5'>" + escapeHtml(f.name) + "</h3></div>" + delBtn + "</div>"
      + (f.description ? "<p class='text-xs text-[#A0B0C8] leading-relaxed'>" + escapeHtml(f.description) + "</p>" : "")
      + "<div class='flex flex-wrap gap-1'>" + secs + ((f.sections || []).length > 4 ? "<span class='text-[11px] text-[#738196] px-1'>+" + (f.sections.length - 4) + " more</span>" : "") + "</div>"
      + "<div class='flex items-center gap-2 mt-auto pt-2 border-t border-white/[0.06]'>"
      + "<button type='button' data-synth-format='" + escapeHtml(f.id) + "'" + (canSynth ? "" : " disabled title='Start a chat or attach a note first'") + " class='flex-1 px-3 py-1.5 rounded-lg bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 disabled:opacity-35 disabled:cursor-not-allowed transition'>✦ Synthesize Now</button>"
      + "<button type='button' data-pin-format='" + escapeHtml(f.id) + "' class='px-2.5 py-1.5 rounded-lg border " + (isPin ? "border-[#4BB8E8] text-[#4BB8E8] bg-[#4BB8E8]/10" : "border-white/15 text-[#A0B0C8] hover:text-[#EEF2F8]") + " text-xs transition'>" + (isPin ? "Unpin" : "Pin") + "</button>"
      + "</div></article>";
  }).join("");
  grid.querySelectorAll("[data-synth-format]").forEach(btn => btn.addEventListener("click", () => runFormatSynthesis(btn.dataset.synthFormat)));
  grid.querySelectorAll("[data-pin-format]").forEach(btn => btn.addEventListener("click", () => pinFormat(btn.dataset.pinFormat)));
  grid.querySelectorAll("[data-del-format]").forEach(btn => btn.addEventListener("click", () => deleteCustomFormatUI(btn.dataset.delFormat)));
}
async function openFormatStudio(tab) {
  if (!availableFormats.length) { await loadOutputFormats(); }
  setFormatStudioTab(tab || "browse"); renderFormatStudio();
  const modal = document.getElementById("format-studio-modal");
  if (modal && !modal.open) { modal.showModal(); }
}
function pinFormat(formatId) {
  pinnedFormatId = pinnedFormatId === formatId ? null : (formatId || null);
  renderFormatStudio();
  if (currentTurns.length) { renderChatStream(); }
  const p = pinnedFormatObj();
  showToast(p ? ("Pinned format: " + p.name + " — replies will follow this structure.") : "Format unpinned — back to free conversation.");
}
async function saveCustomFormatUI(event) {
  event.preventDefault();
  const status = document.getElementById("custom-fmt-status");
  const payload = { name: document.getElementById("custom-fmt-name").value.trim(), category: document.getElementById("custom-fmt-category").value.trim() || "Custom", description: document.getElementById("custom-fmt-desc").value.trim(), sections: document.getElementById("custom-fmt-sections").value.trim(), instructions: document.getElementById("custom-fmt-rules").value.trim() };
  try {
    const res = await fetch("/api/formats", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.detail || "Could not save format."); }
    availableFormats = data.formats || availableFormats;
    document.getElementById("custom-format-form").reset();
    if (status) { status.textContent = "Saved custom format “" + data.format.name + "”."; }
    setFormatStudioTab("browse"); renderFormatStudio();
  } catch (err) { if (status) { status.textContent = err.message; } }
}
async function deleteCustomFormatUI(fmtId) {
  if (!await confirmDeletion("Delete custom format?", "Remove this custom output format?", "Delete")) { return; }
  const res = await fetch("/api/formats/" + encodeURIComponent(fmtId), { method: "DELETE" });
  if (res.ok) { const d = await res.json(); availableFormats = d.formats || []; if (pinnedFormatId === fmtId) { pinnedFormatId = null; } renderFormatStudio(); }
}
async function runFormatSynthesis(formatId) {
  const fmt = availableFormats.find(f => f.id === formatId);
  if (!fmt || !currentChatId) { return; }
  const extra = (document.getElementById("format-extra-focus") && document.getElementById("format-extra-focus").value.trim()) || "";
  const modal = document.getElementById("format-studio-modal"); if (modal && modal.open) { modal.close(); }
  abortActiveRequest();
  const controller = new AbortController(), reqId = "req-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  activeController = controller; activeRequestId = reqId;
  const pendingTurn = { query: "Synthesize as " + fmt.name + (extra ? " — " + extra : ""), ask_tutor: true, loadingTutor: true, streamingText: "", streamingThinking: "", format_name: fmt.name, tutor: null, results: [], collapsed: true };
  currentTurns.push(pendingTurn); setViewMode(true); setLoadingState(true); renderChatStream();
  const synthEl = document.getElementById("turn-" + (currentTurns.length - 1));
  if (synthEl) { scrollIntoViewAsync(synthEl, { behavior: "smooth", block: "start" }); }
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json", "x-request-id": reqId }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/synthesize", { method: "POST", headers, signal: controller.signal, body: JSON.stringify({ format_id: formatId, extra_instruction: extra, free_chat: freeChatMode, provider: providerEl.value, model: modelEl.value.trim() || null, api_key: apiKey || null }) });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Synthesis failed."); }
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let buf = "", doneSession = null;
    const handle = function (raw) {
      let ev = "message", lines = [];
      for (const ln of raw.split(/\r?\n/)) { if (ln.startsWith("event:")) { ev = ln.slice(6).trim(); } else if (ln.startsWith("data:")) { lines.push(ln.slice(5).trim()); } }
      if (!lines.length) { return; }
      let p = null; try { p = JSON.parse(lines.join("\n")); } catch (_e) { return; }
      if (ev === "thinking") {
        const had = Boolean(pendingTurn.streamingThinking);
        pendingTurn.streamingThinking = (pendingTurn.streamingThinking || "") + String(p.delta || "");
        const liveEl = document.getElementById("inspector-live-thinking");
        if (liveEl) { liveEl.textContent = pendingTurn.streamingThinking; liveEl.scrollTop = liveEl.scrollHeight; }
        else if (!had || inspectorOpen) { scheduleStreamRender(); }
      }
      else if (ev === "token") { pendingTurn.streamingText = (pendingTurn.streamingText || "") + String(p.delta || ""); scheduleStreamRender(); }
      else if (ev === "telemetry" && p.context_usage) { lastContextUsage = p.context_usage; }
      else if (ev === "done") { doneSession = p; if (p.context_usage) { lastContextUsage = p.context_usage; } }
    };
    while (true) {
      const step = await reader.read(); if (step.done) { break; }
      buf += decoder.decode(step.value, { stream: true });
      let idx; while ((idx = buf.indexOf("\n\n")) !== -1) { const ch = buf.slice(0, idx); buf = buf.slice(idx + 2); if (ch.trim()) { handle(ch); } }
    }
    if (buf.trim()) { handle(buf); }
    if (doneSession) { currentTurns = (doneSession.turns || []).map(t => Object.assign({}, t, { collapsed: true })); renderChatStream(); await loadRecentChats(); refreshBudget(); }
  } catch (err) { if (!err || err.name !== "AbortError") { pendingTurn.loadingTutor = false; pendingTurn.tutor = { answer: err.message || "Synthesis failed.", cited_titles: [], knowledge_gap_detected: true }; renderChatStream(); } }
  finally { if (activeController === controller) { activeController = null; activeRequestId = null; setLoadingState(false); } }
}
async function refreshContextUsage() {
  if (!currentChatId) { lastContextUsage = null; return; }
  try {
    const params = new URLSearchParams({ provider: providerEl.value || "ollama", model: modelEl.value || "qwen3:8b", free_chat: String(freeChatMode) });
    const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/context?" + params.toString());
    if (res.ok) { const d = await res.json(); lastContextUsage = d.context_usage || null; activeAttachedNotes = d.attached_notes || []; renderChatStream(); }
  } catch (_e) {}
}
async function runCompactContext() {
  if (!currentChatId) { return; }
  const btn = document.getElementById("ctx-compact-btn"); if (btn) { btn.disabled = true; btn.textContent = "Compressing…"; }
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/compact", { method: "POST", headers, body: JSON.stringify({ free_chat: freeChatMode, provider: providerEl.value, model: modelEl.value, api_key: apiKey || null }) });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.detail || "Could not compress context."); }
    lastContextUsage = data.context_usage || lastContextUsage;
    showToast("Context compressed — now at " + (lastContextUsage ? lastContextUsage.percent + "%" : "lower usage") + " while preserving key facts.");
    renderChatStream();
  } catch (err) { showToast(err.message || "Compression failed."); }
  finally { if (btn) { btn.disabled = false; btn.innerHTML = COMPRESS_SVG + "<span>Compress Context</span>"; } }
}
async function runClearContext() {
  if (!currentChatId) { return; }
  const res = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/clear-context", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ free_chat: freeChatMode, provider: providerEl.value, model: modelEl.value }) });
  if (res.ok) { const d = await res.json(); lastContextUsage = d.context_usage || null; showToast("Context memory cleared — visible messages remain, next reply starts fresh."); renderChatStream(); }
}
async function exportPdfRequest(payload, filenameFallback) {
  try {
    showToast("Generating PDF…", 10000);
    const res = await areaFetch("/api/export/pdf", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "PDF export failed."); }
    const blob = await res.blob(), url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = (filenameFallback || "realm-export") + ".pdf"; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
    showToast("PDF exported.");
  } catch (err) { showToast(err.message || "Could not export PDF."); }
}
function exportTurnPdf(tIdx) {
  const turn = currentTurns[tIdx]; if (!turn || !turn.tutor) { return; }
  const title = turn.format_name || turn.query.slice(0, 60) || "REALM Output";
  if (currentChatId && turn.created_at) { exportPdfRequest({ chat_id: currentChatId, turn_index: tIdx, free_chat: freeChatMode }, chatSlug(title)); }
  else { exportPdfRequest({ title: title, markdown: turn.tutor.answer, citations: turn.tutor.cited_titles || [] }, chatSlug(title)); }
}
function exportFullChatPdf() { if (currentChatId) { exportPdfRequest({ chat_id: currentChatId, free_chat: freeChatMode }, chatSlug((currentTurns[0] && currentTurns[0].query) || "conversation")); } }
async function saveTurnToLibrary(tIdx) {
  const turn = currentTurns[tIdx]; if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  const baseTitle = turn.format_name || turn.query.slice(0, 50) || "synthesized-note", fname = chatSlug(baseTitle) + "-" + Date.now().toString(36).slice(-4) + ".md";
  const md = "# " + baseTitle + "\nTags: synthesis\n\n" + turn.tutor.answer + "\n";
  const res = await areaFetch("/api/upload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: fname, content: md, tags: "synthesis" }) });
  const data = await res.json();
  if (!res.ok) { showToast(data.detail || "Could not save to Library."); return; }
  applyWorkspacePayload(data); await loadGuidesCatalog(null);
  showToast("Saved “" + baseTitle + "” into your Library!");
}
function setInspectorOpen(open) {
  inspectorOpen = Boolean(open);
  syncInspectorSidebar();
  if (inspectorOpen) { refreshContextUsage(); }
}
function syncInspectorSidebar() {
  const toggleBtn = document.getElementById("inspector-toggle-btn"), aside = document.getElementById("inspector-sidebar"), body = document.getElementById("inspector-sidebar-body");
  const graphVisible = document.getElementById("graph-view") && !document.getElementById("graph-view").classList.contains("hidden");
  const hasChat = Boolean(currentChatId && (currentTurns.length || activeAttachedNotes.length) && isActiveView && !graphVisible);
  if (toggleBtn) {
    toggleBtn.hidden = !hasChat;
    toggleBtn.setAttribute("aria-expanded", String(Boolean(hasChat && inspectorOpen)));
    toggleBtn.classList.toggle("text-[#4BB8E8]", Boolean(hasChat && inspectorOpen));
  }
  if (!aside || !body) { return; }
  const show = Boolean(hasChat && inspectorOpen);
  aside.hidden = !show;
  if (!show) { return; }
  const ctx = lastContextUsage || { used_tokens: 0, max_tokens: 32768, percent: 0, summary_tokens: 0, history_tokens: 0, notes_tokens: 0, rag_tokens: 0, is_compacted: false };
  const pct = Math.min(100, Number(ctx.percent || 0)), pctLabel = pct > 0 && pct < 1 ? "<1%" : (Math.round(pct) + "%");
  const barColor = pct >= 88 ? "#EF4444" : (pct >= 70 ? "#F59E0B" : "#4BB8E8");
  const noteChips = activeAttachedNotes.map((n, i) => "<span class='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#4BB8E8]/12 border border-[#4BB8E8]/30 text-xs text-[#EEF2F8]'><span class='truncate max-w-[11rem]'>" + escapeHtml(n.name) + "</span><button type='button' data-detach-note='" + i + "' aria-label='Remove attachment' class='text-[#A0B0C8] hover:text-[#EF4444]'>✕</button></span>").join("");
  const notesSection = noteChips ? ("<div class='flex flex-col gap-2'><span class='font-mono uppercase tracking-wider text-[11px] text-[#738196]'>Attached in Context</span><div class='flex flex-wrap gap-1.5'>" + noteChips + "</div></div>") : "";
  const attachVaultRow = freeChatMode ? ("<div class='flex flex-col gap-1.5 pt-2 border-t border-white/10'><span class='text-[11px] font-mono uppercase tracking-wider text-[#738196]'>Connect Knowledge Area</span><div class='flex items-center gap-2'><select id='inspector-vault-select' class='flex-1 min-w-0 rounded-lg bg-[#04060F] border border-white/15 px-2.5 py-1.5 text-xs text-[#EEF2F8]'>" + knowledgeAreas.map(a => "<option value='" + escapeHtml(a.name) + "'>" + escapeHtml(areaTitle(a)) + "</option>").join("") + "</select><button id='inspector-attach-vault-btn' type='button' class='px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-xs text-[#4BB8E8] hover:bg-[#4BB8E8]/25 shrink-0'>Connect</button></div></div>") : "";
  const thinkingBlocks = currentTurns.map(function (t, i) {
    const txt = (t.streamingThinking || t.thinking || "").trim();
    if (!txt) { return ""; }
    const live = Boolean(t.loadingTutor && t.streamingThinking);
    return "<details" + (live || i === currentTurns.length - 1 ? " open" : "") + " class='rounded-xl bg-[#04060F] border border-white/10 p-2.5'><summary class='cursor-pointer font-mono text-[11px] text-[#A0B0C8] hover:text-[#EEF2F8] select-none'>Turn #" + (i + 1) + (live ? " · Thinking live…" : " · " + Math.max(1, Math.round(txt.length / 4)) + " tok") + "</summary><pre" + (live ? " id='inspector-live-thinking'" : "") + " class='mt-2 whitespace-pre-wrap font-mono text-[11px] text-[#A0B0C8] leading-relaxed max-h-52 overflow-y-auto'>" + escapeHtml(txt) + "</pre></details>";
  }).filter(Boolean).join("");
  const logRows = currentTurns.map(function (t, i) {
    const m = t.telemetry || {};
    if (t.loadingTutor && !m.model) {
      return "<tr class='border-t border-white/[0.06]'><td class='py-1.5 pr-2 font-mono text-[#738196]'>#" + (i + 1) + "</td><td colspan='3' class='py-1.5 font-mono text-[#4BB8E8]'>generating…</td></tr>";
    }
    return "<tr class='border-t border-white/[0.06]'><td class='py-1.5 pr-2 font-mono text-[#738196]'>#" + (i + 1) + "</td><td class='py-1.5 pr-2 truncate max-w-[7rem]'>" + escapeHtml(m.model || "—") + "</td><td class='py-1.5 pr-2 font-mono'>" + (m.prompt_tokens || "—") + "→" + (m.completion_tokens || "—") + "</td><td class='py-1.5 font-mono text-[#738196]'>" + (m.tokens_per_sec ? m.tokens_per_sec + " t/s" : (m.duration_ms ? (m.duration_ms / 1000).toFixed(1) + "s" : "—")) + "</td></tr>";
  }).join("");
  body.innerHTML = "<div class='rounded-xl bg-[#04060F] border border-white/10 p-3 flex flex-col gap-2.5'>"
    + "<div class='flex items-center justify-between gap-2'><span class='font-mono uppercase tracking-wider text-[11px] text-[#738196]'>Context Window</span><span class='font-mono text-[#EEF2F8]'>" + fmtTokens(ctx.used_tokens) + " / " + fmtTokens(ctx.max_tokens) + " (" + pctLabel + ")</span></div>"
    + "<div class='w-full h-2 rounded-full bg-white/10 overflow-hidden'><div class='h-full rounded-full transition-all duration-300' style='width:" + Math.max(ctx.used_tokens ? 3 : 0, pct) + "%;background:" + barColor + "'></div></div>"
    + "<div class='font-mono text-[11px] text-[#738196] leading-relaxed'>System " + fmtTokens(ctx.system_tokens ?? 260) + " · History " + fmtTokens(ctx.history_tokens) + " · Summary " + fmtTokens(ctx.summary_tokens) + " · Notes " + fmtTokens(ctx.notes_tokens) + " · RAG " + fmtTokens(ctx.rag_tokens) + "</div>"
    + "<div class='flex items-center gap-2 pt-1'><button id='ctx-compact-btn' type='button' class='flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-[#4BB8E8] hover:bg-[#4BB8E8]/25 font-medium transition'>" + COMPRESS_SVG + "<span>Compress Context</span></button><button id='ctx-clear-btn' type='button' class='px-2.5 py-1.5 rounded-lg border border-white/15 text-[#A0B0C8] hover:text-[#EEF2F8] transition'>Clear</button></div>"
    + "</div>"
    + notesSection + attachVaultRow
    + "<div class='flex flex-col gap-2 pt-2 border-t border-white/10'><span class='font-mono uppercase tracking-wider text-[11px] text-[#738196]'>Reasoning / Chain of Thought</span>" + (thinkingBlocks || "<span class='text-[#738196]'>No reasoning tokens emitted by this model yet.</span>") + "</div>"
    + (logRows ? "<div class='flex flex-col gap-2 pt-2 border-t border-white/10'><span class='font-mono uppercase tracking-wider text-[11px] text-[#738196]'>Token &amp; Speed Log</span><div class='overflow-x-auto'><table class='w-full text-left text-[11px]'><thead class='text-[#738196] font-mono'><tr><th class='pb-1 pr-2'>#</th><th class='pb-1 pr-2'>Model</th><th class='pb-1 pr-2'>In→Out</th><th class='pb-1'>Speed</th></tr></thead><tbody>" + logRows + "</tbody></table></div></div>" : "");
  const cmpBtn = document.getElementById("ctx-compact-btn"), clrBtn = document.getElementById("ctx-clear-btn"), attVaultBtn = document.getElementById("inspector-attach-vault-btn");
  if (cmpBtn) { cmpBtn.addEventListener("click", runCompactContext); }
  if (clrBtn) { clrBtn.addEventListener("click", runClearContext); }
  if (attVaultBtn) { attVaultBtn.addEventListener("click", () => { const sel = document.getElementById("inspector-vault-select"); attachVaultToActiveChat(sel ? sel.value : ""); }); }
  body.querySelectorAll("[data-detach-note]").forEach(b => b.addEventListener("click", () => detachChatNote(Number(b.dataset.detachNote))));
}
function bindStudioControls() {
  const freeBtn = document.getElementById("free-chat-mode-btn"), sideFmtBtn = document.getElementById("sidebar-formats-btn");
  const closeFmt = document.getElementById("close-format-studio-modal"), tabB = document.getElementById("format-tab-browse"), tabC = document.getElementById("format-tab-custom");
  const customForm = document.getElementById("custom-format-form"), vBtn = document.getElementById("upload-mode-vault-btn"), cBtn = document.getElementById("upload-mode-chat-btn");
  const inspBtn = document.getElementById("inspector-toggle-btn"), closeInsp = document.getElementById("close-inspector-btn");
  if (freeBtn) { freeBtn.addEventListener("click", () => setFreeChatMode(!freeChatMode)); }
  if (sideFmtBtn) { sideFmtBtn.addEventListener("click", () => openFormatStudio("browse")); }
  if (closeFmt) { closeFmt.addEventListener("click", () => document.getElementById("format-studio-modal").close()); }
  if (tabB) { tabB.addEventListener("click", () => setFormatStudioTab("browse")); }
  if (tabC) { tabC.addEventListener("click", () => setFormatStudioTab("custom")); }
  if (customForm) { customForm.addEventListener("submit", saveCustomFormatUI); }
  if (vBtn) { vBtn.addEventListener("click", () => setUploadDestinationMode("vault")); }
  if (cBtn) { cBtn.addEventListener("click", () => setUploadDestinationMode("chat")); }
  if (inspBtn) { inspBtn.addEventListener("click", () => setInspectorOpen(!inspectorOpen)); }
  if (closeInsp) { closeInsp.addEventListener("click", () => setInspectorOpen(false)); }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "i" && currentChatId && currentTurns.length && !document.querySelector("dialog[open]")) { e.preventDefault(); setInspectorOpen(!inspectorOpen); }
    else if (e.key === "Escape" && inspectorOpen && !document.querySelector("dialog[open]")) { setInspectorOpen(false); }
  });
  loadOutputFormats();
}
"""
