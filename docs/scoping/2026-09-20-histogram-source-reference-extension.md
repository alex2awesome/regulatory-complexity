# Exact-cohort reference for the existing V6 source hierarchy

2026-09-20. Bounded implementation proposal within the approved source-trust
work. No real fit, transport claim, prior-default change or new architecture.

## Reproduced gap

An invented fixture with one exact administrative histogram and one forum case
has a finite legacy likelihood (`-8.915803776576334` at the zero state). Under
`source-offset-hierarchy/1`, a declaration containing only the actual forum
report document fails with "Reference source type has no mapped duration
document." Adding the histogram's administrative family to the document mapping
also fails: it is not a noisy duration-report document. Both guards are correct
for the narrow v1 contract; together they leave this useful combination
unsupported. No row was silently dropped and the real pilots did not use this
hierarchy.

Exact histogram counts correctly have no reporting offset, precision kernel or
contamination component. Inventing an additional administrative median or
zero-width report would double-count data and is not a repair.

## Narrow v2 contract

Keep v1 and absent declarations unchanged. Opt-in `source-offset-hierarchy/2`
adds a nonempty `reference_histogram_cohorts` list. Each member identifies a
program, cohort ID, source family and canonical SHA-256 of the complete original
cohort object. Resolve it against the supplied input, which the model already
validates as exact, independent elapsed-bin counts. Reject absent, stale,
ambiguous or duplicated references and a cohort from another source family.
All anchors are assigned the declared `reference_type`; any report document
sharing an anchor's family must have that same type.

An exact-cohort anchor permits a reference type with no noisy-report documents.
Its effect stays zero, and every actual nonreference report type retains its
existing free type effect and centered document residuals. Allocate no dummy
document, case, coordinate or extra likelihood factor for the anchor. Preserve
exact histogram likelihoods and all reporting/selection behavior.

Reports must distinguish reference histogram counts/factors from informative
narrative-report rows and say that reference zero is a modeling convention.
Digest validation proves only input identity, not truthful counts, completeness,
unbiased sampling, matched populations or source calibration. Existing semantic
admission, dependence, clock and selection reviews remain required. The ordinary
summary-only comparison/rank checker must not silently certify case/cohort
comparisons. Unmatched real-data rows remain held.

## Checks before adoption

- V1/absent declaration: identical coordinates, likelihoods and short seeded
  trajectories against the frozen source, on source-free fixtures.
- Valid exact-histogram plus forum case: both factors survive once; changing
  the forum type effect changes its report factor but not histogram probability.
- Scalar and vectorized likelihoods agree at tested states; no duplicate
  cohort factor or source coordinate appears in support reporting.
- Reject stale hashes, missing/duplicated references, wrong program/source,
  nonexact/nonindependent cohorts and ambiguous reference identities.
- Reference diagnostics state the actual cohort/factor/case counts and never
  infer empirical trust or a matched comparison from contract acceptance.
- Separate-agent counterexample review, existing regression suite and a
  preserved pre-edit snapshot. No real rerun under this implementation tranche.

Pre-edit core SHA-256:
`ac56a6d0e28322345e4c095282e6598d88a89309fdee55c39f0e49a28f89e352`.
Pre-edit source hierarchy SHA-256:
`0cdda0fffdd8cab7016df678134a6f21b84c5a6f3dcdfeb988d63785ab4804ac`.
