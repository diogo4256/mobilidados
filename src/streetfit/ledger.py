"""The findings ledger: every statement the case can make, with its evidence grade, sources and caveats.

Grades (docs/evidence-standard.md): M measured from official data · D official document text · I inference
from M/D/P · P assumption · NE not found / not verified (which is not the same as "does not exist").

The ledger is generated from the result tables, so a statement can never drift from its number. Letters and
reports should quote the ledger, and ``streetfit check-claims`` verifies drafts against it.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from .config import AnySource, Case, Grade, HttpFiles, standards_catalogue
from .direction import directions
from .envelope import widths
from .gtfs import ALL_TRIPS
from .i18n import num, t
from .provenance import Lock

if TYPE_CHECKING:
    from .pipeline import Run


class Finding(BaseModel):
    id: str
    grade: Grade
    statement: str
    values: dict[str, Any] = {}
    sources: list[str] = []
    method: str = ""
    caveat: str = ""


def build(r: Run) -> list[Finding]:
    cfg, lang = r.cfg, r.case.lang

    def say(key: str, **kw: Any) -> str:
        return t(f"ledger.{key}", lang, **kw)

    def n(x: Any, d: int = 2, sign: bool = False) -> str:
        return num(float(x), lang, d, sign)

    F: list[Finding] = []
    allrow = r.table("summary_by_block").set_index("block").loc["all"]
    fmed = float(allrow.free_median)
    length = float(r.table("street").length_m.iloc[0])
    F.append(
        Finding(
            id="length",
            grade="M",
            statement=say("length", length=n(length)),
            values={"length_m": length},
            sources=[cfg.profiles.axes],
            method="Axis polyline length (projected CRS).",
        )
    )

    if cfg.direction and cfg.network:
        edges = r.table("traffic_direction_edges")
        traffic = directions(edges, cfg.network.open_value)
        F.append(
            Finding(
                id="traffic",
                grade="M",
                statement=say("traffic", traffic=t(f"traffic.{traffic}", lang), n=edges.s_m.nunique()),
                values={"traffic": traffic},
                sources=[cfg.direction.source],
                method="Identify on the routing network at stations along the axis.",
            )
        )

    narrow = r.table("narrow_sections")
    metres = round(float((narrow.s_to - narrow.s_from).sum()), 1)
    free = {
        "min_m": allrow.free_min,
        "median_m": allrow.free_median,
        "max_m": allrow.free_max,
        "p5_m": allrow.free_p5,
        "p95_m": allrow.free_p95,
    }
    F.append(
        Finding(
            id="free_width",
            grade="M",
            statement=say(
                "free",
                metres=n(metres, 0 if metres.is_integer() else 1),
                fmin=n(allrow.free_min),
                fmax=n(allrow.free_max),
                fmed=n(allrow.free_median),
            ),
            values={k: float(v) for k, v in free.items()} | {"metres_two_strips": metres},
            sources=[cfg.profiles.cartography, cfg.profiles.axes],
            method=f"Transects every {cfg.profiles.step_m:g} m, widths read from mapped polygons only.",
            caveat=cfg.cartography.accuracy_note,
        )
    )
    sides = cfg.street.sides
    F.append(
        Finding(
            id="parking_strips",
            grade="M",
            statement=say("strips", sl=n(allrow.strip_L_median), sr=n(allrow.strip_R_median), side_l=sides["L"], side_r=sides["R"]),
            values={"left_m": float(allrow.strip_L_median), "right_m": float(allrow.strip_R_median)},
            sources=[cfg.profiles.cartography],
            method="Mapped area, not parked vehicles.",
        )
    )

    tr = cfg.transit
    if tr:
        tph = r.table("trips_per_hour").set_index("hour")
        up, down = cfg.street.heading_label(1), cfg.street.heading_label(-1)
        trips = {
            "trips_up": int(tph[up].sum()),
            "trips_down": int(tph[down].sum()),
            "max_up_per_hour": int(tph[up].max()),
            "max_down_per_hour": int(tph[down].max()),
        }
        F.append(
            Finding(
                id="transit",
                grade="M",
                statement=say(
                    "routes",
                    routes=", ".join(tr.routes),
                    day=tr.service_date,
                    n_up=trips["trips_up"],
                    n_down=trips["trips_down"],
                    up=up,
                    down=down,
                    max_up=trips["max_up_per_hour"],
                    max_down=trips["max_down_per_hour"],
                ),
                values=trips | {"service_date": str(tr.service_date)},
                sources=[tr.source],
                method="Trips counted at a reference stop per direction; timetable, not observed operation.",
            )
        )
        for ref, g in r.table("scheduled_runtimes").groupby("ref_stop", sort=True):
            whole, day = g[g.scope == ALL_TRIPS].iloc[0], g[g.scope != ALL_TRIPS].iloc[0]
            F.append(
                Finding(
                    id=f"runtime_{ref}",
                    grade="M",
                    statement=say(
                        "runtimes",
                        a=ref,
                        b=f"{whole.next_stop} {whole.next_stop_name}",
                        d=int(whole.dist_straight_m),
                        m_all=f"{whole.median_s:g}",
                        k_all=n(whole.kmh_at_median_min, 1),
                        m_day=f"{day.median_s:g}",
                        k_day=n(day.kmh_at_median_min, 1),
                        day=tr.service_date,
                    ),
                    values={
                        "dist_straight_m": int(whole.dist_straight_m),
                        "median_s_all": float(whole.median_s),
                        "median_s_day": float(day.median_s),
                    },
                    sources=[tr.source],
                    method="Arrival at the next stop minus departure from the reference stop; straight-line distance between stops.",
                )
            )

    e = cfg.envelope
    if e:
        vehicles = cfg.all_vehicles()
        for vid in dict.fromkeys([e.bus, e.car]):
            v = vehicles[vid]
            F.append(
                Finding(
                    id=f"vehicle_{vid}_body",
                    grade=v.grade_body,
                    statement=say("vehicle_body", label=v.text("label", lang), w=n(v.width_body_m), src=v.text("source_body", lang)),
                    values={"width_m": v.width_body_m},
                    sources=[v.source_body],
                )
            )
            F.append(
                Finding(
                    id=f"vehicle_{vid}_mirrors",
                    grade=v.grade_mirrors,
                    statement=say(
                        "vehicle_mirrors", label=v.text("label", lang), w=n(v.width_mirrors_m), src=v.text("source_mirrors", lang)
                    ),
                    values={"width_m": v.width_mirrors_m},
                    sources=[v.source_mirrors],
                )
            )
        bus, car = vehicles[e.bus], vehicles[e.car]
        bb, bbm, bc, bcm = widths(bus, bus, False), widths(bus, bus, True), widths(bus, car, False), widths(bus, car, True)
        F.append(
            Finding(
                id="width_budget",
                grade="I",
                statement=say(
                    "budget",
                    bb=n(bb),
                    bbm=n(bbm),
                    fmed=n(fmed),
                    mbb=n(fmed - bb, sign=True),
                    bc=n(bc),
                    mbc=n(fmed - bc, sign=True),
                    mbcm=n(fmed - bcm, sign=True),
                ),
                values={
                    "bus_bus_margin_m": round(fmed - bb, 2),
                    "bus_bus_margin_mirrors_m": round(fmed - bbm, 2),
                    "bus_car_margin_m": round(fmed - bc, 2),
                    "bus_car_margin_mirrors_m": round(fmed - bcm, 2),
                },
                sources=["free_width", f"vehicle_{e.bus}_body", f"vehicle_{e.bus}_mirrors", f"vehicle_{e.car}_body"],
                method="Static envelope (sum of widths), not a swept-path simulation.",
                caveat="Assumes parked vehicles stay inside the mapped strips; see overhang_sensitivity.csv.",
            )
        )

    if tr:
        es, ed = r.table("encounters_summary"), r.table("encounters_detail")
        assumed, schedule = es[es.basis == "assumed"], es[es.basis == "schedule"]
        counts = sorted({int(x) for x in assumed.encounters_per_day})
        in_narrow = sorted({int(x) for x in ed.groupby("speed_kmh").in_narrow_section.sum()})
        check = (
            say(
                "encounters_check",
                kmh=n(schedule.speed_kmh.iloc[0], 1),
                per_day=int(schedule.encounters_per_day.iloc[0]),
                day=tr.service_date,
            )
            if len(schedule)
            else ""
        )
        F.append(
            Finding(
                id="encounters",
                grade="I",
                statement=say(
                    "encounters",
                    nrange="–".join(map(str, counts)),
                    speeds="/".join(f"{v:g}" for v in assumed.speed_kmh),
                    nnarrow="–".join(map(str, in_narrow)),
                ),
                values={"per_day": counts, "in_narrow_sections": in_narrow},
                sources=["transit", "free_width"],
                method="Presence-interval overlap at constant speed from scheduled times; timetable, not observation.",
                caveat=check,
            )
        )

    o = cfg.occurrences
    if o:
        fname, frx = next(iter(o.filters.items()))
        occ = r.table("occurrences_by_street")  # sorted by rate, so a street's rank is its row
        me = occ[occ.street == cfg.street.name]
        if len(me):
            row, rank = me.iloc[0], int(me.index[0]) + 1
            files = r.table("occurrences_files")
            dated = files[files.first_date.notna() & (files.first_date != "")]  # a file without a located record has no dates
            F.append(
                Finding(
                    id="occurrences",
                    grade="M",
                    statement=say(
                        "occurrences",
                        n=int(row[f"{fname}_n"]),
                        flt=frx.lstrip("^"),
                        period=f"{dated.first_date.min()} – {dated.last_date.max()}",
                        d=f"{o.max_dist_m:g}",
                        rate=n(row[f"{fname}_per_100m"]),
                        rank=rank,
                        total=len(occ),
                        minlen=f"{o.min_street_length_m:g}",
                    ),
                    values={"n": int(row[f"{fname}_n"]), "per_100m": float(row[f"{fname}_per_100m"]), "rank": rank, "of": len(occ)},
                    sources=[o.source],
                    method="Nearest-street attribution of geolocated open-data records.",
                    caveat="A report is not a proven infraction; counts are small.",
                )
            )

    a = cfg.area_scan
    if a and tr:
        area = r.table("area_streets")
        # one-way streets need a single lane, so a narrow free width there is a different situation: only two-way
        # streets share the case's pattern
        k = area[(area.metres_with_pattern >= a.min_pattern_m) & (area.traffic == "two-way")]
        both = k[k.buses_both_directions]
        if len(k):
            and_ = t("report.and", lang)
            F.append(
                Finding(
                    id="area_pattern",
                    grade="M",
                    statement=say(
                        "area",
                        total=len(area),
                        k=len(k),
                        thr=n(a.threshold_m, 1),
                        minm=f"{a.min_pattern_m:g}",
                        names=and_.join(k.street),
                        nb=len(both),
                        names2=and_.join(both.street) or "—",
                    ),
                    values={"two_way_streets": k.street.tolist(), "with_buses_both_directions": both.street.tolist()},
                    sources=[a.cartography, a.axes, a.identify_source or "", tr.source],
                    method=f"Stations every {a.step_m:g} m on every street axis with buses; same width method as the case street; "
                    "traffic direction from the routing network at one station per street.",
                )
            )

    for rid in cfg.standards.compare:
        ref, doc = standards_catalogue().reference(rid)
        F.append(
            Finding(
                id=f"standard_{rid}",
                grade="D",
                statement=say(
                    "standard",
                    doc=doc.title,
                    page=ref.page,
                    kind=t(f"kind.{ref.kind}", lang),
                    label=ref.text("label", lang),
                    value=n(ref.value_m),
                    scope=ref.text("scope", lang),
                    fmed=n(fmed),
                    diff=n(fmed - ref.value_m, sign=True),
                ),
                values={"value_m": ref.value_m, "difference_m": round(fmed - ref.value_m, 2)},
                sources=[rid],
                caveat=ref.text("derivation", lang),
            )
        )

    F += [Finding(id=f"gap_{i}", grade="NE", statement=gap[lang]) for i, gap in enumerate(cfg.known_gaps, 1)]
    return F


def write(r: Run) -> None:
    findings, case = build(r), r.case
    lock = Lock(case.lock_path)
    out = {
        "case": case.config.case.model_dump(mode="json"),
        "findings": [f.model_dump(mode="json") for f in findings],
        "sources": lock.entries,
    }
    (case.results_dir / "findings.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (case.results_dir / "findings.md").write_text(markdown(case, findings, lock), encoding="utf-8")


def markdown(case: Case, findings: list[Finding], lock: Lock) -> str:
    def say(key: str, **kw: Any) -> str:
        return t(f"report.{key}", case.lang, **kw)

    info = case.config.case
    head = ["# " + info.title, "", f"> {info.question}", "", say("intro"), ""]
    body = []
    for f in findings:
        line = f"- **[{f.grade}]** {f.statement}"
        extra = [x for x in (f.method, f.caveat) if x]
        if extra:
            line += f"  \n  <sub>{' · '.join(extra)}</sub>"
        body.append(line)
    src = [
        "",
        "## " + say("sources"),
        "",
        f"| id | {say('origin')} | {say('retrieved')} | {say('licence')} | sha256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    # the lock says what was retrieved and when; the configuration says from where
    for sid, e in sorted(lock.entries.items()):
        source = case.config.sources.get(sid)
        urls = _urls(source) if source else []
        origin = f"<{urls[0]}>" if len(urls) == 1 else say("files", n=len(urls), example=f"<{urls[0]}>") if urls else ""
        files = sorted(e.get("files", {}).items())
        shas = "<br>".join(f"`{m['sha256'][:12]}…` {p}" for p, m in files[:3]) + (f"<br>+{len(files) - 3}" if len(files) > 3 else "")
        licence = source.licence if source else e.get("licence", "")
        src.append(f"| {sid} | {origin} | {e.get('retrieved_utc', '')[:10]} | {licence} | {shas} |")
    return "\n".join(head + body + src + attribution(case)) + "\n"


def _urls(source: AnySource) -> list[str]:
    return [f.url for f in source.files] if isinstance(source, HttpFiles) else [source.url]


def attribution(case: Case) -> list[str]:
    """Attribution and modification notice for openly licensed inputs (as CC BY 4.0, section 3(a), requires)."""
    seen, lines = set(), []
    for src in case.config.sources.values():
        if not src.licence_url or (src.attribution, src.dataset_page) in seen:
            continue
        seen.add((src.attribution, src.dataset_page))
        lines.append(f"- {src.attribution}, <{src.dataset_page or _urls(src)[0]}>, {src.licence} (<{src.licence_url}>).")
    if not lines:
        return []
    return ["", "## " + t("report.attribution", case.lang), "", *lines, "", t("report.transformed", case.lang)]
