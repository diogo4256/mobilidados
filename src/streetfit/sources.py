"""Fetch a case's sources into ``data/raw/`` and record them in ``sources.lock.json``.

The source kinds are the models in :mod:`streetfit.config`: ``arcgis_query``, ``http_file``, ``http_files`` and
``arcgis_identify`` (point queries made during the analysis, cached in one JSON file and locked afterwards).
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import arcgis
from .config import AnySource, ArcgisIdentify, ArcgisQuery, Case, HttpFile, HttpFiles, StreetfitError
from .provenance import DOWNLOAD_TIMEOUT_S, Lock, http_get, now_utc, sha256_bytes, sha256_file, write_atomic

log = logging.getLogger(__name__)


def raw_path(case: Case, source_id: str) -> Path:
    src = case.source(source_id)
    if isinstance(src, HttpFile):
        return case.raw_dir / f"{source_id}{src.suffix or Path(urlparse(src.url).path).suffix or '.bin'}"
    if isinstance(src, HttpFiles):
        return case.raw_dir / source_id
    return case.raw_dir / f"{source_id}.json"


def _files_of(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]


def fetch(case: Case, only: list[str] | None = None, refresh: bool = False, from_dir: Path | None = None) -> None:
    """Download (or copy from ``from_dir``, e.g. an archived snapshot) every source that is not cached yet."""
    case.raw_dir.mkdir(parents=True, exist_ok=True)
    lock = Lock(case.lock_path)
    snapshot_meta = (
        json.loads((from_dir / "_snapshot.json").read_text(encoding="utf-8")) if from_dir and (from_dir / "_snapshot.json").exists() else {}
    )
    for sid in only or list(case.config.sources):
        src, dest = case.source(sid), raw_path(case, sid)
        origin = from_dir / dest.name if from_dir is not None else None
        if isinstance(src, ArcgisIdentify) and not (origin and origin.exists()):
            continue  # filled during the analysis (unless a snapshot has it), locked by `lock_identify_caches`
        if dest.exists() and not refresh:
            log.info("cached   %s", sid)
            continue
        if origin is not None:
            if not origin.exists():
                raise StreetfitError(f"{sid}: {origin} is not in the snapshot; fetch it without --from-dir")
            if origin.is_dir():
                shutil.copytree(origin, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(origin, dest)
            log.info("copied   %s <- %s", sid, origin)
            # keep the original retrieval metadata: from the lock, else from the snapshot's _snapshot.json
            meta = lock.entries.get(sid) or snapshot_meta.get(sid) or {"kind": src.kind, "retrieved_utc": "unknown"}
        else:
            meta = _download(src, dest)
            log.info("fetched  %s", sid)
        lock.record(sid, _files_of(dest), case.raw_dir, **{k: v for k, v in meta.items() if k != "files"})
        lock.save()  # after each source, so a failure further on does not lose what was already fetched


def snapshot(case: Case, out_dir: Path) -> list[str]:
    """Copy the cached sources that may be redistributed (``redistributable = true``) into ``out_dir``, with their
    lock metadata in ``_snapshot.json``, ready to archive (e.g. on Zenodo) and restore with ``fetch --from-dir``.
    Returns the ids of the sources left out, which a user of the snapshot fetches from their origin."""
    lock = Lock(case.lock_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta, skipped = {}, []
    for sid, src in case.config.sources.items():
        p = raw_path(case, sid)
        if not src.redistributable or not p.exists():
            skipped.append(sid)
            continue
        if p.is_dir():
            shutil.copytree(p, out_dir / p.name, dirs_exist_ok=True)
        else:
            shutil.copy2(p, out_dir / p.name)
        meta[sid] = lock.entries.get(sid, {}) | {"licence": src.licence, "attribution": src.attribution}
        log.info("added    %s", sid)
    (out_dir / "_snapshot.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for sid in skipped:
        log.info("left out %s (not marked redistributable)", sid)
    return skipped


def _download(src: AnySource, dest: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {"kind": src.kind, "retrieved_utc": now_utc(), "licence": src.licence}
    if isinstance(src, ArcgisQuery):
        data = arcgis.query_layer(src.url, src.envelope, in_sr=src.envelope_sr, out_sr=src.out_sr, where=src.where)
        write_atomic(dest, json.dumps(data, ensure_ascii=False).encode())
        meta |= {
            "url": src.url,
            "envelope": list(src.envelope),
            "envelope_sr": src.envelope_sr,
            "where": src.where,
            "n_features": len(data["features"]),
            "copyrightText": data.get("copyrightText"),
        }
    elif isinstance(src, HttpFile):
        content = http_get(src.url, timeout=DOWNLOAD_TIMEOUT_S).content
        if src.sha256 and sha256_bytes(content) != src.sha256:
            raise StreetfitError(
                f"{src.url} now serves a different file (sha256 {sha256_bytes(content)[:12]}…) from the one pinned in "
                f"case.toml ({src.sha256[:12]}…); nothing was written. Use an archived copy or update the pin deliberately."
            )
        write_atomic(dest, content)
        meta |= {"url": src.url}
    elif isinstance(src, HttpFiles):
        dest.mkdir(parents=True, exist_ok=True)
        for f in src.files:
            write_atomic(dest / f.name, http_get(f.url, timeout=DOWNLOAD_TIMEOUT_S).content)
        meta |= {"urls": {f.name: f.url for f in src.files}}
    return meta


def check_pins(case: Case) -> list[str]:
    """Sources whose TOML pins a sha256 that the cached file does not match (e.g. a newer GTFS feed)."""
    bad = []
    for sid, src in case.config.sources.items():
        p = raw_path(case, sid)
        if isinstance(src, HttpFile) and src.sha256 and p.is_file() and sha256_file(p) != src.sha256:
            bad.append(sid)
    return bad


def lock_identify_caches(case: Case) -> None:
    lock = Lock(case.lock_path)
    for sid, src in case.config.sources.items():
        p = raw_path(case, sid)
        if isinstance(src, ArcgisIdentify) and p.exists():
            lock.record(
                sid,
                [p],
                case.raw_dir,
                kind=src.kind,
                url=src.url,
                layers=src.layers,
                retrieved_utc=lock.entries.get(sid, {}).get("retrieved_utc") or now_utc(),
                licence=src.licence,
            )
    lock.save()


def load_json(case: Case, source_id: str) -> dict[str, Any]:
    path = raw_path(case, source_id)
    if not path.exists():
        raise StreetfitError(f"{path} is missing: run `streetfit fetch {case.root}` first")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


class IdentifyCache:
    """Point identify results cached on disk, keyed by rounded coordinates, so re-runs work offline."""

    def __init__(self, case: Case, source_id: str, offline: bool = False):
        src = case.source(source_id)
        if not isinstance(src, ArcgisIdentify):
            raise StreetfitError(f"source {source_id!r} is not an arcgis_identify source")
        self.src, self.path, self.offline = src, raw_path(case, source_id), offline
        self.data: dict[str, list[dict[str, Any]]] = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        self.dirty = False

    def get(self, x: float, y: float, tolerance: float | None = None) -> list[dict[str, Any]]:
        tol = self.src.tolerance if tolerance is None else tolerance
        key = f"{x:.0f},{y:.0f}" + ("" if tol == self.src.tolerance else f"@{tol:g}")
        if key not in self.data:
            if self.offline:
                raise StreetfitError(f"identify {key} is not cached and --offline is set")
            self.data[key] = arcgis.identify(self.src.url, x, y, self.src.sr, self.src.layers, tol)
            self.dirty = True
        return self.data[key]

    def save(self) -> None:
        if self.dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
