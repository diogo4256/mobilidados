"""Time buses spend on a stretch of the street, measured from archived vehicle positions (``[delay]``).

**Data.** Snapshots of a real-time feed (GTFS-RT vehicle positions), minutes apart (``archive``). A snapshot is far
too sparse to follow one bus through a street a few hundred metres long; the estimator uses all of them together.

**Estimator (occupancy).** If buses pass a stretch at a rate λ (passages per second) and each spends on average W
seconds on it, then at any instant the expected number of buses on the stretch is λ·W (Little's law). The
snapshots are taken at times set by the archive's schedule, not by where the buses are, so over a set of snapshots

    buses seen on the stretch  ≈  W · Σ λ(t)   (the sum over the snapshots)

and W is the count divided by the *exposure* Σ λ(t).

**What is compared.** The stretch is compared with *control* stretches of the same routes, before and after it
along each route's shape (``control_gap_m`` away, ``control_m`` long), at the evening peak and off-peak on weekdays:

    ratio = (on stretch at peak / on controls at peak) / (on stretch off-peak / on controls off-peak)

The same buses pass the stretch and its controls minutes apart, so λ and the snapshot cadence cancel: the ratio
needs neither. It says how much longer the stretch takes at peak than the controls' own peak slowdown would make
it take. In seconds, per passage at peak:

    excess = W_peak − W_off · (W_controls,peak / W_controls,off) = (n_peak − n_off · c_peak / c_off) / exposure_peak

where n and c are the positions seen on the stretch and on the controls. Only the exposure at peak needs λ.

**λ.** For each route and direction, the trips seen on its shape within ``reach_m`` of the stretch, each counted
once, in the hour of the position nearest the stretch. A trip is only sure to be seen if the archive has a
snapshot often enough: the counts (and so every number in seconds, and the ratio, for coherence) use only the hours
whose snapshots are never more than ``max_gap_s`` apart, from the start of the hour to its end.

**Positions.** A position counts only if the vehicle reported it at most ``max_age_s`` before the snapshot (an
older one repeats a past position, which would be counted twice) and lies within ``max_offset_m`` of its route's
shape in the GTFS feed (a diverted trip is left out).

**Uncertainty.** A bootstrap over days (whole days are resampled, so positions of the same day stay together), with
a fixed seed: the 5th and 95th percentiles of the resampled estimates.

**What it is not.** It measures where the time goes, not why: a stretch can be slow at peak because of the parked
cars, the buses in the other direction, a queue from the junction at its end, or a traffic light. It is the
operation as recorded in the archive, not the timetable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import LineString

from .archive import SNAPSHOT_TIME
from .config import Delay, MobilidadosError
from .gtfs import Feed

PEAK, OFF = "peak", "off_peak"
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
STRETCH, CONTROL = "stretch", "control"


@dataclass(frozen=True)
class Route:
    """One route and direction: its shape and where the stretch, its controls and its reach lie along it (m)."""

    route_id: str
    direction_id: int
    route: str  # the route's short name, as the case lists it
    shape_id: str
    line: LineString
    stretch: tuple[float, float]
    controls: tuple[tuple[float, float], ...]
    reach: tuple[float, float]

    @property
    def key(self) -> str:
        return f"{self.route} {self.direction_id}"


def routes(feed: Feed, names: list[str], axis: LineString, crs: int, cfg: Delay) -> list[Route]:
    """Each route of ``names`` and direction with trips in the feed, on its most frequent shape, with its windows.

    The stretch is where the axis between ``cfg.s_from`` and ``cfg.s_to`` lies along the shape. A shape that does not
    run along the stretch, or does not reach far enough for both controls, is an error naming it.
    """
    trips = feed.table("trips", dtype=str).merge(feed.table("routes", dtype=str)[["route_id", "route_short_name"]], on="route_id")
    trips = trips[trips.route_short_name.isin(names)]
    shapes = feed.table("shapes", dtype={"shape_id": str})
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    a, b = axis.interpolate(cfg.s_from), axis.interpolate(cfg.s_to)
    out = []
    for (route_id, direction), g in trips.groupby(["route_id", "direction_id"]):
        shape_id = str(g.shape_id.value_counts().index[0])
        pts = shapes[shapes.shape_id == shape_id].sort_values("shape_pt_sequence")
        x, y = tr.transform(pts.shape_pt_lon.to_numpy(), pts.shape_pt_lat.to_numpy())
        line = LineString(np.c_[x, y])
        name = str(g.route_short_name.iloc[0])
        if max(line.distance(a), line.distance(b)) > cfg.max_offset_m:
            continue  # this direction does not run along the stretch (e.g. a variant of the route)
        m0, m1 = sorted((line.project(a), line.project(b)))
        lo, hi = m0 - cfg.control_gap_m - cfg.control_m, m1 + cfg.control_gap_m + cfg.control_m
        if lo < 0 or hi > line.length:
            raise MobilidadosError(
                f"delay: route {name} direction {direction} (shape {shape_id}) does not run {cfg.control_gap_m + cfg.control_m:g} m "
                "before and after the stretch, which its control stretches need; lower delay.control_m or delay.control_gap_m"
            )
        controls = ((lo, m0 - cfg.control_gap_m), (m1 + cfg.control_gap_m, hi))
        reach = (max(m0 - cfg.reach_m, 0.0), min(m1 + cfg.reach_m, line.length))
        out.append(Route(str(route_id), int(direction), name, shape_id, line, (m0, m1), controls, reach))
    missing = sorted(set(names) - {r.route for r in out})
    if missing:
        raise MobilidadosError(
            f"delay: routes {missing} have no direction whose shape runs along the stretch s = {cfg.s_from:g}–{cfg.s_to:g} m"
        )
    return sorted(out, key=lambda r: (r.route, r.direction_id))


def load(positions: pd.DataFrame, snapshots: pd.DataFrame, tz: str, source_tz: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse the archive's text: snapshot and report times (in ``source_tz``) to UTC and to local time ``tz``.

    Snapshots where the feed listed no vehicle at all are left out (the feed did not answer)."""
    snaps = snapshots[snapshots.vehicles > 0].copy()
    snaps["t"] = pd.to_datetime(snaps.snapshot, format=SNAPSHOT_TIME).dt.tz_localize(source_tz).dt.tz_convert("UTC")
    snaps["local"] = snaps.t.dt.tz_convert(tz)
    pos = positions[positions.snapshot.isin(set(snaps.snapshot))].copy()
    pos["t"] = pd.to_datetime(pos.snapshot, format=SNAPSHOT_TIME).dt.tz_localize(source_tz).dt.tz_convert("UTC")
    # the collector writes report times as "YYYY-MM-DD HH:MM:SS"; anything else is left out (NaT), never guessed
    reported = pd.to_datetime(pos.timestamp, errors="coerce", format="%Y-%m-%d %H:%M:%S")
    pos["age_s"] = (pos.t - reported.dt.tz_localize(source_tz).dt.tz_convert("UTC")).dt.total_seconds()
    pos["local"] = pos.t.dt.tz_convert(tz)
    return pos, snaps


def place(pos: pd.DataFrame, rts: list[Route], crs: int, max_offset_m: float) -> pd.DataFrame:
    """Each position of a route and direction of ``rts``, with ``m`` (along its shape) and ``offset`` (from it)."""
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    lat = pd.to_numeric(pos.latitude, errors="coerce")
    lon = pd.to_numeric(pos.longitude, errors="coerce")
    ok = lat.notna() & lon.notna()
    pos = pos[ok].copy()
    x, y = tr.transform(lon[ok].to_numpy(), lat[ok].to_numpy())
    pts = shapely.points(x, y)
    pos["key"], pos["m"], pos["offset"] = "", np.nan, np.nan
    direction = pd.to_numeric(pos.direction_id, errors="coerce")
    for r in rts:
        sel = ((pos.route_id == r.route_id) & (direction == r.direction_id)).to_numpy()
        pos.loc[sel, "key"] = r.key
        pos.loc[sel, "m"] = shapely.line_locate_point(r.line, pts[sel])
        pos.loc[sel, "offset"] = shapely.distance(r.line, pts[sel])
    return pos[(pos.key != "") & (pos.offset <= max_offset_m)]


def where(pos: pd.DataFrame, rts: list[Route]) -> pd.Series:
    """``stretch``, ``control`` or ``""`` for each placed position."""
    out = pd.Series("", index=pos.index, dtype=object)
    for r in rts:
        mine = pos.key == r.key
        out[mine & pos.m.between(*r.stretch, inclusive="left")] = STRETCH
        for lo, hi in r.controls:
            out[mine & pos.m.between(lo, hi, inclusive="left")] = CONTROL
    return out


def covered_hours(snaps: pd.DataFrame, max_gap_s: float) -> set[pd.Timestamp]:
    """The hours (keyed by their start in UTC, so the hour repeated when clocks go back is two hours) whose snapshots
    are never more than ``max_gap_s`` apart, counting from the start of the hour to the first snapshot and from the
    last to the end of the hour."""
    if snaps.empty:
        return set()
    sec = pd.DataFrame({"slot": snaps.slot, "t": (snaps.t - EPOCH).dt.total_seconds()}).sort_values(["slot", "t"])
    start = (sec.slot - EPOCH).dt.total_seconds()
    inner = sec.t.diff().where(sec.slot.eq(sec.slot.shift()))  # between snapshots of the same hour
    g = pd.DataFrame({"slot": sec.slot, "inner": inner, "t": sec.t, "start": start}).groupby("slot")
    worst = pd.concat([g.inner.max(), g.t.min() - g.start.first(), g.start.first() + 3600 - g.t.max()], axis=1).max(axis=1)
    return {pd.Timestamp(x) for x in worst[worst <= max_gap_s].index}


def trips_per_hour(pos: pd.DataFrame, rts: list[Route]) -> pd.DataFrame:
    """Trips seen within reach of the stretch, per route and direction and hour (``slot``): each trip once, in the
    hour of its position nearest the middle of the stretch."""
    rows = []
    for r in rts:
        p = pos[(pos.key == r.key) & pos.m.between(*r.reach)]
        if p.empty:
            continue
        mid = sum(r.stretch) / 2
        near = p.assign(d=(p.m - mid).abs()).sort_values("d").drop_duplicates(["trip_id", "date"])
        rows.append(near.groupby("slot").size().rename("trips").reset_index().assign(key=r.key))
    if not rows:  # no trip seen at all: an empty table whose hour column can still be joined on
        return pd.DataFrame({"slot": pd.Series(dtype=pos.slot.dtype), "trips": pd.Series(dtype=int), "key": pd.Series(dtype=object)})
    return pd.concat(rows, ignore_index=True)


def period_of(hour: pd.Series, cfg: Delay) -> pd.Series:
    return pd.Series(np.where(hour.isin(cfg.peak_hours), PEAK, np.where(hour.isin(cfg.off_peak_hours), OFF, "")), index=hour.index)


def prepare(pos: pd.DataFrame, snaps: pd.DataFrame, cfg: Delay) -> None:
    """Add to positions and snapshots their hour (``slot``: its start in UTC, so the hour repeated when clocks go back
    is two hours; Lisbon's offsets are whole hours), local ``date`` and ``hour``, and ``weekday`` (a working day)."""
    excluded = set(cfg.exclude_dates)
    for df in (pos, snaps):
        df["slot"] = df.t.dt.floor("h")
        local = df.slot.dt.tz_convert(cfg.time_zone)
        df["date"], df["hour"] = local.dt.date, local.dt.hour
        df["weekday"] = (local.dt.day_of_week < 5) & ~df.date.isin(excluded)


def daily(pos: pd.DataFrame, snaps: pd.DataFrame, rts: list[Route], cfg: Delay) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Per working day, period and route/direction: positions on the stretch (``n``) and on the controls (``c``) over
    every snapshot, and over the covered hours only (``n_cov``, ``c_cov``), with the passages counted in those hours
    (``trips``) and the exposure (Σ λ over their snapshots). ``prepare`` must have run. Also returns the counts behind
    the selection."""
    fresh = pos[pos.age_s.abs() <= cfg.max_age_s]
    covered = covered_hours(snaps, cfg.max_gap_s)
    work = snaps[snaps.weekday & ~snaps.date.isin(set(cfg.exclude_dates))].assign(period=lambda d: period_of(d.hour, cfg))
    work = work[work.period != ""].assign(covered=lambda d: d.slot.isin(covered))
    placed = fresh.assign(where=where(fresh, rts))
    placed = placed[placed.snapshot.isin(set(work.snapshot)) & (placed["where"] != "")]
    placed = placed.assign(period=lambda d: period_of(d.hour, cfg), covered=lambda d: d.slot.isin(covered))
    lam = trips_per_hour(fresh, rts)
    per_slot = work[work.covered].groupby(["slot", "date", "period"]).size().rename("snapshots").reset_index()
    keys = ["date", "period"]
    rows = []
    for r in rts:
        expo = per_slot.join(lam[lam.key == r.key].set_index("slot").trips, on="slot").fillna({"trips": 0})
        expo["exposure"] = expo.snapshots * expo.trips / 3600.0  # snapshots × passages per second
        p = placed[placed.key == r.key]
        on, ctl = p[p["where"] == STRETCH], p[p["where"] == CONTROL]
        parts = {
            "n": on.groupby(keys).size(),
            "c": ctl.groupby(keys).size(),
            "n_cov": on[on.covered].groupby(keys).size(),
            "c_cov": ctl[ctl.covered].groupby(keys).size(),
            "trips": expo.groupby(keys).trips.sum(),
            "exposure": expo.groupby(keys).exposure.sum(),
            "slots": expo.groupby(keys).slot.nunique(),
        }
        # every working day and period with a snapshot has its row, also one in which no bus of the route was seen
        grid = pd.MultiIndex.from_frame(work[["date", "period"]].drop_duplicates(), names=keys)
        frame = pd.DataFrame(parts).reindex(grid).fillna(0).reset_index()
        rows.append(frame.assign(key=r.key))
    out = pd.concat(rows, ignore_index=True)
    cov = work[work.covered]
    first, last = (min(snaps.date), max(snaps.date)) if len(snaps) else (None, None)
    selection = {
        "first_day": str(first),
        "last_day": str(last),
        "holidays_left_out": sum(
            1 for h in cfg.exclude_dates if h.weekday() < 5 and first is not None and last is not None and first <= h <= last
        ),
        "snapshots": len(snaps),
        "working_day_snapshots": len(work),
        "working_days": int(work.date.nunique()),
        "covered_hours_peak": int(cov[cov.period == PEAK].slot.nunique()),
        "covered_hours_off_peak": int(cov[cov.period == OFF].slot.nunique()),
        "covered_days": int(cov.date.nunique()),
        "positions_on_routes": len(pos),
        "share_too_old": round(1 - len(fresh) / len(pos), 3) if len(pos) else 0.0,
        "positions_used": len(placed),
    }
    return out, selection


SUMS = ["n", "c", "n_cov", "c_cov", "exposure", "trips"]


def _from_sums(peak: np.ndarray, off: np.ndarray, controls_m: float) -> dict[str, np.ndarray]:
    """The estimates from the sums of ``SUMS`` at peak and off-peak (one row per replicate, or a single row)."""
    n_p, c_p, nc_p, cc_p, e_p = (peak[:, i] for i in range(5))
    n_o, c_o, nc_o, cc_o, e_o = (off[:, i] for i in range(5))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where((n_p > 0) & (c_p > 0) & (n_o > 0) & (c_o > 0), (n_p / c_p) / (n_o / c_o), np.nan)
        ok = (nc_p > 0) & (cc_p > 0) & (nc_o > 0) & (cc_o > 0) & (e_p > 0) & (e_o > 0)
        expected = np.where(ok, nc_o * cc_p / cc_o / e_p, np.nan)
        return {
            "ratio": ratio,
            "off_s": np.where(ok, nc_o / e_o, np.nan),
            "peak_s": np.where(ok, nc_p / e_p, np.nan),
            "expected_peak_s": expected,
            "excess_s": np.where(ok, nc_p / e_p - expected, np.nan),
            "controls_off_s_per_100m": np.where(ok, cc_o / e_o / controls_m * 100, np.nan),
            "controls_peak_s_per_100m": np.where(ok, cc_p / e_p / controls_m * 100, np.nan),
        }


def estimate(d: pd.DataFrame, stretch_m: float, controls_m: float) -> dict[str, float]:
    """The estimates from per-day counts (``daily``), all the routes of ``d`` together.

    ``ratio`` uses every snapshot; the seconds use the covered hours: on the stretch per passage off-peak and at
    peak, what the controls' change predicts at peak, and the excess. NaN where a count needed is 0."""
    s = d.groupby("period")[SUMS].sum().reindex([PEAK, OFF], fill_value=0).to_numpy(dtype=float)
    return {k: float(v[0]) for k, v in _from_sums(s[:1], s[1:], controls_m).items()}


def bootstrap(d: pd.DataFrame, stretch_m: float, controls_m: float, reps: int, seed: int) -> pd.DataFrame:
    """The estimates on ``reps`` resamplings of whole days, with replacement (deterministic for a given seed): each
    replicate draws as many days as there are, and weights each day by how often it was drawn."""
    days = np.array(sorted(d.date.unique()))
    per = d.groupby(["period", "date"])[SUMS].sum()
    arrays = {
        p: per.loc[p].reindex(days, fill_value=0).to_numpy(dtype=float)
        if p in per.index.get_level_values(0)
        else np.zeros((len(days), len(SUMS)))
        for p in (PEAK, OFF)
    }
    rng = np.random.default_rng(seed)
    w = np.stack([np.bincount(rng.integers(0, len(days), len(days)), minlength=len(days)) for _ in range(reps)]).astype(float)
    return pd.DataFrame(_from_sums(w @ arrays[PEAK], w @ arrays[OFF], controls_m))


def by_hour(pos: pd.DataFrame, snaps: pd.DataFrame, rts: list[Route], cfg: Delay, stretch_m: float, controls_m: float) -> pd.DataFrame:
    """Working days, hour by hour (6h to 22h), all routes together, over the covered hours: seconds per passage on the
    stretch with its 90% interval (bootstrap over days), and the controls' seconds over the same length. ``prepare``
    must have run."""
    rng = np.random.default_rng(cfg.seed)
    rows = []
    for h in range(6, 23):
        one = cfg.model_copy(update={"peak_hours": [h], "off_peak_hours": [(h + 12) % 24]})
        d, _ = daily(pos, snaps, rts, one)
        per_day = d[d.period == PEAK].groupby("date")[["n_cov", "c_cov", "exposure", "trips"]].sum()
        s = per_day.sum()
        e = float(s.exposure)
        lo = hi = np.nan
        if e and len(per_day):
            w = np.stack([np.bincount(rng.integers(0, len(per_day), len(per_day)), minlength=len(per_day)) for _ in range(cfg.bootstrap)])
            ne = w @ per_day[["n_cov", "exposure"]].to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                lo, hi = np.nanquantile(ne[:, 0] / ne[:, 1], [0.05, 0.95])
        rows.append(
            {
                "hour": h,
                "covered_hours": int(d[d.period == PEAK].groupby("date").slots.max().sum()),
                "positions_stretch": int(s.n_cov),
                "positions_controls": int(s.c_cov),
                "passages": int(s.trips),
                "stretch_s": round(s.n_cov / e, 1) if e else np.nan,
                "stretch_ci90_low_s": round(lo, 1),
                "stretch_ci90_high_s": round(hi, 1),
                "controls_s_same_length": round(s.c_cov / e / controls_m * stretch_m, 1) if e else np.nan,
            }
        )
    return pd.DataFrame(rows)


def ages_by_place(pos: pd.DataFrame, rts: list[Route], max_age_s: float) -> pd.DataFrame:
    """The share of positions dropped for being older than ``max_age_s``, on the stretch and on the controls: if the
    two differ, dropping them would bias the comparison."""
    w = where(pos, rts)
    out = []
    for name in (STRETCH, CONTROL):
        p = pos[w == name]
        out.append(
            {"where": name, "positions": len(p), "share_too_old": round(float((p.age_s.abs() > max_age_s).mean()), 3) if len(p) else np.nan}
        )
    return pd.DataFrame(out)


def heading(r: Route, axis: LineString) -> int:
    """+1 if the route runs along the stretch in the direction of increasing s, −1 otherwise."""
    a, b = (axis.project(r.line.interpolate(m)) for m in r.stretch)
    return 1 if b > a else -1


def passages_checked(d: pd.DataFrame, passings: pd.DataFrame, hours: list[int]) -> pd.DataFrame:
    """Passages counted per covered hour against the timetable's trips per hour on the case's service day, per route
    and direction, over ``hours``: how complete the count behind the seconds is."""
    sched = passings.assign(hour=passings.t // 3600, key=passings.route_short_name.astype(str) + " " + passings.direction_id.astype(str))
    sched = sched[sched.hour.isin(hours)].groupby("key").size() / len(hours)
    seen = d.groupby("key")[["trips", "slots"]].sum()
    out = pd.DataFrame({"passages_per_hour_counted": seen.trips / seen.slots.where(seen.slots > 0), "passages_per_hour_timetable": sched})
    out["counted_over_timetable"] = out.passages_per_hour_counted / out.passages_per_hour_timetable
    return out.round(2).rename_axis("route_direction").reset_index()


def summary(d: pd.DataFrame, scopes: dict[str, pd.DataFrame], stretch_m: float, controls_m: float, cfg: Delay) -> pd.DataFrame:
    """One row per scope (all, each route and direction, each year): counts, the ratio and the seconds with their
    90% intervals (bootstrap over days)."""
    rows = []
    for scope, g in scopes.items():
        e = estimate(g, stretch_m, controls_m)
        b = bootstrap(g, stretch_m, controls_m, cfg.bootstrap, cfg.seed)
        s = g.groupby("period")[["n", "c"]].sum().reindex([PEAK, OFF], fill_value=0)
        # the covered hours are the same for every route: count them once per day, not once per route
        s["slots"] = g.groupby(["date", "period"]).slots.max().groupby("period").sum().reindex([PEAK, OFF], fill_value=0)
        ci = {k: b[k].quantile([0.05, 0.95]).tolist() if b[k].notna().any() else [np.nan, np.nan] for k in ("ratio", "excess_s")}
        rows.append(
            {
                "scope": scope,
                "working_days": int(g.date.nunique()),
                "positions_stretch_peak": int(s.loc[PEAK, "n"]),
                "positions_controls_peak": int(s.loc[PEAK, "c"]),
                "positions_stretch_off_peak": int(s.loc[OFF, "n"]),
                "positions_controls_off_peak": int(s.loc[OFF, "c"]),
                "ratio": e["ratio"],
                "ratio_ci90_low": ci["ratio"][0],
                "ratio_ci90_high": ci["ratio"][1],
                "covered_hours_peak": int(s.loc[PEAK, "slots"]),
                "covered_hours_off_peak": int(s.loc[OFF, "slots"]),
                "off_peak_s": e["off_s"],
                "peak_s": e["peak_s"],
                "expected_peak_s": e["expected_peak_s"],
                "excess_s": e["excess_s"],
                "excess_ci90_low_s": ci["excess_s"][0],
                "excess_ci90_high_s": ci["excess_s"][1],
            }
        )
    out = pd.DataFrame(rows)
    return out.round({c: 3 for c in out.columns if c.startswith("ratio")} | {c: 1 for c in out.columns if c.endswith("_s")})


def sensitivity(cfg: Delay) -> dict[str, dict[str, Any]]:
    """Other reasonable choices, each changing one parameter: the variants of ``delay_sensitivity.csv``. Names that
    start with ``peak hour`` keep one peak hour at a time."""
    one_hour = {f"peak hour {h}h only": {"peak_hours": [h]} for h in cfg.peak_hours} if len(cfg.peak_hours) > 1 else {}
    off = sorted(cfg.off_peak_hours)
    return {
        "as configured": {},
        "no age limit on positions": {"max_age_s": 1e9},
        **one_hour,
        **({f"off-peak without {off[-1]}h": {"off_peak_hours": off[:-1]}} if len(off) > 1 else {}),
        f"controls {cfg.control_gap_m * 2 / 3:g} m away": {"control_gap_m": cfg.control_gap_m * 2 / 3},
        f"controls {cfg.control_gap_m * 5 / 3:g} m away": {"control_gap_m": cfg.control_gap_m * 5 / 3},
        f"controls {cfg.control_m * 6 / 11:g} m long": {"control_m": cfg.control_m * 6 / 11},
        f"passages counted within {cfg.reach_m * 1.5:g} m": {"reach_m": cfg.reach_m * 1.5},
        f"hours with gaps up to {cfg.max_gap_s * 1.25 / 60:g} min": {"max_gap_s": cfg.max_gap_s * 1.25},
    }


def analyse(
    pos: pd.DataFrame, snaps: pd.DataFrame, rts: list[Route], cfg: Delay, axis: LineString, passings: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Every table of the stage, from placed positions and loaded snapshots (``load``, ``place``)."""
    prepare(pos, snaps, cfg)
    stretch_m, controls_m = cfg.s_to - cfg.s_from, 2 * cfg.control_m
    d, selection = daily(pos, snaps, rts, cfg)
    years = sorted({day.year for day in d.date})
    scopes = {"all": d} | {r.key: d[d.key == r.key] for r in rts} | {str(y): d[pd.to_datetime(d.date).dt.year == y] for y in years}
    variants = []
    for name, change in sensitivity(cfg).items():
        v = cfg.model_copy(update=change)
        rv = routes_with(rts, v) if {"control_gap_m", "control_m", "reach_m"} & set(change) else rts
        dv, _ = daily(pos, snaps, rv, v)
        e = estimate(dv, stretch_m, 2 * v.control_m)
        variants.append({"variant": name, "ratio": round(e["ratio"], 3), "excess_s": round(e["excess_s"], 1)})
    peak_off = sorted(set(cfg.peak_hours) | set(cfg.off_peak_hours))
    return {
        "delay_routes": pd.DataFrame(
            [
                {
                    "route_direction": r.key,
                    "route_id": r.route_id,
                    "shape_id": r.shape_id,
                    "heading": heading(r, axis),
                    "stretch_from_m": round(r.stretch[0], 1),
                    "stretch_to_m": round(r.stretch[1], 1),
                    "controls_m": " ".join(f"{a:.0f}-{b:.0f}" for a, b in r.controls),
                }
                for r in rts
            ]
        ),
        "delay_data": pd.DataFrame([{"item": k, "value": v} for k, v in selection.items()]),
        "delay_summary": summary(d, scopes, stretch_m, controls_m, cfg),
        "delay_sensitivity": pd.DataFrame(variants),
        "delay_passages": passages_checked(d, passings, peak_off),
        "delay_by_hour": by_hour(pos, snaps, rts, cfg, stretch_m, controls_m),
    }


def routes_with(rts: list[Route], cfg: Delay) -> list[Route]:
    """The same routes with their controls and reach recomputed for ``cfg`` (sensitivity variants)."""
    out = []
    for r in rts:
        m0, m1 = r.stretch
        lo, hi = max(m0 - cfg.control_gap_m - cfg.control_m, 0.0), min(m1 + cfg.control_gap_m + cfg.control_m, r.line.length)
        controls = ((lo, m0 - cfg.control_gap_m), (m1 + cfg.control_gap_m, hi))
        reach = (max(m0 - cfg.reach_m, 0.0), min(m1 + cfg.reach_m, r.line.length))
        out.append(Route(r.route_id, r.direction_id, r.route, r.shape_id, r.line, r.stretch, controls, reach))
    return out
