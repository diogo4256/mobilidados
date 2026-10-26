# Contributing

Thank you for helping. The most valuable contributions are **new cities and new cases**: each one tests the
method on different cartography and makes the tool useful to more people.

## Ways to contribute

* **A new case** (a street in a city that already has a profile): `mobilidados new-case "<street>" --like
  cases/<a case of that city>` drafts `cases/<city>-<street>/case.toml`; check what its header lists, then add
  `sources.lock.json`, `results/` and a short `README.md`. Open an issue with the *New case*
  template first if you want feedback on the question.
* **A new city**: add `cities/<city>.toml` and one case that uses it. See [docs/adding-a-city.md](docs/adding-a-city.md).
* **Design references**: add entries to `src/mobilidados/data/standards.toml` with the document's URL and SHA-256,
  printed and PDF page, a verbatim quote and the scope. `mobilidados extract-standard` helps read drawings; a
  human confirms every value.
* **Vehicles**: add entries to `src/mobilidados/data/vehicles.toml` with a source and an evidence grade.
  Catalogue text in other languages goes in a `translations.<lang>` table after the entry.
* **A language**: copy `src/mobilidados/locales/en.toml` to `<lang>.toml`, translate the values (keep the
  `{placeholders}`), add the code to `Lang` in `src/mobilidados/config.py` and its plural rule to `PLURAL_RULES` in
  `src/mobilidados/i18n.py`. A message that depends on a count is a table with the forms `one` and `other`
  (`one` is the singular; write both, with the same placeholders in each). A test checks that every key, form and
  placeholder is there.
* **Code**: new source kinds (WFS, OGC API Features, OpenStreetMap), swept-path analysis, orthophoto checks.

## Ground rules

Before changing the method, the tools or the wording, weigh the change against
[docs/stakeholders.md](docs/stakeholders.md): who makes claims with these results, who answers them, who is affected,
whose data is used, and what a toolset like this can and cannot do.

1. **Evidence first.** Every number in a case comes from a source in `sources.lock.json` or the catalogues, with
   a grade (see [docs/evidence-standard.md](docs/evidence-standard.md)). No hand-typed results.
2. **Licences.** Record each source's licence as its publisher states it. Do not commit raw third-party data
   (`cases/*/data/` is git-ignored); commit derived results and the lock file.
3. **No personal data.** Do not commit letters with names or addresses, citizens' individual reports, or
   anything identifying a private person. Aggregates only.
4. **Reproducible.** `pytest -m data` re-runs every case from its locked sources and must leave the committed
   tables and findings unchanged, unless the pull request explains the change. The sources are cached outside
   the repository (`mobilidados fetch` fills the cache, and the live services may have changed since), so the
   maintainer runs this check before merging anything that touches `src/`, `cities/` or a case. A run also
   writes the resolved configuration it used to `results/config.json`, which is committed and checked in the
   same way: method parameters live in city profiles that several cases share, so a change to a city profile
   shows up as a diff in the `config.json` of each case that uses it.
5. **AI output is a proposal.** Code that uses a model must verify its output deterministically before it is
   used (see [docs/ai-tools.md](docs/ai-tools.md)).

## Development

```bash
uv sync --extra agents
uv run pre-commit install     # optional: ruff, formatting and REUSE checks before each commit
make lint test                # what CI runs: ruff, mypy, pytest
make reproduce                # fetches what is not cached, re-runs the case and fails if its lock or results changed
```

Keeping the published cases checkable (sources that change, move or go down; archiving a case's inputs; dependency
and Python updates) is described in [docs/maintaining.md](docs/maintaining.md).

Tests: unit tests use synthetic data and need no network; warnings fail them, so deprecations surface early. `pytest -m data` re-runs every case from its cache
and compares with the committed results. `pytest -m live` calls the Claude API (needs credentials).

## Pull requests

Keep them focused; describe what changed in the results if a case's tables change, and why. By contributing
you agree that your contributions are licensed under Apache-2.0 (code) and CC-BY-4.0 (documentation and
results), as described in [REUSE.toml](REUSE.toml).

## Releasing

1. `uv version X.Y.Z` sets the version in `pyproject.toml` and `uv.lock`. Set it, with the release date, in
   `CITATION.cff` too.
2. In `CHANGELOG.md`, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, open a new empty `[Unreleased]` above it
   and update the link definitions at the bottom.
3. Commit, then tag and push: `git tag -a vX.Y.Z -m "mobilidados X.Y.Z" && git push origin main vX.Y.Z`.

The tag starts `.github/workflows/release.yml`. It stops if the tag differs from the version in `pyproject.toml` or
`CITATION.cff`, if the changelog has no section for it or if the unit tests fail on the tagged commit. Otherwise it
builds the package, checks that the wheel installs, makes a GitHub release with the changelog section as notes and
publishes to PyPI through trusted publishing (no token is stored). Publication can be made to wait for a
maintainer's approval by adding required reviewers to the `pypi` environment in the repository settings.

`README.md` (Portuguese) and `README.en.md` (English) say the same, each written in its own language rather than
translated sentence by sentence; a change to one goes into both. Their links are absolute because PyPI shows
`README.md` as the project page. They point to `main`, so the page of an older release links to the current files.
