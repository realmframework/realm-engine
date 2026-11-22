"""Explicit privacy policy controls and cloud/browser speech admission."""

PRIVACY_SCRIPT: str = r"""
function localOnly() { return workspaceConfig.strict_local_only !== false; }
function cloudSpeech(model) { return /^(openai|elevenlabs)|cloud/i.test(model); }
function applyLocalPolicy() {
  const locked = localOnly();
  document.getElementById("governance-local-only").checked = locked;
  for (const id of ["provider", "onboarding-provider"]) {
    const select = document.getElementById(id);
    for (const option of select.options) { option.disabled = locked && !isLocalProvider(option.value); }
    if (locked && !isLocalProvider(select.value)) { select.value = (typeof isBuiltinInstalled === "function" && isBuiltinInstalled()) ? "builtin" : "ollama"; }
  }
  const speech = document.getElementById("tts-model");
  for (const option of speech.options) { option.disabled = locked && cloudSpeech(option.value); }
  if (locked && cloudSpeech(speech.value)) { speech.value = "disabled"; stopActiveAudio(); }
  micBtn.disabled = locked;
  micBtn.title = locked ? "Cloud-backed browser dictation blocked. Local Whisper is available through /api/audio/transcribe." : "Voice dictation (browser service)";
  document.getElementById("governance-lock-state").textContent = locked ? t("priv_lock_on") : t("priv_lock_off");
  const cloudBtn = document.getElementById("toggle-cloud-access-btn"), cloudBanner = document.getElementById("cloud-access-banner");
  if (cloudBtn) { cloudBtn.textContent = locked ? t("allow_cloud") : t("lock_local"); }
  if (cloudBanner) { cloudBanner.innerHTML = locked ? t("cloud_banner_locked") : t("cloud_banner_open"); }
  if (typeof renderProviderPills === "function") { renderProviderPills(); }
  if (typeof syncWebSearchUI === "function") { syncWebSearchUI(workspaceConfig); }
  syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group");
  syncProviderPrivacyUI(document.getElementById("onboarding-provider").value, "onboarding-privacy-notice", "onboarding-api-key-group");
}
async function setCloudAccess(allowCloud) {
  const version = areaVersion;
  try {
    const response = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { strict_local_only: !allowCloud, run_mode: allowCloud ? "cloud" : "local" })) });
    const data = await safeJson(response);
    if (!response.ok || version !== areaVersion) { if (!response.ok && version === areaVersion) { areaStatus(data.detail || t("st_policy_err")); } return; }
    abortActiveRequest(); stopActiveAudio();
    if (activeRecognition) { activeRecognition.abort(); activeRecognition = null; }
    applyWorkspacePayload(data);
    if (allowCloud && isLocalProvider(providerEl.value)) { providerEl.value = "openai"; document.getElementById("onboarding-provider").value = "openai"; }
    syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group");
    syncProviderPrivacyUI(document.getElementById("onboarding-provider").value, "onboarding-privacy-notice", "onboarding-api-key-group");
    syncKeyStatusUI(); await loadModels(); await refreshBudget(); invalidateAudit();
  } catch (error) { if (version === areaVersion) { areaStatus(error.message || t("st_policy_err")); } }
}
async function saveGovernancePolicy(event) {
  event.preventDefault();
  const button = event.submitter, version = areaVersion, status = document.getElementById("compliance-status");
  if (button) { button.disabled = true; }
  try {
    const enabled = document.getElementById("governance-local-only").checked;
    const response = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { strict_local_only: enabled })) });
    const data = await safeJson(response);
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Policy could not be saved."); }
    abortActiveRequest(); stopActiveAudio();
    if (activeRecognition) { activeRecognition.abort(); activeRecognition = null; }
    applyWorkspacePayload(data); await loadModels(); invalidateAudit();
    status.textContent = "Privacy policy saved. Run a new audit for current evidence.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { if (button) { button.disabled = false; } }
}
document.getElementById("governance-lock-form").addEventListener("submit", saveGovernancePolicy);
"""
