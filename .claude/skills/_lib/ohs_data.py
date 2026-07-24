"""
Shared data access for the Alberta OHS inspection prioritization workspace.

Every rule encoded here comes from knowledge/data-cautions.md and
knowledge/data-profile.md. Do not change a date conversion, a join rule, or
an aggregation approach here without checking those files first, and update
them if the rule changes.

Not a general purpose Excel reader. This module only knows how to read this
one dataset, this one way.
"""

import json
import os
import sys
import time
import pandas as pd


def _progress(message):
    """Progress feedback for long-running loads, written to stderr so it
    never contaminates a skill's JSON stdout output. The 53MB workbook's
    first load is slow (single-digit minutes observed, see
    evaluation/use-log.md, 2026-07-14 entry); a caller with no feedback for
    that long reasonably wonders whether the process has hung."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "2024_ohs-employer-record-open-data.xlsx")

EXCEL_EPOCH = pd.Timestamp("1899-12-30")

SHEET_NAMES = {
    "injury": "Injury (2020-2024)",
    "order": "Order (2020-2024)",
    "penalty": "Penalty (2020-2024)",
    "ticket": "Ticket (2020-2024)",
    "investigation": "Investigation (2020-2024)",
    "acceptance": "Acceptance (2020-2024)",
    "approval": "Approval (2020-2024)",
    "conviction": "Conviction (2020-2024)",
}

CONCERN_STATUSES = {"Revoked", "Denied", "Suspended"}
UNRESOLVED_ORDER_STATUSES = {"Non-Compliance", "Open"}
PERSON_YEARS_STABILITY_THRESHOLD = 40

# Every raw column any of the five skills or this library reads off that
# sheet's frame, not just the join/date/rate columns the first version of
# this manifest covered (an external review on 2026-07-14 caught that gap:
# employer-briefing reads Order.LEGISLATION_CODE/CONTRAVENTION/ORDER_TYPE,
# Penalty.EVENT_YEAR/AMOUNT, Ticket.AMOUNT, Conviction.INCIDENT_DATE/
# INCIDENT_TYPE/OFFENCE_LOCATION, and Acceptance/Approval's
# APPLICABLE_LEGISLATION, none of which the first manifest checked, so a
# rename there would still have crashed with a raw KeyError). Every name
# below was verified against the real workbook's actual header rows on
# 2026-07-14 before being added, so the stricter check cannot false-positive
# on the genuine source file. Checked once per sheet per process, so a
# 302-industry scan pays this cost once, not once per industry. See
# CLAUDE.md's Governance rule to escalate schema drift rather than silently
# work around it; this is that escalation actually enforced in code, found
# missing by a regression test on 2026-07-14 (see
# evaluation/regression-checklist.md, case 10).
# Investigation deliberately lists only EMP_KEY: its DESCRIPTION/URL fields
# exist but are never consumed, per CLAUDE.md refusal 5 (no free-text
# narrative surfacing) and the "binary ever-investigated flag only" rule.
REQUIRED_COLUMNS = {
    "injury": [
        "EMP_KEY", "EMPLOYER_NAME", "YEAR_NO", "WCB_INDUSTRY_NAME", "CITY_NAME",
        "PERSON_YEARS_COUNT", "LOST_TIME_CLAIM_COUNT", "ANNUAL_DISABLING_INJURIES_COUNT",
        "ANNUAL_FATALITY_COUNT",
    ],
    "order": ["EMP_KEY", "ISSUE_DATE", "STATUS", "LEGISLATION_CODE", "CONTRAVENTION", "ORDER_TYPE"],
    "ticket": ["EMP_KEY", "OFFENCE_DATE", "AMOUNT"],
    "penalty": ["EMP_KEY", "SERVED_DATE", "INDUSTRY_SECTOR", "EVENT_YEAR", "AMOUNT"],
    "investigation": ["EMP_KEY"],
    "acceptance": ["EMP_KEY", "ISSUE_DATE", "EXPIRY_DATE", "DESCRIPTION", "APPLICABLE_LEGISLATION"],
    "approval": ["EMP_KEY", "ISSUE_DATE", "EXPIRY_DATE", "DESCRIPTION", "APPLICABLE_LEGISLATION"],
    "conviction": ["EMP_KEY", "DATE_OF_CONVICTION", "INCIDENT_DATE", "INCIDENT_TYPE", "OFFENCE_LOCATION"],
}

_cache = {}


def _excel_serial_to_ts(series):
    return EXCEL_EPOCH + pd.to_timedelta(series, unit="D")


def _fail_schema_drift(sheet_label=None, missing_sheets=None, missing_columns=None):
    """A hard stop, not a returned error dict: prints the clean JSON an analyst
    or calling agent needs and exits before any calculation runs, per CLAUDE.md's
    Governance rule to escalate schema drift rather than silently work around
    it. Deliberately placed here, in the shared library every skill funnels
    through, so no individual skill script has to remember to check this
    itself. Before this existed, a renamed/missing column surfaced as a raw
    KeyError traceback instead (2026-07-14 regression finding, case 10)."""
    payload = {"error": "Source schema drift detected.", "action": "Stop processing and ask the analyst to verify the source workbook."}
    if sheet_label is not None:
        payload["sheet"] = sheet_label
    if missing_sheets is not None:
        payload["missing_sheets"] = missing_sheets
    if missing_columns is not None:
        payload["missing_columns"] = missing_columns
    print(json.dumps(payload, indent=2))
    sys.exit(1)


def _workbook():
    if "_xlfile" not in _cache:
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(
                "Source workbook not found at %s. Skills read the live file, "
                "they never work from a cached copy of the data." % DATA_PATH
            )
        _progress("Loading source workbook (~53MB, first access this run — can take several minutes)...")
        t0 = time.time()
        wb = pd.ExcelFile(DATA_PATH, engine="openpyxl")
        missing_sheets = [name for name in SHEET_NAMES.values() if name not in wb.sheet_names]
        if missing_sheets:
            _fail_schema_drift(missing_sheets=missing_sheets)
        _cache["_xlfile"] = wb
        _progress(f"Workbook opened ({time.time() - t0:.0f}s).")
    return _cache["_xlfile"]


def load_sheet(key):
    """key is one of the SHEET_NAMES keys. Returns a fresh copy every call."""
    if key not in _cache:
        _progress(f"Reading {SHEET_NAMES[key]} sheet...")
        t0 = time.time()
        df = _workbook().parse(SHEET_NAMES[key])
        missing_columns = [c for c in REQUIRED_COLUMNS.get(key, []) if c not in df.columns]
        if missing_columns:
            _fail_schema_drift(sheet_label=SHEET_NAMES[key], missing_columns=missing_columns)
        _cache[key] = df
        _progress(f"{SHEET_NAMES[key]} read ({len(_cache[key])} rows, {time.time() - t0:.0f}s).")
    return _cache[key].copy()


def load_injury():
    """COR_YEAR and TRADE_NAME are dropped here on purpose, both are completely
    empty in this file (0 of 841,761 rows), see data-cautions.md. Any caller
    that still expects those columns has a bug, not this function.

    Also deduplicates on (EMP_KEY, YEAR_NO): 342 of 236,365 EMP_KEYs (0.145%)
    have two rows per year under different EMPLOYER_NAME values (a numbered
    corporation plus an operating name, e.g. "2290682 ALBERTA LTD." / "OG
    DRYWALL LTD."), with identical person years, claim counts, and other
    metrics in every checked case, see data-cautions.md. Left undeduplicated,
    any EMP_KEY-unaware sum (industry-trend-briefing's industry-level rollups)
    double-counts these employers. Keeping one row per (EMP_KEY, YEAR_NO) is
    safe for every numeric column; use ambiguous_employer_names() separately
    to surface which employers this affects rather than silently picking one
    name, per CLAUDE.md's Governance rule to escalate EMP_KEY/name mismatches."""
    if "injury_deduped" not in _cache:
        df = load_sheet("injury").drop(columns=["COR_YEAR", "TRADE_NAME"], errors="ignore")
        _progress("Deduplicating Injury sheet by (EMP_KEY, YEAR_NO)...")
        _cache["injury_deduped"] = df.sort_values(["EMP_KEY", "YEAR_NO"], kind="stable").drop_duplicates(
            subset=["EMP_KEY", "YEAR_NO"], keep="first"
        )
    return _cache["injury_deduped"].copy()


def ambiguous_employer_names():
    """EMP_KEY -> sorted list of every distinct EMPLOYER_NAME seen for that
    key in the raw (undeduplicated) Injury sheet, only for the 342 EMP_KEYs
    with more than one name. TRADE_NAME is empty in this file, so this is the
    closest available signal to a legal-name/trade-name pair; never assume
    which of the two names is the one the analyst should use, show both."""
    if "ambiguous_names" not in _cache:
        raw = load_sheet("injury")
        grouped = raw.groupby("EMP_KEY")["EMPLOYER_NAME"].unique()
        _cache["ambiguous_names"] = {k: sorted(v) for k, v in grouped.items() if len(v) > 1}
    return _cache["ambiguous_names"]


def load_order():
    df = load_sheet("order")
    df["ACTION_DATE"] = _excel_serial_to_ts(df["ISSUE_DATE"])
    return df


def load_ticket():
    df = load_sheet("ticket")
    df["ACTION_DATE"] = _excel_serial_to_ts(df["OFFENCE_DATE"])
    return df


def load_penalty():
    df = load_sheet("penalty")
    df["ACTION_DATE"] = pd.to_datetime(df["SERVED_DATE"], format="%b %d, %Y", errors="coerce")
    return df


def load_conviction():
    df = load_sheet("conviction")
    df["ACTION_DATE"] = pd.to_datetime(df["DATE_OF_CONVICTION"], format="%b %d, %Y", errors="coerce")
    return df


def load_investigation():
    return load_sheet("investigation")


def load_acceptance():
    df = load_sheet("acceptance")
    df["ISSUE_DATE_TS"] = _excel_serial_to_ts(df["ISSUE_DATE"])
    df["EXPIRY_DATE_TS"] = _excel_serial_to_ts(df["EXPIRY_DATE"])
    return df


def load_approval():
    df = load_sheet("approval")
    df["ISSUE_DATE_TS"] = _excel_serial_to_ts(df["ISSUE_DATE"])
    df["EXPIRY_DATE_TS"] = _excel_serial_to_ts(df["EXPIRY_DATE"])
    return df


def unresolved_orders(as_of_year=None):
    """STATUS in (Non-Compliance, Open) only. STATUS "Compliance" is 98.5% of
    all rows and means the order was complied with, a resolved outcome, not a
    pending one. See data-cautions.md, Order STATUS section.

    Pass as_of_year to restrict to orders issued on or before that year. Any
    caller scoring/backtesting "as of" a given year must pass it, or a future
    order leaks into a supposedly historical feature, see data-cautions.md."""
    order = load_order()
    result = order[order["STATUS"].isin(UNRESOLVED_ORDER_STATUSES)]
    if as_of_year is not None:
        result = result[result["ACTION_DATE"].dt.year <= as_of_year]
    return result


def unified_enforcement_actions():
    """EMP_KEY, ACTION_DATE, SOURCE_SHEET across Order/Ticket/Penalty/Conviction.
    Conviction uses DATE_OF_CONVICTION, never INCIDENT_DATE (the incident is
    the underlying event, the conviction date is when OHS actually acted)."""
    frames = [
        load_order()[["EMP_KEY", "ACTION_DATE"]].assign(SOURCE_SHEET="Order"),
        load_ticket()[["EMP_KEY", "ACTION_DATE"]].assign(SOURCE_SHEET="Ticket"),
        load_penalty()[["EMP_KEY", "ACTION_DATE"]].assign(SOURCE_SHEET="Penalty"),
        load_conviction()[["EMP_KEY", "ACTION_DATE"]].assign(SOURCE_SHEET="Conviction"),
    ]
    unified = pd.concat(frames, ignore_index=True)
    return unified.dropna(subset=["ACTION_DATE"])


def first_enforcement_action_by_employer():
    """Minimum ACTION_DATE per EMP_KEY. Used by enforcement-effectiveness."""
    unified = unified_enforcement_actions()
    idx = unified.groupby("EMP_KEY")["ACTION_DATE"].idxmin()
    return unified.loc[idx].reset_index(drop=True)


def most_recent_enforcement_action_by_employer():
    """Maximum ACTION_DATE per EMP_KEY. Used by enforcement-gap-watchlist."""
    unified = unified_enforcement_actions()
    idx = unified.groupby("EMP_KEY")["ACTION_DATE"].idxmax()
    return unified.loc[idx].reset_index(drop=True)


def ever_investigated_employers():
    """Investigation has no date column at all, only usable as a binary flag."""
    return set(load_investigation()["EMP_KEY"].dropna().unique())


def acceptance_approval_concern_employers(as_of_year=None):
    """EMP_KEYs with a Revoked/Denied/Suspended Acceptance or Approval on
    record. Never derived from EXPIRY_DATE, status is not reliably synced to
    its own dates, see data-cautions.md.

    Pass as_of_year to restrict to instruments issued on or before that year
    (ISSUE_DATE_TS), the closest available cutoff given DESCRIPTION has no
    date of its own. Any caller scoring/backtesting "as of" a given year must
    pass it, or a future concern leaks into a supposedly historical feature."""
    acc = load_acceptance()
    app = load_approval()
    if as_of_year is not None:
        acc = acc[acc["ISSUE_DATE_TS"].dt.year <= as_of_year]
        app = app[app["ISSUE_DATE_TS"].dt.year <= as_of_year]
    acc_concern = set(acc.loc[acc["DESCRIPTION"].isin(CONCERN_STATUSES), "EMP_KEY"])
    app_concern = set(app.loc[app["DESCRIPTION"].isin(CONCERN_STATUSES), "EMP_KEY"])
    return acc_concern | app_concern


def industry_lookup():
    """EMP_KEY -> industry name. Injury's WCB_INDUSTRY_NAME is the primary
    source. Penalty's INDUSTRY_SECTOR is a verified fallback (0 mismatches on
    checkable rows) used only for employers missing from Injury entirely."""
    injury = load_injury()
    primary = (
        injury.dropna(subset=["WCB_INDUSTRY_NAME"])
        .groupby("EMP_KEY")["WCB_INDUSTRY_NAME"]
        .first()
    )
    penalty = load_sheet("penalty")
    missing_from_injury = set(penalty["EMP_KEY"]) - set(primary.index)
    fallback = (
        penalty[penalty["EMP_KEY"].isin(missing_from_injury)]
        .dropna(subset=["INDUSTRY_SECTOR"])
        .groupby("EMP_KEY")["INDUSTRY_SECTOR"]
        .first()
    )
    return pd.concat([primary, fallback]).to_dict()


def rate_from_counts(count_sum, person_years_sum):
    """Sum raw counts and person years across a group first, then compute one
    rate. Never average many small per employer rates together, 93% of
    individual employer year rows fall under the 40 person year threshold.
    Returns (rate_or_None, is_stable)."""
    if person_years_sum is None or person_years_sum <= 0:
        return None, False
    rate = (count_sum / person_years_sum) * 100
    return float(rate), bool(person_years_sum >= PERSON_YEARS_STABILITY_THRESHOLD)
