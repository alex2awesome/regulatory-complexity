import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compare_visit_integration import assert_nested_evidence
from pipeline.procbench.generate_visit_interpretations import cycle_cdf, generate


def test_truth_clock_distribution_agrees_with_independent_simulation():
    rng = np.random.default_rng(4812)
    cycles = np.exp(np.log([2., 8.])+.35*rng.normal(size=(200000, 2))).sum(axis=1)
    for value in (7., 10., 14.):
        assert cycle_cdf(value) == pytest.approx(np.mean(cycles <= value), abs=.004)
    assert cycle_cdf(0.) == 0.


def test_frozen_interpretation_conditions_keep_every_original_claim():
    conditions, truth = generate()
    assert truth['geometric_tail_bound'] < 1e-14
    assert truth['process_quantiles']['initial_decision_median_days'] < truth['process_quantiles']['final_decision_median_days']
    assert truth['mean_visit_count'] == 3.
    base = conditions['timing_count_only']
    for name, data in conditions.items():
        assert_nested_evidence(base, data)
        model = VisitHierarchy(data, Config(population_size=16))
        assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [0]))
        assert 'realized_cases' not in data
    added = conditions['mixed_residual25']['programs'][0]['observations'][20:]
    assert len(added) == 10
    assert all(o['operator_weights'] == [.25]*4 for o in added)
    changed = copy.deepcopy(conditions['mixed_residual25'])
    changed['programs'][0]['observations'][0]['lower'] *= 2
    with pytest.raises(ValueError, match='changed or removed'):
        assert_nested_evidence(base, changed)
