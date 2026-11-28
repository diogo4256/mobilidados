"""Which vehicles ran the street's routes, day by day, from a third party's daily records (``[fleet]``).

**Data.** An ``http_series`` source: one file per route and day, each a list of the vehicles recorded on that route
that day, as moverlisboa.com serves them (``/api/carris/historico/daily/vehicles``): the operator's fleet number
(``id_veiculo``), the route (``linha``, the GTFS route_id) and the model the publisher assigns to the vehicle
(``modelo``). A day with no record is an empty list.

**What it gives.** For each route: the vehicle-days per model, the distinct vehicles and the range of their fleet
numbers, and whether the model's series holds the vehicle whose sheet gives the bus width in ``[envelope]``
(``fleet_number`` in the vehicle catalogue). A model label that ends with a range of numbers, such as
"Standard MAN GNC (2601-2820)", is the publisher's grouping of the fleet by number; the series is read from it.

**What it is not.** The vehicles that reported positions on the route, as the publisher matched them to it, not the
operator's own assignment; and the model is the publisher's label, not the operator's technical sheet.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from .config import HttpSeries, MobilidadosError

SERIES = re.compile(r"\((\d+)\s*-\s*(\d+)\)\s*$")
FIELDS = {"id_veiculo": "vehicle", "linha": "route_id", "modelo": "model"}


def series(model: str) -> tuple[int, int] | None:
    """The range of fleet numbers a model label ends with, e.g. ``(2601-2820)``; None if it gives none."""
    m = SERIES.search(model)
    return (int(m.group(1)), int(m.group(2))) if m else None


def load(folder: Path, src: HttpSeries) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Records (day, route_id, vehicle, model) of every file of ``src``, and per file the distinct vehicles kept.

    Only records whose route is the one asked for are kept: a service asked for one route may also list others."""
    rows, files = [], []
    for route in src.routes:
        for day in src.days():
            path = folder / f"{route}_{day.isoformat()}.json"
            if not path.exists():
                raise MobilidadosError(f"{path} is missing: run `mobilidados fetch` first")
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise MobilidadosError(f"{path}: expected a list of vehicle records, got {type(data).__name__}")
            kept: set[str] = set()
            for rec in data:
                missing = sorted(set(FIELDS) - set(rec))
                if missing:
                    raise MobilidadosError(f"{path}: a record has no {missing}")
                if str(rec["linha"]) != route:
                    continue
                rows.append({"day": day.isoformat(), **{new: str(rec[old]) for old, new in FIELDS.items()}})
                kept.add(str(rec["id_veiculo"]))
            files.append({"route_id": route, "day": day.isoformat(), "vehicles": len(kept)})
    cols = ["day", *FIELDS.values()]
    return pd.DataFrame(rows, columns=cols).drop_duplicates(), pd.DataFrame(files)


def models(records: pd.DataFrame, names: dict[str, str], envelope_number: int | None) -> pd.DataFrame:
    """Vehicle-days per route and model, with the vehicles' numbers and whether the series holds ``envelope_number``."""
    out = []
    for (route_id, model), g in records.groupby(["route_id", "model"], sort=True):
        numbers = pd.to_numeric(g.vehicle, errors="coerce").dropna()
        rng = series(str(model))
        out.append(
            {
                "route": names.get(str(route_id), str(route_id)),
                "route_id": route_id,
                "model": model,
                "vehicle_days": len(g),
                "vehicles": g.vehicle.nunique(),
                "number_min": int(numbers.min()) if len(numbers) else None,
                "number_max": int(numbers.max()) if len(numbers) else None,
                "envelope_series": bool(rng and envelope_number is not None and rng[0] <= envelope_number <= rng[1]),
            }
        )
    df = pd.DataFrame(
        out, columns=["route", "route_id", "model", "vehicle_days", "vehicles", "number_min", "number_max", "envelope_series"]
    )
    df["share"] = (df.vehicle_days / df.groupby("route_id").vehicle_days.transform("sum")).round(4)
    return df.sort_values(["route", "vehicle_days", "model"], ascending=[True, False, True]).astype(
        {"number_min": "Int64", "number_max": "Int64"}
    )


def days(files: pd.DataFrame, names: dict[str, str]) -> pd.DataFrame:
    """Per route: the days asked for, those with at least one vehicle recorded, and the first and last of them."""
    out = []
    for route_id, g in files.groupby("route_id", sort=True):
        seen = g[g.vehicles > 0]
        out.append(
            {
                "route": names.get(str(route_id), str(route_id)),
                "route_id": route_id,
                "days_asked": len(g),
                "days_with_records": len(seen),
                "first_day": seen.day.min() if len(seen) else "",
                "last_day": seen.day.max() if len(seen) else "",
                "vehicle_days": int(g.vehicles.sum()),
            }
        )
    return pd.DataFrame(out).sort_values("route")
