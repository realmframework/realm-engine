"""Pane-scoped Split Screen controller: Vertical Dual Chat, Horizontal/Vertical Board <-> Chat, and Guide Split."""

SPLIT_SCRIPT: str = r"""
const splitState = {
  open: false, orientation: "vertical", bMode: "chat", ratio: 50,
  chatId: null, turns: [], agentId: "lisbeth", guideId: "",
  controller: null, reqId: null, streamScheduled: false
};
function syncSplitSelectors() {
  const agSel = document.getElementById("split-agent-select"), thSel = document.getElementById("split-thread-select"), gSel = document.getElementById("split-guide-select");
  if (agSel) {
    const list = typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length ? agentTeam : [{ id: "saga", name: "Saga" }, { id: "lisbeth", name: "Lisbeth" }, { id: "plague", name: "Plague" }];
    if (!list.some(function (a) { return a.id === splitState.agentId; })) {
      splitState.agentId = (list.find(function (a) { return a.id !== (typeof activeAgentId !== "undefined" ? activeAgentId : "saga"); }) || list[0]).id;
    }
    agSel.innerHTML = list.map(function (a) {
      return "<option value='" + escapeHtml(a.id) + "'" + (a.id === splitState.agentId ? " selected" : "") + ">" + escapeHtml(a.name) + "</option>";
    }).join("");
  }
  if (thSel) {
    const opts = ["<option value=''>" + escapeHtml(t("sp_new_thread_opt")) + "</option>"];
    (Array.isArray(savedChats) ? savedChats : []).slice(0, 25).forEach(function (c) {
      opts.push("<option value='" + escapeHtml(c.chat_id) + "'" + (c.chat_id === splitState.chatId ? " selected" : "") + ">" + escapeHtml(c.title || c.chat_id) + "</option>");
    });
    thSel.innerHTML = opts.join("");
    thSel.value = splitState.chatId || "";
  }
  if (gSel) {
    const guides = typeof cachedGuides !== "undefined" && Array.isArray(cachedGuides) ? cachedGuides : [];
    const opts = guides.length ? guides.map(function (g) {
      return "<option value='" + escapeHtml(g.doc_id) + "'" + (g.doc_id === splitState.guideId ? " selected" : "") + ">" + escapeHtml(g.title || g.doc_id) + "</option>";
    }) : ["<option value=''>" + escapeHtml(t("sp_no_guides")) + "</option>"];
    gSel.innerHTML = opts.join("");
    if (guides.length && !splitState.guideId) { splitState.guideId = guides[0].doc_id; gSel.value = splitState.guideId; }
  }
}
function applySplitLayout() {
  const main = document.getElementById("main-content"), resizer = document.getElementById("split-resizer"), paneB = document.getElementById("split-pane-b");
  const toggleBtn = document.getElementById("split-toggle-btn"), closeItem = document.getElementById("split-menu-close-btn");
  if (!main || !resizer || !paneB) { return; }
  const narrow = window.matchMedia && window.matchMedia("(max-width: 959px)").matches;
  const active = splitState.open && !narrow;
  main.classList.toggle("is-split-active", active);
  main.classList.toggle("is-split-vertical", active && splitState.orientation === "vertical");
  main.classList.toggle("is-split-horizontal", active && splitState.orientation === "horizontal");
  main.style.setProperty("--split-a", splitState.ratio + "%");
  resizer.hidden = !active; paneB.hidden = !active;
  resizer.setAttribute("aria-orientation", splitState.orientation === "vertical" ? "vertical" : "horizontal");
  resizer.setAttribute("aria-valuenow", String(Math.round(splitState.ratio)));
  if (toggleBtn) { toggleBtn.classList.toggle("is-active", active); }
  if (closeItem) { closeItem.hidden = !splitState.open; }
  const chatBody = document.getElementById("split-chat-body"), guideBody = document.getElementById("split-guide-body");
  const mChat = document.getElementById("split-mode-chat-btn"), mGuide = document.getElementById("split-mode-guide-btn");
  const agSel = document.getElementById("split-agent-select"), thSel = document.getElementById("split-thread-select"), newBtn = document.getElementById("split-new-chat-btn");
  const isChat = splitState.bMode === "chat";
  if (chatBody) { chatBody.hidden = !isChat; }
  if (guideBody) { guideBody.hidden = isChat; }
  if (mChat) { mChat.setAttribute("aria-pressed", String(isChat)); }
  if (mGuide) { mGuide.setAttribute("aria-pressed", String(!isChat)); }
  if (agSel) { agSel.hidden = !isChat; }
  if (thSel) { thSel.hidden = !isChat; }
  if (newBtn) { newBtn.hidden = !isChat; }
}
function abortSplitRequest() {
  if (splitState.reqId) { cancelBackendRequest(splitState.reqId); splitState.reqId = null; }
  if (splitState.controller) { splitState.controller.abort(); splitState.controller = null; }
  syncSplitSubmitBtn(false);
}
function syncSplitSubmitBtn(loading) {
  const btn = document.getElementById("split-submit-btn"); if (!btn) { return; }
  if (loading) {
    btn.type = "button"; btn.innerHTML = STOP_SVG;
    btn.setAttribute("aria-label", t("stop_generating")); btn.title = t("stop_generating");
    btn.className = "w-8 h-8 rounded-full bg-[#04060F] border border-[#4BB8E8] text-[#4BB8E8] flex items-center justify-center shrink-0 transition";
  } else {
    btn.type = "submit"; btn.textContent = "↑";
    btn.setAttribute("aria-label", t("submit_query")); btn.title = t("submit_query");
    btn.className = "w-8 h-8 rounded-full bg-[#4BB8E8] text-[#04060F] flex items-center justify-center text-sm font-semibold shrink-0 transition";
  }
}
function renderSplitChatStream() {
  const stream = document.getElementById("split-chat-stream"); if (!stream) { return; }
  if (!splitState.turns.length) {
    const agName = typeof agentNameById === "function" ? agentNameById(splitState.agentId) : splitState.agentId;
    stream.innerHTML = "<div class='split-empty-chat'><p style='margin:0 0 0.4rem;font-weight:600;color:var(--text)'>" + escapeHtml(t("sp_ready_title", { agent: agName })) + "</p><p style='margin:0'>" + escapeHtml(t("sp_ready_sub")) + "</p></div>";
    return;
  }
  stream.innerHTML = splitState.turns.map(function (turn, idx) {
    const authorName = typeof turnAuthorName === "function" ? turnAuthorName(turn) : (turn.agent_name || "Saga");
    const authorHex = typeof turnAuthorColor === "function" ? turnAuthorColor(turn) : "";
    const turnStyle = authorHex ? " style='--turn-seed:" + escapeHtml(authorHex) + "'" : "";
    let bodyHtml = "";
    if (turn.loadingTutor) {
      const txt = String(turn.streamingText || "");
      bodyHtml = txt
        ? "<div id='split-turn-" + idx + "-body' class='md-body is-streaming text-sm leading-relaxed flex flex-col gap-2.5'>" + formatMarkdown(txt, true, 3) + "</div>"
        : "<div class='text-xs text-[#A0B0C8]'>" + escapeHtml(t("chat_preparing")) + "</div>";
    } else if (turn.tutor) {
      bodyHtml = "<div class='md-body text-sm leading-relaxed flex flex-col gap-2.5'>" + formatMarkdown(turn.tutor.answer || "", true, 3) + "</div>"
        + "<div class='split-turn-actions'>"
        + "<button type='button' data-split-copy='" + idx + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("copy_btn")) + "</button>"
        + "<button type='button' data-split-extract='" + idx + "' class='wb-btn wb-btn-sm'>" + escapeHtml(t("wb_extract_to_board")) + "</button>"
        + "</div>";
    }
    return "<article class='split-turn turn-themed'" + turnStyle + ">"
      + "<div class='split-user-bubble'>" + escapeHtml(turn.query) + "</div>"
      + "<div class='turn-author-heading flex items-center gap-1.5 text-sm font-semibold'>" + SPARKLE_SVG + "<span>" + escapeHtml(authorName) + "</span></div>"
      + bodyHtml + "</article>";
  }).join("");
  stream.querySelectorAll("[data-split-copy]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const trn = splitState.turns[Number(btn.getAttribute("data-split-copy") || 0)];
      if (trn && trn.tutor && navigator.clipboard) { await navigator.clipboard.writeText(trn.tutor.answer || ""); showToast(t("copied_btn")); }
    });
  });
  stream.querySelectorAll("[data-split-extract]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const idx = Number(btn.getAttribute("data-split-extract") || 0), trn = splitState.turns[idx];
      if (trn && trn.tutor && typeof extractTasksToBoard === "function") {
        await extractTasksToBoard({ chat_id: splitState.chatId || "", turn_index: idx, text: trn.tutor.answer || "" });
      }
    });
  });
  stream.scrollTop = stream.scrollHeight;
}
function scheduleSplitStreamRender() {
  if (splitState.streamScheduled) { return; }
  splitState.streamScheduled = true;
  requestAnimationFrame(function () {
    splitState.streamScheduled = false;
    const idx = splitState.turns.length - 1, last = idx >= 0 ? splitState.turns[idx] : null;
    if (!last || !last.loadingTutor) { return; }
    const el = document.getElementById("split-turn-" + idx + "-body");
    if (!el) { renderSplitChatStream(); return; }
    el.innerHTML = formatMarkdown(String(last.streamingText || ""), true, 3);
    const sc = document.getElementById("split-chat-stream");
    if (sc && sc.scrollHeight - sc.scrollTop - sc.clientHeight < 120) { sc.scrollTop = sc.scrollHeight; }
  });
}
async function runSplitChatSubmit(overridePrompt) {
  const qEl = document.getElementById("split-query");
  const q = String(overridePrompt !== undefined ? overridePrompt : (qEl ? qEl.value : "")).trim();
  if (!q || areaSwitching) { return; }
  abortSplitRequest();
  const version = areaVersion;
  if (!splitState.chatId) { splitState.chatId = newChatId(); }
  if (qEl && overridePrompt === undefined) { qEl.value = ""; }
  const effAgentId = (typeof resolveMentionedAgent === "function" && resolveMentionedAgent(q)) || splitState.agentId || "saga";
  const effAgentName = typeof agentNameById === "function" ? agentNameById(effAgentId) : effAgentId;
  const controller = new AbortController(), reqId = "sreq-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
  splitState.controller = controller; splitState.reqId = reqId;
  const pending = { query: q, ask_tutor: true, loadingTutor: true, agent_id: effAgentId, agent_name: effAgentName, tutor: null, results: [], streamingText: "" };
  splitState.turns.push(pending);
  syncSplitSubmitBtn(true); renderSplitChatStream();
  try {
    const apiKey = getApiKey(), headers = Object.assign({ "Content-Type": "application/json", "x-request-id": reqId }, apiKey ? { "x-api-key": apiKey } : {});
    const body = {
      subfolder: activeScope.subfolder, doc_id: activeScope.doc_id, query: q, tag: null, ask_tutor: true,
      use_web_search: false, free_chat: Boolean(typeof freeChatMode !== "undefined" && freeChatMode),
      agent_id: effAgentId, provider: providerEl.value, model: modelEl.value.trim() || null, api_key: apiKey || null,
      top_k: ragConfig.top_k, retrieval_mode: ragConfig.retrieval_mode, rrf_k: ragConfig.rrf_k, temperature: ragConfig.temperature,
    };
    const res = await areaFetch("/api/chats/" + encodeURIComponent(splitState.chatId) + "/turn/stream", { method: "POST", headers: headers, signal: controller.signal, body: JSON.stringify(body) });
    if (res.status === 499 || controller.signal.aborted || version !== areaVersion) { return; }
    if (!res.ok) { const err = await safeJson(res); throw new Error((err && err.detail) || "Split chat failed."); }
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let buf = "", doneSession = null;
    const onEv = function (raw) {
      if (controller.signal.aborted || version !== areaVersion) { return; }
      let ev = "message", lines = [];
      for (const ln of raw.split(/\r?\n/)) { if (ln.startsWith("event:")) { ev = ln.slice(6).trim(); } else if (ln.startsWith("data:")) { lines.push(ln.slice(5).trim()); } }
      if (!lines.length) { return; }
      let p = null; try { p = JSON.parse(lines.join("\n")); } catch (_e) { return; }
      if (ev === "token") { pending.streamingText += String(p.delta || ""); scheduleSplitStreamRender(); }
      else if (ev === "done") { doneSession = p; }
      else if (ev === "error") { throw new Error((p && p.detail) || "Split chat error"); }
    };
    while (true) {
      const step = await reader.read(); if (step.done) { break; }
      if (controller.signal.aborted || version !== areaVersion) { try { await reader.cancel(); } catch (_e) {} return; }
      buf += decoder.decode(step.value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) !== -1) { const ch = buf.slice(0, idx); buf = buf.slice(idx + 2); if (ch.trim()) { onEv(ch); } }
    }
    buf += decoder.decode(); if (buf.trim()) { onEv(buf); }
    if (controller.signal.aborted || version !== areaVersion) { return; }
    if (doneSession && Array.isArray(doneSession.turns)) { splitState.turns = doneSession.turns; }
    else { pending.loadingTutor = false; pending.tutor = { answer: pending.streamingText.trim() || "Stopped.", cited_titles: [], knowledge_gap_detected: false }; }
    renderSplitChatStream(); await loadRecentChats(); syncSplitSelectors(); refreshBudget();
  } catch (err) {
    if ((err && err.name === "AbortError") || controller.signal.aborted || version !== areaVersion) { return; }
    pending.loadingTutor = false; pending.tutor = { answer: (err && err.message) || "Request failed.", cited_titles: [], knowledge_gap_detected: false };
    renderSplitChatStream();
  } finally {
    if (splitState.controller === controller) { splitState.controller = null; splitState.reqId = null; syncSplitSubmitBtn(false); }
  }
}
async function openSplitThread(chatId) {
  abortSplitRequest();
  if (!chatId) { splitState.chatId = null; splitState.turns = []; renderSplitChatStream(); syncSplitSelectors(); return; }
  const version = areaVersion, free = Boolean(typeof freeChatMode !== "undefined" && freeChatMode);
  const res = await areaFetch("/api/chats/" + encodeURIComponent(chatId) + (free ? "?free_chat=true" : ""));
  if (!res.ok || version !== areaVersion) { return; }
  const session = await safeJson(res);
  splitState.chatId = session.chat_id || chatId; splitState.turns = session.turns || [];
  if (session.last_agent_id) { splitState.agentId = session.last_agent_id; }
  syncSplitSelectors(); renderSplitChatStream();
}
function renderSplitGuide() {
  const box = document.getElementById("split-guide-scroll"); if (!box) { return; }
  const guides = typeof cachedGuides !== "undefined" && Array.isArray(cachedGuides) ? cachedGuides : [];
  const g = guides.find(function (item) { return item.doc_id === splitState.guideId; }) || guides[0];
  if (!g) { box.innerHTML = "<div class='wb-empty'>" + escapeHtml(t("sp_no_guides")) + "</div>"; return; }
  splitState.guideId = g.doc_id;
  box.innerHTML = "<h2 style='margin:0;font-size:calc(1.2rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(g.title) + "</h2>"
    + (g.sections || []).map(function (s) {
      return "<section style='padding:0.9rem 1rem;border-radius:0.85rem;background:var(--surface-raised);border:1px solid var(--border-subtle)'><h3 style='margin:0 0 0.5rem;font-size:calc(1rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(s.section_title) + "</h3><div class='md-body text-sm leading-relaxed flex flex-col gap-2'>" + formatMarkdown(s.content || "", false, 3) + "</div></section>";
    }).join("");
}
async function openSplitView(preset) {
  const menu = document.getElementById("split-mode-menu");
  if (menu && typeof menu.hidePopover === "function") { try { menu.hidePopover(); } catch (_e) {} }
  if (preset === "close") { closeSplitView(); return; }
  splitState.open = true;
  if (preset === "board-h" || preset === "board-v") {
    splitState.orientation = preset === "board-h" ? "horizontal" : "vertical";
    splitState.bMode = "chat";
    if (!wbViewOpen && typeof openWorkBoardView === "function") { await openWorkBoardView(); }
  } else if (preset === "guide-v") {
    splitState.orientation = "vertical"; splitState.bMode = "guide";
    if (wbViewOpen && typeof closeWorkBoardView === "function") { closeWorkBoardView(); document.getElementById("workspace-shell").classList.remove("hidden"); }
    if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
  } else {
    splitState.orientation = "vertical"; splitState.bMode = "chat";
    if (wbViewOpen && typeof closeWorkBoardView === "function") { closeWorkBoardView(); document.getElementById("workspace-shell").classList.remove("hidden"); }
  }
  syncSplitSelectors(); applySplitLayout();
  if (splitState.bMode === "guide") { renderSplitGuide(); } else { renderSplitChatStream(); }
}
function closeSplitView() {
  abortSplitRequest(); splitState.open = false; applySplitLayout();
}
function resetSplitOnAreaChange() {
  abortSplitRequest(); splitState.chatId = null; splitState.turns = []; splitState.guideId = "";
  if (splitState.open) { syncSplitSelectors(); renderSplitChatStream(); renderSplitGuide(); }
}
async function sendTaskToSplitChat(task) {
  if (!task) { return; }
  if (!splitState.open || splitState.bMode !== "chat") { await openSplitView(wbViewOpen ? "board-h" : "chat-v"); }
  const qEl = document.getElementById("split-query");
  const ctx = "Task: " + task.title + (task.due_date ? " (due " + task.due_date + ")" : "") + (task.description ? "\nNotes: " + task.description : "") + "\n\nHelp me plan or draft the next steps for this task.";
  if (qEl) { qEl.value = ctx; qEl.focus(); }
}
function bindSplitResizer() {
  const resizer = document.getElementById("split-resizer"), main = document.getElementById("main-content");
  if (!resizer || !main) { return; }
  let dragging = false;
  const setRatio = function (next) {
    splitState.ratio = Math.max(25, Math.min(75, Math.round(next)));
    main.style.setProperty("--split-a", splitState.ratio + "%");
    resizer.setAttribute("aria-valuenow", String(splitState.ratio));
  };
  resizer.addEventListener("pointerdown", function (e) {
    if (e.button !== 0) { return; }
    dragging = true; resizer.classList.add("is-dragging"); resizer.setPointerCapture(e.pointerId);
  });
  resizer.addEventListener("pointermove", function (e) {
    if (!dragging) { return; }
    const rect = main.getBoundingClientRect();
    const pct = splitState.orientation === "vertical" ? ((e.clientX - rect.left) / rect.width) * 100 : ((e.clientY - rect.top) / rect.height) * 100;
    setRatio(pct);
  });
  const endDrag = function () { dragging = false; resizer.classList.remove("is-dragging"); };
  resizer.addEventListener("pointerup", endDrag); resizer.addEventListener("lostpointercapture", endDrag);
  resizer.addEventListener("keydown", function (e) {
    const dec = splitState.orientation === "vertical" ? "ArrowLeft" : "ArrowUp";
    const inc = splitState.orientation === "vertical" ? "ArrowRight" : "ArrowDown";
    if (e.key === dec) { e.preventDefault(); setRatio(splitState.ratio - 5); }
    else if (e.key === inc) { e.preventDefault(); setRatio(splitState.ratio + 5); }
  });
}
function bindSplitUX() {
  document.querySelectorAll("[data-split-preset]").forEach(function (btn) {
    btn.addEventListener("click", function () { openSplitView(btn.getAttribute("data-split-preset")); });
  });
  document.querySelectorAll("[data-split-b-mode]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      splitState.bMode = btn.getAttribute("data-split-b-mode") || "chat";
      if (splitState.bMode === "guide" && typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      syncSplitSelectors(); applySplitLayout();
      if (splitState.bMode === "guide") { renderSplitGuide(); } else { renderSplitChatStream(); }
    });
  });
  const flipBtn = document.getElementById("split-flip-btn"), closeBtn = document.getElementById("split-close-btn");
  if (flipBtn) { flipBtn.addEventListener("click", function () { splitState.orientation = splitState.orientation === "vertical" ? "horizontal" : "vertical"; applySplitLayout(); }); }
  if (closeBtn) { closeBtn.addEventListener("click", closeSplitView); }
  const agSel = document.getElementById("split-agent-select"), thSel = document.getElementById("split-thread-select"), newBtn = document.getElementById("split-new-chat-btn"), gSel = document.getElementById("split-guide-select");
  if (agSel) { agSel.addEventListener("change", function () { splitState.agentId = agSel.value; renderSplitChatStream(); }); }
  if (thSel) { thSel.addEventListener("change", function () { openSplitThread(thSel.value); }); }
  if (newBtn) { newBtn.addEventListener("click", function () { openSplitThread(""); }); }
  if (gSel) { gSel.addEventListener("change", function () { splitState.guideId = gSel.value; renderSplitGuide(); }); }
  const gExt = document.getElementById("split-guide-extract-btn");
  if (gExt) { gExt.addEventListener("click", function () { if (splitState.guideId && typeof extractTasksToBoard === "function") { extractTasksToBoard({ doc_id: splitState.guideId }); } }); }
  const form = document.getElementById("split-chat-form"), qEl = document.getElementById("split-query"), subBtn = document.getElementById("split-submit-btn");
  if (form) { form.addEventListener("submit", function (e) { e.preventDefault(); if (splitState.controller) { abortSplitRequest(); return; } runSplitChatSubmit(); }); }
  if (subBtn) { subBtn.addEventListener("click", function (e) { if (splitState.controller) { e.preventDefault(); abortSplitRequest(); } }); }
  if (qEl) {
    qEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (e.isComposing || e.keyCode === 229) { return; }
        if (form) { form.requestSubmit(); }
      }
    });
  }
  window.addEventListener("resize", function () { if (splitState.open) { applySplitLayout(); } });
  bindSplitResizer();
}
"""
