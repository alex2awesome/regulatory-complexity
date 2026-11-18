"""Composition checks for the three default-off CalFresh proposals."""

from dataclasses import replace
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench import run_visit_hierarchy as runner
from procbench_fixtures import data_fixture


def elapsed_case_data():
    data=data_fixture()
    data['programs'][0]['observations']=[
        row for row in data['programs'][0]['observations']
        if all(op['basis'] not in {'visit_count','payer_hours','agency_hours'}
               for op in row['operators'])]
    return data


def test_initial_case_local_case_scale_and_rank_guard_compose_on_same_target():
    data=elapsed_case_data()
    cfg=Config(chains=1,warmup=1,draws=8,population_size=16,seed=991,
               modeled_channels=('elapsed',),operation_sd=0.,agency_sd=0.,task_sd=1.5,
               hierarchy_sampler='operation_centered',case_scale_sampler='interwoven')
    model=VisitHierarchy(data,cfg)
    initial=(np.zeros((1,model.layout.size),dtype=np.float32),
             np.zeros((1,len(model.programs)),dtype=np.int64))
    states,routes,likelihood,_=model.sample(initial=initial,case_local_updates=True)
    assert states.dtype==np.float64
    for state,structure,saved in zip(states[0],routes[0],likelihood[0]):
        assert saved==pytest.approx(model.log_likelihood(state,structure),abs=1e-10)

    blocked=VisitHierarchy(data,replace(cfg,hierarchy_sampler='blocked',
                                        case_scale_sampler='blocked'))
    assert blocked.layout.size==model.layout.size
    probe=np.random.default_rng(992).normal(size=model.layout.size)
    structure=np.zeros(len(model.programs),dtype=int)
    assert model.log_likelihood(probe,structure)==blocked.log_likelihood(probe,structure)


def test_all_new_sampler_controls_are_default_off():
    cfg=Config()
    assert cfg.hierarchy_sampler=='blocked'
    assert cfg.case_scale_sampler=='blocked'


def test_runner_preflight_composes_initial_case_local_and_case_scale(tmp_path):
    data=elapsed_case_data()
    cfg=Config(chains=1,warmup=0,draws=8,population_size=16,
               case_scale_sampler='interwoven')
    model=VisitHierarchy(data,cfg)
    data_path=tmp_path/'data.json'
    data_path.write_text(json.dumps(data))
    initial_path=tmp_path/'initial.npz'
    np.savez(initial_path,
             z=np.zeros((1,model.layout.size),dtype=np.float32),
             structures=np.zeros((1,len(model.programs)),dtype=np.int64))
    out=tmp_path/'preflight'
    runner.main(['--data',str(data_path),'--out',str(out),'--preflight',
                 '--initial-state',str(initial_path),'--case-local-updates',
                 '--case-scale-sampler','interwoven','--chains','1','--warmup','0',
                 '--draws','8','--population-size','16'])
    report=json.loads((out/'preflight.json').read_text())
    assert report['sampling_performed'] is False
    assert report['case_scale_transition']['enabled'] is True
    assert report['case_local_updates']['enabled'] is True
    assert report['source_initialization']['chains']==1
