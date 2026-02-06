import React, { useRef } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
} from "chart.js";
import SubscriptSelector from "./SubscriptSelector.jsx";

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend);

export default function ChartCard({
  seriesKey,
  title,
  time,
  baseline,
  simulation,
  availableDims,
  subSelection,
  onSubChange,
  onActivate,
  onPointSelect,
  active,
  footerText
}) {
  const chartRef = useRef(null);
  const labels = (time || []).map((t) => String(t));

  const hasSim = simulation && simulation.length > 0;

  const data = {
    labels,
    datasets: [
      {
        label: "Анхны (суурь)",
        data: baseline || [],
        borderColor: "#2b6fff",
        backgroundColor: "transparent",
        tension: 0.25,
        pointRadius: 0
      },
      {
        label: "Симуляци (шинэ)",
        data: hasSim ? simulation : [],
        borderColor: "#ff3b3b",
        backgroundColor: "transparent",
        tension: 0.25,
        pointRadius: 0
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, labels: { color: "#d8e3ff" } },
      tooltip: { enabled: true }
    },
    scales: {
      x: { ticks: { color: "#a9b8df" }, grid: { color: "rgba(120,140,200,0.10)" } },
      y: { ticks: { color: "#a9b8df" }, grid: { color: "rgba(120,140,200,0.10)" } }
    }
  };

  function handleClick(event) {
    if (onActivate) onActivate(seriesKey);
    const chart = chartRef.current;
    if (!chart || !onPointSelect) return;
    const points = chart.getElementsAtEventForMode(
      event,
      "nearest",
      { intersect: true },
      false
    );
    if (points.length > 0) {
      onPointSelect(seriesKey, points[0].index);
    }
  }

  return (
    <div className={`card chartCard ${active ? "chartActive" : ""}`}>
      <div className="cardTitle">{title}</div>

      <SubscriptSelector
        outputKey={title /* just to keep stable; real binding done in App */}
        availableDims={availableDims}
        selection={subSelection}
        onChange={onSubChange}
      />

      <div className="chartWrap">
        <Line ref={chartRef} data={data} options={options} onClick={handleClick} />
      </div>

      {footerText && (
        <div className="smallHint">
          {footerText}
        </div>
      )}
    </div>
  );
}
