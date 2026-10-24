"""Fetch a case's sources into ``data/raw/`` and record them in ``sources.lock.json``.

Source kinds (``kind`` in the case/city TOML):

* ``arcgis_query`` - features of one MapServer layer intersecting ``envelope`` (optionally filtered by ``where``)
* ``http_file``    - one file (e.g. a GTFS zip); ``sha256`` in the lock pins the exact version used
* ``http_files``   - several files listed as ``files = [{name, url}, ...]`` (e.g. yearly open-data CSVs)
* ``arcgis_identify`` - point queries made during the analysis; cached in one JSON file and locked afterwards
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import arcgis
from .config import Case
from .provenance import Lock, http_get, now_utc, sha256_file


def raw_path(case: Case, source_id: str) -> Path:
    src = case.source(source_id)
    kind = src["kind"]
    if kind in ("arcgis_query", "arcgis_identify"):
        return case.raw_dir / f"{source_id}.json"
    if kind == "http_file":
        return case.raw_dir / f"{source_id}{src.get('suffix', Path(src['url']).suffix or '.bin')}"
    if kind == "http_files":
        return case.raw_dir / source_id
    raise ValueError(f"source {source_id}: unknown kind {kind!r}")


def _files_of(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]


def fetch(case: Case, only: list[str] | None = None, refresh: bool = False, from_dir: Path | None = None, log=print) -> None:
    """Download (or copy from ``from_dir``, e.g. an archived snapshot) every source that is not cached yet."""
    case.raw_dir.mkdir(parents=True, exist_ok=True)
    lock = Lock(case.lock_path)
    snapshot_meta = json.loads((from_dir / "_snapshot.json").read_text()) if from_dir and (from_dir / "_snapshot.json").exists() else {}
    for sid in only or case.source_ids():
        src = case.source(sid)
        if src["kind"] == "arcgis_identify":
            continue  # filled during the analysis, locked by `lock_identify_caches`
        dest = raw_path(case, sid)
        if dest.exists() and not refresh:
            log(f"  cached   {sid}")
            continue
        if from_dir is not None:
            origin = from_dir / dest.name
            if origin.is_dir():
                shutil.copytree(origin, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(origin, dest)
            log(f"  copied   {sid} <- {origin}")
            # keep the original retrieval metadata: from the lock, else from the snapshot's _snapshot.json
            meta = lock.entries.get(sid) or snapshot_meta.get(sid) or {"kind": src["kind"], "retrieved_utc": "unknown"}
        else:
            meta = _download(src, dest)
            log(f"  fetched  {sid}")
        lock.record(sid, _files_of(dest), case.raw_dir, **{k: v for k, v in meta.items() if k != "files"})
    lock.save()


def _download(src: dict, dest: Path) -> dict:
    kind, meta = src["kind"], {"kind": src["kind"], "retrieved_utc": now_utc(), "licence": src.get("licence", "unknown")}
    if kind == "arcgis_query":
        env, in_sr = src["envelope"], int(src.get("envelope_sr", 4326))
        data = arcgis.query_layer(src["url"], env, in_sr=in_sr, out_sr=int(src["out_sr"]), where=src.get("where", "1=1"))
        dest.write_text(json.dumps(data, ensure_ascii=False))
        meta |= {
            "url": src["url"],
            "envelope": env,
            "envelope_sr": in_sr,
            "where": src.get("where", "1=1"),
            "n_features": len(data["features"]),
            "copyrightText": data.get("copyrightText"),
        }
    elif kind == "http_file":
        dest.write_bytes(http_get(src["url"], timeout=600).content)
        meta |= {"url": src["url"]}
    elif kind == "http_files":
        dest.mkdir(parents=True, exist_ok=True)
        for f in src["files"]:
            (dest / f["name"]).write_bytes(http_get(f["url"], timeout=600).content)
        meta |= {"urls": {f["name"]: f["url"] for f in src["files"]}}
    return meta


def check_pins(case: Case) -> list[str]:
    """Sources whose TOML pins a sha256 that the cached file does not match (e.g. a newer GTFS feed)."""
    bad = []
    for sid in case.source_ids():
        pin = case.source(sid).get("sha256")
        p = raw_path(case, sid)
        if pin and p.exists() and p.is_file() and sha256_file(p) != pin:
            bad.append(sid)
    return bad


def lock_identify_caches(case: Case) -> None:
    lock = Lock(case.lock_path)
    for sid in case.source_ids():
        src = case.source(sid)
        p = raw_path(case, sid)
        if src["kind"] == "arcgis_identify" and p.exists():
            lock.record(
                sid,
                [p],
                case.raw_dir,
                kind="arcgis_identify",
                url=src["url"],
                layers=src["layers"],
                retrieved_utc=lock.entries.get(sid, {}).get("retrieved_utc") or now_utc(),
                licence=src.get("licence", "unknown"),
            )
    lock.save()


def load_json(case: Case, source_id: str) -> dict:
    return json.loads(raw_path(case, source_id).read_text())


class IdentifyCache:
    """Point identify results cached on disk, keyed by rounded coordinates, so re-runs work offline."""

    def __init__(self, case: Case, source_id: str, offline: bool = False):
        self.src, self.path, self.offline = case.source(source_id), raw_path(case, source_id), offline
        self.data: dict[str, list[dict]] = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.dirty = False

    def get(self, x: float, y: float, tolerance: float) -> list[dict]:
        key = f"{x:.0f},{y:.0f}" + ("" if tolerance == self.src.get("tolerance", 3) else f"@{tolerance:g}")
        if key not in self.data:
            if self.offline:
                raise RuntimeError(f"identify {key} not cached and --offline is set")
            self.data[key] = arcgis.identify(self.src["url"], x, y, int(self.src["sr"]), self.src["layers"], tolerance)
            self.dirty = True
        return self.data[key]

    def save(self) -> None:
        if self.dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, sort_keys=True))
