"""GTFS reading, service calendars and the encounter model on a tiny synthetic feed."""

import datetime as dt
import zipfile

import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import LineString

from streetfit import encounters, gtfs

CRS = 3763


def make_feed(path):
    """Two routes along a 200 m street in Lisbon's projected CRS; route B only on Tuesdays via calendar_dates."""
    to_ll = Transformer.from_crs(CRS, 4326, always_xy=True)
    (lon0, lon1), (lat0, lat1) = to_ll.transform([-87500, -87300], [-100700, -100700])
    files = {
        "routes.txt": "route_id,route_short_name,route_long_name,route_type\nA,10,Up,3\nB,20,Down,3\n",
        "trips.txt": "route_id,service_id,trip_id,direction_id,shape_id\nA,WK,a1,0,up\nA,WK,a2,0,up\nB,X,b1,1,down\n",
        "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "WK,1,1,1,1,1,0,0,20260101,20261231\n",
        "calendar_dates.txt": "service_id,date,exception_type\nX,20261027,1\nWK,20261028,2\n",
        "shapes.txt": "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
        f"up,{lat0},{lon0},1\nup,{lat1},{lon1},2\ndown,{lat1},{lon1},1\ndown,{lat0},{lon0},2\n",
        "stops.txt": f"stop_id,stop_name,stop_lat,stop_lon\nS1,First,{lat0},{lon0}\nS2,Last,{lat1},{lon1}\n",
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "a1,08:00:00,08:00:00,S1,1\na1,08:01:00,08:01:00,S2,2\n"
        "a2,09:00:00,09:00:00,S1,1\na2,09:01:00,09:01:00,S2,2\n"
        "b1,08:00:20,08:00:20,S2,1\nb1,08:01:20,08:01:20,S1,2\n",
    }
    with zipfile.ZipFile(path, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return LineString([(-87500, -100700), (-87300, -100700)])


def test_calendar_rules_and_exceptions(tmp_path):
    make_feed(tmp_path / "f.zip")
    feed = gtfs.Feed(tmp_path / "f.zip")
    assert gtfs.active_service_ids(feed, dt.date(2026, 10, 27)) == {"WK", "X"}
    assert gtfs.active_service_ids(feed, dt.date(2026, 10, 28)) == set()
    assert gtfs.active_service_ids(feed, dt.date(2026, 10, 31)) == set()


def test_shapes_headings_and_passings(tmp_path):
    axis = make_feed(tmp_path / "f.zip")
    feed = gtfs.Feed(tmp_path / "f.zip")
    shapes = gtfs.shapes_along(feed, axis, CRS).set_index("shape_id")
    assert shapes.loc["up", "heading"] == 1 and shapes.loc["down", "heading"] == -1
    trips = gtfs.trips_on_shapes(feed, shapes.reset_index())
    refs = [
        {"route": "10", "direction_id": "0", "stop_id": "S1", "s_m": 0.0, "heading": 1},
        {"route": "20", "direction_id": "1", "stop_id": "S2", "s_m": 200.0, "heading": -1},
    ]
    p = gtfs.reference_passings(feed, trips, refs, dt.date(2026, 10, 27))
    assert len(p) == 3
    tph = gtfs.trips_per_hour(p)
    assert tph.loc[8, 1] == 1 and tph.loc[9, 1] == 1 and tph.loc[8, -1] == 1


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
