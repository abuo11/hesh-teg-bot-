import { api } from "../api.js";
import { icon } from "../components/icons.js";
import { copyText, errorBox, esc, openModal, setLoading, tagsHtml, toast, withSignature } from "../components/ui.js";

const BTN = `${icon("search")}<span>Ma’lumotlarni olish</span>`;

export function renderHashtag(root, nav) {
  root.innerHTML = `<div class="stack">
    <section class="card hero">
      <div class="card-head"><div class="ico">${icon("instagram")}</div><h2>Hashtag yuklash</h2></div>
      <p>Reels havolasini kiriting va mavjud caption hamda hashtag ma’lumotlarini oling.</p>
      <button class="btn" id="openHashtag">${icon("hash")}<span>Hashtag yuklash</span></button>
    </section>
    <section class="card row" id="goBio"><div class="ico pink">${icon("user")}</div>
      <div class="meta"><h3>Bio yuklash</h3><p>Instagram username yoki profil havolasi orqali mavjud bio ma’lumotlarini oling.</p></div>${icon("chevron")}</section>
    <section class="card row" id="goHist"><div class="ico green">${icon("history")}</div>
      <div class="meta"><h3>History</h3><p>Oldin olingan hashtaglar, captionlar va natijalarni ko‘ring.</p></div>${icon("chevron")}</section>
  </div>`;
  root.querySelector("#openHashtag").onclick = openHashtagModal;
  root.querySelector("#goBio").onclick = () => nav("bio");
  root.querySelector("#goHist").onclick = () => nav("history");
}

export function openHashtagModal() {
  openModal({
    title: "🎬 Reels Hashtag",
    desc: "Instagram Reels havolasini kiriting. Mavjud caption va hashtag ma’lumotlarini olishga harakat qilamiz.",
    body: `<div class="gap"><input class="input" id="url" type="url" inputmode="url" autocomplete="off"
      placeholder="https://www.instagram.com/reel/..."><button class="btn" id="go">${BTN}</button></div><div id="out"></div>`,
    onMount(el) {
      const input = el.querySelector("#url"), go = el.querySelector("#go"), out = el.querySelector("#out");
      const run = async () => {
        const url = input.value.trim();
        if (!url) { out.innerHTML = errorBox("Reels havolasini kiriting."); return; }
        out.innerHTML = ""; setLoading(go, true);
        try {
          const d = await api.loadHashtag(url);
          out.innerHTML = result(d);
          const text = (parts) => withSignature(parts.filter(Boolean).join("\n\n"));
          out.querySelector("#cCap").onclick = () => copyText(withSignature(d.caption));
          out.querySelector("#cTags").onclick = () => copyText(withSignature(d.hashtags.join(" ")));
          out.querySelector("#cAll").onclick = () => copyText(text([d.caption, d.hashtags.join(" ")]));
          out.querySelector("#sv").onclick = async () => {
            try { await api.saveHistory(d.id); toast("Saqlandi"); } catch (e) { toast(e.message, "err"); }
          };
          toast("History ga saqlandi");
        } catch (e) { out.innerHTML = errorBox(e.message); }
        finally { setLoading(go, false, BTN); }
      };
      go.onclick = run;
      input.addEventListener("keydown", (e) => e.key === "Enter" && run());
      setTimeout(() => input.focus(), 50);
    },
  });
}

function result(d) {
  return `<div class="result">
    <div class="label">Asl caption</div><div class="text">${esc(d.caption) || "—"}</div>
    <div class="sep"></div><div class="label">Asl hashtaglar</div>${tagsHtml(d.hashtags)}
    <div class="kv"><span>Manba</span><span>${esc(d.source)}</span></div>
    ${d.video_date ? `<div class="kv"><span>Sana</span><span>${esc(d.video_date)}</span></div>` : ""}
    ${d.views != null ? `<div class="kv"><span>Ko‘rishlar</span><span>${d.views.toLocaleString("ru-RU")}</span></div>` : ""}
    <div class="kv"><span>Havola</span><a href="${esc(d.url)}" target="_blank" rel="noopener" style="color:var(--sky)">Videoni ochish</a></div>
    <div class="actions">
      <button class="btn ghost sm" id="cCap">${icon("copy")}<span>Captionni nusxalash</span></button>
      <button class="btn ghost sm" id="cTags">${icon("hash")}<span>Hashtaglarni nusxalash</span></button>
      <button class="btn sm" id="cAll">${icon("copy")}<span>Hammasini nusxalash</span></button>
      <button class="btn ghost sm" id="sv">${icon("save")}<span>Historyga saqlash</span></button>
    </div></div>`;
}
