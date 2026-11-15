"""Vehicle positions from a git repository that archives a real-time feed, one CSV file per snapshot.

Some public projects poll an operator's real-time feed (GTFS-RT vehicle positions) every few minutes and commit
each answer to a git repository. A commit fixes every file it holds by its hash, so a case pins the archive to one
commit and reads it again bit for bit.

``extract`` reads the snapshots of a period from a local copy of the repository, as text, with ``git cat-file`` (no
checkout: the archive holds tens of thousands of files), and writes two files:

* ``snapshots.csv``: one row per snapshot read: its time, how many vehicles the feed listed, how many of them ran
  the case's routes, and how many of those were inside the envelope. A snapshot with no vehicles at all is a feed
  that did not answer; the analysis leaves it out, but it is listed, so the gaps can be counted.
* ``positions.csv``: one row per position kept (the case's routes, inside the envelope), with the snapshot it
  came from and the archive's own text for every field, unchanged.

The output depends only on the commit and the source's parameters, so the lock's sha256 of these two files says
whether anyone's extraction is the same as the case's. Nothing from the archive is executed.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .config import GitArchive, MobilidadosError

log = logging.getLogger(__name__)

SNAPSHOT_COLUMNS = ["snapshot", "vehicles", "vehicles_on_routes", "positions_kept"]
POSITION_COLUMNS = [
    "snapshot", "trip_id", "route_id", "direction_id", "vehicle_id", "timestamp", "latitude", "longitude",
    "current_status", "stop_id", "current_stop_sequence",
]  # fmt: skip
FILES = ("snapshots.csv", "positions.csv")
SNAPSHOT_TIME = "%Y-%m-%dT%H:%M:%S"  # how the snapshot time is written in both files


def _git(*args: str, cwd: Path | None = None) -> str:
    if shutil.which("git") is None:
        raise MobilidadosError("reading a git archive needs the `git` command, which is not installed")
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        raise MobilidadosError(f"git {' '.join(args[:2])} failed: {run.stderr.strip()[-500:]}")
    return run.stdout


def snapshot_files(repo: Path, src: GitArchive) -> list[tuple[str, dt.datetime]]:
    """(blob id, snapshot time) of every snapshot file of ``src.period`` at ``src.commit``, in time order."""
    listing = _git("ls-tree", src.commit, src.path.rstrip("/") + "/", cwd=repo)
    first, last = src.period
    out = []
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        _, kind, oid = meta.split()
        name = path.rsplit("/", 1)[-1]
        if kind != "blob" or not name.startswith(src.prefix) or not name.endswith(".csv"):
            continue
        try:
            when = dt.datetime.strptime(name[len(src.prefix) : -len(".csv")], src.time_format)
        except ValueError:
            log.warning("left out %s: its name does not hold a time in the format %s", name, src.time_format)
            continue
        if first <= when.date() <= last:
            out.append((oid, when))
    if not out:
        raise MobilidadosError(f"{src.url} at {src.commit[:12]} has no file {src.path}/{src.prefix}* between {first} and {last}")
    return sorted(out, key=lambda x: x[1])


def _blobs(repo: Path, oids: list[str]) -> Iterator[bytes]:
    """The contents of the blobs, in order, from one ``git cat-file --batch`` process."""
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        for oid in oids:
            proc.stdin.write(f"{oid}\n".encode())
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) != 3:
                raise MobilidadosError(f"git cat-file could not read {oid}: {b' '.join(header).decode(errors='replace')}")
            body = proc.stdout.read(int(header[2]))
            proc.stdout.read(1)  # the newline after each object
            yield body
    finally:
        proc.stdin.close()
        proc.stdout.close()
        proc.wait()


def extract(repo: Path, src: GitArchive, out_dir: Path) -> dict[str, Any]:
    """Write ``snapshots.csv`` and ``positions.csv`` (see the module) from the repository at ``repo``."""
    files = snapshot_files(repo, src)
    lon0, lat0, lon1, lat1 = src.envelope
    routes = set(src.route_ids)
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = 0
    with (
        (out_dir / "snapshots.csv").open("w", encoding="utf-8", newline="") as fs,
        (out_dir / "positions.csv").open("w", encoding="utf-8", newline="") as fp,
    ):
        ws, wp = csv.writer(fs, lineterminator="\n"), csv.writer(fp, lineterminator="\n")
        ws.writerow(SNAPSHOT_COLUMNS)
        wp.writerow(POSITION_COLUMNS)
        for i, ((_, when), body) in enumerate(zip(files, _blobs(repo, [oid for oid, _ in files]), strict=True)):
            snap = when.strftime(SNAPSHOT_TIME)
            n = on_routes = here = 0
            for row in csv.DictReader(io.StringIO(body.decode("utf-8", "replace"))):
                n += 1
                if row.get("route_id") not in routes:
                    continue
                on_routes += 1
                try:
                    lat, lon = float(row["latitude"]), float(row["longitude"])
                except (KeyError, TypeError, ValueError):
                    continue
                if lon0 <= lon <= lon1 and lat0 <= lat <= lat1:
                    here += 1
                    wp.writerow([snap, *(row.get(c, "") for c in POSITION_COLUMNS[1:])])
            ws.writerow([snap, n, on_routes, here])
            kept += here
            if i % 10_000 == 0:
                log.info("  %s: %d of %d snapshots read", snap[:10], i, len(files))
    return {"snapshots": len(files), "positions": kept}


def download(src: GitArchive, dest: Path) -> dict[str, Any]:
    """Fetch ``src.commit`` from ``src.url`` into a temporary repository (no checkout), extract it into ``dest`` and
    remove the repository. The archive can be large: the fetch is the whole tree at that commit."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _git("init", "--quiet", cwd=repo)
        log.info("  fetching %s at %s (this can take several minutes)", src.url, src.commit[:12])
        _git("fetch", "--quiet", "--depth", "1", "--no-tags", src.url, src.commit, cwd=repo)
        counts = extract(repo, src, dest)
    return {"url": src.url, "commit": src.commit, "period": [d.isoformat() for d in src.period], **counts}
