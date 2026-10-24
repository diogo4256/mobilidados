"""GTFS reading: service calendars, shapes and headings, and passings at reference stops, on a tiny synthetic feed."""

import datetime as dt

from streetfit import gtfs
from streetfit.config import ReferenceStop

from .builders import CRS, make_feed


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
    assert (shapes.loc["up", "heading"], shapes.loc["down", "heading"]) == (1, -1)
    trips = gtfs.trips_on_shapes(feed, shapes.reset_index())
    refs = [
        ReferenceStop(route="10", direction_id=0, stop_id="S1", s_m=0.0, heading=1),
        ReferenceStop(route="20", direction_id=1, stop_id="S2", s_m=200.0, heading=-1),
    ]
    p = gtfs.reference_passings(feed, trips, feed.stop_times(set(trips.trip_id)), refs, dt.date(2026, 10, 27))
    assert len(p) == 3
    tph = gtfs.trips_per_hour(p)
    assert (tph.loc[8, 1], tph.loc[9, 1], tph.loc[8, -1]) == (1, 1, 1)


def test_a_shape_with_too_little_length_near_the_street_is_left_out(tmp_path):
    axis = make_feed(tmp_path / "f.zip")  # both shapes run along the whole 200 m axis
    feed = gtfs.Feed(tmp_path / "f.zip")
    assert sorted(gtfs.shapes_along(feed, axis, CRS, min_inside_m=150).shape_id) == ["down", "up"]
    assert gtfs.shapes_along(feed, axis, CRS, min_inside_m=250).empty
