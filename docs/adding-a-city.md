# Adding a city

A city profile (`cities/<city>.toml`) holds what every street in that city shares; `cities/lisboa.toml` is a
complete example. It needs:

| Section | What |
| --- | --- |
| `[city]` | id, name, a projected CRS in metres |
| `[cartography]` | the class field and class codes for `road`, `parking`, `sidewalk`, `plot` in a large-scale polygon layer; for the sidewalk tool, also `overhead` (plot classes drawn at roof level: arcades, balconies, canopies) and `yard` (plot classes of open ground) |
| `[axes]` | the street-name field of the street-axis layer |
| `[network]` | fields of a routing network giving per-edge, per-direction access (optional) |
| `[source_templates.*]` | how to fetch each source: kind, URL, CRS, licence as the publisher states it |
| shared settings (optional) | method parameters, vehicles, design references, the sources every case uses, and the known gaps every case shares (listed after a case's own) |

A case can change any value it inherits but cannot remove an inherited section: shared settings are for what every
case of the city has (in Lisbon, buses and citizens' reports).

Data that change over time (a GTFS feed and its service day, yearly files) go in a dated file that extends the
profile, such as `cities/lisboa-2026-10.toml`. Cases extend the dated file. When newer data come out, add another
dated file and point new cases at it: a case that already has results keeps the file it was run with, so it
stays reproducible.

## What the cartography must provide

The method needs **on-street parking mapped as its own polygon class**, separate from the carriageway. Many
large-scale municipal cartographies do (road surface, parking bays, sidewalks, buildings). Where parking is
not mapped, the free width cannot be read from the map, and the case has to rely on field measurements or
orthophotos, which mobilidados does not automate yet.

Check the cartography's survey date and stated accuracy, and record them in `[cartography]` (`survey`,
`accuracy_note`): they go into the ledger as caveats.

For the **sidewalk tool** (`[sidewalks]`, see [methodology.md](methodology.md#sidewalks-sidewalkspy)) the cartography
must map sidewalks as their own class and the buildings as plots. Look at how it draws a building over an arcade or
a balcony, and list those classes in `overhead`: a sidewalk that ends at one has an unknown width and is left
unmeasured. List yards and other open ground inside plots in `yard`: a sidewalk that ends at one is reported as one
to check, never as one below the law. Set `[sidewalks] edge_accuracy_m` to the accuracy per edge your
`accuracy_note` states. To screen every street of the area, give `[area_scan] sidewalks` a source with the road,
parking, sidewalk and plot classes of the area (Lisbon: `area_sidewalks`), and exclude private roads by name with
`exclude_streets`.

## Steps

1. Find the services (by hand or with `mobilidados discover`, see [ai-tools.md](ai-tools.md)):

   ```bash
   mobilidados discover --city <city> --start https://<gis-host>/arcgis/rest/services https://<open-data-host>/api/3 \
       --bbox <lon_min>,<lat_min>,<lon_max>,<lat_max>
   ```

2. Write `cities/<city>.toml`; record each source's licence exactly as the publisher states it. If it is not
   stated, write "not stated", and do not commit the raw data.
3. Create a case (`cases/<city>-<street>/case.toml`) with `extends = "../../cities/<city>.toml"` (or a dated file
   that extends it). Once the city has one case, `mobilidados new-case "<street>" --like <that case>` drafts the
   next ones from a street name. The merged
   configuration is validated when it is loaded (the models are in `src/mobilidados/config.py`): a misspelt key, a
   missing value or a reference to a source, vehicle or design reference that does not exist is reported by
   name before anything runs.
4. `mobilidados fetch`, `mobilidados run`, and inspect `results/figures/free_width_profile.png`: a sensible profile
   (parking strips about as wide as a parked car, a plausible free width) is the first check that the class codes are right.
5. Open a pull request with the city profile, the case and its `results/` (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

## Other source kinds

`git_archive` reads vehicle positions from a git repository that archives a real-time feed one CSV per snapshot
(columns `trip_id`, `route_id`, `direction_id`, `latitude`, `longitude`, `timestamp`, `vehicle_id`, as GTFS-RT
vehicle positions name them), pinned to a commit; it needs the `git` command. A city profile can hold a template
with the archive's address and file names (Lisbon: `carris_positions_archive`), the dated city file its commit and
period, and a case its routes and envelope (see docs/methodology.md, *Time on a stretch*). List the city's public
holidays in `[city] holidays`, so the stage does not count them as working days.

`arcgis_query` and `arcgis_identify` cover ArcGIS servers, and `http_file(s)` covers files. For WFS, OGC API
Features or OpenStreetMap, add a kind in `src/mobilidados/sources.py` that writes the same structure (a JSON with
`features` holding `attributes` and ESRI geometry), or convert in the fetcher. Contributions welcome.
