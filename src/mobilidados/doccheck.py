"""Checking a written document against the case's results, without AI (``mobilidados check-doc``).

Decision papers and reports are written by hand from the result tables, so their numbers can drift when the model
changes, and a sentence can outlive the condition it described. Three checks catch that:

* **claims**: the document's key statements, each pinned in the case's ``doc_check.toml`` to the model output it
  quotes (a cell of a result table, or arithmetic on cells), found by a pattern in each language and compared at
  the precision printed;
* **orphans**: every other number in the document that no result table, input or configured value explains at the
  precision printed, listed with its context for a person to check;
* **languages**: the numbers one language version prints and the other does not.

A number "explains" a printed one when, scaled by 1, 1/1000 (thousands of euros) or 100 (a share as a percentage), it
rounds to it: to the decimals printed, or, for a whole number ending in zeros, to the tens, hundreds or thousands it
was rounded to.
"""

from __future__ import annotations

import math
import re
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

MINUS = "−"
SPACES = "   "
_PT = re.compile(rf"(?<![\w.,/])([+{MINUS}-]?)(\d{{1,3}}(?:[{SPACES}]\d{{3}})+|\d+)(?:,(\d+))?(?![\w/])")
_EN = re.compile(rf"(?<![\w.,/])([+{MINUS}-]?)(?:€)?(\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.(\d+))?(?![\w/])")
_LINK = re.compile(r"\]\(<[^>]*>\)|<https?://[^>]*>|\]\([^)]*\)|https?://\S+|`[^`]*`")
SCALES = (1.0, 1e-3, 100.0)


@dataclass(frozen=True)
class Printed:
    """A number as printed: its value, how precisely it was printed, and where."""

    value: float
    decimals: int
    step: float  # the rounding it shows: 0.01 for two decimals, 100 for 25 800
    raw: str
    line: int
    context: str
    signed: bool = False  # printed with + or −: the sign must match too

    def explained_by(self, v: float) -> bool:
        for s in SCALES:
            x = v * s
            a, b = (x, self.value) if self.signed else (abs(x), abs(self.value))
            if abs(a - b) <= self.step / 2 + 1e-9 * max(1.0, abs(x)):
                return True
        return False


def _step(digits: str, decimals: str | None) -> tuple[int, float]:
    if decimals:
        return len(decimals), 10.0 ** -len(decimals)
    zeros = len(digits) - len(digits.rstrip("0"))
    return 0, 10.0 ** min(zeros, len(digits) - 1) if len(digits) > zeros else 1.0  # +700: to the hundred; 530 000: ten thousand


def numbers(text: str, lang: str) -> list[Printed]:
    """Every number printed in ``text`` (markdown), outside links and code, in the conventions of ``lang``."""
    rx = _PT if lang == "pt" else _EN
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        clean = _LINK.sub(lambda m: " " * len(m.group(0)), line)
        for m in rx.finditer(clean):
            sign, intpart, dec = m.groups()
            digits = re.sub(rf"[{SPACES},]", "", intpart)
            d, step = _step(digits, dec)
            v = float(digits + ("." + dec if dec else ""))
            if sign in (MINUS, "-"):
                v = -v
            ctx = line[max(0, m.start() - 60) : m.end() + 40].strip()
            out.append(Printed(v, d, step, m.group(0).strip(), i, ctx, bool(sign)))
    return out


def _flatten(x: Any) -> list[float]:
    if isinstance(x, bool):
        return []
    if isinstance(x, (int, float)):
        return [float(x)]
    if isinstance(x, dict):
        return [v for y in x.values() for v in _flatten(y)]
    if isinstance(x, list):
        return [v for y in x for v in _flatten(y)]
    return []


#: The result tables a decision document quotes; the rest (positions, profiles, every hour of the timetable) hold so
#: many numbers that any printed number would find one close enough, and the check would prove nothing.
TABLES = ("appraisal_*.csv", "passing_practice.csv", "without_parking.csv", "width_budget.csv", "standards_comparison.csv",
          "delay_summary.csv", "delay_by_part.csv", "delay_copresence.csv", "delay_by_hour.csv", "occurrences_by_street.csv")  # fmt: skip
SKIP = ("appraisal_passages.csv", "appraisal_route_passages.csv")


def catalogue(results: Path, configs: list[Path], tables: tuple[str, ...] = TABLES) -> list[float]:
    """Every number the case's quoted result tables (``tables``, glob patterns) and configuration files hold."""
    vals: list[float] = []
    files = sorted({f for pat in tables for f in (results / "tables").glob(pat) if f.name not in SKIP})
    for f in files:
        df = pd.read_csv(f)
        num = df.select_dtypes("number").to_numpy().ravel()
        vals += [float(v) for v in num if not math.isnan(v)]
    for f in configs:
        if f.suffix == ".toml" and f.exists():
            vals += _flatten(tomllib.loads(f.read_text(encoding="utf-8")))
    return sorted(set(vals))


_REF = re.compile(r"\{([\w.]+\.csv):(\w+)\[([^\]]*)\]\}")


def resolve(expr: str, results: Path) -> float:
    """The value of ``expr``: arithmetic on references ``{table.csv:column[key=value,...]}`` to one cell each."""
    cache: dict[str, pd.DataFrame] = {}

    def cell(m: re.Match[str]) -> str:
        table, column, where = m.groups()
        df = cache.setdefault(table, pd.read_csv(results / "tables" / table))
        rows = df
        for cond in filter(None, (c.strip() for c in where.split(","))):
            k, v = (s.strip() for s in cond.split("=", 1))
            col = rows[k]
            rows = rows[col.astype(str) == v]
        if len(rows) != 1:
            raise ValueError(f"{m.group(0)} selects {len(rows)} rows, not one")
        if column not in rows:
            raise ValueError(f"{m.group(0)}: {table} has no column {column!r}")
        v = float(rows[column].iloc[0])
        if not math.isfinite(v):
            raise ValueError(f"{m.group(0)} is empty or not finite ({v})")
        return repr(v)

    arithmetic = _REF.sub(cell, expr)
    if not re.fullmatch(r"[\d.eE+\-*/() ]+", arithmetic):
        raise ValueError(f"{expr!r}: only references and arithmetic are allowed")
    return float(eval(arithmetic, {"__builtins__": {}}, {}))  # digits and operators only, checked above


@dataclass
class Claim:
    """A statement pinned to model outputs: a pattern per language whose groups capture printed numbers, and one
    expression per group (``value``: one, or a list in group order)."""

    id: str
    value: str | list[str]
    patterns: dict[str, str]
    note: str = ""

    @property
    def values(self) -> list[str]:
        return [self.value] if isinstance(self.value, str) else list(self.value)


@dataclass
class Report:
    claims: list[tuple[Claim, str, float | None, Printed | None]] = field(default_factory=list)  # (claim, status, expected, found)
    orphans: list[Printed] = field(default_factory=list)
    why: dict[str, str] = field(default_factory=dict)  # claim id → why it could not be checked (unresolved, bad_pattern)

    @property
    def failed(self) -> list[tuple[Claim, str, float | None, Printed | None]]:
        return [c for c in self.claims if c[1] != "ok"]


def load_spec(path: Path) -> tuple[list[Claim], list[float], list[str]]:
    spec = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    claims = [Claim(c["id"], c["value"], {k: c[k] for k in ("pt", "en") if k in c}, c.get("note", "")) for c in spec.get("claims", [])]
    return claims, [float(x) for x in spec.get("ignore_values", [])], list(spec.get("ignore_patterns", []))


def spec_tables(path: Path) -> tuple[str, ...]:
    spec = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return tuple(spec.get("tables", TABLES))


def check(text: str, lang: str, results: Path, configs: list[Path], spec: Path) -> Report:
    """Check a document's claims and numbers (see the module's description)."""
    claims, ignore_values, ignore_patterns = load_spec(spec)
    rep = Report()
    for c in claims:
        pat = c.patterns.get(lang)
        if not pat:
            continue
        try:
            expected = [resolve(v, results) for v in c.values]
        except (ValueError, KeyError, FileNotFoundError, SyntaxError, ZeroDivisionError) as e:  # the drift to report
            rep.claims.append((c, "unresolved", None, None))
            rep.why[c.id] = str(e)
            continue
        hits = list(re.finditer(pat, text, re.MULTILINE))
        if not hits:
            rep.claims.append((c, "missing", expected[0], None))
            continue
        for m in hits:
            line = text.count("\n", 0, m.start()) + 1
            groups = (
                [g for g in m.groups() if g is not None] if len(expected) == 1 else list(m.groups())
            )  # alternatives: the one that matched
            if len(groups) < len(expected):  # a value with no group to compare it with would be skipped unseen
                rep.claims.append((c, "bad_pattern", expected[0], None))
                rep.why[c.id] = f"the pattern captures {len(groups)} number(s) for {len(expected)} value(s)"
                continue
            for want, grp in zip(expected, groups, strict=False):
                found = numbers(grp or "", lang)
                if not found:
                    rep.claims.append((c, "unparsed", want, None))
                    continue
                p = found[0]
                p = Printed(p.value, p.decimals, p.step, p.raw, line, m.group(0)[:120], p.signed)
                rep.claims.append((c, "ok" if p.explained_by(want) else "wrong", want, p))
    known = catalogue(results, configs, spec_tables(spec))
    ignore = [re.compile(x) for x in ignore_patterns]
    pinned = {(p.line, abs(p.value)) for _, status, _, p in rep.claims if status == "ok" and p is not None}
    for p in numbers(text, lang):
        if (p.line, abs(p.value)) in pinned:
            continue
        if any(abs(p.value - v) < 1e-9 for v in ignore_values) or any(r.search(p.context) for r in ignore):
            continue
        unsigned = Printed(p.value, p.decimals, p.step, p.raw, p.line, p.context)  # a cost may be printed as a negative
        if not any(unsigned.explained_by(v) for v in known):
            rep.orphans.append(p)
    return rep


def compare_languages(a: str, lang_a: str, b: str, lang_b: str, ignore_values: list[float]) -> tuple[list[Printed], list[Printed]]:
    """The numbers printed in ``a`` that ``b`` never prints (at the same value), and the reverse."""

    def key(p: Printed) -> float:
        return round(abs(p.value), 6)

    na, nb = numbers(a, lang_a), numbers(b, lang_b)
    ca, cb = Counter(key(p) for p in na), Counter(key(p) for p in nb)
    skip = {round(abs(v), 6) for v in ignore_values}
    only_a = [p for p in na if key(p) not in cb and key(p) not in skip]
    only_b = [p for p in nb if key(p) not in ca and key(p) not in skip]
    return only_a, only_b


def render(rep: Report, lang: str, only_here: list[Printed] | None = None) -> str:
    lines = [f"# check-doc ({lang})", "", f"claims: {sum(1 for c in rep.claims if c[1] == 'ok')} ok, {len(rep.failed)} not"]
    for c, status, expected, p in rep.failed:
        got = f"prints {p.raw!r} (line {p.line})" if p else rep.why.get(c.id, "not found")
        model = f"model {expected:.4g}" if expected is not None else "model value unknown"
        lines.append(f"- {status.upper()} {c.id}: {model}; {got}" + (f" — {c.note}" if c.note else ""))
    lines += ["", f"numbers no result or input explains: {len(rep.orphans)}"]
    lines += [f"- line {p.line}: {p.raw!r} … {p.context}" for p in rep.orphans]
    if only_here is not None:
        lines += ["", f"numbers only this language prints: {len(only_here)}"]
        lines += [f"- line {p.line}: {p.raw!r} … {p.context}" for p in only_here]
    return "\n".join(lines) + "\n"
