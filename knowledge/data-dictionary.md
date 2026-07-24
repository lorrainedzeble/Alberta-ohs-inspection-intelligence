# Data Dictionary: Alberta OHS Employer Records

Source file: `data/2024_ohs-employer-record-open-data.xlsx`. Government of Alberta open data, Occupational Health and Safety Division and WCB Alberta, covering 2020 to 2024. Loaded live with `pandas.ExcelFile(path, engine="openpyxl")`, never copied into narrative docs.

A companion vendor file, `employer-records-open-data-fields.docx`, ships alongside the dataset but only documents 2 of the 8 sheets and uses field names that no longer match the live file (for example it calls the join key `EMPLOYER_OPERATION_KEY` and types it as a number; the live file calls it `EMP_KEY` and it is a GUID string). Treat the docx as background terminology only. This dictionary was built by loading the live headers directly with pandas and is the source of truth for field names.

All eight sheets join on `EMP_KEY`. `EMPLOYER_NAME` is present on every sheet but is not the join key and is not guaranteed unique or stable; always join and de duplicate on `EMP_KEY`.

This file is schema only, field names, types, and what each field means. Data quality issues and known traps live in `data-cautions.md`. Distribution and coverage numbers (how many rows, how sparse, what the value counts actually look like) live in `data-profile.md`. Domain vocabulary and formulas live in `domain-notes.md`.

## Injury (2020-2024), 841,761 rows
One row per employer per year. The fact table every other skill benchmarks against.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | not unique, display only |
| TRADE_NAME | text | completely empty in this file, 0 of 841,761 rows populated |
| CITY_NAME | text | mailing address city |
| WCB_INDUSTRY_NAME | text | WCB industry classification |
| WCB_INDUSTRY_CODE | number | WCB industry code |
| COR_YEAR | flag | intended to record whether the employer held a Certificate of Recognition that calendar year, but completely empty in this file, 0 of 841,761 rows populated. See `data-cautions.md`. |
| YEAR_NO | number | calendar year of this row, 2020 to 2024 |
| PERSON_YEARS_COUNT | number | 1 person year equals one full time worker at 2,000 hours |
| LOST_TIME_CLAIM_COUNT | number | accepted lost time claims this year |
| LOST_TIME_CLAIM_RATE | number | LTCs per 100 person years. Not meaningful under 40 person years |
| ANNUAL_FATALITY_COUNT | number | total accepted fatalities this year |
| MOTOR_VEHICLE_FATALITY_COUNT | number | subset of ANNUAL_FATALITY_COUNT |
| WORKPLACE_INCIDENT_FATALITY_COUNT | number | subset of ANNUAL_FATALITY_COUNT |
| OCCUPATIONAL_DISEASE_FATALITY_COUNT | number | subset of ANNUAL_FATALITY_COUNT |
| ANNUAL_DISABLING_INJURIES_COUNT | number | broader than lost time claims, includes modified work |
| DISABLING_INJURIES_RATE | number | DIs per 100 person years. Not meaningful under 40 person years |

## Order (2020-2024), 71,755 rows
Stop Work Orders under the OHS Act.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| ISSUE_DATE | number (Excel serial, with time fraction) | convert before use |
| LEGISLATION_CODE | text | e.g. "OHS-Code-Part-9-Section-139" |
| CONTRAVENTION | text | short label, e.g. "Fall Protection-General Protection" |
| ORDER_TYPE | text | e.g. "Stop Work Order" |
| STATUS | text | e.g. "Compliance" |

## Penalty (2020-2024), about 94 rows
Administrative penalties.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| EVENT_YEAR | number | |
| INDUSTRY_SECTOR | text | free text; verified consistent with Injury's WCB_INDUSTRY_NAME wherever both exist (0 mismatches on 80 checkable rows). Used only as a fallback for the 14 of 94 Penalty employers with no Injury row; Injury's WCB_INDUSTRY_NAME is the primary source, see `data-cautions.md` |
| SERVED_DATE | text | already formatted, e.g. "Nov 09, 2020" |
| LOCATION | text | city |
| NATURE_OF_VIOLATION | text | free text, not surfaced in any skill |
| AMOUNT | text | dollar string, e.g. "$5,000"; strip formatting before summing |

## Ticket (2020-2024), about 76 rows
OHS violation tickets.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| OFFENCE_DATE | number (Excel serial, with time fraction) | convert before use |
| TICKETABLE_PROVISION | text | full legislative text, free text, not surfaced in any skill |
| AMOUNT | number | dollar amount |

## Investigation (2020-2024), about 91 rows
Published investigation reports. No date column at all.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| DESCRIPTION | text | short summary, e.g. "Worker fatally injured at landfill site" |
| URL | text | link to published report |

Because there is no date field, this sheet can only be used as a binary "ever investigated" flag. It cannot support any "in the last N years" windowed logic. This is a hard constraint, not a simplification; do not approximate a date from context.

## Acceptance (2020-2024), 909 rows across 234 employers, and Approval (2020-2024), 253 rows across 83 employers
Ministerial acceptances and approvals under specific OHS Code sections, a different regulatory instrument from COR or from enforcement (Order/Penalty/Ticket/Conviction). Used narrowly: as historical context in `employer briefing`, and as one supplementary signal in `inspection target ranking`. Never used to claim an instrument is currently active or about to lapse; see `data-cautions.md` for why.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| ISSUE_DATE | number (Excel serial) | when the instrument was granted |
| EXPIRY_DATE | number (Excel serial) | the instrument's original scheduled term end. Not reliable as a "still valid" signal, see cautions |
| DESCRIPTION | text | a status field, not narrative: one of Issued, Expired, Revoked, Denied, Suspended, Amended/Varied |
| APPLICABLE_LEGISLATION | text | OHS Code section the instrument was granted under |

## Conviction (2020-2024), about 167 rows
Court convictions under the OHS Act.

| Field | Type | Notes |
|---|---|---|
| EMP_KEY | text (GUID) | join key |
| EMPLOYER_NAME | text | |
| INCIDENT_DATE | text | already formatted, e.g. "Jan 13, 2021" |
| DATE_OF_CONVICTION | text | already formatted |
| INCIDENT_TYPE | text | e.g. "Fatality" |
| OFFENCE_LOCATION | text | |
| DESCRIPTION | text | long narrative, not surfaced in any skill; contains legacy text encoding artifacts (stray characters where apostrophes should be) |
| CONTRAVENTION | text | long narrative including fines and sentencing detail, not surfaced in any skill |
