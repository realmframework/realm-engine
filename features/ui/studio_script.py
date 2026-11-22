"""Format & Synthesis Studio, OpenCode Context Meter/Compaction, Inspector, Free Chat & PDF Export."""

STUDIO_SCRIPT: str = r"""
let freeChatMode = false, pinnedFormatId = null, availableFormats = [], lastContextUsage = null, activeAttachedNotes = [], inspectorOpen = false, uploadDestinationMode = "vault", contextUsageOp = 0;
const FORMAT_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 12h6m-6 4h4'/></svg>";
const COMPRESS_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M4 14h6v6M20 10h-6V4m0 6 7-7M3 21l7-7'/></svg>";
function pinnedFormatObj() { return availableFormats.find(f => f.id === pinnedFormatId) || null; }
function fmtTokens(n) { const v = Number(n || 0); return v >= 1000 ? (v / 1000).toFixed(1) + "k" : String(v); }
function syncFreeChatUI() {
  const btn = document.getElementById("free-chat-mode-btn"), pill = document.getElementById("free-chat-pill");
  if (btn) { btn.setAttribute("aria-pressed", String(freeChatMode)); btn.classList.toggle("border-[#4BB8E8]", freeChatMode); }
  if (pill) { pill.textContent = freeChatMode ? "ON" : "OFF"; pill.className = "text-2xs font-mono " + (freeChatMode ? "text-[#38D399]" : "text-[#738196]"); }
  if (freeChatMode) {
    const title = document.getElementById("brand-title"), dot = document.getElementById("workspace-color-dot");
    if (title) { title.textContent = t("free_chat_short"); title.style.fontSize = ""; }
    if (dot) { dot.innerHTML = "<span class='w-2.5 h-2.5 rounded-full border-2 border-[#4BB8E8] shrink-0'></span>"; }
  }
}
async function setFreeChatMode(on) {
  const next = Boolean(on);
  if (!next && !knowledgeAreas.length) { freeChatMode = true; syncFreeChatUI(); closeWorkspaceMenu(); showToast(t("free_chat_need_ws")); return; }
  if (next === freeChatMode) { closeWorkspaceMenu(); return; }
  freeChatMode = next; closeWorkspaceMenu();
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation(); resetHome();
  activeAttachedNotes = []; lastContextUsage = null; if (typeof renderAttachedChips === "function") { renderAttachedChips(); }
  if (freeChatMode) { syncFreeChatUI(); showToast(t("toast_free_chat_on")); }
  else { renderKnowledgeAreas(); }
  await loadRecentChats();
}
function setUploadDestinationMode(mode) {
  const noWs = typeof knowledgeAreas !== "undefined" && !knowledgeAreas.length;
  uploadDestinationMode = (mode === "chat" || noWs) ? "chat" : "vault";
  const vBtn = document.getElementById("upload-mode-vault-btn"), cBtn = document.getElementById("upload-mode-chat-btn");
  const confirmBtn = document.getElementById("confirm-upload-btn"), subRow = document.getElementById("upload-subfolder") && document.getElementById("upload-subfolder").closest(".flex.flex-col");
  const isChat = uploadDestinationMode === "chat";
  if (vBtn) { vBtn.disabled = noWs; vBtn.setAttribute("aria-pressed", String(!isChat)); vBtn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition disabled:opacity-40 disabled:cursor-not-allowed " + (!isChat ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (cBtn) { cBtn.setAttribute("aria-pressed", String(isChat)); cBtn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (isChat ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (confirmBtn) { confirmBtn.textContent = isChat ? t("up_confirm_chat") : t("up_confirm_lib"); }
  if (subRow) { subRow.hidden = isChat; }
}
async function attachFilesToCurrentChat(files) {
  const statusEl = document.getElementById("upload-status"), btn = document.getElementById("confirm-upload-btn");
  if (!files || !files.length) { if (statusEl) { statusEl.textContent = "Select one or more files first."; } return; }
  if (!currentChatId) { currentChatId = newChatId(); }
  const version = areaVersion, chatAtStart = currentChatId;
  if (btn) { btn.disabled = true; }
  if (statusEl) { statusEl.textContent = "Extracting & attaching to chat…"; }
  try {
    const fd = new FormData(); for (const f of files) { fd.append("files", f); } fd.append("free_chat", String(freeChatMode));
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/attach", { method: "POST", body: fd });
    const data = await safeJson(res);
    if (version !== areaVersion || currentChatId !== chatAtStart) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not attach file to chat."); }
    activeAttachedNotes = data.attached_notes || []; if (data.context_usage) { lastContextUsage = data.context_usage; }
    uploadModal.close(); stageUploadFiles([]); document.getElementById("upload-file-input").value = "";
    if (typeof renderAttachedChips === "function") { renderAttachedChips(); }
    showToast(files.length === 1 ? t("toast_attached_1") : t("toast_attached_n", { n: files.length }));
    if (currentTurns.length) { renderChatStream(); } else if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
  } catch (err) { if (statusEl && version === areaVersion) { statusEl.textContent = err.message || "Attachment failed."; } }
  finally { if (btn) { btn.disabled = false; } }
}
async function detachChatNote(idx) {
  if (!currentChatId) { return; }
  const version = areaVersion, chatAtStart = currentChatId;
  try {
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/attach/" + idx + "?free_chat=" + String(freeChatMode), { method: "DELETE" });
    if (res.ok && version === areaVersion && currentChatId === chatAtStart) {
      const d = await safeJson(res); activeAttachedNotes = d.attached_notes || []; lastContextUsage = d.context_usage || lastContextUsage;
      if (typeof renderAttachedChips === "function") { renderAttachedChips(); }
      if (currentTurns.length) { renderChatStream(); }
      else if (!activeAttachedNotes.length && isActiveView) { resetHome(); }
      else if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
    }
  } catch (_e) {}
}
async function attachVaultToActiveChat(areaName) {
  if (!currentChatId || !freeChatMode) { return; }
  const version = areaVersion, chatAtStart = currentChatId;
  try {
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/attach-vault", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ area: areaName || activeKnowledgeArea }) });
    const data = await safeJson(res);
    if (version !== areaVersion || currentChatId !== chatAtStart) { return; }
    if (!res.ok) { showToast(data.detail || t("err_connect_ws")); return; }
    freeChatMode = false;
    if (data.area && data.area !== activeKnowledgeArea) {
      const wsRes = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { knowledge_dir: data.area, active_dirs: [data.area] })) });
      if (wsRes.ok && version === areaVersion) { activeKnowledgeArea = null; applyWorkspacePayload(await safeJson(wsRes)); }
    } else { renderKnowledgeAreas(); }
    syncFreeChatUI(); await loadRecentChats(); renderChatStream();
    showToast(t("toast_connected_ws", { name: areaTitle(data.area) }));
  } catch (err) { showToast(err.message || t("err_connect_ws")); }
}
async function loadOutputFormats() {
  try { const res = await fetch("/api/formats"); if (res.ok) { const d = await safeJson(res); availableFormats = Array.isArray(d.formats) ? d.formats : []; } } catch (_e) {}
}
function setFormatStudioTab(tab) {
  const isCustom = tab === "custom", bBtn = document.getElementById("format-tab-browse"), cBtn = document.getElementById("format-tab-custom");
  const bPane = document.getElementById("format-browse-pane"), cForm = document.getElementById("custom-format-form");
  if (bBtn) { bBtn.setAttribute("aria-selected", String(!isCustom)); bBtn.tabIndex = isCustom ? -1 : 0; bBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (!isCustom ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (cBtn) { cBtn.setAttribute("aria-selected", String(isCustom)); cBtn.tabIndex = isCustom ? 0 : -1; cBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (isCustom ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (bPane) { bPane.hidden = isCustom; }
  if (cForm) { cForm.hidden = !isCustom; }
}
function renderFormatStudio() {
  const grid = document.getElementById("format-cards-grid"), pinInd = document.getElementById("format-pinned-indicator"), sideBadge = document.getElementById("sidebar-format-badge");
  const pinned = pinnedFormatObj(), canSynth = Boolean(currentChatId && (currentTurns.length || activeAttachedNotes.length));
  if (pinInd) { pinInd.textContent = pinned ? t("fmt_pinned", { name: pinned.name }) : t("fmt_none_pinned"); }
  if (sideBadge) { sideBadge.textContent = pinned ? t("fmt_badge_pinned") : t("fmt_badge_studio"); sideBadge.className = "text-xs font-mono " + (pinned ? "text-[#4BB8E8]" : "text-[#738196]"); }
  if (!grid) { return; }
  grid.innerHTML = availableFormats.map(function (f) {
    const isPin = f.id === pinnedFormatId;
    const secs = (f.sections || []).slice(0, 4).map(s => "<span class='px-2 py-0.5 rounded bg-white/[0.04] text-xs text-[#A0B0C8] truncate max-w-full'>" + escapeHtml(s) + "</span>").join("");
    const delBtn = !f.builtin ? "<button type='button' data-del-format='" + escapeHtml(f.id) + "' title='Delete custom format' class='text-[#738196] hover:text-[#EF4444] text-xs px-1'>✕</button>" : "";
    return "<article class='rounded-xl bg-[#04060F] border " + (isPin ? "border-[#4BB8E8]" : "border-white/10") + " p-3.5 flex flex-col gap-2.5'>"
      + "<div class='flex items-start justify-between gap-2'><div class='min-w-0'><span class='text-2xs font-mono uppercase tracking-wider text-[#4BB8E8]'>" + escapeHtml(f.category || "Format") + "</span><h3 class='text-sm font-semibold text-[#EEF2F8] mt-0.5'>" + escapeHtml(f.name) + "</h3></div>" + delBtn + "</div>"
      + (f.description ? "<p class='text-xs text-[#A0B0C8] leading-relaxed'>" + escapeHtml(f.description) + "</p>" : "")
      + "<div class='flex flex-wrap gap-1'>" + secs + ((f.sections || []).length > 4 ? "<span class='text-xs text-[#738196] px-1'>" + escapeHtml(t("fmt_more", { n: f.sections.length - 4 })) + "</span>" : "") + "</div>"
      + "<div class='flex items-center gap-2 mt-auto pt-2 border-t border-white/[0.06]'>"
      + "<button type='button' data-synth-format='" + escapeHtml(f.id) + "'" + (canSynth ? "" : " disabled title='Start a chat or attach a note first'") + " class='flex-1 px-3 py-1.5 rounded-lg bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 disabled:opacity-35 disabled:cursor-not-allowed transition'>" + escapeHtml(t("fmt_synth_btn")) + "</button>"
      + "<button type='button' data-pin-format='" + escapeHtml(f.id) + "' class='px-2.5 py-1.5 rounded-lg border " + (isPin ? "border-[#4BB8E8] text-[#4BB8E8] bg-[#4BB8E8]/10" : "border-white/15 text-[#A0B0C8] hover:text-[#EEF2F8]") + " text-xs transition'>" + escapeHtml(isPin ? t("fmt_unpin") : t("fmt_pin")) + "</button>"
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
  showToast(p ? t("toast_pinned_fmt", { name: p.name }) : t("toast_unpinned_fmt"));
}
async function saveCustomFormatUI(event) {
  event.preventDefault();
  const status = document.getElementById("custom-fmt-status");
  const payload = { name: document.getElementById("custom-fmt-name").value.trim(), category: document.getElementById("custom-fmt-category").value.trim() || "Custom", description: document.getElementById("custom-fmt-desc").value.trim(), sections: document.getElementById("custom-fmt-sections").value.trim(), instructions: document.getElementById("custom-fmt-rules").value.trim() };
  try {
    const res = await fetch("/api/formats", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || "Could not save format."); }
    availableFormats = data.formats || availableFormats;
    document.getElementById("custom-format-form").reset();
    if (status) { status.textContent = "Saved custom format “" + data.format.name + "”."; }
    setFormatStudioTab("browse"); renderFormatStudio();
  } catch (err) { if (status) { status.textContent = err.message; } }
}
async function deleteCustomFormatUI(fmtId) {
  if (!await confirmDeletion(t("cf_del_fmt_t"), t("cf_del_fmt_m"), t("delete_btn"))) { return; }
  try {
    const res = await fetch("/api/formats/" + encodeURIComponent(fmtId), { method: "DELETE" });
    if (res.ok) { const d = await safeJson(res); availableFormats = d.formats || []; if (pinnedFormatId === fmtId) { pinnedFormatId = null; } renderFormatStudio(); }
  } catch (_e) {}
}
async function runFormatSynthesis(formatId) {
  const fmt = availableFormats.find(f => f.id === formatId);
  if (!fmt || !currentChatId) { return; }
  const extra = (document.getElementById("format-extra-focus") && document.getElementById("format-extra-focus").value.trim()) || "";
  const modal = document.getElementById("format-studio-modal"); if (modal && modal.open) { modal.close(); }
  abortActiveRequest();
  const version = areaVersion, chatAtStart = currentChatId;
  const controller = new AbortController(), reqId = "req-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  activeController = controller; activeRequestId = reqId;
  const stale = () => controller.signal.aborted || version !== areaVersion || currentChatId !== chatAtStart;
  const pendingTurn = { query: "Synthesize as " + fmt.name + (extra ? " — " + extra : ""), ask_tutor: true, loadingTutor: true, streamingText: "", streamingThinking: "", format_name: fmt.name, agent_id: (typeof activeAgentId !== "undefined" && activeAgentId) || "saga", agent_name: activeAgentName(), tutor: null, results: [], collapsed: true };
  currentTurns.push(pendingTurn); setViewMode(true); setLoadingState(true); renderChatStream();
  const synthEl = document.getElementById("turn-" + (currentTurns.length - 1));
  if (synthEl) { scrollIntoViewAsync(synthEl, { behavior: "smooth", block: "start" }); }
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json", "x-request-id": reqId }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/synthesize", { method: "POST", headers, signal: controller.signal, body: JSON.stringify({ format_id: formatId, extra_instruction: extra, free_chat: freeChatMode, agent_id: (typeof activeAgentId !== "undefined" && activeAgentId) || "saga", provider: providerEl.value, model: modelEl.value.trim() || null, api_key: apiKey || null }) });
    if (res.status === 499 || stale()) { return; }
    if (!res.ok) { const e = await safeJson(res); throw new Error(e.detail || "Synthesis failed."); }
    let doneSession = null, stoppedFlag = false;
    const completed = await readSseStream(res, function (ev, p) {
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
      else if (ev === "stopped") { stoppedFlag = true; pendingTurn.loadingTutor = false; pendingTurn.stopped = true; const partial = String((p && p.partial) || pendingTurn.streamingText || "").trim(); if (partial) { pendingTurn.tutor = { answer: partial, cited_titles: [], knowledge_gap_detected: false }; } renderChatStream(); }
      else if (ev === "error") { throw new Error((p && p.detail) || "Synthesis failed."); }
    }, stale);
    if (!completed || stale()) { return; }
    if (doneSession) { currentTurns = (doneSession.turns || []).map(t => Object.assign({}, t, { collapsed: true })); renderChatStream(); await loadRecentChats(); refreshBudget(); }
    else if (!stoppedFlag) { pendingTurn.loadingTutor = false; const partial = String(pendingTurn.streamingText || "").trim(); if (!partial) { pendingTurn.isError = true; } pendingTurn.tutor = { answer: partial || "Synthesis stream ended unexpectedly.", cited_titles: [], knowledge_gap_detected: false }; renderChatStream(); }
  } catch (err) { if ((!err || err.name !== "AbortError") && !stale()) { pendingTurn.loadingTutor = false; pendingTurn.isError = true; pendingTurn.tutor = { answer: err.message || "Synthesis failed.", cited_titles: [], knowledge_gap_detected: false }; renderChatStream(); refreshBudget(); } }
  finally { if (activeController === controller) { activeController = null; activeRequestId = null; setLoadingState(false); } }
}
async function refreshContextUsage() {
  if (!currentChatId) { lastContextUsage = null; return; }
  const version = areaVersion, chatAtStart = currentChatId, op = ++contextUsageOp;
  try {
    const params = new URLSearchParams({ provider: providerEl.value || "ollama", model: modelEl.value || "qwen3:8b", free_chat: String(freeChatMode), agent_id: (typeof activeAgentId !== "undefined" && activeAgentId) || "" });
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/context?" + params.toString());
    if (res.ok && op === contextUsageOp && version === areaVersion && currentChatId === chatAtStart) {
      const d = await safeJson(res), prevNotes = JSON.stringify(activeAttachedNotes);
      if (op !== contextUsageOp || version !== areaVersion || currentChatId !== chatAtStart) { return; }
      lastContextUsage = d.context_usage || null; activeAttachedNotes = d.attached_notes || [];
      if (JSON.stringify(activeAttachedNotes) !== prevNotes) { renderChatStream(); } else { syncInspectorSidebar(); }
    }
  } catch (_e) {}
}
async function runCompactContext() {
  if (!currentChatId) { return; }
  const version = areaVersion, chatAtStart = currentChatId, btn = document.getElementById("ctx-compact-btn");
  if (btn) { btn.disabled = true; btn.textContent = "Compressing…"; }
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/compact", { method: "POST", headers, body: JSON.stringify({ free_chat: freeChatMode, provider: providerEl.value, model: modelEl.value, api_key: apiKey || null }) });
    const data = await safeJson(res);
    if (version !== areaVersion || currentChatId !== chatAtStart) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not compress context."); }
    lastContextUsage = data.context_usage || lastContextUsage;
    showToast(t("toast_ctx_compressed", { pct: lastContextUsage ? lastContextUsage.percent + "%" : "—" }));
    renderChatStream();
  } catch (err) { if (version === areaVersion) { showToast(err.message || t("err_compress")); } }
  finally { if (btn && btn.isConnected) { btn.disabled = false; btn.innerHTML = COMPRESS_SVG + "<span>" + escapeHtml(t("insp_compress")) + "</span>"; } }
}
async function runClearContext() {
  if (!currentChatId) { return; }
  const version = areaVersion, chatAtStart = currentChatId;
  try {
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/clear-context", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ free_chat: freeChatMode, provider: providerEl.value, model: modelEl.value }) });
    if (res.ok && version === areaVersion && currentChatId === chatAtStart) { const d = await safeJson(res); lastContextUsage = d.context_usage || null; showToast(t("toast_ctx_cleared")); renderChatStream(); }
  } catch (_e) {}
}
async function exportPdfRequest(payload, filenameFallback) {
  try {
    showToast(t("toast_exp_pdf_gen"), 10000);
    const res = await areaFetch("/api/export/pdf", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!res.ok) { const e = await safeJson(res); throw new Error(e.detail || t("err_export_pdf")); }
    downloadBlob(await res.blob(), (filenameFallback || "realm-export") + ".pdf");
    showToast(t("toast_exp_pdf_ok"));
  } catch (err) { showToast(err.message || t("err_export_pdf")); }
}
function exportTurnPdf(tIdx) {
  const turn = currentTurns[tIdx]; if (!turn || !turn.tutor) { return; }
  const title = turn.format_name || turn.query.slice(0, 60) || "REALM Output";
  if (currentChatId && turn.created_at) { exportPdfRequest({ chat_id: currentChatId, turn_index: tIdx, free_chat: freeChatMode }, chatSlug(title)); }
  else { exportPdfRequest({ title: title, markdown: turn.tutor.answer, citations: turn.tutor.cited_titles || [] }, chatSlug(title)); }
}
function exportFullChatPdf() { if (currentChatId) { exportPdfRequest({ chat_id: currentChatId, free_chat: freeChatMode }, chatSlug((currentTurns[0] && currentTurns[0].query) || "conversation")); } }
function setInspectorOpen(open, restoreFocus) {
  inspectorOpen = Boolean(open);
  if (typeof setRightSidebarOpen === "function") { setRightSidebarOpen(inspectorOpen, inspectorOpen ? "inspector" : undefined); }
  else { syncInspectorSidebar(); }
  if (inspectorOpen) { refreshContextUsage(); const cb = document.getElementById("close-inspector-btn"); if (cb) { cb.focus({ preventScroll: true }); } }
  else if (restoreFocus) { const tb = document.getElementById("inspector-toggle-btn"); if (tb && !tb.hidden) { tb.focus({ preventScroll: true }); } }
}
function syncInspectorSidebar() {
  const toggleBtn = document.getElementById("inspector-toggle-btn"), aside = document.getElementById("inspector-sidebar"), body = document.getElementById("inspector-sidebar-body");
  const graphVisible = document.getElementById("graph-view") && !document.getElementById("graph-view").classList.contains("hidden");
  const hasChat = Boolean(currentChatId && (currentTurns.length || activeAttachedNotes.length) && isActiveView && !graphVisible);
  const rightOpen = typeof wbLayout !== "undefined" ? Boolean(wbLayout.rightOpen) : inspectorOpen;
  if (toggleBtn) {
    toggleBtn.hidden = !hasChat;
    toggleBtn.setAttribute("aria-expanded", String(Boolean(hasChat && rightOpen && (typeof wbLayout === "undefined" || wbLayout.rightTab === "inspector"))));
    const tokLbl = document.getElementById("inspector-token-label");
    if (tokLbl) { tokLbl.textContent = (lastContextUsage && lastContextUsage.used_tokens > 0) ? fmtTokens(lastContextUsage.used_tokens) : t("insp_tokens_short"); }
  }
  if (!aside || !body) { return; }
  if (typeof wbLayout === "undefined") { aside.hidden = !Boolean(hasChat && inspectorOpen); }
  if (!rightOpen) { return; }
  if (!hasChat) {
    body.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("insp_empty_hint")) + "</div>";
    return;
  }
  const ctx = lastContextUsage || { used_tokens: 0, max_tokens: 32768, percent: 0, summary_tokens: 0, history_tokens: 0, notes_tokens: 0, rag_tokens: 0, is_compacted: false };
  const pct = Math.min(100, Number(ctx.percent || 0)), pctLabel = pct > 0 && pct < 1 ? "<1%" : (Math.round(pct) + "%");
  const barColor = pct >= 88 ? "var(--status-danger)" : (pct >= 70 ? "var(--status-warn)" : "var(--accent)");
  const noteChips = activeAttachedNotes.map((n, i) => "<span class='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#4BB8E8]/12 border border-[#4BB8E8]/30 text-xs text-[#EEF2F8]'><span class='truncate max-w-[11rem]'>" + escapeHtml(n.name) + "</span><button type='button' data-detach-note='" + i + "' aria-label='Remove attachment' class='text-[#A0B0C8] hover:text-[#EF4444]'>✕</button></span>").join("");
  const notesSection = noteChips ? ("<div class='flex flex-col gap-2'><span class='font-mono uppercase tracking-wider text-xs text-[#738196]'>" + escapeHtml(t("insp_attached")) + "</span><div class='flex flex-wrap gap-1.5'>" + noteChips + "</div></div>") : "";
  const attachVaultRow = freeChatMode ? ("<div class='flex flex-col gap-1.5 pt-2 border-t border-white/10'><label for='inspector-vault-select' class='text-xs font-mono uppercase tracking-wider text-[#738196]'>" + escapeHtml(t("insp_connect_area")) + "</label><div class='flex items-center gap-2'><select id='inspector-vault-select' class='flex-1 min-w-0 rounded-lg bg-[#04060F] border border-white/15 px-2.5 py-1.5 text-xs text-[#EEF2F8]'>" + knowledgeAreas.map(a => "<option value='" + escapeHtml(a.name) + "'>" + escapeHtml(areaTitle(a)) + "</option>").join("") + "</select><button id='inspector-attach-vault-btn' type='button' class='px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-xs text-[#4BB8E8] hover:bg-[#4BB8E8]/25 shrink-0'>" + escapeHtml(t("insp_connect_btn")) + "</button></div></div>") : "";
  const thinkingBlocks = currentTurns.map(function (t, i) {
    const txt = (t.streamingThinking || t.thinking || "").trim();
    if (!txt) { return ""; }
    const live = Boolean(t.loadingTutor && t.streamingThinking);
    return "<details" + (live || i === currentTurns.length - 1 ? " open" : "") + " class='rounded-xl bg-[#04060F] border border-white/10 p-2.5'><summary class='cursor-pointer font-mono text-xs text-[#A0B0C8] hover:text-[#EEF2F8] select-none'>Turn #" + (i + 1) + (live ? " · Thinking live…" : " · " + Math.max(1, Math.round(txt.length / 4)) + " tok") + "</summary><pre" + (live ? " id='inspector-live-thinking'" : "") + " class='mt-2 whitespace-pre-wrap font-mono text-xs text-[#A0B0C8] leading-relaxed max-h-52 overflow-y-auto'>" + escapeHtml(txt) + "</pre></details>";
  }).filter(Boolean).join("");
  const logRows = currentTurns.map(function (turnItem, i) {
    const m = turnItem.telemetry || {};
    if (turnItem.loadingTutor && !m.model) {
      return "<tr class='border-t border-white/[0.06]'><td class='py-1.5 pr-2 font-mono text-[#738196]'>#" + (i + 1) + "</td><td colspan='3' class='py-1.5 font-mono text-[#4BB8E8]'>" + escapeHtml(t("insp_generating")) + "</td></tr>";
    }
    return "<tr class='border-t border-white/[0.06]'><td class='py-1.5 pr-2 font-mono text-[#738196]'>#" + (i + 1) + "</td><td class='py-1.5 pr-2 truncate max-w-[7rem]'>" + escapeHtml(m.model || "—") + "</td><td class='py-1.5 pr-2 font-mono'>" + (m.prompt_tokens || "—") + "→" + (m.completion_tokens || "—") + "</td><td class='py-1.5 font-mono text-[#738196]'>" + (m.tokens_per_sec ? m.tokens_per_sec + " t/s" : (m.duration_ms ? (m.duration_ms / 1000).toFixed(1) + "s" : "—")) + "</td></tr>";
  }).join("");
  const agObj = typeof activeAgentObj === "function" ? activeAgentObj() : null;
  const agLabel = (agObj && agObj.name) || activeAgentName();
  const ecoBadge = workspaceConfig && workspaceConfig.eco_mode ? " <span class='px-1.5 py-0.5 rounded bg-[#38D399]/15 text-[#38D399] font-mono text-2xs'>ECO</span>" : "";
  body.innerHTML = "<div class='rounded-xl bg-[#04060F] border border-white/10 p-3 flex flex-col gap-2.5'>"
    + "<div class='flex items-center justify-between gap-2'><span class='font-mono uppercase tracking-wider text-xs text-[#738196]'>" + escapeHtml(t("insp_ctx")) + " · " + escapeHtml(agLabel) + ecoBadge + "</span><span class='font-mono text-[#EEF2F8]'>" + fmtTokens(ctx.used_tokens) + " / " + fmtTokens(ctx.max_tokens) + " (" + pctLabel + ")</span></div>"
    + "<div role='progressbar' aria-valuemin='0' aria-valuemax='100' aria-valuenow='" + Math.round(pct) + "' aria-label='" + escapeHtml(t("insp_ctx")) + "' class='w-full h-2 rounded-full bg-white/10 overflow-hidden'><div class='h-full rounded-full transition-all duration-300' style='width:" + Math.max(ctx.used_tokens ? 3 : 0, pct) + "%;background:" + barColor + "'></div></div>"
    + "<div class='font-mono text-xs text-[#738196] leading-relaxed'>" + escapeHtml(t("insp_sys")) + " " + fmtTokens(ctx.system_tokens ?? 260) + " · " + escapeHtml(t("insp_persona")) + " " + fmtTokens(ctx.persona_tokens ?? 0) + " · " + escapeHtml(t("insp_hist")) + " " + fmtTokens(ctx.history_tokens) + " · " + escapeHtml(t("insp_sum")) + " " + fmtTokens(ctx.summary_tokens) + " · " + escapeHtml(t("insp_notes")) + " " + fmtTokens(ctx.notes_tokens) + " · " + escapeHtml(t("insp_rag")) + " " + fmtTokens(ctx.rag_tokens) + "</div>"
    + "<div class='flex items-center gap-2 pt-1'><button id='ctx-compact-btn' type='button' class='flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-[#4BB8E8] hover:bg-[#4BB8E8]/25 font-medium transition'>" + COMPRESS_SVG + "<span>" + escapeHtml(t("insp_compress")) + "</span></button><button id='ctx-clear-btn' type='button' class='px-2.5 py-1.5 rounded-lg border border-white/15 text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("insp_clear")) + "</button></div>"
    + "</div>"
    + notesSection + attachVaultRow
    + (!freeChatMode ? "<div class='flex flex-col gap-2 pt-2 border-t border-white/10'><span class='font-mono uppercase tracking-wider text-xs text-[#738196]'>" + escapeHtml(t("xray_title")) + "</span><div id='inspector-xray-body' class='flex flex-col gap-2'></div></div>" : "")
    + "<div class='flex flex-col gap-2 pt-2 border-t border-white/10'><span class='font-mono uppercase tracking-wider text-xs text-[#738196]'>" + escapeHtml(t("insp_reasoning")) + "</span>" + (thinkingBlocks || "<span class='text-[#738196]'>" + escapeHtml(t("insp_no_reasoning")) + "</span>") + "</div>"
    + (logRows ? "<div class='flex flex-col gap-2 pt-2 border-t border-white/10'><span class='font-mono uppercase tracking-wider text-xs text-[#738196]'>" + escapeHtml(t("insp_log")) + "</span><div class='overflow-x-auto'><table class='w-full text-left text-xs'><thead class='text-[#738196] font-mono'><tr><th class='pb-1 pr-2'>#</th><th class='pb-1 pr-2'>" + escapeHtml(t("insp_model")) + "</th><th class='pb-1 pr-2'>In→Out</th><th class='pb-1'>" + escapeHtml(t("insp_speed")) + "</th></tr></thead><tbody>" + logRows + "</tbody></table></div></div>" : "");
  const cmpBtn = document.getElementById("ctx-compact-btn"), clrBtn = document.getElementById("ctx-clear-btn"), attVaultBtn = document.getElementById("inspector-attach-vault-btn");
  if (cmpBtn) { cmpBtn.addEventListener("click", runCompactContext); }
  if (clrBtn) { clrBtn.addEventListener("click", runClearContext); }
  if (attVaultBtn) { attVaultBtn.addEventListener("click", () => { const sel = document.getElementById("inspector-vault-select"); attachVaultToActiveChat(sel ? sel.value : ""); }); }
  body.querySelectorAll("[data-detach-note]").forEach(b => b.addEventListener("click", () => detachChatNote(Number(b.dataset.detachNote))));
  if (typeof refreshInspectorXray === "function") { refreshInspectorXray(); }
}
function bindStudioControls() {
  const freeBtn = document.getElementById("free-chat-mode-btn"), sideFmtBtn = document.getElementById("sidebar-formats-btn");
  const closeFmt = document.getElementById("close-format-studio-modal"), tabB = document.getElementById("format-tab-browse"), tabC = document.getElementById("format-tab-custom");
  const customForm = document.getElementById("custom-format-form"), vBtn = document.getElementById("upload-mode-vault-btn"), cBtn = document.getElementById("upload-mode-chat-btn");
  const inspBtn = document.getElementById("inspector-toggle-btn"), closeInsp = document.getElementById("close-inspector-btn");
  if (freeBtn) { freeBtn.addEventListener("click", () => setFreeChatMode(!freeChatMode)); }
  if (sideFmtBtn) { sideFmtBtn.addEventListener("click", () => openFormatStudio("browse")); }
  if (closeFmt) { closeFmt.addEventListener("click", () => document.getElementById("format-studio-modal").close()); }
  if (tabB) { tabB.addEventListener("click", () => setFormatStudioTab("browse")); } if (tabC) { tabC.addEventListener("click", () => setFormatStudioTab("custom")); }
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#format-studio-modal [role='tab']", tab => setFormatStudioTab(tab.id === "format-tab-custom" ? "custom" : "browse")); }
  if (customForm) { customForm.addEventListener("submit", saveCustomFormatUI); }
  if (vBtn) { vBtn.addEventListener("click", () => setUploadDestinationMode("vault")); } if (cBtn) { cBtn.addEventListener("click", () => setUploadDestinationMode("chat")); }
  if (inspBtn) { inspBtn.addEventListener("click", () => setInspectorOpen(!inspectorOpen, true)); }
  if (closeInsp) { closeInsp.addEventListener("click", () => setInspectorOpen(false, true)); }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "i" && currentChatId && currentTurns.length && !document.querySelector("dialog[open]")) { e.preventDefault(); setInspectorOpen(!inspectorOpen, true); }
    else if (e.key === "Escape" && inspectorOpen && !document.querySelector("dialog[open]")) { setInspectorOpen(false, true); }
  });
  loadOutputFormats();
}
"""
