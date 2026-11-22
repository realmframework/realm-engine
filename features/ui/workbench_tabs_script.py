"""Codex-inspired Multi-Tab Side Workbench controller: Launcher, Chat, Guide, Tasks, Focus & Impact Tabs."""

WORKBENCH_TABS_SCRIPT: str = r"""
let wbSideTabs = [{ id: "tab_chat", kind: "chat", title: "" }];
let wbActiveSideTabId = "tab_chat";
const WB_SIDE_TILE_KEYS = { launcher: "wb_new_tab", chat: "wb_tile_chat", guide: "wb_tile_guide", tasks: "wb_tile_tasks", focus: "wb_tile_focus", impact: "wb_tile_impact" };

function wbSideTabTitle(tab) {
  if (tab.title) { return tab.title; }
  return t(WB_SIDE_TILE_KEYS[tab.kind] || "wb_new_tab");
}
function renderSideWorkbenchTabs() {
  const list = document.getElementById("wb-side-tablist");
  if (!list) { return; }
  if (!wbSideTabs.length) { wbSideTabs = [{ id: "tab_launcher", kind: "launcher", title: "" }]; }
  if (!wbSideTabs.some(function (tb) { return tb.id === wbActiveSideTabId; })) { wbActiveSideTabId = wbSideTabs[0].id; }
  list.innerHTML = wbSideTabs.map(function (tb) {
    const sel = tb.id === wbActiveSideTabId;
    const closeBtn = wbSideTabs.length > 1 ? "<span class='wb-tab-x' data-wb-close-tab='" + escapeHtml(tb.id) + "' role='button' aria-label='Close tab'>✕</span>" : "";
    return "<button type='button' role='tab' aria-selected='" + String(sel) + "' data-wb-side-tab='" + escapeHtml(tb.id) + "' class='wb-side-tab'><span>" + escapeHtml(wbSideTabTitle(tb)) + "</span>" + closeBtn + "</button>";
  }).join("");
  list.querySelectorAll("[data-wb-side-tab]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      const closeEl = e.target.closest("[data-wb-close-tab]");
      if (closeEl) { e.stopPropagation(); closeSideWorkbenchTab(closeEl.getAttribute("data-wb-close-tab")); return; }
      activateSideWorkbenchTab(btn.getAttribute("data-wb-side-tab"));
    });
  });
  syncSideWorkbenchBody();
}
function syncSideWorkbenchBody() {
  const active = wbSideTabs.find(function (tb) { return tb.id === wbActiveSideTabId; }) || wbSideTabs[0];
  const kind = active ? active.kind : "chat";
  const panels = {
    launcher: document.getElementById("split-launcher-body"),
    chat: document.getElementById("split-chat-body"),
    guide: document.getElementById("split-guide-body"),
    tasks: document.getElementById("split-tasks-body"),
    focus: document.getElementById("split-focus-body"),
    impact: document.getElementById("split-impact-body")
  };
  Object.entries(panels).forEach(function (pair) { if (pair[1]) { pair[1].hidden = pair[0] !== kind; } });
  if (typeof splitState !== "undefined" && (kind === "chat" || kind === "guide")) { splitState.bMode = kind; }
  if (kind === "guide" && typeof renderSplitGuide === "function") { renderSplitGuide(); }
  else if (kind === "chat" && typeof renderSplitChatStream === "function") { syncSplitSelectors(); renderSplitChatStream(); }
  else if (kind === "tasks") { renderSideQuickTasks(); }
  else if (kind === "focus") { renderSideQuickFocus(); }
  else if (kind === "impact") { renderSideQuickImpact(); }
  else if (kind === "launcher") { renderSideLauncherResults(""); }
}
function activateSideWorkbenchTab(tabId) {
  wbActiveSideTabId = tabId || (wbSideTabs[0] && wbSideTabs[0].id) || "";
  renderSideWorkbenchTabs();
}
function closeSideWorkbenchTab(tabId) {
  wbSideTabs = wbSideTabs.filter(function (tb) { return tb.id !== tabId; });
  if (!wbSideTabs.length) { wbSideTabs.push({ id: "tab_launcher_" + Date.now(), kind: "launcher", title: "" }); }
  if (wbActiveSideTabId === tabId) { wbActiveSideTabId = wbSideTabs[wbSideTabs.length - 1].id; }
  renderSideWorkbenchTabs();
}
function openSideWorkbenchTab(kind, opts) {
  const opt = opts || {}, k = kind || "launcher";
  const existing = opt.reuse !== false ? wbSideTabs.find(function (tb) { return tb.kind === k && (!opt.title || tb.title === opt.title); }) : null;
  if (existing) {
    const cur = wbSideTabs.find(function (tb) { return tb.id === wbActiveSideTabId; });
    if (cur && cur.kind === "launcher" && cur.id !== existing.id) { wbSideTabs = wbSideTabs.filter(function (tb) { return tb.id !== cur.id; }); }
    wbActiveSideTabId = existing.id;
  } else {
    const cur = wbSideTabs.find(function (tb) { return tb.id === wbActiveSideTabId; });
    if (cur && cur.kind === "launcher" && k !== "launcher") { cur.kind = k; cur.title = opt.title || ""; }
    else {
      const id = "tab_" + k + "_" + Date.now().toString(36).slice(-4);
      wbSideTabs.push({ id: id, kind: k, title: opt.title || "" });
      wbActiveSideTabId = id;
    }
  }
  if (typeof splitState !== "undefined" && !splitState.open && typeof openSplitMode === "function") {
    splitState.open = true; splitState.orientation = opt.orientation || splitState.orientation || "vertical";
    if (typeof applySplitLayout === "function") { applySplitLayout(); }
  }
  renderSideWorkbenchTabs();
}
function renderSideLauncherResults(q) {
  const box = document.getElementById("wb-launcher-results"); if (!box) { return; }
  const needle = String(q || "").trim().toLowerCase();
  if (!needle) { box.innerHTML = ""; return; }
  const hits = [];
  (typeof allGuides !== "undefined" && Array.isArray(allGuides) ? allGuides : []).forEach(function (g) {
    if ((g.title || "").toLowerCase().includes(needle)) { hits.push({ kind: "guide", id: g.doc_id, label: g.title || g.doc_id, badge: t("library") }); }
  });
  (typeof wbState !== "undefined" && Array.isArray(wbState.tasks) ? wbState.tasks : []).forEach(function (tk) {
    if ((tk.title || "").toLowerCase().includes(needle)) { hits.push({ kind: "task", id: tk.id, label: tk.title, badge: t("wb_tab_tasks") }); }
  });
  box.innerHTML = hits.slice(0, 6).map(function (h) {
    return "<button type='button' data-lnch-kind='" + escapeHtml(h.kind) + "' data-lnch-id='" + escapeHtml(h.id) + "' class='drawer-item' style='background:var(--surface-raised);border:1px solid var(--border-subtle)'><span class='drawer-item-lead'><span>" + escapeHtml(h.label) + "</span></span><span class='drawer-badge'>" + escapeHtml(h.badge) + "</span></button>";
  }).join("");
  box.querySelectorAll("[data-lnch-kind]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const hk = btn.getAttribute("data-lnch-kind"), hid = btn.getAttribute("data-lnch-id");
      if (hk === "guide") {
        if (typeof splitState !== "undefined") { splitState.guideId = hid || ""; }
        openSideWorkbenchTab("guide", { title: btn.querySelector("span").textContent || "" });
      } else { openSideWorkbenchTab("tasks"); }
    });
  });
}
function renderSideQuickTasks() {
  const list = document.getElementById("wb-side-task-list"); if (!list) { return; }
  const cols = (typeof wbState !== "undefined" && wbState.columns) || [];
  const doneIds = new Set(cols.filter(function (c) { return c.is_done; }).map(function (c) { return c.id; }));
  const doneCol = cols.find(function (c) { return c.is_done; }) || cols[cols.length - 1];
  const openTasks = ((typeof wbState !== "undefined" && wbState.tasks) || []).filter(function (tk) { return !doneIds.has(tk.column_id); }).slice(0, 18);
  if (!openTasks.length) { list.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("wb_empty_tasks")) + "</div>"; return; }
  list.innerHTML = openTasks.map(function (tk) {
    return "<div class='wb-task-row' style='margin:0;padding:0.55rem 0.7rem'><button type='button' data-side-done='" + escapeHtml(tk.id) + "' aria-pressed='false' aria-label='" + escapeHtml(tk.title) + "' class='wb-check-btn'></button><button type='button' data-side-open-tk='" + escapeHtml(tk.id) + "' class='wb-card-title'>" + escapeHtml(tk.title) + "</button>" + (tk.due_date ? "<span class='wb-chip'>" + escapeHtml(tk.due_date) + "</span>" : "") + "</div>";
  }).join("");
  list.querySelectorAll("[data-side-done]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (doneCol && typeof wbApi === "function") { await wbApi("/api/work-board/tasks/" + encodeURIComponent(btn.getAttribute("data-side-done")), { method: "PATCH", body: JSON.stringify({ column_id: doneCol.id }) }); renderSideQuickTasks(); }
    });
  });
  list.querySelectorAll("[data-side-open-tk]").forEach(function (btn) {
    btn.addEventListener("click", function () { if (typeof openWorkTaskModal === "function") { openWorkTaskModal(btn.getAttribute("data-side-open-tk")); } });
  });
}
function renderSideQuickFocus() {
  const box = document.getElementById("wb-side-focus-goals"); if (!box) { return; }
  const goals = (typeof focState !== "undefined" && focState.goals) || [], trajs = (typeof focState !== "undefined" && focState.analytics && focState.analytics.trajectories) || {};
  document.querySelectorAll("[data-side-snd]").forEach(function (b) { b.setAttribute("aria-pressed", String(typeof dfSound !== "undefined" && b.getAttribute("data-side-snd") === dfSound)); });
  box.innerHTML = goals.length ? goals.map(function (g) {
    const tr = trajs[g.id] || { logged_hours: 0, pct_hours: 0 };
    return "<div class='goal-card' style='padding:0.75rem'><div style='display:flex;justify-content:space-between;gap:0.4rem'><strong>" + escapeHtml(g.title) + "</strong><span class='wb-chip'>" + tr.pct_hours + "%</span></div><progress class='goal-progress' value='" + tr.pct_hours + "' max='100' aria-label='" + escapeHtml(g.title) + "'></progress></div>";
  }).join("") : "<div class='wb-empty'>" + escapeHtml(t("foc_empty_goals")) + "</div>";
}
function renderSideQuickImpact() {
  const box = document.getElementById("wb-side-imp-recent"); if (!box) { return; }
  const items = ((typeof impState !== "undefined" && impState.impact_entries) || []).slice(0, 6);
  box.innerHTML = items.map(function (e) {
    return "<div class='wf-run-step'><strong>" + escapeHtml(e.what_done) + "</strong><div style='color:var(--text-muted);font-size:0.8rem'>" + escapeHtml(e.effect) + "</div></div>";
  }).join("");
}
function bindWorkbenchTabsUX() {
  const addBtn = document.getElementById("wb-side-add-tab");
  if (addBtn) { addBtn.addEventListener("click", function () { openSideWorkbenchTab("launcher", { reuse: false }); const inp = document.getElementById("wb-launcher-search"); if (inp) { inp.value = ""; inp.focus(); } }); }
  const lnchSearch = document.getElementById("wb-launcher-search");
  if (lnchSearch) { lnchSearch.addEventListener("input", function () { renderSideLauncherResults(lnchSearch.value); }); }
  document.querySelectorAll("[data-open-side-tile]").forEach(function (btn) {
    btn.addEventListener("click", function () { openSideWorkbenchTab(btn.getAttribute("data-open-side-tile") || "chat"); });
  });
  const stForm = document.getElementById("wb-side-task-form");
  if (stForm) {
    stForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const inp = document.getElementById("wb-side-task-in"), title = inp ? inp.value.trim() : "";
      if (!title || typeof wbApi !== "function") { return; }
      inp.value = "";
      await wbApi("/api/work-board/tasks", { method: "POST", body: JSON.stringify({ title: title }) });
      renderSideQuickTasks();
    });
  }
  const openDeep = document.getElementById("wb-side-open-deep");
  if (openDeep) { openDeep.addEventListener("click", function () { if (typeof openDeepFocusModal === "function") { openDeepFocusModal("", ""); } }); }
  document.querySelectorAll("[data-side-snd]").forEach(function (btn) {
    btn.addEventListener("click", function () { if (typeof startFocusSoundscape === "function") { startFocusSoundscape(btn.getAttribute("data-side-snd") || "off"); renderSideQuickFocus(); } });
  });
  const openImp = document.getElementById("wb-side-open-impact");
  if (openImp) { openImp.addEventListener("click", function () { if (typeof openImpactEntryModal === "function") { openImpactEntryModal(null); } }); }
  const siForm = document.getElementById("wb-side-imp-form");
  if (siForm) {
    siForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const w = document.getElementById("wb-si-what").value.trim(), ef = document.getElementById("wb-si-effect").value.trim();
      if (!w || !ef || typeof impApi !== "function") { return; }
      if (await impApi("/api/impact/entries", { method: "POST", body: JSON.stringify({ what_done: w, effect: ef, outcome_tag: "quality" }) })) {
        document.getElementById("wb-si-what").value = ""; document.getElementById("wb-si-effect").value = "";
        showToast(t("imp_saved_toast")); renderSideQuickImpact();
      }
    });
  }
  renderSideWorkbenchTabs();
}
"""