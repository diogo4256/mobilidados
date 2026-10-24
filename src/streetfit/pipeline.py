"""Run a case end to end: measurements, direction, transit, envelope, encounters, occurrences, area scan,
standards comparison, figures and the findings ledger. Each stage writes CSVs to ``results/tables``."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.ops import linemerge, unary_union

from . import area_scan, encounters, envelope, figures, geometry, gtfs, network, occurrences, report, standards
from .arcgis import features, to_line
from .config import Case
from .sources import IdentifyCache, check_pins, load_json, lock_identify_caches, raw_path

STAGES = ["profiles", "direction", "transit", "envelope", "encounters", "occurrences", "area", "standards", "figures", "ledger"]


@dataclass
class Run:
    case: Case
    offline: bool = False
    log: object = print
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

    @property
    def tables_dir(self) -> Path:
        return self.case.results_dir / "tables"

    def save(self, name: str, df: pd.DataFrame, index: bool = False) -> None:
        self.tables[name] = df
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.tables_dir / f"{name}.csv", index=index)

    # --- shared inputs ----------------------------------------------------------------------------
    def axes(self, source: str = "street_axes") -> dict:
        """Street name -> axis, sorted by name. Features sharing a name (a street split into several) are merged."""
        name_field = self.case.cfg["axes"]["name_field"]
        parts: dict[str, list] = {}
        for f in features(load_json(self.case, source)):
            if f.get("geometry"):
                parts.setdefault(f["attributes"][name_field], []).append(to_line(f["geometry"]))
        return {k: v[0] if len(v) == 1 else linemerge(unary_union(v)) for k, v in sorted(parts.items())}

    def axis(self):
        cfg = self.case.cfg
        return geometry.street_axis(features(load_json(self.case, "street_axes")), cfg["axes"]["name_field"], cfg["street"]["name"])

    def classes(self) -> dict[str, set[str]]:
        return {r: self.case.classes(r) for r in ("road", "parking", "sidewalk", "plot")}


def run(case: Case, stages: list[str] | None = None, offline: bool = False, log=print) -> Run:
    stale = check_pins(case)
    if stale:
        raise RuntimeError(
            f"cached files do not match the sha256 pinned in case.toml: {stale}. "
            "Restore the pinned files (fetch --from-dir) or update the pin deliberately."
        )
    r = Run(case, offline=offline, log=log)
    facts_path = case.results_dir / "facts.json"
    if facts_path.exists():  # facts from earlier stages, so a partial re-run (--stages ...) has them
        r.facts = json.loads(facts_path.read_text())
    for st in stages or STAGES:
        if st == "area" and "area_scan" not in case.cfg:
            continue
        log(f"[{st}]")
        globals()[f"stage_{st}"](r)
        facts_path.write_text(json.dumps(r.facts, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    lock_identify_caches(case)
    return r


def _load_tables(r: Run, *names: str) -> None:
    for n in names:
        if n not in r.tables:
            r.tables[n] = pd.read_csv(r.tables_dir / f"{n}.csv")


# --- stages -----------------------------------------------------------------------------------------
def stage_profiles(r: Run) -> None:
    c, p = r.case, r.case.section("profiles")
    axis = r.axis()
    polys = geometry.classed_polygons(
        features(load_json(c, "cartography")), c.cfg["cartography"]["class_field"], set().union(*r.classes().values())
    )
    step = float(p.get("step_m", 0.5))
    df = geometry.measure_profiles(axis, polys, r.classes(), step=step, half_width=float(p.get("half_width_m", 25)))
    df = geometry.classify(df, c.blocks, narrow_max=float(p.get("narrow_max_m", 7.0)))
    r.save("profiles", df)
    r.save("summary_by_block", geometry.summarize_blocks(df, c.blocks))
    r.save("parking_strip_lengths", geometry.strip_lengths(df, c.blocks, step))
    narrow = geometry.narrow_sections(df, step)
    r.save("narrow_sections", pd.DataFrame(narrow, columns=["s_from", "s_to", "block"]))
    tr = Transformer.from_crs(c.crs, 4326, always_xy=True)
    pts = []
    for s in p.get("check_points_s", []):
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
    r.facts["length_m"] = round(axis.length, 2)
    lo, la = tr.transform(*axis.xy)
    (c.results_dir / "street_axis.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": c.cfg["street"]["name"], "length_m": round(axis.length, 2)},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[round(x, 7), round(y, 7)] for x, y in zip(lo, la, strict=True)],
                        },
                    }
                ],
            }
        )
    )


def stage_direction(r: Run) -> None:
    c, d = r.case, r.case.section("direction")
    if not d:
        return
    cache = IdentifyCache(c, d["source"], offline=r.offline)
    edges = network.edges_along(r.axis(), cache, c.cfg["network"], d["stations_s"], tolerance=c.source(d["source"]).get("tolerance", 6))
    cache.save()
    r.save("traffic_direction_edges", edges)
    r.facts["traffic"] = network.directions(edges, c.cfg["network"]["open_value"])


def stage_transit(r: Run) -> None:
    c, t = r.case, r.case.section("transit")
    feed = gtfs.Feed(raw_path(c, t["source"]))
    axis = r.axis()
    shapes = gtfs.shapes_along(feed, axis, c.crs, buffer_m=float(t.get("buffer_m", 12)))
    trips = gtfs.trips_on_shapes(feed, shapes)
    r.save("routes_on_street", gtfs.route_summary(trips))
    r.save("stops_near_street", gtfs.stops_near(feed, axis, c.crs))
    day = t["service_date"] if isinstance(t["service_date"], dt.date) else dt.date.fromisoformat(t["service_date"])
    passings = gtfs.reference_passings(feed, trips[trips.route_short_name.isin(t["routes"])], t["reference_stops"], day)
    r.save("passings", passings)
    tph = gtfs.trips_per_hour(passings)
    tph.columns = [c.heading_label(h) for h in tph.columns]
    r.save("trips_per_hour", tph, index=True)
    runtimes = []
    on_routes = trips[trips.route_short_name.isin(t["routes"])]
    for ref in sorted({str(s["stop_id"]) for s in t["reference_stops"]}):
        day_trips = on_routes[on_routes.trip_id.isin(passings[passings.ref_stop == ref].trip_id)]
        runtimes.append(gtfs.scheduled_runtimes(feed, on_routes, ref, c.crs) | {"scope": "all trips in the feed"})
        runtimes.append(gtfs.scheduled_runtimes(feed, day_trips, ref, c.crs) | {"scope": f"trips on {day}"})
    r.save("scheduled_runtimes", pd.DataFrame(runtimes))


def stage_envelope(r: Run) -> None:
    c, e = r.case, r.case.section("envelope")
    _load_tables(r, "summary_by_block")
    allrow = r.tables["summary_by_block"].set_index("block").loc["all"]
    free = {"min": float(allrow.free_min), "median": float(allrow.free_median), "p95": float(allrow.free_p95)}
    veh = envelope.load_vehicles(c.cfg.get("vehicles"))
    r.save("width_budget", envelope.width_budget(free, veh, e["scenarios"]))
    r.save("overhang_sensitivity", envelope.overhang_sensitivity(free["median"], veh, e["scenarios"]))


def stage_encounters(r: Run) -> None:
    t = r.case.section("transit")
    _load_tables(r, "passings", "narrow_sections")
    passings = r.tables["passings"].astype({"route_short_name": str, "arrival_time": str})
    length = r.facts.get("length_m") or round(r.axis().length, 2)
    speeds = [float(v) for v in t.get("speeds_kmh", [15, 20])]
    narrow = list(r.tables["narrow_sections"].itertuples(index=False, name=None))
    r.save("encounters_summary", encounters.summary(passings, length, speeds))
    detail = pd.concat([encounters.locate(encounters.encounters(passings, length, v), narrow) for v in speeds], ignore_index=True)
    r.save("encounters_detail", detail)
    r.save("encounters_by_pair", detail.groupby(["speed_kmh", "pair"]).size().rename("encounters_per_day").reset_index())
    # sensitivity: the slowest stop-to-stop speed implied by the service day's schedule (slower buses meet more often)
    _load_tables(r, "scheduled_runtimes")
    day_rows = r.tables["scheduled_runtimes"].query("scope != 'all trips in the feed'")
    if len(day_rows):
        v = float(day_rows.kmh_at_median_min.min())
        r.facts["encounters_at_schedule_speed"] = {"kmh": v, "per_day": len(encounters.encounters(passings, length, v))}


def stage_occurrences(r: Run) -> None:
    c, o = r.case, r.case.section("occurrences")
    if not o:
        return
    src = c.source(o["source"])
    files = sorted(raw_path(c, o["source"]).glob("*.csv"))
    pts = occurrences.load_points(files, src["columns"], c.crs)
    streets = r.axes()
    x0, y0, x1, y1 = r.axis().bounds
    w = float(o.get("window_m", 300))
    near = occurrences.attribute_to_streets(pts, streets, (x0 - w, y0 - w, x1 + w, y1 + w))
    rates = occurrences.rates_by_street(near, streets, o["filters"], float(o.get("max_dist_m", 12)), float(o.get("min_street_length_m", 0)))
    r.save("occurrences_by_street", rates)
    name, first = c.cfg["street"]["name"], next(iter(o["filters"].values()))
    yearly = occurrences.yearly_counts(near, name, first, float(o.get("max_dist_m", 12)))
    r.save("occurrences_by_year", yearly.rename_axis("year").rename("n").reset_index())
    r.facts["occurrences_period"] = [str(pts.date.min().date()), str(pts.date.max().date())]


def stage_area(r: Run) -> None:
    c, a = r.case, r.case.section("area_scan")
    t = c.section("transit")
    polys = geometry.classed_polygons(
        features(load_json(c, "area_cartography")), c.cfg["cartography"]["class_field"], c.classes("road") | c.classes("parking")
    )
    axes = [(n, g) for n, g in r.axes("area_axes").items()]
    env = c.source("area_cartography")["envelope"]
    (bx0, bx1), (by0, by1) = Transformer.from_crs(4326, c.crs, always_xy=True).transform([env[0], env[2]], [env[1], env[3]])
    feed = gtfs.Feed(raw_path(c, t["source"]))
    day = t["service_date"] if isinstance(t["service_date"], dt.date) else dt.date.fromisoformat(t["service_date"])
    shapes, n_trips, route_of = area_scan.bus_shapes(feed, day, c.crs, (bx0 - 50, by0 - 50, bx1 + 50, by1 + 50))
    step = float(a.get("step_m", 3))
    stations = area_scan.scan(axes, geometry.Profiler(polys), r.classes(), shapes, n_trips, route_of, step=step)
    r.save("area_stations", stations)
    cache = IdentifyCache(c, a["identify_source"], offline=r.offline) if a.get("identify_source") else None
    ranked = area_scan.rank_streets(
        stations,
        step,
        float(a.get("threshold_m", 5.5)),
        float(a.get("reference_m", 6.5)),
        cache,
        c.cfg.get("network"),
        c.cfg.get("network", {}).get("open_value", "Traversable"),
    )
    if cache:
        cache.save()
    r.save("area_streets", ranked)


def stage_standards(r: Run) -> None:
    _load_tables(r, "summary_by_block")
    med = float(r.tables["summary_by_block"].set_index("block").loc["all", "free_median"])
    r.save("standards_comparison", standards.compare(med, r.case.section("standards").get("compare", [])))


def stage_figures(r: Run) -> None:
    _load_tables(r, "summary_by_block", "trips_per_hour", "profiles", "width_budget")
    figures.make_all(r)


def stage_ledger(r: Run) -> None:
    report.write(r)
