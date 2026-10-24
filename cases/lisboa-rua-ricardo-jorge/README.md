# Rua Ricardo Jorge (Alvalade, Lisboa)

**Question:** with parking on both sides, does the remaining free width let two scheduled buses pass each
other in opposite directions?

**Pergunta:** com estacionamento dos dois lados, a faixa livre que sobra permite que dois autocarros
programados se cruzem em sentidos opostos?

## Result (reference run, sources retrieved 2026-10-20/22)

| | |
|---|---|
| Street | 209.25 m, two-way (municipal routing network) |
| Free width between the mapped parking strips | **4.78–5.68 m, median 4.90 m**, over 116 m of the street (strips ≈2.0 m each side) |
| Scheduled buses | routes 744 (both directions) and 46B (one direction); on Tue 2026-10-27: 56 trips SW→NE, 76 NE→SW |
| Width budget (bodies) | bus × bus: 5.00 m needed, margin **−0.10 m** (−0.90 m with mirrors); bus × car: +0.60 m (+0.35 m with the car's mirrors) |
| Timetable | 6–7 meetings per weekday between buses in opposite directions on the street (estimate) |
| CML design manual (2018), p. 152 | reference profile for a two-way street with parking on both sides: 6.80 m between the strips (6.50 m without extra width) |
| Area | of 69 streets with buses nearby, 2 are two-way with two-sided parking and a free width < 5.5 m; only this one has buses in both directions |

Full ledger with grades and sources: [results/findings.md](results/findings.md) (Portuguese).
Figures: [results/figures](results/figures). Tables: [results/tables](results/tables).

![Free width along the street](results/figures/free_width_profile.png)

## Reproduce

```bash
streetfit fetch cases/lisboa-rua-ricardo-jorge
streetfit verify cases/lisboa-rua-ricardo-jorge
streetfit run cases/lisboa-rua-ricardo-jorge
```

The GTFS feed is pinned by SHA-256 to the file published on 2026-10-19; the Carris endpoint always serves the
current feed, so a later download will not match. The raw inputs are not redistributed (the GTFS licence is not
stated at the endpoint); `sources.lock.json` lists every input with its checksum, so a copy obtained elsewhere
can be verified with `streetfit fetch --from-dir <dir>` followed by `streetfit verify`.

## Provenance of this case

This analysis was first done with standalone scripts (October 2026) and then rebuilt as streetfit. The
framework reproduces the original outputs exactly: all 419 profile stations, the per-block summary, strip
lengths, trips per hour, the encounter detail and the 69-street area scan are identical. Two things were
fixed on the way: two summary tables used by the original dossier had no script producing them (they are now
generated), and the occurrences filter had drifted to also count bike-parking requests as abusive parking. The
framework uses an anchored category filter that reproduces the figure originally reported (6 reports,
2.87 per 100 m).

## Not verified (NE)

No field observation of two buses meeting; no published delays or incidents per street; no official bus width
with mirrors; parked cars' actual position not measured on site. See the ledger.
