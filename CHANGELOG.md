# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Dependency lower bounds are the oldest versions that pass the test suite, and a `lowest` CI job installs
  exactly them. `urllib3` is declared, since streetfit imports it directly.
- The package ships `py.typed`, so type checkers use its annotations.
- Limits, tolerances and timeouts that were bare numbers in the code are named constants or parameters.
- `streetfit verify` lists every file that does not match the lock, whatever the number of files.
- The module `streetfit.network` is now `streetfit.direction`, after the stage it implements (`network` read as
  network access). `python -m streetfit` works.
- `occurrences_files.csv` has a `with_date` column: the records with coordinates whose date parsed. A file
  without a located record reports 0, not an empty value, and empty dates.
- A street name that is not in the axes layer (or is in several features or in parts) and an error answered by an
  ArcGIS service are reported as `error: ...` by the command line, like other errors the user can fix.
- The unit suite runs a synthetic case through every stage offline (`tests/test_end_to_end.py`), so CI, including the
  `lowest` job, exercises the whole pipeline, the ledger and the figures.

### Fixed

- `streetfit discover` wrote a street-axes template without a licence, which no case could load, and a
  multi-line note or check could break the draft's TOML.
- The claim checker's read tool returned one line more than it told the model.
- The dates of the citizen reports were parsed across all files at once, so a file whose date format differed
  from the first file's lost its dates without a message. Each file is now parsed on its own.

## [0.2.0] - 2026-10-24

### Changed

- The configuration is validated when a case is loaded (`src/streetfit/config.py`): unknown keys, missing
  values and references to sources, vehicles or design references that do not exist are reported by name before
  anything runs. Defaults are defined once, there.
- Stages pass data to each other only through result tables. The hidden `results/facts.json` is gone; what it
  held is now in tables: `street.csv` (axis length), `occurrences_files.csv` (records and dates per file, which
  give the period) and a `schedule` row, told apart by a new `basis` column, in `encounters_summary.csv`.
- The ledger and the figures report what the configuration asks for, not whichever tables are on disk; a full
  run replaces every table and figure.
- All user-facing text is in `locales/<lang>.toml`; catalogue entries use one convention for other languages
  (a `translations.<lang>` table).
- Case files: blocks use `start` / `end`; `direction_id` is an integer, as in GTFS; `feed` is now `description`.
- HTTP retries use urllib3 (backoff, connection errors, 429 and 5xx only). Downloads are written atomically, and
  a file that does not match its pin is never written.
- Logging instead of print, with `-v` / `-q`; errors the user can fix are one line, not a traceback.
- The GTFS `stop_times` table, the largest in the feed, is read once per run instead of once per use.
- Figures are drawn without pyplot, so importing streetfit changes no global matplotlib state.
- Tooling: mypy in CI and `make lint`; tests treat warnings as errors; CI runs every supported Python version
  on Linux and the newest on macOS and Windows, with actions pinned by commit; dependabot waits before adopting
  a new release; zizmor audits the workflows in pre-commit.

### Fixed

- ESRI polygons: a hole touching its exterior ring was dropped, and a hole inside an island inside a hole was
  also given to the outer polygon. Each hole now belongs to the smallest exterior ring that contains it. The
  Lisbon cartography is not affected: every polygon is identical.
- The ledger's sources table showed no origin for a source whose lock entry has no URLs (Na Minha Rua); origins
  now come from the case configuration.
- `metres_two_strips` in `findings.json` is a number, not a string.
- Text files are read and written as UTF-8 on every platform, and lock-file paths use `/` on Windows.
- An AI answer that does not match the expected schema is an error instead of `None` passed on.

### Results

- Lisbon case: every table and every finding statement is identical to 0.1.0, apart from the additions above
  and the station positions in `traffic_direction_edges.csv`, now printed as decimals (they are metres).

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
