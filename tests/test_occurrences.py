"""Loading citizen reports from CSV: rows without usable coordinates are kept, and the per-file summary shows what is located."""

import pytest
from pyproj import Transformer

from streetfit.config import Columns
from streetfit.occurrences import file_summary, load_points

COLS = Columns(lat="latitude", lon="longitude", date="dt_registo", category="tipologia")
HEADER = "latitude,longitude,dt_registo,tipologia\n"


def write_csvs(tmp_path):
    a = tmp_path / "2024.csv"
    a.write_text(
        HEADER
        + "38.75,-9.15,2024-01-05,Estacionamento abusivo\n"  # located
        + ",,2024-02-01,Lixo\n"  # no coordinates
        + "38.76,-9.14,2024-03-10,Estacionamento abusivo\n"  # located
        + "n/a,-9.1,2024-12-01,Lixo\n",  # latitude is not a number
        encoding="utf-8",
    )
    b = tmp_path / "2025.csv"
    b.write_text(HEADER + "38.74,-9.16,2025-06-30,Lixo\n", encoding="utf-8")
    return [a, b]


def test_rows_without_valid_coordinates_are_kept_with_nan(tmp_path):
    df = load_points(write_csvs(tmp_path), COLS, crs=3763)
    assert len(df) == 5
    assert df.file.tolist() == ["2024.csv"] * 4 + ["2025.csv"]
    assert df.x.notna().tolist() == [True, False, True, False, True]
    assert df.y.notna().tolist() == df.x.notna().tolist()
    x, y = Transformer.from_crs(4326, 3763, always_xy=True).transform(-9.15, 38.75)
    assert (df.x[0], df.y[0]) == pytest.approx((x, y))
    assert df.category.tolist()[:2] == ["Estacionamento abusivo", "Lixo"]
    assert df.date.dt.year.tolist() == [2024] * 4 + [2025]


def test_the_summary_counts_records_and_located_records_and_dates_the_located_ones(tmp_path):
    summary = file_summary(load_points(write_csvs(tmp_path), COLS, crs=3763)).set_index("file")
    assert summary.loc["2024.csv", "records"] == 4
    assert summary.loc["2024.csv", "with_coordinates"] == 2
    assert (summary.loc["2024.csv", "first_date"], summary.loc["2024.csv", "last_date"]) == (
        "2024-01-05",
        "2024-03-10",
    )  # the period the counts cover
    assert (summary.loc["2025.csv", "records"], summary.loc["2025.csv", "with_coordinates"]) == (1, 1)
    assert (summary.loc["2025.csv", "first_date"], summary.loc["2025.csv", "last_date"]) == ("2025-06-30", "2025-06-30")
