import { icon } from "./components/icons.js";
import { renderBio } from "./pages/bio.js";
import { renderHashtag } from "./pages/hashtag.js";
import { renderHistory } from "./pages/history.js";

const tg = window.Telegram?.WebApp;
tg?.ready?.(); tg?.expand?.();
try { tg?.setHeaderColor?.("#000000"); tg?.setBackgroundColor?.("#07080a"); } catch { /* eski versiya */ }

const TABS = [
  { id: "hashtag", label: "Hashtag", ic: "hash", render: renderHashtag },
  { id: "bio", label: "Bio", ic: "user", render: renderBio },
  { id: "history", label: "History", ic: "history", render: renderHistory },
];

const page = document.getElementById("page");
const navEl = document.getElementById("nav");

function go(id) {
  const tab = TABS.find((t) => t.id === id) || TABS[0];
  navEl.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.id === tab.id));
  page.replaceChildren();
  tab.render(page, go);
  tg?.HapticFeedback?.selectionChanged?.();
  history.replaceState(null, "", `#${tab.id}`);
  window.scrollTo({ top: 0 });
}

navEl.innerHTML = TABS.map((t) => `<button class="nav-btn" data-id="${t.id}">${icon(t.ic)}<span>${t.label}</span></button>`).join("");
navEl.addEventListener("click", (e) => { const b = e.target.closest(".nav-btn"); if (b) go(b.dataset.id); });

document.getElementById("brandLogo").innerHTML = icon("hash");
document.getElementById("langChip").innerHTML = `${icon("globe")}UZ`;
const u = tg?.initDataUnsafe?.user;
document.getElementById("avatar").textContent = (u?.first_name || "U").slice(0, 1).toUpperCase();

go(location.hash.slice(1));
