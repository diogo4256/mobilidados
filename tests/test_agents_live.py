"""End-to-end checks of the AI tools against the real API. Skipped unless credentials are configured.

Run with:  ANTHROPIC_API_KEY=... pytest -m live
           MOBILIDADOS_MANUAL_PDF=/path/to/manual_de_espaco_publico.pdf  (for the extraction test)
Each test makes a few small requests (one page / one short draft).
"""

import os
from pathlib import Path

import pytest

pytest.importorskip("anthropic")
pytestmark = pytest.mark.live
if not os.environ.get("ANTHROPIC_API_KEY"):
    pytest.skip("ANTHROPIC_API_KEY not set", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases" / "lisboa-rua-ricardo-jorge"


def test_claim_checker_catches_an_overstatement():
    from mobilidados.agents.claim_checker import build_corpus, run_agent, verify
    from mobilidados.config import Case

    draft = (
        "A faixa livre entre as faixas de estacionamento tem uma mediana de 4,90 m.\n"
        "Todos os dias, sempre que passam dois autocarros, ficam bloqueados.\n"
    )
    corpus, findings = build_corpus(Case.load(CASE), [])
    claims = verify(run_agent(draft, corpus), draft, corpus, findings)
    by_text = {c["text"][:20]: c["verdict"] for c in claims}
    assert any(v == "supported" for k, v in by_text.items() if k.startswith("A faixa livre"))
    assert any(v in {"overstated", "unsupported", "needs_human"} for k, v in by_text.items() if "autocarros" in k or k.startswith("Todos"))


@pytest.mark.skipif(not os.environ.get("MOBILIDADOS_MANUAL_PDF"), reason="MOBILIDADOS_MANUAL_PDF not set")
def test_extractor_reads_the_two_way_profile_drawing():
    from mobilidados.agents.standards_extractor import check, ocr, read_page, render_png, text_layer

    pdf = Path(os.environ["MOBILIDADOS_MANUAL_PDF"])
    reading, _ = read_page(pdf, 194, render_png(pdf, 194))
    values = {round(v.value_m, 2) for v in reading.values}
    assert {3.00, 0.40} <= values
    assert any(abs(t.total_m - 6.80) < 0.01 for t in reading.totals)
    result = check(reading, text_layer(pdf, 194), ocr(pdf, 194))
    assert all(t["sum_checks"] for t in result["totals"])
