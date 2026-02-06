from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
import re

from .config import settings
from .schemas import (
    ConfigPayload,
    SimulateRequest,
    ExplainRequest,
    ExplainResponse,
    SliderDef,
    AvailableSubscripts,
    DimDef,
    SeriesPayload,
    ChatGraphRequest,
    ChatGraphResponse,
)
from .model_engine import ModelEngine, OUTPUT_KEYS
from .stats import build_stats_payload
from .openai_client import openai_explain_mn

app = FastAPI(title="Vensim to Python Web API", version="1.0.0")


def _fix_text(value: Any) -> Any:
    if isinstance(value, str):
        if any(ch in value for ch in ("Ã", "Ð", "Ñ", "â", "�")):
            try:
                return value.encode("latin-1").decode("utf-8")
            except Exception:
                return value
        return value
    if isinstance(value, list):
        return [_fix_text(v) for v in value]
    if isinstance(value, dict):
        return {(_fix_text(k) if isinstance(k, str) else k): _fix_text(v) for k, v in value.items()}
    return value

# CORS :contentReference[oaicite:10]{index=10}
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ModelEngine()
engine.load()

OUTPUTS_UI_MN = {
    "herd_total": "Бэлчээрийн малын тоо толгой",
    "births": "Бэлчээрийн мал сүргийн төллөлт",
    "losses": "Малын зүй бус хорогдол",
    "sold_used": "Борлуулсан болон хүнсэнд хэрэглэсэн малын тоо толгой",
    "herd_total_total": "Нийт бэлчээрийн малын тоо",
}

SLIDERS: list[SliderDef] = [
    SliderDef(
        key="repro_rate",
        label_mn="Бэлчээрийн малын нөхөн үржих хувь хэмжээ",
        unit_mn="%",
        min=0.0,
        max=1.0,
        step=0.01,
        default=0.22,
        as_percent=True,
    ),
    SliderDef(
        key="slaughter_share",
        label_mn="Хэрэгцээнд нядалсан малын эзлэх хувь",
        unit_mn="%",
        min=0.0,
        max=1.0,
        step=0.01,
        default=0.12,
        as_percent=True,
    ),
    SliderDef(
        key="initial_herd",
        label_mn="Бэлчээрийн малын анхны тоо толгой",
        unit_mn="толгой",
        min=10000,
        max=5000000,
        step=10000,
        default=800000,
        as_percent=False,
    ),
    SliderDef(
        key="sold_used_share",
        label_mn="Борлуулсан болон хүнсэнд хэрэглэсэн малын хувь хэмжээ",
        unit_mn="%",
        min=0.0,
        max=1.0,
        step=0.01,
        default=0.08,
        as_percent=True,
    ),
    SliderDef(
        key="disaster_impact",
        label_mn="Байгалийн гамшгийн бэлчээрийн мал сүргийн нөхөн төлжих нөлөө",
        unit_mn="%",
        min=0.0,
        max=0.8,
        step=0.01,
        default=0.25,
        as_percent=True,
    ),
    SliderDef(
        key="disaster_first_year",
        label_mn="Байгалийн гамшиг тохиолдсон анхны жил",
        unit_mn="жил",
        min=1980,
        max=2100,
        step=1,
        default=2006,
        as_percent=False,
    ),
    SliderDef(
        key="disaster_freq",
        label_mn="Байгалийн гамшгийн давтамж",
        unit_mn="жил тутам",
        min=1,
        max=15,
        step=1,
        default=5,
        as_percent=False,
    ),
]


@app.get("/")
def root():
    return {"message": "Backend ажиллаж байна. /docs дээр API-г шалгана уу."}


@app.get("/api/health")
def health():
    return {"ok": True, "demo_mode": engine.demo_mode}


@app.get("/api/config")
def get_config():
    av = engine.get_available_subscripts()
    av_pyd = AvailableSubscripts(
        outputs={
            k: [DimDef(**d) for d in v] for k, v in av.items()
        }
    )

    payload = ConfigPayload(
        ui_title_mn="Vensim → Python (PySD) Вэб Симуляци",
        ui_subtitle_mn="",
        outputs_ui_mn=OUTPUTS_UI_MN,
        sliders=SLIDERS,
        variable_map=engine.variable_map,
        param_map=engine.param_map,
        available_subscripts=av_pyd,
        demo_mode=engine.demo_mode,
    )
    fixed = _fix_text(payload.model_dump())
    return JSONResponse(content=fixed)


@app.post("/api/simulate")
def simulate(req: SimulateRequest):
    time, baseline, simulation = engine.simulate(req.params, req.subscripts)
    applied = engine.applied_subscripts_per_output(req.subscripts)

    return SeriesPayload(
        time=time,
        baseline=baseline,
        simulation=simulation,
        applied_subscripts=applied,
    )


@app.post("/api/reset")
def reset(req: SimulateRequest):
    time, baseline = engine.get_baseline_filtered(req.subscripts)
    applied = engine.applied_subscripts_per_output(req.subscripts)

    # reset үед simulation-ийг baseline-тэй адил биш, хоосон болгоно
    simulation = {k: [] for k in OUTPUT_KEYS}

    return SeriesPayload(
        time=time,
        baseline=baseline,
        simulation=simulation,
        applied_subscripts=applied,
    )


@app.post("/api/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    if not settings.OPENAI_API_KEY:
        return ExplainResponse(text_mn="AI API key тохируулаагүй байна.")

    # Frontend stats явуулаагүй бол fallback (хоосон)
    stats = req.stats or {}

        # Prompt (MN) – 3–5 өгүүлбэр, энгийн тайлбар
    prompt = f"""
Та статистикийн үндсэн дээр дараахь график мэдээлэлийг дүн шинжилгээ хийж, "монголь хэлээр" 3-5 өгүүлбэл товч, ойлгомжтой, мэдээлэлтэй тайлбар бичнэ үү.

Өөрчлөгдсөн параметрүүд:
{req.params_used}

Үзүүлэлт бүрийн товч статистик:
{stats}

ЧУХАЛ:
- Архаг эсвэл технологийн нэр томъёо ашиглахгүй, энгийн монголоор бичнэ үү
- Статистик мэдээлэлүүдийг ашиглан үндэстэй дүгнэлт гараа
- Өмнөх болон шинэ өгөгдөлүүдийн ялгаа, үр дүнг товч тайлбарла
""".strip()

    try:
        text_mn = openai_explain_mn(prompt)
        return ExplainResponse(text_mn=text_mn)
    except Exception as e:
        return ExplainResponse(text_mn=f"AI тайлбар үүсгэхэд алдаа гарлаа: {e}")


CHAT_SYSTEM_PROMPT = """
Та зөвхөн өгөгдөл дээр үндэслэн хариулна.

Дүрэм:
- Таамаглал, экстраполяци хийхгүй. Харин time массивт асуусан он байхгүй бол
    хамгийн ойрын байгаа оныг ашиглаж, “ойролцоо” гэдгийг ТОДОРХОЙ дурд.
- Хариуг аль болох тоон баримттай бич.
- Шалтгааныг баталж тайлбарлахгүй; зөвхөн ажиглагдсан өөрчлөлтийг тайлбарлана.
""".strip()


def _pct_delta(b: float, s: float) -> float:
    denom = max(abs(b), 1e-9)
    return (s - b) / denom * 100.0


def _find_time_index(time_list: list, target: Any) -> int | None:
    for i, t in enumerate(time_list):
        if str(t) == str(target):
            return i
        try:
            if float(t) == float(target):
                return i
        except Exception:
            continue
    return None


def _resolve_time_value(time_list: list, target: Any) -> tuple[Any, int | None, bool]:
    idx = _find_time_index(time_list, target)
    if idx is not None:
        return time_list[idx], idx, True
    try:
        target_num = float(target)
    except Exception:
        return None, None, False
    best_idx = None
    best_diff = None
    for i, t in enumerate(time_list):
        try:
            diff = abs(float(t) - target_num)
        except Exception:
            continue
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_idx = i
    if best_idx is None:
        return None, None, False
    return time_list[best_idx], best_idx, False


def _extract_year_from_question(question: str) -> str | None:
    m = re.search(r"\b(19|20)\d{2}\b", question)
    return m.group(0) if m else None


def _extract_year_range(question: str) -> tuple[str, str] | None:
    m = re.search(r"\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2})\b", question)
    if not m:
        return None
    return m.group(1), m.group(2)


def _calc_growth_pct(values: list[float], time: list, start: Any, end: Any) -> float | None:
    start_idx = _find_time_index(time, start)
    end_idx = _find_time_index(time, end)
    if start_idx is None or end_idx is None:
        return None
    try:
        start_val = values[start_idx]
        end_val = values[end_idx]
        if start_val is None or end_val is None:
            return None
        return _pct_delta(start_val, end_val)
    except Exception:
        return None


def _build_chat_context(req: ChatGraphRequest) -> Dict[str, Any]:
    series_context = []
    for s in req.series:
        if not s.time:
            continue

        last_idx = len(s.time) - 1
        b_last = s.baseline_values[last_idx] if len(s.baseline_values) > last_idx else None
        s_last = s.sim_values[last_idx] if len(s.sim_values) > last_idx else None

        delta_last = (s_last - b_last) if (b_last is not None and s_last is not None) else None
        pct_last = _pct_delta(b_last, s_last) if (b_last is not None and s_last is not None) else None

        selected_tp = req.run_meta.selected_time_point
        sel_idx = _find_time_index(s.time, selected_tp) if selected_tp is not None else None
        sel_baseline = None
        sel_sim = None
        sel_delta = None
        sel_pct = None
        if sel_idx is not None:
            if len(s.baseline_values) > sel_idx:
                sel_baseline = s.baseline_values[sel_idx]
            if len(s.sim_values) > sel_idx:
                sel_sim = s.sim_values[sel_idx]
            if sel_baseline is not None and sel_sim is not None:
                sel_delta = sel_sim - sel_baseline
                sel_pct = _pct_delta(sel_baseline, sel_sim)

        series_context.append({
            "series_key": s.series_key,
            "title": s.title,
            "unit": s.unit,
            "time_start": s.time[0],
            "time_end": s.time[-1],
            "baseline_last": b_last,
            "sim_last": s_last,
            "delta_last": delta_last,
            "pct_last": pct_last,
            "selected_time_point": selected_tp,
            "selected_time_baseline": sel_baseline,
            "selected_time_sim": sel_sim,
            "selected_time_delta": sel_delta,
            "selected_time_pct": sel_pct,
            "time": s.time,
            "baseline_values": s.baseline_values,
            "sim_values": s.sim_values,
        })

    params_union = set(req.params.baseline_params.keys()) | set(req.params.sim_params.keys())
    param_changes = []
    changed_only = []
    for k in sorted(params_union):
        b = req.params.baseline_params.get(k)
        s = req.params.sim_params.get(k)
        if b is None and s is None:
            continue
        delta = None
        try:
            if b is not None and s is not None:
                delta = s - b
        except Exception:
            delta = None
        param_changes.append({
            "param": k,
            "baseline": b,
            "sim": s,
            "delta": delta,
        })
        if delta not in (None, 0):
            changed_only.append({
                "param": k,
                "baseline": b,
                "sim": s,
                "delta": delta,
            })

    year = _extract_year_from_question(req.question)
    year_lookup = []
    year_missing = False
    if year:
        for s in req.series:
            idx = _find_time_index(s.time, year)
            if idx is None:
                year_missing = True
                year_lookup.append({
                    "series_key": s.series_key,
                    "title": s.title,
                    "year": year,
                    "available": False,
                })
            else:
                b_val = s.baseline_values[idx] if len(s.baseline_values) > idx else None
                s_val = s.sim_values[idx] if len(s.sim_values) > idx else None
                delta = (s_val - b_val) if (b_val is not None and s_val is not None) else None
                pct = _pct_delta(b_val, s_val) if (b_val is not None and s_val is not None) else None
                year_lookup.append({
                    "series_key": s.series_key,
                    "title": s.title,
                    "year": year,
                    "available": True,
                    "baseline": b_val,
                    "sim": s_val,
                    "delta": delta,
                    "pct": pct,
                })

    return {
        "question": req.question,
        "run_meta": req.run_meta.model_dump(),
        "series": series_context,
        "param_changes": param_changes,
        "changed_params": changed_only,
        "year_lookup": year_lookup,
        "year_missing": year_missing,
    }


@app.post("/api/chat_graph", response_model=ChatGraphResponse)
def chat_graph(req: ChatGraphRequest):
    year_range = _extract_year_range(req.question)
    if year_range and req.series:
        start_year, end_year = year_range
        s0 = req.series[0]
        start_val, start_idx, start_exact = _resolve_time_value(s0.time, start_year)
        end_val, end_idx, end_exact = _resolve_time_value(s0.time, end_year)
        if start_idx is None or end_idx is None:
            return ChatGraphResponse(
                reply=f"{start_year}-{end_year} хоорондох өгөгдөл олдсонгүй. Time массив дотор энэ онууд байхгүй байна."
            )
        base_growth = _calc_growth_pct(s0.baseline_values, s0.time, start_val, end_val)
        sim_growth = _calc_growth_pct(s0.sim_values, s0.time, start_val, end_val)
        parts = [f"{s0.title} ({start_year}–{end_year}) өсөлтийн хувь:"]
        if base_growth is not None:
            parts.append(f"Суурь: {base_growth:.2f}%")
        if sim_growth is not None:
            parts.append(f"Симуляци: {sim_growth:.2f}%")
        if not start_exact or not end_exact:
            parts.append(f"(Ойролцоо: {start_year} → {start_val}, {end_year} → {end_val})")
        return ChatGraphResponse(reply="; ".join(parts))

    if "өсөлтийн хувь" in req.question and req.series:
        s0 = req.series[0]
        start = s0.time[0] if s0.time else None
        end = s0.time[-1] if s0.time else None
        if start is None or end is None:
            return ChatGraphResponse(reply="Өгөгдөл хоосон байна.")

        start_val, start_idx, start_exact = _resolve_time_value(s0.time, start)
        end_val, end_idx, end_exact = _resolve_time_value(s0.time, end)
        if start_idx is None or end_idx is None:
            return ChatGraphResponse(reply="Өгөгдөл олдсонгүй.")

        base_growth = _calc_growth_pct(s0.baseline_values, s0.time, start_val, end_val)
        sim_growth = _calc_growth_pct(s0.sim_values, s0.time, start_val, end_val)
        parts = [f"{s0.title} өсөлтийн хувь ({start_val}–{end_val}):"]
        if base_growth is not None:
            parts.append(f"Суурь: {base_growth:.2f}%")
        if sim_growth is not None:
            parts.append(f"Симуляци: {sim_growth:.2f}%")
        return ChatGraphResponse(reply="; ".join(parts))

    if not settings.OPENAI_API_KEY:
        return ChatGraphResponse(reply="AI API key тохируулаагүй байна.")

    context = _build_chat_context(req)

    try:
        prompt = (
            CHAT_SYSTEM_PROMPT
            + "\n\nАсуулт: "
            + req.question
            + "\n\nӨгөгдлийн контекст (JSON):\n"
            + json.dumps(context, ensure_ascii=False)
        )
        text = openai_explain_mn(prompt)
        if not text:
            return ChatGraphResponse(reply="Өгөгдөлд суурилсан хариу олдсонгүй.")
        return ChatGraphResponse(reply=text)
    except Exception as e:
        return ChatGraphResponse(reply=f"AI хариу үүсгэхэд алдаа гарлаа: {e}")

