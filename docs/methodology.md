# Methodology

## Street axis and stations

The street is the polyline of the municipal street-axis layer with the case's street name (one feature,
single part). Stations are placed every `profiles.step_m` (default 0.5 m) along it; `s` is the distance from
the axis start. Left (`_L`) and right (`_R`) are relative to the direction of increasing `s`; the case names
them (e.g. NW / SE) in `street.sides`.

## Cross-section profiles (`geometry.py`)

At each station a transect perpendicular to the axis (±`half_width_m`, default 25 m) is intersected with the
cartography polygons of four roles defined in the city profile: road surface, parking strips, sidewalks and
plots/buildings. Intervals of the same role closer than 0.15 m are merged.

* **free width**: the road-surface interval that contains the axis (±0.05 m). Where parking is mapped as its
  own polygon, this is the carriageway between the strips.
* **strip_L / strip_R**: a parking interval whose inner edge is within 0.35 m of the free-width edge.
* **kerb_to_kerb**: outer edge of the left strip (or free width) to outer edge of the right one.
* **sidewalk**, **to_plot**: the next sidewalk interval, and the distance to the first plot/building.

A station is `two_strips` when both strips are wider than 0.5 m and the free width is at most
`narrow_max_m` (7 m); `one_strip` when only one side has a strip. A transect lying exactly on a strip's end
edge counts the strip (shared boundary). Summary statistics use `two_strips` stations only.

**What this is not:** parked vehicles are not observed. The strips are mapped areas. Whether cars stay inside
them is tested by `overhang_sensitivity.csv` and can be checked on orthophotos or on site.

**Accuracy:** each mapped edge has a planimetric error (Lisbon: ≤0.30 m assumed, see the city profile), so a
width between two edges is uncertain by roughly ±0.3–0.4 m. Report ranges, not single decimals, when this
matters.

## Traffic direction (`network.py`)

An ArcGIS `identify` on the municipal routing network at stations along the axis returns, per network edge
and direction, whether travel is allowed. The street is two-way if some edge is open in both directions.

## Scheduled buses (`gtfs.py`)

* **Routes on the street**: GTFS shapes within `buffer_m` (12 m) of the axis. The heading along the axis comes
  from the order in which the shape's points within 6 m project onto it; shapes covering less than 20 m of the
  axis (crossing streets, a touched end) get heading 0 and are reported but not counted.
* **Service day**: `calendar.txt` rules plus `calendar_dates.txt` exceptions for `service_date`.
* **Reference stops**: for each route and direction, a stop on or next to the street, with its position `s`
  and heading. Trips per hour are counted at the reference stop. These are timetable values, not observed runs.
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
(15 and 20 km/h in Lisbon) and flagged when the meeting point falls inside a two-strip section. Slower buses
stay longer on the street and meet more often, so the pipeline also reports the count at the slowest
stop-to-stop speed implied by the service day's schedule (straight-line distance over median scheduled time, a
lower bound): in Lisbon 12.7 km/h gives 7, the top of the 6–7 range. It is an estimate of how often the
situation arises, graded I.

## Width budget (`envelope.py`)

Margin = free width − sum of the two vehicles' widths, for the minimum, median and 95th-percentile free
width, bodies only and with mirrors. A bus's mirrors are mounted above a car's body, so in bus × car with
mirrors only the car's mirrors count. Vehicle widths come from the catalogue in `src/streetfit/data/vehicles.toml`,
each graded D (published) or P (assumed). This is a static envelope, not a swept path: it ignores the extra
width a vehicle needs when turning and the safety distance a driver keeps, so it is favourable to the
narrow street.

## Citizen reports (`occurrences.py`)

Geolocated records (Lisbon: *Na Minha Rua*) within a window around the street are attributed to the nearest
street axis within `max_dist_m` (12 m), filtered by category with an anchored regular expression, and counted
per 100 m of street. Only streets of at least `min_street_length_m` are ranked. Counts are small and a report
is not a proven infraction; only aggregates are published.

## Area scan (`area_scan.py`)

The same transect method runs every 3 m along every street axis in a wider area where a scheduled bus shape
runs along the street (within 10 m and 30° of the axis). Per street: metres with buses, buses per weekday,
whether buses run in both directions, median and 10th-percentile free width, share of stations with parking on
both sides, metres below the reference width, metres combining two-sided parking with a free width below the
threshold, and the traffic direction. Only two-way streets share the case's pattern: a one-way street needs a
single lane.

## Design references (`standards.py`)

`src/streetfit/data/standards.toml` lists references with the document's checksum and URL, the printed and PDF
page, a verbatim quote, the derivation of the value and, above all, its **scope**. The comparison table gives
the difference between the measured median and each reference; the scope decides whether the comparison is
meaningful.
