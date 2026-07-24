# Start here

This is a working guide for actually running this workspace, not a description of what it does (that's `CLAUDE.md`). Everything below was checked directly against this repository on 2026-07-14, including a genuine clean-environment test (copying the whole project to a different drive and running every command from scratch, see `evaluation/use-log.md`).

## What you need before you start

- Python 3.12 (this was built and tested on 3.12.10; other 3.x versions likely work but were not tested).
- `pandas` and `openpyxl`, pinned in `requirements.txt` at the workspace root (pandas==3.0.3, openpyxl==3.1.5, the versions this was built and tested on). Install both with:
  ```
  python -m pip install -r requirements.txt
  ```
  If `python script.py ...` fails with `ModuleNotFoundError` after that, your `python` isn't the same interpreter `pip` installed into; check `python -m pip show pandas` resolves.
- Claude Code (or a compatible agent runtime) if you want to run the skills, the workflow, and `validate-metric` the way this workspace is designed to be used, conversationally rather than by typing raw Python commands yourself. Every skill below also runs as a plain Python script with no agent at all, useful for testing, but that skips the analyst-facing framing and the governance gates described in `CLAUDE.md`.

## Where the workbook goes

Put the source file at exactly this path, relative to the workspace root:

```
data/2024_ohs-employer-record-open-data.xlsx
```

Every skill reads this one file directly (no cached or pre-processed copy). If it's missing, every skill fails immediately with a clear `FileNotFoundError` naming the expected path, it does not fall back to old data or guess.

For this public repository, download and validate the current annual resource automatically:

```powershell
python scripts/refresh_data.py
```

Use `--force` to replace an existing local copy. The dataset is excluded from Git; the script records the source URL, download time, SHA-256 hash, size, and validated worksheets in `data/refresh-receipt.json`.

## Opening the workspace

Open this folder (the one containing `CLAUDE.md`) as your project root in Claude Code. `CLAUDE.md` is read automatically; it is the living spec for everything else here.

## Your first command

Ask, in plain language, something like:

> "How is the Roofing industry trending?"

This should route to `industry-trend-briefing`. See the walkthrough below for the full expected exchange (expect the timing discussed below, not a fixed 5 minutes).

## Running each of the 5 skills

All five can be invoked two ways: conversationally (just ask the question in the left column) or directly as a script from its own folder under `.claude/skills/`. The direct commands are what the agent actually runs underneath; useful if you want to test a skill in isolation.

| Skill | Ask this | Or run directly |
|---|---|---|
| Industry trend briefing | "How is [industry] trending?" / "Which industries need attention this quarter?" | `python script.py "INDUSTRY NAME"` or `python script.py --all` (from `.claude/skills/industry-trend-briefing/`) |
| Inspection target ranking | "Who should we target in [industry]?" | `python script.py rank --industry "INDUSTRY NAME" --city "CITY NAME" --top-n 20 --as-of-year 2024` or `python script.py backtest --industry "INDUSTRY NAME" --top-n 20` (from `.claude/skills/inspection-target-ranking/`) |
| Employer briefing | "Brief me on [employer name or EMP_KEY]" | `python script.py "EMP_KEY or exact employer name"` (from `.claude/skills/employer-briefing/`) |
| Enforcement effectiveness | "Did enforcement actually work for [employer/industry]?" | `python script.py employer "EMP_KEY"` or `python script.py industry "INDUSTRY NAME"` (from `.claude/skills/enforcement-effectiveness/`) |
| Enforcement gap watchlist | "Who's flying under the radar?" | `python script.py --industry "INDUSTRY NAME" --city "CITY NAME"` (both flags optional, from `.claude/skills/enforcement-gap-watchlist/`) |

Every flag is named, not positional (`--industry`, not a bare quoted string in argument position), except the `rank`/`backtest` mode word itself and employer-briefing's/enforcement-effectiveness's single identifier argument. This matters most in PowerShell, which silently drops empty-string positional arguments and shifts every argument after it; named flags avoid that failure mode entirely.

Every skill's output must go through `validate-metric` before it's shown to you as final (see "Independent verification" below). This is a required manual step in this runtime, not something that happens on its own.

## Running the full quarterly cycle

Ask Claude Code to run `/quarterly-cycle`, optionally with a comma-separated list of industry names to pre-narrow the scan (`/quarterly-cycle "ROOFING, WELDING"`), or with nothing to scan all 302 industries.

The workflow has a hard stop built in: after Step 1 (the scan), it presents a flagged industry list and ends its turn, waiting for you to reply in a separate message confirming the list or your edits to it. **This is not optional and cannot be skipped in the same response.** Step 3 (ranking and briefing) is enforced in code, not just prose: it runs through `.claude/skills/_lib/run_quarterly_steps.py`, which requires a `--confirmation` value and refuses to run at all (exit code 1, no workbook access) if it's empty. Whatever you actually say to confirm or edit the list becomes that value, and it's logged to `evaluation/use-log.md` automatically before ranking starts.

## What to actually expect for timing

This project's own build notes have quoted several different numbers for how long this workbook takes to load (143 seconds, 6 minutes, 9-11 minutes, 34 seconds). These are not inconsistent measurements of the same thing; they're measurements of *different steps*, taken under *different conditions*, reported without always naming which. Reconciled here with all four dimensions labeled, from real, timestamped runs on 2026-07-14:

| Step | Isolated (solo process) | 2 concurrent processes (both reading the workbook at once) |
|---|---|---|
| `pd.ExcelFile()` open (the container/zip structure only, no cell data yet) | ~34s | 32-42s |
| Injury sheet `.parse()` (841,761 rows, the actual slow step) | 349s (~5.8 min) | 423-483s (~7-8 min) |
| Full 3-industry orchestrated run (`run_quarterly_steps.py`: workbook load + backtest/rank/brief for 3 industries) | 533s total (~8.9 min), of which ~383s (72%) is the one-time load, well under a minute for all 3 industries' actual ranking/briefing once loaded | not separately measured |
| Full 302-industry scan (`industry-trend-briefing --all`), measured end to end with `time` | 501s total (~8.4 min) | — |

Corrections to this project's own earlier claims, made honestly rather than quietly:
- **A prior claim that the workbook "opened in 34 seconds" (implying a fast load) was a measurement error, not a real result.** 34s is consistently how long just the `pd.ExcelFile()` container step takes; the actual Injury sheet read that follows it still took 349-483s in every test run today, isolated or concurrent. Conflating the fast open step with the whole load was wrong and is corrected here.
- **A "warm OS file cache makes this faster" theory did not hold up under direct retesting.** Re-running the load multiple times within the same session, after the file had already been read repeatedly, still cost 349-483s for the Injury sheet parse every time. This strongly suggests the bottleneck is CPU-bound XML/zip parsing inside `openpyxl`, not disk I/O that an OS page cache would speed up. Don't plan around a warm-cache best case; plan around the isolated-process numbers above.
- **`industry-trend-briefing/SKILL.md` and CLAUDE.md's "~143 seconds for all 302 industries" figure could not be reproduced under any condition tested on 2026-07-14** (the closest comparable run, a full `--all` scan, took roughly 8-9 minutes total under both isolated-ish and concurrent conditions). This discrepancy is flagged, not silently resolved: it may reflect a different original measurement environment, a warmer cache state achieved differently, or a figure that only ever counted the vectorized groupby computation and not the sheet read preceding it. Treat 143 seconds as unverified until someone can reproduce it directly; treat the table above as what was actually, repeatedly observed this session.

Practical guidance from the reconciled numbers:
- **Expect 6-9 minutes for the first thing you run in a fresh process**, isolated. Expect 8-11 minutes if something else is also reading the workbook at the same time.
- **After the first load in one process, everything in that same process is fast** (well under a minute per additional industry), which is why `/quarterly-cycle`'s Step 3 runs through `run_quarterly_steps.py` instead of one fresh process per industry.
- Every separate `python script.py` invocation is its own process with no cross-process cache; a raw sequence of separate skill calls each pays the full multi-minute cost again, isolated-process numbers apply to each one.
- If a skill or the workflow appears to hang with no output for several minutes, that's expected during the load. Progress messages (`Loading source workbook...`, `Reading Injury sheet...`, etc.) print as it works; if you're watching stderr you'll see it moving. If there is truly no progress message for more than about 12 minutes, that is worth investigating, not waiting out.

## Where outputs and logs land

- Skill outputs are not saved anywhere by default; they're printed as JSON to stdout (or shown conversationally by the agent) for you to read or pipe elsewhere yourself.
- `evaluation/use-log.md` is where every real use of this workspace gets recorded: quarterly cycle runs, Step 2 confirmations (written automatically by `run_quarterly_steps.py`), and `validate-metric` verdicts (written manually, see below).
- `evaluation/quarterly-memo-2026-07-10.md` is the one real quarterly memo produced so far, an example of Step 6's output format.
- The dashboard (`dashboard/index.html`) is a static snapshot built from one real cycle; it does not update itself when you run a new cycle. See "Updating the dashboard" below.

## Updating the dashboard

`dashboard/index.html` is a single self-contained file: all its data lives in one embedded `const DATA = {...}` JSON literal partway through the file, no server, no live workbook connection, no separate data file to swap in. This makes it easy to view (just open the file) but means updating it is a real, manual step, not a command this workspace runs for you. Be precise about what "current" means before you start:

- **What this dashboard currently represents:** the quarterly cycle run on 2026-07-10 (corrected through 2026-07-13 for the boundary-tie verdict logic fix), with a 5-year (2020-2024) `by_year` trend breakdown added per confirmed industry on 2026-07-14 from a fresh, direct rerun of `industry-trend-briefing`'s own `industry_trend()` function, not a different calculation. The masthead's freshness banner states this same run date on every tab; if you ever see the banner and this section disagree, trust the banner and treat this section as stale.
- **What was embedded, and how:** every number in `DATA` was produced by actually running the real skills (`industry-trend-briefing --all` for the scan, `inspection-target-ranking`'s `rank`/`backtest` for each confirmed industry, `employer-briefing` for each shortlisted employer, and a direct `industry_trend()` call per confirmed industry for the 5-year breakdown), then hand-merged into the embedded JSON by a one-off Python script (not shipped with this workspace, since it was written per-revision against whatever fields that revision needed). There is no persistent `build_dashboard.py` in this repository today; that is a real gap, not a hidden feature.
- **How a future operator would update it for a new cycle:**
  1. Run `/quarterly-cycle` for real (see above), through Step 6's memo.
  2. For each confirmed industry, also capture `industry_trend(name)`'s full JSON (single-industry mode, not `--all`, since only single-industry mode returns `by_year`) to get the 5-year breakdown this dashboard shows.
  3. Write a short Python script that opens `dashboard/index.html`, locates `const DATA = ` followed by the JSON literal (parse it with `json.JSONDecoder().raw_decode`, don't regex-match the braces, they nest), replaces the fields that changed (`industries`, `scan_summary`, `full_scan_all`, `employer_dossiers`, `employer_citations`, `verify_sample_rows`, `gold_example`) with the freshly captured real output, and writes the file back with `json.dumps(data, default=str)` (no `indent`, to match the existing compact style already in the file).
  4. Update the masthead's run-date line and the freshness banner's stated run date (both near the top of the file, inside the `.masthead` div) to the new cycle's actual date. Do this by hand; nothing computes it automatically from the embedded data.
- **What to verify after updating, before treating the new dashboard as final:**
  - The file still opens without a blank page; check the browser console for a JS parse error first if it doesn't.
  - The embedded JSON still parses on its own (`json.JSONDecoder().raw_decode` on the extracted literal, same check used to build it).
  - The pinned gold example (Roofing 2020) still reproduces exactly, since that regression anchor should not change unless the source workbook itself changed.
  - Spot check at least 2-3 industries' `latest_ltc_rate`/`latest_employer_count` in the new `DATA.industries` against a fresh, independent run of `industry-trend-briefing --all` for the same industries, not just trust the merge script.
  - Run `validate-metric` on at least the industries whose numbers changed before presenting the refreshed dashboard as authoritative; log the verdict in `evaluation/use-log.md` per the section below, the same as any other skill output.
- This is not automated on purpose for now (see `knowledge/dashboard-mockup-framing.md` for why the dashboard was built as a static snapshot rather than a live view), but it is meant to be reproducible by a future operator following the steps above, not a one-off artifact only the original builder understands.

## Independent verification (`validate-metric`)

`validate-metric` (`.claude/agents/validate-metric.md`) defines a role: recompute every number in a skill's draft output independently from the raw sheets, with no access to the reasoning that produced it, and report PASS or FAIL per number. **This runtime does not support it as a registered, automatically-dispatched subagent type** (confirmed directly on 2026-07-14: invoking it by name is rejected outright). It has to be run manually: hand `.claude/agents/validate-metric.md`'s exact instructions to a general-purpose agent, alongside a skill's draft output only, never the script or reasoning that produced it.

After running it, log the verdict, PASS or FAIL, and if FAIL, what was found and what was corrected, to `evaluation/use-log.md` the same day. This is a required step, not an optional afterthought; a FAIL that gets fixed but never logged is exactly the kind of gap this workspace's own evaluation practice is supposed to catch.

**Five distinct states, not one, so nothing here gets presented as more settled than it is:**
- **draft** — a skill's raw output, just produced, `validate-metric` not yet run on it. This is the default state of everything any skill prints; treat a number as a draft until one of the states below is explicitly true of it.
- **validation pending** — the analyst or operator has stated intent to run `validate-metric` but hasn't finished yet (e.g. mid-session, or queued for a batch of outputs from one `/quarterly-cycle` run).
- **validation passed** — `validate-metric` was actually run (the manual hand-off described above) and every recomputed number matched.
- **validation failed** — `validate-metric` returned at least one FAIL; the output must not be shown to the analyst as final until the underlying issue is fixed.
- **validation passed after correction** — a FAIL was found, the underlying issue was fixed, and `validate-metric` was rerun and passed; log both the original FAIL and the correction, not just the final PASS (see the fourteenth-fix entry in `evaluation/use-log.md`, 2026-07-14, for a real example of this exact sequence).

Nothing in this workspace's output, printed JSON, a skill's conversational answer, or the dashboard, should be read as having silently passed through an automatic gate. The dashboard's "Validation" tab (`validated`/`deferred`/`rejected`) is a different, automatic, code-level check, `inspection-target-ranking`'s own statistical back-test, not `validate-metric`; the dashboard's "Verification" tab is a one-time independent re-derivation done for that snapshot's own figures, not a record that `validate-metric`'s agent role ran on every number in it. All three, the back-test gate, the verification spot-check, and `validate-metric` itself, are real and useful, but they are not the same check, and conflating them would overstate how settled any given number actually is.

## Common errors and what they mean

| Error | What it means | Fix |
|---|---|---|
| `FileNotFoundError: Source workbook not found at ...` | The workbook isn't at `data/2024_ohs-employer-record-open-data.xlsx` | Move or rename the file to that exact path |
| `error: unrecognized arguments: ROOFING` (or similar) after a positional-looking command | You passed an argument positionally where the script expects a named flag | Use the flag form shown in the table above, e.g. `--industry "ROOFING"`, not a bare quoted string |
| A ranking or trend command returns an error naming no exact match | The industry name doesn't match `WCB_INDUSTRY_NAME` exactly | Check `knowledge/data-dictionary.md` for the exact spelling rather than guessing a close name; the skills deliberately never guess a near match either |
| `employer-briefing` returns a candidate list instead of a dossier | The name you gave matches more than one `EMP_KEY` | Present the candidate list and ask which one; never pick one silently, per `knowledge/data-cautions.md` |
| Step 3 of `/quarterly-cycle` refuses to run, JSON error about `--confirmation` | No confirmation (or an empty one) was supplied | Supply the analyst's actual confirmation text or stated edits as `--confirmation`, this is required, not optional |
| A long silent pause with no output | Almost always the first workbook load in a fresh process | Expected, see the timing section above; check stderr for progress messages before assuming it's hung |
| `AttributeError: module 'script' has no attribute ...` (only relevant if modifying `_lib` scripts) | Two skill folders each ship a file literally named `script.py`; a bare `import script` is ambiguous once both are on `sys.path` | Load by explicit file path with `importlib.util.spec_from_file_location`, as `run_quarterly_steps.py` already does, never a bare `import script` |

## First end-to-end walkthrough: Roofing

1. Ask: **"How is the Roofing industry trending?"**
   The agent runs `industry-trend-briefing` on `"ROOFING"`. Expect a short wait if this is the first workbook access this session (see timing above). You should get back a year-by-year LTC/DI rate and fatality trend for 2020-2024, with `ltc_di_trend_flag` and `fatality_flag` reported separately, never merged into one verdict.
2. Ask: **"Given that, who should we target in Roofing?"**
   This runs `inspection-target-ranking`'s back test first (2020-2022 data scored, checked against 2023-2024 actual enforcement hits), then the ranking itself if the back test clears the bar. Expect the verdict (`validated`, `rejected`, or `deferred_boundary_tie`) stated explicitly, a shortlist grouped by city, and every score component shown per employer, not a bare rank.
3. Pick one employer from that shortlist and ask: **"Brief me on [employer name]."**
   This runs `employer-briefing`. Expect a one-page dossier: injury trend vs. the Roofing industry benchmark, full enforcement history with dates and source sheets, Acceptance/Approval history framed as historical record only, and a legislation hot-spot checklist for Roofing.
4. Before treating any of the above as final, run `validate-metric` manually on each draft output (see above) and log the verdict.

That's the same three-question arc (where to look, who specifically, brief me before the visit) `CLAUDE.md`'s User story brief describes, done once end to end on one real industry.
