"""Taking a bus line off the street: the shortest way round it on the street network (``[[appraisal.reroutes]]``).

For each route and direction an alternative moves, the line's own shape is followed from some way before the street
to some way after it, and two paths between those two points are found on the network of street axes: the one through
the street, as the bus runs today (to where the shape meets the street, along it, and on from where it leaves it), and
the shortest one without it. The difference is the detour. It can be negative: a line that turns into the street to
serve its stops runs a shorter way without it, and what it loses is those stops. Two lead-in lengths are tried and the smaller detour
kept, which favours the rerouting. The network is the municipality's street axes, undirected: one-way rules and
whether a bus can make each turn are not in the data, so the path found is a lower bound on the real detour, and the
streets it uses that carry no bus today are listed to be checked on site.
"""

from __future__ import annotations

import dataclasses
import heapq
import itertools
import math
from collections.abc import Iterable
from dataclasses import dataclass

from shapely.geometry import LineString, MultiLineString, Point
from shapely.geometry.base import BaseGeometry

Node = tuple[int, int]


class Network:
    """An undirected graph of street axes: nodes are vertices rounded to the metre, edges carry the street's name."""

    def __init__(self, axes: Iterable[tuple[str, BaseGeometry]]) -> None:
        self.adj: dict[Node, list[tuple[Node, float, str]]] = {}
        for name, geom in axes:
            lines = list(geom.geoms) if isinstance(geom, MultiLineString) else [geom]
            for line in lines:
                pts = list(line.coords)
                for p, q in itertools.pairwise(pts):
                    a, b = (round(p[0]), round(p[1])), (round(q[0]), round(q[1]))
                    w = math.dist(p[:2], q[:2])
                    if a != b and w > 0:
                        self.adj.setdefault(a, []).append((b, w, name))
                        self.adj.setdefault(b, []).append((a, w, name))
        self.nodes = list(self.adj)

    def nearest(self, x: float, y: float) -> Node:
        return min(self.nodes, key=lambda n: (n[0] - x) ** 2 + (n[1] - y) ** 2)

    def junctions(self, street: str) -> list[Node]:
        """The nodes where another street meets the streets whose name contains ``street``: where a bus enters or
        leaves it."""
        return [
            n
            for n, edges in self.adj.items()
            if any(street in name for _, _, name in edges) and any(street not in name for _, _, name in edges)
        ]

    def shortest(self, a: Node, b: Node, avoid: str | None = None, only: str | None = None) -> tuple[float, list[str], LineString] | None:
        """Length of the shortest path from ``a`` to ``b``, the streets it runs along, in order, and its line; None if
        there is none. Streets whose name contains ``avoid`` are left out; with ``only``, every other street is."""
        dist, prev, queue = {a: 0.0}, {}, [(0.0, a)]
        while queue:
            d, u = heapq.heappop(queue)
            if u == b:
                break
            if d > dist[u]:
                continue
            for v, w, name in self.adj.get(u, []):
                if (avoid and avoid in name) or (only and only not in name):
                    continue
                if d + w < dist.get(v, math.inf):
                    dist[v], prev[v] = d + w, (u, name)
                    heapq.heappush(queue, (d + w, v))
        if b not in dist:
            return None
        names, u, nodes = [], b, [b]
        while u in prev:
            u, name = prev[u]
            names.append(name)
            nodes.append(u)
        streets: list[str] = []
        for name in reversed(names):
            if not streets or streets[-1] != name:
                streets.append(name)
        line = LineString(list(reversed(nodes))) if len(nodes) > 1 else LineString([a, a])
        return dist[b], streets, line


@dataclass(frozen=True)
class Detour:
    """A way round the street: the lead-in it was measured over, the lengths with and without the street, the
    streets it runs along and its line, where it leaves and rejoins the line's shape, and the range over lead-ins."""

    lead_in_m: float
    with_street_m: float
    without_street_m: float
    via: list[str]
    path: LineString
    from_m: float
    to_m: float
    detour_min_m: float = 0.0
    detour_max_m: float = 0.0
    on_bus_streets: bool = False

    @property
    def detour_m(self) -> float:
        return self.without_street_m - self.with_street_m

    @property
    def shorter_without(self) -> bool:
        """The line would run a shorter way without the street: it turns into it for its stops, not to get through."""
        return self.detour_m < 0


def detour(net: Network, shape: LineString, axis: LineString, street: str, lead_ins: Iterable[float] = (200.0, 300.0, 400.0, 500.0),
           near_m: float = 12.0, step_m: float = 2.0, bus_streets: set[str] | None = None) -> Detour | None:  # fmt: skip
    """The detour a bus following ``shape`` would run if it could not use ``street`` (whose axis is ``axis``): for each
    lead-in, the shortest path on the network between the points that far before the shape reaches the street and
    that far after it leaves, without the street, less the path through it (``through``).

    The shortest path depends on the lead-in, and the network does not know which streets a bus can use. So, of the
    lead-ins whose path runs only on ``bus_streets`` (the streets with buses today), the smallest detour is kept; if
    none does, the smallest of all, whose other streets are then to be checked. Of detours within 10 m of each other,
    the shorter lead-in is kept. Also returns the range of the detours found. None if the shape does not run along
    the street."""
    n = int(shape.length // step_m)
    along = [i * step_m for i in range(n + 1) if axis.distance(shape.interpolate(i * step_m)) <= near_m]
    if not along:
        return None
    d0, d1 = min(along), max(along)
    on_street = net.junctions(street)
    if not on_street:
        return None
    pe, px = shape.interpolate(d0), shape.interpolate(d1)
    ne, nx = (min(on_street, key=lambda q: (q[0] - pt.x) ** 2 + (q[1] - pt.y) ** 2) for pt in (pe, px))
    rows: list[Detour] = []
    for lead in lead_ins:
        a, b = max(d0 - lead, 0.0), min(d1 + lead, shape.length)
        pa, pb = shape.interpolate(a), shape.interpolate(b)
        na, nb = net.nearest(pa.x, pa.y), net.nearest(pb.x, pb.y)
        base, alt = through(net, na, ne, nx, nb, street), net.shortest(na, nb, avoid=street)
        if base is None or alt is None:
            continue
        rows.append(Detour(lead, base, alt[0], alt[1], alt[2], a, b))
    if not rows:
        return None
    on_buses = [r for r in rows if bus_streets and set(r.via) <= bus_streets]
    best = None
    for r in on_buses or rows:
        if best is None or r.detour_m < best.detour_m - 10:
            best = r
    assert best is not None
    detours = [r.detour_m for r in rows]
    return dataclasses.replace(best, detour_min_m=min(detours), detour_max_m=max(detours), on_bus_streets=bool(on_buses))


def through(net: Network, a: Node, enter: Node, leave: Node, b: Node, street: str) -> float | None:
    """The length of the path from ``a`` to ``b`` that runs along ``street`` from ``enter`` to ``leave``, as a bus on
    it does today: the shortest way to the street without it, along it, and on from it without it. None if a leg has
    no path."""
    legs = (net.shortest(a, enter, avoid=street), net.shortest(enter, leave, only=street), net.shortest(leave, b, avoid=street))
    if any(leg is None for leg in legs):
        return None
    return sum(leg[0] for leg in legs if leg is not None)


def skipped(points: Iterable[tuple[str, float, float]], shape: LineString, start_m: float, end_m: float, path: LineString,
            near_m: float = 50.0) -> list[str]:  # fmt: skip
    """The ids of the stops (id, x, y) a bus following ``shape`` serves between ``start_m`` and ``end_m`` along it that
    lie more than ``near_m`` from the new ``path``: the stops it would no longer serve."""
    out = []
    for sid, x, y in points:
        p = Point(x, y)
        if shape.distance(p) <= near_m and start_m <= shape.project(p) <= end_m and path.distance(p) > near_m:
            out.append(sid)
    return out
