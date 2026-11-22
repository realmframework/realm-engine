"""Location-agnostic PlainDate Local Calendar (Month/Week/Day) and RFC 5545 .ics Import/Export."""

CALENDAR_SCRIPT: str = r"""
const WB_KIND_KEYS = { event: "wb_kind_event", focus: "wb_kind_focus", milestone: "wb_kind_milestone", deadline: "wb_kind_deadline" };
let wbCalMode = "month", wbCalAnchor = "", wbCalDragPayload = null;
function wbPad2(n) { return String(n).padStart(2, "0"); }
function wbTodayIso() {
  if (typeof Temporal !== "undefined" && Temporal.Now && typeof Temporal.Now.plainDateISO === "function") {
    return Temporal.Now.plainDateISO().toString();
  }
  const d = new Date();
  return d.getFullYear() + "-" + wbPad2(d.getMonth() + 1) + "-" + wbPad2(d.getDate());
}
function wbParseIso(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ""));
  if (!m) { return wbParseIso(wbTodayIso()); }
  return { y: Number(m[1]), m: Number(m[2]), d: Number(m[3]) };
}
function wbFmtIso(y, m, d) { return String(y).padStart(4, "0") + "-" + wbPad2(m) + "-" + wbPad2(d); }
function wbAddDays(iso, delta) {
  if (typeof Temporal !== "undefined" && Temporal.PlainDate) {
    return Temporal.PlainDate.from(iso).add({ days: delta }).toString();
  }
  const p = wbParseIso(iso), dt = new Date(p.y, p.m - 1, p.d + delta);
  return wbFmtIso(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
}
function wbAddMonths(iso, delta) {
  if (typeof Temporal !== "undefined" && Temporal.PlainDate) {
    return Temporal.PlainDate.from(iso).add({ months: delta }).toString();
  }
  const p = wbParseIso(iso), total = (p.y * 12 + (p.m - 1)) + delta;
  const ny = Math.floor(total / 12), nm = ((total % 12) + 12) % 12 + 1;
  const maxDay = new Date(ny, nm, 0).getDate();
  return wbFmtIso(ny, nm, Math.min(p.d, maxDay));
}
function wbDowMon0(iso) {
  if (typeof Temporal !== "undefined" && Temporal.PlainDate) {
    return Temporal.PlainDate.from(iso).dayOfWeek - 1;
  }
  const p = wbParseIso(iso), jsDow = new Date(p.y, p.m - 1, p.d).getDay();
  return (jsDow + 6) % 7;
}
function wbLocaleTag() { return activeLanguage === "de" ? "de-DE" : (activeLanguage === "es" ? "es-ES" : "en-US"); }
function wbWeekdayLabels() {
  const base = "2026-01-05";
  return [0, 1, 2, 3, 4, 5, 6].map(function (i) {
    const p = wbParseIso(wbAddDays(base, i));
    return new Intl.DateTimeFormat(wbLocaleTag(), { weekday: "short" }).format(new Date(p.y, p.m - 1, p.d));
  });
}
function wbFormatDateLabel(iso, opts) {
  const p = wbParseIso(iso);
  return new Intl.DateTimeFormat(wbLocaleTag(), opts).format(new Date(p.y, p.m - 1, p.d));
}
function wbCalItemsForDate(iso) {
  const items = [], filterProj = wbProjectFilter || "";
  const doneIds = new Set((wbState.columns || []).filter(function (c) { return c.is_done; }).map(function (c) { return c.id; }));
  (wbState.events || []).forEach(function (ev) {
    if (ev.date !== iso) { return; }
    if (filterProj && ev.project_id !== filterProj) { return; }
    items.push({ type: "event", id: ev.id, title: ev.title, time: ev.start_time || "", end: ev.end_time || "", kind: ev.kind || "event", raw: ev });
  });
  (wbState.tasks || []).forEach(function (tk) {
    if (tk.due_date !== iso) { return; }
    if (filterProj && tk.project_id !== filterProj) { return; }
    const isDone = doneIds.has(tk.column_id);
    items.push({ type: "task", id: tk.id, title: tk.title, time: tk.scheduled_start || "", end: tk.scheduled_end || "", kind: isDone ? "event" : "deadline", done: isDone, raw: tk });
  });
  return items.sort(function (a, b) { return (a.time || "99:99").localeCompare(b.time || "99:99") || a.title.localeCompare(b.title); });
}
function wbCalItemHtml(item) {
  const timePrefix = item.time ? "<span style='font-family:ui-monospace,monospace;opacity:0.8'>" + escapeHtml(item.time) + "</span> " : "";
  const cls = "wb-cal-item kind-" + escapeHtml(item.kind || "event") + (item.done ? " opacity-60 line-through" : "");
  return "<button type='button' draggable='true' data-cal-item-type='" + item.type + "' data-cal-item-id='" + escapeHtml(item.id) + "' class='" + cls + "' title='" + escapeHtml(item.title) + "'>" + timePrefix + "<span>" + escapeHtml(item.title) + "</span></button>";
}
function renderWorkCalendar() {
  const canvas = document.getElementById("wb-cal-canvas"), labelEl = document.getElementById("wb-cal-label");
  if (!canvas) { return; }
  if (!wbCalAnchor) { wbCalAnchor = wbTodayIso(); }
  const today = wbTodayIso(), dows = wbWeekdayLabels(), anchor = wbParseIso(wbCalAnchor);
  document.querySelectorAll("[data-cal-mode]").forEach(function (btn) {
    btn.setAttribute("aria-pressed", String(btn.getAttribute("data-cal-mode") === wbCalMode));
  });
  if (wbCalMode === "month") {
    if (labelEl) { labelEl.textContent = wbFormatDateLabel(wbCalAnchor, { month: "long", year: "numeric" }); }
    const firstIso = wbFmtIso(anchor.y, anchor.m, 1), lead = wbDowMon0(firstIso), startIso = wbAddDays(firstIso, -lead);
    const cells = [];
    for (let i = 0; i < 42; i++) {
      const iso = wbAddDays(startIso, i), p = wbParseIso(iso), other = p.m !== anchor.m, isToday = iso === today;
      const items = wbCalItemsForDate(iso);
      const cellCls = "wb-cal-cell" + (other ? " is-other-month" : "") + (isToday ? " is-today" : "");
      cells.push("<div class='" + cellCls + "' data-cal-drop-date='" + iso + "'>"
        + "<div class='wb-cal-day-num" + (isToday ? " is-today" : "") + "'><span>" + p.d + "</span>"
        + "<button type='button' data-cal-quick-add='" + iso + "' aria-label='" + escapeHtml(t("wb_ev_modal_new") + " " + iso) + "' class='wb-icon-btn' style='width:1.4rem;height:1.4rem;font-size:calc(0.85rem * var(--ui-scale,1))'>+</button></div>"
        + items.slice(0, 4).map(wbCalItemHtml).join("")
        + (items.length > 4 ? "<span style='font-size:calc(0.72rem * var(--ui-scale,1));color:var(--text-subtle);padding-inline:0.35rem'>+" + (items.length - 4) + "</span>" : "")
        + "</div>");
    }
    canvas.innerHTML = "<div class='wb-cal-month'>" + dows.map(function (d) { return "<div class='wb-cal-dow'>" + escapeHtml(d) + "</div>"; }).join("") + cells.join("") + "</div>";
  } else if (wbCalMode === "week") {
    const monIso = wbAddDays(wbCalAnchor, -wbDowMon0(wbCalAnchor)), sunIso = wbAddDays(monIso, 6);
    if (labelEl) { labelEl.textContent = wbFormatDateLabel(monIso, { month: "short", day: "numeric" }) + " – " + wbFormatDateLabel(sunIso, { month: "short", day: "numeric", year: "numeric" }); }
    const cols = [];
    for (let i = 0; i < 7; i++) {
      const iso = wbAddDays(monIso, i), isToday = iso === today, items = wbCalItemsForDate(iso);
      cols.push("<div class='wb-cal-week-col" + (isToday ? " is-today" : "") + "' data-cal-drop-date='" + iso + "'>"
        + "<div class='wb-cal-day-num" + (isToday ? " is-today" : "") + "'><span>" + escapeHtml(dows[i] + " " + wbParseIso(iso).d) + "</span>"
        + "<button type='button' data-cal-quick-add='" + iso + "' aria-label='" + escapeHtml(t("wb_new_event") + " " + iso) + "' class='wb-icon-btn' style='width:1.5rem;height:1.5rem'>+</button></div>"
        + (items.length ? items.map(wbCalItemHtml).join("") : "<span style='font-size:calc(0.78rem * var(--ui-scale,1));color:var(--text-subtle)'>—</span>")
        + "</div>");
    }
    canvas.innerHTML = "<div class='wb-cal-week'>" + cols.join("") + "</div>";
  } else {
    if (labelEl) { labelEl.textContent = wbFormatDateLabel(wbCalAnchor, { weekday: "long", month: "long", day: "numeric", year: "numeric" }); }
    const items = wbCalItemsForDate(wbCalAnchor);
    const listHtml = items.length ? items.map(function (item) {
      const slot = item.time ? (item.time + (item.end ? " – " + item.end : "")) : t("wb_today");
      return "<div class='wb-task-row'><span class='wb-chip'>" + escapeHtml(slot) + "</span>"
        + "<button type='button' data-cal-item-type='" + item.type + "' data-cal-item-id='" + escapeHtml(item.id) + "' class='wb-card-title'>" + escapeHtml(item.title) + "</button>"
        + "<span class='wb-chip'>" + escapeHtml(t(WB_KIND_KEYS[item.kind] || "wb_kind_event")) + "</span></div>";
    }).join("") : "<div class='wb-empty'>" + escapeHtml(t("wb_empty_day")) + "</div>";
    canvas.innerHTML = "<div data-cal-drop-date='" + wbCalAnchor + "' style='display:flex;flex-direction:column;gap:0.4rem'>" + listHtml + "</div>";
  }
  bindCalendarInteractions(canvas);
}
function bindCalendarInteractions(canvas) {
  canvas.querySelectorAll("[data-cal-quick-add]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.stopPropagation(); openWorkEventModal(null, btn.getAttribute("data-cal-quick-add") || wbTodayIso()); });
  });
  canvas.querySelectorAll("[data-cal-item-id]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const kind = btn.getAttribute("data-cal-item-type"), id = btn.getAttribute("data-cal-item-id");
      if (kind === "task") { openWorkTaskModal(id); } else { openWorkEventModal(id); }
    });
    btn.addEventListener("dragstart", function (e) {
      wbCalDragPayload = { type: btn.getAttribute("data-cal-item-type"), id: btn.getAttribute("data-cal-item-id") };
      if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", JSON.stringify(wbCalDragPayload)); }
    });
    btn.addEventListener("dragend", function () { wbCalDragPayload = null; canvas.querySelectorAll(".is-drop-over").forEach(function (el) { el.classList.remove("is-drop-over"); }); });
  });
  canvas.querySelectorAll("[data-cal-drop-date]").forEach(function (cell) {
    cell.addEventListener("dragover", function (e) { if (!wbCalDragPayload) { return; } e.preventDefault(); cell.classList.add("is-drop-over"); });
    cell.addEventListener("dragleave", function () { cell.classList.remove("is-drop-over"); });
    cell.addEventListener("drop", async function (e) {
      e.preventDefault(); cell.classList.remove("is-drop-over");
      const targetDate = cell.getAttribute("data-cal-drop-date") || "";
      if (!wbCalDragPayload || !targetDate) { return; }
      const payload = wbCalDragPayload; wbCalDragPayload = null;
      const endpoint = payload.type === "task" ? ("/api/work-board/tasks/" + encodeURIComponent(payload.id)) : ("/api/work-board/events/" + encodeURIComponent(payload.id));
      const body = payload.type === "task" ? { due_date: targetDate } : { date: targetDate };
      const ok = await wbApi(endpoint, { method: "PATCH", body: JSON.stringify(body) });
      if (ok) { showToast(t("wb_rescheduled_toast", { date: targetDate })); announceWorkStatus(t("wb_rescheduled_toast", { date: targetDate })); }
    });
  });
}
function openWorkEventModal(eventId, presetDate) {
  const modal = document.getElementById("work-event-modal"); if (!modal) { return; }
  const ev = eventId ? (wbState.events || []).find(function (e) { return e.id === eventId; }) : null;
  document.getElementById("wb-ev-modal-title").textContent = ev ? t("wb_edit_event") : t("wb_ev_modal_new");
  document.getElementById("wb-ef-id").value = ev ? ev.id : "";
  document.getElementById("wb-ef-title").value = ev ? ev.title : "";
  document.getElementById("wb-ef-date").value = ev ? ev.date : (presetDate || wbCalAnchor || wbTodayIso());
  document.getElementById("wb-ef-kind").value = ev ? (ev.kind || "event") : "event";
  document.getElementById("wb-ef-start").value = ev ? (ev.start_time || "") : "";
  document.getElementById("wb-ef-end").value = ev ? (ev.end_time || "") : "";
  document.getElementById("wb-ef-notes").value = ev ? (ev.notes || "") : "";
  populateProjectSelect(document.getElementById("wb-ef-project"), ev ? ev.project_id : wbProjectFilter, true);
  const delBtn = document.getElementById("wb-ef-delete");
  if (delBtn) { delBtn.hidden = !ev; }
  modal.showModal();
  document.getElementById("wb-ef-title").focus();
}
function bindCalendarControls() {
  const prev = document.getElementById("wb-cal-prev"), next = document.getElementById("wb-cal-next"), todayBtn = document.getElementById("wb-cal-today");
  if (prev) { prev.addEventListener("click", function () { wbCalAnchor = wbCalMode === "month" ? wbAddMonths(wbCalAnchor || wbTodayIso(), -1) : wbAddDays(wbCalAnchor || wbTodayIso(), wbCalMode === "week" ? -7 : -1); renderWorkCalendar(); }); }
  if (next) { next.addEventListener("click", function () { wbCalAnchor = wbCalMode === "month" ? wbAddMonths(wbCalAnchor || wbTodayIso(), 1) : wbAddDays(wbCalAnchor || wbTodayIso(), wbCalMode === "week" ? 7 : 1); renderWorkCalendar(); }); }
  if (todayBtn) { todayBtn.addEventListener("click", function () { wbCalAnchor = wbTodayIso(); renderWorkCalendar(); }); }
  document.querySelectorAll("[data-cal-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () { wbCalMode = btn.getAttribute("data-cal-mode") || "month"; renderWorkCalendar(); });
  });
  const newEvBtn = document.getElementById("wb-cal-new-ev-btn");
  if (newEvBtn) { newEvBtn.addEventListener("click", function () { openWorkEventModal(null, wbCalAnchor || wbTodayIso()); }); }
  const expBtn = document.getElementById("wb-cal-export-ics");
  if (expBtn) {
    expBtn.addEventListener("click", async function () {
      try {
        const res = await areaFetch("/api/work-board/calendar.ics");
        if (!res.ok) { throw new Error("Export failed"); }
        const text = await res.text();
        downloadBlobText(text, (activeKnowledgeArea || "realm") + "_calendar.ics", "text/calendar;charset=utf-8");
      } catch (err) { showToast(err.message || "Calendar export failed", 3500); }
    });
  }
  const impBtn = document.getElementById("wb-cal-import-ics-btn"), impFile = document.getElementById("wb-cal-import-ics-file");
  if (impBtn && impFile) {
    impBtn.addEventListener("click", function () { impFile.click(); });
    impFile.addEventListener("change", async function () {
      const f = impFile.files && impFile.files[0]; impFile.value = "";
      if (!f) { return; }
      const raw = await f.text();
      const data = await wbApi("/api/work-board/calendar/import-ics", { method: "POST", body: JSON.stringify({ ics_text: raw }) });
      if (data) { showToast(t("wb_ics_imported_toast", { n: data.imported_count || 0 })); }
    });
  }
  const evForm = document.getElementById("wb-event-form");
  if (evForm) {
    evForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = document.getElementById("wb-ef-id").value.trim();
      const body = {
        title: document.getElementById("wb-ef-title").value.trim(), date: document.getElementById("wb-ef-date").value,
        kind: document.getElementById("wb-ef-kind").value, start_time: document.getElementById("wb-ef-start").value || "",
        end_time: document.getElementById("wb-ef-end").value || "", project_id: document.getElementById("wb-ef-project").value || "",
        notes: document.getElementById("wb-ef-notes").value.trim(),
      };
      if (!body.title || !body.date) { return; }
      const ok = await wbApi(id ? ("/api/work-board/events/" + encodeURIComponent(id)) : "/api/work-board/events", { method: id ? "PATCH" : "POST", body: JSON.stringify(body) });
      if (ok) { document.getElementById("work-event-modal").close(); }
    });
  }
  const delEv = document.getElementById("wb-ef-delete");
  if (delEv) {
    delEv.addEventListener("click", async function () {
      const id = document.getElementById("wb-ef-id").value.trim(); if (!id) { return; }
      const ok = await wbApi("/api/work-board/events/" + encodeURIComponent(id), { method: "DELETE" });
      if (ok) { document.getElementById("work-event-modal").close(); }
    });
  }
}
"""
