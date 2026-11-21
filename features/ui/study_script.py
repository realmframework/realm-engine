"""Active Recall Flashcard Studio client logic: AI generation, custom cards, spaced repetition & Anki export."""

STUDY_SCRIPT: str = r"""
let studyDeck = [], studyIdx = 0, studyRevealed = false, studyScopeOpts = {}, studyDeckMode = "quick", studyOp = 0, studyRatingPending = false;

function syncStudyGenLabel() {
  const genBtn = document.getElementById("study-generate-btn");
  if (!genBtn) { return; }
  genBtn.textContent = studyDeckMode === "ai" ? t("study_regen_ai") : t("study_gen_ai");
}

async function openStudyDeck(opts) {
  const modal = document.getElementById("study-modal"), stage = document.getElementById("study-card-stage"), meta = document.getElementById("study-meta-line"), st = document.getElementById("study-status-msg"), addForm = document.getElementById("study-add-form");
  if (!modal || !stage) { return; }
  if (!knowledgeAreas.length) {
    if (typeof showToast === "function") { showToast(t("sg_need_ws"), 4000); }
    return;
  }
  const op = ++studyOp, version = areaVersion;
  studyScopeOpts = opts || {};
  studyDeck = []; studyIdx = 0; studyRevealed = false; studyDeckMode = "quick"; studyRatingPending = false;
  const scopePill = document.getElementById("study-scope-pill");
  if (scopePill) {
    const scopeLabel = studyScopeOpts.title || studyScopeOpts.subfolder || areaTitle(activeKnowledgeArea || "");
    scopePill.textContent = scopeLabel; scopePill.hidden = !scopeLabel;
  }
  if (st) { st.textContent = ""; }
  if (addForm) { addForm.hidden = true; }
  if (meta) { meta.textContent = t("study_loading"); }
  stage.innerHTML = "<div class='py-6 text-center text-sm text-[#A0B0C8]'>" + escapeHtml(t("study_loading")) + "</div>";
  modal.showModal();
  try {
    const params = new URLSearchParams();
    if (studyScopeOpts.doc_id) { params.set("doc_id", studyScopeOpts.doc_id); }
    if (studyScopeOpts.subfolder) { params.set("subfolder", studyScopeOpts.subfolder); }
    const res = await areaFetch("/api/study/deck" + (params.toString() ? "?" + params.toString() : ""));
    const data = await safeJson(res);
    if (op !== studyOp || version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not load study deck."); }
    studyDeck = Array.isArray(data.cards) ? data.cards : [];
    studyDeckMode = data.deck_mode || "quick";
    studyIdx = 0; studyRevealed = false;
    syncStudyGenLabel();
    renderStudyCard(data.due_count || 0, data.mastered_count || 0);
  } catch (err) {
    if (op === studyOp && version === areaVersion) {
      stage.innerHTML = "<div class='py-6 text-center text-sm text-amber-300'>" + escapeHtml(err.message || "Could not load deck.") + "</div>";
    }
  }
}

async function generateAiStudyDeck() {
  const genBtn = document.getElementById("study-generate-btn"), st = document.getElementById("study-status-msg");
  const cntSel = document.getElementById("study-count-select"), styleSel = document.getElementById("study-style-select");
  if (!genBtn) { return; }
  const op = ++studyOp, version = areaVersion;
  const count = Number((cntSel && cntSel.value) || 10), style = (styleSel && styleSel.value) || "concepts";
  const prov = (typeof providerEl !== "undefined" && providerEl && providerEl.value) || "ollama";
  const mdl = (typeof modelEl !== "undefined" && modelEl && modelEl.value.trim()) || "";
  const apiKey = typeof getApiKey === "function" ? getApiKey() : "";
  genBtn.disabled = true;
  if (st) { st.textContent = t("study_generating", { n: count, model: mdl || prov }); }
  try {
    const headers = Object.assign({ "Content-Type": "application/json" }, apiKey ? { "x-api-key": apiKey } : {});
    const res = await areaFetch("/api/study/generate", {
      method: "POST", headers: headers,
      body: JSON.stringify({ doc_id: studyScopeOpts.doc_id || null, subfolder: studyScopeOpts.subfolder || null, count: count, style: style, provider: prov, model: mdl || null, api_key: apiKey || null }),
    });
    const data = await safeJson(res);
    if (op !== studyOp || version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not generate flashcards."); }
    studyDeck = Array.isArray(data.cards) ? data.cards : [];
    studyDeckMode = "ai"; studyIdx = 0; studyRevealed = false;
    syncStudyGenLabel();
    renderStudyCard(data.due_count || 0, data.mastered_count || 0);
    if (st) { st.textContent = t("study_gen_ready", { n: studyDeck.length }); }
  } catch (err) {
    if (st && op === studyOp && version === areaVersion) { st.textContent = err.message || "Could not generate flashcards."; }
  } finally { if (op === studyOp) { genBtn.disabled = false; } }
}

async function saveCustomStudyCard(event) {
  event.preventDefault();
  const fIn = document.getElementById("study-new-front"), bIn = document.getElementById("study-new-back"), form = document.getElementById("study-add-form"), st = document.getElementById("study-status-msg");
  const front = (fIn && fIn.value.trim()) || "", back = (bIn && bIn.value.trim()) || "";
  if (!front || !back) { return; }
  const op = ++studyOp, version = areaVersion;
  try {
    const res = await areaFetch("/api/study/cards", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ front: front, back: back, doc_id: studyScopeOpts.doc_id || null, subfolder: studyScopeOpts.subfolder || null, source: studyScopeOpts.title || areaTitle(activeKnowledgeArea || "") }),
    });
    const data = await safeJson(res);
    if (op !== studyOp || version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not save card."); }
    studyDeck = Array.isArray(data.cards) ? data.cards : studyDeck;
    studyDeckMode = "ai"; studyIdx = 0; studyRevealed = false;
    if (fIn) { fIn.value = ""; }
    if (bIn) { bIn.value = ""; }
    if (form) { form.hidden = true; }
    syncStudyGenLabel();
    renderStudyCard(data.due_count || 0, data.mastered_count || 0);
    if (st) { st.textContent = t("study_card_added"); }
  } catch (err) { if (st && op === studyOp && version === areaVersion) { st.textContent = err.message || "Could not save card."; } }
}

async function deleteStudyCardById(cardId) {
  if (!cardId) { return; }
  const op = ++studyOp, version = areaVersion, params = new URLSearchParams();
  if (studyScopeOpts.doc_id) { params.set("doc_id", studyScopeOpts.doc_id); }
  if (studyScopeOpts.subfolder) { params.set("subfolder", studyScopeOpts.subfolder); }
  try {
    const res = await areaFetch("/api/study/cards/" + encodeURIComponent(cardId) + (params.toString() ? "?" + params.toString() : ""), { method: "DELETE" });
    if (!res.ok || op !== studyOp || version !== areaVersion) { return; }
    const data = await safeJson(res);
    if (op !== studyOp || version !== areaVersion) { return; }
    studyDeck = Array.isArray(data.cards) ? data.cards : studyDeck.filter(c => c.id !== cardId);
    studyDeckMode = data.deck_mode || studyDeckMode;
    studyIdx = Math.min(studyIdx, Math.max(0, studyDeck.length - 1));
    studyRevealed = false;
    syncStudyGenLabel();
    renderStudyCard(data.due_count || 0, data.mastered_count || 0);
  } catch (_e) {}
}

function exportStudyAnkiTsv() {
  if (!studyDeck.length || typeof downloadBlobText !== "function") { return; }
  const clean = s => String(s || "").replace(/[\t\r\n]+/g, " ").trim();
  const rows = studyDeck.map(c => clean(c.front) + "\t" + clean(c.back) + "\t" + clean((c.tags || []).join(" ")));
  downloadBlobText(rows.join("\n") + "\n", "realm-flashcards-anki.tsv", "text/tab-separated-values;charset=utf-8");
  if (typeof showToast === "function") { showToast(t("study_anki_exported", { n: studyDeck.length }), 3200); }
}

function renderStudyCard(dueOverride, masteredOverride) {
  const stage = document.getElementById("study-card-stage"), meta = document.getElementById("study-meta-line"), rateEl = document.getElementById("study-rate-btns");
  if (!stage || !rateEl) { return; }
  const total = studyDeck.length;
  const due = typeof dueOverride === "number" ? dueOverride : studyDeck.filter(c => c.due).length;
  const mastered = typeof masteredOverride === "number" ? masteredOverride : studyDeck.filter(c => (c.box || 0) >= 3).length;
  const modeTag = studyDeckMode === "ai" ? t("study_mode_ai") : t("study_mode_quick");
  if (meta) { meta.textContent = modeTag + " · " + t("study_meta_fmt", { total: total, due: due, mastered: mastered }); }
  if (!total) {
    stage.innerHTML = "<div class='py-6 text-center text-sm text-[#A0B0C8]'>" + escapeHtml(t("study_empty")) + "</div>";
    rateEl.innerHTML = "";
    return;
  }
  if (studyIdx >= total) {
    stage.innerHTML = "<div class='py-6 flex flex-col items-center gap-3 text-center'><div class='text-lg font-medium text-[#38D399]'>" + escapeHtml(t("study_done_t")) + "</div><p class='text-xs text-[#A0B0C8] max-w-md'>" + escapeHtml(t("study_done_d", { n: total })) + "</p><button id='study-restart-btn' type='button' class='px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 transition'>" + escapeHtml(t("study_restart")) + "</button></div>";
    rateEl.innerHTML = "";
    const rb = document.getElementById("study-restart-btn");
    if (rb) { rb.addEventListener("click", () => { studyIdx = 0; studyRevealed = false; renderStudyCard(); }); }
    return;
  }
  const card = studyDeck[studyIdx];
  const progressPct = Math.round(((studyIdx + 1) / total) * 100);
  const quickHint = studyDeckMode === "quick" ? "<p class='text-xs text-[#738196]' style='margin:0'>" + escapeHtml(t("study_mode_quick")) + " · " + escapeHtml(t("study_gen_ai")) + "</p>" : "";
  const delBtn = studyDeckMode === "ai" ? "<button id='study-del-card-btn' type='button' title='Remove card' aria-label='Remove card' class='text-xs text-[#738196] hover:text-[#EF4444] px-1'>✕</button>" : "";
  stage.innerHTML = quickHint + "<div class='flex items-center justify-between gap-2 text-xs text-[#738196]'><span class='font-mono shrink-0'>" + (studyIdx + 1) + " / " + total + "</span><span class='truncate'>" + escapeHtml(card.source || "") + "</span></div>"
    + "<div class='study-progress-track' role='progressbar' aria-valuemin='0' aria-valuemax='100' aria-valuenow='" + progressPct + "' aria-label='Study progress'><div class='study-progress-fill' style='width:" + progressPct + "%'></div></div>"
    + "<div id='study-card-surface' class='study-card-face'>"
    + "<div class='flex flex-col gap-2'><div class='flex items-center justify-between gap-2'><span class='text-2xs font-mono uppercase tracking-wider text-[#4BB8E8]'>" + escapeHtml(t("study_question_lbl")) + "</span>" + delBtn + "</div><div class='md-body text-base font-medium text-[#EEF2F8] leading-relaxed'>" + escapeHtml(card.front) + "</div></div>"
    + (studyRevealed
      ? "<div class='pt-3 border-t border-white/10 flex flex-col gap-2'><span class='text-2xs font-mono uppercase tracking-wider text-[#38D399]'>" + escapeHtml(t("study_answer_lbl")) + "</span><div class='md-body text-sm text-[#C8D4E6] leading-relaxed'>" + formatMarkdown(card.back) + "</div></div>"
      : "<div class='pt-3 text-center'><button id='study-flip-btn' type='button' class='study-btn-good'>" + escapeHtml(t("study_reveal_btn")) + "</button></div>")
    + "</div>";
  const revealAndFocus = function () {
    studyRevealed = true; renderStudyCard();
    const goodBtn = document.querySelector("[data-study-rate='good']");
    if (goodBtn) { goodBtn.focus({ preventScroll: true }); }
  };
  const surf = document.getElementById("study-card-surface");
  if (surf && !studyRevealed) { surf.addEventListener("click", revealAndFocus); }
  const flipBtn = document.getElementById("study-flip-btn");
  if (flipBtn) { flipBtn.addEventListener("click", e => { e.stopPropagation(); revealAndFocus(); }); }
  const delEl = document.getElementById("study-del-card-btn");
  if (delEl) { delEl.addEventListener("click", e => { e.stopPropagation(); deleteStudyCardById(card.id); }); }
  if (!studyRevealed) {
    rateEl.innerHTML = "<button id='study-skip-btn' type='button' class='px-3 py-1.5 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8]'>" + escapeHtml(t("study_skip")) + "</button>";
    const sk = document.getElementById("study-skip-btn");
    if (sk) { sk.addEventListener("click", () => { studyIdx++; studyRevealed = false; renderStudyCard(); const nxt = document.getElementById("study-flip-btn") || document.getElementById("study-restart-btn"); if (nxt) { nxt.focus({ preventScroll: true }); } }); }
  } else {
    rateEl.innerHTML = "<button type='button' data-study-rate='hard' class='study-btn-hard'>" + escapeHtml(t("study_hard")) + "</button>"
      + "<button type='button' data-study-rate='good' class='study-btn-good'>" + escapeHtml(t("study_good")) + "</button>"
      + "<button type='button' data-study-rate='easy' class='study-btn-easy'>" + escapeHtml(t("study_easy")) + "</button>";
    rateEl.querySelectorAll("[data-study-rate]").forEach(btn => {
      btn.addEventListener("click", () => rateCurrentStudyCard(btn.getAttribute("data-study-rate") || "good"));
    });
  }
}

async function rateCurrentStudyCard(rating) {
  const card = studyDeck[studyIdx];
  if (!card || studyRatingPending) { return; }
  const op = studyOp, version = areaVersion;
  studyRatingPending = true;
  try {
    const res = await areaFetch("/api/study/review", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ card_id: card.id, rating: rating }),
    });
    if (op !== studyOp || version !== areaVersion) { return; }
    if (res.ok) {
      const data = await safeJson(res);
      card.box = (data.review && data.review.box) || card.box;
      card.due = rating === "hard";
    }
  } catch (_e) {}
  finally { studyRatingPending = false; }
  if (op === studyOp && version === areaVersion) {
    studyIdx++; studyRevealed = false; renderStudyCard();
    const nxt = document.getElementById("study-flip-btn") || document.getElementById("study-restart-btn");
    if (nxt) { nxt.focus({ preventScroll: true }); }
  }
}

function launchSocraticQuizFromStudy() {
  const modal = document.getElementById("study-modal");
  if (modal && modal.open) { modal.close(); }
  if (studyScopeOpts.doc_id || studyScopeOpts.subfolder) {
    startScopedChat({ doc_id: studyScopeOpts.doc_id || null, subfolder: studyScopeOpts.subfolder || null });
  } else {
    resetHome();
  }
  const label = studyScopeOpts.title || areaTitle(activeKnowledgeArea || "");
  runSearch(true, {
    displayQuery: t("study_socratic_user_q", { target: label }),
    instructionPrefix: t("study_socratic_prompt", { target: label }),
  });
}

function bindStudyUX() {
  const modal = document.getElementById("study-modal"), closeBtn = document.getElementById("close-study-modal"), socBtn = document.getElementById("study-socratic-btn");
  const genBtn = document.getElementById("study-generate-btn"), addToggle = document.getElementById("study-add-toggle-btn"), addCancel = document.getElementById("study-add-cancel-btn");
  const addForm = document.getElementById("study-add-form"), ankiBtn = document.getElementById("study-export-anki-btn");
  if (closeBtn) { closeBtn.addEventListener("click", () => modal && modal.close()); }
  if (socBtn) { socBtn.addEventListener("click", launchSocraticQuizFromStudy); }
  if (genBtn) { genBtn.addEventListener("click", generateAiStudyDeck); }
  if (addToggle && addForm) { addToggle.addEventListener("click", () => { addForm.hidden = !addForm.hidden; if (!addForm.hidden) { const f = document.getElementById("study-new-front"); if (f) { f.focus(); } } }); }
  if (addCancel && addForm) { addCancel.addEventListener("click", () => { addForm.hidden = true; }); }
  if (addForm) { addForm.addEventListener("submit", saveCustomStudyCard); }
  if (ankiBtn) { ankiBtn.addEventListener("click", exportStudyAnkiTsv); }
  if (modal) {
    modal.addEventListener("keydown", function (e) {
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT")) { return; }
      if (!studyDeck.length || studyIdx >= studyDeck.length) { return; }
      if (e.key === " " && !studyRevealed) {
        if (e.target && e.target.closest("button, a, summary") && e.target.id !== "study-flip-btn") { return; }
        e.preventDefault(); studyRevealed = true; renderStudyCard();
        const goodBtn = document.querySelector("[data-study-rate='good']");
        if (goodBtn) { goodBtn.focus({ preventScroll: true }); }
      }
      else if (studyRevealed && e.key === "1") { e.preventDefault(); rateCurrentStudyCard("hard"); }
      else if (studyRevealed && e.key === "2") { e.preventDefault(); rateCurrentStudyCard("good"); }
      else if (studyRevealed && e.key === "3") { e.preventDefault(); rateCurrentStudyCard("easy"); }
    });
  }
}
"""
