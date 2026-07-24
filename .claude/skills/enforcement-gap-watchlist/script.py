"""
enforcement-gap-watchlist: employers with a rising injury trend and no
Order/Penalty/Ticket/Conviction in the last 3+ years, "ever investigated"
tracked as a separate flag since Investigation has no date column.

Rising injury trend = at least 2 consecutive year over year increases in
ANNUAL_DISABLING_INJURIES_COUNT (the broadest injury metric in this data),
requiring at least 3 consecutive years present to assess; fewer years means
"not enough data to call a trend," not "flagged."

No enforcement in 3+ years = most recent action (Order/Ticket/Penalty/
Conviction, via the same unified date table enforcement-effectiveness uses)
is more than 3 years before the latest year in scope, or absent entirely.

Per CLAUDE.md's gated exception: if more than 15% of the eligible population
is flagged, that is a threshold calibration problem, not a finding, and this
script says so rather than returning an oversized list as meaningful.

Usage: python script.py [--industry "INDUSTRY NAME"] [--city "CITY NAME"]
Both flags are optional and named, not positional; see SKILL.md.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import ohs_data as ohs

GATE_FRACTION = 0.15
LATEST_YEAR = 2024
STALE_ENFORCEMENT_YEARS = 3


def _rising_trend(sub):
    sub = sub.sort_values("YEAR_NO")
    years = sub["YEAR_NO"].tolist()
    counts = sub["ANNUAL_DISABLING_INJURIES_COUNT"].fillna(0).tolist()
    if len(years) < 3:
        return False, "insufficient years to assess a trend"
    for i in range(len(years) - 2):
        if years[i + 1] == years[i] + 1 and years[i + 2] == years[i] + 2:
            if counts[i] < counts[i + 1] < counts[i + 2]:
                return True, f"DI count rose {counts[i]:.0f} -> {counts[i+1]:.0f} -> {counts[i+2]:.0f} ({years[i]}-{years[i+2]})"
    return False, "no 2 consecutive year over year increases found"


def watchlist(industry=None, city=None):
    injury = ohs.load_injury()
    if industry:
        injury = injury[injury["WCB_INDUSTRY_NAME"] == industry]
    if city:
        injury = injury[injury["CITY_NAME"] == city]
    if injury.empty:
        return {"error": f"No employers found for industry={industry!r} city={city!r}."}

    most_recent_action_df = ohs.most_recent_enforcement_action_by_employer().set_index("EMP_KEY")
    most_recent_action = most_recent_action_df["ACTION_DATE"]
    most_recent_action_sheet = most_recent_action_df["SOURCE_SHEET"]
    investigated = ohs.ever_investigated_employers()

    eligible_keys = injury["EMP_KEY"].unique()
    flagged = []
    for key in eligible_keys:
        sub = injury[injury["EMP_KEY"] == key]
        rising, reason = _rising_trend(sub)
        if not rising:
            continue
        last_action = most_recent_action.get(key)
        if last_action is not None and (LATEST_YEAR - last_action.year) < STALE_ENFORCEMENT_YEARS:
            continue  # had a recent enough action, not "flying under the radar"
        flagged.append({
            "EMP_KEY": key,
            "EMPLOYER_NAME": sub.sort_values("YEAR_NO")["EMPLOYER_NAME"].iloc[-1],
            "trend_reason": reason,
            "most_recent_enforcement_action": last_action.strftime("%Y-%m-%d") if last_action is not None else None,
            "most_recent_enforcement_action_source_sheet": most_recent_action_sheet.get(key) if last_action is not None else None,
            "years_since_last_action": (LATEST_YEAR - last_action.year) if last_action is not None else None,
            "ever_investigated": key in investigated,
        })

    eligible_count = len(eligible_keys)
    flagged_count = len(flagged)
    fraction = flagged_count / eligible_count if eligible_count else 0.0
    gate_triggered = fraction > GATE_FRACTION

    return {
        "industry": industry,
        "city": city,
        "eligible_employer_count": eligible_count,
        "flagged_count": flagged_count,
        "flagged_fraction": round(fraction, 4),
        "gate_fraction_threshold": GATE_FRACTION,
        "gated_exception_triggered": gate_triggered,
        "flagged_employers": [] if gate_triggered else flagged,
        "note": (
            "Flagged fraction exceeds 15%; per CLAUDE.md's gated exception this is a threshold "
            "calibration problem, not a finding. The flagged list is withheld; revisit the "
            "trend or staleness definition before using this scope."
            if gate_triggered else
            "Rising trend requires 2 consecutive year over year DI count increases across 3 "
            "consecutive years present in the data; fewer years present means not enough data "
            "to call a trend, not automatically excluded from being flagged later once more "
            "years exist."
        ),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--industry", default=None)
    parser.add_argument("--city", default=None)
    args = parser.parse_args()
    print(json.dumps(watchlist(args.industry, args.city), indent=2, default=str))
