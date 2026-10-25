# Maintaining mobilidados

What keeps the published cases checkable over the years, and what to do when something around them changes. The
cases depend on services run by others (municipal GIS, open-data portals, operators), which update their data,
move and sometimes go down. The toolset cannot prevent that; it records what each case used, notices when a
service no longer serves it, and keeps the inputs that may be redistributed in an archive.

## Regular checks

* **Are the sources still there?** `mobilidados verify CASE --live` downloads every source again into a temporary
  folder and compares it with the case's `sources.lock.json`, without touching the cache or the lock:

  | Status | Meaning | What to do |
  | --- | --- | --- |
  | `same` | the service still serves the locked file | nothing |
  | `changed` | the service now serves different data | see [The data changed](#the-data-changed) |
  | `new` | a file the lock does not have | the case's configuration changed since it was fetched; fetch and run it |
  | `error: ...` | the service did not answer, or a pinned file is no longer served | see [A service moved or is down](#a-service-moved-or-is-down) |

  The `sources` workflow (`.github/workflows/sources.yml`) runs it for every case once a month; a failed run, which
  GitHub reports to the maintainers, means a source changed, moved or did not answer. Run it by hand too before
  using a case in a letter or an article.
  The routing-network answers (`arcgis_identify` sources) are not checked: they are queried point by point during
  a run.
* **Do the results still come out the same?** `pytest -m data` re-runs every case from its cache and compares the
  results with the committed ones. It needs the cache (`mobilidados fetch`, or `fetch --from-dir` from an
  archive), so it runs on a maintainer's machine, before merging anything that touches `src/`, `cities/` or a case.
* **Dependencies.** Dependabot opens one grouped pull request a month for the GitHub Actions and one for the
  Python packages (`.github/dependabot.yml`). Merge them when CI is green, including the `lowest` job, which
  installs the oldest versions `pyproject.toml` allows. When a lower bound no longer passes, raise it to the
  oldest version that does, and say why next to it.
* **Python versions.** The versions supported are the ones in the CI matrix (`.github/workflows/ci.yml`) and
  `requires-python` in `pyproject.toml`. Add a new Python to the matrix when it is released; when one reaches its
  end of life, drop it from both and from the classifiers.

## The data changed

A published case keeps the inputs it was run with: its pins (in the dated city file it extends, such as
`cities/lisboa-2026-10.toml`), its lock and, where the licence allows, an archived copy. Do not change those pins
to follow the new data, and do not re-run a published case on the new data.

To analyse the new data, add a new dated city file (for example `cities/lisboa-2027-03.toml`, extending the same
city profile) and run the case again from it, as a new case or a new reference run. The values already quoted
from the earlier run stay as they were, and the new results are added next to them.

## A service moved or is down

1. **Find out which.** A 503 or a maintenance page from the publisher (the Lisbon portal redirects to
   `offline.cm-lisboa.pt`) means the service is down; a 404, or an address that no longer exists, means it moved.
   A Cloudflare challenge ("Just a moment...") means the request was refused as automated, which can depend on
   where it comes from: try from another network before concluding the service is down.
2. **If it moved:** find the new address of the same file, download it and compare its sha256 with the lock. If
   it is the same file, update the address in the dated city file; `results/config.json` records the change and
   the results stay the same. If it is a different file, it is new data (see above).
3. **If it is down:** restore the inputs from the case's archive with `mobilidados fetch CASE --from-dir FOLDER`,
   which checks each file against the lock. Without an archive, the case cannot be re-run from scratch until the
   service is back; say so where the case is cited.
4. **Sources whose licence is not stated** cannot be archived publicly. For the Carris GTFS, the Mobility
   Database archive keeps the exact file the case pins. The routing-network answers are cached during the run
   and stay on the machine that ran it; if the service moves, the address in the city profile has to be updated
   (the Lisboa Interativa address embeds a backup date and changes from time to time).

## Archiving a case's inputs

`mobilidados snapshot CASE FOLDER` copies the cached inputs whose licence allows redistribution
(`redistributable = true` in the city profile), with their lock metadata in `_snapshot.json`. Publish the folder
on an archive that gives a permanent identifier, such as [Zenodo](https://zenodo.org) (title naming the case and
the date of the data, the licence of the inputs, and the attribution their publishers require), and add the DOI
to the case's `README.md`. Anyone can then rebuild the case with `mobilidados fetch CASE --from-dir FOLDER`
followed by `mobilidados run CASE`, even when the publisher's service is down.

Archive the inputs when a case is first published, and again for each new dated city file.

## Regenerating results

* `mobilidados run CASE` re-runs every stage; `--stages ... --offline` re-runs some of them from the cache, which is
  how a change to the ledger or the figures is applied without downloading anything.
* A run stops when a cached file differs from the lock, and when a pinned file differs from its pin; a missing
  file is not an error, since a partial run may not need it.
* Figures come out the same on any machine: they start from matplotlib's defaults, and a figure whose pixels did
  not change keeps its file.
* Commit the changed results with the change that caused them, and say in the pull request which numbers changed
  and why.

## Releasing

See [CONTRIBUTING.md](../CONTRIBUTING.md#releasing).
