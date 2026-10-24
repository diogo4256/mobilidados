"""Comparison of a measured width against the design references in ``data/standards.toml``."""

from __future__ import annotations

import pandas as pd

from .config import standards_catalogue


def compare(measured: float, ref_ids: list[str]) -> pd.DataFrame:
    """Measured width minus each reference value. The scope column must be read before drawing conclusions."""
    rows = []
    for rid in ref_ids:
        ref, doc = standards_catalogue().reference(rid)
        rows.append(
            {
                "reference": rid,
                "kind": ref.kind,
                "value_m": ref.value_m,
                "also_m": ref.also_m,
                "measured_m": measured,
                "difference_m": round(measured - ref.value_m, 2),
                "scope": ref.scope,
                "document": doc.title,
                "page": ref.page,
            }
        )
    return pd.DataFrame(rows)
