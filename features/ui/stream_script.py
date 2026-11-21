"""Live SSE token streaming, global drag-and-drop upload, and opt-in Web Search UI controls."""

STREAM_SCRIPT: str = r"""
let streamRenderScheduled = false, webSearchForMessage = false;
document.documentElement.classList.add("switch" in HTMLInputElement.prototype ? "has-native-switch" : "no-native-switch");
function scheduleStreamRender() {
  if (streamRenderScheduled) { return; }
  streamRenderScheduled = true;
  requestAnimationFrame(function () {
    streamRenderScheduled = false;
    const idx = currentTurns.length - 1, last = idx >= 0 ? currentTurns[idx] : null;
    const bodyEl = last && last.loadingTutor && last.streamingText ? document.getElementById("turn-" + idx + "-stream-body") : null;
    if (bodyEl) {
      bodyEl.innerHTML = formatMarkdown(last.streamingText, true, 3) + "<span class='stream-cursor' aria-hidden='true'></span>";
      return;
    }
    renderChatStream();
  });
}
async function runStreamingTurn(chatId, bodyObj, headers, signal, pendingTurn, turnIdx, version) {
  const res = await areaFetch("/api/chats/" + encodeURIComponent(chatId) + "/turn/stream", {
    method: "POST", headers: headers, signal: signal, body: JSON.stringify(bodyObj)
  });
  const stale = function () { return signal.aborted || (version !== undefined && version !== areaVersion); };
  if (res.status === 499 || stale()) { return { stopped: true }; }
  if (!res.ok) {
    const err = await safeJson(res);
    throw new Error((err && err.detail) || "Answer failed.");
  }
  if (!res.body || !res.body.getReader) {
    return { fallback: true };
  }
  const reader = res.body.getReader(), decoder = new TextDecoder();
  let buffer = "", doneSession = null, stoppedFlag = false;
  const handleEvent = function (rawEvent) {
    if (stale()) { return; }
    const lines = rawEvent.split(/\r?\n/);
    let evName = "message", dataLines = [];
    for (const ln of lines) {
      if (ln.startsWith("event:")) { evName = ln.slice(6).trim(); }
      else if (ln.startsWith("data:")) { dataLines.push(ln.slice(5).trim()); }
    }
    if (!dataLines.length) { return; }
    let payload = null;
    try { payload = JSON.parse(dataLines.join("\n")); } catch (_e) { return; }
    if (evName === "retrieval") {
      pendingTurn.results = payload.results || [];
      pendingTurn.router_label = (payload.rag_config && payload.rag_config.router_label) || (payload.router_decision && payload.router_decision.label) || "";
      renderChatStream();
    } else if (evName === "thinking") {
      const had = Boolean(pendingTurn.streamingThinking);
      pendingTurn.streamingThinking = (pendingTurn.streamingThinking || "") + String(payload.delta || "");
      const liveEl = document.getElementById("inspector-live-thinking");
      if (liveEl) { liveEl.textContent = pendingTurn.streamingThinking; liveEl.scrollTop = liveEl.scrollHeight; }
      else if (!had || (typeof inspectorOpen !== "undefined" && inspectorOpen)) { scheduleStreamRender(); }
    } else if (evName === "token") {
      pendingTurn.streamingText = (pendingTurn.streamingText || "") + String(payload.delta || "");
      scheduleStreamRender();
    } else if (evName === "telemetry" && payload.context_usage) {
      lastContextUsage = payload.context_usage;
    } else if (evName === "done") {
      doneSession = payload;
      if (payload && payload.context_usage) { lastContextUsage = payload.context_usage; }
    } else if (evName === "stopped") {
      stoppedFlag = true;
      const partial = String((payload && payload.partial) || pendingTurn.streamingText || "").trim();
      pendingTurn.loadingTutor = false; pendingTurn.stopped = true;
      if (partial) { pendingTurn.tutor = { answer: partial, cited_titles: [], knowledge_gap_detected: false, recommended_topics: [] }; }
      renderChatStream();
    } else if (evName === "error") {
      throw new Error((payload && payload.detail) || "Streaming request failed.");
    }
  };
  while (true) {
    const step = await reader.read();
    if (step.done) { break; }
    if (stale()) { try { await reader.cancel(); } catch (_e) {} return { stopped: true }; }
    buffer += decoder.decode(step.value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      if (chunk.trim()) { handleEvent(chunk); }
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) { handleEvent(buffer); }
  if (stale()) { return { stopped: true }; }
  if (doneSession) {
    const rLabel = (doneSession.router_decision && doneSession.router_decision.label) || pendingTurn.router_label || "";
    currentTurns = (doneSession.turns || []).map(function (t, i) {
      return Object.assign({}, t, {
        router_label: i === turnIdx ? rLabel : (currentTurns[i] && currentTurns[i].router_label) || "",
        collapsed: i === turnIdx ? Boolean(t.ask_tutor) : (currentTurns[i] ? currentTurns[i].collapsed : true)
      });
    });
    renderChatStream(); await loadRecentChats(); refreshBudget();
    if (doneSession.notice && typeof showToast === "function") { showToast(doneSession.notice, 5200); }
    if (typeof handleVoiceLoopAfterAnswer === "function") { handleVoiceLoopAfterAnswer(); }
    return { done: true };
  }
  if (!stoppedFlag) {
    pendingTurn.loadingTutor = false;
    const partial = String(pendingTurn.streamingText || "").trim();
    pendingTurn.tutor = { answer: partial || "Stream ended unexpectedly before completing the answer.", cited_titles: [], knowledge_gap_detected: !partial, recommended_topics: [] };
    renderChatStream();
    return { done: true };
  }
  return { stopped: true };
}
async function readEntryFiles(entry, prefix, out) {
  if (!entry) { return; }
  if (entry.isFile) {
    await new Promise(function (resolve) {
      entry.file(function (file) {
        try { Object.defineProperty(file, "_relPath", { value: prefix ? prefix + "/" + file.name : file.name, configurable: true }); } catch (_e) {}
        out.push(file); resolve();
      }, function () { resolve(); });
    });
  } else if (entry.isDirectory) {
    const reader = entry.createReader(), nextPrefix = prefix ? prefix + "/" + entry.name : entry.name;
    let batch = [];
    do {
      batch = await new Promise(function (resolve) { reader.readEntries(resolve, function () { resolve([]); }); });
      for (const child of batch) { await readEntryFiles(child, nextPrefix, out); }
    } while (batch.length > 0);
  }
}
async function extractDroppedFiles(dataTransfer) {
  if (!dataTransfer) { return []; }
  const items = Array.from(dataTransfer.items || []);
  const entries = items.map(function (it) { return it.webkitGetAsEntry ? it.webkitGetAsEntry() : null; }).filter(Boolean);
  if (entries.some(function (en) { return en.isDirectory; })) {
    const collected = [];
    for (const en of entries) { await readEntryFiles(en, "", collected); }
    return collected;
  }
  return Array.from(dataTransfer.files || []);
}
let revealAutoSyncPending = false;
async function revealWorkspaceFolder(subfolder) {
  try {
    const res = await areaFetch("/api/workspace/reveal-folder", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subfolder: subfolder || "" }) });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || "Could not open folder."); }
    revealAutoSyncPending = true;
    showToast(t("toast_opened_sync_hint", { path: data.path || "workspace" }));
  } catch (err) { areaStatus(err.message || t("err_open_folder")); }
}
async function syncWorkspaceFolder(silent) {
  const version = areaVersion;
  try {
    const res = await areaFetch("/api/workspace/sync-folder", { method: "POST" });
    const data = await safeJson(res);
    if (!res.ok || version !== areaVersion) { return; }
    applyWorkspacePayload(data); await loadGuidesCatalog(null);
    if (version === areaVersion && isActiveView && !currentChatId) { await openLibraryCatalog(selectedTag); }
    if (!silent) { showToast(t("toast_synced_lib", { n: data.doc_count || 0 })); }
  } catch (err) { if (!silent) { areaStatus(err.message || t("st_sync_err")); } }
}
function setUploadProgress(visible, title, countText, pct, fileText) {
  const panel = document.getElementById("upload-progress-panel");
  if (!panel) { return; }
  panel.hidden = !visible;
  if (!visible) { return; }
  const tEl = document.getElementById("upload-progress-title"), cEl = document.getElementById("upload-progress-count"), bEl = document.getElementById("upload-progress-bar"), fEl = document.getElementById("upload-progress-file");
  if (tEl && title !== undefined) { tEl.textContent = title; }
  if (cEl && countText !== undefined) { cEl.textContent = countText; }
  if (bEl && pct !== undefined) { const clamped = Math.max(2, Math.min(100, pct)); bEl.style.width = clamped + "%"; bEl.setAttribute("aria-valuenow", String(Math.round(clamped))); }
  if (fEl && fileText !== undefined) { fEl.textContent = fileText; }
}
async function importNativeFolder() {
  const btn = document.getElementById("import-native-folder-btn"), confirmBtn = document.getElementById("confirm-upload-btn"), statusEl = document.getElementById("upload-status");
  if (btn && btn.disabled) { return; }
  const subfolder = destinationValue("upload"), saveArea = document.getElementById("upload-save-area").value || activeKnowledgeArea;
  if (subfolder === null) { return; }
  const anon = Boolean(document.getElementById("cfg-anonymize-uploads").checked), version = areaVersion;
  if (btn) { btn.disabled = true; } if (confirmBtn) { confirmBtn.disabled = true; }
  if (statusEl) { statusEl.textContent = "Importing folder…"; }
  setUploadProgress(true, "Choose a folder in Finder / Explorer…", "", 8, "Waiting for folder selection");
  let donePayload = null, cancelled = false, folderName = "folder";
  try {
    const res = await areaFetch("/api/workspace/import-native-folder/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subfolder: subfolder, area: saveArea, anonymize: anon })
    });
    if (!res.ok) { const err = await safeJson(res); throw new Error(err.detail || "Folder import failed."); }
    if (!res.body || !res.body.getReader) { throw new Error("Streaming folder import is unavailable in this browser."); }
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let buf = "";
    const handle = function (rawEv) {
      let ev = "message", lines = [];
      for (const ln of rawEv.split(/\r?\n/)) { if (ln.startsWith("event:")) { ev = ln.slice(6).trim(); } else if (ln.startsWith("data:")) { lines.push(ln.slice(5).trim()); } }
      if (!lines.length) { return; }
      let p = null; try { p = JSON.parse(lines.join("\n")); } catch (_e) { return; }
      if (ev === "stage") { setUploadProgress(true, p.message || "Working…", p.stage === "indexing" ? "Indexing…" : "", p.stage === "indexing" ? 95 : 10, p.stage === "indexing" ? "Building search index & vectors — almost done" : "Waiting for folder selection"); }
      else if (ev === "start") { folderName = p.folder_name || "folder"; setUploadProgress(true, "Importing “" + folderName + "”…", "0 / " + (p.total || 0), 12, "Scanning files…"); }
      else if (ev === "progress") {
        const pct = p.total ? Math.round(12 + (p.done / p.total) * 78) : 50;
        setUploadProgress(true, "Importing “" + folderName + "”…", p.done + " / " + p.total, pct, p.current || "");
        if (statusEl) { statusEl.textContent = "Converted " + (p.imported || 0) + " guides (" + p.done + "/" + p.total + ")…"; }
      } else if (ev === "cancelled") { cancelled = true; }
      else if (ev === "done") { donePayload = p; setUploadProgress(true, "Import complete!", (p.imported_count || 0) + " guides", 100, ""); }
      else if (ev === "error") { throw new Error((p && p.detail) || "Could not import folder."); }
    };
    while (true) {
      const step = await reader.read();
      if (step.done) { break; }
      buf += decoder.decode(step.value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) !== -1) { const chunk = buf.slice(0, idx); buf = buf.slice(idx + 2); if (chunk.trim()) { handle(chunk); } }
    }
    buf += decoder.decode();
    if (buf.trim()) { handle(buf); }
    if (version !== areaVersion) { return; }
    if (cancelled || !donePayload) { if (statusEl) { statusEl.textContent = ""; } return; }
    uploadModal.close(); stageUploadFiles([]); applyWorkspacePayload(donePayload);
    selectedSubfolder = selectedAreas().length > 1 ? saveArea + (subfolder ? "/" + subfolder : "") : subfolder;
    showToast(t("toast_imported_folder", { n: donePayload.imported_count, folder: donePayload.folder_name || folderName, skipped: donePayload.skipped_count ? " (" + donePayload.skipped_count + " skipped)" : "" }));
    await loadGuidesCatalog(null);
    if (version === areaVersion && isActiveView && !currentChatId) { await openLibraryCatalog(selectedTag); }
  } catch (err) {
    if (statusEl) { statusEl.textContent = err.message || "Could not import folder."; }
  } finally { setUploadProgress(false); if (btn) { btn.disabled = false; } if (confirmBtn) { confirmBtn.disabled = false; } }
}
function bindGlobalDrop() {
  const nativeImportBtn = document.getElementById("import-native-folder-btn");
  if (nativeImportBtn) { nativeImportBtn.addEventListener("click", importNativeFolder); }
  const uploadLinkBtn = document.getElementById("upload-link-vault-btn");
  if (uploadLinkBtn) {
    uploadLinkBtn.addEventListener("click", function () {
      if (typeof uploadModal !== "undefined" && uploadModal && uploadModal.open) { uploadModal.close(); }
      if (typeof linkExistingFolder === "function") { linkExistingFolder(); }
    });
  }
  const overlay = document.getElementById("global-drop-overlay");
  if (!overlay) { return; }
  let dragDepth = 0;
  const hasFiles = function (e) { return e.dataTransfer && Array.from(e.dataTransfer.types || []).includes("Files"); };
  const hideOverlay = function () { dragDepth = 0; overlay.hidden = true; };
  window.addEventListener("dragenter", function (e) {
    if (!hasFiles(e) || (uploadModal && uploadModal.open)) { return; }
    e.preventDefault(); dragDepth += 1; overlay.hidden = false;
  });
  window.addEventListener("dragover", function (e) {
    if (!hasFiles(e) || (uploadModal && uploadModal.open)) { return; }
    e.preventDefault(); e.dataTransfer.dropEffect = "copy";
  });
  window.addEventListener("dragleave", function (e) {
    if (!hasFiles(e)) { return; }
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) { overlay.hidden = true; }
  });
  window.addEventListener("drop", async function (e) {
    if (!hasFiles(e)) { return; }
    if (uploadModal && uploadModal.open) { hideOverlay(); return; }
    e.preventDefault(); hideOverlay();
    const files = await extractDroppedFiles(e.dataTransfer);
    if (files.length) { openUploadDialog(); stageUploadFiles(files); }
  });
  window.addEventListener("blur", hideOverlay);
  window.addEventListener("focus", function () {
    if (revealAutoSyncPending) { revealAutoSyncPending = false; syncWorkspaceFolder(true); }
  });
}
function syncWebSearchUI(cfg) {
  const toggle = document.getElementById("web-search-toggle"), prov = document.getElementById("web-search-provider");
  const badge = document.getElementById("web-search-badge"), lockNote = document.getElementById("web-search-lock-note");
  const ollamaGrp = document.getElementById("web-search-ollama-key-group"), searxGrp = document.getElementById("web-search-searxng-group");
  const searxIn = document.getElementById("web-search-searxng-url"), keyStatus = document.getElementById("ollama-web-key-status");
  const chatBtn = document.getElementById("web-search-chat-btn");
  const locked = localOnly(), enabled = Boolean(cfg && cfg.web_search_enabled), provider = (cfg && cfg.web_search_provider) || "duckduckgo";
  const canUseWeb = !locked && enabled;
  if (!canUseWeb) { webSearchForMessage = false; }
  if (chatBtn) {
    chatBtn.hidden = !canUseWeb;
    chatBtn.setAttribute("aria-pressed", String(webSearchForMessage));
    const tip = webSearchForMessage ? t("web_btn_on") : t("web_btn_off");
    chatBtn.title = tip; chatBtn.setAttribute("aria-label", tip);
  }
  if (!toggle || !prov) { return; }
  toggle.checked = enabled; toggle.disabled = locked;
  prov.value = provider; prov.disabled = locked;
  if (searxIn && cfg && typeof cfg.searxng_url === "string") { searxIn.value = cfg.searxng_url; }
  if (lockNote) { lockNote.hidden = !locked; }
  if (ollamaGrp) { ollamaGrp.hidden = provider !== "ollama"; }
  if (searxGrp) { searxGrp.hidden = provider !== "searxng"; }
  if (badge) {
    badge.textContent = locked ? "LOCKED" : (enabled ? ("READY · " + provider.toUpperCase()) : "OFF");
    badge.className = "text-xs font-mono " + (locked ? "text-amber-300" : (enabled ? "text-[#38D399]" : "text-[#738196]"));
  }
  if (keyStatus) {
    const info = appKeyStatus.ollama_web;
    keyStatus.textContent = info && info.configured ? ("Ollama API key saved (" + (info.hint || "configured") + ")") : "Paste your OLLAMA_API_KEY from ollama.com/settings/keys.";
  }
}
function bindWebSearchControls() {
  const toggle = document.getElementById("web-search-toggle"), prov = document.getElementById("web-search-provider");
  const saveKeyBtn = document.getElementById("save-ollama-web-key-btn"), keyIn = document.getElementById("web-search-ollama-key");
  const saveSearxBtn = document.getElementById("save-searxng-btn"), searxIn = document.getElementById("web-search-searxng-url");
  const chatBtn = document.getElementById("web-search-chat-btn");
  if (chatBtn) {
    chatBtn.addEventListener("click", function () {
      if (localOnly() || !workspaceConfig || !workspaceConfig.web_search_enabled) { webSearchForMessage = false; syncWebSearchUI(workspaceConfig); return; }
      webSearchForMessage = !webSearchForMessage;
      syncWebSearchUI(workspaceConfig);
    });
  }
  if (toggle) {
    toggle.addEventListener("change", function () {
      if (localOnly()) { toggle.checked = false; return; }
      workspaceConfig = Object.assign({}, workspaceConfig, { web_search_enabled: Boolean(toggle.checked) });
      syncWebSearchUI(workspaceConfig);
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ web_search_enabled: Boolean(toggle.checked) }); }
    });
  }
  if (prov) {
    prov.addEventListener("change", function () {
      workspaceConfig = Object.assign({}, workspaceConfig, { web_search_provider: prov.value });
      syncWebSearchUI(workspaceConfig);
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ web_search_provider: prov.value }); }
    });
  }
  if (saveKeyBtn && keyIn) {
    saveKeyBtn.addEventListener("click", async function () {
      if (await saveAppApiKey("ollama_web", keyIn.value, keyIn)) { syncWebSearchUI(workspaceConfig); }
    });
  }
  if (saveSearxBtn && searxIn) {
    saveSearxBtn.addEventListener("click", function () {
      const url = searxIn.value.trim();
      workspaceConfig = Object.assign({}, workspaceConfig, { searxng_url: url });
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ searxng_url: url }); }
      areaStatus(t(url ? "st_searx_saved" : "st_searx_cleared"));
    });
  }
}
"""
