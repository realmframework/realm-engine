"""Workflow Studio Interactive Node Canvas: Full-Card Drag, Zoom/Pan HUD, Ports & Live Wire Connections."""

WORKFLOW_CANVAS_SCRIPT: str = r"""
let wfState = { workflows: [], runs: [], templates: [] };
let wfViewOpen = false, wfActiveId = "", wfSelectedNodeId = "", wfViewMode = "canvas", wfSideTab = "inspect";
let wfNodeRunState = {}, wfActiveRunId = "", wfRunAbort = null, wfLiveSteps = [];
let wfZoom = 1, wfPanX = 0, wfPanY = 0, wfWireDraft = null, wfLastFitId = "";
const WF_KIND_KEYS = { trigger: "wf_k_trigger", vault_search: "wf_k_vault_search", run_agent: "wf_k_run_agent", condition: "wf_k_condition", extract_tasks: "wf_k_extract_tasks", generate_slides: "wf_k_generate_slides", save_guide: "wf_k_save_guide", log_impact: "wf_k_log_impact" };
const WF_TRIG_KEYS = { manual: "wf_trig_manual", schedule: "wf_trig_schedule", file_imported: "wf_trig_file", task_done: "wf_trig_task" };
const WF_STAT_KEYS = { completed: "wf_st_completed", running: "wf_st_running", failed: "wf_st_failed", cancelled: "wf_st_cancelled", skipped: "wf_st_skipped" };
const WF_NODE_W = 204, WF_NODE_H = 96;

function wfAnnounce(msg) {
  const el = document.getElementById("wf-live-status"); if (!el) { return; }
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
  return jsonAreaApi(path, opts, "Workflow request failed", function (data) {
    if (Array.isArray(data.workflows)) { applyWorkflowState(data, selectId || (data.item && data.item.id)); }
    if (opts && opts.method && opts.method !== "GET" && typeof notifyParentFrame === "function") { notifyParentFrame({ type: "realm:work-updated", kind: "workflows" }); }
  });
}
async function loadWorkflowsSummary() { await wfApi("/api/workflows"); }
function closeWorkflowsView() {
  wfViewOpen = false;
  const v = document.getElementById("workflows-view"); if (v) { v.classList.add("hidden"); }
}
async function openWorkflowsView() {
  wfViewOpen = true;
  activateWorkspaceView("workflows-view", { railSection: "workflows" });
  await wfApi("/api/workflows");
  renderWorkflowsView();
  if (typeof updateTopbarContext === "function") { updateTopbarContext(); }
}
function wfNodeSummary(node) {
  const c = node.config || {};
  if (node.kind === "run_agent") { return (c.agent_id || "saga") + (c.prompt ? " · " + String(c.prompt).slice(0, 42) : ""); }
  if (node.kind === "vault_search") { return String(c.query || "{{input}}"); }
  if (node.kind === "condition") { return "if contains '" + String(c.contains || "...") + "'"; }
  if (node.kind === "generate_slides") { return String(c.output_format || "pptx").toUpperCase() + " · " + String(c.title || "Slides"); }
  if (node.kind === "save_guide") { return String(c.subfolder || "workflows") + "/" + String(c.title || "note"); }
  if (node.kind === "trigger") { return t(WF_TRIG_KEYS[c.trigger_kind || "manual"] || "wf_trig_manual"); }
  return t(WF_KIND_KEYS[node.kind] || "wf_k_trigger");
}
function wfApplyCanvasTransform() {
  const stage = document.getElementById("wf-canvas-stage"), vp = document.getElementById("wf-canvas-viewport");
  if (stage) { stage.style.transform = "translate(" + Math.round(wfPanX) + "px," + Math.round(wfPanY) + "px) scale(" + wfZoom + ")"; }
  if (vp && wfViewMode === "canvas") {
    const g = Math.max(10, Math.round(20 * wfZoom));
    vp.style.backgroundSize = g + "px " + g + "px";
    vp.style.backgroundPosition = Math.round(wfPanX) + "px " + Math.round(wfPanY) + "px";
  }
  const pct = document.getElementById("wf-zoom-pct");
  if (pct) { pct.textContent = Math.round(wfZoom * 100) + "%"; }
}
function wfSetZoom(nextZoom, pivotX, pivotY) {
  const vp = document.getElementById("wf-canvas-viewport");
  const clamped = Math.max(0.45, Math.min(1.65, Math.round(nextZoom * 100) / 100));
  if (vp) {
    const rect = vp.getBoundingClientRect();
    const px = pivotX !== undefined ? (pivotX - rect.left) : rect.width / 2;
    const py = pivotY !== undefined ? (pivotY - rect.top) : rect.height / 2;
    const sx = (px - wfPanX) / wfZoom, sy = (py - wfPanY) / wfZoom;
    wfZoom = clamped;
    wfPanX = px - sx * wfZoom;
    wfPanY = py - sy * wfZoom;
  } else { wfZoom = clamped; }
  wfApplyCanvasTransform();
}
function wfFitCanvas(wf) {
  const vp = document.getElementById("wf-canvas-viewport");
  if (!vp || !wf || !(wf.nodes || []).length) { wfZoom = 1; wfPanX = 0; wfPanY = 0; wfApplyCanvasTransform(); return; }
  const vw = vp.clientWidth || 720, vh = vp.clientHeight || 460;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  wf.nodes.forEach(function (n) {
    const x = Number(n.x || 0), y = Number(n.y || 0);
    minX = Math.min(minX, x); minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + WF_NODE_W); maxY = Math.max(maxY, y + WF_NODE_H);
  });
  const bw = Math.max(240, maxX - minX + 80), bh = Math.max(160, maxY - minY + 80);
  wfZoom = Math.max(0.55, Math.min(1.0, Math.round(Math.min(vw / bw, vh / bh) * 100) / 100));
  wfPanX = Math.round((vw - (maxX - minX) * wfZoom) / 2 - minX * wfZoom);
  wfPanY = Math.round((vh - (maxY - minY) * wfZoom) / 2 - minY * wfZoom);
  wfApplyCanvasTransform();
}
function wfClientToStage(cx, cy) {
  const vp = document.getElementById("wf-canvas-viewport");
  if (!vp) { return { x: 0, y: 0 }; }
  const r = vp.getBoundingClientRect();
  return { x: (cx - r.left - wfPanX) / wfZoom, y: (cy - r.top - wfPanY) / wfZoom };
}
function wfPortOutPos(node, branch) {
  const x = Number(node.x || 0) + WF_NODE_W, y = Number(node.y || 0);
  if (node.kind === "condition" && branch === "true") { return { x: x, y: y + Math.round(WF_NODE_H * 0.38) }; }
  if (node.kind === "condition" && branch === "false") { return { x: x, y: y + Math.round(WF_NODE_H * 0.76) }; }
  return { x: x, y: y + Math.round(WF_NODE_H * 0.5) };
}
function wfBezierD(x1, y1, x2, y2) {
  const dx = Math.max(52, Math.abs(x2 - x1) * 0.48);
  return "M " + Math.round(x1) + " " + Math.round(y1) + " C " + Math.round(x1 + dx) + " " + Math.round(y1) + ", " + Math.round(x2 - dx) + " " + Math.round(y2) + ", " + Math.round(x2) + " " + Math.round(y2);
}
function wfRenderEdges(wf) {
  const svg = document.getElementById("wf-svg-layer"); if (!svg) { return; }
  const byId = new Map((wf.nodes || []).map(function (n) { return [n.id, n]; }));
  const parts = [];
  (wf.edges || []).forEach(function (e) {
    const src = byId.get(e.source), dst = byId.get(e.target);
    if (!src || !dst) { return; }
    const p1 = wfPortOutPos(src, e.branch), x2 = Number(dst.x || 0), y2 = Number(dst.y || 0) + Math.round(WF_NODE_H * 0.5);
    const cls = e.branch === "true" ? " is-true" : (e.branch === "false" ? " is-false" : "");
    parts.push("<path class='wf-edge-path" + cls + "' d='" + wfBezierD(p1.x, p1.y, x2, y2) + "'/>");
    const mx = Math.round((p1.x + x2) / 2), my = Math.round((p1.y + y2) / 2);
    const lbl = e.branch === "true" ? "TRUE ×" : (e.branch === "false" ? "FALSE ×" : "×");
    const pw = e.branch === "default" ? 20 : 52;
    parts.push("<g class='wf-edge-pill" + cls + "' data-wf-del-edge='" + escapeHtml(e.id) + "' role='button' aria-label='" + escapeHtml(t("wf_edge_del_aria")) + "'><rect x='" + (mx - pw / 2) + "' y='" + (my - 10) + "' width='" + pw + "' height='20' rx='10'/><text class='wf-edge-label' x='" + mx + "' y='" + my + "'>" + escapeHtml(lbl) + "</text></g>");
  });
  if (wfWireDraft) {
    const dCls = wfWireDraft.branch === "true" ? " is-true" : (wfWireDraft.branch === "false" ? " is-false" : "");
    parts.push("<path class='wf-edge-path is-draft" + dCls + "' d='" + wfBezierD(wfWireDraft.x1, wfWireDraft.y1, wfWireDraft.x2, wfWireDraft.y2) + "'/>");
  }
  svg.innerHTML = parts.join("");
  svg.querySelectorAll("[data-wf-del-edge]").forEach(function (pill) {
    pill.addEventListener("pointerdown", function (ev) { ev.stopPropagation(); });
    pill.addEventListener("click", function (ev) {
      ev.stopPropagation();
      const eid = pill.getAttribute("data-wf-del-edge");
      wf.edges = (wf.edges || []).filter(function (x) { return x.id !== eid; });
      renderWorkflowsView();
    });
  });
}
function wfConnectNodes(wf, srcId, dstId, branch) {
  if (!wf || !srcId || !dstId || srcId === dstId) { return; }
  const src = (wf.nodes || []).find(function (n) { return n.id === srcId; });
  const br = src && src.kind === "condition" ? (branch === "false" ? "false" : "true") : "default";
  wf.edges = (wf.edges || []).filter(function (e) {
    if (e.source === srcId && e.target === dstId && e.branch === br) { return false; }
    if (src && src.kind === "condition" && e.source === srcId && e.branch === br) { return false; }
    return true;
  });
  wf.edges.push({ id: "e_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), source: srcId, target: dstId, branch: br });
}
function wfBindNodeDrag(card, handle, node, wf) {
  let startX = 0, startY = 0, origX = 0, origY = 0, moved = false;
  card.addEventListener("pointerdown", function (e) {
    if (e.button !== 0 || e.target.closest(".wf-port")) { return; }
    e.stopPropagation();
    startX = e.clientX; startY = e.clientY; origX = Number(node.x || 0); origY = Number(node.y || 0); moved = false;
    card.setPointerCapture(e.pointerId);
  });
  card.addEventListener("pointermove", function (e) {
    if (!card.hasPointerCapture(e.pointerId)) { return; }
    const dx = e.clientX - startX, dy = e.clientY - startY;
    if (!moved && Math.hypot(dx, dy) < 5) { return; }
    moved = true; card.classList.add("is-dragging");
    node.x = Math.round(origX + dx / wfZoom);
    node.y = Math.round(origY + dy / wfZoom);
    card.style.left = node.x + "px"; card.style.top = node.y + "px";
    wfRenderEdges(wf);
  });
  card.addEventListener("pointerup", function (e) {
    if (card.hasPointerCapture(e.pointerId)) { card.releasePointerCapture(e.pointerId); }
    card.classList.remove("is-dragging");
    if (!moved) {
      wfSelectedNodeId = node.id;
      if (typeof setWorkflowSideTab === "function") { setWorkflowSideTab("inspect"); }
      renderWorkflowsView();
    } else { wfAnnounce(t("wf_moved_msg", { label: node.label, dir: "position" })); }
  });
  card.addEventListener("lostpointercapture", function () { card.classList.remove("is-dragging"); });
  if (handle) {
    handle.addEventListener("keydown", function (e) {
      const delta = { ArrowRight: [20, 0, "right"], ArrowLeft: [-20, 0, "left"], ArrowDown: [0, 20, "down"], ArrowUp: [0, -20, "up"] }[e.key];
      if (!delta) { return; }
      e.preventDefault(); e.stopPropagation();
      node.x = Math.round(Number(node.x || 0) + delta[0]); node.y = Math.round(Number(node.y || 0) + delta[1]);
      card.style.left = node.x + "px"; card.style.top = node.y + "px";
      wfRenderEdges(wf);
      wfAnnounce(t("wf_moved_msg", { label: node.label, dir: delta[2] }));
    });
  }
}
function wfBindPortWire(portBtn, node, wf) {
  let active = false, hoverId = "";
  const branch = portBtn.getAttribute("data-wf-branch") || "default";
  const clearHover = function () { document.querySelectorAll(".wf-node-card.is-drop-target").forEach(function (el) { el.classList.remove("is-drop-target"); }); };
  portBtn.addEventListener("pointerdown", function (e) {
    if (e.button !== 0) { return; }
    e.stopPropagation(); e.preventDefault();
    active = true; hoverId = "";
    const p1 = wfPortOutPos(node, branch);
    wfWireDraft = { sourceId: node.id, branch: branch, x1: p1.x, y1: p1.y, x2: p1.x, y2: p1.y };
    portBtn.setPointerCapture(e.pointerId);
    wfRenderEdges(wf);
  });
  portBtn.addEventListener("pointermove", function (e) {
    if (!active || !wfWireDraft) { return; }
    const pt = wfClientToStage(e.clientX, e.clientY);
    wfWireDraft.x2 = pt.x; wfWireDraft.y2 = pt.y;
    clearHover(); hoverId = "";
    const hit = document.elementsFromPoint(e.clientX, e.clientY).find(function (el) { return el.classList && el.classList.contains("wf-node-card") && el.getAttribute("data-wf-node") !== node.id; });
    if (hit) { hoverId = hit.getAttribute("data-wf-node") || ""; hit.classList.add("is-drop-target"); }
    wfRenderEdges(wf);
  });
  const finish = function (e) {
    if (!active) { return; }
    active = false;
    if (e && portBtn.hasPointerCapture && portBtn.hasPointerCapture(e.pointerId)) { portBtn.releasePointerCapture(e.pointerId); }
    clearHover();
    const targetId = hoverId; wfWireDraft = null; hoverId = "";
    if (targetId) { wfConnectNodes(wf, node.id, targetId, branch); renderWorkflowsView(); }
    else { wfRenderEdges(wf); }
  };
  portBtn.addEventListener("pointerup", finish);
  portBtn.addEventListener("lostpointercapture", finish);
}
function renderWorkflowCanvas(wf) {
  const layer = document.getElementById("wf-nodes-layer"), stepsPanel = document.getElementById("wf-steps-panel"), stage = document.getElementById("wf-canvas-stage"), vp = document.getElementById("wf-canvas-viewport"), hud = document.getElementById("wf-zoom-hud");
  if (!layer || !stepsPanel || !stage) { return; }
  const isCanvas = wfViewMode === "canvas";
  stage.hidden = !isCanvas; stepsPanel.hidden = isCanvas;
  if (hud) { hud.hidden = !isCanvas; }
  if (vp) { vp.classList.toggle("is-step-mode", !isCanvas); }
  document.querySelectorAll("[data-wf-mode]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-wf-mode") === wfViewMode)); });
  if (isCanvas) {
    if (wfLastFitId !== wf.id) { wfLastFitId = wf.id; wfFitCanvas(wf); } else { wfApplyCanvasTransform(); }
    layer.innerHTML = (wf.nodes || []).map(function (n) {
      const st = wfNodeRunState[n.id] || "", stCls = st ? (" is-" + st) : "", selCls = n.id === wfSelectedNodeId ? " is-selected" : "", gwCls = n.kind === "condition" ? " is-gateway" : "";
      const stRow = st ? ("<div style='margin-top:0.15rem'><span class='wb-chip'>" + escapeHtml(t(WF_STAT_KEYS[st] || "wf_st_completed")) + "</span></div>") : "";
      const inPort = n.kind !== "trigger" ? "<span class='wf-port wf-port-in' aria-hidden='true'></span>" : "";
      const hint = escapeHtml(t("wf_port_hint"));
      const outPorts = n.kind === "condition"
        ? "<span class='wf-port-tag is-true'>TRUE</span><button type='button' class='wf-port wf-port-true' data-wf-out='" + escapeHtml(n.id) + "' data-wf-branch='true' title='" + hint + "' aria-label='TRUE " + hint + "'></button>"
          + "<span class='wf-port-tag is-false'>FALSE</span><button type='button' class='wf-port wf-port-false' data-wf-out='" + escapeHtml(n.id) + "' data-wf-branch='false' title='" + hint + "' aria-label='FALSE " + hint + "'></button>"
        : "<button type='button' class='wf-port wf-port-out' data-wf-out='" + escapeHtml(n.id) + "' data-wf-branch='default' title='" + hint + "' aria-label='" + hint + "'></button>";
      return "<article class='wf-node-card" + gwCls + selCls + stCls + "' data-wf-node='" + escapeHtml(n.id) + "' style='left:" + Math.round(n.x || 0) + "px;top:" + Math.round(n.y || 0) + "px'>"
        + inPort + outPorts
        + "<div class='wf-node-head'><span class='wf-node-badge'>" + escapeHtml(t(WF_KIND_KEYS[n.kind] || "wf_k_trigger")) + "</span>"
        + "<button type='button' class='wf-drag-handle' data-wf-drag='" + escapeHtml(n.id) + "' aria-label='" + escapeHtml(t("wf_drag_aria", { label: n.label })) + "'>" + GRIP_DOTS_SVG + "</button></div>"
        + "<div class='wf-node-title'>" + escapeHtml(n.label) + "</div>"
        + "<div class='wf-node-sub'>" + escapeHtml(wfNodeSummary(n)) + "</div>" + stRow + "</article>";
    }).join("");
    wfRenderEdges(wf);
    layer.querySelectorAll("[data-wf-node]").forEach(function (card) {
      const nid = card.getAttribute("data-wf-node"), node = (wf.nodes || []).find(function (x) { return x.id === nid; });
      if (!node) { return; }
      wfBindNodeDrag(card, card.querySelector("[data-wf-drag]"), node, wf);
      card.querySelectorAll("[data-wf-out]").forEach(function (pBtn) { wfBindPortWire(pBtn, node, wf); });
    });
  } else {
    stepsPanel.innerHTML = (wf.nodes || []).map(function (n, idx) {
      const st = wfNodeRunState[n.id] || "", stCls = st ? (" is-" + st) : "", selCls = n.id === wfSelectedNodeId ? " is-selected" : "";
      const nextNames = (wf.edges || []).filter(function (e) { return e.source === n.id; }).map(function (e) {
        const tNode = (wf.nodes || []).find(function (x) { return x.id === e.target; });
        return (e.branch !== "default" ? ("[" + e.branch.toUpperCase() + "] ") : "") + (tNode ? tNode.label : e.target);
      });
      return "<article class='wf-step-card" + selCls + stCls + "' data-wf-step='" + escapeHtml(n.id) + "'>"
        + "<div style='display:flex;align-items:center;gap:0.75rem;min-width:0'><span class='wf-node-badge'>" + (idx + 1) + ". " + escapeHtml(t(WF_KIND_KEYS[n.kind] || "wf_k_trigger")) + "</span>"
        + "<div style='min-width:0'><div class='wf-node-title'>" + escapeHtml(n.label) + "</div><div class='wf-node-sub'>" + escapeHtml(wfNodeSummary(n)) + "</div></div></div>"
        + (nextNames.length ? ("<span class='wb-chip'>→ " + escapeHtml(nextNames.join(", ")) + "</span>") : "") + "</article>";
    }).join("");
    stepsPanel.querySelectorAll("[data-wf-step]").forEach(function (card) {
      card.addEventListener("click", function () { wfSelectedNodeId = card.getAttribute("data-wf-step") || ""; if (typeof setWorkflowSideTab === "function") { setWorkflowSideTab("inspect"); } renderWorkflowsView(); });
    });
  }
}
function renderWorkflowsView() {
  const wfs = wfState.workflows || [], wf = activeWorkflow(), hasWf = Boolean(wf);
  const sel = document.getElementById("wf-select"), empty = document.getElementById("wf-empty-banner");
  const grid = document.getElementById("wf-workspace-grid"), tb = document.getElementById("wf-toolbar");
  const metaBar = document.getElementById("wf-meta-bar"), pill = document.getElementById("wf-trigger-pill");
  const newBtn = document.getElementById("wf-new-btn"), runBtn = document.getElementById("wf-run-btn");
  if (sel) {
    sel.hidden = !hasWf;
    sel.innerHTML = hasWf ? wfs.map(function (w) { return "<option value='" + escapeHtml(w.id) + "'" + (w.id === wf.id ? " selected" : "") + ">" + escapeHtml(w.name) + "</option>"; }).join("") : "";
    sel.disabled = !hasWf;
  }
  if (pill) { pill.hidden = !hasWf; }
  if (newBtn) { newBtn.hidden = !hasWf; }
  if (runBtn) { runBtn.hidden = !hasWf || Boolean(wfActiveRunId); runBtn.disabled = !hasWf || Boolean(wfActiveRunId); }
  if (empty) { empty.hidden = hasWf; }
  if (grid) { grid.hidden = !hasWf; }
  if (tb) { tb.hidden = !hasWf; }
  if (metaBar) { metaBar.hidden = !hasWf; }
  if (!wf) { if (typeof updateTopbarContext === "function") { updateTopbarContext(); } return; }
  if (pill) { pill.textContent = t(WF_TRIG_KEYS[wf.trigger_kind] || "wf_trig_manual") + (wf.trigger_kind === "schedule" && wf.schedule_minutes ? (" · " + wf.schedule_minutes + "m") : ""); }
  if (!wf.nodes.some(function (n) { return n.id === wfSelectedNodeId; })) {
    const preferred = wf.nodes.find(function (n) { return n.kind !== "trigger"; }) || wf.nodes[0];
    wfSelectedNodeId = preferred ? preferred.id : "";
  }
  const nameIn = document.getElementById("wf-name-in"), trigSel = document.getElementById("wf-trig-sel");
  const schIn = document.getElementById("wf-sched-mins"), schWrap = document.getElementById("wf-sched-wrap");
  if (nameIn && !nameIn.matches(":focus")) { nameIn.value = wf.name || ""; }
  if (trigSel) { trigSel.value = wf.trigger_kind || "manual"; }
  if (schWrap) { schWrap.hidden = wf.trigger_kind !== "schedule"; }
  if (schIn && !schIn.matches(":focus")) { schIn.value = String(wf.schedule_minutes || 60); }
  renderWorkflowCanvas(wf);
  if (typeof renderWorkflowInspector === "function") { renderWorkflowInspector(wf); }
  if (typeof renderWorkflowRuns === "function") { renderWorkflowRuns(); }
  if (typeof updateTopbarContext === "function") { updateTopbarContext(); }
}
function bindWorkflowCanvasViewportUX() {
  const vp = document.getElementById("wf-canvas-viewport");
  if (vp) {
    vp.addEventListener("wheel", function (e) {
      if (wfViewMode !== "canvas") { return; }
      e.preventDefault();
      wfSetZoom(wfZoom + (e.deltaY < 0 ? 0.1 : -0.1), e.clientX, e.clientY);
    }, { passive: false });
    let panOn = false, sx = 0, sy = 0, ox = 0, oy = 0;
    vp.addEventListener("pointerdown", function (e) {
      if (wfViewMode !== "canvas" || e.button !== 0 || e.target.closest(".wf-node-card, .wf-zoom-hud, .wf-edge-pill")) { return; }
      panOn = true; sx = e.clientX; sy = e.clientY; ox = wfPanX; oy = wfPanY;
      vp.classList.add("is-panning"); vp.setPointerCapture(e.pointerId);
    });
    vp.addEventListener("pointermove", function (e) {
      if (!panOn) { return; }
      wfPanX = ox + (e.clientX - sx); wfPanY = oy + (e.clientY - sy);
      wfApplyCanvasTransform();
    });
    const endPan = function () { panOn = false; vp.classList.remove("is-panning"); };
    vp.addEventListener("pointerup", endPan); vp.addEventListener("lostpointercapture", endPan);
  }
  const zIn = document.getElementById("wf-zoom-in"), zOut = document.getElementById("wf-zoom-out"), zFit = document.getElementById("wf-zoom-fit");
  if (zIn) { zIn.addEventListener("click", function () { wfSetZoom(wfZoom + 0.15); }); }
  if (zOut) { zOut.addEventListener("click", function () { wfSetZoom(wfZoom - 0.15); }); }
  if (zFit) { zFit.addEventListener("click", function () { wfFitCanvas(activeWorkflow()); }); }
}
"""
