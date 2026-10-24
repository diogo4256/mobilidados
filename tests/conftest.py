"""A minimal valid case, for tests that need a case folder without data."""

from pathlib import Path

import pytest

MINIMAL_CASE = """
[case]
id = "t"
title = "Test street"

[city]
id = "x"
name = "X"
crs = 3763

[cartography]
class_field = "LAYER"
road = ["road"]
parking = ["park"]

[axes]
name_field = "NAME"

[street]
name = "Test street"
headings = { "+" = "up", "-" = "down" }

[sources.cartography]
kind = "arcgis_query"
url = "https://example.org/MapServer/1"
envelope = [0, 0, 1, 1]
out_sr = 3763
licence = "CC-BY-4.0"
redistributable = true

[sources.street_axes]
kind = "arcgis_query"
url = "https://example.org/MapServer/2"
envelope = [0, 0, 1, 1]
out_sr = 3763
licence = "not stated"
"""


@pytest.fixture
def make_case(tmp_path: Path):
    """Write ``case.toml`` (``prefix``, e.g. an ``extends`` line, + the minimal case + ``extra``) into a new folder."""

    def make(extra: str = "", name: str = "case", prefix: str = "") -> Path:
        root = tmp_path / name
        root.mkdir()
        (root / "case.toml").write_text(prefix + MINIMAL_CASE + extra, encoding="utf-8")
        return root

    return make
