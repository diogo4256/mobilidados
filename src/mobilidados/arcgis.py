"""Minimal ArcGIS REST client (MapServer query and identify) and ESRI JSON -> shapely conversion.

Many municipal GIS portals run old ArcGIS Server versions without pagination, so queries fetch the
object IDs first and then the features in batches.
"""

from __future__ import annotations

import json
from typing import Any

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon

from .config import MobilidadosError
from .provenance import http_get

IMAGE_WIDTH_PX, IMAGE_HEIGHT_PX, IMAGE_DPI = 1600, 900, 96  # the map image an identify request describes; its tolerance is in these pixels


def _json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = http_get(url, params).json()
    if "error" in data:
        raise MobilidadosError(f"{url}: {data['error']}")
    return data


def query_layer(
    layer_url: str, envelope: tuple[float, ...], in_sr: int, out_sr: int, where: str = "1=1", batch: int = 100
) -> dict[str, Any]:
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
    oids = sorted(_json(f"{layer_url}/query", {**spatial, "returnIdsOnly": "true", "f": "json"}).get("objectIds") or [])
    feats: list[dict[str, Any]] = []
    for i in range(0, len(oids), batch):
        chunk = ",".join(map(str, oids[i : i + batch]))
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


def identify(url: str, x: float, y: float, sr: int, layers: str, tolerance: float, half_extent: float = 100) -> list[dict[str, Any]]:
    """Attributes of the features within ``tolerance`` pixels of a point (MapServer identify)."""
    half_height = half_extent * (IMAGE_HEIGHT_PX / IMAGE_WIDTH_PX)  # the extent has the image's aspect ratio
    ext = f"{x - half_extent},{y - half_height},{x + half_extent},{y + half_height}"
    data = _json(
        url,
        {
            "geometry": json.dumps({"x": x, "y": y, "spatialReference": {"wkid": sr}}),
            "geometryType": "esriGeometryPoint",
            "sr": sr,
            "layers": layers,
            "tolerance": tolerance,
            "mapExtent": ext,
            "imageDisplay": f"{IMAGE_WIDTH_PX},{IMAGE_HEIGHT_PX},{IMAGE_DPI}",
            "returnGeometry": "false",
            "f": "json",
        },
    )
    return [r["attributes"] for r in data.get("results", [])]


# --- ESRI JSON geometry -> shapely --------------------------------------------------------------
def to_line(g: dict[str, Any]) -> LineString | MultiLineString:
    parts = [LineString(p) for p in g["paths"] if len(p) > 1]
    return parts[0] if len(parts) == 1 else MultiLineString(parts)


def _signed_area(ring: list[list[float]]) -> float:
    return sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1)) / 2


def to_polygon(g: dict[str, Any]) -> Polygon | MultiPolygon:
    """ESRI rings: exterior rings are clockwise (negative signed area), holes counter-clockwise.

    Each hole belongs to the smallest exterior ring that contains it, so a hole touching its exterior and an
    island inside a hole (an exterior ring of its own) are both kept right.
    """
    shells = [Polygon(r) for r in g["rings"] if _signed_area(r) < 0]
    holes = [Polygon(r) for r in g["rings"] if _signed_area(r) > 0]
    inner: list[list[Any]] = [[] for _ in shells]
    for h in holes:
        around = [i for i, s in enumerate(shells) if s.contains(h)]
        if around:
            inner[min(around, key=lambda i: shells[i].area)].append(h.exterior.coords)
    polys = [Polygon(s.exterior.coords, rings) for s, rings in zip(shells, inner, strict=True)]
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)
