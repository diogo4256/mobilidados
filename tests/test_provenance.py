"""Snapshots, restoring from a snapshot, the lock file and pinned downloads, on a minimal case (no network)."""

import json

import pytest

from streetfit import sources
from streetfit.config import Case, StreetfitError
from streetfit.provenance import Lock
from streetfit.sources import fetch, raw_path, snapshot

IDENTIFY = """
[sources.identify]
kind = "arcgis_identify"
url = "https://example.org/MapServer/identify"
layers = "all:1"
sr = 3763
licence = "CC-BY-4.0"
redistributable = true
"""


def test_snapshot_roundtrip(make_case, tmp_path):
    src = Case.load(make_case(IDENTIFY, name="a"))
    src.raw_dir.mkdir(parents=True)
    for sid, payload in [("cartography", {"features": [1]}), ("street_axes", {"features": [2]}), ("identify", {"1,2": []})]:
        raw_path(src, sid).write_text(json.dumps(payload))
    lock = Lock(src.lock_path)
    lock.record("cartography", [raw_path(src, "cartography")], src.raw_dir, retrieved_utc="2026-10-24T00:00:00+00:00")
    lock.save()

    left_out = snapshot(src, tmp_path / "snap")
    assert left_out == ["street_axes"]  # its licence is not stated, so it is not redistributable
    assert sorted(p.name for p in (tmp_path / "snap").iterdir()) == ["_snapshot.json", "cartography.json", "identify.json"]

    dst = Case.load(make_case(IDENTIFY, name="b"))
    fetch(dst, only=["cartography", "identify"], from_dir=tmp_path / "snap")
    entries = Lock(dst.lock_path).entries
    assert entries["cartography"]["retrieved_utc"] == "2026-10-24T00:00:00+00:00"  # original retrieval kept
    assert raw_path(dst, "identify").exists()  # identify caches restore too, so the case can run offline
    assert all(status == "ok" for *_, status in Lock(dst.lock_path).verify(dst.raw_dir))
    with pytest.raises(StreetfitError, match="not in the snapshot"):
        fetch(dst, only=["street_axes"], from_dir=tmp_path / "snap")


def test_lock_detects_changed_and_missing_files(make_case):
    case = Case.load(make_case())
    case.raw_dir.mkdir(parents=True)
    p = raw_path(case, "cartography")
    p.write_text("{}")
    lock = Lock(case.lock_path)
    lock.record("cartography", [p], case.raw_dir)
    lock.save()
    p.write_text('{"changed": true}')
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["changed"]
    p.unlink()
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["missing"]


def test_a_changed_upstream_file_never_replaces_the_pinned_one(make_case, monkeypatch):
    pinned = "0" * 64
    case = Case.load(
        make_case(f'[sources.feed]\nkind = "http_file"\nurl = "https://example.org/gtfs.zip"\nsha256 = "{pinned}"\nlicence = "x"\n')
    )

    class Response:
        content = b"a newer feed"

    monkeypatch.setattr(sources, "http_get", lambda url, timeout: Response())
    with pytest.raises(StreetfitError, match="different file"):
        fetch(case, only=["feed"])
    assert not raw_path(case, "feed").exists()
    assert "feed" not in Lock(case.lock_path).entries
