"""Client-side JavaScript for the Google Stitch AI Engineering Knowledge Engine UI."""

from features.ui.advisor_script import ADVISOR_SCRIPT
from features.ui.backup_script import BACKUP_SCRIPT
from features.ui.budget_script import BUDGET_SCRIPT
from features.ui.chat_actions import CHAT_ACTIONS_SCRIPT
from features.ui.chat_script import CHAT_SCRIPT
from features.ui.compliance_script import COMPLIANCE_SCRIPT
from features.ui.graph_script import GRAPH_SCRIPT
from features.ui.install_script import INSTALL_SCRIPT
from features.ui.interaction_script import INTERACTION_SCRIPT
from features.ui.library_script import LIBRARY_SCRIPT
from features.ui.privacy_script import PRIVACY_SCRIPT
from features.ui.scope_script import SCOPE_SCRIPT
from features.ui.settings_script import SETTINGS_SCRIPT
from features.ui.topics_script import TOPICS_SCRIPT
from features.ui.workspace_menu_script import WORKSPACE_MENU_SCRIPT

CLIENT_SCRIPT: str = (
    r"""<script>
const resultsEl = document.getElementById("results"), tutorEl = document.getElementById("tutor"), queryEl = document.getElementById("query"), providerEl = document.getElementById("provider"), modelEl = document.getElementById("model"), apiKeyEl = document.getElementById("api-key"), askTutorToggle = document.getElementById("ask-tutor-toggle"), promptBox = document.getElementById("prompt-container"), chunksHeader = document.getElementById("chunks-header"), chunksTitle = document.getElementById("chunks-title"), settingsModal = document.getElementById("settings-modal"), onboardingModal = document.getElementById("onboarding-modal"), uploadModal = document.getElementById("upload-modal"), micBtn = document.getElementById("mic-btn");
let selectedTag = null, isActiveView = false, activeController = null, chunksCollapsed = true, chunkCount = 0, activeRecognition = null;
const PROVIDER_DEFAULTS = { ollama: "qwen3:8b", openai: "gpt-4o-mini", kimi: "kimi-k3.1-pro", deepseek: "deepseek-chat", gemini: "gemini-3.8-flash", anthropic: "claude-sonnet-5-5", xai: "grok-4", mistral: "mistral-small-latest" };
const NON_CHAT_RE = /^(nomic-embed|mxbai-embed|bge-|all-minilm|text-embedding|mistral-embed|whisper|phonon|kokoro|piper|tts-)|embed/i;
const SPARKLE_SVG = "<svg aria-hidden='true' class='w-4 h-4 shrink-0' viewBox='0 0 24 24' fill='currentColor'><path d='M12 2L14.6 9.4L22 12L14.6 14.6L12 22L9.4 14.6L2 12L9.4 9.4L12 2Z'/></svg>";
const PROVIDER_LABELS = { ollama: "Ollama (Local)", openai: "OpenAI", gemini: "Gemini", anthropic: "Anthropic", kimi: "Kimi", deepseek: "DeepSeek", xai: "xAI", mistral: "Mistral" };
const PROVIDER_ORDER = ["ollama", "openai", "gemini", "anthropic", "kimi", "deepseek", "xai", "mistral"];
let appKeyStatus = {};
function getApiKey() { return apiKeyEl.value.trim(); }
function hasSavedKey(provider) { return Boolean(appKeyStatus[provider] && appKeyStatus[provider].configured); }
function renderProviderPills() {
  const locked = localOnly(), active = providerEl.value;
  for (const barId of ["saved-keys-bar", "onboarding-keys-bar"]) {
    const bar = document.getElementById(barId); if (!bar) { continue; }
    bar.innerHTML = PROVIDER_ORDER.map(function (prov) {
      const saved = prov === "ollama" || hasSavedKey(prov), isAct = prov === active, disabled = locked && prov !== "ollama";
      const cls = isAct ? "border-[#4BB8E8] bg-[#4BB8E8]/15 text-[#EEF2F8]" : (saved ? "border-[#38D399]/40 bg-[#04060F] text-[#EEF2F8]" : "border-[rgba(238,242,248,0.12)] bg-[#04060F] text-[#738196]");
      const badge = prov === "ollama" ? "" : (saved ? " ✓" : "");
      return "<button type='button' data-pick-provider='" + prov + "' " + (disabled ? "disabled " : "") + "class='px-2.5 py-1 rounded-full border text-xs transition " + cls + (disabled ? " opacity-40 cursor-not-allowed" : " hover:border-[#4BB8E8]") + "'>" + escapeHtml(PROVIDER_LABELS[prov] + badge) + "</button>";
    }).join("");
    bar.querySelectorAll("[data-pick-provider]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const picked = btn.getAttribute("data-pick-provider"); if (!picked || (localOnly() && picked !== "ollama")) { return; }
        providerEl.value = picked; document.getElementById("onboarding-provider").value = picked;
        apiKeyEl.value = ""; syncProviderPrivacyUI(picked, "settings-privacy-notice", "settings-api-key-group");
        syncProviderPrivacyUI(picked, "onboarding-privacy-notice", "onboarding-api-key-group");
        syncKeyStatusUI(); loadModels();
      });
    });
  }
}
function syncKeyStatusUI() {
  const prov = providerEl.value, info = appKeyStatus[prov], el = document.getElementById("api-key-status");
  renderProviderPills();
  if (!el) { return; }
  if (info && info.configured) {
    el.textContent = (info.source === "env" ? "Loaded from environment" : "Saved securely on this computer") + (info.hint ? " (" + info.hint + ")" : "") + " · persists across restarts";
    apiKeyEl.placeholder = "Key saved (" + (info.hint || "configured") + ") — enter to replace";
  } else {
    el.textContent = "Not saved yet. Paste your key and click Save Key — you can save keys for multiple providers.";
    apiKeyEl.placeholder = "Enter cloud provider API key";
  }
}
async function loadKeyStatus() {
  try {
    const res = await areaFetch("/api/keys/status");
    if (res.ok) { const data = await res.json(); appKeyStatus = data.keys || {}; syncKeyStatusUI(); }
  } catch (_e) {}
}
async function saveAppApiKey(provider, rawKey, inputEl) {
  const key = String(rawKey || "").trim();
  if (!provider || provider === "ollama" || !key) { return false; }
  const res = await areaFetch("/api/keys", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: provider, api_key: key }) });
  if (!res.ok) { return false; }
  const data = await res.json(); appKeyStatus = data.keys || {};
  if (inputEl) { inputEl.value = ""; }
  syncKeyStatusUI();
  return true;
}
function escapeHtml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
"""
    + SETTINGS_SCRIPT
    + TOPICS_SCRIPT
    + WORKSPACE_MENU_SCRIPT
    + LIBRARY_SCRIPT
    + CHAT_SCRIPT
    + CHAT_ACTIONS_SCRIPT
    + GRAPH_SCRIPT
    + INTERACTION_SCRIPT
    + SCOPE_SCRIPT
    + PRIVACY_SCRIPT
    + COMPLIANCE_SCRIPT
    + ADVISOR_SCRIPT
    + BUDGET_SCRIPT
    + BACKUP_SCRIPT
    + INSTALL_SCRIPT
    + r"""
function syncChunksToggle(tutorActive) {
  chunksHeader.classList.toggle("hidden", !tutorActive || chunkCount === 0); chunksHeader.classList.toggle("flex", tutorActive && chunkCount > 0);
  chunksTitle.textContent = (chunksCollapsed ? "▸ View " : "▾ Hide ") + chunkCount + (chunksCollapsed ? " source passages from the handbook" : " source passages");
  resultsEl.classList.toggle("hidden", tutorActive && chunksCollapsed);
}
function setLoadingState(loading) {
  promptBox.className = loading ? "w-full rounded-full bg-[#0B1020] shadow-[inset_0_0_0_1px_#4BB8E8,0_0_20px_rgba(75,184,232,0.22)] animate-pulse flex items-center py-3 px-4 gap-3 transition-all duration-200" : "w-full rounded-full bg-[#0B1020] shadow-[inset_0_0_0_1px_rgba(238,242,248,0.16)] focus-within:shadow-[inset_0_0_0_1px_#4BB8E8] flex items-center py-3 px-4 gap-3 transition-all duration-200";
}
function setViewMode(active, hideDock) {
  document.getElementById("workspace-shell").classList.remove("hidden");
  queryEl.placeholder = active ? "Ask a follow-up..." : defaultPlaceholder;
  const dock = document.getElementById("search-dock"), stream = document.getElementById("active-stream"), gv = document.getElementById("graph-view"); if (gv) { gv.classList.add("hidden"); }
  if (!hideDock) { stream.className = (active ? "flex " : "hidden ") + "w-full max-w-3xl flex-1 pt-8 pb-8 flex-col gap-8 outline-none"; }
  if (!hideDock) {
    dock.className = active ? "chat-dock sticky bottom-0 z-30 w-full max-w-3xl pb-6 pt-3 flex flex-col items-center" : "w-full max-w-3xl mx-auto flex flex-col items-center justify-center relative z-30";
  }
  dock.classList.toggle("hidden", Boolean(active && hideDock));
  if (isActiveView === active) { return Promise.resolve(); }
  isActiveView = active;
  return withViewTransition(function () {
    document.getElementById("workspace-shell").className = active ? "flex flex-col w-full flex-1 items-center px-4 sm:px-6" : "flex flex-col w-full flex-1 justify-center items-center px-4 sm:px-6";
    document.getElementById("hero-heading").classList.toggle("hidden", active); document.getElementById("seed-chips").classList.toggle("hidden", active);
    stream.classList.toggle("hidden", !active); stream.classList.toggle("flex", active);
  }, active ? stream : queryEl);
}
async function toggleDictation() {
  const policyVersion = areaVersion;
  try {
    const response = await areaFetch("/api/workspace");
    if (!response.ok) { throw new Error("Refresh the workspace before starting dictation."); }
    const data = await response.json();
    if (policyVersion !== areaVersion) { return; }
    applyWorkspacePayload(data);
  } catch (error) { areaStatus(error.message); return; }
  if (localOnly()) { areaStatus("Browser dictation is blocked by the local-only lock. Use local Whisper for transcription."); return; }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (activeRecognition) { activeRecognition.stop(); activeRecognition = null; return; }
  if (!SR) { areaFetch("/api/audio/transcribe", { method: "POST" }); return; }
  const rec = new SR(), version = areaVersion; activeRecognition = rec;
  micBtn.setAttribute("aria-pressed", "true"); micBtn.className = "w-9 h-9 rounded-full text-[#4BB8E8] bg-[#4BB8E8]/15 animate-pulse flex items-center justify-center shrink-0 transition";
  rec.onresult = function (e) { if (version !== areaVersion) { return; } const t = e.results[0] && e.results[0][0] ? e.results[0][0].transcript : ""; if (t) { queryEl.value = (queryEl.value ? queryEl.value + " " : "") + t; queryEl.focus(); } };
  rec.onend = rec.onerror = function () { activeRecognition = null; micBtn.setAttribute("aria-pressed", "false"); micBtn.className = "w-9 h-9 rounded-full text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-[#EEF2F8]/10 flex items-center justify-center shrink-0 transition"; };
  rec.start();
}
function syncModelMirrors() {
  for (const id of ["settings-model", "onboarding-model"]) {
    const mirror = document.getElementById(id); if (!mirror) { continue; }
    mirror.innerHTML = modelEl.innerHTML;
    if (modelEl.selectedIndex >= 0) { mirror.selectedIndex = modelEl.selectedIndex; }
    mirror.disabled = modelEl.disabled;
  }
}
function selectActiveModel(value, optProvider) {
  if (!value) { return; }
  if (optProvider && optProvider !== providerEl.value && (!localOnly() || optProvider === "ollama")) {
    providerEl.value = optProvider; document.getElementById("onboarding-provider").value = optProvider;
    syncProviderPrivacyUI(optProvider, "settings-privacy-notice", "settings-api-key-group");
    syncProviderPrivacyUI(optProvider, "onboarding-privacy-notice", "onboarding-api-key-group");
    syncKeyStatusUI();
  }
  modelEl.value = value;
  if (providerEl.value === "ollama") { localStorage.setItem("preferred_local_model", value); }
  syncModelMirrors();
}
async function fetchProviderChatModels(provider) {
  const apiKey = provider === providerEl.value ? getApiKey() : "";
  const res = await areaFetch("/api/models?provider=" + encodeURIComponent(provider), { headers: apiKey ? { "x-api-key": apiKey } : {} });
  if (!res.ok) { return []; }
  const data = await res.json();
  return (data.chat_models || data.models || []).filter(function (m) { return !NON_CHAT_RE.test(m) && (!localOnly() || !/cloud/i.test(m)); });
}
async function loadModels() {
  const activeProv = providerEl.value, prevModel = modelEl.value;
  const providers = localOnly() ? ["ollama"] : PROVIDER_ORDER.filter(function (p) { return p === "ollama" || p === activeProv || hasSavedKey(p); });
  const lists = await Promise.all(providers.map(function (p) { return fetchProviderChatModels(p).catch(function () { return []; }); }));
  modelEl.innerHTML = "";
  const grouped = providers.length > 1;
  let activeModels = [];
  providers.forEach(function (prov, idx) {
    const models = lists[idx] || [];
    if (prov === activeProv) { activeModels = models; }
    if (!models.length) { return; }
    const container = grouped ? document.createElement("optgroup") : modelEl;
    if (grouped) { container.label = PROVIDER_LABELS[prov] || prov; modelEl.appendChild(container); }
    for (const model of models) {
      const opt = document.createElement("option");
      opt.value = model; opt.textContent = model; opt.dataset.provider = prov; opt.className = "bg-[#0B1020] text-[#EEF2F8]";
      container.appendChild(opt);
    }
  });
  const pool = activeModels.length ? activeModels : (lists.find(function (l) { return l.length; }) || []);
  const preferred = activeProv === "ollama" ? localStorage.getItem("preferred_local_model") : null;
  const recommended = pool.find(function (m) { return m.toLowerCase().startsWith("qwen3:") || m.toLowerCase().startsWith("qwen2.5:"); });
  const chosen = (prevModel && !NON_CHAT_RE.test(prevModel) && pool.includes(prevModel)) ? prevModel : ((preferred && pool.includes(preferred) ? preferred : null) || recommended || (PROVIDER_DEFAULTS[activeProv] && pool.includes(PROVIDER_DEFAULTS[activeProv]) ? PROVIDER_DEFAULTS[activeProv] : (pool[0] || "")));
  const match = Array.from(modelEl.options).find(function (o) { return o.value === chosen && o.dataset.provider === activeProv; }) || Array.from(modelEl.options).find(function (o) { return o.value === chosen; });
  if (match) { modelEl.selectedIndex = match.index; }
  syncModelMirrors();
}
function setActiveTag(tag) { selectedTag = tag; renderLibraryTopics(); }
function renderResults(results, tutorActive) {
  resultsEl.innerHTML = ""; chunkCount = (results || []).length; syncChunksToggle(Boolean(tutorActive));
  document.getElementById("stream-divider").classList.toggle("hidden", !tutorEl.innerHTML || chunkCount === 0);
}
function renderTutor(tutor) { if (!tutor) { tutorEl.innerHTML = ""; document.getElementById("stream-divider").classList.add("hidden"); } }
function abortActiveRequest() { ++currentScrollId; if (activeController) { activeController.abort(); activeController = null; } setLoadingState(false); }
function resetHome() { activeScope = { subfolder: null, doc_id: null }; renderScopeChoices(); abortActiveRequest(); if (activeRecognition) { activeRecognition.abort(); activeRecognition = null; } stopActiveAudio(); stopGraphSimulation(); currentChatId = null; currentTurns = []; document.getElementById("chat-stream").innerHTML = ""; queryEl.value = ""; setActiveTag(null); setViewMode(false); renderTutor(null); renderResults([], false); renderRecentChats(); queryEl.focus(); }
async function runSearch(withTutor) {
  const q = queryEl.value.trim(), useTutor = appliedRunMode !== "search" && (withTutor !== undefined ? withTutor : (askTutorToggle.checked && q.length > 0));
  abortActiveRequest();
  if (areaSwitching) { return; }
  if (!q && !selectedTag) { resetHome(); return; }
  if (!q && selectedTag) { await openLibraryCatalog(selectedTag); return; }
  if (!currentChatId) { currentChatId = newChatId(); }
  const controller = new AbortController(); activeController = controller; renderTutor(null); renderResults([], false);
  const pendingTurn = { query: q, tag: selectedTag, ask_tutor: Boolean(useTutor), loadingTutor: Boolean(useTutor), tutor: null, results: [], collapsed: Boolean(useTutor), top_k: ragConfig.top_k, retrieval_mode: ragConfig.retrieval_mode, rrf_k: ragConfig.rrf_k, temperature: ragConfig.temperature };
  currentTurns.push(pendingTurn);
  const turnIdx = currentTurns.length - 1; queryEl.value = ""; setViewMode(true); setLoadingState(true); renderChatStream();
  const newTurnEl = document.getElementById("turn-" + turnIdx); if (newTurnEl) { scrollIntoViewAsync(newTurnEl, { behavior: "smooth", block: "start" }); }
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const fastParams = new URLSearchParams({ q: q, ask_tutor: "false", top_k: String(ragConfig.top_k), retrieval_mode: ragConfig.retrieval_mode, rrf_k: String(ragConfig.rrf_k), temperature: String(ragConfig.temperature) });
    for (const [key, value] of Object.entries(activeScope)) { if (value !== null) { fastParams.set(key, value); } }
    if (providerEl.value !== "ollama") { fastParams.set("retrieval_mode", "lexical"); }
    fastParams.set("provider", providerEl.value); fastParams.set("model", modelEl.value);
    if (selectedTag) { fastParams.set("tag", selectedTag); }
    const fastResponse = await areaFetch("/api/search?" + fastParams.toString(), { headers: headers, signal: controller.signal });
    const fastData = await fastResponse.json();
    if (!fastResponse.ok) { throw new Error(fastData.detail || "Search failed."); }
    if (controller.signal.aborted) { return; }
    pendingTurn.results = fastData.results || []; pendingTurn.router_label = (fastData.rag_config && fastData.rag_config.router_label) || ""; renderChatStream();
    const sessionResponse = await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/turn", {
      method: "POST", headers: headers, signal: controller.signal,
      body: JSON.stringify({ subfolder: activeScope.subfolder, doc_id: activeScope.doc_id, query: q, tag: selectedTag, ask_tutor: Boolean(useTutor), provider: providerEl.value, model: modelEl.value.trim() || null, api_key: apiKey || null, top_k: ragConfig.top_k, retrieval_mode: ragConfig.retrieval_mode, rrf_k: ragConfig.rrf_k, temperature: ragConfig.temperature })
    });
    const session = await sessionResponse.json();
    if (!sessionResponse.ok) { throw new Error(session.detail || "Answer failed."); }
    if (controller.signal.aborted) { return; }
    const rLabel = (session.router_decision && session.router_decision.label) || pendingTurn.router_label || "";
    currentTurns = (session.turns || []).map(function (t, i) { return Object.assign({}, t, { router_label: i === turnIdx ? rLabel : (currentTurns[i] && currentTurns[i].router_label) || "", collapsed: i === turnIdx ? Boolean(t.ask_tutor) : (currentTurns[i] ? currentTurns[i].collapsed : true) }); });
    renderChatStream(); await loadRecentChats(); refreshBudget();
  } catch (err) { if (err && err.name === "AbortError") { return; } pendingTurn.loadingTutor = false; pendingTurn.tutor = { answer: err.message || "Request failed.", cited_titles: [], knowledge_gap_detected: true }; areaStatus(err.message || "Request failed."); renderChatStream(); }
  finally { if (activeController === controller) { activeController = null; setLoadingState(false); } }
}
async function askTutor() { askTutorToggle.checked = appliedRunMode !== "search"; await runSearch(askTutorToggle.checked); }
function submitQuery() { if (queryEl.value.trim() || selectedTag) { runSearch(askTutorToggle.checked && queryEl.value.trim().length > 0); } else { queryEl.focus(); } }
document.getElementById("search-form").addEventListener("submit", function (e) { e.preventDefault(); submitQuery(); }); document.getElementById("model-refresh").addEventListener("click", loadModels);
document.getElementById("new-chat-btn").addEventListener("click", resetHome);
document.getElementById("chunks-toggle-btn").addEventListener("click", function () { chunksCollapsed = !chunksCollapsed; syncChunksToggle(true); });
document.getElementById("sidebar-browse-btn").addEventListener("click", function () { setActiveTag(null); openLibraryCatalog(null); }); document.getElementById("sidebar-graph-btn").addEventListener("click", function () { setActiveTag(null); openGraphView(); }); document.getElementById("home-browse-btn").addEventListener("click", function () { setActiveTag(null); openLibraryCatalog(null); }); document.getElementById("more-ideas-btn").addEventListener("click", cycleIdeas);
document.getElementById("open-settings-btn").addEventListener("click", function () { openSettings(); }); document.getElementById("close-settings-modal").addEventListener("click", function () { settingsModal.close(); }); document.getElementById("save-workspace-btn").addEventListener("click", saveWorkspace);
document.getElementById("open-onboarding-btn").addEventListener("click", function () { settingsModal.close(); onboardingModal.showModal(); }); document.getElementById("close-onboarding-modal").addEventListener("click", function () { onboardingModal.close(); });
document.getElementById("onboarding-start-btn").addEventListener("click", function () { completeOnboarding(false); }); document.getElementById("onboarding-upload-btn").addEventListener("click", function () { completeOnboarding(true); });
const fileIn = document.getElementById("upload-file-input"), dropzone = document.getElementById("upload-dropzone");
document.getElementById("prompt-upload-btn").addEventListener("click", function () { openUploadDialog(); }); document.getElementById("close-upload-modal").addEventListener("click", function () { stageUploadFiles([]); uploadModal.close(); });
document.getElementById("cancel-upload-btn").addEventListener("click", function () { stageUploadFiles([]); uploadModal.close(); }); document.getElementById("confirm-upload-btn").addEventListener("click", function () { uploadFiles(stagedFiles); });
fileIn.addEventListener("change", function () { if (fileIn.files && fileIn.files.length) { stageUploadFiles(fileIn.files); fileIn.value = ""; } });
dropzone.addEventListener("dragover", function (e) { e.preventDefault(); dropzone.classList.add("border-[#4BB8E8]"); }); dropzone.addEventListener("dragleave", function () { dropzone.classList.remove("border-[#4BB8E8]"); });
dropzone.addEventListener("drop", function (e) { e.preventDefault(); dropzone.classList.remove("border-[#4BB8E8]"); if (e.dataTransfer && e.dataTransfer.files) { stageUploadFiles(e.dataTransfer.files); } });
document.getElementById("cfg-folder-select").addEventListener("change", function (e) { document.getElementById("cfg-knowledge-dir").value = e.target.value; syncFolderHelper(e.target.value, "cfg-folder-helper"); });
document.getElementById("onboarding-folder-select").addEventListener("change", function (e) { document.getElementById("onboarding-folder").value = e.target.value; syncFolderHelper(e.target.value, "onboarding-folder-helper"); });
document.getElementById("cfg-new-folder-btn").addEventListener("click", function () { document.getElementById("cfg-folder-select").classList.add("hidden"); const inp = document.getElementById("cfg-knowledge-dir"); inp.classList.remove("hidden"); inp.focus(); });
document.getElementById("onboarding-new-folder-btn").addEventListener("click", function () { document.getElementById("onboarding-folder-select").classList.add("hidden"); const inp = document.getElementById("onboarding-folder"); inp.classList.remove("hidden"); inp.focus(); });
document.getElementById("cfg-knowledge-dir").addEventListener("input", function (e) { syncFolderHelper(e.target.value, "cfg-folder-helper"); }); document.getElementById("onboarding-folder").addEventListener("input", function (e) { syncFolderHelper(e.target.value, "onboarding-folder-helper"); });
document.getElementById("rag-reset-btn").addEventListener("click", function () { ragConfig = { retrieval_mode: "hybrid", top_k: 5, rrf_k: 60, temperature: 0.2 }; syncRagStudioUI(); });
document.querySelectorAll("[data-retrieval-mode]").forEach(function (btn) { btn.addEventListener("click", function () { ragConfig.retrieval_mode = btn.getAttribute("data-retrieval-mode") || "hybrid"; syncRagStudioUI(); }); });
document.getElementById("rag-top-k").addEventListener("input", function (e) { ragConfig.top_k = Number(e.target.value); syncRagStudioUI(); }); document.getElementById("rag-rrf-k").addEventListener("input", function (e) { ragConfig.rrf_k = Number(e.target.value); syncRagStudioUI(); }); document.getElementById("rag-temperature").addEventListener("input", function (e) { ragConfig.temperature = Number(e.target.value); syncRagStudioUI(); });
document.getElementById("tts-model").addEventListener("change", syncTtsVoices); document.getElementById("tts-test-btn").addEventListener("click", previewVoice); document.getElementById("tts-api-key").addEventListener("input", function () { if (currentTurns.length) { renderChatStream(); } }); micBtn.addEventListener("click", toggleDictation);
bindRunModes(); bindBudgetControls(); bindSettingsTabs(); bindWorkspaceMenu(); bindBackupControls();
document.getElementById("download-local-model-btn").addEventListener("click", installRecommendedLocalAI); bindDialogFallbacks(); bindDestination("upload"); bindCardMoveDialog();
document.getElementById("cfg-anonymize-uploads").addEventListener("change", function () { if (stagedFiles.length) { previewUploads(); } });
providerEl.addEventListener("change", function () { document.getElementById("onboarding-provider").value = providerEl.value; syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group"); syncProviderPrivacyUI(providerEl.value, "onboarding-privacy-notice", "onboarding-api-key-group"); apiKeyEl.value = ""; syncKeyStatusUI(); loadModels(); });
document.getElementById("onboarding-provider").addEventListener("change", function (e) { providerEl.value = e.target.value; syncProviderPrivacyUI(e.target.value, "onboarding-privacy-notice", "onboarding-api-key-group"); syncProviderPrivacyUI(e.target.value, "settings-privacy-notice", "settings-api-key-group"); syncKeyStatusUI(); loadModels(); });
for (const selId of ["model", "settings-model", "onboarding-model"]) {
  const sel = document.getElementById(selId);
  if (sel) { sel.addEventListener("change", function (e) { const opt = e.target.options[e.target.selectedIndex]; selectActiveModel(e.target.value, opt && opt.dataset ? opt.dataset.provider : null); }); }
}
document.getElementById("save-api-key-btn").addEventListener("click", async function () { if (await saveAppApiKey(providerEl.value, apiKeyEl.value, apiKeyEl)) { await loadModels(); } });
document.getElementById("onboarding-save-key-btn").addEventListener("click", async function () { const inp = document.getElementById("onboarding-api-key"); if (await saveAppApiKey(document.getElementById("onboarding-provider").value, inp.value, inp)) { await loadModels(); } });
document.getElementById("toggle-cloud-access-btn").addEventListener("click", async function () { await setCloudAccess(localOnly()); });
document.getElementById("save-tts-key-btn").addEventListener("click", async function () { const mVal = document.getElementById("tts-model").value, prov = mVal.startsWith("elevenlabs") ? "elevenlabs" : "openai", el = document.getElementById("tts-api-key"); if (await saveAppApiKey(prov, el.value, el) && currentTurns.length) { renderChatStream(); } });
document.querySelectorAll(".seed-chip").forEach(function (chip) { chip.addEventListener("click", function () { queryEl.value = chip.getAttribute("data-seed") || ""; askTutor(); }); });
document.getElementById("sidebar-collapse-btn").addEventListener("click", function () { document.getElementById("sidebar").classList.add("-translate-x-full"); document.getElementById("main-shell").classList.replace("pl-[250px]", "pl-0"); document.getElementById("sidebar-open-btn").classList.replace("hidden", "flex"); }); document.getElementById("sidebar-open-btn").addEventListener("click", function () { document.getElementById("sidebar").classList.remove("-translate-x-full"); document.getElementById("main-shell").classList.replace("pl-0", "pl-[250px]"); document.getElementById("sidebar-open-btn").classList.replace("flex", "hidden"); });
syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group"); syncRagStudioUI(); initializeWorkspace();
</script>"""
)
