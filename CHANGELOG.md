# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

The project is now called **mobilidados**: tools for data-based mobility claims in Portugal, starting with
Lisbon. The street-width audit is its first tool. Versions 0.1.0 and 0.2.0 were released as
streetfit.

### Added

- The header of a `new-case` draft states what it assumed: each reference stop with its distance from the street
  and its position along it (a stop on a cross street near an end is clamped to that end), both compass readings
  when the bearing is within 10° of a boundary between two points, and, where buses run one way, that the
  question supposes a car beside the bus, which does not hold on a one-way single-lane street.
- `mobilidados new-case "<street>" --like <case>` drafts a case for another street of the same city from its
  name: the axis from the municipal layer, blocks cut at the cross streets, direction and side labels from the
  bearing, check points and traffic-direction stations away from the junctions, and the bus routes and
  reference stops from the model case's GTFS feed. Sources, pins, vehicles and parameters are the model case's.
  A name that matches no axis is looked up by its most distinctive word: a single match that differs only in case
  or accents is used, otherwise the error suggests the closest names. The draft's header, which lists what to
  check, is in the case's language.
  Drafting Rua Ricardo Jorge from its own case gives the same blocks, routes and reference stops as the
  hand-written case.
- `docs/stakeholders.md`: who makes claims with the results, who answers them, who is affected, whose data is
  used and who keeps the toolset alive; the questions to ask before a change; and what a toolset like this can
  and cannot do.
- The free width without the mapped parking on one side, or on both, at the same stations as the measured free
  width (`without_parking.csv`), with a ledger finding and a bar in the width figure. Defined in
  `docs/methodology.md`. The existing tables and values are unchanged.
- `README.md` is in Portuguese and `README.en.md` in English. Both state the project's purpose (better mobility, with
  public transport as part of the solution) and what the tools do not do yet.
- A pushed tag `vX.Y.Z` makes a GitHub release with the changelog's section as notes and publishes the
  package to PyPI (`.github/workflows/release.yml`). The steps are in `CONTRIBUTING.md`.

### Changed

- Lisbon's settings are in three layers: `cities/lisboa.toml` (services, classes and the method parameters every
  case shares), `cities/lisboa-2026-10.toml` (the GTFS feed, service day and Na Minha Rua files pinned in October
  2026) and each case, which keeps only its street. Newer data go in a new dated file, so a case with results
  keeps the inputs it was run with. The Lisbon case's loaded configuration is unchanged, value for value.
- The known gaps of a city profile and of a case are both listed, the case's first; before, a case's list
  replaced the profile's.
- A street stored in the axes layer as several features or parts is joined into one axis when the pieces form
  one continuous line; before, any street in more than one piece was an error.
- The package, module and command are `mobilidados` (were `streetfit`), and so are the environment variables
  (`MOBILIDADOS_MODEL`, `MOBILIDADOS_EFFORT`, `MOBILIDADOS_CONTACT`), the exception (`MobilidadosError`) and the
  User-Agent sent to data providers. The repository moved to `diogo4256/mobilidados`; GitHub redirects the old
  address. The texts generated in `findings.md` and on the figures name mobilidados; tables and findings are
  unchanged.
- The Portuguese texts of the ledger and the figures are rewritten in plain Portuguese (for example "Cada
  afirmação diz em que se apoia", "mediana de 4,90 m"). The width figure says how much width is missing
  ("faltam 0,10 m") instead of "não cabe".
- The pull request checklist asks whether a change can affect results, and if it can, for `pytest -m data` or an
  explanation. It no longer asks contributors for `make reproduce`, which depends on live services and on a
  cache only the maintainer has.
- README links are absolute, so they work on PyPI as well as on GitHub.
- Dependency lower bounds are the oldest versions that pass the test suite, and a `lowest` CI job installs
  exactly them. `urllib3` is declared, since mobilidados imports it directly.
- The package ships `py.typed`, so type checkers use its annotations.
- Limits, tolerances and timeouts that were bare numbers in the code are named constants or parameters.
- `mobilidados verify` lists every file that does not match the lock, whatever the number of files.
- The module `network` is now `direction`, after the stage it implements (`network` read as
  network access). `python -m mobilidados` works.
- `occurrences_files.csv` has a `with_date` column: the records with coordinates whose date parsed. A file
  without a located record reports 0, not an empty value, and empty dates.
- A street name that is not in the axes layer (or is in several features or in parts) and an error answered by an
  ArcGIS service are reported as `error: ...` by the command line, like other errors the user can fix.
- The unit suite runs a synthetic case through every stage offline (`tests/test_end_to_end.py`), so CI, including the
  `lowest` job, exercises the whole pipeline, the ledger and the figures.

### Fixed

- The release workflow pinned the PyPI publishing action to the SHA of its tag object instead of its commit, for
  which no container image exists, so the first publication would have failed after creating the GitHub
  release. It checks out the tag by its full ref (never a branch of the same name), installs the built wheel with
  the locked dependency versions before uploading it, names the release after the tagged project (so tags made
  as streetfit can get their releases), and runs one release at a time. `.env` files are ignored by git.
- A service that is down or keeps answering with an error (the Lisbon open-data portal answered 503 for a whole
  day) is reported as `error: <host> did not answer as expected ...`, with the URL, instead of a Python
  traceback.
- A multi-file source whose download failed halfway (an empty or incomplete folder) was taken as cached by the
  next `fetch`, which skipped it. It is now cached only when every listed file is there.
- Fetching data identical to the locked data again rewrote the retrieval times in `sources.lock.json`, leaving
  the repository modified for no change. An entry now changes only when its files do.
- `mobilidados discover` wrote a street-axes template without a licence, which no case could load, and a
  multi-line note or check could break the draft's TOML.
- The claim checker's read tool returned one line more than it told the model.
- The dates of the citizen reports were parsed across all files at once, so a file whose date format differed
  from the first file's lost its dates without a message. Each file is now parsed on its own.
- Generated text agrees with its counts: "1 trip", "1 meeting", "Of 1 street, 1 is two-way", and in Portuguese
  "Foi atribuída à rua 1 ocorrência". A message whose wording depends on a count is a table with `one` and
  `other` forms in `locales/<lang>.toml`, and `i18n.t(..., count=n)` picks the form; a sentence with several
  counts is composed from messages that each follow one count. Texts for counts above one are unchanged, so the
  Lisbon results are too.

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

[Unreleased]: https://github.com/diogo4256/mobilidados/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/diogo4256/mobilidados/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/diogo4256/mobilidados/releases/tag/v0.1.0
