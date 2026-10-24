"""Citizen reports / occurrences (any point dataset with coordinates) attributed to the nearest street.

Counts are reported per 100 m of street so streets of different length can be compared. A report is not a
proven infraction, and small counts are noisy: the ledger grades these as context, not proof.
Only aggregates are written to the results; individual reports stay in the local cache.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from .config import Columns


def load_points(files: list[Path], cols: Columns, crs: int) -> pd.DataFrame:
    """Concatenate the CSVs and project lat/lon. Rows without valid coordinates keep x, y = NaN.

    Dates are parsed file by file, because every file (e.g. one per year) may use its own format and pandas infers a
    single format per call. A date that does not parse stays NaT; ``file_summary`` counts those.
    """

    def read(f: Path) -> pd.DataFrame:
        df = pd.read_csv(f, dtype=str).assign(file=f.name)
        df["date"] = pd.to_datetime(df[cols.date], errors="coerce")
        return df

    df = pd.concat([read(f) for f in files], ignore_index=True)
    lat, lon = pd.to_numeric(df[cols.lat], errors="coerce"), pd.to_numeric(df[cols.lon], errors="coerce")
    ok = lat.notna() & lon.notna()
    df["category"] = df[cols.category]
    df["x"] = df["y"] = np.nan
    df.loc[ok, "x"], df.loc[ok, "y"] = Transformer.from_crs(4326, crs, always_xy=True).transform(lon[ok].to_numpy(), lat[ok].to_numpy())
    return df


def file_summary(points: pd.DataFrame) -> pd.DataFrame:
    """Per file: records, records with coordinates, those of them whose date parsed, and the dates they span.

    The span is the period the counts cover. A file without a located record has 0 for the counts and empty dates.
    """
    located = points[points.x.notna()]
    dated = located[located.date.notna()]
    files = pd.Index(sorted(points.file.unique()), name="file")

    def count(rows: pd.DataFrame) -> pd.Series:
        return rows.groupby("file").size().reindex(files, fill_value=0)

    def day(how: str) -> pd.Series:
        span = dated.groupby("file").date.agg(how)
        return span.map(lambda d: d.date().isoformat()).reindex(files, fill_value="")

    return pd.DataFrame(
        {
            "records": count(points),
            "with_coordinates": count(located),
            "with_date": count(dated),
            "first_date": day("min"),
            "last_date": day("max"),
        }
    ).reset_index()


def attribute_to_streets(points: pd.DataFrame, streets: dict[str, BaseGeometry], window: tuple[float, float, float, float]) -> pd.DataFrame:
    """Keep points inside ``window`` (xmin, ymin, xmax, ymax) and tag each with its nearest street and distance."""
    x0, y0, x1, y1 = window
    w = points[(points.x > x0) & (points.x < x1) & (points.y > y0) & (points.y < y1)].copy()
    names, geoms = list(streets), list(streets.values())
    pts = [Point(a, b) for a, b in zip(w.x, w.y, strict=True)]
    idx = STRtree(geoms).nearest(pts)
    w["street"] = [names[i] for i in idx]
    w["dist_m"] = [geoms[i].distance(p) for i, p in zip(idx, pts, strict=True)]
    return w


def rates_by_street(
    points: pd.DataFrame, streets: dict[str, BaseGeometry], filters: dict[str, str], max_dist: float = 12.0, min_length: float = 0.0
) -> pd.DataFrame:
    """Per street: count and rate per 100 m for each named category filter (regex on ``category``).

    Sorted by the first filter's rate (highest first), then by street name, so the rank of a street is its row.
    """
    near = points[points.dist_m <= max_dist]
    out = pd.DataFrame({"street": list(streets), "length_m": [round(g.length, 1) for g in streets.values()]})
    for name, rx in filters.items():
        n = near[near.category.str.contains(rx, regex=True, na=False)].groupby("street").size()
        out[f"{name}_n"] = out.street.map(n).fillna(0).astype(int)
        out[f"{name}_per_100m"] = (out[f"{name}_n"] / out.length_m * 100).round(2)
    out = out[out.length_m >= min_length]
    first = next(iter(filters))
    return out.sort_values([f"{first}_per_100m", "street"], ascending=[False, True]).reset_index(drop=True)


def yearly_counts(points: pd.DataFrame, street: str, rx: str, max_dist: float = 12.0) -> pd.DataFrame:
    sel = points[(points.street == street) & (points.dist_m <= max_dist) & points.category.str.contains(rx, regex=True, na=False)]
    return sel.date.dt.year.value_counts().sort_index().rename_axis("year").rename("n").reset_index()
