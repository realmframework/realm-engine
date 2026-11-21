"""Phase 6 client logic: Hands-Free Voice Loop, Offline Audio Briefing, Retrieval X-Ray, Web Clipper & Local API."""

POWER_SCRIPT: str = r"""
let voiceLoopEnabled = false, voiceLoopRestartTimer = null;
let briefingMode = "solo", briefingAudioUrl = null, briefingLastTranscript = "", briefingOp = 0;
let xrayRows = [], xrayMutedDocs = [], xrayPinnedDocs = [], xrayLastQuery = "", xrayOp = 0;

function resetXrayOverrides() {
  xrayRows = []; xrayMutedDocs = []; xrayPinnedDocs = []; xrayLastQuery = ""; ++xrayOp;
}

function setVoiceLoopEnabled(on) {
  voiceLoopEnabled = Boolean(on);
  clearTimeout(voiceLoopRestartTimer);
  const toggle = document.getElementById("voice-loop-toggle"), badge = document.getElementById("voice-loop-badge");
  if (toggle) { toggle.checked = voiceLoopEnabled; }
  if (badge) {
    badge.textContent = voiceLoopEnabled ? "ON" : "OFF";
    badge.className = "text-[11px] font-mono " + (voiceLoopEnabled ? "text-[#38D399]" : "text-[#738196]");
  }
  safeStorageSet("realm_voice_loop", voiceLoopEnabled ? "1" : "0");
  if (typeof showToast === "function") { showToast(voiceLoopEnabled ? t("vl_toast_on") : t("vl_toast_off"), 2800); }
}

function handleVoiceLoopAfterAnswer() {
  if (!voiceLoopEnabled || !isVoiceEnabled() || !currentTurns.length) { return; }
  const idx = currentTurns.length - 1;
  const turn = currentTurns[idx];
  if (!turn || !turn.tutor || !turn.tutor.answer || turn.stopped) { return; }
  toggleSpeakTurn(idx);
}

function handleVoiceLoopAfterSpeechEnd() {
  if (!voiceLoopEnabled || document.querySelector("dialog[open]") || activeController) { return; }
  clearTimeout(voiceLoopRestartTimer);
  voiceLoopRestartTimer = setTimeout(function () {
    if (voiceLoopEnabled && !activeRecognition && !activeController && typeof toggleDictation === "function") {
      toggleDictation();
    }
  }, 550);
}

function openBriefingModal(scopeOpts) {
  const modal = document.getElementById("briefing-modal");
  if (!modal) { return; }
  if (!knowledgeAreas.length) {
    if (typeof showToast === "function") { showToast(t("sg_need_ws"), 4000); }
    return;
  }
  modal.dataset.subfolder = (scopeOpts && scopeOpts.subfolder) || "";
  const stEl = document.getElementById("br-status"), outEl = document.getElementById("br-output-wrap");
  if (stEl) { stEl.textContent = ""; }
  if (outEl) { outEl.hidden = true; }
  syncBriefingModeUI();
  modal.showModal();
}

function syncBriefingModeUI() {
  document.querySelectorAll("[data-br-mode]").forEach(function (btn) {
    const on = btn.getAttribute("data-br-mode") === briefingMode;
    btn.setAttribute("aria-pressed", String(on));
    btn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (on ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
}

async function generateAudioBriefingUI() {
  const modal = document.getElementById("briefing-modal"), btn = document.getElementById("br-generate-btn");
  const stEl = document.getElementById("br-status"), outEl = document.getElementById("br-output-wrap");
  const audioBox = document.getElementById("br-audio-box"), player = document.getElementById("br-audio-player"), trBody = document.getElementById("br-transcript-body");
  if (!btn || !stEl) { return; }
  const version = areaVersion, op = ++briefingOp;
  btn.disabled = true; stEl.textContent = t("br_generating");
  if (briefingAudioUrl) { URL.revokeObjectURL(briefingAudioUrl); briefingAudioUrl = null; }
  try {
    const ttsModel = (document.getElementById("tts-model") && document.getElementById("tts-model").value) || "phonon:latest";
    const voiceA = (document.getElementById("tts-voice") && document.getElementById("tts-voice").value) || "default";
    const res = await areaFetch("/api/audio/briefing", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: briefingMode,
        host_a: briefingMode === "duo" ? "Blomkvist" : activeAgentName(),
        host_b: "Lisbeth",
        voice_a: voiceA,
        voice_b: "Zoey",
        model: ttsModel,
        subfolder: (modal && modal.dataset.subfolder) || "",
      }),
    });
    const data = await safeJson(res);
    if (op !== briefingOp || version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Briefing failed."); }
    briefingLastTranscript = data.transcript || "";
    if (trBody) { trBody.innerHTML = formatMarkdown(briefingLastTranscript); }
    if (outEl) { outEl.hidden = false; }
    if (data.synthesized && data.audio_base64 && player && audioBox) {
      const bin = atob(data.audio_base64), arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) { arr[i] = bin.charCodeAt(i); }
      briefingAudioUrl = URL.createObjectURL(new Blob([arr], { type: data.audio_mime || "audio/wav" }));
      player.src = briefingAudioUrl;
      audioBox.hidden = false;
      stEl.textContent = t("br_ready_audio");
    } else {
      if (audioBox) { audioBox.hidden = true; }
      stEl.textContent = data.notice || t("br_ready_script");
    }
  } catch (err) {
    if (op === briefingOp && version === areaVersion) { stEl.textContent = err.message || "Could not generate briefing."; }
  } finally { if (op === briefingOp) { btn.disabled = false; } }
}

async function refreshInspectorXray() {
  const host = document.getElementById("inspector-xray-body");
  if (!host || !currentTurns.length || freeChatMode || !knowledgeAreas.length) { return; }
  const lastTurn = currentTurns[currentTurns.length - 1];
  if (!lastTurn || !lastTurn.query) { return; }
  const version = areaVersion, op = ++xrayOp, chatAtStart = currentChatId;
  xrayLastQuery = lastTurn.query;
  try {
    const res = await areaFetch("/api/search/xray", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: lastTurn.query, top_k: lastTurn.top_k || ragConfig.top_k, rrf_k: lastTurn.rrf_k || ragConfig.rrf_k,
        retrieval_mode: lastTurn.retrieval_mode || ragConfig.retrieval_mode,
        doc_id: lastTurn.doc_id || null, subfolder: lastTurn.subfolder || null,
        muted_doc_ids: xrayMutedDocs, pinned_doc_ids: xrayPinnedDocs,
      }),
    });
    if (!res.ok || op !== xrayOp || version !== areaVersion || chatAtStart !== currentChatId) { return; }
    const data = await safeJson(res);
    if (op !== xrayOp || version !== areaVersion || chatAtStart !== currentChatId) { return; }
    xrayRows = Array.isArray(data.rows) ? data.rows : [];
    renderInspectorXray();
  } catch (_e) {}
}

function renderInspectorXray() {
  const host = document.getElementById("inspector-xray-body");
  if (!host) { return; }
  if (!xrayRows.length) {
    host.innerHTML = "<span class='text-[#738196]'>" + escapeHtml(t("xray_empty")) + "</span>";
    return;
  }
  const hasOverrides = xrayMutedDocs.length > 0 || xrayPinnedDocs.length > 0;
  host.innerHTML = xrayRows.map(function (r) {
    const docId = r.doc_id || "";
    const pinned = xrayPinnedDocs.includes(docId);
    return "<div class='p-2.5 rounded-xl bg-[#04060F] border " + (pinned ? "border-[#4BB8E8]/50" : "border-white/10") + " flex flex-col gap-1.5'>"
      + "<div class='flex items-center justify-between gap-2'><span class='text-xs font-medium text-[#EEF2F8] truncate'>" + escapeHtml(r.title) + "</span>"
      + "<div class='flex items-center gap-1 shrink-0'>"
      + "<button type='button' data-xray-pin='" + escapeHtml(docId) + "' class='px-1.5 py-0.5 rounded text-[10px] font-mono " + (pinned ? "bg-[#4BB8E8]/20 text-[#4BB8E8]" : "bg-white/5 text-[#A0B0C8] hover:text-[#EEF2F8]") + "'>" + escapeHtml(pinned ? t("xray_pinned") : t("xray_pin")) + "</button>"
      + "<button type='button' data-xray-mute='" + escapeHtml(docId) + "' class='px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/5 text-[#A0B0C8] hover:text-red-300'>" + escapeHtml(t("xray_mute")) + "</button>"
      + "</div></div>"
      + "<div class='flex items-center gap-2 font-mono text-[10px] text-[#738196] flex-wrap'>"
      + "<span>BM25: " + (r.bm25_rank ? "#" + r.bm25_rank + " (" + r.bm25_score + ")" : "—") + "</span>"
      + "<span>Vec: " + (r.vector_rank ? "#" + r.vector_rank + " (" + r.vector_score + ")" : "—") + "</span>"
      + "<span class='text-[#4BB8E8]'>RRF: " + r.rrf_score + "</span></div></div>";
  }).join("")
  + (hasOverrides ? "<div class='flex items-center justify-between gap-2 pt-1'><button id='xray-clear-overrides' type='button' class='text-[11px] text-[#A0B0C8] hover:text-[#EEF2F8] underline'>" + escapeHtml(t("xray_reset")) + "</button><button id='xray-rerun-btn' type='button' class='px-2.5 py-1 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/35 text-[11px] text-[#4BB8E8]'>" + escapeHtml(t("xray_rerun")) + "</button></div>" : "");
  host.querySelectorAll("[data-xray-pin]").forEach(btn => btn.addEventListener("click", () => {
    const id = btn.getAttribute("data-xray-pin");
    if (!id) { return; }
    xrayPinnedDocs = xrayPinnedDocs.includes(id) ? xrayPinnedDocs.filter(x => x !== id) : [...xrayPinnedDocs, id];
    refreshInspectorXray();
  }));
  host.querySelectorAll("[data-xray-mute]").forEach(btn => btn.addEventListener("click", () => {
    const id = btn.getAttribute("data-xray-mute");
    if (!id) { return; }
    if (!xrayMutedDocs.includes(id)) { xrayMutedDocs.push(id); }
    xrayPinnedDocs = xrayPinnedDocs.filter(x => x !== id);
    refreshInspectorXray();
  }));
  const clr = document.getElementById("xray-clear-overrides");
  if (clr) { clr.addEventListener("click", () => { xrayMutedDocs = []; xrayPinnedDocs = []; refreshInspectorXray(); }); }
  const rr = document.getElementById("xray-rerun-btn");
  if (rr) { rr.addEventListener("click", () => { if (xrayLastQuery) { queryEl.value = xrayLastQuery; askTutor(); } }); }
}

async function clipUrlToLibrary() {
  const inp = document.getElementById("clip-url-input"), btn = document.getElementById("clip-url-btn"), st = document.getElementById("upload-status");
  if (!inp || !btn) { return; }
  const url = inp.value.trim(), version = areaVersion;
  if (!url) { if (st) { st.textContent = t("clip_enter_url"); } return; }
  btn.disabled = true; if (st) { st.textContent = t("clip_fetching"); }
  try {
    const sub = typeof destinationValue === "function" ? (destinationValue("upload") || "") : "";
    const area = (document.getElementById("upload-save-area") && document.getElementById("upload-save-area").value) || activeKnowledgeArea;
    const res = await areaFetch("/api/guides/clip-url", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, subfolder: sub, area: area }),
    });
    const data = await safeJson(res);
    if (version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not clip URL."); }
    inp.value = "";
    applyWorkspacePayload(data);
    await loadGuidesCatalog(null);
    if (version !== areaVersion) { return; }
    if (st) { st.textContent = t("clip_done", { title: data.title || url }); }
    if (typeof showToast === "function") { showToast(t("clip_done", { title: data.title || url }), 4000); }
    if (document.getElementById("library-view")) { await openLibraryCatalog(selectedTag); }
  } catch (err) {
    if (st && version === areaVersion) { st.textContent = err.message || "Could not clip URL."; }
  } finally { btn.disabled = false; }
}

function syncLocalApiUI(cfg) {
  const on = Boolean(cfg && cfg.enable_local_api);
  const toggle = document.getElementById("local-api-toggle"), badge = document.getElementById("local-api-badge"), info = document.getElementById("local-api-info"), urlEl = document.getElementById("local-api-url");
  if (toggle) { toggle.checked = on; }
  if (badge) { badge.textContent = on ? "ON" : "OFF"; badge.className = "text-[11px] font-mono " + (on ? "text-[#38D399]" : "text-[#738196]"); }
  if (info) { info.hidden = !on; }
  if (urlEl && window.location && window.location.origin) { urlEl.textContent = window.location.origin + "/v1"; }
}

function bindPowerUX() {
  voiceLoopEnabled = safeStorageGet("realm_voice_loop") === "1";
  const vlToggle = document.getElementById("voice-loop-toggle"), vlBadge = document.getElementById("voice-loop-badge");
  if (vlToggle) {
    vlToggle.checked = voiceLoopEnabled;
    if (vlBadge) { vlBadge.textContent = voiceLoopEnabled ? "ON" : "OFF"; }
    vlToggle.addEventListener("change", () => setVoiceLoopEnabled(vlToggle.checked));
  }
  const brModal = document.getElementById("briefing-modal"), brClose = document.getElementById("close-briefing-modal"), brGen = document.getElementById("br-generate-btn");
  if (brClose) { brClose.addEventListener("click", () => brModal && brModal.close()); }
  if (brModal) {
    brModal.addEventListener("close", function () {
      const player = document.getElementById("br-audio-player");
      if (player) { player.pause(); player.removeAttribute("src"); player.load(); }
      if (briefingAudioUrl) { URL.revokeObjectURL(briefingAudioUrl); briefingAudioUrl = null; }
    });
  }
  if (brGen) { brGen.addEventListener("click", generateAudioBriefingUI); }
  document.querySelectorAll("[data-br-mode]").forEach(btn => btn.addEventListener("click", () => { briefingMode = btn.getAttribute("data-br-mode") || "solo"; syncBriefingModeUI(); }));
  const dlWav = document.getElementById("br-download-wav"), dlMd = document.getElementById("br-download-md");
  if (dlWav) { dlWav.addEventListener("click", () => { if (!briefingAudioUrl) { return; } const a = document.createElement("a"); a.href = briefingAudioUrl; a.download = "realm-briefing.wav"; a.click(); }); }
  if (dlMd) { dlMd.addEventListener("click", () => { if (briefingLastTranscript && typeof downloadBlobText === "function") { downloadBlobText("# REALM Audio Briefing\n\n" + briefingLastTranscript + "\n", "realm-briefing.md", "text/markdown;charset=utf-8"); } }); }
  const clipBtn = document.getElementById("clip-url-btn");
  if (clipBtn) { clipBtn.addEventListener("click", clipUrlToLibrary); }
  const apiToggle = document.getElementById("local-api-toggle");
  if (apiToggle) {
    apiToggle.addEventListener("change", () => {
      const on = Boolean(apiToggle.checked);
      if (typeof workspaceConfig === "object" && workspaceConfig) { workspaceConfig.enable_local_api = on; }
      syncLocalApiUI(workspaceConfig);
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ enable_local_api: on }); }
    });
  }
  syncLocalApiUI(workspaceConfig);
}
"""
