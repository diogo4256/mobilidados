"""The ArcGIS REST client against a fake server (requests made, results returned) and ESRI JSON to shapely conversion."""

import json

import pytest

from streetfit import arcgis

LAYER = "https://gis.example.org/arcgis/rest/services/Base/MapServer/53"
ENVELOPE = (-9.2, 38.7, -9.1, 38.8)

# ESRI rings: exterior clockwise, hole counter-clockwise
OUTER = [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]


class Response:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def fake_server(monkeypatch, object_ids):
    """Serve a layer whose features are ``{"attributes": {"OBJECTID": n}}``; return the list of (url, params) requests."""
    requests = []

    def http_get(url, params=None, timeout=None):
        requests.append((url, params))
        if url == LAYER:
            return Response({"name": "Polygons", "copyrightText": "(c) example", "fields": [{"name": "LAYER"}]})
        if params.get("returnIdsOnly"):
            return Response({"objectIds": object_ids})
        return Response({"features": [{"attributes": {"OBJECTID": int(i)}} for i in params["objectIds"].split(",")]})

    monkeypatch.setattr(arcgis, "http_get", http_get)
    return requests


def test_query_layer_fetches_the_ids_then_the_features_in_sorted_batches(monkeypatch):
    requests = fake_server(monkeypatch, object_ids=[5, 3, 9, 1, 7])
    result = arcgis.query_layer(LAYER, ENVELOPE, in_sr=4326, out_sr=3763, batch=2)

    (meta_url, meta_params), (ids_url, ids_params), *batches = requests
    assert (meta_url, meta_params) == (LAYER, {"f": "json"})
    assert ids_url == f"{LAYER}/query"
    assert ids_params["returnIdsOnly"] == "true"
    assert ids_params["where"] == "1=1"
    assert ids_params["inSR"] == 4326
    assert json.loads(ids_params["geometry"]) == {
        "xmin": -9.2,
        "ymin": 38.7,
        "xmax": -9.1,
        "ymax": 38.8,
        "spatialReference": {"wkid": 4326},
    }
    assert [(url, p["objectIds"]) for url, p in batches] == [(f"{LAYER}/query", "1,3"), (f"{LAYER}/query", "5,7"), (f"{LAYER}/query", "9")]
    assert all(p["outSR"] == 3763 and p["outFields"] == "*" for _, p in batches)

    assert [f["attributes"]["OBJECTID"] for f in result["features"]] == [1, 3, 5, 7, 9]
    assert result["spatialReference"] == {"wkid": 3763}
    assert (result["name"], result["copyrightText"], result["fields"]) == ("Polygons", "(c) example", [{"name": "LAYER"}])


@pytest.mark.parametrize("no_ids", [None, []])
def test_query_layer_without_matches_asks_for_no_features(monkeypatch, no_ids):
    requests = fake_server(monkeypatch, object_ids=no_ids)
    assert arcgis.query_layer(LAYER, ENVELOPE, in_sr=4326, out_sr=3763)["features"] == []
    assert len(requests) == 2  # the layer description and the ids


def test_an_error_in_the_response_body_raises(monkeypatch):
    monkeypatch.setattr(arcgis, "http_get", lambda url, params=None: Response({"error": {"code": 400, "message": "Invalid query"}}))
    with pytest.raises(RuntimeError, match="Invalid query"):
        arcgis.query_layer(LAYER, ENVELOPE, in_sr=4326, out_sr=3763)


def test_identify_asks_for_a_map_extent_with_the_aspect_of_the_image(monkeypatch):
    sent: dict = {}

    def http_get(url, params=None):
        sent.update(url=url, params=params)
        return Response({"results": [{"attributes": {"Oneway": "Traversable"}}, {"attributes": {"Oneway": "Prohibited"}}]})

    monkeypatch.setattr(arcgis, "http_get", http_get)
    attrs = arcgis.identify("https://gis.example.org/MapServer/identify", 1000.0, 2000.0, 3763, "all:203", tolerance=3, half_extent=160.0)

    assert attrs == [{"Oneway": "Traversable"}, {"Oneway": "Prohibited"}]
    p = sent["params"]
    width, height, _dpi = map(int, p["imageDisplay"].split(","))
    x0, y0, x1, y1 = map(float, p["mapExtent"].split(","))
    assert (x1 - x0) / (y1 - y0) == pytest.approx(width / height)
    assert ((x0 + x1) / 2, (y0 + y1) / 2) == (1000.0, 2000.0)
    assert (x1 - x0) / 2 == 160.0
    assert (p["layers"], p["tolerance"], p["sr"]) == ("all:203", 3, 3763)


def test_esri_ring_orientation_and_holes():
    hole = [[2, 2], [4, 2], [4, 4], [2, 4], [2, 2]]
    assert arcgis.to_polygon({"rings": [OUTER, hole]}).area == pytest.approx(100 - 4)


def test_hole_touching_its_exterior_is_kept():
    hole = [[0, 0], [3, 1], [1, 3], [0, 0]]  # touches the exterior at its corner (0, 0)
    p = arcgis.to_polygon({"rings": [OUTER, hole]})
    assert p.is_valid
    assert p.area == pytest.approx(100 - 4)


def test_hole_inside_an_island_inside_a_hole():
    hole = [[1, 1], [9, 1], [9, 9], [1, 9], [1, 1]]
    island = [[3, 3], [3, 7], [7, 7], [7, 3], [3, 3]]
    hole_in_island = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
    p = arcgis.to_polygon({"rings": [OUTER, hole, island, hole_in_island]})
    assert p.geom_type == "MultiPolygon"
    assert p.is_valid
    assert p.area == pytest.approx((100 - 64) + (16 - 4))
