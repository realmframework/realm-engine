"""Readable clustered 2D Knowledge Graph with silky zoom, clean typography, and bottom inspector."""

from features.ui.graph_hud_script import GRAPH_HUD_SCRIPT

GRAPH_SCRIPT: str = GRAPH_HUD_SCRIPT + r"""
let graphAnimFrame = null, graphRunning = false, graphResizeCleanup = null, graphScope = "active";
function stopGraphSimulation() {
  graphRunning = false;
  if (graphAnimFrame) { cancelAnimationFrame(graphAnimFrame); graphAnimFrame = null; }
  if (graphResizeCleanup) { graphResizeCleanup(); graphResizeCleanup = null; }
  document.getElementById("workspace-shell").classList.remove("hidden");
  if (typeof setAmbientGraphPause === "function") { setAmbientGraphPause(false); }
}
async function openGraphGuide(node) {
  if (!selectedAreas().includes(node.area) && !await switchKnowledgeArea(node.area, false)) { return; }
  const version = areaVersion, guides = await loadGuidesCatalog(null);
  const guide = guides.find(function (g) { return g.doc_id === node.doc_id || g.area === node.area && g.doc_id === node.area + "::" + node.doc_id; });
  if (version !== areaVersion) { return; }
  if (!guide) { areaStatus(t("st_doc_missing_ws")); return; }
  stopGraphSimulation();
  await renderGuideReader(guide, null, node.section_index ?? -1);
}
async function openGraphView(scope) {
  graphScope = scope || graphScope;
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  const operation = currentScrollId, version = areaVersion;
  currentChatId = null; currentTurns = [];
  if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); }
  document.getElementById("chat-stream").replaceChildren(); renderRecentChats();
  await setViewMode(true, true);
  if (operation !== currentScrollId || version !== areaVersion) { return; }
  renderTutor(null); chunksHeader.classList.add("hidden");
  document.getElementById("stream-divider").classList.add("hidden");
  const container = document.getElementById("graph-view");
  container.classList.remove("hidden"); document.getElementById("workspace-shell").classList.add("hidden");
  if (typeof setAmbientGraphPause === "function") { setAmbientGraphPause(true); }
  if (!knowledgeAreas.length) {
    container.innerHTML = "<div class='w-full h-full flex flex-col items-center justify-center gap-4 px-6 text-center'><h2 class='text-xl font-medium text-[#EEF2F8]'>" + escapeHtml(t("no_ws_empty_t")) + "</h2><p class='text-sm text-[#A0B0C8] max-w-md'>" + escapeHtml(t("no_ws_empty_d")) + "</p><div class='flex flex-wrap items-center justify-center gap-2.5 pt-2'><button type='button' data-new-area class='px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 transition'>" + escapeHtml(t("new_area_btn")) + "</button><button id='empty-graph-link-btn' type='button' class='px-4 py-2 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs text-[#EEF2F8] transition'>" + escapeHtml(t("open_vault")) + "</button></div></div>";
    bindAreaButtons(container);
    const gb = document.getElementById("empty-graph-link-btn"); if (gb) { gb.addEventListener("click", linkExistingFolder); }
    return;
  }
  container.innerHTML = "<p role='status' class='p-6 text-sm text-[#A0B0C8]'>" + escapeHtml(t("graph_loading")) + "</p>";
  let data;
  try {
    const response = await areaFetch("/api/graph?all_areas=" + String(graphScope === "universe"));
    if (!response.ok) { throw new Error("Graph could not be loaded. Select the area again and retry."); }
    data = await safeJson(response);
  } catch (error) {
    if (operation === currentScrollId) { container.textContent = error.message; }
    return;
  }
  if (operation !== currentScrollId || version !== areaVersion) { return; }
  const nodes = (data.nodes || []).filter(n => graphScope === "active" || n.type !== "section");
  const areas = data.areas || [], byId = new Map(nodes.map(n => [n.id, n]));
  const links = (data.links || []).filter(l => byId.has(l.source) && byId.has(l.target));
  const degree = new Map();
  links.forEach(function (l) { degree.set(l.source, (degree.get(l.source) || 0) + 1); degree.set(l.target, (degree.get(l.target) || 0) + 1); });
  const docTotal = nodes.filter(n => n.type === "doc").length, dense = docTotal > 18;
  container.innerHTML = buildGraphShellHtml(graphScope, areas, docTotal, links.length);
  container.querySelectorAll("[data-graph-scope]").forEach(btn => btn.addEventListener("click", () => openGraphView(btn.dataset.graphScope)));
  const canvas = document.getElementById("knowledge-graph-canvas"), ctx = canvas.getContext("2d");
  const filter = document.getElementById("graph-filter-input"), labelsBtn = document.getElementById("graph-labels-btn");
  const focusBanner = document.getElementById("graph-focus-banner"), focusLabelEl = document.getElementById("graph-focus-label");
  const clearFocusBtn = document.getElementById("graph-clear-focus-btn"), zoomPctEl = document.getElementById("graph-zoom-pct");
  const controlsBtn = document.getElementById("graph-controls-toggle"), controlsPanel = document.getElementById("graph-controls-panel");
  const filterDot = document.getElementById("graph-filter-dot");
  const inspectorEl = document.getElementById("graph-inspector-line"), defaultInspectorHtml = inspectorEl ? inspectorEl.innerHTML : "";
  const isReduced = () => typeof prefersReducedMotion === "function" ? prefersReducedMotion() : window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const { centers, adj } = layoutConstellation(areas, nodes, links);
  nodes.forEach(function (n) {
    n.tx = n.x; n.ty = n.y; n.vx = 0; n.vy = 0;
    const deg = degree.get(n.id) || 1;
    n.r = n.type === "area" ? 14 : n.type === "hub" ? Math.min(12, 8 + Math.sqrt(deg) * 1.0) : n.type === "doc" ? Math.min(8, 5 + Math.sqrt(deg) * 0.6) : 4;
  });
  let width = 900, height = 700, dpr = 1, zoom = 1, camX = 0, camY = 0, tZoom = 1, tCamX = 0, tCamY = 0, animatingCam = false;
  let panVx = 0, panVy = 0, term = "", labelMode = "smart", focused = null, hovered = null;
  let dragging = null, panning = false, moved = false, downX = 0, downY = 0, clock = 0, lastTs = 0, lastPct = "";
  function syncZoomBadge() {
    if (!zoomPctEl) { return; }
    const next = Math.round(zoom * 100) + "%";
    if (next !== lastPct) { lastPct = next; zoomPctEl.textContent = next; }
  }
  function syncInspector(node) {
    if (!inspectorEl) { return; }
    inspectorEl.innerHTML = node ? buildGraphInspectorHtml(node, degree.get(node.id) || 0, node === focused) : defaultInspectorHtml;
  }
  function physics() {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        if (a.area !== b.area) { continue; }
        const dx = b.x - a.x || 0.1, dy = b.y - a.y || 0.1, d2 = dx * dx + dy * dy;
        if (d2 > 22000) { continue; }
        const dist = Math.sqrt(Math.max(180, d2)), force = 1350 / Math.max(180, d2);
        a.vx -= dx / dist * force; a.vy -= dy / dist * force; b.vx += dx / dist * force; b.vy += dy / dist * force;
      }
    }
    nodes.forEach(function (n) {
      if (n === dragging || n.type === "area") { return; }
      n.vx = (n.vx + (n.tx - n.x) * 0.055) * 0.7; n.vy = (n.vy + (n.ty - n.y) * 0.055) * 0.7;
      n.x += n.vx; n.y += n.vy;
    });
  }
  function fitNodes(subset, immediate) {
    const list = subset && subset.length ? subset : nodes;
    if (!list.length) {
      tZoom = 1; tCamX = 0; tCamY = 0; panVx = 0; panVy = 0;
      if (immediate || reduced) { zoom = 1; camX = 0; camY = 0; animatingCam = false; syncZoomBadge(); }
      return;
    }
    const minX = Math.min(...list.map(n => n.x)) - 110, maxX = Math.max(...list.map(n => n.x)) + 110;
    const minY = Math.min(...list.map(n => n.y)) - 90, maxY = Math.max(...list.map(n => n.y)) + 100;
    tZoom = Math.max(0.24, Math.min(1.6, (width - 96) / Math.max(180, maxX - minX), (height - 135) / Math.max(180, maxY - minY)));
    tCamX = -(minX + maxX) / 2 * tZoom; tCamY = -(minY + maxY) / 2 * tZoom;
    panVx = 0; panVy = 0;
    if (immediate || reduced) { zoom = tZoom; camX = tCamX; camY = tCamY; animatingCam = false; syncZoomBadge(); }
    else { animatingCam = true; }
  }
  function activeNeighborhood(centerNode) {
    const s = new Set();
    if (!centerNode) { return s; }
    s.add(centerNode.id); (adj.get(centerNode.id) || []).forEach(id => s.add(id));
    return s;
  }
  function setFocus(node) {
    focused = node || null;
    if (focused) {
      const nb = activeNeighborhood(focused), subset = nodes.filter(n => nb.has(n.id));
      const count = subset.filter(n => n.type === "doc").length;
      if (focusLabelEl) { focusLabelEl.textContent = (focused.type === "hub" ? t("graph_topic_prefix") : t("graph_cluster_prefix")) + focused.label + " (" + t("graph_guides_n", { docs: count }) + ")"; }
      if (focusBanner) { focusBanner.hidden = false; }
      fitNodes(subset, false);
    } else {
      if (focusBanner) { focusBanner.hidden = true; }
      fitNodes(nodes, false);
    }
    guideList(); syncInspector(hovered || focused); draw();
  }
  function resize() {
    const rect = canvas.getBoundingClientRect();
    width = rect.width || 900; height = rect.height || 700; dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    fitNodes(focused ? nodes.filter(n => activeNeighborhood(focused).has(n.id)) : nodes, true); draw();
  }
  function matchesFilter(n) {
    return !term || n.label.toLowerCase().includes(term) || n.area.includes(term) || (n.tags || []).some(t => t.toLowerCase().includes(term));
  }
  function nodeTint(n, pal) {
    if (areas.length > 1) { return n.area_color || pal.accent; }
    if (n.type === "area") { return pal.accent; }
    return n.clusterIdx >= 0 ? pal.clusters[n.clusterIdx % pal.clusters.length] : pal.accent;
  }
  function draw() {
    const pal = graphThemeColors(), nodeScale = Math.pow(zoom, 0.65), fontScale = Math.pow(zoom, 0.82);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, width, height);
    drawGraphBackdrop(ctx, width, height, zoom, camX, camY, pal, centers, areas);
    const activeCenter = hovered || focused, focusSet = activeNeighborhood(activeCenter);
    const hasSpotlight = Boolean(activeCenter), lowNoise = links.length > 55 && !hasSpotlight && !term;
    links.forEach(function (link, idx) {
      const a = byId.get(link.source), b = byId.get(link.target);
      if (!a || !b) { return; }
      const vis = matchesFilter(a) && matchesFilter(b);
      const hot = hasSpotlight && (link.source === activeCenter.id || link.target === activeCenter.id);
      if (focused && !hovered && !hot && !(focusSet.has(link.source) && focusSet.has(link.target))) {
        ctx.globalAlpha = 0.035; ctx.strokeStyle = pal.isDark ? "rgba(238,242,248,0.35)" : "rgba(15,23,42,0.28)";
        ctx.lineWidth = 0.7 / zoom; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); return;
      }
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, curve = (idx % 2 === 0 ? 1 : -1) * 0.09;
      const cx = mx - dy * curve, cy = my + dx * curve;
      ctx.globalAlpha = !vis ? 0.03 : hot ? 0.85 : hasSpotlight ? 0.06 : lowNoise ? (pal.isDark ? 0.12 : 0.16) : (pal.isDark ? 0.28 : 0.36);
      ctx.strokeStyle = hot ? nodeTint(activeCenter, pal) : nodeTint(b, pal);
      ctx.lineWidth = (hot ? 2.0 : lowNoise ? 0.85 : 1.1) / zoom;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo(cx, cy, b.x, b.y); ctx.stroke();
      if (!reduced && vis && (hot || (!hasSpotlight && (!lowNoise || idx % 5 === 0)))) {
        const u = ((clock * (hot ? 0.36 : 0.14) + idx * 0.23) % 1), inv = 1 - u;
        const px = inv * inv * a.x + 2 * inv * u * cx + u * u * b.x, py = inv * inv * a.y + 2 * inv * u * cy + u * u * b.y;
        ctx.globalAlpha = hot ? 0.9 : 0.38; ctx.fillStyle = hot ? "#FFFFFF" : nodeTint(b, pal);
        ctx.beginPath(); ctx.arc(px, py, (hot ? 2.3 : 1.4) / zoom, 0, Math.PI * 2); ctx.fill();
      }
    });
    nodes.forEach(function (n) {
      const vis = matchesFilter(n), inFocus = !hasSpotlight || focusSet.has(n.id), isHov = n === hovered || n === focused;
      const tint = nodeTint(n, pal), r = (n.r + (isHov ? 2.8 : 0)) / nodeScale;
      ctx.globalAlpha = !vis ? 0.07 : inFocus ? 1 : 0.14;
      const haloR = r * (n.type === "area" ? 3.1 : isHov ? 2.8 : 1.9);
      const halo = ctx.createRadialGradient(n.x, n.y, r * 0.2, n.x, n.y, haloR);
      halo.addColorStop(0, hexAlpha(tint, n.type === "area" || isHov ? 0.5 : 0.25)); halo.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(n.x, n.y, haloR, 0, Math.PI * 2); ctx.fill();
      if (n.type === "area" || isHov) {
        const pulse = reduced ? 1 : (1 + 0.1 * Math.sin(clock * 2.1));
        ctx.strokeStyle = hexAlpha(tint, 0.58); ctx.lineWidth = 1.4 / zoom;
        ctx.beginPath(); ctx.arc(n.x, n.y, r * 1.55 * pulse, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      if (n.type === "hub") { ctx.fillStyle = pal.surface; ctx.fill(); ctx.strokeStyle = tint; ctx.lineWidth = 2.1 / nodeScale; ctx.stroke(); }
      else {
        ctx.fillStyle = tint; ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,0.68)"; ctx.beginPath(); ctx.arc(n.x - r * 0.25, n.y - r * 0.25, r * 0.3, 0, Math.PI * 2); ctx.fill();
      }
    });
    const placed = [], pri = { area: 0, hub: 1, doc: 2, section: 3 };
    const docFade = labelMode === "all" || !dense || Boolean(focused) || Boolean(term) ? 1 : labelMode === "hubs" ? 0 : Math.max(0, Math.min(1, (zoom - 0.85) / 0.45));
    const ordered = nodes.toSorted(function (a, b) {
      if (a === hovered) { return -1; } if (b === hovered) { return 1; }
      if (a === focused) { return -1; } if (b === focused) { return 1; }
      if (pri[a.type] !== pri[b.type]) { return pri[a.type] - pri[b.type]; }
      return (degree.get(b.id) || 0) - (degree.get(a.id) || 0);
    });
    for (const n of ordered) {
      if (!matchesFilter(n)) { continue; }
      const isHov = n === hovered, isFoc = n === focused, inFocus = !hasSpotlight || focusSet.has(n.id);
      if (hasSpotlight && !inFocus && !isHov && !isFoc) { continue; }
      const isDocLike = n.type === "doc" || n.type === "section";
      const alpha = isHov || isFoc ? 1 : (isDocLike ? (hasSpotlight && inFocus ? 0.94 : docFade * 0.92) : 0.94);
      if (alpha < 0.06) { continue; }
      if (!isHov && !isFoc && placed.length >= (focused || term ? 42 : 34)) { break; }
      const baseFs = isHov ? 13.5 : n.type === "area" ? 13.5 : n.type === "hub" ? 12.2 : 11.2;
      const fs = baseFs / fontScale;
      ctx.font = (n.type === "area" || n.type === "hub" || isHov || isFoc ? "600 " : "500 ") + fs + "px Inter, system-ui, sans-serif";
      const rawName = n.type === "area" ? areaTitle(n.label) : (n.type === "hub" && n.docTotal ? (n.label + " · " + n.docTotal) : n.label);
      const text = isHov ? rawName : (rawName.length > 30 ? rawName.slice(0, 29) + "…" : rawName);
      const tw = ctx.measureText(text).width, padX = (isHov || isFoc ? 10 : 4) / zoom, padY = (isHov || isFoc ? 5 : 2) / zoom;
      const pw = tw + padX * 2, ph = fs + padY * 2, nr = (n.r + (isHov ? 2.8 : 0)) / nodeScale, gap = nr + 10 / zoom, m = 5 / zoom;
      const spots = [[n.x, n.y + gap + ph * 0.5], [n.x, n.y - gap - ph * 0.5], [n.x + pw / 2 + gap, n.y], [n.x - pw / 2 - gap, n.y]];
      for (const [cx, cy] of spots) {
        const box = { l: cx - pw / 2 - m, r: cx + pw / 2 + m, t: cy - ph / 2 - m, b: cy + ph / 2 + m };
        if (!isHov && placed.some(o => box.l < o.r && box.r > o.l && box.t < o.b && box.b > o.t)) { continue; }
        ctx.globalAlpha = alpha; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        if (isHov || isFoc || n.type === "area") {
          ctx.fillStyle = pal.isDark ? "rgba(11,16,32,0.92)" : "rgba(255,255,255,0.96)";
          ctx.strokeStyle = isHov || isFoc ? nodeTint(n, pal) : hexAlpha(nodeTint(n, pal), 0.45);
          ctx.lineWidth = (isHov ? 1.5 : 1.0) / zoom;
          ctx.beginPath(); ctx.roundRect(cx - pw / 2, cy - ph / 2, pw, ph, ph / 2); ctx.fill(); ctx.stroke();
        } else {
          ctx.lineJoin = "round"; ctx.strokeStyle = pal.bg; ctx.lineWidth = 4.5 / zoom; ctx.strokeText(text, cx, cy);
        }
        ctx.fillStyle = n.type === "area" || n.type === "hub" ? nodeTint(n, pal) : (pal.isDark ? "#EEF2F8" : "#0B1020");
        ctx.fillText(text, cx, cy + 0.4 / zoom);
        placed.push(box); break;
      }
    }
    ctx.restore(); ctx.globalAlpha = 1; syncZoomBadge();
  }
  function guideList() {
    const list = document.getElementById("graph-guide-list"), fSet = focused ? activeNeighborhood(focused) : null;
    list.innerHTML = nodes.filter(n => (n.type === "doc" || n.type === "section") && matchesFilter(n) && (!fSet || fSet.has(n.id))).map(function (n) {
      const lbl = areaTitle(n.area) + " · " + (n.type === "section" ? "Section: " : "") + n.label;
      return "<button type='button' data-graph-node='" + escapeHtml(n.id) + "' class='text-sm text-left text-[#A0B0C8] hover:text-[#EEF2F8] py-2'>" + escapeHtml(lbl) + "</button>";
    }).join("") || "<p class='text-sm text-[#738196] py-2'>" + escapeHtml(t("graph_no_guides")) + "</p>";
    list.querySelectorAll("[data-graph-node]").forEach(b => b.addEventListener("click", () => openGraphGuide(byId.get(b.dataset.graphNode))));
  }
  function position(e) { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; }
  function hit(pt) {
    const x = (pt.x - width / 2 - camX) / zoom, y = (pt.y - height / 2 - camY) / zoom, s = Math.pow(zoom, 0.65);
    return nodes.find(n => matchesFilter(n) && Math.hypot(n.x - x, n.y - y) < (n.r + 11) / s);
  }
  function smoothZoomAt(pt, factor) {
    panVx = 0; panVy = 0;
    const nextZoom = Math.max(0.22, Math.min(3.2, tZoom * factor));
    const wx = (pt.x - width / 2 - tCamX) / tZoom, wy = (pt.y - height / 2 - tCamY) / tZoom;
    tZoom = nextZoom; tCamX = pt.x - width / 2 - wx * tZoom; tCamY = pt.y - height / 2 - wy * tZoom;
    if (isReduced()) { zoom = tZoom; camX = tCamX; camY = tCamY; draw(); } else { animatingCam = true; }
  }
  canvas.addEventListener("wheel", function (e) {
    e.preventDefault();
    const dy = normalizeWheelDelta(e), sens = e.ctrlKey ? 0.0065 : 0.0018;
    smoothZoomAt(position(e), Math.exp(-dy * sens));
  }, { passive: false });
  function setControlsOpen(open) {
    if (!controlsPanel || !controlsBtn) { return; }
    controlsPanel.hidden = !open; controlsBtn.setAttribute("aria-expanded", String(open)); controlsBtn.classList.toggle("text-[#4BB8E8]", open);
  }
  if (controlsBtn && controlsPanel) { controlsBtn.addEventListener("click", () => setControlsOpen(controlsPanel.hidden)); }
  canvas.addEventListener("pointerdown", function (e) {
    if (controlsPanel && !controlsPanel.hidden) { setControlsOpen(false); }
    const pt = position(e); downX = pt.x; downY = pt.y; moved = false; animatingCam = false; panVx = 0; panVy = 0;
    tZoom = zoom; tCamX = camX; tCamY = camY;
    dragging = hit(pt); panning = !dragging; canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", function (e) {
    const pt = position(e), dx = pt.x - downX, dy = pt.y - downY;
    if (dragging || panning) {
      if (Math.hypot(dx, dy) > 3) { moved = true; }
      if (dragging) { dragging.x += dx / zoom; dragging.y += dy / zoom; dragging.tx = dragging.x; dragging.ty = dragging.y; }
      else { camX += dx; camY += dy; tCamX = camX; tCamY = camY; panVx = dx * 0.45 + panVx * 0.55; panVy = dy * 0.45 + panVy * 0.55; }
      downX = pt.x; downY = pt.y;
    } else {
      const next = hit(pt);
      if (next !== hovered) { hovered = next; syncInspector(hovered || focused); }
      canvas.style.cursor = hovered ? "pointer" : "grab";
    }
    if (isReduced()) { draw(); }
  });
  canvas.addEventListener("pointerleave", function () { if (hovered) { hovered = null; syncInspector(focused); if (isReduced()) { draw(); } } });
  canvas.addEventListener("pointerup", function () {
    const target = dragging; dragging = null; panning = false;
    if (moved) { return; }
    panVx = 0; panVy = 0;
    if (!target) { if (focused) { setFocus(null); } return; }
    if (target.doc_id) { openGraphGuide(target); }
    else { setFocus(target === focused ? null : target); }
  });
  canvas.addEventListener("pointercancel", function () { dragging = null; panning = false; panVx = 0; panVy = 0; });
  filter.addEventListener("input", function () { term = filter.value.toLowerCase().trim(); if (filterDot) { filterDot.hidden = !term; } guideList(); draw(); });
  if (labelsBtn) {
    const modes = [["smart", t("graph_lbl_smart")], ["all", t("graph_lbl_all")], ["hubs", t("graph_lbl_hubs")]];
    labelsBtn.addEventListener("click", function () {
      const next = modes[(modes.findIndex(m => m[0] === labelMode) + 1) % modes.length];
      labelMode = next[0]; labelsBtn.textContent = next[1]; draw();
    });
  }
  if (clearFocusBtn) { clearFocusBtn.addEventListener("click", () => setFocus(null)); }
  document.getElementById("graph-zoom-in").addEventListener("click", () => smoothZoomAt({ x: width / 2, y: height / 2 }, 1.18));
  document.getElementById("graph-zoom-out").addEventListener("click", () => smoothZoomAt({ x: width / 2, y: height / 2 }, 1 / 1.18));
  document.getElementById("graph-reset-btn").addEventListener("click", function () { term = ""; filter.value = ""; if (filterDot) { filterDot.hidden = true; } setFocus(null); });
  const onKey = function (e) {
    if (container.classList.contains("hidden") || document.querySelector("dialog[open]")) { return; }
    const ae = document.activeElement, tag = ae && ae.tagName;
    if (e.key === "Escape") { if (controlsPanel && !controlsPanel.hidden) { setControlsOpen(false); if (controlsBtn) { controlsBtn.focus({ preventScroll: true }); } } else if (focused) { setFocus(null); } }
    else if (e.key === "/" && ae !== filter && tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT" && !(ae && ae.isContentEditable)) { e.preventDefault(); setControlsOpen(true); filter.focus(); }
  };
  const observer = new ResizeObserver(resize); observer.observe(container); window.addEventListener("resize", resize); window.addEventListener("keydown", onKey);
  graphResizeCleanup = function () { observer.disconnect(); window.removeEventListener("resize", resize); window.removeEventListener("keydown", onKey); window.syncGraphMotion = null; };
  graphRunning = true; for (let i = 0; i < 45; i++) { physics(); } resize(); guideList();
  function tick(ts) {
    if (!graphRunning || isReduced()) { graphAnimFrame = null; return; }
    if (document.hidden) { lastTs = 0; graphAnimFrame = requestAnimationFrame(tick); return; }
    const dt = lastTs ? Math.min(0.05, Math.max(0.001, (ts - lastTs) / 1000)) : 0.016;
    lastTs = ts; clock += dt;
    if (animatingCam) {
      const a = 1 - Math.exp(-dt * 11);
      zoom += (tZoom - zoom) * a; camX += (tCamX - camX) * a; camY += (tCamY - camY) * a;
      if (Math.abs(tZoom - zoom) < 0.0015 && Math.abs(tCamX - camX) < 0.4 && Math.abs(tCamY - camY) < 0.4) { zoom = tZoom; camX = tCamX; camY = tCamY; animatingCam = false; }
    } else if (!panning && (Math.abs(panVx) > 0.12 || Math.abs(panVy) > 0.12)) {
      const f = Math.exp(-dt * 10), step = dt / 0.016;
      camX += panVx * step; camY += panVy * step; tCamX = camX; tCamY = camY; panVx *= f; panVy *= f;
    }
    draw(); graphAnimFrame = requestAnimationFrame(tick);
  }
  window.syncGraphMotion = function () {
    if (!graphRunning) { return; }
    if (isReduced()) { if (graphAnimFrame) { cancelAnimationFrame(graphAnimFrame); graphAnimFrame = null; } draw(); } else if (!graphAnimFrame) { lastTs = 0; graphAnimFrame = requestAnimationFrame(tick); }
  }; window.syncGraphMotion();
}
"""
