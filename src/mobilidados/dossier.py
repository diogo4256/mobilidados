"""A case's dossier (``dossier.md``): its Annex C, the facts it cites, written from the ledger (``mobilidados dossier``).

A dossier is written by hand and sent on its own, so it cannot point to the case's files. The facts it cites
(``[M `free_width`]``) are copied, with their method and caveats, into its Annex C, together with the facts those rest
on (their ``sources`` that are finding ids). This module writes that annex, so that after a re-run changes the ledger
the dossier can be brought back in line; ``tests/test_cases.py`` checks that it is.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import Case, MobilidadosError
from .i18n import t

CITED = re.compile(r"\[[MDIP] ([^\]]+)\]")


def split(text: str, lang: str) -> tuple[str, str]:
    """A dossier's text and its Annex C (from its heading on, ``""`` if there is none), in the case's language."""
    heading = "\n## " + t("dossier.annex", lang).split(":")[0]
    body, _, rest = text.partition(heading)
    return body, (heading.lstrip("\n") + rest) if rest else ""


def cited(body: str) -> list[str]:
    """Finding ids cited in the text, in the order they first appear."""
    out: list[str] = []
    for group in CITED.findall(body):
        for fid in (x.strip(" `") for x in group.split(",")):
            if fid not in out:
                out.append(fid)
    return out


def annex(body: str, findings: dict[str, dict[str, Any]], lang: str) -> str:
    """Annex C for a dossier whose text (without the annex) is ``body``."""
    order = cited(body)
    missing = [f for f in order if f not in findings]
    if missing:
        raise MobilidadosError(f"the dossier cites findings the ledger does not have: {missing}")
    i = 0
    while i < len(order):  # what the cited facts rest on
        order += [s for s in findings[order[i]].get("sources", []) if s in findings and s not in order]
        i += 1
    lines = ["## " + t("dossier.annex", lang), "", t("dossier.annex_intro", lang), ""]
    for fid in order:
        f = findings[fid]
        lines.append(f"- **[{f['grade']}] `{fid}`** {f['statement']}")
        if f.get("method"):
            lines[-1] += "  "
            lines.append(f"  *{t('dossier.method', lang)}:* {f['method']}")
        if f.get("caveat"):
            lines[-1] += "  "
            lines.append(f"  *{t('dossier.caveat', lang)}:* {f['caveat']}")
    return "\n".join(lines) + "\n"


def write(case: Case) -> Path:
    """Rewrite the Annex C of ``<case>/dossier.md`` from ``results/findings.json``; the rest is left as written."""
    path = case.root / "dossier.md"
    if not path.exists():
        raise MobilidadosError(f"{path} not found: a dossier is written by hand; this command only writes its Annex C")
    findings_path = case.results_dir / "findings.json"
    if not findings_path.exists():
        raise MobilidadosError(f"{findings_path} not found: run `mobilidados run {case.root}` first")
    findings = {f["id"]: f for f in json.loads(findings_path.read_text(encoding="utf-8"))["findings"]}
    body = split(path.read_text(encoding="utf-8"), case.lang)[0].rstrip("\n") + "\n"
    path.write_text(body + "\n" + annex(body, findings, case.lang), encoding="utf-8")
    return path
