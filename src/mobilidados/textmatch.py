"""Deterministic text checks used to verify what a language model proposes.

A model may say a quote is in a source, or that a value is printed on a page. These functions check that
mechanically: accent- and case-insensitive, whitespace- and hyphenation-tolerant, decimal comma == point.
"""

from __future__ import annotations

import re
import unicodedata

_QUOTES = str.maketrans({"«": '"', "»": '"', "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "−": "-"})


def normalize(text: str) -> str:
    """Lower-case, strip accents, unify quotes/dashes, join hyphenated line breaks, collapse whitespace."""
    t = unicodedata.normalize("NFKD", text.translate(_QUOTES))
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)  # "desne-\ncessários" -> "desnecessários"
    return re.sub(r"\s+", " ", t).strip()


def contains(haystack: str, needle: str) -> bool:
    """Verbatim match up to case, accents and whitespace (PDF text layers often split or join words)."""
    h, n = normalize(haystack), normalize(needle)
    return n in h or n.replace(" ", "") in h.replace(" ", "")


def numbers(text: str) -> list[float]:
    """Decimal numbers in a text, accepting both 4,90 and 4.90 (thousands separators are not expected here)."""
    return [float(m.group(0).replace(",", ".").replace("−", "-")) for m in re.finditer(r"(?<![\w.,])[-−]?\d+(?:[.,]\d+)?", text)]


def printed_variants(value: float) -> set[str]:
    """How a metric value can be printed: 3, 3.0, 3,00, 3.00 ..."""
    v = set()
    for d in (0, 1, 2):
        s = f"{value:.{d}f}"
        if float(s) == round(value, 2):
            v |= {s, s.replace(".", ",")}
    return v


def value_in_text(value: float, text: str) -> bool:
    """True if ``value`` appears as a standalone number in ``text`` (any of its printed forms)."""
    t = normalize(text)
    # not part of a longer number on either side: "3" must not match "13", "3,25" or "3.5"
    return any(re.search(rf"(?<![\d.,]){re.escape(p)}(?![\d]|[.,]\d)", t) for p in printed_variants(value))


def quote_near(lines: list[str], quote: str, line: int, window: int = 6) -> bool:
    """True if ``quote`` occurs in ``lines`` within ``window`` lines of 1-based ``line`` (or anywhere if line <= 0)."""
    if line <= 0:
        return contains("\n".join(lines), quote)
    lo, hi = max(0, line - 1 - window), min(len(lines), line + window)
    return contains("\n".join(lines[lo:hi]), quote)
