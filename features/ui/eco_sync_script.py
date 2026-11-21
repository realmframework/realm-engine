"""Phase 5 client logic: Eco Mode UI, Zero-AI instant term highlighting, and incremental auto-sync."""

ECO_SYNC_SCRIPT: str = r"""
let lastKnownSyncVersion = -1, syncPollTimer = null;

function syncEcoModeUI(cfg) {
  const on = Boolean(cfg && cfg.eco_mode);
  const toggle = document.getElementById("eco-mode-toggle"), badge = document.getElementById("eco-mode-badge");
  if (toggle) { toggle.checked = on; }
  if (badge) {
    badge.textContent = on ? "ON" : "OFF";
    badge.className = "text-xs font-mono " + (on ? "text-[#38D399]" : "text-[#738196]");
  }
}

function setEcoModeUI(enabled) {
  const on = Boolean(enabled);
  if (typeof workspaceConfig === "object" && workspaceConfig) { workspaceConfig.eco_mode = on; }
  syncEcoModeUI(workspaceConfig);
  if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ eco_mode: on }); }
  if (typeof showToast === "function") { showToast(on ? t("eco_toast_on") : t("eco_toast_off"), 2800); }
}

function checkEcoRamSuggestion(ramGb) {
  const hint = document.getElementById("eco-mode-ram-hint");
  if (!hint) { return; }
  const low = Number(ramGb || 0) > 0 && Number(ramGb || 0) <= 8;
  hint.hidden = !low || Boolean(workspaceConfig && workspaceConfig.eco_mode);
  if (!hint.hidden) { hint.textContent = t("eco_ram_tip", { ram: ramGb }); }
}

function highlightSearchTerms(rootEl, queryText) {
  if (!rootEl || !queryText) { return; }
  const tokens = Array.from(new Set(String(queryText).toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(w => w.length >= 3))).slice(0, 8);
  if (!tokens.length) { return; }
  const escaped = tokens.map(tok => tok.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const re = new RegExp("(?<![\\p{L}\\p{N}_])(" + escaped.join("|") + ")(?![\\p{L}\\p{N}_])", "giu");
  rootEl.querySelectorAll(".md-prose").forEach(function (prose) {
    const walker = document.createTreeWalker(prose, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    let cur;
    while ((cur = walker.nextNode())) {
      const parent = cur.parentElement;
      if (!parent || parent.closest("code, pre, mark, script, style, button")) { continue; }
      if (re.test(cur.nodeValue || "")) { nodes.push(cur); }
      re.lastIndex = 0;
    }
    for (const txtNode of nodes) {
      const val = txtNode.nodeValue || "";
      re.lastIndex = 0;
      const frag = document.createDocumentFragment();
      let last = 0, m;
      while ((m = re.exec(val)) !== null) {
        if (m.index > last) { frag.appendChild(document.createTextNode(val.slice(last, m.index))); }
        const mark = document.createElement("mark");
        mark.className = "search-hit-mark";
        mark.textContent = m[0];
        frag.appendChild(mark);
        last = m.index + m[0].length;
      }
      if (last < val.length) { frag.appendChild(document.createTextNode(val.slice(last))); }
      if (txtNode.parentNode) { txtNode.parentNode.replaceChild(frag, txtNode); }
    }
  });
}

async function pollIncrementalSync() {
  if (document.hidden || !knowledgeAreas.length || areaSwitching) { return; }
  const version = areaVersion;
  try {
    const res = await fetch("/api/workspace/sync-status");
    if (!res.ok || version !== areaVersion) { return; }
    const st = await safeJson(res);
    if (version !== areaVersion) { return; }
    const ver = Number(st.sync_version || 0);
    if (lastKnownSyncVersion === -1) { lastKnownSyncVersion = ver; return; }
    if (ver > lastKnownSyncVersion) {
      lastKnownSyncVersion = ver;
      const changed = Array.isArray(st.last_changed_files) ? st.last_changed_files.length : 1;
      await loadWorkspace();
      await loadGuidesCatalog(null);
      if (version === areaVersion && document.getElementById("library-view")) { await openLibraryCatalog(selectedTag); }
      if (version === areaVersion && typeof showToast === "function") { showToast(t("sync_auto_toast", { n: changed }), 3200); }
    }
  } catch (_e) {}
}

function bindEcoSyncUX() {
  const ecoToggle = document.getElementById("eco-mode-toggle");
  if (ecoToggle) {
    ecoToggle.addEventListener("change", function () { setEcoModeUI(ecoToggle.checked); });
  }
  syncEcoModeUI(workspaceConfig);
  if (!syncPollTimer) { syncPollTimer = setInterval(pollIncrementalSync, 8000); }
}
"""
