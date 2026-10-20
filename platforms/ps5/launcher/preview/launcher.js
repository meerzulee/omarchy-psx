/* SPDX-License-Identifier: MIT */
"use strict";
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const themes = window.OMARCHY_THEMES || {};
const library = [];
const limit = 64 * 1024 * 1024;
const preferenceKey = "omarchy.ps5.preview.theme";
let activeView = "home", currentTheme = "tokyo-night", currentWallpaper = "";
let appearanceOriginal = null, appearanceReturn = "home";
let selected = null, toastTimer, importing = false;

function announce(message) {
  const toast = $("#toast");
  toast.textContent = message; toast.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { toast.hidden = true; }, 5000);
}
function rgba(hex, alpha) {
  const value = hex.replace("#", "");
  const rgb = value.length === 3 ? [...value].map(char => parseInt(char + char, 16)) : [0, 2, 4].map(index => parseInt(value.slice(index, index + 2), 16));
  return `rgba(${rgb.join(",")},${alpha})`;
}
function setAppearance(id, wallpaper) {
  const theme = themes[id];
  if (!theme) return;
  currentTheme = id;
  currentWallpaper = theme.wallpapers.some(item => item.file === wallpaper) ? wallpaper : theme.wallpapers[0]?.file || "";
  const root = document.documentElement;
  root.dataset.mode = theme.mode;
  root.style.colorScheme = theme.mode;
  for (const [role, value] of Object.entries(theme.colors)) root.style.setProperty(`--${role}`, value);
  const base = theme.mode === "light" ? theme.colors.background : theme.colors.darker;
  for (const [role, alpha] of Object.entries({ strong: .94, middle: .73, soft: theme.mode === "light" ? .36 : .23, top: .24, bottom: .5 })) root.style.setProperty(`--overlay-${role}`, rgba(base, alpha));
  root.style.setProperty("--surface", rgba(theme.colors.dark, .92));
  root.style.setProperty("--line", rgba(theme.colors.bright, .19));
  root.style.setProperty("--wallpaper", currentWallpaper ? `url(${JSON.stringify(currentWallpaper)})` : "none");
  $$("[data-theme-choice]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.themeChoice === id)));
  const index = theme.wallpapers.findIndex(item => item.file === currentWallpaper);
  if (index >= 0) {
    $("#wallpaper-preview").src = currentWallpaper;
    $("#wallpaper-preview").alt = `${theme.name} wallpaper: ${theme.wallpapers[index].name}`;
    $("#wallpaper-name").textContent = theme.wallpapers[index].name;
    $("#wallpaper-count").textContent = `${index + 1} / ${theme.wallpapers.length}`;
  }
  $("#wallpaper-theme").textContent = theme.name;
  $("#shuffle-wallpaper").disabled = theme.wallpapers.length < 2;
}
function renderThemeOptions() {
  const options = $("#theme-options");
  for (const [id, theme] of Object.entries(themes)) {
    const button = document.createElement("button");
    button.className = "theme-option"; button.dataset.nav = ""; button.dataset.themeChoice = id;
    button.setAttribute("aria-pressed", String(id === currentTheme));
    const image = document.createElement("img");
    image.className = "theme-thumbnail"; image.alt = ""; image.src = theme.wallpapers[0]?.file || "";
    const info = document.createElement("span"), name = document.createElement("strong"), palette = document.createElement("span");
    info.className = "theme-info"; name.textContent = theme.name; palette.className = "palette"; palette.setAttribute("aria-hidden", "true");
    for (const role of ["background", "accent", "green", "yellow", "red"]) {
      const dot = document.createElement("i"); dot.style.background = theme.colors[role]; palette.append(dot);
    }
    info.append(name, palette); button.append(image, info);
    button.addEventListener("click", () => setAppearance(id)); options.append(button);
  }
}
function showView(name, focus = true) {
  activeView = name;
  $$(".view").forEach(view => { view.hidden = view.id !== `${name}-view`; });
  if (focus) {
    const target = name === "home" ? $("#open-omarchy") : name === "library" ? $("#library-view [data-import]") : $("[data-theme-choice][aria-pressed=true]");
    target?.focus({ preventScroll: true });
  }
}
function openAppearance() {
  if (activeView === "appearance") return;
  if (!themes[currentTheme]) { announce("Appearance assets are unavailable."); return; }
  $("dialog[open]")?.close();
  appearanceOriginal = { theme: currentTheme, wallpaper: currentWallpaper };
  appearanceReturn = activeView;
  showView("appearance");
}
function cancelAppearance() {
  if (!appearanceOriginal) return;
  setAppearance(appearanceOriginal.theme, appearanceOriginal.wallpaper);
  appearanceOriginal = null; showView(appearanceReturn);
}
function applyAppearance() {
  try { localStorage.setItem(preferenceKey, currentTheme); }
  catch { announce("Theme applied for this session. Browser storage is unavailable."); }
  appearanceOriginal = null; showView(appearanceReturn);
}
$("#shuffle-wallpaper").addEventListener("click", () => {
  const alternatives = themes[currentTheme].wallpapers.filter(item => item.file !== currentWallpaper);
  if (alternatives.length) setAppearance(currentTheme, alternatives[Math.floor(Math.random() * alternatives.length)].file);
});
$("#apply-appearance").addEventListener("click", applyAppearance);
$("#cancel-appearance").addEventListener("click", cancelAppearance);
$$("[data-appearance]").forEach(button => button.addEventListener("click", openAppearance));
renderThemeOptions();
try { const saved = localStorage.getItem(preferenceKey); if (themes[saved]) currentTheme = saved; } catch { /* Appearance still works without persistence. */ }
setAppearance(currentTheme);

function openDialog(dialog) { dialog.showModal(); $("[data-close]", dialog).focus(); }
function openOmarchy() {
  selected = null;
  $("#detail-eyebrow").textContent = "OMARCHY FOR PS5";
  $("#detail-title").textContent = "Linux handoff";
  $("#detail-description").textContent = "A supported Linux loader for system software 12.40 is needed before Omarchy can start. The desktop launch is not available yet.";
  $("#payload-details").hidden = true; $("#remove-payload").hidden = true;
  openDialog($("#detail-dialog"));
}
function formatSize(size) { return size < 1024 ? `${size} B` : size < 1024 ** 2 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1024 ** 2).toFixed(1)} MB`; }
function openPayload(item) {
  selected = item.id;
  $("#detail-eyebrow").textContent = "LOCAL PAYLOAD";
  $("#detail-title").textContent = item.name;
  $("#detail-description").textContent = "File details, inspected locally. This preview cannot send or run the file.";
  $("#remove-payload").hidden = false;
  const details = $("#payload-details"); details.hidden = false; details.replaceChildren();
  for (const [label, value] of [["Size", `${formatSize(item.size)} · ${item.size.toLocaleString()} bytes`], ["Header", item.header], ["SHA-256", item.sha256], ["Compatibility", "Not established by file identity"]]) {
    const row = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = label; dd.textContent = value;
    if (label === "SHA-256") dd.className = "hash";
    row.append(dt, dd); details.append(row);
  }
  openDialog($("#detail-dialog"));
}
function payloadTile(item) {
  const tile = document.createElement("button");
  tile.className = "payload-tile"; tile.dataset.nav = "";
  tile.innerHTML = '<span class="tile-icon"><svg><use href="#file"/></svg></span><span class="tile-copy"><strong></strong><small></small></span><span class="tile-arrow">›</span>';
  $("strong", tile).textContent = item.name;
  $("small", tile).textContent = `${item.isElf ? "ELF" : "Unknown format"} · ${formatSize(item.size)}`;
  tile.addEventListener("click", () => openPayload(item)); return tile;
}
function renderLibrary() {
  $("#payload-library").replaceChildren(...library.map(payloadTile));
  $("#empty-library").hidden = library.length > 0;
  $("#library-count").textContent = library.length ? `${library.length} ${library.length === 1 ? "file" : "files"}` : "Local files";
}
function describeHeader(bytes) {
  if (bytes.length < 4 || bytes[0] !== 0x7f || bytes[1] !== 69 || bytes[2] !== 76 || bytes[3] !== 70) return { isElf: false, header: "ELF signature not present" };
  if (bytes.length < 20) return { isElf: false, header: "Incomplete ELF header" };
  const bits = bytes[4] === 2 ? "64-bit" : bytes[4] === 1 ? "32-bit" : "unknown class";
  const endian = bytes[5] === 1 ? "little endian" : bytes[5] === 2 ? "big endian" : "unknown byte order";
  const machine = bytes[5] === 1 ? bytes[18] | (bytes[19] << 8) : (bytes[18] << 8) | bytes[19];
  return { isElf: true, header: `ELF · ${bits} · ${endian} · ${machine === 62 ? "x86-64" : machine === 3 ? "x86" : `machine ${machine}`}` };
}
async function addFiles(files) {
  if (importing) { announce("File inspection is already in progress."); return; }
  importing = true; let added = 0, skipped = 0;
  try {
    for (const file of files) {
      if (file.size > limit) { skipped++; continue; }
      try {
        const buffer = await file.arrayBuffer();
        const identity = describeHeader(new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 64)));
        let sha256 = "Unavailable in this browser context. No hash has been verified.";
        if (globalThis.crypto?.subtle) {
          try { sha256 = [...new Uint8Array(await crypto.subtle.digest("SHA-256", buffer))].map(byte => byte.toString(16).padStart(2, "0")).join(""); }
          catch { /* Keep an explicit unavailable state when Web Crypto refuses access. */ }
        }
        library.push({ id: `${Date.now()}-${library.length}`, name: file.name, size: file.size, sha256, ...identity }); added++;
      } catch { skipped++; }
    }
    renderLibrary();
    announce(`${added} ${added === 1 ? "file added" : "files added"}${skipped ? ` · ${skipped} unreadable or over 64 MB` : ""}.`);
    if (added) showView("library");
  } finally { importing = false; $("#file-input").value = ""; }
}
$$("[data-view]").forEach(button => button.addEventListener("click", () => showView(button.dataset.view)));
$(".wordmark").addEventListener("click", event => { event.preventDefault(); if (activeView === "appearance") cancelAppearance(); showView("home"); });
$("#open-omarchy").addEventListener("click", openOmarchy);
$$("[data-close]").forEach(button => button.addEventListener("click", () => button.closest("dialog").close()));
$$("[data-import]").forEach(button => button.addEventListener("click", () => $("#file-input").click()));
$("#file-input").addEventListener("change", event => addFiles([...event.target.files]));
$("#remove-payload").addEventListener("click", () => {
  const index = library.findIndex(item => item.id === selected); if (index !== -1) library.splice(index, 1);
  $("#detail-dialog").close(); renderLibrary(); showView("library"); announce("Removed from this library. The original file is unchanged.");
});
document.addEventListener("dragover", event => { event.preventDefault(); if (activeView === "library" && !$("dialog[open]")) $("#drop-zone").classList.add("drag-over"); });
document.addEventListener("dragleave", event => { if (!event.relatedTarget) $("#drop-zone").classList.remove("drag-over"); });
document.addEventListener("drop", event => {
  event.preventDefault(); $("#drop-zone").classList.remove("drag-over");
  if (activeView !== "appearance" && !$("dialog[open]")) addFiles([...event.dataTransfer.files]);
});

// Directional focus is shared by the keyboard and standard controller mapping.
function moveFocus(direction, controller = false) {
  const scope = $("dialog[open]") || $(".view:not([hidden])");
  const buttons = $$("[data-nav]", scope).filter(button => !button.disabled && button.getClientRects().length);
  if (!buttons.length) return;
  const current = document.activeElement;
  let target;
  if (!buttons.includes(current)) target = buttons[0];
  else {
    const rect = current.getBoundingClientRect(), x = rect.x + rect.width / 2, y = rect.y + rect.height / 2;
    const horizontal = direction === "ArrowLeft" || direction === "ArrowRight";
    const sign = direction === "ArrowRight" || direction === "ArrowDown" ? 1 : -1;
    const candidates = buttons.filter(button => button !== current).map(button => {
      const r = button.getBoundingClientRect(), dx = r.x + r.width / 2 - x, dy = r.y + r.height / 2 - y;
      const primary = (horizontal ? dx : dy) * sign, secondary = Math.abs(horizontal ? dy : dx);
      return { button, primary, score: primary + secondary * 3 };
    }).filter(item => item.primary > 8).sort((a, b) => a.score - b.score);
    target = candidates[0]?.button;
  }
  if (target) { $$(".controller-focus").forEach(button => button.classList.remove("controller-focus")); if (controller) target.classList.add("controller-focus"); target.focus(); }
}
function goBack() {
  const dialog = $("dialog[open]");
  if (dialog) dialog.close(); else if (activeView === "appearance") cancelAppearance(); else showView("home");
}
document.addEventListener("keydown", event => {
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)) return;
  $$(".controller-focus").forEach(button => button.classList.remove("controller-focus"));
  if (event.key.startsWith("Arrow")) { event.preventDefault(); moveFocus(event.key); }
  if (event.key === "Escape") { event.preventDefault(); goBack(); }
  if (event.key.toLowerCase() === "o" || event.key === "F2") { event.preventDefault(); openAppearance(); }
});
document.addEventListener("pointerdown", () => $$(".controller-focus").forEach(button => button.classList.remove("controller-focus")));
let lastDirection = "", repeatAt = 0, previousSelect = false, previousBack = false, previousOptions = false;
function pollGamepad(now) {
  let pad;
  try { pad = [...(navigator.getGamepads?.() || [])].find(item => item?.mapping === "standard"); } catch { /* Browser can deny gamepad access. */ }
  if (pad) {
    const down = index => Boolean(pad.buttons[index]?.pressed);
    const direction = down(12) || pad.axes[1] < -.65 ? "ArrowUp" : down(13) || pad.axes[1] > .65 ? "ArrowDown" : down(14) || pad.axes[0] < -.65 ? "ArrowLeft" : down(15) || pad.axes[0] > .65 ? "ArrowRight" : "";
    if (direction && (direction !== lastDirection || now >= repeatAt)) { moveFocus(direction, true); repeatAt = now + (direction !== lastDirection ? 350 : 150); }
    if (down(0) && !previousSelect) document.activeElement?.click();
    if (down(1) && !previousBack) goBack();
    if (down(9) && !previousOptions) openAppearance();
    lastDirection = direction; previousSelect = down(0); previousBack = down(1); previousOptions = down(9);
  } else { lastDirection = ""; previousSelect = previousBack = previousOptions = false; }
  requestAnimationFrame(pollGamepad);
}
showView("home");
requestAnimationFrame(pollGamepad);
