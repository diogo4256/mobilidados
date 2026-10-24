"""Messages for figures, the findings ledger and reports, from ``locales/<lang>.toml``.

Add a language by copying ``locales/en.toml`` and translating the values (keep the ``{placeholders}``), then add
its code to ``config.Lang``.
"""

from __future__ import annotations

import functools
import tomllib
from importlib import resources
from typing import Any


@functools.cache
def messages(lang: str) -> dict[str, str]:
    """All messages of a language, keyed ``section.key`` (e.g. ``ledger.length``)."""
    data = tomllib.loads(resources.files("streetfit.locales").joinpath(f"{lang}.toml").read_text(encoding="utf-8"))
    return {f"{section}.{k}": v for section, table in data.items() for k, v in table.items()}


def t(key: str, lang: str, **kw: Any) -> str:
    return messages(lang)[key].format(**kw)


def num(x: float, lang: str, d: int = 2, sign: bool = False) -> str:
    """A number as printed in ``lang``: decimal comma in Portuguese, a true minus sign in both."""
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−") if lang == "pt" else s.replace("-", "−")
