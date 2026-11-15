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
from shapely import STRtree, make_valid
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
            g = to_polygon(f["geometry"])
            out.append((cls, g if g.is_valid else make_valid(g)))  # a self-touching ring would stop GEOS mid-run
    return out


def drop_slivers(polygons: list[tuple[str, BaseGeometry]], classes: set[str], min_thickness: float) -> list[tuple[str, BaseGeometry]]:
    """The polygons without those of ``classes`` thinner on average (twice the area over the perimeter, the width of a
    long strip) than ``min_thickness``: slivers left where polygons meet, which a transect crossing them at a slant
    would read as a narrow sidewalk."""
    return [(c, g) for c, g in polygons if c not in classes or 2 * g.area / max(g.length, 1e-9) >= min_thickness]


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
    profiler: Profiler | None = None,
) -> pd.DataFrame:
    """One row per station: free carriageway between parking strips, strips, kerb-to-kerb, sidewalks, plots.

    ``sidewalk_*`` is the mapped sidewalk touching the kerb; ``walk_*`` the widest piece of mapped sidewalk between
    the kerb and the plots, the width the ``sidewalks`` stage compares with the free path a pedestrian needs.

    ``classes`` maps the roles ``road``, ``parking``, ``sidewalk`` and ``plot`` to cartography class codes, and
    optionally ``overhead``: plot classes drawn at roof level (arcades, balconies), under which the ground may be open,
    and ``yard``: plot classes of open ground, which do not bound a sidewalk as a building does.
    Columns ending in ``_L`` are on the left of the direction of increasing s, ``_R`` on the right.
    ``snap`` is how far apart (m) two mapped edges may be and still count as touching; ``axis_tol`` is how far
    outside a road interval (m) the axis may lie and still count as on it. ``profiler`` reuses an index already built
    over many polygons (the area scan measures every street against one), instead of ``polygons``.
    """
    prof = profiler or Profiler(polygons)
    rows = []
    for s in np.arange(0.0, axis.length + 1e-6, step):
        c = axis.interpolate(s)
        tx, ty = _tangent(axis, s)
        nrm = (-ty, tx)
        transect = LineString(
            [(c.x - nrm[0] * half_width, c.y - nrm[1] * half_width), (c.x + nrm[0] * half_width, c.y + nrm[1] * half_width)]
        )
        all_road = prof.intervals(transect, c.x, c.y, nrm, classes["road"])
        road = [iv for iv in all_road if iv[0] - axis_tol <= 0 <= iv[1] + axis_tol]
        park = prof.intervals(transect, c.x, c.y, nrm, classes["parking"])
        side = prof.intervals(transect, c.x, c.y, nrm, classes["sidewalk"])
        plot = prof.intervals(transect, c.x, c.y, nrm, classes["plot"])
        overhead = prof.intervals(transect, c.x, c.y, nrm, classes["overhead"]) if classes.get("overhead") else []
        yards = prof.intervals(transect, c.x, c.y, nrm, classes["yard"]) if classes.get("yard") else []
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
        # the widest piece of mapped sidewalk between the kerb and the plots (or the end of the transect): a sidewalk cut
        # by a tree pit, a kiosk or a shelter mapped as another class is walked on its widest piece, not the one at the kerb.
        # A side where another carriageway comes before any plot is a median or an island, not a sidewalk: not measured.
        # Pieces thinner than MIN_WALK_PIECE_M are slivers left where polygons meet, not something one walks on.
        lanes = [iv for iv in all_road if iv not in road]
        edge_L = min((iv[0] for iv in tl), default=half_width)
        edge_R = max((iv[1] for iv in tr), default=-half_width)
        # the same if what bounds the sidewalk is a plot with a carriageway just behind it: an island, not a building line
        back_L = next((b for a, b in plot if a - snap <= edge_L <= b), edge_L)
        back_R = next((a for a, b in plot if a <= edge_R <= b + snap), edge_R)
        island_L = any(outer_L + snap < a < edge_L or back_L <= a <= back_L + ISLAND_BACK_M for a, _ in lanes)
        island_R = any(edge_R < b < outer_R - snap or back_R - ISLAND_BACK_M <= b <= back_R for _, b in lanes)
        # a plot drawn at roof level (an arcade, a balcony, a canopy) hides the ground under it, which may be walked on:
        # a sidewalk ending at one has an unknown width
        under_L = any(a - snap <= edge_L <= b + snap for a, b in overhead) if tl else False
        under_R = any(a - snap <= edge_R <= b + snap for a, b in overhead) if tr else False
        # ``walk_*_bounded``: the piece runs up to the plots, so nothing beyond it can be walked on; where it does not, what
        # lies beyond (a lawn, a square, a wall) is not in the cartography classes read, and the path may continue there
        wl = [(a, b) for a, b in side if a >= outer_L - snap and b <= edge_L + snap and b - a >= MIN_WALK_PIECE_M]
        wr = [(a, b) for a, b in side if b <= outer_R + snap and a >= edge_R - snap and b - a >= MIN_WALK_PIECE_M]
        best_L = max(wl, key=lambda iv: iv[1] - iv[0]) if wl and not (island_L or under_L) else None
        best_R = max(wr, key=lambda iv: iv[1] - iv[0]) if wr and not (island_R or under_R) else None
        r["walk_L"] = round(best_L[1] - best_L[0], 2) if best_L else None
        r["walk_R"] = round(best_R[1] - best_R[0], 2) if best_R else None
        # a yard (open ground inside a plot) does not bound a sidewalk as a building does: it may be a forecourt or a
        # planted island one can step onto
        yard_L = any(abs(a - edge_L) < snap for a, _ in yards)
        yard_R = any(abs(b - edge_R) < snap for _, b in yards)
        r["walk_L_bounded"] = bool(tl) and not yard_L and abs(best_L[1] - edge_L) < snap if best_L else None
        r["walk_R_bounded"] = bool(tr) and not yard_R and abs(best_R[0] - edge_R) < snap if best_R else None
        rows.append(r)
    return pd.DataFrame(rows)


TWO_STRIPS, ONE_STRIP, OTHER = "two_strips", "one_strip", "other"
ISLAND_BACK_M = 3.0  # a plot with a carriageway this close behind it is an island between roads, not a building line
MIN_WALK_PIECE_M = 0.3  # a piece of mapped sidewalk thinner than this is a sliver between polygons, not a sidewalk
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


def covered(s: pd.Series | list[float], step: float, length: float) -> float:
    """The length of street the stations at ``s`` stand for: each station the ``step`` around it, half a step on
    either side, cut at the ends of the axis.

    One convention for every length the ledger gives (the stretches with parking on both sides, the parking they
    hold, the mapped parking per side), and an unbiased one: a run of k stations shows a condition holding over at
    least (k − 1) steps and less than (k + 1) steps; k steps is the middle of that range, so the length is neither
    understated (which would understate the parking an option removes) nor overstated.
    """
    v = np.asarray(s, dtype=float)
    return float((np.minimum(v + step / 2, length) - np.maximum(v - step / 2, 0.0)).clip(min=0.0).sum())


def section_extent(s_from: float, s_to: float, step: float, length: float) -> tuple[float, float]:
    """The stretch of street a section of stations from ``s_from`` to ``s_to`` stands for (see ``covered``)."""
    return max(s_from - step / 2, 0.0), min(s_to + step / 2, length)


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
    df: pd.DataFrame,
    blocks: list[Block],
    step: float,
    stall_lengths: tuple[float, ...],
    length: float,
    min_strip: float = MIN_STRIP_M,
) -> pd.DataFrame:
    """Mapped parking-strip length per side and block (the stations with a strip, by ``covered``), and the stall
    count it implies for given stall lengths (``profiles.parking_space_m``)."""
    rows = []
    for label, sub in [(b.id, df[df.block == b.id]) for b in blocks] + [("all", df)]:
        left = round(covered(sub.s[sub.strip_L > min_strip], step, length), 1)
        right = round(covered(sub.s[sub.strip_R > min_strip], step, length), 1)
        r: dict[str, str | float] = {"block": label, "strip_L_length_m": left, "strip_R_length_m": right}
        for L in stall_lengths:
            r[f"stalls_L_{L:g}m"] = round(left / L, 1)
            r[f"stalls_R_{L:g}m"] = round(right / L, 1)
        rows.append(r)
    return pd.DataFrame(rows)
