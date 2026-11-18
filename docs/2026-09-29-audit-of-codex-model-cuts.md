# Audit: were Codex's model-input cuts valid? (2026-09-29, Claude)

Question (Alex): of the staged evidence Codex did not put into the Solar/ADU fits, how much was cut
validly and how much was over-cut? Method: every excluded timing claim was classified by Gemma 4 31B
against the declared clocks (`runs/solar_model_audit_20260929/`), then a random sample was checked by
hand. Inputs: `runs/solar_model_20260929/pooled_s1_prepared001/route_accounting.json` +
`combined_s1_adopted001/observations.json`; `runs/adu_model_20260929/a1_a42_pooled_prepared001/` +
`a1_a42_clock_compiled001.json`. No fit, packet or source file was changed.

## Solar (10,605 numeric timing candidates; 1,225 fitted)

Why claims were excluded: 9,038 of the 9,041 "outside declared estimands" have
`clock_pooling_status = exact_label_unreviewed`. Readers wrote free-form clock names (7,981 distinct
names among 9,041 claims); the fit only pooled names that exactly matched one of the 15 declared
clocks. The exclusion was **"not yet mapped"**, not "judged invalid".

Classification of all 9,360 non-fitted candidates (9,041 outside + 290 heterogeneous + 29 no clock):

| category | claims | verdict |
|---|---:|---|
| not process timing (outages, repairs, inverter failures, labor, system age, home purchase) | 3,884 (41%) | **valid cut** -- 15/15 hand-checked correct |
| same interval as a declared clock | 1,879 (20%) | **over-cut** -- ~20/25 hand-checked correct (~80%) |
| a real process interval not in the list | 3,509 (37%) | **unused, not invalid**; ~550 carry a declared clock's name (Gemma inconsistency, likely declared); others are new intervals: order->design (80), order->permit submission (46), order->permit approval (44), whole-project (~160), ... |
| unclear | 87 | -- |

Declared-clock matches by target: installation->PTO 431, physical installation 179,
interconnection submission->PTO 171, installation->final inspection 167, final inspection->PTO 165,
contract->installation 147, order->installation 128, permit submission->approval 128, contract->PTO 101,
order->PTO 85, permit approval->installation 56, ...

**Estimate:** at ~80% precision, ~1,500 of the 1,879 are genuine declared-clock reports, plus a share
of the ~550 declared-named "other" items: roughly **1,600-2,000 over-cut reports, i.e. 1.3-1.6x the
1,225 fitted**, before dependence thinning and support gates. Permit submission->approval alone would
go from 39 fitted to ~140; interconnection submission->PTO from 41 to ~200. Some are outside
California (e.g. Houston, National Grid); that is handled by the geography scope, not by this cut.
Typical mapping errors seen: "paid" read as deposit; a 2-year wait that ended in cancellation read as
a completed install; "PG&E's side" read as installation->PTO; a loan notice read as the contract.

## ADU (456 admitted elapsed readings; 161 fitted)

Routes: 161 modeled; 46 same-contributor/same-clock dependent (**valid cut**); 249 below the
15-contributor support gate. Of those 249: 23 match one of the four fitted clocks (first submission->
issuance 11, construction 6, project->completion 3, permitting->issuance 3: **over-cut**, small);
225 are genuinely different intervals (design phases, plan check start->approval, correction
resubmission->agency response, legalization process, planned vs actual completion): **not wrongly
cut from these four frames**, but valuable step-level evidence that no current model uses.

## Verdict
- The cuts are mostly **deferred, not wrong**: nothing was deleted, and the invalid-looking 41% of
  Solar exclusions really are not process timing.
- The real over-cut is Solar's unmapped labels: ~1,600-2,000 reports that measure declared clocks.
- Structural gap: free-form clock names make every new reading pass need a mapping step. The fix is
  prospective (readers record start/end events from a fixed list) plus a one-time crosswalk.

## Bounded task for Codex (paste-ready)
> Task: Solar clock crosswalk. Use `runs/solar_model_audit_20260929/out_solar_clockmap_audit/output.jsonl`
> (Gemma's per-claim mapping of the 9,360 non-fitted candidates; ~80% precision on declared matches)
> as a starting point. Done = a crosswalk file mapping each candidate to a declared clock, a named new
> interval, or `not_process`, reviewed once in bulk by Luna (one pass, no second review), and the 14
> pooled + 8 California-only Solar fits rerun ONCE on the expanded input with unchanged priors and gates.
> Also add the new intervals with >=15 contributors (e.g. order->design, order->permit submission) as
> extra frames. Budget: one working session. Report fitted claims before/after and the new tables,
> then stop. No successor versions, no re-verification of source quotes. Also update READER_BRIEF so
> future timing claims record `start_event`/`end_event` from the fixed event list.
