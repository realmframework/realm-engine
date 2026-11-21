"""Living Northern Lights aurora ribbons + silky Stitch-style 3D depth dot-matrix."""

AMBIENT_SCRIPT: str = r"""
let ambientEnabled = true, ambientPausedByGraph = false, ambientHiddenByBrowser = false;
let ambientRaf = null, ambientDots = [], ambientW = 0, ambientH = 0, ambientDpr = 1;
let ambientLastTs = 0, ambientClock = 4.2;
const ambientRaw = { x: -9999, y: -9999, active: false };
const ambientSmooth = { x: -9999, y: -9999, strength: 0 };
const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
let ambientPaletteCache = null;
let ambientAudioCtx = null, ambientAnalyser = null, ambientAudioData = null, ambientVoiceLevel = 0, ambientVoiceActive = false;

function connectAmbientAudio(audioEl) {
  const stage = ambientStageEl();
  ambientVoiceActive = Boolean(audioEl);
  if (stage) { stage.classList.toggle("is-speaking", ambientVoiceActive); }
  if (!audioEl || reducedMotionQuery.matches) { return; }
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) { return; }
    if (!ambientAudioCtx) { ambientAudioCtx = new AC(); }
    if (ambientAudioCtx.state === "suspended") { ambientAudioCtx.resume().catch(function () {}); }
    const src = ambientAudioCtx.createMediaElementSource(audioEl);
    const analyser = ambientAudioCtx.createAnalyser();
    analyser.fftSize = 256; analyser.smoothingTimeConstant = 0.82;
    src.connect(analyser); analyser.connect(ambientAudioCtx.destination);
    ambientAnalyser = analyser;
    ambientAudioData = new Uint8Array(analyser.frequencyBinCount);
    if (ambientShouldAnimate() && !ambientRaf) { startAmbientLoop(); }
  } catch (_e) { ambientAnalyser = null; }
}
function disconnectAmbientAudio() {
  ambientVoiceActive = false; ambientAnalyser = null;
  const stage = ambientStageEl();
  if (stage) { stage.classList.remove("is-speaking"); }
}
function sampleVoiceEnergy(dt) {
  let target = 0;
  if (ambientVoiceActive && ambientAnalyser && ambientAudioData) {
    ambientAnalyser.getByteFrequencyData(ambientAudioData);
    let sum = 0;
    for (let i = 2; i < 28 && i < ambientAudioData.length; i++) { sum += ambientAudioData[i]; }
    const avg = sum / 26;
    target = Math.min(1, Math.pow(avg / 108, 0.85));
  }
  const rate = target > ambientVoiceLevel ? 10.5 : 4.8;
  ambientVoiceLevel += (target - ambientVoiceLevel) * (1 - Math.exp(-rate * Math.max(0.001, dt)));
  if (ambientVoiceLevel < 0.002 && !ambientVoiceActive) { ambientVoiceLevel = 0; }
  return ambientVoiceLevel;
}

function ambientStageEl() { return document.getElementById("ambient-stage"); }
function ambientAuroraEl() { return document.getElementById("ambient-aurora-canvas"); }
function ambientCanvasEl() { return document.getElementById("ambient-dots-canvas"); }
function ambientShouldAnimate() {
  return ambientEnabled && !ambientPausedByGraph && !ambientHiddenByBrowser && !document.hidden && !reducedMotionQuery.matches;
}
function parseHexRgb(hex, fallback) {
  const clean = /^#[0-9a-f]{6}$/i.test(hex || "") ? hex : fallback;
  return [parseInt(clean.slice(1, 3), 16), parseInt(clean.slice(3, 5), 16), parseInt(clean.slice(5, 7), 16)];
}
function rgbaStr(rgb, a) {
  return "rgba(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + "," + a.toFixed(3) + ")";
}
function mixRgb(a, b, t) {
  return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)];
}
function computeAmbientPalette() {
  const styles = getComputedStyle(document.documentElement);
  const accent = parseHexRgb((styles.getPropertyValue("--accent-seed") || "#4BB8E8").trim(), "#4BB8E8");
  const glow = parseHexRgb((styles.getPropertyValue("--accent-glow") || "#6366F1").trim(), "#6366F1");
  const meta = document.querySelector('meta[name="color-scheme"]');
  const mode = meta ? meta.content : "light dark";
  const isDark = mode === "dark" || (mode !== "light" && systemDarkQuery.matches);
  const core = mixRgb(accent, [255, 255, 255], isDark ? 0.42 : 0.25);
  return {
    accent: accent, glow: glow, core: core, isDark: isDark,
    dotRgb: isDark ? "238,242,248" : "15,23,42",
    baseAlpha: isDark ? 0.22 : 0.16
  };
}
function refreshAmbientPalette() {
  ambientPaletteCache = computeAmbientPalette();
  if (ambientEnabled && !ambientPausedByGraph && !ambientRaf) { drawAmbientFrame(0, !ambientShouldAnimate()); }
}
function getAmbientPalette() {
  if (!ambientPaletteCache) { ambientPaletteCache = computeAmbientPalette(); }
  return ambientPaletteCache;
}
function rebuildAmbientGrid() {
  const canvas = ambientCanvasEl(), aurora = ambientAuroraEl();
  if (aurora) { aurora.width = 280; aurora.height = 170; }
  if (!canvas) { return; }
  const rect = canvas.getBoundingClientRect();
  ambientW = Math.max(1, Math.round(rect.width || window.innerWidth));
  ambientH = Math.max(1, Math.round(rect.height || window.innerHeight));
  ambientDpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(ambientW * ambientDpr);
  canvas.height = Math.round(ambientH * ambientDpr);
  const gap = 22, offsetX = (ambientW % gap) / 2, offsetY = (ambientH % gap) / 2;
  const dots = [];
  for (let y = offsetY; y < ambientH; y += gap) {
    for (let x = offsetX; x < ambientW; x += gap) {
      dots.push({ ox: x, oy: y, x: x, y: y, z: 0 });
    }
  }
  ambientDots = dots;
}
function strokeAuroraRibbon(ctx, w, h, t, cfg, pal, breeze, voice) {
  const steps = 32, pts = [], vAmp = 1 + voice * 0.52;
  const dx = (cfg.x1 - cfg.x0) * w, dy = (cfg.y1 - cfg.y0) * h;
  const len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len;
  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const envelope = Math.sin(u * Math.PI);
    const vocalRipple = voice > 0.01 ? Math.sin(u * 12.5 - t * 3.6 + cfg.phase) * voice * 4.6 : 0;
    const wave = (
      (Math.sin(u * cfg.freq1 - t * cfg.speed1 + cfg.phase + breeze) * cfg.amp1
      + Math.sin(u * cfg.freq2 + t * cfg.speed2 + cfg.phase * 1.6) * cfg.amp2
      + Math.cos(u * 2.1 - t * 0.26 + cfg.phase) * cfg.amp3) * vAmp
      + vocalRipple
    ) * (0.35 + 0.65 * envelope);
    pts.push([cfg.x0 * w + dx * u + nx * wave, cfg.y0 * h + dy * u + ny * wave]);
  }
  const shift = 0.5 + 0.24 * Math.sin(t * 0.52 + cfg.phase);
  const breath = Math.min(1.22, (0.84 + 0.16 * Math.sin(t * 0.64 + cfg.phase)) * (1 + voice * 0.34)) * (pal.isDark ? 1 : 0.44);
  const grad = ctx.createLinearGradient(pts[0][0], pts[0][1], pts[steps][0], pts[steps][1]);
  grad.addColorStop(0, rgbaStr(cfg.c0, 0));
  grad.addColorStop(Math.max(0.08, shift - 0.34), rgbaStr(cfg.c0, 0.58 * breath));
  grad.addColorStop(shift, rgbaStr(cfg.c1, 0.84 * breath));
  grad.addColorStop(Math.min(0.92, shift + 0.32), rgbaStr(cfg.c2, 0.54 * breath));
  grad.addColorStop(1, rgbaStr(cfg.c2, 0));

  const trace = function (offset) {
    ctx.beginPath();
    for (let i = 0; i <= steps; i++) {
      const px = pts[i][0] + nx * offset, py = pts[i][1] + ny * offset;
      if (i === 0) { ctx.moveTo(px, py); } else { ctx.lineTo(px, py); }
    }
  };
  ctx.lineCap = "round"; ctx.lineJoin = "round";
  trace(0); ctx.strokeStyle = grad; ctx.lineWidth = cfg.width * (1 + voice * 0.14); ctx.stroke();
  trace(Math.sin(t * 0.45 + cfg.phase) * 3.5); ctx.strokeStyle = grad; ctx.lineWidth = cfg.width * 0.46 * (1 + voice * 0.22); ctx.stroke();
  const coreGrad = ctx.createLinearGradient(pts[0][0], pts[0][1], pts[steps][0], pts[steps][1]);
  coreGrad.addColorStop(0, rgbaStr(pal.core, 0));
  coreGrad.addColorStop(Math.max(0.14, shift - 0.18), rgbaStr(pal.core, Math.min(0.85, 0.34 * breath * (1 + voice * 0.35))));
  coreGrad.addColorStop(Math.min(0.86, shift + 0.14), rgbaStr(pal.core, Math.min(0.95, 0.56 * breath * (1 + voice * 0.42))));
  coreGrad.addColorStop(1, rgbaStr(pal.core, 0));
  trace(Math.cos(t * 0.58 + cfg.phase) * 2.5); ctx.strokeStyle = coreGrad; ctx.lineWidth = cfg.width * 0.18 * (1 + voice * 0.35); ctx.stroke();
}
function drawAurora(t, pal, dt, staticOnly) {
  const aurora = ambientAuroraEl(); if (!aurora) { return; }
  const ctx = aurora.getContext("2d"); if (!ctx) { return; }
  const w = aurora.width, h = aurora.height;
  const voice = staticOnly ? 0 : sampleVoiceEnergy(dt);
  ctx.clearRect(0, 0, w, h);
  ctx.globalCompositeOperation = pal.isDark ? "screen" : "source-over";
  const breeze = ambientSmooth.strength > 0.01 ? ((ambientSmooth.x / Math.max(1, ambientW)) - 0.5) * 0.28 * ambientSmooth.strength : 0;
  strokeAuroraRibbon(ctx, w, h, t, {
    x0: -0.14, y0: 0.34, x1: 0.78, y1: 1.08, width: 38, phase: 0.4,
    freq1: 4.1, speed1: 0.62, amp1: 14, freq2: 7.4, speed2: 0.38, amp2: 6, amp3: 7,
    c0: pal.glow, c1: pal.accent, c2: pal.glow
  }, pal, breeze, voice);
  strokeAuroraRibbon(ctx, w, h, t, {
    x0: 0.04, y0: 1.08, x1: 1.14, y1: 0.40, width: 34, phase: 2.3,
    freq1: 3.7, speed1: -0.54, amp1: 13, freq2: 6.8, speed2: 0.42, amp2: 5.5, amp3: 6,
    c0: pal.accent, c1: pal.glow, c2: pal.accent
  }, pal, -breeze * 0.8, voice);
  strokeAuroraRibbon(ctx, w, h, t, {
    x0: -0.10, y0: 0.78, x1: 1.08, y1: 0.66, width: 24, phase: 4.4,
    freq1: 5.0, speed1: 0.44, amp1: 10, freq2: 8.6, speed2: -0.32, amp2: 4.5, amp3: 5,
    c0: pal.glow, c1: mixRgb(pal.accent, pal.glow, 0.5), c2: pal.accent
  }, pal, breeze * 0.5, voice);
  ctx.globalCompositeOperation = "source-over";
}
function drawDotMatrix(dt, staticOnly, pal) {
  const canvas = ambientCanvasEl(); if (!canvas) { return; }
  const ctx = canvas.getContext("2d"); if (!ctx) { return; }
  if (!ambientDots.length) { rebuildAmbientGrid(); }
  ctx.setTransform(ambientDpr, 0, 0, ambientDpr, 0, 0);
  ctx.clearRect(0, 0, ambientW, ambientH);
  if (!staticOnly) {
    const follow = 1 - Math.exp(-4.0 * dt);
    const fade = 1 - Math.exp(-(ambientRaw.active ? 3.2 : 2.1) * dt);
    if (ambientRaw.active) {
      if (ambientSmooth.strength < 0.01) { ambientSmooth.x = ambientRaw.x; ambientSmooth.y = ambientRaw.y; }
      else { ambientSmooth.x += (ambientRaw.x - ambientSmooth.x) * follow; ambientSmooth.y += (ambientRaw.y - ambientSmooth.y) * follow; }
    }
    ambientSmooth.strength += ((ambientRaw.active ? 1 : 0) - ambientSmooth.strength) * fade;
  } else {
    ambientSmooth.strength = 0;
  }
  const sigma = 96, twoSigmaSq = 2 * sigma * sigma, cutoffSq = 285 * 285;
  const dotEase = staticOnly ? 1 : (1 - Math.exp(-4.6 * dt));
  const hasField = !staticOnly && ambientSmooth.strength > 0.004;
  const mx = ambientSmooth.x, my = ambientSmooth.y, ms = ambientSmooth.strength;
  const activeDots = [];
  ctx.beginPath();
  for (let i = 0; i < ambientDots.length; i++) {
    const d = ambientDots[i];
    let tx = d.ox, ty = d.oy, tz = 0;
    if (hasField) {
      const dx = d.ox - mx, dy = d.oy - my, distSq = dx * dx + dy * dy;
      if (distSq < cutoffSq) {
        const w = Math.exp(-distSq / twoSigmaSq) * ms;
        tz = w;
        if (distSq > 0.25) {
          const dist = Math.sqrt(distSq);
          const push = (dist / sigma) * w * 24;
          tx = d.ox + (dx / dist) * push;
          ty = d.oy + (dy / dist) * push;
        }
      }
    }
    if (staticOnly) {
      d.x = d.ox; d.y = d.oy; d.z = 0;
    } else {
      d.x += (tx - d.x) * dotEase;
      d.y += (ty - d.y) * dotEase;
      d.z += (tz - d.z) * dotEase;
      if (Math.abs(d.x - d.ox) < 0.03 && Math.abs(d.y - d.oy) < 0.03 && d.z < 0.003) {
        d.x = d.ox; d.y = d.oy; d.z = 0;
      }
    }
    if (d.z > 0.004) {
      activeDots.push(d);
    } else {
      ctx.moveTo(d.x + 0.95, d.y);
      ctx.arc(d.x, d.y, 0.95, 0, Math.PI * 2);
    }
  }
  ctx.fillStyle = "rgba(" + pal.dotRgb + "," + pal.baseAlpha + ")";
  ctx.fill();
  for (let i = 0; i < activeDots.length; i++) {
    const d = activeDots[i];
    const alpha = pal.baseAlpha * Math.max(0.08, 1 - d.z * 0.88);
    const r = Math.max(0.45, 0.95 * (1 - d.z * 0.44));
    ctx.beginPath();
    ctx.arc(d.x, d.y, r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(" + pal.dotRgb + "," + alpha.toFixed(3) + ")";
    ctx.fill();
  }
}
function drawAmbientFrame(dt, staticOnly) {
  const pal = getAmbientPalette();
  if (!staticOnly) { ambientClock += dt * (1 + ambientVoiceLevel * 0.45); }
  drawAurora(ambientClock, pal, dt, staticOnly);
  drawDotMatrix(dt, staticOnly, pal);
}
function ambientLoop(ts) {
  if (!ambientShouldAnimate()) { ambientRaf = null; ambientLastTs = 0; return; }
  const dt = ambientLastTs ? Math.min(0.05, Math.max(0.001, (ts - ambientLastTs) / 1000)) : 0.016;
  ambientLastTs = ts;
  drawAmbientFrame(dt, false);
  ambientRaf = requestAnimationFrame(ambientLoop);
}
function startAmbientLoop() {
  if (!ambientEnabled || ambientPausedByGraph) { return; }
  if (!ambientShouldAnimate()) { stopAmbientDots(); drawAmbientFrame(0, true); return; }
  if (!ambientRaf) { ambientLastTs = 0; ambientRaf = requestAnimationFrame(ambientLoop); }
}
function stopAmbientDots() {
  if (ambientRaf) { cancelAnimationFrame(ambientRaf); ambientRaf = null; }
  ambientLastTs = 0;
}
function setAmbientEffects(enabled, persistLocal) {
  ambientEnabled = enabled !== false;
  const stage = ambientStageEl();
  if (stage) { stage.classList.toggle("is-off", !ambientEnabled); }
  for (const id of ["theme-ambient-toggle", "onboarding-ambient-toggle"]) {
    const chk = document.getElementById(id); if (chk) { chk.checked = ambientEnabled; }
  }
  if (persistLocal !== false) { try { localStorage.setItem("realm_ambient_effects", ambientEnabled ? "1" : "0"); } catch (_e) {} }
  if (ambientEnabled) { rebuildAmbientGrid(); startAmbientLoop(); }
  else { stopAmbientDots(); }
}
function setAmbientDimmed(dimmed) {
  const stage = ambientStageEl(); if (stage) { stage.classList.toggle("is-dimmed", Boolean(dimmed)); }
}
function setAmbientGraphPause(paused) {
  ambientPausedByGraph = Boolean(paused);
  const stage = ambientStageEl(); if (stage) { stage.classList.toggle("is-off", !ambientEnabled || ambientPausedByGraph); }
  if (ambientPausedByGraph) { stopAmbientDots(); } else if (ambientEnabled) { rebuildAmbientGrid(); startAmbientLoop(); }
}
function bindAmbientBackdrop() {
  const stage = ambientStageEl(); if (!stage) { return; }
  let saved = true;
  try { saved = localStorage.getItem("realm_ambient_effects") !== "0"; } catch (_e) {}
  setAmbientEffects(saved, false);
  window.addEventListener("pointermove", function (e) {
    ambientRaw.x = e.clientX; ambientRaw.y = e.clientY; ambientRaw.active = true;
    if (ambientShouldAnimate() && !ambientRaf) { startAmbientLoop(); }
  }, { passive: true });
  document.addEventListener("pointerleave", function () { ambientRaw.active = false; });
  window.addEventListener("blur", function () { ambientRaw.active = false; });
  window.addEventListener("resize", function () { if (ambientEnabled && !ambientPausedByGraph) { rebuildAmbientGrid(); if (!ambientRaf) { drawAmbientFrame(0, !ambientShouldAnimate()); } } });
  document.addEventListener("visibilitychange", function () { if (document.hidden) { stopAmbientDots(); } else if (ambientEnabled) { startAmbientLoop(); } });
  reducedMotionQuery.addEventListener("change", function () { if (reducedMotionQuery.matches) { stopAmbientDots(); drawAmbientFrame(0, true); } else { startAmbientLoop(); } });
  if ("contentVisibility" in document.documentElement.style) {
    stage.addEventListener("contentvisibilityautostatechange", function (event) {
      ambientHiddenByBrowser = Boolean(event.skipped);
      if (ambientHiddenByBrowser) { stopAmbientDots(); } else if (ambientEnabled) { startAmbientLoop(); }
    });
  } else if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      ambientHiddenByBrowser = !entries[0].isIntersecting;
      if (ambientHiddenByBrowser) { stopAmbientDots(); } else if (ambientEnabled) { startAmbientLoop(); }
    }).observe(stage);
  }
}
"""
