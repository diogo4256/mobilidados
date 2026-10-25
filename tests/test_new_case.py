"""Drafting a case for another street from an existing case: the street's axis, blocks, labels and buses."""

import datetime as dt
import logging
import re
import tomllib

import pytest
from shapely.geometry import LineString, Point

from mobilidados import gtfs, new_case
from mobilidados.config import ArcgisQuery, Case, MobilidadosError
from mobilidados.new_case import blocks, compass, directions, other_reading, slug, stations, write
from tests.builders import CRS, LENGTH, at_origin, esri_path, layer_file, make_feed, write_case


def test_directions_and_sides_follow_the_axis_bearing():
    assert directions(LineString([(0, 0), (100, 0)]), "pt") == ({"+": "O→E", "-": "E→O"}, {"L": "N", "R": "S"})
    assert directions(LineString([(0, 0), (70, 70)]), "en") == ({"+": "SW→NE", "-": "NE→SW"}, {"L": "NW", "R": "SE"})


def test_a_bearing_near_a_boundary_between_compass_points_has_another_reading():
    def readings(b):
        near = other_reading(b)
        return near and (near[0], compass(b, "en"), compass(near[1], "en"))

    assert readings(68.7) == (67.5, "E", "NE")  # Rua Ricardo Jorge: 1.2° from the NE/E boundary
    assert readings(66.0) == (67.5, "NE", "E")
    assert readings(12.6) == (22.5, "N", "NE")  # 9.9° away
    assert readings(12.4) is None  # 10.1° away
    assert readings(90.0) is None
    assert readings(337.6) == (337.5, "N", "NW")  # across north
    assert readings(-22.0) == (337.5, "N", "NW")
    on = other_reading(202.5)  # on the boundary: the reading compass() did not pick
    assert on is not None
    assert on[0] == 202.5
    assert {compass(202.5, "en"), compass(on[1], "en")} == {"S", "SW"}


def flat(text):
    """A draft's header with its wrapped comment lines joined, to check sentences that wrap."""
    return re.sub(r"\n#   (?=\S)", " ", text)


def draft_in_portuguese(monkeypatch, like, out):
    """The header of a draft from ``like`` as a case in Portuguese would have it (the synthetic case is in English)."""
    monkeypatch.setattr(Case, "lang", property(lambda self: "pt"))
    return flat((write(like, "Rua do Teste", out) / "case.toml").read_text(encoding="utf-8"))


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
        if "LIKE" in where:  # the lookup by the most distinctive word; the drafter ranks what comes back
            word = where.split("'%")[1].split("%'")[0]
            feats = [f for f in CITY_AXES if re.search(word.replace("_", "."), new_case.normalise(f["attributes"]["NAME"]))]
        else:
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
    header = flat(text)
    assert "compass labels from the axis bearing (90° from grid north), which may need judgement;" in header
    assert "boundary" not in header
    # the reference stops, with their distance from the axis and position along it
    assert "route 10 heading W→E (direction_id 0): stop S1 (First), 0.0 m from the axis, s = 0.0 m;" in header
    assert "route 20 heading E→W (direction_id 1): stop S1 (First), 0.0 m from the axis, s = 0.0 m;" in header
    assert (
        "A stop within 40 m of the axis may be on a cross street near one end; its position s is then that end's (0 or 200.0 m)." in header
    )
    assert set(tomllib.loads(text)["transit"]["reference_stops"][0]) == {"route", "direction_id", "stop_id", "s_m", "heading"}
    assert "one-way" not in header  # route 10 and route 20 run in opposite directions
    # buses run both ways, so the question and the gap are about two buses meeting
    assert (
        case.config.case.question
        == "Does the free width between the two parking strips let two scheduled buses pass each other in opposite directions?"
    )
    assert tomllib.loads(text)["known_gaps"] == [
        {
            "en": "No field observation of two buses meeting on this street: encounters are timetable estimates.",
            "pt": "Não há observação de campo de dois autocarros a cruzar-se nesta rua: os encontros são estimativas do horário.",
        }
    ]


SHARED = {"case", "street"}  # tables that are the case's own; everything else moves to the city file


def split(root):
    """Rewrite a synthetic case the way Lisbon is laid out: the case keeps its street, a city file the rest."""
    data = tomllib.loads((root / "case.toml").read_text(encoding="utf-8"))
    own = {k: data.pop(k) for k in SHARED} | {
        "profiles": {"check_points_s": data["profiles"].pop("check_points_s")},
        "direction": {"stations_s": data["direction"].pop("stations_s")},
        "transit": {k: data["transit"].pop(k) for k in ("routes", "reference_stops")},
        "sources": {
            sid: {"envelope": data["sources"][sid].pop("envelope")}
            for sid in ("cartography", "street_axes", "area_cartography", "area_axes")
        },
        "known_gaps": data.pop("known_gaps"),
    }
    (root.parent / "city.toml").write_text(new_case.dumps(data, "# city\n"), encoding="utf-8")
    (root / "case.toml").write_text(new_case.dumps({"extends": "../city.toml"} | own, "# case\n"), encoding="utf-8")


def test_a_draft_from_a_case_that_extends_a_city_file_holds_only_the_street(tmp_path, city_layer):
    root = write_case(tmp_path / "like")
    before = Case.load(root).config
    split(root)
    like = Case.load(root)
    assert like.config == before  # the split changes nothing in the loaded configuration

    out = write(like, "Rua do Teste", tmp_path / "example-rua-do-teste")
    data = tomllib.loads((out / "case.toml").read_text(encoding="utf-8"))
    assert data["extends"] == "../city.toml"
    assert set(data) == {"extends", "case", "street", "profiles", "direction", "transit", "sources", "known_gaps"}
    assert set(data["sources"]) == {"cartography", "street_axes", "area_cartography", "area_axes"}
    assert all(set(spec) == {"envelope"} for spec in data["sources"].values())
    assert Case.load(out).source("feed") == like.source("feed")  # the pinned feed comes from the city file


def test_a_draft_writes_its_envelopes_in_the_spatial_reference_it_inherits(tmp_path, city_layer):
    root = write_case(tmp_path / "like")
    text = (root / "case.toml").read_text(encoding="utf-8")
    (root / "case.toml").write_text(text.replace("out_sr = 3763", "envelope_sr = 3763\nout_sr = 3763"), encoding="utf-8")
    split(root)  # the city file gives the layers' envelope_sr, the draft only their envelopes
    out = write(Case.load(root), "Rua do Teste", tmp_path / "example-rua-do-teste")
    src = Case.load(out).source("cartography")
    assert isinstance(src, ArcgisQuery)
    assert src.envelope_sr == 3763
    x0, y0 = at_origin(Point(0, 0)).coords[0]
    assert src.envelope == pytest.approx((x0 - 150, y0 - 150, x0 + LENGTH + 150, y0 + 150))  # new_case.AXIS_MARGIN_M around the axis
    assert city_layer[1][0] == pytest.approx(src.envelope)  # the axes around the street are queried with the same envelope


def test_a_draft_outside_the_repository_extends_the_city_file_by_absolute_path(tmp_path, tmp_path_factory, city_layer):
    root = write_case(tmp_path / "like")
    split(root)
    like = Case.load(root)
    inside = tomllib.loads((write(like, "Rua do Teste", tmp_path / "a") / "case.toml").read_text(encoding="utf-8"))
    assert inside["extends"] == "../city.toml"
    elsewhere = tmp_path_factory.mktemp("elsewhere") / "b"
    outside = tomllib.loads((write(like, "Rua do Teste", elsewhere) / "case.toml").read_text(encoding="utf-8"))
    assert outside["extends"] == (tmp_path / "city.toml").resolve().as_posix()
    assert Case.load(elsewhere).source("feed") == like.source("feed")


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


def test_a_name_spelled_differently_is_matched_or_answered_with_suggestions(tmp_path, city_layer, caplog):
    caplog.set_level(logging.INFO, logger="mobilidados.new_case")
    like = Case.load(write_case(tmp_path / "like"))
    out = write(like, "rua do téste", tmp_path / "x")  # only case and accents differ: the layer's spelling is used
    assert Case.load(out).config.street.name == "Rua do Teste"
    assert "using 'Rua do Teste', as the axes layer spells it" in caplog.text
    with pytest.raises(MobilidadosError, match=r"no axis named 'R\. Teste' in field NAME; did you mean: 'Rua do Teste'\?"):
        write(like, "R. Teste", tmp_path / "y")
    with pytest.raises(MobilidadosError, match=r"no axis named 'Rua Nenhuma' in field NAME$"):
        write(like, "Rua Nenhuma", tmp_path / "z")


def test_the_default_folder_is_named_after_the_layers_spelling(tmp_path, city_layer):
    like = Case.load(write_case(tmp_path / "like"))
    assert write(like, "RUA DO TESTE") == tmp_path / "example-rua-do-teste"


def test_the_draft_header_is_in_the_cases_language(tmp_path, city_layer):
    like = Case.load(write_case(tmp_path / "like"))
    assert new_case.dumps({}, new_case.t("draft.header_intro", "pt", model="m", date="d")).startswith(
        "# Rascunho feito por `mobilidados new-case` a partir de m, em d. Confirme antes de usar:"
    )
    text = (write(like, "Rua do Teste", tmp_path / "x") / "case.toml").read_text(encoding="utf-8")
    assert text.startswith("# Draft made by `mobilidados new-case` from synthetic-street on ")  # the synthetic case is in English


def test_a_draft_that_does_not_load_leaves_nothing_behind(tmp_path, city_layer, monkeypatch):
    like = Case.load(write_case(tmp_path / "like"))

    def refuse(case_dir, results_dir=None):
        raise MobilidadosError("invalid configuration")

    monkeypatch.setattr(new_case.Case, "load", refuse)
    with pytest.raises(MobilidadosError, match="invalid configuration"):
        write(like, "Rua do Teste", tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_a_draft_for_buses_one_way_says_the_question_may_not_apply(tmp_path, city_layer, monkeypatch):
    monkeypatch.setattr(new_case.gtfs, "active_service_ids", lambda feed, day: {"WK"})  # route 20 does not run
    like = Case.load(write_case(tmp_path / "like"))
    out = write(like, "Rua do Teste", tmp_path / "x")
    assert Case.load(out).config.case.question == (
        "Does the free width between the two parking strips leave room for a scheduled bus and a car side by side?"
    )
    header = flat((out / "case.toml").read_text(encoding="utf-8"))
    assert "route 10 heading W→E (direction_id 0): stop S1 (First)" in header
    assert "route 20" not in header
    assert (
        "If the street is one-way with a single lane, the question does not apply as written: "
        "rewrite it once `mobilidados run` shows the direction of traffic." in header
    )

    pt = draft_in_portuguese(monkeypatch, like, tmp_path / "y")
    assert "carreira 10 no sentido O→E (direction_id 0): paragem S1 (First), a 0,0 m do eixo, s = 0,0 m;" in pt
    assert (
        "Se a rua tiver um só sentido e uma só via, a pergunta não se aplica tal como está: "
        "reescreva-a depois de o `mobilidados run` mostrar o sentido do trânsito." in pt
    )


def test_a_direction_whose_trips_run_the_street_both_ways_gets_one_reference_stop(tmp_path):
    # a variant of route 10, direction 0, that runs the street the other way (west)
    axis = make_feed(
        tmp_path / "f.zip", more_trips="A,WK,a3,0,down\n", more_stop_times="a3,10:00:00,10:00:00,S2,1\na3,10:01:00,10:01:00,S1,2\n"
    )
    _, refs = new_case.transit(gtfs.Feed(tmp_path / "f.zip"), axis, CRS, dt.date(2026, 10, 27), buffer_m=12)
    assert [(r["route"], r["direction_id"], r["heading"]) for r in refs] == [("10", 0, 1), ("20", 1, -1)]  # most trips run east


def test_a_bearing_near_a_compass_boundary_is_named_with_both_readings(tmp_path, city_layer, monkeypatch):
    monkeypatch.setattr(new_case, "bearing", lambda axis: 68.7)  # as Rua Ricardo Jorge's
    like = Case.load(write_case(tmp_path / "like"))
    out = write(like, "Rua do Teste", tmp_path / "x")
    assert Case.load(out).config.street.headings == {"+": "W→E", "-": "E→W"}
    header = flat((out / "case.toml").read_text(encoding="utf-8"))
    assert (
        "the axis bearing is 68.7° from grid north, only 1.2° from the boundary between E and NE (67.5°). "
        "The draft reads the street as E (headings W→E / E→W, sides N / S), but reading it as NE "
        "(headings SW→NE / NE→SW, sides NW / SE) is just as valid." in header
    )
    assert "which may need judgement" not in header

    pt = draft_in_portuguese(monkeypatch, like, tmp_path / "y")
    assert (
        "o eixo está orientado a 68,7° do norte da quadrícula, a só 1,2° do limite entre E e NE (67,5°). "
        "O rascunho lê a rua como E (sentidos O→E / E→O, lados N / S), mas lê-la como NE "
        "(sentidos SO→NE / NE→SO, lados NO / SE) é igualmente válido." in pt
    )
