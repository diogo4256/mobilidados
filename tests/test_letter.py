"""The letter draft (``mobilidados draft``): built from the ledger only, one topic, assumptions declared, lint-clean."""

import json
import re
from pathlib import Path

import pytest

from mobilidados.cli import main
from mobilidados.config import Case, MobilidadosError
from mobilidados.i18n import t
from mobilidados.letter import compose, select, write
from mobilidados.lint import lint_text

CASES = sorted(p.parent.parent for p in (Path(__file__).parent.parent / "cases").glob("*/results/findings.json"))


def finding(fid, grade, statement="x", sources=()):
    return {"id": fid, "grade": grade, "statement": statement, "sources": list(sources)}


def test_select_adds_what_the_findings_rest_on_and_leaves_out_gaps_and_other_topics():
    ledger = [
        finding("length", "M"),
        finding("free_width", "M", sources=["cartography"]),
        finding("vehicle_bus_body", "D"),
        finding("vehicle_bus_mirrors", "P"),
        finding("width_budget", "I", sources=["free_width", "vehicle_bus_body", "vehicle_bus_mirrors"]),
        finding("standard_a", "D"),
        finding("sidewalks", "M"),
        finding("gap_1", "NE"),
    ]
    ids = [f["id"] for f in select(ledger, "buses")]
    assert ids == ["free_width", "width_budget", "standard_a", "vehicle_bus_body", "vehicle_bus_mirrors"]
    assert [f["id"] for f in select(ledger, "sidewalks")] == ["sidewalks"]
    with pytest.raises(MobilidadosError, match="unknown topic"):
        select(ledger, "trams")


def write_ledger(case: Case, findings) -> None:
    case.results_dir.mkdir(parents=True, exist_ok=True)
    (case.results_dir / "findings.json").write_text(json.dumps({"findings": findings}), encoding="utf-8")


def test_the_draft_copies_statements_groups_them_and_declares_assumptions(make_case):
    case = Case.load(make_case())
    write_ledger(
        case,
        [
            finding("free_width", "M", "A largura livre tem mediana de 4,90 m."),
            finding("vehicle_bus_mirrors", "P", "Largura com espelhos assumida em 2,90 m."),
            finding("width_budget", "I", "Folga de −0,10 m.", sources=["free_width", "vehicle_bus_mirrors"]),
        ],
    )
    text = compose(case, "buses")
    measured, assumed, estimated = (text.index(s) for s in ("A largura livre", "Largura com espelhos", "Folga de"))
    assert measured < estimated < assumed  # the assumptions come after the estimates that use them, under their own heading
    assert f"### {t('letter.assumptions', case.lang)}" in text
    assert t("letter.ref", case.lang, id="width_budget") in text
    assert t("letter.signature", case.lang) in text
    assert "Test street" in text


def test_a_topic_without_findings_is_an_error_that_names_the_topics_there_are(make_case):
    case = Case.load(make_case())
    write_ledger(case, [finding("free_width", "M")])
    with pytest.raises(MobilidadosError, match=r"no findings for the topic 'sidewalks'.*\['buses'\]"):
        compose(case, "sidewalks")


def test_a_case_that_was_never_run_says_so(make_case):
    with pytest.raises(MobilidadosError, match="mobilidados run"):
        compose(Case.load(make_case()), "buses")


@pytest.mark.parametrize("case_dir", CASES, ids=lambda p: p.name)
@pytest.mark.parametrize("ask", ["review", "documents"])
def test_every_committed_case_drafts_a_letter_that_passes_lint(case_dir, ask, tmp_path):
    case = Case.load(case_dir)
    ledger = {f["id"]: f for f in json.loads((case.results_dir / "findings.json").read_text(encoding="utf-8"))["findings"]}
    for topic in ("buses", "sidewalks"):
        path, issues = write(case, topic, ask, tmp_path / f"{topic}.md")
        text = path.read_text(encoding="utf-8")
        assert issues == [] == lint_text(text, case.lang)
        cited = re.findall(r"`([a-z0-9_]+)`\)", text)
        assert cited
        assert set(cited) <= set(ledger)
        for fid in cited:  # each statement is the ledger's, word for word
            assert ledger[fid]["statement"] in text
        assert all(ledger[f]["grade"] != "NE" for f in cited)


def test_draft_command_writes_the_letter_and_exits_0_when_lint_is_clean(make_case, tmp_path, capsys):
    root = make_case()
    write_ledger(Case.load(root), [finding("free_width", "M", "A largura livre tem mediana de 4,90 m.")])
    out = tmp_path / "carta.md"
    assert main(["draft", str(root), "--out", str(out)]) == 0
    assert out.exists()
    assert "check-claims" in capsys.readouterr().out
