from pipeline.procbench.evaluate_burden import realized_burden
from pipeline.procbench.compare_evidence_runs import check_matched_inputs, score_baseline
import pytest
from pipeline.procbench.evidence_support import burden_support
import math
import hashlib
import json


@pytest.mark.parametrize('failure',['unfinished','posterior_hash','different_inputs'])
def test_comparison_does_not_read_gold_before_provenance_checks(tmp_path,monkeypatch,failure):
    from pipeline.procbench import compare_evidence_runs as comparison
    run,baseline = tmp_path/'fit',tmp_path/'baseline'
    run.mkdir()
    baseline.mkdir()
    posterior = run/'posterior.json'
    posterior.write_text(json.dumps({'programs':{}}))
    manifest = {'posterior_sha256':hashlib.sha256(posterior.read_bytes()).hexdigest(),
                'completed_utc':'saved before evaluation','input_sha256':{'evidence':'same'}}
    control = {'input_sha256':{'evidence':'same'},'hidden_truth_provided':False,
               'bayesian_predictions_provided':False}
    if failure=='unfinished':
        manifest.pop('completed_utc')
    elif failure=='posterior_hash':
        manifest['posterior_sha256'] = 'changed'
    else:
        control['input_sha256']['evidence'] = 'different'
    (run/'manifest.json').write_text(json.dumps(manifest))
    (baseline/'manifest.json').write_text(json.dumps(control))
    def forbidden(*args,**kwargs):
        pytest.fail('Gold read before provenance validation')
    monkeypatch.setattr(comparison,'evaluate',forbidden)
    with pytest.raises(ValueError):
        comparison.main(['--run',str(run),'--baseline',str(baseline),
                         '--world',str(tmp_path/'unopened_truth'),'--out',str(tmp_path/'out')])
    assert not (tmp_path/'out').exists()


def test_comparison_refuses_different_information_sets():
    fit = {'input_sha256': {'a': 'content_one', 'b': 'content_two'}}
    base = {'input_sha256': {'a': 'content_one', 'b': 'content_two'},
            'hidden_truth_provided': False, 'bayesian_predictions_provided': False}
    check_matched_inputs(fit,base)
    base['input_sha256']['b'] = 'different'
    with pytest.raises(ValueError,match='equal-information'):
        check_matched_inputs(fit,base)
    base['input_sha256'] = fit['input_sha256']
    base['bayesian_predictions_provided'] = True
    with pytest.raises(ValueError,match='separation'):
        check_matched_inputs(fit,base)


def test_baseline_interval_score_penalizes_width_and_misses_without_inventing_crps():
    p = dict(median_days=10.,median_lower90_days=5.,median_upper90_days=20.)
    score = score_baseline(p,10.)
    assert score['absolute_log_error'] == 0
    assert score['interval_covers_truth']
    assert score['interval_score90_log_median'] == pytest.approx(math.log(4.))
    assert score_baseline(p,40.)['interval_score90_log_median'] == pytest.approx(math.log(4.)+20*math.log(2.))
    p['median_lower90_days'] = None
    assert score_baseline(p,10.)['interval_score90_log_median'] is None
    assert not any('crps' in k for k in score)


def test_comparison_preserves_input_provenance_through_chain_extensions():
    original = {'input_sha256': {'a': 'content_one', 'b': 'content_two'}}
    extended = {'base_manifest': {'base_manifest': original}}
    baseline = {'input_sha256': {'renamed_a': 'content_one', 'renamed_b': 'content_two'},
                'hidden_truth_provided': False, 'bayesian_predictions_provided': False}
    check_matched_inputs(extended,baseline)
    with pytest.raises(ValueError,match='Missing input hashes'):
        check_matched_inputs({'base_manifest': {}},baseline)
    with pytest.raises(ValueError,match='Invalid input hashes'):
        check_matched_inputs({'input_sha256': {}},baseline)
    baseline['input_sha256']['duplicate'] = 'content_one'
    with pytest.raises(ValueError,match='equal-information'):
        check_matched_inputs(extended,baseline)


def test_case_burden_excludes_post_decision_work_and_separates_repeat_visits():
    truth = {'terminal_artifact': 'permit',
        'actors': [{'id': 'payer', 'type': 'external'}, {'id': 'agency', 'type': 'agency'},
                   {'id': 'county', 'type': 'external_government'}],
        'activities': [
            {'id': 'file', 'actor': 'payer'},
            {'id': 'review', 'actor': 'county'},
            {'id': 'decide', 'actor': 'agency', 'element_ref': 'E1',
             'visibility': 'applicant_facing', 'artifacts_out': ['permit']},
            {'id': 'archive', 'actor': 'agency'}]}
    path = [{'a': a} for a in ('file', 'review', 'file', 'review', 'decide', 'archive')]
    records = [{'censored': False, 'outcome': 'approved', 'path': path},
               {'censored': False, 'outcome': 'approved', 'path': [{'a':'file'}]},
               {'censored': True, 'outcome': 'in_progress', 'path': path},
               {'censored': False, 'outcome': 'abandoned', 'path': path}]
    result = realized_burden(truth, records)
    assert result['n_cases'] == 1
    assert result['decided_cases_without_resolved_endpoint'] == 1
    assert result['means'] == dict(distinct_operations=3, operation_visits=5,
                                  distinct_agency_operations=2, distinct_agencies=2)
    assert result['work_hours'] is None


def test_work_hour_support_not_silently_transferred_to_another_program():
    claim = dict(id='hours',metric='agency_work',scope='process',statistic='estimate',
        value=2.,lower=None,upper=None,unit='hours',quote='two hours',source_family='cost-study')
    evidences = [dict(program_id='first',measurements=[claim]),dict(program_id='second',measurements=[])]
    support = burden_support(evidences)
    assert support['first']['agency_work']['direct_numerical_claims']==1
    assert not support['first']['agency_work']['borrowed_only_if_estimated']
    assert support['second']['agency_work']['direct_numerical_claims']==0
    assert support['second']['agency_work']['borrowed_only_if_estimated']
    assert not support['second']['payer_work']['borrowed_only_if_estimated']
