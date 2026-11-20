"""The appraisal's arithmetic on numbers that can be checked by hand: working days, the days of each timetable, the
passages an option covers, attribution, the yearly flows and their present values in both layers, switching values,
the PERT draws, the value of information, and the configuration's checks."""

import dataclasses
import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from mobilidados import appraisal, delay
from mobilidados.config import Appraisal, Criterion, Option

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
        excess_s=(5.0, 10.0, 15.0), peak_passages_per_day=36.0, working_days=100, attribution={"A": (0.5, 1.0, 1.0)}, metres={"A": 55.0},
        passages={"A": (3600.0, 0.0)}, passages_year=3600.0,
    )  # fmt: skip
    return dataclasses.replace(base, **kw)


def test_working_days_leave_out_weekends_and_the_holidays_on_weekdays():
    # 2026 has 261 weekdays; 10 of Lisbon's holidays fall on one (5 April, 25 April, 13 June, 15 August and 1 November do not)
    assert appraisal.working_days(2026, LISBON_2026) == 251


def test_the_yearly_flows_and_present_values_are_the_hand_computed_ones():
    cfg, m = config(), measured()
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
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
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
    assert e["parking_year"] == pytest.approx(250.0)
    assert e["enforcement_year"] == pytest.approx(300.0)


def test_the_switching_value_brings_the_present_value_to_zero():
    cfg, m = config(), measured()
    c = appraisal.layer(appraisal.central(cfg, m), "core")
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
    # total 13 s: B1+B2+B3 = 5 s; the junction before B2 (4 s) shows buses losing time to oncoming buses, the one after (4 s) does not
    lo, ce, hi = appraisal.attribution(parts, cop, ["B1", "B2", "B3"], 0.01)
    assert (lo, ce, hi) == pytest.approx((5 / 13, 9 / 13, 1.0))
    # only B2 widened: its own 4 s, plus the junction before it; at most both junctions next to it
    assert appraisal.attribution(parts, cop, ["B2"], 0.01) == pytest.approx((4 / 13, 8 / 13, 12 / 13))
    # no junction shows buses losing time to oncoming buses: the central value is the narrow sections alone
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


def test_the_days_of_each_timetable_add_up_to_the_year():
    days = appraisal.day_counts(2026, LISBON_2026)
    # 52 Saturdays, three of them holidays (25 April, 13 June, 15 August), which run the Sunday timetable with the 52
    # Sundays and the 10 holidays on weekdays
    assert days == {"working": 251, "saturday": 49, "sunday": 65}
    assert sum(days.values()) == 365


def test_an_option_covers_only_the_passages_of_its_days_and_hours():
    hourly = pd.DataFrame(
        [{"day_kind": k, "hour": h, "passages": n} for k, n in (("working", 6), ("saturday", 4), ("sunday", 2)) for h in range(7, 21)]
    )
    days = {"working": 10, "saturday": 2, "sunday": 3}
    always = Option(id="A", label="x", blocks=["B2"], compliance="comply", signs=0)
    late = Option(id="B", label="x", blocks=["B2"], compliance="comply", signs=0, days="working", hours=(16, 20))
    # the peak is 17h and 18h on working days: 2 hours × 6 × 10 days
    assert appraisal.passages(hourly, days, always, [17, 18]) == (120.0, (14 * 6 - 12) * 10 + 14 * 4 * 2 + 14 * 2 * 3)
    assert appraisal.passages(hourly, days, late, [17, 18]) == (120.0, 2 * 6 * 10)  # 16h and 19h
    assert sum(appraisal.passages(hourly, days, None, [17, 18])) == 14 * (6 * 10 + 4 * 2 + 2 * 3)


EXTENDED = {
    "offpeak_s": parameter(5.0),
    "load_offpeak": parameter(8.0),
    "unexpected_share": parameter(0.5),
    "transfer_share": parameter(0.0),
    "lateness_weight": parameter(3.0),
    "cars_behind": parameter(1.0),
    "car_occupancy": parameter(1.5),
    "elasticity_ivt": parameter(0.6),
    "journey_min": parameter(10.0),
    "diversion_car": parameter(0.25),
    "trip_km": parameter(4.0),
    "external_cost_pkm": parameter(0.2),
    "damage_year": parameter(400.0),
    "room_nearby": parameter(0.5),
    "walk_cost": parameter(20.0),
    "calming_cost": parameter(1000.0),
}


def test_the_core_is_the_extended_layer_with_its_mechanisms_switched_off():
    cfg = config(parameters=EXTENDED)
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    core = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
    plain = appraisal.evaluate(config().options[0], appraisal.layer(appraisal.central(config(), m), "extended"), m, config())
    assert core["npv"] == pytest.approx(plain["npv"])  # a case without the mechanisms: both layers are the core


def test_the_extended_layer_adds_each_mechanism_as_computed_by_hand():
    cfg = config(parameters=EXTENDED)
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "extended"), m, cfg)
    peak_bh, other_bh = 10 * 3600 / 3600, 5 * 7200 / 3600  # 10 bus-hours at peak, 10 off-peak (attribution 1, compliance 1)
    assert e["bus_hours"] == pytest.approx(peak_bh + other_bh)
    on_board = peak_bh * 10 + other_bh * 8  # 180 passenger-hours
    weight = 1.0 + (3.0 - 1.0) * 0.5  # half the delay is unexpected: weighted 3 instead of 1
    assert e["time_value"] == pytest.approx(on_board * 6.0 * weight)
    assert e["traffic_value"] == pytest.approx(20 * 1.0 * 1.5 * 6.0 * 1.0)
    riders = 3600 * 10 + 7200 * 8
    saved = 3600 * on_board / riders
    new = 0.6 * saved / 600 * riders
    assert e["new_riders"] == pytest.approx(new)
    assert e["new_rider_value"] == pytest.approx(0.5 * new * saved / 3600 * 6.0)
    assert e["external_value"] == pytest.approx(new * 0.25 * 4.0 * 0.2)
    assert e["damage_value"] == pytest.approx(400.0)  # in force at every passage, on the whole stretch
    # half the displaced cars find a place nearby (20 € a year), the other half pay 100 €
    assert e["parking_year"] == pytest.approx(10.0 * (0.5 * 20 + 0.5 * 100))
    assert e["works"] == pytest.approx(2 * 100 + 55 * 2 + 1000)


def test_what_a_displaced_driver_pays_a_car_park_with_room_to_spare_is_a_transfer():
    cfg = config(parameters=EXTENDED | {"carpark_walk": parameter(30.0), "spare_capacity": parameter(0.25)})
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "extended"), m, cfg)
    # 10 places: half find a place nearby (20 €), half pay 100 € for a car park and walk 30 € from it
    private = 10.0 * (0.5 * 20 + 0.5 * (100 + 30))
    revenue = 10.0 * 0.5 * 0.25 * 100  # a quarter of what they pay goes to spare room: a transfer, not a cost
    assert e["parking_private_year"] == pytest.approx(private)
    assert e["carpark_revenue_year"] == pytest.approx(revenue)
    assert e["parking_year"] == pytest.approx(private - revenue)
    # the distribution shows both sides; the economic case only their difference
    dist = appraisal.distribution(cfg, m, appraisal.central(cfg, m)).set_index("group")
    assert dist.loc["parkers", "value"] == pytest.approx(-private)
    assert dist.loc["car_parks", "value"] == pytest.approx(revenue)
    # the core counts the price paid in full, with no walk and no transfer
    core = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
    assert core["parking_year"] == pytest.approx(10.0 * 100)


def test_a_draw_through_the_simulation_is_the_same_as_evaluating_it_alone():
    cfg = config(parameters=EXTENDED | {"vot": parameter(6.0, 4.0, 8.0), "room_nearby": parameter(0.5, 0.0, 1.0)}, draws=1000)
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    d = appraisal.draws(cfg, m)
    sims = appraisal.simulate(cfg, m, d, "extended")
    i = 17
    one = appraisal.evaluate(cfg.options[0], appraisal.layer({k: float(v[i]) for k, v in d.items()}, "extended"), m, cfg)
    assert sims.A[i] == pytest.approx(one["npv"])


def test_the_value_of_information_goes_to_the_input_that_can_change_the_decision():
    rng = np.random.default_rng(3)
    decisive, idle = rng.uniform(-1, 1, 4000), rng.uniform(-1, 1, 4000)
    sims = pd.DataFrame({"A": 1000 * decisive})  # worth doing exactly when ``decisive`` > 0
    voi = appraisal.value_of_information(sims, {"decisive": decisive, "idle": idle}).set_index("input").evppi
    assert voi["(all)"] == pytest.approx(np.maximum(1000 * decisive, 0).mean() - max(0, 1000 * decisive.mean()))
    assert voi["decisive"] == pytest.approx(voi["(all)"], rel=0.05)
    assert voi["idle"] < 0.1 * voi["(all)"]


def test_a_criterion_must_say_how_every_option_moves_it():
    crit = {"id": "x", "dimension": "safety", "label": "x", "indicator": "x", "grade": "P", "note": "x"}
    with pytest.raises(ValidationError, match="do not say how every option"):
        config(criteria=[crit | {"effects": {}}])
    with pytest.raises(ValidationError, match="options that do not exist"):
        config(criteria=[crit | {"effects": {"Z": "+", "*": "?"}}])
    table = appraisal.criteria_table(config(criteria=[crit | {"effects": {"*": "?", "A": "+"}}]))
    assert table.loc[0, "A"] == "+"
    assert Criterion(**crit, effects={"*": "0"}).effects == {"*": "0"}


def test_unit_values_grow_with_income_on_both_sides_of_the_account():
    cfg = config(parameters={"income_growth": parameter(0.02)})
    m = measured()
    o = cfg.options[0]
    flat = appraisal.evaluate(o, appraisal.layer(appraisal.central(config(), m), "core"), m, config())
    grown = appraisal.evaluate(o, appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
    factor = sum(1.02**t / 1.05**t for t in range(1, 11)) / sum(1.05**-t for t in range(1, 11))
    # time (elasticity 1), the operator's cost (1) and the value of a place (1) grow alike; the works do not
    assert grown["pv_benefit"] == pytest.approx(flat["pv_benefit"] * factor)
    assert grown["pv_parking"] == pytest.approx(flat["pv_parking"] * factor)
    assert grown["pv_public"] == pytest.approx(flat["pv_public"])


def test_the_dft_ratio_counts_the_parking_as_a_disbenefit_and_the_budget_as_the_cost():
    cfg, m = config(), measured()
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "core"), m, cfg)
    assert e["bcr_budget"] == pytest.approx((e["pv_benefit"] - e["pv_parking"]) / e["pv_public"])
    assert e["npv"] == pytest.approx(e["pv_benefit"] - e["pv_parking"] - e["pv_public"])  # the same NPV either way
    assert [appraisal.vfm_category(x, 1.0) for x in (4.0, 3.9, 1.5, 1.2, 0.5)] == ["very_high", "high", "medium", "low", "poor"]
    assert appraisal.vfm_category(-0.3, -10.0) == "very_poor"


def test_the_bridge_goes_from_the_core_to_the_extended_layer():
    cfg = config(parameters=EXTENDED)
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    c = appraisal.central(cfg, m)
    b = appraisal.bridge(cfg, m, c)
    core = appraisal.evaluate(cfg.options[0], appraisal.layer(c, "core"), m, cfg)["npv"]
    extended = appraisal.evaluate(cfg.options[0], appraisal.layer(c, "extended"), m, cfg)["npv"]
    assert b.npv.iloc[0] == pytest.approx(core)
    assert b.npv.iloc[-1] == pytest.approx(extended)
    assert b.change.sum() == pytest.approx(extended)  # the core's NPV plus every step
    assert b.step.tolist() == ["core", *[k for k in appraisal.MECHANISMS if k in cfg.parameters]]


def test_the_scenarios_bracket_the_central_value_and_longer_periods_are_shown():
    cfg = config(
        parameters=EXTENDED | {"offpeak_s": parameter(5.0, 0.0, 8.0), "room_nearby": parameter(0.5, 0.0, 1.0)}, horizons_tested=[20]
    )
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    s = appraisal.scenarios(cfg, m, appraisal.central(cfg, m)).set_index(["scenario", "years"]).npv
    assert s["cautious", 10] < s["central", 10] < s["favourable", 10]
    # 20 years: ten more years of the same yearly flows, less the repainting, so the NPV moves the way the yearly flow points
    assert ("central", 20) in s.index
    assert ("core", 20) in s.index
    e = appraisal.evaluate(cfg.options[0], appraisal.layer(appraisal.central(cfg, m), "extended"), m, cfg)
    yearly = e["benefit_year"] - e["parking_year"]
    assert (s["central", 20] > s["central", 10]) == (yearly > 0)


def test_correlated_inputs_move_together_and_keep_their_distributions():
    cfg = config(parameters=EXTENDED | {"offpeak_s": parameter(5.0, 0.0, 8.0)}, draws=4000,
                 correlations=[{"a": "excess_s", "b": "offpeak_s", "rho": 0.6}])  # fmt: skip
    m = measured(passages={"A": (3600.0, 7200.0)}, passages_year=10800.0)
    d = appraisal.draws(cfg, m)
    ranks = pd.DataFrame({"a": d["excess_s"], "b": d["offpeak_s"]}).rank()
    assert 0.5 < ranks.corr().iloc[0, 1] < 0.7
    independent = appraisal.draws(config(parameters=EXTENDED | {"offpeak_s": parameter(5.0, 0.0, 8.0)}, draws=4000), m)
    assert np.sort(d["offpeak_s"]).mean() == pytest.approx(np.sort(independent["offpeak_s"]).mean(), rel=0.05)
    with pytest.raises(ValidationError, match="correlations name inputs"):
        config(correlations=[{"a": "excess_s", "b": "nothing", "rho": 0.5}])
