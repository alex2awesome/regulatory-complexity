# Same-estimand source comparisons: executable design screen

2026-09-20. Implements the comparison-support gate in the
[three-family plan](2026-09-20-three-statute-parse-verify-analysis-plan.md), before
adding learned source-type parameters. This is **not** a fitted trust model or
certification that a reviewer interpreted the documents correctly.

[source_comparisons.py](../pipeline/procbench/source_comparisons.py) accepts an
optional `source_comparisons` object in the ordinary integrated V6 data file.
The constructor checks it before sampling; preflight and posterior source-support
reports contain `declared_source_comparisons`. Nothing changes the likelihood,
parameter layout, priors or source taxonomy. Absent reviews remain explicitly
`not_declared`; matching endpoint strings never manufactures an overlap claim.

## Contract

The object has `schema_version: source-comparison-review/1`, `reference_type`
and `blocks`. Each block has `id`, `program_id`, `program_sha256`, `reviewer`,
`review_artifact_sha256` and `members`. The program digest binds its entire
input, including routes and observations. Every member contains:

| Field | Meaning |
|---|---|
| `observation_id`, `observation_sha256` | Exact ordinary input observation, including report values, operator and provenance |
| `source_type`, `document_id`, `lineage_id` | Reviewed source class, source edition and independent evidence lineage; no filename inference |
| `estimand` | Separate reviewed scope for this member, compared against all other members |
| `ascertainment` | Explicitly reviewed sampling/selection scope, not a reputation rating |

`estimand` requires `program_id`, `jurisdiction_id`, `policy_era`,
`window_start`, `window_end` (ISO dates), `population_id`, `outcome_condition`,
`route_scope`, `clock_start`, `clock_end` and `time_unit`. Canonical hashes use
`comparison_digest(value)`: sorted-key compact UTF-8 JSON, Unicode retained,
nonfinite values forbidden. Review artifact hashes declare provenance; this
module does not open or independently verify that artifact or its source text.
The existing semantic/effective-evidence review remains a prerequisite.

Stale hashes, unknown observations, repeated row use, reversed dates, inconsistent
source assignments and calendar mismatches fail before sampling. Different
populations, eras, endpoints, ascertainment or statistics stay visible as held
comparisons. A shared/copy lineage cannot supply independent support within or
across blocks. Two documents of the same source type are not a cross-type pair.

## Deliberately narrow statistical screen

Version 1 screens ordinary elapsed population `median`, `mean` or `p90` reports
with exactly the same statistic, one identical unambiguous operator, declared
population conditioning and reviewed scope. It does not equate an individual
duration with a population median. Individual/selected cases, subjective typical
ranges, exact cohorts and ambiguous operators remain outside **this rank
screen**, not outside V6's existing likelihoods. They need a joint comparison
design with sampling, statistic and dependence modeled explicitly.

For candidate blocks, the report computes the design rank for separate block
locations plus reference-type contrasts. It reports reference connectivity,
disconnected types, distinct block/type cells, document counts and types with
fewer than two documents. Repeated reports of the same block/type cannot create
extra rank or document replication. A document can report distinct cohorts with
separately reviewed lineages: `documents_spanning_blocks` exposes that reuse,
and `document_dependence_adjusted` remains false. The geometric screen does not
turn those cohorts into independent document effects. A connected indirect comparison is distinguished from direct
overlap by the per-block membership records.

Full rank is only a necessary geometric check in that reduced additive model.
It establishes neither full-hierarchy identification nor separability of source
bias, document effects, precision and selection. `bias_identification_established`
therefore remains false. Reference zero remains a convention. No amount, interval
width or fitted result selects a comparison or asserts one source is better.

## Verification and current data

Thirty-four focused cases cover stale bindings, default likelihood equality,
scope/statistic/selection mismatch, unresolved scopes, copy lineage, document
replication, disconnection and transitive overlap. Combined with existing
source-support tests: **45 passed**. The full suite: **1,276 passed**, one
pre-existing tiny-world return-value warning. The
[saved-fit replay](../runs/three_family_20260920/source_support_v5/receipt.json)
preserves the old solar likelihood exactly and C29/C44 to floating-point
roundoff. These are software checks, not source-bias recovery results.

No reviewed real-data comparison block has been admitted yet. The current
twelve-AHJ solar pilot has one source family, so it cannot learn a cross-source
contrast. The next step is source-bound matching plus crossed clean/selected/
outlier calibration fixtures, not declaring the new report itself a successful
source-heterogeneity fit.

### Independent review and repairs

The [independent code review](../runs/three_family_20260920/source_comparison_independent_review_v1/review.md)
found a finite-cohort exclusion missing from the standalone preflight (ordinary
V6 validation already rejected that input), and a source-taxonomy bug where a
present blank/null kind fell back to filename inference. Both are corrected.
The standalone check also rejects duplicate input identities and noncanonical
or invalid calendar dates. Same-document multi-cohort rank is retained but its
dependence is explicitly reported, not called independent replication.

Exact aliases now cover the new public document kinds, including application
guides, completion dashboards and applicant forums. Present unresolved kinds
remain unresolved; default document grouping is unchanged. These aliases are
taxonomy plumbing, not reliability ratings.

After these changes: **112 focused cases passed**, and **1,304 full-suite tests
passed** with the same pre-existing warning. The preceding 1,276-test receipt
remains historical and unchanged. The reference-anchored bias hierarchy is the
next opt-in implementation step, not part of this design screen's claims.
