---
name: enforcement-effectiveness
description: Compares an employer's or an industry's injury and disabling-injury rate before vs. after the first dated enforcement action, with actual numbers shown, not just a verdict. Use when the analyst asks whether enforcement is actually working, for one employer or rolled up across an industry.
---

## When to use this
The analyst's "did our last enforcement action actually work" question, the fourth moment in CLAUDE.md's quarterly cycle, and the workspace's main evaluation hook.

## How to run it
`python script.py employer "EMP_KEY"` for one employer, or `python script.py industry "INDUSTRY NAME"` for an industry rollup, from this folder.

## How to present it
- State the first enforcement action's date and source sheet plainly (it is the minimum of Order.ISSUE_DATE, Ticket.OFFENCE_DATE, Penalty.SERVED_DATE, Conviction.DATE_OF_CONVICTION, never Conviction.INCIDENT_DATE).
- For a single employer: if either `before` or `after` shows `"insufficient data, before/after not computable"`, say exactly that, don't compute a number from an empty or single point window.
- For an industry rollup: this is a pooled comparison across every employer's own before/after window relative to their own first action, not one shared calendar window. Say so, since it's not the same as "the industry's rate in year X vs year Y."
- Always show whether each rate is `rate_stable`; an unstable rate is still shown, but flagged, never hidden.
- This is a signal for the analyst to weigh, not proof that enforcement "worked" or "failed"; state the numbers, avoid a verdict stronger than the data supports, per CLAUDE.md's Governance and governed language table in `governance/governance-rules.md`.

## Conventions this skill must follow
- Never use `Conviction.INCIDENT_DATE` as an action date.
- Never compute a before/after number on a zero year window; report insufficient data instead.
- Every output from this skill must be reviewed by `validate-metric` before being shown to the analyst as final.
