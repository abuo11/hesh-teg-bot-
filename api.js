const tg = window.Telegram?.WebApp;

async function call(method, path, body) {
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers: { "Content-Type": "application/json", "X-Init-Data": tg?.initData || "" },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Server bilan aloqa yo‘q. Internetni tekshiring.");
  }
  let json = null;
  try { json = await res.json(); } catch { /* bo'sh javob */ }
  if (!res.ok || !json?.ok) throw new Error(json?.error || `Xatolik (${res.status})`);
  return json.data;
}

export const api = {
  loadHashtag: (url) => call("POST", "/hashtag", { url }),
  loadBio: (username) => call("POST", "/bio", { username }),
  history: (offset = 0, limit = 10) => call("GET", `/history?offset=${offset}&limit=${limit}`),
  historyItem: (id) => call("GET", `/history/${id}`),
  deleteHistory: (id) => call("DELETE", `/history/${id}`),
  saveHistory: (id) => call("POST", `/history/${id}/save`),
};
