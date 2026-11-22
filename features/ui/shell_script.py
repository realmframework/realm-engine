"""Spatial Shell controller: 52px Activity Rail, Context Drawer, Calm Top Bar & Anchored Popovers."""

SHELL_SCRIPT: str = r"""
let activeRailSection = "chat";

function closeShellPopovers() {
  ["rail-status-popover", "wb-more-menu", "bottom-panel-more-menu"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el && el.matches && el.matches(":popover-open") && el.hidePopover) { try { el.hidePopover(); } catch (_e) {} }
  });
}

function updateTopbarContext() {
  const privEl = document.getElementById("sh-pop-privacy"), agEl = document.getElementById("sh-pop-agent"), tmEl = document.getElementById("sh-pop-timer"), topTm = document.getElementById("topbar-timer-pill");
  if (privEl) { privEl.textContent = (typeof localOnly === "function" && localOnly()) ? t("sh_local_only") : t("sh_cloud_ready"); }
  if (typeof syncOfflineStatusChrome === "function") { syncOfflineStatusChrome(); }
  if (agEl) { agEl.textContent = typeof activeAgentName === "function" ? activeAgentName() : "Saga"; }
  const activeTimer = typeof impState !== "undefined" && impState && impState.active_timer;
  const hms = typeof fmtHMS === "function" && typeof impTimerClientSecs !== "undefined" ? fmtHMS(impTimerClientSecs) : "00:00:00";
  if (tmEl) { tmEl.textContent = activeTimer ? hms : "00:00"; }
  if (topTm) { topTm.hidden = !activeTimer; topTm.textContent = hms; }
  if (typeof syncGlobalControlsWidth === "function") { syncGlobalControlsWidth(); }
  const dot = document.getElementById("rail-work-dot");
  if (dot) {
    const hasOverdue = typeof wbState !== "undefined" && wbState && wbState.summary && (wbState.summary.overdue_tasks > 0 || wbState.summary.today_tasks > 0);
    dot.hidden = !(activeTimer || hasOverdue);
  }
}

function renderDrawerDynamicLists() {
  const wfList = document.getElementById("drawer-workflows-list");
  if (wfList && typeof wfState !== "undefined" && Array.isArray(wfState.workflows)) {
    wfList.innerHTML = wfState.workflows.length ? wfState.workflows.map(function (w) {
      const act = typeof wfActiveId !== "undefined" && wfActiveId === w.id;
      return "<button type='button' data-drawer-wf='" + escapeHtml(w.id) + "' class='drawer-item" + (act ? " is-active" : "") + "'><span class='drawer-item-lead'><span>" + escapeHtml(w.name) + "</span></span><span class='drawer-badge'>" + (w.nodes ? w.nodes.length : 0) + "</span></button>";
    }).join("") : "<div class='px-2.5 py-1.5 text-xs text-[#738196]'>—</div>";
    wfList.querySelectorAll("[data-drawer-wf]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof wfActiveId !== "undefined") { wfActiveId = btn.getAttribute("data-drawer-wf") || ""; wfSelectedNodeId = ""; wfNodeRunState = {}; wfLiveSteps = []; }
        if (typeof openWorkflowsView === "function") { openWorkflowsView(); }
        renderDrawerDynamicLists(); updateTopbarContext();
      });
    });
  }
  const agList = document.getElementById("drawer-agents-list");
  if (agList && typeof agentTeam !== "undefined" && Array.isArray(agentTeam)) {
    agList.innerHTML = agentTeam.map(function (ag) {
      const act = typeof activeAgentId !== "undefined" && activeAgentId === ag.id;
      const col = typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette).accent : "#4BB8E8";
      return "<button type='button' data-drawer-agent='" + escapeHtml(ag.id) + "' class='drawer-item" + (act ? " is-active" : "") + "'><span class='drawer-item-lead'><span class='w-2 h-2 rounded-full shrink-0' style='background:" + escapeHtml(col) + "'></span><span>" + escapeHtml(ag.name) + "</span></span><span class='drawer-badge'>" + escapeHtml((ag.role || "").split(" ")[0]) + "</span></button>";
    }).join("");
    agList.querySelectorAll("[data-drawer-agent]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof selectAgentUI === "function") { selectAgentUI(btn.getAttribute("data-drawer-agent")); }
        renderDrawerDynamicLists(); updateTopbarContext();
      });
    });
  }
}

function setActiveRailSection(section, navigate) {
  const safe = ["chat", "library", "work", "workflows", "studio"].includes(section) ? section : "chat";
  activeRailSection = safe;
  document.querySelectorAll("[data-rail-section]").forEach(function (btn) {
    const active = btn.getAttribute("data-rail-section") === safe;
    if (active) { btn.setAttribute("aria-current", "page"); } else { btn.removeAttribute("aria-current"); }
  });
  ["chat", "library", "work", "workflows", "studio"].forEach(function (name) {
    const p = document.getElementById("drawer-panel-" + name);
    if (p) { p.hidden = name !== safe; }
  });
  if (navigate) {
    if (desktopDrawerCollapsed && !(typeof sidebarNarrowMq !== "undefined" && sidebarNarrowMq.matches)) { toggleContextDrawer(true); }
    if (safe === "chat") {
      if (typeof closeWorkBoardView === "function") { closeWorkBoardView(); }
      if (typeof closeFocusView === "function") { closeFocusView(); }
      if (typeof closeImpactView === "function") { closeImpactView(); }
      if (typeof closeWorkflowsView === "function") { closeWorkflowsView(); }
      if (typeof stopGraphSimulation === "function") { stopGraphSimulation(); }
      if (document.getElementById("library-view") || document.getElementById("reader-heading")) { resultsEl.innerHTML = ""; }
      if (typeof setViewMode === "function") { setViewMode(Boolean(currentTurns && currentTurns.length)); }
    } else if (safe === "library" && typeof openLibraryCatalog === "function") {
      setActiveTag(null); openLibraryCatalog(null);
    } else if (safe === "work" && typeof openWorkBoardView === "function") {
      if (!(typeof wbViewOpen !== "undefined" && wbViewOpen) && !(typeof focViewOpen !== "undefined" && focViewOpen) && !(typeof impViewOpen !== "undefined" && impViewOpen)) {
        openWorkBoardView("kanban");
      }
    } else if (safe === "workflows" && typeof openWorkflowsView === "function") {
      openWorkflowsView();
    }
  }
  renderDrawerDynamicLists();
  updateTopbarContext();
}

function handleShellAction(act) {
  closeShellPopovers();
  if (act === "graph" && typeof openGraphView === "function") { setActiveRailSection("library", false); openGraphView(); }
  else if (act === "study" && typeof openStudyDeck === "function") { openStudyDeck({}); }
  else if (act === "gaps" && typeof openGapAnalysisModal === "function") { openGapAnalysisModal(); }
  else if (act === "briefing" && typeof openBriefingModal === "function") { openBriefingModal({}); }
  else if (act === "link-folder" && typeof linkExistingFolder === "function") { linkExistingFolder(); }
  else if (act === "settings" && typeof openSettings === "function") { openSettings("workspace"); }
  else if (act === "guide" && typeof openGuideModal === "function") { openGuideModal(); }
  else if (act === "new-note" && typeof openNewNoteModal === "function") { openNewNoteModal(); }
  else if (act === "upload" && typeof openUploadDialog === "function") { openUploadDialog(); }
  else if (act === "new-chat" && typeof resetHome === "function") { setActiveRailSection("chat", false); resetHome(); }
  else if (act === "deep-focus" && typeof openDeepFocusModal === "function") { openDeepFocusModal("", ""); }
  else if (act === "log-impact" && typeof openImpactEntryModal === "function") { openImpactEntryModal(null); }
  else if (act === "open-kanban" && typeof openWorkBoardView === "function") { setActiveRailSection("work", false); openWorkBoardView("kanban"); }
  else if (act === "wf-new") {
    if (typeof createBlankWorkflowAndOpen === "function") { createBlankWorkflowAndOpen(); }
    else { const b = document.getElementById("wf-new-btn"); if (b) { b.click(); } }
  }
}

function bindSpatialShellUX() {
  const railTog = document.getElementById("rail-drawer-toggle");
  if (railTog) { railTog.addEventListener("click", function () { toggleContextDrawer(); }); }
  document.querySelectorAll("[data-rail-section]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const sec = btn.getAttribute("data-rail-section") || "chat";
      const inMobileStrip = Boolean(btn.closest("#mobile-rail-strip"));
      if (!inMobileStrip && sec === activeRailSection && sec !== "chat" && sec !== "work" && !desktopDrawerCollapsed) { toggleContextDrawer(false); return; }
      setActiveRailSection(sec, !inMobileStrip);
    });
  });
  document.querySelectorAll("[data-shell-act]").forEach(function (btn) {
    btn.addEventListener("click", function () { handleShellAction(btn.getAttribute("data-shell-act") || ""); });
  });
  const topTimer = document.getElementById("topbar-timer-pill");
  if (topTimer) { topTimer.addEventListener("click", function () { setActiveRailSection("work", false); if (typeof openImpactView === "function") { openImpactView("time"); } }); }
  if (typeof bindAnchoredPopover === "function") {
    bindAnchoredPopover("rail-status-popover", "rail-status-btn", { side: "right", align: "bottom" });
    bindAnchoredPopover("wb-more-menu", "wb-more-btn", { align: "right" });
    bindAnchoredPopover("bottom-panel-more-menu", "bottom-panel-more-btn", { align: "right" });
  }
  const stPop = document.getElementById("rail-status-popover");
  if (stPop) { stPop.addEventListener("toggle", function () { updateTopbarContext(); }); }
  setActiveRailSection("chat", false);
}
"""
