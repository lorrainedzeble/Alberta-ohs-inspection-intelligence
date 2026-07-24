---
name: enforcement-gap-watchlist
description: Flags employers with a rising injury trend and no dated enforcement action (Order/Penalty/Ticket/Conviction) in 3 or more years, tracking "ever investigated" as a separate flag. Use for the analyst's proactive "who's flying under the radar" question, not tied to a specific industry focus already chosen.
---

## When to use this
The analyst's "who's climbing in risk but never shown up on our enforcement radar" question, the workspace's one proactive/watchlist skill. Can run unscoped or narrowed to an industry and/or city.

## How to run it
`python script.py --industry "INDUSTRY NAME" --city "CITY NAME"` from this folder; both flags are optional.

**Check `gated_exception_triggered` before presenting anything.** If true, per CLAUDE.md's gated exception, the flagged list is withheld by the script itself (returned as an empty list) and the correct response is to say the scope's flagged fraction exceeded 15%, that is a threshold calibration problem, not a finding, and to suggest narrowing the scope or revisiting the trend definition, never to present an oversized list as if it were meaningful.

## How to present it
- Rising trend is defined as 2 consecutive year over year increases in `ANNUAL_DISABLING_INJURIES_COUNT` across 3 consecutive years present in the data; state the `trend_reason` given for each employer, don't just assert "rising."
- "No enforcement in 3+ years" is measured against the same unified enforcement date table `enforcement-effectiveness` uses, taking the most recent action per employer; state `most_recent_enforcement_action`, `most_recent_enforcement_action_source_sheet` (Order/Ticket/Penalty/Conviction), and `years_since_last_action` together (or "no enforcement action on record at all" when null), per CLAUDE.md's citation convention. Never state the date alone without naming which sheet it came from.
- `ever_investigated` is shown as its own separate flag, never combined into the "years since last action" framing, since Investigation has no date column at all.
- Only about 5.6% of all employers in this dataset have ever had a dated enforcement action (see `knowledge/data-profile.md`); the "no enforcement" half of this rule is true for most employers almost by default. Say plainly that the rising trend condition is doing nearly all the real filtering, don't imply the enforcement absence half is a strong signal on its own.
- Every employer on this list is a signal for the analyst to weigh, never a claim that something is wrong, per CLAUDE.md's Governance.

## Conventions this skill must follow
- Never override or bypass the 15% gate to show a list anyway.
- Every output from this skill must be reviewed by `validate-metric` before being shown to the analyst as final.
