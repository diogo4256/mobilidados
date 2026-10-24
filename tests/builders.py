"""Synthetic inputs shared by the tests: a street with known widths, a GTFS feed along it and a whole case on disk.

The street runs east along y = ``ORIGIN[1]`` from x = ``ORIGIN[0]`` (projected CRS, metres). ``street`` builds its
cartography, ``make_feed`` the buses that run along it, and ``write_case`` a case folder whose cached sources are in
the formats ``mobilidados fetch`` stores, so a run needs neither network nor real data.
"""

import json
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient

from mobilidados.config import Case
from mobilidados.provenance import Lock, sha256_file
from mobilidados.sources import raw_path

CRS = 3763
ORIGIN = (-87500.0, -100700.0)
LENGTH = 200.0
SERVICE_DATE = "2026-10-27"  # a Tuesday


def street(free=4.90, strip=2.0, walk=2.5, length=100.0, strip_from=20.0, strip_to=80.0):
    """A straight street along +x: road centred on y=0, parking strips on both sides between strip_from and strip_to."""
    h = free / 2
    polys = [
        ("road", box(0, -h, length, h)),
        ("park", box(strip_from, h, strip_to, h + strip)),
        ("park", box(strip_from, -h - strip, strip_to, -h)),
        ("walk", box(0, h + strip, length, h + strip + walk)),
        ("walk", box(0, -h - strip - walk, length, -h - strip)),
        ("plot", box(0, h + strip + walk, length, h + strip + walk + 10)),
        ("plot", box(0, -h - strip - walk - 10, length, -h - strip - walk)),
    ]
    return LineString([(0, 0), (length, 0)]), polys


def make_feed(path):
    """Two routes along a 200 m street in Lisbon's projected CRS; route B only on Tuesdays via calendar_dates."""
    to_ll = Transformer.from_crs(CRS, 4326, always_xy=True)
    (lon0, lon1), (lat0, lat1) = to_ll.transform([-87500, -87300], [-100700, -100700])
    files = {
        "routes.txt": "route_id,route_short_name,route_long_name,route_type\nA,10,Up,3\nB,20,Down,3\n",
        "trips.txt": "route_id,service_id,trip_id,direction_id,shape_id\nA,WK,a1,0,up\nA,WK,a2,0,up\nB,X,b1,1,down\n",
        "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "WK,1,1,1,1,1,0,0,20260101,20261231\n",
        "calendar_dates.txt": "service_id,date,exception_type\nX,20261027,1\nWK,20261028,2\n",
        "shapes.txt": "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
        f"up,{lat0},{lon0},1\nup,{lat1},{lon1},2\ndown,{lat1},{lon1},1\ndown,{lat0},{lon0},2\n",
        "stops.txt": f"stop_id,stop_name,stop_lat,stop_lon\nS1,First,{lat0},{lon0}\nS2,Last,{lat1},{lon1}\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "a1,08:00:00,08:00:00,S1,1\na1,08:01:00,08:01:00,S2,2\n"
        "a2,09:00:00,09:00:00,S1,1\na2,09:01:00,09:01:00,S2,2\n"
        "b1,08:00:20,08:00:20,S2,1\nb1,08:01:20,08:01:20,S1,2\n",
    }
    with zipfile.ZipFile(path, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return LineString([(-87500, -100700), (-87300, -100700)])


# --- ESRI JSON, as ArcGIS returns it and ``mobilidados fetch`` stores it ------------------------------------------
def esri_polygon(poly: Polygon) -> dict[str, Any]:
    """Rings with the exterior clockwise, as ESRI JSON has it."""
    return {"rings": [[list(c) for c in orient(poly, sign=-1.0).exterior.coords]]}


def esri_path(line: LineString) -> dict[str, Any]:
    return {"paths": [[list(c) for c in line.coords]]}


def layer_file(name: str, features: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """The shape of ``arcgis.query_layer``'s result."""
    return {"name": name, "copyrightText": "", "spatialReference": {"wkid": CRS}, "fields": [], "features": list(features)}


def at_origin(geometry: BaseGeometry, dy: float = 0.0) -> Any:
    return affinity.translate(geometry, xoff=ORIGIN[0], yoff=ORIGIN[1] + dy)


# --- a whole case -------------------------------------------------------------------------------------------------
CASE_TOML = """
[case]
id = "synthetic-street"
title = "Synthetic street"
language = "en"
question = "Does the free width fit two buses?"

[city]
id = "example"
name = "Example"
crs = 3763

[cartography]
class_field = "LAYER"
road = ["road"]
parking = ["park"]
sidewalk = ["walk"]
plot = ["plot"]

[axes]
name_field = "NAME"

[street]
name = "{street}"
headings = {{ "+" = "east", "-" = "west" }}
sides = {{ L = "north", R = "south" }}
blocks = [{{ id = "B1", start = 0, end = 100 }}, {{ id = "B2", start = 100, end = 200 }}]

[profiles]
step_m = 1.0
check_points_s = [60.0, 120.0]

[[known_gaps]]
en = "No field observation of two buses meeting on this street."

[sources.cartography]
kind = "arcgis_query"
url = "https://example.org/arcgis/rest/services/Base/MapServer/1"
envelope = {envelope}
out_sr = 3763
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
dataset_page = "https://example.org/data/cartography"
attribution = "Example City Council"
redistributable = true

[sources.street_axes]
kind = "arcgis_query"
url = "https://example.org/arcgis/rest/services/Base/MapServer/2"
envelope = {envelope}
out_sr = 3763
licence = "not stated"

[sources.area_cartography]
kind = "arcgis_query"
url = "https://example.org/arcgis/rest/services/Base/MapServer/1"
envelope = {envelope}
out_sr = 3763
where = "LAYER IN ('road', 'park')"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
dataset_page = "https://example.org/data/cartography"
attribution = "Example City Council"
redistributable = true

[sources.area_axes]
kind = "arcgis_query"
url = "https://example.org/arcgis/rest/services/Base/MapServer/2"
envelope = {envelope}
out_sr = 3763
licence = "not stated"

[sources.network_identify]
kind = "arcgis_identify"
url = "https://example.org/arcgis/rest/services/Network/MapServer/identify"
layers = "all:1"
sr = 3763
licence = "not stated"

[sources.feed]
kind = "http_file"
url = "https://example.org/gtfs.zip"
suffix = ".zip"
licence = "not stated"
attribution = "Example Transit (GTFS)"
{pin}

[sources.reports]
kind = "http_files"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
attribution = "Example City Council"
columns = {{ lat = "latitude", lon = "longitude", date = "dt_registo", category = "tipologia" }}
files = [
  {{ name = "2024.csv", url = "https://example.org/2024.csv" }},
  {{ name = "2025.csv", url = "https://example.org/2025.csv" }},
]
"""

OPTIONAL_TOML = """
[network]
edge = "[EID]"
direction = "[Direction]"
status = "Oneway"
open_value = "Traversable"

[direction]
source = "network_identify"
stations_s = [10, 100, 190]

[transit]
source = "feed"
service_date = {date}
routes = ["10", "20"]
speeds_kmh = [15, 20]
reference_stops = [
  {{ route = "10", direction_id = 0, stop_id = "S1", s_m = 0.0, heading = 1 }},
  {{ route = "20", direction_id = 1, stop_id = "S2", s_m = 200.0, heading = -1 }},
]

[envelope]
bus = "bus_eu_max"
car = "car_typical"
scenarios = [["bus_eu_max"], ["bus_eu_max", "car_typical"], ["bus_eu_max", "bus_eu_max"]]

[occurrences]
source = "reports"
window_m = 300
max_dist_m = 12
min_street_length_m = 100
filters = {{ parking = "^Parking" }}

[area_scan]
cartography = "area_cartography"
axes = "area_axes"
identify_source = "network_identify"
step_m = 4
threshold_m = 5.5
reference_m = 6.5
min_pattern_m = 30

[standards]
compare = ["cml_manual_two_way_profile", "rast06_bus_bus"]
"""

TWO_WAY = [
    {"[EID]": "1", "[Direction]": "Along", "Oneway": "Traversable"},
    {"[EID]": "1", "[Direction]": "Against", "Oneway": "Traversable"},
]


def write_case(root: Path, street_name: str = "Rua do Teste", optional: bool = True) -> Path:
    """Write a complete case into ``root`` (the folder is created): ``case.toml``, the cached sources and the lock.

    Rua do Teste is 200 m long. It is a 4.90 m road with 2.00 m parking strips on both sides between 40.5 m and
    150.5 m (and sidewalks and plots beyond them), traffic is two-way, and two bus routes run along it in opposite
    directions: ``make_feed``'s. Rua Larga is parallel, 80 m to the north. Travessa Curta is a stub shorter than the
    case's ``min_street_length_m``. The reports (two files, each with its own date format) are mostly parking
    reports on Rua do Teste. With ``optional=False`` the case has only the sections every case needs (no transit,
    direction, envelope, occurrences, area scan or design references); the cached sources are written all the same.
    """
    root.mkdir()
    to_ll = Transformer.from_crs(CRS, 4326, always_xy=True)
    (lon0, lon1), (lat0, lat1) = to_ll.transform([ORIGIN[0] - 400, ORIGIN[0] + LENGTH + 400], [ORIGIN[1] - 400, ORIGIN[1] + 500])
    envelope = [round(lon0, 5), round(lat0, 5), round(lon1, 5), round(lat1, 5)]

    def toml(pin: str) -> str:
        text = CASE_TOML.format(street=street_name, envelope=envelope, pin=pin)
        return text + (OPTIONAL_TOML.format(date=SERVICE_DATE) if optional else "")

    (root / "case.toml").write_text(toml(""), encoding="utf-8")
    case = Case.load(root)
    case.raw_dir.mkdir(parents=True)

    def write_json(source: str, data: dict[str, Any]) -> None:
        raw_path(case, source).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _, local = street(length=LENGTH, strip_from=40.5, strip_to=150.5)
    features = [
        {"attributes": {"OBJECTID": i, "LAYER": cls}, "geometry": esri_polygon(at_origin(g))} for i, (cls, g) in enumerate(local, 1)
    ]
    features += [
        {
            "attributes": {"OBJECTID": 98, "LAYER": "tree"},
            "geometry": esri_polygon(at_origin(box(5, 30, 6, 31))),
        },  # not a class of the case
        {"attributes": {"OBJECTID": 99, "LAYER": "road"}},  # a feature without geometry
    ]
    write_json("cartography", layer_file("Polygons", features))
    write_json("area_cartography", layer_file("Polygons", [f for f in features if f["attributes"]["LAYER"] in ("road", "park")]))

    def axis(oid: int, name: str, *points: tuple[float, float], dy: float = 0.0) -> dict[str, Any]:
        return {"attributes": {"OBJECTID": oid, "NAME": name}, "geometry": esri_path(at_origin(LineString(points), dy))}

    write_json(
        "street_axes",
        layer_file(
            "Axes",
            [
                axis(1, "Rua do Teste", (0, 0), (LENGTH, 0)),
                axis(2, "Rua Larga", (0, 0), (LENGTH, 0), dy=80),
                axis(3, "Travessa Curta", (100, -10), (100, -90)),
            ],
        ),
    )
    # the same street split in two features, which the area scan merges back
    write_json(
        "area_axes",
        layer_file(
            "Axes",
            [
                axis(1, "Rua do Teste", (0, 0), (100, 0)),
                axis(2, "Rua do Teste", (100, 0), (LENGTH, 0)),
                axis(3, "Rua Larga", (0, 0), (LENGTH, 0), dy=80),
            ],
        ),
    )

    stations = [f"{ORIGIN[0] + s:.0f},{ORIGIN[1]:.0f}" for s in (10, 100, 190)]  # the keys sources.IdentifyCache builds
    every_metre = [f"{x},{ORIGIN[1]:.0f}" for x in range(int(ORIGIN[0]), int(ORIGIN[0] + LENGTH) + 1)]  # wherever the area scan asks
    write_json("network_identify", dict.fromkeys(stations + every_metre, TWO_WAY))

    make_feed(raw_path(case, "feed"))

    def report(n: int, x: float, y: float, kind: str, when: str) -> str:
        lon, lat = to_ll.transform(ORIGIN[0] + x, ORIGIN[1] + y)
        return f"OCO/{n},{when},Category,{kind},{lat:.7f},{lon:.7f}\n"

    head = "numero,dt_registo,categoria,tipologia,latitude,longitude\n"
    reports = raw_path(case, "reports")
    reports.mkdir()
    (reports / "2024.csv").write_text(
        head
        + report(1, 20, 3, "Parking on the pavement", "2024-03-05 10:11:12.000")
        + report(2, 60, -3, "Parking on the pavement", "2024-05-17 18:30:00.000")
        + report(3, 100, 3, "Parking on the pavement", "2024-11-02 07:05:59.000")
        + report(4, 140, 3, "Litter", "2024-11-03 09:00:00.000")
        + report(5, 50, 80 + 3, "Parking on the pavement", "2024-06-01 12:00:00.000")
        + report(6, 100, -80, "Parking on the pavement", "2024-06-02 12:00:00.000"),  # on Travessa Curta
        encoding="utf-8",
    )
    (reports / "2025.csv").write_text(
        head
        + report(7, 30, -3, "Parking on the pavement", "2025-01-20")
        + report(8, 160, 3, "Parking on the pavement", "2025-06-30")
        + report(9, 90, 80 - 3, "Parking on the pavement", "2025-07-01")
        + report(10, 120, 20, "Parking on the pavement", "2025-07-02")  # 20 m from the axis: attributed but too far to count
        + report(11, 5000, 5000, "Parking on the pavement", "2025-07-03")  # outside the window around the street
        + "OCO/12,2025-07-04,Category,Parking on the pavement,,\n",  # no coordinates
        encoding="utf-8",
    )

    pin = f'sha256 = "{sha256_file(raw_path(case, "feed"))}"'
    (root / "case.toml").write_text(toml(pin), encoding="utf-8")
    case = Case.load(root)
    lock = Lock(case.lock_path)
    for sid, src in case.config.sources.items():
        path = raw_path(case, sid)
        files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
        lock.record(sid, files, case.raw_dir, kind=src.kind, retrieved_utc="2026-10-24T12:00:00+00:00", licence=src.licence)
    lock.save()
    return root
