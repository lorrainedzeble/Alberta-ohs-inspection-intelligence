"""
enforcement-effectiveness: injury/DI rate before vs. after an employer's
first enforcement action. See knowledge/data-cautions.md, sections "First
enforcement action needs one definition across four date formats" and
"Before/after windows are limited by only 5 years of data", before changing
any logic here.

Window rule: up to 2 years before and up to 2 years after the action year,
excluding the action year itself, using whatever years exist in 2020-2024.
If either side has zero available years for a given employer, that employer
is reported as insufficient data, never given a fabricated number.

Usage:
  python script.py employer "EMP_KEY"
  python script.py industry "INDUSTRY NAME"
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import ohs_data as ohs

VALID_YEARS = {2020, 2021, 2022, 2023, 2024}


def _window_years(action_year):
    before = sorted(y for y in (action_year - 2, action_year - 1) if y in VALID_YEARS)
    after = sorted(y for y in (action_year + 1, action_year + 2) if y in VALID_YEARS)
    return before, after


def _pooled_rate(injury, emp_keys, year_pairs, count_col):
    """year_pairs: iterable of (EMP_KEY, year) to include."""
    if not year_pairs:
        return None, False, 0.0
    pairs_df = injury.merge(
        pd_dataframe(year_pairs, columns=["EMP_KEY", "YEAR_NO"]),
        on=["EMP_KEY", "YEAR_NO"],
        how="inner",
    )
    person_years = pairs_df["PERSON_YEARS_COUNT"].sum()
    count_sum = pairs_df[count_col].fillna(0).sum()
    rate, stable = ohs.rate_from_counts(count_sum, person_years)
    return rate, stable, float(person_years)


def pd_dataframe(rows, columns):
    import pandas as pd
    return pd.DataFrame(rows, columns=columns)


def employer_effectiveness(emp_key):
    first_actions = ohs.first_enforcement_action_by_employer()
    row = first_actions[first_actions["EMP_KEY"] == emp_key]
    if row.empty:
        return {"error": f"No dated enforcement action (Order/Ticket/Penalty/Conviction) found for {emp_key}."}

    action_date = row.iloc[0]["ACTION_DATE"]
    action_year = int(action_date.year)
    before_years, after_years = _window_years(action_year)

    injury = ohs.load_injury()
    own = injury[injury["EMP_KEY"] == emp_key]

    def _own_window(years, count_col):
        if not years:
            return {"years_used": [], "status": "insufficient data, before/after not computable"}
        sub = own[own["YEAR_NO"].isin(years)]
        person_years = sub["PERSON_YEARS_COUNT"].sum()
        count_sum = sub[count_col].fillna(0).sum()
        rate, stable = ohs.rate_from_counts(count_sum, person_years)
        return {
            "years_used": years,
            "person_years_sum": round(float(person_years), 2),
            "count_sum": int(count_sum),
            "rate_per_100_person_years": round(rate, 3) if rate is not None else None,
            "rate_stable": stable,
        }

    return {
        "emp_key": emp_key,
        "first_enforcement_action": {
            "date": action_date.strftime("%Y-%m-%d"),
            "source_sheet": row.iloc[0]["SOURCE_SHEET"],
            "year": action_year,
        },
        "ltc": {
            "before": _own_window(before_years, "LOST_TIME_CLAIM_COUNT"),
            "after": _own_window(after_years, "LOST_TIME_CLAIM_COUNT"),
        },
        "disabling_injury": {
            "before": _own_window(before_years, "ANNUAL_DISABLING_INJURIES_COUNT"),
            "after": _own_window(after_years, "ANNUAL_DISABLING_INJURIES_COUNT"),
        },
    }


def industry_effectiveness(industry):
    injury = ohs.load_injury()
    industry_keys = set(injury.loc[injury["WCB_INDUSTRY_NAME"] == industry, "EMP_KEY"])
    if not industry_keys:
        return {"error": f'No employers found with WCB_INDUSTRY_NAME == "{industry}".'}

    first_actions = ohs.first_enforcement_action_by_employer()
    first_actions = first_actions[first_actions["EMP_KEY"].isin(industry_keys)]
    if first_actions.empty:
        return {"error": f'No employer in "{industry}" has a dated enforcement action on record.'}

    before_pairs, after_pairs = [], []
    for _, r in first_actions.iterrows():
        action_year = int(r["ACTION_DATE"].year)
        before_years, after_years = _window_years(action_year)
        before_pairs += [(r["EMP_KEY"], y) for y in before_years]
        after_pairs += [(r["EMP_KEY"], y) for y in after_years]

    ltc_before_rate, ltc_before_stable, before_py = _pooled_rate(injury, industry_keys, before_pairs, "LOST_TIME_CLAIM_COUNT")
    ltc_after_rate, ltc_after_stable, after_py = _pooled_rate(injury, industry_keys, after_pairs, "LOST_TIME_CLAIM_COUNT")
    di_before_rate, di_before_stable, _ = _pooled_rate(injury, industry_keys, before_pairs, "ANNUAL_DISABLING_INJURIES_COUNT")
    di_after_rate, di_after_stable, _ = _pooled_rate(injury, industry_keys, after_pairs, "ANNUAL_DISABLING_INJURIES_COUNT")

    return {
        "industry": industry,
        "employers_with_enforcement_action": int(first_actions["EMP_KEY"].nunique()),
        "note": "Pooled: every employer's own before/after years (relative to their own first "
                "action) are summed together across the whole industry before computing one "
                "rate each side, per knowledge/data-cautions.md. Employers do not all share the "
                "same calendar window.",
        "ltc_rate_before": {"rate": round(ltc_before_rate, 3) if ltc_before_rate is not None else None,
                             "stable": ltc_before_stable, "person_years_sum": round(before_py, 1)},
        "ltc_rate_after": {"rate": round(ltc_after_rate, 3) if ltc_after_rate is not None else None,
                            "stable": ltc_after_stable, "person_years_sum": round(after_py, 1)},
        "di_rate_before": {"rate": round(di_before_rate, 3) if di_before_rate is not None else None,
                            "stable": di_before_stable},
        "di_rate_after": {"rate": round(di_after_rate, 3) if di_after_rate is not None else None,
                           "stable": di_after_stable},
    }


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("employer", "industry"):
        print(json.dumps({"error": 'usage: python script.py employer|industry "VALUE"'}))
        sys.exit(1)
    mode, value = sys.argv[1], sys.argv[2]
    result = employer_effectiveness(value) if mode == "employer" else industry_effectiveness(value)
    print(json.dumps(result, indent=2, default=str))
