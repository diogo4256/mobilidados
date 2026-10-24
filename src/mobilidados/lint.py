"""Deterministic checks for letters to public bodies (no AI involved).

Rules that came out of real use: a citizen states facts and asks. Generalising one observation into "always",
conceding the other side's argument in advance, or putting quotation marks around a paraphrase all cost
credibility. These checks flag such passages; the human decides.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

RULES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "generalisation": {
        "pt": [
            (r"\bsempre\b", "«sempre»: descreva o que foi observado e quando"),
            (r"\bnunca\b", "«nunca»: é verificável?"),
            (r"\btodos os dias\b", "«todos os dias»: é observado ou estimado?"),
            (r"\bconstantemente\b", "«constantemente»: quantifique"),
            (r"\bimposs[íi]ve(?:l|is)\b", "«impossível»: o que a medição mostra é uma folga negativa, diga o número"),
        ],
        "en": [
            (r"\balways\b", "'always': describe what was observed, and when"),
            (r"\bnever\b", "'never': is it verifiable?"),
            (r"\bevery day\b", "'every day': observed or estimated?"),
            (r"\bimpossible\b", "'impossible': state the measured margin instead"),
        ],
    },
    "concession": {
        "pt": [
            (r"\bsei que\b", "concessão antecipada: deixe as objeções para a resposta"),
            (r"\bcompreendo que\b", "concessão antecipada"),
            (r"\bpode ser intencional\b", "concede o argumento da outra parte"),
            (r"\bn[ãa]o (?:pe[çc]o|estou a pedir)\b", "ressalva sobre o que não se pede: retire"),
            (r"\btalvez\b", "hesitação: afirme o facto ou retire"),
        ],
        "en": [
            (r"\bI understand that\b", "pre-emptive concession"),
            (r"\bmay be intentional\b", "concedes the other side's argument"),
            (r"\bI am not asking\b", "disclaimer about what is not requested: remove"),
            (r"\bperhaps\b", "hedge: state the fact or remove"),
        ],
    },
    "unverifiable": {
        "pt": [
            (r"\bn[ãa]o encontrei nada que\b", "implica uma revisão que pode não ter sido feita"),
            (r"\btoda a gente sabe\b", "afirmação sem fonte"),
        ],
        "en": [
            (r"\bI found nothing (?:that|to)\b", "implies a review that may not have happened"),
            (r"\beveryone knows\b", "claim without a source"),
        ],
    },
    "normative_word": {
        "pt": [
            (
                r"\b(?:normas?|regras?|obrigat[óo]ri[oa]s?)\b",
                "um manual de recomendações não é norma: «perfil de referência» ou «recomendação»",
            ),
            (r"\bm[íi]nimos? lega(?:l|is)\b", "confirme a fonte legal exata"),
        ],
        "en": [(r"\b(?:mandatory|regulations? requires?)\b", "a design manual is guidance: say 'reference profile' or 'recommendation'")],
    },
}
QUOTE = re.compile(r"[«\"“]([^»\"”]{12,})[»\"”]")


@dataclass
class Issue:
    line: int
    col: int
    rule: str
    message: str
    excerpt: str


def lint_text(text: str, lang: str = "pt") -> list[Issue]:
    issues = []
    for ln, line in enumerate(text.splitlines(), 1):
        for rule, by_lang in RULES.items():
            for rx, msg in by_lang.get(lang, []):
                for m in re.finditer(rx, line, flags=re.IGNORECASE):
                    issues.append(Issue(ln, m.start() + 1, rule, msg, line.strip()[:120]))
        for m in QUOTE.finditer(line):
            issues.append(
                Issue(
                    ln,
                    m.start() + 1,
                    "quotation",
                    "quoted text must be verbatim from a source: run check-claims or remove the quotes"
                    if lang != "pt"
                    else "texto entre aspas tem de ser citação literal: verifique com check-claims ou retire as aspas",
                    m.group(0)[:120],
                )
            )
    return issues
