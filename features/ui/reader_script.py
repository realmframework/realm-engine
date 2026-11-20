"""Full guide reader with section focus, preview and guarded deletion."""

READER_SCRIPT: str = r"""
async function renderGuideReader(guide, previousTag, sectionIndex = -1) {
  const operation = ++currentScrollId;
  await withViewTransition(function () {
    if (operation !== currentScrollId) { return; }
    setViewMode(true, true); document.getElementById("chat-stream").innerHTML = ""; renderTutor(null); chunksHeader.classList.add("hidden"); document.getElementById("stream-divider").classList.add("hidden"); resultsEl.classList.remove("hidden");
    const tagLine = (guide.tags || []).length ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide mb-6'>// " + (guide.tags || []).map(escapeHtml).join(" · ") + "</div>" : "";
    const sectionsHtml = (guide.sections || []).map(function (s, index) { return "<section class='p-6 sm:p-7 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.08)] flex flex-col'><h3 id='reader-section-" + index + "' tabindex='-1' class='text-xl font-medium text-[#EEF2F8] mb-4 scroll-mt-8 focus-visible:outline'>" + escapeHtml(s.section_title) + "</h3><div class='md-prose text-[#C8D4E6] text-[15.5px] leading-7 flex flex-col gap-3.5'>" + formatMarkdown(s.content) + "</div></section>"; }).join("");
    resultsEl.innerHTML = "<div class='flex flex-col gap-4 pt-6'><div class='flex items-center justify-between gap-3 flex-wrap'><button id='guide-back-btn' type='button' class='text-sm text-[#A0B0C8] hover:text-[#EEF2F8] flex items-center gap-1.5 transition-colors'>← Back to Library</button><div class='flex flex-wrap items-center gap-2'><button id='guide-preview-btn' type='button' class='px-3 py-1.5 rounded-xl border border-white/10 text-xs text-[#A0B0C8] hover:text-white'>" + "<svg aria-hidden='true' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5' class='inline-block align-middle mr-1'><circle cx='10.5' cy='10.5' r='6.5'/><path d='m16 16 5 5'/></svg>" + modeCopy("Preview personal details", "Preview DSGVO Redaction") + "</button><button id='guide-anonymize-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8]/50 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + modeCopy("Hide personal details", "Anonymize (DSGVO)") + "</button><button id='guide-delete-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-red-400/50 text-xs text-[#A0B0C8] hover:text-red-300 transition'>Delete</button><button id='guide-ask-tutor-btn' type='button' class='px-3.5 py-1.5 rounded-xl bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] border border-[#4BB8E8]/30 text-xs font-medium flex items-center gap-1.5 transition-colors'>Chat with this Document</button></div></div><div><h2 id='reader-heading' tabindex='-1' class='text-2xl font-medium text-[#EEF2F8] mb-2 outline-none'>" + escapeHtml(guide.title) + "</h2>" + tagLine + "</div><section class='rounded-xl border border-white/10 p-4'>" + destinationControls("reader", guide.subfolder || "") + "<button id='move-guide-btn' type='button' class='rounded-lg border border-white/15 px-3 py-2 text-sm mt-3'>Move guide</button><p id='move-guide-status' role='status' class='text-xs text-[#A0B0C8] mt-2'></p></section><section id='reader-redaction-inspector' aria-label='Governance and redaction preview' class='hidden p-4 rounded-xl border border-white/10 bg-[#0B1020]'></section>" + sectionsHtml + "</div>";
    bindGuideFolder(guide, previousTag); bindMarkdownLinks(resultsEl, guide.doc_id, previousTag);
    document.getElementById("guide-back-btn").addEventListener("click", function () { openLibraryCatalog(previousTag); }); document.getElementById("guide-ask-tutor-btn").addEventListener("click", function () { startScopedChat({ doc_id: guide.doc_id, subfolder: null }); });
    document.getElementById("guide-anonymize-btn").addEventListener("click", async function () {
      const version = areaVersion;
      const res = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id) + "/anonymize", { method: "POST" });
      if (res.ok && version === areaVersion) { const updated = (await loadGuidesCatalog(null)).find(function (g) { return g.doc_id === guide.doc_id; }); if (updated && version === areaVersion) { renderGuideReader(updated, previousTag); } }
    });
    document.getElementById("guide-preview-btn").addEventListener("click", function () { previewGuideRedaction(guide); });
    document.getElementById("guide-delete-btn").addEventListener("click", function () { deleteLibraryGuide(guide, previousTag); });
  }, document.getElementById("active-stream"));
  if (operation !== currentScrollId) { return; }
  const target = document.getElementById(sectionIndex >= 0 ? "reader-section-" + sectionIndex : "reader-heading");
  if (target) { await scrollIntoViewAsync(target, { behavior: "smooth", block: "start" }); if (operation === currentScrollId && target.isConnected) { target.focus({ preventScroll: true }); } }
}
"""
