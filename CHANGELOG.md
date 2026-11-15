# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

The toolset is for citizens to make their case from published data alone: nothing in it asks anyone to observe,
count or collect anything, and where the data stop, it helps them ask the body that holds the rest.

### Added

- **Sidewalks against the accessibility law** (the `sidewalks` stage, `[sidewalks]` in a case; method in
  docs/methodology.md). Decree-Law 163/2006 requires pedestrian routes to keep a free channel at least 1.2 m wide,
  with obstructions (street furniture, trees, signs) counted against it, and admits a narrower stretch only if it is
  short (section 4.3.3). The values are in `data/standards.toml`, from the 2006 publication pinned by its checksum,
  with their page and quote, as a new kind, `legal_requirement`. At each station the stage reads the widest piece of
  mapped sidewalk between the kerb and the buildings; where it runs up to the buildings, the free channel cannot be
  wider, so a stretch narrower than the law admits for its length rests on the cartography alone. Where it ends at a
  yard or at something unmapped, the stretch is one to check, never one below the law; a wide mapped sidewalk is never
  presented as a clear one. Junctions, widenings, medians, islands, arcades and slivers are left out. Stretches
  still below if each mapped edge were off by the cartography's stated accuracy are told apart. Findings
  `sidewalks` (M), `sidewalks_law` (D), `sidewalks_narrow` (I) and, where it applies, `sidewalks_to_check` (M); tables
  `sidewalks.csv`, `sidewalk_narrow_sections.csv` (with the coordinates of each stretch), `sidewalk_profile.csv`; figure
  `sidewalk_profile.png`. `[cartography]` gains `overhead` and `yard` class lists.
- **Screening of the area** (`area_sidewalks` and `screening` stages, `mobilidados screen CASE`). Every street of the
  case's area is scanned for narrow sidewalks the same way (`[area_scan] sidewalks`, `exclude_streets`), and
  `results/screening.md` ranks the streets with buses squeezed by parking and the streets with sidewalks narrower than
  the law admits, with where to look and the commands that make a case for one. Finding `sidewalks_area` (M) names
  only the streets below even with the accuracy margin. In Lisbon a new source, `area_sidewalks`, holds the area's
  road, parking, sidewalk and plot polygons; `new-case` gives it the area's envelope.
- **Letter drafts** (`mobilidados draft CASE --topic buses|sidewalks [--ask review|documents]`). A first letter to a
  public body, written from `findings.json` alone as docs/writing-to-public-bodies.md advises: one topic; the facts
  grouped as measured, official documents and estimates, each with its finding id; the assumptions they rest on,
  declared; one request (that the services check and act, or a request for documents under Law 26/2016, articles 12
  and 15); the attachments, with the points or stretches where a technician can measure. Every statement is the
  ledger's own, and the draft is linted before it is written.
- **Rua Ricardo Jorge dossier** (`cases/lisboa-rua-ricardo-jorge/dossier.md`, and its PDF): the case written up for
  the Câmara, every number with its finding id and grade, the comparisons that hold within the cartography's error led
  with, and a table of what the data do not show and who can provide it. `tests/test_cases.py` fails if a dossier cites
  a finding that does not exist, fails `lint`, or gives a number with a unit that neither the ledger nor a table it
  links to gives.
- Findings: `width_accuracy` (I), whether the width comparisons hold if every mapped edge were off by the stated
  accuracy (`[cartography] edge_accuracy_m`, which the sidewalk tool now reads too); `fleet` (M), the fleet-number
  series the archive shows on the stretch for each route (`delay_fleet.csv`). The encounters finding splits the
  meetings by pair of routes. In Rua Ricardo Jorge: with 0.30 m per edge, 5.50 m, still short of the 5.80 m of two
  buses with mirrors and 1.30 m short of the municipal reference profile; the bodies-only margin (−0.10 m) is within
  that error. Route 744 runs mostly with 26xx vehicles (79% of positions), the reference vehicle's series; 46B only
  with 2xx; 4–5 of the 6–7 daily meetings are between two 744 buses.
- The reference bus says what Carris's fleet pages show: the 12 standard models are 2.5 to 2.6 m wide, so 2.50 m is
  the narrowest.
- Writing guide: start from a draft, and ask for the documents the data do not cover (Law 26/2016: who must answer,
  in how many days, and the complaint to the CADA). Evidence standard: say which way a measurement can point, and a
  law is not a manual.

### Fixed

- The free-width figure no longer scales to the cross streets at the ends of the axis (up to 50 m), which flattened
  the narrow stretches; close reference values are labelled apart.
- The width-budget finding uses the car's width with mirrors, an assumption, but did not list it among its sources,
  so a letter could not declare it.
- A cartography polygon with an invalid ring is repaired when it is read, instead of stopping the run.

## [0.4.0] - 2026-11-15

### Added

- **Time on a stretch, measured from archived bus positions** (the `delay` stage, `[delay]` in a case; method in
  docs/methodology.md). A new source kind, `git_archive`, reads a public git archive of an operator's real-time
  feed pinned to a commit, and keeps the case's routes inside an envelope; the lock records the commit and the
  sha256 of what was extracted. The stage compares the time buses spend on a stretch between stops with the time
  they spend on control stretches of the same routes, at the evening peak and off-peak on working days
  (occupancy, Little's law): the ratio needs no count of buses and uses every snapshot; the seconds use only the
  hours densely recorded. 90% intervals come from a bootstrap over days. The tables record the checks: the
  passages counted against the timetable, the estimate with each choice changed in turn, by year, by route and
  direction, and by hour; `tests/test_delay.py` simulates buses with known times and checks the estimator gives
  them back. Two findings (grade I) say what was measured, by year, and not why; they name the data's chain (Carris,
  a relay, the archive), which is not Carris's own record. `[city] holidays` lists the public holidays, which are
  not working days. `new-case` leaves `[delay]` out of a draft, since it depends on the street's stops.
- Rua Ricardo Jorge: on working days at 17h–19h the stretch between its stops took 49% longer than the slowdown
  of the routes' neighbouring stretches would explain (90% interval: 34% to 65%); about 14 s more per bus
  (6 to 24 s), the excess coming at 17h. In 2025 +60% (+42% to +80%); in 2026, with far fewer positions, +4%
  (−17% to +31%), which does not confirm it.
- Evidence standard: a rule for data relayed or archived by a third party (name the chain, check it against an
  official source, grade what is computed from it as an inference).

- `mobilidados verify CASE --live` downloads a case's sources again into a temporary folder and says, file by file,
  whether each service still serves what the lock records (`same`, `changed`, `new`) or did not answer, without
  touching the cache or the lock. A monthly workflow (`.github/workflows/sources.yml`) runs it for every case.
- `docs/maintaining.md`: the regular checks, what to do when a source's data changes or a service moves or goes
  down, how to archive a case's inputs, and how dependencies and Python versions are kept up to date.

### Changed

- The READMEs say the package is on PyPI and that the cases and city profiles stay in the repository.
- Every length of street in the ledger follows one rule: each 0.5 m station stands for the stretch within half a
  step of it, cut at the ends of the axis (`geometry.covered`, explained in docs/methodology.md). The stretches with
  parking on both sides were measured from their first to their last station, one step short per section, while
  the mapped parking per side counted a step per station; the shorter length also understated the parking an
  option removes. In Rua Ricardo Jorge the stretches with parking on both sides measure 117.5 m (was 116 m), and
  removing the parking on both sides would remove about 39 to 47 places (was 38 to 46); one side, 19 to 23 places,
  as before. No width, count of meetings or other number changes. Lengths are printed to 0.1 m wherever they
  appear, so the same length reads the same in every finding and figure.
- The READMEs open with what the Rua Ricardo Jorge example finds, each line with its grade, and say who the
  tool is for and what it is not (a street design tool, a parking inventory, a bus-speed tracker).

### Fixed

- `verify` and the data test only looked at the sources the lock lists, so a case that was never fetched passed
  `verify` ("0/0 files match the lock") and the data test then crashed on a missing file. Every source the case
  configures is now checked, and one the lock has no entry for is reported as `not fetched`.
- A case's inputs can no longer change without anyone noticing:
  - `fetch` rewrote the lock to match whatever a service now served, so `verify` then reported nothing. It now
    prepares each source in a temporary folder and compares it with the lock before touching the cache: from a
    service, different data is refused unless `--refresh` takes it deliberately; from a folder (`--from-dir`), only
    exactly the locked files, and any pin, are accepted. A download that fails halfway leaves nothing in the cache.
  - A multi-file source takes, and the occurrences stage reads, only the files the source names; a file left in
    its folder is not read.
  - `snapshot` copied whatever the cache held, an empty folder included, and logged sources it had not found as
    not redistributable. It now refuses a cache that does not hold exactly the locked files of every
    redistributable source, and copies only those files.
  - `verify` no longer fails on a routing-network cache that only a run makes (it lists it as `later`); the data
    test fails, listing the files, instead of being skipped when the cache does not hold the locked ones; and
    `make reproduce` also fails when the run changed the lock.
- A site that refuses a request as automated (a Cloudflare challenge) and an address that no longer exists (404)
  are reported as such, instead of as a service that may be down for a while; the run's remedies name `--refresh`
  where it is needed.
- The AI tools now do what the documentation promised, that nothing a model says counts as evidence by itself:
  - `check-claims` kept a "supported" verdict that no check backed (no evidence quote and no cited finding), and
    checked numbers only when the model labelled the claim a number. A supported claim now needs a verified quote
    of at least 12 characters or a cited finding that exists, and its numbers must be in them, whatever its kind;
    otherwise it becomes `needs_human`.
  - `discover` followed redirects to any host. It no longer follows them: the agent is told the new address and
    may request it if its host is allowed. The docs say class codes are only checked when `--bbox` gives a test
    area.
  - A cut-off answer says what can be done (a lower `MOBILIDADOS_EFFORT`, a shorter draft) instead of naming a
    setting the command line does not have.
- Cases on other streets no longer break or mislead where the Lisbon case did not reach. None of these changes a
  Lisbon number:
  - buses in one direction only, or no meeting at an assumed speed: the encounters statement gives 0 instead of
    an empty count;
  - a street without parking mapped on both sides runs to the end and says so, without a width budget or design
    references, which compare a free width it does not have;
  - a reference stop that no trip serves on the service day, with a following stop, is an error naming the
    route, direction, stop and day, instead of a Python traceback;
  - a profile step that is not a multiple of 10 cm keeps its stretches and check points, and a check point
    beyond the axis is an error naming it;
  - a trip that serves its reference stop twice (a loop) is counted once, and two reference stops for the same
    route and direction are a configuration error; `new-case` keeps the heading most of a direction's trips have;
  - the area scan and `new-case` read and write envelopes in the spatial reference their source states;
  - "em k de n pontos" counts every configured traffic station, also one the routing network gave no answer
    for; runtime medians and years print as numbers of the case's language;
  - the trips-per-hour figure and the area figure name the service day without calling it a weekday.
- The area scan no longer counts a sliver of mapped parking narrower than 0.5 m as a parking strip, the rule the
  case street already followed. In the Lisbon area tables, the share of each street with parking on both sides
  drops by one or two points on four streets (`pct_parking_both_sides` in `area_streets.csv`) and ten stations
  change in `area_stations.csv`; which streets have the pattern, their metres with it, and the ledger are unchanged.
- A run stops when a cached file differs from the sha256 in `sources.lock.json`, which the ledger publishes,
  routing-network answers (identify caches) included. A missing file is not an error, since a partial run may not
  need it. An identify cache is locked each time new answers are saved, with the time of that change; before, it
  was locked only when the whole run ended, after the ledger had published the previous checksum.
- A `new-case` draft written outside the folder that holds the model case and its city file (with `--out`)
  extends the city file by its absolute path. Before, it got a relative path such as
  `../../../../home/user/mobilidados/cities/lisboa.toml`, which broke as soon as either side moved.
- The figures no longer depend on a machine's matplotlib settings. They start from matplotlib's own defaults, so a
  local `matplotlibrc` (another font, for example) no longer changes them, and a figure whose pixels are unchanged
  keeps its file, since the PNG compression differs from one platform to another. With the locked package
  versions, the Lisbon figures drawn on Linux and on macOS were identical pixel for pixel. The figures stage also removes the
  figures an earlier configuration made, which a full run used to do.
- On a street where the timetable has buses in one direction only, the ledger names the direction without buses
  ("72 trips S→N and none N→S") instead of printing 0 trips and at most 0 per hour, and says that buses in one
  direction do not meet head-on instead of "0 meetings; 0 fall within the sections with parking on both sides".
  The values in `findings.json` are unchanged.
- Streets with the same rate of reports share a rank in the occurrences finding; the case street was ranked below
  a street with the same rate whose name sorts first.
- An area scan in which no bus runs along any street axis wrote tables without a header, which the ledger then
  failed to read; they are written empty with their columns.
- A case without a `question` no longer starts its `findings.md` with an empty quote.
- `lint --lang` accepts only the languages it has rules for (`pt`, `en`), instead of silently checking only the
  quotation marks of any other; `extract-standard --pages` reports page numbers it cannot read as a usage error,
  not a traceback.

## [0.3.0] - 2026-10-24

The project is now called **mobilidados**: tools for data-based mobility claims in Portugal, starting with
Lisbon. The street-width audit is its first tool. Versions 0.1.0 and 0.2.0 were released as
streetfit.

### Added

- The option without parking states what it removes: metres of mapped parking (one side and both sides, along
  the stretches with parking on both sides), places as a range over assumed space lengths
  (`profiles.parking_space_m`, the same lengths `parking_strip_lengths.csv` already used), and the mapped parking
  along the whole street on each side, as a ledger finding (`parking_removed`), as columns of `without_parking.csv`
  and as a note on the width figure.
- Each run writes the resolved configuration it used to `results/config.json`, so a change to a city profile shows
  up as a diff in every case that uses it, and the reproduction test compares it.
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

- Every finding states its method and its limits in the case's language (`[method]` and `[caveat]` in the
  locales), and the limits say more:
  - the free width says which stations count and how many with parking on both sides are left out for being
    wider than `profiles.narrow_max_m`, and names the cartography's survey and accuracy (`cartography.survey`
    and `accuracy_note` can be given per language);
  - the width budget says "at least" (bodies with no gap between them), the bus × bus margin at the minimum,
    median and 95th percentile of the free width, the share of stations below two bus bodies, and which mirrors
    count;
  - the traffic direction says at how many of the checked points both directions are open;
  - the encounters name the service day (they said "per weekday", which nothing checked) and the limits of the
    constant-speed model;
  - the occurrences say that the ranking divides by each street's whole length, which favours streets that lie
    wholly inside the attribution window, such as the case street; the computation is unchanged;
  - the area scan says it uses its own parameters and thresholds chosen for the analysis.

  The Lisbon findings keep their ids, grades, values and sources. The Portuguese scope of RASt 06 says "Diretriz
  técnica", vehicle labels lose their quotation marks, the mirror-width gap no longer repeats a configured
  number, and the width figure shows the margin with and without mirrors for both pairs, labels the median free
  width as such, keeps that line from crossing the notes and draws the option without parking in grey.
- The documentation calls the municipal manual and the German guideline design references, not norms; it says
  exactly where each input comes from (the GTFS feed from the Mobility Database archive, the traffic direction
  from the Lisboa Interativa public viewer in guest access, whose address carries a backup date); it states the
  roles of public bodies no further than is certain; and the Lisbon case's README points to the layered settings.
- `mobilidados lint` also flags plural forms of normative words ("normas", "regras", "obrigatórios").
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

[Unreleased]: https://github.com/diogo4256/mobilidados/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/diogo4256/mobilidados/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/diogo4256/mobilidados/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/diogo4256/mobilidados/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/diogo4256/mobilidados/releases/tag/v0.1.0
