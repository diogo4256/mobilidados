"""Figures generated from the result tables only (no number is typed by hand)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.image
import matplotlib.style
import numpy as np
from matplotlib.figure import Figure

from . import envelope, i18n
from .config import Case, Lang, Vehicle

if TYPE_CHECKING:
    from .pipeline import Run

INK, MUTED, GRID = "#1f2933", "#6b7280", "#d9dee5"
FREE, BUS, BUS2, CAR, STRIP, ALERT = "#c9ced6", "#e8915b", "#c8553d", "#5b8fc9", "#8fbfe0", "#b42318"
FREE_ALT = "#aab3bf"  # the free width an alternative layout would leave: a neutral grey, it is an option, not a verdict

STYLE: dict[Any, Any] = {
    "font.size": 10,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def t(key: str, lang: Lang, **kw: Any) -> str:
    return i18n.t(f"figure.{key}", lang, **kw)


def num(x: float, lang: Lang, sign: bool = False) -> str:
    return i18n.num(x, lang, sign=sign)


def make_all(run: Run) -> None:
    out = run.case.results_dir / "figures"
    out.mkdir(parents=True, exist_ok=True)
    cfg, lang = run.cfg, run.case.lang
    # matplotlib's own defaults first, so a machine's matplotlibrc (another font, another dpi) does not change the figures
    with matplotlib.style.context(["default", STYLE]):
        figs = {"free_width_profile": profile(run, lang)}
        if cfg.envelope:
            figs["width_budget"] = width_budget(run, lang)
        if cfg.transit:
            figs["trips_per_hour"] = trips_per_hour(run, lang)
        if cfg.area_scan and cfg.transit and (fig := area(run, lang)) is not None:
            figs["area_streets"] = fig
        note = credit(run.case)
        for old in out.glob("*.png"):
            if old.stem not in figs:  # made by an earlier configuration
                old.unlink()
        for name, f in figs.items():
            f.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=6.5, color=MUTED)
            save(f, out / f"{name}.png")


def save(fig: Figure, path: Path) -> None:
    """Write a figure, leaving the file as it is when its pixels are the same: the PNG compression differs from one
    platform to another, so the same figure drawn on another machine would otherwise show up as changed."""
    png = io.BytesIO()
    fig.savefig(png, format="png", dpi=160)
    if path.exists() and np.array_equal(matplotlib.image.imread(path), matplotlib.image.imread(io.BytesIO(png.getvalue()))):
        return
    path.write_bytes(png.getvalue())


def credit(case: Case) -> str:
    """Data credit printed on every figure (attribution required by the inputs' licences)."""
    parts: list[str] = []
    for s in case.config.sources.values():
        item = f"{s.attribution} ({s.licence})" if s.licence_url else s.attribution
        if item and item not in parts:
            parts.append(item)
    return t("data_credit", case.lang, sources="; ".join(parts))


def width_budget(run: Run, lang: Lang) -> Figure:
    e = run.cfg.envelope
    assert e is not None
    free = float(run.table("summary_by_block").set_index("block").loc["all", "free_median"])
    vehicles = run.cfg.all_vehicles()
    bus, car = vehicles[e.bus], vehicles[e.car]

    def cat(v: Vehicle) -> str:
        return t(v.category, lang) if v.category in ("bus", "car") else v.category

    wp = run.table("without_parking").set_index("without")
    one_side = float(wp.loc[["L", "R"], "free_median"].min())
    lo, hi = int(wp.loc["L", "places_min"]), int(wp.loc["L", "places_max"])
    places = i18n.t("ledger.places", lang, count=hi, n=hi) if lo == hi else i18n.t("ledger.places_range", lang, lo=lo, hi=hi)

    def margin(body: float, mirrors: float) -> str:
        """What is left of the free width (or missing from it) with bodies only, and with mirrors."""
        if body > free:
            return t("short_by", lang, x=num(body - free, lang), xm=num(mirrors - free, lang))
        return t("margin", lang, x=num(free - body, lang, sign=True), xm=num(free - mirrors, lang, sign=True))

    rows = [
        (
            t("without_one_side", lang),
            [(one_side, FREE_ALT, f"{num(one_side, lang)} m")],
            0.0,
            t("removes", lang, m=i18n.num(float(wp.loc["L", "parking_removed_m"]), lang, 0), places=places),
        ),
        (t("free_width_short", lang), [(free, FREE, f"{num(free, lang)} m")], 0.0, ""),
        (
            f"{cat(bus)} × {cat(car)}",
            [(bus.width_body_m, BUS, num(bus.width_body_m, lang)), (car.width_body_m, CAR, num(car.width_body_m, lang))],
            car.width_mirrors_m - car.width_body_m,
            margin(envelope.widths(bus, car, False), envelope.widths(bus, car, True)),
        ),
        (
            f"{cat(bus)} × {cat(bus)}",
            [(bus.width_body_m, BUS, num(bus.width_body_m, lang)), (bus.width_body_m, BUS2, num(bus.width_body_m, lang))],
            2 * (bus.width_mirrors_m - bus.width_body_m),
            margin(envelope.widths(bus, bus, False), envelope.widths(bus, bus, True)),
        ),
    ]
    fig = Figure(figsize=(10, 4.4))
    ax = fig.subplots()
    for i, (lab, parts, mir, note) in enumerate(rows):
        y, x = len(rows) - 1 - i, 0.0
        for w, col, txt in parts:
            ax.barh(y, w, left=x, height=0.55, color=col, edgecolor="white", lw=1.5)
            ax.text(x + w / 2, y, txt, ha="center", va="center", color=INK, fontsize=10)
            x += w
        if mir:
            ax.barh(y, mir, left=x, height=0.55, color="white", edgecolor=MUTED, lw=0.8, hatch="////")
        if note:
            # on a white ground, so the free-width line (zorder 2) does not cross the words; below the axis spine (2.5)
            ax.text(
                0,
                y - 0.38,
                note,
                ha="left",
                va="top",
                fontsize=9,
                color=MUTED,
                zorder=2.2,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
            )
        ax.text(-0.1, y, lab, ha="right", va="center", fontsize=10, color=INK)
    ax.axvline(free, color=ALERT, lw=1.6, ls="--")
    ax.text(free + 0.05, len(rows) - 0.4, f"{t('limit', lang)} {num(free, lang)} m", color=ALERT, fontsize=10, va="center")
    ax.set_xlim(0, max(6.2, 2 * bus.width_mirrors_m + 0.2, one_side + 0.6))
    ax.set_ylim(-0.9, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xlabel(t("width_m", lang))
    fig.subplots_adjust(left=0.27, right=0.98, top=0.95, bottom=0.16)
    return fig


def trips_per_hour(run: Run, lang: Lang) -> Figure:
    assert run.cfg.transit is not None
    tph = run.table("trips_per_hour").set_index("hour")
    fig = Figure(figsize=(9.5, 3.6))
    ax = fig.subplots()
    w = 0.4
    for k, (col, color) in enumerate(zip(tph.columns, (BUS, CAR), strict=False)):
        ax.bar(tph.index + (k - 0.5) * w, tph[col], w, label=f"{col} ({int(tph[col].sum())})", color=color)
    ax.set_xlabel(t("hour", lang))
    ax.set_ylabel(t("trips_per_hour", lang))
    ax.legend(frameon=False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_title(t("weekday_trips", lang, day=run.cfg.transit.service_date), loc="left", fontsize=10, color=INK)
    fig.tight_layout()
    return fig


def profile(run: Run, lang: Lang) -> Figure:
    p = run.table("profiles").dropna(subset=["free_width"])
    fig = Figure(figsize=(10, 3.8))
    ax = fig.subplots()
    for i, b in enumerate(run.cfg.street.blocks):
        ax.axvspan(b.start, b.end, color=GRID if i % 2 else "white", alpha=0.5, lw=0)
        ax.text((b.start + b.end) / 2, 0.15, b.id, ha="center", color=MUTED, fontsize=9)
    ax.plot(p.s, p.free_width, color=INK, lw=1.4, label=t("free_width", lang))
    ax.plot(p.s, p.strip_L, color=STRIP, lw=1, label=t("strips", lang))
    ax.plot(p.s, p.strip_R, color=STRIP, lw=1, ls="--")
    if run.cfg.standards.compare:
        for v in sorted(set(run.table("standards_comparison").value_m)):
            ax.axhline(v, color=ALERT, lw=0.8, ls=":")
            ax.text(p.s.max(), v + 0.08, f"{num(v, lang)} m", color=ALERT, ha="right", fontsize=8)
    ax.set_ylim(0, max(10, p.free_width.quantile(0.98) + 0.5))
    ax.set_xlabel(t("along", lang))
    ax.set_ylabel("m")
    ax.set_title(t("profile_title", lang), loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.tight_layout()
    return fig


def area(run: Run, lang: Lang) -> Figure | None:
    sc = run.cfg.area_scan
    assert sc is not None
    a = run.table("area_streets").dropna(subset=["free_width_median_m"])
    if a.empty:
        return None
    me = run.cfg.street.name
    fig = Figure(figsize=(9, 5))
    ax = fig.subplots()
    # the case's pattern: two-way traffic + parking on both sides + narrow free width over a minimum length
    pattern = (a.traffic == "two-way") & (a.metres_with_pattern >= sc.min_pattern_m)
    one_way = (a.metres_with_pattern >= sc.min_pattern_m) & ~pattern
    rest = ~pattern & ~one_way
    ax.scatter(a.buses_per_day[rest], a.free_width_median_m[rest], s=20, color=MUTED, alpha=0.45, lw=0)
    ax.scatter(
        a.buses_per_day[one_way],
        a.free_width_median_m[one_way],
        s=32,
        facecolor="white",
        edgecolor=BUS,
        lw=1.4,
        label=t("pattern_one_way", lang),
    )
    ax.scatter(a.buses_per_day[pattern], a.free_width_median_m[pattern], s=40, color=ALERT, label=t("pattern_two_way", lang))
    for k, (_, row) in enumerate(a[pattern].sort_values("free_width_median_m").iterrows()):
        ax.annotate(
            row.street,
            (row.buses_per_day, row.free_width_median_m),
            xytext=(8, -14 if k % 2 == 0 else 8),
            textcoords="offset points",
            fontsize=8.5,
            color=ALERT if row.street == me else INK,
            weight="bold" if row.street == me else None,
        )
    ax.axhline(sc.reference_m, color=ALERT, lw=0.8, ls=":")
    ax.set_xlabel(t("buses_day", lang))
    ax.set_ylabel(t("median_free", lang))
    ax.set_title(t("area_title", lang), loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(color=GRID, lw=0.5)
    fig.tight_layout()
    return fig
