"""HTTP access, checksums and the sources lock file.

Every input is recorded in ``sources.lock.json`` with its URL, query, retrieval time, size and SHA-256.
Re-running a case with the same cache reproduces the results bit for bit; re-fetching from live services
tells you, file by file, whether the upstream data changed since the reference run.
"""

from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import __version__

REQUEST_TIMEOUT_S = 120  # seconds, for service queries
DOWNLOAD_TIMEOUT_S = 600  # seconds, for whole files (a GTFS feed, yearly CSVs), which can be much larger than a query response


def user_agent() -> str:
    """Identify the tool to the data provider. Set STREETFIT_CONTACT to add your own contact (optional)."""
    contact = os.environ.get("STREETFIT_CONTACT")
    return f"streetfit/{__version__}" + (f" ({contact})" if contact else "")


@functools.cache
def session() -> requests.Session:
    """A shared HTTP session that retries transient failures (connection errors, 429 and 5xx) with backoff."""
    s = requests.Session()
    retry = Retry(total=4, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504), allowed_methods={"GET"})
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = user_agent()
    return s


def http_get(url: str, params: dict[str, Any] | None = None, timeout: float = REQUEST_TIMEOUT_S) -> requests.Response:
    r = session().get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_atomic(path: Path, data: bytes) -> None:
    """Write via a temporary file, so an interrupted download never leaves a truncated file in the cache."""
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


class Lock:
    """``sources.lock.json``: what was fetched, from where, when, and its checksum."""

    def __init__(self, path: Path):
        self.path = path
        self.entries: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def record(self, source_id: str, files: list[Path], base: Path, **meta: Any) -> None:
        self.entries[source_id] = {
            **meta,
            "files": {p.relative_to(base).as_posix(): {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in sorted(files)},
        }

    def save(self) -> None:
        self.path.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def verify(self, base: Path) -> list[tuple[str, str, str]]:
        """Compare files on disk with the lock. Returns (source_id, file, status) for every locked file."""
        out = []
        for sid, entry in sorted(self.entries.items()):
            for rel, meta in sorted(entry.get("files", {}).items()):
                p = base / rel
                status = "missing" if not p.exists() else ("ok" if sha256_file(p) == meta["sha256"] else "changed")
                out.append((sid, rel, status))
        return out
