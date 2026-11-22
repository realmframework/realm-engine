"""Interactive Agent Builder Chat (Agent Architect) and 1-Click .pptx / 16:9 PDF Slide Deck Export."""

AGENT_BUILDER_SCRIPT: str = r"""
let agentBuilderHistory = [], agentBuilderDraft = null, agentBuilderBusy = false;

async function exportSlidesRequest(payload, filenameFallback, fmt) {
  const ext = fmt === "pdf" ? ".pdf" : ".pptx";
  try {
    showToast(t("toast_exp_slides_gen"), 10000);
    const res = await areaFetch("/api/export/slides", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({}, payload, { format: fmt || "pptx" })),
    });
    if (!res.ok) { const e = await safeJson(res); throw new Error(e.detail || t("err_export_slides")); }
    downloadBlob(await res.blob(), (filenameFallback || "realm-slides") + "-slides" + ext);
    showToast(t("toast_exp_slides_ok"));
  } catch (err) { showToast(err.message || t("err_export_slides")); }
}

function exportTurnSlides(tIdx, fmt) {
  const turn = currentTurns[tIdx]; if (!turn || !turn.tutor) { return; }
  const title = turn.format_name || turn.query.slice(0, 60) || "REALM Slides";
  if (currentChatId && turn.created_at) {
    exportSlidesRequest({ chat_id: currentChatId, turn_index: tIdx, free_chat: freeChatMode }, chatSlug(title), fmt);
  } else {
    exportSlidesRequest({ title: title, markdown: turn.tutor.answer, citations: turn.tutor.cited_titles || [] }, chatSlug(title), fmt);
  }
}

function exportFullChatSlides(fmt) {
  if (!currentChatId) { return; }
  const title = (currentTurns[0] && currentTurns[0].query) || "conversation";
  exportSlidesRequest({ chat_id: currentChatId, free_chat: freeChatMode }, chatSlug(title), fmt);
}

function exportGuideSlides(guide, fmt) {
  if (!guide || !guide.doc_id) { return; }
  exportSlidesRequest({ doc_id: guide.doc_id }, chatSlug(guide.title || guide.doc_id), fmt);
}

function renderAgentBuilderChat() {
  const logEl = document.getElementById("agent-builder-messages");
  const prevEl = document.getElementById("agent-builder-preview");
  const draftBtn = document.getElementById("ab-draft-btn");
  if (!logEl) { return; }
  const msgs = [{ role: "assistant", content: t("ab_welcome") }].concat(agentBuilderHistory);
  logEl.innerHTML = msgs.map(function (m) {
    const isUser = m.role === "user";
    if (isUser) {
      return "<div class='self-end max-w-[85%] rounded-2xl bg-[#4BB8E8]/15 border border-[#4BB8E8]/30 px-3.5 py-2 text-sm text-[#EEF2F8] whitespace-pre-wrap'>" + escapeHtml(m.content) + "</div>";
    }
    return "<div class='self-start max-w-[92%] rounded-2xl bg-[#04060F] border border-white/10 px-3.5 py-2.5 text-sm text-[#EEF2F8] md-body flex flex-col gap-1.5'>" + formatMarkdown(m.content, false, 3) + "</div>";
  }).join("") + (agentBuilderBusy ? "<div class='self-start inline-flex items-center gap-2 rounded-xl bg-[#04060F] border border-white/10 px-3.5 py-2 text-xs text-[#A0B0C8]'><span class='text-[#4BB8E8] animate-spin inline-flex'>" + SPARKLE_SVG + "</span><span>" + escapeHtml(t("ab_thinking")) + "</span></div>" : "");
  logEl.scrollTop = logEl.scrollHeight;
  if (draftBtn) { draftBtn.disabled = agentBuilderBusy || !agentBuilderHistory.some(m => m.role === "user"); }
  if (!prevEl) { return; }
  if (!agentBuilderDraft) { prevEl.hidden = true; prevEl.replaceChildren(); return; }
  const d = agentBuilderDraft, pal = typeof paletteColorsFor === "function" ? paletteColorsFor(d.palette) : { accent: "#4BB8E8", glow: "#6366F1" };
  prevEl.hidden = false;
  prevEl.innerHTML = "<div class='flex items-center justify-between gap-2 flex-wrap'>"
    + "<div class='flex items-center gap-2 min-w-0'><span aria-hidden='true' class='w-3 h-3 rounded-full shrink-0' style='background:linear-gradient(135deg," + pal.accent + "," + pal.glow + ")'></span>"
    + "<span class='text-xs font-mono uppercase tracking-wider text-[#4BB8E8]'>" + escapeHtml(t("ab_preview_lbl")) + "</span></div>"
    + "<span class='text-xs font-mono text-[#738196]'>temp " + Number(d.temperature ?? 0.25).toFixed(2) + (d.palette ? " · " + escapeHtml(d.palette) : "") + "</span></div>"
    + "<div class='flex flex-col gap-0.5'><div class='text-sm font-semibold text-[#EEF2F8]'>" + escapeHtml(d.name) + " <span class='font-normal text-[#A0B0C8]'>— " + escapeHtml(d.role || "Specialist") + "</span></div>"
    + (d.tagline ? "<p class='text-xs text-[#A0B0C8]'>" + escapeHtml(d.tagline) + "</p>" : "") + "</div>"
    + (d.instructions ? "<pre class='max-h-28 overflow-y-auto whitespace-pre-wrap rounded-lg bg-[#0B1020] border border-white/10 px-3 py-2 text-xs font-mono text-[#C8D4E6]'>" + escapeHtml(d.instructions) + "</pre>" : "")
    + "<div class='flex items-center justify-end gap-2 pt-1 flex-wrap'>"
    + "<button id='ab-edit-btn' type='button' class='px-3 py-1.5 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("ab_edit_btn")) + "</button>"
    + "<button id='ab-save-btn' type='button' class='px-3.5 py-1.5 rounded-lg bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition'>" + escapeHtml(t("ab_save_btn")) + "</button></div>";
  const saveBtn = document.getElementById("ab-save-btn"), editBtn = document.getElementById("ab-edit-btn");
  if (saveBtn) { saveBtn.addEventListener("click", saveBuilderDraft); }
  if (editBtn) { editBtn.addEventListener("click", openBuilderDraftInEditor); }
}

function resetAgentBuilder() {
  agentBuilderHistory = [];
  agentBuilderDraft = null;
  agentBuilderBusy = false;
  const inp = document.getElementById("agent-builder-input"), st = document.getElementById("agent-builder-status");
  if (inp) { inp.value = ""; }
  if (st) { st.textContent = ""; }
  renderAgentBuilderChat();
}

async function sendAgentBuilderMessage(forceDraft) {
  if (agentBuilderBusy) { return; }
  const inp = document.getElementById("agent-builder-input"), st = document.getElementById("agent-builder-status");
  const sendBtn = document.getElementById("ab-send-btn");
  const text = inp ? inp.value.trim() : "";
  if (!forceDraft && !text) { if (inp) { inp.focus(); } return; }
  if (text) { agentBuilderHistory.push({ role: "user", content: text }); if (inp) { inp.value = ""; } }
  if (!agentBuilderHistory.length) { return; }
  agentBuilderBusy = true;
  if (sendBtn) { sendBtn.disabled = true; }
  if (st) { st.textContent = ""; }
  renderAgentBuilderChat();
  try {
    const apiKey = typeof getApiKey === "function" ? getApiKey() : "";
    const headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await fetch("/api/agents/builder/chat", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        messages: agentBuilderHistory,
        force_draft: Boolean(forceDraft),
        provider: providerEl ? providerEl.value : "ollama",
        model: modelEl ? (modelEl.value.trim() || null) : null,
        api_key: apiKey || null,
      }),
    });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || "Could not design agent right now."); }
    if (data.reply) { agentBuilderHistory.push({ role: "assistant", content: String(data.reply) }); }
    if (data.draft) { agentBuilderDraft = data.draft; }
    if (typeof refreshBudget === "function") { refreshBudget(); }
  } catch (err) {
    if (st) { st.textContent = err.message || "Could not design agent right now."; }
  } finally {
    agentBuilderBusy = false;
    if (sendBtn) { sendBtn.disabled = false; }
    renderAgentBuilderChat();
    if (inp && !document.getElementById("agent-builder-pane").hidden) { inp.focus(); }
  }
}

async function saveBuilderDraft() {
  if (!agentBuilderDraft) { return; }
  const st = document.getElementById("agent-builder-status"), saveBtn = document.getElementById("ab-save-btn");
  if (saveBtn) { saveBtn.disabled = true; }
  try {
    const d = agentBuilderDraft;
    const res = await fetch("/api/agents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: d.name, role: d.role || "Specialist", tagline: d.tagline || "",
        palette: d.palette || "realm", default_format: d.default_format || "",
        temperature: Number(d.temperature ?? 0.25), instructions: d.instructions || "",
      }),
    });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || "Could not save agent."); }
    agentTeam = data.agents || agentTeam;
    defaultAgentId = data.active_agent || defaultAgentId;
    syncActiveAgentBadge(); renderAgentRoster();
    resetAgentBuilder();
    setAgentStudioTab("roster");
    showToast(t("toast_saved_agent", { name: (data.agent && data.agent.name) || d.name }));
  } catch (err) {
    if (st) { st.textContent = err.message || "Could not save agent."; }
    if (saveBtn) { saveBtn.disabled = false; }
  }
}

function openBuilderDraftInEditor() {
  if (!agentBuilderDraft || typeof openAgentEditor !== "function") { return; }
  const d = agentBuilderDraft;
  openAgentEditor(null);
  document.getElementById("agent-ed-name").value = d.name || "";
  document.getElementById("agent-ed-role").value = d.role || "Specialist";
  document.getElementById("agent-ed-tagline").value = d.tagline || "";
  document.getElementById("agent-ed-palette").value = d.palette || "realm";
  document.getElementById("agent-ed-format").value = d.default_format || "";
  document.getElementById("agent-ed-temp").value = String(d.temperature ?? 0.25);
  document.getElementById("agent-ed-instructions").value = d.instructions || "";
}

function bindAgentBuilderUX() {
  const form = document.getElementById("agent-builder-form"), inp = document.getElementById("agent-builder-input");
  const draftBtn = document.getElementById("ab-draft-btn"), resetBtn = document.getElementById("ab-reset-btn");
  if (form) { form.addEventListener("submit", function (e) { e.preventDefault(); sendAgentBuilderMessage(false); }); }
  if (draftBtn) { draftBtn.addEventListener("click", function () { sendAgentBuilderMessage(true); }); }
  if (resetBtn) { resetBtn.addEventListener("click", resetAgentBuilder); }
  if (inp) {
    inp.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!e.isComposing && e.keyCode !== 229) { sendAgentBuilderMessage(false); }
      }
    });
  }
  renderAgentBuilderChat();
}
"""
