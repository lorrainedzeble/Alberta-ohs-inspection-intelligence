# Data profile

Real coverage numbers, computed directly against the live file with pandas on 2026.07.09, not estimated. Referenced from CLAUDE.md and `data-cautions.md`.

## Injury (841,761 rows)
- 236,365 unique employers (`EMP_KEY`).
- Roughly even split across years: 2020 to 2024 each have 166,789 to 170,113 rows.
- 302 unique `WCB_INDUSTRY_NAME` values.
- `COR_YEAR`: 0 of 841,761 rows populated. Completely empty in this file, not just dateless. No skill may make any COR claim, including "held in year X", since there is no COR data at all in this extract.
- `TRADE_NAME`: 0 of 841,761 rows populated. Completely empty; do not reference it anywhere.
- `PERSON_YEARS_COUNT` under 40: 780,930 of 841,761 rows (93%). The overwhelming majority of individual employer year rows are below the rate stability threshold. Design implication: any skill computing a rate must sum raw counts and person years across the relevant group first, then compute the rate once, never average many small, unstable per employer rates together.
- `LOST_TIME_CLAIM_RATE` populated on only 30,398 of 841,761 rows (3.6%). Expect most individual rows to have no rate at all, not just a suppressed one.
- `ANNUAL_FATALITY_COUNT` greater than 0 on 368 rows.

## Order (71,755 rows, 13,284 unique employers)
`STATUS` values: Compliance (70,662), Suspension (547), Rescission (341), Non-Compliance (140), Order Revoked (23), Open (17), Immediate Compliance historical (15), Extended (5), Order Varied (5).
`ORDER_TYPE` values: Order (65,887), Stop Work Order (4,822), Stop Use Order (1,030), Stop Work Order Multiple-Sites (16).

## Penalty (94 rows, 83 unique employers)
## Ticket (76 rows, 41 unique employers)
## Investigation (91 rows, 61 unique employers)
## Conviction (167 rows, 84 unique employers)
All four are small, sparse tables relative to the 236,365 employers in Injury.

## Acceptance (909 rows, 234 unique employers), Approval (253 rows, 83 unique employers)
See `data-dictionary.md` for the status value counts (Issued/Expired/Revoked/Denied/Suspended/Amended-Varied) and `data-cautions.md` for why their dates cannot be treated as a live status.

## Enforcement coverage, a base rate that matters for calibration
Across Order, Penalty, Ticket, and Conviction combined (the four dated enforcement sheets), only 13,328 unique employers out of 236,365 in Injury (5.6%) have ever had a dated enforcement action in 2020 to 2024. Of those, 10,630 also appear in Injury; the remaining roughly 2,700 enforcement records belong to employers not present in the Injury sheet at all (likely no longer active or not currently reporting), and should be flagged rather than silently dropped when they surface.

This matters for `enforcement-gap-watchlist`: "no Order/Penalty/Ticket/Conviction in 3+ years" is true for the vast majority of all employers almost by default, since so few employers are ever enforced against at all. The skill's real discriminating power comes from the rising injury trend condition, not the enforcement absence condition. Do not describe the enforcement absence half of the rule as if it were a strong filter on its own; the trend condition is doing nearly all the work.
