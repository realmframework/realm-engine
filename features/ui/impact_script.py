"""Time Tracking (Arbeitszeiterfassung), Wirksamkeitsdokumentation, and ROI Dashboard client."""

IMPACT_SCRIPT: str = r"""
let impState = { default_hourly_rate: 85, currency: "EUR", active_timer: null, time_entries: [], impact_entries: [], summary: {}, timer_elapsed_seconds: 0 };
let impViewOpen = false, impActiveTab = "roi", impTimerTick = null, impTimerClientSecs = 0;
const IMP_TAG_KEYS = { quality: "imp_tag_quality", time_saved: "imp_tag_time_saved", revenue: "imp_tag_revenue", wellbeing: "imp_tag_wellbeing", milestone: "imp_tag_milestone" };
function fmtHMS(totalSec) {
  const s = Math.max(0, Math.floor(totalSec)), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
}
function fmtMoney(val, cur) {
  const sym = cur === "USD" ? "$" : (cur === "GBP" ? "£" : (cur === "EUR" ? "€" : (cur + " ")));
  return sym + Number(val || 0).toLocaleString(typeof wbLocaleTag === "function" ? wbLocaleTag() : "en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function syncImpactTimerUI() {
  const timer = impState.active_timer, clk = document.getElementById("imp-timer-clock"), badge = document.getElementById("sidebar-impact-badge");
  const startBtn = document.getElementById("imp-timer-start-btn"), pauseBtn = document.getElementById("imp-timer-pause-btn"), stopBtn = document.getElementById("imp-timer-stop-btn");
  const lblEl = document.getElementById("imp-timer-label"), projEl = document.getElementById("imp-timer-project");
  const hms = fmtHMS(impTimerClientSecs);
  if (clk) { clk.textContent = hms; }
  if (badge) { badge.textContent = timer ? hms.slice(0, 5) : (((impState.summary && impState.summary.total_hours) || 0) + "h"); }
  if (startBtn) { startBtn.hidden = Boolean(timer); }
  if (pauseBtn) { pauseBtn.hidden = !timer; pauseBtn.textContent = timer && timer.is_paused ? t("foc_resume") : t("imp_pause"); }
  if (stopBtn) { stopBtn.hidden = !timer; }
  if (timer && lblEl && !lblEl.matches(":focus")) { lblEl.value = timer.label || ""; }
  if (timer && projEl && timer.project_id) { projEl.value = timer.project_id; }
  if (typeof updateTopbarContext === "function") { updateTopbarContext(); }
}
function syncImpactTimerInterval() {
  if (impTimerTick) { clearInterval(impTimerTick); impTimerTick = null; }
  if (impState.active_timer && !impState.active_timer.is_paused) {
    impTimerTick = setInterval(function () { impTimerClientSecs += 1; syncImpactTimerUI(); }, 1000);
  }
}
function applyImpactState(data) {
  if (!data || !Array.isArray(data.time_entries)) { return; }
  impState = data;
  impTimerClientSecs = Number(data.timer_elapsed_seconds || 0);
  syncImpactTimerUI(); syncImpactTimerInterval();
  if (impViewOpen) { renderImpactView(); }
}
async function impApi(path, opts) {
  return jsonAreaApi(path, opts, "Impact request failed", function (data) {
    if (Array.isArray(data.time_entries)) { applyImpactState(data); }
    if (opts && opts.method && opts.method !== "GET" && typeof notifyParentFrame === "function") { notifyParentFrame({ type: "realm:work-updated", kind: "impact" }); }
  });
}
async function loadImpactSummary() { await impApi("/api/impact"); }
function closeImpactView() {
  impViewOpen = false;
  const v = document.getElementById("impact-view"); if (v) { v.classList.add("hidden"); }
  const b = document.getElementById("sidebar-impact-btn"); if (b) { b.classList.remove("is-active"); }
}
async function openImpactView(tab) {
  impViewOpen = true;
  activateWorkspaceView("impact-view", { sidebarBtnId: "sidebar-impact-btn", railSection: "work" });
  if (tab) { setImpactTab(tab); }
  await impApi("/api/impact");
  renderImpactView();
  if (typeof updateTopbarContext === "function") { updateTopbarContext(); }
}
function setImpactTab(tab) {
  impActiveTab = tab || "roi";
  document.querySelectorAll("[data-imp-tab]").forEach(function (btn) {
    const active = btn.getAttribute("data-imp-tab") === impActiveTab;
    btn.setAttribute("aria-selected", String(active)); btn.tabIndex = active ? 0 : -1;
  });
  ["roi", "journal", "time"].forEach(function (name) {
    const p = document.getElementById("imp-panel-" + name); if (p) { p.hidden = name !== impActiveTab; }
  });
}
function impProjectTitle(pid) {
  if (!pid) { return t("imp_general"); }
  const p = typeof wbProjectById === "function" ? wbProjectById(pid) : null;
  return p ? p.title : pid;
}
function renderImpactView() {
  const s = impState.summary || {}, cur = s.currency || impState.currency || "EUR";
  const stats = document.getElementById("imp-stats");
  if (stats) {
    const roiTxt = s.roi_pct !== null && s.roi_pct !== undefined ? (s.roi_pct + "% ROI") : "—";
    stats.innerHTML = "<span class='wb-stat-pill'>" + (s.total_hours || 0) + "h</span><span class='wb-stat-pill is-accent'>" + escapeHtml(roiTxt) + "</span>";
  }
  if (typeof populateProjectSelect === "function") {
    populateProjectSelect(document.getElementById("imp-timer-project"), (impState.active_timer && impState.active_timer.project_id) || "", true);
    populateProjectSelect(document.getElementById("imp-mt-project"), "", true);
  }
  const rIn = document.getElementById("imp-cfg-rate"), cIn = document.getElementById("imp-cfg-cur");
  if (rIn && !rIn.matches(":focus")) { rIn.value = String(impState.default_hourly_rate ?? 85); }
  if (cIn && !cIn.matches(":focus")) { cIn.value = cur; }
  const kpi = document.getElementById("imp-kpi-grid");
  if (kpi) {
    const roiVal = s.roi_pct !== null && s.roi_pct !== undefined ? ((s.roi_pct >= 0 ? "+" : "") + s.roi_pct + "%") : "—";
    const roiCls = s.roi_pct !== null && s.roi_pct !== undefined ? (s.roi_pct >= 0 ? " is-ok" : " is-warn") : "";
    kpi.innerHTML = "<div class='kpi-card'><span class='kpi-lbl'>" + escapeHtml(t("imp_kpi_hours")) + "</span><span class='kpi-val'>" + (s.total_hours || 0) + "h</span><span class='kpi-sub'>" + escapeHtml(t("imp_rollup", { w: s.week_hours || 0, m: s.month_hours || 0, t: s.total_hours || 0 })) + "</span></div>"
      + "<div class='kpi-card'><span class='kpi-lbl'>" + escapeHtml(t("imp_kpi_cost")) + "</span><span class='kpi-val'>" + escapeHtml(fmtMoney(s.total_cost, cur)) + "</span><span class='kpi-sub'>" + escapeHtml(cur + " " + (impState.default_hourly_rate || 0) + "/h") + "</span></div>"
      + "<div class='kpi-card'><span class='kpi-lbl'>" + escapeHtml(t("imp_kpi_value")) + "</span><span class='kpi-val is-ok'>" + escapeHtml(fmtMoney(s.total_value, cur)) + "</span><span class='kpi-sub'>" + escapeHtml(t("imp_hours_saved_sub", { h: s.time_saved_hours || 0 })) + "</span></div>"
      + "<div class='kpi-card'><span class='kpi-lbl'>" + escapeHtml(t("imp_kpi_roi")) + "</span><span class='kpi-val" + roiCls + "'>" + escapeHtml(roiVal) + "</span><span class='kpi-sub'>" + escapeHtml(fmtMoney(s.net_impact, cur)) + "</span></div>";
  }
  const tblWrap = document.getElementById("imp-roi-table-wrap"), rows = s.by_project || [];
  if (tblWrap) {
    tblWrap.innerHTML = rows.length ? "<table class='roi-table'><thead><tr><th>" + escapeHtml(t("imp_col_project")) + "</th><th>" + escapeHtml(t("imp_col_hours")) + "</th><th>" + escapeHtml(t("imp_col_cost")) + "</th><th>" + escapeHtml(t("imp_col_value")) + "</th><th>" + escapeHtml(t("imp_col_net")) + "</th><th>" + escapeHtml(t("imp_col_roi")) + "</th></tr></thead><tbody>"
      + rows.map(function (r) {
        const pr = r.roi_pct !== null && r.roi_pct !== undefined ? (r.roi_pct + "%") : "—";
        return "<tr><td><strong>" + escapeHtml(impProjectTitle(r.project_id)) + "</strong></td><td>" + r.hours + "h</td><td>" + escapeHtml(fmtMoney(r.cost, cur)) + "</td><td>" + escapeHtml(fmtMoney(r.value, cur)) + "</td><td>" + escapeHtml(fmtMoney(r.net, cur)) + "</td><td>" + escapeHtml(pr) + "</td></tr>";
      }).join("") + "</tbody></table>" : "";
  }
  const jList = document.getElementById("imp-journal-list");
  if (jList) {
    if (!impState.impact_entries.length) { jList.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("imp_empty_journal")) + "</div>"; }
    else {
      jList.innerHTML = impState.impact_entries.map(function (e) {
        return "<article class='impact-card'>"
          + "<div style='display:flex;align-items:center;justify-content:space-between;gap:0.5rem;flex-wrap:wrap'><div style='display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap'><span class='wb-chip'>" + escapeHtml(e.date) + "</span><span class='wb-chip'>" + escapeHtml(t(IMP_TAG_KEYS[e.outcome_tag] || "imp_tag_quality")) + "</span>" + (e.project_id ? "<span class='wb-chip'>" + escapeHtml(impProjectTitle(e.project_id)) + "</span>" : "") + "</div>"
          + "<button type='button' data-imp-edit='" + escapeHtml(e.id) + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("imp_edit_btn")) + "</button></div>"
          + "<div><div class='impact-q-lbl'>" + escapeHtml(t("imp_what_done")) + "</div><div style='font-weight:500;margin-top:0.15rem'>" + escapeHtml(e.what_done) + "</div></div>"
          + "<div><div class='impact-q-lbl'>" + escapeHtml(t("imp_effect")) + "</div><div style='margin-top:0.15rem;color:var(--prose)'>" + escapeHtml(e.effect) + "</div></div>"
          + (e.evidence_notes ? "<div style='font-size:calc(0.85rem * var(--ui-scale,1));color:var(--text-muted)'>" + escapeHtml(e.evidence_notes) + "</div>" : "")
          + "<div style='display:flex;flex-wrap:wrap;gap:0.4rem'>" + (e.hours_invested ? "<span class='wb-chip'>" + e.hours_invested + "h</span>" : "") + (e.time_saved_hours ? "<span class='wb-chip'>+" + e.time_saved_hours + "h</span>" : "") + (e.estimated_value ? "<span class='wb-chip'>" + escapeHtml(fmtMoney(e.estimated_value, cur)) + "</span>" : "") + "</div></article>";
      }).join("");
      jList.querySelectorAll("[data-imp-edit]").forEach(function (btn) { btn.addEventListener("click", function () { openImpactEntryModal(btn.getAttribute("data-imp-edit")); }); });
    }
  }
  const rollup = document.getElementById("imp-time-rollup"), tList = document.getElementById("imp-time-list");
  if (rollup) { rollup.textContent = t("imp_rollup", { w: s.week_hours || 0, m: s.month_hours || 0, t: s.total_hours || 0 }); }
  if (tList) {
    if (!impState.time_entries.length) { tList.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("imp_empty_time")) + "</div>"; }
    else {
      tList.innerHTML = impState.time_entries.slice(0, 60).map(function (te) {
        return "<div class='wb-task-row'><span class='wb-chip'>" + escapeHtml(te.date) + "</span>"
          + "<div style='min-width:0'><div style='font-weight:500'>" + escapeHtml(te.label) + "</div><div style='font-size:calc(0.8rem * var(--ui-scale,1));color:var(--text-muted)'>" + escapeHtml(impProjectTitle(te.project_id) + " · " + te.source) + "</div></div>"
          + "<div style='display:flex;align-items:center;gap:0.45rem'><span class='wb-chip'>" + Math.round(te.duration_minutes) + " min</span><button type='button' data-imp-del-time='" + escapeHtml(te.id) + "' aria-label='Delete time entry' class='wb-icon-btn'>✕</button></div></div>";
      }).join("");
      tList.querySelectorAll("[data-imp-del-time]").forEach(function (b) { b.addEventListener("click", function () { impApi("/api/impact/time/" + encodeURIComponent(b.getAttribute("data-imp-del-time")), { method: "DELETE" }); }); });
    }
  }
  syncImpactTimerUI();
}
function openImpactEntryModal(entryId) {
  const modal = document.getElementById("impact-entry-modal"); if (!modal) { return; }
  const e = entryId ? impState.impact_entries.find(function (x) { return x.id === entryId; }) : null;
  document.getElementById("ie-modal-title").textContent = e ? t("imp_edit_btn") : t("imp_modal_new");
  document.getElementById("ie-id").value = e ? e.id : "";
  document.getElementById("ie-date").value = e ? e.date : (typeof wbTodayIso === "function" ? wbTodayIso() : new Date().toISOString().slice(0, 10));
  if (typeof populateProjectSelect === "function") { populateProjectSelect(document.getElementById("ie-project"), e ? e.project_id : "", true); }
  document.getElementById("ie-what").value = e ? e.what_done : "";
  document.getElementById("ie-effect").value = e ? e.effect : "";
  document.getElementById("ie-notes").value = e ? (e.evidence_notes || "") : "";
  document.getElementById("ie-hours").value = e ? String(e.hours_invested || 0) : "0";
  document.getElementById("ie-saved").value = e ? String(e.time_saved_hours || 0) : "0";
  document.getElementById("ie-cost").value = e ? String(e.direct_cost || 0) : "0";
  document.getElementById("ie-value").value = e ? String(e.estimated_value || 0) : "0";
  document.getElementById("ie-tag").value = e ? (e.outcome_tag || "quality") : "quality";
  document.getElementById("ie-delete").hidden = !e;
  modal.showModal(); document.getElementById("ie-what").focus();
}
async function downloadImpactReport(fmt) {
  try {
    const res = await areaFetch("/api/impact/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ format: fmt }) });
    if (!res.ok) { throw new Error("Report export failed"); }
    downloadBlob(await res.blob(), (activeKnowledgeArea || "realm") + "_impact_roi." + fmt);
    showToast(t("imp_report_toast"));
  } catch (err) { showToast(err.message || "Export failed", 3500); }
}
function bindImpactUX() {
  const sBtn = document.getElementById("sidebar-impact-btn");
  if (sBtn) { sBtn.addEventListener("click", function () { openImpactView(); }); }
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#imp-tablist [role='tab']", function (b) { setImpactTab(b.getAttribute("data-imp-tab")); }); }
  document.querySelectorAll("[data-imp-tab]").forEach(function (b) { b.addEventListener("click", function () { setImpactTab(b.getAttribute("data-imp-tab")); }); });
  const addEntryBtn = document.getElementById("imp-add-entry-btn");
  if (addEntryBtn) { addEntryBtn.addEventListener("click", function () { openImpactEntryModal(null); }); }
  const pdfBtn = document.getElementById("imp-exp-pdf-btn"), pptBtn = document.getElementById("imp-exp-pptx-btn"), csvBtn = document.getElementById("imp-export-csv-btn");
  if (pdfBtn) { pdfBtn.addEventListener("click", function () { downloadImpactReport("pdf"); }); }
  if (pptBtn) { pptBtn.addEventListener("click", function () { downloadImpactReport("pptx"); }); }
  if (csvBtn) {
    csvBtn.addEventListener("click", async function () {
      const res = await areaFetch("/api/impact/timesheet.csv");
      if (res.ok) { downloadBlobText(await res.text(), (activeKnowledgeArea || "realm") + "_timesheet.csv", "text/csv;charset=utf-8"); }
    });
  }
  const stBtn = document.getElementById("imp-timer-start-btn"), paBtn = document.getElementById("imp-timer-pause-btn"), spBtn = document.getElementById("imp-timer-stop-btn");
  if (stBtn) { stBtn.addEventListener("click", function () { impApi("/api/impact/timer/start", { method: "POST", body: JSON.stringify({ label: document.getElementById("imp-timer-label").value.trim() || "Work Session", project_id: document.getElementById("imp-timer-project").value || "" }) }); }); }
  if (paBtn) { paBtn.addEventListener("click", function () { impApi("/api/impact/timer/toggle", { method: "POST" }); }); }
  if (spBtn) { spBtn.addEventListener("click", async function () { if (await impApi("/api/impact/timer/stop", { method: "POST", body: JSON.stringify({ notes: "" }) })) { showToast(t("imp_saved_toast")); } }); }
  const rateForm = document.getElementById("imp-rate-form");
  if (rateForm) { rateForm.addEventListener("submit", async function (e) { e.preventDefault(); if (await impApi("/api/impact/settings", { method: "PATCH", body: JSON.stringify({ default_hourly_rate: Number(document.getElementById("imp-cfg-rate").value || 0), currency: document.getElementById("imp-cfg-cur").value || "EUR" }) })) { showToast(t("imp_saved_toast")); } }); }
  const mtForm = document.getElementById("imp-manual-time-form");
  if (mtForm) {
    mtForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const lbl = document.getElementById("imp-mt-label").value.trim(), mins = Number(document.getElementById("imp-mt-mins").value || 0);
      if (!lbl || mins <= 0) { return; }
      document.getElementById("imp-mt-label").value = "";
      await impApi("/api/impact/time", { method: "POST", body: JSON.stringify({ label: lbl, duration_minutes: mins, date: document.getElementById("imp-mt-date").value || "", project_id: document.getElementById("imp-mt-project").value || "" }) });
    });
  }
  const ieForm = document.getElementById("ie-form"), ieDel = document.getElementById("ie-delete"), ieAi = document.getElementById("ie-ai-draft-btn");
  if (ieAi) {
    ieAi.addEventListener("click", async function () {
      const notes = [document.getElementById("ie-what").value, document.getElementById("ie-effect").value, document.getElementById("ie-notes").value].filter(Boolean).join("\n");
      const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
      const data = await impApi("/api/impact/draft", { method: "POST", headers: headers, body: JSON.stringify({ notes: notes || "Completed project milestones", hours: Number(document.getElementById("ie-hours").value || 0), use_ai: true, provider: providerEl ? providerEl.value : "ollama", model: (modelEl && modelEl.value) || "qwen3:8b", language: activeLanguage || "en" }) });
      if (data && data.draft) {
        document.getElementById("ie-what").value = data.draft.what_done || "";
        document.getElementById("ie-effect").value = data.draft.effect || "";
        if (data.draft.outcome_tag) { document.getElementById("ie-tag").value = data.draft.outcome_tag; }
      }
    });
  }
  if (ieForm) {
    ieForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = document.getElementById("ie-id").value.trim();
      const body = { date: document.getElementById("ie-date").value, project_id: document.getElementById("ie-project").value || "", what_done: document.getElementById("ie-what").value.trim(), effect: document.getElementById("ie-effect").value.trim(), evidence_notes: document.getElementById("ie-notes").value.trim(), hours_invested: Number(document.getElementById("ie-hours").value || 0), time_saved_hours: Number(document.getElementById("ie-saved").value || 0), direct_cost: Number(document.getElementById("ie-cost").value || 0), estimated_value: Number(document.getElementById("ie-value").value || 0), outcome_tag: document.getElementById("ie-tag").value };
      if (!body.what_done || !body.effect) { return; }
      if (await impApi(id ? ("/api/impact/entries/" + encodeURIComponent(id)) : "/api/impact/entries", { method: id ? "PATCH" : "POST", body: JSON.stringify(body) })) { document.getElementById("impact-entry-modal").close(); }
    });
  }
  if (ieDel) { ieDel.addEventListener("click", async function () { const id = document.getElementById("ie-id").value.trim(); if (id && await impApi("/api/impact/entries/" + encodeURIComponent(id), { method: "DELETE" })) { document.getElementById("impact-entry-modal").close(); } }); }
}
"""
