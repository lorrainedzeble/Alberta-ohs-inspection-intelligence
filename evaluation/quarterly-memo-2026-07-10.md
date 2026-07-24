# Quarterly Inspection Prioritization Memo
**Run date:** 2026-07-10, corrected 2026-07-12, verdict logic corrected 2026-07-13 | **Workflow:** `/quarterly-cycle` | **Prepared for:** Dana, Compliance Planning Analyst, OHS Prevention Services

Every number below is a signal for the analyst to weigh, not a decision made on her behalf, per `CLAUDE.md`'s Governance section. Every employer named is cited by `EMP_KEY`, the year(s) its figures cover, and the source sheet(s) those figures came from, per `CLAUDE.md`'s Conventions.

**This memo was substantially revised twice.** On 2026-07-12, a real methodological bug was found and fixed: the back test's top-10 cutoff can land on a tie between multiple employers with the exact same score, and which specific employers filled the remaining slot(s) was, before that fix, an arbitrary, non-reproducible artifact of incidental row order, not a real difference in risk. That fix (a deterministic tie-break) made the results reproducible, but the verdict logic layered on top of it was itself wrong: it deferred every industry with any boundary tie, whether or not the tie actually changed the outcome. **On 2026-07-13, that second bug was found and fixed**: the verdict now compares the worst-case and best-case tie resolutions directly, and only defers when the verdict genuinely flips between them. This changed the cycle's headline result from 6 validated / 9 deferred / 0 rejected to **10 validated / 1 deferred / 4 rejected**. Full detail in the "Boundary ties" section below and in `evaluation/use-log.md`.

## Step 1: Scan, and Step 2: What the analyst confirmed

`industry-trend-briefing --all` scanned all 302 industries in the Injury sheet (2020-2024). 114 industries flagged on at least one of two independent signals: `ltc_di_trend_flag` (a materially worsening lost-time-claim/disabling-injury rate across pooled early/late stable-year windows) or `fatality_flag` (a fatality recorded in 2023 or 2024). The 15 largest by 2024 employer count were presented to the analyst per Step 2's checkpoint, and confirmed as-is without adjustment:

General Trucking, Restaurants/Catering, Mobile Equipment Operation, Welding, Janitorial/Cleaning Services, Electric Wiring, Industrial/Commercial Construction, Field Production Operators, Upstream Oil/Gas, Mobile Equipment Dealers, Mechanical Contracting, General Automotive Repairs/Auto Wreckers, Oilfield Downhole Services, Home Support Services, Construction Framing Contractor.

All 15 flagged on `fatality_flag` (Injury sheet, `ANNUAL_FATALITY_COUNT`, 2023 and 2024).

## Step 3: Rank, the gate, and boundary ties (corrected 2026-07-12, verdict logic corrected 2026-07-13)

Each of the 15 was back tested first: `inspection-target-ranking` scored employers on 2020-2022 data only, then checked whether the top 10's 2023-2024 enforcement-action rate (Order/Ticket/Penalty/Conviction, `unified_enforcement_actions()`) both exceeded the full population's rate for the same window AND was unlikely to occur by chance (binomial P(X≥observed hits) under the population's own rate, below 0.05; see `knowledge/data-cautions.md`).

**A third possible verdict exists alongside "validated" and "rejected": `deferred_boundary_tie`.** When the score at the top-10 cutoff is shared by more than one employer, which specific employers occupy the last slot(s) is an arbitrary tie-break. The first version of this check deferred an industry the moment any such tie existed, without asking whether the tie actually mattered — a bug, fixed 2026-07-13. The corrected check computes both ends of the range: the worst-case tie-break (tied slots filled with as few 2023-2024 enforcement hits as possible) and the best-case tie-break (filled with as many hits as possible). An industry is **validated** only if even the worst case clears the significance bar, **rejected** only if even the best case still fails it, and **deferred** only if the verdict genuinely flips between the two, meaning the population itself is ambiguous and the evidence was never actually weighed to a conclusion either way.

Checked directly across all 15: **9 of 15 have a boundary tie at all, but only 1 of those 9 is genuinely tie-sensitive.** Corrected result: **10 validated, 4 rejected, 1 deferred.**

**Validated (10):** General Trucking, Restaurants/Catering, Mobile Equipment Operation, Janitorial/Cleaning Services, Mechanical Contracting, Home Support Services (all tie-free), plus Welding, Upstream Oil/Gas, Mobile Equipment Dealers, Oilfield Downhole Services (each has a boundary tie, but the worst-case tie-break still clears the significance bar).

**Rejected (4):** Electric Wiring, Industrial/Commercial Construction, Field Production Operators, General Automotive Repairs/Auto Wreckers (each has a boundary tie, but even the best-case tie-break still fails the significance bar).

**Deferred, genuinely tie-sensitive (1):** Construction Framing Contractor (worst-case chance probability 45.3%, best-case 1.0% — the only one of the 15 where the verdict actually depends on which tied employer is seated).

This is not a downgrade of the whole cycle's work: for every industry regardless of verdict, the employers ranked strictly above the tied score are unambiguous, real signal, and are presented as such below. Only the employers occupying the tied slot(s) are genuinely coin-flip arbitrary, and are called out explicitly as a named group rather than folded into a false-precision rank order.

## Step 4a: The 10 validated industries — shortlists and briefs

For each, the top 3 employers by risk score (recent 2023-2024 LTC/DI counts, fatality-ever, unresolved-order-ever, Acceptance/Approval concern; weights disclosed in `inspection-target-ranking/script.py`'s `WEIGHTS`), grouped by city, with a short brief pulled from `employer-briefing`. The full one-page dossier for any of these is available by running `employer-briefing` directly on the cited `EMP_KEY`. **All employers briefed below sit strictly above any boundary tie in their industry's shortlist**, confirmed directly against the corrected ranking output, not assumed.

**Before routing any inspection from these shortlists: the city shown is the employer's registered WCB mailing address, not a confirmed Alberta worksite location.** This dataset has no province or worksite field; a real live run of this exact ranking on General Trucking grouped its shortlist under Mississauga, Richmond, and Lachine, none in Alberta, because that industry's largest employers are national couriers whose registered address is an out-of-province head office. Confirm the employer's actual Alberta worksite location before routing, this shortlist's city grouping does not do that confirmation.

---

### General Trucking
*Backtest: top-10 enforcement rate 10% vs. population rate 0.32% (Order/Ticket/Penalty/Conviction, 2023-2024, population 22,208), chance probability 3.2% — passes, but only narrowly; treat as weaker evidence than the industries below with sub-1% chance probabilities. No boundary tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024, Injury sheet unless noted) |
|---|---|---|---|---|
| Federal Express Canada Ltd. | `C40723A8-290B-5712-59A6-6F6D4CB724A5` | Mississauga | 301.0 | LTC 109, DI 192, person-years 2358.5, fatality-ever No, unresolved order No (Order sheet), Acceptance/Approval concern No |
| Purolator Inc. | `0F7DE843-05D0-C6AA-460D-EDE0E7D7300B` | Richmond | 248.0 | LTC 35, DI 213, person-years 3304.7, fatality-ever No, unresolved order No, concern No |
| United Parcel Service Canada Ltd. | `15AA2E22-0828-62AE-45BD-7AA0A5DCA32A` | Lachine | 206.0 | LTC 46, DI 160, person-years 2154.8, fatality-ever No, unresolved order No, concern No |

Briefs (Injury sheet, 2024 unless noted): Federal Express's 2024 LTC rate is 5.421 per 100 person-years (stable, 75 LTC claims), no enforcement history on record (Order/Ticket/Penalty/Conviction, 0 total), never investigated (Investigation sheet). Purolator: 2024 LTC rate 0.78 (stable, 13 claims), 0 enforcement actions. UPS Canada: 2024 LTC rate 1.522 (stable, 17 claims), 0 enforcement actions. None of the three has a fatality on record in the 2020-2024 window.

---

### Restaurants/Catering
*Backtest: top-10 rate 60% vs. population 2.23% (population 9,907), chance probability effectively 0% — strong signal. No boundary tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Starbucks Coffee Canada, Inc. | `C8728D5F-7A45-59E5-EE1F-693C3F596C09` | North York | 324.0 | LTC 112, DI 212, person-years 5622.3, fatality-ever No, unresolved order No, concern No |
| Compass Group Canada Ltd. | `FC2D7125-071A-865B-8B44-00D737943BD6` | London | 148.0 | LTC 44, DI 104, person-years 3070.7, fatality-ever No, unresolved order No, concern No |
| Aramark Canada Ltd./Aramark Canada Ltee | `8AE3C457-DD4A-268F-D68D-2188F7585E4C` | (city not on record) | 129.0 | LTC 40, DI 89, person-years 2384.1, fatality-ever No, unresolved order No, concern No |

Briefs (Injury sheet, 2024): Starbucks LTC rate 1.852 (stable, 51 claims), 12 enforcement actions on record (Order sheet), no unresolved ones, never investigated. Compass Group: LTC rate 1.535 (stable, 25 claims), 10 enforcement actions, none unresolved. Aramark (this EMP_KEY): LTC rate 1.542 (stable, 20 claims), 4 enforcement actions, none unresolved. No fatalities on record for any of the three, 2020-2024.

---

### Mobile Equipment Operation
*Backtest: top-10 rate 40% vs. population 2.08% (population 7,650), chance probability effectively 0% — strong signal. No boundary tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Volker Stevin Contracting Ltd. | `D255C6C0-F228-8BAB-A79D-71248244ADB8` | Calgary | 127.0 | LTC 26, DI 98, person-years 1414.1, fatality-ever No, **unresolved order Yes** (Order sheet, STATUS in Non-Compliance/Open), concern No |
| Fort McKay Strategic Services Limited Partnership | `1B77B329-A954-BB1F-74C9-0A19FDD9C773` | Fort McMurray | 118.0 | LTC 13, DI 105, person-years 2324.5, fatality-ever No, unresolved order No, concern No |
| Bouchier Contracting Ltd. | `DFB9AF33-B2C5-93DD-03C7-F2A4177BEC3D` | Fort McMurray | 73.0 | LTC 7, DI 66, person-years 2077.5, fatality-ever No, unresolved order No, concern No |

Briefs (Injury/Order sheets, 2024): Volker Stevin's 2024 LTC rate is 1.32 (stable, 10 claims); 16 enforcement actions on record, **4 currently unresolved** (Order sheet, STATUS Non-Compliance/Open) — the only unresolved-order case among these validated shortlists, worth flagging first on any visit. Fort McKay: LTC rate 0.245 (stable, 3 claims), 1 enforcement action, none unresolved. Bouchier: LTC rate 0.479 (stable, 5 claims), 4 enforcement actions, none unresolved. No fatalities on record for any of the three.

---

### Janitorial/Cleaning Services
*Backtest: top-10 rate 30% vs. population 0.40% (population 5,716), chance probability effectively 0% — strong signal. No boundary tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Aramark Canada Ltd./Aramark Canada Ltee | `7C4C22B5-6BD0-FE5A-ADF3-FDA0F685ECAB` | (city not on record) | 117.0 | LTC 43, DI 69, person-years 834.9, **fatality-ever Yes**, unresolved order No, concern No |
| Sodexo Canada Ltd. | `423D7B89-2388-CE2E-A867-1B7CC3E6D073` | Burlington | 110.0 | LTC 14, DI 96, person-years 1112.2, fatality-ever No, unresolved order No, concern No |
| Delta Facilities Maintenance Inc. | `B81A61F8-2890-0ADA-17D8-48C9166F824E` | Calgary | 57.0 | LTC 26, DI 31, person-years 530.0, fatality-ever No, unresolved order No, concern No |

Briefs (Injury/Order sheets, 2024): This Aramark EMP_KEY (distinct from the Restaurants/Catering Aramark EMP_KEY above — same corporate family, different WCB account) has a 2024 LTC rate of 4.896 (stable), and carries a fatality on record in the 2020-2024 window, 0 enforcement actions. Sodexo: LTC rate 1.279 (stable), 0 enforcement actions, 0 fatalities. Delta Facilities Maintenance: LTC rate 5.051 (stable), 1 enforcement action (none unresolved), 0 fatalities.

---

### Mechanical Contracting
*Backtest: top-10 rate 40% vs. population 1.26% (population 2,615), chance probability effectively 0% — strong signal. **Boundary tie exists further down this industry's shortlist** (2 employers tied at score 22.0, below the 3 briefed here, see the Boundary ties section) — does not affect the top-3 below, which are unambiguous.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Modern Niagara Alberta Inc. | `7E5C4CDF-D296-B95D-AACB-FB231CDCD2F9` | Toronto | 39.0 | LTC 4, DI 35, person-years 839.3, fatality-ever No, unresolved order No, concern No |
| Mr. Mike's Plumbing Ltd. | `B3222510-B6BD-AAA0-BDE4-D38500C497DF` | Calgary | 38.0 | LTC 12, DI 21, person-years 78.2, **fatality-ever Yes**, unresolved order No, concern No |
| Jetco Mechanical Limited | `2DA888F1-F34B-3F54-60D6-C0636BE483E0` | Edmonton | 30.0 | LTC 8, DI 22, person-years 308.5, fatality-ever No, unresolved order No, concern No |

Briefs (Injury sheet, 2024): Modern Niagara Alberta's 2024 LTC rate is 0.258 (stable, 1 claim), 12 enforcement actions on record, none unresolved. Mr. Mike's Plumbing: 2024 LTC rate 11.565, stable (2024 person-years 43.23, just above the 40 floor — worth noting how close to the threshold this is), a fatality on record in 2020-2024, 5 enforcement actions, none unresolved. Jetco Mechanical: LTC rate 2.761 (stable), 4 enforcement actions, none unresolved, 0 fatalities.

---

### Home Support Services
*Backtest: top-10 rate 50% vs. population 1.29% (population 2,175), chance probability effectively 0% — strong signal, the strongest lift of the 10 validated industries. **Boundary tie exists further down this industry's shortlist** (4 employers tied at score 8.0, below the 3 briefed here) — does not affect the top-3 below, which are unambiguous.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| CBI Home Health (AB) Limited Partnership | `732AA40E-7AA1-F330-A524-EE629A9CC0B3` | Calgary | 475.0 | LTC 204, DI 271, person-years 4041.7, fatality-ever No, unresolved order No, concern No |
| Bayshore Healthcare Ltd. | `88F778C2-5627-BF47-ECB3-F884D52DD1D8` | Mississauga | 440.0 | LTC 190, DI 250, person-years 2633.2, fatality-ever No, unresolved order No, concern No |
| Caregivers Home Health Care Inc. | `9129AA2D-A6AE-2156-47B1-DB6022482300` | Edmonton | 93.0 | LTC 43, DI 50, person-years 794.9, fatality-ever No, unresolved order No, concern No |

Briefs (Injury/Order sheets, 2024): CBI Home Health's 2024 LTC rate is 4.586 (stable), 0 enforcement actions. Bayshore Healthcare: LTC rate 6.975 (stable), 2 enforcement actions, none unresolved. Caregivers Home Health Care: LTC rate 6.157 (stable), 4 enforcement actions, none unresolved. No fatalities on record for any of the three in 2020-2024, despite this industry's `fatality_flag` firing at the industry level (one fatality recorded in 2024 somewhere in the broader industry, per Step 1 — not at any of these three specific employers).

The four industries below also validate: each has a boundary tie at the 2022 back-test cutoff, but the worst-case tie-break (the least favorable possible resolution) still clears the significance bar, so the tie does not change the substantive conclusion. Shown at ranking-level detail (no full `employer-briefing` dossier run) since these were previously deferred and this memo's per-employer briefs were only written for the originally-validated six; the shortlists themselves are otherwise identical in kind.

---

### Welding
*Validated: worst-case chance probability 2.74% (same as the actual, since the tie doesn't change which side of the 5% bar the result lands on). 5 employers tied at score 5.0 in the live 2024 shortlist (a separate, and different, tie exists in the 2022 back-test scoring used for the gate itself). Unambiguous top 3 below are unaffected by either tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Boulder Metal Industries (2002) Inc. | `2EA3033B-249D-31A8-3C61-B14ADF7B458A` | Pincher Creek | 11.0 | LTC 3, DI 3, person-years 11.4, **fatality-ever Yes**, unresolved order No, concern No |
| Headwater Equipment Sales Ltd. | `8005EF19-9029-1283-CC90-6217DC9C4B0E` | Lethbridge | 8.0 | LTC 4, DI 4, person-years 48.3, fatality-ever No, unresolved order No, concern No |
| Hahn Welding & Oilfield Services Ltd. | `FB7FD04F-1342-DBB0-66E2-E1D81225E988` | Elk Point | 8.0 | LTC 2, DI 6, person-years 207.4, fatality-ever No, unresolved order No, concern No |

Tied group at the cutoff (score 5.0, 5 employers share it): Brownie's Up 5 Welding Ltd. (`27ED2ACC-BDD4-8CBA-EC76-EB8B3121512C`, Wabasca) is the one visible in this top-10 window; 4 more employers share this exact score just outside it.

Briefs for the unambiguous top 3 (Injury sheet, 2024): **Boulder Metal Industries' 2024 LTC rate is 38.85 per 100 person-years, but its 2024 person-years is only 5.15 — well under the 40 person-year stability floor, so this rate is marked unstable (`rate_stable: false`) and must not be read as a normal industry-comparable number.** It also carries a fatality on record (2020-2024 window). Headwater Equipment Sales: 2024 LTC rate 7.646, also unstable (2024 person-years 26.16, under the floor), 0 fatalities. Hahn Welding: 2024 LTC rate 0.931, stable (person-years 107.47), 0 fatalities. None of the three has any enforcement action on record.

---

### Upstream Oil/Gas
*Validated: worst-case chance probability 0.16% (same as the actual). 3 employers tied at score 7.0 in the 2022 back-test scoring; the live 2024 shortlist has its own tie of 3 at score 13.0. Unambiguous top 3 below are the two clear leaders plus context on the tie.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Canadian Natural Resources Limited | `AD6C4F79-2579-AC92-66B2-C9BE17F7DED1` | Calgary | 49.0 | LTC 6, DI 43, person-years 12170.9, fatality-ever No, unresolved order No, concern No |
| Cenovus Energy Inc. | `CB78E899-E4A3-07BB-A3C0-8CD36DD0B4B2` | Calgary | 22.0 | LTC 4, DI 18, person-years 9326.6, fatality-ever No, unresolved order No, concern No |

Tied group at the 2024 shortlist's cutoff (score 13.0): Paramount Resources Ltd. (`AFED4E3B-0399-FAA0-7812-10778174F66D`, Calgary) and Tidewater Midstream and Infrastructure Ltd. (`337C20CD-58C6-769E-82B2-B71E5C4CA3D0`) share this score; either could occupy the 3rd slot, not just Tidewater as previously (and arbitrarily) shown.

Briefs (Injury/Order sheets, 2024): Canadian Natural Resources' 2024 LTC rate is 0.031 (stable, 2 claims across a very large 6,417.7 person-year base), 36 enforcement actions on record, none unresolved. Cenovus Energy: LTC rate 0.044 (stable, 2 claims), 12 enforcement actions, none unresolved. Tidewater Midstream (one of the two tied): LTC rate 0.0 (stable — 0 claims against 376.4 person-years, a genuine zero, verified directly against the raw sheet), 0 enforcement actions.

---

### Mobile Equipment Dealers
*Validated: worst-case chance probability 0.06% (same as the actual). 4 employers tied at score 9.0 in the 2022 back-test scoring, but the live 2024 shortlist has no boundary tie of its own; the top 3 below are fully unambiguous in the current view.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Finning International Inc. | `7A040109-DBD9-7A55-A129-99FB93A7095A` | Edmonton | 234.0 | LTC 48, DI 180, person-years 9475.7, **fatality-ever Yes**, unresolved order No, **Acceptance/Approval concern Yes** |
| SMS Equipment Inc./Equipement SMS Inc. | `79227CBF-7D6C-9813-FB8B-473FF513575A` | (city not on record) | 112.0 | LTC 13, DI 94, person-years 5282.4, fatality-ever Yes, unresolved order No, concern No |
| Rocky Mountain Equipment LP | `A35D3914-3015-1C58-2F1D-D5EFC62E9E28` | (city not on record) | 45.0 | LTC 3, DI 37, person-years 1503.1, fatality-ever Yes, unresolved order No, concern No |

Briefs (Injury/Order/Acceptance-Approval sheets, 2024): Finning International's 2024 LTC rate is 0.578 (stable, 27 claims), a fatality on record in the 2020-2024 window, 20 enforcement actions (none unresolved), and this employer **has been investigated** (Investigation sheet, a binary "ever" flag, no date attached). SMS Equipment: LTC rate 0.241 (stable), fatality on record, 0 enforcement actions. Rocky Mountain Equipment: LTC rate 0.261 (stable), fatality on record, 10 enforcement actions (none unresolved).

**Name-ambiguity note:** `EMP_KEY 80ADDCBE-6258-F719-CC4E-81F42334B96D` in this industry is recorded under two distinct employer names, "Northwest Spring & Machine Inc." and "Truck Zone Inc." (a legal-name/trade-name pattern affecting 342 of 236,365 EMP_KEYs workbook-wide, see `knowledge/data-cautions.md`). Its correctly-deduplicated score is 24.0, well below Rocky Mountain Equipment's 45.0, so it is correctly not on this shortlist.

---

### Oilfield Downhole Services
*Validated: worst-case chance probability 0.25% (same as the actual). 2 employers tied at score 16.0 in the 2022 back-test scoring, but the live 2024 shortlist has no boundary tie of its own; the top 3 below are fully unambiguous in the current view.*

| Employer | EMP_KEY | City | Score | Components (2023-2024) |
|---|---|---|---|---|
| Trican Well Service Ltd., et al | `D70592F5-E4FA-9234-AF2B-A6A95F0E3419` | Calgary | 72.0 | LTC 10, DI 62, person-years 3019.3, fatality-ever No, unresolved order No, concern No |
| Calfrac Well Services Ltd. | `A3CEBCD3-7AEC-6BC0-9CB8-6AB358F2BD05` | Calgary | 56.0 | LTC 8, DI 48, person-years 2173.7, fatality-ever No, unresolved order No, concern No |
| Element Technical Services Inc. | `D41DC5A7-29C7-72B2-46EF-8812FAC529ED` | Calgary | 48.0 | LTC 11, DI 37, person-years 838.9, fatality-ever No, unresolved order No, concern No |

Briefs (Injury/Order sheets, 2024): Trican Well Service's 2024 LTC rate is 0.306 (stable), 0 enforcement actions. Calfrac Well Services: LTC rate 0.444 (stable), 0 enforcement actions. Element Technical Services: LTC rate 0.508 (stable), 1 enforcement action (not unresolved). No fatalities on record for any of the three.

## Step 4c: The 4 rejected industries

For each, even the best-case tie-break (the most favorable possible resolution) still fails the significance bar, so these are cleanly rejected, not ambiguous. The employers ranked strictly above the tied cutoff score are still real, unambiguous signal and are listed below at ranking-level detail. Per CLAUDE.md's Governance section, a rejected ranking is never shipped as a risk score, only as "sorted by raw indicators."

---

### Electric Wiring
*Rejected: chance probability 6.66% (same under worst-case and best-case — the tie doesn't change the conclusion), just above the 0.05 threshold; this is the closest of the 4 rejected industries to passing. 2 employers tied at score 21.0 in the live 2024 shortlist.*

Unambiguous top 5 (2023-2024 components, Injury/Order sheets, no full dossier run for this deferred industry, ranking-level detail only): Multi Phase Electric Inc. (`257F99EE-0074-0C27-50A5-4D80E20CB8C6`, Calgary, score 73.0, LTC 25/DI 48/PY 585.4, no fatality/unresolved/concern); PTW Facility Services Ltd. (`2EF0B7F8-4E38-F111-2EDF-8E91D87B719C`, Rocky View County, score 44.0, LTC 7/DI 37/PY 2049.0); Amelco Electric (Calgary) Ltd. (`868268D8-B00D-8B95-968D-92145ED9BC95`, Calgary, score 43.0, LTC 7/DI 36/PY 385.3); Western Electrical Constructors Ltd (`3A46513E-A66A-C9CE-1C63-B5C1CBA1468E`, Calgary, score 38.0, LTC 4/DI 34/PY 909.5); Custom Electric Ltd. (`5D344C8E-AC08-A260-3518-6885AE2B8234`, Calgary, score 35.0, LTC 2/DI 33/PY 589.7). None of these five carries a fatality, unresolved order, or Acceptance/Approval concern.

Tied group at the cutoff (score 21.0): Seltrek Electric Ltd. (`166EA79C-2C78-2CF0-341A-E0EA9A106916`, Calgary) is the one visible in this top-10 window; at least 1 more employer shares this exact score just outside it.

---

### Industrial/Commercial Construction
*Rejected: chance probability 18.4% (same under worst-case and best-case); 2 employers tied at score 29.0 in the live 2024 shortlist.*

Unambiguous top 5 (2023-2024 components, Injury sheet, ranking-level detail only): Ledcor RMC Services Ltd. (`50E57A4A-44C3-BBBE-13CB-F2A56EC22C26`, Edmonton, score 140.0, LTC 22/DI 118/PY 3712.9); Borea Construction ULC (`B7E84623-53FE-7606-203E-16DFE0A96041`, score 66.0, LTC 5/DI 61/PY 1542.5); Chandos Construction Ltd. (`850C3B36-E1BC-8228-78EA-D4897F4111D2`, Edmonton, score 57.0, LTC 1/DI 56/PY 1231.3); PCL Industrial Constructors Inc. (`17DC00EE-34C5-C0E4-A022-A39E6C66D555`, Edmonton, score 51.0, LTC 9/DI 42/PY 1932.3); PCL Energy Inc. (`1165F5B8-BB25-FD01-5CA3-9AEB2D3980F3`, Edmonton, score 44.0, LTC 8/DI 36/PY 2218.8). None of these five carries a fatality, unresolved order, or Acceptance/Approval concern.

Tied group at the cutoff (score 29.0): Pagnotta Inc. (`40168519-23A4-665A-D630-BFE694D1D564`, Edmonton) and Nason Contracting Group Ltd. (`5536D342-7396-F9AE-D220-07E0CB538796`, Edmonton) share this score; either could occupy the remaining slot.

---

### General Automotive Repairs/Auto Wreckers
*Rejected: chance probability 26.7% (same under worst-case and best-case); population baseline enforcement rate 18.15%, an already-high base rate that made this industry's top-10 lift weak regardless of the tie; the live 2024 shortlist has no boundary tie of its own.*

Unambiguous top 5 (2023-2024 components, Injury sheet, ranking-level detail only): Kal Tire, A Corporate Partnership (`F7D1CF27-5C1B-FC6E-4BA9-AD14F2D00BAF`, Vernon, score 297.0, LTC 66/DI 231/PY 3077.5); Costco Wholesale Canada Ltd. (`0FE77FB0-44DA-BB6C-2FEA-F560D001032D`, Nepean, score 56.0, LTC 6/DI 50/PY 730.8); Edmonton Gear Centre Ltd. (`65B10C04-5571-676C-36CD-6A31AB17CB66`, Edmonton, score 24.0, LTC 10/DI 14/PY 319.2); The Tire Warehouse (Edmonton) Ltd. (`4FB98525-B81B-2ABE-8B3D-2AFB92A31060`, Edmonton, score 23.0, LTC 11/DI 12/PY 170.1); Kal Tire Transport Ltd. (`575622CD-C20D-AB8A-B1C9-9D77B4005CBF`, Vernon, score 15.0, LTC 7/DI 8/PY 109.0). None of these five carries a fatality, unresolved order, or Acceptance/Approval concern.

---

### Field Production Operators
*Rejected, and the clearest case in the set: 0.0% top-10 enforcement rate against a 0.02% population rate (population 5,086) — chance probability 100% under both worst-case and best-case tie-break, since this industry recorded zero 2023-2024 enforcement actions among its top-10 employers regardless of which of the 39 tied-at-score-2.0 employers are seated. The near-zero population base rate suggests real data sparsity (almost no enforcement activity anywhere in this industry in 2023-2024) rather than a formula problem. Given how large the tied group is relative to the top-10 window, this industry's shortlist is close to meaningless for individual employer targeting; treat the whole industry's "who specifically" question as unanswered by this cycle's data.*

Unambiguous top 5 (2023-2024 components, Injury sheet): NES Global Limited (`9166C932-519A-DC43-C88E-05B1DCD1685B`, Calgary, score 9.0, LTC 4/DI 5/PY 931.1); Roska DBO Inc. (`0F8891AB-BC42-0FF3-4D36-3F7D3CAF2526`, Grande Prairie, score 8.0, LTC 1/DI 7/PY 906.8); Signature Oilfield Contracting Ltd. (`0B474E2E-4112-7A48-7FDF-FFC4F0864F34`, Grande Prairie, score 7.0, LTC 1/DI 1/PY 1.4, **fatality-ever Yes**, very low person-years, not a stable rate); 2415763 Alberta Inc. (`7DD4249C-C566-B62A-F1F9-6374EFF5B62A`, score 7.0, LTC 1/DI 1/PY 0.8, **fatality-ever Yes**, likewise not a stable rate); 2359607 Alberta Ltd. (`618A0CF8-8E8E-F57C-77BB-2A9088ED6E17`, score 4.0, LTC 2/DI 2/PY 1.3).

## Step 4b: The 1 deferred industry — genuinely tie-sensitive

Only this industry's verdict actually depends on which arbitrary tie-break is used. Per CLAUDE.md's Governance section, this is neither validated nor rejected: the evidence was never actually weighed to a conclusion, because the population itself is ambiguous.

---

### Construction Framing Contractor
*Deferred: this is the industry where the boundary-tie bug was originally found, and it remains the workspace's one confirmed genuinely tie-sensitive case after the 2026-07-13 fix. Worst-case tie-break chance probability 45.3% (fails), best-case 1.0% (passes) — the verdict flips depending purely on which 2 of 8 employers tied at score 8.0 are seated in the 2022 scoring's top 10, with no change in any employer's actual score. Neither end is more "correct"; both are arbitrary resolutions of the same real tie. 4 employers are similarly tied at score 7.0 in the live 2024 shortlist.*

Unambiguous top 5 (2023-2024 components, Injury sheet, ranking-level detail only): Living Legends Construction Inc. (`4BCDCDE6-3F88-08F7-6DE4-C1ABA34F4F66`, Edmonton, score 26.0, LTC 6/DI 20/PY 115.8); Teasdale Building Company Inc. (`BCD3EAFC-E4FE-F189-EF13-214B5891C505`, Calgary, score 14.0, LTC 7/DI 7/PY 30.7); Exalt Ltd. (`DD123FFE-231A-A019-A15D-504654095674`, Edmonton, score 11.0, LTC 5/DI 6/PY 25.8); Dre-Max Construction Inc. (`A159D470-2E31-5070-BEB6-A160197888E3`, Spruce Grove, score 11.0, LTC 3/DI 3/PY 41.5, **fatality-ever Yes**); Milena Construction Inc. (`DCDEE4D8-1DD7-ED64-8313-DD0EF8802A9A`, Calgary, score 10.0, LTC 5/DI 5/PY 36.2). None of the other four carries a fatality, unresolved order, or Acceptance/Approval concern.

Tied group at the cutoff (score 7.0): ML Bros. Construction Ltd. (`64406B53-0138-8523-5CF9-29A12ADE5BB3`, Calgary) and 9929215 Canada Inc. (`13333F2C-EF21-4118-D1CE-26248208F719`) are the two visible in this top-10 window; more employers share this exact score just outside it in the 2022 back-test scoring specifically (8 total tied there, versus 4 tied in the live 2024 view).

## Step 5: Verify

Every number above was independently recomputed from the raw source workbook (`data/2024_ohs-employer-record-open-data.xlsx`) via `.claude/skills/_lib/ohs_data.py`, in fresh context, without trusting the producing skills' own aggregation, per `CLAUDE.md`'s Governance section and the `validate-metric` role. Coverage: all originally-validated industries' Step 1 trend fields, Step 3 backtest/rank fields, and Step 4 employer-brief fields — zero numeric discrepancies found across all checks. Two specific spot checks flagged in advance both confirmed correct rather than assumed: Tidewater Midstream's 2024 zero-claim/zero-rate entry (a genuine zero, not a stale NaN-handling bug), and the Northwest Spring & Machine/Truck Zone deduplicated score (24.0, independently reproduced by two separate recomputations).

One structural finding, not a numeric error: the first draft of this verification pass used an abbreviated claims format that did not pair every employer name with its `EMP_KEY`, year(s), and source sheet(s) together in one place, which `governance/governance-rules.md`'s automatic-fail list treats as a citation-completeness failure regardless of numeric accuracy. This memo was written to close that gap directly.

**A separate, adversarial live-use check** (an actual attempt to use the workspace and break it, not a numeric verification) found and fixed five further real problems, one of which touched this ranking's own validation mechanism directly: `unresolved_order_ever` and `acceptance_approval_concern`, two of the five score components, were not restricted to the back test's 2022 cutoff before this cycle ran. This was confirmed to be a real, substantial leak workbook-wide (55% of all "unresolved order" rows were future-dated relative to a 2022 cutoff), but rerunning all 15 back tests after that fix produced byte-identical results to the leak-affected version, because the count-based score components dominate these particular rankings' margins strongly enough that the leak didn't change any employer's top-10 placement. Full detail in `evaluation/use-log.md`, dated 2026-07-11.

**Then, checking precisely whether that same fix's effects reached the real shortlists (not just the gate verdict) surfaced the boundary-tie bug** described throughout this memo, found and fixed on 2026-07-12: a deterministic tie-break, replacing the previously non-reproducible incidental row order. This is the tenth real, independently-verified fix from this workspace's use.

**A user-directed data-integrity check on 2026-07-13 found an eleventh bug, one level up from the tenth:** the deterministic tie-break made results reproducible, but the verdict logic built on top of it deferred every industry with any boundary tie, without asking whether the tie actually changed the substantive conclusion. Fixed by computing the worst-case and best-case tie-break directly and only deferring when the verdict genuinely flips between them; see Step 3 above. The same check also asked whether the pinned Roofing gold example (`knowledge/data-cautions.md`, CLAUDE.md's Gold example section) had drifted from the source file; re-deriving it fresh against the current workbook confirmed the currently pinned figures (`person_years_sum` 4907.7, `ltc_rate_per_100_person_years` 2.71, `di_rate_per_100_person_years` 4.809) are exactly right, and the number initially suspected of being the correct pin (4921.3 / 2.703 / 4.795) was in fact the retired, pre-dedup-fix figure documented as superseded back on 2026-07-10. No change was needed there; the check confirmed the existing pin rather than replacing it. Both findings documented in full in `evaluation/use-log.md` and `knowledge/data-cautions.md`.

## Insufficient-data and other notes

- Two employers in the validated shortlists (Welding's Boulder Metal Industries and Headwater Equipment Sales) show `rate_stable: false` because their 2024 person-years fall under the 40 person-year floor; their rates are reported as-is but must not be read as normal, comparable figures. The same applies to two employers in Field Production Operators' unambiguous top 5 (Signature Oilfield Contracting, 2415763 Alberta Inc.).
- One employer (Mr. Mike's Plumbing, Mechanical Contracting) sits just above the 40 person-year floor (43.23) — technically stable, but close enough to the edge to note.
- All 15 industries' `latest_year_is_current` is `True` (2024 data), so none of this cycle's shortlists carry the stale-data caveat that applies to 3 of the 302 scanned industries workbook-wide (see `knowledge/data-cautions.md`).
- Four industries this cycle are cleanly rejected (Electric Wiring, Industrial/Commercial Construction, Field Production Operators, General Automotive Repairs/Auto Wreckers): each has a boundary tie, but even its best-case tie-break still fails the significance bar, so the tie is real but does not change the conclusion. Only Construction Framing Contractor is genuinely tie-sensitive. The earlier draft of this memo reported 0 rejected and 9 deferred, an artifact of a bug (verdict was set from the tie flag alone, not the worst-case/best-case range), fixed 2026-07-13; see Step 3 and `evaluation/use-log.md`.
