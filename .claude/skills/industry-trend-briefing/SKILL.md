---
name: industry-trend-briefing
description: Produces a 5 year lost-time claim rate, disabling injury rate, fatality, and enforcement volume trend briefing for one Alberta WCB industry, flagged if it is moving the wrong way. Use when the analyst asks how an industry is trending, or wants to decide which industries deserve proactive inspection focus this quarter.
---

## When to use this
The analyst's "where should we be looking" question, the first moment in the quarterly cycle described in CLAUDE.md. Input is one industry name matching a `WCB_INDUSTRY_NAME` value exactly (see `knowledge/data-dictionary.md`; if unsure of the exact spelling, look it up rather than guessing).

## How to run it
For one industry: `python script.py "INDUSTRY NAME"` from this folder. It prints a JSON object with one entry per year (2020 to 2024, whichever years that industry has data for), each containing employer count, summed person years, LTC and DI counts and rates (with a stability flag), fatality count, and enforcement action count, plus two independent top-level flags: `ltc_di_trend_flag` and `fatality_flag`.

For scanning every industry at once (used by `/quarterly-cycle`'s first step): `python script.py --all`. One workbook load, one vectorized pass, not 302 relaunches; expect roughly 8-9 minutes end to end, almost all of it the one-time workbook load, not the scan itself (measured directly on 2026-07-14: 501 seconds total, see `GETTING_STARTED.md`'s benchmark table; an earlier ~143-second figure could not be reproduced under any condition tested and should not be planned around). Returns a condensed per-industry summary for all of them, plus `flagged_industries_top` (the 15 largest by `latest_employer_count` among those carrying either flag, same disclosed "favors higher volume" logic as `inspection-target-ranking`) and `flagged_industries_all` (every flagged one, in case the analyst wants to look further than the top 15).

Rates are computed by summing raw counts and person years across every employer in the industry for that year, then computing one rate. Never average individual employer rates together, per `knowledge/data-cautions.md`.

**Two independent flags, never merged (see `knowledge/data-cautions.md` for why this split exists):**
- `ltc_di_trend_flag`: true only if direction is "up" AND the absolute change is at least `ltc_materiality_threshold` (0.15 percentage points) between two *pooled* windows, raw counts and person years summed across the earliest 2 stable years (`ltc_di_early_window_years`, rate in `ltc_di_early_window_rate`) and separately across the latest 2 stable years (`ltc_di_late_window_years`, `ltc_di_late_window_rate`), never a single first-year-vs-last-year comparison. That single-point comparison was tried first and mislabeled two real industries (a volatile mid-series spike, and a decline anchored to an anomalous 2020 baseline); see `knowledge/data-cautions.md`. `ltc_di_trend_direction` shows the raw result (`up`, `down`, `flat_immaterial`, or `insufficient_stable_years_for_pooled_trend` when fewer than 4 stable years exist) for transparency. A technically-"up" direction on a tiny claim count still doesn't qualify without clearing the materiality threshold (Engineering, Quality Control Services - Construction).
- `fatality_flag`: true if at least one fatality was recorded in 2023 or 2024 (`fatality_counts_checked`), a historical fact, never a trend or a forecast. Computed independently of the LTC/DI flag; an industry with an improving rate can still carry `fatality_flag: true` (Mobile Equipment Operation is the clearest real example: rate improving, but 2024 had its highest fatality count of the 5 years).

`flagged_because` on each record (`--all` mode) lists which flag(s) actually fired, `["ltc_di_trend"]`, `["fatality"]`, both, or neither, so the analyst never has to guess why something is on the list.

**Always check `latest_year_is_current` before presenting a record.** 3 of 302 industries only have data through 2021 (see `knowledge/data-cautions.md`); their flags are computed correctly from what they have, but that is not the same recency as an industry current through 2024. State this plainly whenever it's false, don't present it silently alongside current industries. Also never treat `latest_employer_count` as a size signal on its own, check `person_years_sum` in `by_year` too; a handful of accounts can cover a very large workforce (Government of Alberta: 2 employer accounts, ~29,700 person-years).

## How to present it
Turn the JSON into a short prose briefing:
- State the industry, the years covered, and the employer count trend.
- Give the LTC rate and DI rate trend, explicitly noting `ltc_rate_stable`/`di_rate_stable` for each year; if a year's rate is not stable (person years under 40 for the whole industry, rare, but possible for a very small industry), say so rather than presenting it as a normal number.
- State the fatality count per year as a raw count, never a rate, and always state `fatality_flag` on its own, even when `ltc_di_trend_flag` is false or the LTC story looks fine.
- State enforcement action volume per year as a raw count.
- Report `ltc_di_trend_flag` and `fatality_flag` separately, each with its triggering value (the rate change, or the specific year's fatality count). Never collapse them into one summary verdict.

## Conventions this skill must follow
- Never state a rate without knowing whether it is marked stable.
- Never invent an industry name close to what the analyst asked for; if `script.py` returns an error because no exact match was found, say so and ask for the exact name rather than guessing a close one.
- This skill never names individual employers. If the analyst wants employer level detail inside an industry, that is `inspection-target-ranking` or `employer-briefing`, not this skill.
- Every output from this skill must be reviewed by `validate-metric` (fresh context, independent recomputation) before being shown to the analyst as final, per CLAUDE.md's Governance section.
