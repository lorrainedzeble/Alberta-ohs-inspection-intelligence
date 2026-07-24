"""
employer-briefing: one page dossier for a single employer. Injury trend vs.
industry benchmark, full enforcement history across Order/Penalty/Ticket/
Investigation/Conviction, Acceptance/Approval history (historical status
only, never live validity), and a legislation hot spot checklist for the
employer's industry.

Usage:
  python script.py "EMP_KEY or exact employer name"
Prints JSON. If a name matches more than one EMP_KEY, prints the candidates
instead of guessing.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import ohs_data as ohs


def _resolve_emp_key(identifier):
    injury = ohs.load_injury()
    if identifier in set(injury["EMP_KEY"]):
        return identifier, None
    matches = injury.loc[injury["EMPLOYER_NAME"] == identifier, "EMP_KEY"].unique()
    if len(matches) == 1:
        return matches[0], None
    if len(matches) == 0:
        return None, f'No EMP_KEY and no employer named exactly "{identifier}" found in Injury.'
    return None, (f'"{identifier}" matches {len(matches)} different EMP_KEYs '
                   f"(employer name is not unique, see knowledge/data-cautions.md). "
                   f"Candidates: {list(matches)}. Ask the analyst which one.")


def _industry_benchmark(industry, years):
    injury = ohs.load_injury()
    industry_rows = injury[injury["WCB_INDUSTRY_NAME"] == industry]
    benchmark = {}
    for year in years:
        yr = industry_rows[industry_rows["YEAR_NO"] == year]
        person_years = yr["PERSON_YEARS_COUNT"].sum()
        ltc = yr["LOST_TIME_CLAIM_COUNT"].fillna(0).sum()
        rate, stable = ohs.rate_from_counts(ltc, person_years)
        benchmark[int(year)] = {
            "industry_ltc_rate_per_100_person_years": round(rate, 3) if rate is not None else None,
            "industry_rate_stable": stable,
            "industry_employer_count": int(yr["EMP_KEY"].nunique()),
        }
    return benchmark


def employer_briefing(identifier):
    emp_key, error = _resolve_emp_key(identifier)
    if error:
        return {"error": error}

    injury = ohs.load_injury()
    own = injury[injury["EMP_KEY"] == emp_key].sort_values("YEAR_NO")
    if own.empty:
        return {"error": f"EMP_KEY {emp_key} not found in Injury."}

    employer_name = own["EMPLOYER_NAME"].iloc[-1]
    industry = own["WCB_INDUSTRY_NAME"].dropna().iloc[-1] if own["WCB_INDUSTRY_NAME"].notna().any() else None
    city = own["CITY_NAME"].dropna().iloc[-1] if own["CITY_NAME"].notna().any() else None

    name_variants = ohs.ambiguous_employer_names().get(emp_key)
    employer_name_ambiguous = name_variants is not None
    employer_name_all_known_names = name_variants if name_variants else [employer_name]

    own_trend = []
    for _, row in own.iterrows():
        person_years = row["PERSON_YEARS_COUNT"]
        ltc_count_for_rate = row["LOST_TIME_CLAIM_COUNT"] if pd_notna(row["LOST_TIME_CLAIM_COUNT"]) else 0
        ltc_rate, ltc_stable = ohs.rate_from_counts(ltc_count_for_rate, person_years)
        own_trend.append({
            "year": int(row["YEAR_NO"]),
            "person_years": round(float(person_years), 2) if pd_notna(person_years) else None,
            "lost_time_claim_count": int(row["LOST_TIME_CLAIM_COUNT"]) if pd_notna(row["LOST_TIME_CLAIM_COUNT"]) else 0,
            "lost_time_claim_rate": round(ltc_rate, 3) if ltc_rate is not None else None,
            "rate_stable": ltc_stable,
            "disabling_injury_count": int(row["ANNUAL_DISABLING_INJURIES_COUNT"]) if pd_notna(row["ANNUAL_DISABLING_INJURIES_COUNT"]) else 0,
            "fatality_count": int(row["ANNUAL_FATALITY_COUNT"]) if pd_notna(row["ANNUAL_FATALITY_COUNT"]) else 0,
        })

    benchmark = _industry_benchmark(industry, [r["year"] for r in own_trend]) if industry else {}

    def _sheet_history(loader, date_col, display_cols):
        # ISSUE_DATE (Order) and OFFENCE_DATE (Ticket) are raw Excel serials in
        # this file; SERVED_DATE (Penalty) and the Conviction date fields are
        # already formatted text (see knowledge/data-cautions.md, "Date fields
        # are not consistently typed"). Always display the normalized
        # ACTION_DATE ohs_data.py already computed for every sheet, so the
        # analyst never sees a bare serial number regardless of which sheet.
        df = loader()
        rows = df[df["EMP_KEY"] == emp_key].copy()
        rows[date_col] = rows["ACTION_DATE"].dt.strftime("%Y-%m-%d")
        return rows[[date_col] + display_cols].to_dict(orient="records")

    order_history = _sheet_history(ohs.load_order, "ISSUE_DATE", ["LEGISLATION_CODE", "CONTRAVENTION", "ORDER_TYPE", "STATUS"])
    penalty_history = _sheet_history(ohs.load_penalty, "SERVED_DATE", ["EVENT_YEAR", "AMOUNT"])
    ticket_history = _sheet_history(ohs.load_ticket, "OFFENCE_DATE", ["AMOUNT"])
    # Conviction has two distinct dates worth keeping separate: the incident
    # date (the underlying event) and the conviction date (ACTION_DATE, when
    # OHS actually acted, sometimes years later, see data-cautions.md). Both
    # are already formatted text in this sheet; only DATE_OF_CONVICTION is
    # replaced with the normalized ACTION_DATE for consistency across sheets.
    conviction_history = _sheet_history(ohs.load_conviction, "DATE_OF_CONVICTION", ["INCIDENT_DATE", "INCIDENT_TYPE", "OFFENCE_LOCATION"])
    ever_investigated = emp_key in ohs.ever_investigated_employers()

    def _instrument_history(loader):
        df = loader()
        rows = df[df["EMP_KEY"] == emp_key]
        return rows[["ISSUE_DATE_TS", "EXPIRY_DATE_TS", "DESCRIPTION", "APPLICABLE_LEGISLATION"]].assign(
            ISSUE_DATE=lambda d: d["ISSUE_DATE_TS"].dt.strftime("%Y-%m-%d"),
            EXPIRY_DATE_ORIGINAL_TERM=lambda d: d["EXPIRY_DATE_TS"].dt.strftime("%Y-%m-%d"),
        )[["ISSUE_DATE", "EXPIRY_DATE_ORIGINAL_TERM", "DESCRIPTION", "APPLICABLE_LEGISLATION"]].to_dict(orient="records")

    acceptance_history = _instrument_history(ohs.load_acceptance)
    approval_history = _instrument_history(ohs.load_approval)

    hotspot = []
    if industry:
        industry_keys = set(injury.loc[injury["WCB_INDUSTRY_NAME"] == industry, "EMP_KEY"])
        order = ohs.load_order()
        industry_orders = order[order["EMP_KEY"].isin(industry_keys)]
        top = (
            industry_orders.groupby(["LEGISLATION_CODE", "CONTRAVENTION"])
            .size()
            .sort_values(ascending=False)
            .head(5)
        )
        hotspot = [
            {"legislation_code": k[0], "contravention": k[1], "order_count_in_industry": int(v)}
            for k, v in top.items()
        ]

    return {
        "emp_key": emp_key,
        "employer_name": employer_name,
        "employer_name_ambiguous": employer_name_ambiguous,
        "employer_name_all_known_names": employer_name_all_known_names,
        "industry": industry,
        "city": city,
        "injury_trend": own_trend,
        "industry_benchmark": benchmark,
        "enforcement_history": {
            "order": order_history,
            "penalty": penalty_history,
            "ticket": ticket_history,
            "conviction": conviction_history,
            "ever_investigated": ever_investigated,
        },
        "acceptance_history": acceptance_history,
        "approval_history": approval_history,
        "legislation_hotspot_for_industry": hotspot,
        "note": "Acceptance/Approval entries show DESCRIPTION as the most recently recorded "
                "status only (Issued/Expired/Revoked/Denied/Suspended); EXPIRY_DATE_ORIGINAL_TERM "
                "is the originally scheduled term end, not a live validity signal, see "
                "knowledge/data-cautions.md. If employer_name_ambiguous is true, this EMP_KEY is "
                "recorded under more than one distinct employer name (see "
                "employer_name_all_known_names); state this explicitly to the analyst rather than "
                "presenting a single name as certain, per CLAUDE.md's Governance rule to escalate "
                "EMP_KEY/name mismatches.",
    }


def pd_notna(value):
    import pandas as pd
    return pd.notna(value)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "usage: python script.py \"EMP_KEY or exact employer name\""}))
        sys.exit(1)
    print(json.dumps(employer_briefing(sys.argv[1]), indent=2, default=str))
