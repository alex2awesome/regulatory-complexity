from dataclasses import asdict
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_hierarchy import Config, HierarchicalModel
from pipeline.procbench.check_hierarchy import main as check_claims
from pipeline.procbench.check_hierarchy import clock_alternative_probability
from pipeline.procbench.check_effort import effort_diagnostics, expected_work_by_activity
from pipeline.procbench.sensitivity_hierarchy import main as check_sensitivity
from pipeline.procbench.validate_hierarchy import generated_evidence
from pipeline.procbench.run_hierarchical import main as fit_model


def test_clock_diagnostic_integrates_contamination_and_preserves_symmetry():
    bounds = np.log(np.array([[20.,22.]]))
    matching,other = np.log(np.array([21.])),np.log(np.array([3.]))
    probability = clock_alternative_probability(bounds,matching,other,.25,.08)
    assert 0<probability[0]<.05
    reverse = clock_alternative_probability(bounds,other,matching,.25,.08)
    assert probability+reverse == pytest.approx([1.])
    assert clock_alternative_probability(bounds,matching,matching,.25,.08) == pytest.approx([.5])


def saved_fixture(root, corrupt_likelihood=False, config_overrides=None):
    root.mkdir()
    evidence, _ = generated_evidence(n_cases=1)
    options = dict(chains=2,draws=8,warmup=0,thin=1,max_unseen=0,population_size=16)
    options.update(config_overrides or {})
    cfg = Config(**options)
    model = HierarchicalModel([evidence],cfg)
    z = np.full((2,8,model.layout.size),.2)
    structure = np.zeros((2,8,1,2),dtype=int)
    ll = np.full((2,8),model.log_likelihood(z[0,0],structure[0,0]))
    report = model.report(z,structure,ll)
    np.savez_compressed(root/'draws.npz',z=z,structure=structure,
                        log_likelihood=ll+int(corrupt_likelihood))
    for name, value in [('evidence',[evidence]),('manifest',{'config':asdict(cfg)}),('posterior',report)]:
        (root/f'{name}.json').write_text(json.dumps(value))


@pytest.mark.parametrize('checker',[check_claims,check_sensitivity])
def test_postprocessing_checks_saved_statistical_target(checker,tmp_path):
    root,out = tmp_path/'fit',tmp_path/'check'
    saved_fixture(root)
    checker(['--run',str(root),'--out',str(out),'--stride','1'])
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['saved_likelihood_max_error'] == 0
    assert manifest['evidence_sha256']


@pytest.mark.parametrize('checker',[check_claims,check_sensitivity])
def test_postprocessing_rejects_changed_statistical_target(checker,tmp_path):
    root,out = tmp_path/'fit',tmp_path/'check'
    saved_fixture(root,corrupt_likelihood=True)
    with pytest.raises(ValueError,match='Saved likelihood disagrees'):
        checker(['--run',str(root),'--out',str(out),'--stride','1'])
    assert not out.exists()


def test_sensitivity_does_not_claim_overlap_when_enlarging_a_point_prior(tmp_path):
    root,out = tmp_path/'fit',tmp_path/'check'
    saved_fixture(root,config_overrides=dict(max_unseen=2,unseen_mean=0.,source_bias_sd=0.))
    check_sensitivity(['--run',str(root),'--out',str(out),'--stride','1'])
    report = json.loads((out/'sensitivity.json').read_text())
    assert 'source_bias_0.7' in report['refits_required_for_prior_support']
    assert 'unseen_mean_1.0/4.0' in report['refits_required_for_prior_support']
    assert 'source_bias_0.7' not in report['results']


def test_work_hour_checks_include_case_spread_and_step_parameters():
    evidence,_ = generated_evidence(n_cases=1)
    for m in evidence['measurements']:
        m.update(metric='agency_work',unit='hours')
    model = HierarchicalModel([evidence],Config(channel='agency_work',max_unseen=0,population_size=16))
    z = np.full((2,8,model.layout.size),.2)
    z[1,:,model.hyper[5]] = 2.
    structure = np.zeros((2,8,1,2),dtype=int)
    diags = effort_diagnostics(model,z,structure,np.zeros((2,8)))
    assert diags['hyper:common']['rhat'] is None
    assert 'step:validation__generated:slow_held_out' in diags
    assert any(k.startswith('actor_effect:') for k in diags)


def test_analytic_work_mean_respects_conditional_and_alternative_routes():
    import copy
    evidence,_ = generated_evidence(n_cases=1)
    evidence['measurements'] = []
    evidence['activities'][0].update(scope='conditional',condition='requires special review')
    deny = copy.deepcopy(evidence['activities'][-1])
    deny.update(id='deny',scope='conditional',condition='denied')
    evidence['activities'].append(deny)
    model = HierarchicalModel([evidence],Config(channel='agency_work',global_median=.5,max_unseen=0))
    process = model.processes[0]
    z = np.zeros(model.layout.size)
    work = expected_work_by_activity(model,process,z)
    # Eight core operations plus half of the conditional operation. The two
    # decisions are alternatives and must contribute one operation, not two.
    assert work.sum() == pytest.approx(8.5*.5*np.exp(.5*.1**2))
    assert work[0] == pytest.approx(.25*np.exp(.5*.1**2))
    assert work[-1] == pytest.approx(work[-2])


def test_runner_preserves_partial_elapsed_diagnostics_and_refuses_overwrite(tmp_path):
    evidence,_ = generated_evidence(n_cases=1)
    source = tmp_path/'evidence.json'
    source.write_text(json.dumps(evidence))
    out = tmp_path/'fit'
    args = ['--evidence',str(source),'--out',str(out),'--chains','1',
            '--warmup','0','--draws','8','--thin','1','--max-unseen','0','--population-size','16']
    fit_model(args)
    partial = json.loads((out/'elapsed_posterior.json').read_text())
    final = json.loads((out/'posterior.json').read_text())
    manifest = json.loads((out/'manifest.json').read_text())
    assert 'effort' not in partial and 'effort' in final
    assert manifest['elapsed_completed_utc'] and manifest['completed_utc']
    assert (out/'work_progress.jsonl').exists()
    with pytest.raises(ValueError,match='Preserving existing or unfinished run'):
        fit_model(args)
