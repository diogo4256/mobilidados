"""Command-line interface: ``streetfit <command> ...``"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Case


def _agents(name: str):
    try:
        import importlib

        return importlib.import_module(f"streetfit.agents.{name}")
    except ImportError as e:  # pragma: no cover - depends on optional extras
        if "anthropic" in str(e) or "pydantic" in str(e) or "pypdf" in str(e):
            sys.exit("This command needs the optional extras: pip install 'streetfit[agents]'")
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="streetfit", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch", help="download a case's sources into data/raw and update sources.lock.json")
    p.add_argument("case")
    p.add_argument("--only", nargs="*", help="source ids")
    p.add_argument("--refresh", action="store_true", help="re-download even if cached")
    p.add_argument("--from-dir", type=Path, help="copy sources from a local snapshot instead of downloading")

    p = sub.add_parser("run", help="run the analysis and write results/")
    p.add_argument("case")
    p.add_argument("--stages", nargs="*", help="subset of stages (default: all)")
    p.add_argument("--offline", action="store_true", help="never call web services (cached data only)")

    p = sub.add_parser("verify", help="check cached sources against sources.lock.json")
    p.add_argument("case")

    p = sub.add_parser("snapshot", help="copy the redistributable cached sources into a folder for archiving")
    p.add_argument("case")
    p.add_argument("out", type=Path)

    p = sub.add_parser("lint", help="flag generalisations, hedges and quotes in a draft letter (no AI)")
    p.add_argument("draft", type=Path)
    p.add_argument("--lang", default="pt")

    p = sub.add_parser("check-claims", help="AI fact-check of a draft against the case ledger and source texts")
    p.add_argument("case")
    p.add_argument("draft", type=Path)
    p.add_argument("--corpus", type=Path, nargs="*", default=[], help="extra source texts (.txt/.md/.pdf)")
    p.add_argument("--out", type=Path)

    p = sub.add_parser("extract-standard", help="AI + OCR extraction of width values from PDF pages")
    p.add_argument("pdf", type=Path)
    p.add_argument("--pages", required=True, help="1-based PDF page numbers, e.g. 194,198")
    p.add_argument("--out", type=Path)

    p = sub.add_parser("discover", help="AI agent that proposes a city profile from a GIS/open-data portal")
    p.add_argument("--city", required=True)
    p.add_argument("--start", nargs="+", required=True, help="start URLs (ArcGIS services directory, CKAN/udata API)")
    p.add_argument("--hosts", nargs="*", help="allowed hosts (default: the start URLs' hosts)")
    p.add_argument("--bbox", help="lon_min,lat_min,lon_max,lat_max of a test area")
    p.add_argument("--out", type=Path)

    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        from .sources import fetch

        fetch(Case.load(a.case), only=a.only, refresh=a.refresh, from_dir=a.from_dir)
    elif a.cmd == "run":
        from .pipeline import run

        run(Case.load(a.case), stages=a.stages, offline=a.offline)
    elif a.cmd == "verify":
        from .provenance import Lock

        case = Case.load(a.case)
        rows = Lock(case.lock_path).verify(case.raw_dir)
        bad = [r for r in rows if r[2] != "ok"]
        for sid, f, status in rows:
            if status != "ok" or len(rows) < 40:
                print(f"{status:8s} {sid:24s} {f}")
        print(f"{len(rows) - len(bad)}/{len(rows)} files match the lock")
        return 1 if bad else 0
    elif a.cmd == "snapshot":
        from .sources import snapshot

        snapshot(Case.load(a.case), a.out)
    elif a.cmd == "lint":
        from .lint import lint_text

        issues = lint_text(a.draft.read_text(encoding="utf-8"), a.lang)
        for i in issues:
            print(f"{i.line}:{i.col}  {i.rule:14s} {i.message}\n      {i.excerpt}")
        print(f"{len(issues)} issue(s)")
        return 1 if issues else 0
    elif a.cmd == "check-claims":
        return _agents("claim_checker").main(Case.load(a.case), a.draft, a.corpus, a.out)
    elif a.cmd == "extract-standard":
        return _agents("standards_extractor").main(a.pdf, [int(x) for x in a.pages.split(",")], a.out)
    elif a.cmd == "discover":
        return _agents("source_discovery").main(a.city, a.start, a.hosts, a.bbox, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
