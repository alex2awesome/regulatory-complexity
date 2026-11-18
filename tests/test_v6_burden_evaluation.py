"""Source-free checks of post-fit V6 scoring and its truth-read boundary."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from pipeline.procbench import evaluate_burden as evaluation


def fixture():
    truth = dict(actors=[dict(id='payer', type='external'),
                         dict(id='county', type='agency')], activities=[
        dict(id='file', actor='payer', visibility='applicant_facing'),
        dict(id='decide', actor='county', visibility='applicant_facing'),
        dict(id='archive', actor='county', visibility='back_office')])
    def clock(days, censored=False):
        return dict(elapsed_days=days, end_date='2020-01-01', censored=censored)
    records = [dict(censored=False, outcome='approved', elapsed_days=40,
        fees_paid=25, path=[dict(a=a) for a in ('file','file','decide','archive')],
        event_clocks=dict(initial_decision=clock(10), last_decision=clock(40),
                          modeled_work_end=clock(50))),
        dict(censored=True, outcome='in_progress', elapsed_days=100,
             path=[dict(a='file')], event_clocks=dict(initial_decision=clock(20),
                                                     last_decision=clock(100, True)))]
    return truth, records


def posterior():
    return dict(model='joint-visit-hierarchy/6', posterior_converged=True,
                numerically_usable=True, programs={'C29__S12':dict(metrics={
                    'initial_decision_median_days':dict(median=10,ci90=[5,20]),
                    'mean_visit_count':dict(median=4,ci90=[3,5])})})


def receipt():
    truth, records = fixture()
    report = posterior()
    return dict(schema_version='v6-burden-evaluation/1', completed_utc='saved',
        posterior_sha256='bound', reserved_truth_read=False, inference_modified=False,
        programs={'C29__S12':evaluation.compare_burden_v6(
            report['programs']['C29__S12'],truth,records)})


def test_explicit_clocks_full_paths_and_different_observed_cohorts():
    result = evaluation.realized_v6_burden(*fixture())
    assert result['n_cases'] == 1
    assert result['clocks']['initial_decision']['primary']['median'] == 10
    assert result['clocks']['final_decision']['primary']['median'] == 40
    assert result['clocks']['modeled_work_end']['primary']['median'] == 50
    assert result['clocks']['initial_decision']['all_observed_events']['median'] == 15
    assert result['clocks']['initial_decision']['all_observed_events']['n'] == 2
    assert result['clocks']['final_decision']['all_observed_events']['n'] == 1
    assert result['means'] == dict(mean_visit_count=4,mean_operation_count=3,
        mean_agency_count=1,mean_applicant_visit_count=3,mean_applicant_operation_count=2)
    assert result['mean_fee_total'] == 25
    assert result['work_hours'] is None


@pytest.mark.parametrize('clock', [None, 10, {}, dict(elapsed_days=10,end_date=None,censored=False),
    dict(elapsed_days=10,end_date='date',censored=True),
    dict(elapsed_days=float('nan'),end_date='date',censored=False)])
def test_missing_or_unobserved_initial_clock_never_falls_back_to_legacy(clock):
    truth, records = fixture()
    records[0]['event_clocks']['initial_decision'] = clock
    result = evaluation.compare_burden_v6(posterior()['programs']['C29__S12'],truth,records)
    initial = result['truth']['clocks']['initial_decision']
    assert initial['primary']['median'] is None
    assert initial['primary_cases_without_observed_event'] == 1
    assert result['truth']['legacy_elapsed_median_days'] == 40
    assert result['comparisons']['initial_decision_median_days']['scored'] is False
    assert result['development_phase1_clock_recovery_pass'] is False


def test_scalar_scores_width_misses_zero_and_route_conditioning():
    score = evaluation._compare_scalar(dict(median=10,ci90=[5,20]),40)
    assert score['interval_score90'] == pytest.approx(415)
    assert score['ci90_covers_truth'] is False
    assert score['posterior_median_over_truth'] == .25
    zero = evaluation._compare_scalar(dict(median=0,ci90=[0,0]),0)
    assert zero['interval_score90'] == 0
    assert zero['interval_score90_log'] is None
    assert zero['posterior_median_over_truth'] is None
    conditional = evaluation._compare_scalar(dict(conditional_on_defined=dict(median=10,ci90=[5,20])),10)
    assert conditional['scored'] is False
    with pytest.raises(ValueError,match='interval'):
        evaluation._compare_scalar(dict(median=100,ci90=[5,20]),10)


def test_unsupported_metrics_and_missing_fees_are_not_successful_scores():
    truth, records = fixture()
    records[0].pop('fees_paid')
    program = posterior()['programs']['C29__S12']
    program['metrics'].update(mean_fee_total=dict(median=25,ci90=[20,30]),
                              mean_payer_hours=dict(median=1,ci90=[.1,10]))
    result = evaluation.compare_burden_v6(program,truth,records)
    assert result['comparisons']['mean_fee_total']['scored'] is False
    assert 'mean_payer_hours' in result['unsupported_metrics']
    assert 'mean_applicant_visit_count' in result['absent_burden_channels']


def test_release_gate_rejects_unscored_converged_fits_and_mismatched_receipts():
    report = posterior()
    assert evaluation.synthetic_release_gate(report)['failures'] == ['missing_completed_truth_evaluation']
    scored = receipt()
    mismatch = evaluation.synthetic_release_gate(report,scored,posterior_sha256='different')
    assert 'evaluation_not_bound_to_this_posterior' in mismatch['failures']
    scored['programs'] = {}
    mismatch = evaluation.synthetic_release_gate(report,scored,posterior_sha256='bound')
    assert 'evaluation_does_not_cover_all_programs' in mismatch['failures']


def test_development_recovery_is_not_a_general_validation_certificate():
    result = evaluation.synthetic_release_gate(posterior(),receipt(),posterior_sha256='bound')
    assert result['development_clock_gate_passed'] is True
    assert result['synthetic_posterior_quotable_as_validated'] is False
    for key in ('posterior_converged','numerically_usable'):
        report = posterior()
        report[key] = False
        assert not evaluation.synthetic_release_gate(report,receipt(),posterior_sha256='bound')['development_clock_gate_passed']
    forged = receipt()
    forged['programs']['C29__S12']['comparisons']['initial_decision_median_days']['posterior_median_over_truth'] = 3
    assert not evaluation.synthetic_release_gate(posterior(),forged,posterior_sha256='bound')['development_clock_gate_passed']
    unfinished = receipt()
    unfinished.pop('completed_utc')
    assert not evaluation.synthetic_release_gate(posterior(),unfinished,posterior_sha256='bound')['development_clock_gate_passed']


def saved_fit(tmp_path):
    run, world = tmp_path/'run',tmp_path/'world'
    run.mkdir()
    world.mkdir()
    report = posterior()
    p = run/'posterior.json'
    p.write_text(json.dumps(report))
    (run/'manifest.json').write_text(json.dumps(dict(completed_utc='saved',status='completed',
        posterior_sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
    (world/'render_manifest.json').write_text(json.dumps(dict(partitions=dict(
        calibration=['C44'],development=['C29'],reserved=['C03']))))
    return run,world


@pytest.mark.parametrize('failure',['unfinished','hash','reserved','unassigned','partial_reserved','partition_overlap'])
def test_all_integrity_and_partition_checks_precede_every_truth_read(tmp_path,monkeypatch,failure):
    run, world = saved_fit(tmp_path)
    if failure in ('unfinished','hash'):
        manifest = json.loads((run/'manifest.json').read_text())
        manifest['completed_utc' if failure=='unfinished' else 'posterior_sha256'] = None
        (run/'manifest.json').write_text(json.dumps(manifest))
    elif failure=='partition_overlap':
        (world/'render_manifest.json').write_text(json.dumps(dict(partitions=dict(development=['C29'],reserved=['C29']))))
    else:
        report = posterior()
        program = report['programs']['C29__S12']
        if failure!='partial_reserved':
            report['programs'] = {}
        report['programs']['C03__S12' if failure!='unassigned' else 'C02__S12'] = program
        (run/'posterior.json').write_text(json.dumps(report))
        manifest = json.loads((run/'manifest.json').read_text())
        manifest['posterior_sha256'] = hashlib.sha256((run/'posterior.json').read_bytes()).hexdigest()
        (run/'manifest.json').write_text(json.dumps(manifest))
    read_text = Path.read_text
    def guarded_read(path,*args,**kwargs):
        if 'truth' in path.parts:
            pytest.fail('Truth read before validating all program partitions')
        return read_text(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',guarded_read)
    with pytest.raises(ValueError):
        evaluation.main(['--run',str(run),'--world',str(world),'--out',str(tmp_path/'out')])
    assert not (tmp_path/'out').exists()


def test_completed_cli_writes_hash_bound_truth_declared_receipt_without_changing_fit(tmp_path):
    run,world = saved_fit(tmp_path)
    before = {p.name:p.read_bytes() for p in run.iterdir()}
    truth,records = fixture()
    (world/'truth/processes').mkdir(parents=True)
    (world/'truth/log').mkdir()
    (world/'truth/processes/C29__S12.json').write_text(json.dumps(truth))
    (world/'truth/log/C29__S12.jsonl').write_text('\n'.join(json.dumps(r) for r in records))
    out = tmp_path/'out'
    assert evaluation.main(['--run',str(run),'--world',str(world),'--out',str(out)]) == 0
    assert before == {p.name:p.read_bytes() for p in run.iterdir()}
    scored = json.loads((out/'evaluation.json').read_text())
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['status'] == 'completed'
    assert manifest['provenance']['hidden_truth_read'] is True
    assert scored['reserved_truth_read'] is False
    assert scored['partitions'] == {'C29__S12':'development'}
    assert manifest['evaluation_sha256'] == hashlib.sha256((out/'evaluation.json').read_bytes()).hexdigest()
    assert (out/'source/infra/scoring.py').is_file()
    assert json.loads((out/'release_gate.json').read_text())['development_clock_gate_passed'] is True
    with pytest.raises(ValueError,match='fresh'):
        evaluation.main(['--run',str(run),'--world',str(world),'--out',str(out)])
