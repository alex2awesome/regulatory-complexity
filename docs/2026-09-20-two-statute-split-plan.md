# Two statutes, one each: the split between Codex and Claude

**Assignment revised 2026-09-20 by Alex:** Codex takes CalFresh, Claude takes
**solar**, not concealed carry. See the
[solar leg plan](2026-09-20-solar-leg-plan-for-claude.md), which also corrects
this document's dismissal of solar as a leg: the objection applied to the
one-cell-per-authority build, not to the underlying panel, which carries 32,238
timing cells, an install count in every cell, a crossed authority/utility design
and a statutory staggered mandate. Concealed carry stays parsed and available.

Alex's question: if the project focuses on two statutes, which two, and what does
it look like if Codex takes one and Claude takes the other. This replaces the
[single-agency plan](2026-09-20-single-agency-ventura-plan.md), which answered a
narrower question. Ventura is not dropped; it becomes the deepest authority
inside one of the two legs.

## The pair

**Leg 1. California concealed-carry licensing, Penal Code 26150 and following.**
**Leg 2. CalFresh expedited service, Welfare and Institutions Code 18914 with
the federal three-day and seven-day service rules.**

They are chosen as a contrast pair, not as two of the same thing. Both ask the
project's central question, whether one statute produces different burdens in
different jurisdictions, and they answer it through opposite measurement
channels.

| | concealed carry | CalFresh expedited |
|---|---|---|
| channel | applicants' own accounts | the agency's own census |
| jurisdictions | 80 authorities named, 30 with at least 8 cases | 58 counties, 46 in the primary cohort |
| units | 2,011 case identities before cross-ledger deduplication | 59,634 recorded reports |
| denominators | none; selection by who posts | real counts per county |
| burden channels present | steps, trips, effort, fees to four payees | elapsed wait only |
| published comparator | statutory caps and agency targets | the three-day rule |
| policy discontinuity | Bruen June 2022, SB 2 in 2023 | none |
| state today | parsed, never fitted | fitted, one condition done |

Where the two legs agree about the shape of cross-jurisdiction variation, the
finding survives a change of measurement channel, which is the strongest claim
this evidence can support. Where they disagree, the disagreement is the metric
seam and is itself the result. Each leg also supplies what the other lacks:
CalFresh provides a census-based reference for what genuine county variation
looks like, and concealed carry provides the steps, trips and money that an
administrative wait time cannot see.

**Why not solar as a leg.** The SolarTRACE panel has 401 authorities and no
sample size for any of them, so its cross-authority spread is set by an assumed
reporting precision rather than by data. The running conditions should finish and
be released as agency processing time, but it is a weaker third leg, not a
co-equal one. The contractor licence and naturalisation are single-agency and so
carry no cross-jurisdiction design at all.

## Leg 1, Claude: concealed carry

The evidence is already parsed. The bottleneck is model machinery that I have
already diagnosed and specified, so this leg is mostly code plus one structured
review pass.

**The panel.** Authorities with at least eight case identities, from the
73-ledger snapshot:

| authority | cases | elapsed rows | fee rows | effort rows |
|---|---:|---:|---:|---:|
| Ventura County | 130 | 151 | 9 | 26 |
| Los Angeles | 72 | 77 | 10 | 4 |
| Kern County | 63 | 65 | 11 | 2 |
| Merced County | 60 | 46 | 24 | 5 |
| Monterey County | 52 | 57 | 13 | 9 |
| Orange County | 45 | 35 | 12 | 5 |
| San Luis Obispo | 36 | 40 | 13 | 7 |
| Tulare County | 34 | 25 | 7 | 8 |

Thirty authorities clear the threshold. Year mentions split roughly evenly
across the Bruen boundary, so the eras are both populated.

**Work items, in order.**

1. **Structured authority and era identity.** Per-authority attribution today
   comes from free-text cohort strings, and it is unreliable: one authority shows
   414 elapsed rows against 43 cases, which is a matching artefact rather than a
   finding. Every case needs a structured issuing-authority id, an episode type
   (initial, renewal, amendment) and a policy era. This is the one review pass
   this leg needs, and it must apply the cross-ledger duplicate findings rather
   than cite them.
2. **Admit the evidence the compiler drops.** Typical ranges need their own
   likelihood instead of a residual constant, and start-of-process wording needs
   binding to a modelled event. This is the change that made the synthetic clock
   fail, and it is the same change here.
3. **Selection and source trust, minimally.** Forum cases declared selected,
   selection on, and a reference-anchored source offset. Concealed carry has no
   administrative median, so the anchor is the published promise, and the claim
   is explicitly promise against reported experience.
4. **More than one repeat block, or an honest restriction.** Renewal and
   correction are different repetitions and the model holds one slot. Either
   extend it or state which repetition is modelled and which is folded in.
5. **Fit the panel** with a shared step vocabulary across authorities, an agency
   effect that is what remains after the step is accounted for, era as a fixed
   effect, and applicant-facing step count, trips and fee total reported beside
   the clock.
6. **Baselines and a held-out test.** The statutory cap, the agencies' published
   typicals, the corpus's own sentences, and an LLM given the same documents.
   Hold out whole authorities, not cases, so the test is whether the hierarchy
   predicts a county it has never seen. Freeze the split before looking.

**Deliverable.** Per-authority burden profiles with uncertainty, the promise
against experience gap by authority and era, and a held-out score against every
baseline.

## Leg 2, Codex: CalFresh expedited

Codex keeps this because the work is already in flight and the remaining tasks
are its strengrhs: workbook denominators, reporting semantics, census
accounting, and careful cohort binding. No forum parsing is required.

**Work items, in order.**

1. **Finish the four conditions** and release. All 138 reported bin estimands
   already pass their gates; the two failures are a derived agency cycle-days
   quantity and a shared spread, neither of which appears in the report. Re-scope
   the gate to the reported estimands rather than blocking on nuisance
   coordinates.
2. **Resolve the twelve held zero-reporting counties.** A published zero means
   either nothing to report or nothing tracked, and the export cannot tell them
   apart. Either obtain the county comments or state the bound both ways. Twelve
   of 58 counties is a fifth of the census.
3. **State what the model adds beyond the raw table.** Posterior bin
   probabilities currently reproduce observed fractions to a median of 0.0017,
   with 31 of 46 counties inside 0.001. The honest contribution is intervals and
   shrinkage on the fifteen counties under 200 reports. Say so, and consider
   whether a closed-form conjugate version is the right presentation.
4. **Extend the census beyond one month** where the semantics support it. July
   2025 alone cannot separate a county's standing performance from a bad month,
   and this is the single biggest gain available on this leg.
5. **The statutory comparison.** The three-day rule against the observed
   distribution, per county, with the seven-day rule as the secondary threshold.
   This is the same promise-against-practice structure as Leg 1 and should use
   the same table shape.
6. **Baselines.** The raw county fraction, and an LLM given the same workbook.
   A model that cannot beat its own input table on held-out months should be
   reported as not beating it.

**Deliverable.** Per-county service-time distributions with uncertainty, the
statutory comparison, and a stated position on what the hierarchy adds.

## Interface and collision rules

- **Separate corpora, separate run directories.** Neither leg reads the other's
  evidence.
- **Code boundary.** Codex owns the aggregate and census path, including
  `cohort_histograms.py` and `conditional_case_frames.py`, and the compiler
  change for aggregates with reviewed denominators, which CalFresh needs now.
  Claude owns the individual-report path in `compile_visit_durations.py` and the
  hierarchy in `bayes_trace_hierarchy.py`. Running fits carry their own frozen
  source snapshots, so neither side's edits disturb the other's jobs.
- **One shared artefact, by agreement:** the promise-against-practice table
  shape, so the two legs' results can sit side by side without rework.
- Neither leg touches `runs/rw_parse_20260918/` or `runs/rw_parse_20260919/`
  except to read.
- The running solar conditions finish and are released separately. They are not
  a leg and nothing waits on them.

## Timeline and stopping rule

Two to three days per leg, in parallel. Leg 2 is closer to done; Leg 1 has more
code and one review pass.

The stopping rule is the same for both, and it is what ends the validation loop:
**when the held-out score against baselines exists, the leg is reportable,
whether or not the model wins.** A loss to a statute's own published number is a
publishable finding about process modelling. Corpus completeness is not a gate on
either leg, and no further parsing queue blocks either result.
