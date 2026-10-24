"""The encounter model: where two scheduled vehicles in opposite directions meet, and whether they overlap at all."""

import pandas as pd
import pytest

from mobilidados import encounters


def test_meeting_point_is_analytic():
    # A at s=0 at t=0 heading up, B at s=200 at t=0 heading down, both 10 m/s: meet at s=100, t=10
    t, s = encounters.meeting(0, 0, 0, 200, 10)
    assert (t, s) == pytest.approx((10, 100))


def test_encounters_overlap_only():
    p = pd.DataFrame(
        [
            {"route_short_name": "10", "arrival_time": "08:00:00", "t": 8 * 3600, "s_ref": 0.0, "heading": 1},
            {"route_short_name": "20", "arrival_time": "08:00:10", "t": 8 * 3600 + 10, "s_ref": 200.0, "heading": -1},
            {
                "route_short_name": "20",
                "arrival_time": "08:00:20",
                "t": 8 * 3600 + 20,
                "s_ref": 200.0,
                "heading": -1,
            },  # A leaves as it enters
            {"route_short_name": "20", "arrival_time": "09:30:00", "t": 9.5 * 3600, "s_ref": 200.0, "heading": -1},
        ]
    )
    e = encounters.encounters(p, 200, 36)  # 10 m/s: 20 s on the street
    assert len(e) == 1
    assert (e.iloc[0].time, e.iloc[0].s_m) == ("08:00:15", pytest.approx(150.0))
    assert encounters.locate(e, [(100.0, 160.0, "B2")]).in_narrow_section.iloc[0]
    assert not encounters.locate(e, [(20.0, 90.0, "B1")]).in_narrow_section.iloc[0]
