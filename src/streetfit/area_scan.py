"""Scan every street with scheduled buses in an area for the same pattern as the case street.

For each street axis, stations every ``step`` metres are matched to GTFS shapes running along them (within
``near_m`` and ``max_angle`` degrees). At stations with buses, a transect measures the free width between
parking strips. The result ranks streets by how many metres combine two-sided parking with a free width
below a threshold. This turns one complaint into a map of where the same problem exists.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import LineString

from .geometry import Profiler
from .gtfs import Feed, active_service_ids
from .network import directions
from .sources import IdentifyCache


def bus_shapes(feed: Feed, day: dt.date, crs: int, bbox: tuple[float, float, float, float]):
    """Shapes of trips running on ``day`` that intersect ``bbox`` (projected), with trips/day and route."""
    trips = feed.table("trips", dtype=str)
    routes = feed.table("routes", dtype=str)[["route_id", "route_short_name"]]
    t = trips[trips.service_id.isin(active_service_ids(feed, day))].merge(routes, on="route_id")
    n_trips, route_of = t.groupby("shape_id").size(), t.groupby("shape_id").route_short_name.first()
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    box = shapely.box(*bbox)
    shapes = {}
    for sid, g in feed.table("shapes", dtype={"shape_id": str}).groupby("shape_id"):
        if sid not in n_trips.index:
            continue
        g = g.sort_values("shape_pt_sequence")
        x, y = tr.transform(g.shape_pt_lon.values, g.shape_pt_lat.values)
        line = LineString(np.c_[x, y])
        if line.intersects(box):
            shapes[sid] = line
    return shapes, n_trips, route_of


def scan(
    axes: list[tuple[str, LineString]],
    profiler: Profiler,
    classes: dict[str, set[str]],
    shapes: dict,
    n_trips: pd.Series,
    route_of: pd.Series,
    step: float = 3.0,
    half: float = 15.0,
    near_m: float = 10.0,
    max_angle: float = 30.0,
    snap: float = 0.3,
    min_part: float = 30.0,
) -> pd.DataFrame:
    """One row per station with buses: street, buses/day, number of bus directions, routes, free width, two-sided parking."""
    sids = list(shapes)
    stree = STRtree([shapes[s] for s in sids])
    cos_max = math.cos(math.radians(max_angle))
    rows = []
    for name, line in axes:
        for part in getattr(line, "geoms", [line]):
            if part.length < min_part:
                continue
            s = np.arange(step / 2, part.length, step)
            pts = shapely.line_interpolate_point(part, s)
            a = shapely.get_coordinates(shapely.line_interpolate_point(part, np.clip(s - 1, 0, part.length)))
            b = shapely.get_coordinates(shapely.line_interpolate_point(part, np.clip(s + 1, 0, part.length)))
            tv = (b - a) / np.linalg.norm(b - a, axis=1)[:, None]
            bus, dirs, rts = np.zeros(len(s)), [set() for _ in s], [set() for _ in s]
            for j in stree.query(part.buffer(near_m)):
                ln = shapes[sids[j]]
                k = np.where(shapely.distance(ln, pts) <= near_m)[0]
                if not len(k):
                    continue
                loc = shapely.line_locate_point(ln, pts[k])
                u = shapely.get_coordinates(shapely.line_interpolate_point(ln, loc + 1)) - shapely.get_coordinates(
                    shapely.line_interpolate_point(ln, loc - 1)
                )
                u = u / np.maximum(np.linalg.norm(u, axis=1)[:, None], 1e-9)
                for kk, cc in zip(k, (u * tv[k]).sum(axis=1), strict=True):
                    if abs(cc) >= cos_max:
                        bus[kk] += n_trips[sids[j]]
                        dirs[kk].add(int(np.sign(cc)))
                        rts[kk].add(route_of[sids[j]])
            for i in np.where(bus > 0)[0]:
                p = shapely.get_coordinates(pts[i])[0]
                n = (-tv[i][1], tv[i][0])
                tr = LineString([(p[0] - half * n[0], p[1] - half * n[1]), (p[0] + half * n[0], p[1] + half * n[1])])
                road = profiler.intervals(tr, p[0], p[1], n, classes["road"])
                park = profiler.intervals(tr, p[0], p[1], n, classes["parking"])
                free = next(((lo, hi) for lo, hi in road if lo - snap <= 0 <= hi + snap), None)
                left = right = False
                if free:
                    left = any(abs(lo - free[1]) <= snap for lo, _ in park)
                    right = any(abs(hi - free[0]) <= snap for _, hi in park)
                rows.append(
                    {
                        "street": name,
                        "x": round(p[0], 1),
                        "y": round(p[1], 1),
                        "buses_per_day": int(bus[i]),
                        "bus_directions": len(dirs[i]),
                        "routes": " ".join(sorted(rts[i])),
                        "free_width_m": round(free[1] - free[0], 2) if free else np.nan,
                        "parking_both_sides": left and right,
                    }
                )
    return pd.DataFrame(rows)


def rank_streets(
    st: pd.DataFrame,
    step: float,
    threshold: float,
    reference: float,
    cache: IdentifyCache | None,
    fields: dict[str, str] | None,
    open_value: str = "Traversable",
    min_bus_m: float = 45,
    min_below_ref_m: float = 30,
) -> pd.DataFrame:
    out = []
    for name, g in st.groupby("street"):
        v = g.dropna(subset=["free_width_m"])
        if len(g) * step < min_bus_m or v.empty:
            continue
        pattern = v[v.parking_both_sides & (v.free_width_m < threshold)]
        r = {
            "street": name,
            "metres_with_buses": round(len(g) * step),
            "buses_per_day": int(g.buses_per_day.median()),
            "buses_both_directions": bool((g.bus_directions == 2).mean() > 0.5),
            "routes": " ".join(sorted(set(" ".join(g.routes).split()))),
            "free_width_median_m": round(v.free_width_m.median(), 2),
            "free_width_p10_m": round(v.free_width_m.quantile(0.1), 2),
            "pct_parking_both_sides": round(100 * v.parking_both_sides.mean()),
            f"metres_below_{reference:g}m": round((v.free_width_m < reference).sum() * step),
            "metres_with_pattern": round(len(pattern) * step),
            "traffic": "",
        }
        if cache is not None and fields and r[f"metres_below_{reference:g}m"] >= min_below_ref_m:
            ref = pattern if len(pattern) else v.nsmallest(max(1, len(v) // 2), "free_width_m")
            q = ref.iloc[len(pattern) // 2 if len(pattern) else 0]
            edges = pd.DataFrame(
                [
                    {"edge": a.get(fields["edge"]), "direction": a.get(fields["direction"]), "status": a.get(fields["status"])}
                    for a in cache.get(q.x, q.y, cache.src.get("tolerance", 3))
                ]
            )
            r["traffic"] = directions(edges, open_value)
        out.append(r)
    return pd.DataFrame(out).sort_values(["metres_with_pattern", f"metres_below_{reference:g}m"], ascending=False)
