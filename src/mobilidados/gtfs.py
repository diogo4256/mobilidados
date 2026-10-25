"""Scheduled public transport on a street, from an official GTFS feed.

Which shapes run along the street (and in which direction), which stops are nearby, how many trips pass per
hour on a given service day, and the scheduled times at reference stops that feed the encounter model.
All of it is the *timetable*, not observed operation.
"""

from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point

from .config import MobilidadosError, ReferenceStop

ALL_TRIPS = "all trips in the feed"  # scope label of the whole-feed rows in scheduled_runtimes


class Feed:
    """Read GTFS tables directly from the zip (no extraction)."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def table(self, name: str, **kw: Any) -> pd.DataFrame:
        with zipfile.ZipFile(self.path) as z, z.open(f"{name}.txt") as f:
            return pd.read_csv(f, **kw)

    def has(self, name: str) -> bool:
        with zipfile.ZipFile(self.path) as z:
            return f"{name}.txt" in z.namelist()

    def stop_times(self, trip_ids: set[str]) -> pd.DataFrame:
        """stop_times for the given trips only (the full table is large; read it in chunks)."""
        cols = ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]
        with zipfile.ZipFile(self.path) as z, z.open("stop_times.txt") as f:
            parts = [chunk[chunk.trip_id.isin(trip_ids)] for chunk in pd.read_csv(f, usecols=cols, dtype=str, chunksize=500_000)]
        st = pd.concat(parts, ignore_index=True)
        st["stop_sequence"] = st.stop_sequence.astype(int)
        return st


def seconds(hms: str) -> int:
    """GTFS time (may exceed 24:00:00) to seconds after midnight of the service day."""
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def active_service_ids(feed: Feed, day: dt.date) -> set[str]:
    """Service IDs running on ``day`` (calendar.txt rules, then calendar_dates.txt exceptions)."""
    ds, wd = day.strftime("%Y%m%d"), day.strftime("%A").lower()
    active: set[str] = set()
    if feed.has("calendar"):  # optional when calendar_dates.txt carries everything
        cal = feed.table("calendar", dtype=str)
        active = set(cal[(cal[wd] == "1") & (cal.start_date <= ds) & (cal.end_date >= ds)].service_id)
    if feed.has("calendar_dates"):
        cd = feed.table("calendar_dates", dtype=str)
        active |= set(cd[(cd.date == ds) & (cd.exception_type == "1")].service_id)
        active -= set(cd[(cd.date == ds) & (cd.exception_type == "2")].service_id)
    return active


def shapes_along(
    feed: Feed, axis: LineString, crs: int, buffer_m: float = 12.0, near_m: float = 6.0, min_run_m: float = 20.0, min_inside_m: float = 5.0
) -> pd.DataFrame:
    """Shapes passing within ``buffer_m`` of the axis, with their heading along it.

    A shape with less than ``min_inside_m`` of its length inside the buffer is left out (it only grazes the street).

    ``heading`` is +1 (increasing s), -1 (decreasing s) or 0 when the shape only crosses the street or touches
    one end (it covers less than ``min_run_m`` of the axis).
    """
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    buf = axis.buffer(buffer_m)
    rows = []
    for sid, g in feed.table("shapes").groupby("shape_id"):
        g = g.sort_values("shape_pt_sequence")
        x, y = tr.transform(g.shape_pt_lon.to_numpy(), g.shape_pt_lat.to_numpy())
        ls = LineString(np.c_[x, y])
        if ls.distance(axis) > buffer_m:
            continue
        length = ls.intersection(buf).length
        if length < min_inside_m:
            continue
        ss = [axis.project(Point(a, b)) for a, b in zip(x, y, strict=True) if Point(a, b).distance(axis) < near_m]
        run = (ss[-1] - ss[0]) if len(ss) > 1 else 0.0
        heading = 0 if abs(run) < min_run_m else int(np.sign(run))
        rows.append(
            {
                "shape_id": str(sid),
                "length_in_buffer_m": round(length, 1),
                "heading": heading,
                "s_first": round(ss[0], 1) if ss else None,
                "s_last": round(ss[-1], 1) if ss else None,
            }
        )
    return pd.DataFrame(rows)


def trips_on_shapes(feed: Feed, shapes: pd.DataFrame) -> pd.DataFrame:
    trips = feed.table("trips", dtype=str)
    routes = feed.table("routes", dtype=str)[["route_id", "route_short_name", "route_long_name"]]
    return trips.merge(shapes, on="shape_id").merge(routes, on="route_id")


def route_summary(trips: pd.DataFrame) -> pd.DataFrame:
    keys = ["route_short_name", "route_long_name", "direction_id", "shape_id", "length_in_buffer_m", "heading", "s_first", "s_last"]
    return trips.groupby(keys, dropna=False).size().rename("n_trips_in_feed").reset_index()


def stops_near(feed: Feed, axis: LineString, crs: int, max_dist: float = 40.0) -> pd.DataFrame:
    stops = feed.table("stops", dtype={"stop_id": str})
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    x, y = tr.transform(stops.stop_lon.to_numpy(), stops.stop_lat.to_numpy())
    pts = [Point(a, b) for a, b in zip(x, y, strict=True)]
    stops["dist_m"] = [p.distance(axis) for p in pts]
    stops["s_m"] = [axis.project(p) for p in pts]
    near = stops[stops.dist_m < max_dist].sort_values("s_m")
    return near[["stop_id", "stop_name", "stop_lat", "stop_lon", "dist_m", "s_m"]].round({"dist_m": 1, "s_m": 1})


def reference_passings(feed: Feed, trips: pd.DataFrame, stop_times: pd.DataFrame, refs: list[ReferenceStop], day: dt.date) -> pd.DataFrame:
    """Scheduled arrival at each route/direction's reference stop, for trips running on ``day``.

    ``stop_times`` must cover ``trips``. One row per trip: route, direction_id, heading, s_ref (the stop's position
    along the axis), arrival_time and t (seconds after midnight).
    """
    active = active_service_ids(feed, day)
    keyed = {(r.route, str(r.direction_id)): r for r in refs}
    sel = trips[[(rt, d) in keyed for rt, d in zip(trips.route_short_name, trips.direction_id, strict=True)]]
    sel = sel[sel.service_id.isin(active)]
    st = stop_times[stop_times.trip_id.isin(sel.trip_id)]
    last = st.groupby("trip_id").stop_sequence.max()
    rows = []
    for (rt, d), ref in keyed.items():
        at_ref = st[st.stop_id == ref.stop_id].sort_values("stop_sequence").drop_duplicates("trip_id")  # a loop passes once
        t = sel[(sel.route_short_name == rt) & (sel.direction_id == d)].merge(at_ref, on="trip_id")
        if not (t.stop_sequence < t.trip_id.map(last)).any():  # scheduled_runtimes needs the next stop
            raise MobilidadosError(
                f"route {rt} direction {d}: no trip serves stop {ref.stop_id} on {day} with a following stop; "
                "check reference_stops and service_date"
            )
        rows.append(t.assign(ref_stop=ref.stop_id, s_ref=ref.s_m, heading=ref.heading))
    out = pd.concat(rows, ignore_index=True)
    out["t"] = out.arrival_time.map(seconds)
    cols = ["route_short_name", "direction_id", "trip_id", "ref_stop", "s_ref", "heading", "arrival_time", "t"]
    return out.sort_values(["t", "route_short_name"])[cols].reset_index(drop=True)


def trips_per_hour(passings: pd.DataFrame) -> pd.DataFrame:
    """Trips per clock hour (at the reference stop) and heading."""
    p = passings.assign(hour=passings.t // 3600)
    tab = p.groupby(["hour", "heading"]).size().unstack("heading").fillna(0).astype(int)
    return tab.reindex(columns=[1, -1], fill_value=0)


def scheduled_runtimes(stop_times: pd.DataFrame, stops: pd.DataFrame, ref_stop: str, crs: int) -> dict[str, Any]:
    """Scheduled time from ``ref_stop`` to the most common next stop (median, p10, p90 in seconds) over the trips in
    ``stop_times``, the straight-line distance between the two stops and the speed it implies at the median time (a
    lower bound: the route is longer than the straight line)."""
    st = stop_times.sort_values(["trip_id", "stop_sequence"])
    st["t_arr"], st["t_dep"] = st.arrival_time.map(seconds), st.departure_time.map(seconds)
    rows = []
    for _, g in st.groupby("trip_id"):
        g = g.reset_index(drop=True)
        i = g.index[g.stop_id == ref_stop]
        if len(i) and i[0] + 1 < len(g):
            rows.append({"next_stop": g.loc[i[0] + 1, "stop_id"], "dt_s": g.loc[i[0] + 1, "t_arr"] - g.loc[i[0], "t_dep"]})
    r = pd.DataFrame(rows)
    nxt = r.next_stop.value_counts().index[0]
    sel = r[r.next_stop == nxt].dt_s
    stops = stops.set_index("stop_id")
    (x0, x1), (y0, y1) = Transformer.from_crs(4326, crs, always_xy=True).transform(
        stops.loc[[ref_stop, nxt], "stop_lon"].to_numpy(), stops.loc[[ref_stop, nxt], "stop_lat"].to_numpy()
    )
    dist = float(np.hypot(x1 - x0, y1 - y0))
    return {
        "ref_stop": ref_stop,
        "next_stop": nxt,
        "next_stop_name": stops.loc[nxt, "stop_name"],
        "dist_straight_m": round(dist),
        "n": len(sel),
        "median_s": float(sel.median()),
        "p10_s": float(sel.quantile(0.1)),
        "p90_s": float(sel.quantile(0.9)),
        "kmh_at_median_min": round(dist / float(sel.median()) * 3.6, 1),
    }
