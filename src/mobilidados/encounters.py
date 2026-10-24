"""Opposing-direction bus encounters predicted by the timetable.

Model (an estimate, not an observation): each vehicle runs the whole street at a constant speed ``v`` and is at
its reference stop ``s_ref`` at the scheduled time ``t``. A vehicle heading +1 is at ``s_ref + v (t' - t)``,
one heading -1 at ``s_ref - v (t' - t)``. Two vehicles in opposite directions meet if their presence
intervals on the street overlap; the meeting time and point follow from equal positions.
"""

from __future__ import annotations

import pandas as pd


def presence(t: float, s_ref: float, heading: int, length: float, v: float) -> tuple[float, float]:
    """Time interval during which the vehicle is on the street [0, length]."""
    if heading > 0:
        return t - s_ref / v, t + (length - s_ref) / v
    return t - (length - s_ref) / v, t + s_ref / v


def meeting(ta: float, sa: float, tb: float, sb: float, v: float) -> tuple[float, float]:
    """Meeting (time, s) of A (heading +1, at sa at ta) and B (heading -1, at sb at tb)."""
    t = (sb - sa + v * (ta + tb)) / (2 * v)
    return t, sa + v * (t - ta)


def hms(t: float) -> str:
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def encounters(passings: pd.DataFrame, length: float, speed_kmh: float) -> pd.DataFrame:
    """All predicted meetings between opposing vehicles on one service day."""
    v = speed_kmh / 3.6
    up = passings[passings.heading > 0]
    down = passings[passings.heading < 0]
    rows = []
    for a in up.itertuples():
        a0, a1 = presence(a.t, a.s_ref, 1, length, v)
        for b in down.itertuples():
            b0, b1 = presence(b.t, b.s_ref, -1, length, v)
            if a0 < b1 and b0 < a1:
                t, s = meeting(a.t, a.s_ref, b.t, b.s_ref, v)
                rows.append(
                    {
                        "speed_kmh": speed_kmh,
                        "time": hms(t),
                        "s_m": round(s, 1),
                        "up_route": a.route_short_name,
                        "up_time": a.arrival_time[:5],
                        "down_route": b.route_short_name,
                        "down_time": b.arrival_time[:5],
                        "pair": f"{a.route_short_name} x {b.route_short_name}",
                    }
                )
    cols = ["speed_kmh", "time", "s_m", "up_route", "up_time", "down_route", "down_time", "pair"]
    return pd.DataFrame(rows, columns=cols).sort_values("time").reset_index(drop=True)


def locate(enc: pd.DataFrame, narrow: list[tuple[float, float, str]]) -> pd.DataFrame:
    """Flag meetings that fall inside a narrow (two parking strips) section."""
    enc = enc.copy()

    def where(s: float) -> str:
        return next((b for a, z, b in narrow if a <= s <= z), "")

    enc["narrow_block"] = enc.s_m.map(where)
    enc["in_narrow_section"] = enc.narrow_block != ""
    return enc


def summary(passings: pd.DataFrame, length: float, speeds: list[float], basis: str = "assumed") -> pd.DataFrame:
    """Encounters per day at each speed. ``basis`` says where the speeds come from (assumed, or the schedule)."""
    rows = []
    for v in speeds:
        e = encounters(passings, length, v)
        hours = e.time.str[:2].value_counts() if len(e) else pd.Series(dtype=int)
        rows.append(
            {
                "basis": basis,
                "speed_kmh": v,
                "seconds_on_street": round(length / (v / 3.6)),
                "encounters_per_day": len(e),
                "max_per_hour": int(hours.max()) if len(hours) else 0,
                "hours_with_encounter": len(hours),
            }
        )
    return pd.DataFrame(rows)
