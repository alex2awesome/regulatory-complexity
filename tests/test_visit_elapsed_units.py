"""Native clocks do not convert business days or turn aggregate phases into tasks."""
from dataclasses import replace
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import main, preflight_report
from pipeline.procbench.evaluate_burden import compare_burden_v6, synthetic_release_gate
from procbench_fixtures import data_fixture
from test_cohort_histograms import histogram_fixture
from test_cohort_quantiles import cohort_fixture


def native_data():
    data=data_fixture()
    data['elapsed_time_unit']='business_days'
    return data


def coarse_data():
    data=native_data()
    p=data['programs'][0]
    p.update(inventory_granularity='aggregate_phases',
             clock_estimand='Artificial test phase: receipt to permit issue, not whole installation')
    p['observations']=[p['observations'][0]]
    p['observations'][0].update(case_id=None,statistic='median')
    return data


def test_native_units_preserve_numeric_likelihood_without_implicit_conversion():
    cfg=Config(population_size=16)
    calendar=VisitHierarchy(data_fixture(),cfg)
    business=VisitHierarchy(native_data(),replace(cfg,elapsed_time_unit='business_days'))
    assert calendar.layout.size==business.layout.size
    for seed in range(4):
        z=np.random.default_rng(seed).normal(size=calendar.layout.size)
        assert calendar.log_likelihood(z,[0])==business.log_likelihood(z,[0])
    report=preflight_report(business)
    assert report['elapsed_time_unit']=='business_days'
    assert report['duration_priors']['elapsed_clock']=='single_visit_cycle_business_days_including_wait_and_service'


@pytest.mark.parametrize('unit',['days','hours',None,True])
def test_unknown_unit_fails(unit):
    with pytest.raises(ValueError,match='Elapsed time unit'):
        Config(elapsed_time_unit=unit)


@pytest.mark.parametrize('level',['data','program','observation','quantile'])
def test_mismatched_elapsed_declarations_fail(level):
    data=native_data()
    p=data['programs'][0]
    if level=='data': data['elapsed_time_unit']='calendar_days'
    elif level=='program': p['time_unit']='calendar_days'
    elif level=='observation': p['observations'][0]['time_unit']='calendar_days'
    else:
        cohort=cohort_fixture(); cohort['time_unit']='calendar_days'
        p.update(observations=[],quantile_cohorts=[cohort])
    with pytest.raises(ValueError,match='time unit'):
        VisitHierarchy(data,Config(elapsed_time_unit='business_days'))


def test_histogram_contract_still_requires_calendar_axis():
    data=native_data()
    data['programs'][0].update(observations=[],histogram_cohorts=[histogram_fixture()])
    with pytest.raises(ValueError,match='histogram cohorts.*calendar_days'):
        VisitHierarchy(data,Config(elapsed_time_unit='business_days'))


def test_explicit_matching_native_quantile_unit_is_accepted():
    data=native_data()
    cohort=cohort_fixture(); cohort['time_unit']='business_days'
    data['programs'][0].update(observations=[],quantile_cohorts=[cohort])
    model=VisitHierarchy(data,Config(elapsed_time_unit='business_days',population_size=16))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))


def test_coarse_phase_report_preserves_clock_and_suppresses_false_inventories():
    model=VisitHierarchy(coarse_data(),Config(elapsed_time_unit='business_days',
        modeled_channels=('elapsed',),population_size=16,chains=1,warmup=1,draws=8))
    states,routes,ll,_=model.sample()
    report=model.report(states,routes,ll)
    p=report['programs']['J__P']
    assert report['elapsed_time_unit']==p['elapsed_time_unit']=='business_days'
    assert p['inventory_granularity']=='aggregate_phases'
    assert p['clock_estimand'].startswith('Artificial test phase')
    assert 'initial_decision_median_days' in p['metrics']
    assert not any('count' in k or 'fee' in k for k in p['metrics'])
    assert 'mean_payer_hours' not in p['metrics']
    assert report['agencies']['J:Review']['contains_aggregate_phases']
    assert not report['agencies']['J:Review']['intrinsic_agency_effect_headline_eligible']
    # Even a high-contraction block does not earn an intrinsic-speed headline.
    concentrated=np.random.default_rng(20).normal(scale=.1,size=(2,8,model.layout.size))
    info=model.information_report(concentrated,sampling_converged=True)
    block=info['blocks']['agency:elapsed']
    assert block['statistical_contraction_gate_passed']
    assert not block['headline_eligible']


@pytest.mark.parametrize('basis',['visit_count','operation_count','agency_count','payer_fee_total'])
def test_coarse_phase_cannot_use_inventory_based_reports(basis):
    data=coarse_data()
    obs=data['programs'][0]['observations'][0]
    obs.update(case_id='individual',statistic='individual',operators=[dict(basis=basis)])
    with pytest.raises(ValueError,match='Aggregate phases do not establish'):
        VisitHierarchy(data,Config(elapsed_time_unit='business_days'))


def test_coarse_phase_requires_explicit_estimand():
    data=coarse_data(); del data['programs'][0]['clock_estimand']
    with pytest.raises(ValueError,match='explicit clock estimand'):
        VisitHierarchy(data,Config(elapsed_time_unit='business_days'))


def test_native_cli_requires_explicit_unit_and_saves_it(tmp_path):
    path=tmp_path/'data.json'; path.write_text(json.dumps(coarse_data()))
    out=tmp_path/'preflight'
    with pytest.raises(ValueError,match='Data and model elapsed time units'):
        main(['--data',str(path),'--out',str(out),'--preflight'])
    assert not out.exists()
    main(['--data',str(path),'--out',str(out),'--preflight',
          '--elapsed-time-unit','business_days','--observed-channels-only','--population-size','16'])
    report=json.loads((out/'preflight.json').read_text())
    assert report['elapsed_time_unit']=='business_days'
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['provenance']['config']['elapsed_time_unit']=='business_days'


@pytest.mark.parametrize('field,value',[('elapsed_time_unit','business_days'),
    ('inventory_granularity','aggregate_phases')])
def test_truth_evaluator_rejects_unmatched_units_or_granularity_before_reading_records(field,value):
    p={field:value,'metrics':{}}
    with pytest.raises(ValueError):
        compare_burden_v6(p,None,None)
    report=dict(programs={'p':p},posterior_converged=True,numerically_usable=True)
    failures=synthetic_release_gate(report)['failures']
    assert ('unmatched_truth_time_unit' if field=='elapsed_time_unit'
            else 'unmatched_aggregate_phase_estimand') in failures
