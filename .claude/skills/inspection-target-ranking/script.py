"""
inspection-target-ranking: risk ranked employer shortlist within an industry
and/or city, grouped by city for routing. Every score component is disclosed,
never a black box number.

Scoring is deliberately built from raw counts, not rates, because 93% of
individual employer year rows fall under the 40 person year rate stability
threshold (see knowledge/data-profile.md); an individual employer's "rate"
is usually not a stable number, but its raw injury/enforcement counts always
are. This means the score favors higher volume employers in absolute terms.
That is a disclosed design choice, not an accident, and the skill's
presentation instructions must say so.

WEIGHTS below are explicit, disclosed defaults, not a validated statistical
model. They map onto Alberta OHS's own four stated selection criteria (see
CLAUDE.md Purpose): recent LTC/DI counts approximate injury rate and incident
frequency, unresolved orders and Acceptance/Approval concerns approximate
compliance history. Change them here, not in the analyst's head.

Usage:
  python script.py rank --industry "INDUSTRY NAME" --city "CITY NAME" --top-n 20 --as-of-year 2024
  python script.py backtest --industry "INDUSTRY NAME" --city "CITY NAME" --top-n 20
Only "rank"/"backtest" is positional; industry/city/top-n/as-of-year are
named flags, all optional (see SKILL.md).
"""

import json
import sys
import os
from math import comb

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import ohs_data as ohs

WEIGHTS = {
    "recent_ltc_count": 1.0,
    "recent_di_count": 1.0,
    "fatality_ever": 5.0,
    "unresolved_order_ever": 3.0,
    "acceptance_approval_concern": 1.0,
}

# Below this, a top-N hit rate this high is not distinguishable from a random
# draw of the same size at the population's own rate; see knowledge/data-cautions.md.
BACKTEST_SIGNIFICANCE_THRESHOLD = 0.05


def _binomial_upper_tail(n, p, k):
    """P(X >= k) for X ~ Binomial(n, p). Used to check whether an observed
    top-N hit count is unlikely under the population's own rate, not just
    numerically higher than it."""
    return sum(comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def _build_features(industry, city, as_of_year):
    injury = ohs.load_injury()
    rows = injury[injury["YEAR_NO"] <= as_of_year].copy()
    if industry:
        rows = rows[rows["WCB_INDUSTRY_NAME"] == industry]
    if city:
        rows = rows[rows["CITY_NAME"] == city]
    if rows.empty:
        return None

    recent_years = [y for y in (as_of_year - 1, as_of_year) if y >= 2020]
    recent = rows[rows["YEAR_NO"].isin(recent_years)]

    recent_agg = recent.groupby("EMP_KEY").agg(
        recent_ltc_count=("LOST_TIME_CLAIM_COUNT", lambda s: s.fillna(0).sum()),
        recent_di_count=("ANNUAL_DISABLING_INJURIES_COUNT", lambda s: s.fillna(0).sum()),
        recent_person_years=("PERSON_YEARS_COUNT", "sum"),
    )

    fatality_ever = rows.groupby("EMP_KEY")["ANNUAL_FATALITY_COUNT"].apply(
        lambda s: bool(s.fillna(0).sum() > 0)
    )

    latest_row = rows.sort_values("YEAR_NO").groupby("EMP_KEY").last()
    latest_city = latest_row["CITY_NAME"]
    latest_name = latest_row["EMPLOYER_NAME"]

    unresolved = ohs.unresolved_orders(as_of_year=as_of_year)
    unresolved_flag = unresolved.groupby("EMP_KEY").size() > 0

    concern_keys = ohs.acceptance_approval_concern_employers(as_of_year=as_of_year)

    features = recent_agg.join(fatality_ever.rename("fatality_ever"), how="outer")
    features = features.join(latest_city, how="left").join(latest_name, how="left")
    features["fatality_ever"] = features["fatality_ever"].fillna(False)
    features["unresolved_order_ever"] = features.index.map(
        lambda k: bool(unresolved_flag.get(k, False))
    )
    features["acceptance_approval_concern"] = features.index.map(lambda k: k in concern_keys)
    for col in ("recent_ltc_count", "recent_di_count", "recent_person_years"):
        features[col] = features[col].fillna(0.0)
    ambiguous = ohs.ambiguous_employer_names()
    features["employer_name_ambiguous"] = features.index.map(lambda k: k in ambiguous)
    return features.reset_index()


def _score(features):
    features = features.copy()
    features["score_ltc"] = features["recent_ltc_count"] * WEIGHTS["recent_ltc_count"]
    features["score_di"] = features["recent_di_count"] * WEIGHTS["recent_di_count"]
    features["score_fatality"] = features["fatality_ever"].astype(int) * WEIGHTS["fatality_ever"]
    features["score_unresolved_order"] = (
        features["unresolved_order_ever"].astype(int) * WEIGHTS["unresolved_order_ever"]
    )
    features["score_acceptance_approval"] = (
        features["acceptance_approval_concern"].astype(int) * WEIGHTS["acceptance_approval_concern"]
    )
    features["TOTAL_SCORE"] = features[
        ["score_ltc", "score_di", "score_fatality", "score_unresolved_order", "score_acceptance_approval"]
    ].sum(axis=1)
    return features


def rank(industry=None, city=None, top_n=20, as_of_year=2024):
    features = _build_features(industry, city, as_of_year)
    if features is None:
        return {"error": f"No employers found for industry={industry!r} city={city!r}. "
                          f"Check exact spelling against knowledge/data-dictionary.md."}
    # EMP_KEY is a deterministic, arbitrary tie-break, not a judgment about risk;
    # without it, two employers tied on TOTAL_SCORE sort in whatever incidental row
    # order the input happened to have, which is not reproducible across runs or
    # unrelated code changes (found live: a data-loader change silently swapped
    # which of two exactly-tied employers appeared in a real top-3, see
    # knowledge/data-cautions.md).
    scored = _score(features).sort_values(["TOTAL_SCORE", "EMP_KEY"], ascending=[False, True], kind="stable")
    top = scored.head(top_n)

    # An employer's presence in the top N is only unambiguous if no one outside
    # the top N shares their exact score. When the cutoff score is tied, which
    # specific employers fill the remaining slots is an arbitrary, deterministic
    # tie-break choice, not a real difference in risk (see backtest()'s
    # employers_tied_at_top_n_boundary and knowledge/data-cautions.md). Flag this
    # per employer so the shortlist can show "robustly ranked" separately from
    # "tied at the cutoff, could equally be any of the other tied employers."
    boundary_score = None
    if len(scored) >= top_n:
        boundary_score = scored.iloc[top_n - 1]["TOTAL_SCORE"]
    boundary_tie_count = int((scored["TOTAL_SCORE"] == boundary_score).sum()) if boundary_score is not None else 0
    at_boundary_tie = boundary_tie_count > 1

    grouped_by_city = {}
    for _, row in top.iterrows():
        grouped_by_city.setdefault(str(row["CITY_NAME"]), []).append({
            "EMP_KEY": row["EMP_KEY"],
            "EMPLOYER_NAME": row["EMPLOYER_NAME"],
            "employer_name_ambiguous": bool(row["employer_name_ambiguous"]),
            "TOTAL_SCORE": round(float(row["TOTAL_SCORE"]), 2),
            "at_top_n_boundary_tie": bool(at_boundary_tie and row["TOTAL_SCORE"] == boundary_score),
            "components": {
                "recent_ltc_count": int(row["recent_ltc_count"]),
                "recent_di_count": int(row["recent_di_count"]),
                "recent_person_years": round(float(row["recent_person_years"]), 1),
                "fatality_ever": bool(row["fatality_ever"]),
                "unresolved_order_ever": bool(row["unresolved_order_ever"]),
                "acceptance_approval_concern": bool(row["acceptance_approval_concern"]),
            },
        })

    return {
        "industry": industry,
        "city": city,
        "as_of_year": as_of_year,
        "eligible_employer_count": int(len(scored)),
        "weights_used": WEIGHTS,
        "top_n_requested": top_n,
        "top_n_boundary_tied": at_boundary_tie,
        "employers_tied_at_top_n_boundary": boundary_tie_count if at_boundary_tie else 0,
        "shortlist_by_city": grouped_by_city,
        "note": "Score is built from raw counts, not rates, and favors higher volume "
                "employers in absolute terms by design; see script.py docstring and "
                "knowledge/data-profile.md. If employer_name_ambiguous is true for a shortlisted "
                "EMP_KEY, that account is recorded under more than one distinct employer name "
                "(see knowledge/data-cautions.md); check employer-briefing for the full list "
                "before routing an inspection to a named business, never assume EMPLOYER_NAME "
                "here is the only name that account operates under. CITY_NAME (shortlist_by_city's "
                "keys) is the employer's registered WCB mailing address, not a confirmed Alberta "
                "worksite location, this dataset has no province or worksite field; a large or "
                "multi-location employer's registered city can be an out-of-province head office "
                "(see knowledge/data-cautions.md). Confirm the employer's actual Alberta worksite "
                "before routing an inspection off this grouping. If an employer's "
                "at_top_n_boundary_tie is true, its presence in this shortlist (as opposed to any "
                "of the other employers_tied_at_top_n_boundary employers sharing the exact same "
                "score) is an arbitrary, deterministic tie-break, not a real difference in risk; "
                "present it separately from the unambiguously top-ranked employers, per "
                "knowledge/data-cautions.md.",
    }


def backtest(industry=None, city=None, top_n=20):
    features = _build_features(industry, city, as_of_year=2022)
    if features is None:
        return {"error": f"No employers found for industry={industry!r} city={city!r} as of 2022."}
    # EMP_KEY is a deterministic, arbitrary tie-break, not a judgment about risk;
    # without it, two employers tied on TOTAL_SCORE sort in whatever incidental row
    # order the input happened to have, which is not reproducible across runs or
    # unrelated code changes (found live: a data-loader change silently swapped
    # which of two exactly-tied employers appeared in a real top-3, see
    # knowledge/data-cautions.md).
    scored = _score(features).sort_values(["TOTAL_SCORE", "EMP_KEY"], ascending=[False, True], kind="stable")
    top_keys = set(scored.head(top_n)["EMP_KEY"])
    all_keys = set(scored["EMP_KEY"])

    # Which employers land in the top N is only meaningful if the cutoff score is
    # unique. When multiple employers share the exact boundary score, the EMP_KEY
    # tie-break above picks one arbitrary, deterministic set, but a different
    # (equally arbitrary) tie-break would pick a different set and could change
    # top_n_enforcement_rate_2023_2024 and therefore the gate verdict. Found live
    # (2026.07.12): 9 of 15 confirmed industries had a boundary tie; one
    # (Construction Framing Contractor, 8 employers tied at the same score)
    # actually flipped its gate verdict purely from which tied employers the
    # tie-break happened to select. See knowledge/data-cautions.md.
    employers_tied_at_boundary = 0
    boundary_score = None
    if len(scored) >= top_n:
        boundary_score = scored.iloc[top_n - 1]["TOTAL_SCORE"]
        employers_tied_at_boundary = int((scored["TOTAL_SCORE"] == boundary_score).sum())
    top_n_boundary_tied = employers_tied_at_boundary > 1

    unified = ohs.unified_enforcement_actions()
    unified["year"] = unified["ACTION_DATE"].dt.year
    outcome_keys = set(unified.loc[unified["year"].isin([2023, 2024]), "EMP_KEY"])

    top_hits = len(top_keys & outcome_keys)
    pop_hits = len(all_keys & outcome_keys)
    top_rate = top_hits / len(top_keys) if top_keys else None
    pop_rate = pop_hits / len(all_keys) if all_keys else None

    beats_random = (top_rate is not None and pop_rate is not None and top_rate > pop_rate)

    chance_probability = None
    significant = False
    if top_rate is not None and pop_rate is not None and top_keys:
        chance_probability = round(_binomial_upper_tail(len(top_keys), pop_rate, top_hits), 4)
        significant = chance_probability < BACKTEST_SIGNIFICANCE_THRESHOLD

    validated_actual = beats_random and significant

    def _validated_at(hits, n, p):
        if not n or p is None:
            return False, None
        rate = hits / n
        cp = round(_binomial_upper_tail(n, p, hits), 4)
        return (rate > p) and (cp < BACKTEST_SIGNIFICANCE_THRESHOLD), cp

    # A tie flag alone (top_n_boundary_tied) says the cutoff is ambiguous; it
    # does not say whether the verdict actually depends on it. Compute both
    # ends of the range: the worst-case tie-break (the tied slots filled with
    # as few 2023-2024 enforcement hits as possible) and the best-case
    # tie-break (filled with as many hits as possible). Only if the verdict
    # genuinely flips between those two ends is this industry actually
    # tie-sensitive; otherwise the tie is real but immaterial to the outcome.
    worst_case_validated = validated_actual
    best_case_validated = validated_actual
    worst_case_chance_probability = chance_probability
    best_case_chance_probability = chance_probability
    if top_n_boundary_tied and top_keys and pop_rate is not None:
        tied_group = set(scored.loc[scored["TOTAL_SCORE"] == boundary_score, "EMP_KEY"])
        base_keys = top_keys - tied_group
        slots_at_boundary = len(top_keys) - len(base_keys)
        tied_size = len(tied_group)
        tied_hits = len(tied_group & outcome_keys)
        base_hits = len(base_keys & outcome_keys)

        worst_case_added = max(0, slots_at_boundary - (tied_size - tied_hits))
        best_case_added = min(slots_at_boundary, tied_hits)

        worst_case_validated, worst_case_chance_probability = _validated_at(
            base_hits + worst_case_added, len(top_keys), pop_rate
        )
        best_case_validated, best_case_chance_probability = _validated_at(
            base_hits + best_case_added, len(top_keys), pop_rate
        )

    if not top_n_boundary_tied:
        verdict = "validated" if validated_actual else "rejected"
        tie_sensitive = False
    elif worst_case_validated:
        # Even the least favorable tie-break still clears the bar.
        verdict = "validated"
        tie_sensitive = False
    elif not best_case_validated:
        # Even the most favorable tie-break still fails to clear the bar.
        verdict = "rejected"
        tie_sensitive = False
    else:
        # The verdict genuinely depends on which arbitrary tie-break is used.
        verdict = "deferred_boundary_tie"
        tie_sensitive = True

    return {
        "industry": industry,
        "city": city,
        "scored_on": "2020-2022 data only",
        "checked_against": "2023-2024 enforcement outcomes (Order/Ticket/Penalty/Conviction)",
        "top_n": top_n,
        "top_n_enforcement_rate_2023_2024": round(top_rate, 4) if top_rate is not None else None,
        "full_population_enforcement_rate_2023_2024": round(pop_rate, 4) if pop_rate is not None else None,
        "population_size": len(all_keys),
        "beats_random_sample_of_same_size": beats_random,
        "chance_probability_of_this_hit_rate_at_random": chance_probability,
        "significance_threshold": BACKTEST_SIGNIFICANCE_THRESHOLD,
        "significant": significant,
        "gated_exception_triggered": verdict != "validated",
        "employers_tied_at_top_n_boundary": employers_tied_at_boundary,
        "boundary_score": round(float(boundary_score), 2) if boundary_score is not None else None,
        "top_n_boundary_tied": top_n_boundary_tied,
        "tie_sensitive": tie_sensitive,
        "worst_case_chance_probability": worst_case_chance_probability,
        "best_case_chance_probability": best_case_chance_probability,
        "verdict": verdict,
        "note": "Per CLAUDE.md's gated exception: the ranking is validated only if the top-N "
                "hit rate both exceeds the population rate AND is unlikely to occur by chance "
                "(binomial P(X>=observed hits) under the population's own rate, below "
                f"{BACKTEST_SIGNIFICANCE_THRESHOLD}). A higher raw rate alone is not enough at "
                "small top_n, see chance_probability_of_this_hit_rate_at_random. If "
                "gated_exception_triggered is True, the ranking formula is rejected for this "
                "scope and must be revised, or shipped only as \"sorted by raw indicators\" "
                "language, never presented as a risk score. If top_n_boundary_tied is True, the "
                "verdict is NOT set from the single arbitrary, deterministic tie-break resolution "
                "alone (employers_tied_at_top_n_boundary employers share the cutoff score); both "
                "ends of the range are computed instead, worst_case_chance_probability (tied slots "
                "filled with as few 2023-2024 hits as possible) and best_case_chance_probability "
                "(filled with as many hits as possible). 'verdict: validated' means even the "
                "worst-case tie-break still clears the bar; 'rejected' means even the best-case "
                "tie-break still fails it; 'deferred_boundary_tie' (tie_sensitive: true) means the "
                "verdict genuinely flips depending on which arbitrary tie-break is used, per "
                "CLAUDE.md's triage convention (accept/reject/defer, each with a reason) — the "
                "reason here is that the population itself is ambiguous, not that the evidence was "
                "weighed and found wanting either way.",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["rank", "backtest"])
    parser.add_argument("--industry", default=None)
    parser.add_argument("--city", default=None)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--as-of-year", type=int, default=2024)
    args = parser.parse_args()

    if args.mode == "rank":
        result = rank(args.industry, args.city, args.top_n, args.as_of_year)
    else:
        result = backtest(args.industry, args.city, args.top_n)

    print(json.dumps(result, indent=2, default=str))
