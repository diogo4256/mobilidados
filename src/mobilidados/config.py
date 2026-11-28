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
    """Point queries made during the analysis; cached in one JSON file, locked each time new answers are saved."""

    kind: Literal["arcgis_identify"]
    url: Url
    layers: str
    sr: int
    tolerance: float = 3


class GitArchive(Source):
    """Vehicle positions from a public git repository that archives a real-time feed, one CSV per snapshot.

    ``commit`` pins the archive: the files and their contents at that commit are fixed by its hash. ``fetch`` reads
    the snapshots of ``period`` and keeps, for ``route_ids``, the positions inside ``envelope``; it writes them with
    one row per snapshot (``mobilidados.archive``), and the lock records the sha256 of what it wrote.
    """

    kind: Literal["git_archive"]
    url: Url
    commit: str = Field(pattern="^[0-9a-f]{40}$")
    path: str = Field(description="Folder of the snapshots inside the repository")
    prefix: str = Field(description="File name before the snapshot time, e.g. 'carris_gtfsrt-'")
    time_format: str = Field("%Y-%m-%d-%H-%M-%S", description="strftime format of the snapshot time in the file name")
    time_zone: str = Field("UTC", description="Time zone of the snapshot time in the file name and of the vehicle timestamps")
    period: tuple[dt.date, dt.date] = Field(description="First and last day (UTC) of the snapshots read")
    route_ids: list[str] = Field(min_length=1)
    envelope: tuple[float, float, float, float] = Field(description="lon_min, lat_min, lon_max, lat_max of the positions kept")

    @model_validator(mode="after")
    def _period_in_order(self) -> GitArchive:
        if self.period[0] > self.period[1]:
            raise ValueError(f"period {self.period[0]} to {self.period[1]}: the first day comes after the last")
        return self


AnySource = ArcgisQuery | HttpFile | HttpFiles | ArcgisIdentify | GitArchive


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
    holidays: list[dt.date] = Field([], description="Public holidays, national and municipal: not working days for [delay]")


class Cartography(Model):
    class_field: str
    road: list[str] = Field(min_length=1)
    parking: list[str] = Field(min_length=1)
    sidewalk: list[str] = []
    plot: list[str] = []
    survey: str | dict[Lang, str] = Field("", description="When and how the cartography was made; text, or text per language")
    accuracy_note: str | dict[Lang, str] = Field("", description="Its stated positional accuracy; text, or text per language")

    def text(self, key: Literal["survey", "accuracy_note"], lang: Lang) -> str:
        value = getattr(self, key)
        return value if isinstance(value, str) else value.get(lang) or next(iter(value.values()), "")

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
    parking_space_m: list[Annotated[float, Field(gt=0)]] = Field(
        [5.0, 5.5, 6.0],
        min_length=1,
        description="Lengths of one longitudinal parking space, to turn metres of mapped parking into places: an "
        "assumption (grade P), given as a range; set it from the municipality's own standard where one is known",
    )
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
    practical_clearance_m: float | None = Field(
        None,
        ge=0,
        description="Room for movement, mirrors and safety that two meeting vehicles need beyond their bodies, from design guidance",
    )
    practical_clearance_source: str = ""


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


class Delay(Model):
    """Time buses spend on a stretch of the street, from archived vehicle positions (``mobilidados.delay``)."""

    source: str = Field(description="A git_archive source of vehicle positions")
    s_from: float = Field(ge=0, description="Start of the stretch measured, along the street axis (m)")
    s_to: float = Field(gt=0, description="End of the stretch (m); keep the stops out of it, where buses also wait for passengers")
    peak_hours: list[Annotated[int, Field(ge=0, le=23)]] = Field([17, 18], min_length=1, description="Local clock hours")
    off_peak_hours: list[Annotated[int, Field(ge=0, le=23)]] = Field(list(range(10, 17)), min_length=1)
    time_zone: str = "Europe/Lisbon"
    exclude_dates: list[dt.date] = Field([], description="Other weekdays that are not working days, besides the city's holidays")
    max_age_s: float = Field(60, gt=0, description="A position reported longer than this before its snapshot is left out")
    max_offset_m: float = Field(20, gt=0, description="A position farther than this from its route's shape is left out")
    control_gap_m: float = Field(150, ge=0, description="Distance along each shape between the stretch and its controls")
    control_m: float = Field(550, gt=0, description="Length of each of the two control stretches")
    reach_m: float = Field(2000, gt=0, description="How far along each shape a trip counts as passing, to count passages")
    max_gap_s: float = Field(720, gt=0, description="Seconds per passage use only the hours whose snapshots are never further apart")
    bootstrap: int = Field(2000, ge=100)
    seed: int = 1

    @model_validator(mode="after")
    def _consistent(self) -> Delay:
        if self.s_from >= self.s_to:
            raise ValueError(f"delay: s_from ({self.s_from}) must be before s_to ({self.s_to})")
        if set(self.peak_hours) & set(self.off_peak_hours):
            raise ValueError(f"delay: hours {sorted(set(self.peak_hours) & set(self.off_peak_hours))} are both peak and off-peak")
        return self


class Parameter(Model):
    """An appraisal input: a central value and the range it is tested over, with its grade and where it comes from."""

    low: float
    central: float
    high: float
    grade: Grade
    unit: str = ""
    label: str = Field(description="What it is, in the case's language")
    source: str = Field(description="Where the value comes from, in the case's language")

    @model_validator(mode="after")
    def _in_order(self) -> Parameter:
        if not self.low <= self.central <= self.high:
            raise ValueError(f"{self.label}: needs low <= central <= high, not {self.low}, {self.central}, {self.high}")
        return self


class Option(Model):
    """A way of giving the space of one parking strip back to the carriageway in some sections, at some hours."""

    id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    label: str
    blocks: list[str] = Field(min_length=1, description="Blocks whose section with parking on both sides loses one side")
    days: Literal["all", "working"] = "all"
    hours: tuple[int, int] = Field((0, 24), description="Local clock hours [from, to) in which parking is not allowed")
    parking_share: str | None = Field(None, description="Parameter: the part of a place's value lost in those hours (none: all of it)")
    compliance: str = Field(description="Parameter: the share of drivers who keep the restriction")
    signs: int = Field(ge=0, description="Vertical signs to put up (C15, with an additional panel for hours)")

    @model_validator(mode="after")
    def _hours(self) -> Option:
        a, b = self.hours
        if not 0 <= a < b <= 24:
            raise ValueError(f"option {self.id}: hours must be 0 <= from < to <= 24, not {self.hours}")
        return self


class Note(Model):
    """A statement of the feasibility study that is not computed: the law, a plan, a known gap."""

    dimension: Literal["technical", "legal", "operational", "social", "evidence", "options"]
    grade: Grade
    text: str
    source: str = ""


class Alternative(Model):
    """A measure whose effect the data cannot estimate: the appraisal gives the bus-hours a year it must save to pay for
    itself, instead of a net present value it could not support."""

    id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    label: str
    signs: int = Field(0, ge=0)
    works: float = Field(0.0, ge=0, description="Other one-off cost (€)")
    yearly: float = Field(0.0, ge=0, description="Recurring cost (€ a year)")
    parking_m: float = Field(0.0, ge=0, description="Metres of parking strip it removes (0: none), valued as an option's places")


class Reroute(Model):
    """Taking some of the street's buses off it by another way round (``mobilidados.reroute``): no parking removed,
    the meetings between the buses that move and those coming the other way gone, a detour for the buses that move."""

    id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    label: str
    moves: list[str] = Field(min_length=1, description="Routes and directions moved off the street, as 'route direction_id' (e.g. '744 0')")


REROUTE_PARAMETERS = ("detour_speed_kmh", "walk_extra_min", "access_weight")


class Correlation(Model):
    """Two inputs that move together in the simulation, with a rank correlation ``rho`` (Iman-Conover)."""

    a: str
    b: str
    rho: float = Field(gt=-1, lt=1)


class Criterion(Model):
    """An effect the appraisal does not put a price on (quality of life, access to the rail network, safety...): how
    each option moves it, with the evidence. The weights between criteria are the decision-maker's, so none are given."""

    id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    dimension: Literal["passengers", "residents", "network", "environment", "safety", "policy", "equity"]
    label: str
    indicator: str = Field(description="What would measure it")
    effects: dict[str, Literal["++", "+", "0", "-", "--", "?"]] = Field(
        description="Option id (or '*' for every option) -> ++, +, 0, -, -- or ? (not known)"
    )
    grade: Grade
    note: str = Field(description="Why each option moves it as stated")
    source: str = ""


REQUIRED_PARAMETERS = ("vot", "time_weight", "load_peak", "bus_cost_h", "occupancy", "car_value",
                       "sign_cost", "marking_cost_m", "enforcement_year", "stall_m")  # fmt: skip


class Appraisal(Model):
    """Feasibility and cost-benefit appraisal of the options (``mobilidados.appraisal``)."""

    horizon_years: int = Field(10, ge=1)
    discount_rate: float = Field(0.05, gt=0, lt=1)
    discount_rates_tested: list[float] = [0.03, 0.07]
    horizons_tested: list[int] = Field([20], description="Other appraisal periods (years) the central NPV is shown for")
    correlations: list[Correlation] = []
    price_year: int
    repaint_every_years: int = Field(5, ge=1)
    draws: int = Field(20000, ge=1000)
    seed: int = 1
    significance: float = Field(
        0.01, gt=0, lt=1, description="p-value below which a junction counts as where buses lose time to oncoming buses"
    )
    offpeak_from_copresence: bool = Field(
        False,
        description="Take the central off-peak excess (parameter offpeak_s) as the peak excess scaled by how often oncoming"
        " buses meet off-peak relative to the peak, where they demonstrably meet (appraisal.offpeak_ratio); its range stays",
    )
    offpeak_scales_with_service: bool = Field(
        False,
        description="Count off-peak passages on Saturdays and Sundays at that day's buses ÷ a working day's: fewer buses"
        " coming the other way, fewer meetings per passage (appraisal.offpeak_scale)",
    )
    parameters: dict[str, Parameter]
    options: list[Option] = Field(min_length=1)
    reroutes: list[Reroute] = []
    reroute_parameters: dict[str, Parameter] = Field(
        {},
        description=f"For the reroutes: {', '.join(REROUTE_PARAMETERS)}; valued at their central value, the range bracketing the break-even",
    )
    safety_references: dict[str, Parameter] = Field(
        {},
        description="Unit costs of a road crash (e.g. one with slight injuries only), at the appraisal's prices: not counted,"
        " since the scheme's effect on crashes is not known, but shown as the crashes over the period that would equal"
        " each option's NPV (appraisal.safety_equivalents)",
    )
    alternatives: list[Alternative] = []
    criteria: list[Criterion] = []
    notes: list[Note] = []
    references: list[str] = Field([], description="The documents the values and notes come from, cited in full with their address")

    @model_validator(mode="after")
    def _references(self) -> Appraisal:
        missing = [k for k in REQUIRED_PARAMETERS if k not in self.parameters]
        missing += [f"{o.id}: {ref}" for o in self.options for ref in (o.parking_share, o.compliance) if ref and ref not in self.parameters]
        if missing:
            raise ValueError(f"appraisal: parameters missing: {missing}")
        ids = [o.id for o in self.options]
        if len(set(ids)) != len(ids):
            raise ValueError(f"appraisal: option ids repeat: {ids}")
        if self.reroutes:
            lacking = [k for k in REROUTE_PARAMETERS if k not in self.reroute_parameters]
            if lacking:
                raise ValueError(f"appraisal: reroutes need reroute_parameters {lacking}")
            bad = [mv for r in self.reroutes for mv in r.moves if len(mv.split()) != 2]
            if bad:
                raise ValueError(f"appraisal: reroute moves are 'route direction_id', not {bad}")
        known = set(self.parameters) | {"excess_s"} | {f"attribution_{i}" for i in ids}
        loose = sorted({x for c in self.correlations for x in (c.a, c.b)} - known)
        if loose:
            raise ValueError(f"appraisal: correlations name inputs that do not exist: {loose}")
        stray = sorted({k for c in self.criteria for k in c.effects} - set(ids) - {"*"})
        if stray:
            raise ValueError(f"appraisal: criteria name options that do not exist: {stray}")
        bare = [c.id for c in self.criteria if not set(ids) <= set(c.effects) and "*" not in c.effects]
        if bare:
            raise ValueError(f"appraisal: criteria {bare} do not say how every option moves them (give each option, or '*')")
        return self


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
    delay: Delay | None = None
    appraisal: Appraisal | None = None
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
            keys = [(r.route, r.direction_id) for r in self.transit.reference_stops]
            twice = sorted({k for k in keys if keys.count(k) > 1})
            if twice:
                errors.append(f"transit.reference_stops give more than one stop for the same (route, direction_id): {twice}")
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
        if self.delay:
            need(self.delay.source, "git_archive", "delay.source")
            if self.transit is None:
                errors.append("[delay] needs [transit] (its routes and their shapes come from the GTFS feed)")
        if self.appraisal:
            if self.delay is None or self.envelope is None:
                errors.append("[appraisal] needs [delay] (the time it values) and [envelope] (the widths it checks)")
            known = {b.id for b in self.street.blocks}
            errors += [f"appraisal option {o.id}: unknown block {b!r}" for o in self.appraisal.options for b in o.blocks if b not in known]
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
    """Load a TOML file, following ``extends`` (relative to the file) recursively.

    The file's values win over the parent's, except ``known_gaps``: the gaps of both are listed, the file's first,
    so a city profile states the gaps every case shares and a case adds its own.
    """
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    parent = data.pop("extends", None)
    if parent:
        base = load_toml((path.parent / parent).resolve())
        gaps = data.get("known_gaps", []) + base.get("known_gaps", [])
        data = deep_merge(base, data) | ({"known_gaps": gaps} if gaps else {})
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
