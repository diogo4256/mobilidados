"""Stage selection, the table hand-over between stages and the pin check, on a minimal case (no network)."""

import pandas as pd
import pytest

from mobilidados.config import Case, MobilidadosError
from mobilidados.pipeline import Run, run

PINNED_FEED = '[sources.feed]\nkind = "http_file"\nurl = "https://example.org/gtfs.zip"\nsha256 = "{}"\nlicence = "x"\n'


def test_an_unknown_stage_is_rejected_before_anything_runs(make_case):
    case = Case.load(make_case())
    with pytest.raises(MobilidadosError) as err:
        run(case, stages=["profiles", "nope"])
    assert str(err.value).startswith("unknown stages ['nope']")  # only the unknown ones, then the stages that exist
    assert not case.results_dir.exists()


def test_a_table_that_was_never_written_is_an_error_naming_it(make_case):
    r = Run(Case.load(make_case()))
    with pytest.raises(MobilidadosError, match="table 'x' is missing"):
        r.table("x")


def test_a_table_written_by_an_earlier_run_is_read_back(make_case):
    case = Case.load(make_case())
    df = pd.DataFrame({"a": [1, 2], "b": ["u", "v"]})
    Run(case).save("t", df)
    pd.testing.assert_frame_equal(Run(case).table("t"), df)


def test_a_cached_file_that_differs_from_its_pin_stops_the_run(make_case):
    case = Case.load(make_case(PINNED_FEED.format("0" * 64)))
    case.raw_dir.mkdir(parents=True)
    (case.raw_dir / "feed.zip").write_bytes(b"not the pinned feed")
    with pytest.raises(MobilidadosError, match="do not match the sha256 pinned"):
        run(case, stages=["standards"])
