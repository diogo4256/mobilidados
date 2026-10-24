"""Width budget, text matching and the letter linter."""

import pytest

from streetfit import envelope
from streetfit.lint import lint_text
from streetfit.textmatch import contains, numbers, quote_near, value_in_text


def test_width_budget_mirror_rule():
    v = envelope.load_vehicles()
    bus, car = v["carris_man_city_gold"], v["car_typical"]
    assert envelope.widths(bus, bus, False) == pytest.approx(5.00)
    assert envelope.widths(bus, bus, True) == pytest.approx(5.80)
    # a bus mirror passes above a car: only the car's mirrors count
    assert envelope.widths(bus, car, True) == pytest.approx(2.50 + 2.05)
    df = envelope.width_budget({"median": 4.90}, v, [["carris_man_city_gold", "carris_man_city_gold"]])
    assert df[~df.mirrors].margin_m.iloc[0] == pytest.approx(-0.10)


def test_vehicle_catalogue_is_graded():
    for v in envelope.load_vehicles().values():
        assert v.grade_body in {"M", "D", "I", "P"} and v.grade_mirrors in {"M", "D", "I", "P"}
        assert v.source_body and v.source_mirrors


def test_text_matching_is_accent_and_decimal_tolerant():
    assert contains("Onde não circulem  autocarros,\numa largura", "onde nao circulem autocarros, uma largura")
    assert contains("desne-\ncessários", "desnecessários")
    assert numbers("faixa livre 4,90 m e 5.68 m") == [4.90, 5.68]
    assert value_in_text(6.8, "total 6,80 m") and value_in_text(3.0, "3.00 m") and not value_in_text(3.0, "13.00 m")
    assert not value_in_text(3.0, "a largura é de 3,25 m")  # regression: "3" inside "3,25" is not 3.00
    lines = ["a", "b", "Verkehrsraum von 6,50 m", "d"]
    assert quote_near(lines, "verkehrsraum von 6,50", 3) and not quote_near(lines, "nicht da", 3)


def test_lint_flags_the_known_failure_modes():
    draft = (
        "Sempre que passa um autocarro há problemas.\n"
        "Sei que a largura pode ser intencional.\n"
        "O manual diz «a largura mínima obrigatória é de 7 m».\n"
    )
    rules = {i.rule for i in lint_text(draft, "pt")}
    assert {"generalisation", "concession", "quotation", "normative_word"} <= rules
    assert lint_text("Quando passa um autocarro e vem um carro em sentido contrário, o carro recua.", "pt") == []
