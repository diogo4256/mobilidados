"""Draft a case for another street from an existing case of the same city (``mobilidados new-case``).

The draft extends the same file as the model case (in Lisbon, a dated data file such as
``cities/lisboa-2026-10.toml``), so the data pins, the service day, the vehicles, the parameters and the shared known
gaps are inherited, not copied. What depends on the street is derived from the data:

* the axis, found by name in the city's axes layer (the whole layer, not only the model case's area);
* the download envelopes around it, for the case and for the area scan;
* the blocks, cut where other named axes meet the street, labelled with their names;
* the labels of the two directions of travel and of the two sides, from the axis bearing;
* the check points (block midpoints) and the traffic-direction stations;
* the bus routes that run along the street on the service day, and one reference stop per route and direction:
  the stop near the street served by most of that direction's trips;
* the question and the gap about buses meeting, which depend on whether buses run both ways.

The draft is a starting point: its header lists what a person must check before the case is used, and states what
the draft assumed: the reference stops and their distance from the axis, compass labels that could be read either
way, and a question that supposes two-way traffic or two lanes when the buses run one way.
"""

from __future__ import annotations

import datetime as dt
import difflib
import json
import logging
import math
import os
import re
import tomllib
import unicodedata
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, get_args

import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString

from . import arcgis, geometry, gtfs
from .config import ArcgisQuery, Case, Lang, MobilidadosError
from .i18n import num, t
from .sources import raw_path

log = logging.getLogger(__name__)

AXIS_MARGIN_M = 150.0  # around the street's axis: the case's cartography and axes
AREA_MARGIN_M = 1200.0  # around the street's axis: the area scan
CUT_TOLERANCE_M = 5.0  # cross streets closer than this along the axis are one cut; nearer an end, they label it
STATION_SPACING_M = 25.0  # traffic-direction stations along the axis
STATION_END_M = 10.0  # stations keep this far from each end and each junction, where the identify would also find the cross street
STOP_RADIUS_M = 40.0  # reference stops are looked for this far from the axis
COMPASS_MARGIN_DEG = 10.0  # a bearing this close to the boundary between two compass points reads as either
COMPASS = {"pt": ["N", "NE", "E", "SE", "S", "SO", "O", "NO"], "en": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]}
ENDS = {"pt": ("início", "fim"), "en": ("start", "end")}
# words that do not tell one street from another, left out when looking for a street by a name that does not match
GENERIC_WORDS = {"RUA", "R", "AVENIDA", "AV", "TRAVESSA", "TV", "LARGO", "LG", "PRACA", "PC", "CALCADA", "ESTRADA", "BECO",
                 "ALAMEDA", "AL", "DE", "DA", "DO", "DAS", "DOS", "E"}  # fmt: skip
SUGGESTIONS = 5


def normalise(text: str) -> str:
    """Upper case, without accents or punctuation, single spaces: how two spellings of a street name are compared."""
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^A-Za-z0-9]+", " ", ascii_).upper().split())


def find_axis(src: ArcgisQuery, name_field: str, street: str, crs: int) -> tuple[str, LineString]:
    """The street's name as the axes layer spells it, and its axis.

    A name that matches no axis exactly is looked up by its most distinctive word; a single axis name equal to it
    but for case and accents is used, otherwise the closest names are suggested in the error.
    """
    quoted = street.replace("'", "''")
    found = arcgis.query_layer(src.url, None, in_sr=src.envelope_sr, out_sr=crs, where=f"{name_field} = '{quoted}'")["features"]
    if not found:
        words = normalise(street).split()
        word = max([w for w in words if w not in GENERIC_WORDS] or words or [""], key=len)
        pattern = re.sub("[AEIOU]", "_", word)  # '_' matches one character, accented or not
        like = arcgis.query_layer(src.url, None, in_sr=src.envelope_sr, out_sr=crs, where=f"UPPER({name_field}) LIKE '%{pattern}%'")
        names = sorted({str(f["attributes"][name_field]) for f in like["features"] if f["attributes"].get(name_field)})
        same = [n for n in names if normalise(n) == normalise(street)]
        if len(same) != 1:
            close = sorted(names, key=lambda n: -difflib.SequenceMatcher(None, normalise(n), normalise(street)).ratio())
            hint = f"; did you mean: {', '.join(repr(n) for n in close[:SUGGESTIONS])}?" if close else ""
            raise MobilidadosError(f"no axis named {street!r} in field {name_field}{hint}")
        log.info("using %r, as the axes layer spells it", same[0])
        street, found = same[0], [f for f in like["features"] if f["attributes"].get(name_field) == same[0]]
    return street, geometry.street_axis(found, name_field, street)


def slug(text: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def compass(bearing_deg: float, lang: str) -> str:
    names = COMPASS.get(lang, COMPASS["en"])
    return names[round((bearing_deg % 360) / 45) % 8]


def bearing(axis: LineString) -> float:
    """Bearing in degrees (0 = grid north, clockwise) from the first to the last point of the axis."""
    (x0, y0), (x1, y1) = axis.coords[0], axis.coords[-1]
    return math.degrees(math.atan2(x1 - x0, y1 - y0)) % 360


def labels(bearing_deg: float, lang: str) -> tuple[dict[str, str], dict[str, str]]:
    """Labels of the two directions of travel (increasing / decreasing s) and of the two sides (left / right)."""
    b = bearing_deg
    forward, back = compass(b, lang), compass(b + 180, lang)
    return {"+": f"{back}→{forward}", "-": f"{forward}→{back}"}, {"L": compass(b - 90, lang), "R": compass(b + 90, lang)}


def directions(axis: LineString, lang: str) -> tuple[dict[str, str], dict[str, str]]:
    return labels(bearing(axis), lang)


def other_reading(bearing_deg: float) -> tuple[float, float] | None:
    """When the bearing is within COMPASS_MARGIN_DEG of a boundary between two compass points (22.5° + k·45°), the
    boundary and the bearing of the point across it, whose labels read the street as well; otherwise None."""
    b = bearing_deg % 360
    boundary = 22.5 + 45 * round((b - 22.5) / 45)
    if abs(b - boundary) > COMPASS_MARGIN_DEG:
        return None
    lower, upper = boundary - 22.5, boundary + 22.5
    drafted = round(b / 45) % 8  # the point compass() gives
    other = upper if round(lower / 45) % 8 == drafted else lower
    return boundary % 360, other % 360


def crossings(axis: LineString, features: list[dict[str, Any]], name_field: str, name: str) -> list[tuple[float, str]]:
    """(s, name) where another named axis meets the street, sorted along it."""
    out = []
    for f in features:
        other = f["attributes"].get(name_field)
        if not other or other == name:
            continue
        hit = arcgis.to_line(f["geometry"]).intersection(axis.buffer(0.5))
        if hit.is_empty:
            continue
        for part in getattr(hit, "geoms", [hit]):
            out.append((round(axis.project(part.centroid), 2), str(other)))
    return sorted(set(out))


def blocks(length: float, cross: list[tuple[float, str]], lang: str) -> list[dict[str, Any]]:
    """Blocks between consecutive cuts, labelled 'A → B' with the cross streets at each end."""
    groups: list[list[tuple[float, str]]] = []
    for s, n in cross:
        if groups and s - groups[-1][-1][0] < CUT_TOLERANCE_M:
            groups[-1].append((s, n))
        else:
            groups.append([(s, n)])
    cuts = [(round(float(np.mean([s for s, _ in g])), 2), " / ".join(sorted({n for _, n in g}))) for g in groups]
    start_name = next((n for s, n in cuts if s < CUT_TOLERANCE_M), ENDS.get(lang, ENDS["en"])[0])
    end_name = next((n for s, n in cuts if s > length - CUT_TOLERANCE_M), ENDS.get(lang, ENDS["en"])[1])
    inner = [(s, n) for s, n in cuts if CUT_TOLERANCE_M <= s <= length - CUT_TOLERANCE_M]
    edges = [(0.0, start_name), *inner, (round(length, 2), end_name)]
    return [{"id": f"B{i}", "start": a, "end": b, "label": f"{na} → {nb}"} for i, ((a, na), (b, nb)) in enumerate(pairwise(edges), 1)]


def on_grid(s: float, step: float) -> float:
    return round(round(s / step) * step, 6)


def stations(length: float, junctions: list[float]) -> list[float]:
    """Traffic-direction stations every STATION_SPACING_M, away from the ends and the junctions."""
    if length <= 2 * STATION_END_M:
        return [round(length / 2, 1)]
    grid = np.arange(STATION_END_M, length - STATION_END_M + 1e-9, STATION_SPACING_M)
    kept = [round(float(s), 1) for s in grid if all(abs(s - j) >= STATION_END_M for j in junctions)]
    return kept or [round(length / 2, 1)]


def transit(feed: gtfs.Feed, axis: LineString, crs: int, day: dt.date, buffer_m: float) -> tuple[list[str], list[dict[str, Any]]]:
    """Routes running along the street on ``day`` and one reference stop per route and direction.

    Each stop also carries its name and its distance from the axis (``stop_name``, ``dist_m``), for the draft's
    header; they are not part of the case.
    """
    shapes = gtfs.shapes_along(feed, axis, crs, buffer_m=buffer_m)
    if shapes.empty:
        return [], []
    trips = gtfs.trips_on_shapes(feed, shapes[shapes.heading != 0])
    trips = trips[trips.service_id.isin(gtfs.active_service_ids(feed, day))]
    if trips.empty:
        return [], []
    near = gtfs.stops_near(feed, axis, crs, max_dist=STOP_RADIUS_M).set_index("stop_id")
    stop_times = feed.stop_times(set(trips.trip_id))
    stop_times = stop_times[stop_times.stop_id.isin(near.index)]
    refs = []
    for (route, direction_id, heading), g in trips.groupby(["route_short_name", "direction_id", "heading"]):
        served = stop_times[stop_times.trip_id.isin(g.trip_id)].groupby("stop_id").trip_id.nunique()
        if served.empty:
            continue
        ranked = sorted(served.index, key=lambda sid: (-served[sid], near.loc[sid, "dist_m"]))
        stop = ranked[0]
        refs.append(
            {
                "route": str(route),
                "direction_id": int(direction_id),
                "stop_id": str(stop),
                "s_m": float(near.loc[stop, "s_m"]),
                "heading": int(heading),
                "stop_name": str(near.loc[stop, "stop_name"]),
                "dist_m": float(near.loc[stop, "dist_m"]),
            }
        )
    counts = trips.groupby("route_short_name").size().sort_values(ascending=False)
    routes = [str(r) for r in counts.index if any(ref["route"] == str(r) for ref in refs)]
    return routes, refs


def envelope_around(axis: LineString, margin: float, crs: int) -> list[float]:
    x0, y0, x1, y1 = axis.bounds
    tr = Transformer.from_crs(crs, 4326, always_xy=True)
    (lon0, lon1), (lat0, lat1) = tr.transform([x0 - margin, x1 + margin], [y0 - margin, y1 + margin])
    return [round(lon0, 4), round(lat0, 4), round(lon1, 4), round(lat1, 4)]


CASE_STOP_KEYS = ("route", "direction_id", "stop_id", "s_m", "heading")  # what a reference stop holds in case.toml


@dataclass(frozen=True)
class Draft:
    data: dict[str, Any]  # the case.toml content
    out_dir: Path
    bearing_deg: float
    length_m: float = 0.0
    stops: tuple[dict[str, Any], ...] = ()  # the reference stops, with their name and distance from the axis
    one_way: bool = False  # buses run one way, so the question supposes a car beside the bus


def extends_path(city: Path, like_root: Path, out_dir: Path) -> str:
    """How the draft in ``out_dir`` refers to the model case's city file: relative while the draft stays inside the
    folder that holds both the model case and the city file (the repository, for Lisbon), so the two move together;
    absolute outside it, where a relative path would climb through unrelated folders and break when either moves."""
    project = Path(os.path.commonpath([city, like_root]))
    if out_dir.is_relative_to(project) and project != Path(project.anchor):
        return Path(os.path.relpath(city, out_dir)).as_posix()
    return city.as_posix()


def draft(like: Case, street: str, out_dir: Path | None) -> Draft:
    """The case for ``street``, derived from the model case ``like`` and the city's data. ``out_dir`` defaults to
    ``<city>-<street>`` next to the model case, named as the axes layer spells the street."""
    cfg = like.config
    axes_src = like.source(cfg.profiles.axes)
    if not isinstance(axes_src, ArcgisQuery):
        raise MobilidadosError(f"{like.id}: the axes source {cfg.profiles.axes!r} is not an ArcGIS layer, so streets cannot be looked up")
    name_field = cfg.axes.name_field
    street, axis = find_axis(axes_src, name_field, street, like.crs)
    out_dir = out_dir or like.root.parent / f"{cfg.city.id}-{slug(street)}"
    env, area_env = envelope_around(axis, AXIS_MARGIN_M, like.crs), envelope_around(axis, AREA_MARGIN_M, like.crs)
    nearby = arcgis.query_layer(axes_src.url, tuple(env), in_sr=4326, out_sr=like.crs)["features"]
    lang = like.lang
    headings, sides = directions(axis, lang)
    street_blocks = blocks(axis.length, crossings(axis, nearby, name_field, street), lang)

    data = tomllib.loads((like.root / "case.toml").read_text(encoding="utf-8"))
    if "extends" in data:
        data["extends"] = extends_path((like.root / data["extends"]).resolve(), like.root.resolve(), out_dir.resolve())
    data["case"] = {k: v for k, v in data["case"].items() if k not in ("reference_run", "question")} | {
        "id": out_dir.name,
        "title": f"{street} ({cfg.city.name})",
    }
    data.pop("known_gaps", None)  # the model case's own gaps are about its street; the city's are inherited
    data["street"] = {"name": street, "headings": headings, "sides": sides, "blocks": street_blocks}
    step = cfg.profiles.step_m
    data.setdefault("profiles", {})["check_points_s"] = [on_grid((b["start"] + b["end"]) / 2, step) for b in street_blocks]
    if cfg.direction:
        data.setdefault("direction", {})["stations_s"] = stations(axis.length, [b["start"] for b in street_blocks[1:]])
    stops: tuple[dict[str, Any], ...] = ()
    one_way = False
    if cfg.transit:
        feed_path = raw_path(like, cfg.transit.source)
        if not feed_path.exists():
            raise MobilidadosError(f"the GTFS feed of {like.id} is not downloaded: run `mobilidados fetch {like.root}` first")
        routes, refs = transit(gtfs.Feed(feed_path), axis, like.crs, cfg.transit.service_date, cfg.transit.buffer_m)
        if not refs:
            raise MobilidadosError(f"no bus route of the feed runs along {street!r} on {cfg.transit.service_date}")
        data.setdefault("transit", {}).update(routes=routes, reference_stops=[{k: r[k] for k in CASE_STOP_KEYS} for r in refs])
        both_ways = len({r["heading"] for r in refs}) == 2
        stops, one_way = tuple(refs), not both_ways
        data["case"]["question"] = t("draft.question_both" if both_ways else "draft.question_one", lang)
        if both_ways:
            data["known_gaps"] = [{lg: t("draft.gap_meeting", lg) for lg in get_args(Lang)}]

    sources = data.setdefault("sources", {})
    for sid in (cfg.profiles.cartography, cfg.profiles.axes):
        sources.setdefault(sid, {})["envelope"] = env
    if cfg.area_scan:
        for sid in (cfg.area_scan.cartography, cfg.area_scan.axes):
            sources.setdefault(sid, {})["envelope"] = area_env
    return Draft(data, out_dir, bearing(axis), axis.length, stops, one_way)


def header(d: Draft, model: str, date: str, lang: str) -> str:
    """The comment on top of a draft, in the case's language: what to check, and what the draft assumed."""
    street = d.data["street"]
    lines = [t("draft.header_intro", lang, model=model, date=date), t("draft.header_title", lang), t("draft.header_blocks", lang)]
    near = other_reading(d.bearing_deg)
    if near is None:
        lines.append(t("draft.header_compass", lang, bearing=f"{d.bearing_deg:.0f}"))
    else:
        boundary, other = near
        other_headings, other_sides = labels(other, lang)
        lines.append(
            t(
                "draft.header_compass_boundary",
                lang,
                bearing=num(d.bearing_deg, lang, 1),
                gap=num(abs((d.bearing_deg - boundary + 180) % 360 - 180), lang, 1),
                boundary=num(boundary, lang, 1),
                point=compass(d.bearing_deg, lang),
                other_point=compass(other, lang),
                headings=f"{street['headings']['+']} / {street['headings']['-']}",
                sides=f"{street['sides']['L']} / {street['sides']['R']}",
                other_headings=f"{other_headings['+']} / {other_headings['-']}",
                other_sides=f"{other_sides['L']} / {other_sides['R']}",
            )
        )
    if d.stops:
        lines.append(t("draft.header_transit", lang))
        for r in d.stops:
            lines.append(
                t(
                    "draft.header_stop",
                    lang,
                    route=r["route"],
                    direction_id=r["direction_id"],
                    heading=street["headings"]["+" if r["heading"] > 0 else "-"],
                    stop_id=r["stop_id"],
                    name=r["stop_name"],
                    dist=num(r["dist_m"], lang, 1),
                    s=num(r["s_m"], lang, 1),
                )
            )
        lines.append(t("draft.header_stop_note", lang, radius=f"{STOP_RADIUS_M:.0f}", length=num(d.length_m, lang, 1)))
        lines.append(t("draft.header_question", lang))
        if d.one_way:
            lines.append(t("draft.header_one_way", lang))
    lines.append(t("draft.header_inherited", lang, model=model))
    return "\n".join(line.strip("\n") for line in lines) + "\n"


# --- TOML ---------------------------------------------------------------------------------------------------
def _key(k: str) -> str:
    return k if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", k) else json.dumps(k, ensure_ascii=False)


def _value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int | float):
        return repr(v)
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{_key(k)} = {_value(x)}" for k, x in v.items()) + " }"
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v):
            return "[\n" + "".join(f"  {_value(x)},\n" for x in v) + "]"
        return "[" + ", ".join(_value(x) for x in v) + "]"
    raise TypeError(f"cannot write {type(v).__name__} to TOML")


def _table(name: str, d: dict[str, Any]) -> str:
    plain = {k: v for k, v in d.items() if not isinstance(v, dict) or k in ("headings", "sides", "filters", "columns")}
    nested = {k: v for k, v in d.items() if k not in plain}
    out = f"[{name}]\n" + "".join(f"{_key(k)} = {_value(v)}\n" for k, v in plain.items()) if plain or not nested else ""
    return out + "".join("\n" + _table(f"{name}.{_key(k)}", v) for k, v in nested.items())


def dumps(data: dict[str, Any], header: str) -> str:
    top = {
        k: v for k, v in data.items() if not isinstance(v, dict | list) or (isinstance(v, list) and not all(isinstance(x, dict) for x in v))
    }
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    arrays = {k: v for k, v in data.items() if isinstance(v, list) and v and all(isinstance(x, dict) for x in v)}
    parts = [header, "".join(f"{_key(k)} = {_value(v)}\n" for k, v in top.items())]
    parts += [_table(k, v) for k, v in tables.items()]
    parts += [
        "".join(f"[[{_key(k)}]]\n" + "".join(f"{_key(a)} = {_value(b)}\n" for a, b in x.items()) + "\n" for x in v)
        for k, v in arrays.items()
    ]
    return "\n".join(p.strip("\n") + "\n" for p in parts if p.strip())


def write(like: Case, street: str, out_dir: Path | None = None) -> Path:
    """Write ``<out_dir>/case.toml`` for ``street`` and check that it loads. Returns the case directory."""
    d = draft(like, street, out_dir)
    path = d.out_dir / "case.toml"
    if path.exists():
        raise MobilidadosError(f"{path} already exists")
    text = dumps(d.data, header(d, like.id, dt.date.today().isoformat(), like.lang))
    created = not d.out_dir.exists()
    d.out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    try:
        Case.load(d.out_dir)
    except MobilidadosError:
        path.unlink()
        if created:
            d.out_dir.rmdir()
        raise
    return d.out_dir
