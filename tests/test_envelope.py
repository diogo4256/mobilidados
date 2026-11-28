"""Width budget: vehicle widths with and without mirrors, and the margin against the measured free width."""

import pytest

from mobilidados import envelope
from mobilidados.config import vehicle_catalogue


def test_width_budget_mirror_rule():
    v = vehicle_catalogue()
    bus, car = v["carris_man_city_gold"], v["car_typical"]
    assert envelope.widths(bus, bus, False) == pytest.approx(5.00)
    assert envelope.widths(bus, bus, True) == pytest.approx(5.80)
    # a bus mirror passes above a car: only the car's mirrors count
    assert envelope.widths(bus, car, True) == pytest.approx(2.50 + 2.05)
    df = envelope.width_budget({"median": 4.90}, v, [["carris_man_city_gold", "carris_man_city_gold"]])
    assert df[~df.mirrors].margin_m.iloc[0] == pytest.approx(-0.10)


def test_passing_in_practice_adds_the_clearance_design_guidance_leaves_to_the_bodies():
    v = vehicle_catalogue()
    t = envelope.practical_passing(4.90, 6.91, v, [["carris_man_city_gold"], ["carris_man_city_gold", "carris_man_city_gold"],
                                                   ["car_typical", "car_typical"]], clearance_m=1.2)  # fmt: skip
    t = t.set_index("scenario")
    assert "carris_man_city_gold" not in t.index  # one vehicle alone does not meet anyone
    two_buses = t.loc["carris_man_city_gold x carris_man_city_gold"]
    assert two_buses.needed_m == pytest.approx(2.50 + 2.50 + 1.2)  # CIHT's 6.2 m for two buses
    assert two_buses.margin_now_m == pytest.approx(4.90 - 6.2)
    assert two_buses.margin_one_side_m == pytest.approx(6.91 - 6.2)
    assert list(t.needed_m) == sorted(t.needed_m, reverse=True)  # the hardest meeting first
