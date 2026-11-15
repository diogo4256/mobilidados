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

import numpy as np
from pydantic import BaseModel

from .config import AnySource, Case, GitArchive, Grade, HttpFiles, standards_catalogue
from .direction import directions
from .envelope import widths
from .geometry import MIN_STRIP_M, TWO_STRIPS
from .gtfs import ALL_TRIPS
from .i18n import length as street_length
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

    def seconds(x: float) -> str:
        """A median of whole seconds: whole, or halfway between two."""
        return n(x, 0 if float(x).is_integer() else 1)

    def length_m(x: float) -> str:
        return street_length(x, lang)

    def param(x: float) -> str:
        """A parameter as it is set, without trailing zeros (``0.5``, ``3``)."""
        return f"{x:g}".replace(".", ",") if lang == "pt" else f"{x:g}"

    survey, accuracy = cfg.cartography.text("survey", lang), cfg.cartography.text("accuracy_note", lang)
    F: list[Finding] = []
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
        points = len(cfg.direction.stations_s)  # a station where the identify found no edge is checked all the same
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

    # the free width counts the stations with parking on both sides and a narrow free width (geometry.classify): say
    # how many stations with parking on both sides that leaves out for being wider
    profiles = r.table("profiles")
    both_sides = (profiles.strip_L > MIN_STRIP_M) & (profiles.strip_R > MIN_STRIP_M)
    left_out = int((both_sides & (profiles["class"] != TWO_STRIPS)).sum())
    free_filter = caveat("free_filter", count=left_out, max=n(cfg.profiles.narrow_max_m), k=left_out, n=int(both_sides.sum()))
    free_method = method("free_width", step=param(cfg.profiles.step_m))
    survey_note = caveat("survey", survey=survey) if survey else ""
    sides = cfg.street.sides
    if r.two_strips:
        allrow = r.table("summary_by_block").set_index("block").loc["all"]
        fmed = float(allrow.free_median)
        metres = r.two_strips_m
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
                    metres=length_m(metres),
                    fmin=n(allrow.free_min),
                    fmax=n(allrow.free_max),
                    fmed=n(allrow.free_median),
                ),
                values={k: float(v) for k, v in free.items()} | {"metres_two_strips": metres},
                sources=[cfg.profiles.cartography, cfg.profiles.axes],
                method=free_method,
                caveat=sentences(free_filter, survey_note, accuracy),
            )
        )
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
    else:  # nothing to measure between parking strips, so the width budget and the design references do not apply
        F.append(
            Finding(
                id="free_width",
                grade="M",
                statement=say("free_none"),
                values={"metres_two_strips": 0.0},
                sources=[cfg.profiles.cartography, cfg.profiles.axes],
                method=free_method,
                caveat=sentences(free_filter if left_out else "", survey_note, accuracy),
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
        scheduled = say("routes_scheduled", count=len(tr.routes), routes=", ".join(tr.routes))
        # buses in one direction only: name the direction without trips instead of printing 0 trips and 0 per hour
        one_way = (up, "up") if trips["trips_down"] == 0 else (down, "down") if trips["trips_up"] == 0 else None
        if one_way is None:
            routes_statement = say(
                "routes",
                scheduled=scheduled,
                day=tr.service_date,
                trips_up=say("trips", count=trips["trips_up"], n=trips["trips_up"], heading=up),
                trips_down=say("trips", count=trips["trips_down"], n=trips["trips_down"], heading=down),
                max_up=trips["max_up_per_hour"],
                max_down=trips["max_down_per_hour"],
            )
        else:
            heading, key = one_way
            count = trips[f"trips_{key}"]
            routes_statement = say(
                "routes_one_way",
                scheduled=scheduled,
                day=tr.service_date,
                trips=say("trips", count=count, n=count, heading=heading),
                none=down if key == "up" else up,
                max=trips[f"max_{key}_per_hour"],
            )
        F.append(
            Finding(
                id="transit",
                grade="M",
                statement=routes_statement,
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
                        m_all=seconds(whole.median_s),
                        k_all=n(whole.kmh_at_median_min, 1),
                        m_day=seconds(day.median_s),
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
    if e and r.two_strips:
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
                sources=[
                    "free_width",
                    f"vehicle_{e.bus}_body",
                    f"vehicle_{e.bus}_mirrors",
                    f"vehicle_{e.car}_body",
                    f"vehicle_{e.car}_mirrors",
                ],
                method=method("width_budget"),
                caveat=sentences(
                    overhang(r.table("overhang_sensitivity"), f"{e.bus} x {e.bus}", caveat, n, lang),
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
        acc = cfg.cartography.edge_accuracy_m
        if acc:
            widest = fmed + 2 * acc  # every mapped edge off by the stated accuracy, in the street's favour
            ref = next((standards_catalogue().reference(x) for x in cfg.standards.compare), None)
            refs = [ref] if ref and ref[0].kind == "reference_profile" else []
            F.append(
                Finding(
                    id="width_accuracy",
                    grade="I",
                    statement=say(
                        "width_accuracy_short" if widest < bbm else "width_accuracy_fits",
                        acc=n(acc),
                        fw=n(widest),
                        bbm=n(bbm),
                        gap=n(bbm - widest),
                        mbb=n(fmed - bb, sign=True),
                    )
                    + "".join(
                        say("width_accuracy_ref", doc=d.title, page=x.page, v=n(x.value_m), d=n(x.value_m - widest)) for x, d in refs
                    ),
                    values={"free_width_with_accuracy_m": round(widest, 2), "edge_accuracy_m": acc},
                    sources=["free_width", "width_budget", *(f"standard_{x.id}" for x, _ in refs)],
                    method=method("width_accuracy"),
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
                    m=length_m(one.parking_removed_m),
                    places=places(one),
                    m2=length_m(both.parking_removed_m),
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
        # every assumed speed counts, also one at which no meeting falls in a narrow section (or none happens at all)
        in_narrow = sorted({int(x) for x in ed.groupby("speed_kmh").in_narrow_section.sum().reindex(assumed.speed_kmh, fill_value=0)})
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
        if one_way is None:
            statement = say(
                "encounters",
                day=tr.service_date,
                meetings=say("meetings", count=range_count(counts), n="–".join(map(str, counts))),
                speeds="/".join(f"{v:g}" for v in assumed.speed_kmh),
                narrow=say("meetings_narrow", count=range_count(in_narrow), n="–".join(map(str, in_narrow))),
            )
            pairs = r.table("encounters_by_pair").astype({"pair": str})
            if pairs.pair.nunique() > 1:  # which routes meet, when more than one pair of routes does
                per_pair = {
                    p: sorted({int(x) for x in g.set_index("speed_kmh").encounters_per_day.reindex(assumed.speed_kmh, fill_value=0)})
                    for p, g in pairs.groupby("pair", sort=True)
                }
                statement += say(
                    "encounters_pairs",
                    list="; ".join(f"{p}, {'–'.join(map(str, v))}" for p, v in sorted(per_pair.items(), key=lambda kv: -kv[1][-1])),
                )
            notes = sentences(caveat("encounters_model"), check)
        else:  # no model is needed to say that buses in one direction do not meet head-on, at any speed
            statement, notes = say("encounters_one_way", day=tr.service_date, heading=one_way[0]), ""
        F.append(
            Finding(
                id="encounters",
                grade="I",
                statement=statement,
                values={"per_day": counts, "in_narrow_sections": in_narrow},
                sources=["transit", "free_width"],
                method=method("encounters") if one_way is None else "",
                caveat=notes,
            )
        )

    dl = cfg.delay
    if dl and tr:
        F += delay_findings(r, say, method, caveat, n)

    o = cfg.occurrences
    if o:
        fname, frx = next(iter(o.filters.items()))
        occ = r.table("occurrences_by_street")
        me = occ[occ.street == cfg.street.name]
        if len(me):
            # streets with the same rate share a rank: one more than the streets with a higher rate, whatever their names
            rate = f"{fname}_per_100m"
            row = me.iloc[0]
            rank = int((occ[rate] > row[rate]).sum()) + 1
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

    for rid in cfg.standards.compare if r.two_strips else []:
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

    if cfg.sidewalks:
        F += sidewalk_findings(r, say, method, caveat, n)

    F += [Finding(id=f"gap_{i}", grade="NE", statement=gap[lang]) for i, gap in enumerate(cfg.known_gaps, 1)]
    return F


def sidewalk_findings(r: Run, say: Any, method: Any, caveat: Any, n: Any) -> list[Finding]:
    """The sidewalks (``sidewalks`` and ``area_sidewalks`` stages) against the free path of the accessibility law."""
    cfg, lang = r.cfg, r.case.lang
    sw = cfg.sidewalks
    assert sw is not None
    refs = standards_catalogue()
    free, free_doc = refs.reference(sw.free_path)
    short = sorted((ref for ref, _ in map(refs.reference, sw.short)), key=lambda ref: ref.max_length_m or 0)
    sides: dict[str, str] = {str(k): v for k, v in cfg.street.sides.items()}
    survey, accuracy = cfg.cartography.text("survey", lang), cfg.cartography.text("accuracy_note", lang)
    survey_note = caveat("survey", survey=survey) if survey else ""
    table = r.table("sidewalks").astype({"block": str}).set_index(["side", "block"])

    def length(x: float) -> str:
        return street_length(x, lang)

    def side_text(side: str) -> str:
        row = table.loc[(side, "all")]
        if not row.measured_m:
            return str(say("sidewalks_side_none", side=sides[side]))
        return str(
            say(
                "sidewalks_side",
                side=sides[side],
                med=n(row.width_median_m),
                min=n(row.width_min_m),
                m=length(row.measured_m),
                b=length(row.bounded_m),
            )
        )

    out = [
        Finding(
            id="sidewalks",
            grade="M",
            statement=say("sidewalks", left=side_text("L"), right=side_text("R")),
            values={
                side: {k: float(table.loc[(side, "all"), k]) for k in ("measured_m", "bounded_m", "width_min_m", "width_median_m")}
                for side in ("L", "R")
            },
            sources=[cfg.profiles.cartography, cfg.profiles.axes],
            method=method("sidewalks", step=f"{cfg.profiles.step_m:g}".replace(".", "," if lang == "pt" else "."), j=f"{sw.junction_m:g}"),
            caveat=sentences(survey_note, accuracy),
        ),
        Finding(
            id="sidewalks_law",
            grade="D",
            statement=say(
                "sidewalks_law",
                free=n(free.value_m),
                page=free.page,
                w1=n(short[0].value_m),
                l1=n(short[0].max_length_m or 0),
                w2=n(short[-1].value_m),
                l2=n(short[-1].max_length_m or 0),
            ),
            values={"free_path_m": free.value_m, "short": [[ref.max_length_m, ref.value_m] for ref in short]},
            sources=[sw.free_path, *sw.short],
            caveat=sentences(free.text("scope", lang) + ".", free_doc.title + "."),
        ),
    ]
    sec = r.table("sidewalk_narrow_sections")
    bad, sure = sec[sec.below.astype(bool)], sec[sec.below_with_accuracy.astype(bool)]
    bounded_m = float(table.xs("all", level="block").bounded_m.sum())
    unmapped = caveat("sidewalks_unmapped", free=n(free.value_m))
    if len(bad):
        listed = "; ".join(
            say("sidewalk_section", side=sides[x.side], a=n(x.s_from, 0), b=n(x.s_to, 0), len=length(x.length_m), w=n(x.width_min_m))
            for x in bad.sort_values(["side", "s_from"]).itertuples()
        )
        margin = (
            say(
                "sidewalks_margin",
                count=len(sure),
                n=len(sure),
                m=length(sure.length_m.sum()),
                acc=n(cfg.cartography.edge_accuracy_m or 0.0),
            )
            if len(sure)
            else ""
        )
        statement = say("sidewalks_narrow", count=len(bad), n=len(bad), m=length(bad.length_m.sum()), list=listed) + margin
    else:
        statement = say("sidewalks_none", m=length(bounded_m))
    out.append(
        Finding(
            id="sidewalks_narrow",
            grade="I",
            statement=statement,
            values={
                "sections_below": len(bad),
                "metres_below": float(bad.length_m.sum()),
                "sections_below_with_accuracy": len(sure),
                "metres_below_with_accuracy": float(sure.length_m.sum()),
            },
            sources=["sidewalks", "sidewalks_law"],
            method=method("sidewalks_narrow", free=n(free.value_m)),
            caveat=sentences(unmapped, accuracy),
        )
    )
    open_m = float(table.xs("all", level="block")[f"metres_open_below_{free.value_m:g}m"].sum())
    if open_m:
        out.append(
            Finding(
                id="sidewalks_to_check",
                grade="M",
                statement=say("sidewalks_to_check", m=length(open_m), free=n(free.value_m)),
                values={"metres": open_m},
                sources=["sidewalks"],
            )
        )
    a = cfg.area_scan
    if a and a.sidewalks:
        area = r.table("area_sidewalks")
        hit = area[area.metres_below_with_accuracy > 0]  # the streets the case can name: below even with the margin
        within = int(((area.metres_below > 0) & (area.metres_below_with_accuracy == 0)).sum())
        streets = say("sidewalks_area_streets", count=len(area), n=len(area))
        acc = n(cfg.cartography.edge_accuracy_m or 0.0)
        if len(hit):
            names = "; ".join(
                say("sidewalks_area_street", street=x.street, m=length(x.metres_below_with_accuracy)) for x in hit.head(5).itertuples()
            )
            more = f" (+{len(hit) - 5})" if len(hit) > 5 else ""
            statement = say("sidewalks_area", streets=streets, count=len(hit), n=len(hit), acc=acc, names=names + more)
        else:
            statement = say("sidewalks_area_none", streets=streets, acc=acc)
        if within:
            statement += say("sidewalks_area_within", count=within, n=within)
        out.append(
            Finding(
                id="sidewalks_area",
                grade="M",
                statement=statement,
                values={"streets": len(area), "below_with_accuracy": hit.street.tolist(), "below_within_accuracy": within},
                sources=[a.sidewalks, a.axes, "sidewalks_law"],
                method=method("sidewalks_area", step=f"{a.sidewalk_step_m:g}"),
                caveat=sentences(caveat("sidewalks_area"), unmapped),
            )
        )
    return out


def overhang(table: Any, scenario: str, caveat: Any, n: Any, lang: str) -> str:
    """The width-budget caveat on parked vehicles: the bus x bus margin, bodies only, if they stick out of the mapped
    strips by each overhang the sensitivity table gives (``overhang_sensitivity.csv``)."""
    rows = table[(table.scenario == scenario) & (table.overhang_per_side_m > 0)].sort_values("overhang_per_side_m")
    or_ = t("report.or", lang)
    return str(
        caveat(
            "budget_inside",
            list=", ".join(n(x, 2) for x in rows.overhang_per_side_m.iloc[:-1]) + or_ + n(rows.overhang_per_side_m.iloc[-1], 2) + " m",
            margins=", ".join(n(x, 2, sign=True) for x in rows.margin_body_m.iloc[:-1])
            + or_
            + n(rows.margin_body_m.iloc[-1], 2, sign=True),
        )
    )


def delay_findings(r: Run, say: Any, method: Any, caveat: Any, n: Any) -> list[Finding]:
    """The measured time on the stretch (``delay`` stage): the ratio over every snapshot, by year and by direction,
    and the seconds over the hours the archive covers densely enough."""
    cfg, lang = r.cfg, r.case.lang
    dl, tr = cfg.delay, cfg.transit
    assert dl is not None
    assert tr is not None
    src = cfg.sources[dl.source]
    assert isinstance(src, GitArchive)
    summ = r.table("delay_summary").astype({"scope": str}).set_index("scope")
    data = r.table("delay_data").set_index("item").value
    routes = r.table("delay_routes").astype({"route_direction": str})
    sens = r.table("delay_sensitivity")
    checked = r.table("delay_passages")

    def pct(ratio: float) -> str:
        return str(n((float(ratio) - 1) * 100, 0, sign=True))

    def hours(hs: list[int]) -> str:
        return f"{min(hs)}h–{max(hs) + 1}h"

    years = [y for y in summ.index if y.isdigit()]
    unconfirmed = [y for y in years if summ.loc[y, "ratio_ci90_low"] <= 1]
    and_ = t("report.and", lang)
    whole = summ.loc["all"]
    sources = [dl.source, tr.source, cfg.profiles.axes]
    directions = [
        caveat(
            "delay_direction",
            route=row.route_direction.split()[0],
            heading=cfg.street.heading_label(int(row.heading)),
            pct=pct(summ.loc[row.route_direction, "ratio"]),
            lo=pct(summ.loc[row.route_direction, "ratio_ci90_low"]),
            hi=pct(summ.loc[row.route_direction, "ratio_ci90_high"]),
        )
        for row in routes.itertuples()
    ]
    common = [
        caveat("delay_source", url=src.url.removeprefix("https://github.com/"), commit=src.commit[:12]),
        caveat("delay_cause"),
        caveat("delay_days", n=int(data["holidays_left_out"])),
    ]
    out = [
        Finding(
            id="delay",
            grade="I",
            statement=say(
                "delay",
                first=data["first_day"],
                last=data["last_day"],
                days=int(whole.working_days),
                peak=hours(dl.peak_hours),
                off=hours(dl.off_peak_hours),
                routes=and_.join(tr.routes),
                a=n(dl.s_from, 0),
                b=n(dl.s_to, 0),
                length=n(dl.s_to - dl.s_from, 0),
                pct=pct(whole.ratio),
                lo=pct(whole.ratio_ci90_low),
                hi=pct(whole.ratio_ci90_high),
                years="; ".join(
                    say(
                        "delay_year",
                        year=y,
                        pct=pct(summ.loc[y, "ratio"]),
                        lo=pct(summ.loc[y, "ratio_ci90_low"]),
                        hi=pct(summ.loc[y, "ratio_ci90_high"]),
                        days=int(summ.loc[y, "working_days"]),
                    )
                    for y in years
                ),
                unconfirmed=say("delay_unconfirmed", count=len(unconfirmed), years=and_.join(unconfirmed)) if unconfirmed else "",
            ),
            values={
                "ratio": float(whole.ratio),
                "ratio_ci90": [float(whole.ratio_ci90_low), float(whole.ratio_ci90_high)],
                "by_year": {
                    y: {
                        "ratio": float(summ.loc[y, "ratio"]),
                        "ratio_ci90": [float(summ.loc[y, "ratio_ci90_low"]), float(summ.loc[y, "ratio_ci90_high"])],
                    }
                    for y in years
                },
                "working_days": int(whole.working_days),
            },
            sources=sources,
            method=method("delay", cm=n(dl.control_m, 0), gap=n(dl.control_gap_m, 0), reps=dl.bootstrap),
            caveat=sentences(
                caveat("delay_directions", list="; ".join(directions)),
                caveat("delay_sensitivity", lo=pct(sens.ratio.min()), hi=pct(sens.ratio.max())),
                *common,
            ),
        )
    ]
    fl = r.table("delay_fleet").astype({"route": str, "series": str})
    if len(fl):
        parts = []
        for route, g in fl.groupby("route", sort=False):
            main = g[g.share >= 0.05]
            parts.append(
                say(
                    "fleet_route",
                    route=route,
                    list=and_.join(
                        say("fleet_series", series=x.series, pct=n(100 * x.share, 0), k=int(x.vehicles)) for x in main.itertuples()
                    ),
                )
            )
        out.append(
            Finding(
                id="fleet",
                grade="M",
                statement=say("fleet", list="; ".join(parts)),
                values={
                    route: {x.series: {"share": float(x.share), "vehicles": int(x.vehicles)} for x in g.itertuples()}
                    for route, g in fl.groupby("route")
                },
                sources=[dl.source],
                method=method("fleet"),
                caveat=caveat("fleet"),
            )
        )
    if np.isfinite(whole.excess_s):
        by_year = [say("delay_hours_year", n=int(summ.loc[y, "covered_hours_peak"]), year=y) for y in years]
        timetable = float(checked.passages_per_hour_timetable.sum())  # 0 if the service day has no trip at those hours
        counted = float(checked.passages_per_hour_counted.sum()) / timetable if timetable else math.nan
        out.append(
            Finding(
                id="delay_seconds",
                grade="I",
                statement=say(
                    "delay_seconds",
                    hp=int(whole.covered_hours_peak),
                    ho=int(whole.covered_hours_off_peak),
                    gap=n(dl.max_gap_s / 60, 0),
                    by_year=and_.join(by_year),
                    off=n(whole.off_peak_s, 0),
                    peak=n(whole.peak_s, 0),
                    exp=n(whole.expected_peak_s, 0),
                    exc=n(whole.excess_s, 0),
                    lo=n(whole.excess_ci90_low_s, 0),
                    hi=n(whole.excess_ci90_high_s, 0),
                ),
                values={
                    "off_peak_s": float(whole.off_peak_s),
                    "peak_s": float(whole.peak_s),
                    "expected_peak_s": float(whole.expected_peak_s),
                    "excess_s": float(whole.excess_s),
                    "excess_ci90_s": [float(whole.excess_ci90_low_s), float(whole.excess_ci90_high_s)],
                    "covered_hours": {"peak": int(whole.covered_hours_peak), "off_peak": int(whole.covered_hours_off_peak)},
                },
                sources=[*sources, "delay"],
                method=method("delay_seconds", reach=n(dl.reach_m, 0), gap=n(dl.max_gap_s / 60, 0)),
                caveat=sentences(
                    caveat(
                        "delay_by_hour",
                        list="; ".join(
                            caveat("delay_hour", h=row.variant.split()[2].rstrip("h"), s=n(row.excess_s, 0))
                            for row in sens[sens.variant.str.startswith("peak hour")].itertuples()
                        ),
                    )
                    if sens.variant.str.startswith("peak hour").any()
                    else "",
                    caveat("delay_passages", pct=n(100 * counted, 0), day=tr.service_date) if math.isfinite(counted) else "",
                    common[0],
                ),
            )
        )
    return out


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
    head = ["# " + info.title, "", *([f"> {info.question}", ""] if info.question else []), say("intro"), ""]
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
    if isinstance(source, HttpFiles):
        return [f.url for f in source.files]
    if isinstance(source, GitArchive):  # the archive as it was at the pinned commit
        return [f"{source.url}/tree/{source.commit}" if source.url.startswith("https://github.com/") else f"{source.url}@{source.commit}"]
    return [source.url]


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
