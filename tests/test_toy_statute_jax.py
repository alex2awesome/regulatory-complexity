"""Optional accelerator tests; run explicitly on the task's JAX environment."""
import json
import copy

import pytest
import numpy as np

jax = pytest.importorskip('jax')
import jax.numpy as jnp

from pipeline.procbench.toy_statute import spec
from pipeline.procbench.toy_statute.model import Model
from pipeline.procbench.toy_statute.jax_backend import JaxModel
from pipeline.procbench.toy_statute.jax_pool import JaxPool
from pipeline.procbench.toy_statute.config import ExecutionConfig
from test_toy_statute_response_repairs import make_evidence


def test_extreme_conditional_grid_matches_cpu_and_has_finite_gradient():
    from pipeline.procbench.toy_statute.jax_backend import discretized
    from pipeline.procbench.toy_statute import grid
    mu = np.log([2.77e6, 14., 1e-10]); ls = np.log([.2,.6,.1])
    fn = lambda x: discretized(x,jnp.asarray(ls),512)
    np.testing.assert_allclose(np.asarray(fn(jnp.asarray(mu))),
                               grid.discretized_lognormal(np.exp(mu),np.exp(ls),512), atol=2e-10)
    grad = jax.grad(lambda x: jnp.sum(fn(x)*jnp.arange(512)))(jnp.asarray(mu))
    assert np.isfinite(np.asarray(grad)).all()


def test_native_intervals_and_unselected_reporting_match_cpu(tmp_path):
    spec.use_design_space('menu6')
    ev = make_evidence(tmp_path)
    rows = json.loads((ev/'reports.json').read_text())
    for r in rows:
        for g in r.get('gaps',[]):
            g['interval_days'] = [1.,56.]
            g.pop('value',None);g.pop('unit',None)
    (ev/'reports.json').write_text(json.dumps(rows))
    cpu = Model(ev,model_config={'day_grid_size':32,'hour_grid_size':32,'max_loops':2,
                                 'completion_selection':False,'score_timing_mask':False,
                                 'pending_contamination':True})
    other = JaxModel(cpu)
    x = cpu.sample_prior_theta(np.random.default_rng(8))
    np.testing.assert_allclose(float(other.loglik(x)),cpu.loglik(x),rtol=0,atol=1e-10)
    assert np.isfinite(np.asarray(other.value_grad(x)[1])).all()


@pytest.mark.parametrize('kernel', ['joint','hmc'])
def test_device_mutation_gaussian_target_and_reproducibility(kernel):
    pool = object.__new__(JaxPool)
    pool.config = ExecutionConfig(backend='jax', kernel=kernel, hmc_steps=4)
    class Gaussian:
        def _logprior(self, x): return -.5*jnp.sum(x*x)
        def _loglik(self, x): return -.5*x[0]**2
    pool.jm = Gaussian()
    X = jnp.zeros((2048,2)); zeros = jnp.zeros(2048)
    fn = jax.jit(pool._mutate, static_argnames=('moves',))
    args = (X,zeros,zeros,1.,jnp.eye(2),.6,jax.random.PRNGKey(7),jnp.ones(2048,dtype=bool))
    a = fn(*args,moves=128); b = fn(*args,moves=128)
    for x,y in zip(a,b): np.testing.assert_array_equal(x,y)
    assert np.max(np.abs(np.asarray(a[0]).mean(axis=0))) < .08
    np.testing.assert_allclose(np.asarray(a[0]).var(axis=0),[.5,1.],rtol=.12)
    assert 0 < int(a[3]) < 2048*128


def test_bucketed_copies_with_different_observations_match_cpu(tmp_path):
    spec.use_design_space('menu6')
    ev = make_evidence(tmp_path)
    for file in ('admin_records.json','reports.json','webpages.json','public_spec.json'):
        p = ev/file; value = json.loads(p.read_text())
        if isinstance(value,list):
            value += [dict(r,town='Birch') for r in copy.deepcopy(value)]
        elif file == 'webpages.json':
            value['Birch'] = copy.deepcopy(value['Amber'])
            field=next(iter(value['Birch']['listed_steps']))
            value['Birch']['listed_steps'][field]=not value['Birch']['listed_steps'][field]
        else: value['towns'].append('Birch')
        p.write_text(json.dumps(value))
    cpu = Model(ev,center_towns=True,model_config={'day_grid_size':64,'hour_grid_size':32,'max_loops':2})
    grouped = JaxModel(cpu,True); single = JaxModel(cpu,False)
    assert len(grouped.buckets) == 1 and len(single.buckets) == 2
    x = cpu.sample_prior_theta(np.random.default_rng(8))
    x[cpu.idx['la_Birch']] += .2
    for gpu in (grouped,single):
        np.testing.assert_allclose(float(gpu.loglik(x)),cpu.loglik(x),atol=1e-10,rtol=0)
        assert np.isfinite(np.asarray(gpu.value_grad(x)[1])).all()
