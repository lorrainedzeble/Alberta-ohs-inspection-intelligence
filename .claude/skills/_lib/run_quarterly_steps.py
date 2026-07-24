"""
Orchestrates /quarterly-cycle's Steps 3 (rank) and 4 (brief) in one Python
process instead of one fresh `python script.py ...` process per industry
and per employer.

Why this exists: quarterly-cycle.md originally told the operating agent to
shell out to inspection-target-ranking/script.py once per confirmed
industry (backtest + rank, two calls) and employer-briefing/script.py once
per briefed employer. Each of those is a separate OS process, and every
separate process reloads the entire 841,761-row, 8-sheet workbook from
scratch (measured 8-11 minutes per cold load, see evaluation/use-log.md,
2026-07-14 entry). For a real cycle with up to 15 confirmed industries,
that is dozens of redundant full reloads of the same file inside one
workflow run. This script loads the workbook exactly once and reuses the
same in-process cache (ohs_data.py's _cache dict) across every industry
and every employer.

Usage:
  python run_quarterly_steps.py --industries "IND1,IND2,..." [--top-n 10]

Prints one consolidated JSON to stdout: {industry: {backtest, rank, briefs}}.
Progress messages go to stderr (see ohs_data.py's _progress), never stdout,
so stdout stays valid JSON for a caller to parse.
"""

import json
import sys
import os
import time
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import ohs_data as ohs  # noqa: E402
import importlib.util


def _load_module(name, path):
    """Both inspection-target-ranking and employer-briefing ship a file
    literally named script.py; a bare `import script` is ambiguous once
    both directories are on sys.path (whichever loads first silently wins,
    found live: `import script as ranking` bound to the wrong module and
    failed with AttributeError on `backtest`). Loading each by explicit
    file path under a distinct module name avoids that collision entirely."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ranking = _load_module("ranking_script", os.path.join(_HERE, "..", "inspection-target-ranking", "script.py"))
briefing = _load_module("briefing_script", os.path.join(_HERE, "..", "employer-briefing", "script.py"))


def run(industries, top_n=10, briefs_per_industry=3):
    results = {}
    total = len(industries)
    for i, industry in enumerate(industries, 1):
        ohs._progress(f"[{i}/{total}] Calculating industry metrics for {industry!r} (back test)...")
        bt = ranking.backtest(industry=industry, top_n=top_n)
        entry = {"backtest": bt, "rank": None, "briefs": []}

        if bt.get("verdict") == "rejected":
            ohs._progress(f"[{i}/{total}] {industry!r} rejected at the gate; skipping rank/brief per Step 3.")
            results[industry] = entry
            continue

        ohs._progress(f"[{i}/{total}] Ranking employers for {industry!r}...")
        rank_result = ranking.rank(industry=industry, top_n=top_n)
        entry["rank"] = rank_result

        shortlist = [
            e for city_list in rank_result.get("shortlist_by_city", {}).values() for e in city_list
        ]
        shortlist_unambiguous = [e for e in shortlist if not e.get("at_top_n_boundary_tie")]
        shortlist_unambiguous.sort(key=lambda e: e["TOTAL_SCORE"], reverse=True)
        to_brief = shortlist_unambiguous[:briefs_per_industry]

        for j, emp in enumerate(to_brief, 1):
            ohs._progress(f"[{i}/{total}] Briefing employer {j}/{len(to_brief)} for {industry!r}: {emp['EMPLOYER_NAME']}...")
            brief = briefing.employer_briefing(emp["EMP_KEY"])
            entry["briefs"].append(brief)

        results[industry] = entry

    return results


USE_LOG_PATH = os.path.join(_HERE, "..", "..", "..", "evaluation", "use-log.md")


def _log_confirmation(confirmation, industries):
    """Step 2's confirmation pause is an instruction to the operating agent
    (quarterly-cycle.md), not a code-level lock on its own; this is the one
    piece of that pause enforceable in code, since Step 3 cannot proceed
    without going through this script. It still cannot stop an operator from
    typing an arbitrary string, but it can stop Step 3 from running with no
    confirmation input at all, and it makes the confirmation an observable,
    logged fact rather than a step that's easy to silently skip."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"\n### {time.strftime('%Y-%m-%d')}: Step 2 confirmation recorded (automated)\n"
        f"Confirmed at {stamp}. Analyst-supplied confirmation text: \"{confirmation}\". "
        f"Confirmed industry list ({len(industries)}): {', '.join(industries)}.\n"
    )
    with open(USE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
    ohs._progress(f"Confirmation logged to evaluation/use-log.md.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--industries", required=True, help="Comma-separated list of confirmed industry names")
    parser.add_argument(
        "--confirmation",
        required=True,
        help='Required. The analyst\'s explicit confirmation text (e.g. "CONFIRMED" or a one-line '
             'note on what was changed from the Step 1 list). Step 3 refuses to run without this.',
    )
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--briefs-per-industry", type=int, default=3)
    args = parser.parse_args()

    confirmation = args.confirmation.strip()
    if not confirmation:
        print(
            json.dumps({
                "error": "Step 3 refused to run: --confirmation was empty. Per CLAUDE.md's Governance "
                         "section and quarterly-cycle.md's Step 2, the analyst's confirmation of the "
                         "flagged industry list (or her edits to it) must be supplied explicitly before "
                         "ranking runs. This is not an optional flag."
            }, indent=2),
            file=sys.stderr,
        )
        sys.exit(1)

    industries = [s.strip() for s in args.industries.split(",") if s.strip()]
    if not industries:
        print(json.dumps({"error": "Step 3 refused to run: --industries was empty."}, indent=2), file=sys.stderr)
        sys.exit(1)

    _log_confirmation(confirmation, industries)

    t0 = time.time()
    ohs._progress(f"Starting Steps 3-4 for {len(industries)} confirmed industries: {', '.join(industries)}")
    output = run(industries, top_n=args.top_n, briefs_per_industry=args.briefs_per_industry)
    ohs._progress(f"Steps 3-4 complete in {time.time() - t0:.0f}s total (one workbook load, not {len(industries)}+).")
    print(json.dumps(output, indent=2, default=str))
