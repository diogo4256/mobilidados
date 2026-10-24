# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-24

### Added

- Pipeline: cross-section profiles from municipal cartography, traffic direction, GTFS routes and trips per
  hour, timetable encounters, width budget, citizen-report rates, area scan, design-reference comparison,
  figures and an evidence-graded findings ledger.
- Provenance: `sources.lock.json` with SHA-256 per input, `fetch --from-dir` for archived snapshots,
  `verify`, offline runs.
- Catalogues: vehicles and design references (CML manual 2018; RASt 06 as cited by the Berlin Senate), with
  grades, pages, quotes and scope.
- Optional AI tools: `check-claims` (fact-checking agent), `extract-standard` (vision + multi-pass OCR),
  `discover` (city-profile agent); deterministic `lint` for letters.
- Lisbon city profile and the Rua Ricardo Jorge case, reproducing the original October 2026 analysis exactly.
