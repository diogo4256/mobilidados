"""Everything mobilidados reads from TOML, validated: case files, city profiles and the packaged catalogues.

A case file names the street, the analysis parameters and the data sources. A city profile
(``cities/<city>.toml``) holds what every street in that city shares: service URLs, cartography class codes,
licences. ``extends = "../../cities/lisboa.toml"`` merges the profile underneath the case, and a source can start
from one of the profile's ``[source_templates.<name>]`` with ``template = "<name>"``.

The merged configuration is checked against the models below when it is loaded: a misspelt key, a missing value
or a reference to something that does not exist (a source, a vehicle, a design reference) stops the run with a
message that names it, instead of failing halfway through the analysis.
"""

from __future__ import annotations

import datetime as dt
import functools
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Lang = Literal["en", "pt"]
Grade = Literal["M", "D", "I", "P", "NE"]  # evidence grades, see docs/evidence-standard.md
Url = Annotated[str, Field(pattern=r"^https?://\S+$")]


class MobilidadosError(Exception):
    """An error the user can fix (configuration, missing data, changed sources). The CLI prints it without a traceback."""


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- sources -----------------------------------------------------------------------------------------
class Source(Model):
    licence: str = Field(description="SPDX id (e.g. CC-BY-4.0) or what the publisher states, e.g. 'not stated'")
    licence_url: Url | None = None
    licence_evidence: str = ""
    dataset_page: Url | None = None
    attribution: str = ""
    redistributable: bool = Field(False, description="May be copied into a public snapshot (`mobilidados snapshot`)")
    description: str = ""
    note: str = ""


class ArcgisQuery(Source):
    """Features of one MapServer layer intersecting ``envelope``, optionally filtered by ``where``."""

    kind: Literal["arcgis_query"]
    url: Url
    envelope: tuple[float, float, float, float]
    envelope_sr: int = 4326
    out_sr: int
    where: str = "1=1"


class HttpFile(Source):
    """One file, e.g. a GTFS zip. ``sha256`` pins the exact version the case used."""

    kind: Literal["http_file"]
    url: Url
    suffix: str = ""
    sha256: str | None = Field(None, pattern="^[0-9a-f]{64}$")


class RemoteFile(Model):
    name: str = Field(pattern=r"^[\w.-]+$")
    url: Url


class Columns(Model):
    """Column names of a point dataset (citizen reports)."""

    lat: str
    lon: str
    date: str
    category: str


class HttpFiles(Source):
    """Several files, e.g. yearly open-data CSVs."""

    kind: Literal["http_files"]
    files: list[RemoteFile] = Field(min_length=1)
    columns: Columns | None = None


class ArcgisIdentify(Source):
    """Point queries made during the analysis; cached in one JSON file and locked afterwards."""

    kind: Literal["arcgis_identify"]
    url: Url
    layers: str
    sr: int
    tolerance: float = 3


AnySource = ArcgisQuery | HttpFile | HttpFiles | ArcgisIdentify


# --- catalogues (packaged in mobilidados/data, extendable per case) -------------------------------------
class VehicleText(Model):
    label: str | None = None
    source_body: str | None = None
    source_mirrors: str | None = None


class Vehicle(Model):
    label: str
    category: str = Field(description="'bus', 'car', ...: a bus's mirrors pass above a car (see mirrors_clear_cars)")
    width_body_m: float = Field(gt=0)
    width_mirrors_m: float = Field(gt=0)
    grade_body: Grade
    grade_mirrors: Grade
    source_body: str
    source_mirrors: str
    mirrors_clear_cars: bool = False
    translations: dict[Lang, VehicleText] = {}

    def text(self, key: Literal["label", "source_body", "source_mirrors"], lang: Lang) -> str:
        tr = self.translations.get(lang)
        return str((getattr(tr, key) if tr else None) or getattr(self, key))


class Document(Model):
    title: str
    publisher: str
    year: int
    url: Url
    document_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    nature: str
    url_checked: str = ""
    isbn: str = ""


class ReferenceText(Model):
    label: str | None = None
    scope: str | None = None
    derivation: str | None = None


class Reference(Model):
    """A design reference with an explicit scope, never a universal rule."""

    id: str
    document: str
    page: int
    pdf_page: int
    kind: Literal["reference_profile", "conditional_value", "secondary_citation"]
    value_m: float
    also_m: float | None = None
    label: str
    scope: str
    derivation: str = ""
    quote: str
    quote_location: Literal["text", "image"] = "text"
    extraction: str = ""
    translations: dict[Lang, ReferenceText] = {}

    def text(self, key: Literal["label", "scope", "derivation"], lang: Lang) -> str:
        tr = self.translations.get(lang)
        return str((getattr(tr, key) if tr else None) or getattr(self, key))


class Standards(Model):
    documents: dict[str, Document]
    references: list[Reference]

    @model_validator(mode="after")
    def _documents_exist(self) -> Standards:
        missing = sorted({r.document for r in self.references} - set(self.documents))
        if missing:
            raise ValueError(f"references cite unknown documents: {missing}")
        return self

    def reference(self, ref_id: str) -> tuple[Reference, Document]:
        ref = next((r for r in self.references if r.id == ref_id), None)
        if ref is None:
            raise MobilidadosError(f"unknown design reference {ref_id!r}")
        return ref, self.documents[ref.document]


def _packaged(name: str) -> dict[str, Any]:
    return tomllib.loads(resources.files("mobilidados.data").joinpath(name).read_text(encoding="utf-8"))


@functools.cache
def vehicle_catalogue() -> dict[str, Vehicle]:
    return {k: Vehicle.model_validate(v) for k, v in _packaged("vehicles.toml")["vehicles"].items()}


@functools.cache
def standards_catalogue() -> Standards:
    return Standards.model_validate(_packaged("standards.toml"))


# --- the case ------------------------------------------------------------------------------------------
class CaseInfo(Model):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str
    language: Lang = "en"
    reference_run: dt.date | None = None
    question: str = ""


class City(Model):
    id: str
    name: str
    country: str = ""
    crs: int = Field(description="Projected CRS in metres (EPSG code)")


class Cartography(Model):
    class_field: str
    road: list[str] = Field(min_length=1)
    parking: list[str] = Field(min_length=1)
    sidewalk: list[str] = []
    plot: list[str] = []
    survey: str = ""
    accuracy_note: str = ""

    def roles(self) -> dict[str, set[str]]:
        """Cartography class codes per role: road, parking, sidewalk, plot."""
        return {"road": set(self.road), "parking": set(self.parking), "sidewalk": set(self.sidewalk), "plot": set(self.plot)}


class Axes(Model):
    name_field: str


class Network(Model):
    """Field names of a routing network layer queried with identify (e.g. Lisbon: ``[EID]``, ``[Direction]``)."""

    edge: str
    direction: str
    status: str
    open_value: str


class Block(Model):
    id: str
    start: float
    end: float
    label: str = ""


class Street(Model):
    name: str
    headings: dict[Literal["+", "-"], str] = Field(description="Labels of the directions of travel along the axis")
    sides: dict[Literal["L", "R"], str] = {"L": "L", "R": "R"}
    blocks: list[Block] = []

    @model_validator(mode="after")
    def _contiguous_blocks(self) -> Street:
        for a, b in zip(self.blocks, self.blocks[1:], strict=False):
            if a.end != b.start:
                raise ValueError(f"blocks must be contiguous and in order: {a.id} ends at {a.end}, {b.id} starts at {b.start}")
        if any(b.start >= b.end for b in self.blocks):
            raise ValueError("every block needs start < end")
        return self

    def heading_label(self, heading: int) -> str:
        """Label of a direction of travel along the street axis (+1 = increasing s)."""
        return self.headings["+" if heading > 0 else "-"]


class Profiles(Model):
    cartography: str = "cartography"
    axes: str = "street_axes"
    step_m: float = Field(0.5, gt=0)
    half_width_m: float = Field(25, gt=0)
    narrow_max_m: float = 7.0
    check_points_s: list[float] = []

    @model_validator(mode="after")
    def _check_points_on_grid(self) -> Profiles:
        off = [s for s in self.check_points_s if abs(s / self.step_m - round(s / self.step_m)) > 1e-9]
        if off:
            raise ValueError(f"check_points_s {off} are not multiples of step_m = {self.step_m}")
        return self


class Direction(Model):
    source: str
    stations_s: list[float] = Field(min_length=1)


class ReferenceStop(Model):
    route: str
    direction_id: int
    stop_id: str
    s_m: float = Field(description="Position of the stop along the street axis")
    heading: Literal[1, -1]


class Transit(Model):
    source: str
    service_date: dt.date
    routes: list[str] = Field(min_length=1)
    speeds_kmh: list[float] = Field([15, 20], min_length=1)
    buffer_m: float = 12
    reference_stops: list[ReferenceStop] = Field(min_length=1)


class Envelope(Model):
    bus: str
    car: str
    scenarios: list[Annotated[list[str], Field(min_length=1, max_length=2)]] = Field(min_length=1)


class Occurrences(Model):
    source: str
    window_m: float = 300
    max_dist_m: float = 12
    min_street_length_m: float = 0
    filters: dict[str, str] = Field(min_length=1, description="Name -> regex on the category; the first one is reported")


class AreaScan(Model):
    cartography: str = "area_cartography"
    axes: str = "area_axes"
    identify_source: str | None = None
    step_m: float = Field(3, gt=0)
    threshold_m: float = 5.5
    reference_m: float = 6.5
    min_pattern_m: float = 30


class Comparison(Model):
    compare: list[str] = []


class Config(Model):
    case: CaseInfo
    city: City
    cartography: Cartography
    axes: Axes
    street: Street
    sources: dict[str, Annotated[AnySource, Field(discriminator="kind")]]
    network: Network | None = None
    profiles: Profiles = Profiles()
    direction: Direction | None = None
    transit: Transit | None = None
    envelope: Envelope | None = None
    occurrences: Occurrences | None = None
    area_scan: AreaScan | None = None
    standards: Comparison = Comparison()
    known_gaps: list[dict[Lang, str]] = []
    vehicles: dict[str, Vehicle] = {}

    def all_vehicles(self) -> dict[str, Vehicle]:
        """The packaged vehicle catalogue plus the case's own ``[vehicles.<id>]``."""
        return vehicle_catalogue() | self.vehicles

    @model_validator(mode="after")
    def _references(self) -> Config:
        errors: list[str] = []

        def need(sid: str, kind: str, where: str) -> None:
            src = self.sources.get(sid)
            if src is None:
                errors.append(f"{where} = {sid!r}: no such source")
            elif src.kind != kind:
                errors.append(f"{where} = {sid!r}: needs a source of kind {kind!r}, not {src.kind!r}")

        need(self.profiles.cartography, "arcgis_query", "profiles.cartography")
        need(self.profiles.axes, "arcgis_query", "profiles.axes")
        if self.direction:
            need(self.direction.source, "arcgis_identify", "direction.source")
            if self.network is None:
                errors.append("[direction] needs a [network] section (field names of the routing network)")
        if self.transit:
            need(self.transit.source, "http_file", "transit.source")
            stray = sorted({r.route for r in self.transit.reference_stops} - set(self.transit.routes))
            if stray:
                errors.append(f"transit.reference_stops use routes not in transit.routes: {stray}")
        if self.occurrences:
            need(self.occurrences.source, "http_files", "occurrences.source")
            src = self.sources.get(self.occurrences.source)
            if isinstance(src, HttpFiles) and src.columns is None:
                errors.append(f"occurrences.source {self.occurrences.source!r} needs `columns` (lat, lon, date, category)")
        if self.area_scan:
            need(self.area_scan.cartography, "arcgis_query", "area_scan.cartography")
            need(self.area_scan.axes, "arcgis_query", "area_scan.axes")
            if self.area_scan.identify_source is not None:
                need(self.area_scan.identify_source, "arcgis_identify", "area_scan.identify_source")
                if self.network is None:
                    errors.append("area_scan.identify_source needs a [network] section")
            if self.transit is None:
                errors.append("[area_scan] needs [transit] (the buses come from its GTFS feed)")
        if self.envelope:
            used = {self.envelope.bus, self.envelope.car, *(v for sc in self.envelope.scenarios for v in sc)}
            errors += [f"envelope: unknown vehicle {v!r}" for v in sorted(used - set(self.all_vehicles()))]
        refs = {r.id for r in standards_catalogue().references}
        errors += [f"standards.compare: unknown design reference {r!r}" for r in self.standards.compare if r not in refs]
        lang = self.case.language
        errors += [f"known_gaps[{i}] has no {lang!r} text" for i, g in enumerate(self.known_gaps) if lang not in g]
        if errors:
            raise ValueError("; ".join(errors))
        return self


# --- loading -----------------------------------------------------------------------------------------
def deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    """Return ``base`` updated recursively with ``over`` (``over`` wins; lists are replaced, not merged)."""
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file, following ``extends`` (relative to the file) recursively."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    parent = data.pop("extends", None)
    if parent:
        data = deep_merge(load_toml((path.parent / parent).resolve()), data)
    return data


def resolve_templates(data: dict[str, Any]) -> dict[str, Any]:
    """Expand ``template = "<name>"`` in each source from ``[source_templates]``, which is then dropped."""
    templates = data.pop("source_templates", {})
    sources = {}
    for sid, src in data.get("sources", {}).items():
        name = src.get("template")
        if name is not None and name not in templates:
            raise MobilidadosError(f"sources.{sid}: unknown template {name!r} (known: {sorted(templates)})")
        sources[sid] = deep_merge(templates[name], {k: v for k, v in src.items() if k != "template"}) if name else src
    return data | {"sources": sources}


@dataclass(frozen=True)
class Case:
    """A loaded case: its folder, its validated configuration and where results go."""

    root: Path
    config: Config
    results_dir: Path

    @classmethod
    def load(cls, case_dir: str | Path, results_dir: str | Path | None = None) -> Case:
        """Load ``<case_dir>/case.toml``. ``results_dir`` defaults to ``<case_dir>/results``."""
        root = Path(case_dir).resolve()
        path = root / "case.toml"
        if not path.exists():
            raise MobilidadosError(f"{path} not found")
        try:
            config = Config.model_validate(resolve_templates(load_toml(path)))
        except ValidationError as e:
            raise MobilidadosError(f"{path}: invalid configuration\n{e}") from None
        return cls(root=root, config=config, results_dir=Path(results_dir).resolve() if results_dir else root / "results")

    @property
    def id(self) -> str:
        return self.config.case.id

    @property
    def lang(self) -> Lang:
        return self.config.case.language

    @property
    def crs(self) -> int:
        return self.config.city.crs

    @property
    def raw_dir(self) -> Path:
        """Downloaded source data (never committed; re-created by ``mobilidados fetch``)."""
        return self.root / "data" / "raw"

    @property
    def lock_path(self) -> Path:
        return self.root / "sources.lock.json"

    def source(self, source_id: str) -> AnySource:
        try:
            return self.config.sources[source_id]
        except KeyError:
            raise MobilidadosError(f"unknown source {source_id!r} (known: {sorted(self.config.sources)})") from None
