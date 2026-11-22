"""Shared client-side DRY utilities: SSE parser, area API wrapper, popovers, dialogs & embed sync."""

SHARED_UI_SCRIPT: str = r"""
const _embedParams = new URLSearchParams(window.location.search || "");
const IS_EMBED = _embedParams.get("embed") === "1";
const EMBED_ROLE = _embedParams.get("role") || "";
const EMBED_VIEW = _embedParams.get("view") || "chat";
const EMBED_CHAT_ID = _embedParams.get("chat_id") || "";
const EMBED_AGENT_ID = _embedParams.get("agent_id") || "";
const EMBED_SUBTAB = _embedParams.get("tab") || "";
const GRIP_DOTS_SVG = "<svg aria-hidden='true' width='13' height='13' viewBox='0 0 24 24' fill='currentColor'><circle cx='9' cy='6' r='1.7'/><circle cx='15' cy='6' r='1.7'/><circle cx='9' cy='12' r='1.7'/><circle cx='15' cy='12' r='1.7'/><circle cx='9' cy='18' r='1.7'/><circle cx='15' cy='18' r='1.7'/></svg>";

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob), link = document.createElement("a");
  link.href = url; link.download = filename || "realm-export";
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
}

async function readSseStream(res, onEvent, isStale) {
  if (!res || !res.body || !res.body.getReader) { throw new Error("Streaming is unavailable in this browser."); }
  const reader = res.body.getReader(), decoder = new TextDecoder();
  let buf = "";
  const dispatch = function (raw) {
    if (isStale && isStale()) { return; }
    let ev = "message";
    const dataLines = [];
    for (const ln of raw.split(/\r?\n/)) {
      if (ln.startsWith("event:")) { ev = ln.slice(6).trim(); }
      else if (ln.startsWith("data:")) { dataLines.push(ln.slice(5).trim()); }
    }
    if (!dataLines.length) { return; }
    let payload = null;
    try { payload = JSON.parse(dataLines.join("\n")); } catch (_e) { return; }
    if (ev === "message" && payload && typeof payload.event === "string") { ev = payload.event; }
    onEvent(ev, payload);
  };
  while (true) {
    const step = await reader.read();
    if (step.done) { break; }
    if (isStale && isStale()) { try { await reader.cancel(); } catch (_e) {} return false; }
    buf += decoder.decode(step.value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const chunk = buf.slice(0, idx); buf = buf.slice(idx + 2);
      if (chunk.trim()) { dispatch(chunk); }
    }
  }
  buf += decoder.decode();
  if (buf.trim()) { dispatch(buf); }
  return !(isStale && isStale());
}

async function jsonAreaApi(path, opts, errFallback, onSuccess) {
  const version = areaVersion, cfg = Object.assign({ headers: {} }, opts || {});
  if (cfg.body && !cfg.headers["Content-Type"]) { cfg.headers["Content-Type"] = "application/json"; }
  try {
    const res = await areaFetch(path, cfg), data = await safeJson(res);
    if (version !== areaVersion) { return null; }
    if (!res.ok) { throw new Error((data && data.detail) || errFallback || "Request failed"); }
    if (onSuccess) { onSuccess(data); }
    return data;
  } catch (err) {
    if (version === areaVersion) { showToast((err && err.message) || errFallback || "Request error", 3500); }
    return null;
  }
}

function positionPopoverNearTrigger(pop, trigger, opts) {
  if (!pop || !trigger) { return; }
  const opt = opts || {}, gap = opt.gap !== undefined ? opt.gap : 6, pad = 8;
  const tr = trigger.getBoundingClientRect();
  const pr = pop.getBoundingClientRect();
  const pw = pr.width || 220, ph = pr.height || 160;
  let left = opt.align === "right" ? (tr.right - pw) : (opt.side === "right" ? (tr.right + gap) : tr.left);
  let top = opt.side === "right" ? tr.top : (tr.bottom + gap);
  if (opt.side === "right" && opt.align === "bottom") { top = tr.bottom - ph; }
  if (top + ph > window.innerHeight - pad) { top = opt.side === "right" ? (window.innerHeight - ph - pad) : (tr.top - ph - gap); }
  if (left + pw > window.innerWidth - pad) { left = window.innerWidth - pw - pad; }
  pop.style.left = Math.max(pad, Math.round(left)) + "px";
  pop.style.top = Math.max(pad, Math.round(top)) + "px";
  pop.style.right = "auto";
  pop.style.bottom = "auto";
}

function bindAnchoredPopover(popId, triggerId, opts) {
  const pop = document.getElementById(popId), trig = document.getElementById(triggerId);
  if (!pop || !trig) { return; }
  pop.addEventListener("toggle", function (e) {
    const open = e.newState === "open";
    trig.setAttribute("aria-expanded", String(open));
    if (open) { positionPopoverNearTrigger(pop, trig, opts); }
  });
}

function bindDialogCloseAttr() {
  document.addEventListener("click", function (e) {
    const btn = e.target && e.target.closest ? e.target.closest("[data-close-dialog], [data-wb-close], [data-m4-close], [data-m5-close]") : null;
    if (!btn) { return; }
    const id = btn.getAttribute("data-close-dialog") || btn.getAttribute("data-wb-close") || btn.getAttribute("data-m4-close") || btn.getAttribute("data-m5-close");
    const dlg = id ? document.getElementById(id) : btn.closest("dialog");
    if (dlg && dlg.open) { if (typeof requestSafeCloseDialog === "function") { requestSafeCloseDialog(dlg); } else { dlg.close(); } }
  });
}

function activateWorkspaceView(viewId, opts) {
  const opt = opts || {};
  if (typeof abortActiveRequest === "function") { abortActiveRequest(); }
  if (typeof stopActiveAudio === "function") { stopActiveAudio(); }
  if (typeof stopGraphSimulation === "function") { stopGraphSimulation(); }
  if (typeof closeWorkBoardView === "function" && viewId !== "work-board-view") { closeWorkBoardView(); }
  if (typeof closeFocusView === "function" && viewId !== "focus-view") { closeFocusView(); }
  if (typeof closeImpactView === "function" && viewId !== "impact-view") { closeImpactView(); }
  if (typeof closeWorkflowsView === "function" && viewId !== "workflows-view") { closeWorkflowsView(); }
  const shell = document.getElementById("workspace-shell"), gv = document.getElementById("graph-view"), fv = document.getElementById("center-file-view");
  if (shell) { shell.classList.toggle("hidden", viewId !== "workspace-shell"); }
  if (gv) { gv.classList.toggle("hidden", viewId !== "graph-view"); }
  if (fv) { fv.hidden = true; }
  const target = document.getElementById(viewId);
  if (target) { target.classList.remove("hidden"); }
  ["sidebar-work-btn", "sidebar-focus-btn", "sidebar-impact-btn"].forEach(function (bid) {
    const el = document.getElementById(bid);
    if (el) { el.classList.toggle("is-active", Boolean(opt.sidebarBtnId && bid === opt.sidebarBtnId)); }
  });
  if (typeof setAmbientDimmed === "function") { setAmbientDimmed(opt.dimAmbient !== false); }
  if (opt.railSection && typeof setActiveRailSection === "function") { setActiveRailSection(opt.railSection, false); }
  if (typeof syncCenterTabbarVisibility === "function") { syncCenterTabbarVisibility(viewId === "workspace-shell"); }
  if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
  if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
}

function notifyParentFrame(msg) {
  if (!IS_EMBED || !window.parent || window.parent === window) { return; }
  try { window.parent.postMessage(Object.assign({ source: "realm-embed", role: EMBED_ROLE }, msg), window.location.origin); } catch (_e) {}
}

function broadcastToEmbedFrames(msg) {
  if (IS_EMBED) { return; }
  ["center-split-frame", "bottom-panel-frame"].forEach(function (fid) {
    const fr = document.getElementById(fid);
    if (fr && fr.contentWindow && fr.dataset.loaded === "1") {
      try { fr.contentWindow.postMessage(Object.assign({ source: "realm-parent" }, msg), window.location.origin); } catch (_e) {}
    }
  });
}

function openEmbeddedView(view, subtab) {
  if (view === "work") { if (typeof openWorkBoardView === "function") { openWorkBoardView(subtab || "kanban"); } }
  else if (view === "focus") { if (typeof openFocusView === "function") { openFocusView(); } }
  else if (view === "impact") { if (typeof openImpactView === "function") { openImpactView(subtab || "roi"); } }
  else if (view === "workflows") { if (typeof openWorkflowsView === "function") { openWorkflowsView(); } }
  else if (view === "library") { if (typeof openLibraryCatalog === "function") { setActiveTag(null); openLibraryCatalog(null); } }
  else if (view === "chat") {
    if (typeof closeWorkBoardView === "function") { closeWorkBoardView(); }
    if (typeof closeFocusView === "function") { closeFocusView(); }
    if (typeof closeImpactView === "function") { closeImpactView(); }
    if (typeof closeWorkflowsView === "function") { closeWorkflowsView(); }
    if (typeof setViewMode === "function") { setViewMode(Boolean(currentTurns && currentTurns.length)); }
  }
}

function bindEmbedMessageBridge() {
  window.addEventListener("message", async function (e) {
    if (e.origin !== window.location.origin || !e.data || typeof e.data !== "object") { return; }
    const msg = e.data;
    if (IS_EMBED && msg.source === "realm-parent") {
      if (msg.type === "realm:sync-theme") {
        if (typeof msg.syncAgentPalette === "boolean" && typeof syncAgentPalette !== "undefined") { syncAgentPalette = msg.syncAgentPalette; }
        if (msg.mode && typeof workspaceConfig === "object" && workspaceConfig) { workspaceConfig.theme_mode = msg.mode; }
        if (msg.mode && typeof applyThemeTokens === "function") {
          const ownAg = EMBED_ROLE === "split-chat" && typeof syncAgentPalette !== "undefined" && syncAgentPalette && typeof activeAgentObj === "function" ? activeAgentObj() : null;
          const ownPal = ownAg && typeof paletteColorsFor === "function" ? paletteColorsFor(ownAg.palette) : null;
          applyThemeTokens(msg.mode, ownPal ? ownPal.accent : msg.accent, ownPal ? ownPal.glow : msg.glow, false);
        }
        if (msg.lang && typeof applyLanguage === "function") { applyLanguage(msg.lang, false); }
        if (msg.comfort && typeof applyReadingComfort === "function") { applyReadingComfort(msg.comfort); }
      } else if (msg.type === "realm:sync-area") {
        if (typeof loadWorkspace === "function") {
          await loadWorkspace();
          await Promise.all([loadRecentChats(), loadGuidesCatalog(null), loadModels(), typeof loadWorkBoardSummary === "function" ? loadWorkBoardSummary(true) : Promise.resolve(), typeof loadFocusSummary === "function" ? loadFocusSummary() : Promise.resolve(), typeof loadImpactSummary === "function" ? loadImpactSummary() : Promise.resolve(), typeof loadWorkflowsSummary === "function" ? loadWorkflowsSummary() : Promise.resolve()]);
          if (EMBED_ROLE === "bottom-panel") { openEmbeddedView(window._activeEmbedView || EMBED_VIEW, EMBED_SUBTAB); }
        }
      } else if (msg.type === "realm:open-view") {
        window._activeEmbedView = msg.view || "work";
        openEmbeddedView(window._activeEmbedView, msg.tab || "");
      } else if (msg.type === "realm:load-chat") {
        if (msg.agentId) { window._embedRequestedAgentId = msg.agentId; }
        if (msg.chatId) { if (typeof openSavedChat === "function") { await openSavedChat(msg.chatId); } }
        else if (typeof resetHome === "function") { resetHome(); }
        if (msg.agentId && typeof selectAgentUI === "function") { await selectAgentUI(msg.agentId); }
        if (msg.draft && queryEl) { queryEl.value = msg.draft; if (typeof autoResizeQuery === "function") { autoResizeQuery(); } queryEl.focus(); }
      } else if (msg.type === "realm:set-agent") {
        if (msg.agentId) { window._embedRequestedAgentId = msg.agentId; }
        if (msg.agentId && typeof selectAgentUI === "function") { await selectAgentUI(msg.agentId); }
      }
    } else if (!IS_EMBED && msg.source === "realm-embed") {
      if (msg.type === "realm:chat-state" && typeof handleSplitFrameChatState === "function") {
        handleSplitFrameChatState(msg);
      } else if (msg.type === "realm:work-updated") {
        if (msg.kind === "work" && typeof loadWorkBoardSummary === "function") { loadWorkBoardSummary(true); }
        else if (msg.kind === "focus" && typeof loadFocusSummary === "function") { loadFocusSummary(); }
        else if (msg.kind === "impact" && typeof loadImpactSummary === "function") { loadImpactSummary(); }
        else if (msg.kind === "workflows" && typeof loadWorkflowsSummary === "function") { loadWorkflowsSummary(); }
      } else if (msg.type === "realm:parent-action") {
        if (msg.action === "open-chat" && msg.chatId && typeof openSavedChat === "function") { openSavedChat(msg.chatId); }
        else if (msg.action === "ask-task" && msg.task && typeof sendTaskToSplitChat === "function") { sendTaskToSplitChat(msg.task); }
      }
    }
  });
}

async function bootstrapEmbeddedPane() {
  if (!IS_EMBED) { return; }
  window._activeEmbedView = EMBED_VIEW;
  if (EMBED_VIEW && EMBED_VIEW !== "chat") {
    openEmbeddedView(EMBED_VIEW, EMBED_SUBTAB);
  } else {
    if (typeof loadAgentTeam === "function" && (!agentTeam || !agentTeam.length)) { await loadAgentTeam(); }
    if (EMBED_CHAT_ID && typeof openSavedChat === "function") { await openSavedChat(EMBED_CHAT_ID); }
    const targetAg = window._embedRequestedAgentId || EMBED_AGENT_ID;
    if (targetAg && typeof selectAgentUI === "function") { await selectAgentUI(targetAg); }
  }
  notifyParentFrame({ type: "realm:embed-ready", view: EMBED_VIEW });
}
"""
