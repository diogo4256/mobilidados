"""Drafting a case for another street from an existing case: the street's axis, blocks, labels and buses."""

import tomllib

import pytest
from shapely.geometry import LineString

from mobilidados import new_case
from mobilidados.config import ArcgisQuery, Case, MobilidadosError
from mobilidados.new_case import blocks, directions, slug, stations, write
from tests.builders import CRS, LENGTH, at_origin, esri_path, layer_file, write_case


def test_directions_and_sides_follow_the_axis_bearing():
    assert directions(LineString([(0, 0), (100, 0)]), "pt") == ({"+": "O→E", "-": "E→O"}, {"L": "N", "R": "S"})
    assert directions(LineString([(0, 0), (70, 70)]), "en") == ({"+": "SW→NE", "-": "NE→SW"}, {"L": "NW", "R": "SE"})


def test_blocks_are_cut_at_the_cross_streets_and_named_after_them():
    cross = [(0.3, "Rua A"), (99.0, "Rua B"), (101.5, "Rua B2"), (200.0, "Rua C")]
    assert blocks(200.0, cross, "pt") == [
        {"id": "B1", "start": 0.0, "end": 100.25, "label": "Rua A → Rua B / Rua B2"},
        {"id": "B2", "start": 100.25, "end": 200.0, "label": "Rua B / Rua B2 → Rua C"},
    ]
    assert blocks(80.0, [], "en") == [{"id": "B1", "start": 0.0, "end": 80.0, "label": "start → end"}]


def test_traffic_direction_stations_keep_away_from_the_ends_and_the_junctions():
    assert stations(110.0, [55.0]) == [10.0, 35.0, 85.0]  # 60 m is 5 m from the junction
    assert stations(15.0, []) == [7.5]


def test_slug():
    assert slug("Rua Dr. António José d'Almeida") == "rua-dr-antonio-jose-d-almeida"


def axis(oid, name, *points):
    return {"attributes": {"OBJECTID": oid, "NAME": name}, "geometry": esri_path(at_origin(LineString(points)))}


# the city's axes layer as the drafter sees it: the street in two pieces, a cross street at 120 m and one at the start
CITY_AXES = [
    axis(1, "Rua do Teste", (0, 0), (120, 0)),
    axis(2, "Rua do Teste", (120, 0), (LENGTH, 0)),
    axis(3, "Rua Transversal", (120, -40), (120, 40)),
    axis(4, "Rua Inicial", (0, -40), (0, 40)),
    axis(5, "Rua Larga", (0, 80), (LENGTH, 80)),
]


@pytest.fixture
def city_layer(monkeypatch):
    calls = []

    def query_layer(url, envelope, in_sr, out_sr, where="1=1"):
        calls.append((envelope, where))
        assert out_sr == CRS
        feats = [f for f in CITY_AXES if where == "1=1" or f"= '{f['attributes']['NAME']}'" in where]
        return layer_file("Axes", feats)

    monkeypatch.setattr(new_case.arcgis, "query_layer", query_layer)
    return calls


def test_a_drafted_case_loads_and_carries_the_new_street(tmp_path, city_layer):
    like = Case.load(write_case(tmp_path / "like"))
    out = write(like, "Rua do Teste", tmp_path / "example-rua-do-teste")
    assert city_layer[0] == (None, "NAME = 'Rua do Teste'")  # looked up in the whole layer
    assert city_layer[1][1] == "1=1"  # then every axis around it
    assert city_layer[1][0] is not None

    case = Case.load(out)
    s = case.config.street
    assert (case.id, case.config.case.title) == ("example-rua-do-teste", "Rua do Teste (Example)")
    assert [(b.start, b.end, b.label) for b in s.blocks] == [
        (0.0, 120.0, "Rua Inicial → Rua Transversal"),
        (120.0, LENGTH, "Rua Transversal → end"),
    ]
    assert (s.headings, s.sides) == ({"+": "W→E", "-": "E→W"}, {"L": "N", "R": "S"})
    assert case.config.profiles.check_points_s == [60.0, 160.0]
    assert case.config.direction is not None
    assert case.config.direction.stations_s == [10.0, 35.0, 60.0, 85.0, 110.0, 135.0, 160.0, 185.0]  # 110 m is 10 m from the junction

    t, like_transit = case.config.transit, like.config.transit
    assert t is not None
    assert like_transit is not None
    assert t.routes == ["10", "20"]  # route 10 has more trips
    assert [(r.route, r.direction_id, r.stop_id, r.s_m, r.heading) for r in t.reference_stops] == [
        ("10", 0, "S1", 0.0, 1),
        ("20", 1, "S1", 0.0, -1),
    ]
    assert t.service_date == like_transit.service_date

    # the street's own downloads get an envelope around it, the area scan a wider one; pins are kept
    sources = {sid: case.source(sid) for sid in ("cartography", "street_axes", "area_cartography", "area_axes")}
    assert all(isinstance(src, ArcgisQuery) for src in sources.values())
    env = {sid: tuple(src.envelope) for sid, src in sources.items() if isinstance(src, ArcgisQuery)}
    assert env["cartography"] == env["street_axes"] != env["area_cartography"] == env["area_axes"]
    small, wide = env["cartography"], env["area_cartography"]
    assert wide[0] < small[0] < small[2] < wide[2]
    assert wide[1] < small[1] < small[3] < wide[3]
    assert case.source("feed") == like.source("feed")

    text = (out / "case.toml").read_text(encoding="utf-8")
    assert text.startswith("# Draft made by `mobilidados new-case` from synthetic-street")
    assert "(90° from grid north)" in text
    assert tomllib.loads(text)["known_gaps"] == tomllib.loads((like.root / "case.toml").read_text(encoding="utf-8"))["known_gaps"]


def test_drafting_refuses_to_overwrite_and_reports_a_street_without_buses(tmp_path, city_layer):
    like = Case.load(write_case(tmp_path / "like"))
    out = write(like, "Rua do Teste", tmp_path / "a")
    with pytest.raises(MobilidadosError, match="already exists"):
        write(like, "Rua do Teste", out)
    with pytest.raises(MobilidadosError, match="no bus route of the feed runs along 'Rua Larga'"):
        write(like, "Rua Larga", tmp_path / "b")
    assert not (tmp_path / "b" / "case.toml").exists()
    with pytest.raises(MobilidadosError, match="no axis named 'Rua Nenhuma'"):
        write(like, "Rua Nenhuma", tmp_path / "c")
