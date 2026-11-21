"""Live reservation meter, explicit limit saves and narrowly scoped browser-key removal."""

BUDGET_SCRIPT: str = r"""
let budgetRefreshId = 0;
async function refreshBudget() {
  const version = areaVersion, operation = ++budgetRefreshId;
  try {
    const response = await areaFetch("/api/budget"), data = await safeJson(response);
    if (version !== areaVersion || operation !== budgetRefreshId) { return; }
    if (!response.ok || data.state_error) { throw new Error(data.state_error || data.detail || "Budget meter could not be loaded."); }
    const rawCost = Number(data.estimated_cost_usd || 0);
    document.getElementById("budget-meter").textContent = t("budget_meter_fmt", { req: data.cloud_requests_today, reqLim: data.daily_cloud_request_limit, cost: (rawCost > 0 && rawCost < 0.01 ? rawCost.toFixed(4) : rawCost.toFixed(2)), costLim: Number(data.daily_budget_usd_limit).toFixed(2) });
    document.getElementById("budget-details").textContent = Number(data.estimated_tokens_today).toLocaleString() + " reserved token estimate · " + data.requests_last_minute + " / 12 requests in the last minute · " + data.date_str + " (UTC)";
  } catch (error) { if (version === areaVersion && operation === budgetRefreshId) { document.getElementById("budget-meter").textContent = error.message; } }
}
async function saveBudgetLimits(event) {
  event.preventDefault(); const form = event.currentTarget, button = event.submitter;
  if (!form.reportValidity()) { return; }
  const version = areaVersion, status = document.getElementById("budget-action-status"); if (button) { button.disabled = true; }
  try {
    const payload = Object.assign({}, workspaceConfig, { daily_cloud_request_limit: Number(document.getElementById("daily-cloud-request-limit").value), daily_budget_usd_limit: Number(document.getElementById("daily-budget-usd-limit").value) });
    const response = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }), data = await safeJson(response);
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Budget limits could not be saved."); }
    applyWorkspacePayload(data); await refreshBudget(); status.textContent = "Budget limits saved. A zero limit blocks cloud AI.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { if (button) { button.disabled = false; } }
}
async function resetBudgetCounter() {
  const version = areaVersion, status = document.getElementById("budget-action-status"), button = document.getElementById("reset-budget-btn");
  if (button) { button.disabled = true; }
  try {
    const response = await areaFetch("/api/budget/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: true }) }), data = await safeJson(response);
    if (version !== areaVersion) { return; }
    if (!response.ok || data.state_error) { throw new Error(data.detail || data.state_error || "Counter reset failed."); }
    await refreshBudget(); status.textContent = "Daily counter reset. More cloud requests are permitted within your cap; the 12/minute limit is unchanged.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { if (button) { button.disabled = false; } }
}
async function forgetSavedKeys() {
  abortActiveRequest(); stopActiveAudio();
  try { for (const key of Object.keys(localStorage)) { if (key.startsWith("tutor_api_key_")) { localStorage.removeItem(key); } } } catch (_e) {}
  for (const id of ["api-key", "onboarding-api-key", "tts-api-key"]) { const el = document.getElementById(id); if (el) { el.value = ""; } }
  try {
    const res = await areaFetch("/api/keys", { method: "DELETE" });
    if (res.ok) { const data = await safeJson(res); appKeyStatus = data.keys || {}; if (typeof keyVerifyState === "object") { keyVerifyState = {}; } keyReplaceMode = false; onboardingReplaceMode = false; syncKeyStatusUI(); }
  } catch (_e) {}
  document.getElementById("budget-action-status").textContent = "Saved API keys removed from app storage. Your other settings are preserved.";
}
function bindBudgetControls() {
  document.getElementById("budget-limits-form").addEventListener("submit", saveBudgetLimits);
  document.getElementById("reset-budget-btn").addEventListener("click", resetBudgetCounter);
  document.getElementById("forget-api-key-btn").addEventListener("click", forgetSavedKeys);
  setInterval(function () { if (settingsModal.open) { refreshBudget(); } }, 15000);
}
"""
