import React from "react";

function formatValue(s, v) {
  if (s.as_percent) {
    return `${Math.round(v * 100)} ${s.unit_mn}`;
  }
  if (s.unit_mn === "толгой") {
    return `${Math.round(v).toLocaleString()} ${s.unit_mn}`;
  }
  return `${v} ${s.unit_mn}`;
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (s.includes(",") || s.includes("\n") || s.includes('"')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function buildCsv(series, outputs, mode) {
  if (!series?.time?.length) return "";
  const header = ["time", ...outputs.map((o) => o.key)].join(",");
  const rows = series.time.map((t, i) => {
    const cols = [csvEscape(t)];
    for (const o of outputs) {
      const arr = series?.[mode]?.[o.key] || [];
      cols.push(csvEscape(arr[i]));
    }
    return cols.join(",");
  });
  return [header, ...rows].join("\n");
}

function downloadCsv(series, outputs, mode, filename) {
  const csv = buildCsv(series, outputs, mode);
  if (!csv) return;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function SliderPanel({ sliders, values, onChange, onRun, onReset, running, series, outputs }) {
  const canDownload = !!series?.time?.length;
  return (
    <div className="card">
      <div className="cardTitle">Симуляци</div>
      <div className="cardDesc">
        Slider-уудаар параметрүүдийг тохируулж, “Симуляци ажиллуулах” дарж шинэ үр дүнг улаанаар харьцуулна.
      </div>

      <div className="sliderList">
        {sliders.map((s) => {
          const v = values[s.key] ?? s.default;
          return (
            <div className="sliderItem" key={s.key}>
              <div className="sliderTop">
                <div className="sliderLabel">{s.label_mn}</div>
                <div className="sliderValue">{formatValue(s, v)}</div>
              </div>

              <input
                className="slider"
                type="range"
                min={s.min}
                max={s.max}
                step={s.step}
                value={v}
                onChange={(e) => onChange(s.key, Number(e.target.value))}
              />
              <div className="sliderMinMax">
                <span>{formatValue(s, s.min)}</span>
                <span>{formatValue(s, s.max)}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="btnRow">
        <button className="btnPrimary" onClick={onRun} disabled={running}>
          {running ? "Ажиллаж байна..." : "Симуляци ажиллуулах"}
        </button>
        <button className="btnGhost" onClick={onReset} disabled={running}>
          Reset / Анхны утга
        </button>
      </div>

      <div className="btnRow">
        <button
          className="btnGhost"
          onClick={() => downloadCsv(series, outputs, "baseline", "baseline.csv")}
          disabled={!canDownload}
        >
          CSV татах (суурь)
        </button>
        <button
          className="btnGhost"
          onClick={() => downloadCsv(series, outputs, "simulation", "simulation.csv")}
          disabled={!canDownload}
        >
          CSV татах (симуляци)
        </button>
      </div>

      <div className="legendHint">
        <span className="dot dotBlue"></span> Анхны (суурь)
        <span className="dot dotRed"></span> Симуляци (шинэ)
      </div>
    </div>
  );
}
