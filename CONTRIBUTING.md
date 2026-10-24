# Contributing

Thank you for helping. The most valuable contributions are **new cities and new cases**: each one tests the
method on different cartography and makes the tool useful to more people.

## Ways to contribute

* **A new case** (a street in a city that already has a profile): add `cases/<city>-<street>/` with
  `case.toml`, `sources.lock.json`, `results/` and a short `README.md`. Open an issue with the *New case*
  template first if you want feedback on the question.
* **A new city**: add `cities/<city>.toml` and one case that uses it. See [docs/adding-a-city.md](docs/adding-a-city.md).
* **Design references**: add entries to `src/streetfit/data/standards.toml` with the document's URL and SHA-256,
  printed and PDF page, a verbatim quote and the scope. `streetfit extract-standard` helps read drawings; a
  human confirms every value.
* **Vehicles**: add entries to `src/streetfit/data/vehicles.toml` with a source and an evidence grade.
* **Code**: new source kinds (WFS, OGC API Features, OpenStreetMap), swept-path analysis, orthophoto checks,
  translations of the ledger templates (`report.py`, `i18n.py`).

## Ground rules

1. **Evidence first.** Every number in a case comes from a source in `sources.lock.json` or the catalogues, with
   a grade (see [docs/evidence-standard.md](docs/evidence-standard.md)). No hand-typed results.
2. **Licences.** Record each source's licence as its publisher states it. Do not commit raw third-party data
   (`cases/*/data/` is git-ignored); commit derived results and the lock file.
3. **No personal data.** Do not commit letters with names or addresses, citizens' individual reports, or
   anything identifying a private person. Aggregates only.
4. **Reproducible.** `make reproduce CASE=cases/<case>` must leave `results/tables` unchanged.
5. **AI output is a proposal.** Code that uses a model must verify its output deterministically before it is
   used (see [docs/ai-tools.md](docs/ai-tools.md)).

## Development

```bash
uv sync --extra agents        # Python 3.11+
uv run pre-commit install     # optional: ruff, formatting and REUSE checks before each commit
make lint test                # what CI runs
make reproduce                # re-runs the Lisbon case from its sources (downloads ~250 MB)
```

Tests: unit tests use synthetic data and need no network. `pytest -m data` re-runs every case from its cache
and compares with the committed results. `pytest -m live` calls the Claude API (needs credentials).

## Pull requests

Keep them focused; describe what changed in the results if a case's tables change, and why. By contributing
you agree that your contributions are licensed under Apache-2.0 (code) and CC-BY-4.0 (documentation and
results), as described in [REUSE.toml](REUSE.toml).
