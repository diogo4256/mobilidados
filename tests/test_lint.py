"""The letter linter: deterministic checks for drafts addressed to public bodies."""

import pytest

from mobilidados.lint import lint_text


def test_lint_flags_the_known_failure_modes():
    draft = (
        "Sempre que passa um autocarro há problemas.\n"
        "Sei que a largura pode ser intencional.\n"
        "O manual diz «a largura mínima obrigatória é de 7 m».\n"
    )
    rules = {i.rule for i in lint_text(draft, "pt")}
    assert {"generalisation", "concession", "quotation", "normative_word"} <= rules
    assert lint_text("Quando passa um autocarro e vem um carro em sentido contrário, o carro recua.", "pt") == []


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("As normas de desenho exigem 6,5 m.", "pt"),
        ("O manual fixa regras para a largura.", "pt"),
        ("As larguras obrigatórias não são cumpridas.", "pt"),
        ("Ficam abaixo dos mínimos legais.", "pt"),
        ("The regulations require 6.5 m.", "en"),
    ],
)
def test_lint_flags_normative_words_in_the_plural_too(text, lang):
    assert [i.rule for i in lint_text(text, lang)] == ["normative_word"]


def test_lint_flags_impossible_in_the_plural_too():
    assert [i.rule for i in lint_text("Cruzamentos impossíveis.", "pt")] == ["generalisation"]
