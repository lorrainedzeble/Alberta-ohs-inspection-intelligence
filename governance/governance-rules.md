# Governance rules

Referenced from CLAUDE.md. Detail lives here so the top level spec stays short.

## Automatic fails (any skill output must never)
- State or imply that a named employer "is non-compliant," "is guilty," "should be inspected," or "is unsafe" as settled fact. Enforcement records are history, not a verdict on the present.
- Show a number that has not been checked by the `validate metric` subagent.
- Report an injury or disabling injury rate computed from fewer than 40 person years without flagging it as statistically unstable.
- Describe COR using an expiry or renewal date. COR_YEAR has no date; see CLAUDE.md refusal 1.
- Name an employer without also citing its `EMP_KEY`, the year(s) involved, and the source sheet(s) the figures came from.
- Present a composite risk score without showing its components. No hidden weights.

## Governed language
Use the left column, never the right column, in any skill output.

| Use this | Not this |
|---|---|
| has an enforcement action on record | is non-compliant |
| flagged for review | should be inspected |
| named in a conviction, order, or penalty record | guilty, violator |
| shows a rising injury rate trend | predicted to have a fatality |
| COR not held in the most recent year | COR expiring |
| lapsed between year X and year Y | COR expired on [date] |
| risk signal | risk verdict / finding of fact |

## Gated exceptions, written in advance
These are decided now, before any run produces a surprising result, so a bad number cannot quietly become the new rule.

- Enforcement gap watchlist: if more than 15% of employers in a given scope qualify as flagged, treat that as a threshold calibration problem in the skill, not as a real finding about the industry. The skill must say so explicitly and stop, rather than returning an oversized list as if it were meaningful.
- Inspection target ranking: if the back test described in CLAUDE.md's success criteria does not show the top ranked shortlist beating a random sample of the same size on enforcement action rate, the ranking formula is rejected. It must be revised, or the skill must be shipped only as "sorted by raw indicators" language, never presented as a risk score, until it passes.

## Independent verification
`validate-metric` (`.claude/agents/validate-metric.md`) defines a role, not a registered subagent type this runtime will dispatch automatically — confirmed directly on 2026-07-14 by attempting to invoke it by name and being rejected. In practice it is run as a manual step: its role instructions are handed to a general-purpose agent alongside a skill's draft output. When actually run this way, it is deliberately kept separate from the skill that produced the number:
- It runs with fresh context. It never sees the producing skill's reasoning or intermediate work, only the draft output and the raw sheets.
- It recomputes every number from the source sheets itself. It never imports or trusts a value the producing skill already calculated.
- It reports PASS or FAIL per number, not a summary judgment. A single FAIL blocks that whole output from being shown to the analyst as final, and is escalated rather than silently patched.
- Whoever operates this workspace must run this step explicitly on every skill invocation and log the verdict (PASS or FAIL, and any correction made) to `evaluation/use-log.md` the same day; nothing in the tooling does either step automatically.

## Human review triage
When a critic (the `validate metric` subagent, or a human review pass) raises a finding, it gets one of three verdicts, recorded with a reason:
- Accept: the finding is real, the skill or spec is changed, and the change is dated.
- Reject: the finding does not hold up; the reason is written down so the same claim is not re litigated later without new evidence. A critic's finding is a claim, not a fact, until it survives this check.
- Defer: the finding is plausible but out of scope for now; noted for a later pass, not silently dropped.
