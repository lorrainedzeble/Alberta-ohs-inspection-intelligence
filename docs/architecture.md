# Architecture and trust boundaries

## Data plane

1. `scripts/refresh_data.py` queries the open-data catalogue for the current Employer Records XLSX.
2. The download is written to a temporary `.part` file.
3. Basic XLSX integrity and required worksheet names are checked.
4. The file replaces the local snapshot atomically.
5. `.claude/skills/_lib/ohs_data.py` validates every consumed column before calculations.

The source workbook is never committed to Git.

## Analytical plane

- `industry-trend-briefing`: pooled industry rates, fatality and enforcement trends.
- `inspection-target-ranking`: transparent indicator score plus historical back-test.
- `employer-briefing`: source-cited employer dossier.
- `enforcement-effectiveness`: before/after descriptive comparison.
- `enforcement-gap-watchlist`: rising trend with stale or absent dated enforcement.

Shared data loading centralizes schema validation, date normalization, stable joins, and `EMP_KEY` deduplication. Analytical aggregations remain inside their respective skills.

## Governance plane

- The agent may compute, rank, and draft.
- The analyst confirms the industry set before employer ranking.
- A rejected back-test blocks risk-score language.
- A calibration gate blocks oversized watchlists.
- Independent verification checks claimed metrics.
- The analyst owns the final operational decision.

## Independent-check boundary

`scripts/verify_gold.py` deliberately does not import `ohs_data.py` or any skill. It opens the raw workbook itself and independently reproduces the pinned Roofing benchmark. This makes checker and producer separate for the most load-bearing regression anchor.

The broader `validate-metric` role remains a fresh-context review procedure for arbitrary narrative outputs. Automating every possible narrative claim would require a structured claim schema; that is a sensible future extension rather than something this repository pretends is already solved.

## Known boundaries

- Annual public extract, not a real-time operational feed.
- Mailing city is not a verified worksite.
- Ranking weights are transparent heuristics, not fitted causal estimates.
- Back-testing against later enforcement measures predictive alignment with enforcement activity, not injury prevention impact.
- No production authentication, case-management integration, or personally identifying worker data.

