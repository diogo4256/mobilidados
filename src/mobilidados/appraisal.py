"""Feasibility and cost-benefit appraisal of giving one parking strip back to the carriageway (``[appraisal]``).

The method follows the European Commission's *Economic Appraisal Vademecum 2021-2027*: an incremental economic
analysis of each option against doing nothing, at constant prices, over ``horizon_years``, discounted at the social
discount rate. Docs: docs/appraisal.md.

**Two layers.** The *core* counts only what the data measure or official documents state; the *extended* layer adds
the mechanisms the measurement cannot see yet, each with a sourced unit value, a stated range and a grade (``P``
until it is measured). The core is the extended layer with those mechanisms switched off (``MECHANISMS``), so the two
differ only by them, and each mechanism can be read off on its own.

**Benefits.** Time the buses no longer lose, valued for the passengers on board and for the operator:

* at the evening peak on working days: the ``delay`` stage's measured excess, times the share an option can remove
  (*attribution*, read from where the excess sits along the stretch and where buses give way to oncoming ones);
* (extended) at every other hour and day the option is in force: an excess of ``offpeak_s`` seconds per passage,
  removed in the same share, for the passages the timetable schedules then (``passages``: the reference week's hours,
  times the days of each kind in the reference year).

The passengers' time is weighted as congestion (``time_weight``), except (extended) the part that is unpredictable
(``unexpected_share``: buses held by an oncoming bus) and the time of those who change to a train or the metro
further on (``transfer_share``), weighted as lateness (``lateness_weight``). Also (extended): the occupants of the
cars held behind a bus (``cars_behind``), the new passengers a faster trip brings (``elasticity_ivt``: half their
gain, and the external costs of the car trips they leave, ``diversion_car`` × ``trip_km`` × ``external_cost_pkm``) and
the damage to buses and parked cars the narrowness causes (``damage_year``, in the same share and for the part of
the passages the option is in force).

**Costs.** The places removed, valued for whoever loses them: (extended) those who find a free place nearby
(``room_nearby``) lose a walk (``walk_cost``), the others what parking elsewhere costs (``car_value``); for the part of
the day the restriction applies, times how many places are occupied. The works (signs, markings, repainted
periodically, and (extended) traffic calming, ``calming_cost``) and, for a restriction by hours, its enforcement.
Benefits and the parking cost scale with compliance: a car that stays blocks the bus and keeps its place. Fees and
fares are transfers and stay out.

**Uncertainty.** Every input has a low, central and high value. For each layer: the central result, switching values,
a Monte Carlo simulation with PERT distributions (fixed seed, the same draws for every option); for the extended
layer, each input's swing (tornado) and the value of information: how much knowing each input before deciding is
worth (expected value of partial perfect information, from the simulation).

**Not priced** (``[[appraisal.criteria]]``, a multi-criteria table): quality of life, the street's noise and air,
access to the rail network, safety, emergency access, the municipal design references, equity. The weights between
them are the decision-maker's.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .config import Appraisal, Option

DAY_KINDS = ("working", "saturday", "sunday")

#: The mechanisms the measurement does not cover, and the value at which each is absent (the core layer).
MECHANISMS = {
    "offpeak_s": 0.0,
    "unexpected_share": 0.0,
    "transfer_share": 0.0,
    "cars_behind": 0.0,
    "elasticity_ivt": 0.0,
    "damage_year": 0.0,
    "room_nearby": 0.0,
    "calming_cost": 0.0,
}
#: Inputs that only matter through a mechanism; a case that leaves the mechanism out need not give them.
COMPANIONS = {
    "load_offpeak": "load_peak",
    "lateness_weight": "time_weight",
    "car_occupancy": 0.0,
    "journey_min": 1.0,
    "diversion_car": 0.0,
    "trip_km": 0.0,
    "external_cost_pkm": 0.0,
    "walk_cost": 0.0,
    "income_growth": 0.0,
}
LAYERS = ("core", "extended")
#: Elasticity of each stream's unit value to real income (GDP per capita), for its real growth over the years (EAV
#: 2021-2027, p. 59: 1 for values of time set from Eurostat labour costs; 0.8 for externalities other than CO2).
#: The operator's cost (mostly wages) and the value of a place to whoever parks are given 1 too, so that both sides of
#: the account grow alike; damage, works and enforcement are held at their prices.
GROWTH = {"time": 1.0, "operator": 1.0, "external": 0.8, "parking": 1.0}
#: DfT Value for Money Framework (May 2025), box 5.1: lower bound of each category's benefit-cost ratio.
VFM_CATEGORIES = (("very_high", 4.0), ("high", 2.0), ("medium", 1.5), ("low", 1.0), ("poor", 0.0))


@dataclass(frozen=True)
class Measured:
    """What the appraisal takes from the run's tables (all measured or inferred from data, none typed in)."""

    excess_s: tuple[float, float, float]  # the peak excess per passage: 90% low, estimate, 90% high
    peak_passages_per_day: float  # buses the timetable schedules through the street at peak on a working day
    working_days: int  # in the reference year, without the city's holidays
    attribution: dict[str, tuple[float, float, float]]  # option id -> low, central, high
    metres: dict[str, float]  # option id -> metres of parking strip removed (one side, in its sections)
    passages: dict[str, tuple[float, float]]  # option id -> passages a year while it is in force: (at peak, other)
    passages_year: float  # every passage of the year


def working_days(year: int, holidays: list[dt.date]) -> int:
    """Monday to Friday in ``year``, without the holidays that fall on them."""
    first, off = dt.date(year, 1, 1), set(holidays)
    days = (first + dt.timedelta(days=i) for i in range((dt.date(year + 1, 1, 1) - first).days))
    return sum(1 for d in days if d.weekday() < 5 and d not in off)


def day_counts(year: int, holidays: list[dt.date]) -> dict[str, int]:
    """Days of ``year`` by the timetable they run: working days, Saturdays, and Sundays with the holidays (a holiday
    runs the Sunday timetable)."""
    first, off = dt.date(year, 1, 1), set(holidays)
    out = dict.fromkeys(DAY_KINDS, 0)
    for i in range((dt.date(year + 1, 1, 1) - first).days):
        d = first + dt.timedelta(days=i)
        out["sunday" if d in off or d.weekday() == 6 else "saturday" if d.weekday() == 5 else "working"] += 1
    return out


def passages(hourly: pd.DataFrame, days: dict[str, int], option: Option | None, peak_hours: list[int]) -> tuple[float, float]:
    """Passages a year (at peak, at other times) in the hours and days ``option`` is in force (None: always).

    ``hourly`` has a row per day kind and clock hour with the passages the timetable schedules on a representative day
    of that kind (columns ``day_kind``, ``hour``, ``passages``). The peak is ``peak_hours`` on working days."""
    a, b = option.hours if option else (0, 24)
    kinds = ("working",) if option and option.days == "working" else DAY_KINDS
    peak = other = 0.0
    for r in hourly.itertuples():
        if r.day_kind not in kinds or not a <= r.hour < b:
            continue
        n = r.passages * days[r.day_kind]
        if r.day_kind == "working" and r.hour in peak_hours:
            peak += n
        else:
            other += n
    return peak, other


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
    ``delay_copresence``, ``passings`` (the service day), ``appraisal_passages`` (the reference week, by hour) and the
    metres of each block's sections with parking on both sides."""
    whole = tables["delay_summary"].astype({"scope": str}).set_index("scope").loc["all"]
    passings = tables["passings"]
    peak = passings[(passings.t // 3600).isin(peak_hours)]
    days = day_counts(year, holidays)
    hourly = tables["appraisal_passages"]
    return Measured(
        excess_s=(float(whole.excess_ci90_low_s), float(whole.excess_s), float(whole.excess_ci90_high_s)),
        peak_passages_per_day=float(len(peak)),
        working_days=days["working"],
        attribution={
            o.id: attribution(tables["delay_by_part"], tables["delay_copresence"], o.blocks, cfg.significance) for o in cfg.options
        },
        metres={o.id: round(sum(block_metres.get(b, 0.0) for b in o.blocks), 1) for o in cfg.options},
        passages={o.id: passages(hourly, days, o, peak_hours) for o in cfg.options},
        passages_year=sum(passages(hourly, days, None, peak_hours)),
    )


# --- the model ---------------------------------------------------------------------------------------------------------
def central(cfg: Appraisal, m: Measured) -> dict[str, float]:
    """Every input at its central value, keyed as ``evaluate`` reads them."""
    return {k: v[1] for k, v in ranges(cfg, m).items()}


def ranges(cfg: Appraisal, m: Measured) -> dict[str, tuple[float, float, float]]:
    """Every input's low, central and high value."""
    r = {k: (v.low, v.central, v.high) for k, v in cfg.parameters.items()}
    r["excess_s"] = m.excess_s
    r |= {f"attribution_{o}": a for o, a in m.attribution.items()}
    return r


def layer(p: dict[str, Any], name: str) -> dict[str, Any]:
    """The inputs ``evaluate`` reads for a layer: the core switches every mechanism off; a mechanism the case does not
    configure is off in both; an input that only serves a mechanism the case leaves out takes a neutral value."""
    q = dict(p)
    for k, off in MECHANISMS.items():
        if name == "core" or k not in q:
            q[k] = off
    for k, default in COMPANIONS.items():
        if k not in q:
            q[k] = q[default] if isinstance(default, str) else default
    return q


def _num(x: Any) -> Any:
    """A scalar stays a float; an array of draws stays an array."""
    return float(x) if np.ndim(x) == 0 else x


def _ratio(a: Any, b: Any) -> Any:
    """a / b, and 0 where b is 0 (no passenger, no saving per passenger)."""
    b = np.asarray(b, dtype=float)
    return np.where(b > 0, np.asarray(a, dtype=float) / np.where(b > 0, b, 1.0), 0.0)


def evaluate(o: Option, p: dict[str, Any], m: Measured, cfg: Appraisal, rate: float | None = None) -> dict[str, Any]:
    """One option's yearly flows, present values, net present value and benefit-cost ratio for inputs ``p`` (pass them
    through ``layer``). Every input may be a number or an array of draws: the arithmetic is the same."""
    r = cfg.discount_rate if rate is None else rate
    years = np.arange(1, cfg.horizon_years + 1)
    annuity = float(np.sum((1 + r) ** -years.astype(float)))
    g = p["income_growth"]

    def growing(kind: str) -> Any:
        """The present value of 1 a year whose unit value grows with income at the elasticity of ``kind``."""
        return sum((1 + g) ** (GROWTH[kind] * t) / (1 + r) ** t for t in range(1, cfg.horizon_years + 1))

    comply = p[o.compliance]
    peak_y, other_y = m.passages[o.id]
    share_removed = p[f"attribution_{o.id}"]  # where the time is lost along the stretch: the same at every hour
    peak_bh = p["excess_s"] * share_removed * peak_y / 3600 * comply
    other_bh = p["offpeak_s"] * share_removed * other_y / 3600 * comply
    bus_hours = peak_bh + other_bh
    on_board_h = peak_bh * p["load_peak"] + other_bh * p["load_offpeak"]
    passenger_hours = on_board_h * p["downstream"]
    late = 1 - (1 - p["unexpected_share"]) * (1 - p["transfer_share"])  # the share of their time weighted as lateness
    weight = p["time_weight"] + (p["lateness_weight"] - p["time_weight"]) * late
    time_value = passenger_hours * p["vot"] * weight
    operator_value = bus_hours * p["bus_cost_h"]
    car_hours = bus_hours * p["cars_behind"] * p["car_occupancy"]
    traffic_value = car_hours * p["vot"] * p["time_weight"]
    riders = peak_y * p["load_peak"] + other_y * p["load_offpeak"]
    saved_s = _ratio(3600 * on_board_h, riders)  # seconds saved per passenger on these buses
    new_riders = p["elasticity_ivt"] * saved_s / (p["journey_min"] * 60) * riders
    new_rider_value = 0.5 * new_riders * saved_s / 3600 * p["vot"] * p["time_weight"]  # the rule of a half
    external_value = new_riders * p["diversion_car"] * p["trip_km"] * p["external_cost_pkm"]
    in_force = (peak_y + other_y) / m.passages_year if m.passages_year else 0.0
    damage_value = p["damage_year"] * share_removed * in_force * comply
    benefit = time_value + operator_value + traffic_value + new_rider_value + external_value + damage_value
    places = m.metres[o.id] / p["stall_m"]
    share = p[o.parking_share] if o.parking_share else 1.0
    place_value = p["room_nearby"] * p["walk_cost"] + (1 - p["room_nearby"]) * p["car_value"]
    parking = places * p["occupancy"] * place_value * share * comply
    enforcement = p["enforcement_year"] if (o.days != "all" or o.hours != (0, 24)) else 0.0 * comply
    marking = m.metres[o.id] * p["marking_cost_m"]
    works = o.signs * p["sign_cost"] + marking + p["calming_cost"]
    repaints = range(cfg.repaint_every_years, cfg.horizon_years + 1, cfg.repaint_every_years)
    repaint_pv = sum(0.5 * marking * (1 + r) ** -t for t in repaints)  # half the marking, every few years
    pv_time, pv_traffic, pv_new = (x * growing("time") for x in (time_value, traffic_value, new_rider_value))
    pv_operator, pv_external, pv_damage = operator_value * growing("operator"), external_value * growing("external"), damage_value * annuity
    pv_benefit = pv_time + pv_operator + pv_traffic + pv_new + pv_external + pv_damage
    pv_parking = parking * growing("parking")
    pv_works, pv_enforcement = works + repaint_pv, enforcement * annuity
    pv_public = pv_works + pv_enforcement
    pv_cost = pv_parking + pv_public
    flows = {
        "bus_hours": bus_hours,
        "passenger_hours": passenger_hours,
        "riders": riders,
        "saved_s_per_passenger": saved_s,
        "new_riders": new_riders,
        "car_hours": car_hours,
        "time_value": time_value,
        "operator_value": operator_value,
        "traffic_value": traffic_value,
        "new_rider_value": new_rider_value,
        "external_value": external_value,
        "damage_value": damage_value,
        "benefit_year": benefit,
        "places": places,
        "parking_year": parking,
        "enforcement_year": enforcement,
        "works": works,
        "pv_benefit": pv_benefit,
        "pv_cost": pv_cost,
        "pv_time": pv_time,
        "pv_operator": pv_operator,
        "pv_traffic": pv_traffic,
        "pv_new_riders": pv_new,
        "pv_external": pv_external,
        "pv_damage": pv_damage,
        "pv_parking": pv_parking,
        "pv_works": pv_works,
        "pv_enforcement": pv_enforcement,
        "pv_public": pv_public,
        "npv": pv_benefit - pv_cost,
        "bcr": pv_benefit / pv_cost,
        # the DfT's ratio: the parking lost is a disbenefit to its users, the cost is what the public budget pays
        "bcr_budget": (pv_benefit - pv_parking) / pv_public,
    }
    return {k: _num(v) for k, v in flows.items()}


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


def option_inputs(o: Option, cfg: Appraisal, name: str = "extended") -> list[str]:
    """The inputs an option's value depends on in a layer: the parking share and compliance it names, the shared ones
    and, in the extended layer, the configured mechanisms and their companions."""
    shared = ["excess_s", f"attribution_{o.id}", "load_peak", "downstream", "vot", "time_weight", "bus_cost_h", "stall_m", "occupancy",
              "car_value", "sign_cost", "marking_cost_m"]  # fmt: skip
    timed = o.days != "all" or o.hours != (0, 24)
    own = ([o.parking_share] if o.parking_share else []) + [o.compliance] + (["enforcement_year"] if timed else [])
    extra = [k for k in [*MECHANISMS, *COMPANIONS] if k in cfg.parameters] if name == "extended" else []
    growth = ["income_growth"] if "income_growth" in cfg.parameters and name == "core" else []
    return shared + own + growth + extra


def pert(rng: np.random.Generator, lo: float, mode: float, hi: float, size: int) -> np.ndarray:
    """Draws from the PERT distribution on [lo, hi] with its mode at ``mode``: a beta distribution with
    α = 1 + 4 (mode − lo)/(hi − lo) and β = 1 + 4 (hi − mode)/(hi − lo), so the mean is (lo + 4 mode + hi)/6.

    The usual distribution for a three-point estimate in project risk analysis: unlike the triangular one, it keeps
    most of its weight near the central value, so a long range on one side (a place worth up to a garage's rent) does
    not drag the mean far from the value the evidence points to."""
    if hi == lo:
        return np.full(size, mode)
    a = 1 + 4 * (mode - lo) / (hi - lo)
    b = 1 + 4 * (hi - mode) / (hi - lo)
    return lo + (hi - lo) * rng.beta(a, b, size)


def draws(cfg: Appraisal, m: Measured) -> dict[str, np.ndarray]:
    """``cfg.draws`` draws of every input from its PERT distribution (fixed seed). Inputs that ``cfg.correlations``
    pairs are then reordered so their ranks follow a correlated normal pair (Iman-Conover): each keeps its own
    distribution, and the two move together."""
    rng = np.random.default_rng(cfg.seed)
    d = {k: pert(rng, lo, c, hi, cfg.draws) for k, (lo, c, hi) in sorted(ranges(cfg, m).items())}
    for pair in cfg.correlations:
        z1 = rng.standard_normal(cfg.draws)
        z2 = pair.rho * z1 + np.sqrt(1 - pair.rho**2) * rng.standard_normal(cfg.draws)
        for key, z in ((pair.a, z1), (pair.b, z2)):
            d[key] = np.sort(d[key])[np.argsort(np.argsort(z))]
    return d


def simulate(cfg: Appraisal, m: Measured, d: dict[str, np.ndarray], name: str) -> pd.DataFrame:
    """Net present value of every option in each draw of ``d``, in a layer. The same draws serve every option, so the
    options are compared on the same uncertain world."""
    q = layer(d, name)
    return pd.DataFrame({o.id: np.broadcast_to(evaluate(o, q, m, cfg)["npv"], (cfg.draws,)) for o in cfg.options})


def value_of_information(sims: pd.DataFrame, d: dict[str, np.ndarray], bins: int = 20) -> pd.DataFrame:
    """How much knowing each input before deciding is worth: the expected value of partial perfect information.

    The decision is to do the best option or nothing. Without more information it is worth max(0, best mean NPV);
    knowing input k exactly, the decision is taken for each value of k, worth the mean of max(0, best mean NPV given
    k). The difference, never negative, is estimated by cutting the draws into ``bins`` groups of equal size by k. The
    expected value of perfect information (all inputs known) bounds them all."""
    base = max(0.0, float(sims.mean().max()))
    evpi = float(np.maximum(sims.max(axis=1), 0).mean()) - base
    rows = [{"input": "(all)", "evppi": evpi}]
    for k, x in sorted(d.items()):
        if np.ptp(x) == 0:
            continue
        group = pd.Series(pd.qcut(pd.Series(x).rank(method="first"), bins, labels=False), index=sims.index)
        informed = float(np.maximum(sims.groupby(group).mean().max(axis=1), 0).mean())
        rows.append({"input": k, "evppi": max(informed - base, 0.0)})
    out = pd.DataFrame(rows)
    return out.sort_values("evppi", ascending=False, kind="stable").reset_index(drop=True)


def distribution(cfg: Appraisal, m: Measured, c: dict[str, float]) -> pd.DataFrame:
    """Who gains and who loses a year, per option, at the central values of the extended layer."""
    q = layer(c, "extended")
    annuity = float(np.sum((1 + cfg.discount_rate) ** -np.arange(1, cfg.horizon_years + 1, dtype=float)))
    rows = []
    for o in cfg.options:
        e = evaluate(o, q, m, cfg)
        works_year = e["works"] / annuity
        rows += [
            {"option": o.id, "group": "passengers", "people": e["riders"], "quantity": e["passenger_hours"], "unit": "h", "value": e["time_value"]},
            {"option": o.id, "group": "operator", "people": None, "quantity": e["bus_hours"], "unit": "bus-h", "value": e["operator_value"]},
            {"option": o.id, "group": "drivers_behind", "people": None, "quantity": e["car_hours"], "unit": "h", "value": e["traffic_value"]},
            {"option": o.id, "group": "new_passengers", "people": e["new_riders"], "quantity": None, "unit": "", "value": e["new_rider_value"]},
            {"option": o.id, "group": "society", "people": None, "quantity": None, "unit": "", "value": e["external_value"]},
            {"option": o.id, "group": "vehicle_owners", "people": None, "quantity": None, "unit": "", "value": e["damage_value"]},
            {"option": o.id, "group": "parkers", "people": e["places"], "quantity": e["places"], "unit": "places", "value": -e["parking_year"]},
            {"option": o.id, "group": "public_bodies", "people": None, "quantity": None, "unit": "", "value": -(e["enforcement_year"] + works_year)},
        ]  # fmt: skip
    return pd.DataFrame(rows)


def vfm_category(bcr_budget: float, npv: float) -> str:
    """The DfT value-for-money category of a benefit-cost ratio to the public budget (``very_poor`` below 0)."""
    if npv < 0 and bcr_budget < 0:
        return "very_poor"
    return next((name for name, low in VFM_CATEGORIES if bcr_budget >= low), "very_poor")


def bridge(cfg: Appraisal, m: Measured, c: dict[str, float]) -> pd.DataFrame:
    """From the core's NPV to the extended layer's, one mechanism at a time (in the order of ``MECHANISMS``), at central
    values: how much of the difference each mechanism makes. With the interactions between them, a step depends on the
    ones before it; the order is fixed so the table is the same in every run."""
    rows = []
    for o in cfg.options:
        q = layer(c, "core")
        npv = float(evaluate(o, q, m, cfg)["npv"])
        rows.append({"option": o.id, "step": "core", "npv": npv, "change": npv})
        for k in MECHANISMS:
            if k not in cfg.parameters:
                continue
            q = q | {k: c[k]}
            after = float(evaluate(o, q, m, cfg)["npv"])
            rows.append({"option": o.id, "step": k, "npv": after, "change": after - npv})
            npv = after
    return pd.DataFrame(rows)


def criteria_table(cfg: Appraisal) -> pd.DataFrame:
    """The effects not priced: one row per criterion, one column per option."""
    rows = []
    for c in cfg.criteria:
        row: dict[str, Any] = {"criterion": c.id, "dimension": c.dimension, "label": c.label, "indicator": c.indicator}
        row |= {o.id: c.effects.get(o.id, c.effects.get("*", "?")) for o in cfg.options}
        rows.append(row | {"grade": c.grade, "note": c.note, "source": c.source})
    return pd.DataFrame(
        rows, columns=["criterion", "dimension", "label", "indicator", *[o.id for o in cfg.options], "grade", "note", "source"]
    )


def scenarios(cfg: Appraisal, m: Measured, c: dict[str, float]) -> pd.DataFrame:
    """Each option's NPV in named scenarios: the core; the extended layer with every input the measurement does not
    cover at the end of its range that is least favourable to the option (*cautious*), at its central value, and at the
    most favourable end (*favourable*); and the central extended layer over each of ``cfg.horizons_tested`` years.
    Which end is least favourable is read input by input, the others central, so the cautious scenario is the
    worst combination of those ends, not a probability."""
    rg = ranges(cfg, m)
    unmeasured = [k for k in [*MECHANISMS, *COMPANIONS] if k in cfg.parameters]
    rows = []
    for o in cfg.options:
        central_q = layer(c, "extended")

        def npv(q: dict[str, Any], conf: Appraisal = cfg, opt: Option = o) -> float:
            return float(evaluate(opt, q, m, conf)["npv"])

        worst, best = dict(central_q), dict(central_q)
        for k in unmeasured:
            lo, _, hi = rg[k]
            at_lo, at_hi = npv(central_q | {k: lo}), npv(central_q | {k: hi})
            worst[k], best[k] = (lo, hi) if at_lo <= at_hi else (hi, lo)
        rows += [
            {"option": o.id, "scenario": "core", "years": cfg.horizon_years, "npv": npv(layer(c, "core"))},
            {"option": o.id, "scenario": "cautious", "years": cfg.horizon_years, "npv": npv(worst)},
            {"option": o.id, "scenario": "central", "years": cfg.horizon_years, "npv": npv(central_q)},
            {"option": o.id, "scenario": "favourable", "years": cfg.horizon_years, "npv": npv(best)},
        ]
        for h in cfg.horizons_tested:
            longer = cfg.model_copy(update={"horizon_years": h})
            rows += [
                {"option": o.id, "scenario": "core", "years": h, "npv": npv(layer(c, "core"), longer)},
                {"option": o.id, "scenario": "central", "years": h, "npv": npv(central_q, longer)},
            ]
    return pd.DataFrame(rows)


def appraise(cfg: Appraisal, m: Measured) -> dict[str, pd.DataFrame]:
    """Every table of the appraisal (see ``docs/appraisal.md``)."""
    c, rg = central(cfg, m), ranges(cfg, m)
    results, switching, tornado, mc = [], [], [], []
    d = draws(cfg, m)
    sims = {name: simulate(cfg, m, d, name) for name in LAYERS}
    for name in LAYERS:
        q = layer(c, name)
        for o in cfg.options:
            e = evaluate(o, q, m, cfg)
            lo_a, ce_a, hi_a = m.attribution[o.id]
            results.append(
                {"layer": name, "option": o.id, "label": o.label, "metres": m.metres[o.id], "passages_peak": m.passages[o.id][0],
                 "passages_other": m.passages[o.id][1], "attribution_low": lo_a, "attribution": ce_a, "attribution_high": hi_a}
                | e
                | {"vfm": vfm_category(e["bcr_budget"], e["npv"])}
                | {f"npv_at_{int(r * 100)}pct": evaluate(o, q, m, cfg, rate=r)["npv"] for r in cfg.discount_rates_tested}
            )  # fmt: skip
            for k in option_inputs(o, cfg, name):
                lo, ce, hi = rg[k]

                def npv_at(x: float, key: str = k, opt: Option = o, base: dict[str, Any] = q) -> float:
                    return float(evaluate(opt, base | {key: x}, m, cfg)["npv"])

                sv = switching_value(npv_at, *search_domain(lo, hi))
                switching.append({"layer": name, "option": o.id, "input": k, "central": ce, "switching_value": sv,
                                  "within_range": sv is not None and lo <= sv <= hi})  # fmt: skip
                if name == "extended":
                    tornado.append({"option": o.id, "input": k, "low": lo, "high": hi, "npv_at_low": npv_at(lo), "npv_at_high": npv_at(hi)})
        s = sims[name]
        mc += [
            {"layer": name, "option": k, "mean": float(v.mean()), "p10": float(v.quantile(0.10)), "p50": float(v.median()),
             "p90": float(v.quantile(0.90)), "probability_positive": float((v > 0).mean()), "probability_best": float((s.idxmax(axis=1) == k).mean())}
            for k, v in s.items()
        ]  # fmt: skip
    core = layer(c, "core")
    value_bus_hour = core["load_peak"] * core["downstream"] * core["vot"] * core["time_weight"] + core["bus_cost_h"]
    annuity = float(np.sum((1 + cfg.discount_rate) ** -np.arange(1, cfg.horizon_years + 1, dtype=float)))
    alternatives = []
    peak_year = m.peak_passages_per_day * m.working_days  # 0 where no bus is scheduled at peak: no time to save per passage
    for alt in cfg.alternatives:
        parking = alt.parking_m / core["stall_m"] * core["occupancy"] * core["car_value"]
        pv_cost = alt.signs * core["sign_cost"] + alt.works + (alt.yearly + parking) * annuity
        hours = pv_cost / annuity / value_bus_hour
        alternatives.append(
            {"alternative": alt.id, "label": alt.label, "parking_m": alt.parking_m, "places": alt.parking_m / core["stall_m"], "pv_cost": pv_cost,
             "value_per_bus_hour": value_bus_hour, "breakeven_bus_hours_per_year": hours,
             "breakeven_seconds_per_peak_passage": hours * 3600 / peak_year if peak_year else np.nan,
             "breakeven_seconds_per_passage": hours * 3600 / m.passages_year if m.passages_year else np.nan}
        )  # fmt: skip
    tor = pd.DataFrame(tornado, columns=["option", "input", "low", "high", "npv_at_low", "npv_at_high"])
    tor["swing"] = (tor.npv_at_high - tor.npv_at_low).abs()
    inputs = [
        {"input": k, "low": lo, "central": ce, "high": hi, "grade": cfg.parameters[k].grade, "unit": cfg.parameters[k].unit,
         "label": cfg.parameters[k].label, "source": cfg.parameters[k].source, "layer": "extended" if k in MECHANISMS or k in COMPANIONS else "core"}
        for k, (lo, ce, hi) in rg.items()
        if k in cfg.parameters
    ]  # fmt: skip
    alt_columns = ["alternative", "label", "parking_m", "places", "pv_cost", "value_per_bus_hour", "breakeven_bus_hours_per_year",
                   "breakeven_seconds_per_peak_passage", "breakeven_seconds_per_passage"]  # fmt: skip
    return {
        "appraisal_inputs": pd.DataFrame(inputs),
        "appraisal_results": pd.DataFrame(results),
        "appraisal_switching": pd.DataFrame(switching),
        "appraisal_tornado": tor.sort_values(["option", "swing"], ascending=[True, False]).reset_index(drop=True),
        "appraisal_montecarlo": pd.DataFrame(mc),
        "appraisal_voi": value_of_information(sims["extended"], d),
        "appraisal_distribution": distribution(cfg, m, c),
        "appraisal_bridge": bridge(cfg, m, c),
        "appraisal_scenarios": scenarios(cfg, m, c),
        "appraisal_criteria": criteria_table(cfg),
        "appraisal_alternatives": pd.DataFrame(alternatives, columns=alt_columns),
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
