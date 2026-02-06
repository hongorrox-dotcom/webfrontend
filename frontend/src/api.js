const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

function fixMojibake(value) {
  if (typeof value !== "string") return value;
  // Heuristic: common mojibake markers for UTF-8 decoded as Latin-1
  if (!/[ÃÐÑ]/.test(value)) return value;
  try {
    const bytes = Uint8Array.from(value, (c) => c.charCodeAt(0));
    return new TextDecoder("utf-8").decode(bytes);
  } catch {
    return value;
  }
}

function normalizeText(obj) {
  if (Array.isArray(obj)) return obj.map(normalizeText);
  if (obj && typeof obj === "object") {
    const out = {};
    for (const [k, v] of Object.entries(obj)) {
      out[k] = normalizeText(v);
    }
    return out;
  }
  return fixMojibake(obj);
}

export async function apiGetConfig() {
  const res = await fetch(`${API_BASE}/api/config`);
  if (!res.ok) throw new Error("Тохиргоо татахад алдаа гарлаа");
  const data = await res.json();
  return normalizeText(data);
}

export async function apiSimulate(payload) {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Симуляци хийхэд алдаа гарлаа");
  return await res.json();
}

export async function apiReset(payload) {
  const res = await fetch(`${API_BASE}/api/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Reset хийхэд алдаа гарлаа");
  return await res.json();
}

export async function apiExplain(payload) {
  const res = await fetch(`${API_BASE}/api/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("AI тайлбар авахад алдаа гарлаа");
  return await res.json();
}

export async function apiChatGraph(payload) {
  const res = await fetch(`${API_BASE}/api/chat_graph`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Чатбот хариу авахад алдаа гарлаа");
  return await res.json();
}
