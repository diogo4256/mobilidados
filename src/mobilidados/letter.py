"""A first draft of a letter to a public body, written from a case's findings ledger (``mobilidados draft``).

The draft follows docs/writing-to-public-bodies.md: one topic per letter; the facts first, grouped by what they
rest on (measured in official data, written in an official document, estimated from them), each with the id of its
finding in the ledger so the recipient, and ``mobilidados check-claims``, can trace it; the assumptions the
estimates use, declared as such; one request; the evidence attached, with points where a technician can measure.

Nothing is computed here: every sentence about the street is a ledger statement copied as it is, so the letter
cannot say more than the ledger does. What only the sender knows (name, address, recipient, date) is left as
``[placeholders]``. The draft is linted (``mobilidados.lint``) before it is written; the ledger statements are
worded to pass, and a statement that does not is reported rather than silently changed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Case, MobilidadosError
from .i18n import num, t
from .lint import Issue, lint_text

# The findings each topic's letter is built from, in the order they are told. Findings these rest on (their
# ``sources`` that are finding ids) are added: documents to the documents section, assumptions to the assumptions.
TOPICS: dict[str, list[str]] = {
    "buses": [
        "free_width",
        "traffic",
        "transit",
        "width_budget",
        "encounters",
        "delay",
        "delay_seconds",
        "area_pattern",
        "standard_*",
        "without_parking",
        "parking_removed",
    ],
    "sidewalks": ["sidewalks", "sidewalks_law", "sidewalks_narrow", "sidewalks_to_check", "sidewalks_area"],
}
SECTIONS = {"M": "measured", "D": "documents", "I": "estimates"}


def load_findings(case: Case) -> list[dict[str, Any]]:
    path = case.results_dir / "findings.json"
    if not path.exists():
        raise MobilidadosError(f"{path} not found: run `mobilidados run {case.root}` first")
    return list(json.loads(path.read_text(encoding="utf-8"))["findings"])


def _matches(fid: str, pattern: str) -> bool:
    return fid.startswith(pattern[:-1]) if pattern.endswith("*") else fid == pattern


def select(findings: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
    """The topic's findings present in the ledger, in the topic's order, plus the findings they rest on."""
    if topic not in TOPICS:
        raise MobilidadosError(f"unknown topic {topic!r}; the topics are {sorted(TOPICS)}")
    by_id = {f["id"]: f for f in findings}
    chosen: list[str] = []
    for pattern in TOPICS[topic]:
        chosen += [f["id"] for f in findings if _matches(f["id"], pattern) and f["id"] not in chosen]
    stack = list(chosen)
    while stack:  # what the chosen findings rest on, followed through the ledger
        for sid in by_id[stack.pop()].get("sources", []):
            if sid in by_id and sid not in chosen:
                chosen.append(sid)
                stack.append(sid)
    return [by_id[i] for i in chosen if by_id[i]["grade"] != "NE"]


def topics_available(findings: list[dict[str, Any]]) -> list[str]:
    """The topics with at least one finding of their own in the ledger (not only a finding they rest on)."""
    ids = [f["id"] for f in findings]
    return [k for k, pats in TOPICS.items() if any(_matches(i, p) for p in pats for i in ids)]


def check_points(case: Case, topic: str) -> list[str]:
    """Places where a technician can measure, one line each, from the tables the run wrote."""
    lang = case.lang
    tables = case.results_dir / "tables"
    lines = []
    if topic == "buses" and (tables / "check_points.csv").exists():
        for p in pd.read_csv(tables / "check_points.csv").itertuples():
            lines.append(
                t("letter.point_free", lang, s=num(p.s_m, lang, 0), lat=f"{p.lat:.6f}", lon=f"{p.lon:.6f}", w=num(p.free_width_m, lang))
            )
    if topic == "sidewalks" and (tables / "sidewalk_narrow_sections.csv").exists():
        sides = case.config.street.sides
        sections = pd.read_csv(tables / "sidewalk_narrow_sections.csv")
        for p in sections[sections.below.astype(bool)].itertuples():
            lines.append(
                t(
                    "letter.point_sidewalk",
                    lang,
                    side=sides[p.side],
                    a=num(p.s_from, lang, 0),
                    b=num(p.s_to, lang, 0),
                    lat=f"{p.lat:.6f}",
                    lon=f"{p.lon:.6f}",
                    w=num(p.width_min_m, lang),
                )
            )
    return lines


def compose(case: Case, topic: str, ask: str = "review") -> str:
    lang = case.lang

    def say(key: str, **kw: Any) -> str:
        return t(f"letter.{key}", lang, **kw)

    findings = load_findings(case)
    chosen = select(findings, topic)
    if not chosen:
        have = topics_available(findings)
        raise MobilidadosError(f"the ledger has no findings for the topic {topic!r}; it has findings for {have or 'no topic'}")
    info = case.config.case
    street = case.config.street.name
    out = [
        say("comment"),
        "",
        say("sender"),
        "",
        say("recipient"),
        "",
        say("place_date"),
        "",
        f"**{say('subject_label')}** {say(f'subject_{topic}', street=street)}",
        "",
        say("salutation"),
        "",
        say(f"opening_{topic}", street=street, title=info.title),
        "",
    ]
    for grade, section in SECTIONS.items():
        items = [f for f in chosen if f["grade"] == grade]
        if items:
            out += [f"### {say(section)}", ""]
            out += [f"- {f['statement']} {say('ref', id=f['id'])}" for f in items]
            out.append("")
    assumed = [f for f in chosen if f["grade"] == "P"]
    if assumed:
        out += [f"### {say('assumptions')}", "", say("assumptions_intro"), ""]
        out += [f"- {f['statement']} {say('ref', id=f['id'])}" for f in assumed]
        out.append("")
    out += [f"### {say('request')}", "", say(f"ask_{topic}_{ask}", street=street), ""]
    points = check_points(case, topic)
    out += [f"### {say('attachments')}", "", f"- {say('attach_ledger')}", f"- {say('attach_figures')}"]
    if (case.results_dir / "screening.md").exists():
        out.append(f"- {say('attach_screening')}")
    if points:
        out += [f"- {say(f'attach_points_{topic}')}", *[f"  - {p}" for p in points]]
    out += ["", say("closing"), "", say("signature"), ""]
    return "\n".join(out)


ASKS = ("review", "documents")


def write(case: Case, topic: str, ask: str = "review", out: Path | None = None) -> tuple[Path, list[Issue]]:
    """Write the draft (default ``results/letter-<topic>.md``) and return where, with what the linter flags in it."""
    if ask not in ASKS:
        raise MobilidadosError(f"unknown request {ask!r}; the requests are {list(ASKS)}")
    text = compose(case, topic, ask)
    path = out or case.results_dir / f"letter-{topic}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path, lint_text(text, case.lang)
