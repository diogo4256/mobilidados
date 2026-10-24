"""The deterministic halves of the AI tools, with the model's output faked (no API calls)."""

import pytest

pytest.importorskip("anthropic")
pytest.importorskip("pydantic")

from streetfit.agents.claim_checker import Claim, ClaimReport, Corpus, Evidence, verify
from streetfit.agents.standards_extractor import DerivedTotal, PageReading, WidthValue, check

FINDINGS = {
    "free_width": {
        "id": "free_width",
        "grade": "M",
        "statement": "faixa livre mediana 4,90 m",
        "caveat": "",
        "values": {"median_m": 4.9, "min_m": 4.78},
    }
}


def corpus():
    c = Corpus()
    c.add("ledger", "[M] free_width: faixa livre mediana 4,90 m")
    c.add("manual", "linha 1\nonde não circulem autocarros, uma largura de 2,75 m por via\nlinha 3")
    return c


def claim(**kw):
    base = {
        "text": "a faixa livre é de 4,90 m",
        "kind": "number",
        "verdict": "supported",
        "finding_ids": ["free_width"],
        "evidence": [Evidence(doc_id="ledger", line=0, quote="faixa livre mediana 4,90 m")],
        "problem": "",
        "suggestion": "",
    }
    return Claim(**(base | kw))


def test_supported_claim_passes():
    out = verify(ClaimReport(claims=[claim()]), "Na rua, a faixa livre é de 4,90 m.", corpus(), FINDINGS)
    assert out[0]["verdict"] == "supported"
    assert out[0]["checks"] == []


def test_wrong_number_is_downgraded():
    out = verify(ClaimReport(claims=[claim(text="a faixa livre é de 4,50 m")]), "a faixa livre é de 4,50 m", corpus(), FINDINGS)
    assert out[0]["verdict"] == "needs_human"
    assert "numbers not in the cited findings" in out[0]["checks"][0]


def test_invented_evidence_is_caught():
    bad = claim(evidence=[Evidence(doc_id="manual", line=2, quote="a largura mínima é 7 m")])
    out = verify(ClaimReport(claims=[bad]), "a faixa livre é de 4,90 m", corpus(), FINDINGS)
    assert out[0]["verdict"] == "needs_human"
    assert any("evidence quote not found" in c for c in out[0]["checks"])


def test_paraphrase_in_quotes_is_flagged_without_the_model():
    draft = "O manual diz «só se admite 2,75 m quando não há autocarros nenhuns»."
    out = verify(ClaimReport(claims=[]), draft, corpus(), FINDINGS)
    assert out
    assert out[0]["kind"] == "quotation"
    assert out[0]["verdict"] == "needs_human"


def test_corpus_search_is_accent_insensitive():
    hits = corpus().search("nao circulem autocarros")
    assert hits
    assert hits[0]["doc_id"] == "manual"
    assert hits[0]["line"] == 2


def test_extraction_values_are_cross_checked():
    reading = PageReading(
        page_title="Perfil",
        values=[
            WidthValue(
                value_m=3.25, printed="3.25", measures="lane", applies_to="two-way", conditions="", location="caption", page_quote=""
            ),
            WidthValue(
                value_m=0.40, printed="0.40", measures="extra width", applies_to="two-way", conditions="", location="drawing", page_quote=""
            ),
            WidthValue(
                value_m=3.00, printed="3.00 m", measures="lane", applies_to="two-way", conditions="", location="drawing", page_quote=""
            ),
        ],
        totals=[DerivedTotal(label="between strips", components_m=[0.4, 3.0, 3.0, 0.4], total_m=6.8)],
    )
    r = check(reading, text="a largura recomendada é de 3,25 m", ocr_text="0.40 | 3.00m | 3.00m | 0.40")
    status = [v["verified_by"] for v in r["values"]]
    assert status == ["text_layer", "ocr", "ocr"]
    assert r["totals"][0]["sum_checks"] is True
    wrong = check(PageReading(page_title="", values=[], totals=[DerivedTotal(label="x", components_m=[3.0, 3.0], total_m=6.8)]), "", None)
    assert wrong["totals"][0]["sum_checks"] is False
