"""The area scan on an area where no bus runs along any street axis: empty tables that keep their columns."""

import pandas as pd
from shapely.geometry import LineString

from mobilidados import area_scan
from mobilidados.geometry import Profiler


def test_an_area_without_buses_gives_empty_tables_with_their_columns(tmp_path):
    road = [("road", LineString([(-5, 0), (5, 0)]).buffer(1))]
    roles = {"road": {"road"}, "parking": {"parking"}, "sidewalk": set(), "plot": set()}
    axes = [("Rua Sem Autocarros", LineString([(0, -50), (0, 50)]))]
    stations = area_scan.scan(axes, Profiler(road), roles, {}, pd.Series(dtype=int), pd.Series(dtype=str))
    assert stations.empty
    assert stations.columns.tolist() == area_scan.STATION_COLUMNS
    ranked = area_scan.rank_streets(stations, step=3, threshold=5.5, reference=6.5, cache=None, net=None)
    assert ranked.empty
    assert {"street", "metres_with_pattern", "metres_below_6.5m", "traffic"} <= set(ranked.columns)
    # written and read back as the pipeline does, the table is empty, not missing
    ranked.to_csv(tmp_path / "area_streets.csv", index=False)
    assert pd.read_csv(tmp_path / "area_streets.csv").columns.tolist() == ranked.columns.tolist()
