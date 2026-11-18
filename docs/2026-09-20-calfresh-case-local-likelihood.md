# CalFresh: exact case-local likelihood evaluation

The 47-case joint input exposed a computational bottleneck: V6 recomputed all
case likelihoods when updating only one case's latent timing. A source-supported
state took about 0.006 seconds per full evaluation. With 53 update blocks,
3,000 sweeps and four chains on two workers, even one evaluation per update
implied over 31 minutes per condition, before slice-bracket retries.

The new opt-in `case_local_updates=True` reuses the existing likelihood on a
one-case compiled view. It changes no priors, observations, latent coordinates,
path semantics, draw counts or diagnostic gates. This is not another Bayesian
architecture or an approximate likelihood.

For an exact case-coordinate block, other cases and population/cohort factors
are constant. The elliptical-slice threshold uses the old local factor. After
acceptance, the complete log likelihood changes by `new_local - old_local`.
Before any subsequent nonlocal update, and at the end of a local-update
sequence, the sampler recomputes the complete target and fails if it disagrees.
The full value, not an unchecked accumulated approximation, is used thereafter.

Views preserve the case's joint path, all its report groups, fixed path priors,
optional-event censoring, and selection numerator/normalizer. Source, task,
route, repeat, phase and dwell parameters retain their existing meaning. Only
observation arrays and case rows are sliced; shared-group columns are remapped.
Trace and selection caches are view-local and parameter-keyed. Non-case blocks
and programs without explicit paths retain full-target evaluation. Defaults are
unchanged; the histogram-ridge opt-in cannot be combined with this one.

At the supported real-data starting state, all 47 local factors exactly matched
their full-target contributions. Mean local evaluation time was 0.000341 seconds,
about 17.5 times faster than a full evaluation. This is a factor-level timing,
not a full-fit speed guarantee or a convergence result.

Implementation: [compiled views](../pipeline/procbench/case_local_likelihood.py),
[sampler](../pipeline/procbench/bayes_trace_hierarchy.py),
[worker](../pipeline/procbench/run_visit_hierarchy.py), and
[tests](../tests/test_case_local_likelihood.py).
The [pre-fit computational addendum](../runs/three_family_20260920/calfresh_joint47_execution_v1/case_local_computational_addendum.json)
preserves the original scientific protocol and requires fresh source bindings.
The original candidate preflight and baseline launch plan remain historical;
their earlier source hashes are not silently rewritten.

The [independent review](../runs/three_family_20260920/calfresh_case_local_likelihood_review_v1/report.md)
passes after adding full-target refreshes before later nonlocal blocks in
multi-program layouts. Fifteen focused tests pass; the repository's `tests/`
suite passes all 1888 tests. The
[root receipt](../runs/three_family_20260920/calfresh_case_local_likelihood_review_v1/root_adoption.md)
also records the initial overly broad collection failure rather than treating
archived/vendor tests as an executed suite.
