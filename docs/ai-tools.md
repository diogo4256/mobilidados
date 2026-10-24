# AI-assisted tools

Install with `pip install 'streetfit[agents]'` (or `uv sync --extra agents`). The tools call the Claude API
(default model `claude-opus-5-5`; override with `STREETFIT_MODEL`, effort with `STREETFIT_EFFORT`). Set
`ANTHROPIC_API_KEY`, or log in with Anthropic's `ant` CLI. Server-side refusal fallback is enabled.

## Design rule: the model proposes, code verifies

Language models are good at reading messy documents, drawings and APIs, and at noticing an overstatement. They
also make things up. So nothing a model says enters the evidence chain directly:

| Tool | Model output | Deterministic check | If the check fails |
|---|---|---|---|
| `check-claims` | per-claim verdict with evidence quotes | the claim is in the draft; each quote is verbatim in the cited document near the cited line; cited findings exist; the claim's numbers are in the cited finding; quoted passages in the draft are literal | a "supported" verdict becomes `needs_human`, with the reason |
| `extract-standard` | values printed on a page, what they measure, scope, component sums | each value is searched in the PDF text layer and in pooled OCR; sums are recomputed | the value is marked `vision_only`, and the page image is saved for a person to read |
| `discover` | a draft city profile | each proposed layer is fetched again: fields exist, class codes occur in the test area | the check result is written at the top of the draft |

The deterministic halves are unit-tested without network access (`tests/test_agents_offline.py`); the
end-to-end tests run only with credentials (`pytest -m live`).

## `streetfit check-claims CASE draft.md [--corpus source.pdf ...] [--out report.json]`

A fact-checking agent (tool runner with three read-only tools: `list_findings`, `search_sources`,
`read_source`) over the case's findings ledger, the standards catalogue and any extra source texts you pass.
It classifies each claim as supported, overstated, contradicted, unsupported or needs_human, and suggests a
corrected wording in the draft's language. Use it on every letter before sending.

**Privacy:** the draft is sent to the Claude API. Remove names, addresses and other personal data from the
draft first (keep placeholders such as `[nome]`).

## `streetfit extract-standard manual.pdf --pages 194,198 [--out review.json]`

Design manuals put key widths in cross-section drawings, often raster images without a text layer. Each page
gets three independent readings:

1. the PDF text layer (pypdf);
2. OCR with Tesseract: an 8× render, upright and rotated 90° (dimension labels are often vertical), in two
   sparse-text modes, pooled;
3. Claude reading the page as PDF and as a high-resolution image, returning structured values.

On the Lisbon manual's two-way profile (printed p. 152) the text layer contains none of the drawing's
dimensions; pooled OCR recovers 3.00 m and 3.25 m but not 0.40 m. So 0.40 m stays `vision_only` until a person
confirms it on the saved page image. The output is a review file; adding an entry to `standards.toml` remains
a human decision.

## `streetfit discover --city NAME --start URL [URL ...] [--hosts ...] [--bbox lon,lat,lon,lat]`

An agent explores a municipality's ArcGIS REST directory and open-data catalogue (CKAN/udata APIs) with
GET-only tools limited to allow-listed hosts and a request budget. It proposes the cartography layer and class
codes, the street-axis layer, a traffic-direction layer, the GTFS feed, a citizen-reports dataset and the
licence of each, with the evidence it saw. Responses from third-party servers are treated as data, never as
instructions. The result is a `*.draft.toml` with the automatic checks at the top.

## Costs

Each command prints the number of requests and tokens. One manual page or one short letter is a few requests;
`discover` explores more and is capped at 60 agent turns and 80 HTTP requests.
