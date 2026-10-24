"""Minimal ArcGIS REST client (MapServer query and identify) and ESRI JSON -> shapely conversion.

Many municipal GIS portals run old ArcGIS Server versions without pagination, so queries fetch the
object IDs first and then the features in batches.
"""

from __future__ import annotations

import json
from typing import Any

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon

from .provenance import http_get


def _json(url: str, params: dict) -> dict:
    data = http_get(url, params).json()
    if "error" in data:
        raise RuntimeError(f"{url}: {data['error']}")
    return data


def query_layer(layer_url: str, envelope: list[float], in_sr: int, out_sr: int, where: str = "1=1", batch: int = 100) -> dict:
    """All features of a layer intersecting an envelope [xmin, ymin, xmax, ymax], with all attributes."""
    meta = _json(layer_url, {"f": "json"})
    env = dict(zip(("xmin", "ymin", "xmax", "ymax"), envelope, strict=True)) | {"spatialReference": {"wkid": in_sr}}
    spatial = {
        "geometry": json.dumps(env),
        "geometryType": "esriGeometryEnvelope",
        "inSR": in_sr,
        "spatialRel": "esriSpatialRelIntersects",
        "where": where,
    }
    oids = _json(f"{layer_url}/query", {**spatial, "returnIdsOnly": "true", "f": "json"}).get("objectIds") or []
    feats: list[dict] = []
    for i in range(0, len(oids), batch):
        chunk = ",".join(map(str, sorted(oids)[i : i + batch]))
        feats += _json(
            f"{layer_url}/query", {"objectIds": chunk, "outFields": "*", "returnGeometry": "true", "outSR": out_sr, "f": "json"}
        ).get("features", [])
    return {
        "name": meta.get("name"),
        "copyrightText": meta.get("copyrightText"),
        "spatialReference": {"wkid": out_sr},
        "fields": meta.get("fields"),
        "features": feats,
    }


def identify(url: str, x: float, y: float, sr: int, layers: str, tolerance: float, half_extent: float = 100) -> list[dict]:
    """Attributes of the features within ``tolerance`` pixels of a point (MapServer identify)."""
    ext = f"{x - half_extent},{y - half_extent * 0.5625},{x + half_extent},{y + half_extent * 0.5625}"
    data = _json(
        url,
        {
            "geometry": json.dumps({"x": x, "y": y, "spatialReference": {"wkid": sr}}),
            "geometryType": "esriGeometryPoint",
            "sr": sr,
            "layers": layers,
            "tolerance": tolerance,
            "mapExtent": ext,
            "imageDisplay": "1600,900,96",
            "returnGeometry": "false",
            "f": "json",
        },
    )
    return [r["attributes"] for r in data.get("results", [])]


# --- ESRI JSON geometry -> shapely --------------------------------------------------------------
def to_line(g: dict[str, Any]) -> LineString | MultiLineString:
    parts = [LineString(p) for p in g["paths"] if len(p) > 1]
    return parts[0] if len(parts) == 1 else MultiLineString(parts)


def _signed_area(ring: list) -> float:
    return sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1)) / 2


def to_polygon(g: dict[str, Any]) -> Polygon | MultiPolygon:
    """ESRI rings: exterior rings are clockwise (negative signed area), holes counter-clockwise."""
    ext, holes = [], []
    for r in g["rings"]:
        (ext if _signed_area(r) < 0 else holes).append(r)
    polys = []
    for e in ext:
        shell = Polygon(e)
        polys.append(Polygon(e, [h for h in holes if shell.contains(Point(h[0]))]))
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def features(collection: dict) -> list[dict]:
    return collection.get("features", [])
