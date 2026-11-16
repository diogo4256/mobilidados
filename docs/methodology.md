# Methodology

Parameters are named where they are set: a key of the case configuration (e.g. `profiles.step_m`, with its
default in `src/mobilidados/config.py`) or an argument of the function that applies it (e.g. `snap` in
`geometry.measure_profiles`). Values are not repeated here, so this text cannot disagree with the code; a case's
ledger states the values it used where they matter.

Every run writes the resolved configuration it used (case, city profile and defaults) to `results/config.json`.

## Street axis and stations

The street is the polyline of the municipal street-axis layer with the case's street name. A street stored as
several features or parts is joined when the pieces form one continuous line; one that branches or has gaps is
refused (`geometry.street_axis`). Stations are placed every `profiles.step_m` along it; `s` is the distance from the axis start.
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
only. Consecutive `two_strips` stations within a block form a section (`narrow_sections.csv`, which lists the
first and last station of each).

**Lengths.** Every length of street the ledger gives follows one rule (`geometry.covered`): each station stands
for the stretch within half a step on either side of it, cut at the ends of the axis. A run of k stations shows a
condition holding over at least (k − 1) steps and less than (k + 1) steps; k steps is the middle of that range.
This applies to the stretches with parking on both sides (the free-width finding, and the parking an option
removes, measured on the same stretches) and to the mapped parking per side (`parking_strip_lengths.csv`), so the
lengths can be compared with each other. Taking the distance from the first to the last station instead would
understate every length by one step per section, and with it the parking an option removes; the error of the rule
used is at most half a step at each end of a section. A meeting of two buses counts as inside a section over the
same stretch (`encounters_detail.csv`). The free-width finding's caveat states this filter, with
the value of `profiles.narrow_max_m`, and how many stations with parking on both sides it leaves out for being
wider, next to the cartography's survey and accuracy notes.

**What this is not:** parked vehicles are not observed. The strips are mapped areas. Whether cars stay inside
them is tested by `overhang_sensitivity.csv` and can be checked on orthophotos or on site.

**Accuracy:** each mapped edge has a planimetric error, recorded in the city profile's
`cartography.accuracy_note` and repeated as a caveat in the ledger. A width is measured between two edges, so
its uncertainty combines both: report ranges, not single decimals, when this matters.

## Traffic direction (`direction.py`)

An ArcGIS `identify` on the municipal routing network at `direction.stations_s` returns, per network edge and
direction, whether travel is allowed, with each edge's geometry. An identify answers with every edge within its
tolerance, and near a junction that includes the edges of the crossing street: only the edges that run along the
street count, within `direction.MAX_ANGLE` (30°) of its direction and `direction.MAX_DIST_M` (6 m) of the station.
Reading every edge made a one-way street next to a two-way crossing read as two-way (Lisbon's Rua de São Bento did).
The street is two-way if one of its edges is open in both directions; the ledger also says at how many of the
stations checked that is so. Answers cached before the geometry was kept are asked again (offline, the run stops).

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
longer on the street and meet more often, so the pipeline also computes the count at the lowest of the service
day's stop-to-stop speeds from the reference stops (straight-line distance over median scheduled time).
Both are rows of `encounters_summary.csv`, told apart by its `basis` column (`assumed` or `schedule`), and the
ledger reports both. It is an estimate of how often the situation arises, graded I. The model has no dwell
times at stops, so a meeting a few metres from the edge of a section may in fact fall inside it; the ledger
says so.

## Width budget (`envelope.py`)

Margin = free width − sum of the two vehicles' widths, for the minimum, median and 95th-percentile free
width, bodies only and with mirrors. A bus's mirrors are mounted above a car's body, so in bus × car with
mirrors only the car's mirrors count. Vehicle widths come from the catalogue in `src/mobilidados/data/vehicles.toml`,
each graded D (published) or P (assumed). This is a static envelope, not a swept path: it ignores the extra
width a vehicle needs when turning and the safety distance a driver keeps, so it is favourable to the
narrow street: the summed width is the least the vehicles need. The ledger's caveat gives the bus × bus margin
at the three free widths, the share of two-strip stations narrower than two bus bodies and how mirrors are
counted.

## Without parking (`envelope.py`)

The same stations, with the space of the mapped parking given back to the carriageway: on each station with
parking on both sides, the free width plus the strip on side L, plus the strip on side R, or plus both
(`without_parking.csv`). The ledger states the resulting widths and the bus × bus margin with parking on one
side only (the narrower of the two options). It measures an option, it is not a design: it assumes nothing else
(trees, bins, loading bays, bike parking) takes the space. The scenario is not compared with the design
references, because a reference's scope may assume the parking that the scenario removes.

What it removes is stated next to it: one side removes, along the same stretches, as much mapped parking as the
length of street with parking on both sides (the length the free-width finding gives), and both sides twice that.
Places are that length divided by the longest and by the shortest length of one space (`profiles.parking_space_m`,
a range and an assumption, to be set from the municipality's standard where one is known), rounded down: a range,
not a count. The same lengths give the stall counts of `parking_strip_lengths.csv`, which also gives the mapped
parking along the whole street on each side; the finding states those lengths too, since removing a whole side
would remove more than the stretches with parking on both sides. The strips are mapped areas, not counted
spaces: entrances and other gaps inside them are not subtracted.

## Time on a stretch (`delay.py`, `archive.py`)

What the timetable cannot say, the operation can: how long buses actually take on a stretch of the street. The
`delay` stage measures it from archived vehicle positions (GTFS-RT), where a public archive of the operator's
real-time feed exists. It answers one question: **at the evening peak, do buses spend more time on this stretch
than the slowdown of the same routes' neighbouring stretches would explain?** It does not say why.

**The data.** A real-time feed answers with every vehicle's last reported position. Some projects poll it every
few minutes and commit each answer to a git repository; a `git_archive` source pins such an archive to one commit
and reads the snapshots of a period (`archive.py`). For Lisbon the archive is LIVREpt/lisboa_carris_api. Its
collector does not read Carris directly but a relay (`rt.jdcp.workers.dev`), so two parties stand between Carris
and the files; neither states a licence. The positions are used and not redistributed, the source is named in
every finding, and the checks below test the archive instead of trusting it. The snapshots are irregular: in the
Lisbon case half of the hours have a gap of 20 minutes or more somewhere.

**The stretch and its controls.** `delay.s_from` and `delay.s_to` mark the stretch along the street axis; keep it
clear of the stops, where buses also wait for passengers. For each route and direction of `transit.routes`, the
GTFS shape the most trips use locates the stretch along the route and two *control* stretches of `control_m`,
`control_gap_m` before and after it. A position counts if the vehicle reported it at most `max_age_s` before the
snapshot (an older one repeats a past position and would be counted twice) and lies within `max_offset_m` of the
shape (a diverted trip drops out). Working days are Monday to Friday, without the city profile's `holidays` and
`delay.exclude_dates`. Hours are keyed by their start in UTC, so the hour repeated when clocks go back is two
hours.

**The estimator (occupancy).** If buses pass a stretch at a rate λ and each spends W seconds on it, the expected
number on it at any instant is λ·W (Little's law). The archive's snapshot times do not depend on where the buses
are, so over a set of snapshots the positions seen on the stretch, divided by the sum of λ at those snapshots,
estimate W. Two quantities follow:

* **The ratio** (finding `delay`): (on the stretch ÷ on the controls) at peak, divided by the same off-peak. The
  same buses pass the stretch and its controls minutes apart, so λ and the snapshot cadence cancel exactly: the
  ratio needs no count of buses and uses every working-day snapshot. A ratio of 1 means the stretch slows down at
  peak exactly as much as its surroundings.
* **The seconds** (finding `delay_seconds`): the time per passage off-peak and at peak, what the controls' peak
  slowdown predicts at peak (off-peak time × controls' peak ÷ off-peak time), and the excess. These need λ: the
  trips seen within `reach_m` of the stretch along their shape, each counted once, in the hour of its position
  nearest the stretch. A trip is sure to be seen only if snapshots are frequent enough, so the seconds (and their
  inputs) use only the hours whose snapshots are never more than `max_gap_s` apart. In Lisbon those are 120 peak
  hours, nearly all of 2025.

**Uncertainty.** 90% intervals from a bootstrap over whole days (`delay.bootstrap` replicates, fixed `seed`, so a
run gives the same intervals every time): positions of the same day stay together.

**Checks, all in the tables.**

* `delay_passages.csv`: the passages counted per covered hour against the timetable's trips per hour on the
  service day. In Lisbon, 90–95%: if passages are missing, the seconds are overstated in that proportion; the
  ratio does not depend on them. The count does not grow with a longer reach (3 km instead of 2), so trips are not
  being missed between snapshots.
* `delay_data.csv`: the snapshots, working days and covered hours behind the estimates, and the share of positions
  left out for being too old, on the stretch and on the controls apart: if the two differed much, leaving them out
  would bias the comparison (Lisbon: 0.8% and 2.3%; with no age limit at all, the ratio moves from 1.49 to 1.48).
* `delay_sensitivity.csv`: the ratio and the excess with one choice changed at a time (each peak hour alone, the
  off-peak hours, the controls' distance and length, no age limit on positions, a longer reach, longer gaps).
* `delay_summary.csv`: the estimates for all routes, each route and direction, and each year. A year whose ratio
  interval includes 1 is named in the finding as not confirming the excess.
* `delay_by_hour.csv` and `figures/delay_by_hour.png`: hour by hour, with the interval of each hour.
* `tests/test_delay.py` simulates buses with known speeds, samples them at irregular snapshots and checks that the
  estimator gives back their times, the ratio and the excess within its intervals, and no excess where there is
  none.

**What it is not.** It measures where the time goes, not why. Parked cars, buses in the other direction, a queue
from a junction at either end and a traffic light can all slow a stretch at peak; the per-direction ratios
(the finding's caveat) help to tell a queue towards one end from a slowdown in both directions, but do not settle
it. It is the operation as an archive recorded it, not the operator's own record.

## Citizen reports (`occurrences.py`)

Geolocated records (Lisbon: *Na Minha Rua*) within `occurrences.window_m` of the street are attributed to the
nearest street axis within `occurrences.max_dist_m`, filtered by category with a regular expression searched in
the category (`occurrences.filters`; Lisbon's starts with `^`, so it must match from the start), and counted per 100 m of street. Only streets of at least
`occurrences.min_street_length_m` are ranked. `occurrences_files.csv` records, per file, how many records there
are, how many have coordinates, how many of those have a date that parsed (each file's dates are parsed on their
own, so files may use different formats) and the dates they span. Counts are small and a report is not a proven
infraction; only aggregates are published. The window is a rectangle around the street, but a street's rate
divides the reports counted inside it by the street's whole length, which favours streets that lie wholly
inside the window, such as the case street; the ledger states this bias.

## Area scan (`area_scan.py`)

A transect method like the case street's runs every `area_scan.step_m` along every street axis in a wider area
where a scheduled bus shape runs along the street (within `near_m` of the axis and `max_angle` of its direction,
in `area_scan.scan`), with its own transect half-width and tolerances (`half`, `snap`). Per street: metres with
buses, buses on the service day, whether buses run in both directions, median and 10th-percentile free width, share of
stations with parking on both sides, metres below `area_scan.reference_m`, metres combining two-sided parking
with a free width below `area_scan.threshold_m`, and, for streets with enough metres below
`area_scan.reference_m` (`min_below_ref_m` in `area_scan.rank_streets`), the traffic direction, read the
same way at a quarter, half and three quarters of its narrowest stations, by majority (a tie, or no reading, is `?`). Only two-way streets share the case's pattern: a one-way street needs a single
lane. The thresholds are parameters of the analysis, not values from a design document.

## Sidewalks (`sidewalks.py`)

The law, not a design manual: Decree-Law 163/2006 applies to sidewalks and other paved pedestrian routes on the
public way (article 2(2)(a)) and requires a continuous channel free of obstructions at least **1.2 m** wide,
measured at ground level, counting street furniture, trees, signs, hydrants and bins as obstructions (annex,
sections 4.3.1 and 4.3.2). A narrower stretch is admitted only if it is short: at least 0.80 m wide over at most
0.60 m of length, at least 0.90 m over at most 1.50 m (section 4.3.3, read from its drawings: A is the width, B the
length). Sidewalks next to main and distributor roads need 1.5 m (section 1.2.1); the decree does not say which roads
those are, so a case uses that value only where the municipality classifies its street so (`[sidewalks] main_roads`,
with `main_roads_basis`). The values, pages and quotes are in `data/standards.toml`, kind `legal_requirement`; the
document is the 2006 publication pinned by its checksum, and the consolidated text on diariodarepublica.pt was
checked to keep these sections and article 9 as published (amendments by Decrees-Law 136/2014, 125/2017, 95/2019
and 10/2024 touch other parts).

**What is measured.** At each station of the case street (and every metre of every street in the area,
`area_scan.sidewalk_step_m`) the transect reads the widest piece of mapped sidewalk between the kerb (the road edge,
or the outer edge of a parking strip) and the first plot on that side (`walk_L`, `walk_R` in `profiles.csv`). A
sidewalk cut by a tree pit, a kiosk or a shelter mapped as another class is walked on its widest piece.

**Why the mapped width can show a stretch is too narrow, and never that it is wide enough.** Obstructions only take
width away. Where the piece runs up to the plots (`walk_*_bounded`), nothing beyond it can be walked on, so the free
channel cannot be wider than the mapped sidewalk: a stretch narrower than the law admits for its length is one where
the free channel is too, and the case for it rests on the municipality's own cartography. The reverse does not hold:
poles, bins, café terraces and cars on the sidewalk are not mapped, so a wide mapped sidewalk does not show a wide
free channel, and the ledger says so.

**What is left out, so a reading is not a slip of the map.**

* stations within `sidewalks.junction_m` (10 m in Lisbon) of a junction or an end of the axis, and where the street
  is more than 1.5 times wider kerb to kerb than its median (a junction, a slip lane, a square): there a transect
  crosses corners and other streets;
* a side where another carriageway comes before any plot, or where the plot that bounds the sidewalk has a
  carriageway within 3 m behind it: a median or an island, not a sidewalk (`geometry.ISLAND_BACK_M`);
* a sidewalk that ends at a plot class drawn at roof level (`cartography.overhead`: in Lisbon, raised and
  cantilevered building bodies and canopies): the ground under an arcade may be walked on, so its width is unknown;
* sidewalk polygons thinner on average than 0.3 m, and pieces of sidewalk narrower than that on a transect: slivers
  where polygons meet (`geometry.MIN_WALK_PIECE_M`).

**Two tiers, never mixed.** A sidewalk that ends at a yard (`cartography.yard`: open ground, which may be a forecourt
or a planted island) or at something the classes read do not cover (a lawn, a wall, a public building) is reported as
metres *to check*, never as below the law. Of the stretches below, those still below if each of the two mapped edges
were `cartography.edge_accuracy_m` off in the sidewalk's favour (the accuracy per edge the city profile states, 0.30 m
in Lisbon) are counted apart, and the area finding names only those streets.

**Tables.** `sidewalks.csv` (per side and block: metres measured, metres up to the plots, width, metres below each
threshold and metres to check), `sidewalk_narrow_sections.csv` (each run of narrow stations: its length, narrowest
width, the width the law admits for that length, whether it is below, with and without the accuracy margin, and the
coordinates of its middle, for the letter), `sidewalk_profile.csv` (the readings the figure draws) and
`area_sidewalks.csv` (one row per street of the area, the most robust first).

This was checked by drawing the cartography at the stretches the scan flagged in the Alvalade area before and after
each rule above: what remains are buildings at the edge of narrow streets (Rua das Mimosas, the lanes of São João de
Brito) and long sidewalks about 1 m wide between the kerb and the buildings.

## Screening (`screening.py`)

`results/screening.md` turns the area tables into two ranked lists: the streets with buses where parking on both
sides leaves less than `area_scan.threshold_m` of free width over at least `area_scan.min_pattern_m`, and the streets
with sidewalks narrower than the law admits. It computes nothing, says where to look, not what to conclude, and ends
with the commands that make a case for a listed street. `mobilidados screen CASE` re-runs just the area stages and
writes it.

## Letter drafts (`letter.py`)

`mobilidados draft CASE --topic buses|sidewalks [--ask review|documents]` writes `results/letter-<topic>.md` from
`findings.json` alone: one topic; the topic's findings and the findings they rest on (their `sources`), grouped as
measured (M), official documents (D) and estimates (I), each followed by its finding id; the assumptions (P) they
use, declared as such; one request (that the services check and act, or, with `--ask documents`, a request for
documents under Law 26/2016, articles 12 and 15); the attachments, with the points or stretches where a technician
can measure. Gaps (NE) stay out: they are for the sender's notes. Every statement is copied from the ledger, so the
draft says no more than the ledger, and the draft is linted before it is written.

## Design references (`standards.py`)

`src/mobilidados/data/standards.toml` lists references with the document's checksum and URL, the printed and PDF
page, a verbatim quote, the derivation of the value and, above all, its **scope**. The comparison table gives
the difference between the measured median and each reference; the scope decides whether the comparison is
meaningful.
