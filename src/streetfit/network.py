"""Official traffic direction of the street (and of crossing streets) from a municipal routing network.

Uses an ArcGIS ``identify`` on a network layer whose features carry, per edge and per direction, whether
travel is allowed (Lisbon: ``Oneway`` = ``Traversable`` / ``Prohibited``, ``[Direction]`` = ``Along`` /
``Against``). Field names come from the city profile.
"""

from __future__ import annotations

import pandas as pd
from shapely.geometry import LineString

from .sources import IdentifyCache


def edges_along(
    axis: LineString, cache: IdentifyCache, fields: dict[str, str], stations: list[float], tolerance: float = 6
) -> pd.DataFrame:
    rows = []
    for s in stations:
        p = axis.interpolate(s)
        for a in cache.get(p.x, p.y, tolerance):
            rows.append(
                {"s_m": s, "edge": a.get(fields["edge"]), "direction": a.get(fields["direction"]), "status": a.get(fields["status"])}
            )
    return pd.DataFrame(rows).drop_duplicates()


def directions(edges: pd.DataFrame, open_value: str) -> str:
    """'two-way' if some edge is open in both directions, 'one-way' if open in one, '?' if no data."""
    if edges.empty:
        return "?"
    open_dirs = edges[edges.status == open_value].groupby("edge").direction.apply(set)
    if any(len(v) >= 2 for v in open_dirs):
        return "two-way"
    return "one-way" if len(open_dirs) else "?"
