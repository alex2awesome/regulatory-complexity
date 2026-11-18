# Solar leg, stages 0 and A: frozen estimands and the design audit

Executed against `docs/2026-09-20-solar-leg-plan-for-claude.md`. No model has been
fitted. No benchmark truth was read, no network was used, no input file outside
this leg's own run directory was modified.

Artefacts:

| | |
|---|---|
| frozen estimands, splits, baselines, decision rule | `runs/solar_panel_20260920/estimands_frozen_v1.json` |
| panel | `runs/solar_panel_20260920/panel_v1.csv`, 22,512 rows |
| build manifest with input hashes | `runs/solar_panel_20260920/panel_build_manifest.json` |
| design audit | `runs/solar_panel_20260920/design_audit_v1.json` |
| code | `pipeline/procbench/solar_panel/build_panel.py`, `audit_design.py` |

## Stage 0: what is frozen

Four estimands, each with its population, endpoints and units: authority phase
time; authority load elasticity, defined as the change in that time per doubling
of installations in the same cell; the composed applicant total wait; and the
utility-level reporting offset. Estimand 1 covers permit review and inspection
only, because plan section 2c established that the two interconnection phases are
utility-level values repeated once per served authority.

Both held-out splits are frozen by rule, not by inspection. Authorities are held
out when the SHA-256 of the owner id with a recorded salt is congruent to zero
modulo five, which is reproducible from the id alone. The forward-year split is
2022, the last year in the window.

Three baselines are named in advance: the raw cell median, a two-way fixed-effects
regression, and a language model given the same information. The decision rule is
explicit. The model passes only if it beats the first two baselines on interval
score on both splits and achieves coverage between 0.85 and 0.95. A loss to the
raw medians is a reportable finding and does not license acquiring more data.

Six prohibitions are recorded, including that installation counts may never be
used as the sample size behind a median, and that no automation-mandate or
net-metering effect may be reported from this window.

## Stage A: the panel

Built from Codex's corrected owner-consolidated coverage matrix, not from the raw
long file, so the repeated utility rows cannot be double counted. The raw file is
read only for installation counts and for which utility serves an authority.

| | |
|---|---:|
| slots in the 2017 to 2022 window | 22,512 |
| present cells | 7,366 |
| permit review / inspection, authority level | 3,711 / 3,258 |
| pre-install interconnection / final to permission to operate, utility level | 189 / 208 |
| authority owners, and those with at least one cell | 440 and 433 |
| utility owners with at least one cell | 28 |
| authorities held out by the frozen rule | 90 of 461, 19.5% |
| cells held out by authority / by forward year | 1,356 / 2,061 |

County, population and rurality joined for all but three owners: Cathedral City,
Laguna Woods and the state housing department. The first two are genuinely absent
from the housing crosswalk, so they are carried as missing rather than assigned
from memory, which would be inventing a source.

## The gates

**Gate 1, authority separability: passes.** On the 6,969 authority-level cells the
design matrix has 441 columns and rank 441, so the deficiency is zero. Every
retained authority, year, phase, size-class and technology contrast is estimable.
This is the gate that failed in the earlier 60-authority fits, where every
operation belonged to exactly one agency and the hierarchy could not be separated.
It passes here because authorities are observed across years and phases.

**Gate 2, provenance: trips as written, and the gate is the wrong instrument.**
83.7% of present cells rest on a single source row, far past the quarter that the
plan said to report before any estimate. Having run it, I inspected what the field
counts. `source_row_count` is the number of raw rows consolidated into one owner
cell, and the dominant case is one geographic identifier with one source row,
which is simply an authority that needed no consolidation. It is not a sample size
and not a corroboration count. So the gate tests a property that does not mean
what I assumed when I froze it. I have reported it as frozen and recorded that it
is uninformative, rather than quietly redefining it. The real provenance
limitation is unchanged and separate: the number of projects behind each median is
unknown and bounded above only by the installation count.

**Elasticity kill criterion: survives.** The threshold was 200 authorities with
four or more usable years. There are 346, and the figure is stable as the
installation floor rises: 346 at floors of one and five, 335 at ten, and 231 at
thirty. Estimand 2 stands.

## What the audit found beyond the gates

**Exposure range is adequate but smaller than my earlier figure.** Within an
authority and stratum, across 560 qualifying strata, annual installations swing by
a median factor of 4.19, with quartiles of 2.89 and 6.95. That is about two
doublings, which is enough to identify an elasticity. My earlier claim of 6.9
times was computed by pooling strata within an authority and is superseded.

**Reported zeros split three ways, and only one is clean.** Of 376 zeros, 323 are
same-day approvals, all in permit review, and those are measured zeros belonging
in the model as a sub-day interval. 42 are the ambiguous pre-install category,
where a zero may mean the step does not exist or may mean it took no time; those
are different processes and must be held or modelled as a mixture, never treated
silently as a fast step. The remaining 11 are declared as genuine zero business
days.

**The same-day interval convention matters more than most effects we will
estimate.** 323 cells, 4.4% of the panel, are affected, and the two candidate
conventions differ by 0.693 on the log scale. Against a median of 12 business days
for positive cells, this is a declared sensitivity to run both ways, not a default
to choose quietly.

**A threat the plan did not anticipate, surfaced here.** Panel coverage expands
over the window, from 208 authorities and 391 cells in 2017 to 421 authorities and
1,958 cells in 2022, and that expansion runs in the same direction as the
installation boom. Most entry is early, with 345 of 433 authorities present by
2018, and the median installation count in an authority's first observed year
falls from 101 in 2017 to the twenties later, which looks like widening coverage
rather than authorities crossing a volume threshold. Within-authority minimum
observed volume has a median of 52 and a tenth percentile of 12, so the exposure
range is not badly truncated from below. Stage B must nevertheless estimate the
elasticity on the balanced subpanel of authorities present in all six years as a
sensitivity, because coverage growth and volume growth are confounded.

## A defect in the source matrix, reported not edited

For utility-scoped owners, Codex's coverage matrix carries the utility's EIA
identifier in the `state` column instead of a state code. Filtering on state, the
obvious thing to do, silently drops every utility-phase row. My first build did
exactly that and lost all 397 utility cells and two of the three zero semantics.
My reader now admits utility-scoped rows on their scope, since the source file is
California-only. Codex's file is unmodified and this is flagged for them.

## Verdict, and what Stage B inherits

Stage A clears. The authority effect is separable, the elasticity estimand
survives its kill criterion, and the panel is built with its provenance and
missingness carried rather than filled.

Three things Stage B must handle that are now measured rather than assumed: the
same-day convention as a two-way sensitivity; the ambiguous pre-install zeros held
out of the authority analysis; and the balanced-subpanel check for coverage
expansion. The provenance gate should be replaced in a versioned successor to the
frozen estimands file, since it does not measure what it was written to measure,
with the original preserved and the reason recorded.
