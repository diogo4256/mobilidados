# Adding a city

A city profile (`cities/<city>.toml`) holds what every street in that city shares. It needs:

| Section | What | Lisbon example |
|---|---|---|
| `[city]` | id, name, a projected CRS in metres | EPSG:3763 (ETRS89 / PT-TM06) |
| `[cartography]` | the class field and class codes for `road`, `parking`, `sidewalk`, `plot` in a large-scale polygon layer | `LAYER`; `10100104_ParqueEstacionamentoArea` for parking |
| `[axes]` | the street-name field of the street-axis layer | `DESIGNACAO` |
| `[network]` | fields of a routing network giving per-edge, per-direction access (optional) | `[EID]`, `[Direction]`, `Oneway` = `Traversable` |
| `[source_templates.*]` | how to fetch each source: kind, URL, CRS, licence as the publisher states it | see `cities/lisboa.toml` |

## What the cartography must provide

The method needs **on-street parking mapped as its own polygon class**, separate from the carriageway. Many
municipal 1:500–1:2000 cartographies do (road surface, parking bays, sidewalks, buildings). Where parking is
not mapped, the free width cannot be read from the map, and the case has to rely on field measurements or
orthophotos, which streetfit does not automate yet.

Check the cartography's survey date and stated accuracy, and record them in `[cartography]` (`survey`,
`accuracy_note`): they go into the ledger as caveats.

## Steps

1. Find the services (by hand or with `streetfit discover`, see [ai-tools.md](ai-tools.md)):
   ```bash
   streetfit discover --city Porto --start https://<gis-host>/arcgis/rest/services https://<open-data-host>/api/3 \
       --bbox -8.62,41.15,-8.60,41.16
   ```
2. Write `cities/<city>.toml`; record each source's licence exactly as the publisher states it. If it is not
   stated, write "not stated", and do not commit the raw data.
3. Create a case (`cases/<city>-<street>/case.toml`) with `extends = "../../cities/<city>.toml"`.
4. `streetfit fetch`, `streetfit run`, and inspect `results/figures/free_width_profile.png`: a sensible profile
   (strips around 2 m, a plausible free width) is the first check that the class codes are right.
5. Open a pull request with the city profile, the case and its `results/` (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

## Other source kinds

`arcgis_query` and `arcgis_identify` cover ArcGIS servers, and `http_file(s)` covers files. For WFS, OGC API
Features or OpenStreetMap, add a kind in `src/streetfit/sources.py` that writes the same structure (a JSON with
`features` holding `attributes` and ESRI geometry), or convert in the fetcher. Contributions welcome.
