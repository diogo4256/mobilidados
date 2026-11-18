"""The appraisal's arithmetic on numbers that can be checked by hand: working days, attribution, the yearly flows and
their present values, switching values, the PERT draws, and the configuration's checks."""

import dataclasses
import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from mobilidados import appraisal, delay
from mobilidados.config import Appraisal, Option

LISBON_2026 = [dt.date(2026, m, d) for m, d in [(1, 1), (2, 17), (4, 3), (4, 5), (4, 25), (5, 1), (6, 4), (6, 10), (6, 13), (8, 15),
                                                (10, 5), (11, 1), (12, 1), (12, 8), (12, 25)]]  # fmt: skip


def parameter(central, low=None, high=None, grade="P"):
    return {
        "low": central if low is None else low,
        "central": central,
        "high": central if high is None else high,
        "grade": grade,
        "label": "x",
        "source": "y",
    }


BASE = {
    "vot": parameter(6.0, 4.0, 8.0),
    "time_weight": parameter(1.0),
    "load_peak": parameter(10.0, 5.0, 20.0),
    "downstream": parameter(1.0),
    "bus_cost_h": parameter(40.0),
    "occupancy": parameter(1.0),
    "car_value": parameter(100.0, 50.0, 400.0),
    "sign_cost": parameter(100.0),
    "marking_cost_m": parameter(2.0),
    "enforcement_year": parameter(0.0),
    "stall_m": parameter(5.5),
    "comply": parameter(1.0),
}


def config(**kw):
    options = kw.pop("options", [{"id": "A", "label": "one side", "blocks": ["B2"], "compliance": "comply", "signs": 2}])
    return Appraisal.model_validate({"price_year": 2025, "parameters": BASE | kw.pop("parameters", {}), "options": options} | kw)


def measured(**kw):
    base = appraisal.Measured(
        excess_s=(5.0, 10.0, 15.0), peak_passages_per_day=36.0, working_days=100, attribution={"A": (0.5, 1.0, 1.0)}, metres={"A": 55.0}
    )
    return dataclasses.replace(base, **kw)


def test_working_days_leave_out_weekends_and_the_holidays_on_weekdays():
    # 2026 has 261 weekdays; 10 of Lisbon's holidays fall on one (5 April, 25 April, 13 June, 15 August and 1 November do not)
    assert appraisal.working_days(2026, LISBON_2026) == 251


def test_the_yearly_flows_and_present_values_are_the_hand_computed_ones():
    cfg, m = config(), measured()
    e = appraisal.evaluate(cfg.options[0], appraisal.central(cfg, m), m, cfg)
    # 10 s × 36 passages × 100 days = 10 bus-hours; a bus-hour is worth 10 passengers × 6 €/h + 40 € = 100 €
    assert e["bus_hours"] == pytest.approx(10.0)
    assert e["benefit_year"] == pytest.approx(1000.0)
    # 55 m ÷ 5,5 m = 10 places at 100 € a year
    assert e["places"] == pytest.approx(10.0)
    assert e["parking_year"] == pytest.approx(1000.0)
    # works: 2 signs × 100 € + 55 m × 2 €; half the marking repainted in years 5 and 10, discounted at 5 %
    works = 2 * 100 + 55 * 2
    repaint = 0.5 * 110 * (1.05**-5 + 1.05**-10)
    assert e["works"] == pytest.approx(works)
    assert e["npv"] == pytest.approx(-(works + repaint))
    annuity = sum(1.05**-t for t in range(1, 11))
    assert e["pv_benefit"] == pytest.approx(1000 * annuity)


def test_a_restriction_by_hours_pays_only_the_share_of_the_parking_and_its_enforcement():
    params = {"share": parameter(0.25), "enforcement_year": parameter(300.0)}
    option = {
        "id": "A",
        "label": "x",
        "blocks": ["B2"],
        "days": "working",
        "hours": [16, 20],
        "parking_share": "share",
        "compliance": "comply",
        "signs": 2,
    }
    cfg, m = config(parameters=params, options=[option]), measured()
    e = appraisal.evaluate(cfg.options[0], appraisal.central(cfg, m), m, cfg)
    assert e["parking_year"] == pytest.approx(250.0)
    assert e["enforcement_year"] == pytest.approx(300.0)


def test_the_switching_value_brings_the_present_value_to_zero():
    cfg, m = config(), measured()
    c = appraisal.central(cfg, m)
    o = cfg.options[0]
    sv = appraisal.switching_value(
        lambda x: appraisal.evaluate(o, c | {"car_value": x}, m, cfg)["npv"], *appraisal.search_domain(50.0, 400.0)
    )
    assert sv is not None
    assert appraisal.evaluate(o, c | {"car_value": sv}, m, cfg)["npv"] == pytest.approx(0.0, abs=1e-6)
    assert sv < 100  # the works must also be paid for, so a place must be worth a little less than the benefit per place
    assert appraisal.switching_value(lambda x: 1.0 + x, 0.0, 1.0) is None  # never zero there


def test_the_search_for_a_switching_value_keeps_shares_in_zero_to_one_and_lengths_above_zero():
    assert appraisal.search_domain(0.25, 0.7) == (0.0, 1.0)
    lo, hi = appraisal.search_domain(5.0, 6.0)
    assert 0 < lo < 5
    assert hi > 6
    assert appraisal.search_domain(0.0, 5000.0)[0] == 0.0


def test_pert_draws_stay_in_range_have_the_pert_mean_and_repeat_with_the_seed():
    a = appraisal.pert(np.random.default_rng(1), 325.0, 555.6, 2100.0, 200_000)
    assert a.min() >= 325
    assert a.max() <= 2100
    assert a.mean() == pytest.approx((325 + 4 * 555.6 + 2100) / 6, rel=0.01)
    np.testing.assert_array_equal(a, appraisal.pert(np.random.default_rng(1), 325.0, 555.6, 2100.0, 200_000))
    assert (appraisal.pert(np.random.default_rng(1), 2.0, 2.0, 2.0, 5) == 2.0).all()


def parts_and_copresence(p_gap_before=1e-6, p_gap_after=0.5):
    parts = pd.DataFrame(
        {
            "part": ["B1 45–76 m", "76–95 m", "B2 95–149 m", "149–166 m", "B3 166–190 m"],
            "narrow": [True, False, True, False, True],
            "excess_s": [2.0, 4.0, 4.0, 4.0, -1.0],
        }
    )
    cop = pd.DataFrame({"part": parts.part, "period": "peak", "p_value": [0.5, p_gap_before, 0.5, p_gap_after, 0.5]})
    return parts, cop


def test_attribution_counts_the_widened_sections_and_the_junctions_where_buses_give_way():
    parts, cop = parts_and_copresence()
    # total 13 s: B1+B2+B3 = 5 s; the junction before B2 (4 s) shows buses giving way, the one after (4 s) does not
    lo, ce, hi = appraisal.attribution(parts, cop, ["B1", "B2", "B3"], 0.01)
    assert (lo, ce, hi) == pytest.approx((5 / 13, 9 / 13, 1.0))
    # only B2 widened: its own 4 s, plus the junction before it; at most both junctions next to it
    assert appraisal.attribution(parts, cop, ["B2"], 0.01) == pytest.approx((4 / 13, 8 / 13, 12 / 13))
    # no junction shows giving way: the central value is the narrow sections alone
    parts, cop = parts_and_copresence(p_gap_before=0.2)
    assert appraisal.attribution(parts, cop, ["B1", "B2", "B3"], 0.01)[1] == pytest.approx(5 / 13)


def test_the_stretch_is_cut_into_narrow_sections_and_what_lies_between():
    cuts = delay.parts([(41.0, 76.0, "B1"), (95.5, 149.0, "B2"), (166.5, 194.0, "B3")], 45.0, 190.0)
    assert [(c[0], c[3]) for c in cuts] == [("B1 45–76 m", True), ("76–95.5 m", False), ("B2 95.5–149 m", True), ("149–166.5 m", False),
                                            ("B3 166.5–190 m", True)]  # fmt: skip
    assert delay.parts([(0.0, 3.0, "B1")], 0.0, 100.0) == [("0–100 m", 0.0, 100.0, False)]  # a sliver is left to its neighbour


def test_the_binomial_tail_is_exact():
    assert delay.binomial_tail(0, 10, 0.3) == 1.0
    assert delay.binomial_tail(3, 5, 0.5) == pytest.approx(sum(math.comb(5, k) for k in (3, 4, 5)) / 32)
    assert delay.binomial_tail(34, 135, 0.109) < 1e-5


def test_a_missing_parameter_or_a_repeated_option_is_refused():
    with pytest.raises(ValidationError, match="parameters missing"):
        Appraisal.model_validate({"price_year": 2025, "parameters": {k: v for k, v in BASE.items() if k != "vot"},
                                  "options": [{"id": "A", "label": "x", "blocks": ["B2"], "compliance": "comply", "signs": 0}]})  # fmt: skip
    with pytest.raises(ValidationError, match="option ids repeat"):
        config(options=[{"id": "A", "label": "x", "blocks": ["B2"], "compliance": "comply", "signs": 0}] * 2)
    with pytest.raises(ValidationError, match="low <= central <= high"):
        config(parameters={"vot": parameter(6.0, 7.0, 8.0)})
    with pytest.raises(ValidationError, match="hours"):
        Option(id="A", label="x", blocks=["B2"], compliance="comply", signs=0, hours=(20, 16))
