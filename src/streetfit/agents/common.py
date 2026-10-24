"""Shared Claude API settings for the agents."""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = os.environ.get("STREETFIT_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("STREETFIT_EFFORT", "high")
# Server-side fallback: if a request is declined by a safety classifier, the API retries it on a fallback model
# chosen by refusal category, inside the same call.
BETAS = ["server-side-fallback-2026-07-01"]
FALLBACKS = "default"


def client() -> anthropic.Anthropic:
    """Credentials come from the environment (ANTHROPIC_API_KEY) or an `ant auth login` profile."""
    return anthropic.Anthropic()


def request_kwargs(max_tokens: int = 16000) -> dict:
    return {"model": MODEL, "max_tokens": max_tokens, "output_config": {"effort": EFFORT}, "betas": BETAS, "fallbacks": FALLBACKS}


def check_stop(message) -> None:
    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        sys.exit(f"The model declined the request ({getattr(details, 'category', None)}): {getattr(details, 'explanation', '')}")
    if message.stop_reason == "max_tokens":
        sys.exit("The response hit max_tokens before finishing; raise max_tokens or split the input.")


def report_usage(messages: list, log=print) -> None:
    inp = sum(m.usage.input_tokens for m in messages)
    out = sum(m.usage.output_tokens for m in messages)
    cached = sum(getattr(m.usage, "cache_read_input_tokens", 0) or 0 for m in messages)
    log(f"[usage] {len(messages)} request(s), {inp} input tokens ({cached} read from cache), {out} output tokens, model {MODEL}")
