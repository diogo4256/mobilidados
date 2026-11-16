"""Official traffic direction of a street from a municipal routing network.

Uses an ArcGIS ``identify`` on a network layer whose features carry, per edge and per direction, whether
travel is allowed (Lisbon: ``Oneway`` = ``Traversable`` / ``Prohibited``, ``[Direction]`` = ``Along`` /
``Against``). Field names come from the city profile's ``[network]``.

An identify at a point answers with every edge within its tolerance, including those of a street that crosses or
meets the one asked about there. Only the edges that run along the street count (``along``): within ``MAX_ANGLE`` of
its direction and ``MAX_DIST_M`` of the point. Without that, a one-way street next to a two-way crossing reads as
two-way.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Protocol

import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from .arcgis import GEOMETRY, to_line
from .config import Network


class PointAnswers(Protocol):
    """What the direction needs from an identify cache (``sources.IdentifyCache``): the features at a point."""

    def get(self, x: float, y: float) -> list[dict[str, Any]]: ...


MAX_ANGLE = 30.0  # degrees between an edge and the street for the edge to be the street's
MAX_DIST_M = 6.0  # how far from the point asked about an edge of the street may lie (axis and network are drawn apart)


def tangent(line: BaseGeometry, x: float, y: float, half: float = 2.0) -> np.ndarray:
    """The unit direction of ``line`` where it passes nearest to (x, y)."""
    s = line.project(Point(x, y))
    a, b = line.interpolate(max(s - half, 0.0)), line.interpolate(min(s + half, line.length))
    v = np.array([b.x - a.x, b.y - a.y])
    n = float(np.linalg.norm(v))
    return v / n if n else v


def runs_along(geometry: dict | None, x: float, y: float, along: np.ndarray) -> bool:
    """Whether an edge (ESRI JSON polyline) runs along the direction ``along`` at (x, y), and passes close to it."""
    if not geometry or not geometry.get("paths"):
        return False
    edge = to_line(geometry)
    if edge.distance(Point(x, y)) > MAX_DIST_M:
        return False
    return abs(float(np.dot(tangent(edge, x, y), along))) >= math.cos(math.radians(MAX_ANGLE))


def edges_at(cache: PointAnswers, net: Network, x: float, y: float, along: np.ndarray) -> list[dict[str, object]]:
    """The edges of the street at (x, y): those of the identify answer that run along ``along``."""
    return [
        {"edge": a.get(net.edge), "direction": a.get(net.direction), "status": a.get(net.status)}
        for a in cache.get(x, y)
        if runs_along(a.get(GEOMETRY), x, y, along)
    ]


def edges_along(axis: LineString, cache: PointAnswers, net: Network, stations: list[float]) -> pd.DataFrame:
    rows = []
    for s in stations:
        p = axis.interpolate(s)
        rows += [{"s_m": s, **e} for e in edges_at(cache, net, p.x, p.y, tangent(axis, p.x, p.y))]
    return pd.DataFrame(rows, columns=["s_m", "edge", "direction", "status"]).drop_duplicates()


def directions(edges: pd.DataFrame, open_value: str) -> str:
    """'two-way' if some edge is open in both directions, 'one-way' if open in one, '?' if no data."""
    if edges.empty:
        return "?"
    open_dirs = edges[edges.status == open_value].groupby("edge").direction.apply(set)
    if any(len(v) >= 2 for v in open_dirs):
        return "two-way"
    return "one-way" if len(open_dirs) else "?"


def majority(readings: list[str]) -> str:
    """The direction most points of a street read, among those that read one; '?' if none did or two tie."""
    counts = Counter(r for r in readings if r in ("two-way", "one-way")).most_common()
    if not counts or (len(counts) > 1 and counts[0][1] == counts[1][1]):
        return "?"
    return counts[0][0]
