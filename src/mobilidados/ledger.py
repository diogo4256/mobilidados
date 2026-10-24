"""The findings ledger: every statement the case can make, with its evidence grade, sources and caveats.

Grades (docs/evidence-standard.md): M measured from official data · D official document text · I inference
from M/D/P · P assumption · NE not found / not verified (which is not the same as "does not exist").

The ledger is generated from the result tables, so a statement can never drift from its number. Letters and
reports should quote the ledger, and ``mobilidados check-claims`` verifies drafts against it.
"""

from __future__ import annotations

import json
import math
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from .config import AnySource, Case, Grade, HttpFiles, standards_catalogue
from .direction import directions
from .envelope import widths
from .geometry import MIN_STRIP_M, TWO_STRIPS
from .gtfs import ALL_TRIPS
from .i18n import num, t
from .provenance import Lock

if TYPE_CHECKING:
    from .pipeline import Run


def range_count(values: list[int]) -> float:
    """The count that picks the plural form of the range ``min–max`` printed for ``values`` (sorted, distinct)."""
    return values[0] if len(values) == 1 else math.inf  # a range of different numbers is plural


def sentences(*parts: str) -> str:
    """A caveat made of several sentences; empty parts (a note the city profile does not give) are left out."""
    return " ".join(p for p in parts if p)


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

    def method(key: str, **kw: Any) -> str:
        return t(f"method.{key}", lang, **kw)

    def caveat(key: str, **kw: Any) -> str:
        return t(f"caveat.{key}", lang, **kw)

    def n(x: Any, d: int = 2, sign: bool = False) -> str:
        return num(float(x), lang, d, sign)

    def param(x: float) -> str:
        """A parameter as it is set, without trailing zeros (``0.5``, ``3``)."""
        return f"{x:g}".replace(".", ",") if lang == "pt" else f"{x:g}"

    survey, accuracy = cfg.cartography.text("survey", lang), cfg.cartography.text("accuracy_note", lang)
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
            method=method("length"),
        )
    )

    if cfg.direction and cfg.network:
        edges = r.table("traffic_direction_edges")
        traffic = directions(edges, cfg.network.open_value)
        points = edges.s_m.nunique()
        two_way_at = sum(directions(g, cfg.network.open_value) == "two-way" for _, g in edges.groupby("s_m"))
        F.append(
            Finding(
                id="traffic",
                grade="M",
                statement=say("traffic", count=points, traffic=t(f"traffic.{traffic}", lang), k=two_way_at, n=points),
                values={"traffic": traffic},
                sources=[cfg.direction.source],
                method=method("traffic"),
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
    # the free width counts the stations with parking on both sides and a narrow free width (geometry.classify): say
    # how many stations with parking on both sides that leaves out for being wider
    profiles = r.table("profiles")
    both_sides = (profiles.strip_L > MIN_STRIP_M) & (profiles.strip_R > MIN_STRIP_M)
    left_out = int((both_sides & (profiles["class"] != TWO_STRIPS)).sum())
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
            method=method("free_width", step=param(cfg.profiles.step_m)),
            caveat=sentences(
                caveat("free_filter", count=left_out, max=n(cfg.profiles.narrow_max_m), k=left_out, n=int(both_sides.sum())),
                caveat("survey", survey=survey) if survey else "",
                accuracy,
            ),
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
            method=method("parking_strips"),
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
                    scheduled=say("routes_scheduled", count=len(tr.routes), routes=", ".join(tr.routes)),
                    day=tr.service_date,
                    trips_up=say("trips", count=trips["trips_up"], n=trips["trips_up"], heading=up),
                    trips_down=say("trips", count=trips["trips_down"], n=trips["trips_down"], heading=down),
                    max_up=trips["max_up_per_hour"],
                    max_down=trips["max_down_per_hour"],
                ),
                values=trips | {"service_date": str(tr.service_date)},
                sources=[tr.source],
                method=method("transit"),
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
                    method=method("runtimes"),
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
        wb = r.table("width_budget")  # the bus x bus margin, bodies only, at each free width it was computed for
        spread = wb[(wb.scenario == f"{e.bus} x {e.bus}") & ~wb.mirrors].set_index("free_width_ref").margin_m
        two = profiles[profiles["class"] == TWO_STRIPS]
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
                method=method("width_budget"),
                caveat=sentences(
                    caveat("budget_inside"),
                    caveat(
                        "budget_spread",
                        fmin=n(spread["min"], sign=True),
                        fmed=n(spread["median"], sign=True),
                        fp95=n(spread["p95"], sign=True),
                    )
                    if len(spread)
                    else "",
                    caveat("budget_share", pct=round(100 * float((two.free_width < bb).mean())), bb=n(bb)),
                    caveat("mirrors_clear" if bus.mirrors_clear_cars and car.category == "car" else "mirrors_all"),
                    accuracy,
                ),
            )
        )
        wp = r.table("without_parking").set_index("without")
        one_side = float(wp.loc[["L", "R"], "free_median"].min())
        F.append(
            Finding(
                id="without_parking",
                grade="I",
                statement=say(
                    "without_parking",
                    side_l=sides["L"],
                    lmin=n(wp.loc["L", "free_min"]),
                    lmax=n(wp.loc["L", "free_max"]),
                    lmed=n(wp.loc["L", "free_median"]),
                    side_r=sides["R"],
                    rmin=n(wp.loc["R", "free_min"]),
                    rmax=n(wp.loc["R", "free_max"]),
                    rmed=n(wp.loc["R", "free_median"]),
                    bmed=n(wp.loc["both", "free_median"]),
                    bb=n(bb),
                    bbm=n(bbm),
                    m1=n(one_side - bb, sign=True),
                    m1m=n(one_side - bbm, sign=True),
                ),
                values={f"without_{side}_median_m": float(wp.loc[side, "free_median"]) for side in ("L", "R", "both")}
                | {"bus_bus_margin_one_side_m": round(one_side - bb, 2), "bus_bus_margin_one_side_mirrors_m": round(one_side - bbm, 2)},
                sources=["free_width", "parking_strips", f"vehicle_{e.bus}_body", f"vehicle_{e.bus}_mirrors"],
                method=method("without_parking"),
                caveat=caveat("without_parking"),
            )
        )
        one, both = wp.loc["L"], wp.loc["both"]
        spaces = cfg.profiles.parking_space_m
        whole = r.table("parking_strip_lengths").set_index("block").loc["all"]

        def places(row: Any) -> str:
            lo, hi = int(row.places_min), int(row.places_max)
            return say("places", count=hi, n=hi) if lo == hi else say("places_range", lo=lo, hi=hi)

        F.append(
            Finding(
                id="parking_removed",
                grade="I",
                statement=say(
                    "parking_removed",
                    m=n(one.parking_removed_m, 0),
                    places=places(one),
                    m2=n(both.parking_removed_m, 0),
                    places2=places(both),
                    space=n(min(spaces)) if len(set(spaces)) == 1 else f"{n(min(spaces))}–{n(max(spaces))}",
                    wl=n(whole.strip_L_length_m, 1),
                    wr=n(whole.strip_R_length_m, 1),
                    side_l=sides["L"],
                    side_r=sides["R"],
                ),
                values={
                    "removed_one_side_m": float(one.parking_removed_m),
                    "places_one_side": [int(one.places_min), int(one.places_max)],
                    "removed_both_sides_m": float(both.parking_removed_m),
                    "places_both_sides": [int(both.places_min), int(both.places_max)],
                    "parking_space_m": list(spaces),
                    "whole_street_parking_m": {"left": float(whole.strip_L_length_m), "right": float(whole.strip_R_length_m)},
                },
                sources=["free_width", "parking_strips"],
                method=method("parking_removed"),
                caveat=caveat("parking_removed"),
            )
        )

    if tr:
        es, ed = r.table("encounters_summary"), r.table("encounters_detail")
        assumed, schedule = es[es.basis == "assumed"], es[es.basis == "schedule"]
        counts = sorted({int(x) for x in assumed.encounters_per_day})
        in_narrow = sorted({int(x) for x in ed.groupby("speed_kmh").in_narrow_section.sum()})
        check = (
            caveat(
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
                    day=tr.service_date,
                    meetings=say("meetings", count=range_count(counts), n="–".join(map(str, counts))),
                    speeds="/".join(f"{v:g}" for v in assumed.speed_kmh),
                    narrow=say("meetings_narrow", count=range_count(in_narrow), n="–".join(map(str, in_narrow))),
                ),
                values={"per_day": counts, "in_narrow_sections": in_narrow},
                sources=["transit", "free_width"],
                method=method("encounters"),
                caveat=sentences(caveat("encounters_model"), check),
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
                        attributed=say("reports_attributed", count=int(row[f"{fname}_n"]), n=int(row[f"{fname}_n"]), flt=frx.lstrip("^")),
                        period=f"{dated.first_date.min()} – {dated.last_date.max()}",
                        d=f"{o.max_dist_m:g}",
                        rate=n(row[f"{fname}_per_100m"]),
                        ranking=say("street_rank", count=len(occ), rank=rank, total=len(occ), minlen=f"{o.min_street_length_m:g}"),
                    ),
                    values={"n": int(row[f"{fname}_n"]), "per_100m": float(row[f"{fname}_per_100m"]), "rank": rank, "of": len(occ)},
                    sources=[o.source],
                    method=method("occurrences"),
                    # the rate divides the reports inside the window by each street's whole length (the bias is stated, not
                    # corrected: the raw records are needed to recount streets that leave the window)
                    caveat=caveat("occurrences", w=param(o.window_m)),
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
                        streets=say("area_streets", count=len(area), n=len(area)),
                        pattern=say(
                            "area_pattern",
                            count=len(k),
                            n=len(k),
                            thr=n(a.threshold_m, 1),
                            minm=f"{a.min_pattern_m:g}",
                            names=and_.join(k.street),
                        ),
                        nb=len(both),
                        names2=and_.join(both.street) or "—",
                    ),
                    values={"two_way_streets": k.street.tolist(), "with_buses_both_directions": both.street.tolist()},
                    sources=[a.cartography, a.axes, a.identify_source or "", tr.source],
                    method=method("area_pattern", step=param(a.step_m)),
                    caveat=caveat("area_pattern", thr=n(a.threshold_m, 1), minm=param(a.min_pattern_m)),
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
        origin = f"<{urls[0]}>" if len(urls) == 1 else say("files", count=len(urls), n=len(urls), example=f"<{urls[0]}>") if urls else ""
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
