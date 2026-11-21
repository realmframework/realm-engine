"""Modern two-state API key management: Connected card, Test/Verify, Replace, Remove, and Show/Hide."""

KEYS_SCRIPT: str = r"""
const PROVIDER_KEY_URLS = {
  openai: "https://platform.openai.com/api-keys",
  gemini: "https://aistudio.google.com/apikey",
  anthropic: "https://console.anthropic.com/settings/keys",
  kimi: "https://platform.moonshot.ai/console/api-keys",
  deepseek: "https://platform.deepseek.com/api_keys",
  xai: "https://console.x.ai/",
  mistral: "https://console.mistral.ai/api-keys",
  elevenlabs: "https://elevenlabs.io/app/settings/api-keys",
  ollama_web: "https://ollama.com/settings/keys"
};
const PROVIDER_KEY_HINTS = {
  openai: "sk-…", gemini: "AIza…", anthropic: "sk-ant-…", kimi: "sk-…",
  deepseek: "sk-…", xai: "xai-…", mistral: "…", elevenlabs: "sk_…", ollama_web: "…"
};
const EYE_OPEN_SVG = "<svg aria-hidden='true' class='w-4 h-4' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5-9.5-6.5-9.5-6.5Z'/><circle cx='12' cy='12' r='3'/></svg>";
const EYE_OFF_SVG = "<svg aria-hidden='true' class='w-4 h-4' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='M3 3l18 18M10.6 10.6a2.5 2.5 0 0 0 3.5 3.5M9.9 5.3A9.8 9.8 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3.2 4.1M6.6 6.7C4.2 8.4 2.5 12 2.5 12s3.5 6.5 9.5 6.5c1.3 0 2.6-.3 3.7-.8'/></svg>";
let keyReplaceMode = false, onboardingReplaceMode = false, keyVerifyState = {}, keyVerifyBusy = {};

function formatMaskedKey(hint) {
  const raw = String(hint || "").trim();
  if (!raw || raw === "saved") { return "••••••••"; }
  const tail = raw.replace(/^[.…]+/, "");
  return tail ? ("••••" + tail) : "••••••••";
}

function setSecretVisibility(inputId, btnId, visible) {
  const inp = document.getElementById(inputId), btn = document.getElementById(btnId);
  if (!inp || !btn) { return; }
  inp.type = visible ? "text" : "password";
  btn.setAttribute("aria-pressed", String(visible));
  const lbl = visible ? t("key_hide_aria") : t("key_show_aria");
  btn.setAttribute("aria-label", lbl);
  btn.title = lbl;
  btn.innerHTML = visible ? EYE_OFF_SVG : EYE_OPEN_SVG;
}

function renderProviderPills() {
  const locked = localOnly(), active = providerEl.value;
  for (const barId of ["saved-keys-bar", "onboarding-keys-bar"]) {
    const bar = document.getElementById(barId); if (!bar) { continue; }
    bar.innerHTML = PROVIDER_ORDER.map(function (prov) {
      const saved = prov === "ollama" || hasSavedKey(prov), isAct = prov === active, disabled = locked && prov !== "ollama";
      const vSt = keyVerifyState[prov], isBad = Boolean(vSt && vSt.status === "invalid");
      const cls = isAct ? "border-[#4BB8E8] bg-[#4BB8E8]/15 text-[#EEF2F8] font-medium" : (saved ? (isBad ? "border-[#EF4444]/40 bg-[#04060F] text-[#EEF2F8]" : "border-[#38D399]/40 bg-[#04060F] text-[#EEF2F8]") : "border-[rgba(238,242,248,0.12)] bg-[#04060F] text-[#A0B0C8]");
      const dotCls = isBad ? "bg-[#EF4444]" : "bg-[#38D399]";
      const dot = prov === "ollama" ? "" : (saved ? "<span aria-hidden='true' class='w-2 h-2 rounded-full " + dotCls + " shrink-0'></span>" : "");
      return "<button type='button' data-pick-provider='" + prov + "' " + (disabled ? "disabled " : "") + "class='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs transition " + cls + (disabled ? " opacity-40 cursor-not-allowed" : " hover:border-[#4BB8E8]") + "'>" + dot + "<span>" + escapeHtml(PROVIDER_LABELS[prov]) + "</span></button>";
    }).join("");
    bar.querySelectorAll("[data-pick-provider]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const picked = btn.getAttribute("data-pick-provider"); if (!picked || (localOnly() && picked !== "ollama")) { return; }
        providerEl.value = picked; document.getElementById("onboarding-provider").value = picked;
        keyReplaceMode = false; onboardingReplaceMode = false;
        apiKeyEl.value = ""; setSecretVisibility("api-key", "toggle-api-key-visibility", false);
        syncProviderPrivacyUI(picked, "settings-privacy-notice", "settings-api-key-group");
        syncProviderPrivacyUI(picked, "onboarding-privacy-notice", "onboarding-api-key-group");
        syncKeyStatusUI(); loadModels();
      });
    });
  }
}

function renderKeyVerifyLine(prov, info, statusEl) {
  if (!statusEl) { return; }
  const state = keyVerifyState[prov];
  if (keyVerifyBusy[prov]) {
    statusEl.className = "text-xs text-[#4BB8E8]";
    statusEl.textContent = t("key_testing");
    return;
  }
  if (state) {
    if (state.status === "valid") {
      statusEl.className = "text-xs text-[#38D399]";
      statusEl.textContent = state.models_count > 0 ? t("key_verified_models", { n: state.models_count }) : t("key_verified_ok");
      return;
    }
    if (state.status === "rate_limited") {
      statusEl.className = "text-xs text-amber-300";
      statusEl.textContent = t("key_rate_limited");
      return;
    }
    if (state.status === "invalid") {
      statusEl.className = "text-xs text-[#FCA5A5]";
      statusEl.textContent = t("key_invalid_err");
      return;
    }
    if (state.status === "unreachable") {
      statusEl.className = "text-xs text-amber-300";
      statusEl.textContent = t("key_unreachable_err");
      return;
    }
    if (state.status === "removed") {
      statusEl.className = "text-xs text-[#A0B0C8]";
      statusEl.textContent = t("key_removed_ok", { provider: PROVIDER_LABELS[prov] || prov });
      return;
    }
    statusEl.className = "text-xs text-[#FCA5A5]";
    statusEl.textContent = t("key_verify_err");
    return;
  }
  if (info && info.configured) {
    statusEl.className = "text-xs text-[#A0B0C8]";
    statusEl.textContent = info.source === "env" ? t("key_env_managed") : t("key_click_test_hint");
  } else {
    statusEl.className = "text-xs text-[#A0B0C8]";
    statusEl.textContent = t("api_key_not_saved");
  }
}

function syncOnboardingKeyUI() {
  const obProvEl = document.getElementById("onboarding-provider"), card = document.getElementById("onboarding-key-connected"), row = document.getElementById("onboarding-key-entry-row");
  if (!obProvEl || !card || !row) { return; }
  const prov = obProvEl.value, info = appKeyStatus[prov], configured = Boolean(info && info.configured), showCard = configured && !onboardingReplaceMode;
  card.hidden = !showCard; row.hidden = showCard;
  const obInp = document.getElementById("onboarding-api-key"), cancelBtn = document.getElementById("onboarding-cancel-replace-btn");
  if (obInp) { obInp.placeholder = t("key_paste_ph", { provider: PROVIDER_LABELS[prov] || prov, hint: PROVIDER_KEY_HINTS[prov] || "…" }); }
  if (cancelBtn) { cancelBtn.hidden = !(configured && onboardingReplaceMode); }
  if (showCard) {
    const mask = document.getElementById("onboarding-key-mask"), badge = document.getElementById("onboarding-key-badge"), remBtn = document.getElementById("onboarding-remove-key-btn");
    if (mask) { mask.textContent = formatMaskedKey(info.hint); }
    if (badge) { badge.textContent = info.source === "env" ? t("key_from_env_short") : t("key_connected"); }
    if (remBtn) { remBtn.hidden = info.source === "env"; }
  }
}

function syncTtsKeyUI() {
  const mSel = document.getElementById("tts-model"), stEl = document.getElementById("tts-key-status"), inp = document.getElementById("tts-api-key");
  if (!mSel || !stEl) { return; }
  const prov = mSel.value.startsWith("elevenlabs") ? "elevenlabs" : "openai", info = appKeyStatus[prov];
  if (inp) { inp.placeholder = t("key_paste_ph", { provider: prov === "elevenlabs" ? "ElevenLabs" : "OpenAI", hint: PROVIDER_KEY_HINTS[prov] || "…" }); }
  if (info && info.configured) {
    stEl.className = "text-xs text-[#38D399]";
    stEl.textContent = t("key_saved_badge", { mask: formatMaskedKey(info.hint) });
  } else {
    stEl.className = "text-xs text-[#A0B0C8]";
    stEl.textContent = "";
  }
}

function syncKeyStatusUI() {
  const prov = providerEl.value, info = appKeyStatus[prov], configured = Boolean(info && info.configured), showCard = configured && !keyReplaceMode;
  renderProviderPills();
  if (typeof syncWebSearchUI === "function") { syncWebSearchUI(workspaceConfig); }
  const lbl = document.getElementById("settings-api-key-label"), getLink = document.getElementById("api-key-get-link");
  const card = document.getElementById("api-key-connected-card"), row = document.getElementById("api-key-entry-row");
  const cancelBtn = document.getElementById("cancel-replace-key-btn"), remBtn = document.getElementById("remove-api-key-btn");
  const badge = document.getElementById("api-key-connected-badge"), mask = document.getElementById("api-key-mask"), src = document.getElementById("api-key-source-note");
  const testBtn = document.getElementById("test-api-key-btn");
  const provName = PROVIDER_LABELS[prov] || prov;
  if (lbl) { lbl.textContent = prov === "ollama" ? t("api_key_lbl") : (provName + " " + t("api_key_lbl")); }
  if (getLink) {
    const url = PROVIDER_KEY_URLS[prov] || "";
    getLink.hidden = !url;
    if (url) { getLink.href = url; }
  }
  if (card) { card.hidden = !showCard; }
  if (row) { row.hidden = showCard; }
  if (cancelBtn) { cancelBtn.hidden = !(configured && keyReplaceMode); }
  if (apiKeyEl) { apiKeyEl.placeholder = t("key_paste_ph", { provider: provName, hint: PROVIDER_KEY_HINTS[prov] || "…" }); }
  if (showCard && info) {
    const vSt = keyVerifyState[prov], isInvalid = Boolean(vSt && vSt.status === "invalid"), isVerified = Boolean(vSt && vSt.status === "valid"), isWarn = Boolean(vSt && (vSt.status === "rate_limited" || vSt.status === "unreachable"));
    const wrap = document.getElementById("api-key-badge-wrap"), dot = document.getElementById("api-key-status-dot");
    if (card) { card.className = "rounded-xl bg-[#04060F] border px-4 py-3 flex flex-wrap items-center justify-between gap-3 " + (isInvalid ? "border-[#EF4444]/40" : (isWarn ? "border-amber-400/35" : "border-[#38D399]/40")); }
    if (wrap) { wrap.className = "inline-flex items-center gap-1.5 text-xs font-semibold " + (isInvalid ? "text-[#FCA5A5]" : (isWarn ? "text-amber-300" : "text-[#38D399]")); }
    if (dot) { dot.className = "w-2.5 h-2.5 rounded-full shrink-0 " + (isInvalid ? "bg-[#EF4444]" : (isWarn ? "bg-amber-400" : "bg-[#38D399]")); }
    if (badge) { badge.textContent = isInvalid ? t("key_invalid_badge") : (isVerified ? t("key_verified_badge") : (isWarn ? t("key_saved_short") : (info.source === "env" ? t("key_from_env_short") : t("key_connected")))); }
    if (mask) { mask.textContent = formatMaskedKey(info.hint); }
    if (src) { src.textContent = info.source === "env" ? t("api_key_from_env") : t("key_stored_local"); }
    if (remBtn) { remBtn.hidden = info.source === "env"; }
    if (testBtn) { testBtn.disabled = Boolean(keyVerifyBusy[prov]); testBtn.textContent = keyVerifyBusy[prov] ? t("key_testing") : t("key_test_btn"); }
  }
  renderKeyVerifyLine(prov, info, document.getElementById("api-key-status"));
  syncOnboardingKeyUI();
  syncTtsKeyUI();
}

async function loadKeyStatus() {
  try {
    const res = await areaFetch("/api/keys/status");
    if (res.ok) { const data = await safeJson(res); appKeyStatus = data.keys || {}; syncKeyStatusUI(); }
  } catch (_e) {}
}

async function verifyAppApiKey(provider) {
  if (!provider || provider === "ollama" || localOnly()) { return null; }
  keyVerifyBusy[provider] = true; syncKeyStatusUI();
  try {
    const res = await areaFetch("/api/keys/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: provider }) });
    const data = await safeJson(res);
    keyVerifyState[provider] = res.ok ? { ok: Boolean(data.ok), status: String(data.status || "error"), models_count: Number(data.models_count || 0) } : { ok: false, status: "error", models_count: 0 };
    if (keyVerifyState[provider].ok) { await loadModels(); }
    return keyVerifyState[provider];
  } catch (_e) {
    keyVerifyState[provider] = { ok: false, status: "unreachable", models_count: 0 };
    return keyVerifyState[provider];
  } finally {
    keyVerifyBusy[provider] = false; syncKeyStatusUI();
  }
}

async function saveAppApiKey(provider, rawKey, inputEl) {
  const key = String(rawKey || "").trim();
  if (!provider || provider === "ollama" || !key) { return false; }
  const res = await areaFetch("/api/keys", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: provider, api_key: key }) });
  if (!res.ok) { return false; }
  const data = await safeJson(res); appKeyStatus = data.keys || {};
  if (inputEl) { inputEl.value = ""; inputEl.type = "password"; }
  keyReplaceMode = false; onboardingReplaceMode = false;
  delete keyVerifyState[provider];
  setSecretVisibility("api-key", "toggle-api-key-visibility", false);
  setSecretVisibility("onboarding-api-key", "toggle-onboarding-key-visibility", false);
  setSecretVisibility("tts-api-key", "toggle-tts-key-visibility", false);
  syncKeyStatusUI();
  if (!localOnly() && PROVIDER_ORDER.includes(provider)) { verifyAppApiKey(provider); }
  return true;
}

async function removeAppApiKey(provider) {
  if (!provider || provider === "ollama") { return false; }
  const res = await areaFetch("/api/keys?provider=" + encodeURIComponent(provider), { method: "DELETE" });
  if (!res.ok) { return false; }
  const data = await safeJson(res); appKeyStatus = data.keys || {};
  keyReplaceMode = false; onboardingReplaceMode = false;
  keyVerifyState[provider] = { ok: false, status: "removed", models_count: 0 };
  if (apiKeyEl) { apiKeyEl.value = ""; }
  syncKeyStatusUI();
  await loadModels();
  return true;
}

function bindSecretToggle(inputId, btnId) {
  const btn = document.getElementById(btnId), inp = document.getElementById(inputId);
  if (!btn || !inp) { return; }
  setSecretVisibility(inputId, btnId, false);
  btn.addEventListener("click", function () { setSecretVisibility(inputId, btnId, inp.type === "password"); inp.focus(); });
}

function bindApiKeyControls() {
  bindSecretToggle("api-key", "toggle-api-key-visibility");
  bindSecretToggle("onboarding-api-key", "toggle-onboarding-key-visibility");
  bindSecretToggle("tts-api-key", "toggle-tts-key-visibility");
  bindSecretToggle("web-search-ollama-key", "toggle-ollama-web-key-visibility");
  const testBtn = document.getElementById("test-api-key-btn"), repBtn = document.getElementById("replace-api-key-btn"), canBtn = document.getElementById("cancel-replace-key-btn"), remBtn = document.getElementById("remove-api-key-btn");
  if (testBtn) { testBtn.addEventListener("click", function () { verifyAppApiKey(providerEl.value); }); }
  if (repBtn) { repBtn.addEventListener("click", function () { keyReplaceMode = true; syncKeyStatusUI(); if (apiKeyEl) { apiKeyEl.focus(); } }); }
  if (canBtn) { canBtn.addEventListener("click", function () { keyReplaceMode = false; if (apiKeyEl) { apiKeyEl.value = ""; } setSecretVisibility("api-key", "toggle-api-key-visibility", false); syncKeyStatusUI(); }); }
  if (remBtn) { remBtn.addEventListener("click", function () { removeAppApiKey(providerEl.value); }); }
  if (apiKeyEl) { apiKeyEl.addEventListener("keydown", async function (e) { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); if (await saveAppApiKey(providerEl.value, apiKeyEl.value, apiKeyEl)) { await loadModels(); } } }); }
  const obRep = document.getElementById("onboarding-replace-key-btn"), obCan = document.getElementById("onboarding-cancel-replace-btn"), obRem = document.getElementById("onboarding-remove-key-btn"), obIn = document.getElementById("onboarding-api-key");
  if (obRep) { obRep.addEventListener("click", function () { onboardingReplaceMode = true; syncOnboardingKeyUI(); if (obIn) { obIn.focus(); } }); }
  if (obCan) { obCan.addEventListener("click", function () { onboardingReplaceMode = false; if (obIn) { obIn.value = ""; } setSecretVisibility("onboarding-api-key", "toggle-onboarding-key-visibility", false); syncOnboardingKeyUI(); }); }
  if (obRem) { obRem.addEventListener("click", function () { removeAppApiKey(document.getElementById("onboarding-provider").value); }); }
  if (obIn) { obIn.addEventListener("keydown", async function (e) { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); if (await saveAppApiKey(document.getElementById("onboarding-provider").value, obIn.value, obIn)) { await loadModels(); } } }); }
}
"""
