"""Workflow Studio Visual Node Canvas, SVG Bezier Edges, Accessible Drag & Linear Step View."""

WORKFLOW_CANVAS_SCRIPT: str = r"""
let wfState = { workflows: [], runs: [], templates: [] };
let wfViewOpen = false, wfActiveId = "", wfSelectedNodeId = "", wfViewMode = "canvas", wfSideTab = "inspect";
let wfNodeRunState = {}, wfActiveRunId = "", wfRunAbort = null, wfLiveSteps = [];
const WF_KIND_KEYS = { trigger: "wf_k_trigger", vault_search: "wf_k_vault_search", run_agent: "wf_k_run_agent", condition: "wf_k_condition", extract_tasks: "wf_k_extract_tasks", generate_slides: "wf_k_generate_slides", save_guide: "wf_k_save_guide", log_impact: "wf_k_log_impact" };
const WF_TRIG_KEYS = { manual: "wf_trig_manual", schedule: "wf_trig_schedule", file_imported: "wf_trig_file", task_done: "wf_trig_task" };
const WF_STAT_KEYS = { completed: "wf_st_completed", running: "wf_st_running", failed: "wf_st_failed", cancelled: "wf_st_cancelled", skipped: "wf_st_skipped" };
const WF_NODE_W = 196, WF_NODE_H = 92;
const WF_GRIP_SVG = "<svg aria-hidden='true' width='13' height='13' viewBox='0 0 24 24' fill='currentColor'><circle cx='9' cy='6' r='1.7'/><circle cx='15' cy='6' r='1.7'/><circle cx='9' cy='12' r='1.7'/><circle cx='15' cy='12' r='1.7'/><circle cx='9' cy='18' r='1.7'/><circle cx='15' cy='18' r='1.7'/></svg>";

function wfAnnounce(msg) {
  const el = document.getElementById("wf-live-status");
  if (!el) { return; }
  el.textContent = "";
  setTimeout(function () { el.textContent = msg; }, 50);
  setTimeout(function () { if (el.textContent === msg) { el.textContent = ""; } }, 1200);
}
function activeWorkflow() {
  return (wfState.workflows || []).find(function (w) { return w.id === wfActiveId; }) || (wfState.workflows || [])[0] || null;
}
function applyWorkflowState(data, selectId) {
  if (!data || !Array.isArray(data.workflows)) { return; }
  wfState = { workflows: data.workflows, runs: data.runs || [], templates: data.templates || wfState.templates || [] };
  if (selectId) { wfActiveId = selectId; }
  if (!wfState.workflows.some(function (w) { return w.id === wfActiveId; })) {
    wfActiveId = wfState.workflows[0] ? wfState.workflows[0].id : "";
  }
  const badge = document.getElementById("sidebar-workflows-badge");
  if (badge) { badge.textContent = String(wfState.workflows.length); }
  if (typeof renderDrawerDynamicLists === "function") { renderDrawerDynamicLists(); }
  if (wfViewOpen) { renderWorkflowsView(); }
}
async function wfApi(path, opts, selectId) {
  const version = areaVersion, cfg = Object.assign({ headers: {} }, opts || {});
  if (cfg.body && !cfg.headers["Content-Type"]) { cfg.headers["Content-Type"] = "application/json"; }
  try {
    const res = await areaFetch(path, cfg), data = await safeJson(res);
    if (version !== areaVersion) { return null; }
    if (!res.ok) { throw new Error(data.detail || "Workflow request failed"); }
    if (Array.isArray(data.workflows)) { applyWorkflowState(data, selectId || (data.item && data.item.id)); }
    return data;
  } catch (err) {
    if (version === areaVersion) { showToast(err.message || "Workflow error", 3800); }
    return null;
  }
}
async function loadWorkflowsSummary() { await wfApi("/api/workflows"); }
function closeWorkflowsView() {
  wfViewOpen = false;
  const v = document.getElementById("workflows-view"); if (v) { v.classList.add("hidden"); }
  const b = document.getElementById("sidebar-workflows-btn"); if (b) { b.classList.remove("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
}
async function openWorkflowsView() {
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  if (typeof closeWorkBoardView === "function") { closeWorkBoardView(); }
  if (typeof closeFocusView === "function") { closeFocusView(); }
  if (typeof closeImpactView === "function") { closeImpactView(); }
  if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); }
  wfViewOpen = true;
  if (typeof setAmbientDimmed === "function") { setAmbientDimmed(true); }
  const shell = document.getElementById("workspace-shell"), gv = document.getElementById("graph-view"), v = document.getElementById("workflows-view");
  if (shell) { shell.classList.add("hidden"); } if (gv) { gv.classList.add("hidden"); } if (v) { v.classList.remove("hidden"); }
  const b = document.getElementById("sidebar-workflows-btn"); if (b) { b.classList.add("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
  if (typeof setActiveRailSection === "function") { setActiveRailSection("workflows", false); }
  await wfApi("/api/workflows");
  renderWorkflowsView();
  if (typeof updateTopbarContext === "function") { updateTopbarContext(); }
}
function wfNodeSummary(node) {
  const c = node.config || {};
  if (node.kind === "run_agent") { return (c.agent_id || "saga") + (c.prompt ? " · " + String(c.prompt).slice(0, 42) : ""); }
  if (node.kind === "vault_search") { return String(c.query || "{{input}}"); }
  if (node.kind === "condition") { return "if contains '" + String(c.contains || "") + "'"; }
  if (node.kind === "generate_slides") { return String(c.output_format || "pptx").toUpperCase() + " · " + String(c.title || "Slides"); }
  if (node.kind === "save_guide") { return String(c.subfolder || "workflows") + "/" + String(c.title || "note"); }
  if (node.kind === "trigger") { return t(WF_TRIG_KEYS[c.trigger_kind || "manual"] || "wf_trig_manual"); }
  return t(WF_KIND_KEYS[node.kind] || "wf_k_trigger");
}
function wfRenderEdges(wf) {
  const svg = document.getElementById("wf-svg-layer"); if (!svg) { return; }
  const byId = new Map((wf.nodes || []).map(function (n) { return [n.id, n]; }));
  const parts = [];
  (wf.edges || []).forEach(function (e) {
    const src = byId.get(e.source), dst = byId.get(e.target);
    if (!src || !dst) { return; }
    const x1 = Number(src.x || 0) + WF_NODE_W, y1 = Number(src.y || 0) + WF_NODE_H / 2;
    const x2 = Number(dst.x || 0), y2 = Number(dst.y || 0) + WF_NODE_H / 2;
    const dx = Math.max(48, Math.abs(x2 - x1) * 0.48);
    const d = "M " + x1 + " " + y1 + " C " + (x1 + dx) + " " + y1 + ", " + (x2 - dx) + " " + y2 + ", " + x2 + " " + y2;
    const cls = e.branch === "true" ? " is-true" : (e.branch === "false" ? " is-false" : "");
    parts.push("<path class='wf-edge-path" + cls + "' d='" + d + "'/>");
    if (e.branch === "true" || e.branch === "false") {
      parts.push("<text class='wf-edge-label' x='" + Math.round((x1 + x2) / 2) + "' y='" + Math.round((y1 + y2) / 2 - 6) + "'>" + escapeHtml(e.branch.toUpperCase()) + "</text>");
    }
  });
  svg.innerHTML = parts.join("");
}
function wfClampPos(x, y) {
  const stage = document.getElementById("wf-canvas-stage");
  const maxX = Math.max(920, (stage ? stage.offsetWidth : 1180) - WF_NODE_W - 16);
  const maxY = Math.max(360, (stage ? stage.offsetHeight : 460) - WF_NODE_H - 16);
  return { x: Math.max(12, Math.min(Math.round(x), maxX)), y: Math.max(12, Math.min(Math.round(y), maxY)) };
}
function wfBindNodeDrag(card, handle, node, wf) {
  let startX = 0, startY = 0, origX = 0, origY = 0, moved = false;
  handle.addEventListener("pointerdown", function (e) {
    if (e.button !== 0) { return; }
    e.stopPropagation();
    startX = e.clientX; startY = e.clientY; origX = Number(node.x || 0); origY = Number(node.y || 0); moved = false;
    handle.setPointerCapture(e.pointerId);
  });
  handle.addEventListener("pointermove", function (e) {
    if (!handle.hasPointerCapture(e.pointerId)) { return; }
    const dx = e.clientX - startX, dy = e.clientY - startY;
    if (!moved && Math.hypot(dx, dy) < 4) { return; }
    moved = true; handle.classList.add("dragging");
    const pos = wfClampPos(origX + dx, origY + dy);
    node.x = pos.x; node.y = pos.y;
    card.style.left = pos.x + "px"; card.style.top = pos.y + "px";
    wfRenderEdges(wf);
  });
  handle.addEventListener("lostpointercapture", function () {
    handle.classList.remove("dragging");
    if (moved) { wfAnnounce(t("wf_moved_msg", { label: node.label, dir: "position" })); }
  });
  handle.addEventListener("keydown", function (e) {
    const delta = { ArrowRight: [20, 0, "right"], ArrowLeft: [-20, 0, "left"], ArrowDown: [0, 20, "down"], ArrowUp: [0, -20, "up"] }[e.key];
    if (!delta) { return; }
    e.preventDefault(); e.stopPropagation();
    const pos = wfClampPos(Number(node.x || 0) + delta[0], Number(node.y || 0) + delta[1]);
    node.x = pos.x; node.y = pos.y;
    card.style.left = pos.x + "px"; card.style.top = pos.y + "px";
    wfRenderEdges(wf);
    wfAnnounce(t("wf_moved_msg", { label: node.label, dir: delta[2] }));
  });
}
function renderWorkflowCanvas(wf) {
  const layer = document.getElementById("wf-nodes-layer"), stepsPanel = document.getElementById("wf-steps-panel"), stage = document.getElementById("wf-canvas-stage");
  if (!layer || !stepsPanel || !stage) { return; }
  const isCanvas = wfViewMode === "canvas";
  stage.hidden = !isCanvas; stepsPanel.hidden = isCanvas;
  document.querySelectorAll("[data-wf-mode]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-wf-mode") === wfViewMode)); });
  if (isCanvas) {
    const maxX = Math.max(900, ...(wf.nodes || []).map(function (n) { return Number(n.x || 0) + WF_NODE_W + 48; }));
    const maxY = Math.max(420, ...(wf.nodes || []).map(function (n) { return Number(n.y || 0) + WF_NODE_H + 56; }));
    stage.style.minWidth = maxX + "px"; stage.style.minHeight = maxY + "px";
    layer.innerHTML = (wf.nodes || []).map(function (n) {
      const st = wfNodeRunState[n.id] || "", stCls = st ? (" is-" + st) : "", selCls = n.id === wfSelectedNodeId ? " is-selected" : "";
      const stRow = st ? ("<div style='margin-top:0.15rem'><span class='wb-chip'>" + escapeHtml(t(WF_STAT_KEYS[st] || "wf_st_completed")) + "</span></div>") : "";
      return "<article class='wf-node-card" + selCls + stCls + "' data-wf-node='" + escapeHtml(n.id) + "' style='left:" + Math.round(n.x || 0) + "px;top:" + Math.round(n.y || 0) + "px'>"
        + "<div class='wf-node-head'><span class='wf-node-badge'>" + escapeHtml(t(WF_KIND_KEYS[n.kind] || "wf_k_trigger")) + "</span>"
        + "<button type='button' class='wf-drag-handle' data-wf-drag='" + escapeHtml(n.id) + "' aria-label='" + escapeHtml(t("wf_drag_aria", { label: n.label })) + "'>" + WF_GRIP_SVG + "</button></div>"
        + "<div class='wf-node-title'>" + escapeHtml(n.label) + "</div>"
        + "<div class='wf-node-sub'>" + escapeHtml(wfNodeSummary(n)) + "</div>" + stRow + "</article>";
    }).join("");
    wfRenderEdges(wf);
    layer.querySelectorAll("[data-wf-node]").forEach(function (card) {
      const nid = card.getAttribute("data-wf-node"), node = (wf.nodes || []).find(function (x) { return x.id === nid; });
      const handle = card.querySelector("[data-wf-drag]");
      if (node && handle) { wfBindNodeDrag(card, handle, node, wf); }
      card.addEventListener("click", function () { wfSelectedNodeId = nid || ""; renderWorkflowsView(); });
    });
  } else {
    stepsPanel.innerHTML = (wf.nodes || []).map(function (n, idx) {
      const st = wfNodeRunState[n.id] || "", stCls = st ? (" is-" + st) : "", selCls = n.id === wfSelectedNodeId ? " is-selected" : "";
      const nextNames = (wf.edges || []).filter(function (e) { return e.source === n.id; }).map(function (e) {
        const tNode = (wf.nodes || []).find(function (x) { return x.id === e.target; });
        return (e.branch !== "default" ? ("[" + e.branch + "] ") : "") + (tNode ? tNode.label : e.target);
      });
      return "<article class='wf-step-card" + selCls + stCls + "' data-wf-step='" + escapeHtml(n.id) + "'>"
        + "<div style='display:flex;align-items:center;gap:0.75rem;min-width:0'><span class='wf-node-badge'>" + (idx + 1) + ". " + escapeHtml(t(WF_KIND_KEYS[n.kind] || "wf_k_trigger")) + "</span>"
        + "<div style='min-width:0'><div class='wf-node-title'>" + escapeHtml(n.label) + "</div><div class='wf-node-sub'>" + escapeHtml(wfNodeSummary(n)) + "</div></div></div>"
        + (nextNames.length ? ("<span class='wb-chip'>→ " + escapeHtml(nextNames.join(", ")) + "</span>") : "") + "</article>";
    }).join("");
    stepsPanel.querySelectorAll("[data-wf-step]").forEach(function (card) {
      card.addEventListener("click", function () { wfSelectedNodeId = card.getAttribute("data-wf-step") || ""; renderWorkflowsView(); });
    });
  }
}
function renderWorkflowsView() {
  const wfs = wfState.workflows || [], wf = activeWorkflow();
  const sel = document.getElementById("wf-select"), empty = document.getElementById("wf-empty-banner"), grid = document.getElementById("wf-workspace-grid"), tb = document.getElementById("wf-toolbar"), pill = document.getElementById("wf-trigger-pill");
  if (sel) {
    sel.innerHTML = wfs.length ? wfs.map(function (w) { return "<option value='" + escapeHtml(w.id) + "'" + (w.id === (wf && wf.id) ? " selected" : "") + ">" + escapeHtml(w.name) + "</option>"; }).join("") : "<option value=''>—</option>";
    sel.disabled = !wfs.length;
  }
  if (empty) { empty.hidden = wfs.length > 0; }
  if (grid) { grid.hidden = !wf; }
  if (tb) { tb.hidden = !wf; }
  const runBtn = document.getElementById("wf-run-btn");
  if (runBtn) { runBtn.disabled = !wf || Boolean(wfActiveRunId); }
  if (!wf) { if (pill) { pill.textContent = "—"; } return; }
  if (pill) { pill.textContent = t(WF_TRIG_KEYS[wf.trigger_kind] || "wf_trig_manual") + (wf.trigger_kind === "schedule" && wf.schedule_minutes ? (" · " + wf.schedule_minutes + "m") : ""); }
  if (!wf.nodes.some(function (n) { return n.id === wfSelectedNodeId; })) { wfSelectedNodeId = wf.nodes[0] ? wf.nodes[0].id : ""; }
  const nameIn = document.getElementById("wf-name-in"), trigSel = document.getElementById("wf-trig-sel"), schIn = document.getElementById("wf-sched-mins");
  if (nameIn && !nameIn.matches(":focus")) { nameIn.value = wf.name || ""; }
  if (trigSel) { trigSel.value = wf.trigger_kind || "manual"; }
  if (schIn && !schIn.matches(":focus")) { schIn.value = String(wf.schedule_minutes || 0); }
  renderWorkflowCanvas(wf);
  if (typeof renderWorkflowInspector === "function") { renderWorkflowInspector(wf); }
  if (typeof renderWorkflowRuns === "function") { renderWorkflowRuns(); }
}
function bindWorkflowToolbarFallback() {
  const bar = document.getElementById("wf-toolbar");
  if (!bar || ("focusGroup" in HTMLElement.prototype)) { return; }
  const items = Array.from(bar.querySelectorAll("button, select"));
  items.forEach(function (el, i) { el.tabIndex = i === 0 ? 0 : -1; });
  bar.addEventListener("focusin", function (e) { if (items.includes(e.target)) { items.forEach(function (el) { el.tabIndex = el === e.target ? 0 : -1; }); } });
  bar.addEventListener("keydown", function (e) {
    const idx = items.indexOf(document.activeElement); if (idx < 0) { return; }
    const rtl = getComputedStyle(bar).direction === "rtl";
    let nxt = -1;
    if (e.key === "ArrowRight") { nxt = (idx + (rtl ? -1 : 1) + items.length) % items.length; }
    else if (e.key === "ArrowLeft") { nxt = (idx + (rtl ? 1 : -1) + items.length) % items.length; }
    else if (e.key === "Home") { nxt = 0; }
    else if (e.key === "End") { nxt = items.length - 1; }
    if (nxt >= 0) { e.preventDefault(); items[nxt].focus(); }
  });
}
"""