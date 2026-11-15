# Writing to a public body with the results

Lessons from using the results of mobilidados in real requests. They apply to any letter a citizen sends to a
municipality, a transport operator or a parliament committee.

## Start from a draft

```bash
mobilidados draft cases/<case> --topic buses        # or --topic sidewalks
mobilidados draft cases/<case> --topic sidewalks --ask documents
```

`draft` writes `results/letter-<topic>.md` from the case's findings ledger, following everything below: one topic;
the facts first, grouped by what they rest on (measured in official data, written in an official document, estimated
from them), each with the id of its finding so the recipient can trace it; the assumptions the estimates use,
declared as such; one request; the evidence attached, with the points or stretches where a technician can measure.
Every sentence about the street is the ledger's own, and the draft is linted before it is written. Fill in what is
in [square brackets], cut what you do not need, and check what you changed with `mobilidados check-claims`.

Nothing in it asks you to observe or count anything yourself. Where the data stop, the request asks the body that
holds the rest (the services, who can measure on site; the operator, who keeps its own records) to check or to
provide it.

## State facts and ask

* **Open with what can be verified from the recipient's own data.** "Your cartography shows a free width of
  *x*–*y* m between the parking strips" invites a check; "the street is too narrow" invites an
  opinion.
* **Ask for something the recipient can do and answer**: an inspection, a review of the street's design, a
  copy of a document, a reply within the legal deadline. One request per topic, one topic per letter.
* **Be direct.** Describe the problem as what it is and ask for it to be corrected, with a deadline where the
  law gives one.

## Leave out what weakens the request

* **No pre-emptive concessions.** Do not anticipate and grant the other side's likely argument ("I know the
  width may be intentional…"). Keep likely objections and your answers to them in your own notes, for the reply.
* **No disclaimers about what you are not asking.** They put the idea in the reader's head.
* **No claims about documents you have not read.** If you have asked for a project file, ask for it; do not
  describe what it does or does not contain.
* **No generalising.** Write what was observed, where and when, or what the timetable implies, and say which.
* **No "rule", "minimum" or "law" for a recommendation.** A design manual gives reference profiles; quote the
  page and its scope. Apply a table only to the cases it covers.
* **No quotation marks around a paraphrase or a translation.**
* **No numbers that rest on an assumption without saying so.** If the bus width with mirrors is assumed, keep
  it out of the letter or label it.

`mobilidados lint` catches the mechanical cases; `mobilidados check-claims` checks every claim against the ledger.

## Practicalities

* **Use the official channels** and keep the reference number of every submission; record dates and legal
  deadlines (in Portugal, for example, the Administrative Procedure Code and the access-to-documents law set
  reply deadlines).
* **Ask for the documents the data do not cover.** In Portugal, Law 26/2016 of 22 August gives everyone access to
  administrative documents held by the municipality, its companies (Carris, EMEL) and other public bodies (article
  4): ask in writing, with your name and contact (article 12). The body has 10 days to reply, give access, refuse
  with reasons, or say who holds the document (article 15); without a reply, or after a refusal, you can complain to
  the CADA within 20 days (article 16). `mobilidados draft --ask documents` writes such a request; name the documents
  as precisely as you can (the street's project, a study, the operator's recorded running times, the grounds for an
  exception to the accessibility law under its article 10).
* **Attach the evidence** in a form the recipient can audit: the findings ledger, the figures and the
  coordinates of the check points (`check_points.csv`) so a technician can measure on site.
* **Do not send more than needed.** A follow-up is worth sending when there is a reply to answer or a deadline
  has passed, not to add volume.
* **Keep personal data out of shared files.** Fill in names and addresses only in the final document you send.
