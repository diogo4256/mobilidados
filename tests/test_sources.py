"""Fetching sources, snapshots and restoring from them, pinned downloads and the identify cache, with the network faked."""

import json

import pytest

from streetfit import arcgis, sources
from streetfit.config import Case, StreetfitError
from streetfit.provenance import DOWNLOAD_TIMEOUT_S, Lock
from streetfit.sources import IdentifyCache, fetch, lock_identify_caches, raw_path, snapshot

IDENTIFY = """
[sources.identify]
kind = "arcgis_identify"
url = "https://example.org/MapServer/identify"
layers = "all:1"
sr = 3763
tolerance = 3
licence = "not stated"
"""

REDISTRIBUTABLE_IDENTIFY = """
[sources.identify]
kind = "arcgis_identify"
url = "https://example.org/MapServer/identify"
layers = "all:1"
sr = 3763
licence = "CC-BY-4.0"
redistributable = true
"""

DOWNLOADS = """
[sources.feed]
kind = "http_file"
url = "https://example.org/gtfs"
suffix = ".zip"
licence = "x"

[sources.reports]
kind = "http_files"
licence = "x"
files = [
  { name = "2024.csv", url = "https://example.org/2024.csv" },
  { name = "2025.csv", url = "https://example.org/2025.csv" },
]
"""


def identify_cache(make_case, offline=False, cached=None):
    case = Case.load(make_case(IDENTIFY))
    if cached is not None:
        case.raw_dir.mkdir(parents=True)
        raw_path(case, "identify").write_text(json.dumps(cached, indent=1), encoding="utf-8")
    return case, IdentifyCache(case, "identify", offline=offline)


def no_network(*args, **kwargs):
    raise AssertionError("the network must not be called")


def test_offline_an_uncached_point_is_an_error_and_a_cached_one_needs_no_network(make_case, monkeypatch):
    monkeypatch.setattr(arcgis, "identify", no_network)
    _, cache = identify_cache(make_case, offline=True, cached={"1000,2000": [{"Oneway": "Traversable"}]})
    assert cache.get(1000.2, 1999.8) == [{"Oneway": "Traversable"}]  # keyed by the rounded coordinates
    with pytest.raises(StreetfitError, match=r"identify 1500,2000 is not cached"):
        cache.get(1500, 2000)
    with pytest.raises(StreetfitError, match=r"identify 1000,2000@5 is not cached"):
        cache.get(1000, 2000, tolerance=5)  # another tolerance is another query


def test_a_cache_that_fetched_nothing_does_not_rewrite_its_file(make_case, monkeypatch):
    monkeypatch.setattr(arcgis, "identify", no_network)
    case, cache = identify_cache(make_case, cached={"1000,2000": []})
    before = raw_path(case, "identify").read_text(encoding="utf-8")
    cache.get(1000, 2000)
    cache.save()
    assert raw_path(case, "identify").read_text(encoding="utf-8") == before  # not even re-serialised


def test_an_unused_cache_does_not_create_its_file(make_case):
    case, cache = identify_cache(make_case)
    cache.save()
    assert not raw_path(case, "identify").exists()


def test_a_new_point_is_fetched_once_and_saved(make_case, monkeypatch):
    calls = []

    def identify(url, x, y, sr, layers, tolerance):
        calls.append((url, x, y, sr, layers, tolerance))
        return [{"Oneway": "Prohibited"}]

    monkeypatch.setattr(arcgis, "identify", identify)
    case, cache = identify_cache(make_case, cached={"1000,2000": []})
    assert cache.get(1000, 2000) == []
    assert cache.get(1500, 2500) == [{"Oneway": "Prohibited"}]
    assert cache.get(1500, 2500) == [{"Oneway": "Prohibited"}]
    assert calls == [("https://example.org/MapServer/identify", 1500, 2500, 3763, "all:1", 3)]
    cache.save()
    assert json.loads(raw_path(case, "identify").read_text(encoding="utf-8")) == {"1000,2000": [], "1500,2500": [{"Oneway": "Prohibited"}]}

    cache.get(1500, 2500, tolerance=8)  # the tolerance is passed on and part of the key
    assert calls[-1][-1] == 8
    assert "1500,2500@8" in cache.data


def test_identify_caches_are_locked_and_keep_their_first_retrieval_time(make_case, monkeypatch):
    monkeypatch.setattr(arcgis, "identify", lambda *a: [])
    case, cache = identify_cache(make_case)
    cache.get(1000, 2000)
    cache.save()
    lock_identify_caches(case)
    first = Lock(case.lock_path).entries["identify"]
    assert first["layers"] == "all:1"
    assert list(first["files"]) == ["identify.json"]

    cache.get(1100, 2000)
    cache.save()
    lock_identify_caches(case)
    second = Lock(case.lock_path).entries["identify"]
    assert second["retrieved_utc"] == first["retrieved_utc"]
    assert second["files"] != first["files"]  # the new checksum
    assert all(status == "ok" for *_, status in Lock(case.lock_path).verify(case.raw_dir))


def test_fetch_downloads_every_kind_locks_it_and_skips_what_is_cached(make_case, monkeypatch):
    requests = []

    class Response:
        def __init__(self, content):
            self.content = content

    def http_get(url, timeout):
        requests.append((url, timeout))
        return Response(f"body of {url}".encode())

    def query_layer(url, envelope, in_sr, out_sr, where):
        return {"features": [{"attributes": {"id": 1}}, {"attributes": {"id": 2}}], "copyrightText": "(c) example"}

    monkeypatch.setattr(sources, "http_get", http_get)
    monkeypatch.setattr(arcgis, "query_layer", query_layer)
    case = Case.load(make_case(DOWNLOADS))

    fetch(case)
    assert raw_path(case, "feed").read_bytes() == b"body of https://example.org/gtfs"
    assert sorted(p.name for p in raw_path(case, "reports").iterdir()) == ["2024.csv", "2025.csv"]
    assert len(json.loads(raw_path(case, "cartography").read_text(encoding="utf-8"))["features"]) == 2
    assert {t for _, t in requests} == {DOWNLOAD_TIMEOUT_S}
    entries = Lock(case.lock_path).entries
    assert set(entries) == {"cartography", "street_axes", "feed", "reports"}
    assert entries["cartography"]["n_features"] == 2
    assert entries["reports"]["urls"] == {"2024.csv": "https://example.org/2024.csv", "2025.csv": "https://example.org/2025.csv"}
    assert all(status == "ok" for *_, status in Lock(case.lock_path).verify(case.raw_dir))

    n = len(requests)
    fetch(case)
    assert len(requests) == n  # everything is cached
    fetch(case, only=["feed"], refresh=True)
    assert len(requests) == n + 1


def test_snapshot_roundtrip(make_case, tmp_path):
    src = Case.load(make_case(REDISTRIBUTABLE_IDENTIFY, name="a"))
    src.raw_dir.mkdir(parents=True)
    for sid, payload in [("cartography", {"features": [1]}), ("street_axes", {"features": [2]}), ("identify", {"1,2": []})]:
        raw_path(src, sid).write_text(json.dumps(payload))
    lock = Lock(src.lock_path)
    lock.record("cartography", [raw_path(src, "cartography")], src.raw_dir, retrieved_utc="2026-10-24T00:00:00+00:00")
    lock.save()

    left_out = snapshot(src, tmp_path / "snap")
    assert left_out == ["street_axes"]  # its licence is not stated, so it is not redistributable
    assert sorted(p.name for p in (tmp_path / "snap").iterdir()) == ["_snapshot.json", "cartography.json", "identify.json"]

    dst = Case.load(make_case(REDISTRIBUTABLE_IDENTIFY, name="b"))
    fetch(dst, only=["cartography", "identify"], from_dir=tmp_path / "snap")
    entries = Lock(dst.lock_path).entries
    assert entries["cartography"]["retrieved_utc"] == "2026-10-24T00:00:00+00:00"  # original retrieval kept
    assert raw_path(dst, "identify").exists()  # identify caches restore too, so the case can run offline
    assert all(status == "ok" for *_, status in Lock(dst.lock_path).verify(dst.raw_dir))
    with pytest.raises(StreetfitError, match="not in the snapshot"):
        fetch(dst, only=["street_axes"], from_dir=tmp_path / "snap")


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
