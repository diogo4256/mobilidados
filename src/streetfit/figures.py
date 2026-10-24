"""Figures generated from the result tables only (no number is typed by hand)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import envelope  # noqa: E402
from .i18n import num, t  # noqa: E402

INK, MUTED, GRID = "#1f2933", "#6b7280", "#d9dee5"
FREE, BUS, BUS2, CAR, STRIP, ALERT = "#c9ced6", "#e8915b", "#c8553d", "#5b8fc9", "#8fbfe0", "#b42318"

plt.rcParams.update(
    {
        "font.size": 10,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def make_all(run) -> None:
    out = run.case.results_dir / "figures"
    out.mkdir(parents=True, exist_ok=True)
    lang = run.case.lang
    width_budget(run, lang).savefig(out / "width_budget.png", dpi=160)
    trips_per_hour(run, lang).savefig(out / "trips_per_hour.png", dpi=160)
    profile(run, lang).savefig(out / "free_width_profile.png", dpi=160)
    if "area_streets" in run.tables or (run.tables_dir / "area_streets.csv").exists():
        f = area(run, lang)
        if f:
            f.savefig(out / "area_streets.png", dpi=160)
    plt.close("all")


def width_budget(run, lang):
    s = run.tables["summary_by_block"].set_index("block").loc["all"]
    free = float(s.free_median)
    e = run.case.section("envelope")
    veh = envelope.load_vehicles(run.case.cfg.get("vehicles"))
    bus, car = veh[e["bus"]], veh[e["car"]]
    cat = lambda v: t(v.category, lang) if v.category in ("bus", "car") else v.category  # noqa: E731
    rows = [
        (t("free_width_short", lang), [(free, FREE, f"{num(free, lang)} m")], 0.0, ""),
        (
            f"{cat(bus)} × {cat(car)}",
            [(bus.width_body_m, BUS, num(bus.width_body_m, lang)), (car.width_body_m, CAR, num(car.width_body_m, lang))],
            car.width_mirrors_m - car.width_body_m,
            f"{t('margin', lang)} {num(free - bus.width_body_m - car.width_body_m, lang, sign=True)} m · "
            f"{t('with_mirrors', lang)} {num(free - envelope.widths(bus, car, True), lang, sign=True)} m",
        ),
        (
            f"{cat(bus)} × {cat(bus)}",
            [(bus.width_body_m, BUS, num(bus.width_body_m, lang)), (bus.width_body_m, BUS2, num(bus.width_body_m, lang))],
            2 * (bus.width_mirrors_m - bus.width_body_m),
            f"{num(2 * bus.width_body_m, lang)} m · {t('with_mirrors', lang)} {num(2 * bus.width_mirrors_m, lang)} m: {t('does_not_fit', lang)}"
            if 2 * bus.width_body_m > free
            else "",
        ),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    for i, (lab, parts, mir, note) in enumerate(rows):
        y, x = len(rows) - 1 - i, 0.0
        for w, col, txt in parts:
            ax.barh(y, w, left=x, height=0.55, color=col, edgecolor="white", lw=1.5)
            ax.text(x + w / 2, y, txt, ha="center", va="center", color=INK, fontsize=10)
            x += w
        if mir:
            ax.barh(y, mir, left=x, height=0.55, color="white", edgecolor=MUTED, lw=0.8, hatch="////")
        if note:
            ax.text(0, y - 0.38, note, ha="left", va="top", fontsize=9, color=MUTED)
        ax.text(-0.1, y, lab, ha="right", va="center", fontsize=10, color=INK)
    ax.axvline(free, color=ALERT, lw=1.6, ls="--")
    ax.text(free + 0.05, len(rows) - 0.4, f"{t('limit', lang)} {num(free, lang)} m", color=ALERT, fontsize=10, va="center")
    ax.set_xlim(0, max(6.2, 2 * bus.width_mirrors_m + 0.2))
    ax.set_ylim(-0.9, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xlabel(t("width_m", lang))
    fig.subplots_adjust(left=0.27, right=0.98, top=0.95, bottom=0.16)
    return fig


def trips_per_hour(run, lang):
    tph = run.tables["trips_per_hour"]
    tph = tph.set_index("hour") if "hour" in tph.columns else tph
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    w = 0.4
    for k, (col, color) in enumerate(zip(tph.columns, (BUS, CAR), strict=False)):
        ax.bar(tph.index + (k - 0.5) * w, tph[col], w, label=f"{col} ({int(tph[col].sum())})", color=color)
    ax.set_xlabel(t("hour", lang))
    ax.set_ylabel(t("trips_per_hour", lang))
    ax.legend(frameon=False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_title(t("weekday_trips", lang, day=run.case.section("transit")["service_date"]), loc="left", fontsize=10, color=INK)
    fig.tight_layout()
    return fig


def profile(run, lang):
    p = run.tables["profiles"].dropna(subset=["free_width"])
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for b in run.case.blocks:
        ax.axvspan(b.start, b.end, color=GRID if run.case.blocks.index(b) % 2 else "white", alpha=0.5, lw=0)
        ax.text((b.start + b.end) / 2, 0.15, b.id, ha="center", color=MUTED, fontsize=9)
    ax.plot(p.s, p.free_width, color=INK, lw=1.4, label=t("free_width", lang))
    ax.plot(p.s, p.strip_L, color=STRIP, lw=1, label=t("strips", lang))
    ax.plot(p.s, p.strip_R, color=STRIP, lw=1, ls="--")
    if "standards_comparison" in run.tables or (run.tables_dir / "standards_comparison.csv").exists():
        import pandas as pd

        sc = run.tables.get("standards_comparison")
        sc = sc if sc is not None else pd.read_csv(run.tables_dir / "standards_comparison.csv")
        for v in sorted(set(sc.value_m)):
            ax.axhline(v, color=ALERT, lw=0.8, ls=":")
            ax.text(p.s.max(), v + 0.08, f"{num(v, lang)} m", color=ALERT, ha="right", fontsize=8)
    ax.set_ylim(0, max(10, p.free_width.quantile(0.98) + 0.5))
    ax.set_xlabel(t("along", lang))
    ax.set_ylabel("m")
    ax.set_title(t("profile_title", lang), loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.tight_layout()
    return fig


def area(run, lang):
    import pandas as pd

    a = run.tables.get("area_streets")
    a = a if a is not None else pd.read_csv(run.tables_dir / "area_streets.csv")
    a = a.dropna(subset=["free_width_median_m"])
    if a.empty:
        return None
    me = run.case.cfg["street"]["name"]
    sc = run.case.section("area_scan")
    fig, ax = plt.subplots(figsize=(9, 5))
    # the case's pattern: two-way traffic + parking on both sides + narrow free width over a minimum length
    pattern = (a.traffic == "two-way") & (a.metres_with_pattern >= sc.get("min_pattern_m", 30))
    one_way = (a.metres_with_pattern >= sc.get("min_pattern_m", 30)) & ~pattern
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
    ax.axhline(sc.get("reference_m", 6.5), color=ALERT, lw=0.8, ls=":")
    ax.set_xlabel(t("buses_day", lang))
    ax.set_ylabel(t("median_free", lang))
    ax.set_title(t("area_title", lang), loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(color=GRID, lw=0.5)
    fig.tight_layout()
    return fig
