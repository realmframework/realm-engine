"""Full guide reader with section focus, preview and guarded deletion."""

READER_SCRIPT: str = r"""
async function renderGuideReader(guide, previousTag, sectionIndex = -1) {
  stopGraphSimulation();
  const operation = ++currentScrollId;
  activeReaderGuide = guide; readerEditMode = false;
  if (typeof hideSelectionPill === "function") { hideSelectionPill(); }
  await withViewTransition(function () {
    if (operation !== currentScrollId) { return; }
    setViewMode(true, true); document.getElementById("chat-stream").replaceChildren(); renderTutor(null); chunksHeader.classList.add("hidden"); document.getElementById("stream-divider").classList.add("hidden"); resultsEl.classList.remove("hidden");
    const tagLine = (guide.tags || []).length ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide mb-6'>// " + (guide.tags || []).map(escapeHtml).join(" · ") + "</div>" : "";
    const sectionsHtml = (guide.sections || []).map(function (s, index) { return "<section class='p-6 sm:p-7 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.08)] flex flex-col'><h2 id='reader-section-" + index + "' tabindex='-1' class='text-xl font-medium text-[#EEF2F8] mb-4 scroll-mt-8 focus-visible:outline'>" + escapeHtml(s.section_title) + "</h2><div class='md-body md-prose text-[#C8D4E6] text-[15.5px] leading-7 flex flex-col gap-3.5'>" + formatMarkdown(s.content, false, 3) + "</div></section>"; }).join("");
    const readerMore = "<details id='reader-more-menu' class='turn-more-menu relative inline-block'><summary aria-label='" + escapeHtml(t("reader_more_aria")) + "' title='" + escapeHtml(t("reader_more_aria")) + "' class='list-none cursor-pointer px-2.5 py-1.5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8]/50 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition inline-flex items-center justify-center'>" + MORE_SVG + "</summary><div class='header-popover-panel'><button id='guide-study-btn' type='button' class='turn-popover-item'>" + escapeHtml(t("study_btn")) + "</button><button id='guide-preview-btn' type='button' class='turn-popover-item'>" + modeCopy(t("reader_prev_pii"), "Preview GDPR Redaction") + "</button><button id='guide-anonymize-btn' type='button' class='turn-popover-item'>" + modeCopy(t("reader_hide_pii"), "Anonymize (GDPR)") + "</button><button id='guide-delete-btn' type='button' class='turn-popover-item hover:text-red-300'>" + escapeHtml(t("delete_btn")) + "</button></div></details>";
    resultsEl.innerHTML = "<div class='flex flex-col gap-4 pt-6'><div class='flex items-center justify-between gap-3 flex-wrap'><button id='guide-back-btn' type='button' class='text-sm text-[#A0B0C8] hover:text-[#EEF2F8] flex items-center gap-1.5 transition-colors'>" + escapeHtml(t("reader_back")) + "</button><div class='flex flex-wrap items-center gap-2'>" + readerMore + "<button id='guide-edit-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8]/50 text-xs text-[#EEF2F8] transition'>" + escapeHtml(t("ed_edit_btn")) + "</button><button id='guide-ask-tutor-btn' type='button' class='px-3.5 py-1.5 rounded-xl bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] border border-[#4BB8E8]/30 text-xs font-medium flex items-center gap-1.5 transition-colors'>" + escapeHtml(t("lib_chat_doc")) + "</button></div></div><div><h1 id='reader-heading' tabindex='-1' class='text-2xl font-medium text-[#EEF2F8] mb-2 outline-none'>" + escapeHtml(guide.title) + "</h1>" + tagLine + "</div><section class='rounded-xl border border-white/10 p-4'>" + destinationControls("reader", guide.subfolder || "") + "<button id='move-guide-btn' type='button' class='rounded-xl border border-white/15 px-3 py-2 text-sm mt-3'>" + escapeHtml(t("reader_move_btn")) + "</button><p id='move-guide-status' role='status' class='text-xs text-[#A0B0C8] mt-2'></p></section><section id='reader-redaction-inspector' aria-label='Governance and redaction preview' class='hidden p-4 rounded-xl border border-white/10 bg-[#0B1020]'></section><div id='reader-sections-wrap' class='flex flex-col gap-4'>" + sectionsHtml + "</div></div>";
    const closeReaderMenu = function () { const m = document.getElementById("reader-more-menu"); if (m) { m.open = false; } };
    bindGuideFolder(guide, previousTag); bindMarkdownLinks(resultsEl, guide.doc_id, previousTag);
    document.getElementById("guide-edit-btn").addEventListener("click", function () { if (typeof openGuideMarkdownEditor === "function") { openGuideMarkdownEditor(guide, previousTag); } });
    document.getElementById("guide-study-btn").addEventListener("click", function () { closeReaderMenu(); if (typeof openStudyDeck === "function") { openStudyDeck({ doc_id: guide.doc_id, title: guide.title }); } });
    document.getElementById("guide-back-btn").addEventListener("click", function () { openLibraryCatalog(previousTag); }); document.getElementById("guide-ask-tutor-btn").addEventListener("click", function () { startScopedChat({ doc_id: guide.doc_id, subfolder: null }); });
    const anonBtn = document.getElementById("guide-anonymize-btn");
    anonBtn.addEventListener("click", async function () {
      closeReaderMenu();
      const version = areaVersion;
      if (anonBtn.disabled) { return; }
      anonBtn.disabled = true;
      try {
        const res = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id) + "/anonymize", { method: "POST" });
        const data = await safeJson(res);
        if (version !== areaVersion) { return; }
        if (!res.ok) { throw new Error(data.detail || "Could not anonymize guide."); }
        const updated = (await loadGuidesCatalog(null)).find(function (g) { return g.doc_id === guide.doc_id; });
        if (updated && version === areaVersion) { renderGuideReader(updated, previousTag); }
      } catch (err) {
        if (version === areaVersion) { showToast(err.message || t("err_anonymize"), 4000); }
      } finally { if (anonBtn.isConnected) { anonBtn.disabled = false; } }
    });
    document.getElementById("guide-preview-btn").addEventListener("click", function () { closeReaderMenu(); previewGuideRedaction(guide); });
    document.getElementById("guide-delete-btn").addEventListener("click", function () { closeReaderMenu(); deleteLibraryGuide(guide, previousTag); });
  }, document.getElementById("active-stream"));
  if (operation !== currentScrollId) { return; }
  const target = document.getElementById(sectionIndex >= 0 ? "reader-section-" + sectionIndex : "reader-heading");
  if (target) { await scrollIntoViewAsync(target, { behavior: "smooth", block: "start" }); if (operation === currentScrollId && target.isConnected) { target.focus({ preventScroll: true }); } }
}
"""
