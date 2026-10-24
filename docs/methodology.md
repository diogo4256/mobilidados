# Methodology

Parameters are named where they are set: a key of the case configuration (e.g. `profiles.step_m`, with its
default in `src/mobilidados/config.py`) or an argument of the function that applies it (e.g. `snap` in
`geometry.measure_profiles`). Values are not repeated here, so this text cannot disagree with the code; a case's
ledger states the values it used where they matter.

Every run writes the resolved configuration it used (case, city profile and defaults) to `results/config.json`.

## Street axis and stations

The street is the polyline of the municipal street-axis layer with the case's street name (one feature,
single part). Stations are placed every `profiles.step_m` along it; `s` is the distance from the axis start.
Left (`_L`) and right (`_R`) are relative to the direction of increasing `s`; the case names them (e.g. NW / SE)
in `street.sides`.

## Cross-section profiles (`geometry.py`)

At each station a transect perpendicular to the axis, reaching `profiles.half_width_m` to each side, is
intersected with the cartography polygons of four roles defined in the city profile: road surface, parking
strips, sidewalks and plots/buildings. Intervals of the same role separated by less than a small tolerance
(`tol` in `geometry._merge`) are merged.

* **free width**: the road-surface interval that contains the axis. Where parking is mapped as its own polygon,
  this is the carriageway between the strips.
* **strip_L / strip_R**: a parking interval whose inner edge lies within `snap` of the free-width edge.
* **kerb_to_kerb**: outer edge of the left strip (or free width) to outer edge of the right one.
* **sidewalk**, **to_plot**: the next sidewalk interval, and the distance to the first plot/building.

A station is `two_strips` when both strips are wider than `min_strip` and the free width is at most
`profiles.narrow_max_m`; `one_strip` when only one side has a strip (`geometry.classify`). A transect lying
exactly on a strip's end edge counts the strip (shared boundary). Summary statistics use `two_strips` stations
only. Consecutive `two_strips` stations within a block form a section (`narrow_sections.csv`); the length the
ledger gives for them is the distance from the first to the last station of each section, summed. It is not
the station count times `profiles.step_m`, which would add one step per section, and it is not the mapped
strip length per side in `parking_strip_lengths.csv`.

**What this is not:** parked vehicles are not observed. The strips are mapped areas. Whether cars stay inside
them is tested by `overhang_sensitivity.csv` and can be checked on orthophotos or on site.

**Accuracy:** each mapped edge has a planimetric error, recorded in the city profile's
`cartography.accuracy_note` and repeated as a caveat in the ledger. A width is measured between two edges, so
its uncertainty combines both: report ranges, not single decimals, when this matters.

## Traffic direction (`direction.py`)

An ArcGIS `identify` on the municipal routing network at `direction.stations_s` returns, per network edge and
direction, whether travel is allowed. The street is two-way if some edge is open in both directions.

## Scheduled buses (`gtfs.py`)

* **Routes on the street**: GTFS shapes within `transit.buffer_m` of the axis. The heading along the axis comes
  from the order in which the shape's points near the axis (`near_m`) project onto it; shapes covering less
  than `min_run_m` of the axis (crossing streets, a touched end) get heading 0 and are reported but not counted
  (`gtfs.shapes_along`).
* **Service day**: `calendar.txt` rules plus `calendar_dates.txt` exceptions for `transit.service_date`.
* **Reference stops**: for each route and direction, a stop on or next to the street, with its position `s`
  and heading (`transit.reference_stops`). Trips per hour are counted at the reference stop. These are
  timetable values, not observed runs.
* **Scheduled runtimes**: time from the reference stop to the next stop, for all trips in the feed and for the
  service day, as a check on the speeds used below.

## Encounters (`encounters.py`)

Each scheduled vehicle crosses the whole street at a constant speed `v`, passing its reference stop at the
scheduled time. Vehicles in opposite directions meet if their presence intervals on the street overlap; the
meeting time and point follow from equal positions:

```text
t* = (s_b - s_a + v (t_a + t_b)) / (2 v)        s* = s_a + v (t* - t_a)
```

for A heading +1 at `s_a` at `t_a` and B heading −1 at `s_b` at `t_b`. Results are given for the case's speeds
(`transit.speeds_kmh`) and flagged when the meeting point falls inside a two-strip section. Slower buses stay
longer on the street and meet more often, so the pipeline also computes the count at the slowest stop-to-stop
speed implied by the service day's schedule (straight-line distance over median scheduled time, a lower bound).
Both are rows of `encounters_summary.csv`, told apart by its `basis` column (`assumed` or `schedule`), and the
ledger reports both. It is an estimate of how often the situation arises, graded I.

## Width budget (`envelope.py`)

Margin = free width − sum of the two vehicles' widths, for the minimum, median and 95th-percentile free
width, bodies only and with mirrors. A bus's mirrors are mounted above a car's body, so in bus × car with
mirrors only the car's mirrors count. Vehicle widths come from the catalogue in `src/mobilidados/data/vehicles.toml`,
each graded D (published) or P (assumed). This is a static envelope, not a swept path: it ignores the extra
width a vehicle needs when turning and the safety distance a driver keeps, so it is favourable to the
narrow street.

## Without parking (`envelope.py`)

The same stations, with the space of the mapped parking given back to the carriageway: on each station with
parking on both sides, the free width plus the strip on side L, plus the strip on side R, or plus both
(`without_parking.csv`). The ledger states the resulting widths and the bus × bus margin with parking on one
side only (the narrower of the two options). It measures an option, it is not a design: it assumes nothing else
(trees, bins, loading bays, bike parking) takes the space. The scenario is not compared with the design
references, because a reference's scope may assume the parking that the scenario removes.

## Citizen reports (`occurrences.py`)

Geolocated records (Lisbon: *Na Minha Rua*) within `occurrences.window_m` of the street are attributed to the
nearest street axis within `occurrences.max_dist_m`, filtered by category with an anchored regular expression
(`occurrences.filters`), and counted per 100 m of street. Only streets of at least
`occurrences.min_street_length_m` are ranked. `occurrences_files.csv` records, per file, how many records there
are, how many have coordinates, how many of those have a date that parsed (each file's dates are parsed on their
own, so files may use different formats) and the dates they span. Counts are small and a report is not a proven
infraction; only aggregates are published.

## Area scan (`area_scan.py`)

The same transect method runs every `area_scan.step_m` along every street axis in a wider area where a
scheduled bus shape runs along the street (within `near_m` of the axis and `max_angle` of its direction, in
`area_scan.scan`). Per street: metres with buses, buses per weekday, whether buses run in both directions,
median and 10th-percentile free width, share of stations with parking on both sides, metres below
`area_scan.reference_m`, metres combining two-sided parking with a free width below `area_scan.threshold_m`,
and the traffic direction. Only two-way streets share the case's pattern: a one-way street needs a single
lane.

## Design references (`standards.py`)

`src/mobilidados/data/standards.toml` lists references with the document's checksum and URL, the printed and PDF
page, a verbatim quote, the derivation of the value and, above all, its **scope**. The comparison table gives
the difference between the measured median and each reference; the scope decides whether the comparison is
meaningful.
