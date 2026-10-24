CASE ?= cases/lisboa-rua-ricardo-jorge

.PHONY: install test lint reproduce fetch verify

install:            ## dev environment with the optional AI tools
	uv sync --extra agents

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

test:               ## unit tests (no network, no data)
	uv run pytest -m "not data and not live"

fetch:
	uv run streetfit fetch $(CASE)

verify:
	uv run streetfit verify $(CASE)

reproduce: fetch verify   ## re-run a case and fail if any committed table changes
	uv run streetfit run $(CASE)
	git diff --exit-code -- $(CASE)/results/tables $(CASE)/results/findings.json
