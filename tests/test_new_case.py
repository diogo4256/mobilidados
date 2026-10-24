"""Drafting a case for another street from an existing case: the street's axis, blocks, labels and buses."""

import logging
import re
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
    assert "one direction only" not in text  # route 10 and route 20 run in opposite directions
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
    assert new_case.dumps({}, new_case.t("draft.header", "pt", model="m", date="d", bearing="9")).startswith(
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
