"""Reading a git archive of real-time snapshots: only the period's files, the case's routes inside the envelope, the
archive's own text, and the same bytes on every reading."""

import datetime as dt
import os
import shutil
import subprocess

import pytest

from mobilidados import archive
from mobilidados.config import GitArchive, MobilidadosError

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs the git command")

HEADER = "id,trip_id,route_id,direction_id,latitude,longitude,current_stop_sequence,current_status,timestamp,stop_id,vehicle_id,license_plate,geometry\n"


def row(route, lat, lon, trip="t1", ts="2025-03-10 17:00:00"):
    return f"x,{trip},{route},0,{lat},{lon},5,IN_TRANSIT_TO,{ts},11315,v1,AA-00-00,POINT ({lon} {lat})\n"


def git(repo, *args):
    # the whole environment (git on Windows needs more than PATH), with an author for the test commits
    who = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org"}
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=os.environ | who).stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "archive"
    folder = r / "data"
    folder.mkdir(parents=True)
    git(r, "init", "--quiet")
    snaps = {
        "feed-2025-03-09-23-59-00.csv": HEADER + row("200_0", 38.75, -9.14),  # the day before the period
        "feed-2025-03-10-17-00-00.csv": HEADER
        + row("200_0", 38.75, -9.14)  # kept
        + row("200_0", 38.90, -9.14)  # outside the envelope
        + row("999_0", 38.75, -9.14)  # another route
        + row("239_0", "", "", trip="t2"),  # no position
        "feed-2025-03-10-17-04-30.csv": HEADER,  # the feed did not answer
        "feed-2025-03-11-08-00-00.csv": HEADER + row("239_0", 38.751, -9.139, trip="t3", ts="2025-03-11 07:59:40"),
        "notes.txt": "not a snapshot",
    }
    for name, text in snaps.items():
        (folder / name).write_text(text, encoding="utf-8")
    git(r, "add", ".")
    git(r, "commit", "--quiet", "-m", "snapshots")
    return r, git(r, "rev-parse", "HEAD").strip()


def source(commit, **kw):
    return GitArchive(
        kind="git_archive",
        licence="not stated",
        url="https://example.org/archive",
        commit=commit,
        path="data",
        prefix="feed-",
        period=kw.pop("period", (dt.date(2025, 3, 10), dt.date(2025, 3, 11))),
        route_ids=["200_0", "239_0"],
        envelope=(-9.2, 38.7, -9.1, 38.8),
        **kw,
    )


def test_the_period_s_snapshots_keep_the_routes_inside_the_envelope(repo, tmp_path):
    r, commit = repo
    counts = archive.extract(r, source(commit), tmp_path / "out")
    assert counts == {"snapshots": 3, "positions": 2}
    snaps = (tmp_path / "out" / "snapshots.csv").read_text(encoding="utf-8").splitlines()
    assert snaps == [
        "snapshot,vehicles,vehicles_on_routes,positions_kept",
        "2025-03-10T17:00:00,4,3,1",  # four vehicles, three on the case's routes, one of them inside the envelope with a position
        "2025-03-10T17:04:30,0,0,0",  # listed, so the gap can be counted; the analysis leaves it out
        "2025-03-11T08:00:00,1,1,1",
    ]
    positions = (tmp_path / "out" / "positions.csv").read_text(encoding="utf-8").splitlines()
    assert positions[0].split(",") == archive.POSITION_COLUMNS
    # the archive's own text, unchanged: no number is parsed and printed again
    assert positions[2] == "2025-03-11T08:00:00,t3,239_0,0,v1,2025-03-11 07:59:40,38.751,-9.139,IN_TRANSIT_TO,11315,5"


def test_two_readings_of_the_same_commit_are_the_same_bytes(repo, tmp_path):
    r, commit = repo
    archive.extract(r, source(commit), tmp_path / "a")
    archive.extract(r, source(commit), tmp_path / "b")
    for name in archive.FILES:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_a_later_commit_does_not_change_what_the_pinned_one_holds(repo, tmp_path):
    r, commit = repo
    (r / "data" / "feed-2025-03-11-09-00-00.csv").write_text(HEADER + row("200_0", 38.75, -9.14), encoding="utf-8")
    git(r, "add", ".")
    git(r, "commit", "--quiet", "-m", "one more")
    assert archive.extract(r, source(commit), tmp_path / "out")["snapshots"] == 3


def test_a_period_without_snapshots_is_an_error(repo, tmp_path):
    r, commit = repo
    with pytest.raises(MobilidadosError, match="has no file data/feed-"):
        archive.extract(r, source(commit, period=(dt.date(2024, 1, 1), dt.date(2024, 1, 31))), tmp_path / "out")


def test_the_period_must_be_in_order():
    with pytest.raises(ValueError, match="the first day comes after the last"):
        source("0" * 40, period=(dt.date(2025, 3, 11), dt.date(2025, 3, 10)))
