"""Right Sidebar Context-Aware REALM Copilot: Live Q&A, Inline Diff Previews & 1-Click Apply/Undo Actions."""

COPILOT_SCRIPT: str = r"""
const cpThreads = new Map();
let cpController = null, cpStreaming = false, cpRenderedKey = "";
const CP_BADGE_LABELS = { update_document: "DOCUMENT", create_note: "NEW NOTE", create_task: "TASK", update_task: "UPDATE TASK", create_event: "CALENDAR", create_goal: "GOAL", upsert_agent: "AGENT", upsert_workflow: "WORKFLOW" };
const CP_EVENT_KINDS = new Set(["event", "focus", "milestone", "deadline"]), CP_PRIOS = new Set(["low", "medium", "high", "urgent"]);

function cpActiveFileTab() {
  const fv = document.getElementById("center-file-view");
  if (!fv || fv.hidden || typeof centerChatTabs === "undefined") { return null; }
  const tb = centerChatTabs.find(function (item) { return item.id === activeCenterTabId; });
  return tb && tb.kind === "file" ? tb : null;
}

function cpCurrentViewKind() {
  if (cpActiveFileTab()) { return "file"; }
  if (typeof wbViewOpen !== "undefined" && wbViewOpen) { return "work"; }
  if (typeof focViewOpen !== "undefined" && focViewOpen) { return "focus"; }
  if (typeof impViewOpen !== "undefined" && impViewOpen) { return "impact"; }
  if (typeof wfViewOpen !== "undefined" && wfViewOpen) { return "workflows"; }
  const gv = document.getElementById("graph-view");
  if (gv && !gv.classList.contains("hidden")) { return "graph"; }
  if (document.getElementById("library-view") || document.getElementById("reader-heading")) { return "library"; }
  return "chat";
}

function cpActiveWf() {
  if (typeof activeWorkflow === "function") { return activeWorkflow(); }
  if (typeof wfState === "undefined" || !Array.isArray(wfState.workflows)) { return null; }
  const id = typeof wfActiveId !== "undefined" ? wfActiveId : "";
  return wfState.workflows.find(function (w) { return w.id === id; }) || wfState.workflows[0] || null;
}

function cpContextKey() {
  const f = cpActiveFileTab();
  if (f) { return "file:" + f.docId; }
  const v = cpCurrentViewKind();
  if (v === "workflows") { const wf = cpActiveWf(); if (wf && wf.id) { return "wf:" + wf.id; } }
  return "view:" + v;
}

function cpGetThread() {
  const key = cpContextKey();
  if (!cpThreads.has(key)) { cpThreads.set(key, []); }
  return cpThreads.get(key);
}

function cpContextLabel() {
  const f = cpActiveFileTab();
  if (f) { return f.filename || f.title || "Document"; }
  const v = cpCurrentViewKind();
  if (v === "work") { return t("work_board_nav"); }
  if (v === "focus") { return t("focus_nav"); }
  if (v === "impact") { return t("impact_nav"); }
  if (v === "workflows") { const wf = cpActiveWf(); return (wf && wf.name) || t("workflows_nav"); }
  if (v === "library") { return t("library"); }
  if (v === "graph") { return t("graph_view"); }
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  return dirs.length === 1 && typeof areaTitle === "function" ? areaTitle(dirs[0]) : (dirs.length > 1 ? t("areas_active_n", { n: dirs.length }) : t("no_ws_short"));
}

function cpCollectContext() {
  const view = cpCurrentViewKind(), ft = cpActiveFileTab();
  let docContent = "";
  if (ft) {
    const ta = document.getElementById("cf-editor-ta");
    docContent = ta ? ta.value : (ft.rawContent || "");
    if (!docContent && typeof allGuides !== "undefined" && Array.isArray(allGuides)) {
      const g = allGuides.find(function (item) { return item.doc_id === ft.docId; });
      if (g && Array.isArray(g.sections)) { docContent = g.sections.map(function (s) { return "## " + s.section_title + "\n" + (s.content || ""); }).join("\n\n"); }
    }
  }
  let workSummary = "";
  if (typeof wbState !== "undefined" && wbState) {
    const cols = (wbState.columns || []).map(function (c) { return c.id + ":" + c.title; }).join(", ");
    const projs = (wbState.projects || []).slice(0, 12).map(function (p) { return p.id + ":" + p.title; }).join(", ");
    const tasks = (wbState.tasks || []).slice(0, 25).map(function (tk) { return "- [" + tk.id + "] " + tk.title + " (col=" + tk.column_id + ", prio=" + tk.priority + (tk.due_date ? ", due=" + tk.due_date : "") + ")"; }).join("\n");
    if (cols || tasks) { workSummary = "Columns: " + cols + (projs ? "\nProjects: " + projs : "") + (tasks ? "\nTasks:\n" + tasks : ""); }
  }
  const activeWf = cpActiveWf();
  const workflowSummary = activeWf ? JSON.stringify({ id: activeWf.id, name: activeWf.name, trigger_kind: activeWf.trigger_kind, nodes: activeWf.nodes, edges: activeWf.edges }).slice(0, 4400) : "";
  const agentsSummary = typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length ? agentTeam.map(function (a) { return a.id + " (" + a.name + " · " + a.role + " · palette=" + a.palette + ")"; }).join("\n").slice(0, 3800) : "";
  return { view: view, doc_id: ft ? String(ft.docId || "") : "", filename: ft ? String(ft.filename || "") : "", doc_content: String(docContent || "").slice(0, 23000), doc_readonly: ft ? Boolean(ft.readOnly) : false, work_summary: workSummary.slice(0, 5800), workflow_summary: workflowSummary, agents_summary: agentsSummary };
}

function cpStartersForView() {
  const v = cpCurrentViewKind();
  return v === "file" ? [t("cp_st_doc_1"), t("cp_st_doc_2"), t("cp_st_doc_3")] : (v === "workflows" ? [t("cp_st_wf_1"), t("cp_st_gen_1")] : [t("cp_st_work_1"), t("cp_st_gen_1")]);
}

function cpPreviewDetailsHtml(act) {
  if (act.kind === "update_document" && (act.diff_before || act.diff_after)) {
    const fmt = function (txt, pfx) { return String(txt || "").split("\n").map(function (l) { return pfx + l; }).join("\n"); };
    return "<div class='cp-diff'>"
      + (act.diff_before ? ("<div class='cp-diff-del'>" + escapeHtml(fmt(act.diff_before, "- ")) + "</div>") : "")
      + (act.diff_after ? ("<div class='cp-diff-add'>" + escapeHtml(fmt(act.diff_after, "+ ")) + "</div>") : "")
      + "</div>";
  }
  const p = act.payload || {}, lines = [];
  if (p.title && act.kind !== "update_document") { lines.push("Title: " + p.title); }
  if (p.name) { lines.push("Name: " + p.name + (p.role ? " · " + p.role : "")); }
  if (p.priority) { lines.push("Priority: " + p.priority + (p.due_date ? " · Due " + p.due_date : "")); }
  if (p.date) { lines.push("Date: " + p.date + (p.start_time ? " " + p.start_time : "") + (p.end_time ? "–" + p.end_time : "")); }
  if (Array.isArray(p.nodes)) { lines.push("Steps: " + p.nodes.map(function (n) { return n.label || n.kind; }).join(" → ")); }
  return lines.length ? ("<div class='cp-diff'><div class='cp-diff-add'>" + escapeHtml(lines.join("\n")) + "</div></div>") : "";
}

function cpRenderActionCard(act, mIdx, aIdx) {
  const badge = CP_BADGE_LABELS[act.kind] || act.kind, st = act.status || "pending";
  let footer = "";
  if (st === "applied") {
    const undoBtn = act.kind === "update_document" && act.prevContent !== undefined
      ? "<button type='button' data-cp-undo='" + mIdx + ":" + aIdx + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("cp_undo")) + "</button>" : "";
    const openBtn = act.createdDocId
      ? "<button type='button' data-cp-open-doc='" + escapeHtml(act.createdDocId) + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("cp_open")) + "</button>" : "";
    footer = "<div class='cp-act-btns'><span class='cp-act-done'>✓ " + escapeHtml(t("cp_applied")) + "</span>" + undoBtn + openBtn + "</div>";
  } else if (st === "dismissed") {
    footer = "<div class='cp-act-btns'><span class='text-xs text-[#738196]'>" + escapeHtml(t("cp_dismiss")) + "</span></div>";
  } else {
    const busy = st === "applying";
    footer = "<div class='cp-act-btns'>"
      + "<button type='button' data-cp-apply='" + mIdx + ":" + aIdx + "'" + (busy ? " disabled" : "") + " class='wb-btn wb-btn-sm wb-btn-primary'>" + escapeHtml(busy ? t("cp_applying") : t("cp_apply")) + "</button>"
      + "<button type='button' data-cp-dismiss='" + mIdx + ":" + aIdx + "'" + (busy ? " disabled" : "") + " class='wb-btn wb-btn-sm'>" + escapeHtml(t("cp_dismiss")) + "</button>"
      + (act.error ? ("<span class='text-xs text-[#FCA5A5]'>" + escapeHtml(act.error) + "</span>") : "")
      + "</div>";
  }
  return "<div class='cp-action-card" + (st === "applied" ? " is-applied" : (st === "dismissed" ? " is-dismissed" : "")) + "'>"
    + "<div class='cp-act-head'><span class='cp-act-badge'>" + escapeHtml(badge) + "</span></div>"
    + "<div class='cp-act-title'>" + escapeHtml(act.title || badge) + "</div>"
    + (act.summary ? ("<div class='cp-act-sum'>" + escapeHtml(act.summary) + "</div>") : "")
    + cpPreviewDetailsHtml(act) + footer + "</div>";
}

function renderCopilotThread() {
  const box = document.getElementById("cp-messages"); if (!box) { return; }
  cpRenderedKey = cpContextKey();
  const msgs = cpGetThread();
  if (!msgs.length) {
    const starters = cpStartersForView().map(function (s) {
      return "<button type='button' data-cp-starter='" + escapeHtml(s) + "' class='cp-starter-btn'>↳ " + escapeHtml(s) + "</button>";
    }).join("");
    box.innerHTML = "<div class='cp-empty'><h3 class='cp-empty-title'>" + escapeHtml(t("cp_empty_t")) + "</h3><p class='cp-empty-desc'>" + escapeHtml(t("cp_empty_d")) + "</p><div class='cp-starters'>" + starters + "</div></div>";
    box.querySelectorAll("[data-cp-starter]").forEach(function (b) {
      b.addEventListener("click", function () { cpSendPrompt(b.getAttribute("data-cp-starter") || ""); });
    });
    return;
  }
  box.innerHTML = msgs.map(function (m, mIdx) {
    if (m.role === "user") { return "<div class='cp-msg-user'>" + escapeHtml(m.content) + "</div>"; }
    const body = m.streaming && !m.content
      ? "<span class='text-xs font-mono text-[#738196]'>" + escapeHtml(t("cp_thinking")) + "</span>"
      : (m.content ? ("<div class='md-body" + (m.streaming ? " is-streaming" : "") + " flex flex-col gap-2'>" + formatMarkdown(m.content, Boolean(m.streaming), 4) + "</div>") : "");
    const cards = Array.isArray(m.actions) && m.actions.length
      ? m.actions.map(function (a, aIdx) { return cpRenderActionCard(a, mIdx, aIdx); }).join("") : "";
    const metaHtml = typeof cpMsgMetaHtml === "function" ? cpMsgMetaHtml(m.meta) : "";
    return "<div class='cp-msg-ai'>" + metaHtml + body + (m.error ? ("<div class='text-xs text-[#FCA5A5]'>" + escapeHtml(m.error) + "</div>") : "") + cards + "</div>";
  }).join("");
  box.querySelectorAll("[data-cp-apply]").forEach(function (b) {
    b.addEventListener("click", function () { const [mi, ai] = (b.getAttribute("data-cp-apply") || "").split(":").map(Number); cpApplyAction(mi, ai); });
  });
  box.querySelectorAll("[data-cp-dismiss]").forEach(function (b) {
    b.addEventListener("click", function () { const [mi, ai] = (b.getAttribute("data-cp-dismiss") || "").split(":").map(Number); const m = cpGetThread()[mi]; if (m && m.actions && m.actions[ai]) { m.actions[ai].status = "dismissed"; renderCopilotThread(); } });
  });
  box.querySelectorAll("[data-cp-undo]").forEach(function (b) {
    b.addEventListener("click", function () { const [mi, ai] = (b.getAttribute("data-cp-undo") || "").split(":").map(Number); cpUndoDocAction(mi, ai); });
  });
  box.querySelectorAll("[data-cp-open-doc]").forEach(function (b) {
    b.addEventListener("click", function () { if (typeof openFileInCenterTab === "function") { openFileInCenterTab(b.getAttribute("data-cp-open-doc") || ""); } });
  });
  box.scrollTop = box.scrollHeight;
}

function syncCopilotContextUI(force) {
  if (force && typeof syncCopilotControls === "function") { syncCopilotControls(); }
  if (force || cpRenderedKey !== cpContextKey()) { renderCopilotThread(); }
}

function cpSetBusy(busy) {
  cpStreaming = Boolean(busy);
  const btn = document.getElementById("cp-send-btn");
  if (!btn) { return; }
  btn.type = cpStreaming ? "button" : "submit";
  btn.classList.toggle("is-stop", cpStreaming);
  btn.textContent = cpStreaming ? "■" : "↑";
  btn.setAttribute("aria-label", cpStreaming ? t("stop_generating") : t("submit_query"));
}

async function cpJsonReq(url, method, body, useArea) {
  const fn = useArea ? areaFetch : fetch;
  const res = await fn(url, { method: method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await safeJson(res);
  if (!res.ok) { throw new Error((data && data.detail) || "Action failed."); }
  return data;
}

async function cpSyncDocUi(docId, nextText, data) {
  const tab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; }) : null;
  if (tab) { tab.rawContent = nextText; tab.dirty = false; if (activeCenterTabId === tab.id && typeof renderCenterFileTab === "function") { renderCenterFileTab(tab); } }
  if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
  if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
  if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
}

async function cpSyncWorkUi() {
  if (typeof loadWorkBoardSummary === "function") { await loadWorkBoardSummary(true); }
  if (typeof wbViewOpen !== "undefined" && wbViewOpen && typeof renderWorkBoardAll === "function") { renderWorkBoardAll(); }
  if (typeof broadcastToEmbedFrames === "function") { broadcastToEmbedFrames({ type: "realm:sync-area" }); }
}

async function cpApplyAction(mIdx, aIdx) {
  const m = cpGetThread()[mIdx], act = m && m.actions && m.actions[aIdx];
  if (!act || act.status === "applying" || act.status === "applied") { return; }
  act.status = "applying"; act.error = ""; renderCopilotThread();
  const p = act.payload || {};
  try {
    if (act.kind === "update_document") {
      const docId = String(p.doc_id || ""), nextText = String(p.content || "");
      const tab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; }) : null;
      act.prevContent = tab && tab.rawContent !== null ? tab.rawContent : cpCollectContext().doc_content;
      const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(docId) : encodeURIComponent(docId);
      await cpSyncDocUi(docId, nextText, await cpJsonReq("/api/guides/" + enc + "/raw", "PUT", { content: nextText }, true));
    } else if (act.kind === "create_note") {
      const data = await cpJsonReq("/api/guides/create", "POST", { title: p.title || "Untitled Note", content: p.content || "", subfolder: p.subfolder || "", tags: Array.isArray(p.tags) ? p.tags : [] }, true);
      act.createdDocId = data.doc_id || "";
      if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
    } else if (act.kind === "create_task") {
      const prio = CP_PRIOS.has(p.priority) ? p.priority : "medium";
      await cpJsonReq("/api/work-board/tasks", "POST", { title: p.title, description: p.description || "", priority: prio, due_date: p.due_date || "", column_id: p.column_id || "", project_id: p.project_id || "", linked_doc_id: p.linked_doc_id || (cpActiveFileTab() ? cpActiveFileTab().docId : "") }, true);
      await cpSyncWorkUi();
    } else if (act.kind === "update_task") {
      const patch = {};
      for (const k of ["title", "description", "priority", "due_date", "column_id", "project_id"]) { if (p[k] !== undefined && p[k] !== "") { patch[k] = k === "priority" && !CP_PRIOS.has(p[k]) ? "medium" : p[k]; } }
      await cpJsonReq("/api/work-board/tasks/" + encodeURIComponent(String(p.task_id || "")), "PATCH", patch, true);
      await cpSyncWorkUi();
    } else if (act.kind === "create_event") {
      const evKind = CP_EVENT_KINDS.has(p.kind) ? p.kind : "event";
      await cpJsonReq("/api/work-board/events", "POST", { title: p.title, date: p.date || new Date().toISOString().slice(0, 10), start_time: p.start_time || "", end_time: p.end_time || "", kind: evKind, notes: p.notes || "" }, true);
      await cpSyncWorkUi();
    } else if (act.kind === "create_goal") {
      const today = new Date().toISOString().slice(0, 10), end = new Date(Date.now() + 84 * 86400000).toISOString().slice(0, 10);
      await cpJsonReq("/api/focus/goals", "POST", { title: p.title, why: p.why || "", target_hours: Math.max(1, Number(p.target_hours || 20)), start_date: p.start_date || today, end_date: p.end_date || end }, true);
      if (typeof loadFocusSummary === "function") { await loadFocusSummary(); }
      if (typeof focViewOpen !== "undefined" && focViewOpen && typeof renderFocusView === "function") { renderFocusView(); }
    } else if (act.kind === "upsert_agent") {
      await cpJsonReq("/api/agents", "POST", { id: p.id || "", name: p.name, role: p.role || "Specialist", tagline: p.tagline || "", palette: p.palette || "realm", temperature: Number(p.temperature ?? 0.2), instructions: p.instructions || "" }, false);
      if (typeof loadAgentTeam === "function") { await loadAgentTeam(); }
    } else if (act.kind === "upsert_workflow") {
      const wfId = String(p.workflow_id || "").trim();
      const data = await cpJsonReq(wfId ? ("/api/workflows/" + encodeURIComponent(wfId)) : "/api/workflows", wfId ? "PATCH" : "POST", { name: p.name, description: p.description || "", trigger_kind: p.trigger_kind || "manual", schedule_minutes: Number(p.schedule_minutes || 0), nodes: p.nodes || [], edges: p.edges || [] }, true);
      if (typeof loadWorkflowsSummary === "function") { await loadWorkflowsSummary(); }
      if (data.item && data.item.id && typeof wfActiveId !== "undefined") { wfActiveId = data.item.id; }
      if (typeof wfViewOpen !== "undefined" && wfViewOpen && typeof renderWorkflowsView === "function") { renderWorkflowsView(); }
    }
    act.status = "applied";
    if (typeof showToast === "function") { showToast("✓ " + (act.title || t("cp_applied")), 2600); }
  } catch (err) {
    act.status = "pending"; act.error = (err && err.message) || "Action failed.";
  }
  renderCopilotThread();
}

async function cpUndoDocAction(mIdx, aIdx) {
  const m = cpGetThread()[mIdx], act = m && m.actions && m.actions[aIdx];
  if (!act || act.kind !== "update_document" || act.prevContent === undefined) { return; }
  const docId = String((act.payload && act.payload.doc_id) || "");
  try {
    const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(docId) : encodeURIComponent(docId);
    await cpSyncDocUi(docId, act.prevContent, await cpJsonReq("/api/guides/" + enc + "/raw", "PUT", { content: act.prevContent }, true));
    act.status = "pending";
    if (typeof showToast === "function") { showToast(t("cp_undo") + " ✓", 2200); }
    renderCopilotThread();
  } catch (_e) {}
}

async function cpSendPrompt(rawText) {
  const text = String(rawText || "").trim();
  if (!text || cpStreaming) { return; }
  const inp = document.getElementById("cp-input");
  if (inp) { inp.value = ""; inp.style.height = "auto"; }
  const thread = cpGetThread();
  thread.push({ role: "user", content: text });
  const cfg = typeof cpResolveRequestConfig === "function" ? cpResolveRequestConfig() : { agentId: "saga", agentName: "Saga", provider: "ollama", model: null, formatId: null, formatName: "" };
  const aiMsg = { role: "assistant", content: "", streaming: true, actions: [], error: "", meta: { agent_name: cfg.agentName, model: cfg.model || "", format_name: cfg.formatName || "" } };
  thread.push(aiMsg);
  renderCopilotThread(); cpSetBusy(true);
  const ctrl = new AbortController(); cpController = ctrl;
  const payloadMsgs = thread.slice(0, -1).filter(function (m) { return m.content && (m.role === "user" || m.role === "assistant"); }).slice(-16).map(function (m) { return { role: m.role, content: m.content }; });
  try {
    const apiKey = typeof getApiKey === "function" ? getApiKey() : "";
    const headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/copilot/chat/stream", {
      method: "POST", headers: headers, signal: ctrl.signal,
      body: JSON.stringify({ messages: payloadMsgs, context: cpCollectContext(), provider: cfg.provider, model: cfg.model, api_key: apiKey || null, agent_id: cfg.agentId, format_id: cfg.formatId }),
    });
    if (!res.ok) { const e = await safeJson(res); throw new Error((e && e.detail) || "Copilot unavailable."); }
    await readSseStream(res, function (ev, d) {
      if (ev === "meta" && d) { aiMsg.meta = d; renderCopilotThread(); }
      else if (ev === "token" && d && d.delta) { aiMsg.content += String(d.delta); renderCopilotThread(); }
      else if (ev === "done" && d) {
        if (d.meta) { aiMsg.meta = d.meta; }
        if (typeof d.reply === "string") { aiMsg.content = d.reply; }
        aiMsg.actions = Array.isArray(d.actions) ? d.actions.map(function (a) { return Object.assign({}, a, { status: "pending" }); }) : [];
      } else if (ev === "error") { throw new Error((d && d.detail) || "Copilot error."); }
    }, function () { return ctrl.signal.aborted; });
  } catch (err) {
    if (!err || err.name !== "AbortError") { aiMsg.error = (err && err.message) || "Copilot request failed."; }
  } finally {
    aiMsg.streaming = false;
    if (cpController === ctrl) { cpController = null; }
    cpSetBusy(false); renderCopilotThread();
  }
}

function openCopilotForCurrentContext() {
  if (typeof setRightSidebarOpen === "function") { setRightSidebarOpen(true, "copilot"); }
  syncCopilotContextUI(true);
  const inp = document.getElementById("cp-input");
  if (inp) { inp.focus({ preventScroll: true }); }
}

function bindCopilotUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const form = document.getElementById("cp-form"), inp = document.getElementById("cp-input"), sendBtn = document.getElementById("cp-send-btn"), clrBtn = document.getElementById("cp-clear-btn");
  if (form) { form.addEventListener("submit", function (e) { e.preventDefault(); cpSendPrompt(inp ? inp.value : ""); }); }
  if (sendBtn) { sendBtn.addEventListener("click", function () { if (cpStreaming && cpController) { cpController.abort(); } }); }
  if (clrBtn) { clrBtn.addEventListener("click", function () { if (cpStreaming && cpController) { cpController.abort(); } cpThreads.set(cpContextKey(), []); renderCopilotThread(); if (inp) { inp.focus({ preventScroll: true }); } }); }
  if (inp) {
    inp.addEventListener("input", function () { inp.style.height = "auto"; inp.style.height = Math.min(120, inp.scrollHeight) + "px"; });
    inp.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); cpSendPrompt(inp.value); }
    });
  }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j" && !document.querySelector("dialog[open]")) {
      e.preventDefault();
      const already = typeof wbLayout !== "undefined" && wbLayout.rightOpen && wbLayout.rightTab === "copilot";
      if (already) { setRightSidebarOpen(false); } else { openCopilotForCurrentContext(); }
    }
  });
  syncCopilotContextUI(true);
}
"""
