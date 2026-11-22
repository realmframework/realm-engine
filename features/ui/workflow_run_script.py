"""Workflow Studio Node Inspector (with Dual-Branch Gateways), Templates Gallery & Live SSE Runner."""

WORKFLOW_RUN_SCRIPT: str = r"""
function setWorkflowSideTab(tab) {
  wfSideTab = tab || "inspect";
  document.querySelectorAll("[data-wf-side]").forEach(function (b) {
    const active = b.getAttribute("data-wf-side") === wfSideTab;
    b.setAttribute("aria-selected", String(active)); b.tabIndex = active ? 0 : -1;
  });
  const p1 = document.getElementById("wf-panel-inspect"), p2 = document.getElementById("wf-panel-runs");
  if (p1) { p1.hidden = wfSideTab !== "inspect"; }
  if (p2) { p2.hidden = wfSideTab !== "runs"; }
}
async function persistActiveWorkflow(showMsg) {
  const wf = activeWorkflow(); if (!wf) { return null; }
  const nameIn = document.getElementById("wf-name-in"), trigSel = document.getElementById("wf-trig-sel"), schIn = document.getElementById("wf-sched-mins");
  if (nameIn && nameIn.value.trim()) { wf.name = nameIn.value.trim(); }
  if (trigSel) { wf.trigger_kind = trigSel.value; }
  wf.schedule_minutes = wf.trigger_kind === "schedule" && schIn ? Math.max(5, Number(schIn.value || 60)) : 0;
  const res = await wfApi("/api/workflows/" + encodeURIComponent(wf.id), {
    method: "PATCH",
    body: JSON.stringify({ name: wf.name, description: wf.description, enabled: wf.enabled, trigger_kind: wf.trigger_kind, schedule_minutes: wf.schedule_minutes, nodes: wf.nodes, edges: wf.edges })
  }, wf.id);
  if (res && showMsg) { showToast(t("wf_saved_toast")); }
  return res;
}
function nextBlankWorkflowName() {
  const base = t("wf_default_name"), used = new Set((wfState.workflows || []).map(function (w) { return String(w.name || "").trim().toLowerCase(); }));
  if (!used.has(base.toLowerCase())) { return base; }
  let n = 2;
  while (used.has((base + " " + n).toLowerCase())) { n += 1; }
  return base + " " + n;
}
async function createBlankWorkflowAndOpen() {
  if (!wfViewOpen && typeof openWorkflowsView === "function") { await openWorkflowsView(); }
  const name = nextBlankWorkflowName();
  const data = await wfApi("/api/workflows", {
    method: "POST",
    body: JSON.stringify({
      name: name, description: "", trigger_kind: "manual", schedule_minutes: 0,
      nodes: [
        { id: "n1", kind: "trigger", label: t("wf_trig_manual"), x: 36, y: 120, config: { trigger_kind: "manual" } },
        { id: "n2", kind: "run_agent", label: t("wf_k_run_agent"), x: 300, y: 120, config: { agent_id: "saga", prompt: "Summarize key takeaways:\n\n{{input}}" } }
      ],
      edges: [{ id: "e1", source: "n1", target: "n2", branch: "default" }]
    })
  });
  if (data && data.item) {
    wfActiveId = data.item.id; wfSelectedNodeId = "n2"; wfNodeRunState = {}; wfLiveSteps = []; wfLastFitId = "";
    setWorkflowSideTab("inspect");
    renderWorkflowsView();
    showToast(t("wf_created_toast"));
    const nameIn = document.getElementById("wf-name-in");
    if (nameIn) { nameIn.focus(); nameIn.select(); }
  }
}
function wfAddStepNode(kind, fromNode, branch) {
  const wf = activeWorkflow(); if (!wf) { return null; }
  const src = fromNode || (wf.nodes || []).find(function (n) { return n.id === wfSelectedNodeId; }) || wf.nodes[wf.nodes.length - 1] || null;
  const nid = "n_" + Date.now().toString(36).slice(-5) + Math.random().toString(36).slice(2, 4);
  const outCount = src ? (wf.edges || []).filter(function (e) { return e.source === src.id; }).length : 0;
  let x = src ? Number(src.x || 0) + 260 : 40;
  let y = src ? Number(src.y || 120) : 120;
  if (branch === "true") { y = Math.max(20, y - 78); }
  else if (branch === "false") { y = y + 84; }
  else if (outCount > 0) { y = y + outCount * 118; }
  const cfg = kind === "run_agent" ? { agent_id: "saga", prompt: "Process:\n\n{{prev}}" } : (kind === "condition" ? { contains: "" } : {});
  const node = { id: nid, kind: kind, label: t(WF_KIND_KEYS[kind] || "wf_k_run_agent"), x: Math.round(x), y: Math.round(y), config: cfg };
  wf.nodes.push(node);
  if (src) { wfConnectNodes(wf, src.id, nid, branch || (src.kind === "condition" ? "true" : "default")); }
  wfSelectedNodeId = nid; setWorkflowSideTab("inspect");
  renderWorkflowsView();
  wfFitCanvas(wf);
  return node;
}
function renderWorkflowInspector(wf) {
  const box = document.getElementById("wf-node-inspector"); if (!box) { return; }
  const node = (wf.nodes || []).find(function (n) { return n.id === wfSelectedNodeId; });
  if (!node) { box.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("wf_select_hint")) + "</div>"; return; }
  const cfg = node.config || {}, agents = (typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length) ? agentTeam : [{ id: "saga", name: "Saga" }, { id: "lisbeth", name: "Lisbeth" }, { id: "plague", name: "Plague" }];
  let fields = "<div class='wb-field'><label for='wfi-label'>" + escapeHtml(t("wf_step_label")) + "</label><input id='wfi-label' type='text' maxlength='120' value='" + escapeHtml(node.label) + "' class='wb-input'/></div>";
  if (node.kind === "run_agent") {
    fields += "<div class='wb-field'><label for='wfi-agent'>" + escapeHtml(t("wf_agent_lbl")) + "</label><select id='wfi-agent' class='wb-select'>"
      + agents.map(function (a) { return "<option value='" + escapeHtml(a.id) + "'" + ((cfg.agent_id || "saga") === a.id ? " selected" : "") + ">" + escapeHtml(a.name) + "</option>"; }).join("") + "</select></div>"
      + "<div class='wb-field'><label for='wfi-prompt'>" + escapeHtml(t("wf_prompt_lbl")) + "</label><textarea id='wfi-prompt' rows='4' class='wb-textarea'>" + escapeHtml(cfg.prompt || "") + "</textarea></div>";
  } else if (node.kind === "vault_search") {
    fields += "<div class='wb-field'><label for='wfi-query'>" + escapeHtml(t("wf_query_lbl")) + "</label><input id='wfi-query' type='text' value='" + escapeHtml(cfg.query || "{{input}}") + "' class='wb-input'/></div>";
  } else if (node.kind === "condition") {
    fields += "<div class='wb-field'><label for='wfi-contains'>" + escapeHtml(t("wf_contains_lbl")) + "</label><input id='wfi-contains' type='text' placeholder='e.g. urgent, approved, error' value='" + escapeHtml(cfg.contains || "") + "' class='wb-input'/></div>";
  } else if (node.kind === "generate_slides") {
    fields += "<div class='wb-field'><label for='wfi-title'>" + escapeHtml(t("wf_out_title")) + "</label><input id='wfi-title' type='text' value='" + escapeHtml(cfg.title || "Executive Brief") + "' class='wb-input'/></div>"
      + "<div class='wb-field'><label for='wfi-fmt'>" + escapeHtml(t("wf_out_fmt")) + "</label><select id='wfi-fmt' class='wb-select'><option value='pptx'" + (cfg.output_format !== "pdf" ? " selected" : "") + ">PowerPoint (.pptx)</option><option value='pdf'" + (cfg.output_format === "pdf" ? " selected" : "") + ">PDF Slides (16:9)</option></select></div>";
  } else if (node.kind === "save_guide") {
    fields += "<div class='wb-field'><label for='wfi-title'>" + escapeHtml(t("wf_out_title")) + "</label><input id='wfi-title' type='text' value='" + escapeHtml(cfg.title || "Workflow Note") + "' class='wb-input'/></div>"
      + "<div class='wb-field'><label for='wfi-sub'>" + escapeHtml(t("wf_subfolder_lbl")) + "</label><input id='wfi-sub' type='text' value='" + escapeHtml(cfg.subfolder || "workflows") + "' class='wb-input'/></div>";
  }
  const otherNodes = (wf.nodes || []).filter(function (n) { return n.id !== node.id; });
  const nodeOpts = function (cur) {
    return "<option value=''>" + escapeHtml(t("wf_no_next")) + "</option>"
      + otherNodes.map(function (n) { return "<option value='" + escapeHtml(n.id) + "'" + (n.id === cur ? " selected" : "") + ">" + escapeHtml(n.label) + "</option>"; }).join("");
  };
  if (node.kind === "condition") {
    const tEdge = (wf.edges || []).find(function (e) { return e.source === node.id && e.branch === "true"; });
    const fEdge = (wf.edges || []).find(function (e) { return e.source === node.id && e.branch === "false"; });
    fields += "<div class='wb-field'><label for='wfi-next-true' class='wf-branch-lbl-true'>" + escapeHtml(t("wf_true_next")) + "</label><div class='wf-branch-row'><select id='wfi-next-true' class='wb-select'>" + nodeOpts(tEdge ? tEdge.target : "") + "</select><button id='wfi-add-true-btn' type='button' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wf_add_branch_step")) + "</button></div></div>"
      + "<div class='wb-field'><label for='wfi-next-false' class='wf-branch-lbl-false'>" + escapeHtml(t("wf_false_next")) + "</label><div class='wf-branch-row'><select id='wfi-next-false' class='wb-select'>" + nodeOpts(fEdge ? fEdge.target : "") + "</select><button id='wfi-add-false-btn' type='button' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wf_add_branch_step")) + "</button></div></div>";
  } else {
    const outEdge = (wf.edges || []).find(function (e) { return e.source === node.id; });
    fields += "<div class='wb-field'><label for='wfi-next'>" + escapeHtml(t("wf_connect_next")) + "</label><select id='wfi-next' class='wb-select'>" + nodeOpts(outEdge ? outEdge.target : "") + "</select></div>";
  }
  const rmBtn = wf.nodes.length > 1 ? "<button id='wfi-remove-btn' type='button' class='wb-btn wb-btn-sm wb-btn-danger'>" + escapeHtml(t("wf_remove_step")) + "</button>" : "";
  box.innerHTML = "<div style='display:flex;flex-direction:column;gap:0.65rem'>"
    + "<div style='display:flex;align-items:center;justify-content:space-between'><span class='wf-node-badge'>" + escapeHtml(t(WF_KIND_KEYS[node.kind] || "wf_k_trigger")) + "</span>" + rmBtn + "</div>" + fields + "</div>";
  const bindVal = function (id, fn) { const el = document.getElementById(id); if (el) { el.addEventListener("change", function () { fn(el.value); renderWorkflowCanvas(wf); }); } };
  bindVal("wfi-label", function (v) { if (v.trim()) { node.label = v.trim(); } });
  bindVal("wfi-agent", function (v) { node.config.agent_id = v; });
  bindVal("wfi-prompt", function (v) { node.config.prompt = v; });
  bindVal("wfi-query", function (v) { node.config.query = v; });
  bindVal("wfi-contains", function (v) { node.config.contains = v; });
  bindVal("wfi-title", function (v) { node.config.title = v; });
  bindVal("wfi-fmt", function (v) { node.config.output_format = v; });
  bindVal("wfi-sub", function (v) { node.config.subfolder = v; });
  if (node.kind === "condition") {
    const bindBr = function (selId, addId, br) {
      const selEl = document.getElementById(selId), addEl = document.getElementById(addId);
      if (selEl) {
        selEl.addEventListener("change", function () {
          wf.edges = (wf.edges || []).filter(function (e) { return !(e.source === node.id && e.branch === br); });
          if (selEl.value) { wfConnectNodes(wf, node.id, selEl.value, br); }
          renderWorkflowCanvas(wf);
        });
      }
      if (addEl) { addEl.addEventListener("click", function () { wfAddStepNode("run_agent", node, br); }); }
    };
    bindBr("wfi-next-true", "wfi-add-true-btn", "true");
    bindBr("wfi-next-false", "wfi-add-false-btn", "false");
  } else {
    const nextSel = document.getElementById("wfi-next");
    if (nextSel) {
      nextSel.addEventListener("change", function () {
        wf.edges = (wf.edges || []).filter(function (e) { return e.source !== node.id; });
        if (nextSel.value) { wfConnectNodes(wf, node.id, nextSel.value, "default"); }
        renderWorkflowCanvas(wf);
      });
    }
  }
  const rm = document.getElementById("wfi-remove-btn");
  if (rm) {
    rm.addEventListener("click", function () {
      wf.nodes = wf.nodes.filter(function (n) { return n.id !== node.id; });
      wf.edges = wf.edges.filter(function (e) { return e.source !== node.id && e.target !== node.id; });
      wfSelectedNodeId = wf.nodes[0] ? wf.nodes[0].id : "";
      renderWorkflowsView();
    });
  }
}
function renderWorkflowRuns() {
  const liveBox = document.getElementById("wf-live-console"), histBox = document.getElementById("wf-runs-history");
  if (liveBox) {
    liveBox.innerHTML = wfLiveSteps.map(function (s) {
      return "<div class='wf-run-step'><div style='display:flex;justify-content:space-between;gap:0.4rem'><strong>" + escapeHtml(s.label) + "</strong><span class='wb-chip'>" + escapeHtml(t(WF_STAT_KEYS[s.status] || "wf_st_completed")) + (s.duration_ms ? (" · " + s.duration_ms + "ms") : "") + "</span></div>"
        + (s.artifact_note ? "<div style='color:var(--accent);font-size:calc(0.8rem * var(--ui-scale,1))'>" + escapeHtml(s.artifact_note) + "</div>" : "")
        + (s.output_preview ? "<div style='color:var(--text-muted);font-size:calc(0.78rem * var(--ui-scale,1));white-space:pre-wrap;max-height:5rem;overflow:auto'>" + escapeHtml(s.output_preview.slice(0, 260)) + "</div>" : "") + "</div>";
    }).join("");
  }
  if (histBox) {
    const runs = wfState.runs || [];
    if (!runs.length && !wfLiveSteps.length) { histBox.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("wf_empty_runs")) + "</div>"; return; }
    histBox.innerHTML = runs.slice(0, 12).map(function (r) {
      return "<div class='wf-run-step'><div style='display:flex;justify-content:space-between;gap:0.4rem'><strong>" + escapeHtml(r.workflow_name) + "</strong><span class='wb-chip'>" + escapeHtml(t(WF_STAT_KEYS[r.status] || "wf_st_completed")) + "</span></div>"
        + "<div style='font-size:calc(0.78rem * var(--ui-scale,1));color:var(--text-muted)'>" + escapeHtml((r.started_at || "").slice(0, 16).replace("T", " ")) + " · " + escapeHtml(t("wf_steps_n", { n: r.steps ? r.steps.length : 0 })) + "</div>"
        + (r.error ? "<div style='font-size:calc(0.78rem * var(--ui-scale,1));color:var(--status-danger)'>" + escapeHtml(r.error) + "</div>" : "") + "</div>";
    }).join("");
  }
}
function openWorkflowTemplatesModal() {
  const modal = document.getElementById("wf-templates-modal"), grid = document.getElementById("wf-tpl-grid");
  if (!modal || !grid) { return; }
  grid.innerHTML = (wfState.templates || []).map(function (tpl) {
    return "<article class='wf-tpl-card'><div style='display:flex;justify-content:space-between;gap:0.4rem;align-items:center'><span class='wf-node-badge'>" + escapeHtml(t(WF_TRIG_KEYS[tpl.trigger_kind] || "wf_trig_manual")) + "</span><span class='wb-chip'>" + escapeHtml(t("wf_steps_n", { n: tpl.node_count })) + "</span></div>"
      + "<h3 style='margin:0;font-size:calc(0.95rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(tpl.name) + "</h3>"
      + "<p style='margin:0;font-size:calc(0.84rem * var(--ui-scale,1));color:var(--text-muted);line-height:1.45;flex:1'>" + escapeHtml(tpl.description) + "</p>"
      + "<button type='button' data-wf-install-tpl='" + escapeHtml(tpl.id) + "' class='wb-btn wb-btn-sm wb-btn-primary'>" + escapeHtml(t("wf_use_template")) + "</button></article>";
  }).join("");
  grid.querySelectorAll("[data-wf-install-tpl]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const data = await wfApi("/api/workflows/from-template/" + encodeURIComponent(btn.getAttribute("data-wf-install-tpl") || ""), { method: "POST" });
      if (data) { wfLastFitId = ""; modal.close(); showToast(t("wf_installed_toast")); }
    });
  });
  modal.showModal();
}
async function runActiveWorkflowStream(inputText) {
  const wf = activeWorkflow(); if (!wf) { return; }
  await persistActiveWorkflow(false);
  wfNodeRunState = {}; wfLiveSteps = []; wfActiveRunId = "pending";
  setWorkflowSideTab("runs");
  const runBtn = document.getElementById("wf-run-btn"), stopBtn = document.getElementById("wf-stop-btn");
  if (runBtn) { runBtn.hidden = true; } if (stopBtn) { stopBtn.hidden = false; }
  renderWorkflowsView();
  const ctrl = new AbortController(); wfRunAbort = ctrl;
  const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
  try {
    const res = await areaFetch("/api/workflows/" + encodeURIComponent(wf.id) + "/run/stream", { method: "POST", headers: headers, signal: ctrl.signal, body: JSON.stringify({ input_text: inputText || wf.name, provider: providerEl ? providerEl.value : "ollama", model: (modelEl && modelEl.value) || "", trigger_source: "manual" }) });
    if (!res.ok) { const d = await safeJson(res); throw new Error(d.detail || "Workflow run failed"); }
    await readSseStream(res, function (evName, ev) {
      if (evName === "run_start") { wfActiveRunId = ev.run_id || ""; }
      else if (evName === "step_start") { wfNodeRunState[ev.node_id] = "running"; renderWorkflowCanvas(wf); }
      else if (evName === "step_done" && ev.step) { wfNodeRunState[ev.step.node_id] = ev.step.status; wfLiveSteps.push(ev.step); renderWorkflowCanvas(wf); renderWorkflowRuns(); }
      else if (evName === "step_skipped" && ev.step) { wfNodeRunState[ev.step.node_id] = "skipped"; wfLiveSteps.push(ev.step); renderWorkflowCanvas(wf); renderWorkflowRuns(); }
      else if (evName === "run_error") { showToast(ev.error || "Workflow failed", 4000); }
      else if (evName === "run_done" && ev.run) { showToast(ev.run.status === "cancelled" ? t("wf_run_stopped_toast") : t("wf_run_done_toast")); }
    }, function () { return ctrl.signal.aborted; });
  } catch (err) {
    if (!ctrl.signal.aborted) { showToast(err.message || "Workflow error", 3800); }
  } finally {
    wfActiveRunId = ""; wfRunAbort = null;
    if (runBtn) { runBtn.hidden = false; } if (stopBtn) { stopBtn.hidden = true; }
    await loadWorkflowsSummary();
    if (typeof loadWorkBoardSummary === "function") { loadWorkBoardSummary(true); }
    if (typeof loadImpactSummary === "function") { loadImpactSummary(); }
    if (typeof loadGuidesCatalog === "function") { loadGuidesCatalog(null); }
  }
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
function bindWorkflowStudioUX() {
  bindWorkflowToolbarFallback();
  if (typeof bindWorkflowCanvasViewportUX === "function") { bindWorkflowCanvasViewportUX(); }
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#wf-side-tablist [role='tab']", function (b) { setWorkflowSideTab(b.getAttribute("data-wf-side")); }); }
  document.querySelectorAll("[data-wf-side]").forEach(function (b) { b.addEventListener("click", function () { setWorkflowSideTab(b.getAttribute("data-wf-side")); }); });
  document.querySelectorAll("[data-wf-mode]").forEach(function (b) { b.addEventListener("click", function () { wfViewMode = b.getAttribute("data-wf-mode") || "canvas"; renderWorkflowsView(); }); });
  const sel = document.getElementById("wf-select");
  if (sel) { sel.addEventListener("change", function () { wfActiveId = sel.value; wfSelectedNodeId = ""; wfNodeRunState = {}; wfLiveSteps = []; wfLastFitId = ""; renderWorkflowsView(); if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); } }); }
  ["wf-templates-btn", "wf-empty-tpl-btn"].forEach(function (id) { const el = document.getElementById(id); if (el) { el.addEventListener("click", openWorkflowTemplatesModal); } });
  ["wf-new-btn", "wf-empty-new-btn"].forEach(function (id) { const el = document.getElementById(id); if (el) { el.addEventListener("click", createBlankWorkflowAndOpen); } });
  const nameIn = document.getElementById("wf-name-in"), trigSel = document.getElementById("wf-trig-sel"), schIn = document.getElementById("wf-sched-mins");
  if (nameIn) {
    nameIn.addEventListener("input", function () {
      const wf = activeWorkflow(); if (!wf) { return; }
      const v = nameIn.value.trim();
      if (v) { wf.name = v; if (sel && sel.selectedOptions && sel.selectedOptions[0]) { sel.selectedOptions[0].textContent = v; } if (typeof renderDrawerDynamicLists === "function") { renderDrawerDynamicLists(); } }
    });
  }
  if (trigSel) {
    trigSel.addEventListener("change", function () {
      const wf = activeWorkflow(); if (!wf) { return; }
      wf.trigger_kind = trigSel.value;
      if (wf.trigger_kind === "schedule" && !wf.schedule_minutes) { wf.schedule_minutes = 60; }
      const trigNode = (wf.nodes || []).find(function (n) { return n.kind === "trigger"; });
      if (trigNode) { trigNode.config = Object.assign({}, trigNode.config, { trigger_kind: wf.trigger_kind }); trigNode.label = t(WF_TRIG_KEYS[wf.trigger_kind] || "wf_trig_manual"); }
      renderWorkflowsView();
    });
  }
  if (schIn) { schIn.addEventListener("change", function () { const wf = activeWorkflow(); if (wf) { wf.schedule_minutes = Math.max(5, Number(schIn.value || 60)); renderWorkflowsView(); } }); }
  const addNodeBtn = document.getElementById("wf-add-node-btn"), addGwBtn = document.getElementById("wf-add-gateway-btn");
  if (addNodeBtn) { addNodeBtn.addEventListener("click", function () { wfAddStepNode(document.getElementById("wf-add-kind").value || "run_agent"); }); }
  if (addGwBtn) { addGwBtn.addEventListener("click", function () { wfAddStepNode("condition"); const c = document.getElementById("wfi-contains"); if (c) { c.focus(); } }); }
  const saveBtn = document.getElementById("wf-save-btn"), delBtn = document.getElementById("wf-delete-btn"), runBtn = document.getElementById("wf-run-btn"), stopBtn = document.getElementById("wf-stop-btn");
  if (saveBtn) { saveBtn.addEventListener("click", function () { persistActiveWorkflow(true); }); }
  if (delBtn) {
    delBtn.addEventListener("click", async function () {
      const wf = activeWorkflow(); if (!wf) { return; }
      if (typeof confirmDeletion === "function" && !(await confirmDeletion(t("wf_del_confirm_t"), t("wf_del_confirm_m", { name: wf.name }), t("delete_btn")))) { return; }
      const res = await wfApi("/api/workflows/" + encodeURIComponent(wf.id), { method: "DELETE" });
      if (res) { showToast(t("wf_deleted_toast")); }
    });
  }
  if (runBtn) { runBtn.addEventListener("click", function () { const m = document.getElementById("wf-run-modal"); if (m) { m.showModal(); document.getElementById("wf-run-input").focus(); } }); }
  const runForm = document.getElementById("wf-run-form");
  if (runForm) { runForm.addEventListener("submit", function (e) { e.preventDefault(); document.getElementById("wf-run-modal").close(); runActiveWorkflowStream(document.getElementById("wf-run-input").value.trim()); }); }
  if (stopBtn) {
    stopBtn.addEventListener("click", async function () {
      if (wfActiveRunId && wfActiveRunId !== "pending") { await areaFetch("/api/workflows/runs/" + encodeURIComponent(wfActiveRunId) + "/cancel", { method: "POST" }); }
      if (wfRunAbort) { wfRunAbort.abort(); }
    });
  }
}
"""
