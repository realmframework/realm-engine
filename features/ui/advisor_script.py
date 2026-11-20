"""Explicit, plain-language run modes preserve privacy policy and retrieval choices."""

ADVISOR_SCRIPT: str = r"""
let appliedRunMode = null;
function showHardwareAdvice(status) {
  const ram = Number(status.ram_gb || 0), advice = status.ram_tier_advice || "RAM could not be detected. Search and anonymization are ready without AI setup.";
  document.querySelectorAll("[data-ram-detected]").forEach(el => { el.textContent = ram ? "Detected " + ram + " GB RAM on this computer" : "RAM could not be detected on this computer"; });
  document.getElementById("local-model-recommendation").innerHTML = modeCopy(ram >= 16 ? "Recommended download for this computer: about 6 GB including the search helper." : "Recommended smaller download: about 2 GB including the search helper.", "Recommended: " + (status.recommended_local_model || (ram >= 16 ? "qwen3:8b" : "qwen2.5:3b")) + " + nomic-embed-text:v1.5");
  document.querySelectorAll("[data-ram-advice]").forEach(el => { el.innerHTML = modeCopy(!ram ? "We could not check this computer’s memory. Search and privacy tools are ready now." : ram < 16 ? "Start with the smaller recommended AI. It leaves more room for your other apps." : "This computer can try the recommended local AI. Smaller models usually respond faster.", advice); });
}
function syncRunMode() {
  const mode = workspaceConfig.run_mode === "cloud" && localOnly() ? "local" : workspaceConfig.run_mode || "local";
  for (const prefix of ["settings", "onboarding"]) {
    const radio = document.getElementById(prefix + "-mode-" + mode); if (radio) { radio.checked = true; }
  }
  if (mode !== appliedRunMode) {
    askTutorToggle.checked = mode !== "search";
    ragConfig.retrieval_mode = mode === "search" ? "lexical" : "hybrid";
    if (mode === "search") { document.getElementById("tts-model").value = "disabled"; }
    appliedRunMode = mode; syncRagStudioUI();
  }
  modelEl.disabled = mode === "search"; askTutorToggle.disabled = mode === "search";
  for (const id of ["settings-model", "onboarding-model"]) { const m = document.getElementById(id); if (m) { m.disabled = modelEl.disabled; } }
}
async function applySelectedMode(prefix) {
  const radio = document.querySelector('input[name="' + prefix + '_run_mode"]:checked'), mode = radio ? radio.value : "local";
  const status = document.getElementById(prefix + "-mode-status"), version = areaVersion;
  const selectedProvider = prefix === "onboarding" ? document.getElementById("onboarding-provider").value : providerEl.value;
  status.textContent = "Applying your choice…";
  try {
    const response = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.assign({}, workspaceConfig, { run_mode: mode, strict_local_only: mode !== "cloud" })) });
    const data = await response.json();
    if (version !== areaVersion) { return false; }
    if (!response.ok) { throw new Error(data.detail || "Mode could not be saved."); }
    abortActiveRequest(); stopActiveAudio();
    if (activeRecognition) { activeRecognition.abort(); activeRecognition = null; }
    applyWorkspacePayload(data);
    providerEl.value = mode === "cloud" ? (selectedProvider === "ollama" ? "openai" : selectedProvider) : "ollama";
    document.getElementById("onboarding-provider").value = providerEl.value;
    apiKeyEl.value = ""; syncKeyStatusUI();
    syncProviderPrivacyUI(providerEl.value, "settings-privacy-notice", "settings-api-key-group");
    syncProviderPrivacyUI(providerEl.value, "onboarding-privacy-notice", "onboarding-api-key-group");
    await loadModels(); await refreshBudget();
    if (version !== areaVersion) { return false; }
    status.textContent = mode === "search" ? "Keyword search and redaction are ready. No AI setup needed." : mode === "cloud" ? "Local Ollama & Cloud APIs enabled. Click any provider below to save keys and switch models anytime." : "Local-only lock enabled. Choose an installed Ollama model below.";
    return true;
  } catch (error) { if (version === areaVersion) { status.textContent = error.message || "Mode could not be saved."; } return false; }
}
function bindRunModes() {
  for (const prefix of ["settings", "onboarding"]) {
    const form = document.getElementById(prefix + "-run-form"); if (!form) { continue; }
    form.addEventListener("submit", async function (event) {
      event.preventDefault(); const button = event.submitter; if (button) { button.disabled = true; }
      try { await applySelectedMode(prefix); } finally { if (button) { button.disabled = false; } }
    });
    form.querySelectorAll('input[name="' + prefix + '_run_mode"]').forEach(function (radio) {
      radio.addEventListener("change", function () { applySelectedMode(prefix); });
    });
  }
}
"""
