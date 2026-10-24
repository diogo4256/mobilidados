"""Command-line interface: ``mobilidados <command> ...``"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType

from .config import Case, MobilidadosError


def _agents(name: str) -> ModuleType:
    try:
        return importlib.import_module(f"mobilidados.agents.{name}")
    except ImportError as e:  # pragma: no cover - depends on optional extras
        if e.name in {"anthropic", "pypdf", "pypdfium2"}:
            raise MobilidadosError("this command needs the optional extras: pip install 'mobilidados[agents]'") from e
        raise


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mobilidados", description=__doc__)
    ap.add_argument("-v", "--verbose", action="store_true", help="show debug messages")
    ap.add_argument("-q", "--quiet", action="store_true", help="show warnings and errors only")
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
    p.add_argument("--pages", required=True, help="comma-separated PDF page numbers, counted from 1")
    p.add_argument("--out", type=Path)

    p = sub.add_parser("new-case", help="draft a case for another street from an existing case of the same city")
    p.add_argument("street", help="the street's name as in the city's axes layer, e.g. 'Rua Teixeira de Pascoais'")
    p.add_argument("--like", type=Path, required=True, help="an existing case of the same city to copy the rest from")
    p.add_argument("--out", type=Path, help="case directory (default: next to --like, named <city>-<street>)")

    p = sub.add_parser("discover", help="AI agent that proposes a city profile from a GIS/open-data portal")
    p.add_argument("--city", required=True)
    p.add_argument("--start", nargs="+", required=True, help="start URLs (ArcGIS services directory, CKAN/udata API)")
    p.add_argument("--hosts", nargs="*", help="allowed hosts (default: the start URLs' hosts)")
    p.add_argument("--bbox", help="lon_min,lat_min,lon_max,lat_max of a test area")
    p.add_argument("--out", type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.WARNING if a.quiet else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s" if a.verbose else "%(message)s",
    )
    try:
        return _dispatch(a)
    except MobilidadosError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _dispatch(a: argparse.Namespace) -> int:
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
        for sid, f, status in bad:
            print(f"{status:8s} {sid:24s} {f}")
        print(f"{len(rows) - len(bad)}/{len(rows)} files match the lock")
        return 1 if bad else 0
    elif a.cmd == "new-case":
        from .new_case import write

        out = write(Case.load(a.like), a.street, a.out)
        print(f"wrote {out / 'case.toml'}: check the points listed at its top, then\n  mobilidados fetch {out}\n  mobilidados run {out}")
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
        return int(_agents("claim_checker").main(Case.load(a.case), a.draft, a.corpus, a.out))
    elif a.cmd == "extract-standard":
        return int(_agents("standards_extractor").main(a.pdf, [int(x) for x in a.pages.split(",")], a.out))
    elif a.cmd == "discover":
        return int(_agents("source_discovery").main(a.city, a.start, a.hosts, a.bbox, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
