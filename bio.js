import { api } from "../api.js";
import { icon } from "../components/icons.js";
import { copyText, errorBox, esc, openModal, setLoading } from "../components/ui.js";

const BTN = `${icon("search")}<span>Bio olish</span>`;

export function renderBio(root) {
  root.innerHTML = `<div class="stack"><section class="card hero">
    <div class="card-head"><div class="ico pink">${icon("user")}</div><h2>Bio yuklash</h2></div>
    <p>Instagram username yoki profil havolasi orqali mavjud bio ma’lumotlarini oling.</p>
    <button class="btn" id="open">${icon("user")}<span>Bio yuklash</span></button></section></div>`;
  root.querySelector("#open").onclick = openBioModal;
}

export function openBioModal() {
  openModal({
    title: "👤 Instagram Bio",
    desc: "Instagram username yoki profil havolasini kiriting.",
    body: `<div class="gap"><input class="input" id="u" autocomplete="off" autocapitalize="none" placeholder="@username">
      <button class="btn" id="go">${BTN}</button></div><div id="out"></div>`,
    onMount(el, close) {
      const input = el.querySelector("#u"), go = el.querySelector("#go"), out = el.querySelector("#out");
      const run = async () => {
        const v = input.value.trim();
        if (!v) { out.innerHTML = errorBox("Username kiriting."); return; }
        out.innerHTML = ""; setLoading(go, true);
        try {
          const d = await api.loadBio(v);
          out.innerHTML = `<div class="result">
            <div class="label">Username</div><div class="text">@${esc(d.username)}</div><div class="sep"></div>
            <div class="label">Profil nomi</div><div class="text">${esc(d.name) || "—"}</div><div class="sep"></div>
            <div class="label">Bio</div><div class="text">${esc(d.biography) || "—"}</div>
            <div class="kv"><span>Profil</span><a href="${esc(d.url)}" target="_blank" rel="noopener" style="color:var(--sky)">Ochish</a></div>
            <div class="kv"><span>Manba</span><span>${esc(d.source)}</span></div>
            <div class="actions"><button class="btn sm" id="cp">${icon("copy")}<span>Bio nusxalash</span></button>
            <button class="btn ghost sm" id="bk">⬅️ Orqaga</button></div></div>`;
          out.querySelector("#cp").onclick = () => copyText(d.biography || "");
          out.querySelector("#bk").onclick = close;
        } catch (e) { out.innerHTML = errorBox(e.message); }
        finally { setLoading(go, false, BTN); }
      };
      go.onclick = run;
      input.addEventListener("keydown", (e) => e.key === "Enter" && run());
      setTimeout(() => input.focus(), 50);
    },
  });
}
