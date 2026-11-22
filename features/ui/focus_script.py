"""Superfocus Engine client: Goal Seasons, Web Audio Soundscapes, Deep Focus Ring, and AI Weekly Planner."""

FOCUS_SCRIPT: str = r"""
let focState = { goals: [], sessions: [], analytics: {} }, focViewOpen = false, focPlanBlocks = [];
let dfPlannedMins = 45, dfRemainingSec = 2700, dfElapsedSec = 0, dfRunning = false, dfTickId = null, dfSound = "off", dfQuality = 4;
let dfAudioCtx = null, dfGainNode = null, dfAudioNodes = [];
const FOC_PACE_KEYS = { ahead: "foc_pace_ahead", on_track: "foc_pace_on_track", behind: "foc_pace_behind" };
const FOC_SND_KEYS = { off: "foc_snd_off", brown: "foc_snd_brown", rain: "foc_snd_rain", drone: "foc_snd_drone" };
function stopFocusSoundscape() {
  dfAudioNodes.forEach(function (n) { try { if (n.stop) { n.stop(); } n.disconnect(); } catch (_e) {} });
  dfAudioNodes = [];
  if (dfAudioCtx) { try { dfAudioCtx.close(); } catch (_e) {} dfAudioCtx = null; dfGainNode = null; }
}
function startFocusSoundscape(mode) {
  stopFocusSoundscape();
  dfSound = mode || "off";
  document.querySelectorAll("[data-df-sound]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-df-sound") === dfSound)); });
  if (dfSound === "off") { return; }
  const AC = window.AudioContext || window.webkitAudioContext; if (!AC) { return; }
  try {
    const ctx = new AC(), gain = ctx.createGain(), volEl = document.getElementById("df-vol");
    gain.gain.value = (Number(volEl ? volEl.value : 35) / 100) * 0.25;
    gain.connect(ctx.destination);
    dfAudioCtx = ctx; dfGainNode = gain;
    if (dfSound === "drone") {
      const filt = ctx.createBiquadFilter(); filt.type = "lowpass"; filt.frequency.value = 320; filt.connect(gain);
      [110, 164.81, 220].forEach(function (freq) {
        const osc = ctx.createOscillator(); osc.type = "sine"; osc.frequency.value = freq; osc.connect(filt); osc.start(); dfAudioNodes.push(osc);
      });
      dfAudioNodes.push(filt);
    } else {
      const len = ctx.sampleRate * 3, buf = ctx.createBuffer(1, len, ctx.sampleRate), ch = buf.getChannelData(0);
      let last = 0;
      for (let i = 0; i < len; i++) {
        const w = Math.random() * 2 - 1;
        if (dfSound === "brown") { last = (last + 0.02 * w) / 1.02; ch[i] = last * 3.2; }
        else { ch[i] = w * 0.6; }
      }
      const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
      const filt = ctx.createBiquadFilter();
      filt.type = dfSound === "brown" ? "lowpass" : "bandpass";
      filt.frequency.value = dfSound === "brown" ? 260 : 950;
      if (dfSound === "rain") { filt.Q.value = 0.7; }
      src.connect(filt); filt.connect(gain); src.start();
      dfAudioNodes.push(src, filt);
    }
  } catch (_e) { stopFocusSoundscape(); }
}
function fmtFocusClock(sec) {
  const s = Math.max(0, Math.floor(sec)), m = Math.floor(s / 60), r = s % 60;
  return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
}
function syncDeepFocusRing() {
  const prog = document.getElementById("df-progress"), clk = document.getElementById("df-clock"), stLbl = document.getElementById("df-state-lbl");
  const totalSec = Math.max(60, dfPlannedMins * 60);
  const pct = Math.min(100, Math.round((dfElapsedSec / totalSec) * 100));
  const txt = fmtFocusClock(dfRemainingSec);
  if (clk) { clk.textContent = txt; }
  if (prog) {
    prog.value = pct; prog.setAttribute("value", String(pct));
    prog.style.setProperty("--value", String(pct));
    prog.setAttribute("aria-valuetext", txt + " (" + pct + "%)");
  }
  if (stLbl) { stLbl.textContent = dfRunning ? t("foc_running") : (dfElapsedSec > 0 ? t("foc_paused") : t("foc_ready")); }
  const spBtn = document.getElementById("df-start-pause-btn");
  if (spBtn) { spBtn.textContent = dfRunning ? t("imp_pause") : (dfElapsedSec > 0 ? t("foc_resume") : t("foc_begin")); }
}
function stopDeepFocusTick() { if (dfTickId) { clearInterval(dfTickId); dfTickId = null; } dfRunning = false; }
function openDeepFocusModal(presetGoalId, presetLabel) {
  const modal = document.getElementById("deep-focus-modal"); if (!modal) { return; }
  stopDeepFocusTick(); dfElapsedSec = 0; dfRemainingSec = dfPlannedMins * 60;
  document.getElementById("df-label").value = presetLabel || "Deep Work Sprint";
  const gSel = document.getElementById("df-goal-select");
  if (gSel) {
    gSel.innerHTML = "<option value=''>" + escapeHtml(t("foc_no_goal")) + "</option>" + (focState.goals || []).map(function (g) {
      return "<option value='" + escapeHtml(g.id) + "'" + (g.id === presetGoalId ? " selected" : "") + ">" + escapeHtml(g.title) + "</option>";
    }).join("");
    if (presetGoalId) { gSel.value = presetGoalId; }
  }
  document.getElementById("df-checkin-form").hidden = true;
  document.getElementById("df-controls-row").hidden = false;
  syncDeepFocusRing(); modal.showModal();
}
function showFocusCheckin() {
  stopDeepFocusTick(); stopFocusSoundscape(); syncDeepFocusRing();
  document.getElementById("df-controls-row").hidden = true;
  document.getElementById("df-checkin-form").hidden = false;
  document.getElementById("df-reflection").focus();
}
function applyFocusState(data) {
  if (!data || !Array.isArray(data.goals)) { return; }
  focState = { goals: data.goals, sessions: data.sessions || [], analytics: data.analytics || {} };
  const badge = document.getElementById("sidebar-focus-badge");
  if (badge) { badge.textContent = ((focState.analytics && focState.analytics.week_hours) || 0) + "h"; }
  if (focViewOpen) { renderFocusView(); }
}
async function focApi(path, opts) {
  const version = areaVersion, cfg = Object.assign({ headers: {} }, opts || {});
  if (cfg.body && !cfg.headers["Content-Type"]) { cfg.headers["Content-Type"] = "application/json"; }
  try {
    const res = await areaFetch(path, cfg), data = await safeJson(res);
    if (version !== areaVersion) { return null; }
    if (!res.ok) { throw new Error(data.detail || "Focus request failed"); }
    if (Array.isArray(data.goals)) { applyFocusState(data); }
    return data;
  } catch (err) {
    if (version === areaVersion) { showToast(err.message || "Focus error", 3500); }
    return null;
  }
}
async function loadFocusSummary() { await focApi("/api/focus"); }
function closeFocusView() {
  focViewOpen = false;
  const v = document.getElementById("focus-view"); if (v) { v.classList.add("hidden"); }
  const b = document.getElementById("sidebar-focus-btn"); if (b) { b.classList.remove("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
}
async function openFocusView() {
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  if (typeof closeWorkBoardView === "function") { closeWorkBoardView(); }
  if (typeof closeImpactView === "function") { closeImpactView(); }
  if (typeof closeWorkflowsView === "function") { closeWorkflowsView(); }
  if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); }
  focViewOpen = true;
  if (typeof setAmbientDimmed === "function") { setAmbientDimmed(true); }
  const shell = document.getElementById("workspace-shell"), gv = document.getElementById("graph-view"), v = document.getElementById("focus-view");
  if (shell) { shell.classList.add("hidden"); } if (gv) { gv.classList.add("hidden"); } if (v) { v.classList.remove("hidden"); }
  const b = document.getElementById("sidebar-focus-btn"); if (b) { b.classList.add("bg-[#4BB8E8]/15", "text-[#4BB8E8]"); }
  await focApi("/api/focus");
  renderFocusView();
}
function renderFocusView() {
  const an = focState.analytics || {}, stats = document.getElementById("foc-stats");
  if (stats) {
    stats.innerHTML = "<span class='wb-stat-pill is-accent'>" + escapeHtml(t("foc_stat_week", { h: an.week_hours || 0 })) + "</span>"
      + "<span class='wb-stat-pill'>" + escapeHtml(t("foc_stat_streak", { n: an.streak_days || 0 })) + "</span>"
      + (an.avg_quality ? "<span class='wb-stat-pill'>" + escapeHtml(t("foc_stat_quality", { q: an.avg_quality })) + "</span>" : "");
  }
  const grid = document.getElementById("foc-goals-grid"), trajs = an.trajectories || {};
  if (grid) {
    if (!focState.goals.length) {
      grid.innerHTML = "<div class='wb-empty' style='grid-column:1/-1'>" + escapeHtml(t("foc_empty_goals")) + "</div>";
    } else {
      grid.innerHTML = focState.goals.map(function (g) {
        const tr = trajs[g.id] || { logged_hours: 0, pct_hours: 0, pace: "on_track", days_left: 0 };
        const paceKey = FOC_PACE_KEYS[tr.pace] || "foc_pace_on_track";
        const msHtml = (g.weekly_milestones || []).slice(0, 3).map(function (m) { return "<li style='font-size:0.82rem;color:var(--text-muted)'>• " + escapeHtml(m) + "</li>"; }).join("");
        return "<article class='goal-card'>"
          + "<div style='display:flex;align-items:center;justify-content:space-between;gap:0.5rem'><h3 style='margin:0;font-size:calc(1rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(g.title) + "</h3><span class='wb-chip goal-pace-" + escapeHtml(tr.pace) + "'>" + escapeHtml(t(paceKey)) + "</span></div>"
          + (g.why ? "<p style='margin:0;font-size:0.85rem;color:var(--text-muted)'>" + escapeHtml(g.why) + "</p>" : "")
          + "<div style='display:flex;justify-content:space-between;font-size:0.8rem;color:var(--text-muted)'><span>" + tr.logged_hours + "h / " + g.target_hours + "h (" + tr.pct_hours + "%)</span><span>" + escapeHtml(g.start_date + " → " + g.end_date) + "</span></div>"
          + "<progress class='goal-progress' value='" + tr.pct_hours + "' max='100' aria-label='" + escapeHtml(g.title + " progress") + "'></progress>"
          + (msHtml ? "<ul style='margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:0.2rem'>" + msHtml + "</ul>" : "")
          + "<div style='display:flex;gap:0.45rem;margin-top:0.2rem'><button type='button' data-foc-start-goal='" + escapeHtml(g.id) + "' class='wb-btn wb-btn-sm wb-btn-primary'>" + escapeHtml(t("foc_focus_this")) + "</button><button type='button' data-foc-edit-goal='" + escapeHtml(g.id) + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("foc_edit_goal")) + "</button></div>"
          + "</article>";
      }).join("");
      grid.querySelectorAll("[data-foc-start-goal]").forEach(function (btn) {
        btn.addEventListener("click", function () { const g = focState.goals.find(function (x) { return x.id === btn.getAttribute("data-foc-start-goal"); }); openDeepFocusModal(g ? g.id : "", g ? g.title : ""); });
      });
      grid.querySelectorAll("[data-foc-edit-goal]").forEach(function (btn) {
        btn.addEventListener("click", function () { openGoalSeasonModal(btn.getAttribute("data-foc-edit-goal")); });
      });
    }
  }
  const list = document.getElementById("foc-sessions-list");
  if (list) {
    if (!focState.sessions.length) { list.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("foc_empty_sessions")) + "</div>"; }
    else {
      list.innerHTML = focState.sessions.slice(0, 20).map(function (s) {
        return "<div class='wb-task-row'><span class='wb-chip'>" + escapeHtml(s.date) + "</span>"
          + "<div style='min-width:0'><div style='font-weight:500'>" + escapeHtml(s.label) + "</div>" + (s.reflection ? "<div style='font-size:0.82rem;color:var(--text-muted)'>" + escapeHtml(s.reflection) + "</div>" : "") + "</div>"
          + "<div style='display:flex;align-items:center;gap:0.4rem'><span class='wb-chip'>" + Math.round(s.actual_minutes) + " min</span><span class='wb-chip'>" + escapeHtml(t(FOC_SND_KEYS[s.soundscape] || "foc_snd_off")) + "</span><span class='wb-chip'>" + s.quality_rating + "/5</span></div></div>";
      }).join("");
    }
  }
}
function openGoalSeasonModal(goalId) {
  const modal = document.getElementById("goal-season-modal"); if (!modal) { return; }
  const g = goalId ? focState.goals.find(function (x) { return x.id === goalId; }) : null;
  document.getElementById("gs-modal-title").textContent = g ? t("foc_edit_goal") : t("foc_new_goal");
  document.getElementById("gs-id").value = g ? g.id : "";
  document.getElementById("gs-title").value = g ? g.title : "";
  document.getElementById("gs-why").value = g ? (g.why || "") : "";
  const today = typeof wbTodayIso === "function" ? wbTodayIso() : new Date().toISOString().slice(0, 10);
  document.getElementById("gs-start").value = g ? g.start_date : today;
  document.getElementById("gs-end").value = g ? g.end_date : (typeof wbAddDays === "function" ? wbAddDays(today, 84) : today);
  document.getElementById("gs-hours").value = g ? String(g.target_hours) : "24";
  document.getElementById("gs-milestones").value = g && g.weekly_milestones ? g.weekly_milestones.join("\n") : "";
  if (typeof populateProjectSelect === "function") { populateProjectSelect(document.getElementById("gs-project"), g ? g.project_id : "", true); }
  document.getElementById("gs-delete").hidden = !g;
  modal.showModal(); document.getElementById("gs-title").focus();
}
function bindFocusUX() {
  const sBtn = document.getElementById("sidebar-focus-btn");
  if (sBtn) { sBtn.addEventListener("click", openFocusView); }
  const startDeep = document.getElementById("foc-start-deep-btn"), newGoal = document.getElementById("foc-new-goal-btn");
  if (startDeep) { startDeep.addEventListener("click", function () { openDeepFocusModal("", ""); }); }
  if (newGoal) { newGoal.addEventListener("click", function () { openGoalSeasonModal(null); }); }
  document.querySelectorAll("[data-m4-close]").forEach(function (b) { b.addEventListener("click", function () { const d = document.getElementById(b.getAttribute("data-m4-close")); if (d && d.open) { d.close(); } }); });
  const dfModal = document.getElementById("deep-focus-modal"), dfClose = document.getElementById("df-close-btn");
  if (dfClose && dfModal) { dfClose.addEventListener("click", function () { stopDeepFocusTick(); stopFocusSoundscape(); dfModal.close(); }); }
  if (dfModal) { dfModal.addEventListener("close", function () { stopDeepFocusTick(); stopFocusSoundscape(); }); }
  document.querySelectorAll("[data-df-mins]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (dfRunning) { return; }
      dfPlannedMins = Number(btn.getAttribute("data-df-mins") || 45); dfElapsedSec = 0; dfRemainingSec = dfPlannedMins * 60;
      document.querySelectorAll("[data-df-mins]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      syncDeepFocusRing();
    });
  });
  document.querySelectorAll("[data-df-sound]").forEach(function (btn) {
    btn.addEventListener("click", function () { startFocusSoundscape(btn.getAttribute("data-df-sound") || "off"); });
  });
  const volEl = document.getElementById("df-vol");
  if (volEl) { volEl.addEventListener("input", function () { if (dfGainNode) { dfGainNode.gain.value = (Number(volEl.value) / 100) * 0.25; } }); }
  const spBtn = document.getElementById("df-start-pause-btn"), finBtn = document.getElementById("df-finish-btn");
  if (spBtn) {
    spBtn.addEventListener("click", function () {
      if (dfRunning) { stopDeepFocusTick(); syncDeepFocusRing(); return; }
      dfRunning = true; syncDeepFocusRing();
      dfTickId = setInterval(function () {
        dfElapsedSec += 1; dfRemainingSec = Math.max(0, dfPlannedMins * 60 - dfElapsedSec);
        syncDeepFocusRing();
        if (dfRemainingSec <= 0) { showFocusCheckin(); }
      }, 1000);
    });
  }
  if (finBtn) { finBtn.addEventListener("click", showFocusCheckin); }
  const cancelCi = document.getElementById("df-cancel-checkin");
  if (cancelCi) { cancelCi.addEventListener("click", function () { document.getElementById("df-checkin-form").hidden = true; document.getElementById("df-controls-row").hidden = false; }); }
  document.querySelectorAll("[data-df-q]").forEach(function (btn) {
    btn.addEventListener("click", function () { dfQuality = Number(btn.getAttribute("data-df-q") || 4); document.querySelectorAll("[data-df-q]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); }); });
  });
  const ciForm = document.getElementById("df-checkin-form");
  if (ciForm) {
    ciForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const gid = document.getElementById("df-goal-select").value || "";
      const goal = focState.goals.find(function (g) { return g.id === gid; });
      const actualMins = Math.max(1, Math.round(dfElapsedSec / 60) || dfPlannedMins);
      const ok = await focApi("/api/focus/sessions", { method: "POST", body: JSON.stringify({ label: document.getElementById("df-label").value.trim() || "Deep Focus", planned_minutes: dfPlannedMins, actual_minutes: actualMins, quality_rating: dfQuality, soundscape: dfSound, reflection: document.getElementById("df-reflection").value.trim(), goal_id: gid, project_id: goal ? goal.project_id : "", log_time: true }) });
      if (ok) { document.getElementById("df-reflection").value = ""; dfModal.close(); showToast(t("foc_logged_toast")); if (typeof loadImpactSummary === "function") { loadImpactSummary(); } }
    });
  }
  const gsForm = document.getElementById("gs-form"), gsDel = document.getElementById("gs-delete");
  if (gsForm) {
    gsForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const id = document.getElementById("gs-id").value.trim();
      const ms = document.getElementById("gs-milestones").value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
      const body = { title: document.getElementById("gs-title").value.trim(), why: document.getElementById("gs-why").value.trim(), start_date: document.getElementById("gs-start").value, end_date: document.getElementById("gs-end").value, target_hours: Number(document.getElementById("gs-hours").value || 24), project_id: document.getElementById("gs-project").value || "", weekly_milestones: ms };
      if (!body.title) { return; }
      const ok = await focApi(id ? ("/api/focus/goals/" + encodeURIComponent(id)) : "/api/focus/goals", { method: id ? "PATCH" : "POST", body: JSON.stringify(body) });
      if (ok) { document.getElementById("goal-season-modal").close(); }
    });
  }
  if (gsDel) { gsDel.addEventListener("click", async function () { const id = document.getElementById("gs-id").value.trim(); if (id && await focApi("/api/focus/goals/" + encodeURIComponent(id), { method: "DELETE" })) { document.getElementById("goal-season-modal").close(); } }); }
  const planBtn = document.getElementById("foc-plan-btn"), planAcc = document.getElementById("foc-plan-accept-btn"), planDis = document.getElementById("foc-plan-dismiss-btn");
  if (planBtn) {
    planBtn.addEventListener("click", async function () {
      const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
      const data = await focApi("/api/focus/weekly-plan", { method: "POST", headers: headers, body: JSON.stringify({ use_ai: true, provider: providerEl ? providerEl.value : "ollama", model: (modelEl && modelEl.value) || "qwen3:8b", language: activeLanguage || "en" }) });
      if (data && Array.isArray(data.blocks)) {
        focPlanBlocks = data.blocks;
        document.getElementById("foc-plan-list").innerHTML = focPlanBlocks.map(function (b) {
          return "<div class='wb-task-row' style='margin-bottom:0'><span class='wb-chip'>" + escapeHtml(b.date + " " + b.start_time + "–" + b.end_time) + "</span><span style='font-weight:500'>" + escapeHtml(b.title) + "</span><span style='font-size:0.8rem;color:var(--text-muted)'>" + escapeHtml(b.notes || "") + "</span></div>";
        }).join("");
        document.getElementById("foc-plan-box").hidden = false;
      }
    });
  }
  if (planDis) { planDis.addEventListener("click", function () { document.getElementById("foc-plan-box").hidden = true; }); }
  if (planAcc) {
    planAcc.addEventListener("click", async function () {
      if (!focPlanBlocks.length) { return; }
      const data = await focApi("/api/focus/weekly-plan/accept", { method: "POST", body: JSON.stringify({ blocks: focPlanBlocks }) });
      if (data) { document.getElementById("foc-plan-box").hidden = true; showToast(t("foc_plan_saved_toast", { n: data.scheduled_count || 0 })); if (typeof loadWorkBoardSummary === "function") { loadWorkBoardSummary(true); } }
    });
  }
}
"""
