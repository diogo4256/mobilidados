"""The whole pipeline on a synthetic case: every stage runs offline and the results say what the built street implies.

``builders.write_case`` documents the street and the services around it. Nothing here needs the network or the
cached Lisbon sources, so the pipeline, the ledger, the figures and the area scan run in the unit suite.
"""

import json

import pandas as pd
import pytest

from mobilidados import cli
from mobilidados.config import Case
from mobilidados.direction import directions
from mobilidados.pipeline import run

from .builders import write_case

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

TABLES = {
    "area_stations",
    "area_streets",
    "check_points",
    "encounters_by_pair",
    "encounters_detail",
    "encounters_summary",
    "narrow_sections",
    "occurrences_by_street",
    "occurrences_by_year",
    "occurrences_files",
    "overhang_sensitivity",
    "parking_strip_lengths",
    "passings",
    "profiles",
    "routes_on_street",
    "scheduled_runtimes",
    "standards_comparison",
    "stops_near_street",
    "street",
    "summary_by_block",
    "traffic_direction_edges",
    "trips_per_hour",
    "width_budget",
}


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    return Case.load(write_case(tmp_path_factory.mktemp("synthetic") / "case"))


@pytest.fixture(scope="module")
def results(case):
    run(case, offline=True)
    return case.results_dir


@pytest.fixture(scope="module")
def table(results):
    def read(name):
        return pd.read_csv(results / "tables" / f"{name}.csv")

    return read


@pytest.fixture(scope="module")
def findings(results):
    out = json.loads((results / "findings.json").read_text(encoding="utf-8"))
    return {f["id"]: f for f in out["findings"]}


def test_every_stage_writes_its_outputs(results):
    assert {p.stem for p in (results / "tables").glob("*.csv")} == TABLES
    for name in ("free_width_profile", "width_budget", "trips_per_hour", "area_streets"):
        assert (results / "figures" / f"{name}.png").read_bytes().startswith(PNG_SIGNATURE)
    for name in ("findings.json", "findings.md", "street_axis.geojson"):
        assert (results / name).stat().st_size > 0


def test_the_cross_section_is_measured_where_the_polygons_are_mapped(table):
    assert table("street").iloc[0].to_dict() == {"name": "Rua do Teste", "length_m": 200.0}
    # transects every profiles.step_m, strips mapped between 40.5 m and 150.5 m, block B1 ending at 100 m (see write_case)
    by_block = table("summary_by_block").set_index("block")
    assert by_block.n_stations.to_dict() == {"B1": 60, "B2": 50, "all": 110}
    assert by_block.loc["all", ["free_min", "free_median", "free_max"]].tolist() == [4.9, 4.9, 4.9]
    assert by_block.loc["all", ["strip_L_median", "strip_R_median", "kerb_to_kerb_median"]].tolist() == [2.0, 2.0, 8.9]
    assert by_block.loc["all", ["to_plot_L_median", "to_plot_R_median"]].tolist() == [2.5, 2.5]
    assert table("narrow_sections").values.tolist() == [[41.0, 100.0, "B1"], [101.0, 150.0, "B2"]]
    strips = table("parking_strip_lengths").set_index("block")
    assert strips.loc["all", ["strip_L_length_m", "strip_R_length_m"]].tolist() == [110.0, 110.0]
    checks = table("check_points").set_index("s_m")
    assert checks.block.to_dict() == {60.0: "B1", 120.0: "B2"}
    assert checks.free_width_m.tolist() == [4.9, 4.9]
    assert table("profiles").free_width.dropna().eq(4.9).all()


def test_traffic_is_two_way(table):
    edges = table("traffic_direction_edges")
    assert sorted(edges.s_m.unique()) == [10, 100, 190]
    assert directions(edges, "Traversable") == "two-way"


def test_the_timetable_gives_trips_per_hour_and_runtimes(table):
    assert table("routes_on_street")[["route_short_name", "heading", "s_first", "s_last"]].values.tolist() == [
        [10, 1, 0.0, 200.0],
        [20, -1, 200.0, 0.0],
    ]
    assert table("trips_per_hour").values.tolist() == [[8, 1, 1], [9, 1, 0]]  # hour, east, west
    assert list(table("trips_per_hour").columns) == ["hour", "east", "west"]
    assert table("passings")[["route_short_name", "heading", "arrival_time"]].values.tolist() == [
        [10, 1, "08:00:00"],
        [20, -1, "08:00:20"],
        [10, 1, "09:00:00"],
    ]
    runtimes = table("scheduled_runtimes")
    assert set(runtimes.median_s) == {60.0}
    assert set(runtimes.dist_straight_m) == {200}
    assert runtimes.kmh_at_median_min.tolist() == [12.0] * 4
    assert table("stops_near_street").stop_id.tolist() == ["S1", "S2"]


def test_the_buses_meet_once_per_speed_and_only_the_slower_meeting_is_in_a_narrow_section(table):
    summary = table("encounters_summary").set_index("basis")
    assert summary.loc["assumed", "speed_kmh"].tolist() == [15.0, 20.0]
    assert summary.loc["assumed", "encounters_per_day"].tolist() == [1, 1]
    assert summary.loc["schedule", ["speed_kmh", "encounters_per_day"]].tolist() == [12.0, 1]  # the speed the timetable implies
    detail = table("encounters_detail").set_index("speed_kmh")
    # route 20 enters the street at the other end 20 s after route 10: the faster they go, the nearer route 20's end they meet
    assert detail.loc[15.0, ["time", "s_m", "pair", "narrow_block", "in_narrow_section"]].tolist() == [
        "08:00:34",
        141.7,
        "10 x 20",
        "B2",
        True,
    ]
    assert detail.loc[20.0, ["time", "s_m", "in_narrow_section"]].tolist() == ["08:00:28", 155.6, False]  # past the last strip
    assert table("encounters_by_pair").encounters_per_day.tolist() == [1, 1]


def test_the_width_budget_margins(table):
    margin = table("width_budget").set_index(["scenario", "free_width_ref", "mirrors"]).margin_m
    assert margin["bus_eu_max", "median", False] == pytest.approx(4.90 - 2.55)
    assert margin["bus_eu_max x car_typical", "median", False] == pytest.approx(4.90 - 2.55 - 1.80)
    assert margin["bus_eu_max x car_typical", "median", True] == pytest.approx(4.90 - 2.55 - 2.05)  # a bus mirror passes over a car
    assert margin["bus_eu_max x bus_eu_max", "median", False] == pytest.approx(-0.20)
    assert margin["bus_eu_max x bus_eu_max", "median", True] == pytest.approx(-1.00)
    overhang = table("overhang_sensitivity").set_index(["scenario", "overhang_per_side_m"]).margin_body_m
    assert overhang["bus_eu_max x bus_eu_max", 0.3] == pytest.approx(-0.20 - 2 * 0.3)


def test_occurrences_are_counted_per_street_and_per_file(table):
    files = table("occurrences_files").set_index("file")
    # 2025.csv has a report without coordinates: it counts as a record, not in the period the counts cover
    assert files.loc["2024.csv", ["records", "with_coordinates", "with_date"]].tolist() == [6, 6, 6]
    assert files.loc["2025.csv", ["records", "with_coordinates", "with_date"]].tolist() == [6, 5, 5]
    assert files.first_date.to_dict() == {"2024.csv": "2024-03-05", "2025.csv": "2025-01-20"}
    assert files.last_date.to_dict() == {"2024.csv": "2024-11-03", "2025.csv": "2025-07-03"}
    by_street = table("occurrences_by_street").set_index("street")
    # Travessa Curta has a report but is shorter than min_street_length_m; the report 20 m from the axis is too far to count
    assert by_street.index.tolist() == ["Rua do Teste", "Rua Larga"]
    assert by_street.parking_n.tolist() == [5, 2]
    assert by_street.parking_per_100m.tolist() == [2.5, 1.0]
    assert table("occurrences_by_year").values.tolist() == [[2024, 3], [2025, 2]]


def test_the_area_scan_finds_the_street_with_buses_and_parking_on_both_sides(table):
    street = table("area_streets").iloc[0]
    assert len(table("area_streets")) == 1  # Rua Larga has no buses
    assert (street.street, street.buses_per_day, street.buses_both_directions, street.routes) == ("Rua do Teste", 3, True, "10 20")
    assert (street.free_width_median_m, street.traffic) == (4.9, "two-way")
    assert street.metres_with_pattern == 112  # one station per area_scan.step_m between the strips
    stations = table("area_stations")
    assert set(stations.street) == {"Rua do Teste"}
    assert stations.parking_both_sides.sum() * 4 == street.metres_with_pattern


def test_the_ledger_states_what_the_tables_show(findings, results):
    assert list(findings) == [
        "length",
        "traffic",
        "free_width",
        "parking_strips",
        "transit",
        "runtime_S1",
        "runtime_S2",
        "vehicle_bus_eu_max_body",
        "vehicle_bus_eu_max_mirrors",
        "vehicle_car_typical_body",
        "vehicle_car_typical_mirrors",
        "width_budget",
        "encounters",
        "occurrences",
        "area_pattern",
        "standard_cml_manual_two_way_profile",
        "standard_rast06_bus_bus",
        "gap_1",
    ]
    grades = {k: v["grade"] for k, v in findings.items()}
    assert grades["length"] == grades["free_width"] == grades["occurrences"] == "M"
    assert (grades["width_budget"], grades["encounters"]) == ("I", "I")
    assert (grades["vehicle_bus_eu_max_body"], grades["vehicle_bus_eu_max_mirrors"], grades["standard_rast06_bus_bus"]) == ("D", "P", "D")
    assert grades["gap_1"] == "NE"

    assert findings["length"]["statement"] == "The street axis is 200.00 m long."
    assert findings["traffic"]["values"] == {"traffic": "two-way"}
    assert "two-way traffic (edges checked at 3 points" in findings["traffic"]["statement"]
    assert "is 4.90–4.90 m (median 4.90 m)" in findings["free_width"]["statement"]
    assert "2.00 m (north) and 2.00 m (south)" in findings["parking_strips"]["statement"]
    assert findings["transit"]["values"] == {
        "trips_up": 2,
        "trips_down": 1,
        "max_up_per_hour": 1,
        "max_down_per_hour": 1,
        "service_date": "2026-10-27",
    }
    # a count of 1 is singular, a count of several (or a range) plural, and each clause agrees with its own count
    assert findings["transit"]["statement"].startswith(
        "Routes 10, 20 are scheduled along the street. On 2026-10-27: 2 trips east and 1 trip west ("
    )
    assert "implies 1 meeting per weekday" in findings["encounters"]["statement"]
    assert "; 0–1 fall within the sections with parking on both sides." in findings["encounters"]["statement"]
    assert findings["area_pattern"]["statement"].startswith(
        "Of 1 street with scheduled buses in the surrounding area, 1 is two-way and combines parking on both sides"
    )
    assert findings["occurrences"]["statement"].startswith("5 reports in category 'Parking' were attributed to the street")
    assert findings["width_budget"]["values"] == {
        "bus_bus_margin_m": -0.2,
        "bus_bus_margin_mirrors_m": -1.0,
        "bus_car_margin_m": 0.55,
        "bus_car_margin_mirrors_m": 0.3,
    }
    assert "margin −0.20 m" in findings["width_budget"]["statement"]
    assert findings["encounters"]["values"] == {"per_day": [1], "in_narrow_sections": [0, 1]}
    assert findings["occurrences"]["values"] == {"n": 5, "per_100m": 2.5, "rank": 1, "of": 2}
    assert "(2024-03-05 – 2025-07-03, within 12 m of the axis): 2.50 per 100 m, rank 1 of 2 streets" in findings["occurrences"]["statement"]
    assert findings["area_pattern"]["values"] == {"two_way_streets": ["Rua do Teste"], "with_buses_both_directions": ["Rua do Teste"]}

    report = (results / "findings.md").read_text(encoding="utf-8")
    assert all(f["statement"] in report for f in findings.values())
    assert "## Sources" in report
    assert "## Attribution" in report
    locked = json.loads((results / "findings.json").read_text(encoding="utf-8"))["sources"]
    assert sorted(locked) == ["area_axes", "area_cartography", "cartography", "feed", "network_identify", "reports", "street_axes"]


def test_the_cached_sources_match_the_lock(case, results, capsys):
    assert cli.main(["verify", str(case.root)]) == 0
    assert "files match the lock" in capsys.readouterr().out


def test_a_second_run_gives_identical_results(case, results, tmp_path):
    again = tmp_path / "again"
    run(Case.load(case.root, results_dir=again), offline=True)
    names = sorted(p.relative_to(results).as_posix() for p in results.rglob("*") if p.is_file())
    assert names == sorted(p.relative_to(again).as_posix() for p in again.rglob("*") if p.is_file())
    for name in names:
        if not name.endswith(".png"):
            assert (again / name).read_bytes() == (results / name).read_bytes(), name


def test_a_partial_run_reads_the_tables_an_earlier_run_wrote(case, results):
    before = (results / "findings.json").read_bytes()
    (results / "findings.json").unlink()
    run(case, stages=["ledger"], offline=True)
    assert (results / "findings.json").read_bytes() == before


def test_a_street_name_that_is_not_in_the_axes_is_reported_in_one_line(tmp_path, capsys):
    root = write_case(tmp_path / "wrong", street_name="Rua Inexistente")
    assert cli.main(["run", str(root), "--stages", "profiles", "--offline"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: expected exactly one axis named 'Rua Inexistente'")
    assert len(err.splitlines()) == 1


def test_a_full_run_removes_the_outputs_of_an_earlier_configuration(case, tmp_path):
    (tmp_path / "tables").mkdir()
    (tmp_path / "figures").mkdir()
    (tmp_path / "tables" / "left_over.csv").write_text("a\n1\n", encoding="utf-8")
    (tmp_path / "figures" / "left_over.png").write_bytes(PNG_SIGNATURE)
    run(Case.load(case.root, results_dir=tmp_path), offline=True)
    assert not (tmp_path / "tables" / "left_over.csv").exists()
    assert not (tmp_path / "figures" / "left_over.png").exists()
    assert (tmp_path / "tables" / "street.csv").exists()


def test_a_case_with_only_the_required_sections_reports_only_the_measurements(tmp_path):
    case = Case.load(write_case(tmp_path / "required", optional=False))
    run(case, offline=True)
    assert {p.stem for p in (case.results_dir / "tables").glob("*.csv")} == {
        "check_points",
        "narrow_sections",
        "parking_strip_lengths",
        "profiles",
        "street",
        "summary_by_block",
    }
    assert [p.name for p in (case.results_dir / "figures").iterdir()] == ["free_width_profile.png"]
    ledger = json.loads((case.results_dir / "findings.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in ledger["findings"]] == ["length", "free_width", "parking_strips", "gap_1"]
