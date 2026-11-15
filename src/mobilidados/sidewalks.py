"""Sidewalk width along a street, against the free path the accessibility law requires (the ``sidewalks`` stage).

Decree-Law 163/2006 (annex, section 4.3) requires pedestrian routes to keep a continuous channel free of
obstructions at least 1.2 m wide, counting street furniture, trees, signs and the like as obstructions; a stretch
may be narrower only if it is short: at least 0.80 m wide over at most 0.60 m, at least 0.90 m over at most 1.50 m
(section 4.3.3). The values are in ``data/standards.toml`` with their page.

The width compared is the widest piece of mapped sidewalk at each station (``geometry.measure_profiles``,
``walk_L`` / ``walk_R``). Where that piece runs from the kerb side up to the plots (``walk_*_bounded``), nothing
beyond it can be walked on; obstructions only take width away, and those mapped as their own polygons (kiosks, tree
pits, shelters) already have. So there the free channel cannot be wider than the mapped sidewalk, and a stretch
narrower than the law allows is one where the free channel is too: the case for it rests on the cartography alone.
Where the piece ends at something the cartography classes read do not cover (a lawn, a square, a wall), the path
may continue beyond it: such a stretch is reported as one to check, never as below the law. The reverse never holds:
poles, bins and parked vehicles are not mapped, so a wide mapped sidewalk does not show a wide free channel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from shapely import STRtree
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from .config import Block
from .geometry import Profiler, covered, measure_profiles

SIDES = ("L", "R")


def allowed_width(length_m: float, free_path_m: float, short: list[tuple[float, float]]) -> float:
    """The narrowest width the law admits for a stretch of ``length_m``: the short-stretch allowances (``short``:
    (maximum length, minimum width), shortest first), else the free path."""
    for max_len, min_width in short:
        if length_m <= max_len + 1e-9:
            return min_width
    return free_path_m


def bounded(profiles: pd.DataFrame, side: str) -> pd.Series:
    """The stations whose sidewalk reading on ``side`` runs up to the plots (see the module's docstring)."""
    return profiles[f"walk_{side}"].notna() & profiles[f"walk_{side}_bounded"].eq(True)


def away_from_junctions(profiles: pd.DataFrame, junctions: list[float], margin_m: float) -> pd.DataFrame:
    """The profiles with the sidewalk left unmeasured within ``margin_m`` of a junction or an end of the axis (positions
    along it in ``junctions``): there a transect crosses corners and the other street, not the sidewalk."""
    near = np.zeros(len(profiles), dtype=bool)
    for j in junctions:
        near |= (profiles.s - j).abs().to_numpy() <= margin_m
    return profiles.assign(**{f"walk_{side}": profiles[f"walk_{side}"].where(~near) for side in SIDES})


def away_from_widenings(profiles: pd.DataFrame, factor: float = 1.5) -> pd.DataFrame:
    """The profiles with the sidewalk left unmeasured where the street is much wider kerb to kerb than it usually is
    (more than ``factor`` times its median): a junction, a slip lane or a square, where a transect does not cross a
    sidewalk along the street."""
    if "kerb_to_kerb" not in profiles or profiles.kerb_to_kerb.isna().all():
        return profiles
    wide = (profiles.kerb_to_kerb > factor * profiles.kerb_to_kerb.median()).to_numpy()
    return profiles.assign(**{f"walk_{side}": profiles[f"walk_{side}"].where(~wide) for side in SIDES})


def junctions_along(part: LineString, others: list[BaseGeometry]) -> list[float]:
    """Positions along ``part`` where it ends or meets another axis."""
    out = [0.0, part.length]
    for g in others:
        x = part.intersection(g)
        out += [part.project(pt.centroid) for pt in getattr(x, "geoms", [x]) if not pt.is_empty]
    return sorted(out)


SECTION_COLUMNS = ["side", "s_from", "s_to", "length_m", "width_min_m", "width_median_m", "allowed_m", "below",
                   "below_with_accuracy", "x", "y"]  # fmt: skip


def narrow_sections(
    profiles: pd.DataFrame,
    step: float,
    length: float,
    free_path_m: float,
    short: list[tuple[float, float]],
    edge_accuracy_m: float,
) -> pd.DataFrame:
    """Runs of consecutive stations on one side where the sidewalk, read up to the plots, is narrower than
    ``free_path_m``.

    Each run says how long it is (``geometry.covered``), how narrow, the width the law admits for a stretch that long,
    whether the mapped width is below it, and whether it still is if each of the two mapped edges were
    ``edge_accuracy_m`` off in the sidewalk's favour. ``x``, ``y`` is the station in the middle of the run."""
    rows = []
    for side in SIDES:
        d = profiles[bounded(profiles, side) & (profiles[f"walk_{side}"] < free_path_m)].sort_values("s")
        runs: list[list[int]] = []
        for i, s in zip(d.index, d.s, strict=True):
            if runs and abs(s - profiles.s[runs[-1][-1]] - step) < step / 2:
                runs[-1].append(i)
            else:
                runs.append([i])
        for run in runs:
            g = profiles.loc[run]
            span = covered(g.s, step, length)
            narrowest = float(g[f"walk_{side}"].min())
            allowed = allowed_width(span, free_path_m, short)
            mid = g.iloc[len(g) // 2]
            rows.append(
                {
                    "side": side,
                    "s_from": float(g.s.min()),
                    "s_to": float(g.s.max()),
                    "length_m": round(span, 1),
                    "width_min_m": narrowest,
                    "width_median_m": round(float(g[f"walk_{side}"].median()), 2),
                    "allowed_m": allowed,
                    "below": narrowest < allowed - 1e-9,
                    "below_with_accuracy": narrowest + 2 * edge_accuracy_m < allowed - 1e-9,
                    "x": float(mid.x),
                    "y": float(mid.y),
                }
            )
    # typed even when empty, so that selecting the rows below the law selects rows, not columns
    types = {"side": str, "below": bool, "below_with_accuracy": bool} | {
        c: float for c in SECTION_COLUMNS if c not in ("side", "below", "below_with_accuracy")
    }
    return pd.DataFrame(rows, columns=SECTION_COLUMNS).astype(types)


def summary(profiles: pd.DataFrame, blocks: list[Block], step: float, length: float, thresholds: list[float]) -> pd.DataFrame:
    """Per side and block (and ``all``): how much of the street has a mapped sidewalk measured, how much of it up to
    the plots, its width, and the length of street where it is narrower than each threshold: read up to the plots
    (``metres_below_*``), and where what lies beyond it is not known (``metres_open_below_*``, to check)."""
    rows = []
    parts = [(b.id, profiles[profiles.block == b.id]) for b in blocks] + [("all", profiles)]
    for side in SIDES:
        for label, sub in parts:
            w = sub[f"walk_{side}"]
            m, b = sub[w.notna()], sub[bounded(sub, side)]
            o = m[~bounded(m, side)]
            r: dict[str, object] = {
                "side": side,
                "block": label,
                "stations": len(sub),
                "measured_m": round(covered(m.s, step, length), 1),
                "bounded_m": round(covered(b.s, step, length), 1),
                "width_min_m": float(w.min()) if len(m) else np.nan,
                "width_p10_m": round(float(w.quantile(0.1)), 2) if len(m) else np.nan,
                "width_median_m": round(float(w.median()), 2) if len(m) else np.nan,
            }
            for th in thresholds:
                r[f"metres_below_{th:g}m"] = round(covered(b.s[b[f"walk_{side}"] < th], step, length), 1)
                r[f"metres_open_below_{th:g}m"] = round(covered(o.s[o[f"walk_{side}"] < th], step, length), 1)
            rows.append(r)
    return pd.DataFrame(rows)


AREA_COLUMNS = ["street", "measured_m", "bounded_m", "width_median_m", "sections_below", "metres_below",
                "sections_below_with_accuracy", "metres_below_with_accuracy", "metres_open_below", "narrowest_m",
                "worst_x", "worst_y"]  # fmt: skip


def _metres(found: list[tuple[pd.DataFrame, pd.DataFrame, float]], pick: str, step: float, free_path_m: float) -> float:
    """Length of a street's parts with the sidewalk ``measured``, read up to the plots (``bounded``), or narrower than
    the free path where it does not reach them (``open``, to check), both sides added."""
    total = 0.0
    for p, _, n in found:
        for side in SIDES:
            ok, w = bounded(p, side), p[f"walk_{side}"]
            sel = {"measured": w.notna(), "bounded": ok, "open": w.notna() & ~ok & (w < free_path_m)}[pick]
            total += covered(p.s[sel], step, n)
    return round(total, 1)


def scan_area(
    axes: list[tuple[str, BaseGeometry]],
    profiler: Profiler,
    classes: dict[str, set[str]],
    step: float,
    free_path_m: float,
    short: list[tuple[float, float]],
    edge_accuracy_m: float,
    junction_m: float,
    half_width: float = 25.0,
    min_part: float = 20.0,
) -> pd.DataFrame:
    """Every street in an area, measured as the case street is (``geometry.measure_profiles``), with its stretches of
    sidewalk narrower than the law admits (``narrow_sections``): one row per street, the most such metres first."""
    rows = []
    lines = [g for _, g in axes]
    tree = STRtree(lines)
    for k, (name, line) in enumerate(axes):
        found: list[tuple[pd.DataFrame, pd.DataFrame, float]] = []
        others = [lines[j] for j in tree.query(line) if j != k]
        for part in getattr(line, "geoms", [line]):
            if part.length < min_part:
                continue
            p = measure_profiles(part, [], classes, step=step, half_width=half_width, profiler=profiler)
            if "walk_L" not in p:  # the axis is nowhere on a mapped road
                continue
            p = away_from_widenings(away_from_junctions(p.assign(block=""), junctions_along(part, others), junction_m))
            found.append((p, narrow_sections(p, step, part.length, free_path_m, short, edge_accuracy_m), part.length))
        widths = pd.concat([p[f"walk_{side}"] for p, _, _ in found for side in SIDES]) if found else pd.Series(dtype=float)
        widths = widths.dropna()
        if widths.empty:
            continue

        sec = pd.concat([s for _, s, _ in found])
        bad, sure = sec[sec.below], sec[sec.below_with_accuracy]
        worst = bad.sort_values("width_min_m").head(1)
        rows.append(
            {
                "street": name,
                "measured_m": _metres(found, "measured", step, free_path_m),
                "bounded_m": _metres(found, "bounded", step, free_path_m),
                "width_median_m": round(float(widths.median()), 2),
                "sections_below": len(bad),
                "metres_below": round(float(bad.length_m.sum()), 1),
                "sections_below_with_accuracy": len(sure),
                "metres_below_with_accuracy": round(float(sure.length_m.sum()), 1),
                "metres_open_below": _metres(found, "open", step, free_path_m),
                "narrowest_m": float(bad.width_min_m.min()) if len(bad) else np.nan,
                "worst_x": float(worst.x.iloc[0]) if len(worst) else np.nan,
                "worst_y": float(worst.y.iloc[0]) if len(worst) else np.nan,
            }
        )
    out = pd.DataFrame(rows, columns=AREA_COLUMNS)
    keys = ["metres_below_with_accuracy", "metres_below", "metres_open_below", "street"]
    return out.sort_values(keys, ascending=[False, False, False, True], ignore_index=True)
