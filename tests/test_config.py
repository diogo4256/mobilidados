"""Configuration errors are caught when a case is loaded, with a message that names the problem."""

import string
import typing

import pytest

from streetfit.config import ArcgisQuery, Case, Lang, StreetfitError, standards_catalogue, vehicle_catalogue
from streetfit.i18n import messages

FEED = "[sources.feed]\nkind = 'http_file'\nurl = 'https://example.org/gtfs.zip'\nlicence = 'x'\n"
STOP_20 = "{ route = '20', direction_id = 0, stop_id = 's', s_m = 0, heading = 1 }"
REPORTS = "[sources.reports]\nkind = 'http_files'\nlicence = 'x'\nfiles = [{ name = 'a.csv', url = 'https://example.org/a.csv' }]\n"


def test_minimal_case_loads_with_defaults(make_case):
    case = Case.load(make_case())
    assert case.config.profiles.step_m == 0.5
    assert case.config.transit is None
    assert case.results_dir == case.root / "results"


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ("[profiles]\nstep = 1\n", "step"),  # misspelt key (step_m)
        ("[profiles]\ncartography = 'nope'\n", "profiles.cartography = 'nope': no such source"),
        ("[profiles]\ncheck_points_s = [1.25]\n", "not multiples of step_m"),
        ("[direction]\nsource = 'street_axes'\nstations_s = [1]\n", "needs a source of kind 'arcgis_identify'"),
        ("[envelope]\nbus = 'tram'\ncar = 'car_typical'\nscenarios = [['tram']]\n", "unknown vehicle 'tram'"),
        ("[standards]\ncompare = ['made_up']\n", "unknown design reference 'made_up'"),
        ("[[known_gaps]]\npt = 'só em português'\n", "has no 'en' text"),
        ("[[street.blocks]]\nid = 'A'\nstart = 0\nend = 10\n[[street.blocks]]\nid = 'B'\nstart = 12\nend = 20\n", "contiguous"),
        ("[[street.blocks]]\nid = 'A'\nstart = 5\nend = 5\n", "every block needs start < end"),
        (
            FEED + "[transit]\nsource = 'feed'\nservice_date = 2026-10-27\nroutes = ['10']\nreference_stops = [" + STOP_20 + "]\n",
            "not in transit.routes",
        ),
        (REPORTS + "[occurrences]\nsource = 'reports'\nfilters = { a = 'x' }\n", "needs `columns`"),
        ("[area_scan]\n", "[area_scan] needs [transit]"),
    ],
)
def test_invalid_configuration_is_reported(make_case, extra, message):
    with pytest.raises(StreetfitError, match="invalid configuration") as err:
        Case.load(make_case(extra))
    assert message in str(err.value)


def test_city_profile_and_templates(make_case, tmp_path):
    (tmp_path / "city.toml").write_text(
        '[source_templates.layer]\nkind = "arcgis_query"\nurl = "https://example.org/MapServer/9"\nout_sr = 3763\nlicence = "CC-BY-4.0"\n'
    )
    templated = '[sources.area]\ntemplate = "layer"\nenvelope = [0, 0, 1, 1]\n'
    src = Case.load(make_case(templated, prefix='extends = "../city.toml"\n')).source("area")
    assert isinstance(src, ArcgisQuery)
    assert (src.url, src.licence, src.envelope) == ("https://example.org/MapServer/9", "CC-BY-4.0", (0, 0, 1, 1))
    with pytest.raises(StreetfitError, match="unknown template 'other'"):
        Case.load(make_case(templated.replace("layer", "other"), name="b", prefix='extends = "../city.toml"\n'))


def test_packaged_catalogues_are_valid_and_translated():
    for v in vehicle_catalogue().values():
        assert v.source_body
        assert v.source_mirrors
    for r in standards_catalogue().references:
        assert r.quote
        assert r.text("label", "pt") != r.label, f"{r.id}: no Portuguese label"


def test_every_message_exists_in_every_language_with_the_same_placeholders():
    def fields(s: str) -> set[str]:
        return {f for _, f, _, _ in string.Formatter().parse(s) if f}

    en = messages("en")
    for lang in typing.get_args(Lang):
        other = messages(lang)
        assert other.keys() == en.keys(), f"{lang}: keys differ from en"
        assert all(fields(other[k]) == fields(en[k]) for k in en), f"{lang}: placeholders differ from en"


def test_an_unknown_source_id_is_an_error_listing_the_known_ones(make_case):
    with pytest.raises(StreetfitError, match="unknown source 'nope'") as err:
        Case.load(make_case()).source("nope")
    assert "['cartography', 'street_axes']" in str(err.value)
