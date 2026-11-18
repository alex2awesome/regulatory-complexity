# Toy statute: blind process-model construction — results (2026-09-30)

Plan: `2026-09-30-toy-statute-blind-process-plan.md` (predeclared). Question: when inference has to build its
own step catalogue, design menu and evidence vocabulary from free text, how much of the oracle's design and
burden recovery survives? World `runs/toy_statute3_20260930/HEN3`: hen v2 statute, 14 towns, plus a step
outside the standard catalogue (neighbour signature collection) and two designs outside the standard menu
(S12 signatures+desk, S13 notice+comment+desk, no hearing). S12/S13 ended up in 4 towns (Halite, Mica
forced; Flint, Nephrite by the generator's choice rule). Evidence: 210 applicant reports (163 decided,
47 pending), 240 admin records with milestone dates in 6 towns, 14 web pages; all rendered to free text by
deterministic templates (`toy_statute/render_text.py`).

## 1. Catalogue recovery (two builders, text only)

| Builder | Steps | Designs | True steps found | Signature step | Merges |
|---|---|---|---|---|---|
| Opus (fitted) | 9 | 24 | 10/10 | yes | neighbour notice + comment period → one step |
| Sonnet (scored only) | 9 | 24 | 10/10 | yes | same merge |

Both builders recovered every step that appears in the rendered text, including the out-of-catalogue
signature step. Both merged neighbour notice and the 14-day comment period into one step; the text never
separates them by an observable event, so this is the right granularity for the data (the oracle's split is
unidentified; see §3). The Opus design menu covers all 11 true designs in use up to that merge, except
that S4's exact order (desk review before hearing) appears only with the hearing first (B19); it also
contains no desk-review + inspection combination. Predeclared expectation "builder finds every rendered
step including signature collection": **holds** (both builders).

## 1a. Blind decision-model skeleton (added after Alex's instruction: no hand-written inputs at inference)

The D-step skeleton had been passed to the blind builders from the package. Two builders (Opus, Sonnet)
now receive the statute text alone and write the skeleton (`blind001/skeleton_{opus,sonnet}.json`).
The skeleton enters the model only through burden roll-ups (which p-steps serve which D-step), never
the likelihood, so the running blind fit is unaffected and roll-ups are recomputed under the blind
skeleton when it finishes.

| Hand-written (package) | Opus (6 steps) | Sonnet (5 steps) |
|---|---|---|
| D1 application (Sec. 2 + Sec. 4 'complete'), concrete | D1 submit application (vague), D2 site plan (concrete), D3 completeness (vague) | D2 application + site plan (concrete), D3 completeness (vague) |
| D2 nuisance determination (Sec. 3), vague | D5 no-nuisance determination, vague | D4 nuisance determination, vague |
| D3 issue or deny (Sec. 4), concrete | D6 issue or deny, concrete | D5 issue or deny, vague |
| (none) | D4 eligibility under Sec. 1, concrete | D1 eligibility under Sec. 1, vague |

Both blind skeletons recover the three hand-written determinations and both add a Sec. 1 eligibility
check that the hand-written skeleton omitted. Both split the hand-written D1 into submission and a
separate completeness determination, and both tag completeness vague (no cure procedure in the text).
Both leave the Sec. 5 fee out as permissive. Both read the deadline identically (complete application →
issue/deny, 30 days). Disagreements: Opus tags submission vague and issuance concrete; Sonnet the reverse
on issuance (no written reasons or grounds in the text). The eligibility step has no process step in the
catalogue serving it, which is itself a finding: the law requires a determination that no observed
process step performs, or that is folded into completeness.

## 2. Extraction (Sonnet, catalogue + documents only; admin CSVs by the builder's column map)

Field-by-field against the generator's structured evidence after mapping through the synonym key:
status 210/210, pending ages 47/47, mentions 815/815, timed-gap sequences 163/163 exact, hours 89/89,
fees 78/78, web listings 108/112 (4 wrong). One scripted vocabulary check per file: 0 problems. This is
near-perfect because the rendering is templated (one phrase per step, no contradictions); it measures
vocabulary discovery, not messy-language extraction.

## 3. Oracle fit (true package, structured evidence)

`HEN3/fit_oracle001`: 2 runs × 4,000 particles × 20 moves, seed 20261030, `--center-towns --gate v2`,
no step blocks; 3.1 h on sk3.

| | Oracle |
|---|---|
| MAP design correct | 13/14 (Emery S4 → S9, P(true) = 0.14) |
| Mean posterior P(true design) | 0.92 |
| Out-of-menu towns (S12/S13) P(true) | Flint 1.00, Halite 1.00, Mica 1.00, Nephrite 0.95 (in the oracle's menu, so expected) |
| Total days, MAE vs held-out mean (500 cases/town) | 3.0 days |
| Total days, 90% interval coverage | 13/14 (Iolite misses: 47.4 vs 38.3) |
| Per-step days, 90% coverage (mapped steps) | 0.90 |

**Convergence gate: FAILS.** Worst between-run R-hat 1.33; 56 parameter and 188 estimand
standardized-mean-difference fails (median SMD 0.35). The large ones (SMD 1.0–1.5) are all
`pstep_days.neighbor_notice` and `pstep_days.comment_period`: the two runs split the same notice+comment
total differently, because no observed event separates the steps (no `notice_mailed` milestone). The split
is unidentified; the sum, totals and design posteriors agree across runs. The failure is reported, not
re-run: 4,000 particles is the predeclared budget, below the 10k×30 production setting.

## 4. Blind fit (compiled Opus package, extracted evidence)

Attempt 1 (`blind001/fit_blind001`, log kept as `fit_blind001_attempt1.log`) failed the single-draw
preflight: the one prior draw gave `site_inspection` a median under one day with a tiny spread, so the exact
hearing → inspection admin milestone gaps (7–20 days, Cobalt and Kyanite, true S11) had probability
exactly zero under every design, including the matching B4. Exact milestone likelihoods have no
contamination floor by design; the oracle package is −inf at 2 of 11 prior draws too and passed on the
seed. Fix in `toy_statute/smc.py`: preflight tries up to 20 prior draws (the first is the old draw, so the
oracle preflight is reproduced exactly, loglik −4043.4); model and sampler unchanged. Attempt 2
(`blind001/fit_blind002`) passed preflight at draw 2 and is running with the oracle's settings.

Attempt 2: `blind001/fit_blind002`, 2 runs × 4,000 particles × 20 moves, 4.7 h (oracle 3.1 h; 24 designs
vs 13).

| | Oracle | Blind |
|---|---|---|
| MAP design correct (up to the notice+comment merge) | 13/14 | 12/14 |
| Mean posterior P(true design) | 0.92 | 0.85 |
| Out-of-menu towns P(true): Flint, Halite, Mica, Nephrite | 1.00, 1.00, 1.00, 0.95 | 0.99, 0.94, 0.99, 0.92 |
| Total days, MAE vs held-out mean | 3.0 d | 2.8 d |
| Total days, 90% coverage | 13/14 | 13/14 (same miss: Iolite) |
| Per-step days, 90% coverage (mapped steps) | 0.90 | 0.89 |
| Gate v2 | FAIL (R-hat 1.33; notice/comment split) | FAIL (R-hat 1.04, worst SMD 0.50; 33 params, 76 estimands, only three above SMD 1, all `total.days_q10`) |

**Design recovery.** The blind fit recovers the same designs as the oracle in 12 towns, including all four
towns on the out-of-menu designs S12/S13, which the builder had reconstructed from the text as B7
(signatures + desk) and B10 (notice + desk). The two misses are Basalt and Emery, both true S4 (notice →
comment → desk review → hearing if objection); the blind posterior puts all its mass on B2 (notice → hearing),
i.e. drops the desk review. Two different causes:
- *Basalt* (oracle 0.98 on S4): the Opus menu has no design with desk review **before** the hearing; its
  only notice+desk+hearing design is B19 with desk review after the hearing. Basalt keeps admin records with
  hearing dates, and the exact hearing → decision gaps are too short to contain a desk review, so B19 is
  rejected and the fit falls back to B2. This is the menu gap flagged in §1 (S4's order absent), not a
  fitting failure: the catalogue, not the likelihood, lost the design.
- *Emery* (oracle 0.86 on S9, also wrong): no admin records, two timed hearings, desk review unlisted on the
  web page and without an event. The desk review is unidentified for both fits; the blind B2 is the oracle's
  S9. Here the blind matches the oracle's error.

**Burden.** Total days are as good blind as oracle (MAE 2.8 vs 3.0 d; the same town, Iolite, falls outside
the interval in both). Per-step coverage is within 0.01. The blind fit's gate is less bad than the oracle's
because the builder merged notice and comment period into one step: the unidentified split that drove the
oracle's R-hat to 1.33 does not exist in the blind model. The remaining blind gate failures are mostly
small (median SMD 0.35) with the 10th percentile of total days the only estimand family above SMD 1.

**Blind skeleton roll-up** (`blind001/fit_blind002/answers_skel.json`: the same blind particles,
re-labelled by the Opus text-only skeleton via `rechunk_answers.py`; the script reproduces the oracle's own
answers exactly when given the oracle package, zero difference on 255 estimands). Blind D-steps are mapped
to the hand-written ones by clause for scoring only (Opus D1+D2+D3 → application, D5 → nuisance, D6 → issue).

| Blind D-step group | Score vs truth (14 towns) |
|---|---|
| Application (submission + completeness; 3 blind D-steps summed) | MAE of summed medians 2.0 d (range 0.0–4.9) |
| Nuisance determination (one-to-one) | 90% interval covers truth in 12/14 (misses: Amber, Lapis) |
| Issue or deny (one-to-one) | 90% interval covers truth in 12/14 (misses: Cobalt, Kyanite, the two permit-on-site towns, where the blind skeleton assigns the inspection to the nuisance step only) |
| Eligibility (Sec. 1, no process step serves it) | 0 days in every town, by construction |

One-to-one coverage 0.86. Burden attaches to the law's determinations end to end from text: no hand-written
input remains anywhere in the blind chain except the model conventions in the compiler (fixed
prepare/completeness/correction skeleton, one objection-conditional step type, pace scaling).

## 5. Predeclared directions

| Expectation | Result |
|---|---|
| Builder finds every rendered step incl. signature collection | **holds** (both builders) |
| Blind design MAP accuracy below oracle | **holds**, narrowly (12/14 vs 13/14); the one extra miss is a design-menu order gap, the other miss is shared with the oracle |
| Blind burden error larger than oracle, intervals still cover | **fails on the first half, holds on the second**: blind total-days MAE is slightly *smaller* (2.8 vs 3.0 d) and coverage identical (13/14); per-step coverage 0.89 vs 0.90 |

## 6. Limits

Templated rendering (one synonym per mention, no contradictions, no missing fields) makes extraction a
vocabulary test, not a language test. One builder fitted. Builder/extractor blindness rests on instruction,
not a sandbox. Stage C (readings) out of scope: readers' validity rules refer to the oracle menu. The
oracle gate failure means per-step notice/comment numbers from this fit are not usable; totals and designs
are consistent across runs.
