"""Projects, Kanban Board, and Task Manager rendering + drag/keyboard interactions."""

from features.ui.calendar_script import CALENDAR_SCRIPT
from features.ui.work_board_modals_script import WORK_BOARD_MODALS_SCRIPT

WORK_BOARD_SCRIPT: str = CALENDAR_SCRIPT + WORK_BOARD_MODALS_SCRIPT + r"""
let wbState = { columns: [], projects: [], tasks: [], events: [], summary: {} };
let wbActiveTab = "kanban", wbProjectFilter = "", wbTaskFilter = "open", wbTaskSearch = "", wbEditingSubtasks = [], wbDragTaskId = null, wbViewOpen = false, wbLoadedArea = null;
const WB_GRIP_SVG = "<svg aria-hidden='true' width='13' height='13' viewBox='0 0 24 24' fill='currentColor'><circle cx='9' cy='6' r='1.7'/><circle cx='15' cy='6' r='1.7'/><circle cx='9' cy='12' r='1.7'/><circle cx='15' cy='12' r='1.7'/><circle cx='9' cy='18' r='1.7'/><circle cx='15' cy='18' r='1.7'/></svg>";
const WB_PRIO_KEYS = { low: "wb_prio_low", medium: "wb_prio_medium", high: "wb_prio_high", urgent: "wb_prio_urgent" };
const WB_REC_KEYS = { none: "wb_rec_none", daily: "wb_rec_daily", weekly: "wb_rec_weekly", monthly: "wb_rec_monthly" };
const WB_DEF_COL_MAP = { todo: ["To Do", "wb_col_todo"], doing: ["In Progress", "wb_col_doing"], review: ["Review", "wb_col_review"], done: ["Done", "wb_col_done"] };
function wbColTitle(col) {
  if (!col) { return ""; }
  const def = WB_DEF_COL_MAP[col.id];
  return def && col.title === def[0] ? t(def[1]) : col.title;
}
function announceWorkStatus(msg) {
  const live = document.getElementById("app-live-status");
  if (!live) { return; }
  live.textContent = "";
  setTimeout(function () { live.textContent = msg; }, 80);
}
function applyWorkBoardState(data) {
  if (!data || !Array.isArray(data.columns)) { return; }
  wbState = { columns: data.columns, projects: data.projects || [], tasks: data.tasks || [], events: data.events || [], summary: data.summary || {} };
  const badge = document.getElementById("sidebar-work-badge");
  if (badge) { badge.textContent = String((wbState.summary && wbState.summary.open_tasks) || 0); }
  if (wbViewOpen) { renderWorkBoardAll(); }
}
async function wbApi(path, opts) {
  const version = areaVersion, cfg = Object.assign({ headers: {} }, opts || {});
  if (cfg.body && !cfg.headers["Content-Type"]) { cfg.headers["Content-Type"] = "application/json"; }
  try {
    const res = await areaFetch(path, cfg), data = await safeJson(res);
    if (version !== areaVersion) { return null; }
    if (!res.ok) { throw new Error(data.detail || "Work Board request failed"); }
    applyWorkBoardState(data);
    return data;
  } catch (err) {
    if (version === areaVersion) { showToast(err.message || "Work Board error", 3500); }
    return null;
  }
}
async function loadWorkBoardSummary(force) {
  const area = activeKnowledgeArea || "";
  if (!force && wbLoadedArea === area) { return; }
  wbLoadedArea = area; wbProjectFilter = "";
  await wbApi("/api/work-board");
}
function closeWorkBoardView() {
  wbViewOpen = false;
  const view = document.getElementById("work-board-view");
  if (view) { view.classList.add("hidden"); }
  const btn = document.getElementById("sidebar-work-btn");
  if (btn) { btn.classList.remove("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
}
async function openWorkBoardView(tab) {
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); }
  wbViewOpen = true;
  if (typeof setAmbientDimmed === "function") { setAmbientDimmed(true); }
  const shell = document.getElementById("workspace-shell"), gv = document.getElementById("graph-view"), view = document.getElementById("work-board-view");
  if (shell) { shell.classList.add("hidden"); }
  if (gv) { gv.classList.add("hidden"); }
  if (view) { view.classList.remove("hidden"); }
  const btn = document.getElementById("sidebar-work-btn");
  if (btn) { btn.classList.add("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
  if (tab) { setWorkBoardTab(tab); }
  await wbApi("/api/work-board");
  renderWorkBoardAll();
}
function setWorkBoardTab(tab) {
  wbActiveTab = tab || "kanban";
  document.querySelectorAll("[data-wb-tab]").forEach(function (btn) {
    const active = btn.getAttribute("data-wb-tab") === wbActiveTab;
    btn.setAttribute("aria-selected", String(active));
    btn.tabIndex = active ? 0 : -1;
  });
  ["kanban", "tasks", "calendar", "projects"].forEach(function (name) {
    const panel = document.getElementById("wb-panel-" + name);
    if (panel) { panel.hidden = name !== wbActiveTab; }
  });
  if (wbActiveTab === "calendar") { renderWorkCalendar(); }
  else if (wbActiveTab === "tasks") { renderWorkTasks(); }
  else if (wbActiveTab === "projects") { renderWorkProjects(); }
  else { renderWorkKanban(); }
}
function populateProjectSelect(sel, selectedId, includeEmpty) {
  if (!sel) { return; }
  const cur = selectedId !== undefined ? selectedId : sel.value;
  const opts = [];
  if (includeEmpty) { opts.push("<option value=''>" + escapeHtml(sel.id === "wb-project-filter" ? t("wb_all_projects") : t("wb_no_project")) + "</option>"); }
  (wbState.projects || []).forEach(function (p) {
    opts.push("<option value='" + escapeHtml(p.id) + "'" + (p.id === cur ? " selected" : "") + ">" + escapeHtml(p.title) + "</option>");
  });
  sel.innerHTML = opts.join("");
  if (cur) { sel.value = cur; }
}
function populateColumnSelect(sel, selectedId) {
  if (!sel) { return; }
  sel.innerHTML = (wbState.columns || []).map(function (c) {
    return "<option value='" + escapeHtml(c.id) + "'" + (c.id === selectedId ? " selected" : "") + ">" + escapeHtml(wbColTitle(c)) + "</option>";
  }).join("");
}
function wbProjectById(pid) { return (wbState.projects || []).find(function (p) { return p.id === pid; }) || null; }
function renderWorkBoardAll() {
  const s = wbState.summary || {}, statsEl = document.getElementById("wb-stats");
  if (statsEl) {
    statsEl.innerHTML = "<span class='wb-stat-pill'>" + escapeHtml(t("wb_stat_open", { n: s.open_tasks || 0 })) + "</span>"
      + (s.today_tasks ? "<span class='wb-stat-pill is-accent'>" + escapeHtml(t("wb_stat_today", { n: s.today_tasks })) + "</span>" : "")
      + (s.overdue_tasks ? "<span class='wb-stat-pill is-warn'>" + escapeHtml(t("wb_stat_overdue", { n: s.overdue_tasks })) + "</span>" : "");
  }
  populateProjectSelect(document.getElementById("wb-project-filter"), wbProjectFilter, true);
  populateProjectSelect(document.getElementById("wb-quick-project"), wbProjectFilter, true);
  renderWorkKanban(); renderWorkTasks(); renderWorkCalendar(); renderWorkProjects();
}
function wbTaskMetaHtml(task) {
  const today = wbTodayIso(), proj = wbProjectById(task.project_id), parts = [];
  if (task.priority && task.priority !== "medium") {
    parts.push("<span class='wb-chip prio-" + escapeHtml(task.priority) + "'>" + escapeHtml(t(WB_PRIO_KEYS[task.priority] || "wb_prio_medium")) + "</span>");
  }
  if (task.due_date) {
    const doneIds = new Set((wbState.columns || []).filter(function (c) { return c.is_done; }).map(function (c) { return c.id; }));
    const isDone = doneIds.has(task.column_id);
    const cls = !isDone && task.due_date < today ? " is-overdue" : (!isDone && task.due_date === today ? " is-today" : "");
    parts.push("<span class='wb-chip" + cls + "'>" + escapeHtml(task.due_date + (task.scheduled_start ? " " + task.scheduled_start : "")) + "</span>");
  }
  if (proj) { parts.push("<span class='wb-chip'><span class='wb-dot' style='background:" + escapeHtml(proj.color) + "'></span>" + escapeHtml(proj.title) + "</span>"); }
  if (task.subtasks && task.subtasks.length) {
    const dCount = task.subtasks.filter(function (s) { return s.done; }).length;
    parts.push("<span class='wb-chip'>" + dCount + "/" + task.subtasks.length + "</span>");
  }
  if (task.recurrence && task.recurrence !== "none") { parts.push("<span class='wb-chip'>↻ " + escapeHtml(t(WB_REC_KEYS[task.recurrence] || "wb_rec_none")) + "</span>"); }
  return parts.length ? "<div class='wb-card-meta'>" + parts.join("") + "</div>" : "";
}
function renderWorkKanban() {
  const wrap = document.getElementById("wb-kanban-columns"); if (!wrap) { return; }
  const cols = wbState.columns || [];
  const filtered = (wbState.tasks || []).filter(function (tk) { return !wbProjectFilter || tk.project_id === wbProjectFilter; });
  const colsHtml = cols.map(function (col, cIdx) {
    const cards = filtered.filter(function (tk) { return tk.column_id === col.id; }).sort(function (a, b) { return (a.position || 0) - (b.position || 0); });
    const cardsHtml = cards.map(function (tk) {
      const prevCol = cIdx > 0 ? cols[cIdx - 1] : null, nextCol = cIdx < cols.length - 1 ? cols[cIdx + 1] : null;
      const moveBtns = "<div class='wb-card-move'>"
        + (prevCol ? "<button type='button' data-wb-move='" + escapeHtml(tk.id) + "' data-wb-dest='" + escapeHtml(prevCol.id) + "' aria-label='" + escapeHtml(t("wb_move_left")) + "' title='" + escapeHtml(wbColTitle(prevCol)) + "' class='wb-icon-btn' style='width:1.45rem;height:1.45rem'>←</button>" : "")
        + (nextCol ? "<button type='button' data-wb-move='" + escapeHtml(tk.id) + "' data-wb-dest='" + escapeHtml(nextCol.id) + "' aria-label='" + escapeHtml(t("wb_move_right")) + "' title='" + escapeHtml(wbColTitle(nextCol)) + "' class='wb-icon-btn' style='width:1.45rem;height:1.45rem'>→</button>" : "")
        + "</div>";
      return "<article class='wb-card' draggable='true' data-wb-card='" + escapeHtml(tk.id) + "'>"
        + "<div class='wb-card-top'>"
        + "<span class='wb-drag-handle' aria-label='" + escapeHtml(t("wb_drag_aria", { title: tk.title })) + "'>" + WB_GRIP_SVG + "</span>"
        + "<button type='button' data-wb-open-task='" + escapeHtml(tk.id) + "' class='wb-card-title" + (col.is_done ? " is-done" : "") + "'>" + escapeHtml(tk.title) + "</button>"
        + moveBtns + "</div>" + wbTaskMetaHtml(tk) + "</article>";
    }).join("");
    const colLabel = wbColTitle(col);
    const delCol = cols.length > 1 ? "<button type='button' data-wb-del-col='" + escapeHtml(col.id) + "' aria-label='" + escapeHtml(t("delete_btn") + " " + colLabel) + "' class='wb-icon-btn' style='width:1.5rem;height:1.5rem;font-size:0.78rem'>✕</button>" : "";
    return "<section class='wb-col' data-wb-col='" + escapeHtml(col.id) + "' aria-label='" + escapeHtml(colLabel) + "'>"
      + "<div class='wb-col-head'><div class='wb-col-title-wrap'><span class='wb-dot' style='background:" + escapeHtml(col.color) + "'></span><h2 class='wb-col-title'>" + escapeHtml(colLabel) + "</h2><span class='wb-col-count'>" + cards.length + "</span></div>" + delCol + "</div>"
      + "<div class='wb-col-list' data-wb-col-list='" + escapeHtml(col.id) + "'>" + cardsHtml + "</div>"
      + "<form class='wb-quick-add' data-wb-col-quick='" + escapeHtml(col.id) + "'><input type='text' maxlength='200' aria-label='" + escapeHtml(t("wb_col_quick_ph")) + "' placeholder='" + escapeHtml(t("wb_col_quick_ph")) + "' class='wb-input' /><button type='submit' class='wb-btn wb-btn-sm'>+</button></form>"
      + "</section>";
  }).join("");
  const addColHtml = "<form id='wb-add-col-form' class='wb-add-col-card'><input id='wb-new-col-name' type='text' maxlength='60' aria-label='" + escapeHtml(t("wb_add_col_ph")) + "' placeholder='" + escapeHtml(t("wb_add_col_ph")) + "' class='wb-input' /><button type='submit' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_add_col_btn")) + "</button></form>";
  wrap.innerHTML = colsHtml + addColHtml;
  bindKanbanEvents(wrap);
}
function bindKanbanEvents(wrap) {
  wrap.querySelectorAll("[data-wb-open-task]").forEach(function (btn) {
    btn.addEventListener("click", function () { openWorkTaskModal(btn.getAttribute("data-wb-open-task")); });
  });
  wrap.querySelectorAll("[data-wb-move]").forEach(function (btn) {
    btn.addEventListener("click", async function (e) {
      e.stopPropagation();
      const tid = btn.getAttribute("data-wb-move"), dest = btn.getAttribute("data-wb-dest");
      const task = (wbState.tasks || []).find(function (tk) { return tk.id === tid; });
      const col = (wbState.columns || []).find(function (c) { return c.id === dest; });
      const ok = await wbApi("/api/work-board/tasks/reorder", { method: "POST", body: JSON.stringify({ task_id: tid, target_column_id: dest, target_index: 0 }) });
      if (ok && task && col) { const msg = t("wb_moved_toast", { title: task.title, col: wbColTitle(col) }); announceWorkStatus(msg); showToast(msg); }
    });
  });
  wrap.querySelectorAll("[data-wb-card]").forEach(function (card) {
    card.addEventListener("dragstart", function (e) {
      wbDragTaskId = card.getAttribute("data-wb-card");
      card.classList.add("is-dragging");
      if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", wbDragTaskId || ""); }
    });
    card.addEventListener("dragend", function () {
      wbDragTaskId = null; card.classList.remove("is-dragging");
      wrap.querySelectorAll(".is-drop-over").forEach(function (el) { el.classList.remove("is-drop-over"); });
    });
  });
  wrap.querySelectorAll("[data-wb-col]").forEach(function (colEl) {
    colEl.addEventListener("dragover", function (e) { if (!wbDragTaskId) { return; } e.preventDefault(); colEl.classList.add("is-drop-over"); });
    colEl.addEventListener("dragleave", function (e) { if (!colEl.contains(e.relatedTarget)) { colEl.classList.remove("is-drop-over"); } });
    colEl.addEventListener("drop", async function (e) {
      e.preventDefault(); colEl.classList.remove("is-drop-over");
      const tid = wbDragTaskId, dest = colEl.getAttribute("data-wb-col");
      if (!tid || !dest) { return; }
      wbDragTaskId = null;
      const list = colEl.querySelector("[data-wb-col-list]"), cards = list ? Array.from(list.querySelectorAll("[data-wb-card]")) : [];
      let idx = cards.length;
      for (let i = 0; i < cards.length; i++) {
        const r = cards[i].getBoundingClientRect();
        if (e.clientY < r.top + r.height / 2) { idx = i; break; }
      }
      const task = (wbState.tasks || []).find(function (tk) { return tk.id === tid; });
      const col = (wbState.columns || []).find(function (c) { return c.id === dest; });
      const ok = await wbApi("/api/work-board/tasks/reorder", { method: "POST", body: JSON.stringify({ task_id: tid, target_column_id: dest, target_index: idx }) });
      if (ok && task && col) { announceWorkStatus(t("wb_moved_toast", { title: task.title, col: col.title })); }
    });
  });
  wrap.querySelectorAll("[data-wb-col-quick]").forEach(function (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const inp = form.querySelector("input"), title = inp ? inp.value.trim() : "";
      if (!title) { return; }
      inp.value = "";
      await wbApi("/api/work-board/tasks", { method: "POST", body: JSON.stringify({ title: title, column_id: form.getAttribute("data-wb-col-quick") || "", project_id: wbProjectFilter || "" }) });
    });
  });
  wrap.querySelectorAll("[data-wb-del-col]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      await wbApi("/api/work-board/columns/" + encodeURIComponent(btn.getAttribute("data-wb-del-col") || ""), { method: "DELETE" });
    });
  });
  const addColForm = document.getElementById("wb-add-col-form");
  if (addColForm) {
    addColForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const inp = document.getElementById("wb-new-col-name"), title = inp ? inp.value.trim() : "";
      if (!title) { return; }
      inp.value = "";
      await wbApi("/api/work-board/columns", { method: "POST", body: JSON.stringify({ title: title, color: "#4BB8E8", is_done: false }) });
    });
  }
}
function renderWorkTasks() {
  const listEl = document.getElementById("wb-task-list"); if (!listEl) { return; }
  const today = wbTodayIso(), q = wbTaskSearch.toLowerCase();
  const doneIds = new Set((wbState.columns || []).filter(function (c) { return c.is_done; }).map(function (c) { return c.id; }));
  const doneCol = (wbState.columns || []).find(function (c) { return c.is_done; }) || (wbState.columns || [])[(wbState.columns || []).length - 1];
  const openCol = (wbState.columns || []).find(function (c) { return !c.is_done; }) || (wbState.columns || [])[0];
  const items = (wbState.tasks || []).filter(function (tk) {
    if (wbProjectFilter && tk.project_id !== wbProjectFilter) { return false; }
    if (q && !tk.title.toLowerCase().includes(q) && !(tk.description || "").toLowerCase().includes(q)) { return false; }
    const isDone = doneIds.has(tk.column_id);
    if (wbTaskFilter === "done") { return isDone; }
    if (isDone) { return false; }
    if (wbTaskFilter === "today") { return tk.due_date === today; }
    if (wbTaskFilter === "overdue") { return Boolean(tk.due_date && tk.due_date < today); }
    if (wbTaskFilter === "upcoming") { return Boolean(tk.due_date && tk.due_date > today); }
    return true;
  }).sort(function (a, b) { return (a.due_date || "9999-99-99").localeCompare(b.due_date || "9999-99-99"); });
  if (!items.length) { listEl.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("wb_empty_tasks")) + "</div>"; return; }
  listEl.innerHTML = items.map(function (tk) {
    const isDone = doneIds.has(tk.column_id), col = (wbState.columns || []).find(function (c) { return c.id === tk.column_id; });
    return "<div class='wb-task-row'>"
      + "<button type='button' data-wb-toggle-done='" + escapeHtml(tk.id) + "' aria-pressed='" + String(isDone) + "' aria-label='" + escapeHtml(tk.title) + "' class='wb-check-btn'>" + (isDone ? CHECK_SVG : "") + "</button>"
      + "<div style='min-width:0;display:flex;flex-direction:column;gap:0.28rem'><button type='button' data-wb-open-task='" + escapeHtml(tk.id) + "' class='wb-card-title" + (isDone ? " is-done" : "") + "'>" + escapeHtml(tk.title) + "</button>" + wbTaskMetaHtml(tk) + "</div>"
      + "<span class='wb-chip'>" + escapeHtml(col ? wbColTitle(col) : "") + "</span></div>";
  }).join("");
  listEl.querySelectorAll("[data-wb-open-task]").forEach(function (btn) {
    btn.addEventListener("click", function () { openWorkTaskModal(btn.getAttribute("data-wb-open-task")); });
  });
  listEl.querySelectorAll("[data-wb-toggle-done]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const tid = btn.getAttribute("data-wb-toggle-done"), isDone = btn.getAttribute("aria-pressed") === "true";
      const destCol = isDone ? (openCol && openCol.id) : (doneCol && doneCol.id);
      if (destCol) { await wbApi("/api/work-board/tasks/" + encodeURIComponent(tid), { method: "PATCH", body: JSON.stringify({ column_id: destCol }) }); }
    });
  });
}
function renderWorkProjects() {
  const grid = document.getElementById("wb-projects-grid"); if (!grid) { return; }
  const projects = wbState.projects || [];
  if (!projects.length) { grid.innerHTML = "<div class='wb-empty' style='grid-column:1/-1'>" + escapeHtml(t("wb_empty_projects")) + "</div>"; return; }
  const doneIds = new Set((wbState.columns || []).filter(function (c) { return c.is_done; }).map(function (c) { return c.id; }));
  grid.innerHTML = projects.map(function (p) {
    const pTasks = (wbState.tasks || []).filter(function (tk) { return tk.project_id === p.id; });
    const done = pTasks.filter(function (tk) { return doneIds.has(tk.column_id); }).length;
    const pct = pTasks.length ? Math.round((done / pTasks.length) * 100) : 0;
    const stKey = p.status === "on_hold" ? "wb_st_hold" : (p.status === "completed" ? "wb_st_done" : "wb_st_active");
    return "<article class='wb-project-card'>"
      + "<div style='display:flex;align-items:center;justify-content:space-between;gap:0.5rem'><div style='display:flex;align-items:center;gap:0.5rem;min-width:0'><span class='wb-dot' style='background:" + escapeHtml(p.color) + "'></span><h3 style='margin:0;font-size:calc(1rem * var(--ui-scale,1));font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>" + escapeHtml(p.title) + "</h3></div><span class='wb-chip'>" + escapeHtml(t(stKey)) + "</span></div>"
      + (p.description ? "<p style='margin:0;color:var(--text-muted);font-size:calc(0.875rem * var(--ui-scale,1));line-height:1.5'>" + escapeHtml(p.description) + "</p>" : "")
      + "<div style='display:flex;justify-content:space-between;font-size:0.8rem;color:var(--text-muted)'><span>" + done + " / " + pTasks.length + " · " + pct + "%</span><span>" + escapeHtml(p.target_date || "") + (p.target_hours ? " · " + p.target_hours + "h" : "") + "</span></div>"
      + "<div class='wb-progress-track'><div class='wb-progress-fill' style='width:" + pct + "%;background:" + escapeHtml(p.color) + "'></div></div>"
      + "<div style='display:flex;gap:0.45rem;margin-top:0.2rem'><button type='button' data-wb-focus-proj='" + escapeHtml(p.id) + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_open_on_board")) + "</button><button type='button' data-wb-edit-proj='" + escapeHtml(p.id) + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_edit_project")) + "</button></div>"
      + "</article>";
  }).join("");
  grid.querySelectorAll("[data-wb-focus-proj]").forEach(function (btn) {
    btn.addEventListener("click", function () { wbProjectFilter = btn.getAttribute("data-wb-focus-proj") || ""; renderWorkBoardAll(); setWorkBoardTab("kanban"); });
  });
  grid.querySelectorAll("[data-wb-edit-proj]").forEach(function (btn) {
    btn.addEventListener("click", function () { openWorkProjectModal(btn.getAttribute("data-wb-edit-proj")); });
  });
}
"""
