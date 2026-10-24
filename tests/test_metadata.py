"""Repository metadata agrees with the package."""

from pathlib import Path

import streetfit

ROOT = Path(__file__).resolve().parents[1]


def test_citation_matches_the_package_version():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f"\nversion: {streetfit.__version__}\n" in cff
