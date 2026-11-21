"""Phase 2 client logic: Save Answer as Guide modal, In-App Markdown Editor, Highlight-to-Ask."""

EDITOR_SCRIPT: str = r"""
let sgPendingCitations = [];
let activeReaderGuide = null, readerEditMode = false, readerRawDraft = "";
let readerSelectedText = "";

function openSaveGuideModal(opts) {
  const modal = document.getElementById("save-guide-modal");
  if (!modal) { return; }
  if (!knowledgeAreas.length) {
    if (typeof showToast === "function") { showToast(t("sg_need_ws"), 4200); }
    return;
  }
  const titleEl = document.getElementById("save-guide-title");
  const titleIn = document.getElementById("sg-title-input");
  const areaSel = document.getElementById("sg-area-select");
  const subIn = document.getElementById("sg-subfolder-input");
  const tagsIn = document.getElementById("sg-tags-input");
  const bodyIn = document.getElementById("sg-content-input");
  const stEl = document.getElementById("sg-status");
  const dirs = selectedAreas().length ? selectedAreas() : knowledgeAreas.map(a => a.name);
  if (titleEl) { titleEl.textContent = opts && opts.isNew ? t("sg_new_title") : t("sg_modal_title"); }
  if (areaSel) {
    areaSel.innerHTML = dirs.map(d => "<option value='" + escapeHtml(d) + "'>" + escapeHtml(areaTitle(d)) + "</option>").join("");
    areaSel.value = (opts && opts.area && dirs.includes(opts.area)) ? opts.area : (activeKnowledgeArea || dirs[0] || "");
  }
  if (titleIn) { titleIn.value = (opts && opts.title) || ""; }
  if (subIn) { subIn.value = (opts && opts.subfolder) || (typeof selectedSubfolder === "string" && selectedSubfolder ? selectedSubfolder : ""); }
  if (tagsIn) { tagsIn.value = (opts && opts.tags) || ""; }
  if (bodyIn) { bodyIn.value = (opts && opts.content) || ""; }
  if (stEl) { stEl.textContent = ""; }
  sgPendingCitations = Array.isArray(opts && opts.citations) ? opts.citations : [];
  modal.showModal();
  if (titleIn) { titleIn.focus(); titleIn.select(); }
}

function openNewNoteModal() {
  openSaveGuideModal({ isNew: true, title: "", content: "## Overview\n\n", tags: "notes" });
}

function saveTurnToLibrary(tIdx) {
  const turn = currentTurns[tIdx];
  if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  const title = (turn.format_name || turn.query || "Research Note").slice(0, 80);
  const author = typeof turnAuthorName === "function" ? turnAuthorName(turn) : activeAgentName();
  const baseTags = ["synthesis", author.toLowerCase().replace(/[^a-z0-9_-]+/g, "-")].filter(Boolean);
  openSaveGuideModal({
    isNew: false,
    title: title,
    content: turn.tutor.answer,
    tags: Array.from(new Set(baseTags)).join(", "),
    citations: turn.tutor.cited_titles || [],
  });
}

async function submitSaveGuideForm(event) {
  event.preventDefault();
  const modal = document.getElementById("save-guide-modal"), stEl = document.getElementById("sg-status"), btn = document.getElementById("submit-save-guide-btn");
  const title = (document.getElementById("sg-title-input").value || "").trim();
  const area = (document.getElementById("sg-area-select").value || activeKnowledgeArea || "").trim();
  const subfolder = (document.getElementById("sg-subfolder-input").value || "").trim();
  const tags = (document.getElementById("sg-tags-input").value || "").trim();
  const content = document.getElementById("sg-content-input").value || "";
  if (!title || !content.trim()) { if (stEl) { stEl.textContent = t("sg_required_err"); } return; }
  const version = areaVersion;
  btn.disabled = true; if (stEl) { stEl.textContent = t("sg_saving"); }
  try {
    const res = await areaFetch("/api/guides/create", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, area, subfolder, tags, content, citations: sgPendingCitations }),
    });
    const data = await safeJson(res);
    if (version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not save guide."); }
    applyWorkspacePayload(data);
    await loadGuidesCatalog(null);
    if (version !== areaVersion) { return; }
    if (modal && modal.open) { modal.close(); }
    if (typeof showToast === "function") { showToast(t("sg_saved_toast", { title: data.title || title }), 4200); }
    if (document.getElementById("library-view")) { await openLibraryCatalog(selectedTag); }
  } catch (err) {
    if (stEl && version === areaVersion) { stEl.textContent = err.message || "Could not save guide."; }
  } finally { btn.disabled = false; }
}

function hideSelectionPill() {
  const pill = document.getElementById("reader-selection-pill");
  if (pill) { pill.hidden = true; }
  readerSelectedText = "";
}

function updateReaderSelectionPill() {
  const pill = document.getElementById("reader-selection-pill");
  const body = document.getElementById("reader-sections-wrap");
  if (!pill || !body || readerEditMode) { hideSelectionPill(); return; }
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) { hideSelectionPill(); return; }
  const text = sel.toString().trim();
  if (text.length < 6) { hideSelectionPill(); return; }
  const range = sel.getRangeAt(0);
  if (!body.contains(range.commonAncestorContainer)) { hideSelectionPill(); return; }
  const rect = range.getBoundingClientRect();
  if (!rect || (!rect.width && !rect.height)) { hideSelectionPill(); return; }
  readerSelectedText = text.slice(0, 1200);
  const askBtn = document.getElementById("sel-ask-agent-btn");
  if (askBtn) { askBtn.textContent = t("sel_ask_named", { agent: typeof activeAgentName === "function" ? activeAgentName() : "Saga" }); }
  pill.hidden = false;
  const pw = pill.offsetWidth || 280, ph = pill.offsetHeight || 38;
  const left = Math.max(12, Math.min(window.innerWidth - pw - 12, rect.left + rect.width / 2 - pw / 2));
  const top = rect.top > ph + 18 ? rect.top - ph - 10 : Math.min(window.innerHeight - ph - 12, rect.bottom + 10);
  pill.style.left = Math.round(left) + "px";
  pill.style.top = Math.round(top) + "px";
}

function launchSelectionAction(mode) {
  const quote = readerSelectedText.trim();
  const guide = activeReaderGuide;
  hideSelectionPill();
  if (!quote) { return; }
  const snippet = quote.length > 420 ? quote.slice(0, 420) + "…" : quote;
  if (guide && typeof startScopedChat === "function") {
    startScopedChat({ doc_id: guide.doc_id, subfolder: null });
  } else {
    resetHome();
  }
  if (mode === "explain") {
    queryEl.value = t("sel_explain_prompt", { quote: snippet });
    askTutor();
  } else if (mode === "ask") {
    queryEl.value = t("sel_ask_prompt", { quote: snippet });
    queryEl.focus();
  } else {
    queryEl.value = "> " + snippet + "\n\n";
    queryEl.focus();
  }
}

async function openGuideMarkdownEditor(guide, previousTag) {
  const wrap = document.getElementById("reader-sections-wrap"), btn = document.getElementById("guide-edit-btn");
  if (!wrap) { return; }
  if (readerEditMode) {
    readerEditMode = false;
    renderGuideReader(guide, previousTag);
    return;
  }
  const version = areaVersion;
  hideSelectionPill();
  if (btn) { btn.disabled = true; }
  try {
    const res = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id) + "/raw");
    const data = await safeJson(res);
    if (version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not load Markdown source."); }
    readerEditMode = true;
    readerRawDraft = data.raw_markdown || "";
    if (btn) { btn.textContent = t("ed_view_mode"); btn.disabled = false; }
    wrap.innerHTML = "<section class='rounded-2xl border border-[#4BB8E8]/35 bg-[#0B1020] p-4 flex flex-col gap-3'>"
      + "<div class='flex items-center justify-between gap-2 flex-wrap'>"
      + "<div class='flex items-center gap-1 bg-[#04060F] p-1 rounded-xl border border-white/10'>"
      + "<button id='ed-tab-write' type='button' class='px-3 py-1 rounded-lg text-xs font-medium bg-[#4BB8E8] text-[#04060F]'>" + escapeHtml(t("ed_write")) + "</button>"
      + "<button id='ed-tab-preview' type='button' class='px-3 py-1 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8]'>" + escapeHtml(t("ed_preview")) + "</button></div>"
      + "<div class='flex items-center gap-2'><span id='ed-word-count' class='text-xs font-mono text-[#738196]'></span>"
      + "<button id='ed-cancel-btn' type='button' class='px-3 py-1.5 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8]'>" + escapeHtml(t("cancel")) + "</button>"
      + "<button id='ed-save-btn' type='button' class='px-3.5 py-1.5 rounded-lg bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 transition'>" + escapeHtml(t("ed_save_reindex")) + "</button></div></div>"
      + "<label for='guide-md-textarea' class='visually-hidden'>" + escapeHtml(t("sg_content_lbl")) + "</label>"
      + "<textarea id='guide-md-textarea' rows='18' class='md-editor-area w-full rounded-xl bg-[#04060F] border border-white/15 focus:border-[#4BB8E8] p-4 text-sm text-[#EEF2F8] outline-none'></textarea>"
      + "<div id='guide-md-preview' hidden class='md-body md-prose rounded-xl bg-[#04060F] border border-white/10 p-5 text-base leading-7 flex flex-col gap-3'></div>"
      + "<p id='ed-status' role='status' class='text-xs text-[#A0B0C8]'></p></section>";
    const ta = document.getElementById("guide-md-textarea"), pv = document.getElementById("guide-md-preview");
    const wcEl = document.getElementById("ed-word-count"), stEl = document.getElementById("ed-status");
    ta.value = readerRawDraft;
    const syncWords = () => {
      const words = (ta.value.trim().match(/\S+/g) || []).length;
      if (wcEl) { wcEl.textContent = words + " " + t("ed_words"); }
    };
    syncWords();
    ta.addEventListener("input", syncWords);
    ta.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        const saveBtn = document.getElementById("ed-save-btn");
        if (!saveBtn || !saveBtn.disabled) { saveEditedGuide(); }
      }
    });
    const setTab = (isPreview) => {
      ta.hidden = isPreview; pv.hidden = !isPreview;
      if (isPreview) {
        const bodyOnly = ta.value.replace(/^---\n[\s\S]*?\n---\n*/, "");
        pv.innerHTML = formatMarkdown(bodyOnly);
      }
      document.getElementById("ed-tab-write").className = "px-3 py-1 rounded-lg text-xs font-medium " + (!isPreview ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
      document.getElementById("ed-tab-preview").className = "px-3 py-1 rounded-lg text-xs font-medium " + (isPreview ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
    };
    document.getElementById("ed-tab-write").addEventListener("click", () => setTab(false));
    document.getElementById("ed-tab-preview").addEventListener("click", () => setTab(true));
    document.getElementById("ed-cancel-btn").addEventListener("click", () => { readerEditMode = false; renderGuideReader(guide, previousTag); });
    async function saveEditedGuide() {
      const saveBtn = document.getElementById("ed-save-btn"), saveVer = areaVersion;
      if (saveBtn && saveBtn.disabled) { return; }
      if (saveBtn) { saveBtn.disabled = true; }
      if (stEl) { stEl.textContent = t("sg_saving"); }
      try {
        const saveRes = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id) + "/raw", {
          method: "PUT", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: ta.value }),
        });
        const saved = await safeJson(saveRes);
        if (saveVer !== areaVersion) { return; }
        if (!saveRes.ok) { throw new Error(saved.detail || "Could not save changes."); }
        readerEditMode = false;
        applyWorkspacePayload(saved);
        const refreshed = (await loadGuidesCatalog(null)).find(g => g.doc_id === guide.doc_id) || saved.guide || guide;
        if (saveVer !== areaVersion) { return; }
        if (typeof showToast === "function") { showToast(t("ed_saved_toast"), 3200); }
        renderGuideReader(refreshed, previousTag);
      } catch (err) {
        if (stEl && saveVer === areaVersion) { stEl.textContent = err.message || "Could not save changes."; }
        if (saveBtn && saveBtn.isConnected) { saveBtn.disabled = false; }
      }
    }
    document.getElementById("ed-save-btn").addEventListener("click", saveEditedGuide);
    ta.focus();
  } catch (err) {
    if (btn && btn.isConnected) { btn.disabled = false; }
    if (version === areaVersion && typeof showToast === "function") { showToast(err.message || t("err_open_editor"), 4000); }
  }
}

function bindEditorUX() {
  const modal = document.getElementById("save-guide-modal"), form = document.getElementById("save-guide-form");
  const closeBtn = document.getElementById("close-save-guide-btn"), cancelBtn = document.getElementById("cancel-save-guide-btn");
  if (form) { form.addEventListener("submit", submitSaveGuideForm); }
  if (closeBtn) { closeBtn.addEventListener("click", () => modal && modal.close()); }
  if (cancelBtn) { cancelBtn.addEventListener("click", () => modal && modal.close()); }
  const expBtn = document.getElementById("sel-explain-btn"), askBtn = document.getElementById("sel-ask-agent-btn"), qBtn = document.getElementById("sel-quote-btn");
  const pill = document.getElementById("reader-selection-pill");
  for (const pair of [[expBtn, "explain"], [askBtn, "ask"], [qBtn, "quote"]]) {
    if (pair[0]) {
      pair[0].addEventListener("mousedown", e => e.preventDefault());
      pair[0].addEventListener("click", () => launchSelectionAction(pair[1]));
    }
  }
  if (pill) {
    pill.addEventListener("keydown", function (e) {
      const btns = Array.from(pill.querySelectorAll("button"));
      const cur = btns.indexOf(document.activeElement);
      if (e.key === "Escape") { e.preventDefault(); hideSelectionPill(); }
      else if (e.key === "ArrowRight" && cur >= 0) { e.preventDefault(); btns[(cur + 1) % btns.length].focus(); }
      else if (e.key === "ArrowLeft" && cur >= 0) { e.preventDefault(); btns[(cur - 1 + btns.length) % btns.length].focus(); }
    });
  }
  document.addEventListener("mouseup", () => setTimeout(updateReaderSelectionPill, 20));
  document.addEventListener("keyup", () => setTimeout(updateReaderSelectionPill, 20));
  document.addEventListener("scroll", hideSelectionPill, true);
  document.addEventListener("mousedown", function (e) {
    const pill = document.getElementById("reader-selection-pill");
    if (pill && !pill.hidden && !pill.contains(e.target)) { hideSelectionPill(); }
  });
}
"""
