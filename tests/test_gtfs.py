"""GTFS reading: service calendars, shapes and headings, and passings at reference stops, on a tiny synthetic feed."""

import datetime as dt

import pytest

from mobilidados import gtfs
from mobilidados.config import MobilidadosError, ReferenceStop

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


def passings(tmp_path, refs, day=dt.date(2026, 10, 27), **more):
    axis = make_feed(tmp_path / "f.zip", **more)
    feed = gtfs.Feed(tmp_path / "f.zip")
    trips = gtfs.trips_on_shapes(feed, gtfs.shapes_along(feed, axis, CRS))
    return gtfs.reference_passings(feed, trips, feed.stop_times(set(trips.trip_id)), refs, day)


def test_a_loop_that_serves_the_reference_stop_twice_passes_once(tmp_path):
    refs = [ReferenceStop(route="10", direction_id=0, stop_id="S1", s_m=0.0, heading=1)]
    loop = "a3,10:00:00,10:00:00,S1,1\na3,10:01:00,10:01:00,S2,2\na3,10:02:00,10:02:00,S1,3\n"
    p = passings(tmp_path, refs, more_trips="A,WK,a3,0,up\n", more_stop_times=loop)
    assert p.trip_id.tolist() == ["a1", "a2", "a3"]
    assert p[p.trip_id == "a3"].arrival_time.tolist() == ["10:00:00"]  # its first visit


@pytest.mark.parametrize(
    ("stop_id", "day"),
    [("S1", dt.date(2026, 10, 31)), ("S2", dt.date(2026, 10, 27))],
    ids=["no service that day", "always the last stop"],
)
def test_a_reference_stop_without_a_trip_going_on_from_it_that_day_is_an_error(tmp_path, stop_id, day):
    refs = [ReferenceStop(route="10", direction_id=0, stop_id=stop_id, s_m=0.0, heading=1)]
    with pytest.raises(MobilidadosError) as err:
        passings(tmp_path, refs, day)
    assert str(err.value) == (
        f"route 10 direction 0: no trip serves stop {stop_id} on {day} with a following stop; check reference_stops and service_date"
    )


def test_a_shape_with_too_little_length_near_the_street_is_left_out(tmp_path):
    axis = make_feed(tmp_path / "f.zip")  # both shapes run along the whole 200 m axis
    feed = gtfs.Feed(tmp_path / "f.zip")
    assert sorted(gtfs.shapes_along(feed, axis, CRS, min_inside_m=150).shape_id) == ["down", "up"]
    assert gtfs.shapes_along(feed, axis, CRS, min_inside_m=250).empty
