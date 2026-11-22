"""Modal controllers, task extraction helper, and event bindings for Work Board."""

WORK_BOARD_MODALS_SCRIPT: str = r"""
function renderEditingSubtasks() {
  const box = document.getElementById("wb-tf-subtasks"); if (!box) { return; }
  box.innerHTML = wbEditingSubtasks.map(function (s, idx) {
    return "<div class='wb-subtask-row'><input type='checkbox' data-sub-toggle='" + idx + "' aria-label='" + escapeHtml(s.title) + "'" + (s.done ? " checked" : "") + " />"
      + "<span style='" + (s.done ? "text-decoration:line-through;opacity:0.65" : "") + "'>" + escapeHtml(s.title) + "</span>"
      + "<button type='button' data-sub-del='" + idx + "' aria-label='Remove subtask' class='wb-icon-btn' style='width:1.4rem;height:1.4rem'>✕</button></div>";
  }).join("");
  box.querySelectorAll("[data-sub-toggle]").forEach(function (cb) {
    cb.addEventListener("change", function () { const i = Number(cb.getAttribute("data-sub-toggle")); if (wbEditingSubtasks[i]) { wbEditingSubtasks[i].done = cb.checked; renderEditingSubtasks(); } });
  });
  box.querySelectorAll("[data-sub-del]").forEach(function (btn) {
    btn.addEventListener("click", function () { wbEditingSubtasks.splice(Number(btn.getAttribute("data-sub-del")), 1); renderEditingSubtasks(); });
  });
}
function openWorkTaskModal(taskId) {
  const modal = document.getElementById("work-task-modal"); if (!modal) { return; }
  const tk = taskId ? (wbState.tasks || []).find(function (item) { return item.id === taskId; }) : null;
  document.getElementById("wb-task-modal-title").textContent = tk ? t("wb_edit_task") : t("wb_task_modal_new");
  document.getElementById("wb-tf-id").value = tk ? tk.id : "";
  document.getElementById("wb-tf-title").value = tk ? tk.title : "";
  document.getElementById("wb-tf-desc").value = tk ? (tk.description || "") : "";
  populateColumnSelect(document.getElementById("wb-tf-col"), tk ? tk.column_id : ((wbState.columns[0] && wbState.columns[0].id) || "todo"));
  populateProjectSelect(document.getElementById("wb-tf-project"), tk ? tk.project_id : wbProjectFilter, true);
  document.getElementById("wb-tf-priority").value = tk ? (tk.priority || "medium") : "medium";
  document.getElementById("wb-tf-recur").value = tk ? (tk.recurrence || "none") : "none";
  document.getElementById("wb-tf-due").value = tk ? (tk.due_date || "") : "";
  document.getElementById("wb-tf-tags").value = tk && tk.tags ? tk.tags.join(", ") : "";
  document.getElementById("wb-tf-start").value = tk ? (tk.scheduled_start || "") : "";
  document.getElementById("wb-tf-end").value = tk ? (tk.scheduled_end || "") : "";
  wbEditingSubtasks = tk && tk.subtasks ? tk.subtasks.map(function (s) { return Object.assign({}, s); }) : [];
  renderEditingSubtasks();
  const linksEl = document.getElementById("wb-tf-links");
  if (linksEl) {
    const lnks = [];
    if (tk && tk.linked_doc_id) { lnks.push("<button type='button' id='wb-tf-open-doc' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_open_guide_link")) + "</button>"); }
    if (tk && tk.linked_chat_id) { lnks.push("<button type='button' id='wb-tf-open-chat' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_open_chat_link")) + "</button>"); }
    linksEl.hidden = !lnks.length; linksEl.innerHTML = lnks.join("");
    const dBtn = document.getElementById("wb-tf-open-doc"), cBtn = document.getElementById("wb-tf-open-chat");
    if (dBtn && tk) { dBtn.addEventListener("click", async function () { modal.close(); closeWorkBoardView(); const g = (await loadGuidesCatalog(null)).find(function (x) { return x.doc_id === tk.linked_doc_id; }); if (g) { renderGuideReader(g, null); } }); }
    if (cBtn && tk) { cBtn.addEventListener("click", function () { modal.close(); closeWorkBoardView(); openSavedChat(tk.linked_chat_id); }); }
  }
  const delBtn = document.getElementById("wb-tf-delete"); if (delBtn) { delBtn.hidden = !tk; }
  const askBtn = document.getElementById("wb-tf-ask-chat"); if (askBtn) { askBtn.hidden = !tk; }
  modal.showModal(); document.getElementById("wb-tf-title").focus();
}
function openWorkProjectModal(projectId) {
  const modal = document.getElementById("work-project-modal"); if (!modal) { return; }
  const proj = projectId ? wbProjectById(projectId) : null;
  document.getElementById("wb-proj-modal-title").textContent = proj ? t("wb_edit_project") : t("wb_proj_modal_new");
  document.getElementById("wb-pf-id").value = proj ? proj.id : "";
  document.getElementById("wb-pf-title").value = proj ? proj.title : "";
  document.getElementById("wb-pf-desc").value = proj ? (proj.description || "") : "";
  document.getElementById("wb-pf-status").value = proj ? (proj.status || "active") : "active";
  document.getElementById("wb-pf-color").value = proj ? (proj.color || "#4BB8E8") : "#4BB8E8";
  document.getElementById("wb-pf-target").value = proj ? (proj.target_date || "") : "";
  document.getElementById("wb-pf-hours").value = proj ? String(proj.target_hours || 0) : "0";
  const delBtn = document.getElementById("wb-pf-delete"); if (delBtn) { delBtn.hidden = !proj; }
  modal.showModal(); document.getElementById("wb-pf-title").focus();
}
async function extractTasksToBoard(opts) {
  const o = opts || {}, apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
  const body = {
    chat_id: o.chat_id || "", turn_index: o.turn_index !== undefined ? o.turn_index : null, doc_id: o.doc_id || "",
    text: o.text || "", project_id: o.project_id !== undefined ? o.project_id : wbProjectFilter,
    column_id: o.column_id || "", use_ai: o.use_ai !== false, save: true,
    provider: providerEl ? providerEl.value : "ollama", model: (modelEl && modelEl.value) || "", language: activeLanguage || "en",
  };
  const data = await wbApi("/api/work-board/extract", { method: "POST", headers: headers, body: JSON.stringify(body) });
  if (data) { showToast(t("wb_extracted_toast", { n: data.created_count || 0 })); }
  return data;
}
function bindWorkBoardUX() {
  const sideBtn = document.getElementById("sidebar-work-btn");
  if (sideBtn) { sideBtn.addEventListener("click", function () { openWorkBoardView(); }); }
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#wb-tablist [data-wb-tab]", function (btn) { setWorkBoardTab(btn.getAttribute("data-wb-tab")); }); }
  document.querySelectorAll("[data-wb-tab]").forEach(function (btn) { btn.addEventListener("click", function () { setWorkBoardTab(btn.getAttribute("data-wb-tab")); }); });
  const projFilter = document.getElementById("wb-project-filter");
  if (projFilter) { projFilter.addEventListener("change", function () { wbProjectFilter = projFilter.value; renderWorkBoardAll(); }); }
  const addBtn = document.getElementById("wb-add-task-btn"), newProjBtn = document.getElementById("wb-new-project-btn");
  if (addBtn) { addBtn.addEventListener("click", function () { openWorkTaskModal(null); }); }
  if (newProjBtn) { newProjBtn.addEventListener("click", function () { openWorkProjectModal(null); }); }
  const extBtn = document.getElementById("wb-extract-open-btn");
  if (extBtn) {
    extBtn.addEventListener("click", function () {
      populateProjectSelect(document.getElementById("wb-ext-project"), wbProjectFilter, true);
      populateColumnSelect(document.getElementById("wb-ext-col"), (wbState.columns[0] && wbState.columns[0].id) || "todo");
      document.getElementById("work-extract-modal").showModal(); document.getElementById("wb-ext-text").focus();
    });
  }
  const syncBtn = document.getElementById("wb-sync-vault-btn");
  if (syncBtn) {
    syncBtn.addEventListener("click", async function () {
      const res = await areaFetch("/api/work-board/sync-vault", { method: "POST" }), data = await safeJson(res);
      if (!res.ok) { showToast(data.detail || "Sync failed", 3500); return; }
      showToast(t("wb_synced_toast")); if (typeof loadGuidesCatalog === "function") { loadGuidesCatalog(null); }
    });
  }
  const askChatBtn = document.getElementById("wb-tf-ask-chat");
  if (askChatBtn) {
    askChatBtn.addEventListener("click", function () {
      const id = document.getElementById("wb-tf-id").value.trim(), tk = (wbState.tasks || []).find(function (x) { return x.id === id; });
      if (tk && typeof sendTaskToSplitChat === "function") { document.getElementById("work-task-modal").close(); sendTaskToSplitChat(tk); }
    });
  }
  document.querySelectorAll("[data-wb-filter]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      wbTaskFilter = btn.getAttribute("data-wb-filter") || "open";
      document.querySelectorAll("[data-wb-filter]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      renderWorkTasks();
    });
  });
  const searchInp = document.getElementById("wb-task-search");
  if (searchInp) { searchInp.addEventListener("input", function () { wbTaskSearch = searchInp.value.trim(); renderWorkTasks(); }); }
  const quickForm = document.getElementById("wb-quick-task-form");
  if (quickForm) {
    quickForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const titleEl = document.getElementById("wb-quick-title"), title = titleEl.value.trim(); if (!title) { return; }
      titleEl.value = "";
      await wbApi("/api/work-board/tasks", { method: "POST", body: JSON.stringify({ title: title, priority: document.getElementById("wb-quick-priority").value, due_date: document.getElementById("wb-quick-due").value || "", project_id: document.getElementById("wb-quick-project").value || "" }) });
    });
  }
  const subAdd = document.getElementById("wb-tf-sub-add"), subInp = document.getElementById("wb-tf-sub-input");
  if (subAdd && subInp) {
    subAdd.addEventListener("click", function () {
      const val = subInp.value.trim(); if (!val) { return; }
      wbEditingSubtasks.push({ id: "sub_" + Date.now().toString(36), title: val, done: false });
      subInp.value = ""; renderEditingSubtasks();
    });
  }
  const taskForm = document.getElementById("wb-task-form");
  if (taskForm) {
    taskForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = document.getElementById("wb-tf-id").value.trim();
      const tags = document.getElementById("wb-tf-tags").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      const body = {
        title: document.getElementById("wb-tf-title").value.trim(), description: document.getElementById("wb-tf-desc").value.trim(),
        column_id: document.getElementById("wb-tf-col").value, project_id: document.getElementById("wb-tf-project").value || "",
        priority: document.getElementById("wb-tf-priority").value, recurrence: document.getElementById("wb-tf-recur").value,
        due_date: document.getElementById("wb-tf-due").value || "", scheduled_start: document.getElementById("wb-tf-start").value || "",
        scheduled_end: document.getElementById("wb-tf-end").value || "", subtasks: wbEditingSubtasks, tags: tags,
      };
      if (!body.title) { return; }
      const ok = await wbApi(id ? ("/api/work-board/tasks/" + encodeURIComponent(id)) : "/api/work-board/tasks", { method: id ? "PATCH" : "POST", body: JSON.stringify(body) });
      if (ok) { document.getElementById("work-task-modal").close(); }
    });
  }
  const delTask = document.getElementById("wb-tf-delete");
  if (delTask) { delTask.addEventListener("click", async function () { const id = document.getElementById("wb-tf-id").value.trim(); if (id && await wbApi("/api/work-board/tasks/" + encodeURIComponent(id), { method: "DELETE" })) { document.getElementById("work-task-modal").close(); } }); }
  const projForm = document.getElementById("wb-project-form");
  if (projForm) {
    projForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = document.getElementById("wb-pf-id").value.trim();
      const body = {
        title: document.getElementById("wb-pf-title").value.trim(), description: document.getElementById("wb-pf-desc").value.trim(),
        status: document.getElementById("wb-pf-status").value, color: document.getElementById("wb-pf-color").value || "#4BB8E8",
        target_date: document.getElementById("wb-pf-target").value || "", target_hours: Number(document.getElementById("wb-pf-hours").value || 0),
      };
      if (!body.title) { return; }
      const ok = await wbApi(id ? ("/api/work-board/projects/" + encodeURIComponent(id)) : "/api/work-board/projects", { method: id ? "PATCH" : "POST", body: JSON.stringify(body) });
      if (ok) { document.getElementById("work-project-modal").close(); }
    });
  }
  const delProj = document.getElementById("wb-pf-delete");
  if (delProj) { delProj.addEventListener("click", async function () { const id = document.getElementById("wb-pf-id").value.trim(); if (id && await wbApi("/api/work-board/projects/" + encodeURIComponent(id), { method: "DELETE" })) { document.getElementById("work-project-modal").close(); } }); }
  const extForm = document.getElementById("wb-extract-form");
  if (extForm) {
    extForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const txt = document.getElementById("wb-ext-text").value.trim(); if (!txt) { return; }
      const ok = await extractTasksToBoard({ text: txt, project_id: document.getElementById("wb-ext-project").value || "", column_id: document.getElementById("wb-ext-col").value || "", use_ai: document.getElementById("wb-ext-use-ai").checked });
      if (ok) { document.getElementById("wb-ext-text").value = ""; document.getElementById("work-extract-modal").close(); }
    });
  }
  bindCalendarControls();
}
"""
