# Optional reference-anchored source-bias hierarchy in V6

## Status and scope

V6 now has an optional, declaration-driven hierarchy for systematic source
bias in elapsed-duration reports. It is part of the existing
`VisitHierarchy`; it is not a separate model. The declaration is off by
default. When it is absent, the historical coordinate layout, fixed
per-source prior scale, likelihood, and source/location transition remain
unchanged. No existing real-data fit enables this hierarchy, and this document
reports no real-data or rendered-corpus recovery result. Source-free numerical
development is recorded separately below.

All real fits remain off for this option. The declaration-absent default still
uses the legacy independent source offsets with `Config.source_sd=0.25`; no
production default, saved coordinate layout, or historical likelihood target
was changed to enable the new hierarchy.

This first version changes source bias only. It does not learn or alter report
precision, contamination, selection, calendars, inventories, or source
reliability. It is restricted to configurations whose modeled channels are
exactly `("elapsed",)`. Labor-channel source effects are refused rather than
silently assigned this elapsed-time parameterization.

The implementation is in
[`source_offset_hierarchy.py`](../pipeline/procbench/source_offset_hierarchy.py)
and is integrated into
[`bayes_trace_hierarchy.py`](../pipeline/procbench/bayes_trace_hierarchy.py).
Its source-free mechanical gate is frozen separately in the
[`source-bias mechanics protocol`](scoping/2026-09-20-source-bias-mechanics-protocol.md).

## Input contract

The opt-in declaration is a top-level member of the V6 input:

```json
{
  "source_offset_hierarchy": {
    "schema_version": "source-offset-hierarchy/1",
    "source_family_grouping": "document",
    "elapsed_time_unit": "calendar_days",
    "reference_type": "declared_reference_type",
    "type_scale_prior": {
      "median": 1.0,
      "log_sd": 0.5
    },
    "document_scale_prior": {
      "median": 1.0,
      "log_sd": 0.5
    },
    "documents": [
      {
        "document_id": "exact_duration_source_family_id",
        "source_type": "declared_reference_type"
      },
      {
        "document_id": "another_duration_source_family_id",
        "source_type": "another_declared_type"
      }
    ]
  }
}
```

The numeric prior values in this schema example are illustrative, not defaults
or calibrated recommendations.

The schema is strict: extra or missing fields are rejected. Names must be
nonempty, trimmed, and resolved rather than placeholders such as `unknown`.
Prior medians and log standard deviations must be positive finite numbers.
The declared elapsed-time unit must equal the V6 model unit; no calendar
conversion is implicit.

Document IDs must be distinct and must exactly equal the set of source-family
IDs having at least one non-residual elapsed-duration candidate. The reference
type must have a mapped duration document, and at least one nonreference type
must be present. This exact mapping preserves the document level needed for
nested residuals. A declaration marked as type-grouped, a duplicate document
ID, or a declaration that omits or adds a duration family is refused. The
`source_family_grouping` field remains a supplied assertion, not independent
proof that an upstream identifier is semantically a document.

If a validated `source_comparisons` review is also supplied, any document ID
shared by the two declarations must have the same source type. A conflict is a
hard error. Agreement is only internal consistency; it does not turn the
source-comparison rank screen into evidence of source truth.

## Parameterization

Let source type `0` be the declared reference. Let type `t` contain `n_t`
documents. Every sampled coordinate below has an independent standard-normal
prior.

The shared positive type spread is

\[
\tau_{\mathrm{type}}
  = m_{\mathrm{type}}\exp(s_{\mathrm{type}}z_{\tau,\mathrm{type}}),
\qquad z_{\tau,\mathrm{type}}\sim N(0,1).
\]

The reference mean is fixed exactly to zero, while each nonreference type has

\[
\alpha_0=0,
\qquad
\alpha_t=\tau_{\mathrm{type}}z_t,
\quad z_t\sim N(0,1),\quad t>0.
\]

Fixing `alpha_0` is an anchoring convention. It does not assert that the
reference type is unbiased.

When at least one type has two or more documents, V6 also allocates one shared
positive document spread,

\[
\tau_{\mathrm{doc}}
  =m_{\mathrm{doc}}\exp(s_{\mathrm{doc}}z_{\tau,\mathrm{doc}}).
\]

For a type with `n_t >= 2`, let `Q_t` be the `n_t` by `n_t-1` orthonormal
Helmert contrast matrix. Thus

\[
Q_t^TQ_t=I,\qquad \mathbf 1^TQ_t=0,\qquad
Q_tQ_t^T=I-\frac{1}{n_t}\mathbf 1\mathbf 1^T.
\]

Its document residual vector is

\[
\delta_t=\tau_{\mathrm{doc}}Q_tz_{\mathrm{doc},t},
\qquad z_{\mathrm{doc},t}\sim N(0,I_{n_t-1}).
\]

Consequently, document residuals sum to zero within each type. Conditional on
`tau_doc`, each document residual has variance
`tau_doc^2 (1 - 1/n_t)`. A type with one document has residual zero and no
document coordinate. The effective log offset for document `d` of type `t` is

\[
b_{td}=\alpha_t+\delta_{td}.
\]

There is no unconstrained full set of both type and document effects, so the
parameterization does not introduce the redundant type/document translation
ridge that centering is meant to remove.

If there are `T` represented types and `D=sum_t n_t` duration documents, the
source hierarchy has

\[
1+(T-1)+\mathbf 1[D>T]+\sum_t(n_t-1)
=D+\mathbf 1[D>T]
\]

whitened coordinates. The indicator is the document-spread coordinate, which
exists only when document replication exists. Singleton types contribute no
document contrast coordinate.

## Likelihood meaning

For an elapsed-duration report whose latent process value is `v`, the existing
duration kernel uses location

\[
\log(v)+b_{td}.
\]

The interval-report likelihood, reporting scale, and contamination mixture
are otherwise unchanged. A positive `b_td` therefore means reports from that
document are centered multiplicatively above the latent process duration by
`exp(b_td)`; it does not lengthen the latent process itself.

The transformed document offsets are supplied through the existing
`parameters()["source"]` interface. Scalar and vectorized likelihood paths,
finite quantile-cohort likelihoods and interpretation weights, support
summaries, and operation-plus-source diagnostics therefore consume the same
transformed offset. Latent process burden predictions remain source-offset
free, as before. The historical fixed-scale source/location ridge transition
is an exact no-op in hierarchy mode because its direction is not
prior-preserving under learned scales and centered document contrasts.

The following sources do not receive this hierarchy:

- Count reports retain their existing discrete reporting kernel and no source
  offset.
- Money reports retain a zero source offset; published amounts are not timing
  measurements.
- Residual-only `unmodeled_duration` alternatives remain process-independent
  references.
- Exact histogram cohorts retain provenance only, with no narrative source
  offset, report-noise coordinate, or contamination coordinate.
- Payer-hours and agency-hours channels are outside this first version.

## Prior moments and reported summaries

For a scale `tau=m exp(sz)`,

\[
E[\tau^2]=m^2\exp(2s^2),
\]

and

\[
\operatorname{Var}(\tau)
=m^2\exp(s^2)\left(\exp(s^2)-1\right).
\]

Accordingly, a nonreference type effect has analytic prior variance

\[
\operatorname{Var}(\alpha_t)
=m_{\mathrm{type}}^2\exp(2s_{\mathrm{type}}^2),
\]

and a document residual in a type of size `n_t` has

\[
\operatorname{Var}(\delta_{td})
=\left(1-\frac1{n_t}\right)
 m_{\mathrm{doc}}^2\exp(2s_{\mathrm{doc}}^2).
\]

Because the type and document terms use independent coordinates, the analytic
prior variance of `b_td` is the sum of the applicable terms. The reference
type contributes no type-effect variance; a singleton reference document is
fixed at exactly zero.

Reports use these analytic variances for transformed log-offset and scale
marginal-contraction calculations. Prior interval quantiles for transformed
log offsets are deterministic numerical summaries from a fixed local draw and
are labeled as such. Marginal variance contraction is parameterization
dependent and is not identification.

Multiplier summaries require an additional qualification. For any
nondegenerate term of the form `b=tau z` with lognormal `tau`,
`E[exp(b)]` and `Var(exp(b))` are infinite. V6 therefore does not report a
multiplier prior mean, multiplier variance, or multiplier variance
contraction. It reports multiplier medians and intervals by exponentiating
log-offset quantiles. If an exponentiated quantile exceeds finite floating
point range, its numeric value is `null` while the finite log quantile and an
overflow flag are retained. The fixed-zero case alone has multiplier mean one
and variance zero.

## Optional transition kernel

`Config.source_hierarchy_sampler="blocked"` remains the default. The opt-in
`"interwoven"` mode splits the independent-normal source ESS blocks and adds
fixed-actual-effect scale moves with their Gaussian-prior and Jacobian
corrections. The CLI exposes the same choice with
`--source-hierarchy-sampler`. There is no change to the statistical target;
without a hierarchy declaration the extra mechanism is a bitwise RNG no-op.

The initial blocked source-free fit failed its predeclared extended convergence
gate. The separately recorded [numerical development protocol](scoping/2026-09-20-source-bias-sampler-development-02.md)
preserves that failure and defines the optional-kernel check prospectively.
It is not an unseen validation experiment. Transformed type means, both
spreads, centered document residuals and effective offsets now also participate
directly in the convergence gate; fixed reference zeros are marked deterministic.

## Support and interpretation limits

The source-support report distinguishes:

- membership in the declared hierarchy;
- whether a free coordinate can affect a document offset;
- an exact fixed-zero reference offset;
- duration-candidate row counts by document and type;
- limited-replication warnings; and
- measured transformed marginal contraction below the declared reporting
  threshold.

Replication counts are structural warnings, not a proof that a scale was or
was not learned. Conversely, posterior contraction does not establish semantic
comparability, full identification, unbiasedness, or transportability. Sparse
type and document replication can leave the shared scales strongly
prior-sensitive even when some effective offsets move away from their priors.

The hierarchy assumes the declared type grouping and exchangeability model. It
does not repair copied evidence, document dependence, incompatible clocks or
populations, selection into publication, institutional selection, or missing
process operations. Source type, document identity, and reference choice are
inputs, not inferred facts.

The reduced declared-review rank screen in
[`source_comparisons.py`](../pipeline/procbench/source_comparisons.py) is useful
for checking proposed contrasts but is insufficient to certify this learned
hierarchy. The broader distinctions among source bias, reporting precision,
contamination, and selection are recorded in the
[`source-trust note`](2026-09-20-source-trust-note-for-codex.md), and the
three-family workflow boundaries are in the
[`parse/verify/analysis plan`](2026-09-20-three-statute-parse-verify-analysis-plan.md).

## Verification boundary

The implementation was checked with source-free mechanical fixtures covering
strict declaration validation, calendar and channel refusal, exact coordinate
counts, reference anchoring, within-type centering, singleton behavior,
analytic prior-variance formulas, multiplier moment handling, strict JSON
serialization under broad priors, source-comparison type conflicts, scalar and
vectorized likelihood agreement, the analytic single-phase path, sampler
compatibility, transformed reporting, and frozen legacy replay.

At the latest checkpoint, `python -m pytest tests
benchmark/synth/generator/test_generator.py -q` reported **1,344 passed**, with
one pre-existing generator-test return-value warning. This combined count
establishes mechanical regression coverage only.

The [source-free recovery results](2026-09-20-source-bias-mechanical-results.md)
now report six numerically usable hierarchy fits and successful relative-shift
checks. The full comparison remains failed because one legacy control does not
converge within its declared budget. Independent scoring replay reproduces all
reported values. These are deliberately aligned mathematical fixtures, not
real-source trust calibration, realistic rendered-corpus validation or evidence
against an LLM baseline. The hierarchy remains disabled in real fits.
