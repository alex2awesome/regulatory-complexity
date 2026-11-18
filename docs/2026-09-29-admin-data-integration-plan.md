# Plan: getting the administrative datasets into the Bayesian model (2026-09-29)

Inputs: `runs/admin_data_20260929/manifest.json` (payloads on sk3 under
`/dfs/scratch0/alexspan/admin_data_20260929/`). Goal: turn per-permit / per-interconnection records
into model-ready observations that (a) give population timing per jurisdiction/utility/year and
(b) calibrate forum reports against the same cells -- the source-offset step every current fit
leaves at zero. Owners: **S** = deterministic script (Claude), **G** = Gemma 4 31B on sk2 (validated
first), **C** = Codex modeling, **A** = Alex decision.

## What each source gives (checked columns)

| source | rows | how to find ADU / solar records | dated events available | keys |
|---|---:|---|---|---|
| CA DG Stats (PG&E, SCE, SDG&E) | 2.2M sites / 2.4M apps | all are interconnections; `Technology Type`, storage fields | App Received -> App Complete -> App Approved (= PTO); Decommissioned | utility, city, ZIP, size; **no address** |
| SF DBI permits | 1.3M | `ADU` flag; solar via `Description` text | Filed -> approved -> Issued -> First Construction Doc -> Completed | address/block-lot |
| LA LADBS (3 vintages) | 1.29M | `ADU_CHANGED`, `JUNIOR_ADU`, `Solar` flags | SUBMITTED -> ISSUE -> COFO | APN, address, lat/lon |
| LA County EPIC-LA | 0.92M (1.41M history rows) | `JUNIOR_ADU` + ADU fields; solar via `DESCRIPTION`/`WORKCLASS_NAME` | APPLY -> COMPLETE -> ISSUANCE -> LAST_INSPECTION; EXPIRE | address |
| San Diego DSD approvals | 1.6M | `APPROVAL_ADU_TOTAL`, `APPROVAL_JADU_*`; solar via scope text | PROJECT_CREATE -> DEEMED_COMPLETE -> APPROVAL_ISSUE -> CLOSE; EXPIRE | APN, address |
| Sacramento (applied + issued files) | 0.6M | `Type`/`Sub_Type`, `Work_Desc` text | one `Status_Date` per row; apply and issue in **separate files** -> must be joined per permit | parcel, address |
| San Jose (active + expired only) | 93k | `SUBTYPEDESCRIPTION`, `WORKDESCRIPTION` text | ISSUE -> FINAL (no filed date; no finaled archive -> survivor-biased) | APN |
| HCD APR Table A / A2 | 386k / 1.0M | `PROJECT_TYPE` / unit-type columns (ADU, JADU) | Table A application; A2 entitlement -> building permit -> CO dates | APN, address |
| LBNL Tracking the Sun | 2.05M CA | all PV | install date only | ZIP, utility, installer |
| SolarTRACE (held), SolarAPP+ PDFs, CEC CalAPP, CPUC Rule 21 PDFs, Terner PDFs | aggregates | -- | medians / adoption dates / compliance tables | jurisdiction, utility |

## Steps

1. **Freeze + profile (S).** Load each file once, parse dates, count missing/invalid (e.g. 1901
   dates, issue-before-file), status vocabularies, per-year volumes. One profile JSON per source,
   bound to the manifest sha256. No cleaning yet.
2. **Event crosswalk per source (S, A signs off).** Map each date column to the SAME canonical event
   list the forum clock crosswalk uses (application submitted, application complete/accepted,
   permit issued, construction start, final/CO, interconnection submitted, PTO). One small table per
   source with explicit caveats (SF "filed" vs "approved"; DG Stats "Received" vs "Complete";
   APR entitlement vs building permit; San Diego "deemed complete"). A dozen columns in total: a
   human-reviewed table, not a model task.
3. **Select ADU and solar records.**
   - Flag-based where flags exist (S): LADBS, SF ADU, San Diego ADU/JADU, EPIC-LA JADU, APR unit types.
   - Text-based where they do not (G): classify permit descriptions into a closed codebook
     {ADU new detached, ADU conversion/attached, JADU, ADU legalization, solar PV, PV+storage,
     storage only, reroof-with-solar, other}. Validate first on sources that have BOTH flags and
     text (LADBS `Solar`/`ADU_CHANGED` vs `WORK_DESC`; SF `ADU` vs `Description`): measure precision/
     recall on ~500 held-out rows; only then run on SF solar, EPIC-LA, San Diego scope, Sacramento
     and San Jose. Pre-filter with a keyword regex so Gemma sees ~5-10% of rows (tens of thousands,
     not millions -- minutes on one GPU).
4. **Project assembly (S).** One project can span several permits (building + electrical for solar;
   ADU plan check, revisions, supplemental permits). Group by parcel/address + permit-number
   lineage + time window; keep the grouping rule and its ambiguous cases. Sacramento: join applied
   and issued files per permit. APR: reuse the existing A<->A2 APN join
   (`corpus/counties/audit_apr_linkage.py`). DG Stats cannot link to city permits (no address):
   keep interconnection as its own phase.
5. **Durations + censoring (S).** Per project and canonical clock: completed interval, or
   right-censored at the extract date when the later event is missing and the status is open;
   expired/withdrawn/cancelled as a separate terminal outcome (not a long duration, not dropped).
   Business vs calendar days kept explicit. Same censoring vocabulary as the forum claims.
6. **Keys and eras (S, G for messy names).** Attach jurisdiction (AHJ id used by the SolarTRACE
   panel `stable_owner_id`), county, utility, year, system-size class; normalize city names
   (deterministic dictionary first, Gemma only for leftovers). Era flags the model should see:
   solar NEM 2 -> NEM 3 (April 2023), SB 379 / SolarAPP+ adoption date per jurisdiction (CEC CalAPP
   list); ADU law changes (2017, 2020, 2023-24) and each city's ordinance date where known.
7. **Model-ready aggregates (S).** Millions of rows should not be sampled one by one:
   - exact **histogram cohorts** per (clock, jurisdiction or utility, year, size class, era):
     completed-duration bins + censored counts. These are what `source-offset-hierarchy/2` accepts
     as hash-bound reference anchors (exact data, no reporting offset);
   - per-cell summaries for the existing collapsed admin component (the SolarTRACE panel pattern),
     so SolarTRACE medians and the new per-project cells can be checked against each other.
8. **Line forum claims up with the same cells (S, C).** Forum timing claims (after the clock
   crosswalk) need the same keys: clock, jurisdiction/utility, year. Use existing county/utility
   weights; claims with unknown geography stay in the forum likelihood but cannot calibrate. This
   is what makes the forum-vs-admin comparison ("eligible matched comparisons", currently zero)
   non-empty.
9. **Model integration (C, A for assumptions).** In V6: admin cohorts as the reference level per
   cell; forum reports get a source offset (bias) and precision relative to it; declare the
   case-to-cohort overlap assumption (forum projects are a vanishing share of millions of admin
   records, so treat overlap as negligible, stated). One fit per domain, same gates as now.
10. **Held-out check (C).** Hold out whole jurisdictions/years: predict admin cell medians from
    forum-only vs forum+admin models, and run the same-evidence LLM baseline on the same queries.
    This is the test of whether the Bayesian layer adds anything.

## Decisions needed from Alex (A)
- Estimands to headline: e.g. ADU application->permit issued and issued->final by city; solar
  permit filed->issued, issued->final, interconnection received->PTO by utility and year.
- Era cut points and whether to model pre-2019 at all.
- Whether San Jose (survivor-biased, no filed date) enters the likelihood or only descriptive tables.
- Overlap assumption wording (step 9).

## Rough effort
Steps 1-2, 4-7: deterministic scripts, about a day on sk3, no frontier tokens. Step 3: Gemma, well
under an hour of GPU after a ~500-row validation. Step 8 depends on the forum clock crosswalk
(`docs/2026-09-29-audit-of-codex-model-cuts.md`). Steps 9-10: Codex, one bounded task each.

## Decisions taken (2026-09-30; Alex: "not sure what the right decisions are ... use San Jose")
Defaults chosen by Claude, recorded so they can be changed; each is the conservative option.
- **Headline estimands.** ADU: application submitted -> permit issued; permit issued -> final/CO.
  Solar: permit application -> permit issued; permit issued -> final inspection; interconnection
  application received -> PTO (by utility and year). Everything else is computed but secondary.
- **Eras.** Model 2017-2025 (ADU: after the 2017 state law; solar: SolarTRACE window). Era flags,
  not separate models: ADU 2017-19 / 2020-22 / 2023-25; solar pre/post NEM 3 (2023-04-15) and each
  jurisdiction's SolarAPP+ adoption date. Earlier records are profiled but not modeled.
- **San Jose: used** (Alex). Its files hold only active and expired permits and no filed date, so it
  contributes issued -> final only, with a source indicator so its survivor bias can be estimated
  rather than assumed away.
- **Overlap.** Forum projects are treated as a negligible share of admin records; stated as an
  assumption in the model record, not corrected for.
