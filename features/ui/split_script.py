"""True-DRY VS Code 4-Zone Workbench controller: Split Chat, Bottom Work Tools & Docked Right Sidebar."""

SPLIT_SCRIPT: str = r"""
const BP_TOOLS = ["terminal", "work", "focus", "impact", "workflows", "library"];
const wbLayout = {
  splitOpen: false, splitRatio: 50,
  bottomOpen: false, bottomMax: false, bottomTool: "terminal", editorHeightPct: 58,
  bottomVisible: { terminal: true, work: true, focus: true, impact: true, workflows: true, library: true },
  rightOpen: false, rightTab: "copilot", rightWidthPx: 348,
  splitAgentId: "lisbeth",
  splitTabs: [{ id: "sp_0", chatId: "", title: "" }],
  activeSplitTabId: "sp_0",
};

function loadBottomToolPrefs() {
  try {
    const raw = safeStorageGet("realm_bp_visible");
    if (!raw) { return; }
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") {
      let anyOn = false;
      BP_TOOLS.forEach(function (k) { wbLayout.bottomVisible[k] = parsed[k] !== false; if (wbLayout.bottomVisible[k]) { anyOn = true; } });
      if (!anyOn) { wbLayout.bottomVisible.work = true; }
    }
  } catch (_e) {}
}

function saveBottomToolPrefs() { safeStorageSet("realm_bp_visible", JSON.stringify(wbLayout.bottomVisible)); }

function applyWorkbenchGrid() {
  const grid = document.getElementById("workbench-grid");
  const centerCol = document.getElementById("workbench-center-col");
  const editorRow = document.getElementById("center-editor-row");
  const spRes = document.getElementById("center-split-resizer"), spPane = document.getElementById("center-split-pane");
  const bpRes = document.getElementById("bottom-panel-resizer"), bpPane = document.getElementById("bottom-panel");
  const rsRes = document.getElementById("right-sidebar-resizer"), rsPane = document.getElementById("inspector-sidebar");
  const narrow = window.matchMedia && window.matchMedia("(max-width: 959px)").matches;
  const splitOn = wbLayout.splitOpen && (typeof wbCenterIsChat === "undefined" || wbCenterIsChat) && !narrow;
  const bottomOn = wbLayout.bottomOpen && !narrow;
  const rightOn = wbLayout.rightOpen;

  if (editorRow) {
    editorRow.classList.toggle("has-split", splitOn);
    editorRow.style.setProperty("--split-a", wbLayout.splitRatio + "%");
  }
  if (spRes) { spRes.hidden = !splitOn; spRes.setAttribute("aria-valuenow", String(Math.round(wbLayout.splitRatio))); }
  if (spPane) { spPane.hidden = !splitOn; }

  if (centerCol) {
    centerCol.classList.toggle("has-bottom", bottomOn);
    centerCol.classList.toggle("is-bottom-max", bottomOn && wbLayout.bottomMax);
    centerCol.style.setProperty("--editor-h", wbLayout.editorHeightPct + "%");
  }
  if (bpRes) { bpRes.hidden = !bottomOn || wbLayout.bottomMax; bpRes.setAttribute("aria-valuenow", String(Math.round(wbLayout.editorHeightPct))); }
  if (bpPane) { bpPane.hidden = !bottomOn; }

  if (grid) {
    grid.classList.toggle("has-right", rightOn && !narrow);
    grid.style.setProperty("--right-w", wbLayout.rightWidthPx + "px");
  }
  if (rsRes) { rsRes.hidden = !rightOn || narrow; rsRes.setAttribute("aria-valuenow", String(Math.round(wbLayout.rightWidthPx))); }
  if (rsPane) { rsPane.hidden = !rightOn; }

  const splitBtn = document.getElementById("center-split-btn");
  const bpBtn = document.getElementById("layout-bottom-btn");
  const rsBtn = document.getElementById("layout-right-btn");
  const maxBtn = document.getElementById("bottom-panel-max-btn");
  if (splitBtn) { splitBtn.setAttribute("aria-pressed", String(splitOn)); }
  if (bpBtn) { bpBtn.setAttribute("aria-pressed", String(bottomOn)); }
  if (rsBtn) { rsBtn.setAttribute("aria-pressed", String(rightOn)); }
  if (maxBtn) {
    maxBtn.setAttribute("aria-pressed", String(wbLayout.bottomMax));
    const lbl = t(wbLayout.bottomMax ? "bp_restore_aria" : "bp_max_aria");
    maxBtn.setAttribute("aria-label", lbl); maxBtn.title = lbl;
    maxBtn.innerHTML = wbLayout.bottomMax
      ? '<svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>'
      : '<svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>';
  }
  if (typeof syncGlobalControlsWidth === "function") { syncGlobalControlsWidth(); }
}

function ensureEmbedFrame(frameId, url, onReadyMsg) {
  const fr = document.getElementById(frameId); if (!fr) { return; }
  if (fr.dataset.loaded === "1" && fr.contentWindow) {
    if (onReadyMsg) { try { fr.contentWindow.postMessage(Object.assign({ source: "realm-parent" }, onReadyMsg), window.location.origin); } catch (_e) {} }
    return;
  }
  fr.dataset.pendingMsg = onReadyMsg ? JSON.stringify(onReadyMsg) : "";
  if (fr.dataset.loading === "1") { return; }
  fr.dataset.loading = "1";
  fr.onload = function () {
    fr.dataset.loaded = "1"; fr.dataset.loading = "0";
    if (fr.dataset.pendingMsg && fr.contentWindow) {
      try { fr.contentWindow.postMessage(Object.assign({ source: "realm-parent" }, JSON.parse(fr.dataset.pendingMsg)), window.location.origin); } catch (_e) {}
      fr.dataset.pendingMsg = "";
    }
  };
  fr.src = url;
}

function syncSplitPaneAccent() {
  const pane = document.getElementById("center-split-pane"); if (!pane) { return; }
  const syncOn = typeof syncAgentPalette === "undefined" || syncAgentPalette;
  const ag = syncOn && typeof agentTeam !== "undefined" && Array.isArray(agentTeam)
    ? agentTeam.find(function (a) { return a.id === wbLayout.splitAgentId; })
    : null;
  const pal = ag && typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette) : null;
  if (pal && pal.accent) {
    pane.style.setProperty("--accent-seed", pal.accent);
    pane.style.setProperty("--accent", pal.accent);
  } else {
    pane.style.removeProperty("--accent-seed");
    pane.style.removeProperty("--accent");
  }
}

function syncSplitSelectors() {
  const centerSel = document.getElementById("center-agent-select");
  if (centerSel && typeof populateAgentSelect === "function") {
    populateAgentSelect(centerSel, typeof activeAgentId !== "undefined" ? activeAgentId : "saga");
  }
  const agSel = document.getElementById("split-agent-select");
  if (agSel && typeof populateAgentSelect === "function") {
    const list = typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length ? agentTeam : [];
    if (list.length && !list.some(function (a) { return a.id === wbLayout.splitAgentId; })) {
      wbLayout.splitAgentId = (list.find(function (a) { return a.id !== (typeof activeAgentId !== "undefined" ? activeAgentId : "saga"); }) || list[0]).id;
    }
    wbLayout.splitAgentId = populateAgentSelect(agSel, wbLayout.splitAgentId);
  }
  syncSplitPaneAccent();
}

function renderSplitChatTabs() {
  if (!wbLayout.splitTabs.length) { wbLayout.splitTabs = [{ id: "sp_" + (++wbTabSeq), chatId: "", title: "" }]; }
  wbLayout.activeSplitTabId = renderChatTabStrip("split-chat-tablist", wbLayout.splitTabs, wbLayout.activeSplitTabId, "sp", activateSplitChatTab, closeSplitChatTab);
}

function activateSplitChatTab(tabId) {
  const tb = wbLayout.splitTabs.find(function (item) { return item.id === tabId; });
  if (!tb) { return; }
  wbLayout.activeSplitTabId = tb.id;
  renderSplitChatTabs();
  ensureEmbedFrame("center-split-frame", "/?embed=1&role=split-chat&view=chat&agent_id=" + encodeURIComponent(wbLayout.splitAgentId) + (tb.chatId ? ("&chat_id=" + encodeURIComponent(tb.chatId)) : ""), { type: "realm:load-chat", chatId: tb.chatId || "", agentId: wbLayout.splitAgentId });
}

function closeSplitChatTab(tabId) {
  wbLayout.splitTabs = wbLayout.splitTabs.filter(function (tb) { return tb.id !== tabId; });
  if (!wbLayout.splitTabs.length) { wbLayout.splitTabs.push({ id: "sp_" + (++wbTabSeq), chatId: "", title: "" }); }
  if (wbLayout.activeSplitTabId === tabId) { activateSplitChatTab(wbLayout.splitTabs[wbLayout.splitTabs.length - 1].id); }
  else { renderSplitChatTabs(); }
}

function openSplitChat(opts) {
  const o = opts || {};
  wbLayout.splitOpen = true;
  syncSplitSelectors();
  if (o.chatId) {
    let tb = wbLayout.splitTabs.find(function (item) { return item.chatId === o.chatId; });
    if (!tb) {
      const cur = wbLayout.splitTabs.find(function (item) { return item.id === wbLayout.activeSplitTabId; });
      const found = Array.isArray(savedChats) ? savedChats.find(function (c) { return c.chat_id === o.chatId; }) : null;
      const title = (found && found.title) || o.title || "";
      if (cur && !cur.chatId) { cur.chatId = o.chatId; cur.title = title; tb = cur; }
      else { tb = { id: "sp_" + (++wbTabSeq), chatId: o.chatId, title: title }; wbLayout.splitTabs.push(tb); }
    }
    wbLayout.activeSplitTabId = tb.id;
  }
  const active = wbLayout.splitTabs.find(function (item) { return item.id === wbLayout.activeSplitTabId; }) || wbLayout.splitTabs[0];
  renderSplitChatTabs();
  applyWorkbenchGrid();
  const qs = "/?embed=1&role=split-chat&view=chat&agent_id=" + encodeURIComponent(wbLayout.splitAgentId) + (active && active.chatId ? ("&chat_id=" + encodeURIComponent(active.chatId)) : "");
  ensureEmbedFrame("center-split-frame", qs, { type: "realm:load-chat", chatId: (active && active.chatId) || "", agentId: wbLayout.splitAgentId, draft: o.draft || "" });
}

function closeSplitChat() { wbLayout.splitOpen = false; applyWorkbenchGrid(); }
function openChatInSplit(chatId) { openSplitChat({ chatId: chatId || "" }); }

function handleSplitFrameChatState(msg) {
  const cur = wbLayout.splitTabs.find(function (tb) { return tb.id === wbLayout.activeSplitTabId; });
  if (cur) {
    if (msg.chatId !== undefined) { cur.chatId = msg.chatId || ""; }
    if (msg.title) { cur.title = msg.title; }
    else if (!cur.chatId) { cur.title = ""; }
    renderSplitChatTabs();
  }
  if (msg.agentId) { wbLayout.splitAgentId = msg.agentId; syncSplitSelectors(); }
  if (msg.refreshChats && typeof loadRecentChats === "function") { loadRecentChats(); }
}

function sendTaskToSplitChat(task) {
  if (!task) { return; }
  if (IS_EMBED) { notifyParentFrame({ type: "realm:parent-action", action: "ask-task", task: task }); return; }
  const ctx = "Task: " + task.title + (task.due_date ? " (due " + task.due_date + ")" : "") + (task.description ? "\nNotes: " + task.description : "") + "\n\nHelp me plan or draft the next steps for this task.";
  openSplitChat({ draft: ctx });
}

function renderBottomPanelTabs() {
  BP_TOOLS.forEach(function (tool) {
    const tab = document.querySelector("[data-bp-tool='" + tool + "']");
    const chk = document.querySelector("[data-bp-vis='" + tool + "']");
    const vis = wbLayout.bottomVisible[tool] !== false;
    if (tab) {
      tab.hidden = !vis;
      const sel = tool === wbLayout.bottomTool;
      tab.setAttribute("aria-selected", String(sel));
      tab.tabIndex = sel ? 0 : -1;
    }
    if (chk) { chk.setAttribute("aria-checked", String(vis)); }
  });
}

function syncBottomPanelContent() {
  const tp = document.getElementById("bottom-terminal-pane"), fr = document.getElementById("bottom-panel-frame"), isTerm = wbLayout.bottomTool === "terminal";
  if (tp) { tp.hidden = !isTerm; }
  if (fr) { fr.hidden = isTerm; }
  if (isTerm) { if (typeof ensureTerminalReady === "function") { ensureTerminalReady(); } }
  else { ensureEmbedFrame("bottom-panel-frame", "/?embed=1&role=bottom-panel&view=" + encodeURIComponent(wbLayout.bottomTool), { type: "realm:open-view", view: wbLayout.bottomTool }); }
}
function setBottomTool(tool) {
  if (!BP_TOOLS.includes(tool)) { return; }
  wbLayout.bottomVisible[tool] = true; wbLayout.bottomTool = tool; saveBottomToolPrefs(); renderBottomPanelTabs();
  if (wbLayout.bottomOpen) { syncBottomPanelContent(); }
  const activeTab = document.querySelector("[data-bp-tool='" + tool + "']");
  if (activeTab && activeTab.scrollIntoView) { activeTab.scrollIntoView({ block: "nearest", inline: "nearest" }); }
}
function openBottomPanel(tool) {
  if (tool && BP_TOOLS.includes(tool)) { wbLayout.bottomTool = tool; wbLayout.bottomVisible[tool] = true; saveBottomToolPrefs(); }
  if (!wbLayout.bottomVisible[wbLayout.bottomTool]) { wbLayout.bottomTool = BP_TOOLS.find(function (k) { return wbLayout.bottomVisible[k]; }) || "terminal"; }
  wbLayout.bottomOpen = true; renderBottomPanelTabs(); applyWorkbenchGrid(); syncBottomPanelContent();
}

function closeBottomPanel() { wbLayout.bottomOpen = false; wbLayout.bottomMax = false; applyWorkbenchGrid(); }
function toggleBottomPanel(tool) { if (wbLayout.bottomOpen && (!tool || tool === wbLayout.bottomTool)) { closeBottomPanel(); } else { openBottomPanel(tool); } }

function toggleBottomToolVisibility(tool) {
  const enabledCount = BP_TOOLS.filter(function (k) { return wbLayout.bottomVisible[k]; }).length;
  if (wbLayout.bottomVisible[tool] && enabledCount <= 1) { return; }
  wbLayout.bottomVisible[tool] = !wbLayout.bottomVisible[tool];
  saveBottomToolPrefs();
  if (!wbLayout.bottomVisible[wbLayout.bottomTool]) {
    const fallback = BP_TOOLS.find(function (k) { return wbLayout.bottomVisible[k]; }) || "work";
    setBottomTool(fallback);
  } else { renderBottomPanelTabs(); }
}

function resetSplitOnAreaChange() {
  wbLayout.splitTabs = [{ id: "sp_" + (++wbTabSeq), chatId: "", title: "" }];
  wbLayout.activeSplitTabId = wbLayout.splitTabs[0].id;
  renderSplitChatTabs();
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
  if (wbLayout.rightOpen && wbLayout.rightTab === "copilot" && typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
  if (typeof broadcastToEmbedFrames === "function") { broadcastToEmbedFrames({ type: "realm:sync-area" }); }
}

function bindWorkbenchResizer(resId, axis, onDelta, onKeyboard) {
  const res = document.getElementById(resId); if (!res) { return; }
  let dragging = false;
  res.addEventListener("pointerdown", function (e) {
    if (e.button !== 0) { return; }
    dragging = true; res.classList.add("is-dragging"); document.body.classList.add("is-resizing-panes");
    res.setPointerCapture(e.pointerId);
  });
  res.addEventListener("pointermove", function (e) { if (dragging) { onDelta(e); } });
  const end = function () { dragging = false; res.classList.remove("is-dragging"); document.body.classList.remove("is-resizing-panes"); };
  res.addEventListener("pointerup", end); res.addEventListener("lostpointercapture", end);
  res.addEventListener("keydown", function (e) {
    const dec = axis === "v" ? "ArrowLeft" : "ArrowUp", inc = axis === "v" ? "ArrowRight" : "ArrowDown";
    if (e.key === dec) { e.preventDefault(); onKeyboard(-1); }
    else if (e.key === inc) { e.preventDefault(); onKeyboard(1); }
  });
}

function bindSplitUX() {
  if (IS_EMBED) { return; }
  loadBottomToolPrefs();
  renderBottomPanelTabs();
  renderSplitChatTabs();

  const splitBtn = document.getElementById("center-split-btn"), spClose = document.getElementById("split-chat-close-btn"), spAdd = document.getElementById("split-chat-add-btn");
  if (splitBtn) { splitBtn.addEventListener("click", function () { if (wbLayout.splitOpen) { closeSplitChat(); } else { openSplitChat({}); } }); }
  if (spClose) { spClose.addEventListener("click", closeSplitChat); }
  if (spAdd) {
    spAdd.addEventListener("click", function () {
      const id = "sp_" + (++wbTabSeq);
      wbLayout.splitTabs.push({ id: id, chatId: "", title: "" });
      activateSplitChatTab(id);
    });
  }
  const agSel = document.getElementById("split-agent-select");
  if (agSel) {
    agSel.addEventListener("change", function () {
      wbLayout.splitAgentId = agSel.value;
      syncSplitPaneAccent();
      const fr = document.getElementById("center-split-frame");
      if (fr && fr.contentWindow && fr.dataset.loaded === "1") {
        fr.contentWindow.postMessage({ source: "realm-parent", type: "realm:set-agent", agentId: wbLayout.splitAgentId }, window.location.origin);
      }
    });
  }

  const bpBtn = document.getElementById("layout-bottom-btn"), bpClose = document.getElementById("bottom-panel-close-btn"), bpMax = document.getElementById("bottom-panel-max-btn");
  if (bpBtn) { bpBtn.addEventListener("click", function () { toggleBottomPanel(); }); }
  if (bpClose) { bpClose.addEventListener("click", closeBottomPanel); }
  if (bpMax) { bpMax.addEventListener("click", function () { wbLayout.bottomMax = !wbLayout.bottomMax; applyWorkbenchGrid(); }); }
  document.querySelectorAll("[data-bp-tool]").forEach(function (btn) {
    btn.addEventListener("click", function () { setBottomTool(btn.getAttribute("data-bp-tool")); });
  });
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#bottom-panel-tablist [role='tab']", function (btn) { setBottomTool(btn.getAttribute("data-bp-tool")); }); }
  document.querySelectorAll("[data-bp-vis]").forEach(function (btn) {
    btn.addEventListener("click", function () { toggleBottomToolVisibility(btn.getAttribute("data-bp-vis")); });
  });

  const rsBtn = document.getElementById("layout-right-btn");
  if (rsBtn) { rsBtn.addEventListener("click", function () { setRightSidebarOpen(!wbLayout.rightOpen); }); }
  document.querySelectorAll("[data-right-tab]").forEach(function (btn) {
    btn.addEventListener("click", function () { setRightSidebarTab(btn.getAttribute("data-right-tab")); });
  });
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#right-sidebar-tablist [role='tab']", function (btn) { setRightSidebarTab(btn.getAttribute("data-right-tab")); }); }

  bindWorkbenchResizer("center-split-resizer", "v", function (e) {
    const row = document.getElementById("center-editor-row"); if (!row) { return; }
    const rect = row.getBoundingClientRect();
    wbLayout.splitRatio = Math.max(28, Math.min(72, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
    applyWorkbenchGrid();
  }, function (dir) { wbLayout.splitRatio = Math.max(28, Math.min(72, wbLayout.splitRatio + dir * 4)); applyWorkbenchGrid(); });

  bindWorkbenchResizer("bottom-panel-resizer", "h", function (e) {
    const col = document.getElementById("workbench-center-col"); if (!col) { return; }
    const rect = col.getBoundingClientRect();
    wbLayout.editorHeightPct = Math.max(22, Math.min(78, Math.round(((e.clientY - rect.top) / rect.height) * 100)));
    applyWorkbenchGrid();
  }, function (dir) { wbLayout.editorHeightPct = Math.max(22, Math.min(78, wbLayout.editorHeightPct + dir * 4)); applyWorkbenchGrid(); });

  bindWorkbenchResizer("right-sidebar-resizer", "v", function (e) {
    const grid = document.getElementById("workbench-grid"); if (!grid) { return; }
    const rect = grid.getBoundingClientRect();
    wbLayout.rightWidthPx = Math.max(260, Math.min(560, Math.round(rect.right - e.clientX)));
    applyWorkbenchGrid();
  }, function (dir) { wbLayout.rightWidthPx = Math.max(260, Math.min(560, wbLayout.rightWidthPx - dir * 24)); applyWorkbenchGrid(); });

  window.addEventListener("resize", applyWorkbenchGrid);
  applyWorkbenchGrid();
}
"""
