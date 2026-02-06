import React, { useEffect, useMemo, useState } from "react";
import Header from "./components/Header.jsx";
import SliderPanel from "./components/SliderPanel.jsx";
import ChartCard from "./components/ChartCard.jsx";
import AiExplain from "./components/AiExplain.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import ChatbotWidget from "./components/ChatbotWidget.jsx";
import { useChat } from "./hooks/useChat.js";
import { apiGetConfig, apiSimulate, apiReset, apiExplain, apiChatGraph } from "./api.js";

function pct(a, b) {
  if (a === 0 || a === null || a === undefined) return null;
  return ((b - a) / a) * 100;
}

function summarizeOne(time, baseline, simulation) {
  if (!time?.length || !baseline?.length || !simulation?.length) return {};
  const b0 = baseline[0], bN = baseline[baseline.length - 1];
  const s0 = simulation[0], sN = simulation[simulation.length - 1];

  const bMin = Math.min(...baseline), bMax = Math.max(...baseline);
  const sMin = Math.min(...simulation), sMax = Math.max(...simulation);

  return {
    time_start: time[0],
    time_end: time[time.length - 1],
    baseline_last: bN,
    sim_last: sN,
    pct_change_last: pct(bN, sN),
    baseline_min: bMin,
    baseline_max: bMax,
    sim_min: sMin,
    sim_max: sMax,
    baseline_trend: bN > b0 ? "өсөх" : "буурах/тогтвортой",
    sim_trend: sN > s0 ? "өсөх" : "буурах/тогтвортой"
  };
}

function downsampleSeries(time, baseline, simulation, maxPoints = 180) {
  const len = time?.length || 0;
  if (len <= maxPoints) {
    return { time, baseline, simulation };
  }
  const step = Math.ceil(len / maxPoints);
  const t = [];
  const b = [];
  const s = [];
  for (let i = 0; i < len; i += step) {
    t.push(time[i]);
    b.push(baseline[i]);
    s.push(simulation[i]);
  }
  if (t[t.length - 1] !== time[len - 1]) {
    t.push(time[len - 1]);
    b.push(baseline[len - 1]);
    s.push(simulation[len - 1]);
  }
  return { time: t, baseline: b, simulation: s };
}

function diffParams(baseParams, params) {
  const changes = [];
  const keys = new Set([...(Object.keys(baseParams || {})), ...(Object.keys(params || {}))]);
  for (const key of Array.from(keys)) {
    const b = baseParams?.[key];
    const s = params?.[key];
    if (b === s) continue;
    const delta = (typeof b === "number" && typeof s === "number") ? (s - b) : null;
    changes.push({ key, baseline: b, sim: s, delta });
  }
  return changes;
}

export default function App() {
  const [config, setConfig] = useState(null);
  const [params, setParams] = useState({});
  const [baseParams, setBaseParams] = useState({});
  const [subscripts, setSubscripts] = useState({}); // global subscript selection
  const [series, setSeries] = useState(null);
  const [running, setRunning] = useState(false);

  const [aiText, setAiText] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [activeSeriesKey, setActiveSeriesKey] = useState(null);
  const [selectedTimePoint, setSelectedTimePoint] = useState(null);

  useEffect(() => {
    (async () => {
      const cfg = await apiGetConfig();
      setConfig(cfg);

      // init slider defaults
      const initParams = {};
      for (const s of cfg.sliders) initParams[s.key] = s.default;
      setParams(initParams);
      setBaseParams(initParams);

      // init subscripts: use first output's dims as global selection
      const initSubs = {};
      const outputs = cfg.available_subscripts?.outputs || {};
      const firstOutKey = Object.keys(outputs)[0];
      const dims = firstOutKey ? (outputs[firstOutKey] || []) : [];
      if (dims.length > 0) {
        for (const d of dims) initSubs[d.name] = d.values[0];
      }
      setSubscripts(initSubs);

      // baseline load (reset endpoint returns baseline, empty simulation)
      const resetPayload = {
        params: initParams,
        subscripts: Object.fromEntries(
          outputs ? Object.keys(outputs).map((k) => [k, initSubs]) : []
        )
      };
      const sData = await apiReset(resetPayload);
      setSeries(sData);
      setActiveSeriesKey(Object.keys(outputs)[0] || null);
    })().catch((e) => {
      console.error(e);
      alert("Апп эхлүүлэхэд алдаа гарлаа. Backend ажиллаж байгаа эсэхийг шалгана уу.");
    });
  }, []);

  const outputs = useMemo(() => {
    if (!config) return [];
    return [
      { key: "herd_total_total", title: config.outputs_ui_mn.herd_total_total },
      { key: "herd_total", title: config.outputs_ui_mn.herd_total },
      { key: "births", title: config.outputs_ui_mn.births },
      { key: "losses", title: config.outputs_ui_mn.losses },
      { key: "sold_used", title: config.outputs_ui_mn.sold_used }
    ];
  }, [config]);

  const chatSeriesKey = outputs.find((o) => o.key === "herd_total_total")?.key || outputs[0]?.key || null;
  const chatSeriesTitle = outputs.find((o) => o.key === chatSeriesKey)?.title || "";
  const changedParams = useMemo(() => diffParams(baseParams, params), [baseParams, params]);
  const chatAppliedSubscripts = series?.applied_subscripts?.[chatSeriesKey] || subscripts || {};

  const { messages, loading: chatLoading, error: chatError, sendMessage, resetMessages } = useChat(async (question) => {
    const seriesKey = chatSeriesKey || activeSeriesKey || outputs[0]?.key || null;
    const selectedSeries = outputs.find((o) => o.key === seriesKey) || outputs[0];
    const time = series?.time || [];
    const baseline = series?.baseline?.[seriesKey] || [];
    const simulation = series?.simulation?.[seriesKey] || [];
    const wantsYear = /(?:19|20)\d{2}/.test(question);
    const ds = wantsYear ? { time, baseline, simulation } : downsampleSeries(time, baseline, simulation, 180);

    const payload = {
      question,
      run_meta: {
        selected_series_key: seriesKey,
        selected_series_title: selectedSeries?.title || "",
        selected_time_point: selectedTimePoint ?? null,
        selected_time_window: null,
        selected_subscripts: subscripts || {},
        applied_subscripts: chatAppliedSubscripts || {},
        changed_params: changedParams || []
      },
      params: {
        baseline_params: baseParams,
        sim_params: params
      },
      series: [
        {
          series_key: seriesKey || "unknown",
          title: selectedSeries?.title || "",
          unit: null,
          time: ds.time || [],
          baseline_values: ds.baseline || [],
          sim_values: ds.simulation || []
        }
      ]
    };

    const res = await apiChatGraph(payload);
    return res.reply || "";
  });

  function handleParamChange(key, value) {
    setParams((p) => ({ ...p, [key]: value }));
  }

  async function handleSubChange(_outputKey, dimName, value) {
    const nextSubs = {
      ...subscripts,
      [dimName]: value
    };

    setSubscripts(nextSubs);

    try {
      setRunning(true);
      const outputsMap = config?.available_subscripts?.outputs || {};
      const payload = {
        params,
        subscripts: Object.fromEntries(
          Object.keys(outputsMap).map((k) => [k, nextSubs])
        )
      };
      const sData = await apiReset(payload);
      setSeries(sData);
      setAiText("");
      resetMessages();
    } catch (e) {
      console.error(e);
      alert("Subscript сонголт хийхэд алдаа гарлаа.");
    } finally {
      setRunning(false);
    }
  }

  async function runSimulation() {
    setRunning(true);
    setAiText("");
    resetMessages();
    try {
      const outputsMap = config?.available_subscripts?.outputs || {};
      const defaults = {};
      for (const s of config.sliders) defaults[s.key] = s.default;

      const changedParams = {};
      for (const key of Object.keys(params)) {
        if (params[key] !== defaults[key]) changedParams[key] = params[key];
      }

      const payload = {
        params: changedParams,
        subscripts: Object.fromEntries(
          Object.keys(outputsMap).map((k) => [k, subscripts])
        )
      };

      // If no params changed, just return baseline (no sim change)
      const sData = Object.keys(changedParams).length === 0
        ? await apiReset(payload)
        : await apiSimulate(payload);

      setSeries(sData);
    } catch (e) {
      console.error(e);
      alert("Симуляци хийхэд алдаа гарлаа.");
    } finally {
      setRunning(false);
    }
  }

  async function runExplain() {
    if (!series?.time?.length) {
      alert("Эхлээд симуляци ажиллуулна уу.");
      return;
    }

    const hasSim = outputs.some((o) => (series.simulation?.[o.key] || []).length > 0);
    if (!hasSim) {
      alert("Симуляци ажиллуулаагүй байна.");
      return;
    }

    setAiLoading(true);
    setAiText("");
    try {
      const stats = {};
      for (const o of outputs) {
        const baseArr = series.baseline?.[o.key] || [];
        const simArr = series.simulation?.[o.key] || [];
        if (simArr.length > 0) {
          stats[o.key] = summarizeOne(series.time, baseArr, simArr);
        }
      }
      const exp = await apiExplain({ params_used: params, stats });
      setAiText(exp.text_mn || "");
    } catch (e) {
      console.error(e);
      setAiText("AI тайлбар үүсгэхэд алдаа гарлаа");
    } finally {
      setAiLoading(false);
    }
  }

  async function doReset() {
    setRunning(true);
    setAiText("");
    resetMessages();
    try {
      // reset sliders to defaults
      const initParams = {};
      for (const s of config.sliders) initParams[s.key] = s.default;
      setParams(initParams);
      setBaseParams(initParams);

      const outputsMap = config?.available_subscripts?.outputs || {};
      const sData = await apiReset({
        params: initParams,
        subscripts: Object.fromEntries(
          Object.keys(outputsMap).map((k) => [k, subscripts])
        )
      });
      setSeries(sData);
    } catch (e) {
      console.error(e);
      alert("Reset хийхэд алдаа гарлаа.");
    } finally {
      setRunning(false);
    }
  }

  if (!config || !series) {
    return (
      <div className="appShell">
        <div className="loading">Ачаалж байна...</div>
      </div>
    );
  }

  const av = config.available_subscripts?.outputs || {};
  const firstOutKey = Object.keys(av)[0];
  const globalDims = firstOutKey ? (av[firstOutKey] || []) : [];
  const timeLabel = "TIME";

  return (
    <>
    <div className="appShell">
      <Header
        title={config.ui_title_mn}
        subtitle={config.ui_subtitle_mn}
        demoMode={config.demo_mode}
      />

      <div className="layout">
        <div className="leftCol">
          <SliderPanel
            sliders={config.sliders}
            values={params}
            onChange={handleParamChange}
            onRun={runSimulation}
            onReset={doReset}
            running={running}
            series={series}
            outputs={outputs}
          />

          <AiExplain
            text={aiText}
            loading={aiLoading}
            onExplain={runExplain}
            disabled={running}
          />
        </div>

        <div className="rightCol">
          {/* Global subscript selector */}
          {Array.isArray(globalDims) && globalDims.length > 0 && (
            <div className="card" style={{ marginBottom: 14 }}>
              <div className="cardTitle">Subscript сонголт</div>
              <div className="subsel">
                {globalDims.map((dim) => {
                  const cur = subscripts?.[dim.name] ?? dim.values[0];
                  return (
                    <div key={dim.name} className="subselDim">
                      <div className="subselDimName">{dim.name}</div>
                      <div className="segmented">
                        {dim.values.map((v) => {
                          const active = v === cur;
                          return (
                            <button
                              key={v}
                              className={`segBtn ${active ? "segBtnActive" : ""}`}
                              onClick={() => handleSubChange("__global__", dim.name, v)}
                              type="button"
                            >
                              {v}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid">
            {outputs.map((o, idx) => (
              <div className={`gridItem ${idx === 0 ? "gridItemLarge" : ""}`} key={o.key}>
                <ChartCard
                  seriesKey={o.key}
                  title={o.title}
                  time={series.time}
                  baseline={series.baseline?.[o.key] || []}
                  simulation={series.simulation?.[o.key] || []}
                  availableDims={[]}
                  subSelection={{}}
                  onSubChange={() => {}}
                  active={activeSeriesKey === o.key}
                  onActivate={(key) => setActiveSeriesKey(key)}
                  onPointSelect={(key, idx) => {
                    setActiveSeriesKey(key);
                    const tp = series?.time?.[idx];
                    setSelectedTimePoint(tp ?? null);
                  }}
                  footerText={`X тэнхлэг: ${timeLabel} (модель дээрх нэгжээс хамаарна)`}
                />
              </div>
            ))}
          </div>

          <div className="footnote">
            Цэнхэр = Анхны (суурь), Улаан = Симуляци (шинэ)
          </div>

          <ChatPanel
            messages={messages}
            loading={chatLoading}
            error={chatError}
            onSend={sendMessage}
            selectedSeriesTitle={chatSeriesTitle}
            selectedTimePoint={selectedTimePoint}
            selectedSubscripts={subscripts}
            appliedSubscripts={chatAppliedSubscripts}
            changedParams={changedParams}
          />
        </div>
      </div>
    </div>
    <ChatbotWidget />
    </>
  );
}
