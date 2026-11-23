"""``mobilidados check-doc``: a document's numbers against the case's results, without AI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from mobilidados import doccheck


@pytest.fixture
def results(tmp_path: Path) -> Path:
    tables = tmp_path / "results" / "tables"
    tables.mkdir(parents=True)
    pd.DataFrame({"layer": ["core", "extended"], "option": ["C", "C"], "npv": [-22197.2, 25766.5], "bcr": [0.43, 1.823]}).to_csv(
        tables / "appraisal_results.csv", index=False
    )
    pd.DataFrame({"option": ["C"], "input": ["offpeak_s"], "npv_at_low": [707.3]}).to_csv(tables / "appraisal_tornado.csv", index=False)
    return tmp_path / "results"


def spec(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "doc_check.toml"
    p.write_text(body, encoding="utf-8")
    return p


def test_numbers_are_read_in_each_language_with_the_rounding_they_show():
    pt = doccheck.numbers("negativo: −22 200 €; rácio 1,82; 86% dos casos; 530 000 viagens", "pt")
    assert [(p.value, p.step) for p in pt] == [(-22200, 100), (1.82, 0.01), (86, 1), (530000, 10000)]
    assert pt[0].signed
    assert not pt[1].signed
    en = doccheck.numbers("pays: +€25,800 (BCR 1.82); see [link](https://x.org/a-2024-5)", "en")
    assert [(p.value, p.step) for p in en] == [(25800, 100), (1.82, 0.01)]  # nothing read from the link


def test_a_printed_number_is_explained_at_its_precision_scale_and_sign():
    p = doccheck.numbers("+700 €", "pt")[0]
    assert p.explained_by(707.3)
    assert not p.explained_by(-707.3)  # printed with a sign: the sign counts
    assert doccheck.numbers("25,8", "pt")[0].explained_by(25766.5)  # thousands of euros
    assert doccheck.numbers("86%", "pt")[0].explained_by(0.8611)  # a share as a percentage
    assert not doccheck.numbers("26,8", "pt")[0].explained_by(25766.5)


def test_expressions_resolve_cells_and_refuse_anything_else(results: Path):
    assert doccheck.resolve(
        "{appraisal_results.csv:npv[layer=extended,option=C]} - {appraisal_tornado.csv:npv_at_low[option=C,input=offpeak_s]}", results
    ) == pytest.approx(25059.2)
    with pytest.raises(ValueError, match="selects 2 rows"):
        doccheck.resolve("{appraisal_results.csv:npv[option=C]}", results)
    with pytest.raises(ValueError, match="only references and arithmetic"):
        doccheck.resolve("__import__('os')", results)


def test_a_stale_or_vanished_claim_fails_and_a_current_one_passes(tmp_path: Path, results: Path):
    s = spec(
        tmp_path,
        """
[[claims]]
id = "npv"
value = "{appraisal_results.csv:npv[layer=extended,option=C]}"
pt = 'é positivo: (\\+[\\d ]+) €'

[[claims]]
id = "without_offpeak"
value = "{appraisal_tornado.csv:npv_at_low[option=C,input=offpeak_s]}"
pt = 'sem atraso fora da ponta, (\\+[\\d ]+) €'
""",
    )
    ok = doccheck.check("é positivo: +25 800 €; sem atraso fora da ponta, +700 €.", "pt", results, [], s)
    assert not ok.failed
    # the flaw this check was written for: a headline kept after the model moved, and a condition dropped
    stale = doccheck.check("é positivo: +26 800 €, mesmo sem atraso fora da hora de ponta.", "pt", results, [], s)
    assert [(c.id, status) for c, status, _, _ in stale.failed] == [("npv", "wrong"), ("without_offpeak", "missing")]


def test_numbers_no_table_explains_are_listed_and_languages_are_compared(tmp_path: Path, results: Path):
    s = spec(tmp_path, "ignore_values = [2025]\n")
    rep = doccheck.check("VAL −22 200 € em 2025; rácio 1,82; e 4 321 € sem fonte.", "pt", results, [], s)
    assert [p.raw for p in rep.orphans] == ["4 321"]
    only_pt, only_en = doccheck.compare_languages("VAL −22 200 €, 86%", "pt", "NPV −€22,200, 87%", "en", [])
    assert [p.raw for p in only_pt] == ["86"]
    assert [p.raw for p in only_en] == ["87"]
