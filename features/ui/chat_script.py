"""Client-side multi-turn chat session, turn stream rendering, RAG Studio, and Phonon TTS helpers."""

CHAT_SCRIPT: str = r"""
let currentChatId = null, currentTurns = [], savedChats = [], ragConfig = { retrieval_mode: "hybrid", top_k: 5, rrf_k: 60, temperature: 0.2 }, activeSpeechTurn = null, activeAudio = null, activeAudioUrl = null, ttsCatalog = [], phononAvailable = true;
const SPEAKER_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M11 5L6 9H2v6h4l5 4V5Zm4.5 3.5a5 5 0 0 1 0 7m2.5-9.5a9 9 0 0 1 0 12'/></svg>";
const STOP_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0' fill='currentColor' viewBox='0 0 24 24'><rect x='6' y='6' width='12' height='12' rx='2'/></svg>";
const VOICE_LABELS = { Zoey: "Zoey (US Female)", Easton: "Easton (US Male)", Freya: "Freya (UK Female)", Hugh: "Hugh (UK Male)", Hadley: "Hadley (US Female)", Anton: "Anton (DE Male)", Henrik: "Henrik (DE Male)", Lotte: "Lotte (DE Female)", Maja: "Maja (DE Female)", Emil: "Emil (DE Male)", Greta: "Greta (DE Female)", alloy: "Alloy (OpenAI)", nova: "Nova (OpenAI)", echo: "Echo (OpenAI)" };
const EXCLUDED_RPG_RE = /grub the ogre|vyrmathrax|thing under the stairs|fairy godmother|snow queen|fennick|captain silas|sir bramwell|master aldric|morwenna|old mortlake/i;
function getTtsApiKey(mVal) { const kEl = document.getElementById("tts-api-key"), direct = kEl ? kEl.value.trim() : ""; return direct || (mVal.startsWith("openai") ? getApiKey() : ""); }
function isVoiceEnabled() { const mSel = document.getElementById("tts-model"), mVal = (mSel && mSel.value) || "phonon:latest", prov = mVal.startsWith("elevenlabs") ? "elevenlabs" : "openai"; return (!localOnly() || !cloudSpeech(mVal)) && mVal !== "disabled" && ((mVal.startsWith("openai") || mVal.startsWith("elevenlabs")) ? Boolean(getTtsApiKey(mVal) || hasSavedKey(prov)) : phononAvailable); }
function formatTtsModelLabel(m) { return m === "openai:tts-1" ? "OpenAI TTS (tts-1 — Alloy / Nova / Echo)" : (m === "elevenlabs:tts" ? "ElevenLabs TTS" : (m === "disabled" ? "Disabled (Hide Voice Controls)" : (m.includes("-de") ? m + " (Local Phonon DE)" : m + " (Local Phonon)"))); }
function newChatId() { return "chat-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7); }
function formatRagLabel(turn) { const mode = (turn && turn.retrieval_mode) || ragConfig.retrieval_mode || "hybrid", topK = (turn && turn.top_k) || ragConfig.top_k || 5, temp = Number(turn && turn.temperature !== undefined ? turn.temperature : ragConfig.temperature).toFixed(1); return "mode: " + mode + " · top-k: " + topK + " · temp: " + temp; }
function syncProviderPrivacyUI(prov, noticeId, groupId) {
  const notice = document.getElementById(noticeId), group = document.getElementById(groupId); if (!notice || !group) { return; }
  if (prov === "ollama") { group.classList.add("hidden"); group.classList.remove("flex"); notice.textContent = "Local execution — data stays on this device"; notice.className = "text-xs text-[#738196]"; return; }
  group.classList.remove("hidden"); group.classList.add("flex"); const region = (prov === "kimi" || prov === "deepseek") ? "cloud servers in China/Asia" : (prov === "mistral" ? "EU cloud servers" : "US cloud servers");
  notice.textContent = "Cloud Privacy Notice: Selected passages will be sent to " + region + " to prepare your answer."; notice.className = "text-xs text-amber-300";
}
function syncSliderCss(slider, valText) { if (!slider) { return; } slider.style.setProperty("--attr-min", slider.min || 0); slider.style.setProperty("--attr-max", slider.max || 100); slider.style.setProperty("--control-value", slider.value); if (valText) { slider.setAttribute("aria-valuetext", valText); } }
function syncRagStudioUI() {
  const topKEl = document.getElementById("rag-top-k"), rrfKEl = document.getElementById("rag-rrf-k"), tempEl = document.getElementById("rag-temperature");
  if (topKEl) { topKEl.value = String(ragConfig.top_k); const txt = "Top " + ragConfig.top_k + " chunks"; document.getElementById("rag-top-k-badge").textContent = txt; syncSliderCss(topKEl, txt); }
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
  if (currentTurns.length) { renderChatStream(); }
}
async function loadSystemStatus() {
  try {
    const st = await (await areaFetch("/api/system-status")).json(); showHardwareAdvice(st);
    const pill = document.getElementById("system-status-pill"), obStatus = document.getElementById("onboarding-status-text"), ragBadge = document.getElementById("rag-engine-status-badge"), isHybrid = st.retrieval_tier === "hybrid_local";
    if (pill) { const label = st.ollama_online ? "Local AI Connected" : "Search Tools Ready"; pill.setAttribute("aria-label", label); pill.setAttribute("title", label); pill.className = "text-xs font-mono " + (st.ollama_online ? "text-[#38D399]" : "text-[#4BB8E8]"); }
    const statusMsg = isHybrid ? "● Hybrid Vector + Keyword Search Active (nomic-embed-text)" : "● Fast Keyword Search Mode (No Embedding Model Needed)";
    if (ragBadge) { ragBadge.textContent = statusMsg; ragBadge.className = "text-xs font-mono " + (isHybrid ? "text-[#38D399]" : "text-[#4BB8E8]"); }
    if (obStatus) { obStatus.innerHTML = modeCopy(st.ollama_online ? "Local AI is connected. Choose a model to start chatting." : "Search and privacy tools are ready. Connect AI when you want answers, too.", statusMsg); }
    if (st.is_first_run && !localStorage.getItem("onboarded")) { document.getElementById("onboarding-modal").showModal(); }
    const aud = await (await areaFetch("/api/audio/status")).json(), mSel = document.getElementById("tts-model");
    phononAvailable = aud.phonon_available !== false;
    ttsCatalog = Array.isArray(aud.tts_models) && aud.tts_models.length ? aud.tts_models : [{ model: "phonon:latest", voices: ["default", "Zoey", "Easton", "Freya", "Hugh", "Hadley"] }, { model: "openai:tts-1", voices: ["alloy", "nova", "echo"] }, { model: "elevenlabs:tts", voices: ["Rachel", "Adam", "Josh", "Bella"] }, { model: "disabled", voices: ["none"] }];
    if (mSel) { mSel.innerHTML = ttsCatalog.map(function (item) { return "<option value='" + escapeHtml(item.model) + "'>" + escapeHtml(formatTtsModelLabel(item.model)) + "</option>"; }).join(""); if (appliedRunMode === "search" || !phononAvailable && !getTtsApiKey("openai")) { mSel.value = "disabled"; } applyLocalPolicy(); syncTtsVoices(); }
  } catch (_e) {}
}
async function completeOnboarding(openUploader) {
  if (!await applySelectedMode("onboarding")) { return; }
  localStorage.setItem("onboarded", "1");
  const obProv = document.getElementById("onboarding-provider").value, obKey = document.getElementById("onboarding-api-key").value.trim(), obTitle = document.getElementById("onboarding-title").value.trim() || "AI Engineering", obFolder = document.getElementById("onboarding-folder").value.trim() || "knowledge_base";
  providerEl.value = obProv; syncProviderPrivacyUI(obProv, "settings-privacy-notice", "settings-api-key-group");
  if (obKey) { await saveAppApiKey(obProv, obKey, document.getElementById("onboarding-api-key")); }
  await loadModels();
  if (obTitle !== document.getElementById("cfg-app-title").value || obFolder !== document.getElementById("cfg-knowledge-dir").value) { document.getElementById("cfg-app-title").value = obTitle; document.getElementById("cfg-knowledge-dir").value = obFolder; await saveWorkspace(); }
  document.getElementById("onboarding-modal").close(); if (openUploader) { document.getElementById("upload-modal").showModal(); }
}
function stopActiveAudio() { if (activeAudio) { activeAudio.pause(); activeAudio = null; } if (activeAudioUrl) { URL.revokeObjectURL(activeAudioUrl); activeAudioUrl = null; } activeSpeechTurn = null; }
async function previewVoice() {
  stopActiveAudio(); const mSel = document.getElementById("tts-model"), vSel = document.getElementById("tts-voice"), mVal = (mSel && mSel.value) || "phonon:latest"; if (mVal === "disabled" || localOnly() && cloudSpeech(mVal)) { return; }
  try {
    const res = await areaFetch("/api/audio/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: mVal.includes("-de") ? "Sprachausgabe bereit." : "Voice check ready.", model: mVal, voice: (vSel && vSel.value) || "default", api_key: getTtsApiKey(mVal) || null }) });
    if (res.ok) { activeAudioUrl = URL.createObjectURL(await res.blob()); activeAudio = new Audio(activeAudioUrl); activeAudio.onended = activeAudio.onerror = stopActiveAudio; await activeAudio.play(); }
  } catch (_e) { stopActiveAudio(); }
}
async function toggleSpeakTurn(tIdx) {
  if (!isVoiceEnabled()) { return; }
  const speechVersion = areaVersion;
  if (activeSpeechTurn === tIdx) { stopActiveAudio(); renderChatStream(); return; }
  stopActiveAudio(); const turn = currentTurns[tIdx]; if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  activeSpeechTurn = tIdx; renderChatStream();
  try {
    const mSel = document.getElementById("tts-model"), vSel = document.getElementById("tts-voice"), mVal = (mSel && mSel.value) || "phonon:latest";
    const res = await areaFetch("/api/audio/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: turn.tutor.answer, model: mVal, voice: (vSel && vSel.value) || "default", api_key: getTtsApiKey(mVal) || null }) });
    if (speechVersion !== areaVersion) { return; }
    if (!res.ok || activeSpeechTurn !== tIdx) { stopActiveAudio(); renderChatStream(); return; }
    activeAudioUrl = URL.createObjectURL(await res.blob()); activeAudio = new Audio(activeAudioUrl);
    activeAudio.onended = activeAudio.onerror = function () { if (speechVersion === areaVersion) { stopActiveAudio(); renderChatStream(); } }; await activeAudio.play();
  } catch (_e) { stopActiveAudio(); renderChatStream(); }
}
async function loadRecentChats() { const version = areaVersion, data = await (await areaFetch("/api/chats")).json(); if (version === areaVersion) { savedChats = data; renderRecentChats(); } }
function renderRecentChats() {
  const listEl = document.getElementById("recent-chats-list"); if (!listEl) { return; }
  if (!Array.isArray(savedChats) || !savedChats.length) { listEl.innerHTML = "<div class='px-4 py-1.5 text-xs text-[#738196]'>No recent chats</div>"; return; }
  listEl.innerHTML = savedChats.map(function (c) {
    const rowCls = c.chat_id === currentChatId ? "group w-full flex items-center justify-between gap-1 px-4 py-2 rounded-lg bg-[#4BB8E8]/15 text-[#4BB8E8] text-sm font-medium transition-colors" : "group w-full flex items-center justify-between gap-1 px-4 py-2 rounded-lg text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/[0.04] transition-colors";
    return "<div class='" + rowCls + "'><button type='button' data-open-chat='" + escapeHtml(c.chat_id) + "' class='flex-1 text-left truncate focus:outline-none'>" + escapeHtml(c.title) + "</button><button type='button' data-del-chat='" + escapeHtml(c.chat_id) + "' aria-label='Delete chat " + escapeHtml(c.title) + "' class='opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus:opacity-100 text-xs text-[#738196] hover:text-[#EEF2F8] px-1 transition-opacity'>✕</button></div>";
  }).join("");
  listEl.querySelectorAll("[data-open-chat]").forEach(function (btn) { btn.addEventListener("click", function () { openSavedChat(btn.getAttribute("data-open-chat") || ""); }); });
  listEl.querySelectorAll("[data-del-chat]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.stopPropagation(); deleteSavedChat(btn.getAttribute("data-del-chat") || ""); });
  });
}
async function openSavedChat(chatId) {
  if (!chatId) { return; }
  const version = areaVersion; abortActiveRequest(); const res = await areaFetch("/api/chats/" + encodeURIComponent(chatId)); if (!res.ok) { return; }
  const session = await res.json(); if (version !== areaVersion) { return; } currentChatId = session.chat_id; adoptChatScope(session);
  currentTurns = (session.turns || []).map(function (t) { return Object.assign({}, t, { collapsed: Boolean(t.ask_tutor) }); });
  setActiveTag(null); setViewMode(true); renderTutor(null); renderResults([], false); renderChatStream(); renderRecentChats();
}
function renderTurnTutorHtml(turn, tIdx) {
  if (turn.loadingTutor) {
    const activeModel = modelEl.value.trim() || PROVIDER_DEFAULTS[providerEl.value] || "qwen3:8b";
    return "<section aria-busy='true' class='w-full flex flex-col gap-3'><div class='flex items-center gap-2.5'><img src='/static/logo-192.png' width='20' height='20' class='w-5 h-5 animate-pulse' alt=''/><span class='text-[#4BB8E8] animate-spin inline-flex'>" + SPARKLE_SVG + "</span><span class='text-[#A0B0C8] text-sm font-medium'>" + modeCopy("Preparing your answer…", "Synthesizing answer with " + activeModel + "...") + "</span></div><div class='flex flex-col gap-2.5 pt-1'><div class='bg-gradient-to-r from-[#0B1020] via-[#162240] to-[#0B1020] animate-pulse rounded-lg h-4 w-full'></div><div class='bg-gradient-to-r from-[#0B1020] via-[#162240] to-[#0B1020] animate-pulse rounded-lg h-4 w-11/12'></div><div class='bg-gradient-to-r from-[#0B1020] via-[#162240] to-[#0B1020] animate-pulse rounded-lg h-4 w-4/5'></div></div></section>";
  }
  const tutor = turn.tutor; if (!tutor) { return ""; }
  const isGap = tutor.knowledge_gap_detected, cited = tutor.cited_titles || [], uniqueCited = cited.filter(function (t, i) { return cited.indexOf(t) === i; }), speaking = activeSpeechTurn === tIdx;
  const speakBtn = isVoiceEnabled() ? "<button type='button' data-speak-turn='" + tIdx + "' aria-pressed='" + String(speaking) + "' class='flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0B1020] border border-[rgba(238,242,248,0.12)] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + (speaking ? STOP_SVG + "<span>Stop</span>" : SPEAKER_SVG + "<span>Listen</span>") + "</button>" : "";
  const badge = isGap ? "<span class='px-3 py-1 rounded-full bg-amber-400/10 text-amber-300 shadow-[inset_0_0_0_1px_rgba(252,211,77,0.25)] text-xs font-medium'>" + modeCopy("No matching source found", "Knowledge gap detected") + "</span>" : "<span class='px-3 py-1 rounded-full bg-[#4BB8E8]/10 text-[#4BB8E8] shadow-[inset_0_0_0_1px_rgba(75,184,232,0.25)] text-xs font-medium'>" + modeCopy("Sources available", "Grounded · Knowledge gap: none") + "</span>";
  const citations = uniqueCited.map(function (title, i) {
    const parts = String(title).split(/\s+—\s+|\s+-\s+/), label = parts.length > 1 ? parts[0] + " · " + parts.slice(1).join(" · ") : title;
    return "<button type='button' data-turn-cite='" + tIdx + "' data-cite-idx='" + i + "' data-cite-title='" + escapeHtml(title) + "' class='text-sm text-[#A0B0C8] hover:text-[#4BB8E8] transition cursor-pointer py-1 flex items-center gap-2 text-left focus:outline-none w-fit'><span class='text-xs font-mono text-[#4BB8E8] bg-[#0B1020] px-1.5 py-0.5 rounded shrink-0'>[" + (i + 1) + "]</span><span>" + escapeHtml(label) + "</span></button>";
  }).join("");
  const topics = (tutor.recommended_topics || []).map(function (topic) { return "<button type='button' data-topic='" + escapeHtml(topic) + "' class='flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] text-xs font-medium transition-colors focus:outline-none'>" + SPARKLE_SVG + "<span>" + escapeHtml(topic) + "</span></button>"; }).join("");
  return "<section class='w-full flex flex-col'><div class='flex items-center justify-between gap-2 mb-3'><div class='flex items-center gap-2.5 text-[#4BB8E8] text-lg font-medium select-none'>" + SPARKLE_SVG + "<span>AI Tutor</span>" + speakBtn + "</div>" + badge + "</div><div class='text-[#EEF2F8] text-base leading-relaxed flex flex-col gap-3 font-normal'>" + formatMarkdown(tutor.answer) + "</div>" + (citations ? "<div class='mt-5 pt-3 border-t border-[rgba(238,242,248,0.06)]'><div class='text-xs uppercase tracking-wider text-[#738196] mb-2'>Sources</div><div class='flex flex-col gap-0.5'>" + citations + "</div></div>" : "") + (topics ? "<div class='flex flex-wrap items-center gap-2 mt-4'>" + topics + "</div>" : "") + "</section>";
}
function renderChatStream() {
  const streamEl = document.getElementById("chat-stream"); if (!streamEl) { return; }
  streamEl.innerHTML = chatActionsHeader() + currentTurns.map(function (turn, tIdx) {
    const resList = turn.results || [], count = resList.length, isCollapsed = turn.ask_tutor && turn.collapsed !== false;
    const rLabel = turn.router_label || ((turn.top_k || 5) >= 7 ? "Auto-Router: Deep Synthesis" : "Auto-Router: Exact Lookup");
    const ragBadge = "<div data-specialist-only class='flex items-center gap-1.5 flex-wrap'><span class='px-2.5 py-0.5 rounded-full bg-[#4BB8E8]/10 border border-[#4BB8E8]/25 text-[11px] font-mono text-[#4BB8E8]'>" + escapeHtml(rLabel) + "</span><span class='px-2.5 py-0.5 rounded-full bg-[#0B1020] border border-[rgba(238,242,248,0.10)] text-[11px] font-mono text-[#738196]'>" + escapeHtml(formatRagLabel(turn)) + "</span></div>";
    const toggleBtn = count > 0 ? "<div class='flex items-center justify-between gap-2 flex-wrap'>" + (turn.ask_tutor ? "<button type='button' data-turn-toggle='" + tIdx + "' class='text-sm text-[#A0B0C8] hover:text-[#EEF2F8] transition-colors focus:outline-none w-fit'>" + (isCollapsed ? "▸ View " + count + " source passages" : "▾ Hide " + count + " source passages") + "</button>" : "<span class='text-sm text-[#A0B0C8]'>" + count + " source passages</span>") + ragBadge + "</div>" : "";
    const cardsHtml = resList.map(function (item, idx) {
      const tagLabel = (item.chunk.tags || []).map(escapeHtml).join(" · ");
      return "<article id='turn-" + tIdx + "-chunk-" + idx + "' data-chunk-title='" + escapeHtml(item.chunk.title || "") + "' tabindex='-1' class='group w-full p-6 rounded-xl bg-[#0B1020] shadow-[inset_0_0_0_1px_rgba(238,242,248,0.08)] hover:shadow-[inset_0_0_0_1px_rgba(238,242,248,0.16)] transition-all duration-300 flex flex-col gap-3 outline-none'><div class='flex items-baseline justify-between gap-3'><div class='flex items-center gap-2.5 min-w-0'><span class='px-1.5 py-0.5 rounded bg-[#4BB8E8]/15 text-[#4BB8E8] font-mono text-xs font-semibold shrink-0'>[" + (idx + 1) + "]</span><h2 class='text-xl font-medium text-[#EEF2F8] truncate'><a href='#reader-heading' data-reader-turn='" + tIdx + "' data-reader-chunk='" + idx + "' class='hover:underline focus-visible:outline'>" + escapeHtml(item.chunk.title) + "</a></h2></div><span data-specialist-only class='text-[#738196] font-mono text-xs shrink-0'>score: " + Number(item.score).toFixed(2) + "</span></div>" + (tagLabel ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide'>// " + tagLabel + "</div>" : "") + "<div class='md-prose text-[#C8D4E6] text-[15px] leading-relaxed flex flex-col gap-2.5'>" + formatMarkdown(item.chunk.content) + "</div><a href='#reader-heading' data-reader-turn='" + tIdx + "' data-reader-chunk='" + idx + "' class='text-xs text-[#A0B0C8] hover:text-[#EEF2F8] self-start focus-visible:outline'>Open in Reader ↗</a></article>";
    }).join("");
    return "<article id='turn-" + tIdx + "' tabindex='-1' class='flex flex-col gap-5 w-full outline-none border-b border-[rgba(238,242,248,0.06)] pb-8 last:border-b-0'><div class='self-end max-w-[85%] rounded-2xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] px-5 py-3 text-[#EEF2F8] text-base leading-relaxed'>" + escapeHtml(turn.query) + "</div>" + (turn.ask_tutor ? renderTurnTutorHtml(turn, tIdx) : "") + toggleBtn + "<div id='turn-" + tIdx + "-results' class='" + (isCollapsed ? "hidden " : "flex ") + "flex-col gap-4'>" + cardsHtml + "</div></article>";
  }).join("");
  bindChatActions(streamEl); bindMarkdownLinks(streamEl, "", selectedTag);
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
