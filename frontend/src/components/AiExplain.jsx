import React from "react";

export default function AiExplain({ text, loading, onExplain, disabled }) {
  return (
    <div className="card">
      <div className="cardTitle">AI тайлбар</div>
      <div className="cardDesc">
        Анхны (суурь) ба Симуляци (шинэ) үр дүнгийн ялгааг автоматаар тайлбарлана.
      </div>

      <div className="btnRow">
        <button className="btnPrimary" onClick={onExplain} disabled={disabled || loading}>
          {loading ? "Тайлбар үүсгэж байна..." : "AI тайлбар гаргах"}
        </button>
      </div>

      {!loading && (
        <div className="aiText">
          {text || "Тайлбар хараахан алга байна."}
        </div>
      )}

      {!loading && text === "AI тайлбар үүсгэхэд алдаа гарлаа" && (
        <div className="errorText">AI тайлбар үүсгэхэд алдаа гарлаа</div>
      )}
    </div>
  );
}
