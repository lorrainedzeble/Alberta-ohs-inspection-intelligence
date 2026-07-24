# Domain notes

Distilled background on how Alberta OHS enforcement and WCB reporting actually work, so skill output uses this domain's real vocabulary rather than generic data language. Referenced from CLAUDE.md.

## Why this persona and this workspace exist
Alberta OHS publicly states how it chooses where to send proactive inspection effort:

> "Each year OHS chooses particular industrial sectors to proactively inspect, selecting sectors that have relatively high injury and illness rates, high frequency of incidents or complaints, persistently low rates of compliance, or are emerging trends." OHS officers focus on worksites "identified by OHS as chronically noncompliant."
> Source: alberta.ca/ohs-proactive-inspection-program

Those four criteria (injury rate, incident/complaint frequency, compliance history, emerging trend) are the reason this workspace's five skills exist. Each skill computes one of those criteria, at the employer level instead of the sector level, using the WCB injury data and the OHS Act Part 7 enforcement records in this dataset.

## Terms (from the vendor docx, still accurate)
- Lost Time Claim (LTC): a claim accepted in the calendar year for an occupational injury or disease causing time away from work beyond the day of injury.
- Disabling Injury (DI) claim: combines lost time and modified work claims into a broader figure; not expected to reconcile with LTC based figures published elsewhere.
- Person year: estimate of full time worker equivalents from WCB payroll data; 2,000 hours equals one person year.
- Certificate of Recognition (COR): awarded to employers whose health and safety management system passes an external audit at 80% or higher overall, 50% or higher per element; typically valid three years with maintenance audits required in between. This dataset has a column meant to record whether it was held in a given year, but that column is completely empty in this file. See `data-cautions.md`. Kept here for vocabulary only; this workspace makes no COR claims anywhere.
- Fatality: a worker death accepted by WCB for compensation, including motor vehicle, workplace incident, and occupational disease deaths.
- Stop Work Order: issued when an OHS officer finds work being done in an unhealthy or unsafe manner; lifted once the order's requirements are met.
- Acceptance / Approval: a Ministerial acceptance or approval lets an employer meet an OHS Code requirement through an alternate, equivalent method under a named legislation section. A different mechanism from COR and from enforcement; see `data-cautions.md` for why its dates cannot be treated as a live status.

## Formulas
- LTC rate equals number of LTCs divided by person years worked, times 100.
- DI rate equals number of DIs divided by person years worked, times 100.
- Both rates are suppressed or flagged when person years worked is under 40, since the rate becomes too volatile to compare meaningfully.
