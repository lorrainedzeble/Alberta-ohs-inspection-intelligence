# Alberta OHS Inspection Intelligence

Decision-support tooling that turns Alberta's employer-level injury and enforcement records into a governed quarterly workflow:

**[Open the live dashboard](https://lorrainedzeble.github.io/Alberta-ohs-inspection-intelligence/)** · [View the portfolio](https://lorrainedzeble.github.io/)

1. **Where should attention go?** Scan 302 industries for worsening injury trends or recent fatalities.
2. **Which employers warrant review?** Back-test and rank employers within an analyst-confirmed industry.
3. **What should an officer know before a visit?** Produce a source-cited employer briefing.

This is a portfolio project built from Government of Alberta open data. It is not affiliated with Alberta Occupational Health and Safety, and its outputs are risk signals for analyst review—not findings of non-compliance or inspection decisions.

## Why this decision matters

Alberta reported **9,801 inspections** and **5,975 re-inspections** in 2023–24. Thirty-five percent of inspections were proactive, and the ministry attributed increased activity to an operational shift toward evidence-based, intelligence-led inspection planning. Applied to the reported inspection volume, that is roughly **3,430 proactive inspections** whose targeting must coexist with a reactive workload representing the other 65%.

The public employer-records extract contains five years of injury and enforcement information across eight sheets. This workspace makes the triage repeatable while preserving the human decision point between an industry scan and employer-level ranking.

Sources: [annual report](https://open.alberta.ca/dataset/6dfd08a7-1e12-4b6b-b3c0-749d960f1143/resource/aa08e0f6-9db2-443f-aa3f-8ed5efb3c6f3/download/jet-annual-report-2023-2024.pdf), [proactive inspection program](https://www.alberta.ca/ohs-proactive-inspection-program), [Employer Records catalogue](https://open.canada.ca/data/en/dataset/a2772d8c-48be-4d39-bcf2-dafca456d724).

## What is distinctive here

- **A real governance seam.** The quarterly orchestrator refuses to proceed without a non-empty analyst confirmation and records that confirmation before ranking begins.
- **Statistical gating.** A shortlist can be called a risk ranking only when its historical back-test beats the population rate and clears a 0.05 binomial significance threshold.
- **Visible judgment.** The project refuses unsupported COR claims, public “worst offender” leaderboards, predictions of future fatalities, and current-status claims inferred from unreliable expiry dates.
- **Evaluation that changed the system.** Testing exposed double-counting, non-deterministic ties, look-ahead leakage, an over-broad tie deferral rule, incomplete schema checks, and misleading runtime claims.
- **Independent verification.** `scripts/verify_gold.py` re-derives the pinned Roofing benchmark directly from the workbook without importing workspace calculation code.
- **Refreshable source.** `scripts/refresh_data.py` resolves the current XLSX resource from the catalogue, downloads it atomically, and validates its workbook structure.

## Architecture

```text
Government open-data catalogue
          |
          v
 scripts/refresh_data.py -----> data/*.xlsx (ignored by Git)
          |
          v
 shared schema/date/join layer
          |
   +------+------+------------------+-------------------+
   |             |                  |                   |
 industry     target            employer          enforcement
 trend        ranking           briefing          effectiveness/gap
   |             |
   +------> /quarterly-cycle <---- analyst confirmation
                    |
                    v
             governed memo + use log
```

See [docs/architecture.md](docs/architecture.md) for the detailed flow and trust boundaries.

## Quick start

Requirements: Python 3.12, `pandas`, and `openpyxl`.

```powershell
git clone https://github.com/lorrainedzeble/alberta-ohs-inspection-intelligence.git
cd alberta-ohs-inspection-intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/refresh_data.py
python .claude/skills/industry-trend-briefing/script.py "ROOFING"
python scripts/verify_gold.py
```

The workbook is about 53 MB and is intentionally not committed. Its first parse can take 6–9 minutes with `openpyxl`; progress messages are written to stderr.

For conversational use, open the repository root in Claude Code and ask: **“How is the Roofing industry trending?”**

Full operating instructions are in [GETTING_STARTED.md](GETTING_STARTED.md).

## Load-bearing mechanisms

### One-place scoring weights

The ranking is transparent and deterministic:

```python
WEIGHTS = {
    "recent_ltc_count": 1.0,
    "recent_di_count": 1.0,
    "fatality_ever": 5.0,
    "unresolved_order_ever": 3.0,
    "acceptance_approval_concern": 1.0,
}
```

Every ranked result shows the component scores; the back-test decides whether the result may be described as a risk ranking.

### Code-enforced analyst checkpoint

Step 3 requires `--confirmation`. Empty confirmation returns exit code 1 before workbook access:

```python
confirmation = args.confirmation.strip()
if not confirmation:
    print(json.dumps({"error": "Step 3 refused to run: --confirmation was empty."}))
    return 1
```

The mechanism proves that confirmation text was supplied and logs it. It cannot prove that the text reflects a considered human decision.

### Positive output acceptance checklist

An output is acceptable only when all are true:

- It answers one of the three named analyst decisions.
- Every employer is identified by `EMP_KEY`, year(s), and source sheet(s).
- Every score exposes its components and weights.
- Rates under 40 person-years are explicitly marked unstable.
- Missing or ambiguous data is surfaced rather than guessed.
- Ranking language matches the back-test verdict: validated, rejected, or deferred.
- Independent verification is recorded as draft, pending, passed, failed, or passed after correction.
- The final action remains with the analyst.

## Evaluation highlights

| Check | Before | After |
|---|---:|---:|
| Quarterly-cycle verdicts | 6 validated / 9 deferred / 0 rejected | 10 validated / 4 rejected / 1 deferred |
| Ranking gate | Raw lift only | Lift plus binomial significance at 0.05 |
| Roofing 2020 person-years | 4,921.3 | 4,907.7 after `EMP_KEY` deduplication |
| Ranking reproducibility issues | 2 industries | 0 after deterministic tie-break |
| Schema-drift regression | Raw `KeyError` | Structured error naming sheet and missing columns |
| Executed failure cases | 10/11 passing initially | 11/11 after correction |

The full chronology is in [evaluation/before-after-table.md](evaluation/before-after-table.md) and [evaluation/regression-checklist.md](evaluation/regression-checklist.md).

## Data and responsible use

- The dataset is updated annually; `scripts/refresh_data.py` resolves the current XLSX rather than committing a snapshot.
- `CITY_NAME` is a WCB mailing address, not a confirmed worksite.
- Employer claim rates are indicators, not conclusive measures of safety performance.
- Acceptance/Approval status is not reliably synchronized with expiry dates.
- `COR_YEAR` and `TRADE_NAME` were empty in the evaluated 2020–2024 extract.
- The dashboard is a demonstration snapshot, not a live operational system.

Read [knowledge/data-cautions.md](knowledge/data-cautions.md) before interpreting results.

## Repository map

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Living specification and governed operating contract |
| `.claude/skills/` | Five reusable analytical capabilities |
| `.claude/commands/quarterly-cycle.md` | End-to-end workflow |
| `scripts/refresh_data.py` | Catalogue-resolved, atomic dataset refresh |
| `scripts/verify_gold.py` | Independent pinned-metric verification |
| `knowledge/` | Dictionary, cautions, profile, domain notes, opportunity framing |
| `governance/` | Automatic fails, governed language, escalation rules |
| `evaluation/` | Use log, regression checklist, before/after evidence |
| `dashboard/` | Static demonstration dashboard |

## License and attribution

Project code and original documentation are available under the [MIT License](LICENSE).

The Government of Alberta data is not included in this repository. When downloaded, it remains subject to the [Open Government Licence – Alberta](https://open.alberta.ca/licence). Attribution: Government of Alberta, *Employer Records*.
