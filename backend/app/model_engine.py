from typing import Dict, List, Tuple, Any
import pandas as pd

from .config import settings
from .utils import file_exists
from .demo_data import demo_time_series, demo_baseline_and_sim, demo_available_subscripts

try:
    import pysd
except Exception:
    pysd = None


TOTAL_HERD_KEY = "herd_total_total"
OUTPUT_KEYS = ["herd_total", "births", "losses", "sold_used", TOTAL_HERD_KEY]

# UI нэр (output_key) → Vensim variable нэр (солих боломжтой)
VARIABLE_MAP_DEFAULT: Dict[str, str] = {
    "herd_total": "Бэлчээрийн малын тоо толгой",
    "births": "Бэлчээрийн мал сүргийн төллөлт",
    "losses": "Малын зүй бус хорогдол",
    "sold_used": "Борлуулсан болон хүнсэнд хэрэглэсэн малын тоо толгой",
    TOTAL_HERD_KEY: "Бэлчээрийн малын тоо толгой",
}

# Slider key → Vensim parameter нэр (солих боломжтой)
PARAM_MAP_DEFAULT: Dict[str, str] = {
    "repro_rate": "Бэлчээрийн малын нөхөн үржих хувь хэмжээ",
    "slaughter_share": "Хэрэгцээнд нядалсан малын эзлэх хувь",
    "initial_herd": "Бэлчээрийн малын анхны тоо толгой",
    "sold_used_share": "Борлуулсан болон хүнсэнд хэрэглэсэн малын хувь хэмжээ",
    "disaster_impact": "Байгалийн гамшгийн бэлчээрийн мал сүргийн нөхөн төлжих нөлөө",
    "disaster_first_year": "Байгалийн гамшиг тохиолдсон анхны жил",
    "disaster_freq": "Байгалийн гамшгийн давтамж",
}


class ModelEngine:
    def __init__(self):
        self.demo_mode: bool = True
        self.model: Any = None
        self.time_unit_label: str = "TIME"
        self.variable_map = dict(VARIABLE_MAP_DEFAULT)
        self.param_map = dict(PARAM_MAP_DEFAULT)

        self._baseline_df: pd.DataFrame | None = None
        self._baseline_time: List[float] = []
        self._available_subscripts: Dict[str, List[Dict[str, Any]]] = {}

    def load(self) -> None:
        # Auto demo if no pysd or file missing
        if pysd is None:
            self.demo_mode = True
            self._prime_demo()
            return

        if not file_exists(settings.MODEL_PATH):
            # demo fallback
            self.demo_mode = True
            self._prime_demo()
            return

        try:
            self.model = pysd.read_vensim(settings.MODEL_PATH)
            # time unit label (best-effort)
            time_obj = getattr(self.model, "time", None)
            units = getattr(time_obj, "units", None)
            self.time_unit_label = str(units) if units is not None else "TIME"

            # baseline run
            self._baseline_df = self.model.run()
            if self._baseline_df is None:
                raise RuntimeError("Model run returned None")
            self._baseline_time = self._extract_time(self._baseline_df)
            self.demo_mode = False

            # subscripts detect using get_coords (PySD docs) :contentReference[oaicite:7]{index=7}
            self._available_subscripts = self._detect_subscripts()

        except Exception:
            # Any model translation/run crash -> demo
            self.demo_mode = True
            self._prime_demo()

    def _prime_demo(self):
        t = demo_time_series()
        b, s = demo_baseline_and_sim({}, t)
        # baseline_df-г demo дээр хиймлээр бүтээнэ
        self._baseline_time = t
        self._baseline_df = self._to_df(t, b)
        self._available_subscripts = demo_available_subscripts()
        self.time_unit_label = "жил"

    def _to_df(self, time: List[float], series_by_key: Dict[str, List[float]]) -> pd.DataFrame:
        df = pd.DataFrame({"TIME": time})
        for k, arr in series_by_key.items():
            df[k] = arr
        df = df.set_index("TIME")
        return df

    def _extract_time(self, df: pd.DataFrame | None) -> List[float]:
        if df is None:
            return []
        try:
            return [float(x) for x in df.index.values.tolist()]
        except Exception:
            return []

    def _detect_subscripts(self) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = {}
        if self.demo_mode or self.model is None:
            return demo_available_subscripts()

        for out_key, vensim_name in self.variable_map.items():
            if out_key == TOTAL_HERD_KEY:
                out[out_key] = []
                continue
            dims_list: List[Dict[str, Any]] = []
            try:
                coords_raw = self.model.get_coords(vensim_name)  # returns dict dim->values :contentReference[oaicite:8]{index=8}
                coords: Dict[str, Any] = {}
                if isinstance(coords_raw, dict):
                    coords = coords_raw
                elif isinstance(coords_raw, tuple) and coords_raw:
                    first = coords_raw[0]
                    if isinstance(first, dict):
                        coords = first
                # coords might be {} for scalar
                for dim_name, values in coords.items():
                    # values can be list/Index
                    dims_list.append({"name": str(dim_name), "values": [str(v) for v in list(values)]})
            except Exception:
                dims_list = []
            out[out_key] = dims_list
        # If all outputs are scalar (no subscripts), provide demo subscripts for UI selection.
        if all(len(v) == 0 for v in out.values()):
            return demo_available_subscripts()
        return out

    def get_available_subscripts(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._available_subscripts

    def get_time_unit_label(self) -> str:
        return self.time_unit_label

    def get_baseline_filtered(self, subscripts: Dict[str, Dict[str, str]]) -> Tuple[List[float], Dict[str, List[float]]]:
        if self._baseline_df is None:
            self._prime_demo()

        time = self._baseline_time
        baseline: Dict[str, List[float]] = {}
        for k in OUTPUT_KEYS:
            if k == TOTAL_HERD_KEY:
                baseline[k] = self._extract_total_series(self.variable_map.get(k, k), self._baseline_df)
            else:
                baseline[k] = self._extract_series(k, self.variable_map.get(k, k), self._baseline_df, subscripts.get(k, {}))
        return time, baseline

    def simulate(self, params: Dict[str, float], subscripts: Dict[str, Dict[str, str]]) -> Tuple[List[float], Dict[str, List[float]], Dict[str, List[float]]]:
        # baseline
        time, baseline = self.get_baseline_filtered(subscripts)

        # simulation
        if self.demo_mode or self.model is None or pysd is None:
            b2, s2 = demo_baseline_and_sim(params, time)
            sim = {}
            for k in OUTPUT_KEYS:
                sim[k] = s2.get(k, [])
            return time, baseline, sim

        # Map slider keys -> vensim param names
        overrides = {}
        for slider_key, val in params.items():
            vname = self.param_map.get(slider_key, slider_key)
            overrides[vname] = val

        # IMPORTANT: PySD params override via run(params=...) :contentReference[oaicite:9]{index=9}
        df_sim = self.model.run(params=overrides)

        sim: Dict[str, List[float]] = {}
        for k in OUTPUT_KEYS:
            if k == TOTAL_HERD_KEY:
                sim[k] = self._extract_total_series(self.variable_map.get(k, k), df_sim)
            else:
                sim[k] = self._extract_series(k, self.variable_map.get(k, k), df_sim, subscripts.get(k, {}))
        return time, baseline, sim

    def _extract_total_series(self, vensim_var: str, df: pd.DataFrame | None) -> List[float]:
        if df is None:
            return []
        if vensim_var in df.columns:
            return [float(x) for x in df[vensim_var].values.tolist()]
        candidates = [c for c in df.columns if str(c).startswith(f"{vensim_var}[")]
        if candidates:
            totals = df[candidates].sum(axis=1)
            return [float(x) for x in totals.values.tolist()]
        return [0.0 for _ in range(len(df.index))]

    def _extract_series(self, out_key: str, vensim_var: str, df: pd.DataFrame | None, subsel: Dict[str, str]) -> List[float]:
        """
        PySD output columns ихэвчлэн:
        - scalar: "Var"
        - subscript: "Var[Dim1,Dim2]" маягийн хэлбэртэй байх нь түгээмэл.
        Энэ функц нь хамгийн боломжит байдлаар сонгосон subscript-д таарсан series-ийг олно.
        Олдохгүй бол scalar fallback.
        """
        if df is None:
            return []
        # 1) direct column
        if vensim_var in df.columns:
            return [float(x) for x in df[vensim_var].values.tolist()]

        # 2) try bracket matching
        candidates = [c for c in df.columns if str(c).startswith(f"{vensim_var}[")]
        if not candidates:
            # demo key fallback (demo үед df дээр out_key нэртэй байж болно)
            if out_key in df.columns:
                return [float(x) for x in df[out_key].values.tolist()]
            return [0.0 for _ in range(len(df.index))]

        # ensure deterministic ordering across runs
        candidates = sorted(candidates, key=lambda c: str(c))

        if not subsel:
            # no selection -> first candidate
            col = candidates[0]
            return [float(x) for x in df[col].values.tolist()]

        # subsel dict: dim->value, but column string contains only values order.
        # We'll match values existence in bracket part.
        def score(colname: str) -> int:
            inside = colname.split("[", 1)[1].rstrip("]")
            parts = [p.strip() for p in inside.split(",")]
            s = 0
            for _, v in subsel.items():
                if str(v) in parts:
                    s += 1
            return s

        best = max(candidates, key=lambda c: (score(c), str(c)))
        return [float(x) for x in df[best].values.tolist()]

    def applied_subscripts_per_output(self, subscripts: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        applied = {}
        for k in OUTPUT_KEYS:
            applied[k] = {} if k == TOTAL_HERD_KEY else subscripts.get(k, {})
        return applied
