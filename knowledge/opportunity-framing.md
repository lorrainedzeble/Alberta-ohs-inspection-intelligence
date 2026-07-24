# Opportunity framing: candidates considered, and why one won

Referenced from CLAUDE.md. Written down so the "converge on one" judgment behind this workspace is checkable by a stranger, not just implied.

## Criteria, locked before comparing candidates
1. Serves one real, recurring decision, not a one-off report someone reads once.
2. Has a clear user and purpose, not a tour of the dataset.
3. Has a genuine evaluation hook: a claim that can be independently recomputed and checked, not just asserted.
4. Realistic for a maintainable solo build.
5. The data actually has to be able to support the claim, checked directly against the live file, not assumed from the field names.

## Candidates

**1. Inspection prioritization workflow for an OHS compliance planning analyst (chosen).** Directly operationalizes Alberta OHS's own published sector-selection criteria (injury rate, incident frequency, compliance history, emerging trend, see `domain-notes.md`) at the employer level. Wins on criterion 3 especially: the ranking skill's back test against 2023-2024 enforcement outcomes and the enforcement-effectiveness skill's before/after comparison are both real, recomputable evaluations, not narrative claims. Wins on criterion 1 because it's a recurring quarterly cycle (trend scan, then targeting, then briefing), not a single question answered once.

**2. Employer/EHS manager self-benchmarking briefing.** A company's own safety manager checking their standing against industry peers before a COR audit or WCB review. Real and useful, but thinner on criterion 1: mostly a one-shot lookup before/after date`s a single external event, not a recurring decision loop. Not rejected outright, folded in instead as the `employer-briefing` skill, used by Dana to prep before a specific visit rather than standing alone as the whole workspace.

**3. Standalone industry-trend briefing for a WCB/policy analyst.** Tracking injury/fatality trends by industry for resourcing decisions. Fails criterion 1 alone: describing a trend is not itself an allocation decision, it's an input to one. Folded in as `industry-trend-briefing`, the first stage of the chosen workflow, not a standalone framing.

**4. COR program effectiveness, a policy question ("does having a COR actually track with lower injury rates?").** Appealing because it's a sharp, single, testable question. Rejected on criterion 1 (thin, mostly one-shot policy analysis, not a recurring operational decision) before it was rejected again, harder, on criterion 5: `COR_YEAR` turned out to be completely empty in this file (0 of 841,761 rows populated, see `data-cautions.md`), so the question could not have been answered honestly from this dataset regardless. The second rejection confirmed the first was the right call.

**5. Enforcement consistency audit** (do penalties/convictions scale with injury severity consistently across industries?). A real internal-reviewer question, but no accessible named persona or decision cadence was identified for it within this build's scope, and it risks becoming an open-ended statistical exploration rather than a bounded decision-support tool. Not pursued past the discussion stage.

**6. Union/worker-advocacy flagging** (employers with high injury/fatality counts but light enforcement follow-through, for member advocacy). Legitimate, but a different, more adversarial stakeholder position than the one this workspace was already converging on, and ethically sharper-edged (naming employers to an advocacy audience). Not pursued.

**7. Public "worst offenders" leaderboard.** Rejected explicitly and stated in CLAUDE.md's refusal 2: technically easy, but a one-off public report, not a recurring internal decision, and starts to look like a dataset tour with a punitive angle attached.

## What this means for the rest of the spec
Candidates 2 and 3 did not disappear, they became skills inside candidate 1 rather than competing framings. Candidate 4's rejection is the direct ancestor of `enforcement-gap-watchlist` (it replaced the COR-based proactive-watchlist idea once COR was confirmed unusable). Candidates 5-7 are genuinely not part of this workspace and are named here so that omission reads as a decision, not an oversight.
