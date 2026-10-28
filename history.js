import { api } from "../api.js";
import { icon } from "../components/icons.js";
import { copyText, errorBox, esc, openModal, tagsHtml, toast, withSignature } from "../components/ui.js";

const TYPES = { reel_caption: "Reels caption", ai_generated: "AI generator", top3: "TOP-3 tahlil" };
const PAGE = 10;
const fmt = (iso) => { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleString("uz-UZ", { dateStyle: "medium", timeStyle: "short" }); };
const copyAll = (it) => withSignature([it.caption, (it.hashtags || []).join(" ")].filter(Boolean).join("\n\n"));

export async function renderHistory(root) {
  root.innerHTML = `<div class="stack" id="list"><div class="skeleton"></div><div class="skeleton"></div></div><div class="stack" id="more"></div>`;
  const list = root.querySelector("#list"), more = root.querySelector("#more");
  let offset = 0;

  const load = async (first) => {
    let data;
    try { data = await api.history(offset, PAGE); }
    catch (e) { list.innerHTML = errorBox(e.message); return; }
    if (first) list.innerHTML = "";
    if (first && !data.items.length) {
      list.innerHTML = `<section class="card empty"><div class="big">🕘 Hozircha tarix bo‘sh</div>
        <p>Hashtag natijalaringiz shu yerda avtomatik saqlanadi.</p></section>`;
      more.innerHTML = ""; return;
    }
    for (const it of data.items) list.appendChild(card(it, list, more));
    offset += data.items.length;
    more.innerHTML = data.has_more ? `<button class="btn ghost" id="lm">Yana yuklash</button>` : "";
    more.querySelector("#lm")?.addEventListener("click", () => load(false));
  };
  await load(true);
}

function card(it, list) {
  const el = document.createElement("section");
  el.className = "card hcard";
  el.innerHTML = `<div class="top"><span class="badge ${esc(it.result_type)}">${esc(TYPES[it.result_type] || it.result_type)}</span>
      <span class="date">${esc(fmt(it.created_at))}</span></div>
    <div class="text">${esc(it.caption) || "—"}${it.caption.length >= 140 ? "…" : ""}</div>
    <div style="margin-top:10px">${tagsHtml((it.hashtags || []).slice(0, 8))}</div>
    ${it.reel_url ? `<div class="kv"><span>Video</span><a href="${esc(it.reel_url)}" target="_blank" rel="noopener" style="color:var(--sky)">Havola</a></div>` : ""}
    <div class="actions">
      <button class="btn sm" data-a="view">${icon("film")}<span>To‘liq ko‘rish</span></button>
      <button class="btn ghost sm" data-a="copy">${icon("copy")}<span>Nusxalash</span></button>
      <button class="btn danger sm" data-a="del">${icon("trash")}<span>O‘chirish</span></button></div>`;
  el.querySelector('[data-a="view"]').onclick = () => view(it.id);
  el.querySelector('[data-a="copy"]').onclick = async () => {
    try { copyText(copyAll(await api.historyItem(it.id))); } catch (e) { toast(e.message, "err"); }
  };
  el.querySelector('[data-a="del"]').onclick = () => confirmDelete(it.id, el, list);
  return el;
}

async function view(id) {
  try {
    const it = await api.historyItem(id);
    openModal({
      title: TYPES[it.result_type] || "Natija", titleIcon: "history", desc: fmt(it.created_at),
      body: `<div class="result"><div class="label">Caption</div><div class="text">${esc(it.caption) || "—"}</div><div class="sep"></div>
        <div class="label">Hashtaglar</div>${tagsHtml(it.hashtags)}
        ${it.direction ? `<div class="kv"><span>Yo‘nalish</span><span>${esc(it.direction)}</span></div>` : ""}
        ${it.source ? `<div class="kv"><span>Manba</span><span>${esc(it.source)}</span></div>` : ""}
        ${it.video_date ? `<div class="kv"><span>Video sanasi</span><span>${esc(it.video_date)}</span></div>` : ""}
        ${it.views != null ? `<div class="kv"><span>${esc(it.metric_label || "Ko‘rishlar")}</span><span>${it.views.toLocaleString("ru-RU")}</span></div>` : ""}
        <div class="actions"><button class="btn sm" id="c">${icon("copy")}<span>Hammasini nusxalash</span></button></div></div>`,
      onMount: (el) => { el.querySelector("#c").onclick = () => copyText(copyAll(it)); },
    });
  } catch (e) { toast(e.message, "err"); }
}

function confirmDelete(id, el, list) {
  openModal({
    title: "O‘chirishni tasdiqlang", titleIcon: "trash", desc: "Bu yozuv bazadan butunlay o‘chiriladi.",
    body: `<div class="actions"><button class="btn ghost sm" id="no">Bekor qilish</button><button class="btn danger sm" id="yes">${icon("trash")}<span>O‘chirish</span></button></div>`,
    onMount(m, close) {
      m.querySelector("#no").onclick = close;
      m.querySelector("#yes").onclick = async () => {
        try {
          await api.deleteHistory(id);
          el.remove(); close(); toast("O‘chirildi");
          if (!list.children.length) list.innerHTML = `<section class="card empty"><div class="big">🕘 Hozircha tarix bo‘sh</div><p>Hashtag natijalaringiz shu yerda avtomatik saqlanadi.</p></section>`;
        } catch (e) { toast(e.message, "err"); close(); }
      };
    },
  });
}
