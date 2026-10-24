"""Reading the official traffic direction from identify results."""

import pandas as pd
import pytest

from mobilidados.direction import directions

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
