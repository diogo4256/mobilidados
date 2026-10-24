"""Case configuration, catalogues, and (when the cached sources are present) bit-for-bit reproduction of the
committed results of every case under ``cases/``."""

import json
from pathlib import Path

import pandas as pd
import pytest

from streetfit import standards
from streetfit.config import Case
from streetfit.provenance import Lock

ROOT = Path(__file__).resolve().parents[1]
CASES = sorted(p.parent for p in (ROOT / "cases").glob("*/case.toml"))


@pytest.mark.parametrize("case_dir", CASES, ids=lambda p: p.name)
def test_case_config_is_complete(case_dir):
    case = Case.load(case_dir)
    for sid in case.source_ids():
        src = case.source(sid)
        assert src["kind"] and src.get("licence"), f"{sid}: every source needs a kind and a licence statement"
    for rid in case.section("standards").get("compare", []):
        standards.reference(rid)
    assert case.blocks == sorted(case.blocks, key=lambda b: b.start)


def test_standards_catalogue_is_well_formed():
    cat = standards.catalogue()
    for r in cat["references"]:
        assert r["document"] in cat["documents"]
        assert r["kind"] in {"reference_profile", "conditional_value", "secondary_citation"}
        assert r["scope"] and r["quote"] and r["page"] and r["pdf_page"]


@pytest.mark.data
@pytest.mark.parametrize("case_dir", CASES, ids=lambda p: p.name)
def test_results_reproduce(case_dir, tmp_path):
    """Re-run the case from the locked cache into a scratch copy and compare every table with the committed one."""
    case = Case.load(case_dir)
    if not case.lock_path.exists() or any(s != "ok" for *_, s in Lock(case.lock_path).verify(case.raw_dir)):
        pytest.skip("cached sources missing or different from the lock (run `streetfit fetch`)")
    from streetfit.pipeline import run

    scratch = tmp_path / case_dir.name
    scratch.mkdir()
    text = (case_dir / "case.toml").read_text(encoding="utf-8")
    text = text.replace('extends = "../../', f'extends = "{ROOT.as_posix()}/', 1)
    (scratch / "case.toml").write_text(text, encoding="utf-8")
    (scratch / "data").mkdir()
    (scratch / "data" / "raw").symlink_to(case.raw_dir)
    (scratch / "sources.lock.json").write_text(case.lock_path.read_text())
    run(Case.load(scratch), offline=True, log=lambda *_: None)
    committed = case.results_dir / "tables"
    for f in sorted(committed.glob("*.csv")):
        new = pd.read_csv(scratch / "results" / "tables" / f.name)
        pd.testing.assert_frame_equal(new, pd.read_csv(f), check_exact=False, rtol=0, atol=1e-9, obj=f.name)
    a = json.loads((case.results_dir / "findings.json").read_text())["findings"]
    b = json.loads((scratch / "results" / "findings.json").read_text())["findings"]
    assert a == b
