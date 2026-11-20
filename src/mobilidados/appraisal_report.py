"""The feasibility study and cost-benefit analysis as a document: ``results/appraisal.md``, in the case's language.

Every number comes from the run's tables (``appraisal_*``, ``delay_*`` and the measurement tables) or from the case's
``[appraisal]`` configuration, and every conclusion is a sentence chosen by the numbers, so the text cannot drift from
them. Money is rounded to 100 € and shares to whole percents: the inputs do not support more.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from . import envelope
from .i18n import num, t

if TYPE_CHECKING:
    from .pipeline import Run

MONEY_INPUTS = ("excess_s", "load_peak", "car_value", "occupancy", "enforcement_year", "share_E", "share_G", "offpeak_s", "room_nearby")


def grouped(x: float, lang: str, d: int = 0) -> str:
    """A number with thousands grouped as the language writes them: ``2 100,5`` / ``2,100.5``; a true minus sign."""
    s = f"{abs(x):,.{d}f}"
    s = s.replace(",", " ").replace(".", ",") if lang == "pt" else s
    return (
        ("−" if x < 0 and float(s.replace(" ", "").replace(",", ".")) else "") + s
        if lang == "pt"
        else ("−" if x < 0 and abs(x) >= 0.5 * 10**-d else "") + s
    )


def money(x: float, lang: str) -> str:
    """Euros, rounded to 10 below a thousand and to 100 above (the inputs support no more), grouped: ``−61 100 €`` / ``−€61,100``."""
    if not math.isfinite(x):
        return "—"
    step = 10 if abs(x) < 1000 else 100
    v = round(x / step) * step
    digits = grouped(abs(v), lang)
    sign = "−" if v < 0 else ""
    return f"{sign}{digits} €" if lang == "pt" else f"{sign}€{digits}"


def pvalue(p: float, lang: str) -> str:
    """A small p-value as a power of ten: ``1,5 × 10⁻⁶``."""
    if p >= 0.001:
        return num(p, lang, 3)
    exp = math.floor(math.log10(p))
    sup = str(exp).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{num(p / 10**exp, lang, 1)} × 10{sup}"


def first_lower(text: str) -> str:
    """A label inside a sentence: its first letter in lower case, the rest as written (``Opção C`` stays ``opção C``)."""
    return text[:1].lower() + text[1:]


def build(r: Run) -> str:
    cfg, lang = r.cfg, r.case.lang
    a, dl, e = cfg.appraisal, cfg.delay, cfg.envelope
    assert a is not None
    assert dl is not None
    assert e is not None

    def say(key: str, **kw: Any) -> str:
        return t(f"study.{key}", lang, **kw)

    def n(x: float, d: int = 1, sign: bool = False) -> str:
        if sign or abs(float(x)) < 1000:
            return num(float(x), lang, d, sign)
        return grouped(float(x), lang, d)

    def part_label(name: str) -> str:
        """A narrow section by its block; a junction by the cross street that meets the street there (from the block labels)."""
        row = parts[parts.part == name].iloc[0]
        span = f"{n(row.from_m, 1)}–{n(row.to_m, 1)} m"
        if row.narrow:
            return f"{name.split()[0]} ({span})"
        cross = [b.label.split("→")[-1].strip() for b in cfg.street.blocks if b.label and "→" in b.label and row.from_m < b.end < row.to_m]
        return f"({cross[0]}, {span})" if cross else f"({span})"

    def measured_label(k: str) -> str:
        head, _, tail = k.partition("_")
        if k == "excess_s":
            return say("m_excess_s")
        if k == "peak_passages_per_working_day":
            return say("m_peak_passages")
        if k == "working_days_per_year":
            return say("m_working_days")
        if k == "passages_year":
            return say("m_passages_year")
        if head == "passages":
            part, _, oid = tail.partition("_")
            return say(f"m_passages_{part}", id=oid)
        return say("m_attribution" if head == "attribution" else "m_metres", id=tail)

    def label_of(k: str) -> str:
        return str(inputs.label[k]) if k in inputs.index else measured_label(k)

    def pct(ratio: float) -> str:
        return n((float(ratio) - 1) * 100, 0, sign=True)

    tab = r.table
    results = tab("appraisal_results")
    res = results[results.layer == "core"].set_index("option")
    ext = results[results.layer == "extended"].set_index("option")
    mcs = tab("appraisal_montecarlo")
    mc = mcs[mcs.layer == "core"].set_index("option")
    mce = mcs[mcs.layer == "extended"].set_index("option")
    sw = tab("appraisal_switching")
    tor = tab("appraisal_tornado")
    voi = tab("appraisal_voi")
    bridge = tab("appraisal_bridge")
    dist = tab("appraisal_distribution")
    crit = tab("appraisal_criteria")
    inputs = tab("appraisal_inputs").set_index("input")
    measured = tab("appraisal_measured").set_index("input")
    feas = tab("appraisal_feasibility")
    alts = tab("appraisal_alternatives")
    summ = tab("delay_summary").astype({"scope": str}).set_index("scope")
    parts = tab("delay_by_part")
    copres = tab("delay_copresence")
    whole = summ.loc["all"]
    vehicles = cfg.all_vehicles()
    bus = vehicles[e.bus]
    out: list[str] = [f"# {say('title', street=cfg.street.name)}", "", say("intro"), ""]
    dims = {d: say(f"dim_{d}") for d in ("technical", "legal", "operational", "social")}

    # --- the problem ---------------------------------------------------------------------------------------------------
    allrow = tab("summary_by_block").set_index("block").loc["all"]
    one_side = float(tab("without_parking").set_index("without").loc[["L", "R"], "free_median"].min())
    years = "; ".join(
        f"{y}: {pct(summ.loc[y, 'ratio'])}%" + (f", {say('year_unconfirmed')}" if summ.loc[y, "ratio_ci90_low"] <= 1 else "")
        for y in summ.index
        if y.isdigit()
    )
    problem = say(
        "problem",
        metres=n(r.two_strips_m, 1),
        free=n(allrow.free_median, 2),
        bb=n(envelope.widths(bus, bus, False), 2),
        bbm=n(envelope.widths(bus, bus, True), 2),
        one_side=n(one_side, 2),
        peak=f"{min(dl.peak_hours)}h–{max(dl.peak_hours) + 1}h",
        pct=pct(whole.ratio),
        lo=pct(whole.ratio_ci90_low),
        hi=pct(whole.ratio_ci90_high),
        s=n(whole.excess_s, 0),
        slo=n(whole.excess_ci90_low_s, 0),
        shi=n(whole.excess_ci90_high_s, 0),
        years=years,
    )
    peak = copres[copres.period == "peak"].set_index("part")
    gaps = parts[~parts.narrow.astype(bool)]
    giving = [p for p in gaps.part if p in peak.index and peak.p_value[p] < a.significance]
    total = float(parts.excess_s.sum())
    narrow_s = float(parts[parts.narrow.astype(bool)].excess_s.sum())
    attr = float(measured.loc[f"attribution_{a.options[0].id}", "central"]) if a.options else 0.0
    if giving:
        g = peak.loc[giving[0]]
        parts_text = say("problem_parts", narrow=n(narrow_s, 1), gaps=n(total - narrow_s, 1), giving=part_label(giving[0]), share=n(100 * g.share, 0),
                         chance=n(100 * g.chance, 0), p=pvalue(g.p_value, lang), attr=n(100 * attr, 0))  # fmt: skip
    else:
        parts_text = say("problem_parts_none", narrow=n(narrow_s, 1), gaps=n(total - narrow_s, 1), attr=n(100 * attr, 0))
    problem_block = [f"## {say('h_problem')}", "", problem, "", parts_text, ""]

    # --- the options ---------------------------------------------------------------------------------------------------
    opts = [f"## {say('h_options')}", "", say("options_intro"), "", say("option_header"), "| --- | --- | ---: | ---: | --- |"]
    for o in a.options:
        timed = o.days != "all" or o.hours != (0, 24)
        when = (
            say("when_hours", days=say("working_days" if o.days == "working" else "all_days"), a=o.hours[0], b=o.hours[1])
            if timed
            else say("when_always")
        )
        opts.append(
            say("option_row", id=o.id, label=o.label, metres=n(res.loc[o.id, "metres"], 1), places=n(res.loc[o.id, "places"], 0), when=when)
        )
    screened = [nt for nt in a.notes if nt.dimension == "options"]
    if screened:
        opts += ["", say("screened"), ""] + [f"- {nt.text}" for nt in screened]
    opts.append("")

    # --- feasibility ---------------------------------------------------------------------------------------------------
    fe = [f"## {say('h_feasibility')}", "", say("feasibility_header"), "| --- | --- | --- | --- | --- |"]
    for row in feas.itertuples():
        if row.dimension in ("evidence", "options"):
            continue
        if pd.notna(row.value_m):
            result = f"{n(row.value_m, 2)} m / {n(row.reference_m, 2)} m: {say('st_ok' if row.status == 'ok' else 'st_short')}"
        elif pd.notna(row.share_low):
            result = say("places_share_value", lo=n(100 * row.share_low, 1), hi=n(100 * row.share_high, 1))
        else:
            result = ""
        fe.append(
            f"| {dims.get(row.dimension, row.dimension)} | {row.check} | {result} | {row.grade} | {row.source if pd.notna(row.source) else ''} |"
        )
    fe.append("")

    # --- cost-benefit --------------------------------------------------------------------------------------------------
    rate = n(100 * a.discount_rate, 0)
    tested = " / ".join(f"{n(100 * x, 0)}%" for x in a.discount_rates_tested)
    layer_name = {"core": say("layer_core"), "extended": say("layer_extended")}
    cba = [
        f"## {say('h_cba')}",
        "",
        say("cba_method", year=a.price_year, years=a.horizon_years, rate=rate, tested=tested),
        "",
        say("layers_intro"),
        "",
    ]
    cba += [f"### {say('h_inputs')}", "", say("inputs_header"), "| --- | --- | ---: | ---: | ---: | --- | --- | --- |"]
    for _, row in inputs.iterrows():
        cba.append(
            f"| {row.label} | {layer_name[row.layer]} | {n(row.low, 2)} | {n(row['central'], 2)} | {n(row.high, 2)} | "
            f"{row.unit if pd.notna(row.unit) else ''} | {row.grade} | {row.source} |"
        )
    cba += ["", say("measured_header"), "| --- | ---: | ---: | ---: |"]
    for k, row in measured.iterrows():
        d = 0 if str(k).startswith(("peak_passages", "working_days", "passages")) else 1 if str(k).startswith(("metres_", "excess_")) else 2
        cba.append(f"| {measured_label(str(k))} | {n(row.low, d)} | {n(row['central'], d)} | {n(row.high, d)} |")
    r1, r2 = (round(100 * x) for x in a.discount_rates_tested[:2]) if len(a.discount_rates_tested) >= 2 else (3, 7)
    cba += ["", f"### {say('h_results')}", "", say("results_core_intro"), "", say("results_header", years=a.horizon_years, rate=rate, r1=r1, r2=r2),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]  # fmt: skip
    for oid, row in res.iterrows():
        cba.append(
            f"| {oid} | {money(row.benefit_year, lang)} | {money(row.parking_year + row.enforcement_year, lang)} | {money(row.works, lang)} | "
            f"{money(row.npv, lang)} | {n(row.bcr, 2)} | {money(row.get(f'npv_at_{r1}pct', np.nan), lang)} | {money(row.get(f'npv_at_{r2}pct', np.nan), lang)} |"
        )
    cba += [
        "",
        say("results_ext_intro"),
        "",
        say("results_ext_header"),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for oid, row in ext.iterrows():
        cba.append(
            f"| {oid} | {money(row.time_value, lang)} | {money(row.operator_value, lang)} | {money(row.traffic_value, lang)} | {money(row.new_rider_value, lang)} | "
            f"{money(row.external_value, lang)} | {money(row.damage_value, lang)} | {money(row.benefit_year, lang)} | "
            f"{money(row.parking_year + row.enforcement_year, lang)} | {money(row.works, lang)} | {money(row.npv, lang)} | {n(row.bcr, 2)} |"
        )
    cba += ["", f"### {say('h_vfm')}", "", say("vfm_intro"), "", say("vfm_header"), "| --- | --- | ---: | ---: | ---: | --- |"]
    for row in results.itertuples():
        cba.append(
            f"| {layer_name[row.layer]} | {row.option} | {money(row.npv, lang)} | {n(row.bcr, 2)} | {n(row.bcr_budget, 2)} | {say('vfm_' + row.vfm)} |"
        )
    ids_b = list(dict.fromkeys(bridge.option))
    cba += ["", f"### {say('h_bridge')}", "", say("bridge_intro"), "", "| " + say("bridge_step") + " | " + " | ".join(ids_b) + " |",
            "| --- |" + " ---: |" * len(ids_b)]  # fmt: skip
    for step in dict.fromkeys(bridge.step):
        vals = bridge[bridge.step == step].set_index("option").change
        sign = step != "core"
        cba.append(
            f"| {say('bridge_' + step)} | "
            + " | ".join((("+" if vals[i] > 0 and sign else "") + money(float(vals[i]), lang)) for i in ids_b)
            + " |"
        )
    final = bridge.groupby("option").npv.last()
    cba.append(f"| **{say('bridge_extended')}** | " + " | ".join(f"**{money(float(final[i]), lang)}**" for i in ids_b) + " |")
    cba += ["", f"### {say('h_uncertainty')}", "", say("mc_intro", draws=f"{a.draws:,}".replace(",", " " if lang == "pt" else ",")), "", say("mc_header"),
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]  # fmt: skip
    for row in mcs.itertuples():
        cba.append(
            f"| {layer_name[row.layer]} | {row.option} | {money(row.p10, lang)} | {money(row.p50, lang)} | {money(row.p90, lang)} | "
            f"{n(100 * row.probability_positive, 0)}% | {n(100 * row.probability_best, 0)}% |"
        )
    cba += [
        "",
        f"### {say('h_switching')}",
        "",
        say("switching_intro"),
        "",
        say("switching_header"),
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    key = sw[sw.input.isin(MONEY_INPUTS) | sw.input.str.startswith("attribution_")]
    for row in key.itertuples():
        sv = "—" if pd.isna(row.switching_value) else n(row.switching_value, 2)
        cba.append(
            f"| {layer_name[row.layer]} | {row.option} | {label_of(row.input)} | {n(row.central, 2)} | {sv} | {'✓' if row.within_range else '✗'} |"
        )
    best = str(mce["mean"].idxmax())
    top = tor[tor.option == best].head(8)
    cba += ["", say("tornado_intro", id=best), "", say("tornado_header"), "| --- | ---: | ---: |"]
    cba += [f"| {label_of(row.input)} | {money(row.npv_at_low, lang)} | {money(row.npv_at_high, lang)} |" for row in top.itertuples()]
    evpi = float(voi.loc[voi.input == "(all)", "evppi"].iloc[0]) if len(voi) else 0.0
    worth = voi[(voi.input != "(all)") & (voi.evppi >= max(50.0, 0.01 * evpi))]
    cba += ["", f"### {say('h_voi')}", "", say("voi_intro", evpi=money(evpi, lang)), ""]
    if len(worth):
        cba += [say("voi_header"), "| --- | ---: |"] + [
            f"| {label_of(row.input)} | {money(row.evppi, lang)} |" for row in worth.itertuples()
        ]
    else:
        cba.append(say("voi_none"))
    ids = [o.id for o in a.options]
    cba += ["", f"### {say('h_distribution')}", "", say("distribution_intro"), "", "| " + say("group") + " | " + " | ".join(ids) + " |",
            "| --- |" + " ---: |" * len(ids)]  # fmt: skip
    cba.append(f"| {say('g_trips')} | " + " | ".join(grouped(float(ext.loc[i, "riders"]), lang) for i in ids) + " |")
    cba.append(f"| {say('g_saved')} | " + " | ".join(n(float(ext.loc[i, "saved_s_per_passenger"]), 1) for i in ids) + " |")
    cba.append(f"| {say('g_places')} | " + " | ".join(n(float(ext.loc[i, "places"]), 0) for i in ids) + " |")
    for g in dist.group.drop_duplicates():
        vals = dist[dist.group == g].set_index("option").value
        cba.append(f"| {say('g_' + g)} | " + " | ".join(money(float(vals[i]), lang) for i in ids) + " |")
    cba.append("")

    # --- what has no price ---------------------------------------------------------------------------------------------
    crit_block: list[str] = []
    if len(crit):
        crit_block = [f"## {say('h_criteria')}", "", say("criteria_intro"), "", "| " + say("criteria_head") + " | " + " | ".join(ids) + " | " + say("criteria_tail") + " |",
                      "| --- | --- |" + " :---: |" * len(ids) + " --- | --- |"]  # fmt: skip
        for row in crit.itertuples():
            cells = " | ".join(str(getattr(row, i)).replace("-", "−") for i in ids)
            crit_block.append(f"| {row.label} | {row.indicator} | {cells} | {row.grade} | {row.note} |")
        crit_block.append("")

    # --- the alternative, the gaps, the conclusions -------------------------------------------------------------------
    alt_block: list[str] = []
    removable_s = float(whole.excess_s) * attr
    if len(alts):
        alt_block = [f"## {say('h_alternatives')}", ""]
        for row in alts.itertuples():
            alt_block += [say("alternative", label=row.label[:1].upper() + row.label[1:], places=n(row.places, 0), cost=money(row.pv_cost, lang),
                              hours=n(row.breakeven_bus_hours_per_year, 1), secs=n(row.breakeven_seconds_per_peak_passage, 1),
                              secs_all=n(row.breakeven_seconds_per_passage, 1), attr_s=n(removable_s, 0)), ""]  # fmt: skip
    gaps_block = (
        [f"## {say('h_gaps')}", "", say("gaps_intro"), ""] + [f"- {nt.text}" for nt in a.notes if nt.dimension == "evidence"] + [""]
    )

    core_best = str(mc["mean"].idxmax())
    b = res.loc[core_best]
    prob = float(mc.loc[core_best, "probability_positive"])
    conclusions = [
        say(
            "conclusion_none" if prob < 0.5 else "conclusion_some",
            best=core_best,
            npv=money(b.npv, lang),
            bcr=n(b.bcr, 2),
            prob=n(100 * prob, 0),
        )
    ]
    svb = sw[(sw.option == core_best) & (sw.layer == "core")].set_index("input").switching_value
    if prob < 0.5:
        p = a.parameters
        ways = []  # only the inputs whose switching value exists: none is printed as a blank
        if pd.notna(svb.get("excess_s", np.nan)):
            ways.append(say("switch_excess", sv=n(svb["excess_s"], 1), excess=n(whole.excess_s, 1), hi=n(whole.excess_ci90_high_s, 1)))
        if pd.notna(svb.get("car_value", np.nan)):
            ways.append(say("switch_car", sv=money(svb["car_value"], lang), central=money(p["car_value"].central, lang)))
        if pd.notna(svb.get("enforcement_year", np.nan)):
            ways.append(say("switch_enf", sv=money(svb["enforcement_year"], lang), central=money(p["enforcement_year"].central, lang)))
        if ways:
            conclusions.append(say("conclusion_switch", best=core_best, list=say("switch_join").join(ways)))
    e_best, e_prob = ext.loc[best], float(mce.loc[best, "probability_positive"])
    conclusions.append(
        say(
            "conclusion_ext_some" if e_best.npv > 0 else "conclusion_ext_none",
            best=best,
            npv=money(e_best.npv, lang),
            bcr=n(e_best.bcr, 2),
            prob=n(100 * e_prob, 0),
            list="; ".join(f"{i} {n(float(ext.loc[i, 'bcr']), 2)}" for i in ids),
        )
    )
    if len(worth):
        conclusions.append(say("conclusion_voi", list="; ".join(first_lower(label_of(x)) for x in worth.input.head(3))))
    if len(crit):
        effects = crit.set_index("label")[best]
        plus = [first_lower(k) for k, v in effects.items() if v in ("+", "++")]
        minus = [first_lower(k) for k, v in effects.items() if v in ("-", "--")]
        if plus or minus:
            conclusions.append(say("conclusion_criteria", best=best, plus="; ".join(plus) or "—", minus="; ".join(minus) or "—"))
    for row in alts.itertuples():
        conclusions.append(say("conclusion_alt", id=row.alternative, label=row.label, places=n(row.places, 0), secs=n(row.breakeven_seconds_per_peak_passage, 1),
                               secs_all=n(row.breakeven_seconds_per_passage, 1)))  # fmt: skip
    conclusions.append(say("conclusion_data"))
    lead = [s_ + "." for s_ in problem.split(". ")[:3:2]]  # the width, and the measured time
    summary = [f"## {say('h_summary')}", ""] + [f"- {c.rstrip('.')}." for c in lead + conclusions] + [""]
    concl_block = [f"## {say('h_conclusions')}", ""] + [f"{i}. {c}" for i, c in enumerate(conclusions, 1)] + [""]

    src_block = [f"## {say('h_sources')}", ""] + [f"- {s_}" for s_ in a.references] + [""]
    out += summary + problem_block + opts + fe + cba + crit_block + alt_block + gaps_block + concl_block + src_block
    return "\n".join(out).rstrip("\n") + "\n"


def write(r: Run) -> None:
    (r.case.results_dir / "appraisal.md").write_text(build(r), encoding="utf-8")
