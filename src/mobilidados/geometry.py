"""Cross-section profiles of a street, measured only from mapped polygons.

For each station ``s`` along the street axis a transect is drawn perpendicular to the axis, and the widths of
the mapped road surface, parking strips, sidewalks and the distance to the plot boundary are read from where
the transect crosses the cartography polygons. Nothing here infers where vehicles actually are: a parking
strip is mapped area, not a parked car.

Offsets are measured along the left-hand normal of the axis: positive = left of the direction of increasing s.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd
from shapely import STRtree
from shapely.geometry import LineString, MultiLineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge

from .arcgis import to_line, to_polygon
from .config import Block, MobilidadosError


def street_axis(features: Iterable[dict], name_field: str, name: str) -> LineString:
    """The axis polyline of a named street. A street stored as several features or parts is joined when the pieces
    form one continuous line; a street that branches or has gaps is an error."""
    found = [f for f in features if f["attributes"].get(name_field) == name]
    if not found:
        raise MobilidadosError(f"no axis named {name!r} in field {name_field}")
    lines = [to_line(f["geometry"]) for f in found]
    parts = [p for g in lines for p in (g.geoms if isinstance(g, MultiLineString) else [g])]
    line = parts[0] if len(parts) == 1 else linemerge(MultiLineString(parts))
    if not isinstance(line, LineString):
        raise MobilidadosError(
            f"the axis of {name!r} is not one continuous line (it branches or has gaps); split the case into one case per part"
        )
    return line


def classed_polygons(features: Iterable[dict], class_field: str, keep: set[str]) -> list[tuple[str, BaseGeometry]]:
    out = []
    for f in features:
        cls = f["attributes"].get(class_field)
        if cls in keep and f.get("geometry"):
            out.append((cls, to_polygon(f["geometry"])))
    return out


def _tangent(axis: LineString, s: float, eps: float = 0.5) -> tuple[float, float]:
    a, b = axis.interpolate(max(s - eps, 0)), axis.interpolate(min(s + eps, axis.length))
    dx, dy = b.x - a.x, b.y - a.y
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def _merge(iv: list[tuple[float, float]], tol: float = 0.15) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1] + tol:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


class Profiler:
    """Measures transects against a set of classed polygons (spatially indexed)."""

    def __init__(self, polygons: list[tuple[str, BaseGeometry]]):
        self.polys = polygons
        self.tree = STRtree([g for _, g in polygons])

    def intervals(
        self, transect: LineString, cx: float, cy: float, nrm: tuple[float, float], classes: set[str]
    ) -> list[tuple[float, float]]:
        out = []
        for i in self.tree.query(transect):
            cls, g = self.polys[i]
            if cls not in classes:
                continue
            ip = transect.intersection(g)
            if ip.is_empty:
                continue
            for seg in getattr(ip, "geoms", [ip]):
                if seg.geom_type != "LineString":
                    continue
                o = [(q[0] - cx) * nrm[0] + (q[1] - cy) * nrm[1] for q in seg.coords]
                out.append((min(o), max(o)))
        return _merge(out)


def measure_profiles(
    axis: LineString,
    polygons: list[tuple[str, BaseGeometry]],
    classes: dict[str, set[str]],
    step: float = 0.5,
    half_width: float = 25.0,
    snap: float = 0.35,
    axis_tol: float = 0.05,
) -> pd.DataFrame:
    """One row per station: free carriageway between parking strips, strips, kerb-to-kerb, sidewalks, plots.

    ``classes`` maps the roles ``road``, ``parking``, ``sidewalk`` and ``plot`` to cartography class codes.
    Columns ending in ``_L`` are on the left of the direction of increasing s, ``_R`` on the right.
    ``snap`` is how far apart (m) two mapped edges may be and still count as touching; ``axis_tol`` is how far
    outside a road interval (m) the axis may lie and still count as on it.
    """
    prof = Profiler(polygons)
    rows = []
    for s in np.arange(0.0, axis.length + 1e-6, step):
        c = axis.interpolate(s)
        tx, ty = _tangent(axis, s)
        nrm = (-ty, tx)
        transect = LineString(
            [(c.x - nrm[0] * half_width, c.y - nrm[1] * half_width), (c.x + nrm[0] * half_width, c.y + nrm[1] * half_width)]
        )
        road = [iv for iv in prof.intervals(transect, c.x, c.y, nrm, classes["road"]) if iv[0] - axis_tol <= 0 <= iv[1] + axis_tol]
        park = prof.intervals(transect, c.x, c.y, nrm, classes["parking"])
        side = prof.intervals(transect, c.x, c.y, nrm, classes["sidewalk"])
        plot = prof.intervals(transect, c.x, c.y, nrm, classes["plot"])
        r: dict = {"s": round(float(s), 3), "x": round(c.x, 2), "y": round(c.y, 2)}
        if not road:
            r["note"] = "axis outside the mapped road polygon"
            rows.append(r)
            continue
        ra, rb = road[0]
        r["free_width"] = round(rb - ra, 2)
        r["road_off_R"], r["road_off_L"] = round(ra, 2), round(rb, 2)
        sl = [iv for iv in park if abs(iv[0] - rb) < snap]
        sr = [iv for iv in park if abs(iv[1] - ra) < snap]
        r["strip_L"] = round(sl[0][1] - sl[0][0], 2) if sl else 0.0
        r["strip_R"] = round(sr[0][1] - sr[0][0], 2) if sr else 0.0
        outer_L = sl[0][1] if sl else rb
        outer_R = sr[0][0] if sr else ra
        r["kerb_to_kerb"] = round(outer_L - outer_R, 2)
        pl = [iv for iv in side if abs(iv[0] - outer_L) < snap]
        pr = [iv for iv in side if abs(iv[1] - outer_R) < snap]
        r["sidewalk_L"] = round(pl[0][1] - pl[0][0], 2) if pl else None
        r["sidewalk_R"] = round(pr[0][1] - pr[0][0], 2) if pr else None
        tl = [iv for iv in plot if iv[0] >= outer_L - snap]
        tr = [iv for iv in plot if iv[1] <= outer_R + snap]
        r["to_plot_L"] = round(min(iv[0] for iv in tl) - outer_L, 2) if tl else None
        r["to_plot_R"] = round(outer_R - max(iv[1] for iv in tr), 2) if tr else None
        rows.append(r)
    return pd.DataFrame(rows)


TWO_STRIPS, ONE_STRIP, OTHER = "two_strips", "one_strip", "other"
MIN_STRIP_M = 0.5  # a mapped parking strip narrower than this at a station does not count as parking there


def classify(
    df: pd.DataFrame, blocks: list[Block], narrow_max: float = 7.0, one_strip_max: float = 12.5, min_strip: float = MIN_STRIP_M
) -> pd.DataFrame:
    """Label stations: ``two_strips`` = parking mapped on both sides with a narrow free width between them."""
    df = df.copy()
    edges = [-1.0] + [b.end for b in blocks[:-1]] + [1e9]
    df["block"] = pd.cut(df.s, edges, labels=[b.id for b in blocks]).astype(str) if blocks else ""
    left, right = df.strip_L > min_strip, df.strip_R > min_strip
    df["class"] = np.where((df.free_width <= narrow_max) & left & right, TWO_STRIPS, OTHER)
    df.loc[(df["class"] == OTHER) & (left ^ right) & (df.free_width <= one_strip_max), "class"] = ONE_STRIP
    return df


SUMMARY_COLUMNS = ["block", "n_stations", "s_min", "s_max", "free_min", "free_p5", "free_median", "free_p95", "free_max",
                   "strip_L_median", "strip_R_median", "kerb_to_kerb_min", "kerb_to_kerb_median", "kerb_to_kerb_max",
                   "to_plot_L_median", "to_plot_R_median"]  # fmt: skip


def summarize_blocks(df: pd.DataFrame, blocks: list[Block]) -> pd.DataFrame:
    """Quantiles of the two-strip stations per block and overall (the headline measurement table). A street without
    two-strip stations gets the header only, with no ``all`` row."""
    d = df[df["class"] == TWO_STRIPS]
    rows = []
    for label, sub in [(b.id, d[d.block == b.id]) for b in blocks] + [("all", d)]:
        if sub.empty:
            continue
        q = sub.free_width.astype(float).quantile([0, 0.05, 0.5, 0.95, 1]).round(2).tolist()
        rows.append(
            {
                "block": label,
                "n_stations": len(sub),
                "s_min": sub.s.min(),
                "s_max": sub.s.max(),
                "free_min": q[0],
                "free_p5": q[1],
                "free_median": q[2],
                "free_p95": q[3],
                "free_max": q[4],
                "strip_L_median": round(sub.strip_L.median(), 2),
                "strip_R_median": round(sub.strip_R.median(), 2),
                "kerb_to_kerb_min": round(sub.kerb_to_kerb.min(), 2),
                "kerb_to_kerb_median": round(sub.kerb_to_kerb.median(), 2),
                "kerb_to_kerb_max": round(sub.kerb_to_kerb.max(), 2),
                "to_plot_L_median": round(sub.to_plot_L.median(), 2),
                "to_plot_R_median": round(sub.to_plot_R.median(), 2),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def narrow_sections(df: pd.DataFrame, step: float) -> list[tuple[float, float, str]]:
    """Contiguous runs of two-strip stations as (s_from, s_to, block)."""
    d = df[df["class"] == TWO_STRIPS].sort_values("s")
    runs: list[list] = []
    for s, b in zip(d.s, d.block, strict=True):
        if runs and abs(s - runs[-1][1] - step) < step / 2 and runs[-1][2] == b:
            runs[-1][1] = s
        else:
            runs.append([s, s, b])
    return [(a, z, b) for a, z, b in runs]


def strip_lengths(
    df: pd.DataFrame, blocks: list[Block], step: float, stall_lengths: tuple[float, ...], min_strip: float = MIN_STRIP_M
) -> pd.DataFrame:
    """Mapped parking-strip length per side and block, and the stall count it implies for given stall lengths
    (``profiles.parking_space_m``)."""
    rows = []
    for label, sub in [(b.id, df[df.block == b.id]) for b in blocks] + [("all", df)]:
        r = {
            "block": label,
            "strip_L_length_m": round((sub.strip_L > min_strip).sum() * step, 1),
            "strip_R_length_m": round((sub.strip_R > min_strip).sum() * step, 1),
        }
        for L in stall_lengths:
            r[f"stalls_L_{L:g}m"] = round(r["strip_L_length_m"] / L, 1)
            r[f"stalls_R_{L:g}m"] = round(r["strip_R_length_m"] / L, 1)
        rows.append(r)
    return pd.DataFrame(rows)
