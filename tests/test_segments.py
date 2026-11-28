"""The [delay] comparison made again on published speeds per segment: segments placed along the shape, the ratio
and seconds given back for speeds that are known, and a route left out when its segments do not cover enough."""

import json

import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import LineString

from mobilidados import delay, segments
from mobilidados.config import Delay, MobilidadosError, SegmentCheck

CRS = 3763
X0, Y0 = -87500.0, -100700.0
TO_LL = Transformer.from_crs(CRS, 4326, always_xy=True)
DL = Delay(source="positions", s_from=45, s_to=190)
SC = SegmentCheck(source="segment_speeds")
STRETCH = (2000.0, 2145.0)
SEG_M = 60.0
AXIS = LineString([(X0 + 1955, Y0), (X0 + 2165, Y0)])  # the street: s = 0 at 1955 m along the route
KMH = 1 / 3.6


def route() -> delay.Route:
    line = LineString([(X0, Y0), (X0 + 4000, Y0)])
    m0, m1 = STRETCH
    g, c = DL.control_gap_m, DL.control_m
    return delay.Route("R_0", 0, "R", "R_shape", line, STRETCH, ((m0 - g - c, m0 - g), (m1 + g, m1 + g + c)), (m0 - 2000, m1 + 2000), "R 0")


def published(v_other_kmh: float, v_stretch_kmh: float, samples: int = 40, shape: str = "R_shape", dy: float = 0.0) -> pd.DataFrame:
    """Segments of 60 m along the route as the service publishes them: metres and seconds summed over the samples."""
    rows = []
    for k in range(66):
        a, b = k * SEG_M, (k + 1) * SEG_M
        on = STRETCH[0] <= (a + b) / 2 <= STRETCH[1]
        v = (v_stretch_kmh if on else v_other_kmh) * KMH
        lon1, lat1 = TO_LL.transform(X0 + a, Y0 + dy)
        lon2, lat2 = TO_LL.transform(X0 + b, Y0 + dy)
        meters = samples * SEG_M
        rows.append(
            {
                "segment_id": f"{shape}:{k}",
                "shape_id": shape,
                "seq": k,
                "seconds": meters / v,
                "meters": meters,
                "samples": samples,
                "lat1": lat1,
                "lon1": lon1,
                "lat2": lat2,
                "lon2": lon2,
                "length_m": SEG_M,
                "period_start": "2025-12-08",
                "period_end": "2026-01-06",
            }
        )
    return pd.DataFrame(rows)


def test_known_speeds_give_back_the_ratio_and_the_seconds():
    peak, off = published(15, 8), published(20, 20)
    other = published(5, 5, shape="Other_shape")  # another route's shape: not read
    table, data = segments.compare(pd.concat([peak, other]), off, [route()], CRS, AXIS, DL, SC)
    row = table.iloc[0]
    assert (row.segments_stretch, row.segments_controls) == (3, 18)  # midpoints 2010, 2070, 2130; 9 + 9 controls
    assert (row.s_first, row.s_last) == (25.0, 205.0)  # the segments reach past the stretch on the street
    assert row.coverage_stretch == pytest.approx(180 / 145, abs=1e-3)
    assert row.coverage_controls == pytest.approx(1080 / 1100, abs=1e-3)
    assert bool(row.compared)
    # stretch: 145 m at 8 km/h at peak, 20 km/h off-peak; controls 15 km/h at peak: expected 145 m at 20 * 20 / 15
    assert row.ratio == pytest.approx((20 / 8) / (20 / 15), abs=1e-3)
    assert row.peak_s == pytest.approx(145 / (8 * KMH), abs=0.1)
    assert row.expected_peak_s == pytest.approx(145 / (15 * KMH), abs=0.1)
    assert row.excess_s == pytest.approx(row.peak_s - row.expected_peak_s, abs=0.11)
    assert row.samples_stretch_peak == 3 * 40
    assert data["period_first"] == "2025-12-08"
    assert data["period_last"] == "2026-01-06"


def test_a_route_whose_controls_lack_records_or_samples_is_not_compared():
    peak, off = published(15, 8), published(20, 20)
    thin = peak[~peak.seq.between(22, 30)]  # the first control stretch has no record at peak
    row = segments.compare(thin, off, [route()], CRS, AXIS, DL, SC)[0].iloc[0]
    assert row.coverage_controls < SC.min_coverage
    assert not bool(row.compared)
    assert np.isnan(row.ratio)
    few = segments.compare(published(15, 8, samples=5), published(20, 20, samples=5), [route()], CRS, AXIS, DL, SC)[0].iloc[0]
    assert few.samples_stretch_peak == 15
    assert not bool(few.compared)


def test_segments_away_from_the_shape_are_left_out():
    far = published(15, 8, dy=50)  # 50 m off the shape, beyond max_offset_m
    assert segments.place(far, route(), CRS, DL.max_offset_m).empty
    row = segments.compare(far, published(20, 20), [route()], CRS, AXIS, DL, SC)[0].iloc[0]
    assert row.segments_stretch == 0
    assert not bool(row.compared)


def test_the_answers_must_be_for_the_delay_hours():
    base = "https://example.org/transit-stats?window=30d&routes=1"
    good = {"peak.json": base + "&hour_start=17&hour_end=18", "off_peak.json": base + "&hour_start=10&hour_end=16"}
    segments.check_hours(good, DL)
    with pytest.raises(MobilidadosError, match=r"peak.json is asked for hours \[17, 18, 19\]"):
        segments.check_hours(good | {"peak.json": base + "&hour_start=17&hour_end=19"}, DL)
    with pytest.raises(MobilidadosError, match=r"off_peak.json is asked for hours None"):
        segments.check_hours(good | {"off_peak.json": base}, DL)


def test_an_answer_that_is_not_a_list_of_segments_is_an_error(tmp_path):
    path = tmp_path / "peak.json"
    path.write_text(json.dumps({"detail": "window must be one of ['1h', '24h', '30d']"}), encoding="utf-8")
    with pytest.raises(MobilidadosError, match="expected a list of segments"):
        segments.load(path)
    path.write_text(json.dumps([{"segment_id": "a", "shape_id": "s"}]), encoding="utf-8")
    with pytest.raises(MobilidadosError, match="the segments have no"):
        segments.load(path)
    path.write_text(published(15, 8).head(2).to_json(orient="records"), encoding="utf-8")
    assert len(segments.load(path)) == 2
