---
description: Run the analyst's full quarterly inspection prioritization cycle end to end, scan every industry, pause for the analyst to confirm or adjust the flagged list, rank targets in the confirmed set, brief the top employers, verify every number, and produce one consolidated memo.
---

This is the workflow version of CLAUDE.md's quarterly cycle. It strings together `industry-trend-briefing`, `inspection-target-ranking`, `employer-briefing`, and `validate-metric` so the analyst gets one memo, not four things to stitch together by hand. Follow these steps in order; do not skip the gate checks or the confirmation pause to save time.

## Scope
`$ARGUMENTS` is optional: a comma separated list of industry names (must match `WCB_INDUSTRY_NAME` exactly, check `knowledge/data-dictionary.md` if unsure) to pre-narrow the scan to. If `$ARGUMENTS` is empty, scan every industry, that is the default, and it is the point of running `industry-trend-briefing` as this workflow's own first step: the analyst should not need to already know which industries are trending badly before running the tool that tells them that, or skill 1 becomes redundant with the workflow.

## Step 1: Scan
Run `python .claude/skills/industry-trend-briefing/script.py --all`. This is one pass over the whole dataset, not 302 separate relaunches; expect roughly 8-9 minutes end to end, almost all of it the one-time workbook load (measured directly on 2026-07-14: 501 seconds total, see `GETTING_STARTED.md`'s benchmark table; an earlier ~143-second figure could not be reproduced and should not be planned around). If `$ARGUMENTS` was given, filter the result down to just those industries first. Otherwise use `flagged_industries_top` as the working set (the 15 largest flagged industries by employer count) and note `flagged_industries_remaining_count`.

## Step 2: Confirm with the analyst — HARD STOP, no exceptions

>  STOP. Do not call any Step 3 command. Do not run `inspection-target-ranking` in any mode.
>  Do not do this "in the same response" as Step 1 to save a round trip.
>  End your turn here and wait for a new, separate message from the analyst.

Present the flagged list (industry, `flagged_because`, `ltc_di_trend_direction`, latest LTC rate, `fatality_counts_checked`, employer count, latest enforcement action count). State plainly which flag fired for each industry, an LTC/DI trend, a recent fatality, or both, they are independent signals per `knowledge/data-cautions.md` and must not be collapsed into one line. For any industry with `latest_year_is_current: false`, say so explicitly rather than presenting it as equally current with the rest. The analyst may accept the list as is, drop any industry from it, or add one they have outside knowledge about (from `flagged_industries_all`, `all_industries`, or not in either). Only the confirmed set proceeds, and only after that confirmation actually arrives as its own message.

This is the same propose then confirm pattern used everywhere else in this workspace's governance (CLAUDE.md: "the analyst makes the final call, not the workspace"), applied to the workflow's first step instead of only its final output. `industry-trend-briefing` does real work generating the candidate list; it is just not allowed to become this workflow's unreviewed input.

**This pause now has one real, code-level teeth, not just prose.** Step 3 runs through `run_quarterly_steps.py` (see below), which takes a required `--confirmation` argument and refuses to run at all, exit code 1, no workbook access, if it is empty or omitted (verified directly on 2026-07-14). Whatever the analyst actually says to confirm or edit the list is what gets passed as that argument, and the script logs it to `evaluation/use-log.md` itself before doing anything else, so the confirmation is an observable, timestamped fact, not something that can be silently skipped inside a single response.

**Known limitation, narrowed but not eliminated:** the code-level check confirms *that* a confirmation string was supplied, not that it is a genuine, considered analyst decision; an operator could still type a placeholder string and pass the check. A live adversarial test of the old, prose-only version of this seam (2026-07-11) confirmed it could be walked through with zero human input; the 2026-07-14 hardening closes the "walked through with literally nothing" version of that gap but does not, and cannot from inside this workspace alone, verify the confirmation's sincerity. Anyone reviewing this workspace's governance should test this seam directly rather than trust the prose either way.

## Step 3: Rank and brief (one process, not one per industry)
Run `python .claude/skills/_lib/run_quarterly_steps.py --industries "IND1,IND2,..." --confirmation "<the analyst's actual confirmation or stated edits>" --top-n 10`, where `--industries` is the confirmed set from Step 2 (in the analyst's own words if she edited the list, otherwise the Step 1 list verbatim) and `--confirmation` is not a fixed keyword, it is whatever the analyst actually said. This single script performs the old Steps 3 and 4 (per-industry back test + rank, then briefing the top 3 unambiguous employers per validated/deferred industry) inside one Python process with one workbook load, not a fresh reload per industry and per employer; each fresh reload was independently measured at 8-11 minutes (see `evaluation/use-log.md`, 2026-07-14 entry), so running Steps 3-4 the old way for a real 15-industry cycle could mean dozens of redundant reloads. Progress prints to stderr as it works through each industry and employer; do not assume the process has hung during a long gap with no new stdout, check the progress stream.

For each industry in the JSON result, check `backtest.verdict`:
- `"rejected"`: `rank` will be `null` in the output (the script already skipped it). Note the gate was triggered and why, and move on; do not silently fall back to presenting a ranked list anyway.
- `"validated"` or `"deferred_boundary_tie"`: `rank` and up to 3 `briefs` are present.

**For a `"deferred_boundary_tie"` industry, never present its shortlist the same way as a validated one.** Check `top_n_boundary_tied` on the `rank` output: the employers with `at_top_n_boundary_tie: false` are unambiguously top-ranked (no one outside the shortlist shares their exact score) and remain real signal regardless of the industry's overall verdict; state them plainly. The employers with `at_top_n_boundary_tie: true` occupy the remaining slot(s) only because of an arbitrary, deterministic tie-break among `employers_tied_at_top_n_boundary` employers who all share the exact same score; present this group separately, named as a tied group, not as a definite 3rd/4th/etc. place, and say plainly that any of the tied employers could equally occupy that slot.

## Step 4: (folded into Step 3 above)
Briefing the top employers is now part of the single Step 3 script call, not a separate per-employer command. This step number is kept in the list so cross-references elsewhere in this workspace (CLAUDE.md, `evaluation/use-log.md` entries written before 2026-07-14) still make sense; nothing new happens here.

## Step 5: Verify
Before assembling the memo, every number produced in Steps 1 and 3 must be checked using the `validate-metric` role. **This is a manual step in this runtime, not an automatic one** (confirmed directly 2026-07-14: this workspace's `validate-metric` agent type is not registered here and invoking it by name is rejected; see CLAUDE.md's Governance section and `evaluation/deployment-assessment.md`). Perform it by handing `.claude/agents/validate-metric.md`'s exact role instructions to a general-purpose agent alongside the draft numbers and citations only, never the scripts or intermediate reasoning that produced them. If it returns any FAIL, fix the underlying issue and rerun the affected step; do not present a number that failed verification with a caveat instead of fixing it. **Log the verdict before moving to Step 6**: append to `evaluation/use-log.md` whether it was PASS or FAIL, and if FAIL, what was found and what was corrected. This logging is a required step of Step 5, not an optional afterthought (see CLAUDE.md's Governance section) — a caught, fixed, but unlogged FAIL is exactly the kind of gap this workspace's own evaluation is supposed to catch, not commit.

## Step 6: Assemble one memo
Structure: which industries were flagged in Step 1 and what the analyst confirmed or changed in Step 2; for each confirmed industry, its shortlist grouped by city with score components shown; for each briefed employer, a short paragraph (not the full dossier) pulling out what's most relevant for a visit decision, with a note that the full dossier is available via `employer-briefing` directly. Close with any gated exceptions or insufficient data notes hit along the way, since those are informative, not failures to hide.

## Step 7: Log it
Append one entry to `evaluation/use-log.md`: date, how many industries were flagged, what the analyst confirmed or changed, which industries were actually ranked and briefed. This turns a workflow run into auditable evidence of use and evaluation, not just a one-off convenience.

Every output from this workflow is still a signal for the analyst to weigh, never a decision made on their behalf, per CLAUDE.md's Governance section.
