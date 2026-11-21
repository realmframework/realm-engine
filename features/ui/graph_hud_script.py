"""Theme color helpers, clustered sector layout, and frosted HUD for the 2D Knowledge Graph."""

GRAPH_HUD_SCRIPT: str = r"""
function graphThemeColors() {
  const rootStyle = getComputedStyle(document.documentElement);
  const bodyStyle = getComputedStyle(document.body);
  const accent = (rootStyle.getPropertyValue("--accent-seed") || "#4BB8E8").trim() || "#4BB8E8";
  const glow = (rootStyle.getPropertyValue("--accent-glow") || "#6366F1").trim() || "#6366F1";
  const meta = document.querySelector('meta[name="color-scheme"]');
  const mode = meta ? meta.content : "light dark";
  const isDark = mode === "dark" || (mode !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const resolvedBg = bodyStyle.backgroundColor, resolvedText = bodyStyle.color;
  const bg = (resolvedBg && resolvedBg !== "rgba(0, 0, 0, 0)" && resolvedBg !== "transparent") ? resolvedBg : (isDark ? "#04060F" : "#F3F7FC");
  const text = resolvedText || (isDark ? "#EEF2F8" : "#0B1020");
  const surface = isDark ? "#0B1020" : "#FFFFFF";
  const clusters = [accent, glow, "#34D399", "#F59E0B", "#F472B6", "#38BDF8", "#A78BFA", "#FB7185"];
  return { accent: accent, glow: glow, bg: bg, surface: surface, text: text, isDark: isDark, clusters: clusters };
}
function hexAlpha(hex, a) {
  const clean = /^#[0-9a-f]{6}$/i.test(hex || "") ? hex : "#4BB8E8";
  return "rgba(" + parseInt(clean.slice(1, 3), 16) + "," + parseInt(clean.slice(3, 5), 16) + "," + parseInt(clean.slice(5, 7), 16) + "," + a + ")";
}
function layoutConstellation(areas, nodes, links) {
  const adj = new Map();
  links.forEach(function (l) {
    if (!adj.has(l.source)) { adj.set(l.source, new Set()); }
    if (!adj.has(l.target)) { adj.set(l.target, new Set()); }
    adj.get(l.source).add(l.target); adj.get(l.target).add(l.source);
  });
  const centers = new Map(areas.map(function (area, i) {
    const areaDocs = nodes.filter(n => n.area === area.name && n.type === "doc").length;
    const spread = 620 + Math.sqrt(Math.max(1, areaDocs)) * 62;
    const radius = areas.length === 1 ? 0 : spread * Math.sqrt(i), angle = i * 2.399963;
    return [area.name, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius, color: area.color, maxR: 280 }];
  }));
  areas.forEach(function (area) {
    const center = centers.get(area.name), members = nodes.filter(n => n.area === area.name);
    const hubs = members.filter(n => n.type === "hub"), docs = members.filter(n => n.type === "doc");
    const root = members.find(n => n.type === "area");
    if (root) { root.x = center.x; root.y = center.y; root.clusterIdx = -1; }
    const hubCounts = new Map(hubs.map(h => [h.id, 0]));
    links.forEach(function (l) {
      if (hubCounts.has(l.source)) { hubCounts.set(l.source, hubCounts.get(l.source) + 1); }
      if (hubCounts.has(l.target)) { hubCounts.set(l.target, hubCounts.get(l.target) + 1); }
    });
    hubs.forEach(function (h, i) { h.clusterIdx = i; h.docTotal = Math.max(0, (hubCounts.get(h.id) || 1) - 1); });
    const buckets = new Map(hubs.map(h => [h.id, []])), orphanDocs = [];
    docs.forEach(function (doc) {
      const neighbors = Array.from(adj.get(doc.id) || []).filter(id => buckets.has(id));
      if (!neighbors.length) { doc.clusterIdx = -1; orphanDocs.push(doc); return; }
      neighbors.sort((a, b) => (hubCounts.get(a) || 999) - (hubCounts.get(b) || 999));
      const primary = neighbors[0], hubObj = hubs.find(h => h.id === primary);
      doc.clusterIdx = hubObj ? hubObj.clusterIdx : 0;
      buckets.get(primary).push(doc);
    });
    const groups = hubs.map(h => ({ hub: h, docs: buckets.get(h.id) || [] }));
    if (orphanDocs.length) { groups.push({ hub: null, docs: orphanDocs }); }
    const weights = groups.map(g => Math.max(1.35, Math.sqrt(g.docs.length + 1)));
    const totalWeight = weights.reduce((s, w) => s + w, 0) || 1;
    const hubOrbit = Math.max(165, 105 + hubs.length * 11 + Math.sqrt(docs.length) * 16);
    let cursor = -Math.PI / 2, maxR = hubOrbit + 160;
    groups.forEach(function (g, gi) {
      const span = (weights[gi] / totalWeight) * Math.PI * 2, mid = cursor + span / 2;
      if (g.hub) {
        g.hub.x = center.x + Math.cos(mid) * hubOrbit;
        g.hub.y = center.y + Math.sin(mid) * hubOrbit;
      }
      const nDocs = g.docs.length, perRing = Math.max(4, Math.round(span * 10));
      g.docs.forEach(function (doc, di) {
        const ring = Math.floor(di / perRing), slot = di % perRing;
        const countInRing = Math.min(perRing, nDocs - ring * perRing);
        const frac = countInRing <= 1 ? 0.5 : (slot + 0.5) / countInRing;
        const ang = cursor + span * (0.09 + frac * 0.82);
        const dist = hubOrbit + 132 + ring * 74 + (slot % 2) * 24;
        doc.x = center.x + Math.cos(ang) * dist; doc.y = center.y + Math.sin(ang) * dist;
        maxR = Math.max(maxR, dist + 60);
        const sections = members.filter(n => n.type === "section" && n.doc_id === doc.doc_id);
        sections.forEach(function (sec, si) {
          const spread = sections.length === 1 ? 0 : (si / (sections.length - 1) - 0.5) * Math.PI * 1.1;
          const sd = 76 + Math.floor(si / 8) * 34;
          sec.x = doc.x + Math.cos(ang + spread) * sd; sec.y = doc.y + Math.sin(ang + spread) * sd;
          sec.clusterIdx = doc.clusterIdx; maxR = Math.max(maxR, Math.hypot(sec.x - center.x, sec.y - center.y) + 45);
        });
      });
      cursor += span;
    });
    center.hubOrbit = hubOrbit; center.maxR = maxR;
  });
  return { centers: centers, adj: adj };
}
function normalizeWheelDelta(e) {
  let dy = e.deltaY;
  if (e.deltaMode === 1) { dy *= 20; }
  else if (e.deltaMode === 2) { dy *= 240; }
  return Math.max(-55, Math.min(55, dy));
}
function buildGraphInspectorHtml(node, count, isFocused) {
  const typeTitles = { area: t("graph_t_area"), hub: t("graph_t_hub"), doc: t("graph_t_doc"), section: t("graph_t_section") };
  const title = node.type === "area" ? areaTitle(node.label) : node.label;
  const tags = (node.tags || []).length ? "<span class='font-mono text-xs text-[#738196] truncate'>(" + escapeHtml(node.tags.slice(0, 4).join(", ")) + ")</span>" : "";
  const hint = node.doc_id ? t("graph_h_read") : (isFocused ? t("graph_h_unfocus") : t("graph_h_focus"));
  const linkLbl = count === 1 ? t("graph_link_1") : t("graph_links_n", { n: count });
  return "<div class='flex items-center gap-2 min-w-0 flex-1'>"
    + "<span class='px-2 py-0.5 rounded-full bg-[#4BB8E8]/15 text-[#4BB8E8] font-mono text-xs shrink-0'>" + escapeHtml(typeTitles[node.type] || "Node") + "</span>"
    + "<span class='font-medium text-[#EEF2F8] truncate'>" + escapeHtml(title) + "</span>"
    + "<span class='font-mono text-xs text-[#738196] shrink-0'>" + escapeHtml(linkLbl) + "</span>" + tags + "</div>"
    + "<span class='hidden sm:inline font-mono text-xs text-[#A0B0C8] shrink-0'>" + escapeHtml(hint) + "</span>";
}
function drawGraphBackdrop(ctx, width, height, zoom, camX, camY, pal, centers, areas) {
  const gridStep = Math.max(28, 54 * zoom), ox = ((width / 2 + camX) % gridStep + gridStep) % gridStep, oy = ((height / 2 + camY) % gridStep + gridStep) % gridStep;
  ctx.fillStyle = pal.isDark ? "rgba(238,242,248,0.09)" : "rgba(15,23,42,0.09)";
  ctx.beginPath();
  for (let gx = ox; gx < width; gx += gridStep) { for (let gy = oy; gy < height; gy += gridStep) { ctx.moveTo(gx + 0.85, gy); ctx.arc(gx, gy, 0.85, 0, Math.PI * 2); } }
  ctx.fill();
  ctx.save(); ctx.translate(width / 2 + camX, height / 2 + camY); ctx.scale(zoom, zoom);
  centers.forEach(function (c) {
    const tint = areas.length === 1 ? pal.accent : c.color, radMax = c.maxR || 320;
    const neb = ctx.createRadialGradient(c.x, c.y, 8, c.x, c.y, radMax);
    neb.addColorStop(0, hexAlpha(tint, pal.isDark ? 0.08 : 0.06));
    neb.addColorStop(0.55, hexAlpha(pal.glow, pal.isDark ? 0.035 : 0.02)); neb.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = neb; ctx.beginPath(); ctx.arc(c.x, c.y, radMax, 0, Math.PI * 2); ctx.fill();
    ctx.save(); ctx.setLineDash([4 / zoom, 10 / zoom]);
    ctx.strokeStyle = pal.isDark ? "rgba(238,242,248,0.06)" : "rgba(15,23,42,0.06)"; ctx.lineWidth = 1 / zoom;
    for (const rad of [c.hubOrbit || 165, (c.hubOrbit || 165) + 132]) { ctx.beginPath(); ctx.arc(c.x, c.y, rad, 0, Math.PI * 2); ctx.stroke(); }
    ctx.restore();
  });
}
function buildGraphShellHtml(graphScope, areas, docTotal, linkTotal) {
  const buttons = [["active", t("graph_active_area")], ["universe", t("graph_universe")]].map(function (s) {
    const on = graphScope === s[0];
    return `<button type='button' data-graph-scope='${s[0]}' aria-pressed='${on}'
      class='flex-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${on ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]"}'>${modeCopy(s[0] === "active" ? t("graph_this_ws") : t("graph_all_ws"), s[1])}</button>`;
  }).join("");
  const legend = areas.map(function (a) {
    return "<span class='flex items-center gap-1.5'><span aria-hidden='true' class='w-2 h-2 rounded-full' style='background:"
      + a.color + ";box-shadow:0 0 6px " + a.color + "'></span><span>" + escapeHtml(a.display_name || areaLabel(a.name)) + "</span></span>";
  }).join("");
  const tuneSvg = "<svg aria-hidden='true' class='w-4 h-4' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round'><path d='M4 7h16M4 17h16'/><circle cx='9' cy='7' r='2.2' fill='currentColor'/><circle cx='15' cy='17' r='2.2' fill='currentColor'/></svg>";
  const resetSvg = "<svg aria-hidden='true' class='w-3.5 h-3.5' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><path d='M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5'/></svg>";
  return `<h1 class='visually-hidden'>${escapeHtml(t("graph_view"))}</h1><div id='graph-focus-banner' hidden class='graph-hud absolute top-4 left-16 z-10 flex items-center gap-2.5 rounded-full px-3.5 py-1.5 text-xs text-[#EEF2F8]'>
      <span id='graph-focus-label' class='truncate max-w-[16rem] font-medium'></span>
      <button id='graph-clear-focus-btn' type='button' class='text-[#4BB8E8] hover:underline font-medium shrink-0'>${escapeHtml(t("graph_full_graph"))}</button>
    </div>
    <div class='absolute top-4 right-4 z-20 flex flex-col items-end gap-2'>
      <div class='flex items-center gap-2'>
        <span class='graph-hud hidden sm:inline-flex items-center rounded-full px-3 py-1.5 text-xs font-mono text-[#A0B0C8] select-none'>${escapeHtml(t("graph_guides_links", { docs: docTotal, links: linkTotal }))}</span>
        <button id='graph-controls-toggle' type='button' aria-expanded='false' aria-controls='graph-controls-panel' aria-label='${escapeHtml(t("graph_controls"))}' title='${escapeHtml(t("graph_controls"))} (/)'
          class='graph-hud relative h-9 w-9 rounded-full flex items-center justify-center text-[#A0B0C8] hover:text-[#EEF2F8] transition'>${tuneSvg}<span id='graph-filter-dot' hidden class='absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#4BB8E8]'></span></button>
      </div>
      <div id='graph-controls-panel' hidden class='graph-hud w-72 max-w-[calc(100vw-2rem)] rounded-2xl p-3.5 flex flex-col gap-3'>
        <div class='flex items-center justify-between'><span class='text-xs font-mono uppercase tracking-wider text-[#738196]'>${escapeHtml(t("graph_controls"))}</span><span class='text-xs font-mono text-[#738196]'>${escapeHtml(t("graph_guides_n", { docs: docTotal }))}</span></div>
        <div role='group' aria-label='Graph knowledge area scope' class='flex bg-[#04060F] p-1 rounded-xl border border-white/10 gap-1'>${buttons}</div>
        <input id='graph-filter-input' aria-label='Filter graph guides and topics' type='search' placeholder='${escapeHtml(t("graph_filter_ph"))}'
          class='w-full rounded-xl bg-[#04060F] border border-white/10 focus:border-[#4BB8E8] px-3 py-1.5 text-sm text-[#EEF2F8] outline-none'/>
        <div class='flex items-center justify-between gap-2'>
          <span class='text-xs text-[#A0B0C8]'>${escapeHtml(t("graph_node_labels"))}</span>
          <button id='graph-labels-btn' type='button'
            class='px-2.5 py-1 rounded-lg bg-[#04060F] border border-white/10 hover:border-[#4BB8E8] text-xs font-medium text-[#EEF2F8] transition'>${escapeHtml(t("graph_lbl_smart"))}</button>
        </div>
        <details class='border-t border-white/10 pt-2.5'><summary class='text-xs cursor-pointer text-[#A0B0C8] hover:text-[#EEF2F8]'>${escapeHtml(t("graph_browse_guides", { docs: docTotal }))}</summary>
          <div id='graph-guide-list' class='max-h-48 overflow-y-auto flex flex-col mt-1.5'></div></details>
      </div>
    </div>
    <canvas id='knowledge-graph-canvas' aria-label='Knowledge graph. Open Graph Controls to browse guides with keyboard.'
      class='w-full h-full block touch-none'></canvas>
    <div id='graph-inspector-line' aria-live='polite' class='graph-hud absolute bottom-4 left-4 right-44 sm:right-auto sm:max-w-xl z-10 rounded-full px-3.5 py-1.5 flex items-center gap-2.5 text-xs text-[#A0B0C8] min-h-[2rem]'>
      <div class='flex flex-wrap items-center gap-3'>${legend}</div>
      <span class='hidden md:inline font-mono text-xs text-[#738196]'>${escapeHtml(t("graph_hint_bar"))}</span>
    </div>
    <div class='graph-hud absolute bottom-4 right-4 z-10 rounded-full p-1 inline-flex items-center gap-0.5'>
      <button id='graph-zoom-out' type='button' aria-label='Zoom out' class='h-7 w-7 rounded-full flex items-center justify-center text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5'>−</button>
      <span id='graph-zoom-pct' class='px-1.5 text-xs font-mono text-[#738196] min-w-[2.6rem] text-center select-none'>100%</span>
      <button id='graph-zoom-in' type='button' aria-label='Zoom in' class='h-7 w-7 rounded-full flex items-center justify-center text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5'>+</button>
      <button id='graph-reset-btn' type='button' aria-label='${escapeHtml(t("graph_reset_view"))}' title='${escapeHtml(t("graph_reset_view"))}' class='h-7 px-2 rounded-full flex items-center gap-1 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5'>${resetSvg}<span class='hidden sm:inline'>${escapeHtml(t("graph_reset_view"))}</span></button>
    </div>`;
}
"""
