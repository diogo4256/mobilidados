"""The deterministic halves of the AI tools, with the model's output faked (no API calls)."""

import json
from urllib.parse import urlparse

import pytest
import requests

pytest.importorskip("anthropic")
pytest.importorskip("pydantic")

from mobilidados.agents import source_discovery
from mobilidados.agents.claim_checker import Claim, ClaimReport, Corpus, Evidence, verify
from mobilidados.agents.source_discovery import CityProfileDraft, DataSource, LayerChoice, to_toml
from mobilidados.agents.standards_extractor import DerivedTotal, PageReading, WidthValue, check
from mobilidados.config import ArcgisQuery, Case, HttpFile

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


def test_supported_verdict_without_evidence_or_findings_needs_a_person():
    bare = claim(text="a rua é estreita", kind="other", finding_ids=[], evidence=[])
    out = verify(ClaimReport(claims=[bare]), "a rua é estreita", corpus(), FINDINGS)
    assert out[0]["verdict"] == "needs_human"
    assert "not backed" in out[0]["checks"][0]


def test_numbers_are_checked_whatever_kind_the_model_gives():
    wrong = claim(text="a faixa livre é de 4,50 m", kind="other")
    out = verify(ClaimReport(claims=[wrong]), "a faixa livre é de 4,50 m", corpus(), FINDINGS)
    assert out[0]["verdict"] == "needs_human"
    assert "numbers not in the cited findings" in out[0]["checks"][0]
    # a number backed by a verified quote, with no finding cited, still passes
    quoted = claim(
        text="uma largura de 2,75 m por via",
        kind="document",
        finding_ids=[],
        evidence=[Evidence(doc_id="manual", line=2, quote="uma largura de 2,75 m por via")],
    )
    out = verify(ClaimReport(claims=[quoted]), "O manual indica uma largura de 2,75 m por via.", corpus(), FINDINGS)
    assert out[0]["verdict"] == "supported"
    assert out[0]["checks"] == []


def test_a_short_evidence_quote_backs_nothing():
    short = claim(finding_ids=[], evidence=[Evidence(doc_id="ledger", line=0, quote="4,90 m")])
    out = verify(ClaimReport(claims=[short]), "a faixa livre é de 4,90 m", corpus(), FINDINGS)
    assert out[0]["verdict"] == "needs_human"
    assert "not backed" in out[0]["checks"][0]


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


def test_corpus_read_returns_at_most_the_limit():
    c = Corpus()
    c.add("long", "\n".join(f"line {i}" for i in range(1, 3 * Corpus.READ_LIMIT)))
    text = c.read("long", 5, 10 * Corpus.READ_LIMIT)
    assert len(text.splitlines()) == Corpus.READ_LIMIT
    assert text.startswith("5: line 5")


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


CASE_ON_A_PROFILE = """extends = "exampleton.toml"

[case]
id = "t"
title = "Test street"

[street]
name = "Rua do Teste"
headings = { "+" = "up", "-" = "down" }

[sources.cartography]
template = "cartography_polygons"
envelope = [-9.2, 38.7, -9.1, 38.8]

[sources.street_axes]
template = "street_axes"
envelope = [-9.2, 38.7, -9.1, 38.8]
"""
GTFS_FROM_THE_PROFILE = '\n[sources.feed]\ntemplate = "gtfs"\n'


def layer(name, field, values):
    base = "https://gis.example.org/arcgis/rest/services/Base/MapServer"
    return LayerChoice(layer_url=f"{base}/{name}", field=field, values=values, evidence="fields and sample", confidence=0.9)


def draft_of(full):
    optional = (
        {
            "sidewalk_polygons": layer(54, "LAYER", ["sidewalk"]),
            "plot_polygons": layer(53, "LAYER", ["building", "yard"]),
            "traffic_direction": None,
            "gtfs": DataSource(
                url="https://example.org/gtfs.zip", licence="CC-BY-4.0", licence_evidence_url="https://example.org", evidence="page"
            ),
            "occurrences": None,
            "cartography_licence": DataSource(
                url="https://example.org/data", licence="CC0-1.0", licence_evidence_url="https://example.org", evidence="page"
            ),
            "notes": ['Survey date unknown.\nScale is "1:1000", check it.'],
        }
        if full
        else dict.fromkeys(("sidewalk_polygons", "plot_polygons", "traffic_direction", "gtfs", "occurrences", "cartography_licence"))
        | {"notes": []}
    )
    return CityProfileDraft(
        city="São João",
        crs_epsg=3763,
        road_polygons=layer(53, "LAYER", ["road"]),
        parking_polygons=layer(53, "LAYER", ["park"]),
        street_axes=layer(79, "NAME", []),
        **optional,
    )


@pytest.mark.parametrize("full", [False, True], ids=["minimal", "full"])
def test_a_discovered_draft_is_a_city_profile_a_case_can_extend(tmp_path, full):
    checks = ["road_polygons: layer 'Polygons' ok", "street_axes: CHECK FAILED (HTTP 500:\nServer Error)"]
    (tmp_path / "exampleton.toml").write_text(to_toml(draft_of(full), checks), encoding="utf-8")
    (tmp_path / "case.toml").write_text(CASE_ON_A_PROFILE + (GTFS_FROM_THE_PROFILE if full else ""), encoding="utf-8")

    case = Case.load(tmp_path)

    assert (case.config.city.name, case.crs) == ("São João", 3763)
    assert case.config.cartography.roles()["road"] == {"road"}
    assert case.config.axes.name_field == "NAME"
    cartography, axes = case.source("cartography"), case.source("street_axes")
    assert isinstance(cartography, ArcgisQuery)
    assert isinstance(axes, ArcgisQuery)
    assert cartography.url.endswith("/MapServer/53")
    assert axes.url.endswith("/MapServer/79")
    assert cartography.licence == ("CC0-1.0" if full else "REVIEW: not found")
    assert axes.licence.startswith("REVIEW")  # the draft holds no evidence for it, and a source cannot load without one
    if full:
        feed = case.source("feed")
        assert isinstance(feed, HttpFile)
        assert (feed.url, feed.licence, feed.suffix) == ("https://example.org/gtfs.zip", "CC-BY-4.0", ".zip")
        assert case.config.cartography.roles()["plot"] == {"building", "yard"}


def test_discovery_requests_are_cached_budgeted_and_time_limited(monkeypatch):
    seen = []

    class Session:
        def get(self, url, params, timeout, allow_redirects):
            seen.append((url, timeout))

            class Response:
                is_redirect = False

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"url": url}

            return Response()

    monkeypatch.setattr(source_discovery, "session", Session)
    http = source_discovery.Http({"example.org"}, max_calls=2)
    assert http.get_json("https://gis.example.org/a") == {"url": "https://gis.example.org/a"}
    http.get_json("https://gis.example.org/a")  # answered from the cache: it does not use the budget
    http.get_json("https://gis.example.org/b")
    with pytest.raises(RuntimeError, match="request budget exhausted"):
        http.get_json("https://gis.example.org/c")
    assert seen == [
        ("https://gis.example.org/a", source_discovery.REQUEST_TIMEOUT_S),
        ("https://gis.example.org/b", source_discovery.REQUEST_TIMEOUT_S),
    ]


def test_discovery_does_not_follow_a_redirect_off_the_allowlist(monkeypatch):
    seen = []

    class Server(requests.adapters.BaseAdapter):
        def send(self, request, *args, **kw):
            seen.append(request.url)
            r = requests.Response()
            r.url, r.request, r._content = request.url, request, b"{}"
            if urlparse(request.url).hostname == "gis.example.org":
                r.status_code, r.headers["Location"] = 302, "https://evil.example.com/x"
            else:
                r.status_code = 200
            return r

        def close(self):
            pass

    def session():
        s = requests.Session()
        s.mount("https://", Server())
        return s

    monkeypatch.setattr(source_discovery, "session", session)
    with pytest.raises(RuntimeError, match="redirected to https://evil"):
        source_discovery.Http({"gis.example.org"}).get_json("https://gis.example.org/a")
    assert seen == ["https://gis.example.org/a"]


def test_long_tool_results_are_cut_before_they_reach_the_model():
    short = {"a": "x"}
    assert json.loads(source_discovery._clip(short)) == short
    clipped = source_discovery._clip({"a": "x" * 3 * source_discovery.MAX_CHARS})
    assert clipped.startswith('{"a": "xxx')
    assert clipped.endswith("chars]")
    assert "[truncated, " in clipped
