"""A screening of the area around a case's street (``results/screening.md``): where else the same problems are.

It turns the area tables the run already wrote into two ranked lists a resident or an association can act on: the
streets with buses where parking on both sides leaves too little room for them (``area_streets.csv``), and the
streets whose sidewalks are narrower than the accessibility law admits (``area_sidewalks.csv``). Nothing is computed
here. The screening says where to look; a claim about a street needs that street's own case, and the report ends with
the commands that make one.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from .config import standards_catalogue
from .i18n import length, num, t
from .new_case import AREA_MARGIN_M

if TYPE_CHECKING:
    from .pipeline import Run

MAX_ROWS = 30


def _cell(x: Any) -> str:
    return str(x).replace("|", "/")


def markdown(r: Run) -> str | None:
    cfg, lang = r.cfg, r.case.lang
    a = cfg.area_scan
    if a is None or cfg.transit is None:
        return None

    def say(key: str, **kw: Any) -> str:
        return t(f"screening.{key}", lang, **kw)

    def n(x: float, d: int = 2) -> str:
        return num(float(x), lang, d)

    out = [
        "# " + say("title", street=cfg.street.name),
        "",
        say("intro", km=n(AREA_MARGIN_M / 1000, 1)),
        "",
        "## " + say("buses"),
        "",
        say("buses_intro", thr=n(a.threshold_m, 1), minm=f"{a.min_pattern_m:g}"),
        "",
    ]
    area = r.table("area_streets")
    hit = area[area.metres_with_pattern >= a.min_pattern_m]
    if len(hit):
        out += [say("buses_head"), "| --- | ---: | --- | --- | --- | ---: | ---: |"]
        for x in hit.head(MAX_ROWS).itertuples():
            both = say("yes") if x.buses_both_directions else say("no")
            traffic = t(f"traffic.{x.traffic}", lang) if isinstance(x.traffic, str) and x.traffic else "—"
            out.append(
                f"| {_cell(x.street)} | {x.buses_per_day} | {_cell(x.routes)} | {both} | {traffic} | "
                f"{n(x.free_width_median_m)} | {x.metres_with_pattern} |"
            )
    else:
        out.append(say("buses_none"))
    out.append("")
    sw = cfg.sidewalks
    if a.sidewalks and sw:
        free = standards_catalogue().reference(sw.free_path)[0].value_m
        out += ["## " + say("sidewalks"), "", say("sidewalks_intro", free=n(free)), ""]
        side = r.table("area_sidewalks")
        listed = side[(side.metres_below > 0) | (side.metres_open_below > 0)]
        if len(listed):
            out += [say("sidewalks_head"), "| --- | ---: | ---: | ---: | ---: | --- |"]
            for x in listed.head(MAX_ROWS).itertuples():
                where = f"{x.worst_lat:.6f}, {x.worst_lon:.6f}" if not math.isnan(x.worst_lat) else "—"
                narrowest = n(x.narrowest_m) if not math.isnan(x.narrowest_m) else "—"
                out.append(
                    f"| {_cell(x.street)} | {length(x.metres_below, lang)} | {length(x.metres_below_with_accuracy, lang)} | "
                    f"{narrowest} | {length(x.metres_open_below, lang)} | {where} |"
                )
            if len(listed) > MAX_ROWS:
                out.append(f"| … (+{len(listed) - MAX_ROWS}) | | | | | |")
        else:
            out.append(say("sidewalks_none"))
        out.append("")
    like = r.case.root.relative_to(Path.cwd()) if r.case.root.is_relative_to(Path.cwd()) else r.case.root
    example = next(iter(hit.street), None) if len(hit) else None
    if a.sidewalks and sw:
        side = r.table("area_sidewalks")
        example = example or next(iter(side[side.metres_below > 0].street), None)
    out += ["## " + say("next"), "", say("next_body"), "", "```bash"]
    out += [
        f'mobilidados new-case "{example or "…"}" --like {like}',
        "mobilidados fetch cases/<…>",
        "mobilidados run cases/<…>",
        "mobilidados draft cases/<…> --topic buses      # --topic sidewalks",
        "```",
        "",
    ]
    return "\n".join(out)


def write(r: Run) -> None:
    text = markdown(r)
    path = r.case.results_dir / "screening.md"
    if text is None:
        path.unlink(missing_ok=True)
        return
    path.write_text(text, encoding="utf-8")


def summary_rows(r: Run) -> pd.DataFrame:
    """The streets the screening lists, for the command line: street, topic, metres."""
    rows = []
    a = r.cfg.area_scan
    if a:
        area = r.table("area_streets")
        rows += [(x.street, "buses", float(x.metres_with_pattern)) for x in area[area.metres_with_pattern >= a.min_pattern_m].itertuples()]
        if a.sidewalks and r.cfg.sidewalks:
            side = r.table("area_sidewalks")
            rows += [(x.street, "sidewalks", float(x.metres_below)) for x in side[side.metres_below > 0].itertuples()]
    return pd.DataFrame(rows, columns=["street", "topic", "metres"])
