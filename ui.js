import { icon } from "./icons.js";

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const SIGNATURE = "Тг канал : @o11abu";
export const withSignature = (t) => `${String(t).trimEnd()}\n\n\n${SIGNATURE}`;

export function toast(msg, kind = "ok") {
  const root = document.getElementById("toastRoot");
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.innerHTML = `${icon(kind === "ok" ? "check" : "alert")}<span>${esc(msg)}</span>`;
  root.replaceChildren(el);
  setTimeout(() => el.remove(), 2200);
  window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.(kind === "ok" ? "success" : "error");
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch { /* ignore */ }
    ta.remove();
    if (!ok) { toast("Nusxalab bo‘lmadi", "err"); return; }
  }
  toast("Nusxalandi");
}

export function openModal({ title, titleIcon, desc = "", body = "", onMount }) {
  const root = document.getElementById("modalRoot");
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.innerHTML = `<div class="modal" role="dialog" aria-modal="true">
    <button class="modal-x" aria-label="Yopish">${icon("x")}</button>
    <div class="modal-title">${titleIcon ? icon(titleIcon) : ""}<span>${esc(title)}</span></div>
    ${desc ? `<p class="modal-desc">${esc(desc)}</p>` : ""}
    <div class="modal-body">${body}</div></div>`;
  const close = () => { ov.remove(); document.body.style.overflow = ""; };
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  ov.querySelector(".modal-x").addEventListener("click", close);
  root.appendChild(ov);
  document.body.style.overflow = "hidden";
  onMount?.(ov.querySelector(".modal-body"), close);
  return close;
}

export function setLoading(btn, on, label) {
  btn.disabled = on;
  btn.innerHTML = on ? `<span class="spin"></span><span>Tahlil qilinmoqda...</span>` : label;
}

export function errorBox(msg) {
  return `<div class="result err">${icon("alert")}<div>${esc(msg)}</div></div>`;
}

export function tagsHtml(tags) {
  return tags?.length ? `<div class="tags">${tags.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>` : "—";
}
