"""Snapshots, restoring from a snapshot and the lock file, on a minimal synthetic case (no network)."""

import json

from streetfit.config import Case
from streetfit.provenance import Lock
from streetfit.sources import fetch, raw_path, snapshot

CASE_TOML = """
[case]
id = "t"
[city]
crs = 3763
[street]
name = "X"
[sources.open_layer]
kind = "arcgis_query"
url = "https://example.org/MapServer/1"
envelope = [0, 0, 1, 1]
out_sr = 3763
licence = "CC-BY"
redistributable = true
[sources.closed_layer]
kind = "arcgis_query"
url = "https://example.org/MapServer/2"
envelope = [0, 0, 1, 1]
out_sr = 3763
licence = "not stated"
[sources.identify]
kind = "arcgis_identify"
url = "https://example.org/MapServer/identify"
layers = "all:1"
sr = 3763
licence = "CC-BY"
redistributable = true
"""


def make_case(root):
    root.mkdir()
    (root / "case.toml").write_text(CASE_TOML)
    return Case.load(root)


def test_snapshot_roundtrip(tmp_path):
    src = make_case(tmp_path / "a")
    src.raw_dir.mkdir(parents=True)
    for sid, payload in [("open_layer", {"features": [1]}), ("closed_layer", {"features": [2]}), ("identify", {"1,2": []})]:
        raw_path(src, sid).write_text(json.dumps(payload))
    lock = Lock(src.lock_path)
    lock.record("open_layer", [raw_path(src, "open_layer")], src.raw_dir, retrieved_utc="2026-10-24T00:00:00+00:00")
    lock.save()

    left_out = snapshot(src, tmp_path / "snap", log=lambda *_: None)
    assert left_out == ["closed_layer"]
    assert sorted(p.name for p in (tmp_path / "snap").iterdir()) == ["_snapshot.json", "identify.json", "open_layer.json"]

    dst = make_case(tmp_path / "b")
    fetch(dst, only=["open_layer", "identify"], from_dir=tmp_path / "snap", log=lambda *_: None)
    entries = Lock(dst.lock_path).entries
    assert entries["open_layer"]["retrieved_utc"] == "2026-10-24T00:00:00+00:00"  # original retrieval kept
    assert raw_path(dst, "identify").exists()  # identify caches restore too, so the case can run offline
    assert all(status == "ok" for *_, status in Lock(dst.lock_path).verify(dst.raw_dir))


def test_lock_detects_changed_and_missing_files(tmp_path):
    case = make_case(tmp_path / "c")
    case.raw_dir.mkdir(parents=True)
    p = raw_path(case, "open_layer")
    p.write_text("{}")
    lock = Lock(case.lock_path)
    lock.record("open_layer", [p], case.raw_dir)
    lock.save()
    p.write_text('{"changed": true}')
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["changed"]
    p.unlink()
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["missing"]
