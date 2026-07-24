"""
industry-trend-briefing: 5 year LTC/DI rate, fatality, and enforcement volume
trend for one WCB industry. Rates are computed by summing raw counts and
person years across every employer in the industry for a given year, then
computing one rate, never by averaging individual employer rates. See
knowledge/data-cautions.md and knowledge/data-profile.md for why.

Usage:
  python script.py "INDUSTRY NAME"      one industry, full detail
  python script.py --all                every industry in one pass, condensed

--all exists because /quarterly-cycle's first step needs to scan every
industry, and relaunching this script once per industry would reload the
53MB workbook from scratch 302 times. The trend computation itself is a
groupby, doing it for every industry at once costs about the same as doing
it for one; only the per-industry loop for the trend_direction verdict runs
in Python, and that loop is over ~302 small already-aggregated rows, not
over the 841,761 row Injury sheet.
Prints a JSON object; the skill instructions turn this into prose.
"""

import difflib
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import ohs_data as ohs

# Minimum absolute percentage-point change (per 100 person-years) between an industry's
# earliest and latest stable-rate year before a direction counts as a real trend, not noise.
# Grounded on 2026.07.09 against two real false positives from the first full scan: Engineering
# (rate 0.049 -> 0.079, a 0.030pp change on 16-36 LTC claims/year) and Quality Control Services -
# Construction (0.199 -> 0.266, a 0.067pp change on 7-21 claims/year), both technically "up" but
# noise on a tiny claim count. 0.15 sits comfortably above both. See knowledge/data-cautions.md.
LTC_MATERIALITY_THRESHOLD = 0.15

# Fatality is checked as a pure historical fact (did one occur), never a trend or a forecast,
# per CLAUDE.md refusal 3. Independent of, and never merged with, the LTC/DI rate flag.
FATALITY_CHECK_YEARS = (2023, 2024)

# Most recent year the dataset covers. A handful of industries (found 2026.07.09: Government of
# Alberta, Health Care Services - Alberta Health Services, Health Care Services - Covenant
# Health) only have data through 2021, likely reclassified under different WCB_INDUSTRY_NAME
# values afterward. Their flags are computed correctly from the years they have, but that is not
# the same recency as an industry current through 2024; latest_year_is_current makes this
# impossible to silently overlook. See knowledge/data-cautions.md.
DATASET_MAX_YEAR = 2024

# A first-stable-year-vs-last-stable-year comparison was replaced on 2026.07.09 after it
# mislabeled two real industries: Iron/Steel Foundries (rate 2.056 -> 5.415 -> 4.698 -> 6.13 ->
# 2.659, a spike that mostly came back down, endpoints called it a mild "up") and Air Service -
# Scheduled Commercial (4.389 -> 7.196 -> 7.177 -> 5.901 -> 5.722, declining for 3 straight years
# since its 2021 peak, but endpoints called it "up" because 2020 was an anomalously low
# pandemic-affected baseline). Both person-years floors were fine, the endpoints-only comparison
# was the actual problem. Requires at least 4 stable years so the early and late windows never
# overlap; fewer than that is reported as insufficient data, the same convention
# enforcement-effectiveness uses for its own before/after windows, never approximated.
MIN_STABLE_YEARS_FOR_POOLED_TREND = 4


def _pooled_ltc_trend(years, counts, person_years):
    """years/counts/person_years are parallel lists already filtered to stable years, sorted
    ascending by year. Pools raw counts and person years across the earliest 2 and latest 2
    stable years separately (sum first, then one rate each side, never averaging two already
    computed rates), then compares those two pooled rates. See MIN_STABLE_YEARS_FOR_POOLED_TREND
    above and knowledge/data-cautions.md for why this replaced a first-vs-last single-year
    comparison."""
    if len(years) < MIN_STABLE_YEARS_FOR_POOLED_TREND:
        return {
            "ltc_di_trend_direction": "insufficient_stable_years_for_pooled_trend",
            "ltc_di_trend_flag": False,
            "ltc_di_early_window_years": None,
            "ltc_di_late_window_years": None,
            "ltc_di_early_window_rate": None,
            "ltc_di_late_window_rate": None,
            "ltc_rate_change_pooled_windows": None,
        }
    early_rate, _ = ohs.rate_from_counts(sum(counts[:2]), sum(person_years[:2]))
    late_rate, _ = ohs.rate_from_counts(sum(counts[-2:]), sum(person_years[-2:]))
    delta = round(late_rate - early_rate, 3)
    if abs(delta) < LTC_MATERIALITY_THRESHOLD:
        direction = "flat_immaterial"
    elif delta > 0:
        direction = "up"
    else:
        direction = "down"
    return {
        "ltc_di_trend_direction": direction,
        "ltc_di_trend_flag": direction == "up",
        "ltc_di_early_window_years": years[:2],
        "ltc_di_late_window_years": years[-2:],
        "ltc_di_early_window_rate": round(early_rate, 3) if early_rate is not None else None,
        "ltc_di_late_window_rate": round(late_rate, 3) if late_rate is not None else None,
        "ltc_rate_change_pooled_windows": delta,
    }


def industry_trend(industry_name):
    injury = ohs.load_injury()
    rows = injury[injury["WCB_INDUSTRY_NAME"] == industry_name]
    if rows.empty:
        # data-dictionary.md documents the field's type/meaning, not its 302 real
        # values, so pointing there for a spelling check is a dead end; suggest
        # live close matches from the actual data instead. Match case-insensitively
        # first (WCB_INDUSTRY_NAME is always upper case; a differently-cased query
        # would otherwise score as dissimilar on every letter, not just the typo),
        # then return the real on-file casing.
        all_names = injury["WCB_INDUSTRY_NAME"].dropna().unique().tolist()
        upper_to_real = {name.upper(): name for name in all_names}
        upper_matches = difflib.get_close_matches(industry_name.upper(), list(upper_to_real), n=5, cutoff=0.5)
        suggestions = [upper_to_real[m] for m in upper_matches]
        suggestion_text = (
            f" Closest real industry names on file: {suggestions}." if suggestions
            else " No close match found; run `python script.py --all` and read the "
                  "industry names back out of its output, or ask the analyst to confirm the spelling."
        )
        return {"error": f'No employers found with WCB_INDUSTRY_NAME == "{industry_name}". '
                          f"Industry names must match exactly.{suggestion_text}"}

    by_year = []
    for year in sorted(rows["YEAR_NO"].unique()):
        yr = rows[rows["YEAR_NO"] == year]
        person_years = yr["PERSON_YEARS_COUNT"].sum()
        ltc_count = yr["LOST_TIME_CLAIM_COUNT"].fillna(0).sum()
        di_count = yr["ANNUAL_DISABLING_INJURIES_COUNT"].fillna(0).sum()
        fatalities = int(yr["ANNUAL_FATALITY_COUNT"].fillna(0).sum())
        employer_count = yr["EMP_KEY"].nunique()

        ltc_rate, ltc_stable = ohs.rate_from_counts(ltc_count, person_years)
        di_rate, di_stable = ohs.rate_from_counts(di_count, person_years)

        by_year.append({
            "year": int(year),
            "employer_count": int(employer_count),
            "person_years_sum": round(float(person_years), 1),
            "ltc_count": int(ltc_count),
            "ltc_rate_per_100_person_years": round(ltc_rate, 3) if ltc_rate is not None else None,
            "ltc_rate_stable": ltc_stable,
            "di_count": int(di_count),
            "di_rate_per_100_person_years": round(di_rate, 3) if di_rate is not None else None,
            "di_rate_stable": di_stable,
            "fatality_count": fatalities,
        })

    industry_emp_keys = set(rows["EMP_KEY"].unique())
    unified = ohs.unified_enforcement_actions()
    industry_actions = unified[unified["EMP_KEY"].isin(industry_emp_keys)].copy()
    industry_actions["year"] = industry_actions["ACTION_DATE"].dt.year
    enforcement_by_year = (
        industry_actions.groupby("year").size().to_dict()
    )
    for row in by_year:
        row["enforcement_action_count"] = int(enforcement_by_year.get(row["year"], 0))

    years_present = [row["year"] for row in by_year]
    stable_rate_years = [r for r in by_year if r["ltc_rate_stable"]]
    trend = _pooled_ltc_trend(
        years=[r["year"] for r in stable_rate_years],
        counts=[r["ltc_count"] for r in stable_rate_years],
        person_years=[r["person_years_sum"] for r in stable_rate_years],
    )

    fatality_by_year = {r["year"]: r["fatality_count"] for r in by_year}
    fatality_counts_checked = {y: fatality_by_year.get(y, 0) for y in FATALITY_CHECK_YEARS}
    fatality_flag = any(count > 0 for count in fatality_counts_checked.values())

    latest_year_value = years_present[-1] if years_present else None
    return {
        "industry": industry_name,
        "years_covered": years_present,
        "latest_year_is_current": (latest_year_value == DATASET_MAX_YEAR) if latest_year_value else None,
        "by_year": by_year,
        "ltc_materiality_threshold": LTC_MATERIALITY_THRESHOLD,
        "fatality_counts_checked": fatality_counts_checked,
        "fatality_flag": fatality_flag,
        "note": "ltc_di_trend_flag and fatality_flag are independent and never merged into one "
                "boolean; an industry can carry either, both, or neither. ltc_di_trend compares "
                "the earliest 2 vs. latest 2 stable years pooled, never a single-year endpoint "
                "comparison. See knowledge/data-cautions.md.",
        "source": "Injury and unified enforcement (Order/Ticket/Penalty/Conviction) sheets, "
                  "data/2024_ohs-employer-record-open-data.xlsx",
        **trend,
    }


def all_industries_trend():
    injury = ohs.load_injury()
    injury = injury.copy()
    for col in ("LOST_TIME_CLAIM_COUNT", "ANNUAL_DISABLING_INJURIES_COUNT", "ANNUAL_FATALITY_COUNT"):
        injury[col] = injury[col].fillna(0)

    grouped = injury.groupby(["WCB_INDUSTRY_NAME", "YEAR_NO"]).agg(
        person_years_sum=("PERSON_YEARS_COUNT", "sum"),
        ltc_count=("LOST_TIME_CLAIM_COUNT", "sum"),
        di_count=("ANNUAL_DISABLING_INJURIES_COUNT", "sum"),
        fatality_count=("ANNUAL_FATALITY_COUNT", "sum"),
        employer_count=("EMP_KEY", "nunique"),
    ).reset_index()

    grouped["ltc_rate"] = (grouped["ltc_count"] / grouped["person_years_sum"]) * 100
    grouped["ltc_stable"] = grouped["person_years_sum"] >= ohs.PERSON_YEARS_STABILITY_THRESHOLD

    unified = ohs.unified_enforcement_actions()
    unified = unified.copy()
    unified["year"] = unified["ACTION_DATE"].dt.year
    industry_map = ohs.industry_lookup()
    unified["industry"] = unified["EMP_KEY"].map(industry_map)
    enforcement_counts = (
        unified.dropna(subset=["industry"])
        .groupby(["industry", "year"])
        .size()
        .rename("enforcement_action_count")
        .reset_index()
    )
    grouped = grouped.merge(
        enforcement_counts,
        left_on=["WCB_INDUSTRY_NAME", "YEAR_NO"],
        right_on=["industry", "year"],
        how="left",
    )
    grouped["enforcement_action_count"] = grouped["enforcement_action_count"].fillna(0).astype(int)

    results = []
    for industry, sub in grouped.groupby("WCB_INDUSTRY_NAME"):
        sub = sub.sort_values("YEAR_NO")
        stable = sub[sub["ltc_stable"]]
        trend = _pooled_ltc_trend(
            years=[int(y) for y in stable["YEAR_NO"].tolist()],
            counts=[float(c) for c in stable["ltc_count"].tolist()],
            person_years=[float(p) for p in stable["person_years_sum"].tolist()],
        )
        direction = trend["ltc_di_trend_direction"]
        ltc_di_trend_flag = trend["ltc_di_trend_flag"]

        fatality_counts_checked = {}
        for y in FATALITY_CHECK_YEARS:
            year_row = sub[sub["YEAR_NO"] == y]
            fatality_counts_checked[y] = int(year_row["fatality_count"].sum()) if not year_row.empty else 0
        fatality_flag = any(count > 0 for count in fatality_counts_checked.values())

        flagged_because = []
        if ltc_di_trend_flag:
            flagged_because.append("ltc_di_trend")
        if fatality_flag:
            flagged_because.append("fatality")

        latest = sub.iloc[-1]
        latest_year_value = int(latest["YEAR_NO"])
        results.append({
            "industry": industry,
            "years_covered": [int(y) for y in sub["YEAR_NO"].tolist()],
            **trend,
            "fatality_counts_checked": {str(y): c for y, c in fatality_counts_checked.items()},
            "fatality_flag": fatality_flag,
            "flagged_because": flagged_because,
            "latest_year": latest_year_value,
            "latest_year_is_current": latest_year_value == DATASET_MAX_YEAR,
            "latest_employer_count": int(latest["employer_count"]),
            "latest_ltc_rate_per_100_person_years": (
                round(float(latest["ltc_rate"]), 3) if pd_notna(latest["ltc_rate"]) else None
            ),
            "latest_rate_stable": bool(latest["ltc_stable"]),
            "latest_enforcement_action_count": int(latest["enforcement_action_count"]),
        })

    flagged = [r for r in results if r["ltc_di_trend_flag"] or r["fatality_flag"]]
    flagged_sorted = sorted(flagged, key=lambda r: r["latest_employer_count"], reverse=True)
    top_n = 15
    return {
        "scanned_industry_count": len(results),
        "flagged_industry_count": len(flagged),
        "flagged_industries_top": flagged_sorted[:top_n],
        "flagged_industries_remaining_count": max(0, len(flagged_sorted) - top_n),
        "flagged_industries_all": flagged_sorted,
        "all_industries": results,
        "note": (
            f"{len(flagged)} of {len(results)} industries carry ltc_di_trend_flag and/or "
            f"fatality_flag, two independent flags, never merged into one boolean; see "
            f"flagged_because on each record and knowledge/data-cautions.md. "
            f"flagged_industries_top holds the {top_n} largest by latest_employer_count among "
            f"those carrying either flag (same disclosed 'favors higher volume in absolute "
            f"terms' logic used in inspection-target-ranking); the rest are in "
            f"flagged_industries_all. ltc_di_trend_flag requires direction 'up' AND at least a "
            f"{LTC_MATERIALITY_THRESHOLD} percentage-point absolute change between the pooled "
            f"earliest-2 and latest-2 stable (>=40 person years) years, never a single-year "
            f"endpoint comparison (that mislabeled real industries, see knowledge/data-"
            f"cautions.md); fewer than {MIN_STABLE_YEARS_FOR_POOLED_TREND} stable years reports "
            f"'insufficient_stable_years_for_pooled_trend' rather than approximating. "
            f"fatality_flag is a historical fact only, at least one fatality in "
            f"{FATALITY_CHECK_YEARS[0]} or {FATALITY_CHECK_YEARS[1]}, never a forecast. "
            f"Check latest_year_is_current on every record before presenting it alongside "
            f"others: a handful of industries (found 2026.07.09) only have data through 2021, "
            f"likely reclassified since, and their flags are computed correctly from what they "
            f"have but are not the same recency as an industry current through "
            f"{DATASET_MAX_YEAR}."
        ),
    }


def pd_notna(value):
    import pandas as pd
    return pd.notna(value)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        print(json.dumps(all_industries_trend(), indent=2, default=str))
    elif len(sys.argv) == 2:
        print(json.dumps(industry_trend(sys.argv[1]), indent=2, default=str))
    else:
        print(json.dumps({"error": 'usage: python script.py "INDUSTRY NAME"  OR  python script.py --all'}))
        sys.exit(1)
