"""Every case under ``cases/`` loads, and (when its cached sources are present) reproduces its committed results."""

import json
from pathlib import Path

import pandas as pd
import pytest

from mobilidados.config import Case
from mobilidados.provenance import Lock

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
    if any(s != "ok" for *_, s in Lock(case.lock_path).verify(case.raw_dir)):
        pytest.skip("cached sources missing or different from the lock (run `mobilidados fetch`)")
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
