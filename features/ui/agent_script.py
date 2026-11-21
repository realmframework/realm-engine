"""Client-side REALM Agent Team (persona.md roster, per-chat memory, editor & palette sync)."""

AGENT_SCRIPT: str = r"""
let agentTeam = [], defaultAgentId = "saga", activeAgentId = "saga", syncAgentPalette = true, agentEditorRawMode = false, agentModelOp = 0;
function activeAgentObj() {
  return agentTeam.find(a => a.id === activeAgentId) || agentTeam[0] || null;
}
function agentNameById(agentId) {
  if (agentId && Array.isArray(agentTeam)) {
    const found = agentTeam.find(a => a.id === agentId);
    if (found && found.name) { return found.name; }
  }
  return activeAgentName();
}
function isInsideChat() {
  return Boolean(currentChatId && (currentTurns.length || (typeof activeAttachedNotes !== "undefined" && activeAttachedNotes.length)));
}
function turnAuthorName(turn) {
  if (turn && turn.agent_name) { return turn.agent_name; }
  if (turn && turn.agent_id && Array.isArray(agentTeam)) {
    const found = agentTeam.find(a => a.id === turn.agent_id);
    if (found && found.name) { return found.name; }
  }
  return (workspaceConfig && workspaceConfig.agent_name) || "Saga";
}
function turnAuthorColor(turn) {
  if (!syncAgentPalette || !turn || !Array.isArray(agentTeam) || !agentTeam.length) { return ""; }
  const ag = (turn.agent_id && agentTeam.find(a => a.id === turn.agent_id))
    || (turn.agent_name && agentTeam.find(a => String(a.name || "").toLowerCase() === String(turn.agent_name).toLowerCase()));
  return (ag && ag.palette) ? (paletteColorsFor(ag.palette).accent || "") : "";
}
function paletteColorsFor(paletteId) {
  const presets = typeof THEME_PRESETS !== "undefined" ? THEME_PRESETS : [];
  return presets.find(p => p.id === paletteId) || presets[0] || { accent: "#4BB8E8", glow: "#6366F1" };
}
function applyPaletteForAgent(agent, persist) {
  if (!syncAgentPalette || !agent || typeof applyThemeTokens !== "function") { return; }
  const pal = paletteColorsFor(agent.palette);
  const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
  applyThemeTokens(mode, pal.accent, pal.glow, Boolean(persist));
  if (persist) {
    if (typeof workspaceConfig === "object" && workspaceConfig) { workspaceConfig.theme_accent = pal.accent; workspaceConfig.theme_glow = pal.glow; }
    if (typeof persistThemeWorkspace === "function") { persistThemeWorkspace(mode, pal.accent, pal.glow); }
  }
}
function syncActiveAgentBadge() {
  const ag = activeAgentObj(), name = (ag && ag.name) || (typeof activeAgentLabel !== "undefined" && activeAgentLabel) || "Saga";
  const badge = document.getElementById("sidebar-agent-badge");
  if (badge) { badge.textContent = name; }
  for (const id of ["agent-sync-palette-toggle", "onboarding-sync-agent-palette"]) {
    const chk = document.getElementById(id); if (chk) { chk.checked = Boolean(syncAgentPalette); }
  }
}
function resolveSessionAgentId(session) {
  if (!session || !agentTeam.length) { return defaultAgentId; }
  const turns = Array.isArray(session.turns) ? session.turns : [];
  let chatAgentId = session.last_agent_id || "";
  if (!chatAgentId) {
    for (let i = turns.length - 1; i >= 0; i -= 1) {
      if (turns[i] && turns[i].agent_id) { chatAgentId = turns[i].agent_id; break; }
    }
  }
  if (chatAgentId && agentTeam.some(a => a.id === chatAgentId)) { return chatAgentId; }
  if (turns.length && agentTeam.some(a => a.id === "saga")) { return "saga"; }
  return defaultAgentId;
}
function adoptChatAgent(session) {
  if (!session || !agentTeam.length) { return; }
  const targetId = resolveSessionAgentId(session);
  const changed = targetId !== activeAgentId;
  activeAgentId = targetId;
  syncActiveAgentBadge(); renderAgentRoster();
  const chosen = activeAgentObj();
  applyPaletteForAgent(chosen, false);
  if (changed && chosen && typeof showToast === "function") {
    showToast(t("toast_resumed_agent", { name: chosen.name, role: chosen.role }));
  }
}
function restoreDefaultAgent() {
  if (activeAgentId === defaultAgentId) { return; }
  activeAgentId = defaultAgentId;
  syncActiveAgentBadge(); renderAgentRoster();
  applyPaletteForAgent(activeAgentObj(), false);
}
async function loadAgentTeam() {
  try {
    const res = await fetch("/api/agents");
    if (!res.ok) { return; }
    const d = await safeJson(res);
    agentTeam = Array.isArray(d.agents) ? d.agents : [];
    defaultAgentId = d.active_agent || "saga";
    if (!currentChatId || !agentTeam.some(a => a.id === activeAgentId)) { activeAgentId = defaultAgentId; }
    syncAgentPalette = d.sync_agent_palette !== false;
    const restoreBtn = document.getElementById("restore-agents-btn");
    if (restoreBtn) { restoreBtn.hidden = !d.has_missing_defaults; }
    syncActiveAgentBadge();
    renderAgentRoster();
  } catch (_e) {}
}
function setAgentStudioTab(tab) {
  const isEd = tab === "editor", rBtn = document.getElementById("agent-tab-roster"), eBtn = document.getElementById("agent-tab-editor");
  const rPane = document.getElementById("agent-roster-pane"), eForm = document.getElementById("agent-editor-form");
  if (rBtn) { rBtn.setAttribute("aria-selected", String(!isEd)); rBtn.tabIndex = isEd ? -1 : 0; rBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (!isEd ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (eBtn) { eBtn.setAttribute("aria-selected", String(isEd)); eBtn.tabIndex = isEd ? 0 : -1; eBtn.className = "px-3.5 py-1.5 rounded-lg text-xs font-medium transition " + (isEd ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (rPane) { rPane.hidden = isEd; }
  if (eForm) { eForm.hidden = !isEd; }
}
function buildRawMarkdownFromGuided() {
  const name = document.getElementById("agent-ed-name").value.trim() || "Custom Agent";
  const id = document.getElementById("agent-edit-id").value.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "agent";
  const role = document.getElementById("agent-ed-role").value.trim() || "Specialist";
  const tagline = document.getElementById("agent-ed-tagline").value.trim();
  const palette = document.getElementById("agent-ed-palette").value || "realm";
  const fmt = document.getElementById("agent-ed-format").value || "";
  const prov = (document.getElementById("agent-ed-provider") && document.getElementById("agent-ed-provider").value) || "";
  const mdl = prov && document.getElementById("agent-ed-model") ? (document.getElementById("agent-ed-model").value || "") : "";
  const temp = document.getElementById("agent-ed-temp").value || "0.2";
  const body = document.getElementById("agent-ed-instructions").value.trim();
  return "---\nid: " + id + "\nname: " + name + "\nrole: " + role + "\ntagline: " + tagline + "\npalette: " + palette + "\ndefault_format: " + fmt + "\nmodel_provider: " + prov + "\nmodel_name: " + mdl + "\ntemperature: " + temp + "\n---\n\n" + body + "\n";
}
function setAgentEditorMode(raw) {
  agentEditorRawMode = Boolean(raw);
  const gBtn = document.getElementById("agent-mode-guided-btn"), rBtn = document.getElementById("agent-mode-raw-btn");
  const gPane = document.getElementById("agent-guided-pane"), rPane = document.getElementById("agent-raw-pane");
  if (agentEditorRawMode) {
    const rawEl = document.getElementById("agent-ed-raw");
    if (rawEl && (!rawEl.value.trim() || rawEl.dataset.synced !== "1")) { rawEl.value = buildRawMarkdownFromGuided(); }
  }
  if (gBtn) { gBtn.setAttribute("aria-pressed", String(!agentEditorRawMode)); gBtn.className = "px-2.5 py-1 rounded-md text-xs font-medium transition " + (!agentEditorRawMode ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (rBtn) { rBtn.setAttribute("aria-pressed", String(agentEditorRawMode)); rBtn.className = "px-2.5 py-1 rounded-md text-xs font-medium transition " + (agentEditorRawMode ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"); }
  if (gPane) { gPane.hidden = agentEditorRawMode; }
  if (rPane) { rPane.hidden = !agentEditorRawMode; }
}
async function syncAgentModelChoices(selectedProvider, selectedModel) {
  const mdlSel = document.getElementById("agent-ed-model");
  if (!mdlSel) { return; }
  const op = ++agentModelOp;
  if (!selectedProvider) {
    mdlSel.innerHTML = "<option value=''>" + escapeHtml(t("agents_model_follow")) + "</option>";
    mdlSel.value = ""; mdlSel.disabled = true; return;
  }
  mdlSel.disabled = false;
  mdlSel.innerHTML = "<option value=''>Loading…</option>";
  let list = [];
  try {
    const res = await areaFetch("/api/models?provider=" + encodeURIComponent(selectedProvider));
    if (res.ok) { const d = await safeJson(res); list = (d.chat_models || d.models || []).filter(m => !NON_CHAT_RE.test(m)); }
  } catch (_e) {}
  if (op !== agentModelOp) { return; }
  if (selectedModel && !list.includes(selectedModel)) { list = [selectedModel].concat(list); }
  const defMdl = (typeof PROVIDER_DEFAULTS !== "undefined" && PROVIDER_DEFAULTS[selectedProvider]) || "";
  if (!list.length && defMdl) { list = [defMdl]; }
  mdlSel.innerHTML = list.map(m => "<option value='" + escapeHtml(m) + "'>" + escapeHtml(m) + "</option>").join("");
  mdlSel.value = selectedModel && list.includes(selectedModel) ? selectedModel : (list[0] || "");
}
function populateAgentEditorSelects() {
  const palSel = document.getElementById("agent-ed-palette"), fmtSel = document.getElementById("agent-ed-format"), provSel = document.getElementById("agent-ed-provider");
  if (palSel && !palSel.options.length && typeof THEME_PRESETS !== "undefined") {
    palSel.innerHTML = THEME_PRESETS.map(p => "<option value='" + escapeHtml(p.id) + "'>" + escapeHtml(p.name) + "</option>").join("");
  }
  if (fmtSel) {
    const fmts = typeof availableFormats !== "undefined" ? availableFormats : [], cur = fmtSel.value;
    fmtSel.innerHTML = "<option value=''>" + escapeHtml(t("agents_none_fmt")) + "</option>" + fmts.map(f => "<option value='" + escapeHtml(f.id) + "'>" + escapeHtml(f.name) + "</option>").join("");
    if (cur) { fmtSel.value = cur; }
  }
  if (provSel && typeof PROVIDER_ORDER !== "undefined") {
    const curP = provSel.value;
    provSel.innerHTML = "<option value=''>" + escapeHtml(t("agents_model_follow")) + "</option>"
      + PROVIDER_ORDER.map(p => "<option value='" + escapeHtml(p) + "'>" + escapeHtml((PROVIDER_LABELS && PROVIDER_LABELS[p]) || p) + "</option>").join("");
    if (curP) { provSel.value = curP; }
  }
}
function openAgentEditor(agent) {
  populateAgentEditorSelects();
  const isNew = !agent, heading = document.getElementById("agent-editor-heading"), status = document.getElementById("agent-ed-status");
  if (heading) { heading.textContent = isNew ? "Create Custom Agent (persona.md)" : ("Editing " + agent.name + " · agents/" + agent.id + "/persona.md"); }
  if (status) { status.textContent = ""; }
  document.getElementById("agent-edit-id").value = isNew ? "" : agent.id;
  document.getElementById("agent-ed-name").value = isNew ? "" : agent.name;
  document.getElementById("agent-ed-role").value = isNew ? "" : (agent.role || "");
  document.getElementById("agent-ed-tagline").value = isNew ? "" : (agent.tagline || "");
  document.getElementById("agent-ed-palette").value = isNew ? "realm" : (agent.palette || "realm");
  document.getElementById("agent-ed-format").value = isNew ? "" : (agent.default_format || "");
  const provSel = document.getElementById("agent-ed-provider");
  const pinProv = isNew ? "" : (agent.model_provider || ""), pinMdl = isNew ? "" : (agent.model_name || "");
  if (provSel) { provSel.value = pinProv; }
  syncAgentModelChoices(pinProv, pinMdl);
  document.getElementById("agent-ed-temp").value = isNew ? "0.2" : String(agent.temperature ?? 0.2);
  document.getElementById("agent-ed-instructions").value = isNew ? "## Analytical Lens\n\n\n## Signature Moves\n- \n\n## Communication Style\n\n\n## Boundaries\nNever " : (agent.instructions || "");
  const rawEl = document.getElementById("agent-ed-raw");
  if (rawEl) { rawEl.value = isNew ? "" : (agent.raw_markdown || ""); rawEl.dataset.synced = isNew ? "0" : "1"; }
  setAgentEditorMode(false); setAgentStudioTab("editor");
}
function renderAgentRoster() {
  const grid = document.getElementById("agent-cards-grid");
  if (!grid) { return; }
  const fmts = typeof availableFormats !== "undefined" ? availableFormats : [];
  const inChat = isInsideChat();
  grid.innerHTML = agentTeam.map(function (a) {
    const isAct = a.id === activeAgentId, isDef = a.id === defaultAgentId, pal = paletteColorsFor(a.palette);
    const pairedFmt = a.default_format ? (fmts.find(f => f.id === a.default_format) || { name: a.default_format }).name : "";
    const tagChip = isAct ? "<span class='px-2 py-0.5 rounded-full bg-[#4BB8E8]/15 text-[#4BB8E8] text-2xs font-mono'>" + escapeHtml(inChat ? t("agents_tag_chat") : t("agents_btn_active")) + "</span>" : (isDef ? "<span class='px-2 py-0.5 rounded-full bg-white/[0.06] text-[#A0B0C8] text-2xs font-mono'>" + escapeHtml(t("agents_tag_default")) + "</span>" : (a.customized ? "<span class='px-2 py-0.5 rounded-full bg-white/[0.06] text-[#A0B0C8] text-2xs font-mono'>" + escapeHtml(t("agents_tag_edited")) + "</span>" : (!a.builtin ? "<span class='px-2 py-0.5 rounded-full bg-white/[0.06] text-[#A0B0C8] text-2xs font-mono'>" + escapeHtml(t("agents_tag_custom")) + "</span>" : "")));
    const resetBtn = a.builtin && a.customized ? "<button type='button' data-reset-agent='" + escapeHtml(a.id) + "' title='Restore default persona.md' class='px-2 py-1.5 rounded-lg border border-white/10 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("agents_btn_reset")) + "</button>" : "";
    const delBtn = agentTeam.length > 1 ? "<button type='button' data-del-agent='" + escapeHtml(a.id) + "' title='Remove agent' aria-label='Remove " + escapeHtml(a.name) + "' class='px-1.5 py-1 text-xs text-[#738196] hover:text-[#EF4444] transition'>✕</button>" : "";
    return "<article class='rounded-xl bg-[#04060F] border " + (isAct ? "border-[#4BB8E8]" : "border-white/10") + " p-3.5 flex flex-col gap-2.5'>"
      + "<div class='flex items-start justify-between gap-2'><div class='flex items-center gap-2 min-w-0'><span aria-hidden='true' class='w-3 h-3 rounded-full shrink-0' style='background:linear-gradient(135deg," + pal.accent + "," + pal.glow + ")'></span><div class='min-w-0'><h3 class='text-sm font-semibold text-[#EEF2F8] truncate'>" + escapeHtml(a.name) + "</h3><div class='text-xs font-mono text-[#4BB8E8] truncate'>" + escapeHtml(a.role) + "</div></div></div><div class='flex items-center gap-1 shrink-0'>" + tagChip + delBtn + "</div></div>"
      + (a.tagline ? "<p class='text-xs text-[#A0B0C8] leading-relaxed'>" + escapeHtml(a.tagline) + "</p>" : "")
      + "<div class='text-xs font-mono text-[#738196] truncate'>persona.md" + (a.model_name ? " · " + escapeHtml(a.model_name) : "") + " · temp " + Number(a.temperature ?? 0.2).toFixed(2) + (pairedFmt ? " · " + escapeHtml(pairedFmt) : "") + "</div>"
      + "<div class='flex items-center gap-1.5 mt-auto pt-2 border-t border-white/[0.06]'>"
      + "<button type='button' data-select-agent='" + escapeHtml(a.id) + "' class='flex-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition " + (isAct ? "bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-[#4BB8E8]" : "bg-[#4BB8E8] text-[#04060F] hover:brightness-110") + "'>" + escapeHtml(isAct ? t("agents_btn_active") : (inChat ? t("agents_btn_switch") : t("agents_btn_use"))) + "</button>"
      + "<button type='button' data-edit-agent='" + escapeHtml(a.id) + "' class='px-2.5 py-1.5 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("agents_btn_edit")) + "</button>"
      + resetBtn + "</div></article>";
  }).join("");
  grid.querySelectorAll("[data-select-agent]").forEach(b => b.addEventListener("click", () => selectAgentUI(b.dataset.selectAgent)));
  grid.querySelectorAll("[data-edit-agent]").forEach(b => b.addEventListener("click", () => { const a = agentTeam.find(x => x.id === b.dataset.editAgent); if (a) { openAgentEditor(a); } }));
  grid.querySelectorAll("[data-reset-agent]").forEach(b => b.addEventListener("click", () => resetAgentUI(b.dataset.resetAgent)));
  grid.querySelectorAll("[data-del-agent]").forEach(b => b.addEventListener("click", () => deleteAgentUI(b.dataset.delAgent)));
}
async function openAgentStudio(tab) {
  if (!agentTeam.length) { await loadAgentTeam(); }
  if (typeof availableFormats !== "undefined" && !availableFormats.length && typeof loadOutputFormats === "function") { await loadOutputFormats(); }
  renderAgentRoster();
  if (tab === "editor") { openAgentEditor(null); } else { setAgentStudioTab("roster"); }
  const modal = document.getElementById("agent-studio-modal");
  if (modal && !modal.open) { modal.showModal(); }
}
async function selectAgentUI(agentId) {
  const inOpenChat = isInsideChat();
  try {
    if (!inOpenChat) {
      const res = await fetch("/api/agents/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_id: agentId }) });
      const d = await safeJson(res);
      if (!res.ok) { throw new Error(d.detail || "Could not switch agent."); }
      agentTeam = d.agents || agentTeam; defaultAgentId = d.active_agent || agentId; syncAgentPalette = d.sync_agent_palette !== false;
      if (d.config) { workspaceConfig = d.config; }
    } else if (currentChatId) {
      await areaFetch("/api/chats/" + encodeURIComponent(currentChatId) + "/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent_id: agentId, free_chat: Boolean(typeof freeChatMode !== "undefined" && freeChatMode) }) }).catch(() => {});
    }
    activeAgentId = agentId;
    syncActiveAgentBadge(); renderAgentRoster();
    const chosen = activeAgentObj();
    applyPaletteForAgent(chosen, !inOpenChat);
    const modal = document.getElementById("agent-studio-modal"); if (modal && modal.open) { modal.close(); }
    if (chosen) { showToast(t(inOpenChat ? "toast_next_agent" : "toast_default_agent", { name: chosen.name, role: chosen.role })); }
    if (typeof refreshContextUsage === "function" && currentChatId) { refreshContextUsage(); }
  } catch (err) { showToast(err.message || t("err_switch_agent")); }
}
async function saveAgentUI(event) {
  event.preventDefault();
  const status = document.getElementById("agent-ed-status");
  const edProv = document.getElementById("agent-ed-provider"), edMdl = document.getElementById("agent-ed-model");
  const payload = agentEditorRawMode
    ? { id: document.getElementById("agent-edit-id").value.trim(), name: document.getElementById("agent-ed-name").value.trim(), raw_markdown: document.getElementById("agent-ed-raw").value }
    : { id: document.getElementById("agent-edit-id").value.trim(), name: document.getElementById("agent-ed-name").value.trim(), role: document.getElementById("agent-ed-role").value.trim(), tagline: document.getElementById("agent-ed-tagline").value.trim(), palette: document.getElementById("agent-ed-palette").value, default_format: document.getElementById("agent-ed-format").value, model_provider: edProv ? edProv.value : "", model_name: edProv && edProv.value && edMdl ? edMdl.value : "", temperature: Number(document.getElementById("agent-ed-temp").value || 0.2), instructions: document.getElementById("agent-ed-instructions").value };
  try {
    const res = await fetch("/api/agents", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const d = await safeJson(res);
    if (!res.ok) { throw new Error(d.detail || t("err_switch_agent")); }
    agentTeam = d.agents || agentTeam; defaultAgentId = d.active_agent || defaultAgentId;
    if (d.agent && d.agent.id === "saga" && typeof syncAgentNameUI === "function") { syncAgentNameUI(d.agent.name); }
    syncActiveAgentBadge(); renderAgentRoster(); setAgentStudioTab("roster");
    showToast(t("toast_saved_agent", { name: (d.agent && d.agent.name) || payload.name || "Agent" }));
  } catch (err) { if (status) { status.textContent = err.message; } }
}
async function deleteAgentUI(agentId) {
  const ag = agentTeam.find(a => a.id === agentId);
  if (!await confirmDeletion(t("cf_rm_agent_t"), t("cf_rm_agent_m", { name: (ag && ag.name) || agentId }), t("cf_rm_agent_btn"))) { return; }
  try {
    const res = await fetch("/api/agents/" + encodeURIComponent(agentId), { method: "DELETE" });
    const d = await safeJson(res);
    if (!res.ok) { showToast(d.detail || t("err_remove_agent")); return; }
    agentTeam = d.agents || []; defaultAgentId = d.active_agent || "saga";
    if (!agentTeam.some(a => a.id === activeAgentId)) { activeAgentId = defaultAgentId; }
    const rBtn = document.getElementById("restore-agents-btn"); if (rBtn) { rBtn.hidden = !d.has_missing_defaults; }
    syncActiveAgentBadge(); renderAgentRoster();
  } catch (err) { showToast(err.message || t("err_remove_agent")); }
}
async function resetAgentUI(agentId) {
  try {
    const res = await fetch("/api/agents/" + encodeURIComponent(agentId) + "/reset", { method: "POST" });
    if (res.ok) { const d = await safeJson(res); agentTeam = d.agents || agentTeam; if (agentId === "saga" && typeof syncAgentNameUI === "function") { syncAgentNameUI("Saga"); } syncActiveAgentBadge(); renderAgentRoster(); showToast(t("toast_reset_agent", { name: agentNameById(agentId) })); }
  } catch (err) { showToast(err.message || t("err_reset_agent")); }
}
async function restoreDefaultAgentsUI() {
  try {
    const res = await fetch("/api/agents/restore-defaults", { method: "POST" });
    if (res.ok) { const d = await safeJson(res); agentTeam = d.agents || []; const rBtn = document.getElementById("restore-agents-btn"); if (rBtn) { rBtn.hidden = true; } syncActiveAgentBadge(); renderAgentRoster(); showToast(t("toast_restored_agents")); }
  } catch (err) { showToast(err.message || t("err_restore_agents")); }
}
async function revealAgentsFolderUI() {
  try {
    const res = await fetch("/api/agents/reveal-folder", { method: "POST" });
    if (res.ok) { const d = await safeJson(res); showToast(t("toast_opened_folder", { path: d.path || "agents" })); }
  } catch (err) { showToast(err.message || t("err_open_folder")); }
}
function bindAgentControls() {
  const sideBtn = document.getElementById("sidebar-agents-btn"), closeBtn = document.getElementById("close-agent-studio-modal");
  const tabR = document.getElementById("agent-tab-roster"), tabE = document.getElementById("agent-tab-editor");
  const form = document.getElementById("agent-editor-form"), cancelBtn = document.getElementById("agent-ed-cancel-btn");
  const gBtn = document.getElementById("agent-mode-guided-btn"), rBtn = document.getElementById("agent-mode-raw-btn");
  const restoreBtn = document.getElementById("restore-agents-btn"), revBtn = document.getElementById("reveal-agents-folder-btn");
  if (sideBtn) { sideBtn.addEventListener("click", () => openAgentStudio("roster")); }
  if (closeBtn) { closeBtn.addEventListener("click", () => document.getElementById("agent-studio-modal").close()); }
  if (tabR) { tabR.addEventListener("click", () => setAgentStudioTab("roster")); }
  if (tabE) { tabE.addEventListener("click", () => openAgentEditor(null)); }
  if (typeof bindRovingTablist === "function") { bindRovingTablist("#agent-studio-modal [role='tab']", tab => { if (tab.id === "agent-tab-editor") { openAgentEditor(null); } else { setAgentStudioTab("roster"); } }); }
  if (cancelBtn) { cancelBtn.addEventListener("click", () => setAgentStudioTab("roster")); }
  if (form) { form.addEventListener("submit", saveAgentUI); }
  if (gBtn) { gBtn.addEventListener("click", () => setAgentEditorMode(false)); }
  if (rBtn) { rBtn.addEventListener("click", () => setAgentEditorMode(true)); }
  if (restoreBtn) { restoreBtn.addEventListener("click", restoreDefaultAgentsUI); }
  if (revBtn) { revBtn.addEventListener("click", revealAgentsFolderUI); }
  const provSel = document.getElementById("agent-ed-provider");
  if (provSel) { provSel.addEventListener("change", () => syncAgentModelChoices(provSel.value, "")); }
  for (const id of ["agent-sync-palette-toggle", "onboarding-sync-agent-palette"]) {
    const chk = document.getElementById(id);
    if (chk) {
      chk.addEventListener("change", async function () {
        syncAgentPalette = Boolean(chk.checked); syncActiveAgentBadge();
        if (syncAgentPalette) { applyPaletteForAgent(activeAgentObj(), !isInsideChat()); }
        if (typeof currentTurns !== "undefined" && currentTurns.length && typeof renderChatStream === "function") { renderChatStream(); }
        await fetch("/api/agents/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sync_agent_palette: syncAgentPalette }) }).catch(() => {});
      });
    }
  }
  loadAgentTeam();
}
"""
