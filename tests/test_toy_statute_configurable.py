"""Whole-record compression and model-local configuration regressions."""
import copy
import json

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pipeline.procbench.toy_statute import estimands, readings, spec
from pipeline.procbench.toy_statute.config import ModelConfig, ExecutionConfig
from pipeline.procbench.toy_statute.compression import compress_admin
from pipeline.procbench.toy_statute.model import Model
from test_toy_statute_response_repairs import make_evidence


@pytest.fixture(autouse=True)
def restore():
    spec.use_design_space("menu6")
    yield
    spec.use_design_space("menu6")


@pytest.mark.parametrize("milestones", [False, True])
def test_compression_preserves_whole_case_marginal_likelihood(tmp_path, milestones):
    ev = make_evidence(tmp_path, milestones=milestones)
    path = ev / "admin_records.json"
    original = json.loads(path.read_text())
    rows = []
    for j in range(7):
        for row in original:
            rows.append(dict(row, record_id=f"distinct_project_{j}_{len(rows)}"))
    path.write_text(json.dumps(rows))
    full, compressed = Model(ev, compress_administrative=False), Model(ev)
    a, b = full.data['Amber'], compressed.data['Amber']
    assert len(b.admin_x) + b.n_ms < len(a.admin_x) + a.n_ms
    assert b.case_weights.sum() == a.case_weights.sum()
    for seed in (2, 8, 12):
        x = full.sample_prior_theta(np.random.default_rng(seed))
        assert_allclose(compressed.town_struct_loglik(x, 'Amber'), full.town_struct_loglik(x, 'Amber'), atol=1e-10, rtol=0)
        assert_allclose(compressed.struct_posterior(x, 'Amber'), full.struct_posterior(x, 'Amber'), atol=1e-12, rtol=0)


def test_compression_retains_cohort_and_joint_milestone_pairs():
    base = dict(town='A', submitted='2020-01-01', decided='2020-01-11', source='registry')
    a = dict(base, milestones={'complete':'2020-01-03'}, cohort='2020')
    b = dict(base, milestones={'complete':'2020-01-09'}, cohort='2020')
    c = dict(a, cohort='different_sampling_frame')
    rows = compress_admin([a, a, b, c])
    assert len(rows) == 3
    assert [r['multiplicity'] for r in rows] == [2, 1, 1]
    assert a.get('multiplicity') is None
    for value in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            compress_admin([dict(a, multiplicity=value)])


def test_configuration_is_model_local_and_reaches_summaries(tmp_path):
    from types import SimpleNamespace
    from pipeline.procbench.toy_statute import hypotheses
    ev = make_evidence(tmp_path)
    original = Model(ev)
    x = original.sample_prior_theta(np.random.default_rng(2))
    old = original.loglik(x)
    small = Model(ev, model_config={'day_grid_size':64, 'hour_grid_size':32, 'max_loops':2,
                                   'contamination_probability':.03, 'post_day_range':[5,180]})
    assert original.loglik(x) == old
    p = small.param_dict(x)
    assert estimands.day_step_pmfs(p, 'Amber').shape[1] == 64
    assert estimands.hour_step_pmfs(p).shape[1] == 32
    assert small.data['Amber'].combo_k.max() == 2
    e, pmf = estimands.town_estimands(p, 'Amber', 'S5', {})
    assert len(pmf) == estimands.total_support_length(small.config)
    assert e['total.days_mean'] == pytest.approx(sum(e[f'pstep_days.{s}'] for s in spec.DAY_STEPS))
    assert readings.burden_indices(p, 'Amber', {})[4] == pytest.approx(e['total.days_mean']+4*e['total.hours_mean'])
    summary_model = SimpleNamespace(towns=['Amber'], param_dict=lambda _:p, fee_table=lambda *args:{})
    cost, summaries = hypotheses.conditional_burdens(summary_model, [x])
    for di, sid in enumerate(spec.STRUCTURE_IDS):
        reference, _ = estimands.town_estimands(p, 'Amber', sid, {})
        assert summaries['total.days_mean'][0,0,di] == pytest.approx(reference['total.days_mean'])
        assert summaries['total.hours_mean'][0,0,di] == pytest.approx(reference['total.hours_mean'])
        assert summaries['complexity.expected_psteps'][0,0,di] == pytest.approx(reference['complexity.expected_psteps'])
    with pytest.raises(ValueError, match='configuration'):
        small.require_fit_target({'observation_model':original.observation_metadata})
    small.require_fit_target({'observation_model':small.observation_metadata})


@pytest.mark.parametrize('value', [{'day_grid_size':1}, {'max_loops':1.2}, {'contamination_probability':float('nan')},
                                 {'post_day_range':[10,5]}, {'observation_family':'partial'},
                                 {'process_family':'parallel'}, {'misspelled':1}])
def test_bad_model_config_fails(value):
    with pytest.raises(ValueError): ModelConfig.parse(value)


@pytest.mark.parametrize('value', [{'backend':'cpu','kernel':'hmc'}, {'batch_size':0}, {'hmc_steps':False},
                                 {'hmc_step_size':float('nan')}, {'bucket_towns':'yes'}, {'dtype':'float32'}])
def test_bad_execution_config_fails(value):
    with pytest.raises(ValueError): ExecutionConfig.parse(value)


def test_cli_records_scientific_and_execution_settings(tmp_path, monkeypatch):
    from pipeline.procbench.toy_statute import smc, fit
    class Immediate:
        def __init__(self, max_workers, initializer, initargs): initializer(*initargs)
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def map(self, fn, values): return map(fn, values)
    monkeypatch.setattr(smc,'ProcessPoolExecutor',Immediate)
    monkeypatch.setattr(fit,'N_ESTIMAND_DRAWS',2)
    ev=make_evidence(tmp_path)
    model_config=tmp_path/'model.json'; execution=tmp_path/'execution.json'
    model_config.write_text(json.dumps({'max_loops':2,'day_grid_size':64,'hour_grid_size':32}))
    execution.write_text(json.dumps({'backend':'cpu','kernel':'joint'}))
    output=tmp_path/'fit'
    smc.main(['--evidence',str(ev),'--out',str(output),'--model-config',str(model_config),
              '--execution-config',str(execution),'--particles','8','--moves','1','--workers','1','--runs','2'])
    manifest=json.loads((output/'manifest.json').read_text())
    answers=json.loads((output/'answers.json').read_text())
    assert manifest['model_config']['max_loops']==2
    assert manifest['execution_config']['backend']=='cpu'
    assert answers['model_metadata']['scientific_config']==manifest['model_config']
    assert manifest['model_config_sha256'] and manifest['execution_config_sha256']
    # This tiny run exercises wiring/provenance only, not posterior accuracy.
