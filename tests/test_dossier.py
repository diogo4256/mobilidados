"""The Annex C of a dossier: the facts its text cites and those they rest on, copied from the ledger."""

import json

import pytest

from mobilidados.config import Case, MobilidadosError
from mobilidados.dossier import annex, cited, split, write

LEDGER = {
    "free_width": {"id": "free_width", "grade": "M", "statement": "4,90 m.", "sources": ["cartography"], "method": "Perfis.", "caveat": ""},
    "width_budget": {
        "id": "width_budget",
        "grade": "I",
        "statement": "Folga de −0,10 m.",
        "sources": ["free_width", "mirrors"],
        "method": "",
        "caveat": "Pressupõe espelhos.",
    },
    "mirrors": {"id": "mirrors", "grade": "P", "statement": "2,90 m (pressuposto).", "sources": [], "method": "", "caveat": ""},
    "length": {"id": "length", "grade": "M", "statement": "209 m.", "sources": [], "method": "", "caveat": ""},
}


def test_cited_ids_in_order_of_first_appearance():
    assert cited("A [I `width_budget`, `free_width`]. B [M `free_width`].") == ["width_budget", "free_width"]


def test_the_annex_holds_the_cited_facts_then_what_they_rest_on_word_for_word():
    text = annex("A largura [I `width_budget`].", LEDGER, "pt")
    assert [line.split("`")[1] for line in text.splitlines() if line.startswith("- **[")] == ["width_budget", "free_width", "mirrors"]
    assert "- **[I] `width_budget`** Folga de −0,10 m.  \n  *Reservas:* Pressupõe espelhos." in text
    assert "*Método:* Perfis." in text
    assert "length" not in text  # not cited, and nothing cited rests on it


def test_a_citation_the_ledger_does_not_have_is_an_error():
    with pytest.raises(MobilidadosError, match=r"does not have: \['nope'\]"):
        annex("[M `nope`]", LEDGER, "pt")


def test_write_replaces_only_the_annex(make_case):
    case = Case.load(make_case())
    case.results_dir.mkdir(parents=True)
    (case.results_dir / "findings.json").write_text(json.dumps({"findings": list(LEDGER.values())}), encoding="utf-8")
    (case.root / "dossier.md").write_text("# T\n\nText [M `length`].\n\n## Annex C: old\n\n- junk\n", encoding="utf-8")
    write(case)
    text = (case.root / "dossier.md").read_text(encoding="utf-8")
    assert text.startswith("# T\n\nText [M `length`].\n\n## Annex C: facts cited\n")  # in the case's language (en)
    assert "junk" not in text
    assert "`length`** 209 m." in text
    write(case)
    assert (case.root / "dossier.md").read_text(encoding="utf-8") == text  # idempotent


def test_a_case_without_a_dossier_says_one_is_written_by_hand(make_case):
    with pytest.raises(MobilidadosError, match="written by hand"):
        write(Case.load(make_case()))


@pytest.mark.parametrize(("lang", "heading"), [("pt", "## Anexo C"), ("en", "## Annex C")])
def test_the_annex_is_found_by_its_heading_in_the_case_language(lang, heading):
    body, rest = split(f"# T\n\nx\n\n{heading}: y\n- z\n", lang)
    assert body == "# T\n\nx\n"
    assert rest.startswith(heading)
    assert split("# T\n", lang) == ("# T\n", "")
