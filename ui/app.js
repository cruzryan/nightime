/**
 * Nighttime — webview UI logic.
 * Communicates with Python via pywebview's exposed API.
 */

"use strict";

let dimLevel = 0;
let redLevel = 0;
let dragging = null;

const TRACK_W = 312;

const dimValue   = document.getElementById("dim-value");
const dimFill    = document.getElementById("dim-fill");
const dimThumb   = document.getElementById("dim-thumb");
const dimTrack   = document.getElementById("dim-track");
const redValue   = document.getElementById("red-value");
const redFill    = document.getElementById("red-fill");
const redThumb   = document.getElementById("red-thumb");
const redTrack   = document.getElementById("red-track");
const previewSwatch = document.getElementById("preview-swatch");
const btnDisable    = document.getElementById("btn-disable");
const btnExit       = document.getElementById("btn-exit");
const btnClose      = document.getElementById("btn-close");

function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

function levelToX(level) { return (level / 100) * TRACK_W; }

function setDim(level, apply = false) {
  dimLevel = clamp(level, 0, 100);
  renderSlider("dim", dimLevel);
  syncPreview();
  if (apply) applyOverlay();
}

function setRed(level, apply = false) {
  redLevel = clamp(level, 0, 100);
  renderSlider("red", redLevel);
  syncPreview();
  if (apply) applyOverlay();
}

function applyOverlay() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.nt_set_dim(dimLevel);
    window.pywebview.api.nt_set_red(redLevel);
  }
}

function syncPreview() {
  const a = Math.round(dimLevel * 0.9); // Cap opacity in preview for visibility
  const r = Math.round(redLevel * 1.6); // Scale red for better preview visibility
  previewSwatch.style.background = `rgba(${r}, 0, 0, ${dimLevel / 100})`;
  previewSwatch.style.boxShadow = `0 0 15px rgba(${r}, 0, 0, 0.2)`;
}

function renderSlider(which, level) {
  const isDim = which === "dim";
  const fill  = isDim ? dimFill  : redFill;
  const thumb = isDim ? dimThumb : redThumb;
  const value = isDim ? dimValue : redValue;
  const x     = levelToX(level);

  fill.style.width  = x + "px";
  thumb.style.left  = (x - 9) + "px";
  value.textContent = level + "%";
}

function getTrackOffset(e) {
  const rect = dimTrack.getBoundingClientRect();
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  return clientX - rect.left;
}

function onDrag(which, e) {
  e.preventDefault();
  const x    = clamp(getTrackOffset(e), 0, TRACK_W);
  const level = Math.round((x / TRACK_W) * 100);
  if (which === "dim") setDim(level, true);
  else                 setRed(level, true);
}

function startDrag(which, e) {
  e.preventDefault();
  dragging = which;
  onDrag(which, e);
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup",   stopDrag);
  document.addEventListener("touchmove", onTouchMove, { passive: false });
  document.addEventListener("touchend",  stopDrag);
}

function onMouseMove(e) { if (dragging) onDrag(dragging, e); }
function onTouchMove(e) { if (dragging) onDrag(dragging, e); }

function stopDrag() {
  if (dragging) applyOverlay();
  dragging = null;
  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup",   stopDrag);
  document.removeEventListener("touchmove", onTouchMove);
  document.removeEventListener("touchend",  stopDrag);
}

dimTrack.addEventListener("mousedown",  e => startDrag("dim", e));
dimTrack.addEventListener("touchstart", e => startDrag("dim", e), { passive: false });
dimThumb.addEventListener("mousedown",  e => startDrag("dim", e));
dimThumb.addEventListener("touchstart", e => startDrag("dim", e), { passive: false });

redTrack.addEventListener("mousedown",  e => startDrag("red", e));
redTrack.addEventListener("touchstart", e => startDrag("red", e), { passive: false });
redThumb.addEventListener("mousedown",  e => startDrag("red", e));
redThumb.addEventListener("touchstart", e => startDrag("red", e), { passive: false });

btnDisable.addEventListener("click", () => {
  setDim(0, false);
  setRed(0, false);
  if (window.pywebview && window.pywebview.api) window.pywebview.api.nt_disable();
});

btnExit.addEventListener("click", () => {
  if (window.pywebview && window.pywebview.api) window.pywebview.api.nt_quit();
});

if (btnClose) {
  btnClose.addEventListener("click", () => {
    if (window.pywebview && window.pywebview.api) window.pywebview.api.nt_hide();
  });
}

document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    setDim(0, false);
    setRed(0, false);
    if (window.pywebview && window.pywebview.api) window.pywebview.api.nt_disable();
  }
});

// Sync initial state
async function init() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const state = await window.pywebview.api.nt_get_state();
      if (state) { setDim(state.dim, false); setRed(state.red, false); return; }
    } catch (_) {}
  }
  renderSlider("dim", 0);
  renderSlider("red", 0);
  syncPreview();
}

init();
