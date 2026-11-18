"""Feasibility and cost-benefit appraisal of giving one parking strip back to the carriageway (``[appraisal]``).

The method follows the European Commission's *Economic Appraisal Vademecum 2021-2027*: an incremental economic
analysis of each option against doing nothing, at constant prices, over ``horizon_years``, discounted at the social
discount rate. Docs: docs/appraisal.md.

**Benefit (monetised): the time buses lose at the evening peak.** The ``delay`` stage measures how much longer buses
take on the stretch at peak than the neighbouring stretches explain (``delay_summary``, with its 90% interval). Only
the part an option can remove counts (*attribution*), read from where the excess sits along the stretch
(``delay_by_part``) and where buses give way to oncoming ones (``delay_copresence``):

* low: the excess inside the sections the option widens;
* central: plus the excess at the junctions next to them where buses have an oncoming bus on the street far more
  often than chance (they wait there for the narrow section to clear);
* high: plus the excess at every junction next to them.

The time is valued for the passengers on board (value of time × the weight of delay) and for the operator (the cost
of a bus-hour), for the buses the timetable schedules through the street at peak, on every working day of a year.

**Costs (monetised):** the parking places removed (the value of a place to whoever loses it, for the part of the
day the restriction applies), the works (signs and markings, repainted periodically) and, for a restriction by hours,
its enforcement. Both the benefit and the parking cost scale with compliance: a car that stays still blocks the bus
and keeps its place.

**Not monetised** (said so in the report): the time lost off-peak, which the measurement cannot separate; the delay
of people in cars; safety; emergency access; the search for a place.

**Uncertainty:** every input has a low, central and high value (a measured input: its 90% interval). The appraisal
gives the central result, the value of each input at which the result changes sign (switching values), each input's
swing (tornado) and a Monte Carlo simulation with triangular distributions (fixed seed): the probability that an
option is worth doing and the spread of its value.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .config import Appraisal, Option

DAY_KINDS = ("working", "other")


@dataclass(frozen=True)
class Measured:
    """What the appraisal takes from the run's tables (all measured or inferred from data, none typed in)."""

    excess_s: tuple[float, float, float]  # the peak excess per passage: 90% low, estimate, 90% high
    peak_passages_per_day: float  # buses the timetable schedules through the street at peak on a working day
    working_days: int  # in the reference year, without the city's holidays
    attribution: dict[str, tuple[float, float, float]]  # option id -> low, central, high
    metres: dict[str, float]  # option id -> metres of parking strip removed (one side, in its sections)


def working_days(year: int, holidays: list[dt.date]) -> int:
    """Monday to Friday in ``year``, without the holidays that fall on them."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    off = set(holidays)
    return int(sum(1 for d in days if d.dayofweek < 5 and d.date() not in off))


def attribution(by_part: pd.DataFrame, copresence: pd.DataFrame, blocks: list[str], significance: float) -> tuple[float, float, float]:
    """The share of the measured excess an option widening the narrow sections of ``blocks`` can remove (see the module).

    Shares are of the sum of the parts' excesses, so they add up across the parts; each bound is cut to [0, 1]."""
    parts = by_part.reset_index(drop=True)
    total = float(parts.excess_s.sum())
    if total <= 0:
        return (0.0, 0.0, 0.0)
    peak = copresence[copresence.period == "peak"].set_index("part")

    def block(name: str) -> str:
        return name.split()[0]

    widened = [i for i, p in parts.iterrows() if p.narrow and block(p.part) in blocks]
    gaps = [i for i, p in parts.iterrows() if not p.narrow and any(j in widened for j in (i - 1, i + 1))]
    giving_way = [i for i in gaps if parts.part[i] in peak.index and peak.p_value[parts.part[i]] < significance]
    low = sum(parts.excess_s[i] for i in widened) / total
    central = low + sum(parts.excess_s[i] for i in giving_way) / total
    high = low + sum(parts.excess_s[i] for i in gaps) / total
    lo, ce, hi = sorted(min(max(x, 0.0), 1.0) for x in (low, central, high))
    return (lo, ce, hi)


def measured(tables: dict[str, pd.DataFrame], cfg: Appraisal, block_metres: dict[str, float], peak_hours: list[int], year: int,
             holidays: list[dt.date]) -> Measured:  # fmt: skip
    """The appraisal's measured inputs, from the run's tables: ``delay_summary``, ``delay_by_part``,
    ``delay_copresence``, ``passings``, and the metres of each block's sections with parking on both sides."""
    whole = tables["delay_summary"].astype({"scope": str}).set_index("scope").loc["all"]
    passings = tables["passings"]
    peak = passings[(passings.t // 3600).isin(peak_hours)]
    return Measured(
        excess_s=(float(whole.excess_ci90_low_s), float(whole.excess_s), float(whole.excess_ci90_high_s)),
        peak_passages_per_day=float(len(peak)),
        working_days=working_days(year, holidays),
        attribution={
            o.id: attribution(tables["delay_by_part"], tables["delay_copresence"], o.blocks, cfg.significance) for o in cfg.options
        },
        metres={o.id: round(sum(block_metres.get(b, 0.0) for b in o.blocks), 1) for o in cfg.options},
    )


# --- the model ---------------------------------------------------------------------------------------------------------
def central(cfg: Appraisal, m: Measured) -> dict[str, float]:
    """Every input at its central value, keyed as ``evaluate`` reads them."""
    p = {k: v.central for k, v in cfg.parameters.items()}
    p["excess_s"] = m.excess_s[1]
    p |= {f"attribution_{o}": a[1] for o, a in m.attribution.items()}
    return p


def ranges(cfg: Appraisal, m: Measured) -> dict[str, tuple[float, float, float]]:
    """Every input's low, central and high value."""
    r = {k: (v.low, v.central, v.high) for k, v in cfg.parameters.items()}
    r["excess_s"] = m.excess_s
    r |= {f"attribution_{o}": a for o, a in m.attribution.items()}
    return r


def evaluate(o: Option, p: dict[str, float], m: Measured, cfg: Appraisal, rate: float | None = None) -> dict[str, float]:
    """One option's yearly flows, present values, net present value and benefit-cost ratio for inputs ``p``."""
    r = cfg.discount_rate if rate is None else rate
    years = np.arange(1, cfg.horizon_years + 1)
    annuity = float(np.sum((1 + r) ** -years.astype(float)))
    comply = p[o.compliance]
    bus_hours = p["excess_s"] * p[f"attribution_{o.id}"] * m.peak_passages_per_day * m.working_days / 3600 * comply
    passenger_hours = bus_hours * p["load_peak"] * p["downstream"]
    time_value = passenger_hours * p["vot"] * p["time_weight"]
    operator_value = bus_hours * p["bus_cost_h"]
    benefit = time_value + operator_value
    places = m.metres[o.id] / p["stall_m"]
    share = p[o.parking_share] if o.parking_share else 1.0
    parking = places * p["occupancy"] * p["car_value"] * share * comply
    enforcement = p["enforcement_year"] if (o.days != "all" or o.hours != (0, 24)) else 0.0
    marking = m.metres[o.id] * p["marking_cost_m"]
    works = o.signs * p["sign_cost"] + marking
    repaints = range(cfg.repaint_every_years, cfg.horizon_years + 1, cfg.repaint_every_years)
    repaint_pv = sum(0.5 * marking * (1 + r) ** -t for t in repaints)  # half the marking, every few years
    pv_benefit = benefit * annuity
    pv_cost = (parking + enforcement) * annuity + works + repaint_pv
    return {
        "bus_hours": bus_hours,
        "passenger_hours": passenger_hours,
        "time_value": time_value,
        "operator_value": operator_value,
        "benefit_year": benefit,
        "places": places,
        "parking_year": parking,
        "enforcement_year": enforcement,
        "works": works,
        "pv_benefit": pv_benefit,
        "pv_cost": pv_cost,
        "npv": pv_benefit - pv_cost,
        "bcr": pv_benefit / pv_cost if pv_cost else np.inf,
    }


def switching_value(f: Callable[[float], float], lo: float, hi: float) -> float | None:
    """The input value in [lo, hi] at which ``f`` (the net present value) changes sign, by bisection; None if it does
    not change sign there."""
    a, b, fa, fb = lo, hi, f(lo), f(hi)
    if fa == 0:
        return lo
    if fa * fb > 0:
        return None
    for _ in range(80):
        mid = (a + b) / 2
        fm = f(mid)
        if fa * fm <= 0:
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2


def search_domain(lo: float, hi: float) -> tuple[float, float]:
    """Where to look for an input's switching value: a share (0 ≤ low, high ≤ 1) within [0, 1]; a positive quantity from
    a hundredth of its low value (never 0: a length divides) to 20 times its high value; anything else symmetrically."""
    if lo >= 0 and hi <= 1:
        return 0.0, 1.0
    span = max(abs(lo), abs(hi), 1.0) * 20
    if lo > 0:
        return lo / 100, span
    return (0.0 if lo == 0 else -span), span


def option_inputs(o: Option) -> list[str]:
    """The inputs an option's value depends on (the parking share and compliance it names, and the shared ones)."""
    shared = ["excess_s", f"attribution_{o.id}", "load_peak", "downstream", "vot", "time_weight", "bus_cost_h", "stall_m", "occupancy",
              "car_value", "sign_cost", "marking_cost_m"]  # fmt: skip
    timed = o.days != "all" or o.hours != (0, 24)
    return shared + ([o.parking_share] if o.parking_share else []) + [o.compliance] + (["enforcement_year"] if timed else [])


def simulate(cfg: Appraisal, m: Measured) -> pd.DataFrame:
    """Net present values over ``cfg.draws`` draws of every input from its triangular distribution (fixed seed). The same
    draws serve every option, so the options are compared on the same uncertain world."""
    rng = np.random.default_rng(cfg.seed)
    rg = ranges(cfg, m)
    draws = {k: (np.full(cfg.draws, c) if lo == hi else rng.triangular(lo, c, hi, cfg.draws)) for k, (lo, c, hi) in sorted(rg.items())}
    out = {}
    for o in cfg.options:
        out[o.id] = [evaluate(o, {k: float(v[i]) for k, v in draws.items()}, m, cfg)["npv"] for i in range(cfg.draws)]
    return pd.DataFrame(out)


def appraise(cfg: Appraisal, m: Measured) -> dict[str, pd.DataFrame]:
    """Every table of the appraisal (see ``docs/appraisal.md``)."""
    c, rg = central(cfg, m), ranges(cfg, m)
    results, switching, tornado = [], [], []
    for o in cfg.options:
        e = evaluate(o, c, m, cfg)
        lo_a, ce_a, hi_a = m.attribution[o.id]
        results.append(
            {
                "option": o.id,
                "label": o.label,
                "metres": m.metres[o.id],
                "attribution_low": lo_a,
                "attribution": ce_a,
                "attribution_high": hi_a,
            }
            | e
            | {f"npv_at_{int(r * 100)}pct": evaluate(o, c, m, cfg, rate=r)["npv"] for r in cfg.discount_rates_tested}
        )
        for k in option_inputs(o):
            lo, ce, hi = rg[k]

            def npv_at(x: float, key: str = k, opt: Option = o) -> float:
                return evaluate(opt, c | {key: x}, m, cfg)["npv"]

            sv = switching_value(npv_at, *search_domain(lo, hi))
            switching.append(
                {"option": o.id, "input": k, "central": ce, "switching_value": sv, "within_range": sv is not None and lo <= sv <= hi}
            )
            tornado.append({"option": o.id, "input": k, "low": lo, "high": hi, "npv_at_low": npv_at(lo), "npv_at_high": npv_at(hi)})
    sims = simulate(cfg, m)
    mc = [
        {
            "option": k,
            "mean": float(v.mean()),
            "p10": float(v.quantile(0.10)),
            "p50": float(v.median()),
            "p90": float(v.quantile(0.90)),
            "probability_positive": float((v > 0).mean()),
            "probability_best": float((sims.idxmax(axis=1) == k).mean()),
        }
        for k, v in sims.items()
    ]
    value_bus_hour = c["load_peak"] * c["downstream"] * c["vot"] * c["time_weight"] + c["bus_cost_h"]
    annuity = float(np.sum((1 + cfg.discount_rate) ** -np.arange(1, cfg.horizon_years + 1, dtype=float)))
    alternatives = []
    for alt in cfg.alternatives:
        pv_cost = alt.signs * c["sign_cost"] + alt.works + alt.yearly * annuity
        hours = pv_cost / annuity / value_bus_hour
        alternatives.append(
            {"alternative": alt.id, "label": alt.label, "pv_cost": pv_cost, "value_per_bus_hour": value_bus_hour, "breakeven_bus_hours_per_year": hours,
             "breakeven_seconds_per_peak_passage": hours * 3600 / (m.peak_passages_per_day * m.working_days), "keeps_parking": alt.keeps_parking}
        )  # fmt: skip
    tor = pd.DataFrame(tornado)
    tor["swing"] = (tor.npv_at_high - tor.npv_at_low).abs()
    inputs = [
        {
            "input": k,
            "low": lo,
            "central": ce,
            "high": hi,
            "grade": cfg.parameters[k].grade,
            "unit": cfg.parameters[k].unit,
            "label": cfg.parameters[k].label,
            "source": cfg.parameters[k].source,
        }
        for k, (lo, ce, hi) in rg.items()
        if k in cfg.parameters
    ]
    return {
        "appraisal_inputs": pd.DataFrame(inputs),
        "appraisal_results": pd.DataFrame(results),
        "appraisal_switching": pd.DataFrame(switching),
        "appraisal_tornado": tor.sort_values(["option", "swing"], ascending=[True, False]).reset_index(drop=True),
        "appraisal_montecarlo": pd.DataFrame(mc),
        "appraisal_alternatives": pd.DataFrame(
            alternatives,
            columns=[
                "alternative",
                "label",
                "pv_cost",
                "value_per_bus_hour",
                "breakeven_bus_hours_per_year",
                "breakeven_seconds_per_peak_passage",
                "keeps_parking",
            ],
        ),
    }


def feasibility(cfg: Appraisal, without: pd.DataFrame, two_buses_m: float, two_buses_mirrors_m: float, references: list[tuple[str, float]],
                places: tuple[float, float], supply_places: dict[int, float], lang_text: Callable[..., str]) -> pd.DataFrame:  # fmt: skip
    """The feasibility checks: the width one side's parking leaves against the vehicles and the design references, the
    places removed against the parking mapped nearby, and the statements of ``cfg.notes`` (law, plans, gaps)."""
    one_side = float(without.set_index("without").loc[["L", "R"], "free_median"].min())
    rows: list[dict[str, Any]] = [
        {"dimension": "technical", "check": lang_text("width_two_buses"), "value_m": one_side, "reference_m": two_buses_m,
         "status": "ok" if one_side >= two_buses_m else "short", "grade": "I", "source": "without_parking.csv, width_budget.csv"},
        {"dimension": "technical", "check": lang_text("width_two_buses_mirrors"), "value_m": one_side, "reference_m": two_buses_mirrors_m,
         "status": "ok" if one_side >= two_buses_mirrors_m else "short", "grade": "I", "source": "without_parking.csv, width_budget.csv"},
    ]  # fmt: skip
    rows += [
        {"dimension": "technical", "check": lang_text("width_reference", ref=name), "value_m": one_side, "reference_m": value,
         "status": "ok" if one_side >= value else "short", "grade": "D", "source": "standards_comparison.csv"}
        for name, value in references
    ]  # fmt: skip
    for radius, supply in sorted(supply_places.items()):
        rows.append(
            {"dimension": "social", "check": lang_text("places_share", radius=radius), "value_m": None, "reference_m": None,
             "share_low": places[0] / supply if supply else None, "share_high": places[1] / supply if supply else None, "status": "share",
             "grade": "I", "source": lang_text("places_share_source", n=round(supply))}
        )  # fmt: skip
    rows += [
        {
            "dimension": n.dimension,
            "check": n.text,
            "value_m": None,
            "reference_m": None,
            "status": "note",
            "grade": n.grade,
            "source": n.source,
        }
        for n in cfg.notes
    ]
    columns = ["dimension", "check", "value_m", "reference_m", "share_low", "share_high", "status", "grade", "source"]
    return pd.DataFrame(rows, columns=columns)
