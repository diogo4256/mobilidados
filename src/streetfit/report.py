"""The findings ledger: every statement the case can make, with its evidence grade, sources and caveats.

Grades (docs/evidence-standard.md): M measured from official data · D official document text · I inference
from M/D/P · P assumption · NE not found / not verified (which is not the same as "does not exist").

The ledger is generated from the result tables, so a statement can never drift from its number. Letters and
reports should quote the ledger, and ``streetfit check-claims`` verifies drafts against it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

import pandas as pd

from . import envelope, standards
from .i18n import num
from .provenance import Lock


@dataclass
class Finding:
    id: str
    grade: str
    statement: str
    values: dict = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    method: str = ""
    caveat: str = ""


TXT = {
    "length": {
        "en": "The street axis is {length} m long.",
        "pt": "O eixo da rua tem {length} m.",
    },
    "traffic": {
        "en": "The municipal routing network marks the street as {traffic} (edges checked at {n} points along it).",
        "pt": "A rede viária municipal marca a rua como de {traffic} (arestas verificadas em {n} pontos ao longo da rua).",
    },
    "free": {
        "en": "Where parking strips are mapped on both sides ({metres} m of the street), the mapped free width between "
        "them is {fmin}–{fmax} m (median {fmed} m).",
        "pt": "Onde há faixas de estacionamento cartografadas dos dois lados ({metres} m da rua), a faixa livre "
        "cartografada entre elas mede {fmin}–{fmax} m (mediana {fmed} m).",
    },
    "strips": {
        "en": "The mapped parking strips are {sl} m ({side_l}) and {sr} m ({side_r}) wide (medians).",
        "pt": "As faixas de estacionamento cartografadas têm {sl} m (lado {side_l}) e {sr} m (lado {side_r}) (medianas).",
    },
    "routes": {
        "en": "Routes {routes} are scheduled along the street. On {day}: {n_up} trips {up} and {n_down} trips {down} "
        "(at most {max_up} and {max_down} per hour).",
        "pt": "As carreiras {routes} estão programadas ao longo da rua. Em {day}: {n_up} viagens {up} e {n_down} "
        "viagens {down} (no máximo {max_up} e {max_down} por hora).",
    },
    "vehicle_body": {
        "en": "Reference vehicle '{label}': body width {w} m ({src}).",
        "pt": "Veículo de referência «{label}»: largura da carroçaria {w} m ({src}).",
    },
    "vehicle_mirrors": {
        "en": "Width with mirrors of '{label}' taken as {w} m ({src}).",
        "pt": "Largura com espelhos de «{label}» considerada {w} m ({src}).",
    },
    "budget": {
        "en": "With both strips occupied and parked vehicles inside them, two buses need {bb} m (bodies only; {bbm} m "
        "with mirrors) against a median free width of {fmed} m: margin {mbb} m. A bus and a car need {bc} m: "
        "margin {mbc} m ({mbcm} m with the car's mirrors).",
        "pt": "Com as duas faixas ocupadas e os veículos estacionados dentro delas, dois autocarros precisam de {bb} m "
        "(só carroçaria; {bbm} m com espelhos) para uma faixa livre mediana de {fmed} m: folga {mbb} m. Um "
        "autocarro e um ligeiro precisam de {bc} m: folga {mbc} m ({mbcm} m com o espelho do ligeiro).",
    },
    "encounters": {
        "en": "The timetable implies {nrange} meetings per weekday between buses in opposite directions on the street "
        "(constant-speed model at {speeds} km/h); {nnarrow} fall within the sections with parking on both sides.",
        "pt": "O horário implica {nrange} encontros por dia útil entre autocarros em sentidos opostos na rua (modelo "
        "de velocidade constante a {speeds} km/h); {nnarrow} caem nos troços com estacionamento dos dois lados.",
    },
    "occurrences": {
        "en": "{n} reports in category '{flt}' were attributed to the street ({period}, within {d} m of the axis): "
        "{rate} per 100 m, rank {rank} of {total} streets of at least {minlen} m in the surrounding area.",
        "pt": "Foram atribuídas à rua {n} ocorrências da categoria «{flt}» ({period}, a ≤{d} m do eixo): {rate} por "
        "100 m, {rank}.ª de {total} ruas com pelo menos {minlen} m na envolvente.",
    },
    "area": {
        "en": "Of {total} streets with scheduled buses in the surrounding area, {k} are two-way and combine parking on both "
        "sides with a free width below {thr} m over at least {minm} m ({names}); of these, {nb} with buses in "
        "both directions: {names2}.",
        "pt": "Das {total} ruas com autocarros programados na envolvente, {k} são de dois sentidos e combinam "
        "estacionamento dos dois lados com uma faixa livre inferior a {thr} m em pelo menos {minm} m ({names}); "
        "destas, {nb} com autocarros nos dois sentidos: {names2}.",
    },
    "standard": {
        "en": "{doc}, p. {page} ({kind}): {label}: {value} m. Scope: {scope}. Measured median: {fmed} m ({diff} m).",
        "pt": "{doc}, p. {page} ({kind}): {label}: {value} m. Âmbito: {scope}. Mediana medida: {fmed} m ({diff} m).",
    },
}
KIND = {
    "reference_profile": {"en": "reference profile", "pt": "perfil de referência"},
    "conditional_value": {"en": "conditional value", "pt": "valor condicionado"},
    "secondary_citation": {"en": "cited by an official document", "pt": "citado em documento oficial"},
}
TRAFFIC = {
    "two-way": {"en": "two-way traffic", "pt": "dois sentidos"},
    "one-way": {"en": "one-way traffic", "pt": "sentido único"},
    "?": {"en": "unknown direction", "pt": "sentido desconhecido"},
}


def _tables(run, *names):
    out = []
    for n in names:
        if n not in run.tables and (run.tables_dir / f"{n}.csv").exists():
            run.tables[n] = pd.read_csv(run.tables_dir / f"{n}.csv")
        out.append(run.tables.get(n))
    return out


def build(run) -> list[Finding]:
    c, lang = run.case, run.case.lang
    L = lambda key, **kw: TXT[key].get(lang, TXT[key]["en"]).format(**kw)  # noqa: E731
    n = lambda x, d=2, sign=False: num(x, lang, d, sign)  # noqa: E731
    F: list[Finding] = []
    (summary,) = _tables(run, "summary_by_block")
    allrow = summary.set_index("block").loc["all"]
    length = run.facts.get("length_m") or float(
        json.loads((c.results_dir / "street_axis.geojson").read_text())["features"][0]["properties"]["length_m"]
    )
    F.append(
        Finding(
            "length", "M", L("length", length=n(length)), {"length_m": length}, ["street_axes"], "Axis polyline length (projected CRS)."
        )
    )

    (edges,) = _tables(run, "traffic_direction_edges")
    if edges is not None:
        from .network import directions

        tr = directions(edges, c.cfg["network"]["open_value"])
        F.append(
            Finding(
                "traffic",
                "M",
                L("traffic", traffic=TRAFFIC[tr][lang], n=edges.s_m.nunique()),
                {"traffic": tr},
                [c.section("direction")["source"]],
                "Identify on the routing network at stations along the axis.",
            )
        )

    (narrow,) = _tables(run, "narrow_sections")
    step = float(c.section("profiles").get("step_m", 0.5))
    metres = n(float((narrow.s_to - narrow.s_from).sum()), 1).rstrip("0").rstrip(",.")
    F.append(
        Finding(
            "free_width",
            "M",
            L("free", metres=metres, fmin=n(allrow.free_min), fmax=n(allrow.free_max), fmed=n(allrow.free_median)),
            {
                "min_m": allrow.free_min,
                "median_m": allrow.free_median,
                "max_m": allrow.free_max,
                "p5_m": allrow.free_p5,
                "p95_m": allrow.free_p95,
                "metres_two_strips": metres,
            },
            ["cartography", "street_axes"],
            f"Transects every {step:g} m, widths read from mapped polygons only.",
            c.cfg["cartography"].get("accuracy_note", ""),
        )
    )
    sides = c.cfg["street"].get("sides", {"L": "L", "R": "R"})
    F.append(
        Finding(
            "parking_strips",
            "M",
            L("strips", sl=n(allrow.strip_L_median), sr=n(allrow.strip_R_median), side_l=sides["L"], side_r=sides["R"]),
            {"left_m": allrow.strip_L_median, "right_m": allrow.strip_R_median},
            ["cartography"],
            "Mapped area, not parked vehicles.",
        )
    )

    (tph,) = _tables(run, "trips_per_hour")
    if tph is not None:
        t = c.section("transit")
        tph = tph.set_index("hour") if "hour" in tph.columns else tph
        up, down = c.heading_label(1), c.heading_label(-1)
        F.append(
            Finding(
                "transit",
                "M",
                L(
                    "routes",
                    routes=", ".join(t["routes"]),
                    day=t["service_date"],
                    n_up=int(tph[up].sum()),
                    n_down=int(tph[down].sum()),
                    up=up,
                    down=down,
                    max_up=int(tph[up].max()),
                    max_down=int(tph[down].max()),
                ),
                {
                    "trips_up": int(tph[up].sum()),
                    "trips_down": int(tph[down].sum()),
                    "max_up_per_hour": int(tph[up].max()),
                    "max_down_per_hour": int(tph[down].max()),
                    "service_date": str(t["service_date"]),
                },
                [t["source"]],
                "Trips counted at a reference stop per direction; timetable, not observed operation.",
            )
        )

    e = c.section("envelope")
    veh = envelope.load_vehicles(c.cfg.get("vehicles"))
    for vid in dict.fromkeys([e["bus"], e["car"]]):
        v = veh[vid]
        tr = lambda key, v=v: v.translations.get(lang, {}).get(key, getattr(v, key))  # noqa: E731
        F.append(
            Finding(
                f"vehicle_{vid}_body",
                v.grade_body,
                L("vehicle_body", label=tr("label"), w=n(v.width_body_m), src=tr("source_body")),
                {"width_m": v.width_body_m},
                [v.source_body],
            )
        )
        F.append(
            Finding(
                f"vehicle_{vid}_mirrors",
                v.grade_mirrors,
                L("vehicle_mirrors", label=tr("label"), w=n(v.width_mirrors_m), src=tr("source_mirrors")),
                {"width_m": v.width_mirrors_m},
                [v.source_mirrors],
            )
        )
    bus, car = veh[e["bus"]], veh[e["car"]]
    fmed = float(allrow.free_median)
    bb, bbm, bc, bcm = (
        envelope.widths(bus, bus, False),
        envelope.widths(bus, bus, True),
        envelope.widths(bus, car, False),
        envelope.widths(bus, car, True),
    )
    F.append(
        Finding(
            "width_budget",
            "I",
            L(
                "budget",
                bb=n(bb),
                bbm=n(bbm),
                fmed=n(fmed),
                mbb=n(fmed - bb, sign=True),
                bc=n(bc),
                mbc=n(fmed - bc, sign=True),
                mbcm=n(fmed - bcm, sign=True),
            ),
            {
                "bus_bus_margin_m": round(fmed - bb, 2),
                "bus_bus_margin_mirrors_m": round(fmed - bbm, 2),
                "bus_car_margin_m": round(fmed - bc, 2),
                "bus_car_margin_mirrors_m": round(fmed - bcm, 2),
            },
            ["free_width", f"vehicle_{bus.id}_body", f"vehicle_{bus.id}_mirrors", f"vehicle_{car.id}_body"],
            "Static envelope (sum of widths), not a swept-path simulation.",
            "Assumes parked vehicles stay inside the mapped strips; see overhang_sensitivity.csv.",
        )
    )

    es, ed = _tables(run, "encounters_summary", "encounters_detail")
    if es is not None:
        counts = sorted(set(es.encounters_per_day))
        nn = sorted(set(ed.groupby("speed_kmh").in_narrow_section.sum().astype(int)))
        F.append(
            Finding(
                "encounters",
                "I",
                L(
                    "encounters",
                    nrange="–".join(map(str, counts)),
                    speeds="/".join(f"{v:g}" for v in es.speed_kmh),
                    nnarrow="–".join(map(str, nn)),
                ),
                {"per_day": counts, "in_narrow_sections": nn},
                ["transit", "free_width"],
                "Presence-interval overlap at constant speed from scheduled times; timetable, not observation.",
            )
        )

    (occ,) = _tables(run, "occurrences_by_street")
    if occ is not None:
        o = c.section("occurrences")
        fname, frx = next(iter(o["filters"].items()))
        occ = occ.sort_values(f"{fname}_per_100m", ascending=False).reset_index(drop=True)
        me = occ[occ.street == c.cfg["street"]["name"]]
        if len(me):
            row = me.iloc[0]
            period = run.facts.get("occurrences_period") or o.get("period", "")
            period = " – ".join(period) if isinstance(period, list) else period
            F.append(
                Finding(
                    "occurrences",
                    "M",
                    L(
                        "occurrences",
                        n=int(row[f"{fname}_n"]),
                        flt=frx.lstrip("^"),
                        period=period,
                        d=o.get("max_dist_m", 12),
                        rate=n(row[f"{fname}_per_100m"]),
                        rank=int(me.index[0]) + 1,
                        total=len(occ),
                        minlen=o.get("min_street_length_m", 0),
                    ),
                    {
                        "n": int(row[f"{fname}_n"]),
                        "per_100m": float(row[f"{fname}_per_100m"]),
                        "rank": int(me.index[0]) + 1,
                        "of": len(occ),
                    },
                    [o["source"]],
                    "Nearest-street attribution of geolocated open-data records.",
                    "A report is not a proven infraction; counts are small.",
                )
            )

    (area,) = _tables(run, "area_streets")
    if area is not None and len(area):
        a = c.section("area_scan")
        minm = a.get("min_pattern_m", 30)
        # one-way streets need a single lane, so a narrow free width there is a different situation: only two-way
        # streets share the case's pattern
        k = area[(area.metres_with_pattern >= minm) & (area.traffic == "two-way")]
        both = k[k.buses_both_directions]
        if len(k):
            and_ = " e " if lang == "pt" else " and "
            F.append(
                Finding(
                    "area_pattern",
                    "M",
                    L(
                        "area",
                        total=len(area),
                        k=len(k),
                        thr=n(a.get("threshold_m", 5.5), 1),
                        minm=minm,
                        names=and_.join(k.street),
                        nb=len(both),
                        names2=and_.join(both.street) or "—",
                    ),
                    {"two_way_streets": k.street.tolist(), "with_buses_both_directions": both.street.tolist()},
                    ["area_cartography", "area_axes", a.get("identify_source", ""), c.section("transit")["source"]],
                    "Stations every 3 m on every street axis with buses; same width method as the case street; "
                    "traffic direction from the routing network at one station per street.",
                )
            )

    for rid in c.section("standards").get("compare", []):
        ref, doc = standards.reference(rid)
        tr = lambda key, ref=ref: ref.get(f"{key}_{lang}", ref[key])  # noqa: E731
        F.append(
            Finding(
                f"standard_{rid}",
                "D",
                L(
                    "standard",
                    doc=doc["title"],
                    page=ref["page"],
                    kind=KIND[ref["kind"]][lang],
                    label=tr("label"),
                    value=n(ref["value_m"]),
                    scope=tr("scope"),
                    fmed=n(fmed),
                    diff=n(fmed - ref["value_m"], sign=True),
                ),
                {"value_m": ref["value_m"], "difference_m": round(fmed - ref["value_m"], 2)},
                [rid],
                "",
                tr("derivation"),
            )
        )

    for i, gap in enumerate(c.cfg.get("known_gaps", []), 1):
        F.append(Finding(f"gap_{i}", "NE", gap.get(lang, gap.get("en", ""))))
    return F


def write(run) -> None:
    findings = build(run)
    c = run.case
    lock = Lock(c.lock_path)
    out = {
        "case": c.cfg["case"],
        "findings": [asdict(f) for f in findings],
        "sources": {sid: {k: v for k, v in e.items() if k != "files"} | {"files": e.get("files", {})} for sid, e in lock.entries.items()},
    }
    (c.results_dir / "findings.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n")
    (c.results_dir / "findings.md").write_text(markdown(c, findings, lock))


def markdown(c, findings: list[Finding], lock: Lock) -> str:
    pt = c.lang == "pt"
    head = [
        "# " + c.cfg["case"]["title"],
        "",
        f"> {c.cfg['case'].get('question', '')}",
        "",
        (
            "Gerado por `streetfit run` a partir das tabelas em `tables/`. Cada afirmação tem um grau de evidência: "
            "**M** medido em dados oficiais · **D** texto de documento oficial · **I** inferência · **P** pressuposto · "
            "**NE** não encontrado / não verificado (≠ não existe)."
        )
        if pt
        else (
            "Generated by `streetfit run` from the tables in `tables/`. Every statement carries an evidence grade: "
            "**M** measured from official data · **D** official document text · **I** inference · **P** assumption · "
            "**NE** not found / not verified (≠ does not exist)."
        ),
        "",
    ]
    body = []
    for f in findings:
        line = f"- **[{f.grade}]** {f.statement}"
        extra = [x for x in (f.method, f.caveat) if x]
        if extra:
            line += f"  \n  <sub>{' · '.join(extra)}</sub>"
        body.append(line)
    src = [
        "",
        "## " + ("Fontes" if pt else "Sources"),
        "",
        "| id | "
        + ("origem" if pt else "origin")
        + " | "
        + ("obtido" if pt else "retrieved")
        + " | "
        + ("licença" if pt else "licence")
        + " | sha256 |",
        "|---|---|---|---|---|",
    ]
    for sid, e in sorted(lock.entries.items()):
        origin = e.get("url") or ", ".join(sorted(e.get("urls", {}).values()))[:120]
        shas = "<br>".join(f"`{m['sha256'][:12]}…` {p}" for p, m in sorted(e.get("files", {}).items())[:3])
        more = len(e.get("files", {})) - 3
        if more > 0:
            shas += f"<br>+{more}"
        src.append(f"| {sid} | {origin} | {e.get('retrieved_utc', '')[:10]} | {e.get('licence', '')} | {shas} |")
    return "\n".join(head + body + src) + "\n"
