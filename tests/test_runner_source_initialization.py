"""Source-free checks for explicit runner initialization and case-local opt-in."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench import run_visit_hierarchy as runner
from pipeline.procbench import bayes_trace_hierarchy as hierarchy


def observation(ident, case, lower, upper, activity):
    return dict(id=ident, case_id=case, source_family='fixture', sampling='unselected',
        statistic='individual', lower=lower, upper=upper,
        operators=[dict(basis='single_visit_cycle', activity_ids=[activity])],
        operator_weights=[1.])


def path_data():
    operations=[
        dict(id='file',actor_id='payer',actor_role='payer',task_type='filing',
             markers=['submission'],payer_work=True,agency_work=False),
        dict(id='approve',actor_id='agency',actor_role='agency',task_type='decision',
             markers=['decision'],payer_work=False,agency_work=True),
        dict(id='deny',actor_id='agency',actor_role='agency',task_type='decision',
             markers=['decision'],payer_work=False,agency_work=True),
    ]
    return dict(programs=[dict(id='fixture',routes=[dict(id='inventory',prior_weight=1.,
        operations=operations,paths=[
            dict(id='approved',probability_weight=1.,blocks=[dict(id='approved',operations=['file','approve'])]),
            dict(id='denied',probability_weight=1.,blocks=[dict(id='denied',operations=['file','deny'])]),
        ])],observations=[
            observation('a','a',1.,20.,'approve'),observation('b','b',1.,20.,'deny')],
        case_path_scope={'a':['approved'],'b':['denied']})])


def fixture(chains=2):
    cfg=Config(chains=chains,warmup=0,draws=8,population_size=16,
               modeled_channels=('elapsed',))
    model=VisitHierarchy(path_data(),cfg)
    z=np.zeros((chains,model.layout.size))
    structures=np.zeros((chains,len(model.programs)),dtype=np.int64)
    return cfg,model,z,structures


def save(path,z,structures,**extra):
    np.savez(path,z=z,structures=structures,**extra)


def test_real_model_initial_support_is_validated_and_hash_bound(tmp_path):
    cfg,model,z,structures=fixture()
    path=tmp_path/'initial.npz'; save(path,z,structures)
    initial,metadata=runner.load_source_initialization(path,model,cfg.chains)
    np.testing.assert_array_equal(initial[0],z)
    np.testing.assert_array_equal(initial[1],structures)
    assert metadata['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert metadata['chains']==2 and metadata['dimensions']==model.layout.size
    assert len(metadata['initial_full_log_likelihood'])==2
    assert all(np.isfinite(metadata['initial_full_log_likelihood']))


@pytest.mark.parametrize('dtype',[np.int64,np.float32,np.float64])
def test_loader_normalizes_real_numeric_states_to_float64(tmp_path,dtype):
    cfg,model,z,structures=fixture()
    z=(z+1).astype(dtype)
    path=tmp_path/'initial.npz'; save(path,z,structures)
    initial,_=runner.load_source_initialization(path,model,cfg.chains)
    assert initial[0].dtype==np.float64
    np.testing.assert_array_equal(initial[0],z.astype(np.float64))


@pytest.mark.parametrize('dtype',[np.int64,np.float32,np.float64])
def test_public_sampler_normalizes_initial_states_before_updates(monkeypatch,dtype):
    cfg,model,z,structures=fixture(chains=1)
    z=(z+1).astype(dtype)
    seen=[]
    def unchanged(state,block,likelihood,current,rng):
        assert state.dtype==np.float64
        seen.append(state.copy())
        return state,current,0
    monkeypatch.setattr(hierarchy,'elliptical_slice',unchanged)
    model.sample(initial=(z,structures))
    assert seen


@pytest.mark.parametrize('problem',[
    'extra_field','wrong_z_shape','wrong_structures_shape','float_structures',
    'boolean_structures','complex_state','invalid_route','nonfinite_state',
    'nonfinite_full_likelihood'])
def test_invalid_source_initialization_fails_closed(tmp_path,problem):
    cfg,model,z,structures=fixture()
    path=tmp_path/'initial.npz'
    if problem=='extra_field':
        save(path,z,structures,resume_iteration=np.array([10]))
    elif problem=='wrong_z_shape':
        save(path,z[:1],structures)
    elif problem=='wrong_structures_shape':
        save(path,z,structures[:1])
    elif problem=='float_structures':
        save(path,z,structures.astype(float))
    elif problem=='boolean_structures':
        save(path,z,structures.astype(bool))
    elif problem=='complex_state':
        save(path,z.astype(complex),structures)
    elif problem=='invalid_route':
        structures[:,0]=1; save(path,z,structures)
    elif problem=='nonfinite_state':
        z[0,0]=np.nan; save(path,z,structures)
    else:
        save(path,z,structures)
        model.log_likelihood=lambda *_: -np.inf
    with pytest.raises(ValueError):
        runner.load_source_initialization(path,model,cfg.chains)


def test_chain_dispatch_uses_exact_one_row_slices_and_case_local_keyword(tmp_path):
    cfg,_,z,structures=fixture(chains=3)
    z[:]=np.arange(z.size).reshape(z.shape)
    calls=[]
    class CapturePool:
        def submit(self,fn,*args,**kwargs):
            calls.append((fn,args,kwargs))
            return object()
    futures=runner.submit_chains(CapturePool(),path_data(),cfg,tmp_path,(z,structures),
                                 case_local_updates=True)
    assert len(futures)==len(calls)==3
    for index,(fn,args,kwargs) in enumerate(calls):
        assert fn is runner.worker and args[2]==index
        assert len(args)==4
        initial=kwargs['initial']
        assert initial[0].shape==(1,z.shape[1]) and initial[1].shape==(1,1)
        np.testing.assert_array_equal(initial[0],z[index:index+1])
        np.testing.assert_array_equal(initial[1],structures[index:index+1])
        assert kwargs['case_local_updates'] is True
    assert runner.chain_initial(None,0) is None


def test_default_dispatch_omits_initial_argument(tmp_path):
    cfg,_,_,_=fixture(chains=1)
    calls=[]
    class CapturePool:
        def submit(self,fn,*args,**kwargs):
            calls.append((fn,args,kwargs))
            return object()
    runner.submit_chains(CapturePool(),path_data(),cfg,tmp_path,None)
    _,args,kwargs=calls[0]
    assert len(args)==4
    assert 'initial' not in kwargs


@pytest.mark.parametrize('flags',[
    ['--diagnose-run','missing','--initial-state','missing.npz'],
    ['--diagnose-run','missing','--case-local-updates'],
    ['--data','missing','--marginalize-conditional-cases','--initial-state','missing.npz'],
    ['--data','missing','--marginalize-conditional-cases','--case-local-updates'],
    ['--data','missing','--histogram-ridge-moves','--initial-state','missing.npz'],
    ['--data','missing','--histogram-ridge-moves','--case-local-updates'],
])
def test_cli_refuses_incompatible_modes_before_reading_inputs(tmp_path,flags):
    with pytest.raises(SystemExit):
        runner.main(flags+['--out',str(tmp_path/'out')])


def test_preflight_validates_initial_state_and_case_views_without_sampling(tmp_path,monkeypatch):
    cfg,model,z,structures=fixture()
    data_path=tmp_path/'data.json'; data_path.write_text(json.dumps(path_data()))
    initial_path=tmp_path/'initial.npz'; save(initial_path,z,structures)
    out=tmp_path/'preflight'
    def forbidden(*args,**kwargs):
        raise AssertionError('Preflight must not launch workers or sample')
    monkeypatch.setattr(runner,'ProcessPoolExecutor',forbidden)
    monkeypatch.setattr(runner.VisitHierarchy,'sample',forbidden)
    runner.main(['--data',str(data_path),'--out',str(out),'--preflight',
        '--initial-state',str(initial_path),'--case-local-updates',
        '--observed-channels-only','--chains','2','--warmup','0','--draws','8',
        '--population-size','16'])
    report=json.loads((out/'preflight.json').read_text())
    manifest=json.loads((out/'manifest.json').read_text())
    assert report['sampling_performed'] is False
    assert report['source_initialization']['sha256']==hashlib.sha256(initial_path.read_bytes()).hexdigest()
    assert report['case_local_updates']['enabled'] is True
    assert report['case_local_updates']['case_coordinate_blocks']==2
    assert manifest['provenance']['input_sha256'][str(initial_path)]==report['source_initialization']['sha256']
    assert not (out/'draws.npz').exists() and not (out/'posterior.json').exists()


def test_omitted_options_do_not_add_provenance_fields(tmp_path):
    data_path=tmp_path/'data.json'; data_path.write_text(json.dumps(path_data()))
    out=tmp_path/'preflight'
    runner.main(['--data',str(data_path),'--out',str(out),'--preflight',
        '--observed-channels-only','--population-size','16'])
    report=json.loads((out/'preflight.json').read_text())
    manifest=json.loads((out/'manifest.json').read_text())
    assert 'source_initialization' not in report and 'case_local_updates' not in report
    assert 'source_initialization' not in manifest and 'case_local_updates' not in manifest
