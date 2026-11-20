"""Area-aware radial galaxies, Retina canvas interactions and accessible navigation."""

GRAPH_SCRIPT: str = r"""
let graphAnimFrame = null, graphRunning = false, graphResizeCleanup = null, graphScope = "active";
function stopGraphSimulation() {
  graphRunning = false;
  if (graphAnimFrame) { cancelAnimationFrame(graphAnimFrame); graphAnimFrame = null; }
  if (graphResizeCleanup) { graphResizeCleanup(); graphResizeCleanup = null; }
  document.getElementById("workspace-shell").classList.remove("hidden");
}
async function openGraphGuide(node) {
  if (!selectedAreas().includes(node.area) && !await switchKnowledgeArea(node.area, false)) { return; }
  const version = areaVersion, guides = await loadGuidesCatalog(null);
  const guide = guides.find(function (g) { return g.doc_id === node.doc_id || g.area === node.area && g.doc_id === node.area + "::" + node.doc_id; });
  if (version !== areaVersion) { return; }
  if (!guide) { areaStatus("This guide is no longer in its knowledge area."); return; }
  stopGraphSimulation();
  await renderGuideReader(guide, null, node.section_index ?? -1);
}
async function openGraphView(scope) {
  graphScope = scope || graphScope;
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation();
  const operation = currentScrollId, version = areaVersion;
  currentChatId = null; currentTurns = [];
  document.getElementById("chat-stream").innerHTML = ""; renderRecentChats();
  await setViewMode(true, true);
  if (operation !== currentScrollId || version !== areaVersion) { return; }
  renderTutor(null); chunksHeader.classList.add("hidden");
  document.getElementById("stream-divider").classList.add("hidden");
  const container = document.getElementById("graph-view");
  container.classList.remove("hidden"); document.getElementById("workspace-shell").classList.add("hidden");
  container.innerHTML = "<p role='status' class='p-6 text-sm text-[#A0B0C8]'>Loading knowledge galaxies...</p>";
  let data;
  try {
    const response = await areaFetch("/api/graph?all_areas=" + String(graphScope === "universe"));
    if (!response.ok) { throw new Error("Graph could not be loaded. Select the area again and retry."); }
    data = await response.json();
  } catch (error) {
    if (operation === currentScrollId) { container.textContent = error.message; }
    return;
  }
  if (operation !== currentScrollId || version !== areaVersion) { return; }
  const nodes = (data.nodes || []).filter(n => graphScope === "active" || n.type !== "section");
  const areas = data.areas || [];
  const byId = new Map(nodes.map(function (n) { return [n.id, n]; }));
  const links = (data.links || []).filter(link => byId.has(link.source) && byId.has(link.target));
  const buttons = [["active", "Active Area Only"], ["universe", "All Knowledge Areas (Universe View)"]].map(function (s) {
    return `<button type='button' data-graph-scope='${s[0]}' aria-pressed='${graphScope === s[0]}'
      class='rounded-lg px-2 py-1 text-xs border border-white/15 ${graphScope === s[0] ? "bg-white/10 text-white" : "text-[#A0B0C8]"}'>${modeCopy(s[0] === "active" ? "This Workspace" : "All Workspaces", s[1])}</button>`;
  }).join("");
  const legend = areas.map(function (a) {
    return "<span class='flex items-center gap-1.5'><span aria-hidden='true' class='w-2 h-2 rounded-full' style='background:"
      + a.color + "'></span>" + escapeHtml(areaLabel(a.name)) + "</span>";
  }).join("");
  container.innerHTML = `<div class='absolute top-4 left-16 right-4 sm:right-auto z-10 rounded-xl bg-[#0B1020]/95 border border-white/10 p-3 flex flex-col gap-2'>
    <div role='group' aria-label='Graph knowledge area scope' class='flex flex-wrap gap-1'>${buttons}</div>
    <div class='flex items-center gap-2'>
      <input id='graph-filter-input' aria-label='Filter graph guides and topics' type='search' placeholder='Filter nodes...'
        class='min-w-0 flex-1 rounded-lg bg-[#04060F] px-2 py-1 text-xs'/>
      <button id='graph-reset-btn' type='button' class='text-xs text-[#A0B0C8]'>Reset View</button>
      <span class='text-[11px] text-[#738196]'>${nodes.filter(n => n.type === "doc").length} guides</span>
    </div></div>
    <canvas id='knowledge-graph-canvas' aria-label='Knowledge graph. Use Browse graph guides below for keyboard navigation.'
      class='w-full h-full block touch-none'></canvas>
    <div id='graph-tooltip' class='hidden pointer-events-none absolute z-20 max-w-xs bg-[#0B1020] border border-white/15 rounded-lg px-3 py-2 text-xs'></div>
    <div class='absolute bottom-4 left-4 right-4 z-10 bg-[#0B1020]/95 rounded-xl border border-white/10 p-3'>
      <div class='flex flex-wrap gap-3 text-[11px] text-[#A0B0C8] mb-2'>${legend}</div>
      <details><summary class='text-xs cursor-pointer text-[#A0B0C8]'>Browse graph guides · Scroll to zoom · Drag to pan</summary>
        <div id='graph-guide-list' class='max-h-40 overflow-y-auto flex flex-col'></div></details>
    </div>`;
  container.querySelectorAll("[data-graph-scope]").forEach(function (button) {
    button.addEventListener("click", function () { openGraphView(button.dataset.graphScope); });
  });
  const canvas = document.getElementById("knowledge-graph-canvas"), ctx = canvas.getContext("2d");
  const tooltip = document.getElementById("graph-tooltip"), filter = document.getElementById("graph-filter-input");
  let width = 900, height = 700, dpr = 1, zoom = 1, camX = 0, camY = 0, term = "";
  let dragging = null, panning = false, moved = false, downX = 0, downY = 0, hovered = null;
  const centers = new Map(areas.map(function (area, i) {
    const radius = areas.length === 1 ? 0 : 650 * Math.sqrt(i), angle = i * 2.399963;
    return [area.name, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius }];
  }));
  areas.forEach(function (area) {
    const center = centers.get(area.name), members = nodes.filter(n => n.area === area.name);
    const hubs = members.filter(n => n.type === "hub"), docs = members.filter(n => n.type === "doc");
    const place = function (node, x, y) { node.x = x; node.y = y; };
    const root = members.find(n => n.type === "area");
    if (root) { place(root, center.x, center.y); }
    hubs.forEach(function (node, i) {
      const angle = i * Math.PI * 2 / Math.max(1, hubs.length) - Math.PI / 2;
      place(node, center.x + Math.cos(angle) * 90, center.y + Math.sin(angle) * 90);
    });
    docs.forEach(function (node, i) {
      const angle = i * Math.PI * 2 / Math.max(1, docs.length) + Math.PI / 5;
      const orbit = 170 + Math.floor(i / 16) * 50;
      place(node, center.x + Math.cos(angle) * orbit, center.y + Math.sin(angle) * orbit);
      const sections = members.filter(n => n.type === "section" && n.doc_id === node.doc_id);
      sections.forEach(function (section, index) {
        const spread = sections.length === 1 ? 0 : (index / (sections.length - 1) - 0.5) * Math.PI * 1.35;
        const distance = 65 + Math.floor(index / 10) * 35;
        place(section, node.x + Math.cos(angle + spread) * distance, node.y + Math.sin(angle + spread) * distance);
      });
    });
  });
  nodes.forEach(function (node) {
    node.tx = node.x; node.ty = node.y; node.vx = 0; node.vy = 0;
    node.r = { area: 10, hub: 7.5, doc: 5, section: 3.5 }[node.type] || 4;
  });
  function physics() {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        if (a.area !== b.area) { continue; }
        const dx = b.x - a.x || 0.1, dy = b.y - a.y || 0.1;
        const d2 = Math.max(100, dx * dx + dy * dy), distance = Math.sqrt(d2), force = 850 / d2;
        a.vx -= dx / distance * force; a.vy -= dy / distance * force;
        b.vx += dx / distance * force; b.vy += dy / distance * force;
      }
    }
    nodes.forEach(function (node) {
      if (node === dragging || node.type === "area") { return; }
      node.vx = (node.vx + (node.tx - node.x) * 0.03) * 0.72;
      node.vy = (node.vy + (node.ty - node.y) * 0.03) * 0.72;
      node.x += node.vx; node.y += node.vy;
    });
  }
  const bounds = {
    left: Math.min(0, ...nodes.map(n => n.tx)) - 65, right: Math.max(0, ...nodes.map(n => n.tx)) + 65,
    top: Math.min(0, ...nodes.map(n => n.ty)) - 45, bottom: Math.max(0, ...nodes.map(n => n.ty)) + 65
  };
  function resetCamera() {
    zoom = Math.max(0.1, Math.min(1.6, (width - 64) / (bounds.right - bounds.left), (height - 240) / (bounds.bottom - bounds.top)));
    camX = -(bounds.left + bounds.right) / 2 * zoom;
    camY = -(bounds.top + bounds.bottom) / 2 * zoom + 24;
  }
  function resize() {
    const rect = canvas.getBoundingClientRect();
    width = rect.width || 900; height = rect.height || 700; dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    resetCamera(); draw();
  }
  function visible(node) {
    return !term || node.label.toLowerCase().includes(term) || node.area.includes(term)
      || (node.tags || []).some(t => t.toLowerCase().includes(term));
  }
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, width, height);
    ctx.save(); ctx.translate(width / 2 + camX, height / 2 + camY); ctx.scale(zoom, zoom);
    links.forEach(function (link) {
      const a = byId.get(link.source), b = byId.get(link.target);
      if (!a || !b) { return; }
      ctx.globalAlpha = visible(a) && visible(b) ? 0.32 : 0.04;
      ctx.strokeStyle = a.area_color; ctx.lineWidth = 1 / zoom;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    });
    nodes.forEach(function (node) {
      ctx.globalAlpha = visible(node) ? 1 : 0.1;
      ctx.fillStyle = node.area_color;
      ctx.shadowColor = node.area_color; ctx.shadowBlur = node.type === "area" ? 24 : 0;
      ctx.beginPath(); ctx.arc(node.x, node.y, (node.r + (node === hovered ? 2 : 0)) / zoom, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
    });
    const labels = [], priority = { area: 0, doc: 1, hub: 2, section: 3 };
    nodes.slice().sort((a, b) => priority[a.type] - priority[b.type]).forEach(function (node) {
      const detailed = graphScope === "active" || zoom >= 0.8;
      if (!visible(node) || !(node.type === "area" || detailed || node === hovered || term)) { return; }
      ctx.globalAlpha = 1;
      ctx.fillStyle = node.type === "area" ? node.area_color : "#EEF2F8";
      ctx.font = (node.type === "area" ? "600 " : "") + (11 / zoom) + "px Inter, sans-serif";
      ctx.textAlign = "center";
      const fullLabel = node.type === "area" ? areaLabel(node.label) : node.label;
      const label = fullLabel.length > 32 ? fullLabel.slice(0, 31) + "…" : fullLabel;
      const w = ctx.measureText(label).width, h = 15 / zoom, gap = (node.r + 14) / zoom;
      const positions = [[node.x, node.y + gap], [node.x, node.y - gap],
        [node.x + w / 2 + gap, node.y], [node.x - w / 2 - gap, node.y]];
      for (const [x, y] of positions) {
        const box = { left: x - w / 2 - 3 / zoom, right: x + w / 2 + 3 / zoom, top: y - h, bottom: y + 3 / zoom };
        if (node !== hovered && labels.some(b => box.left < b.right && box.right > b.left && box.top < b.bottom && box.bottom > b.top)) { continue; }
        ctx.fillText(label, x, y); labels.push(box); break;
      }
    });
    ctx.restore(); ctx.globalAlpha = 1;
  }
  function guideList() {
    const list = document.getElementById("graph-guide-list");
    list.innerHTML = nodes.filter(n => (n.type === "doc" || n.type === "section") && visible(n)).map(function (node) {
      const label = areaLabel(node.area) + " · " + (node.type === "section" ? "Section: " : "") + node.label;
      return "<button type='button' data-graph-node='" + escapeHtml(node.id)
        + "' class='text-xs text-left text-[#A0B0C8] hover:text-white py-2'>" + escapeHtml(label) + "</button>";
    }).join("") || "<p class='text-xs text-[#738196] py-2'>No matching guides. Upload a document to add one.</p>";
    list.querySelectorAll("[data-graph-node]").forEach(function (button) {
      button.addEventListener("click", function () { openGraphGuide(byId.get(button.dataset.graphNode)); });
    });
  }
  function position(event) {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }
  function hit(point) {
    const x = (point.x - width / 2 - camX) / zoom, y = (point.y - height / 2 - camY) / zoom;
    return nodes.find(n => visible(n) && Math.hypot(n.x - x, n.y - y) < (n.r + 10) / zoom);
  }
  canvas.addEventListener("wheel", function (event) {
    event.preventDefault(); zoom = Math.max(0.1, Math.min(3, zoom * (event.deltaY < 0 ? 1.1 : 0.9))); draw();
  }, { passive: false });
  canvas.addEventListener("pointerdown", function (event) {
    const point = position(event); downX = point.x; downY = point.y; moved = false;
    dragging = hit(point); panning = !dragging; canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", function (event) {
    const point = position(event), dx = point.x - downX, dy = point.y - downY;
    if (dragging || panning) {
      if (Math.hypot(dx, dy) > 3) { moved = true; }
      if (dragging) { dragging.x += dx / zoom; dragging.y += dy / zoom; }
      else { camX += dx; camY += dy; }
      downX = point.x; downY = point.y;
    } else {
      hovered = hit(point); canvas.style.cursor = hovered ? "pointer" : "grab";
      tooltip.classList.toggle("hidden", !hovered);
      if (hovered) {
        tooltip.textContent = areaLabel(hovered.area) + " · " + hovered.label;
        tooltip.style.left = Math.max(8, Math.min(width - 220, point.x + 12)) + "px";
        tooltip.style.top = Math.max(100, point.y - 30) + "px";
      }
    }
    draw();
  });
  canvas.addEventListener("pointerleave", function () { tooltip.classList.add("hidden"); hovered = null; draw(); });
  canvas.addEventListener("pointerup", function () {
    const target = dragging; dragging = null; panning = false;
    if (!target || moved) { return; }
    if (target.doc_id) { openGraphGuide(target); }
    else { term = target.type === "area" ? target.area : target.label.toLowerCase(); filter.value = term; guideList(); draw(); }
  });
  canvas.addEventListener("pointercancel", function () { dragging = null; panning = false; });
  filter.addEventListener("input", function () { term = filter.value.toLowerCase().trim(); guideList(); draw(); });
  document.getElementById("graph-reset-btn").addEventListener("click", function () {
    term = ""; filter.value = ""; resetCamera(); guideList(); draw();
  });
  const observer = new ResizeObserver(resize);
  observer.observe(container); window.addEventListener("resize", resize);
  graphResizeCleanup = function () { observer.disconnect(); window.removeEventListener("resize", resize); };
  graphRunning = true; resize(); guideList();
  let steps = 0;
  function settle() {
    if (!graphRunning) { return; }
    physics(); draw();
    if (++steps < 80) { graphAnimFrame = requestAnimationFrame(settle); }
    else { graphAnimFrame = null; }
  }
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    for (let i = 0; i < 80; i++) { physics(); }
    draw();
  } else { graphAnimFrame = requestAnimationFrame(settle); }
}
"""
