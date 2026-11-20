"""Explicit privacy policy controls and cloud/browser speech admission."""

PRIVACY_SCRIPT: str = r"""
function localOnly() { return workspaceConfig.strict_local_only !== false; }
function cloudSpeech(model) { return /^(openai|elevenlabs)|cloud/i.test(model); }
function applyLocalPolicy() {
  const locked = localOnly();
  document.getElementById("governance-local-only").checked = locked;
  for (const id of ["provider", "onboarding-provider"]) {
    const select = document.getElementById(id);
    for (const option of select.options) { option.disabled = locked && option.value !== "ollama"; }
    if (locked && select.value !== "ollama") { select.value = "ollama"; }
  }
  const speech = document.getElementById("tts-model");
  for (const option of speech.options) { option.disabled = locked && cloudSpeech(option.value); }
  if (locked && cloudSpeech(speech.value)) { speech.value = "disabled"; stopActiveAudio(); }
  micBtn.disabled = locked;
  micBtn.title = locked ? "Cloud-backed browser dictation blocked. Local Whisper is available through /api/audio/transcribe." : "Voice dictation (browser service)";
  document.getElementById("governance-lock-state").textContent = locked ? "AI stays on this computer · external AI services are blocked" : "External AI services are allowed · review your provider settings";
  syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group");
  syncProviderPrivacyUI(document.getElementById("onboarding-provider").value, "onboarding-privacy-notice", "onboarding-api-key-group");
}
async function saveGovernancePolicy(event) {
  event.preventDefault();
  const button = event.submitter, version = areaVersion, status = document.getElementById("compliance-status");
  button.disabled = true;
  try {
    const enabled = document.getElementById("governance-local-only").checked;
    const response = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { strict_local_only: enabled })) });
    const data = await response.json();
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Policy could not be saved."); }
    abortActiveRequest(); stopActiveAudio();
    if (activeRecognition) { activeRecognition.abort(); activeRecognition = null; }
    applyWorkspacePayload(data); await loadModels(); invalidateAudit();
    status.textContent = "Privacy policy saved. Run a new audit for current evidence.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { button.disabled = false; }
}
document.getElementById("governance-lock-form").addEventListener("submit", saveGovernancePolicy);
"""
