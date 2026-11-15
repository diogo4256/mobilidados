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
    """The placeholders of the plural messages; the count prints as ``n``, or is the ``total`` of the streets ranked, or
    the ``k`` transects left out of the free width."""
    return {
        "ledger.traffic": {"traffic": "TRAFFIC", "k": 1, "n": count},
        "ledger.routes_scheduled": {"routes": "744"},
        "ledger.trips": {"n": count, "heading": "HEADING"},
        "ledger.meetings": {"n": count},
        "ledger.meetings_narrow": {"n": count},
        "ledger.delay_unconfirmed": {"years": "2026" if count == 1 else "2025 and 2026"},
        "ledger.reports_attributed": {"n": count, "flt": "Parking"},
        "ledger.street_rank": {"rank": 1, "total": count, "minlen": "100"},
        "ledger.area_streets": {"n": count},
        "ledger.area_pattern": {"n": count, "thr": "5,5", "minm": "30", "names": "Rua A"},
        "ledger.places": {"n": count},
        "report.files": {"n": count, "example": "<u>"},
        "caveat.free_filter": {"max": "7,00", "k": count, "n": 240},
        "ledger.sidewalks_narrow": {"n": count, "m": "12", "list": "LIST"},
        "ledger.sidewalks_margin": {"n": count, "m": "8", "acc": "0,30"},
        "ledger.sidewalks_area_streets": {"n": count},
        "ledger.sidewalks_area": {"streets": "STREETS", "n": count, "acc": "0,30", "names": "Rua A"},
        "ledger.sidewalks_area_within": {"n": count},
    }[key]


# (count of 1, count of 3) for each plural message
WORDING = {
    "en": {
        "ledger.delay_unconfirmed": (
            " The interval for 2026 includes 0: that year's data do not confirm the excess.",
            " The intervals for 2025 and 2026 include 0: those years' data do not confirm the excess.",
        ),
        "ledger.traffic": (
            "The municipal routing network marks the street as TRAFFIC: an edge is open in both directions at 1 of 1 point checked along it.",
            "The municipal routing network marks the street as TRAFFIC: an edge is open in both directions at 1 of 3 points checked along it.",
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
        "ledger.places": ("about 1 place", "about 3 places"),
        "report.files": ("1 file, e.g. <u>", "3 files, e.g. <u>"),
        "caveat.free_filter": (
            "Only transects with parking mapped on both sides and a free width of at most 7,00 m count: "
            "1 of the 240 transects with parking on both sides is wider and was left out.",
            "Only transects with parking mapped on both sides and a free width of at most 7,00 m count: "
            "3 of the 240 transects with parking on both sides are wider and were left out.",
        ),
        "ledger.sidewalks_narrow": (
            "On 1 stretch (12 m), the mapped sidewalk reaches the buildings and is narrower than the decree-law admits for "
            "a stretch that long, so the free channel is too: LIST.",
            "On 3 stretches (12 m in all), the mapped sidewalk reaches the buildings and is narrower than the decree-law "
            "admits for a stretch that long, so the free channel is too: LIST.",
        ),
        "ledger.sidewalks_margin": (
            " 1 of them (8 m) is still below it if each mapped edge were 0,30 m off, in the sidewalk's favour.",
            " 3 of them (8 m) are still below it if each mapped edge were 0,30 m off, in the sidewalk's favour.",
        ),
        "ledger.sidewalks_area_streets": (
            "Of 1 street in the area with a sidewalk measured",
            "Of the 3 streets in the area with a sidewalk measured",
        ),
        "ledger.sidewalks_area": (
            "STREETS, 1 has stretches where the mapped sidewalk reaches the buildings and is narrower than Decree-Law "
            "163/2006 admits, even if each mapped edge were 0,30 m off in the sidewalk's favour: Rua A.",
            "STREETS, 3 have stretches where the mapped sidewalk reaches the buildings and is narrower than Decree-Law "
            "163/2006 admits, even if each mapped edge were 0,30 m off in the sidewalk's favour: Rua A.",
        ),
        "ledger.sidewalks_area_within": (
            " In 1 more street, that happens only within that margin.",
            " In 3 more streets, that happens only within that margin.",
        ),
    },
    "pt": {
        "ledger.delay_unconfirmed": (
            " O intervalo de 2026 inclui 0: os dados desse ano não confirmam o excesso.",
            " Os intervalos de 2025 and 2026 incluem 0: os dados desses anos não confirmam o excesso.",
        ),
        "ledger.traffic": (
            "Segundo a rede viária da Câmara, a rua tem TRAFFIC: em 1 de 1 ponto verificado ao longo da rua, "
            "a circulação é permitida em ambos os sentidos.",
            "Segundo a rede viária da Câmara, a rua tem TRAFFIC: em 1 de 3 pontos verificados ao longo da rua, "
            "a circulação é permitida em ambos os sentidos.",
        ),
        "ledger.routes_scheduled": (
            "Segundo o horário, a carreira 744 passa nesta rua.",
            "Segundo o horário, as carreiras 744 passam nesta rua.",
        ),
        "ledger.trips": ("1 viagem HEADING", "3 viagens HEADING"),
        "ledger.meetings": ("1 encontro", "3 encontros"),
        "ledger.meetings_narrow": (
            "1 acontece nos troços com estacionamento dos dois lados",
            "3 acontecem nos troços com estacionamento dos dois lados",
        ),
        "ledger.reports_attributed": (
            "Foi atribuída à rua 1 ocorrência da categoria «Parking»",
            "Foram atribuídas à rua 3 ocorrências da categoria «Parking»",
        ),
        "ledger.street_rank": (
            "1.ª de 1 rua com pelo menos 100 m na envolvente",
            "1.ª de 3 ruas com pelo menos 100 m na envolvente",
        ),
        "ledger.area_streets": ("De 1 rua da zona com autocarros no horário", "Das 3 ruas da zona com autocarros no horário"),
        "ledger.area_pattern": (
            "1 tem dois sentidos e estacionamento dos dois lados, com menos de 5,5 m de largura livre em pelo menos 30 m (Rua A)",
            "3 têm dois sentidos e estacionamento dos dois lados, com menos de 5,5 m de largura livre em pelo menos 30 m (Rua A)",
        ),
        "ledger.places": ("cerca de 1 lugar", "cerca de 3 lugares"),
        "report.files": ("1 ficheiro, p. ex. <u>", "3 ficheiros, p. ex. <u>"),
        "caveat.free_filter": (
            "Só contam os perfis com estacionamento cartografado dos dois lados e até 7,00 m de largura livre: "
            "1 dos 240 perfis com estacionamento dos dois lados tem mais largura livre e ficou de fora.",
            "Só contam os perfis com estacionamento cartografado dos dois lados e até 7,00 m de largura livre: "
            "3 dos 240 perfis com estacionamento dos dois lados têm mais largura livre e ficaram de fora.",
        ),
        "ledger.sidewalks_narrow": (
            "Em 1 troço (12 m), o passeio cartografado vai até às construções e é mais estreito do que o decreto-lei admite "
            "para um troço desse comprimento, pelo que o canal livre também o é: LIST.",
            "Em 3 troços (12 m no total), o passeio cartografado vai até às construções e é mais estreito do que o "
            "decreto-lei admite para um troço desse comprimento, pelo que o canal livre também o é: LIST.",
        ),
        "ledger.sidewalks_margin": (
            " 1 deles (8 m) continua abaixo mesmo que cada aresta cartografada esteja 0,30 m fora do sítio, a favor do passeio.",
            " 3 deles (8 m) continuam abaixo mesmo que cada aresta cartografada esteja 0,30 m fora do sítio, a favor do passeio.",
        ),
        "ledger.sidewalks_area_streets": ("De 1 rua da zona com passeio medido", "Das 3 ruas da zona com passeio medido"),
        "ledger.sidewalks_area": (
            "STREETS, 1 tem troços em que o passeio cartografado vai até às construções e é mais estreito do que o "
            "Decreto-Lei n.º 163/2006 admite, mesmo que cada aresta cartografada esteja 0,30 m fora do sítio, a favor do passeio: Rua A.",
            "STREETS, 3 têm troços em que o passeio cartografado vai até às construções e é mais estreito do que o "
            "Decreto-Lei n.º 163/2006 admite, mesmo que cada aresta cartografada esteja 0,30 m fora do sítio, a favor do passeio: Rua A.",
        ),
        "ledger.sidewalks_area_within": (
            " Em mais 1 rua, isso só acontece dentro dessa margem.",
            " Em mais 3 ruas, isso só acontece dentro dessa margem.",
        ),
    },
}


@pytest.mark.parametrize("lang", LANGUAGES)
def test_every_plural_message_reads_right_for_one_and_for_several(lang):
    assert WORDING[lang].keys() == set(plural_keys(lang)), "a plural message without a wording check"
    for key, (one, several) in WORDING[lang].items():
        assert t(key, lang, count=1, **args_for(key, 1)) == one
        assert t(key, lang, count=3, **args_for(key, 3)) == several
