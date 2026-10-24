# Evidence standard

A request to a public body is only as strong as its weakest sentence. One overstated number, one paraphrase
in quotation marks, or one design recommendation called "the law" gives the recipient a reason to dismiss the
whole request. mobilidados therefore attaches a grade to every statement it produces, and its tools check drafts
against those grades.

## Grades

| Grade | Use it for | Example |
| --- | --- | --- |
| **M** measured | values computed or counted directly from official data | the free width between the parking strips, read from the municipal cartography |
| **D** document | what an official document says, with page | the width a design manual's reference profile gives between parking strips, with its page |
| **I** inference | results of a model or a calculation on M/D/P inputs | how often the timetable implies that buses in opposite directions meet on the street |
| **P** assumption | values nobody publishes, which the analysis needs | a bus's width with mirrors, where no technical sheet states it |
| **NE** not found | what was looked for and not found, or not verified | "no field observation of two buses meeting on this street" |

**NE is not "does not exist".** "I did not find delay data per street" is a fact about the search; "there is
no delay data" is a claim about the world.

## Rules

1. **Separate the kinds of statement.** Measured facts, document text, estimates, the author's own observations
   and hypotheses are different things and are written differently.
2. **Cite primary sources with dates and versions.** A layer's metadata page is not the same as having
   extracted records from it; a summary of a law is not the law.
3. **Keep each value within its scope.** A value from a table for one-way streets says nothing about two-way
   streets; a manual of recommendations is not a regulation; a foreign guideline is not Portuguese law.
4. **Do not generalise an observation.** "When a bus passes and a car comes the other way, the car reverses"
   is an observation; "every time a bus passes" is a generalisation that one counter-example refutes.
5. **Quotation marks mean verbatim.** A translation or a paraphrase is not put in quotes.
6. **Do not imply a review that did not happen.** "I found nothing in the project that…" implies the project
   was read.
7. **Record assumptions where they are used**, with the reason (grade P), and test how much the result
   depends on them (e.g. `overhang_sensitivity.csv`).
8. **Distinguish an infraction from a design problem.** Parking inside a marked bay is not an infraction even
   if the remaining width is insufficient; that is a question for the street's design, not for enforcement.

## How the tools apply it

* The **findings ledger** (`results/findings.md`, `findings.json`) is generated from the result tables, so a
  statement cannot drift from its number. Each finding lists its sources (ids in `sources.lock.json`), method
  and caveats.
* **`mobilidados lint`** mechanically flags generalisations, quotation marks, implied reviews, pre-emptive
  concessions and normative words (the patterns are `RULES` in `src/mobilidados/lint.py`).
* **`mobilidados check-claims`** has an AI agent compare each claim in a draft with the ledger and sources, then
  verifies the agent's evidence mechanically (quotes, numbers, finding ids). See [ai-tools.md](ai-tools.md).
