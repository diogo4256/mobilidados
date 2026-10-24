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
    assert summary.loc["2024.csv", "with_date"] == 2
    assert (summary.loc["2024.csv", "first_date"], summary.loc["2024.csv", "last_date"]) == (
        "2024-01-05",
        "2024-03-10",
    )  # the period the counts cover
    assert tuple(summary.loc["2025.csv", ["records", "with_coordinates", "with_date"]]) == (1, 1, 1)
    assert (summary.loc["2025.csv", "first_date"], summary.loc["2025.csv", "last_date"]) == ("2025-06-30", "2025-06-30")


def test_every_file_is_parsed_with_its_own_date_format(tmp_path):
    first = tmp_path / "2024.csv"
    first.write_text(HEADER + "38.75,-9.15,2024-01-05 08:30:00.000,Lixo\n38.76,-9.14,2024-03-10 17:45:10.000,Lixo\n", encoding="utf-8")
    second = tmp_path / "2025.csv"
    second.write_text(HEADER + "38.75,-9.15,2025-06-30,Lixo\n", encoding="utf-8")
    for files in ([first, second], [second, first]):
        points = load_points(files, COLS, crs=3763)
        assert points.date.notna().all()  # one file's format does not turn another file's dates into NaT
    summary = file_summary(load_points([first, second], COLS, crs=3763)).set_index("file")
    assert (summary.loc["2024.csv", "first_date"], summary.loc["2024.csv", "last_date"]) == ("2024-01-05", "2024-03-10")
    assert summary.loc["2025.csv", "first_date"] == "2025-06-30"


def test_located_records_whose_date_does_not_parse_are_counted_apart(tmp_path):
    f = tmp_path / "2024.csv"
    f.write_text(
        HEADER + "38.75,-9.15,2024-01-05,Lixo\n38.76,-9.14,not a date,Lixo\n38.77,-9.13,2024-02-20,Lixo\n,,2024-07-01,Lixo\n",
        encoding="utf-8",
    )
    row = file_summary(load_points([f], COLS, crs=3763)).iloc[0]
    assert (row.records, row.with_coordinates, row.with_date) == (4, 3, 2)
    assert (row.first_date, row.last_date) == ("2024-01-05", "2024-02-20")


def test_a_file_without_a_located_record_has_zero_counts_and_no_dates(tmp_path):
    empty = tmp_path / "2023.csv"
    empty.write_text(HEADER + ",,2023-02-01,Lixo\n,,2023-03-01,Lixo\n", encoding="utf-8")
    summary = file_summary(load_points([empty, *write_csvs(tmp_path)], COLS, crs=3763))
    assert summary.file.tolist() == ["2023.csv", "2024.csv", "2025.csv"]
    row = summary.iloc[0]
    assert (row.records, row.with_coordinates, row.with_date) == (2, 0, 0)
    assert (row.first_date, row.last_date) == ("", "")
    assert [str(dtype) for dtype in summary.dtypes[["records", "with_coordinates", "with_date"]]] == ["int64"] * 3
