"""Client controller for Built-in Private AI setup, SSE progress, Eco/Performance & offline badge."""

LOCAL_AI_SCRIPT: str = r"""
let localAiStatus = null, localAiBusy = false;

function isBuiltinInstalled() {
  return Boolean(localAiStatus && localAiStatus.offline_ready);
}

function formatBuiltinModelLabel(modelId) {
  const presets = (localAiStatus && localAiStatus.presets) || [];
  const hit = presets.find(function (p) { return p.id === modelId; });
  if (hit && hit.label_key) { return t(hit.label_key); }
  const id = String(modelId || "");
  if (id.startsWith("ultra-")) { return t("lai_tier_ultra"); }
  if (id.startsWith("compact-")) { return t("lai_tier_compact"); }
  if (id.startsWith("balanced-")) { return t("lai_tier_balanced"); }
  if (id.startsWith("deep-")) { return t("lai_tier_deep"); }
  return id;
}

function formatDiskSize(mb) {
  const n = Number(mb || 0);
  return n >= 1024 ? ((n / 1024).toFixed(1) + " GB") : (Math.max(0, Math.round(n)) + " MB");
}

function syncOfflineStatusChrome() {
  const privEl = document.getElementById("sh-pop-privacy");
  const pillEl = document.getElementById("system-status-pill");
  const usingBuiltin = providerEl && providerEl.value === "builtin" && isBuiltinInstalled();
  if (privEl && usingBuiltin) { privEl.textContent = t("lai_privacy_offline"); }
  if (pillEl && usingBuiltin) {
    pillEl.title = t("lai_privacy_offline");
    pillEl.setAttribute("aria-label", t("lai_privacy_offline"));
  }
}

function updateLocalAiProgress(stage, pct, dlMb, totMb) {
  const stageKey = "lai_stage_" + String(stage || "runtime");
  const label = t(stageKey) !== stageKey ? t(stageKey) : t("lai_st_downloading");
  const meta = totMb > 0 ? (pct + "% · " + formatDiskSize(dlMb) + " / " + formatDiskSize(totMb)) : (pct + "%");
  for (const pfx of ["onboarding", "settings"]) {
    const box = document.getElementById(pfx + "-lai-progress-box");
    const st = document.getElementById(pfx + "-lai-progress-stage");
    const mt = document.getElementById(pfx + "-lai-progress-meta");
    const bar = document.getElementById(pfx + "-lai-progress-bar");
    if (box) { box.hidden = false; }
    if (st) { st.textContent = label; }
    if (mt) { mt.textContent = meta; }
    if (bar) { bar.style.width = Math.max(0, Math.min(100, pct)) + "%"; bar.setAttribute("aria-valuenow", String(pct)); }
  }
}

function setLocalAiStatusMsg(msg) {
  for (const pfx of ["onboarding", "settings"]) {
    const el = document.getElementById(pfx + "-lai-status");
    if (el) { el.textContent = msg || ""; }
  }
}

function renderLocalAiPanels() {
  const st = localAiStatus;
  if (!st) { return; }
  const stateKey = "lai_st_" + (st.state || "not_installed");
  for (const pfx of ["onboarding", "settings"]) {
    const badge = document.getElementById(pfx + "-lai-offline-badge");
    const pill = document.getElementById(pfx + "-lai-state-pill");
    const fit = document.getElementById(pfx + "-lai-fit-note");
    const lowRam = document.getElementById(pfx + "-lai-low-ram");
    const sel = document.getElementById(pfx + "-lai-tier-select");
    const setupBtn = document.getElementById(pfx + "-lai-setup-btn");
    const progBox = document.getElementById(pfx + "-lai-progress-box");
    const ctrlBox = document.getElementById(pfx + "-lai-controls-box");
    const profNote = document.getElementById(pfx + "-lai-profile-note");
    const remBtn = document.querySelector("[data-lai-remove-btn='" + pfx + "']");
    const sleepBtn = document.querySelector("[data-lai-sleep-btn='" + pfx + "']");

    if (badge) { badge.hidden = !st.offline_ready; }
    if (pill) { pill.textContent = t(stateKey); }
    if (lowRam) { lowRam.hidden = !st.low_ram_warning; }
    if (fit) {
      if (!st.supported) { fit.textContent = t("lai_unsupported"); }
      else {
        fit.textContent = st.ram_gb
          ? t("lai_fit_detected", { ram: st.ram_gb, size: st.recommended_size_gb, free: st.free_disk_gb })
          : t("lai_fit_unknown", { size: st.recommended_size_gb, free: st.free_disk_gb });
      }
    }
    if (sel) {
      const prevVal = sel.value;
      sel.innerHTML = (st.presets || []).map(function (p) {
        const flags = [];
        if (p.recommended) { flags.push(t("lai_tag_rec")); }
        if (p.installed) { flags.push(t("lai_tag_inst")); }
        const extra = flags.length ? (" · " + flags.join(" · ")) : "";
        return "<option value='" + escapeHtml(p.id) + "'>" + escapeHtml(t(p.label_key) + " (~" + p.size_gb + " GB" + extra + ")") + "</option>";
      }).join("");
      const desired = (prevVal && (st.presets || []).some(function (p) { return p.id === prevVal; }))
        ? prevVal : (st.active_model_id || st.recommended_model_id || "");
      if (desired) { sel.value = desired; }
      sel.disabled = !st.supported || localAiBusy;
    }
    if (setupBtn && sel) {
      const chosen = (st.presets || []).find(function (p) { return p.id === sel.value; });
      const chosenInst = Boolean(chosen && chosen.installed && st.runtime_installed);
      const isActive = chosenInst && st.active_model_id === sel.value && providerEl && providerEl.value === "builtin";
      setupBtn.disabled = !st.supported || localAiBusy || isActive;
      setupBtn.textContent = isActive ? t("lai_active_btn") : (chosenInst ? t("lai_use_tier_btn") : (st.offline_ready ? t("lai_download_tier_btn") : t("lai_setup_btn")));
    }
    if (progBox && !localAiBusy) { progBox.hidden = true; }
    if (ctrlBox) { ctrlBox.hidden = !st.offline_ready; }
    if (ctrlBox && st.offline_ready) {
      ctrlBox.querySelectorAll("[data-lai-profile]").forEach(function (btn) {
        const active = btn.getAttribute("data-lai-profile") === st.profile;
        btn.setAttribute("aria-pressed", String(active));
        btn.className = active
          ? "px-3 py-1 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]"
          : "px-3 py-1 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]";
      });
    }
    if (profNote) {
      profNote.textContent = st.profile === "performance"
        ? t("lai_prof_perf_note", { mins: st.idle_minutes })
        : t("lai_prof_eco_note", { mins: st.idle_minutes });
    }
    if (remBtn) { remBtn.textContent = t("lai_remove_btn", { size: formatDiskSize(st.disk_used_mb) }); remBtn.disabled = localAiBusy; }
    if (sleepBtn) { sleepBtn.disabled = localAiBusy || st.state !== "ready"; }
  }
  syncOfflineStatusChrome();
  if (typeof modelEl !== "undefined" && modelEl) {
    let changed = false;
    Array.from(modelEl.options).forEach(function (o) {
      if (!o.value && o.disabled) {
        const lbl = t("no_models_avail");
        if (o.textContent !== lbl) { o.textContent = lbl; changed = true; }
      } else if (o.dataset.provider === "builtin") {
        const lbl = formatBuiltinModelLabel(o.value);
        if (o.textContent !== lbl) { o.textContent = lbl; changed = true; }
      }
    });
    if (changed && typeof syncModelMirrors === "function") { syncModelMirrors(); }
  }
  if (typeof renderProviderPills === "function") { renderProviderPills(); }
}

async function loadLocalAiStatus() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  try {
    const res = await fetch("/api/local-ai/status");
    if (!res.ok) { return; }
    localAiStatus = await safeJson(res);
    renderLocalAiPanels();
    const prefModel = safeStorageGet("preferred_local_model", "");
    if (localAiStatus.offline_ready && providerEl && providerEl.value === "ollama" && (safeStorageGet("preferred_provider") === "builtin" || (prefModel && (localAiStatus.installed_models || []).includes(prefModel)))) {
      await activateBuiltinProvider(localAiStatus.active_model_id || prefModel);
    }
  } catch (_e) {}
}

async function activateBuiltinProvider(modelId) {
  safeStorageSet("preferred_provider", "builtin");
  if (providerEl) { providerEl.value = "builtin"; }
  const obProv = document.getElementById("onboarding-provider");
  if (obProv) { obProv.value = "builtin"; }
  if (typeof syncProviderPrivacyUI === "function") {
    syncProviderPrivacyUI("builtin", "settings-privacy-notice", "settings-api-key-group");
    syncProviderPrivacyUI("builtin", "onboarding-privacy-notice", "onboarding-api-key-group");
  }
  if (typeof loadModels === "function") { await loadModels(); }
  if (modelId && typeof selectActiveModel === "function") { selectActiveModel(modelId, "builtin"); }
  if (typeof syncKeyStatusUI === "function") { syncKeyStatusUI(); }
  renderLocalAiPanels();
}

async function handleLocalAiSetupClick(prefix) {
  if (localAiBusy || !localAiStatus || !localAiStatus.supported) { return; }
  const sel = document.getElementById(prefix + "-lai-tier-select");
  const modelId = (sel && sel.value) || localAiStatus.recommended_model_id || "recommended";
  const chosen = (localAiStatus.presets || []).find(function (p) { return p.id === modelId; });
  if (chosen && chosen.installed && localAiStatus.runtime_installed) {
    try {
      const res = await fetch("/api/local-ai/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ active_model_id: modelId }) });
      if (res.ok) { localAiStatus = await safeJson(res); }
      await activateBuiltinProvider(modelId);
      renderLocalAiPanels();
      setLocalAiStatusMsg(t("lai_ready_msg"));
    } catch (_e) {}
    return;
  }
  localAiBusy = true;
  renderLocalAiPanels();
  setLocalAiStatusMsg("");
  updateLocalAiProgress("runtime", 0, 0, 0);
  try {
    const res = await fetch("/api/local-ai/setup/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_id: modelId }),
    });
    if (!res.ok) {
      const err = await safeJson(res);
      throw new Error(err.detail || "Setup could not start.");
    }
    let finalErr = "";
    await readSseStream(res, function (ev, payload) {
      if (ev === "progress" && payload) {
        updateLocalAiProgress(payload.stage, Number(payload.pct || 0), Number(payload.downloaded_mb || 0), Number(payload.total_mb || 0));
      } else if (ev === "done" && payload) {
        localAiStatus = payload;
      } else if (ev === "error" && payload) {
        finalErr = payload.detail || "Setup did not finish.";
      }
    });
    if (finalErr) {
      setLocalAiStatusMsg(finalErr);
    } else if (localAiStatus && localAiStatus.offline_ready) {
      await activateBuiltinProvider(localAiStatus.active_model_id || modelId);
      setLocalAiStatusMsg(t("lai_ready_msg"));
    }
  } catch (err) {
    setLocalAiStatusMsg((err && err.message) || "Setup could not be completed.");
  } finally {
    localAiBusy = false;
    await loadLocalAiStatus();
  }
}

async function cancelLocalAiSetup() {
  try { await fetch("/api/local-ai/cancel-setup", { method: "POST" }); } catch (_e) {}
}

async function setLocalAiProfile(profile) {
  try {
    const res = await fetch("/api/local-ai/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ profile: profile }) });
    if (res.ok) { localAiStatus = await safeJson(res); renderLocalAiPanels(); }
  } catch (_e) {}
}

async function sleepLocalAiNow() {
  try {
    const res = await fetch("/api/local-ai/unload", { method: "POST" });
    if (res.ok) {
      const data = await safeJson(res);
      if (data.status) { localAiStatus = data.status; }
      renderLocalAiPanels();
      setLocalAiStatusMsg(t("lai_slept_msg"));
    }
  } catch (_e) {}
}

async function removeLocalAiRuntime() {
  if (!localAiStatus) { return; }
  const size = formatDiskSize(localAiStatus.disk_used_mb);
  if (typeof confirmDeletion === "function" && !(await confirmDeletion(t("lai_remove_confirm", { size: size })))) { return; }
  try {
    const res = await fetch("/api/local-ai/runtime", { method: "DELETE" });
    const data = await safeJson(res);
    if (!res.ok) { setLocalAiStatusMsg(data.detail || "Could not remove files."); return; }
    if (data.status) { localAiStatus = data.status; }
    if (providerEl && providerEl.value === "builtin") {
      safeStorageRemove("preferred_provider");
      providerEl.value = "ollama";
      const obProv = document.getElementById("onboarding-provider");
      if (obProv) { obProv.value = "ollama"; }
      if (typeof loadModels === "function") { await loadModels(); }
    }
    renderLocalAiPanels();
    setLocalAiStatusMsg(t("lai_removed_msg", { size: formatDiskSize(data.freed_mb) }));
  } catch (_e) {}
}

function bindLocalAiUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  document.querySelectorAll("[data-lai-setup-btn]").forEach(function (btn) {
    btn.addEventListener("click", function () { handleLocalAiSetupClick(btn.getAttribute("data-lai-setup-btn")); });
  });
  document.querySelectorAll("[data-lai-tier-select]").forEach(function (sel) {
    sel.addEventListener("change", function () {
      const val = sel.value;
      document.querySelectorAll("[data-lai-tier-select]").forEach(function (other) { if (other !== sel) { other.value = val; } });
      renderLocalAiPanels();
    });
  });
  document.querySelectorAll("[data-lai-cancel-btn]").forEach(function (btn) {
    btn.addEventListener("click", cancelLocalAiSetup);
  });
  document.querySelectorAll("[data-lai-profile]").forEach(function (btn) {
    btn.addEventListener("click", function () { setLocalAiProfile(btn.getAttribute("data-lai-profile")); });
  });
  document.querySelectorAll("[data-lai-sleep-btn]").forEach(function (btn) {
    btn.addEventListener("click", sleepLocalAiNow);
  });
  document.querySelectorAll("[data-lai-remove-btn]").forEach(function (btn) {
    btn.addEventListener("click", removeLocalAiRuntime);
  });
  loadLocalAiStatus();
}
"""
