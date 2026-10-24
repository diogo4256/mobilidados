"""Width budget: does the free width between parking strips hold two vehicles side by side?

A static envelope model, not a swept-path simulation: it compares the measured free width with the sum of
the vehicles' widths, assuming parked cars stay inside their mapped strips. Mirrors are counted unless a
vehicle's mirrors sit above the other vehicle's body (``mirrors_clear_cars``: a bus mirror passes over a car).
The vehicles come from ``data/vehicles.toml`` and the case's own ``[vehicles.<id>]`` (see ``Config.all_vehicles``).
"""

from __future__ import annotations

import pandas as pd

from .config import Vehicle


def widths(a: Vehicle, b: Vehicle | None, with_mirrors: bool) -> float:
    def w(v: Vehicle, other: Vehicle | None) -> float:
        if not with_mirrors or (other is not None and v.mirrors_clear_cars and other.category == "car"):
            return v.width_body_m
        return v.width_mirrors_m

    return w(a, b) + (w(b, a) if b else 0.0)


def _pair(vehicles: dict[str, Vehicle], scenario: list[str]) -> tuple[Vehicle, Vehicle | None, str]:
    a, b = vehicles[scenario[0]], (vehicles[scenario[1]] if len(scenario) > 1 else None)
    return a, b, " x ".join(scenario)


def width_budget(free: dict[str, float], vehicles: dict[str, Vehicle], scenarios: list[list[str]]) -> pd.DataFrame:
    """Margin (free width minus vehicle widths) for each scenario, reference width and mirror assumption.

    ``scenarios``: lists of one or two vehicle ids, e.g. ``[["bus"], ["bus", "car"], ["bus", "bus"]]``.
    """
    rows = []
    for sc in scenarios:
        a, b, name = _pair(vehicles, sc)
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
    free: float, vehicles: dict[str, Vehicle], scenarios: list[list[str]], overhangs: tuple[float, ...] = (0.0, 0.1, 0.2, 0.3)
) -> pd.DataFrame:
    """Margins (bodies only) if parked vehicles protrude ``p`` metres beyond each strip."""
    rows = []
    for p in overhangs:
        for sc in scenarios:
            a, b, name = _pair(vehicles, sc)
            if b is None:
                continue
            rows.append(
                {
                    "overhang_per_side_m": p,
                    "scenario": name,
                    "free_width_m": round(free - 2 * p, 2),
                    "margin_body_m": round(free - 2 * p - widths(a, b, False), 2),
                }
            )
    return pd.DataFrame(rows)
