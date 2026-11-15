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


@pytest.mark.parametrize("case_dir", [c for c in CASES if (c / "dossier.md").exists()], ids=lambda p: p.name)
def test_a_dossier_says_nothing_the_results_do_not(case_dir):
    """A dossier is written by hand, so it is held to its results: lint-clean, every finding it cites exists, and every
    number with a unit is one the ledger gives, or a result table the dossier links to."""
    case = Case.load(case_dir)
    text = (case_dir / "dossier.md").read_text(encoding="utf-8")
    assert lint_text(text, case.lang) == []
    findings = json.loads((case.results_dir / "findings.json").read_text(encoding="utf-8"))["findings"]
    cited = set(re.findall(r"\[[MDIP] ([^\]]+)\]", text))
    ids = {i.strip(" `") for group in cited for i in group.split(",")}
    assert ids <= {f["id"] for f in findings}
    ledger = (case.results_dir / "findings.md").read_text(encoding="utf-8")
    # a number that is not in the ledger must come from a table the dossier links to
    linked = set(re.findall(r"results/tables/([\w-]+\.csv)", text))
    tables = " ".join((case.results_dir / "tables" / name).read_text(encoding="utf-8") for name in linked)
    printed = {x.lstrip("+−-") for x in UNIT.findall(ledger)}
    printed |= {p for x in printed for p in x.split("–")}  # each end of a range the ledger gives

    def tabled(x: str) -> str:  # 122.0 in a table is the 122 a text prints; 4.87 is 4,87
        return x.rstrip("0").rstrip(".").replace(".", ",") if "." in x else x

    known = printed | {tabled(x) for x in re.findall(r"\d+\.\d+|\d+", tables)}
    for x in {x.lstrip("+−-") for x in UNIT.findall(text)}:
        assert x in known or all(p in known for p in x.split("–")), f"{x} is not in the results"
