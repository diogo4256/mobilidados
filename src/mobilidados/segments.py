"""The [delay] comparison made again on a third party's speeds per segment (``[segment_check]``).

**Data.** Two answers of an API that publishes, for each route shape cut into short segments, the metres and the
seconds that the recorded passages of its vehicles add up to on each segment, over a period and a range of hours,
with the number of samples behind them: ``peak.json`` and ``off_peak.json``, asked for the hours of ``[delay]``
(moverlisboa.com's ``/api/carris/transit-stats``). The publisher computes them from the operator's real-time feed with
a method it does not document, and a collector of its own, not the archive ``[delay]`` reads.

**Comparison.** A segment is placed along its route's shape in the GTFS feed (the same ``shape_id``) by its end
points, and left out if they lie farther than ``max_offset_m`` from it. It belongs to the stretch, or to a control
stretch, when its midpoint lies there (the stretch and controls of ``[delay]``), and counts only if it has records
in both periods. The time a bus takes per metre on a set of segments is Σ (seconds / metres × length) / Σ length,
and as in ``[delay]``:

    ratio = (stretch peak / stretch off-peak) / (controls peak / controls off-peak)

with the seconds per passage scaled to the stretch's length. A route and direction is compared only when the
segments with records in both periods cover ``min_coverage`` of the stretch and of the controls, with at least
``min_samples`` samples in each period.

**What it is not.** It gives no interval: the publisher's sums do not show the passages behind them. Segments do
not end where the stretch does: the stretch's segments can reach past it (``s_first``, ``s_last``), onto a stop.
And the period and its days are the publisher's (``period_first``, ``period_last``), not those of ``[delay]``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import LineString

from .config import Delay, MobilidadosError, SegmentCheck
from .delay import CONTROL, OFF, PEAK, STRETCH, Route

FIELDS = (
    "segment_id",
    "shape_id",
    "seq",
    "seconds",
    "meters",
    "samples",
    "lat1",
    "lon1",
    "lat2",
    "lon2",
    "length_m",
    "period_start",
    "period_end",
)
COLUMNS = [
    "route_direction", "shape_id", "segments_stretch", "segments_controls", "s_first", "s_last", "coverage_stretch",
    "coverage_controls", "samples_stretch_peak", "samples_stretch_off_peak", "samples_controls_peak",
    "samples_controls_off_peak", "compared", "off_peak_s", "peak_s", "expected_peak_s", "excess_s", "ratio",
]  # fmt: skip


def load(path: Path) -> pd.DataFrame:
    """The segments of one answer, with the fields the comparison reads."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise MobilidadosError(f"{path}: expected a list of segments, got {type(data).__name__}")
    df = pd.DataFrame(data)
    missing = sorted(set(FIELDS) - set(df.columns)) if len(df) else []
    if missing:
        raise MobilidadosError(f"{path}: the segments have no {missing}")
    return df.reindex(columns=list(FIELDS)).astype({"shape_id": str})


def hours_asked(url: str) -> list[int] | None:
    """The clock hours an answer covers, from ``hour_start`` and ``hour_end`` (both included) in its URL."""
    q = parse_qs(urlparse(url).query)
    if "hour_start" not in q or "hour_end" not in q:
        return None
    return list(range(int(q["hour_start"][0]), int(q["hour_end"][0]) + 1))


def check_hours(urls: dict[str, str], cfg: Delay) -> None:
    """The answers must be for the [delay] peak and off-peak hours, or the comparison is not the same."""
    for name, want in ((f"{PEAK}.json", cfg.peak_hours), (f"{OFF}.json", cfg.off_peak_hours)):
        got = hours_asked(urls[name])
        if got != sorted(want):
            raise MobilidadosError(
                f"segment_check: {name} is asked for hours {got} ({urls[name]}), but [delay] uses {sorted(want)}; "
                "ask the service for hour_start and hour_end of the [delay] hours"
            )


def place(seg: pd.DataFrame, r: Route, crs: int, max_offset_m: float) -> pd.DataFrame:
    """The segments of ``r``'s shape near it, each with where its midpoint lies: stretch, control or neither."""
    g = seg[seg.shape_id == r.shape_id]
    if g.empty:
        return g.assign(where=pd.Series(dtype=str))
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    x1, y1 = tr.transform(g.lon1.to_numpy(float), g.lat1.to_numpy(float))
    x2, y2 = tr.transform(g.lon2.to_numpy(float), g.lat2.to_numpy(float))
    p1, p2 = shapely.points(x1, y1), shapely.points(x2, y2)
    m = (shapely.line_locate_point(r.line, p1) + shapely.line_locate_point(r.line, p2)) / 2
    near = np.maximum(shapely.distance(r.line, p1), shapely.distance(r.line, p2)) <= max_offset_m
    where = np.full(len(g), "", dtype=object)
    where[(m >= r.stretch[0]) & (m <= r.stretch[1])] = STRETCH
    for a, b in r.controls:
        where[(m >= a) & (m <= b)] = CONTROL
    return g.assign(m=m, where=where, x1=x1, y1=y1, x2=x2, y2=y2)[near & (where != "")]


def _time_per_m(g: pd.DataFrame) -> float:
    return float((g.seconds / g.meters * g.length_m).sum() / g.length_m.sum())


def compare(
    peak: pd.DataFrame, off: pd.DataFrame, rts: list[Route], crs: int, axis: LineString, dl: Delay, sc: SegmentCheck
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """One row per route and direction: the segments used, their coverage and samples, and the [delay] estimates."""
    rows = []
    for r in rts:
        a, b = place(peak, r, crs, dl.max_offset_m), place(off, r, crs, dl.max_offset_m)
        both = sorted(set(a.segment_id) & set(b.segment_id))
        a, b = a[a.segment_id.isin(both)].set_index("segment_id"), b[b.segment_id.isin(both)].set_index("segment_id")
        st, ct = a[a["where"] == STRETCH], a[a["where"] == CONTROL]
        stretch_m, controls_m = r.stretch[1] - r.stretch[0], sum(z - y for y, z in r.controls)
        on_axis = [axis.project(shapely.Point(x, y)) for x, y in zip([*st.x1, *st.x2], [*st.y1, *st.y2], strict=True)]
        row: dict[str, Any] = {
            "route_direction": r.label,
            "shape_id": r.shape_id,
            "segments_stretch": len(st),
            "segments_controls": len(ct),
            "s_first": round(min(on_axis), 1) if on_axis else np.nan,
            "s_last": round(max(on_axis), 1) if on_axis else np.nan,
            "coverage_stretch": round(float(st.length_m.sum()) / stretch_m, 3),
            "coverage_controls": round(float(ct.length_m.sum()) / controls_m, 3),
        }
        for name, tab in ((PEAK, a), (OFF, b)):
            row[f"samples_stretch_{name}"] = int(tab.loc[st.index, "samples"].sum())
            row[f"samples_controls_{name}"] = int(tab.loc[ct.index, "samples"].sum())
        row["compared"] = bool(
            min(row["coverage_stretch"], row["coverage_controls"]) >= sc.min_coverage
            and min(row[f"samples_{w}_{p}"] for w in ("stretch", "controls") for p in (PEAK, OFF)) >= sc.min_samples
        )
        if row["compared"]:
            sp, so = _time_per_m(a.loc[st.index]), _time_per_m(b.loc[st.index])
            cp, co = _time_per_m(a.loc[ct.index]), _time_per_m(b.loc[ct.index])
            expected = so * cp / co * stretch_m
            row |= {
                "off_peak_s": round(so * stretch_m, 1),
                "peak_s": round(sp * stretch_m, 1),
                "expected_peak_s": round(expected, 1),
                "excess_s": round(sp * stretch_m - expected, 1),
                "ratio": round(sp * stretch_m / expected, 3),
            }
        rows.append(row)
    periods = pd.concat([peak.period_start, peak.period_end, off.period_start, off.period_end]).astype(str).str[:10]
    data = {"period_first": periods.min(), "period_last": periods.max(), "segments_peak": len(peak), "segments_off_peak": len(off)}
    return pd.DataFrame(rows).reindex(columns=COLUMNS), data
