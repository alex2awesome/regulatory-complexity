"""Bounded regression tests for the real-data refit, including the ADU failure."""
import json
import math

import numpy as np
from scipy.special import ndtr

from pipeline.procbench.toy_statute import grid, spec
from pipeline.procbench.toy_statute.model import Model
from test_toy_statute_response_repairs import make_evidence


def test_far_above_grid_lognormal_is_conditional_not_zero_mass():
    p = grid.discretized_lognormal([2.77e6, 1e12, 1e-10], [.2, .15, .1], 512)
    np.testing.assert_allclose(p.sum(axis=1), 1, atol=2e-11)
    assert np.isfinite(p).all() and (p >= 0).all()
    assert p[0, -1] > .1 and p[-1, 0] == 1


def test_lognormal_matches_ordinary_cdf_and_geometric_endpoints():
    p = grid.discretized_lognormal([14.], [.6], 512)[0]
    edges = np.maximum(np.arange(513)-.5, 1e-300)
    cdf = ndtr((np.log(edges)-math.log(14))/.6)
    q = np.diff(cdf); q /= q.sum()
    np.testing.assert_allclose(p, q, atol=2e-16)
    np.testing.assert_allclose(grid.truncated_geometric(1,5), np.ones(6)/6)
    np.testing.assert_array_equal(grid.truncated_geometric(0,5), [1,0,0,0,0,0])


def test_full_survival_retains_tiny_tail_and_no_immortal_mass():
    p = np.array([[1., 1e-25, 1e-40]])
    np.testing.assert_allclose(grid.survival_from_full_pmf(p,[0,1,2,20]),
                               [[1e-25+1e-40,1e-40,0,0]],rtol=1e-14,atol=0)


def test_native_interval_kernel_does_not_use_midpoint():
    p = grid.report_lik_days((28.,56.),'interval',.01,100)
    assert p[30] > .99 and p[50] > .99 and p[60] < 1e-10


def test_real_reporting_options_and_exact_prior_controls(tmp_path):
    spec.use_design_space('menu6')
    ev = make_evidence(tmp_path)
    rows = json.loads((ev/'reports.json').read_text())
    for r in rows:
        r.pop('hours_total',None)
        for g in r.get('gaps',[]):
            g['interval_days'] = [1.,56.]
            g.pop('value',None); g.pop('unit',None)
    (ev/'reports.json').write_text(json.dumps(rows))
    m = Model(ev, model_config={'day_grid_size':32,'hour_grid_size':32,'max_loops':2,
                               'completion_selection':False,'score_timing_mask':False})
    x = m.sample_prior_theta(np.random.default_rng(8)); before = m.loglik(x)
    assert np.isfinite(before)
    for n in m.prior_only_names(): x[m.idx[n]] += .4
    assert m.loglik(x) == before
    assert m.prior_only_names()
    assert (m.surv_post == 1).all()
    for d in m.data.values():
        mask = m.timing_mask_loglik(d)
        assert (mask[d.timing_compatible] == 0).all()
