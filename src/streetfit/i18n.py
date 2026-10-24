"""Messages for figures, the findings ledger and reports, from ``locales/<lang>.toml``.

A message is a string with ``{placeholders}``. A message whose wording depends on a count is a table with one
string per plural category (``one``, ``other``), and ``t(..., count=n)`` picks the form with the language's rule.
A sentence with several counts is composed from messages that each depend on one count.

Add a language by copying ``locales/en.toml`` and translating the values (keep the ``{placeholders}``), then add
its code to ``config.Lang`` and its plural rule to ``PLURAL_RULES``.
"""

from __future__ import annotations

import functools
import tomllib
from collections.abc import Callable
from importlib import resources
from typing import Any

Message = str | dict[str, str]


def one_only_for_exactly_one(count: float) -> str:
    """English and European Portuguese: the singular is for 1 and nothing else (0 is plural in both)."""
    return "one" if count == 1 else "other"


# CLDR plural rule of each language; the categories a rule returns are the forms a plural message must have.
PLURAL_RULES: dict[str, Callable[[float], str]] = {"en": one_only_for_exactly_one, "pt": one_only_for_exactly_one}


@functools.cache
def messages(lang: str) -> dict[str, Message]:
    """All messages of a language, keyed ``section.key`` (e.g. ``ledger.length``)."""
    data = tomllib.loads(resources.files("streetfit.locales").joinpath(f"{lang}.toml").read_text(encoding="utf-8"))
    return {f"{section}.{k}": v for section, table in data.items() for k, v in table.items()}


def t(key: str, lang: str, count: float | None = None, **kw: Any) -> str:
    """A message with its placeholders filled from ``kw``. ``count`` only picks the form of a plural message."""
    message = messages(lang)[key]
    if isinstance(message, dict):
        if count is None:
            raise TypeError(f"{key} has plural forms: pass count=")
        message = message[PLURAL_RULES[lang](count)]
    return message.format(**kw)


def num(x: float, lang: str, d: int = 2, sign: bool = False) -> str:
    """A number as printed in ``lang``: decimal comma in Portuguese, a true minus sign in both."""
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−") if lang == "pt" else s.replace("-", "−")
