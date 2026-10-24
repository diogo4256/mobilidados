"""Shared Claude API settings for the agents."""

from __future__ import annotations

import logging
import os
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from ..config import StreetfitError

log = logging.getLogger(__name__)

MODEL = os.environ.get("STREETFIT_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("STREETFIT_EFFORT", "high")
# Server-side fallback: if a request is declined by a safety classifier, the API retries it on a fallback model
# chosen by refusal category, inside the same call.
BETAS = ["server-side-fallback-2026-07-01"]
FALLBACKS = "default"


def client() -> anthropic.Anthropic:
    """Credentials come from the environment (ANTHROPIC_API_KEY) or an `ant auth login` profile."""
    return anthropic.Anthropic()


def request_kwargs(max_tokens: int = 16000) -> dict[str, Any]:
    return {"model": MODEL, "max_tokens": max_tokens, "output_config": {"effort": EFFORT}, "betas": BETAS, "fallbacks": FALLBACKS}


Output = TypeVar("Output", bound=BaseModel)


def parsed(message: Any, schema: type[Output]) -> Output:
    """The structured output of a final message, after checking that the model finished its answer."""
    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        raise StreetfitError(
            f"the model declined the request ({getattr(details, 'category', None)}): {getattr(details, 'explanation', '')}"
        )
    if message.stop_reason == "max_tokens":
        raise StreetfitError("the response hit max_tokens before finishing; raise max_tokens or split the input")
    out = message.parsed_output
    if not isinstance(out, schema):
        raise StreetfitError(f"the answer does not match the {schema.__name__} schema")
    return out


def report_usage(messages: list[Any]) -> None:
    inp = sum(m.usage.input_tokens for m in messages)
    out = sum(m.usage.output_tokens for m in messages)
    cached = sum(getattr(m.usage, "cache_read_input_tokens", 0) or 0 for m in messages)
    log.info(
        "[usage] %d request(s), %d input tokens (%d read from cache), %d output tokens, model %s", len(messages), inp, cached, out, MODEL
    )
