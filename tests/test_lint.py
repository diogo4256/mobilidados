"""The letter linter: deterministic checks for drafts addressed to public bodies."""

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
