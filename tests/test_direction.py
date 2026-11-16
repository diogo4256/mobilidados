"""Reading the official traffic direction from identify results."""

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString

from mobilidados.config import Network
from mobilidados.direction import directions, edges_along, edges_at, majority, runs_along

OPEN = "Traversable"


def edges(*rows):
    return pd.DataFrame(rows, columns=["edge", "direction", "status"])


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([(1, "Along", OPEN), (1, "Against", OPEN)], "two-way"),
        ([(1, "Along", OPEN), (1, "Against", "Prohibited")], "one-way"),
        ([(1, "Along", OPEN), (2, "Against", OPEN)], "one-way"),  # two edges, each open in one direction only
        ([(1, "Along", "Prohibited"), (1, "Against", "Prohibited")], "?"),
        ([], "?"),
    ],
    ids=["both open", "one open", "different edges", "none open", "no data"],
)
def test_directions(rows, expected):
    assert directions(edges(*rows), OPEN) == expected


NET = Network(edge="[EID]", direction="[Direction]", status="Oneway", open_value=OPEN)
EAST = np.array([1.0, 0.0])


def edge(eid, direction, status, *points):
    return {"[EID]": eid, "[Direction]": direction, "Oneway": status, "_geometry": {"paths": [[list(p) for p in points]]}}


class Answers:
    """An identify cache that answers every point with the same edges."""

    def __init__(self, edges):
        self.edges = edges

    def get(self, x, y):
        return self.edges


# a one-way street running east (edge 1) at the point where a two-way street (edge 2) crosses it: what Rua de São
# Bento looked like to a point identify, until only the street's own edges were read
ONE_WAY_AT_A_CROSSING = [
    edge("1", "Along", OPEN, (-50, 0), (50, 0)),
    edge("1", "Against", "Prohibited", (-50, 0), (50, 0)),
    edge("2", "Along", OPEN, (0, -50), (0, 50)),
    edge("2", "Against", OPEN, (0, -50), (0, 50)),
]


def test_a_crossing_streets_edges_do_not_make_a_one_way_street_two_way():
    mine = pd.DataFrame(edges_at(Answers(ONE_WAY_AT_A_CROSSING), NET, 0.0, 0.0, EAST))
    assert set(mine.edge) == {"1"}
    assert directions(mine, OPEN) == "one-way"
    everything = pd.DataFrame([{"edge": e["[EID]"], "direction": e["[Direction]"], "status": e["Oneway"]} for e in ONE_WAY_AT_A_CROSSING])
    assert directions(everything, OPEN) == "two-way"  # the old reading


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (((-50, 0), (50, 0)), True),  # along
        (((-50, -20), (50, 20)), True),  # 22° off
        (((-50, -40), (50, 40)), False),  # 39° off
        (((-50, 10), (50, 10)), False),  # parallel, but 10 m away: another street
    ],
)
def test_an_edge_runs_along_the_street_within_30_degrees_and_6_m(points, expected):
    assert runs_along(edge("1", "Along", OPEN, *points)["_geometry"], 0.0, 0.0, EAST) is expected


def test_an_edge_without_geometry_is_not_taken_for_the_streets():
    assert runs_along(None, 0.0, 0.0, EAST) is False


def test_edges_along_a_street_follow_its_bends():
    axis = LineString([(0, 0), (100, 0), (100, 100)])  # east, then north
    north = edge("3", "Along", OPEN, (100, -50), (100, 150))
    east = edge("4", "Along", OPEN, (-50, 0), (150, 0))
    found = edges_along(axis, Answers([north, east]), NET, [50.0, 150.0])
    assert found.set_index("s_m").edge.to_dict() == {50.0: "4", 150.0: "3"}


@pytest.mark.parametrize(
    ("readings", "expected"),
    [
        (["two-way", "two-way", "one-way"], "two-way"),
        (["one-way", "?", "one-way"], "one-way"),
        (["two-way", "one-way", "?"], "?"),
        (["?", "?"], "?"),
    ],
)
def test_a_streets_direction_is_what_most_points_read(readings, expected):
    assert majority(readings) == expected
