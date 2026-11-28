"""Run a case end to end: measurements, direction, transit, envelope, encounters, occurrences, area scan,
standards comparison, figures and the findings ledger.

Each stage reads the case's cached sources and the tables of earlier stages, and writes its own tables to
``results/tables``. Tables are the only thing passed between stages, so a partial run (``--stages``) reads what
an earlier run wrote, and a missing table is an error that names the stage to run first.
"""

from __future__ import annotations

import datetime as dt
import functools
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import linemerge, unary_union

from . import (
    appraisal,
    appraisal_report,
    area_scan,
    delay,
    direction,
    encounters,
    envelope,
    figures,
    geometry,
    gtfs,
    i18n,
    ledger,
    occurrences,
    reroute,
    standards,
)
from .arcgis import to_line
from .config import ArcgisQuery, Case, Config, GitArchive, HttpFiles, MobilidadosError
from .sources import IdentifyCache, check_lock, check_pins, load_json, raw_path

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
                raise MobilidadosError(f"table {name!r} is missing from {self.tables_dir}: run the stage that writes it first")
            self.tables[name] = pd.read_csv(path)
        return self.tables[name]

    @property
    def two_strips(self) -> bool:
        """Whether the street has stations with parking mapped on both sides (``summary_by_block`` has its ``all``
        row). Without them there is no free width between parking strips, and the width budget and the design
        references, which compare it, do not apply."""
        return "all" in set(self.table("summary_by_block").block)

    @property
    def two_strips_m(self) -> float:
        """The length of street with parking on both sides (the stations the free width counts), by
        ``geometry.covered``: the free-width finding states it and the parking an option removes is measured on it."""
        profiles = self.table("profiles")
        two = profiles.s[profiles["class"] == geometry.TWO_STRIPS]
        return round(geometry.covered(two, self.cfg.profiles.step_m, float(self.table("street").length_m.iloc[0])), 1)

    def narrow_extents(self) -> list[tuple[float, float, str]]:
        """The sections with parking on both sides as stretches of street (``geometry.section_extent``)."""
        step, length = self.cfg.profiles.step_m, float(self.table("street").length_m.iloc[0])
        return [
            (*geometry.section_extent(a, z, step, length), b)
            for a, z, b in self.table("narrow_sections").itertuples(index=False, name=None)
        ]

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
        raise MobilidadosError(f"unknown stages {unknown}; the stages are {list(STAGES)}")
    stale = check_pins(case)
    if stale:
        raise MobilidadosError(
            f"cached files do not match the sha256 pinned in the case's configuration: {stale}. "
            "Restore the pinned files (fetch --refresh --from-dir FOLDER) or update the pin deliberately."
        )
    changed = check_lock(case)
    if changed:
        raise MobilidadosError(
            f"cached files do not match the sha256 recorded in sources.lock.json: {changed}. "
            "Restore the locked files (fetch --refresh --from-dir FOLDER), or take new data deliberately (fetch --refresh); "
            "a routing-network cache (*identify.json) is not downloaded by fetch: delete it and run without --offline to "
            "query the service again."
        )
    r = Run(case, offline=offline)
    write_config(case)
    if stages is None:  # a full run replaces every table, so nothing from an earlier configuration lingers
        for old in case.results_dir.glob("tables/*.csv"):  # the figures stage removes the figures it no longer makes
            old.unlink()
    for name in stages or STAGES:
        log.info("[%s]", name)
        STAGES[name](r)
    return r


def write_config(case: Case) -> Path:
    """Write the resolved, validated configuration to ``results/config.json``, so a run records the parameters it
    used even when they come from a city profile that later changes."""
    path = case.results_dir / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(case.config.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")
    return path


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
    r.save("parking_strip_lengths", geometry.strip_lengths(df, r.cfg.street.blocks, p.step_m, tuple(p.parking_space_m), r.axis.length))
    r.save("narrow_sections", pd.DataFrame(geometry.narrow_sections(df, p.step_m), columns=["s_from", "s_to", "block"]))
    tr = Transformer.from_crs(c.crs, 4326, always_xy=True)
    pts = []
    for s in p.check_points_s:
        i = (df.s - s).abs().idxmin()  # the station at s (check points are on the grid of stations)
        if abs(df.s[i] - s) > p.step_m / 2:
            raise MobilidadosError(f"profiles.check_points_s: {s} m is outside the street axis (0 to {length} m)")
        row = df.loc[i]
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
    edges = direction.edges_along(r.axis, cache, net, d.stations_s)
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
    r.save("downstream_km", gtfs.downstream_km(stop_times, passings))
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
    if e is None or not r.two_strips:
        return
    allrow = r.table("summary_by_block").set_index("block").loc["all"]
    free = {"min": float(allrow.free_min), "median": float(allrow.free_median), "p95": float(allrow.free_p95)}
    vehicles = r.cfg.all_vehicles()
    r.save("width_budget", envelope.width_budget(free, vehicles, e.scenarios))
    r.save("overhang_sensitivity", envelope.overhang_sensitivity(free["median"], vehicles, e.scenarios))
    r.save("without_parking", envelope.without_parking(r.table("profiles"), r.two_strips_m, r.cfg.profiles.parking_space_m))
    if e.practical_clearance_m is not None:
        one_side = float(r.table("without_parking").set_index("without").loc[["L", "R"], "free_median"].min())
        r.save("passing_practice", envelope.practical_passing(free["median"], one_side, vehicles, e.scenarios, e.practical_clearance_m))


def stage_encounters(r: Run) -> None:
    t = r.cfg.transit
    if t is None:
        return
    passings = r.table("passings").astype({"route_short_name": str, "arrival_time": str})
    length = float(r.table("street").length_m.iloc[0])
    narrow = r.narrow_extents()  # a meeting counts in a section over the whole stretch its stations stand for
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


def stage_delay(r: Run) -> None:
    dl, t = r.cfg.delay, r.cfg.transit
    if dl is None or t is None:
        return
    src = r.case.source(dl.source)
    assert isinstance(src, GitArchive)  # checked when the config was loaded
    cfg = dl.model_copy(update={"exclude_dates": sorted(set(dl.exclude_dates) | set(r.cfg.city.holidays))})
    rts = delay.routes(r.feed, t.routes, r.axis, r.case.crs, cfg)
    unread = sorted({x.route_id for x in rts} - set(src.route_ids))
    if unread:
        raise MobilidadosError(
            f"sources.{dl.source}.route_ids does not include {unread}, the GTFS route_id of the routes in transit.routes"
        )
    folder = raw_path(r.case, dl.source)
    for name in ("positions.csv", "snapshots.csv"):
        if not (folder / name).exists():
            raise MobilidadosError(f"{folder / name} is missing: run `mobilidados fetch {r.case.root}` first")
    pos, snaps = delay.load(
        pd.read_csv(folder / "positions.csv", dtype=str), pd.read_csv(folder / "snapshots.csv"), cfg.time_zone, src.time_zone
    )
    placed = delay.place(pos, rts, r.case.crs, cfg.max_offset_m)
    for name, table in delay.analyse(placed, snaps, rts, cfg, r.axis, r.table("passings")).items():
        r.save(name, table)
    # where along the stretch the excess sits, and whether buses there give way to oncoming ones (appraisal's attribution)
    cuts = delay.parts(r.narrow_extents(), cfg.s_from, cfg.s_to)
    r.save("delay_by_part", delay.by_part(placed, snaps, cuts, cfg, rts, r.axis))
    fresh = placed[placed.age_s.abs() <= cfg.max_age_s]
    r.save("delay_copresence", delay.copresence(delay.on_axis(fresh, rts, r.axis, r.case.crs), snaps, cuts, cfg))


def stage_occurrences(r: Run) -> None:
    o = r.cfg.occurrences
    if o is None:
        return
    src = r.case.source(o.source)
    assert isinstance(src, HttpFiles)
    assert src.columns is not None
    folder = raw_path(r.case, o.source)  # only the files the source names: anything else in the folder is not its data
    pts = occurrences.load_points(sorted(folder / f.name for f in src.files), src.columns, r.case.crs)
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
    (bx0, bx1), (by0, by1) = Transformer.from_crs(src.envelope_sr, r.case.crs, always_xy=True).transform([env[0], env[2]], [env[1], env[3]])
    shapes, n_trips, route_of = area_scan.bus_shapes(r.feed, t.service_date, r.case.crs, (bx0 - 50, by0 - 50, bx1 + 50, by1 + 50))
    stations = area_scan.scan(list(r.axes(a.axes).items()), geometry.Profiler(polys), roles, shapes, n_trips, route_of, step=a.step_m)
    r.save("area_stations", stations)
    cache = IdentifyCache(r.case, a.identify_source, offline=r.offline) if a.identify_source else None
    ranked = area_scan.rank_streets(stations, a.step_m, a.threshold_m, a.reference_m, cache, r.cfg.network)
    if cache:
        cache.save()
    r.save("area_streets", ranked)


def stage_standards(r: Run) -> None:
    if not r.cfg.standards.compare or not r.two_strips:
        return
    med = float(r.table("summary_by_block").set_index("block").loc["all", "free_median"])
    r.save("standards_comparison", standards.compare(med, r.cfg.standards.compare))


def stage_appraisal(r: Run) -> None:
    a, dl, t, e = r.cfg.appraisal, r.cfg.delay, r.cfg.transit, r.cfg.envelope
    if a is None or dl is None or t is None or e is None or not r.two_strips:
        # no appraisal to make: a study written by an earlier run would outlive the results it described
        (r.case.results_dir / "appraisal.md").unlink(missing_ok=True)
        return
    block_metres: dict[str, float] = {}
    for x, z, block in r.narrow_extents():
        block_metres[block] = block_metres.get(block, 0.0) + (z - x)
    tables = {k: r.table(k) for k in ("delay_summary", "delay_by_part", "delay_copresence", "passings", "downstream_km")}
    holidays = sorted(set(dl.exclude_dates) | set(r.cfg.city.holidays))
    tables["appraisal_passages"] = a_passages(r, holidays)
    r.save("appraisal_passages", tables["appraisal_passages"])
    m = appraisal.measured(tables, a, block_metres, dl.peak_hours, t.service_date.year, holidays)
    for name, table in appraisal.appraise(a, m).items():
        r.save(name, table)
    r.save("appraisal_measured", pd.DataFrame(
        [{"input": "excess_s", "low": m.excess_s[0], "central": m.excess_s[1], "high": m.excess_s[2]}]
        + [{"input": f"attribution_{k}", "low": v[0], "central": v[1], "high": v[2]} for k, v in m.attribution.items()]
        + [{"input": "peak_passages_per_working_day", "low": m.peak_passages_per_day, "central": m.peak_passages_per_day, "high": m.peak_passages_per_day},
           {"input": "working_days_per_year", "low": m.working_days, "central": m.working_days, "high": m.working_days}]
        + [{"input": f"metres_{k}", "low": v, "central": v, "high": v} for k, v in m.metres.items()]
        + [{"input": f"passages_{part}_{k}", "low": v[i], "central": v[i], "high": v[i]}
           for k, v in m.passages.items() for i, part in enumerate(("peak", "other"))]
        + [{"input": "passages_year", "low": m.passages_year, "central": m.passages_year, "high": m.passages_year}]
        + [{"input": k, "low": v, "central": v, "high": v} for k, v in (
            ("km_after_street", m.km_after),
            ("headway_peak_min", 1 / m.inv_headway[0] / 60 if m.inv_headway[0] else float("nan")),
            ("headway_other_min", 1 / m.inv_headway[1] / 60 if m.inv_headway[1] else float("nan")),
            ("meet_share_peak", m.meet_share if m.meet_share is not None else float("nan")),
            ("offpeak_ratio", m.offpeak_ratio if m.offpeak_ratio is not None else float("nan")))]
    ))  # fmt: skip
    # the parking mapped around the street, as places at the central length of a place (occupancy is not known)
    roles = r.cfg.cartography.roles()
    park = unary_union(
        [
            g
            for _, g in geometry.classed_polygons(
                load_json(r.case, a_cartography(r))["features"], r.cfg.cartography.class_field, roles["parking"]
            )
        ]
    )
    stall = a.parameters["stall_m"].central
    depth = float(r.table("summary_by_block").set_index("block").loc["all", ["strip_L_median", "strip_R_median"]].mean())
    supply = {radius: park.intersection(r.axis.buffer(radius)).area / depth / stall for radius in (150, 300)}
    vehicles = r.cfg.all_vehicles()
    bus = vehicles[e.bus]
    refs = (
        [(row.document + ", p. " + str(row.page), float(row.value_m)) for row in r.table("standards_comparison").itertuples()]
        if r.cfg.standards.compare
        else []
    )
    one_side = r.cfg.profiles.parking_space_m
    metres = max(m.metres.values())
    places = (metres / max(one_side), metres / min(one_side))
    lang = r.case.lang

    def say(key: str, **kw: Any) -> str:
        return i18n.t(f"appraisal.{key}", lang, **kw)

    r.save("appraisal_feasibility", appraisal.feasibility(
        a, r.table("without_parking"), envelope.widths(bus, bus, False), envelope.widths(bus, bus, True), refs, places, supply, say
    ))  # fmt: skip
    if a.reroutes:
        route_days = a_route_passages(r, holidays)
        r.save("appraisal_route_passages", route_days)
        detours = a_detours(r, sorted({mv for rr in a.reroutes for mv in rr.moves}))
        r.save("appraisal_detours", detours)
        all_blocks = sorted({b for o in a.options for b in o.blocks})
        attr_all = appraisal.attribution(tables["delay_by_part"], tables["delay_copresence"], all_blocks, a.significance)[1]
        r.save("appraisal_reroutes", appraisal.reroutes(a, m, appraisal.central(a, m), attr_all, route_days, detours))
    appraisal_report.write(r)


def a_route_passages(r: Run, holidays: list[dt.date]) -> pd.DataFrame:
    """Passages a day of each route and direction through the street, on the representative day of each kind."""
    t = r.cfg.transit
    assert t is not None
    shapes = gtfs.shapes_along(r.feed, r.axis, r.case.crs, buffer_m=t.buffer_m)
    trips = gtfs.trips_on_shapes(r.feed, shapes)
    on_routes = trips[trips.route_short_name.isin(t.routes)]
    stop_times = r.feed.stop_times(set(on_routes.trip_id))
    days = sorted({row.date for row in r.table("appraisal_passages")[["day_kind", "date"]].drop_duplicates().itertuples()})
    kinds = dict(r.table("appraisal_passages")[["date", "day_kind"]].drop_duplicates().itertuples(index=False, name=None))
    rows = []
    for day in days:
        kind = kinds[day]
        p = gtfs.reference_passings(
            r.feed, on_routes, stop_times, t.reference_stops, dt.date.fromisoformat(str(day)), strict=kind == "working"
        )
        for (route, d, h), g in p.groupby(["route_short_name", "direction_id", "heading"]) if len(p) else []:
            rows.append({"day_kind": kind, "key": f"{route} {d}", "heading": int(h), "passages": len(g)})
    return pd.DataFrame(rows, columns=["day_kind", "key", "heading", "passages"])


def a_detours(r: Run, keys: list[str]) -> pd.DataFrame:
    """For each 'route direction_id' in ``keys``: its busiest shape on the street, the smallest detour round the street
    on the area's street network (``reroute.detour``), the streets it uses that carry no bus today, and the stops on
    the street it would no longer serve."""
    t = r.cfg.transit
    assert t is not None
    source = r.cfg.area_scan.axes if r.cfg.area_scan else r.cfg.profiles.axes
    net = reroute.Network(r.axes(source).items())
    shapes = gtfs.shapes_along(r.feed, r.axis, r.case.crs, buffer_m=t.buffer_m)
    trips = gtfs.trips_on_shapes(r.feed, shapes)
    pts = r.feed.table("shapes", dtype={"shape_id": str})
    stops = r.feed.table("stops", dtype={"stop_id": str})
    tr = Transformer.from_crs(4326, r.case.crs, always_xy=True)
    with_buses = set(r.table("area_streets").street) if r.cfg.area_scan else set()
    rows = []
    for key in keys:
        route, d = key.split()
        mine = trips[(trips.route_short_name == route) & (trips.direction_id == d) & (trips.heading != 0)]
        if mine.empty:
            raise MobilidadosError(f"appraisal.reroutes: {key} does not run along {r.cfg.street.name}")
        sid = str(mine.shape_id.value_counts().index[0])
        g = pts[pts.shape_id == sid].sort_values("shape_pt_sequence")
        x, y = tr.transform(g.shape_pt_lon.to_numpy(), g.shape_pt_lat.to_numpy())
        found = reroute.detour(net, LineString(list(zip(x, y, strict=True))), r.axis, r.cfg.street.name, bus_streets=with_buses)
        if found is None:
            raise MobilidadosError(f"appraisal.reroutes: no way round {r.cfg.street.name} found for {key}")
        trip = mine[mine.shape_id.astype(str) == sid].trip_id.iloc[0]  # the stops of the shape the detour follows
        served = r.feed.stop_times({trip}).merge(stops, on="stop_id")
        sx, sy = tr.transform(served.stop_lon.to_numpy(), served.stop_lat.to_numpy())
        shape = LineString(list(zip(x, y, strict=True)))
        skipped = reroute.skipped(zip(served.stop_id, sx, sy, strict=True), shape, found.from_m, found.to_m, found.path)
        rows.append({"key": key, "shape_id": sid, "lead_in_m": found.lead_in_m, "current_route_m": found.to_m - found.from_m,
                     "with_street_m": found.with_street_m, "without_street_m": found.without_street_m, "detour_m": found.detour_m,
                     "shorter_without_street": found.shorter_without, "detour_min_m": found.detour_min_m, "detour_max_m": found.detour_max_m, "on_bus_streets": found.on_bus_streets,
                     "via": "; ".join(found.via), "via_without_buses_today": "; ".join(v for v in found.via if with_buses and v not in with_buses),
                     "stops_skipped": " ".join(f"{s} ({n})" for s, n in zip(served.stop_id, served.stop_name, strict=True) if s in skipped)})  # fmt: skip
    return pd.DataFrame(rows)


def a_passages(r: Run, holidays: list[dt.date]) -> pd.DataFrame:
    """Passages the timetable schedules through the street in each clock hour of a representative day of each kind: the
    service day (a working day), and the first Saturday and the first Sunday after it that are not holidays."""
    t = r.cfg.transit
    assert t is not None
    shapes = gtfs.shapes_along(r.feed, r.axis, r.case.crs, buffer_m=t.buffer_m)
    trips = gtfs.trips_on_shapes(r.feed, shapes)
    on_routes = trips[trips.route_short_name.isin(t.routes)]
    stop_times = r.feed.stop_times(set(on_routes.trip_id))
    off = set(holidays)

    def next_day(weekday: int) -> dt.date:
        d = t.service_date + dt.timedelta(days=1)
        while d.weekday() != weekday or d in off:
            d += dt.timedelta(days=1)
        return d

    rows = []
    for kind, day in (("working", t.service_date), ("saturday", next_day(5)), ("sunday", next_day(6))):
        p = gtfs.reference_passings(r.feed, on_routes, stop_times, t.reference_stops, day, strict=kind == "working")
        hours = (p.t.astype(int) // 3600 % 24).value_counts() if len(p) else pd.Series(dtype=int)
        rows += [{"day_kind": kind, "date": day.isoformat(), "hour": h, "passages": int(hours.get(h, 0))} for h in range(24)]
    return pd.DataFrame(rows)


def a_cartography(r: Run) -> str:
    """The cartography that covers the surroundings: the area scan's if there is one, else the case's."""
    return r.cfg.area_scan.cartography if r.cfg.area_scan else r.cfg.profiles.cartography


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
    "delay": stage_delay,
    "occurrences": stage_occurrences,
    "area": stage_area,
    "standards": stage_standards,
    "appraisal": stage_appraisal,
    "figures": stage_figures,
    "ledger": stage_ledger,
}
