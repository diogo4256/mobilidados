"""HTTP access, checksums and the sources lock file.

Every input is recorded in ``sources.lock.json`` with its URL, query, retrieval time, size and SHA-256.
Re-running a case with the same cache reproduces the results bit for bit; re-fetching from live services
tells you, file by file, whether the upstream data changed since the reference run.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from . import __version__


def user_agent() -> str:
    """Identify the tool to the data provider. Set STREETFIT_CONTACT to add your own contact (optional)."""
    contact = os.environ.get("STREETFIT_CONTACT")
    return f"streetfit/{__version__}" + (f" ({contact})" if contact else "")


def http_get(url: str, params: dict | None = None, timeout: float = 120, retries: int = 3) -> requests.Response:
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": user_agent()})
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


class Lock:
    """``sources.lock.json``: what was fetched, from where, when, and its checksum."""

    def __init__(self, path: Path):
        self.path = path
        self.entries: dict[str, dict[str, Any]] = json.loads(path.read_text()) if path.exists() else {}

    def record(self, source_id: str, files: list[Path], base: Path, **meta: Any) -> None:
        self.entries[source_id] = {
            **meta,
            "files": {str(p.relative_to(base)): {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in sorted(files)},
        }

    def save(self) -> None:
        self.path.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    def verify(self, base: Path) -> list[tuple[str, str, str]]:
        """Compare files on disk with the lock. Returns (source_id, file, status) for every locked file."""
        out = []
        for sid, entry in sorted(self.entries.items()):
            for rel, meta in sorted(entry.get("files", {}).items()):
                p = base / rel
                status = "missing" if not p.exists() else ("ok" if sha256_file(p) == meta["sha256"] else "changed")
                out.append((sid, rel, status))
        return out
