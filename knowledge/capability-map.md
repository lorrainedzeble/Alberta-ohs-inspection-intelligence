# Capability-to-form map

Referenced from CLAUDE.md's Skills section. The design rule is to name what the workspace must do as a plain verb first, then choose the simplest form before any tool gets named.

| Verb | Form chosen | Why this form, not a simpler one |
|---|---|---|
| Read and normalize the 8-sheet, 841,761-row workbook: convert four different date formats, attribute industry across sheets, build the unified enforcement-date table | Shared code library (`.claude/skills/_lib/ohs_data.py`), not native action | Too large and too easy to get subtly wrong for the model to read and reason over row by row each time (date formats alone differ per sheet, see `data-cautions.md`). Same reasoning that puts real computation in code rather than native action generally: a browser, or a model reading raw text, cannot do this reliably at this scale. |
| Compute a 5-year industry trend | Fixed pipeline (`industry-trend-briefing/script.py`), wrapped in a skill for discovery | Must be reproducible: same industry, same years, same rate, every run. A skill without a code check would only advise the right method, not enforce it. |
| Rank employers by a disclosed risk score | Fixed pipeline (`inspection-target-ranking/script.py`), wrapped in a skill | The scoring formula must be deterministic and inspectable on demand, not improvised differently per request. |
| Brief one employer | Fixed pipeline (`employer-briefing/script.py`), wrapped in a skill | One employer, one dossier shape, every time. |
| Compare an employer's or industry's rate before vs. after an enforcement action | Fixed pipeline (`enforcement-effectiveness/script.py`), wrapped in a skill | The windowing rule (up to 2 years each side, "insufficient data" handling at the edges) must apply identically every run, not be re-derived per request. |
| Flag employers with a rising trend and no recent enforcement | Fixed pipeline (`enforcement-gap-watchlist/script.py`), wrapped in a skill, with a hard-coded 15% calibration gate | The gate must trigger the same way every time; a soft, judgment-based version of the same rule would drift. |
| Independently re-check a draft output's numbers before it's shown | Subagent (`validate-metric`) | One distinct decision worth isolating in its own context: is this number actually right, checked with no visibility into how the producing skill got it. Exactly the isolation subagents are for. |
| String the quarterly scan, confirm, rank, and brief sequence into one memo | Workflow (`/quarterly-cycle`) | Genuinely multi-step, and needs an analyst confirmation pause partway through (see CLAUDE.md's workflow description) that a single skill call cannot provide. |
| Reach a live outside system while doing the analysis | Left empty on purpose, no connector built | The data is one local file; every skill reads it directly and writes its output as a return value. Nothing is called mid-analysis outside this workspace, the same reasoning that left Kinquiry's connector form empty for its own local-file survey analysis. |

No native-action row survives past the first one: everything downstream of loading the data needed either a fixed pipeline (for reproducibility) or a subagent/workflow (for isolation or sequencing), because the underlying computation is real code over hundreds of thousands of rows, not something safely left to per-request model reasoning.

## Skill posture: hard-gate vs. advisory vs. render

Which form a capability takes (the table above) is a different question from what happens when the output looks shaky. Three postures, defined once here so no two skills use the same word to mean different things:
- **Hard-gate**: a defined condition can block the output entirely or force it into a different, less confident category. The analyst never sees a false-precision answer dressed up as a clean one.
- **Advisory**: a flag or caveat is attached, but the underlying answer is still shown; the analyst decides what to do with the flag.
- **Render**: pure presentation of an already-computed number or dossier; no gate or flag logic of its own runs at this layer.

| Capability | Posture | Where the gate/flag actually lives |
|---|---|---|
| industry trend briefing | Advisory | `ltc_di_trend_flag`/`fatality_flag` surface a signal, never block a briefing from being shown |
| inspection target ranking | Hard-gate | The 0.05 significance test and the worst-case/best-case tie range force `validated`/`rejected`/`deferred_boundary_tie`, never a bare pass/fail on request |
| employer briefing | Render | Assembles a dossier from already-flagged data; `employer_name_ambiguous` is passed through, not re-decided here |
| enforcement effectiveness | Advisory | "Insufficient data" is a non-answer surfaced per employer, not a block on the whole comparison |
| enforcement gap watchlist | Hard-gate | The 15% calibration rule refuses to present an oversized list as a meaningful finding |
| `validate-metric` subagent | Hard-gate | A FAIL blocks that output from reaching the analyst at all and escalates, per CLAUDE.md's Governance |
| `/quarterly-cycle` Step 2 pause | **Code-enforced for presence, not for sincerity, since 2026-07-14** | Until 2026-07-14 this was advisory only in code, prose that read like a hard-gate but wasn't one, confirmed by direct adversarial test on 2026-07-11 (see CLAUDE.md's Governance section, "Known limitation"). `run_quarterly_steps.py` now requires a non-empty `--confirmation` value and refuses to run without it (exit code 1, no workbook access), logging it to `evaluation/use-log.md` automatically. This blocks the "zero human input" version of the gap but cannot verify the confirmation text is a genuine analyst decision rather than a placeholder typed only to pass the check; naming that limitation plainly here is the same discipline the rest of this table asks for. |

This table exists because a skill claiming to "flag" something and a skill claiming to "gate" something make very different promises to Dana, and CLAUDE.md's prose descriptions alone don't force a reader to notice which promise each skill is actually making.
