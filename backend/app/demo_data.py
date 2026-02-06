import numpy as np
from typing import Dict, List, Tuple


OUTPUT_KEYS = ["herd_total", "births", "losses", "sold_used", "herd_total_total"]


def demo_time_series(n: int = 25) -> List[float]:
    # Жишээ: 2000-2024
    start = 2000
    return [float(start + i) for i in range(n)]


def _smooth(base: np.ndarray, noise_scale: float = 0.03) -> np.ndarray:
    noise = np.random.default_rng(42).normal(0, noise_scale, size=base.shape)
    return base * (1 + noise)


def demo_baseline_and_sim(params: Dict[str, float], time: List[float]) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
    t = np.arange(len(time), dtype=float)

    # Параметрүүдийг demo логикт нөлөөлүүлж үзүүлнэ
    repro = float(params.get("repro_rate", 0.22))         # 0-1
    slaughter = float(params.get("slaughter_share", 0.12))# 0-1
    initial = float(params.get("initial_herd", 800000))   # head
    sold_share = float(params.get("sold_used_share", 0.08)) # 0-1
    disaster_impact = float(params.get("disaster_impact", 0.25)) # 0-1
    disaster_year = int(params.get("disaster_first_year", 2006))
    disaster_freq = int(params.get("disaster_freq", 5))

    # baseline
    herd_base = initial * (1 + 0.02 * t)  # өсөлт
    births_base = herd_base * (repro * 0.6)
    losses_base = herd_base * 0.05
    sold_base = herd_base * (sold_share + slaughter * 0.5)

    # simulation: disaster effect + params effect
    herd_sim = herd_base.copy()
    for i, year in enumerate(time):
        if int(year) >= disaster_year and disaster_freq > 0 and ((int(year) - disaster_year) % disaster_freq == 0):
            herd_sim[i:] = herd_sim[i:] * (1 - disaster_impact)

    # params effect
    herd_sim = herd_sim * (1 + (repro - 0.22) * 1.2) * (1 - (slaughter - 0.12) * 0.6)
    births_sim = herd_sim * (repro * 0.65)
    losses_sim = herd_sim * (0.05 + disaster_impact * 0.04)
    sold_sim = herd_sim * (sold_share + slaughter * 0.55)

    baseline = {
        "herd_total": _smooth(herd_base, 0.015).tolist(),
        "births": _smooth(births_base, 0.02).tolist(),
        "losses": _smooth(losses_base, 0.02).tolist(),
        "sold_used": _smooth(sold_base, 0.02).tolist(),
        "herd_total_total": _smooth(herd_base, 0.01).tolist(),
    }
    simulation = {
        "herd_total": _smooth(herd_sim, 0.015).tolist(),
        "births": _smooth(births_sim, 0.02).tolist(),
        "losses": _smooth(losses_sim, 0.02).tolist(),
        "sold_used": _smooth(sold_sim, 0.02).tolist(),
        "herd_total_total": _smooth(herd_sim, 0.01).tolist(),
    }
    return baseline, simulation


def demo_available_subscripts() -> Dict[str, list]:
    # Жишээ болгож “Сум”, “Малын төрөл” dimension өгнө
    dornod_soums = [
        "Хэрлэн",
        "Баяндун",
        "Баянтүмэн",
        "Баян Уул",
        "Булган",
        "Гурванзагал",
        "Дашбалбар",
        "Матад",
        "Сэргэлэн",
        "Халхгол",
        "Хөлөнбуйр",
        "Цагаан Овоо",
        "Чойбалсан",
        "Чулуунхороот",
    ]
    livestock_types = ["Адуу", "Үхэр", "Тэмээ", "Хонь", "Ямаа"]

    dims = [
        {"name": "Сум", "values": dornod_soums},
        {"name": "Малын төрөл", "values": livestock_types},
    ]
    out = {k: dims for k in OUTPUT_KEYS}
    out["herd_total_total"] = []
    return out
