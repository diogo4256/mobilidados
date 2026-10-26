"""Fetch a case's sources into ``data/raw/`` and record them in ``sources.lock.json``.

The source kinds are the models in :mod:`mobilidados.config`: ``arcgis_query``, ``http_file``, ``http_files`` and
``arcgis_identify`` (point queries made during the analysis, cached in one JSON file and locked as it is saved).
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import arcgis
from .config import AnySource, ArcgisIdentify, ArcgisQuery, Case, HttpFile, HttpFiles, MobilidadosError
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
    """Download (or copy from ``from_dir``, e.g. an archived snapshot) every source that is not cached yet, or every
    source with ``refresh``. A source the lock knows must come out as exactly the files it records, or nothing is
    written: always from a folder, and from its service unless ``refresh`` takes the new data deliberately."""
    case.raw_dir.mkdir(parents=True, exist_ok=True)
    lock = Lock(case.lock_path)
    snapshot_meta = (
        json.loads((from_dir / "_snapshot.json").read_text(encoding="utf-8")) if from_dir and (from_dir / "_snapshot.json").exists() else {}
    )
    for sid in only or list(case.config.sources):
        src, dest = case.source(sid), raw_path(case, sid)
        origin = from_dir / dest.name if from_dir is not None else None
        if isinstance(src, ArcgisIdentify) and not (origin and origin.exists()):
            continue  # filled during the analysis (unless a snapshot has it), locked by `IdentifyCache.save`
        if _cached(src, dest) and not refresh:
            log.info("cached   %s", sid)
            continue
        with tempfile.TemporaryDirectory(dir=case.raw_dir) as tmp:  # the cache is only touched once the files pass
            new = Path(tmp) / dest.name
            if origin is not None:
                _copy(src, origin, new)
                # keep the original retrieval metadata: from the lock, else from the snapshot's _snapshot.json
                meta = lock.entries.get(sid) or snapshot_meta.get(sid) or {"kind": src.kind, "retrieved_utc": "unknown"}
            else:
                meta = _download(src, new)
            if isinstance(src, HttpFile) and src.sha256 and sha256_file(new) != src.sha256:
                raise MobilidadosError(f"{sid}: {origin} is not the file pinned in the case's configuration; nothing was written.")
            differ = _differences(lock, sid, new, dest.relative_to(case.raw_dir))
            if differ and origin is not None:
                raise MobilidadosError(
                    f"{sid}: {differ} in {from_dir} are missing, extra or different from sources.lock.json, so this is not "
                    "the data the case was run with; nothing was written."
                )
            if differ and not refresh:
                raise MobilidadosError(
                    f"{sid}: the service now serves different data from what sources.lock.json records ({differ}); nothing "
                    "was written. `mobilidados verify CASE --live` lists the differences; `fetch --refresh` takes the new "
                    "data deliberately (the lock changes, and the results may), and `fetch --refresh --from-dir FOLDER` "
                    "restores the locked files from an archive."
                )
            if dest.is_dir():
                shutil.rmtree(dest)
            new.replace(dest)
        log.info("%s %s", "copied  " if origin is not None else "fetched ", sid)
        lock.record(sid, _files_of(dest), case.raw_dir, **{k: v for k, v in meta.items() if k != "files"})
        lock.save()  # after each source, so a failure further on does not lose what was already fetched


def _copy(src: AnySource, origin: Path, new: Path) -> None:
    """Copy a source from a folder: for a multi-file source, only the files it names."""
    if not origin.exists():
        raise MobilidadosError(f"{origin} is not in the folder; fetch the source without --from-dir")
    if isinstance(src, HttpFiles):
        new.mkdir()
        for f in src.files:
            if not (origin / f.name).is_file():
                raise MobilidadosError(f"{origin / f.name} is not in the folder; nothing was written")
            shutil.copy2(origin / f.name, new / f.name)
    else:
        shutil.copy2(origin, new)


def _differences(lock: Lock, sid: str, new: Path, rel: Path) -> list[str]:
    """Files that are missing, extra or different, compared with the lock's entry for ``sid`` (none if it has no entry)."""
    locked = {f: m["sha256"] for f, m in lock.entries.get(sid, {}).get("files", {}).items()}
    if not locked:
        return []
    offered = {(rel / p.relative_to(new) if new.is_dir() else rel).as_posix(): sha256_file(p) for p in _files_of(new)}
    return sorted(f for f in locked.keys() | offered.keys() if locked.get(f) != offered.get(f))


def snapshot(case: Case, out_dir: Path) -> list[str]:
    """Copy the cached sources that may be redistributed (``redistributable = true``) into ``out_dir``, with their
    lock metadata in ``_snapshot.json``, ready to archive (e.g. on Zenodo) and restore with ``fetch --from-dir``.
    Returns the ids of the sources left out, which a user of the snapshot fetches from their origin."""
    lock = Lock(case.lock_path)
    archived = sorted(sid for sid, src in case.config.sources.items() if src.redistributable)
    # an archive is only worth anything if it holds exactly the locked files: refuse a cache with one missing or changed
    bad = [f"{f} ({status})" for sid, f, status in lock.verify(case.raw_dir) if sid in archived and status != "ok"]
    bad += [f"{sid} (not in the lock)" for sid in archived if sid not in lock.entries]
    if bad:
        raise MobilidadosError(
            f"the cache does not hold the locked files, so it cannot be archived: {bad}. Fetch them first, or restore them "
            "with `fetch --refresh --from-dir`; a routing-network cache is made by a run without --offline."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {}
    for sid in archived:
        for rel in lock.entries[sid]["files"]:  # the locked files only, not whatever else the folder holds
            (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(case.raw_dir / rel, out_dir / rel)
        src = case.config.sources[sid]
        meta[sid] = lock.entries[sid] | {"licence": src.licence, "attribution": src.attribution}
        log.info("added    %s", sid)
    (out_dir / "_snapshot.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    skipped = [sid for sid in case.config.sources if sid not in archived]
    for sid in skipped:
        log.info("left out %s (not marked redistributable)", sid)
    return skipped


def check_live(case: Case) -> list[tuple[str, str, str]]:
    """Download every source again into a temporary folder and compare it with the lock, leaving the cache and the
    lock as they are. Returns (source_id, file, status) with status ``same``, ``changed``, ``new`` (not in the lock)
    or ``error: ...`` (the source did not answer, or a pinned file is no longer served). Identify caches are left
    out: they are queried point by point during a run."""
    lock = Lock(case.lock_path)
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for sid, src in case.config.sources.items():
            if isinstance(src, ArcgisIdentify):
                continue
            dest = base / raw_path(case, sid).relative_to(case.raw_dir)
            log.info("checking %s", sid)  # a source that does not answer is retried for a while
            try:
                _download(src, dest)
            except MobilidadosError as e:
                out.append((sid, "", f"error: {e}"))
                continue
            locked = lock.entries.get(sid, {}).get("files", {})
            for p in _files_of(dest):
                rel = p.relative_to(base).as_posix()
                status = "new" if rel not in locked else ("same" if sha256_file(p) == locked[rel]["sha256"] else "changed")
                out.append((sid, rel, status))
    return out


def _cached(src: AnySource, dest: Path) -> bool:
    """A multi-file source is cached only when every file is there: a download that failed halfway is not."""
    if isinstance(src, HttpFiles):
        return all((dest / f.name).exists() for f in src.files)
    return dest.exists()


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
            raise MobilidadosError(
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


def check_lock(case: Case) -> list[str]:
    """Cached files whose sha256 differs from the one in the lock, which the ledger publishes. A missing file is not
    listed: a partial run may lack sources it does not read."""
    return [rel for _, rel, status in Lock(case.lock_path).verify(case.raw_dir) if status == "changed"]


def load_json(case: Case, source_id: str) -> dict[str, Any]:
    path = raw_path(case, source_id)
    if not path.exists():
        raise MobilidadosError(f"{path} is missing: run `mobilidados fetch {case.root}` first")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


class IdentifyCache:
    """Point identify results cached on disk, keyed by rounded coordinates, so re-runs work offline."""

    def __init__(self, case: Case, source_id: str, offline: bool = False):
        src = case.source(source_id)
        if not isinstance(src, ArcgisIdentify):
            raise MobilidadosError(f"source {source_id!r} is not an arcgis_identify source")
        self.case, self.source_id, self.src, self.path, self.offline = case, source_id, src, raw_path(case, source_id), offline
        self.data: dict[str, list[dict[str, Any]]] = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        self.dirty = False

    def get(self, x: float, y: float, tolerance: float | None = None) -> list[dict[str, Any]]:
        tol = self.src.tolerance if tolerance is None else tolerance
        key = f"{x:.0f},{y:.0f}" + ("" if tol == self.src.tolerance else f"@{tol:g}")
        if key not in self.data:
            if self.offline:
                raise MobilidadosError(f"identify {key} is not cached and --offline is set")
            self.data[key] = arcgis.identify(self.src.url, x, y, self.src.sr, self.src.layers, tol)
            self.dirty = True
        return self.data[key]

    def save(self) -> None:
        """Write the new answers and lock the file at once, so the lock (which the ledger publishes) never lags behind
        the cache, even when a run stops further on. Its time is that of the last change."""
        if not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(self.path, json.dumps(self.data, ensure_ascii=False, sort_keys=True).encode())
        lock = Lock(self.case.lock_path)
        lock.record(
            self.source_id,
            [self.path],
            self.case.raw_dir,
            kind=self.src.kind,
            url=self.src.url,
            layers=self.src.layers,
            retrieved_utc=now_utc(),
            licence=self.src.licence,
        )
        lock.save()
        self.dirty = False
