import React from "react";

export default function Header({ title, subtitle, demoMode }) {
  return (
    <div className="header">
      <div>
        <div className="title">{title}</div>
        <div className="subtitle">{subtitle}</div>
      </div>
      <div className="badgeRow">
        <span className={`badge ${demoMode ? "badgeWarn" : "badgeOk"}`}>
          {demoMode ? "DEMO MODE" : "MODEL MODE"}
        </span>
      </div>
    </div>
  );
}
