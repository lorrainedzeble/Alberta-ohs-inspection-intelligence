# Failure-case regression checklist

Each case below was actually run against the live workbook on 2026-07-14, not just listed as a hypothetical. The pass/fail bar is: does the output explain the condition clearly to an analyst, rather than crashing with a raw traceback or silently guessing an answer.

## 1. Misspelled industry name

Command: `python .claude/skills/industry-trend-briefing/script.py "ROOFNIG"`

Result:
```
{
  "error": "No employers found with WCB_INDUSTRY_NAME == \"ROOFNIG\". Industry names must match exactly. Closest real industry names on file: ['ROOFING']."
}
```

**Pass.** Clean, analyst-facing error naming the closest real match as a hint, without silently substituting it (per `industry-trend-briefing/SKILL.md`'s convention: "never invent an industry name close to what the analyst asked for").

## 2. Unknown EMP_KEY

Command: `python .claude/skills/employer-briefing/script.py "00000000-0000-0000-0000-000000000000"`

Result:
```
{
  "error": "No EMP_KEY and no employer named exactly \"00000000-0000-0000-0000-000000000000\" found in Injury."
}
```

**Pass.** No traceback, no fabricated dossier.

## 3. Employer name mapped to multiple EMP_KEYs

Found live: 12,235 `EMPLOYER_NAME` values in the Injury sheet map to more than one `EMP_KEY` (the opposite direction of the already-known "one EMP_KEY, two names" case). Tested with `"0832894 B.C. LTD."`, which maps to 2 distinct EMP_KEYs.

Command: `python .claude/skills/employer-briefing/script.py "0832894 B.C. LTD."`

Result:
```
{
  "error": "\"0832894 B.C. LTD.\" matches 2 different EMP_KEYs (employer name is not unique, see knowledge/data-cautions.md). Candidates: ['0F8EC0DB-210B-AFB9-7FA7-98D2C9BA2CDA', '991BD9B1-F51B-9A2B-5729-518A5CA11C0C']. Ask the analyst which one.".
}
```

**Pass.** Returns the candidate list and asks rather than silently picking one, exactly per `employer-briefing/SKILL.md`'s convention.

## 4. Rate under 40 person-years

Captured live as part of case 7 below: the same employer's "before" enforcement-effectiveness window (2022-2023) had `person_years_sum: 15.2`, well under the 40 person-year floor, and correctly returned `rate_stable: false` while still reporting the computed rate rather than hiding it.

**Pass.** Rate shown, flagged unstable, not suppressed and not presented as solid.

## 5. Industry with no recent data

3 of 302 industries only have data through 2021 (found live via direct pandas query: `GOVERNMENT OF ALBERTA`, `HEALTH CARE SERVICES - ALBERTA HEALTH SERVICES`, `HEALTH CARE SERVICES - COVENANT HEALTH`).

Command: `python .claude/skills/industry-trend-briefing/script.py "GOVERNMENT OF ALBERTA"`

Result: `latest_year_is_current: False`, `by_year` contains only 2020 and 2021 (2 employer accounts, ~29,700-29,800 person-years each year, matching the figure already cited in CLAUDE.md), `ltc_di_trend_flag: False`, `fatality_flag: False`.

**Pass.** The staleness flag is set correctly and independently of the trend/fatality flags; nothing presents 2021 as if it were as current as a 2024 industry.

## 6. Employer with no enforcement history at all

Found live: 225,735 employers with zero rows in `unified_enforcement_actions()` across Order/Ticket/Penalty/Conviction combined (consistent with the ~5.6% enforcement-action coverage rate already documented in `knowledge/data-profile.md`; the vast majority of employers have never had a dated enforcement action). Tested with EMP_KEY `000017F5-8D14-9BC1-F1F7-A4303067C525`.

Command: `python .claude/skills/enforcement-effectiveness/script.py employer "000017F5-8D14-9BC1-F1F7-A4303067C525"`

Result:
```
{
  "error": "No dated enforcement action (Order/Ticket/Penalty/Conviction) found for 000017F5-8D14-9BC1-F1F7-A4303067C525."
}
```

**Pass.** No fabricated before/after comparison, no crash; states plainly that there's nothing to compute a first-action date from.

## 7. Employer with insufficient before/after years for enforcement effectiveness

Found live: employers whose first enforcement action fell in 2024 (2,283 of them), leaving zero years of "after" data since the workbook stops at 2024.

Command: `python .claude/skills/enforcement-effectiveness/script.py employer "000BE459-7000-8521-3955-12E67C40056C"`

Result (abridged):
```
"before": { "years_used": [2022, 2023], "person_years_sum": 15.2, "count_sum": 0, "rate_per_100_person_years": 0.0, "rate_stable": false },
"after":  { "years_used": [], "status": "insufficient data, before/after not computable" }
```

**Pass.** Two failure conditions hit at once (insufficient "after" data, unstable "before" rate) and both are reported plainly rather than either crashing or fabricating a number for the missing side.

## 8. Ranking tied at cutoff

Real example from the 2026-07-14 orchestrator run (`run_quarterly_steps.py`): WELDING's back test has `employers_tied_at_top_n_boundary: 4`, `boundary_score: 5.0`, `top_n_boundary_tied: true`, but `tie_sensitive: false` (`worst_case_chance_probability` and `best_case_chance_probability` both 0.0274). Verdict: `validated`.

**Pass.** A tied boundary alone did not force a deferred verdict; the range test correctly determined the tie was immaterial to the conclusion, consistent with CLAUDE.md's governed gated-exception rule and the 2026-07-13 fix that introduced worst-case/best-case tie resolution.

## 9. Ranking failing statistical validation

Real example from the same 2026-07-14 orchestrator run: FIELD PRODUCTION OPERATORS' back test: `top_n_enforcement_rate_2023_2024: 0.0`, `full_population_enforcement_rate_2023_2024: 0.0002`, `chance_probability_of_this_hit_rate_at_random: 1.0`, `significant: false`, `gated_exception_triggered: true`. Also has a large tied boundary (39 employers), but `tie_sensitive: false` since both worst- and best-case chance probability are 1.0. Verdict: `rejected`.

**Pass.** `run_quarterly_steps.py` correctly skipped ranking and briefing for this industry once the backtest verdict came back rejected (`rank: null`, 0 briefs), rather than presenting a ranked list anyway.

## 10. Missing/renamed workbook columns

**Initial test, 2026-07-14 (afternoon): FAIL.** Built a minimal synthetic workbook mirroring the real sheet structure, with `WCB_INDUSTRY_NAME` renamed to `WCB_INDUSTRY_NAME_RENAMED`, and pointed `ohs_data.DATA_PATH` at it directly.

Result: `KeyError: ['WCB_INDUSTRY_NAME']`, a raw Python traceback, not a clean analyst-facing message.

At the time, this was logged as a real, disclosed gap and deliberately **not fixed**, since the robustness pass then in progress was explicitly scoped to proving robustness on what already existed, not adding new defensive code. That was the right call for that pass, but left a genuine schema-drift blind spot open: nothing in `ohs_data.py` validated the presence of expected columns before using them, contradicting CLAUDE.md's own Governance rule to escalate schema drift rather than silently work around it (or, as it stood, crash on it).

**Fix added, 2026-07-14 (evening), after an external review flagged this as worth closing before freezing the project.** `.claude/skills/_lib/ohs_data.py` gained a `REQUIRED_COLUMNS` manifest (one list per sheet, scoped to the columns the shared library and skills actually read off each raw sheet) and a `_fail_schema_drift()` helper. `_workbook()` now checks every sheet name in `SHEET_NAMES` exists in the opened file before caching it; `load_sheet(key)` checks every column in `REQUIRED_COLUMNS[key]` exists in the parsed frame before caching it. Either check failing prints a clean, structured JSON error to stdout and exits immediately (`sys.exit(1)`), before any calculation runs:
```json
{
  "error": "Source schema drift detected.",
  "action": "Stop processing and ask the analyst to verify the source workbook.",
  "sheet": "Injury (2020-2024)",
  "missing_columns": ["WCB_INDUSTRY_NAME", "..."]
}
```

**Rerun of the original failing condition, same synthetic workbook, after the fix:**
```json
{
  "error": "Source schema drift detected.",
  "action": "Stop processing and ask the analyst to verify the source workbook.",
  "sheet": "Injury (2020-2024)",
  "missing_columns": [
    "WCB_INDUSTRY_NAME",
    "PERSON_YEARS_COUNT",
    "LOST_TIME_CLAIM_COUNT",
    "ANNUAL_FATALITY_COUNT"
  ]
}
```
The rerun caught more than the single renamed column originally tested: the synthetic workbook's other columns (`PERSON_YEARS`, `ANNUAL_LOST_TIME_CLAIMS_COUNT`, `FATALITY_COUNT`) didn't match the real schema's exact names either, and the fix correctly flagged all of them in one pass rather than stopping at the first mismatch, columns that were genuinely present under their correct names (`EMP_KEY`, `EMPLOYER_NAME`, `YEAR_NO`, `CITY_NAME`, `ANNUAL_DISABLING_INJURIES_COUNT`) were correctly left out of `missing_columns`.

**Regression check against the real workbook, same day:** `python .claude/skills/industry-trend-briefing/script.py "ROOFING"` was rerun against the unmodified real source file to confirm the new validation produces zero false positives. It passed cleanly and reproduced the pinned gold example exactly (2020: `employer_count` 1137, `person_years_sum` 4907.7, `ltc_count` 133, `ltc_rate_per_100_person_years` 2.71, `di_count` 236, `di_rate_per_100_person_years` 4.809, `fatality_count` 1, `enforcement_action_count` 802).

**Second finding on the same case, from a follow-up external review, same day: the first fix's manifest was incomplete.** The initial `REQUIRED_COLUMNS` covered only the join/date/rate columns the shared library itself reads, not the raw fields `employer-briefing` reads directly off each enforcement sheet (`Order.LEGISLATION_CODE`/`CONTRAVENTION`/`ORDER_TYPE`, `Penalty.EVENT_YEAR`/`AMOUNT`, `Ticket.AMOUNT`, `Conviction.INCIDENT_DATE`/`INCIDENT_TYPE`/`OFFENCE_LOCATION`, `Acceptance`/`Approval.APPLICABLE_LEGISLATION`). Renaming any of those would still have produced a raw `KeyError`. The manifest was expanded to every raw column any of the five skills consumes, with each name first verified against the real workbook's actual header rows (read directly via openpyxl on 2026-07-14) so the stricter check cannot false-positive on the genuine source file. `Investigation` deliberately still lists only `EMP_KEY`: its `DESCRIPTION`/`URL` fields exist but are never consumed, per CLAUDE.md refusal 5.

**New test for the expanded manifest:** built a second synthetic workbook, correct everywhere (including a fully correct Injury sheet) except `Order` missing `LEGISLATION_CODE`, and ran `employer-briefing`'s actual `employer_briefing()` function against it. Result: the correct Injury sheet passed the check, then the Order read stopped cleanly before the briefing produced anything:
```json
{
  "error": "Source schema drift detected.",
  "action": "Stop processing and ask the analyst to verify the source workbook.",
  "sheet": "Order (2020-2024)",
  "missing_columns": ["LEGISLATION_CODE"]
}
```
The original Injury-columns test was rerun under the expanded manifest with the same clean result as before, and the Roofing gold example was rerun against the real workbook a second time after the expansion to confirm the stricter check still produces zero false positives on the genuine file.

**Final result: PASS.** Both the initial FAIL, the first (incomplete) fix, the review finding against that fix, and the completed fix are all preserved here rather than replaced, since a corrected regression checklist that only shows 11/11 passing would hide the fact that real gaps existed and were found by this checklist and its reviewers doing their jobs, not invented after the fact. See `evaluation/use-log.md`'s dated entries for the same chronology in the project's evaluation record.

## 11. Deliberately wrong metric fed to validate-metric

Already run and logged in full under the 2026-07-14 entry in `use-log.md` (the fourteenth-fix entry): a Roofing 2020 draft with `person_years_sum` corrupted from 4907.7 to 5200.0 was handed to a general-purpose agent running `validate-metric`'s role instructions. It returned **FAIL**, caught the corruption via genuine independent recomputation (not pattern-matching against the draft), flagged the internal inconsistency between the corrupted value and the draft's own correct rate fields, and separately surfaced an unplanted incomplete-citation issue.

**Pass.** The manual verification procedure works when actually run; the gap found alongside it (the FAIL not auto-logging) was closed separately as part of this same robustness pass (see CLAUDE.md's Governance section and `run_quarterly_steps.py`'s automated confirmation logging).

## Summary

**Final: 11 of 11 cases pass.** That was not true on first run: case 10 (missing/renamed workbook columns) genuinely failed, crashing with a raw `KeyError` traceback instead of a clean analyst-facing message. That failure was recorded honestly at the time, not hidden, and is still fully preserved in case 10's section above rather than quietly replaced with only the final passing result, a checklist that only ever showed 11/11 would erase the fact that this checklist did its job: it found a real gap, the gap was fixed (`ohs_data.py`'s new schema-drift validation), the original failing condition was rerun and confirmed fixed, and the real workbook was separately reverified to confirm the fix introduced no false positives.
