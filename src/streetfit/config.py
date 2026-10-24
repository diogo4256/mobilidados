"""Case configuration: a TOML file per case, optionally extending a city profile.

A case file names the street, the analysis parameters and the data sources. A city profile
(``cities/<city>.toml``) holds what every street in that city shares: service URLs, cartography
class codes, licences. ``extends = "../../cities/lisboa.toml"`` merges the profile underneath the case.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def deep_merge(base: dict, over: dict) -> dict:
    """Return ``base`` updated recursively with ``over`` (``over`` wins; lists are replaced, not merged)."""
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_toml(path: Path) -> dict:
    """Load a TOML file, following ``extends`` (relative to the file) recursively."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    parent = data.pop("extends", None)
    if parent:
        data = deep_merge(load_toml((path.parent / parent).resolve()), data)
    return data


@dataclass(frozen=True)
class Block:
    id: str
    start: float
    end: float
    label: str = ""


@dataclass
class Case:
    """A loaded case. ``cfg`` keeps the full merged TOML; typed accessors cover what the pipeline needs."""

    root: Path
    cfg: dict[str, Any]
    blocks: list[Block] = field(default_factory=list)

    @classmethod
    def load(cls, case_dir: str | Path) -> Case:
        root = Path(case_dir).resolve()
        cfg = load_toml(root / "case.toml")
        for key in ("case", "street", "sources"):
            if key not in cfg:
                raise ValueError(f"{root / 'case.toml'}: missing [{key}] section")
        blocks = [Block(b["id"], float(b["from"]), float(b["to"]), b.get("label", "")) for b in cfg["street"].get("blocks", [])]
        return cls(root=root, cfg=cfg, blocks=blocks)

    # --- identity -------------------------------------------------------------------------------
    @property
    def id(self) -> str:
        return self.cfg["case"]["id"]

    @property
    def lang(self) -> str:
        return self.cfg["case"].get("language", "en")

    @property
    def crs(self) -> int:
        return int(self.cfg["city"]["crs"])

    # --- paths ------------------------------------------------------------------------------------
    @property
    def raw_dir(self) -> Path:
        """Downloaded source data (never committed; re-created by ``streetfit fetch``)."""
        return self.root / "data" / "raw"

    @property
    def results_dir(self) -> Path:
        """Derived tables, figures and the findings ledger (committed for the reference run)."""
        return self.root / "results"

    @property
    def lock_path(self) -> Path:
        return self.root / "sources.lock.json"

    # --- sections -------------------------------------------------------------------------------
    def section(self, name: str) -> dict[str, Any]:
        return self.cfg.get(name, {})

    def source(self, source_id: str) -> dict[str, Any]:
        """A source definition, with its ``template`` (from the city profile) merged underneath."""
        src = dict(self.cfg["sources"][source_id])
        tpl = src.pop("template", None)
        if tpl:
            src = deep_merge(self.cfg["source_templates"][tpl], src)
        src["id"] = source_id
        return src

    def source_ids(self) -> list[str]:
        return list(self.cfg["sources"])

    def classes(self, role: str) -> set[str]:
        """Cartography class codes for a role (road, parking, sidewalk, plot), from the city profile."""
        return set(self.cfg["cartography"][role])

    def heading_label(self, heading: int) -> str:
        """Human label for a direction of travel along the street axis (+1 = increasing s)."""
        return self.cfg["street"]["headings"]["+" if heading > 0 else "-"]
