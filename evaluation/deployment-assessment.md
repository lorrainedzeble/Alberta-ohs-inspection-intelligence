# Deployment assessment

A literal spec-vs-build check, done last, because gaps between what a specification claims and what is actually deployed are recurring, avoidable review findings. Every claim below was checked directly against the current repository state on 2026-07-14, not assumed from earlier build notes.

## Every skill and workflow named in CLAUDE.md, confirmed to exist

| Named in CLAUDE.md | File(s) checked | Exists |
|---|---|---|
| industry trend briefing | `.claude/skills/industry-trend-briefing/script.py` + `SKILL.md` | Yes |
| inspection target ranking | `.claude/skills/inspection-target-ranking/script.py` + `SKILL.md` | Yes |
| employer briefing | `.claude/skills/employer-briefing/script.py` + `SKILL.md` | Yes |
| enforcement effectiveness | `.claude/skills/enforcement-effectiveness/script.py` + `SKILL.md` | Yes |
| enforcement gap watchlist | `.claude/skills/enforcement-gap-watchlist/script.py` + `SKILL.md` | Yes |
| Shared data library | `.claude/skills/_lib/ohs_data.py` | Yes |
| `validate-metric` subagent | `.claude/agents/validate-metric.md` | Yes, file exists — **see known limitation below** |
| `/quarterly-cycle` workflow | `.claude/commands/quarterly-cycle.md` | Yes |

No skill named in CLAUDE.md is missing from the repository. This is the narrow, mechanical half of "ship what the spec promises"; the honest half is the limitations below, which no file-existence check can catch.

## Known limitations, stated rather than buried

1. **`validate-metric` is a file, not a live agent invocation, confirmed directly on 2026-07-14.** `.claude/agents/validate-metric.md` exists and defines the subagent's role correctly, but attempting to invoke it by its registered name is rejected outright by this runtime, which lists only 6 real agent types, none of which is it. This is not a sometimes-works gap; it is the actual, confirmed mechanism in every runtime this workspace has been used in during this build window. In practice its role instructions are handed verbatim to a general-purpose agent instead, tested directly with a deliberately corrupted number (see `evaluation/use-log.md`, 2026-07-14 entry): the manual mechanism works and is genuinely rigorous, but nothing in this workspace runs it automatically, and nothing writes its verdict to the use-log automatically either, both are required manual steps (see CLAUDE.md's Governance section). A stranger deploying this workspace in a different runtime should not assume `validate-metric` runs itself; every skill invocation must include this step, and its verdict, explicitly.
2. **`/quarterly-cycle`'s Step 2 confirmation pause is now code-enforced for presence, not for sincerity.** Until 2026-07-14 this was advisory only: a live adversarial test on 2026-07-11 confirmed it could be walked through with zero human input and still produce a fully "validated" memo. `.claude/skills/_lib/run_quarterly_steps.py` now requires a non-empty `--confirmation` argument and refuses to run without it (exit code 1, no workbook access), logging whatever confirmation text is supplied to `evaluation/use-log.md` automatically, before any ranking work happens. This is a real, testable code path, not prose, but it can only confirm that some confirmation string was supplied, never that it reflects a genuine analyst decision rather than a placeholder typed to pass the check. Already stated in CLAUDE.md's Governance section and `knowledge/capability-map.md`'s posture table; repeated here because this document is supposed to be the final spec-versus-build check, and leaving an obsolete limitation here would undermine that purpose.
3. **No user research grounds the "Story #1, interrogated" caveat in CLAUDE.md's User story brief.** Whether Dana's informal, experience-based sense of "which industries are usually bad" already substitutes for Step 1's scan in practice was never tested with a real analyst; this workspace was built and evaluated by one person role-playing the persona and by an adversarial critic, not by the named user herself. Stated as a limitation, not resolved.
4. **The dashboard is a snapshot of one real quarterly cycle (2026-07-10, corrected through 2026-07-14), not a live view.** It reads from pre-computed, embedded JSON, not the live workbook; a future quarter's run requires regenerating the dashboard's data files, not just reopening `dashboard/index.html`. This is a deliberate, documented design choice (see `knowledge/dashboard-mockup-framing.md`), not an oversight, but worth stating plainly here too.
5. **City-based routing is not resolved, only caveated.** `CITY_NAME` is the employer's registered WCB mailing address, not a confirmed Alberta worksite; this is surfaced everywhere a shortlist is shown, but no skill in this workspace can currently confirm an employer's actual physical worksite location. An analyst using this workspace to route an actual visit must confirm the worksite separately every time.

## Deployment status: ready for the one use case it claims, not for anything broader

This workspace is ready to support Dana's three named decisions (`CLAUDE.md`'s User story brief) using the current 2020-2024 workbook snapshot, with the limitations above disclosed rather than hidden. It is explicitly **not** ready, and not intended, for: a different analyst or OHS branch (no persona research beyond one), a live/real-time data connection (no connector exists, see `knowledge/capability-map.md`), or any decision outside the five skills named in CLAUDE.md's Skills section (out of scope by design, see CLAUDE.md's Scope section). A future maintainer's first task, if this workspace were to be extended, should be closing limitation 3 (real user research with the actual persona) before adding any new capability.
