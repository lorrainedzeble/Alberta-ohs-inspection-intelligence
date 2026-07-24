"""Independently verify the pinned Roofing 2020 regression benchmark.

This checker intentionally imports no workspace loader or skill code.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = PROJECT_ROOT / "data" / "2024_ohs-employer-record-open-data.xlsx"

EXPECTED = {
    "employer_count": 1137,
    "person_years_sum": 4907.7,
    "ltc_count": 133,
    "ltc_rate_per_100_person_years": 2.71,
    "di_count": 236,
    "di_rate_per_100_person_years": 4.809,
    "fatality_count": 1,
    "enforcement_action_count": 802,
}

DATED_ACTION_SHEETS = {
    "Order (2020-2024)": "ISSUE_DATE",
    "Penalty (2020-2024)": "SERVED_DATE",
    "Ticket (2020-2024)": "OFFENCE_DATE",
    "Conviction (2020-2024)": "DATE_OF_CONVICTION",
}


def _year_from_mixed_excel_date(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    from_serial = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    numeric_mask = numeric.notna()
    from_serial.loc[numeric_mask] = (
        pd.Timestamp("1899-12-30")
        + pd.to_timedelta(numeric.loc[numeric_mask], unit="D")
    )
    from_text = pd.to_datetime(series.where(numeric.isna()), errors="coerce")
    return from_serial.fillna(from_text).dt.year


def calculate(path: Path) -> dict:
    injury = pd.read_excel(path, sheet_name="Injury (2020-2024)", engine="openpyxl")
    roofing_all_years = injury[injury["WCB_INDUSTRY_NAME"] == "ROOFING"]
    scoped = injury[
        (injury["WCB_INDUSTRY_NAME"] == "ROOFING") & (injury["YEAR_NO"] == 2020)
    ].sort_values(["EMP_KEY", "EMPLOYER_NAME"], kind="stable")
    scoped = scoped.drop_duplicates(subset=["EMP_KEY"], keep="first")

    person_years = float(scoped["PERSON_YEARS_COUNT"].fillna(0).sum())
    ltc_count = int(scoped["LOST_TIME_CLAIM_COUNT"].fillna(0).sum())
    di_count = int(scoped["ANNUAL_DISABLING_INJURIES_COUNT"].fillna(0).sum())
    fatality_count = int(scoped["ANNUAL_FATALITY_COUNT"].fillna(0).sum())
    # The production briefing attributes enforcement to the industry's full
    # five-year employer population, then groups actions by action year. Keep
    # that scope explicit: using only employers present in 2020 undercounts
    # the pinned 2020 enforcement total by seven.
    employer_keys = set(roofing_all_years["EMP_KEY"].dropna())

    action_count = 0
    for sheet, date_column in DATED_ACTION_SHEETS.items():
        actions = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
        years = _year_from_mixed_excel_date(actions[date_column])
        action_count += int((actions["EMP_KEY"].isin(employer_keys) & (years == 2020)).sum())

    return {
        "employer_count": int(scoped["EMP_KEY"].nunique()),
        "person_years_sum": round(person_years, 1),
        "ltc_count": ltc_count,
        "ltc_rate_per_100_person_years": round(ltc_count / person_years * 100, 3),
        "di_count": di_count,
        "di_rate_per_100_person_years": round(di_count / person_years * 100, 3),
        "fatality_count": fatality_count,
        "enforcement_action_count": action_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    actual = calculate(args.data)
    checks = {}
    for key, expected in EXPECTED.items():
        observed = actual[key]
        passed = (
            math.isclose(observed, expected, rel_tol=0, abs_tol=0.0005)
            if isinstance(expected, float)
            else observed == expected
        )
        checks[key] = {"expected": expected, "actual": observed, "status": "PASS" if passed else "FAIL"}
    result = {
        "checker": "independent raw-workbook rederivation; no workspace code imported",
        "scope": "ROOFING, 2020",
        "checks": checks,
        "overall": "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL",
    }
    print(json.dumps(result, indent=2))
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
