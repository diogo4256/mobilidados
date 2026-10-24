"""Official traffic direction of the street (and of crossing streets) from a municipal routing network.

Uses an ArcGIS ``identify`` on a network layer whose features carry, per edge and per direction, whether
travel is allowed (Lisbon: ``Oneway`` = ``Traversable`` / ``Prohibited``, ``[Direction]`` = ``Along`` /
``Against``). Field names come from the city profile's ``[network]``.
"""

from __future__ import annotations

import pandas as pd
from shapely.geometry import LineString

from .config import Network
from .sources import IdentifyCache


def edges_at(cache: IdentifyCache, net: Network, x: float, y: float) -> list[dict[str, object]]:
    return [{"edge": a.get(net.edge), "direction": a.get(net.direction), "status": a.get(net.status)} for a in cache.get(x, y)]


def edges_along(axis: LineString, cache: IdentifyCache, net: Network, stations: list[float]) -> pd.DataFrame:
    rows = []
    for s in stations:
        p = axis.interpolate(s)
        rows += [{"s_m": s, **e} for e in edges_at(cache, net, p.x, p.y)]
    return pd.DataFrame(rows).drop_duplicates()


def directions(edges: pd.DataFrame, open_value: str) -> str:
    """'two-way' if some edge is open in both directions, 'one-way' if open in one, '?' if no data."""
    if edges.empty:
        return "?"
    open_dirs = edges[edges.status == open_value].groupby("edge").direction.apply(set)
    if any(len(v) >= 2 for v in open_dirs):
        return "two-way"
    return "one-way" if len(open_dirs) else "?"
