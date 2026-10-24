"""Width budget: does the free width between parking strips hold two vehicles side by side?

A static envelope model, not a swept-path simulation: it compares the measured free width with the sum of
the vehicles' widths, assuming parked cars stay inside their mapped strips. Mirrors are counted unless a
vehicle's mirrors sit above the other vehicle's body (``mirrors_clear_cars``: a bus mirror passes over a car).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from importlib import resources

import pandas as pd


@dataclass(frozen=True)
class Vehicle:
    id: str
    label: str
    category: str  # "bus" | "car" | ...
    width_body_m: float
    width_mirrors_m: float
    grade_body: str  # evidence grades, see docs/evidence-standard.md
    grade_mirrors: str
    source_body: str
    source_mirrors: str
    mirrors_clear_cars: bool = False
    translations: dict = field(default_factory=dict)  # {"pt": {"label": ..., "source_body": ...}}


def load_vehicles(extra: dict | None = None) -> dict[str, Vehicle]:
    """The packaged vehicle catalogue, plus any vehicles defined in the case (``[vehicles.<id>]``)."""
    data = tomllib.loads(resources.files("streetfit.data").joinpath("vehicles.toml").read_text(encoding="utf-8"))
    data = {**data.get("vehicles", {}), **(extra or {})}
    out = {}
    for k, v in data.items():
        tr = {lang: v.pop(lang) for lang in [x for x in v if isinstance(v[x], dict)]}
        out[k] = Vehicle(id=k, translations=tr, **v)
    return out


def widths(a: Vehicle, b: Vehicle | None, with_mirrors: bool) -> float:
    def w(v: Vehicle, other: Vehicle | None) -> float:
        if not with_mirrors or (other is not None and v.mirrors_clear_cars and other.category == "car"):
            return v.width_body_m
        return v.width_mirrors_m

    return w(a, b) + (w(b, a) if b else 0.0)


def width_budget(free: dict[str, float], vehicles: dict[str, Vehicle], scenarios: list[list[str]]) -> pd.DataFrame:
    """Margin (free width minus vehicle widths) for each scenario, reference width and mirror assumption.

    ``scenarios``: lists of one or two vehicle ids, e.g. ``[["bus"], ["bus", "car"], ["bus", "bus"]]``.
    """
    rows = []
    for sc in scenarios:
        a, b = vehicles[sc[0]], (vehicles[sc[1]] if len(sc) > 1 else None)
        name = a.id if b is None else f"{a.id} x {b.id}"
        for ref, w in free.items():
            for mirrors in (False, True):
                need = widths(a, b, mirrors)
                rows.append(
                    {
                        "scenario": name,
                        "free_width_ref": ref,
                        "free_width_m": round(w, 2),
                        "mirrors": mirrors,
                        "vehicles_width_m": round(need, 2),
                        "margin_m": round(w - need, 2),
                    }
                )
    return pd.DataFrame(rows)


def overhang_sensitivity(
    free: float, vehicles: dict[str, Vehicle], scenarios: list[list[str]], overhangs=(0.0, 0.1, 0.2, 0.3)
) -> pd.DataFrame:
    """Margins (bodies only) if parked vehicles protrude ``p`` metres beyond each strip."""
    rows = []
    for p in overhangs:
        for sc in scenarios:
            if len(sc) < 2:
                continue
            a, b = vehicles[sc[0]], vehicles[sc[1]]
            rows.append(
                {
                    "overhang_per_side_m": p,
                    "scenario": f"{a.id} x {b.id}",
                    "free_width_m": round(free - 2 * p, 2),
                    "margin_body_m": round(free - 2 * p - widths(a, b, False), 2),
                }
            )
    return pd.DataFrame(rows)
