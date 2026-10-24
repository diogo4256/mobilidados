"""Cross-section measurement on a synthetic street with known widths, and ESRI JSON geometry conversion."""

import pytest
from shapely import affinity
from shapely.geometry import LineString, box

from streetfit.arcgis import to_polygon
from streetfit.config import Block
from streetfit.geometry import TWO_STRIPS, classify, measure_profiles, narrow_sections, strip_lengths, summarize_blocks

CLASSES = {"road": {"road"}, "parking": {"park"}, "sidewalk": {"walk"}, "plot": {"plot"}}


def street(free=4.90, strip=2.0, walk=2.5, length=100.0, strip_from=20.0, strip_to=80.0):
    """A straight street along +x: road centred on y=0, parking strips on both sides between strip_from and strip_to."""
    h = free / 2
    polys = [
        ("road", box(0, -h, length, h)),
        ("park", box(strip_from, h, strip_to, h + strip)),
        ("park", box(strip_from, -h - strip, strip_to, -h)),
        ("walk", box(0, h + strip, length, h + strip + walk)),
        ("walk", box(0, -h - strip - walk, length, -h - strip)),
        ("plot", box(0, h + strip + walk, length, h + strip + walk + 10)),
        ("plot", box(0, -h - strip - walk - 10, length, -h - strip - walk)),
    ]
    return LineString([(0, 0), (length, 0)]), polys


def test_widths_on_two_strip_section():
    axis, polys = street()
    mid = measure_profiles(axis, polys, CLASSES, step=1.0).set_index("s").loc[50]
    assert mid.free_width == pytest.approx(4.90)
    assert mid.strip_L == pytest.approx(2.0)
    assert mid.strip_R == pytest.approx(2.0)
    assert mid.kerb_to_kerb == pytest.approx(8.90)
    assert mid.sidewalk_L == pytest.approx(2.5)
    assert mid.to_plot_R == pytest.approx(2.5)


@pytest.mark.parametrize("angle", [0, 17, 90, 133, 241])
def test_measurement_does_not_depend_on_the_street_orientation(angle):
    axis, polys = street(free=5.3, strip=1.9)
    turn = lambda g: affinity.rotate(g, angle, origin=(0, 0))  # noqa: E731
    mid = measure_profiles(turn(axis), [(c, turn(g)) for c, g in polys], CLASSES, step=1.0).set_index("s").loc[50]
    assert (mid.free_width, mid.strip_L, mid.strip_R, mid.kerb_to_kerb) == pytest.approx((5.3, 1.9, 1.9, 9.1), abs=0.011)


def test_no_strip_outside_parking_section():
    axis, polys = street()
    end = measure_profiles(axis, polys, CLASSES, step=1.0).set_index("s").loc[5]
    assert end.strip_L == 0
    assert end.strip_R == 0
    assert end.kerb_to_kerb == pytest.approx(4.90)


def test_the_axis_may_lie_slightly_outside_the_road_polygon():
    axis = LineString([(0, 0), (100, 0)])
    road = [("road", box(0, 0.03, 100, 5))]  # the axis runs 3 cm outside it
    inside = measure_profiles(axis, road, CLASSES, step=50.0).iloc[1]
    assert inside.free_width == pytest.approx(4.97)
    strict = measure_profiles(axis, road, CLASSES, step=50.0, axis_tol=0.01).iloc[1]
    assert strict.note == "axis outside the mapped road polygon"


def test_classify_summary_and_sections():
    axis, polys = street()
    blocks = [Block(id="A", start=0, end=50), Block(id="B", start=50, end=100)]
    df = classify(measure_profiles(axis, polys, CLASSES, step=1.0), blocks)
    two = df[df["class"] == TWO_STRIPS]
    # a transect lying exactly on a strip's end edge counts the strip (shared boundary), as in the original scripts
    assert (two.s.min(), two.s.max()) == (20, 80)
    assert summarize_blocks(df, blocks).set_index("block").loc["all", "free_median"] == pytest.approx(4.90)
    assert [b for _, _, b in narrow_sections(df, 1.0)] == ["A", "B"]
    assert strip_lengths(df, blocks, 1.0).set_index("block").loc["all", "strip_L_length_m"] == pytest.approx(61.0)


# ESRI rings: exterior clockwise, hole counter-clockwise
OUTER = [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]


def test_esri_ring_orientation_and_holes():
    hole = [[2, 2], [4, 2], [4, 4], [2, 4], [2, 2]]
    assert to_polygon({"rings": [OUTER, hole]}).area == pytest.approx(100 - 4)


def test_hole_touching_its_exterior_is_kept():
    hole = [[0, 0], [3, 1], [1, 3], [0, 0]]  # touches the exterior at its corner (0, 0)
    p = to_polygon({"rings": [OUTER, hole]})
    assert p.is_valid
    assert p.area == pytest.approx(100 - 4)


def test_hole_inside_an_island_inside_a_hole():
    hole = [[1, 1], [9, 1], [9, 9], [1, 9], [1, 1]]
    island = [[3, 3], [3, 7], [7, 7], [7, 3], [3, 3]]
    hole_in_island = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
    p = to_polygon({"rings": [OUTER, hole, island, hole_in_island]})
    assert p.geom_type == "MultiPolygon"
    assert p.is_valid
    assert p.area == pytest.approx((100 - 64) + (16 - 4))
