"""Cross-section measurement on a synthetic street with known widths."""

import pytest
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
    df = measure_profiles(axis, polys, CLASSES, step=1.0)
    mid = df[df.s == 50].iloc[0]
    assert mid.free_width == pytest.approx(4.90)
    assert mid.strip_L == pytest.approx(2.0) and mid.strip_R == pytest.approx(2.0)
    assert mid.kerb_to_kerb == pytest.approx(8.90)
    assert mid.sidewalk_L == pytest.approx(2.5) and mid.to_plot_R == pytest.approx(2.5)


def test_no_strip_outside_parking_section():
    axis, polys = street()
    df = measure_profiles(axis, polys, CLASSES, step=1.0)
    end = df[df.s == 5].iloc[0]
    assert end.strip_L == 0 and end.strip_R == 0
    assert end.kerb_to_kerb == pytest.approx(4.90)


def test_classify_summary_and_sections():
    axis, polys = street()
    blocks = [Block("A", 0, 50), Block("B", 50, 100)]
    df = classify(measure_profiles(axis, polys, CLASSES, step=1.0), blocks)
    two = df[df["class"] == TWO_STRIPS]
    # a transect lying exactly on a strip's end edge counts the strip (shared boundary), as in the original scripts
    assert two.s.min() == 20 and two.s.max() == 80
    s = summarize_blocks(df, blocks).set_index("block")
    assert s.loc["all", "free_median"] == pytest.approx(4.90)
    assert [b for _, _, b in narrow_sections(df, 1.0)] == ["A", "B"]
    lengths = strip_lengths(df, blocks, 1.0).set_index("block")
    assert lengths.loc["all", "strip_L_length_m"] == pytest.approx(61.0)


def test_esri_rings_orientation_and_holes():
    # ESRI: exterior clockwise, hole counter-clockwise
    ext = [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]
    hole = [[2, 2], [4, 2], [4, 4], [2, 4], [2, 2]]
    p = to_polygon({"rings": [ext, hole]})
    assert p.area == pytest.approx(100 - 4)
