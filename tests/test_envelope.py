"""Width budget: vehicle widths with and without mirrors, and the margin against the measured free width."""

import pytest

from streetfit import envelope
from streetfit.config import vehicle_catalogue


def test_width_budget_mirror_rule():
    v = vehicle_catalogue()
    bus, car = v["carris_man_city_gold"], v["car_typical"]
    assert envelope.widths(bus, bus, False) == pytest.approx(5.00)
    assert envelope.widths(bus, bus, True) == pytest.approx(5.80)
    # a bus mirror passes above a car: only the car's mirrors count
    assert envelope.widths(bus, car, True) == pytest.approx(2.50 + 2.05)
    df = envelope.width_budget({"median": 4.90}, v, [["carris_man_city_gold", "carris_man_city_gold"]])
    assert df[~df.mirrors].margin_m.iloc[0] == pytest.approx(-0.10)
