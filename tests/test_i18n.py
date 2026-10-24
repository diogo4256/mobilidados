"""Message catalogues (``locales/<lang>.toml``): the same keys, forms and placeholders in every language, and plural forms."""

import string
import typing

import pytest

from mobilidados.config import Lang
from mobilidados.i18n import PLURAL_RULES, messages, t

LANGUAGES = typing.get_args(Lang)
FORMS = {"one", "other"}


def fields(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


def plural_keys(lang):
    return sorted(k for k, v in messages(lang).items() if isinstance(v, dict))


def forms(lang, key) -> dict[str, str]:
    message = messages(lang)[key]
    assert isinstance(message, dict), f"{lang}: {key} has no plural forms"
    return message


def test_every_message_exists_in_every_language_with_the_same_placeholders():
    en = messages("en")
    for lang in LANGUAGES:
        other = messages(lang)
        assert other.keys() == en.keys(), f"{lang}: keys differ from en"
        for key, message in en.items():
            translated = other[key]
            assert isinstance(translated, dict) == isinstance(message, dict), f"{lang}: {key} is plural in only one language"
            if isinstance(message, str) and isinstance(translated, str):
                assert fields(translated) == fields(message), f"{lang}: placeholders of {key} differ from en"


def test_plural_messages_have_the_same_forms_and_placeholders_in_every_language():
    assert plural_keys("en"), "no plural messages to compare"
    for lang in LANGUAGES:
        assert plural_keys(lang) == plural_keys("en")
        for key in plural_keys("en"):
            assert forms(lang, key).keys() == FORMS, f"{lang}: {key} must have the forms {sorted(FORMS)}"
            for form, text in forms(lang, key).items():
                assert fields(text) == fields(forms("en", key)[form]), f"{lang}: placeholders of {key}.{form} differ from en"


def test_every_language_has_a_plural_rule():
    assert set(PLURAL_RULES) == set(LANGUAGES)


@pytest.mark.parametrize("lang", LANGUAGES)
def test_the_singular_is_for_exactly_one(lang):
    assert [PLURAL_RULES[lang](n) for n in (0, 1, 2, 5, 1.5, float("inf"))] == ["other", "one", "other", "other", "other", "other"]


def test_the_count_picks_the_form_and_a_plural_message_needs_one():
    assert t("report.files", "en", count=1, n=1, example="<u>") == "1 file, e.g. <u>"
    assert t("report.files", "en", count=0, n=0, example="<u>") == "0 files, e.g. <u>"
    with pytest.raises(TypeError, match=r"report\.files"):
        t("report.files", "en", n=1, example="<u>")
    assert t("report.sources", "en", count=1) == "Sources"  # a message without forms ignores the count


def args_for(key, count):
    """The placeholders of the plural messages; the count prints as ``n``, or is the ``total`` of the streets ranked."""
    return {
        "ledger.traffic": {"traffic": "TRAFFIC", "n": count},
        "ledger.routes_scheduled": {"routes": "744"},
        "ledger.trips": {"n": count, "heading": "HEADING"},
        "ledger.meetings": {"n": count},
        "ledger.meetings_narrow": {"n": count},
        "ledger.reports_attributed": {"n": count, "flt": "Parking"},
        "ledger.street_rank": {"rank": 1, "total": count, "minlen": "100"},
        "ledger.area_streets": {"n": count},
        "ledger.area_pattern": {"n": count, "thr": "5,5", "minm": "30", "names": "Rua A"},
        "report.files": {"n": count, "example": "<u>"},
    }[key]


# (count of 1, count of 3) for each plural message
WORDING = {
    "en": {
        "ledger.traffic": (
            "The municipal routing network marks the street as TRAFFIC (edges checked at 1 point along it).",
            "The municipal routing network marks the street as TRAFFIC (edges checked at 3 points along it).",
        ),
        "ledger.routes_scheduled": ("Route 744 is scheduled along the street.", "Routes 744 are scheduled along the street."),
        "ledger.trips": ("1 trip HEADING", "3 trips HEADING"),
        "ledger.meetings": ("1 meeting", "3 meetings"),
        "ledger.meetings_narrow": (
            "1 falls within the sections with parking on both sides",
            "3 fall within the sections with parking on both sides",
        ),
        "ledger.reports_attributed": (
            "1 report in category 'Parking' was attributed to the street",
            "3 reports in category 'Parking' were attributed to the street",
        ),
        "ledger.street_rank": (
            "rank 1 of 1 street of at least 100 m in the surrounding area",
            "rank 1 of 3 streets of at least 100 m in the surrounding area",
        ),
        "ledger.area_streets": (
            "Of 1 street with scheduled buses in the surrounding area",
            "Of 3 streets with scheduled buses in the surrounding area",
        ),
        "ledger.area_pattern": (
            "1 is two-way and combines parking on both sides with a free width below 5,5 m over at least 30 m (Rua A)",
            "3 are two-way and combine parking on both sides with a free width below 5,5 m over at least 30 m (Rua A)",
        ),
        "report.files": ("1 file, e.g. <u>", "3 files, e.g. <u>"),
    },
    "pt": {
        "ledger.traffic": (
            "A rede viária municipal marca a rua como de TRAFFIC (arestas verificadas em 1 ponto ao longo da rua).",
            "A rede viária municipal marca a rua como de TRAFFIC (arestas verificadas em 3 pontos ao longo da rua).",
        ),
        "ledger.routes_scheduled": (
            "A carreira 744 está programada ao longo da rua.",
            "As carreiras 744 estão programadas ao longo da rua.",
        ),
        "ledger.trips": ("1 viagem HEADING", "3 viagens HEADING"),
        "ledger.meetings": ("1 encontro", "3 encontros"),
        "ledger.meetings_narrow": (
            "1 cai nos troços com estacionamento dos dois lados",
            "3 caem nos troços com estacionamento dos dois lados",
        ),
        "ledger.reports_attributed": (
            "Foi atribuída à rua 1 ocorrência da categoria «Parking»",
            "Foram atribuídas à rua 3 ocorrências da categoria «Parking»",
        ),
        "ledger.street_rank": (
            "1.ª de 1 rua com pelo menos 100 m na envolvente",
            "1.ª de 3 ruas com pelo menos 100 m na envolvente",
        ),
        "ledger.area_streets": ("De 1 rua com autocarros programados na envolvente", "Das 3 ruas com autocarros programados na envolvente"),
        "ledger.area_pattern": (
            "1 é de dois sentidos e combina estacionamento dos dois lados com uma faixa livre inferior a 5,5 m em pelo menos 30 m (Rua A)",
            "3 são de dois sentidos e combinam estacionamento dos dois lados com uma faixa livre inferior a 5,5 m em pelo menos 30 m (Rua A)",
        ),
        "report.files": ("1 ficheiro, p. ex. <u>", "3 ficheiros, p. ex. <u>"),
    },
}


@pytest.mark.parametrize("lang", LANGUAGES)
def test_every_plural_message_reads_right_for_one_and_for_several(lang):
    assert WORDING[lang].keys() == set(plural_keys(lang)), "a plural message without a wording check"
    for key, (one, several) in WORDING[lang].items():
        assert t(key, lang, count=1, **args_for(key, 1)) == one
        assert t(key, lang, count=3, **args_for(key, 3)) == several
