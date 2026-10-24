"""Labels for figures and the findings ledger. Add a language by adding a column to ``T``."""

from __future__ import annotations

T = {
    "free_width": {"en": "Free width between parking strips", "pt": "Faixa livre entre as faixas de estacionamento"},
    "width_m": {"en": "width (m), to scale", "pt": "largura (m), à escala"},
    "limit": {"en": "limit", "pt": "limite"},
    "mirrors": {"en": "mirrors", "pt": "espelhos"},
    "does_not_fit": {"en": "does not fit", "pt": "não cabe"},
    "margin": {"en": "margin", "pt": "folga"},
    "with_mirrors": {"en": "with mirrors", "pt": "com espelhos"},
    "trips_per_hour": {"en": "trips per hour", "pt": "viagens por hora"},
    "hour": {"en": "hour of day", "pt": "hora do dia"},
    "weekday_trips": {"en": "Scheduled trips on the street, weekday {day}", "pt": "Viagens programadas na rua, dia útil {day}"},
    "along": {"en": "distance along the street (m)", "pt": "distância ao longo da rua (m)"},
    "strips": {"en": "Mapped parking strips (left / right)", "pt": "Faixas de estacionamento cartografadas (esq. / dir.)"},
    "profile_title": {"en": "Mapped cross-section along the street", "pt": "Perfil cartografado ao longo da rua"},
    "area_title": {
        "en": "Streets with buses in the area: free width vs. buses per day",
        "pt": "Ruas com autocarros na zona: faixa livre vs. autocarros por dia",
    },
    "buses_day": {"en": "buses per weekday", "pt": "autocarros por dia útil"},
    "median_free": {"en": "median free width (m)", "pt": "faixa livre mediana (m)"},
    "parking_both": {"en": "parking on both sides", "pt": "estacionamento dos dois lados"},
    "free_width_short": {"en": "Free width", "pt": "Faixa livre"},
    "data_credit": {"en": "Data: {sources}; adapted. Analysis: streetfit.", "pt": "Dados: {sources}; adaptados. Análise: streetfit."},
    "bus": {"en": "bus", "pt": "autocarro"},
    "car": {"en": "car", "pt": "ligeiro"},
    "pattern_two_way": {"en": "two-way, parking both sides, narrow", "pt": "dois sentidos, estacionamento dos dois lados, estreita"},
    "pattern_one_way": {"en": "one-way, parking both sides, narrow", "pt": "sentido único, estacionamento dos dois lados, estreita"},
}


def t(key: str, lang: str, **kw) -> str:
    entry = T[key]
    return entry.get(lang, entry["en"]).format(**kw)


def num(x: float, lang: str, d: int = 2, sign: bool = False) -> str:
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−") if lang == "pt" else s.replace("-", "−")
