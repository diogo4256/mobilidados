# AI-assisted tools

Install with `pip install 'mobilidados[agents]'` (or `uv sync --extra agents`). The tools call the Claude API
with the model and effort set in `src/mobilidados/agents/common.py` (`MODEL`, `EFFORT`); override them with
`MOBILIDADOS_MODEL` and `MOBILIDADOS_EFFORT`. Set
`ANTHROPIC_API_KEY`, or log in with Anthropic's `ant` CLI. Server-side refusal fallback is enabled.

## Design rule: the model proposes, code verifies

Language models are good at reading messy documents, drawings and APIs, and at noticing an overstatement. They
also make things up. So nothing a model says enters the evidence chain directly:

| Tool | Model output | Deterministic check | If the check fails |
| --- | --- | --- | --- |
| `check-claims` | per-claim verdict with evidence quotes | the claim is in the draft; each quote is verbatim in the cited document near the cited line; cited findings exist; a "supported" claim is backed by a verified quote (12 characters or more) or a cited finding, and its numbers are in that quote or finding; quoted passages in the draft (12 characters or more) are literal | a "supported" verdict becomes `needs_human`, with the reason |
| `extract-standard` | values printed on a page, what they measure, scope, component sums | each value is searched in the PDF text layer and in pooled OCR; sums are recomputed | the value is marked `vision_only`, and the page image is saved for a person to read |
| `discover` | a draft city profile | each proposed layer is fetched again: fields exist; class codes occur in the test area (only with `--bbox`; without it, class codes are not checked) | the check result is written at the top of the draft |

Tests, from cheapest to most complete:

* `tests/test_agents_offline.py`: the deterministic checks, with fabricated model outputs.
* `tests/test_agents_sdk.py`: each tool end to end through the real Anthropic SDK against a mock HTTP transport.
  It asserts the requests (model, effort, structured-output schema, fallback beta, tools, PDF and image blocks),
  runs the tool-runner loop with our tools, and feeds the parsed responses into the checks. No key, no network.
* `tests/test_agents_live.py`: the real API (`pytest -m live`, needs `ANTHROPIC_API_KEY`).

## `mobilidados check-claims CASE draft.md [--corpus source.pdf ...] [--out report.json]`

A fact-checking agent (tool runner with three read-only tools: `list_findings`, `search_sources`,
`read_source`) over the case's findings ledger, the catalogue of design references (`standards.toml`) and any
extra source texts you pass. It classifies each claim as supported, overstated, contradicted, unsupported or
needs_human, and suggests a corrected wording in the draft's language. Use it on every letter before sending.

**Privacy:** the draft is sent to the Claude API. Remove names, addresses and other personal data from the
draft first (keep placeholders such as `[nome]`).

## `mobilidados extract-standard manual.pdf --pages N[,N ...] [--out review.json]`

Design manuals put key widths in cross-section drawings, often raster images without a text layer. Each page
gets three independent readings:

1. the PDF text layer (pypdf);
2. OCR with Tesseract of a high-resolution render, upright and rotated (dimension labels are often vertical),
   in several sparse-text modes, pooled (`OCR_SCALE`, `OCR_PASSES` in `agents/standards_extractor.py`);
3. Claude reading the page as PDF and as a high-resolution image, returning structured values.

A cross-section drawing may have none of its dimensions in the text layer, and OCR may recover only some of
them; the Lisbon manual's two-way profile (catalogue entry `cml_manual_two_way_profile`) is such a page. A value
found by neither stays `vision_only` until a person confirms it on the saved page image. The output is a
review file; adding an entry to `standards.toml` remains a human decision.

## `mobilidados discover --city NAME --start URL [URL ...] [--hosts ...] [--bbox lon,lat,lon,lat]`

An agent explores a municipality's ArcGIS REST directory and open-data catalogue (CKAN/udata APIs) with
GET-only tools limited to allow-listed hosts and a request budget. Redirects are not followed, since the next
hop could leave the allowlist: the agent is told the new address and may request it if its host is allowed.
It proposes the cartography layer and class codes, the street-axis layer, a traffic-direction layer, the GTFS
feed, a citizen-reports dataset and the licence of each, with the evidence it saw. Responses from third-party servers are treated as data, never as
instructions. The result is a `*.draft.toml` with the automatic checks at the top.

## Costs

Each command logs the number of requests and tokens it used. Checking a letter or reading a page takes few
requests; `discover` explores more, within the agent-turn and HTTP-request limits `MAX_TURNS` and
`MAX_REQUESTS` in `agents/source_discovery.py` (`check-claims` has its own `MAX_TURNS`).
