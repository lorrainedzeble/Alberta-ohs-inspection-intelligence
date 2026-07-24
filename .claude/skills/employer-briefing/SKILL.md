---
name: employer-briefing
description: Produces a one page dossier for a single employer, injury trend vs. industry benchmark, full enforcement history, Acceptance/Approval history, and a legislation hot spot checklist for the employer's industry. Flags when the EMP_KEY is recorded under more than one distinct employer name. Use when the analyst is about to visit or review a specific employer, whether pulled from inspection-target-ranking or requested directly.
---

## When to use this
The analyst's "I'm about to visit this employer, brief me" question, the third moment in CLAUDE.md's quarterly cycle. Input is an `EMP_KEY` or an exact employer name.

## How to run it
`python script.py "EMP_KEY or exact employer name"` from this folder. If the identifier is a name that matches more than one `EMP_KEY` (names are not unique, see `knowledge/data-cautions.md`), the script returns the candidate list instead of guessing; present that list to the analyst and ask which one, never pick one silently.

## How to present it
- Injury trend: show each year's raw counts and, where `rate_stable` is true, the rate; where false, say the rate is not statistically stable rather than omitting it silently.
- Industry benchmark: compare the employer's own numbers to `industry_benchmark`'s pooled industry rate for the same years, so the analyst sees whether this employer runs above or below its industry, not just its own numbers in isolation.
- Enforcement history: list Order, Penalty, Ticket, and Conviction rows with their dates, plus the `ever_investigated` flag on its own, clearly marked as dateless (see `knowledge/data-cautions.md`), never folded into a "last N years" statement.
- Acceptance/Approval history: present as historical record only, "most recently recorded status: X, granted [date], originally scheduled to end [date]." Never say an instrument is currently active or about to lapse, per CLAUDE.md refusal 4 and `knowledge/data-cautions.md`.
- Legislation hot spot: the top legislation codes/contraventions for this employer's industry, framed as "what to check for on this visit," not as a claim about this specific employer unless one of those codes also appears in this employer's own `enforcement_history`.
- Cite `EMP_KEY` and the source sheet for every fact stated, per CLAUDE.md's Conventions.
- If `employer_name_ambiguous` is true, state plainly that this `EMP_KEY` is recorded under more than one name (list every name in `employer_name_all_known_names`) before naming the employer for a visit; this is a legal-name/trade-name pattern affecting 342 of 236,365 employers, see `knowledge/data-cautions.md`. Never present one of the names as the only one on file.

## Conventions this skill must follow
- Never surface the free text `NATURE_OF_VIOLATION` (Penalty), `TICKETABLE_PROVISION` full text (Ticket), or `DESCRIPTION`/`CONTRAVENTION` narrative (Conviction); this skill uses only the structured fields, per CLAUDE.md refusal 5.
- Every output from this skill must be reviewed by `validate-metric` before being shown to the analyst as final.
