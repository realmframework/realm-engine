"""Client-side multi-turn chat session, turn stream rendering, RAG Studio, and Phonon TTS helpers."""

CHAT_SCRIPT: str = r"""
let currentChatId = null, currentTurns = [], savedChats = [], ragConfig = { retrieval_mode: "hybrid", top_k: 5, rrf_k: 60, temperature: 0.2 }, activeSpeechTurn = null, activeAudio = null, activeAudioUrl = null, ttsCatalog = [], phononAvailable = true, speechOp = 0, recentChatsOp = 0, openChatOp = 0;
const SPEAKER_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M11 5L6 9H2v6h4l5 4V5Zm4.5 3.5a5 5 0 0 1 0 7m2.5-9.5a9 9 0 0 1 0 12'/></svg>";
const STOP_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='currentColor' viewBox='0 0 24 24'><rect x='6' y='6' width='12' height='12' rx='2'/></svg>";
const COPY_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><rect x='9' y='9' width='11' height='11' rx='2'/><path stroke-linecap='round' d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/></svg>";
const CHECK_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.75' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='m5 13 4 4L19 7'/></svg>";
const MORE_SVG = "<svg aria-hidden='true' class='w-4 h-4 shrink-0' fill='currentColor' viewBox='0 0 24 24'><circle cx='5' cy='12' r='1.6'/><circle cx='12' cy='12' r='1.6'/><circle cx='19' cy='12' r='1.6'/></svg>";
const SOURCES_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M4 6.5A2.5 2.5 0 0 1 6.5 4H19v14.5H6.5A2.5 2.5 0 0 0 4 21V6.5Zm0 12A2.5 2.5 0 0 1 6.5 16H19'/></svg>";
const VOICE_LABELS = { Zoey: "Zoey (US Female)", Easton: "Easton (US Male)", Freya: "Freya (UK Female)", Hugh: "Hugh (UK Male)", Hadley: "Hadley (US Female)", Anton: "Anton (DE Male)", Henrik: "Henrik (DE Male)", Lotte: "Lotte (DE Female)", Maja: "Maja (DE Female)", Emil: "Emil (DE Male)", Greta: "Greta (DE Female)", alloy: "Alloy (OpenAI)", nova: "Nova (OpenAI)", echo: "Echo (OpenAI)" };
const EXCLUDED_RPG_RE = /grub the ogre|vyrmathrax|thing under the stairs|fairy godmother|snow queen|fennick|captain silas|sir bramwell|master aldric|morwenna|old mortlake/i;
function getTtsApiKey(mVal) { const kEl = document.getElementById("tts-api-key"), direct = kEl ? kEl.value.trim() : ""; return direct || (mVal.startsWith("openai") ? getApiKey() : ""); }
function isVoiceEnabled() { const mSel = document.getElementById("tts-model"), mVal = (mSel && mSel.value) || "phonon:latest", prov = mVal.startsWith("elevenlabs") ? "elevenlabs" : "openai"; return (!localOnly() || !cloudSpeech(mVal)) && mVal !== "disabled" && ((mVal.startsWith("openai") || mVal.startsWith("elevenlabs")) ? Boolean(getTtsApiKey(mVal) || hasSavedKey(prov)) : phononAvailable); }
function formatTtsModelLabel(m) { return m === "openai:tts-1" ? "OpenAI TTS (tts-1 — Alloy / Nova / Echo)" : (m === "elevenlabs:tts" ? "ElevenLabs TTS" : (m === "disabled" ? "Disabled (Hide Voice Controls)" : (m.includes("-de") ? m + " (Local Phonon DE)" : m + " (Local Phonon)"))); }
function newChatId() { return "chat-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7); }
function formatRagLabel(turn) { const mode = (turn && turn.retrieval_mode) || ragConfig.retrieval_mode || "hybrid", topK = (turn && turn.top_k) || ragConfig.top_k || 5, temp = Number(turn && turn.temperature !== undefined ? turn.temperature : ragConfig.temperature).toFixed(1); return "mode: " + mode + " · top-k: " + topK + " · temp: " + temp; }
function syncProviderPrivacyUI(prov, noticeId, groupId) {
  const notice = document.getElementById(noticeId), group = document.getElementById(groupId); if (!notice || !group) { return; }
  if (prov === "ollama") { group.classList.add("hidden"); group.classList.remove("flex"); notice.textContent = t("local_exec_notice"); notice.className = "text-xs text-[#738196]"; return; }
  group.classList.remove("hidden"); group.classList.add("flex"); const region = (prov === "kimi" || prov === "deepseek") ? t("region_asia") : (prov === "mistral" ? t("region_eu") : t("region_us"));
  notice.textContent = t("cloud_privacy_notice", { region: region }); notice.className = "text-xs text-amber-300";
}
function syncSliderCss(slider, valText) { if (!slider) { return; } slider.style.setProperty("--attr-min", slider.min || 0); slider.style.setProperty("--attr-max", slider.max || 100); slider.style.setProperty("--control-value", slider.value); if (valText) { slider.setAttribute("aria-valuetext", valText); } }
function syncRagStudioUI() {
  const topKEl = document.getElementById("rag-top-k"), rrfKEl = document.getElementById("rag-rrf-k"), tempEl = document.getElementById("rag-temperature");
  if (topKEl) { topKEl.value = String(ragConfig.top_k); const txt = t("rag_top_k_val", { n: ragConfig.top_k }); document.getElementById("rag-top-k-badge").textContent = txt; syncSliderCss(topKEl, txt); }
  if (rrfKEl) { rrfKEl.value = String(ragConfig.rrf_k); const txt = "k = " + ragConfig.rrf_k; document.getElementById("rag-rrf-k-badge").textContent = txt; syncSliderCss(rrfKEl, txt); }
  if (tempEl) { tempEl.value = String(ragConfig.temperature); const txt = Number(ragConfig.temperature).toFixed(1); document.getElementById("rag-temperature-badge").textContent = txt; syncSliderCss(tempEl, txt); }
  document.querySelectorAll("[data-retrieval-mode]").forEach(function (btn) {
    const active = btn.getAttribute("data-retrieval-mode") === ragConfig.retrieval_mode; btn.setAttribute("aria-pressed", String(active));
    btn.className = active ? "rag-mode-btn py-2 px-2 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]" : "rag-mode-btn py-2 px-2 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]";
  });
  const pillEl = document.getElementById("chunks-rag-pill"); if (pillEl) { pillEl.textContent = formatRagLabel(null); }
}
function syncTtsVoices() {
  const mSel = document.getElementById("tts-model"), vSel = document.getElementById("tts-voice"), kGrp = document.getElementById("tts-api-key-group"); if (!mSel || !vSel) { return; }
  const isCloud = mSel.value.startsWith("openai") || mSel.value.startsWith("elevenlabs");
  if (kGrp) { kGrp.classList.toggle("hidden", !isCloud); kGrp.classList.toggle("flex", isCloud); }
  const entry = ttsCatalog.find(function (item) { return item.model === mSel.value; }) || ttsCatalog[0] || { voices: ["default", "Zoey (US Female)", "Easton (US Male)", "Freya (UK Female)", "Hugh (UK Male)", "Hadley (US Female)", "Alfie", "Bryony", "Delia", "Edwin", "Elodie-Rose", "Everly", "Harper", "Imogen", "Juniper", "Lottie", "Maeve", "Micah", "Miles", "Pippa", "Preston", "Russell", "Spencer", "Teddy", "Toby", "Trevor"] };
  const curated = (entry.voices || ["default"]).filter(function (v) { return !EXCLUDED_RPG_RE.test(v); });
  vSel.innerHTML = (curated.length ? curated : ["default"]).map(function (v) { return "<option value='" + escapeHtml(v) + "'>" + escapeHtml(VOICE_LABELS[v] || v) + "</option>"; }).join("");
  if (typeof syncTtsKeyUI === "function") { syncTtsKeyUI(); }
  if (currentTurns.length) { renderChatStream(); }
}
async function loadSystemStatus() {
  try {
    const stRes = await areaFetch("/api/system-status");
    if (!stRes.ok) { return; }
    const st = await safeJson(stRes); showHardwareAdvice(st);
    if (typeof checkEcoRamSuggestion === "function") { checkEcoRamSuggestion(st.ram_gb); }
    const pill = document.getElementById("system-status-pill"), obStatus = document.getElementById("onboarding-status-text"), ragBadge = document.getElementById("rag-engine-status-badge"), isHybrid = st.retrieval_tier === "hybrid_local";
    if (pill) { const label = st.ollama_online ? "Local AI Connected" : "Search Tools Ready"; pill.setAttribute("aria-label", label); pill.setAttribute("title", label); pill.className = "text-xs font-mono " + (st.ollama_online ? "text-[#38D399]" : "text-[#4BB8E8]"); }
    const statusMsg = isHybrid ? t("rag_hybrid_active") : t("rag_keyword_active");
    if (ragBadge) { ragBadge.textContent = statusMsg; ragBadge.className = "text-xs font-mono " + (isHybrid ? "text-[#38D399]" : "text-[#4BB8E8]"); }
    if (obStatus) { obStatus.innerHTML = modeCopy(st.ollama_online ? "Local AI is connected. Choose a model to start chatting." : "Search and privacy tools are ready. Connect AI when you want answers, too.", statusMsg); }
    if (st.is_first_run && !safeStorageGet("onboarded")) { openOnboardingWizard(1); }
    const audRes = await areaFetch("/api/audio/status"), aud = audRes.ok ? await safeJson(audRes) : {}, mSel = document.getElementById("tts-model");
    phononAvailable = aud.phonon_available !== false;
    ttsCatalog = Array.isArray(aud.tts_models) && aud.tts_models.length ? aud.tts_models : [{ model: "phonon:latest", voices: ["default", "Zoey", "Easton", "Freya", "Hugh", "Hadley"] }, { model: "openai:tts-1", voices: ["alloy", "nova", "echo"] }, { model: "elevenlabs:tts", voices: ["Rachel", "Adam", "Josh", "Bella"] }, { model: "disabled", voices: ["none"] }];
    if (mSel) { mSel.innerHTML = ttsCatalog.map(function (item) { return "<option value='" + escapeHtml(item.model) + "'>" + escapeHtml(formatTtsModelLabel(item.model)) + "</option>"; }).join(""); if (appliedRunMode === "search" || !phononAvailable && !getTtsApiKey("openai")) { mSel.value = "disabled"; } applyLocalPolicy(); syncTtsVoices(); }
  } catch (_e) {}
}
async function completeOnboarding(openUploader) {
  if (!await applySelectedMode("onboarding")) { return; }
  safeStorageSet("onboarded", "1");
  const obProv = document.getElementById("onboarding-provider").value, obModel = (document.getElementById("onboarding-model") && document.getElementById("onboarding-model").value) || "", obKey = document.getElementById("onboarding-api-key").value.trim(), obTitle = document.getElementById("onboarding-title").value.trim() || "My Knowledge Base", obFolder = document.getElementById("onboarding-folder").value.trim();
  providerEl.value = obProv; syncProviderPrivacyUI(obProv, "settings-privacy-notice", "settings-api-key-group");
  if (obKey) { await saveAppApiKey(obProv, obKey, document.getElementById("onboarding-api-key")); }
  if (obModel) { selectActiveModel(obModel); }
  await loadModels();
  if (obTitle !== document.getElementById("cfg-app-title").value || obFolder !== document.getElementById("cfg-knowledge-dir").value) { document.getElementById("cfg-app-title").value = obTitle; document.getElementById("cfg-knowledge-dir").value = obFolder; await saveWorkspace(); }
  document.getElementById("onboarding-modal").close(); if (openUploader) { openUploadDialog(); }
}
function stopActiveAudio() { ++speechOp; if (typeof disconnectAmbientAudio === "function") { disconnectAmbientAudio(); } if (activeAudio) { activeAudio.pause(); activeAudio = null; } if (activeAudioUrl) { URL.revokeObjectURL(activeAudioUrl); activeAudioUrl = null; } activeSpeechTurn = null; }
async function previewVoice() {
  stopActiveAudio(); const op = ++speechOp, mSel = document.getElementById("tts-model"), vSel = document.getElementById("tts-voice"), mVal = (mSel && mSel.value) || "phonon:latest"; if (mVal === "disabled" || localOnly() && cloudSpeech(mVal)) { return; }
  try {
    const res = await areaFetch("/api/audio/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: mVal.includes("-de") ? "Sprachausgabe bereit." : "Voice check ready.", model: mVal, voice: (vSel && vSel.value) || "default", api_key: getTtsApiKey(mVal) || null }) });
    if (op !== speechOp || !res.ok) { return; }
    const blob = await res.blob(); if (op !== speechOp) { return; }
    activeAudioUrl = URL.createObjectURL(blob); activeAudio = new Audio(activeAudioUrl); activeAudio.onended = activeAudio.onerror = stopActiveAudio; if (typeof connectAmbientAudio === "function") { connectAmbientAudio(activeAudio); } await activeAudio.play();
  } catch (_e) { if (op === speechOp) { stopActiveAudio(); } }
}
async function toggleSpeakTurn(tIdx) {
  if (!isVoiceEnabled()) { return; }
  const speechVersion = areaVersion;
  if (activeSpeechTurn === tIdx) { stopActiveAudio(); renderChatStream(); return; }
  stopActiveAudio(); const op = ++speechOp, turn = currentTurns[tIdx]; if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  activeSpeechTurn = tIdx; renderChatStream();
  try {
    const mSel = document.getElementById("tts-model"), vSel = document.getElementById("tts-voice"), mVal = (mSel && mSel.value) || "phonon:latest";
    const res = await areaFetch("/api/audio/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: turn.tutor.answer, model: mVal, voice: (vSel && vSel.value) || "default", api_key: getTtsApiKey(mVal) || null }) });
    if (op !== speechOp || speechVersion !== areaVersion) { return; }
    if (!res.ok || activeSpeechTurn !== tIdx) { stopActiveAudio(); renderChatStream(); return; }
    const blob = await res.blob(); if (op !== speechOp || speechVersion !== areaVersion) { return; }
    activeAudioUrl = URL.createObjectURL(blob); activeAudio = new Audio(activeAudioUrl);
    activeAudio.onended = function () { if (op === speechOp && speechVersion === areaVersion) { stopActiveAudio(); renderChatStream(); if (typeof handleVoiceLoopAfterSpeechEnd === "function") { handleVoiceLoopAfterSpeechEnd(); } } };
    activeAudio.onerror = function () { if (op === speechOp && speechVersion === areaVersion) { stopActiveAudio(); renderChatStream(); } };
    if (typeof connectAmbientAudio === "function") { connectAmbientAudio(activeAudio); }
    await activeAudio.play();
  } catch (_e) { if (op === speechOp) { stopActiveAudio(); renderChatStream(); } }
}
async function copyTurnAnswer(tIdx, btn) {
  const turn = currentTurns[tIdx];
  if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  const cited = Array.from(new Set(turn.tutor.cited_titles || []));
  const text = turn.tutor.answer + (cited.length ? ("\n\nSources:\n" + cited.map(function (c, i) { return (i + 1) + ". " + c; }).join("\n")) : "");
  let ok = false;
  try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(text); ok = true; } } catch (_e) {}
  if (!ok) {
    try {
      const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); ok = document.execCommand("copy"); ta.remove();
    } catch (_e) {}
  }
  if (ok && btn) {
    btn.innerHTML = CHECK_SVG;
    btn.setAttribute("aria-label", t("copied_btn")); btn.title = t("copied_btn"); btn.style.color = "var(--status-ok)";
    setTimeout(function () { if (btn.isConnected) { btn.innerHTML = COPY_SVG; btn.setAttribute("aria-label", t("copy_btn")); btn.title = t("copy_btn"); btn.style.color = ""; } }, 1600);
  }
}
async function loadRecentChats() {
  const version = areaVersion, op = ++recentChatsOp, free = Boolean(typeof freeChatMode !== "undefined" && freeChatMode);
  try {
    const res = await areaFetch("/api/chats" + (free ? "?free_chat=true" : ""));
    if (!res.ok) { return; }
    const data = await safeJson(res);
    if (version === areaVersion && op === recentChatsOp && free === Boolean(typeof freeChatMode !== "undefined" && freeChatMode) && Array.isArray(data)) {
      savedChats = data; renderRecentChats();
    }
  } catch (_e) {}
}
function renderRecentChats() {
  const listEl = document.getElementById("recent-chats-list"); if (!listEl) { return; }
  if (!Array.isArray(savedChats) || !savedChats.length) { listEl.innerHTML = "<div class='px-4 py-1.5 text-xs text-[#738196]'>" + escapeHtml(t("no_recent_chats")) + "</div>"; return; }
  listEl.innerHTML = savedChats.map(function (c) {
    const rowCls = c.chat_id === currentChatId ? "group w-full flex items-center justify-between gap-1 px-4 py-2 rounded-lg bg-[#4BB8E8]/15 text-[#4BB8E8] text-sm font-medium transition-colors" : "group w-full flex items-center justify-between gap-1 px-4 py-2 rounded-lg text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/[0.04] transition-colors";
    return "<div class='" + rowCls + "'><button type='button' data-open-chat='" + escapeHtml(c.chat_id) + "' class='flex-1 text-left truncate'>" + escapeHtml(c.title) + "</button><button type='button' data-del-chat='" + escapeHtml(c.chat_id) + "' aria-label='" + escapeHtml(t("aria_del_chat", { title: c.title })) + "' class='opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100 text-xs text-[#738196] hover:text-[#EEF2F8] px-1 transition-opacity'>✕</button></div>";
  }).join("");
  listEl.querySelectorAll("[data-open-chat]").forEach(function (btn) { btn.addEventListener("click", function () { openSavedChat(btn.getAttribute("data-open-chat") || ""); }); });
  listEl.querySelectorAll("[data-del-chat]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.stopPropagation(); deleteSavedChat(btn.getAttribute("data-del-chat") || ""); });
  });
}
async function openSavedChat(chatId) {
  if (!chatId) { return; }
  const version = areaVersion, op = ++openChatOp, free = Boolean(typeof freeChatMode !== "undefined" && freeChatMode);
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  if (typeof resetXrayOverrides === "function") { resetXrayOverrides(); }
  try {
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatId) + (free ? "?free_chat=true" : ""));
    if (!res.ok || op !== openChatOp || version !== areaVersion) { return; }
    const session = await safeJson(res);
    if (op !== openChatOp || version !== areaVersion || !session.chat_id) { return; }
    if (typeof loadAgentTeam === "function" && typeof agentTeam !== "undefined" && !agentTeam.length) {
      await loadAgentTeam();
      if (op !== openChatOp || version !== areaVersion) { return; }
    }
    currentChatId = session.chat_id; adoptChatScope(session);
    activeAttachedNotes = (session.attached_notes || []).map(function (n) { return { name: n.name || "Note", chars: (n.content || "").length }; });
    if (typeof renderAttachedChips === "function") { renderAttachedChips(); }
    currentTurns = (session.turns || []).map(function (t) { return Object.assign({}, t, { collapsed: Boolean(t.ask_tutor) }); });
    if (typeof adoptChatAgent === "function") { adoptChatAgent(session); }
    setActiveTag(null); setViewMode(true); renderTutor(null); renderResults([], false); renderChatStream(); renderRecentChats();
    if (typeof refreshContextUsage === "function") { refreshContextUsage(); }
  } catch (_e) {}
}
function renderTurnTutorHtml(turn, tIdx) {
  const authorHex = typeof turnAuthorColor === "function" ? turnAuthorColor(turn) : "";
  const turnStyle = authorHex ? " style='--turn-seed:" + escapeHtml(authorHex) + "'" : "";
  if (turn.loadingTutor) {
    const activeModel = modelEl.value.trim() || PROVIDER_DEFAULTS[providerEl.value] || "qwen3:8b";
    const stopPill = "<button type='button' data-stop-query class='ml-auto inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0B1020] border border-[rgba(238,242,248,0.14)] hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + STOP_SVG + "<span>" + escapeHtml(t("stop_btn")) + "</span></button>";
    if (turn.streamingText) {
      const shownLen = typeof turn.displayedChars === "number" && turn.displayedChars > 0 ? Math.min(turn.displayedChars, turn.streamingText.length) : turn.streamingText.length;
      const visibleMd = turn.streamingText.slice(0, shownLen);
      return "<section aria-busy='true' class='turn-themed w-full flex flex-col gap-3'" + turnStyle + "><div class='turn-author-heading flex items-center gap-2.5 text-lg font-medium select-none'>" + SPARKLE_SVG + "<span>" + escapeHtml(turn.format_name || turnAuthorName(turn)) + "</span>" + stopPill + "</div><div id='turn-" + tIdx + "-stream-body' class='md-body is-streaming text-[#EEF2F8] text-base leading-relaxed flex flex-col gap-3 font-normal'>" + formatMarkdown(visibleMd, true, 3) + "</div></section>";
    }
    const loadCopyHtml = turn.streamingThinking ? escapeHtml(t("chat_thinking")) : modeCopy(t("chat_preparing"), "Synthesizing answer with " + activeModel + "...");
    return "<section aria-busy='true' class='turn-themed w-full flex flex-col gap-3'" + turnStyle + "><div class='flex items-center gap-2.5'><img src='" + escapeHtml(activeLogoSrc()) + "' width='20' height='20' class='w-5 h-5 rounded object-cover animate-pulse' alt=''/><span class='turn-author-heading animate-spin inline-flex'>" + SPARKLE_SVG + "</span><span class='text-[#A0B0C8] text-sm font-medium'>" + loadCopyHtml + "</span>" + stopPill + "</div><div class='flex flex-col gap-2.5 pt-1'><div class='realm-skeleton animate-pulse rounded-lg h-4 w-full'></div><div class='realm-skeleton animate-pulse rounded-lg h-4 w-11/12'></div><div class='realm-skeleton animate-pulse rounded-lg h-4 w-4/5'></div></div></section>";
  }
  if (turn.stopped && !turn.tutor) {
    return "<div class='inline-flex items-center gap-2 text-xs text-[#738196] py-1'>" + STOP_SVG + "<span>" + escapeHtml(t("stopped_msg")) + "</span></div>";
  }
  const tutor = turn.tutor; if (!tutor) { return ""; }
  const speaking = activeSpeechTurn === tIdx, srcCount = (turn.results || []).length, isCollapsed = turn.collapsed !== false;
  const isErr = Boolean(turn.isError || /^Cloud Budget Guardrail|^AI provider /i.test(String(tutor.answer || "")));
  const isGap = !isErr && Boolean(tutor.knowledge_gap_detected) && srcCount === 0 && !freeChatMode;
  const copyBtn = "<button type='button' data-copy-turn='" + tIdx + "' class='turn-icon-btn' title='" + escapeHtml(t("copy_btn")) + "' aria-label='" + escapeHtml(t("copy_btn")) + "'>" + COPY_SVG + "</button>";
  const speakLbl = speaking ? t("stop_btn") : t("chat_listen");
  const speakBtn = isVoiceEnabled() ? "<button type='button' data-speak-turn='" + tIdx + "' aria-pressed='" + String(speaking) + "' class='turn-icon-btn' title='" + escapeHtml(speakLbl) + "' aria-label='" + escapeHtml(speakLbl) + "'>" + (speaking ? STOP_SVG : SPEAKER_SVG) + "</button>" : "";
  const exportMenu = typeof exportMenuHtml === "function" ? exportMenuHtml("turn", tIdx, false, true) : "";
  const moreItems = "<button type='button' data-review-turn='" + tIdx + "' class='turn-popover-item'>" + escapeHtml(t("chat_cross_examine")) + "…</button>"
    + "<button type='button' data-format-turn='" + tIdx + "' class='turn-popover-item'>" + escapeHtml(t("chat_format_btn")) + "</button>"
    + (knowledgeAreas.length ? "<button type='button' data-save-turn='" + tIdx + "' class='turn-popover-item'>" + escapeHtml(t("chat_save_guide")) + "</button>" : "")
    + (currentChatId ? "<button type='button' data-fork-turn='" + tIdx + "' class='turn-popover-item'>" + escapeHtml(t("chat_fork")) + "</button>" : "");
  const moreMenu = "<details class='turn-more-menu relative inline-block'><summary class='turn-icon-btn list-none' title='" + escapeHtml(t("chat_more_actions")) + "' aria-label='" + escapeHtml(t("chat_more_actions")) + "'>" + MORE_SVG + "</summary><div class='turn-popover-panel'>" + moreItems + "</div></details>";
  const sourcesChip = srcCount > 0 ? "<button type='button' data-turn-toggle='" + tIdx + "' aria-expanded='" + String(!isCollapsed) + "' class='turn-sources-chip'>" + SOURCES_SVG + "<span>" + escapeHtml(t("chat_sources_btn", { n: srcCount })) + "</span><span aria-hidden='true'>" + (isCollapsed ? "⌄" : "⌃") + "</span></button>" : "";
  const fmtPill = turn.format_name ? "<span class='px-2.5 py-0.5 rounded-full bg-[#4BB8E8]/15 text-[#4BB8E8] border border-[#4BB8E8]/35 text-xs font-mono'>" + escapeHtml(turn.format_name) + "</span>" : "";
  const pinnedModelTag = (turn.telemetry && turn.telemetry.pinned_agent_model && turn.telemetry.model) ? "<span class='text-xs font-mono text-[#738196] font-normal'>· " + escapeHtml(turn.telemetry.model) + "</span>" : "";
  const errPill = "<span role='status' class='px-2.5 py-0.5 rounded-full text-xs font-medium' style='background:color-mix(in oklab,var(--status-danger) 12%,transparent);color:var(--status-danger);border:1px solid color-mix(in oklab,var(--status-danger) 35%,transparent)'>" + escapeHtml(t("chat_err_badge")) + "</span>";
  const badge = turn.stopped ? "<span class='px-2.5 py-0.5 rounded-full bg-white/10 text-[#A0B0C8] text-xs font-medium'>" + escapeHtml(t("stopped_msg")) + "</span>" : (isErr ? errPill : (isGap ? "<span class='px-2.5 py-0.5 rounded-full bg-amber-400/10 text-amber-300 shadow-[inset_0_0_0_1px_rgba(252,211,77,0.25)] text-xs font-medium'>" + modeCopy(t("chat_no_source"), t("chat_gap_spec")) + "</span>" : (freeChatMode ? "<span class='px-2.5 py-0.5 rounded-full bg-white/5 text-[#A0B0C8] text-xs'>" + escapeHtml(t("free_chat_short")) + "</span>" : "<span data-specialist-only class='px-2.5 py-0.5 rounded-full bg-[#4BB8E8]/10 text-[#4BB8E8] shadow-[inset_0_0_0_1px_rgba(75,184,232,0.25)] text-xs font-medium'>" + escapeHtml(t("chat_grounded")) + "</span>")));
  const footerBar = "<div role='toolbar' class='turn-action-row' aria-label='Response actions'>" + copyBtn + speakBtn + exportMenu + moreMenu + sourcesChip + "</div>";
  const topics = (tutor.recommended_topics || []).map(function (topic) { return "<button type='button' data-topic='" + escapeHtml(topic) + "' class='flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] text-xs font-medium transition-colors'>" + SPARKLE_SVG + "<span>" + escapeHtml(topic) + "</span></button>"; }).join("");
  return "<section class='turn-themed w-full flex flex-col'" + turnStyle + "><div class='flex items-center justify-between gap-2 mb-3 flex-wrap'><div class='turn-author-heading flex items-center gap-2 text-lg font-medium select-none flex-wrap'>" + SPARKLE_SVG + "<span>" + escapeHtml(turnAuthorName(turn)) + "</span>" + pinnedModelTag + fmtPill + "</div>" + badge + "</div><div class='md-body text-[#EEF2F8] text-base leading-relaxed flex flex-col gap-3 font-normal'>" + formatMarkdown(tutor.answer, true, 3) + "</div>" + footerBar + (topics ? "<div class='flex flex-wrap items-center gap-2 mt-3'>" + topics + "</div>" : "") + "</section>";
}
function renderChatStream() {
  const streamEl = document.getElementById("chat-stream"); if (!streamEl) { return; }
  streamEl.innerHTML = chatActionsHeader() + currentTurns.map(function (turn, tIdx) {
    const resList = turn.results || [], count = resList.length, isCollapsed = turn.ask_tutor && turn.collapsed !== false;
    const rLabel = turn.router_label || ((turn.top_k || 5) >= 7 ? "Auto-Router: Deep Synthesis" : "Auto-Router: Exact Lookup");
    const ragBadge = "<div data-specialist-only class='flex items-center gap-1.5 flex-wrap'><span class='px-2.5 py-0.5 rounded-full bg-[#4BB8E8]/10 border border-[#4BB8E8]/25 text-xs font-mono text-[#4BB8E8]'>" + escapeHtml(rLabel) + "</span><span class='px-2.5 py-0.5 rounded-full bg-[#0B1020] border border-[rgba(238,242,248,0.10)] text-xs font-mono text-[#738196]'>" + escapeHtml(formatRagLabel(turn)) + "</span></div>";
    const cited = (turn.tutor && turn.tutor.cited_titles) || [], uniqueCited = cited.filter(function (x, i) { return cited.indexOf(x) === i; });
    const citeStrip = uniqueCited.length ? "<div class='flex flex-wrap gap-1.5 pb-1'>" + uniqueCited.map(function (title, i) {
      const parts = String(title).split(/\s+—\s+|\s+-\s+/), label = parts.length > 1 ? parts[0] + " · " + parts.slice(1).join(" · ") : title;
      return "<button type='button' data-turn-cite='" + tIdx + "' data-cite-idx='" + i + "' data-cite-title='" + escapeHtml(title) + "' class='inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0B1020] border border-white/10 hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'><span class='font-mono text-[#4BB8E8]'>[" + (i + 1) + "]</span><span class='truncate max-w-[16rem]'>" + escapeHtml(label) + "</span></button>";
    }).join("") + "</div>" : "";
    const rawHeader = (!turn.ask_tutor && count > 0) ? "<div class='flex items-center justify-between gap-2 flex-wrap'><span class='text-sm text-[#A0B0C8]'>" + escapeHtml(t("chat_passages_n", { n: count })) + "</span>" + ragBadge + "</div>" : "";
    const cardsHtml = resList.map(function (item, idx) {
      const tagLabel = (item.chunk.tags || []).map(escapeHtml).join(" · ");
      const isWeb = Boolean(item.chunk.url && /^https?:\/\//i.test(item.chunk.url));
      const titleLink = isWeb ? "<a href='" + escapeHtml(item.chunk.url) + "' target='_blank' rel='noopener noreferrer' class='hover:underline focus-visible:outline'>" + escapeHtml(item.chunk.title) + "</a>" : "<a href='#reader-heading' data-reader-turn='" + tIdx + "' data-reader-chunk='" + idx + "' class='hover:underline focus-visible:outline'>" + escapeHtml(item.chunk.title) + "</a>";
      const footerLink = isWeb ? "<a href='" + escapeHtml(item.chunk.url) + "' target='_blank' rel='noopener noreferrer' class='text-xs text-[#4BB8E8] hover:underline self-start focus-visible:outline'>" + escapeHtml(t("chat_open_web")) + "</a>" : "<a href='#reader-heading' data-reader-turn='" + tIdx + "' data-reader-chunk='" + idx + "' class='text-xs text-[#A0B0C8] hover:text-[#EEF2F8] self-start focus-visible:outline'>" + escapeHtml(t("chat_open_reader")) + "</a>";
      const badgeChip = isWeb ? "<span class='px-1.5 py-0.5 rounded bg-amber-400/15 text-amber-300 font-mono text-xs font-semibold shrink-0'>WEB</span>" : "<span class='px-1.5 py-0.5 rounded bg-[#4BB8E8]/15 text-[#4BB8E8] font-mono text-xs font-semibold shrink-0'>[" + (idx + 1) + "]</span>";
      return "<article id='turn-" + tIdx + "-chunk-" + idx + "' data-chunk-title='" + escapeHtml(item.chunk.title || "") + "' tabindex='-1' class='group w-full p-5 rounded-xl bg-[#0B1020] shadow-[inset_0_0_0_1px_rgba(238,242,248,0.08)] hover:shadow-[inset_0_0_0_1px_rgba(238,242,248,0.16)] transition-all duration-300 flex flex-col gap-3 outline-none'><div class='flex items-baseline justify-between gap-3'><div class='flex items-center gap-2.5 min-w-0'>" + badgeChip + "<h2 class='text-base font-medium text-[#EEF2F8] truncate'>" + titleLink + "</h2></div><span data-specialist-only class='text-[#738196] font-mono text-xs shrink-0'>score: " + Number(item.score).toFixed(2) + "</span></div>" + (tagLabel ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide'>// " + tagLabel + "</div>" : "") + "<div class='md-prose text-[#C8D4E6] text-base leading-relaxed flex flex-col gap-2.5'>" + formatMarkdown(item.chunk.content) + "</div>" + footerLink + "</article>";
    }).join("");
    const drawerContent = (turn.ask_tutor ? (ragBadge + citeStrip) : "") + cardsHtml;
    return "<article id='turn-" + tIdx + "' tabindex='-1' class='flex flex-col gap-5 w-full outline-none border-b border-[rgba(238,242,248,0.06)] pb-8 last:border-b-0'><div class='chat-user-msg self-end max-w-[85%] rounded-2xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] px-5 py-3 text-[#EEF2F8] text-base leading-relaxed'>" + escapeHtml(turn.query) + "</div>" + (turn.ask_tutor ? renderTurnTutorHtml(turn, tIdx) : "") + rawHeader + (count > 0 ? "<div id='turn-" + tIdx + "-results' class='" + (isCollapsed ? "hidden " : "flex ") + "flex-col gap-3 pt-1'>" + drawerContent + "</div>" : "") + "</article>";
  }).join("");
  bindChatActions(streamEl); bindMarkdownLinks(streamEl, "", selectedTag);
  if (typeof highlightSearchTerms === "function") {
    currentTurns.forEach(function (turn, tIdx) {
      const box = document.getElementById("turn-" + tIdx + "-results");
      if (box && turn.query) { highlightSearchTerms(box, turn.query); }
    });
  }
  if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
  const closeMore = function (btn) { const d = btn.closest("details"); if (d) { d.open = false; } };
  streamEl.querySelectorAll("[data-stop-query]").forEach(function (btn) { btn.addEventListener("click", function () { stopActiveRequest(); }); });
  streamEl.querySelectorAll("[data-copy-turn]").forEach(function (btn) { btn.addEventListener("click", function () { copyTurnAnswer(Number(btn.getAttribute("data-copy-turn") || 0), btn); }); });
  streamEl.querySelectorAll("[data-format-turn]").forEach(function (btn) { btn.addEventListener("click", function () { closeMore(btn); if (typeof openFormatStudio === "function") { openFormatStudio("browse"); } }); });
  streamEl.querySelectorAll("[data-review-turn]").forEach(function (btn) { btn.addEventListener("click", function () { closeMore(btn); if (typeof openCrossExamineModal === "function") { openCrossExamineModal(Number(btn.getAttribute("data-review-turn") || 0)); } }); });
  streamEl.querySelectorAll("[data-fork-turn]").forEach(function (btn) { btn.addEventListener("click", function () { closeMore(btn); if (typeof forkChatAtTurn === "function") { forkChatAtTurn(Number(btn.getAttribute("data-fork-turn") || 0)); } }); });
  streamEl.querySelectorAll("[data-save-turn]").forEach(function (btn) { btn.addEventListener("click", function () { closeMore(btn); saveTurnToLibrary(Number(btn.getAttribute("data-save-turn") || 0)); }); });
  streamEl.querySelectorAll("[data-topic]").forEach(function (btn) { btn.addEventListener("click", function () { queryEl.value = btn.dataset.topic || ""; submitQuery(); }); });
  streamEl.querySelectorAll("[data-speak-turn]").forEach(function (btn) { btn.addEventListener("click", function () { toggleSpeakTurn(Number(btn.getAttribute("data-speak-turn") || 0)); }); });
  streamEl.querySelectorAll("[data-turn-toggle]").forEach(function (btn) { btn.addEventListener("click", function () { const idx = Number(btn.getAttribute("data-turn-toggle") || 0); if (currentTurns[idx]) { currentTurns[idx].collapsed = !currentTurns[idx].collapsed; renderChatStream(); } }); });
  streamEl.querySelectorAll("[data-turn-cite]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const scrollId = ++currentScrollId, tIdx = Number(btn.getAttribute("data-turn-cite") || 0), cIdx = Number(btn.getAttribute("data-cite-idx") || 0), citeTitle = btn.getAttribute("data-cite-title") || "";
      if (currentTurns[tIdx] && currentTurns[tIdx].collapsed !== false) { currentTurns[tIdx].collapsed = false; renderChatStream(); }
      const container = document.getElementById("turn-" + tIdx + "-results"), target = (container && Array.from(container.children).find(function (el) { return el.getAttribute("data-chunk-title") === citeTitle; })) || document.getElementById("turn-" + tIdx + "-chunk-" + cIdx) || document.getElementById("turn-" + tIdx + "-chunk-0");
      if (target) { await scrollIntoViewAsync(target, { behavior: "smooth", block: "center" }); if (scrollId !== currentScrollId) { return; } target.focus({ preventScroll: true }); target.classList.add("ring-2", "ring-[#4BB8E8]"); setTimeout(function () { target.classList.remove("ring-2", "ring-[#4BB8E8]"); }, 1600); }
    });
  });
}
"""
