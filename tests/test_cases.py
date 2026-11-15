"""Every case under ``cases/`` loads, and (when its cached sources are present) reproduces its committed results."""

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from mobilidados.config import Case
from mobilidados.lint import lint_text
from mobilidados.sources import check_cache

ROOT = Path(__file__).resolve().parents[1]
CASES = sorted(p.parent for p in (ROOT / "cases").glob("*/case.toml"))


@pytest.mark.parametrize("case_dir", CASES, ids=lambda p: p.name)
def test_case_loads(case_dir):
    case = Case.load(case_dir)  # validation is the test: unknown keys, missing values, dangling references
    assert case.lock_path.exists(), "a published case ships the lock of its reference run"


@pytest.mark.data
@pytest.mark.parametrize("case_dir", CASES, ids=lambda p: p.name)
def test_results_reproduce(case_dir, tmp_path):
    """Re-run the case from the locked cache into a scratch folder and compare every table, the findings and the
    recorded configuration with the committed ones."""
    case = Case.load(case_dir)
    differ = [f"{f or sid} ({s})" for sid, f, s in check_cache(case) if s != "ok"]
    assert not differ, f"the cache does not hold the locked sources, so the case cannot be re-run from it: {differ}"
    from mobilidados.pipeline import run

    run(Case.load(case_dir, results_dir=tmp_path), offline=True)
    committed = sorted(p.name for p in (case.results_dir / "tables").glob("*.csv"))
    assert committed == sorted(p.name for p in (tmp_path / "tables").glob("*.csv"))
    for name in committed:
        new, old = pd.read_csv(tmp_path / "tables" / name), pd.read_csv(case.results_dir / "tables" / name)
        pd.testing.assert_frame_equal(new, old, check_exact=False, rtol=0, atol=1e-9, obj=name)
    findings = [json.loads((d / "findings.json").read_text(encoding="utf-8"))["findings"] for d in (tmp_path, case.results_dir)]
    assert findings[0] == findings[1]
    assert (tmp_path / "config.json").read_text(encoding="utf-8") == (case.results_dir / "config.json").read_text(encoding="utf-8")


UNIT = re.compile(r"[+−-]?\d+(?:,\d+)?(?:–\d+(?:,\d+)?)?(?=\s?(?:m\b|%|s\b|km/h|lugares|encontros|viagens|veículos|perfis))")
ANNEX = "\n## Anexo C"


@pytest.mark.parametrize("case_dir", [c for c in CASES if (c / "dossier.md").exists()], ids=lambda p: p.name)
def test_a_dossier_stands_alone_and_says_nothing_the_results_do_not(case_dir):
    """A dossier is sent on its own, so it refers to no file of the case: its sources are cited, with where they are
    published, in Annex B, and the facts it cites are in its Annex C, copied from the ledger word for word. Its own text passes lint, and every number with a unit in it is a
    number the ledger gives, or one of the check points (``check_points.csv``) its Annex A lists."""
    case = Case.load(case_dir)
    text = (case_dir / "dossier.md").read_text(encoding="utf-8")
    body, annex = text.split(ANNEX)
    # citations may give where a source is published (Annex B); nothing may send the reader to the case's own files
    cited_sources = body.split("\n## Anexo B")[1]
    assert not re.search(r"\]\((?!results/figures/)|\.csv|\.json|findings\.md|mobilidados", text), "a link or a file name"
    assert not re.search(r"https?://", body.split("\n## Anexo B")[0] + annex), "an address outside the citations"
    assert re.search(r"https?://", cited_sources), "the sources are cited with where they are published"
    assert lint_text(body, case.lang) == []
    findings = {f["id"]: f for f in json.loads((case.results_dir / "findings.json").read_text(encoding="utf-8"))["findings"]}
    cited = {i.strip(" `") for group in re.findall(r"\[[MDIP] ([^\]]+)\]", body) for i in group.split(",")}
    in_annex = set(re.findall(r"^- \*\*\[[MDIP]\] `([^`]+)`\*\*", annex, flags=re.M))
    assert cited <= in_annex <= set(findings)
    for fid in in_annex:  # word for word
        f = findings[fid]
        assert f"`{fid}`** {f['statement']}" in annex
        assert not f["method"] or f"*Método:* {f['method']}" in annex
        assert not f["caveat"] or f"*Reservas:* {f['caveat']}" in annex
    ledger = (case.results_dir / "findings.md").read_text(encoding="utf-8")
    printed = {x.lstrip("+−-") for x in UNIT.findall(ledger)}
    printed |= {p for x in printed for p in x.split("–")}  # each end of a range the ledger gives
    points = pd.read_csv(case.results_dir / "tables" / "check_points.csv")
    known = printed | {f"{x:g}".replace(".", ",") for c in ("s_m", "free_width_m") for x in points[c]}
    known |= {f"{x:.2f}".replace(".", ",") for x in points.free_width_m}
    for x in {x.lstrip("+−-") for x in UNIT.findall(body)}:
        assert x in known or all(p in known for p in x.split("–")), f"{x} is not in the results"
