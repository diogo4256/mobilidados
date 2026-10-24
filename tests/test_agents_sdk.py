"""The AI tools run end to end through the real Anthropic SDK against a mock HTTP transport (no network, no key).

This checks what unit tests cannot: that the requests the tools build are well formed (model, effort, structured
output schema, fallback beta, tools, PDF/image blocks), that the tool-runner loop executes our tools and feeds the
results back, and that the parsed responses flow into the deterministic checks.
"""

import json
from pathlib import Path

import pytest

anthropic = pytest.importorskip("anthropic")
httpx2 = pytest.importorskip("httpx2")

from mobilidados.agents import claim_checker, common, source_discovery, standards_extractor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases" / "lisboa-rua-ricardo-jorge"


class FakeAPI:
    """Queue of Messages API responses; records every request body and header."""

    def __init__(self, *contents):
        self.queue = list(contents)
        self.requests: list[dict] = []

    def handler(self, request):
        self.requests.append({"body": json.loads(request.content), "headers": dict(request.headers)})
        content, stop = self.queue.pop(0)
        return httpx2.Response(
            200,
            json={
                "id": f"msg_{len(self.requests)}",
                "type": "message",
                "role": "assistant",
                "model": common.MODEL,
                "content": content,
                "stop_reason": stop,
                "stop_sequence": None,
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
        )

    def install(self, monkeypatch):
        client = anthropic.Anthropic(api_key="test", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(self.handler)))
        for mod in (claim_checker, standards_extractor, source_discovery):
            monkeypatch.setattr(mod, "client", lambda c=client: c)
        return self


def tool_use(name, **inp):
    return ([{"type": "tool_use", "id": f"toolu_{name}", "name": name, "input": inp}], "tool_use")


def final(obj):
    return ([{"type": "text", "text": json.dumps(obj, ensure_ascii=False)}], "end_turn")


def common_request_checks(body, headers):
    assert body["model"] == common.MODEL
    assert body["output_config"]["effort"] == common.EFFORT
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in headers.get("anthropic-beta", "")
    assert "thinking" not in body or body["thinking"].get("type") == "adaptive"
    assert "tool_choice" not in body or body["tool_choice"]["type"] == "auto"  # forced tool use is rejected on this model


@pytest.mark.skipif(not (CASE / "results" / "findings.json").exists(), reason="case results not generated")
def test_claim_checker_end_to_end(monkeypatch):
    draft = "A faixa livre entre as faixas tem uma mediana de 4,90 m."
    report = {
        "claims": [
            {
                "text": "A faixa livre entre as faixas tem uma mediana de 4,90 m",
                "kind": "number",
                "verdict": "supported",
                "finding_ids": ["free_width"],
                "evidence": [{"doc_id": "ledger", "line": 0, "quote": "mediana 4,90 m"}],
                "problem": "",
                "suggestion": "",
            }
        ]
    }
    api = FakeAPI(tool_use("search_sources", query="faixa livre mediana"), final(report)).install(monkeypatch)

    corpus, findings = claim_checker.build_corpus(claim_checker.Case.load(CASE), [])
    claims = claim_checker.verify(claim_checker.run_agent(draft, corpus), draft, corpus, findings)

    first, second = api.requests
    common_request_checks(first["body"], first["headers"])
    assert {t["name"] for t in first["body"]["tools"]} == {"list_findings", "search_sources", "read_source"}
    assert first["body"]["output_config"]["format"]["schema"]["properties"].keys() == {"claims"}
    results = [
        b
        for m in second["body"]["messages"]
        for b in (m["content"] if isinstance(m["content"], list) else [])
        if b.get("type") == "tool_result"
    ]
    assert results
    assert "ledger" in json.dumps(results[0]["content"])
    assert claims[0]["verdict"] == "supported"
    assert claims[0]["checks"] == []


def test_extractor_end_to_end(monkeypatch, tmp_path):
    pypdf = pytest.importorskip("pypdf")
    pdf = tmp_path / "manual.pdf"
    w = pypdf.PdfWriter()
    w.add_blank_page(width=595, height=842)
    w.write(pdf)
    reading = {
        "page_title": "Perfil",
        "totals": [{"label": "between strips", "components_m": [0.4, 3.0, 3.0, 0.4], "total_m": 6.8}],
        "values": [
            {
                "value_m": 3.0,
                "printed": "3.00 m",
                "measures": "lane",
                "applies_to": "two-way",
                "conditions": "",
                "location": "drawing",
                "page_quote": "",
            }
        ],
    }
    api = FakeAPI(final(reading)).install(monkeypatch)

    parsed, _ = standards_extractor.read_page(pdf, 1, standards_extractor.render_png(pdf, 1, scale=1))
    result = standards_extractor.check(parsed, text="", ocr_text=None)

    body = api.requests[0]["body"]
    common_request_checks(body, api.requests[0]["headers"])
    kinds = [b["type"] for b in body["messages"][0]["content"]]
    assert kinds == ["document", "image", "text"]
    assert body["messages"][0]["content"][1]["source"]["media_type"] == "image/jpeg"
    assert result["values"][0]["verified_by"] == "vision_only"
    assert result["totals"][0]["sum_checks"]


def test_discover_end_to_end(monkeypatch, tmp_path):
    layer = "https://gis.example.org/arcgis/rest/services/Base/MapServer/53"
    served = {
        layer: {"name": "Polygons", "fields": [{"name": "LAYER", "type": "esriFieldTypeString"}, {"name": "NAME", "type": "x"}]},
        f"{layer}/query": {"count": 12},
    }
    monkeypatch.setattr(source_discovery.Http, "get_json", lambda self, url, params=None: served[url])
    choice = {"layer_url": layer, "field": "LAYER", "values": ["road"], "evidence": "fields", "confidence": 0.9}
    draft = {
        "city": "Exampleton",
        "crs_epsg": 3763,
        "road_polygons": choice,
        "parking_polygons": choice | {"values": ["park"]},
        "sidewalk_polygons": None,
        "plot_polygons": None,
        "street_axes": choice | {"field": "NAME", "values": []},
        "traffic_direction": None,
        "gtfs": None,
        "occurrences": None,
        "cartography_licence": None,
        "notes": ["test"],
    }
    api = FakeAPI(tool_use("arcgis_layer", layer_url=layer), final(draft)).install(monkeypatch)

    out = tmp_path / "x.draft.toml"
    assert source_discovery.main("Exampleton", ["https://gis.example.org/arcgis/rest/services"], None, "-9.2,38.7,-9.1,38.8", out) == 0

    common_request_checks(api.requests[0]["body"], api.requests[0]["headers"])
    text = out.read_text()
    assert "road_polygons: layer 'Polygons' ok; road: 12 features in test area" in text
    assert 'class_field = "LAYER"' in text
    import tomllib

    tomllib.loads(text)  # the draft is valid TOML


def test_http_allowlist_blocks_other_hosts():
    http = source_discovery.Http({"gis.example.org"})
    with pytest.raises(PermissionError):
        http.get_json("https://evil.example.com/steal")
