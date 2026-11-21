"""Phase 3 client logic: Multi-Agent Cross-Examine, Chat Forking, and Contradiction / Gap Scan."""

WORKFLOW_SCRIPT: str = r"""
let cxTargetTurnIdx = -1, gapScanOp = 0;

function openCrossExamineModal(tIdx) {
  const modal = document.getElementById("cross-examine-modal"), listEl = document.getElementById("cx-agent-list"), angleIn = document.getElementById("cx-angle-input");
  const turn = currentTurns[tIdx];
  if (!modal || !listEl || !turn || !turn.tutor) { return; }
  cxTargetTurnIdx = tIdx;
  if (angleIn) { angleIn.value = ""; }
  const origAuthor = typeof turnAuthorName === "function" ? turnAuthorName(turn) : "Saga";
  const origId = turn.agent_id || "";
  const agents = (typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length)
    ? agentTeam
    : [{ id: "lisbeth", name: "Lisbeth", role: "Investigator", tagline: "Verify facts & expose weak assumptions", palette: "lisbeth" }];
  const ordered = agents.toSorted((a, b) => (a.id === origId ? 1 : 0) - (b.id === origId ? 1 : 0));
  listEl.innerHTML = ordered.map(function (ag) {
    const col = typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette).accent : "#4BB8E8";
    const same = ag.id === origId || ag.name === origAuthor;
    return "<button type='button' data-cx-agent='" + escapeHtml(ag.id) + "' class='w-full text-left p-3 rounded-xl bg-[#04060F] border border-white/10 hover:border-[#4BB8E8] transition flex items-start gap-3'>"
      + "<span aria-hidden='true' class='w-2.5 h-2.5 rounded-full mt-1.5 shrink-0' style='background:" + col + "'></span>"
      + "<span class='min-w-0 flex-1'><span class='flex items-center gap-2'><span class='text-sm font-medium text-[#EEF2F8]'>" + escapeHtml(ag.name) + "</span>"
      + (ag.role ? "<span class='text-[11px] font-mono text-[#738196]'>" + escapeHtml(ag.role) + "</span>" : "")
      + (same ? "<span class='ml-auto text-[10px] font-mono text-[#738196]'>" + escapeHtml(t("cx_original")) + "</span>" : "")
      + "</span>" + (ag.tagline ? "<span class='block text-xs text-[#A0B0C8] mt-0.5'>" + escapeHtml(ag.tagline) + "</span>" : "") + "</span></button>";
  }).join("");
  listEl.querySelectorAll("[data-cx-agent]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const agId = btn.getAttribute("data-cx-agent") || "";
      const angle = angleIn ? angleIn.value.trim() : "";
      modal.close();
      runCrossExamineTurn(cxTargetTurnIdx, agId, angle);
    });
  });
  modal.showModal();
}

async function runCrossExamineTurn(tIdx, agentId, customAngle) {
  const turn = currentTurns[tIdx];
  if (!turn || !turn.tutor || !turn.tutor.answer) { return; }
  const ag = (typeof agentTeam !== "undefined" && Array.isArray(agentTeam)) ? agentTeam.find(a => a.id === agentId) : null;
  const agName = (ag && ag.name) || agentId, origName = typeof turnAuthorName === "function" ? turnAuthorName(turn) : "Saga";
  const excerpt = turn.tutor.answer.length > 1800 ? turn.tutor.answer.slice(0, 1800) + "\n…" : turn.tutor.answer;
  const angleNote = customAngle ? ("\n\nFocus specifically on: " + customAngle) : "";
  const hiddenInstr = t("cx_prompt_tpl", { agent: agName, orig: origName, q: turn.query }) + "\n\n---\n" + excerpt + "\n---" + angleNote;
  const shortQ = String(turn.query || "").slice(0, 90);
  const visibleQ = customAngle
    ? t("cx_user_msg_angle", { agent: agName, q: shortQ, angle: customAngle })
    : t("cx_user_msg", { agent: agName, q: shortQ });
  await runSearch(true, { agentId: agentId, displayQuery: visibleQ, instructionPrefix: hiddenInstr });
}

async function forkChatAtTurn(tIdx) {
  if (!currentChatId) { return; }
  const version = areaVersion, chatAtStart = currentChatId;
  try {
    const res = await areaFetch("/api/chats/" + encodeURIComponent(chatAtStart) + "/fork", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ turn_index: tIdx, free_chat: Boolean(typeof freeChatMode !== "undefined" && freeChatMode) }),
    });
    const data = await safeJson(res);
    if (version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Could not fork chat."); }
    await loadRecentChats();
    if (version === areaVersion && data.session && data.session.chat_id) {
      await openSavedChat(data.session.chat_id);
      if (typeof showToast === "function") { showToast(t("fork_toast", { n: tIdx + 1 }), 3600); }
    }
  } catch (err) {
    if (version === areaVersion && typeof showToast === "function") { showToast(err.message || t("err_fork_chat"), 4000); }
  }
}

async function openGapAnalysisModal() {
  const modal = document.getElementById("gap-analysis-modal"), bodyEl = document.getElementById("gap-results-body"), sumEl = document.getElementById("gap-summary-line");
  if (!modal || !bodyEl) { return; }
  if (!knowledgeAreas.length) {
    if (typeof showToast === "function") { showToast(t("sg_need_ws"), 4000); }
    return;
  }
  const version = areaVersion, op = ++gapScanOp;
  bodyEl.innerHTML = "<div class='py-6 text-center text-sm text-[#A0B0C8]'>" + escapeHtml(t("gap_scanning")) + "</div>";
  modal.showModal();
  try {
    const res = await areaFetch("/api/workspace/analyze-gaps", { method: "POST" });
    const data = await safeJson(res);
    if (op !== gapScanOp || version !== areaVersion) { return; }
    if (!res.ok) { throw new Error(data.detail || "Gap scan failed."); }
    const conflicts = data.conflicts || [], dups = data.duplicates || [], orphans = data.orphan_topics || [];
    if (sumEl) {
      sumEl.textContent = t("gap_summary_fmt", { docs: data.total_guides || 0, conflicts: conflicts.length, dups: dups.length, orphans: orphans.length });
    }
    let html = "";
    html += "<section class='flex flex-col gap-2'><h3 class='text-xs font-mono uppercase tracking-wider text-amber-300'>" + escapeHtml(t("gap_sec_conflicts")) + " (" + conflicts.length + ")</h3>";
    if (!conflicts.length) { html += "<p class='text-xs text-[#738196]'>" + escapeHtml(t("gap_none_conflicts")) + "</p>"; }
    else {
      html += conflicts.map(function (c) {
        const rows = (c.entries || []).map(e => "<li class='text-xs text-[#A0B0C8] flex items-baseline gap-2'><button type='button' data-gap-open='" + escapeHtml(e.doc_id) + "' class='text-[#4BB8E8] hover:underline shrink-0'>" + escapeHtml(e.title) + "</button><span class='font-mono text-[#EEF2F8] truncate'>" + escapeHtml(e.excerpt) + "</span></li>").join("");
        return "<div class='p-3 rounded-xl bg-[#04060F] border border-amber-400/25 flex flex-col gap-1.5'><div class='flex items-center justify-between gap-2'><span class='text-sm font-medium text-[#EEF2F8]'>" + escapeHtml(c.field) + "</span><button type='button' data-gap-investigate='" + escapeHtml(c.field) + "' class='text-xs text-[#4BB8E8] hover:underline'>" + escapeHtml(t("gap_ask_investigate")) + "</button></div><ul class='flex flex-col gap-1'>" + rows + "</ul></div>";
      }).join("");
    }
    html += "</section>";
    html += "<section class='flex flex-col gap-2'><h3 class='text-xs font-mono uppercase tracking-wider text-[#4BB8E8]'>" + escapeHtml(t("gap_sec_orphans")) + " (" + orphans.length + ")</h3>";
    if (!orphans.length) { html += "<p class='text-xs text-[#738196]'>" + escapeHtml(t("gap_none_orphans")) + "</p>"; }
    else {
      html += orphans.map(function (o) {
        const gNames = (o.guides || []).map(g => g.title).join(", ");
        return "<div class='p-3 rounded-xl bg-[#04060F] border border-white/10 flex items-center justify-between gap-3'><div class='min-w-0'><div class='text-sm font-medium text-[#EEF2F8] truncate'>" + escapeHtml(o.topic) + " <span class='text-xs font-mono text-[#738196]'>(" + o.count + ")</span></div><div class='text-xs text-[#738196] truncate'>" + escapeHtml(gNames) + "</div></div><button type='button' data-gap-create='" + escapeHtml(o.topic) + "' class='shrink-0 px-2.5 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/35 text-xs text-[#4BB8E8] hover:bg-[#4BB8E8]/25 transition'>" + escapeHtml(t("gap_create_overview")) + "</button></div>";
      }).join("");
    }
    html += "</section>";
    html += "<section class='flex flex-col gap-2'><h3 class='text-xs font-mono uppercase tracking-wider text-[#A0B0C8]'>" + escapeHtml(t("gap_sec_dups")) + " (" + dups.length + ")</h3>";
    if (!dups.length) { html += "<p class='text-xs text-[#738196]'>" + escapeHtml(t("gap_none_dups")) + "</p>"; }
    else {
      html += dups.map(function (d) {
        return "<div class='p-3 rounded-xl bg-[#04060F] border border-white/10 flex items-center justify-between gap-2 text-xs'><div class='flex items-center gap-2 flex-wrap'><button type='button' data-gap-open='" + escapeHtml(d.first.doc_id) + "' class='text-[#4BB8E8] hover:underline'>" + escapeHtml(d.first.title) + "</button><span class='text-[#738196]'>↔</span><button type='button' data-gap-open='" + escapeHtml(d.second.doc_id) + "' class='text-[#4BB8E8] hover:underline'>" + escapeHtml(d.second.title) + "</button></div><span class='font-mono text-amber-300 shrink-0'>" + d.similarity + "%</span></div>";
      }).join("");
    }
    html += "</section>";
    bodyEl.innerHTML = html;
    bodyEl.querySelectorAll("[data-gap-open]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const docId = btn.getAttribute("data-gap-open");
        const found = allGuides.find(g => g.doc_id === docId);
        modal.close();
        if (found) { renderGuideReader(found, null, -1); }
      });
    });
    bodyEl.querySelectorAll("[data-gap-create]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const topic = btn.getAttribute("data-gap-create") || "Overview";
        modal.close();
        if (typeof openSaveGuideModal === "function") {
          openSaveGuideModal({ isNew: true, title: topic + " Overview", tags: topic.toLowerCase().replace(/[^a-z0-9_-]+/g, "-"), content: "## Overview\n\nSynthesize key facts and references about **" + topic + "** here.\n" });
        }
      });
    });
    bodyEl.querySelectorAll("[data-gap-investigate]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const field = btn.getAttribute("data-gap-investigate") || "";
        modal.close();
        resetHome();
        queryEl.value = t("gap_investigate_prompt", { field: field });
        askTutor();
      });
    });
  } catch (err) {
    bodyEl.innerHTML = "<div class='py-6 text-center text-sm text-amber-300'>" + escapeHtml(err.message || "Gap scan failed.") + "</div>";
  }
}

function bindWorkflowUX() {
  const cxModal = document.getElementById("cross-examine-modal"), cxClose = document.getElementById("close-cx-modal");
  if (cxClose) { cxClose.addEventListener("click", () => cxModal && cxModal.close()); }
  const gapModal = document.getElementById("gap-analysis-modal"), gapClose = document.getElementById("close-gap-modal");
  if (gapClose) { gapClose.addEventListener("click", () => gapModal && gapModal.close()); }
}
"""
