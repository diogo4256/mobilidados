"""Run a case end to end: measurements, direction, transit, envelope, encounters, occurrences, area scan,
standards comparison, figures and the findings ledger.

Each stage reads the case's cached sources and the tables of earlier stages, and writes its own tables to
``results/tables``. Tables are the only thing passed between stages, so a partial run (``--stages``) reads what
an earlier run wrote, and a missing table is an error that names the stage to run first.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, unary_union

from . import area_scan, encounters, envelope, figures, geometry, gtfs, ledger, network, occurrences, standards
from .arcgis import to_line
from .config import ArcgisQuery, Case, Config, HttpFiles, StreetfitError
from .sources import IdentifyCache, check_pins, load_json, lock_identify_caches, raw_path

log = logging.getLogger(__name__)


@dataclass
class Run:
    case: Case
    offline: bool = False
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)

    @property
    def cfg(self) -> Config:
        return self.case.config

    @property
    def tables_dir(self) -> Path:
        return self.case.results_dir / "tables"

    def save(self, name: str, df: pd.DataFrame, index: bool = False) -> None:
        self.tables[name] = df
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.tables_dir / f"{name}.csv", index=index)

    def table(self, name: str) -> pd.DataFrame:
        """A result table: from this run, else as an earlier run wrote it."""
        if name not in self.tables:
            path = self.tables_dir / f"{name}.csv"
            if not path.exists():
                raise StreetfitError(f"table {name!r} is missing from {self.tables_dir}: run the stage that writes it first")
            self.tables[name] = pd.read_csv(path)
        return self.tables[name]

    # --- shared inputs ----------------------------------------------------------------------------
    @functools.cached_property
    def axis(self) -> LineString:
        return geometry.street_axis(
            load_json(self.case, self.cfg.profiles.axes)["features"], self.cfg.axes.name_field, self.cfg.street.name
        )

    @functools.cached_property
    def feed(self) -> gtfs.Feed:
        assert self.cfg.transit is not None
        return gtfs.Feed(raw_path(self.case, self.cfg.transit.source))

    def axes(self, source: str) -> dict[str, BaseGeometry]:
        """Street name -> axis, sorted by name. Features sharing a name (a street split into several) are merged."""
        parts: dict[str, list[BaseGeometry]] = {}
        for f in load_json(self.case, source)["features"]:
            if f.get("geometry"):
                parts.setdefault(f["attributes"][self.cfg.axes.name_field], []).append(to_line(f["geometry"]))
        return {k: v[0] if len(v) == 1 else linemerge(unary_union(v)) for k, v in sorted(parts.items())}


def run(case: Case, stages: list[str] | None = None, offline: bool = False) -> Run:
    unknown = sorted(set(stages or []) - set(STAGES))
    if unknown:
        raise StreetfitError(f"unknown stages {unknown}; the stages are {list(STAGES)}")
    stale = check_pins(case)
    if stale:
        raise StreetfitError(
            f"cached files do not match the sha256 pinned in case.toml: {stale}. "
            "Restore the pinned files (fetch --from-dir) or update the pin deliberately."
        )
    r = Run(case, offline=offline)
    if stages is None:  # a full run replaces every output, so nothing from an earlier configuration lingers
        for pattern in ("tables/*.csv", "figures/*.png"):
            for old in case.results_dir.glob(pattern):
                old.unlink()
    for name in stages or STAGES:
        log.info("[%s]", name)
        STAGES[name](r)
    if not offline:
        lock_identify_caches(case)
    return r


# --- stages -----------------------------------------------------------------------------------------
def stage_profiles(r: Run) -> None:
    c, p = r.case, r.cfg.profiles
    roles = r.cfg.cartography.roles()
    polys = geometry.classed_polygons(load_json(c, p.cartography)["features"], r.cfg.cartography.class_field, set().union(*roles.values()))
    df = geometry.measure_profiles(r.axis, polys, roles, step=p.step_m, half_width=p.half_width_m)
    df = geometry.classify(df, r.cfg.street.blocks, narrow_max=p.narrow_max_m)
    length = round(r.axis.length, 2)
    r.save("street", pd.DataFrame([{"name": r.cfg.street.name, "length_m": length}]))
    r.save("profiles", df)
    r.save("summary_by_block", geometry.summarize_blocks(df, r.cfg.street.blocks))
    r.save("parking_strip_lengths", geometry.strip_lengths(df, r.cfg.street.blocks, p.step_m))
    r.save("narrow_sections", pd.DataFrame(geometry.narrow_sections(df, p.step_m), columns=["s_from", "s_to", "block"]))
    tr = Transformer.from_crs(c.crs, 4326, always_xy=True)
    pts = []
    for s in p.check_points_s:
        row = df[(df.s - s).abs() < 1e-6].iloc[0]
        lon, lat = tr.transform(row.x, row.y)
        pts.append(
            {
                "s_m": s,
                "block": row.block,
                "x": row.x,
                "y": row.y,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "free_width_m": row.free_width,
                "strip_L_m": row.strip_L,
                "strip_R_m": row.strip_R,
                "kerb_to_kerb_m": row.kerb_to_kerb,
            }
        )
    r.save("check_points", pd.DataFrame(pts))
    lo, la = tr.transform(*r.axis.xy)
    feature = {
        "type": "Feature",
        "properties": {"name": r.cfg.street.name, "length_m": length},
        "geometry": {"type": "LineString", "coordinates": [[round(x, 7), round(y, 7)] for x, y in zip(lo, la, strict=True)]},
    }
    (c.results_dir / "street_axis.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8")


def stage_direction(r: Run) -> None:
    d, net = r.cfg.direction, r.cfg.network
    if d is None or net is None:
        return
    cache = IdentifyCache(r.case, d.source, offline=r.offline)
    edges = network.edges_along(r.axis, cache, net, d.stations_s)
    cache.save()
    r.save("traffic_direction_edges", edges)


def stage_transit(r: Run) -> None:
    t = r.cfg.transit
    if t is None:
        return
    shapes = gtfs.shapes_along(r.feed, r.axis, r.case.crs, buffer_m=t.buffer_m)
    trips = gtfs.trips_on_shapes(r.feed, shapes)
    r.save("routes_on_street", gtfs.route_summary(trips))
    r.save("stops_near_street", gtfs.stops_near(r.feed, r.axis, r.case.crs))
    on_routes = trips[trips.route_short_name.isin(t.routes)]
    stop_times = r.feed.stop_times(set(on_routes.trip_id))  # the largest table: read it once
    passings = gtfs.reference_passings(r.feed, on_routes, stop_times, t.reference_stops, t.service_date)
    r.save("passings", passings)
    tph = gtfs.trips_per_hour(passings)
    tph.columns = pd.Index([r.cfg.street.heading_label(h) for h in tph.columns])
    r.save("trips_per_hour", tph.rename_axis("hour").reset_index())
    stops = r.feed.table("stops", dtype={"stop_id": str})
    runtimes = []
    for ref in sorted({s.stop_id for s in t.reference_stops}):
        on_day = stop_times[stop_times.trip_id.isin(passings[passings.ref_stop == ref].trip_id)]
        runtimes.append(gtfs.scheduled_runtimes(stop_times, stops, ref, r.case.crs) | {"scope": gtfs.ALL_TRIPS})
        runtimes.append(gtfs.scheduled_runtimes(on_day, stops, ref, r.case.crs) | {"scope": f"trips on {t.service_date}"})
    r.save("scheduled_runtimes", pd.DataFrame(runtimes))


def stage_envelope(r: Run) -> None:
    e = r.cfg.envelope
    if e is None:
        return
    allrow = r.table("summary_by_block").set_index("block").loc["all"]
    free = {"min": float(allrow.free_min), "median": float(allrow.free_median), "p95": float(allrow.free_p95)}
    vehicles = r.cfg.all_vehicles()
    r.save("width_budget", envelope.width_budget(free, vehicles, e.scenarios))
    r.save("overhang_sensitivity", envelope.overhang_sensitivity(free["median"], vehicles, e.scenarios))


def stage_encounters(r: Run) -> None:
    t = r.cfg.transit
    if t is None:
        return
    passings = r.table("passings").astype({"route_short_name": str, "arrival_time": str})
    length = float(r.table("street").length_m.iloc[0])
    narrow = list(r.table("narrow_sections").itertuples(index=False, name=None))
    summary = [encounters.summary(passings, length, t.speeds_kmh, basis="assumed")]
    # sensitivity: the slowest stop-to-stop speed implied by the service day's schedule (slower buses meet more often)
    rt = r.table("scheduled_runtimes")
    day_rows = rt[rt.scope != gtfs.ALL_TRIPS]
    if len(day_rows):
        summary.append(encounters.summary(passings, length, [float(day_rows.kmh_at_median_min.min())], basis="schedule"))
    r.save("encounters_summary", pd.concat(summary, ignore_index=True))
    detail = pd.concat([encounters.locate(encounters.encounters(passings, length, v), narrow) for v in t.speeds_kmh], ignore_index=True)
    r.save("encounters_detail", detail)
    r.save("encounters_by_pair", detail.groupby(["speed_kmh", "pair"]).size().rename("encounters_per_day").reset_index())


def stage_occurrences(r: Run) -> None:
    o = r.cfg.occurrences
    if o is None:
        return
    src = r.case.source(o.source)
    assert isinstance(src, HttpFiles)
    assert src.columns is not None
    pts = occurrences.load_points(sorted(raw_path(r.case, o.source).glob("*.csv")), src.columns, r.case.crs)
    r.save("occurrences_files", occurrences.file_summary(pts))
    streets = r.axes(r.cfg.profiles.axes)
    x0, y0, x1, y1 = r.axis.bounds
    w = o.window_m
    near = occurrences.attribute_to_streets(pts, streets, (x0 - w, y0 - w, x1 + w, y1 + w))
    r.save("occurrences_by_street", occurrences.rates_by_street(near, streets, o.filters, o.max_dist_m, o.min_street_length_m))
    first = next(iter(o.filters.values()))
    r.save("occurrences_by_year", occurrences.yearly_counts(near, r.cfg.street.name, first, o.max_dist_m))


def stage_area(r: Run) -> None:
    a, t = r.cfg.area_scan, r.cfg.transit
    if a is None or t is None:
        return
    roles = r.cfg.cartography.roles()
    polys = geometry.classed_polygons(
        load_json(r.case, a.cartography)["features"], r.cfg.cartography.class_field, roles["road"] | roles["parking"]
    )
    src = r.case.source(a.cartography)
    assert isinstance(src, ArcgisQuery)  # checked when the config was loaded
    env = src.envelope
    (bx0, bx1), (by0, by1) = Transformer.from_crs(4326, r.case.crs, always_xy=True).transform([env[0], env[2]], [env[1], env[3]])
    shapes, n_trips, route_of = area_scan.bus_shapes(r.feed, t.service_date, r.case.crs, (bx0 - 50, by0 - 50, bx1 + 50, by1 + 50))
    stations = area_scan.scan(list(r.axes(a.axes).items()), geometry.Profiler(polys), roles, shapes, n_trips, route_of, step=a.step_m)
    r.save("area_stations", stations)
    cache = IdentifyCache(r.case, a.identify_source, offline=r.offline) if a.identify_source else None
    ranked = area_scan.rank_streets(stations, a.step_m, a.threshold_m, a.reference_m, cache, r.cfg.network)
    if cache:
        cache.save()
    r.save("area_streets", ranked)


def stage_standards(r: Run) -> None:
    if not r.cfg.standards.compare:
        return
    med = float(r.table("summary_by_block").set_index("block").loc["all", "free_median"])
    r.save("standards_comparison", standards.compare(med, r.cfg.standards.compare))


def stage_figures(r: Run) -> None:
    figures.make_all(r)


def stage_ledger(r: Run) -> None:
    ledger.write(r)


STAGES: dict[str, Callable[[Run], None]] = {
    "profiles": stage_profiles,
    "direction": stage_direction,
    "transit": stage_transit,
    "envelope": stage_envelope,
    "encounters": stage_encounters,
    "occurrences": stage_occurrences,
    "area": stage_area,
    "standards": stage_standards,
    "figures": stage_figures,
    "ledger": stage_ledger,
}
