"""Deterministic text matching: accent-, case-, whitespace-, hyphenation- and decimal-separator-tolerant."""

from mobilidados.textmatch import contains, numbers, quote_near, value_in_text


def test_text_matching_is_accent_and_decimal_tolerant():
    assert contains("Onde não circulem  autocarros,\numa largura", "onde nao circulem autocarros, uma largura")
    assert contains("desne-\ncessários", "desnecessários")
    assert numbers("faixa livre 4,90 m e 5.68 m") == [4.90, 5.68]
    assert value_in_text(6.8, "total 6,80 m")
    assert value_in_text(3.0, "3.00 m")
    assert not value_in_text(3.0, "13.00 m")
    assert not value_in_text(3.0, "a largura é de 3,25 m")  # regression: "3" inside "3,25" is not 3.00
    lines = ["a", "b", "Verkehrsraum von 6,50 m", "d"]
    assert quote_near(lines, "verkehrsraum von 6,50", 3)
    assert not quote_near(lines, "nicht da", 3)
