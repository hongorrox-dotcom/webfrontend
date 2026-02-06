import React, { useState } from "react";

export default function ChatPanel({
  messages,
  loading,
  error,
  onSend,
  selectedSeriesTitle,
  selectedTimePoint,
  selectedSubscripts,
  appliedSubscripts,
  changedParams
}) {
  const [input, setInput] = useState("");

  const subscriptText = (subs) => {
    if (!subs || Object.keys(subs).length === 0) return "-";
    return Object.entries(subs)
      .map(([k, v]) => `${k}=${v}`)
      .join(", ");
  };

  const changedText = Array.isArray(changedParams) && changedParams.length > 0
    ? changedParams.map((p) => {
      const delta = p.delta === null || p.delta === undefined ? "" : ` (Δ ${p.delta})`;
      return `${p.key}: ${p.baseline} → ${p.sim}${delta}`;
    }).join("; ")
    : "-";

  function handleSubmit(e) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    onSend(q);
    setInput("");
  }

  return (
    <div className="card chatPanel">
      <div className="cardTitle">Чатбот анализ</div>
      <div className="cardDesc">
        Сонгосон графикийн өгөгдөл дээр тулгуурлан тайлбарлана.
      </div>

      <div className="chatMeta">
        <div>Идэвхтэй үзүүлэлт: <b>{selectedSeriesTitle || "-"}</b></div>
        <div>Сонгосон хугацаа: <b>{selectedTimePoint ?? "-"}</b></div>
        <div>Subscript сонголт: <b>{subscriptText(selectedSubscripts)}</b></div>
        <div>Хэрэгжсэн subscript: <b>{subscriptText(appliedSubscripts)}</b></div>
        <div>Өөрчилсөн параметрүүд: <b>{changedText}</b></div>
      </div>

      <div className="chatList">
        {messages.length === 0 && (
          <div className="chatEmpty">Асуултаа бичээд илгээнэ үү.</div>
        )}
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`chatMsg ${m.role === "user" ? "chatMsgUser" : "chatMsgAssistant"}`}
          >
            {m.text}
          </div>
        ))}
      </div>

      {error && <div className="errorText">{error}</div>}

      <form className="chatInputRow" onSubmit={handleSubmit}>
        <input
          className="chatInput"
          placeholder="Жишээ: Өсөлтийн хувь хэд вэ?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button className="btnPrimary" type="submit" disabled={loading || !input.trim()}>
          {loading ? "Илгээж байна..." : "Илгээх"}
        </button>
      </form>
    </div>
  );
}
