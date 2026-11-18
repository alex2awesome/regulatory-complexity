# Next steps after the burden audit, 2026-09-19

**Work order superseded on 2026-09-20:** after selecting solar and concealed
carry, Alex requested a plan including CalFresh. Follow the
[three-family plan](2026-09-20-three-statute-parse-verify-analysis-plan.md), which
distinguishes planning from execution and covers the full frozen three-family corpus.
The broader phases below remain historical proposals, not authorization to
expand parsing or fit all 489 processes.

One plan for the three workstreams that were being tracked in three places:
the parse (Codex's continuation record), the model (the burden audit's ranked
list), and the fits (the watch file). Ordered by what unblocks what, with a
gate for each step that says when it is done. Owners are proposals; Alex
assigns.

The governing fact from the audit: on the synthetic world the model's clock is
1.8 to 4.2 times the truth, its step counts are the hand-authored inventory
plus a prior, and its cost is never reported. Nothing downstream, including
the agency-culture question and Dan's decision-versus-process comparison, is
worth running until the synthetic ratio is near one. So the model work comes
before more fitting, and it runs in parallel with the parse, which does not
depend on it.

## Phase 0. Stop quoting, start scoring (this week, one day)

| step | owner | gate |
|---|---|---|
| Treat every V6 clock as provisional in every document that cites one: the first-results note, the burden-channel note, the watch file. Add one line to each pointing at the audit. | Claude | done when no document reports a V6 clock without the pointer |
| Add V6 posterior support to `evaluate_burden.py` so truth scoring is a runner step, not a scratch script. Keep `runs/w2_v6_fits_20260918/compare_to_truth.py` as the reference implementation. | Claude | `evaluate_burden.py --run <v6 fit> --world W2_DEV_001` reproduces `truth_comparison.json` |
| Make the synthetic release path refuse to mark a fit quotable unless it has been scored. | Claude | test pinned |

## Phase 1. Remove the three known-direction biases, validated on W2 (one to two weeks)

Each change is small. Each is validated the same way: refit C29 and C44 on
sk3 at the settings that already converge, score against truth, and keep the
change only if the ratio moves toward one and the interval still covers.

| step | what changes | gate |
|---|---|---|
| 1a. Model forum selection | compiler policy declares forum cases `delay_selected`; `selection_sd` on; the compiler reads the source type, not the case id, to decide | C29 and C44 ratios fall; the fitted selection strength is consistent with the planted 0.35 / 0.08 |
| 1b. Stop treating silence as serial | within a block with no declared order, report the clock under serial and critical-path readings, or put a prior on overlap fraction fitted from spans that cross the block | truth's 18 to 38 percent overlap is recovered on C29 and C44 |
| 1c. Task-informed priors for unreported steps | elicited prior medians per task type (payment, notification, filing are hours; technical review, inspection are days) replacing the flat seven-day prior; document the elicitation | a payment step no longer carries 2.4 days at the prior; per-step errors on C29 shrink in both directions |
| 1d. No pooled fits | until 1a lands, fit one programme at a time; pooling amplified the bias | policy, no gate |

Phase 1 gate: C29 and C44 converged single-programme fits within 0.7 to 1.4 of
truth with the interval covering. If 1a alone gets there, 1b and 1c become
refinements rather than prerequisites.

## Phase 2. Report what the priorities ask for (two days, can run inside Phase 1)

| step | gate |
|---|---|
| Applicant-facing visit count as a headline metric, from `payer_work` and `actor_role == payer`, beside total visits | reported on every fit; scored against the truth's `applicant_facing` activities on W2 |
| Fee total in `expected_burden` and `report()`, with its spread over paths and repeats | C29 reports $400 and C44 $380 |
| Count observations per fit as a coverage number, now that `burden-count-evidence/2` lets count-only cases exist | the number is in every compilation report |
| Contract channel for money to third parties, money to the applicant, and the cost of delay, per the handoff's recommendation | schema bump reviewed by Alex before any ledger moves |

## Phase 3. Let administrative data in, then refit solar (one week)

| step | gate |
|---|---|
| Cohort bindings for every published median with a stated n, starting with the 69 SolarTRACE and dashboard rows the solar fit dropped; the compiler should propose a binding when scope is resolved rather than require one to be authored from nothing | solar compilation reports 0 medians dropped for want of a binding |
| Refit solar with administrative cohorts plus forum cases under Phase 1a | the clock is compared with SolarTRACE at the same endpoint (the bridge's initial decision is the PTO grant, not the permit) and the comparison is stated with both numbers' definitions |
| Retire the "published 4 versus posterior 37" framing everywhere it appears | done |

## Phase 4. Agency speed and culture (two to three weeks, after Phase 1)

The design exists twice: SolarTRACE across 60 jurisdictions, and the
concealed-carry forum corpus across 119 issuing authorities under one statute.
The model needs three changes before either can answer the question.

| step | gate |
|---|---|
| Share operation identities across jurisdictions for the same step, so the agency effect is what remains after the step is accounted for (today operations are keyed per programme and the agency effect is collinear with them) | rerun `rw_fit_solartrace60` from its existing input: hierarchy coordinates converge, agency block headline-eligible |
| Learn the agency spread with a hyperprior instead of the fixed 1.0 | the posterior spread on SolarTRACE is reported with an interval; on synthetic S06 to S08 the planted 0.37 is recovered |
| Case-level jurisdiction: a structured issuing-authority id on each concealed-carry case, reviewed from the `cohort` free text and the 48 declared per-county actors | 574 cases carry an authority; the 14 authorities with ten or more cases are the first fit |
| Validate on synthetic counties before real ones. Requires structural handoffs for many synthetic processes; the derived handoff is acceptable for a spread-recovery test only if the test is about the spread and not the clock, and that caveat is written down | recovered spread within its interval of 0.37 on at least one statute with 60 implementations |

## Phase 5. Parse completion and fit-readiness (Codex, ongoing, independent of the above)

Unchanged from Codex's record: 19 megathreads, reviewed revisions with
before-and-after lineage, the reviewed-fit holds, cross-ledger case candidates,
the naturalisation supplement, and the 753 semantic decisions per ledger. Two
things the audit adds to the semantic audits: record each population median's
scope and n so Phase 3 can bind it, and mark each forum case's issuing
authority so Phase 4 can use it. Both are one field each at parse time and a
review job later.

## Phase 6. Dan's question (after Phases 1 and 4)

Does decision-tree complexity track outcomes, and is the process model the
right object? The synthetic world plants both a decision model per statute
and a process per county with separate speed and availability knobs, so the
comparison runs on ground truth first: statute-level decision complexity
against recovered county-level burden, across the twelve statutes with 17 to
61 implementations. Then the same on the concealed-carry corpus, one statute
against 119 implementations. This is not started and should not be until the
model recovers the clock it is being compared on.

## What is deliberately not on the plan

- Relaunching Claude parse agents while Codex holds the parse.
- More than one repeat block per programme. Real, ranked ninth in the audit,
  and not on the critical path to a clock that is right.
- Any real-corpus headline number before the Phase 1 gate.

## Where each piece lives

- Parse state: `runs/rw_parse_20260919/FORUM_WORK_PLAN_v2.json` and
  `docs/2026-09-19-codex-parse-continuation.md`.
- Model audit and evidence: `docs/2026-09-19-bayesian-burden-audit.md`,
  receipts in `runs/w2_v6_fits_20260918/truth_comparison.json` and
  `runs/w2_v6_fits_sk3_20260919/truth_comparison.json`.
- Fits: local under `runs/w2_v6_fits_20260918`, collected sk3 fits under
  `runs/w2_v6_fits_sk3_20260919`, solar extension under
  `runs/rw_parse_20260918/solar_permit/fit_full_ext`.
- Running record: `docs/scoping/FINDINGS.jsonl`, packet `W2-V6-WATCH`, and
  `docs/scoping/W2_V6_WATCH.json`.
