"""The delay estimator on buses whose times are known: simulated runs, sampled at irregular snapshots as an archive
of a real-time feed would sample them, must give back the time on the stretch, the ratio and the excess."""

import datetime as dt

import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import LineString

from mobilidados import delay
from mobilidados.archive import SNAPSHOT_TIME
from mobilidados.config import Delay

CRS = 3763
X0, Y0 = -87500.0, -100700.0  # Lisbon, projected
ROUTE_M = 4000.0  # the route runs 4 km along +x
STRETCH = (2000.0, 2145.0)  # 145 m, as in the Lisbon case
TO_LL = Transformer.from_crs(CRS, 4326, always_xy=True)
CFG = Delay(source="positions", s_from=0, s_to=145, bootstrap=200)


def route() -> delay.Route:
    line = LineString([(X0, Y0), (X0 + ROUTE_M, Y0)])
    m0, m1 = STRETCH
    g, c = CFG.control_gap_m, CFG.control_m
    return delay.Route("R_0", 0, "R", "R_shape", line, STRETCH, ((m0 - g - c, m0 - g), (m1 + g, m1 + g + c)), (m0 - 2000, m1 + 2000), "R 0")


def position(m: float, v_other: float, v_stretch: float) -> float:
    """Time (s) for a bus to reach ``m`` from the start of the route, at v_other outside the stretch and v_stretch on it."""
    a, b = STRETCH
    if m <= a:
        return m / v_other
    if m <= b:
        return a / v_other + (m - a) / v_stretch
    return a / v_other + (b - a) / v_stretch + (m - b) / v_other


def where_at(t: float, v_other: float, v_stretch: float) -> float:
    """Inverse of ``position``: where a bus is ``t`` seconds after it started (NaN once it has left the route)."""
    a, b = STRETCH
    ta, tb = a / v_other, a / v_other + (b - a) / v_stretch
    if t < ta:
        return t * v_other
    if t < tb:
        return a + (t - ta) * v_stretch
    m = b + (t - tb) * v_other
    return m if m <= ROUTE_M else np.nan


KMH = 1 / 3.6
SPEEDS = {  # (outside the stretch, on the stretch) in m/s
    "off_peak": (20 * KMH, 20 * KMH),
    "peak": (15 * KMH, 8 * KMH),  # everything slower at peak, and the stretch far more
}


def simulate(days: list[dt.date], headway_s: float = 360, seed: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Positions and snapshots as ``archive.extract`` writes them: snapshots 1 to 7 minutes apart, a bus starting every
    ``headway_s``, each seen with the position it had when it reported, 10 s before the snapshot."""
    rng = np.random.default_rng(seed)
    snaps, rows = [], []
    for day in days:
        start = pd.Timestamp(day, tz="Europe/Lisbon") + pd.Timedelta(hours=9)
        end = start + pd.Timedelta(hours=11)  # 9h to 20h
        departures = pd.date_range(start - pd.Timedelta(minutes=30), end, freq=f"{int(headway_s)}s")
        t = start
        while t < end:
            snap = t.tz_convert("UTC")
            seen = 0
            for k, dep in enumerate(departures):
                hour = dep.hour
                speeds = SPEEDS["peak"] if hour in (17, 18) else SPEEDS["off_peak"]
                reported = snap - pd.Timedelta(seconds=10)
                m = where_at((reported - dep.tz_convert("UTC")).total_seconds(), *speeds)
                if np.isnan(m) or m < 0:
                    continue
                lon, lat = TO_LL.transform(X0 + m, Y0)
                rows.append([snap.strftime(SNAPSHOT_TIME), f"{day}-{k}", "R_0", "0", f"v{k % 20}",
                             reported.strftime("%Y-%m-%d %H:%M:%S"), f"{lat:.7f}", f"{lon:.7f}", "IN_TRANSIT_TO", "", ""])  # fmt: skip
                seen += 1
            snaps.append([snap.strftime(SNAPSHOT_TIME), 200, seen, seen])
            t += pd.Timedelta(seconds=int(rng.integers(60, 420)))
    pos = pd.DataFrame(rows, columns=["snapshot", "trip_id", "route_id", "direction_id", "vehicle_id", "timestamp", "latitude",
                                      "longitude", "current_status", "stop_id", "current_stop_sequence"])  # fmt: skip
    return pos, pd.DataFrame(snaps, columns=["snapshot", "vehicles", "vehicles_on_routes", "positions_kept"])


def weekdays(n: int) -> list[dt.date]:
    days: list[dt.date] = []
    d = dt.date(2026, 1, 5)  # a Monday, in winter (Lisbon on UTC)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    return days


@pytest.fixture(scope="module")
def counted():
    pos, snaps = simulate(weekdays(40))
    pos, snaps = delay.load(pos, snaps, CFG.time_zone, "UTC")
    placed = delay.place(pos, [route()], CRS, CFG.max_offset_m)
    delay.prepare(placed, snaps, CFG)
    return placed, snaps


def truth() -> dict[str, float]:
    length = STRETCH[1] - STRETCH[0]
    off = length / SPEEDS["off_peak"][1]
    peak = length / SPEEDS["peak"][1]
    expected = off * SPEEDS["off_peak"][0] / SPEEDS["peak"][0]  # the controls are slower at peak by this factor
    return {"off_s": off, "peak_s": peak, "expected_peak_s": expected, "excess_s": peak - expected, "ratio": peak / expected}


def test_the_estimator_gives_back_the_simulated_times(counted):
    placed, snaps = counted
    d, selection = delay.daily(placed, snaps, [route()], CFG)
    est = delay.estimate(d, 2 * CFG.control_m)
    want = truth()  # 26.1 s off-peak, 65.3 s at peak where the controls predict 34.8 s: +30.5 s, ratio 1.875
    assert selection["covered_hours_peak"] > 40  # snapshots at most 7 min apart: every hour is covered
    for key in ("off_s", "peak_s", "expected_peak_s", "excess_s", "ratio"):
        assert est[key] == pytest.approx(want[key], rel=0.12), key


def test_the_ratio_does_not_depend_on_the_passages_counted(counted):
    placed, snaps = counted
    d, _ = delay.daily(placed, snaps, [route()], CFG)
    halved = d.assign(trips=d.trips / 2, exposure=d.exposure / 2)  # half the passages: every second doubles
    full, half = delay.estimate(d, 1100), delay.estimate(halved, 1100)
    assert half["ratio"] == full["ratio"]
    assert half["excess_s"] == pytest.approx(2 * full["excess_s"])


def test_the_interval_covers_the_simulated_excess_and_is_the_same_on_every_run(counted):
    placed, snaps = counted
    d, _ = delay.daily(placed, snaps, [route()], CFG)
    a, b = delay.bootstrap(d, 1100, 200, 1), delay.bootstrap(d, 1100, 200, 1)
    pd.testing.assert_frame_equal(a, b)
    lo, hi = a.excess_s.quantile([0.05, 0.95])
    assert lo < truth()["excess_s"] < hi
    lo, hi = a.ratio.quantile([0.05, 0.95])
    assert lo < truth()["ratio"] < hi


def test_without_a_slower_stretch_there_is_no_excess():
    saved = dict(SPEEDS)
    SPEEDS["peak"] = (15 * KMH, 15 * KMH)  # slower at peak everywhere, the stretch no more than its surroundings
    try:
        pos, snaps = simulate(weekdays(40))
    finally:
        SPEEDS.update(saved)
    pos, snaps = delay.load(pos, snaps, CFG.time_zone, "UTC")
    placed = delay.place(pos, [route()], CRS, CFG.max_offset_m)
    delay.prepare(placed, snaps, CFG)
    d, _ = delay.daily(placed, snaps, [route()], CFG)
    b = delay.bootstrap(d, 1100, 200, 1)
    assert b.ratio.quantile(0.05) < 1 < b.ratio.quantile(0.95)
    assert b.excess_s.quantile(0.05) < 0 < b.excess_s.quantile(0.95)


def test_stale_positions_and_holidays_are_left_out(counted):
    placed, snaps = counted
    first = min(snaps.date)
    d, sel = delay.daily(placed, snaps, [route()], CFG.model_copy(update={"exclude_dates": [first]}))
    assert first not in set(d.date)
    old = placed.assign(age_s=placed.age_s + 100)  # every position reported 110 s before its snapshot
    d, sel = delay.daily(old, snaps, [route()], CFG)
    assert sel["share_too_old"] == 1.0
    assert sel["positions_used"] == 0


def test_an_hour_counts_as_covered_only_without_a_long_gap():
    t = pd.to_datetime(["2026-01-05 10:05", "2026-01-05 10:15", "2026-01-05 10:25", "2026-01-05 10:35", "2026-01-05 10:45",
                        "2026-01-05 10:55", "2026-01-05 11:20", "2026-01-05 11:58"]).tz_localize("UTC")  # fmt: skip
    snaps = pd.DataFrame({"t": t, "slot": t.floor("h")})
    covered = delay.covered_hours(snaps, 720)
    assert covered == {pd.Timestamp("2026-01-05 10:00", tz="UTC")}  # 10h: never 12 min without one; 11h: 20 min to the first


def test_the_hour_repeated_when_clocks_go_back_is_two_hours():
    t = pd.to_datetime(["2025-10-26 00:30", "2025-10-26 01:30"]).tz_localize("UTC")  # 01:30 and 01:30 again in Lisbon
    snaps = pd.DataFrame({"t": t})
    pos = pd.DataFrame({"t": t})
    delay.prepare(pos, snaps, CFG)
    assert snaps.hour.tolist() == [1, 1]
    assert snaps.slot.nunique() == 2
    assert not snaps.weekday.any()  # a Sunday


def test_two_gtfs_routes_with_the_same_short_name_stay_apart(tmp_path):
    import zipfile

    from mobilidados.gtfs import Feed

    (lon0, lon1), (lat0, lat1) = TO_LL.transform([X0, X0 + ROUTE_M], [Y0, Y0])
    files = {
        "routes.txt": "route_id,route_short_name,route_long_name,route_type\nX_0,727,One,3\nX_1,727,Another,3\n",
        "trips.txt": "route_id,service_id,trip_id,direction_id,shape_id\nX_0,WK,a,0,s\nX_1,WK,b,0,s\n",
        "shapes.txt": f"shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\ns,{lat0},{lon0},1\ns,{lat1},{lon1},2\n",
    }
    with zipfile.ZipFile(tmp_path / "feed.zip", "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    axis = LineString([(X0 + STRETCH[0], Y0), (X0 + STRETCH[1], Y0)])
    rts = delay.routes(Feed(tmp_path / "feed.zip"), ["727"], axis, CRS, CFG)
    assert [(r.key, r.label) for r in rts] == [("X_0 0", "727 (X_0) 0"), ("X_1 0", "727 (X_1) 0")]
    lon, lat = TO_LL.transform(X0 + 2050, Y0)
    pos = pd.DataFrame({"route_id": ["X_0", "X_1"], "direction_id": ["0", "0"], "latitude": [str(lat)] * 2, "longitude": [str(lon)] * 2})
    assert delay.place(pos, rts, CRS, CFG.max_offset_m).key.tolist() == ["X_0 0", "X_1 0"]
