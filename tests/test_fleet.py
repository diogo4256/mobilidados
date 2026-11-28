"""The vehicles recorded on a route, day by day: records read as served, counted per model and checked against the
series of the vehicle whose sheet gives the width used in the scenarios."""

import datetime as dt
import json

import pytest

from mobilidados import fleet
from mobilidados.config import HttpSeries, MobilidadosError

SRC = HttpSeries(
    kind="http_series",
    url="https://example.org/vehicles?line_id={route}&day={day}",
    routes=["200_0", "239_0"],
    period=(dt.date(2026, 3, 2), dt.date(2026, 3, 4)),
    licence="not stated",
)
NAMES = {"200_0": "744", "239_0": "46B"}


def rec(vehicle, route, model):
    return {"id_veiculo": vehicle, "linha": route, "modelo": model, "plate": "x", "distance": 1.0}


MAN = "Standard MAN GNC (2601-2820)"
MINI = "Mini MAN (251-283)"
SPRINTER = "Mini Mercedes Sprinter (201-240)"


def write(folder, served):
    folder.mkdir(exist_ok=True)
    for name in SRC.requests():
        (folder / name).write_text(json.dumps(served.get(name, [])), encoding="utf-8")


def test_the_requests_are_one_per_route_and_day():
    req = SRC.requests()
    assert len(req) == 6
    assert req["239_0_2026-03-04.json"] == "https://example.org/vehicles?line_id=239_0&day=2026-03-04"


@pytest.mark.parametrize(("label", "rng"), [(MAN, (2601, 2820)), ("Mini MAN (251 - 283)", (251, 283)), ("Articulado", None)])
def test_the_series_comes_from_the_end_of_the_model_label(label, rng):
    assert fleet.series(label) == rng


def test_vehicle_days_per_model_and_the_envelope_series(tmp_path):
    served = {
        "200_0_2026-03-02.json": [rec("2609", "200_0", MAN), rec("2650", "200_0", MAN), rec("1701", "199_1", "Standard Volvo (1701-1780)")],
        "200_0_2026-03-03.json": [rec("2609", "200_0", MAN), rec("2609", "200_0", MAN)],  # listed twice: one vehicle-day
        "200_0_2026-03-04.json": [rec("2640", "200_0", MAN)],
        "239_0_2026-03-02.json": [rec("211", "239_0", SPRINTER)],
        "239_0_2026-03-04.json": [rec("260", "239_0", MINI)],
    }
    write(tmp_path, served)
    records, files = fleet.load(tmp_path, SRC)
    assert len(records) == 6  # the Volvo on another route is left out, the duplicate counted once
    models = fleet.models(records, NAMES, envelope_number=2643)
    man = models[models.model == MAN].iloc[0]
    assert (man.route, man.vehicle_days, man.vehicles, man.number_min, man.number_max, man.share) == ("744", 4, 3, 2609, 2650, 1.0)
    assert bool(man.envelope_series)
    mini = models[models.route == "46B"].set_index("model")
    assert mini.share.to_dict() == {SPRINTER: 0.5, MINI: 0.5}
    assert not mini.envelope_series.any()
    days = fleet.days(files, NAMES).set_index("route")
    assert days.loc["46B"].to_dict() == {
        "route_id": "239_0",
        "days_asked": 3,
        "days_with_records": 2,
        "first_day": "2026-03-02",
        "last_day": "2026-03-04",
        "vehicle_days": 2,
    }
    assert int(days.loc["744", "vehicle_days"]) == 4


def test_without_a_fleet_number_no_series_is_the_envelope_s(tmp_path):
    write(tmp_path, {"200_0_2026-03-02.json": [rec("2609", "200_0", MAN)]})
    records, _ = fleet.load(tmp_path, SRC)
    assert not fleet.models(records, NAMES, envelope_number=None).envelope_series.any()


def test_a_missing_file_or_an_unexpected_answer_is_an_error(tmp_path):
    with pytest.raises(MobilidadosError, match="is missing"):
        fleet.load(tmp_path, SRC)
    write(tmp_path, {})
    (tmp_path / "200_0_2026-03-03.json").write_text('{"detail": "Not Found"}', encoding="utf-8")
    with pytest.raises(MobilidadosError, match="expected a list of vehicle records"):
        fleet.load(tmp_path, SRC)
    (tmp_path / "200_0_2026-03-03.json").write_text('[{"id_veiculo": "1"}]', encoding="utf-8")
    with pytest.raises(MobilidadosError, match=r"a record has no \['linha', 'modelo'\]"):
        fleet.load(tmp_path, SRC)
