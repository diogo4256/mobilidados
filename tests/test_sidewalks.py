"""Sidewalks against the free path of the accessibility law: what the mapped width can show, and what it cannot."""

import json

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, box

from mobilidados.config import Case, MobilidadosError, standards_catalogue
from mobilidados.geometry import Profiler, drop_slivers, measure_profiles
from mobilidados.letter import compose
from mobilidados.lint import lint_text
from mobilidados.pipeline import run
from mobilidados.sidewalks import allowed_width, away_from_junctions, away_from_widenings, narrow_sections, scan_area, summary

from .builders import PINCH, street, write_case

CLASSES = {"road": {"road"}, "parking": {"park"}, "sidewalk": {"walk"}, "plot": {"plot"}, "overhead": {"arcade"}, "yard": {"yard"}}
SHORT = [(0.6, 0.8), (1.5, 0.9)]  # Decree-Law 163/2006, section 4.3.3: (longest stretch, narrowest width)


def at(polys, s=50.0):
    """The station at ``s`` of a 100 m street along +x."""
    return measure_profiles(LineString([(0, 0), (100, 0)]), polys, CLASSES, step=1.0).set_index("s").loc[s]


def lane(y0, y1, cls="walk"):
    return (cls, box(0, y0, 100, y1))


ROAD = ("road", box(0, -3, 100, 3))


def test_the_catalogue_holds_the_law_as_published():
    refs = standards_catalogue()
    free, doc = refs.reference("dl163_free_path")
    assert (free.value_m, free.kind, free.page) == (1.20, "legal_requirement", 5686)
    assert "1,2 m" in free.quote
    assert doc.document_sha256 == "5b800bfbee2efde7d768e77c9193dc0643b0a35b7aae96cef1c59f6436a617a1"
    short = sorted((r.max_length_m, r.value_m) for r, _ in map(refs.reference, ["dl163_short_060", "dl163_short_150"]))
    assert short == SHORT


def test_a_sidewalk_from_the_kerb_to_the_buildings_is_measured_and_bounded():
    row = at([ROAD, lane(3, 4.1), lane(4.1, 20, "plot"), lane(-4, -3), lane(-20, -4, "plot")])
    assert (row.walk_L, row.walk_L_bounded, row.walk_R, row.walk_R_bounded) == (pytest.approx(1.1), True, pytest.approx(1.0), True)


def test_a_sidewalk_cut_by_a_tree_pit_is_walked_on_its_widest_piece():
    row = at([ROAD, lane(3, 3.6), ("pit", box(0, 3.6, 100, 4.4)), lane(4.4, 5.9), lane(5.9, 20, "plot")])
    assert row.walk_L == pytest.approx(1.5)
    assert row.walk_L_bounded


def test_a_median_between_carriageways_is_not_a_sidewalk():
    row = at([ROAD, lane(3, 4), ("road", box(0, 4, 100, 10)), lane(10, 13), lane(13, 20, "plot")])
    assert pd.isna(row.walk_L)


def test_an_island_bounded_by_a_yard_with_a_carriageway_behind_it_is_not_a_sidewalk():
    row = at([ROAD, lane(3, 3.4), lane(3.4, 8, "plot"), ("road", box(0, 9, 100, 15))])
    assert pd.isna(row.walk_L)


def test_a_sidewalk_ending_under_an_arcade_has_an_unknown_width():
    row = at([ROAD, lane(3, 3.5), ("arcade", box(0, 3.5, 100, 8)), ("plot", box(0, 3.5, 100, 20))])
    assert pd.isna(row.walk_L)


def test_a_sidewalk_ending_at_a_yard_or_at_nothing_mapped_is_to_check_not_bounded():
    yard = at([ROAD, lane(3, 3.8), ("yard", box(0, 3.8, 100, 9)), ("plot", box(0, 3.8, 100, 9))])
    open_ = at([ROAD, lane(3, 3.8)])
    assert yard.walk_L == pytest.approx(0.8)
    assert open_.walk_L == pytest.approx(0.8)
    assert not yard.walk_L_bounded
    assert not open_.walk_L_bounded


def test_slivers_are_neither_sidewalks_nor_pieces_of_one():
    sliver = ("walk", box(0, 3, 100, 3.05))
    assert [c for c, _ in drop_slivers([ROAD, sliver, lane(3.05, 5)], {"walk"}, 0.3)] == ["road", "walk"]
    row = at([ROAD, lane(3, 3.2), lane(3.2, 20, "plot")])  # a 20 cm piece read on a transect
    assert pd.isna(row.walk_L)


@pytest.mark.parametrize(
    ("length", "expected"),
    [(0.5, 0.8), (0.6, 0.8), (1.0, 0.9), (1.5, 0.9), (2.0, 1.2)],
)
def test_the_law_admits_a_narrower_stretch_only_if_it_is_short(length, expected):
    assert allowed_width(length, 1.2, SHORT) == expected


def profiles(widths, bounded=True, step=0.5):
    """Stations every ``step`` m with the left sidewalk ``widths`` (the right one wide), all bounded or all open."""
    s = np.arange(len(widths)) * step
    return pd.DataFrame(
        {
            "s": s,
            "x": s,
            "y": 0.0,
            "block": "B1",
            "walk_L": widths,
            "walk_L_bounded": bounded,
            "walk_R": 3.0,
            "walk_R_bounded": True,
        }
    )


def sections(widths, bounded=True):
    p = profiles(widths, bounded)
    return narrow_sections(p, 0.5, float(p.s.max()) + 0.5, 1.2, SHORT, 0.3)


def test_short_narrow_stretches_are_judged_by_their_length():
    wide = [2.0] * 4
    one_station = sections([*wide, 0.85, *wide])  # 0.5 m long at 0.85 m: the law admits 0.80 m there
    assert one_station.below.tolist() == [False]
    three = sections(wide + [0.95] * 3 + wide)  # 1.5 m at 0.95 m: admitted (0.90 m)
    assert three.below.tolist() == [False]
    four = sections(wide + [0.95] * 4 + wide)  # 2.0 m at 0.95 m: below 1.2 m
    assert four.below.tolist() == [True]
    assert four.length_m.tolist() == [2.0]
    assert four.allowed_m.tolist() == [1.2]


def test_a_stretch_below_even_with_the_cartographys_accuracy_is_told_apart():
    s = sections([2.0, 0.5, 0.5, 0.5, 0.5, 2.0, 0.7, 0.7, 0.7, 0.7, 2.0])
    assert s.below.tolist() == [True, True]
    assert s.below_with_accuracy.tolist() == [True, False]  # 0.5 + 2 × 0.3 < 1.2; 0.7 + 0.6 is not


def test_a_sidewalk_that_does_not_reach_the_buildings_is_never_below_the_law_only_to_check():
    assert sections([2.0, 0.5, 0.5, 0.5, 0.5, 2.0], bounded=False).empty
    table = summary(profiles([2.0, 0.5, 0.5, 0.5, 0.5, 2.0], bounded=False), [], 0.5, 3.0, [1.2]).set_index(["side", "block"])
    assert table.loc[("L", "all"), "metres_below_1.2m"] == 0
    assert table.loc[("L", "all"), "metres_open_below_1.2m"] == pytest.approx(2.0)


def test_junctions_and_widenings_are_left_unmeasured():
    p = profiles([0.5] * 41)  # 20 m
    near = away_from_junctions(p, [0.0, 20.0], 5.0)
    assert near.walk_L.notna().sum() == 19  # 5.5 m to 14.5 m
    wide = away_from_widenings(p.assign(kerb_to_kerb=[9.0] * 30 + [20.0] * 11))
    assert wide.walk_L.notna().sum() == 30


def test_the_area_scan_lists_a_street_whose_sidewalk_a_building_narrows():
    axis, polys = street(length=100.0, strip_from=20, strip_to=80)
    north = polys[3][1]
    building = box(40, north.bounds[1] + 0.5, 50, north.bounds[3])
    polys[3] = ("walk", north.difference(building))
    polys.append(("plot", building))
    found = scan_area([("Rua A", axis)], Profiler(polys), CLASSES, 1.0, 1.2, SHORT, 0.3, 10.0)
    row = found.set_index("street").loc["Rua A"]
    assert row.sections_below == 1
    assert row.metres_below == pytest.approx(10.0, abs=1.0)
    assert row.narrowest_m == pytest.approx(0.5)
    assert row.metres_below_with_accuracy == pytest.approx(row.metres_below)


@pytest.fixture(scope="module")
def sidewalk_case(tmp_path_factory):
    case = Case.load(write_case(tmp_path_factory.mktemp("sidewalks") / "case", sidewalks=True))
    run(case, offline=True)
    return case


def test_a_run_finds_the_pinch_states_the_law_and_names_the_street_in_the_area(sidewalk_case):
    tables = sidewalk_case.results_dir / "tables"
    sec = pd.read_csv(tables / "sidewalk_narrow_sections.csv")
    x0, x1, left = PINCH
    pinch = sec[sec.below]
    assert pinch.side.tolist() == ["L"]
    assert pinch.width_min_m.tolist() == [pytest.approx(left)]
    assert (pinch.s_from.iloc[0], pinch.s_to.iloc[0]) == (pytest.approx(x0 + 1, abs=1), pytest.approx(x1 - 1, abs=1))
    findings = {f["id"]: f for f in json.loads((sidewalk_case.results_dir / "findings.json").read_text())["findings"]}
    assert findings["sidewalks_law"]["grade"] == "D"
    assert findings["sidewalks_narrow"]["grade"] == "I"
    assert findings["sidewalks_narrow"]["values"]["sections_below_with_accuracy"] == 1
    assert "north side, s = " in findings["sidewalks_narrow"]["statement"]
    assert findings["sidewalks_area"]["values"]["below_with_accuracy"] == ["Rua do Teste"]
    assert (sidewalk_case.results_dir / "figures" / "sidewalk_profile.png").exists()
    screening = (sidewalk_case.results_dir / "screening.md").read_text()
    assert "Rua do Teste" in screening.split("## Sidewalks")[1]


def test_the_sidewalk_letter_lists_the_pinch_and_passes_lint(sidewalk_case):
    text = compose(sidewalk_case, "sidewalks")
    assert lint_text(text, "en") == []
    assert "north side, s = " in text.split("### Attachments")[1]
    assert "`sidewalks_law`" in text


def test_sidewalks_need_the_sidewalk_classes_and_known_references(make_case):
    with pytest.raises(MobilidadosError, match=r"\[sidewalks\] needs the sidewalk class codes"):
        Case.load(make_case("[sidewalks]\n"))
    root = make_case("[sidewalks]\nfree_path = 'nope'\nshort = ['dl163_free_path']\n", name="b")
    toml = root / "case.toml"
    toml.write_text(toml.read_text().replace('parking = ["park"]', 'parking = ["park"]\nsidewalk = ["walk"]'))
    with pytest.raises(MobilidadosError, match=r"sidewalks\.free_path: unknown reference 'nope'") as err:
        Case.load(root)
    assert "sidewalks.short: 'dl163_free_path' has no max_length_m" in str(err.value)


def test_screen_command_lists_the_streets_to_look_at(sidewalk_case, capsys):
    from mobilidados.cli import main

    assert main(["screen", str(sidewalk_case.root), "--offline"]) == 0
    out = capsys.readouterr().out
    assert "sidewalks" in out
    assert "Rua do Teste" in out
    assert "screening.md" in out
