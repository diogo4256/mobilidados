"""Design references (``data/standards.toml``) and the comparison of a measured width against them."""

from __future__ import annotations

import tomllib
from importlib import resources

import pandas as pd


def catalogue() -> dict:
    return tomllib.loads(resources.files("streetfit.data").joinpath("standards.toml").read_text(encoding="utf-8"))


def reference(ref_id: str) -> tuple[dict, dict]:
    cat = catalogue()
    ref = next(r for r in cat["references"] if r["id"] == ref_id)
    return ref, cat["documents"][ref["document"]]


def compare(measured: float, ref_ids: list[str]) -> pd.DataFrame:
    """Measured width minus each reference value. The scope column must be read before drawing conclusions."""
    rows = []
    for rid in ref_ids:
        ref, doc = reference(rid)
        rows.append(
            {
                "reference": rid,
                "kind": ref["kind"],
                "value_m": ref["value_m"],
                "also_m": ref.get("also_m"),
                "measured_m": measured,
                "difference_m": round(measured - ref["value_m"], 2),
                "scope": ref["scope"],
                "document": doc["title"],
                "page": ref["page"],
            }
        )
    return pd.DataFrame(rows)
