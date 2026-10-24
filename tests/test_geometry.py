"""Cross-section measurement on a synthetic street with known widths."""

import pytest
from shapely import affinity
from shapely.geometry import LineString, box

from mobilidados.config import Block, MobilidadosError
from mobilidados.geometry import TWO_STRIPS, classify, measure_profiles, narrow_sections, street_axis, strip_lengths, summarize_blocks

from .builders import street

CLASSES = {"road": {"road"}, "parking": {"park"}, "sidewalk": {"walk"}, "plot": {"plot"}}


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


def axis_feature(name, *paths):
    return {"attributes": {"NAME": name}, "geometry": {"paths": [[list(p) for p in path] for path in paths]}}


def test_the_axis_of_a_street_is_found_by_name():
    features = [axis_feature("Rua A", [(0, 0), (10, 0)]), axis_feature("Rua B", [(0, 5), (10, 5)])]
    assert street_axis(features, "NAME", "Rua B").length == pytest.approx(10)


@pytest.mark.parametrize(
    ("features", "message"),
    [
        ([axis_feature("Rua A", [(0, 0), (10, 0)])], "found 0"),
        ([axis_feature("Rua B", [(0, 0), (10, 0)]), axis_feature("Rua B", [(10, 0), (20, 0)])], "found 2"),
        ([axis_feature("Rua B", [(0, 0), (10, 0)], [(20, 0), (30, 0)])], "multi-part"),
    ],
    ids=["missing", "duplicate", "multi-part"],
)
def test_an_axis_that_is_missing_duplicated_or_in_parts_is_a_user_error(features, message):
    with pytest.raises(MobilidadosError, match=message):
        street_axis(features, "NAME", "Rua B")
