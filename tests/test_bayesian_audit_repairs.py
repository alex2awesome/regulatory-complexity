import copy

import numpy as np
import pytest

from benchmark.synth.generator.world import GENERATOR_VERSION, build_world
from pipeline.procbench.align import _end_to_end
from pipeline.procbench.metrics import _find_median
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.audit_visit_hypotheses import validate_hypotheses
from procbench_fixtures import data_fixture
from test_visit_hypotheses import hypothesis_inputs
from test_visit_interpretation_likelihood import residual


@pytest.mark.parametrize('kind', ['statutory_cap', 'target', 'deadline', ' Deadline '])
@pytest.mark.parametrize('field', ['process_timing', 'end_to_end'])
def test_process_caps_are_not_realized_medians(kind, field):
    assert _end_to_end({field: dict(kind=kind, median_days=30)}) is None
    assert _find_median(dict(kind=kind, median_days=30)) is None


def test_log_median_is_independent_of_key_order_and_never_a_fee_or_step():
    fields = [('fees_paid', dict(median=500)), ('per_activity', dict(a=dict(median=2))),
              ('elapsed_days', dict(median=74))]
    assert _find_median(dict(fields)) == _find_median(dict(reversed(fields))) == 74
    assert _find_median(dict(fields[:2])) is None
    assert _find_median(True) is None
    assert _end_to_end(dict(process_timing=dict(kind='observed', median_days=55))) == 55


def test_generator_records_revision_and_explicit_accounting_version():
    knobs = dict(only_jurisdictions=['J1'], only_domains=['sidewalk_vending'], neighbor_state=False)
    current = build_world('test', 1, knobs)
    legacy = build_world('test', 1, dict(knobs, visit_accounting_version=1))
    assert current['generator_version'] == legacy['generator_version'] == GENERATOR_VERSION
    assert current['visit_accounting_version'] == current['knobs']['visit_accounting_version'] == 2
    assert legacy['visit_accounting_version'] == legacy['knobs']['visit_accounting_version'] == 1


def test_absent_event_has_only_original_residual_mass_in_both_likelihoods():
    data = data_fixture()
    o = data['programs'][0]['observations'][0]
    o['operators'][0]['end'] = 'legal_closeout'
    o.update(operators=o['operators'] + [residual()], operator_weights=[.8, .2])
    model = VisitHierarchy(data, Config(population_size=16))
    z = np.zeros(model.layout.size)
    from pipeline.procbench.bayes_trace_hierarchy import unmodeled_duration_log_probability
    expected = np.log(.2) + unmodeled_duration_log_probability(o['lower'], o['upper'], residual())
    for likelihood in (model.log_likelihood, model.log_likelihood_reference):
        assert likelihood(z, [0], parts=True)['J__P:total'] == pytest.approx(expected)


@pytest.mark.parametrize('operator', [dict(basis='typo'), dict(basis='whole_case_clock'),
    dict(basis='whole_case_clock', start='process_start', end='invented_event'),
    dict(basis='single_visit_cycle'), dict(basis='additional_rounds')])
def test_malformed_operator_fails_at_model_construction(operator):
    data = data_fixture()
    data['programs'][0]['observations'][0]['operators'] = [operator]
    with pytest.raises(ValueError, match='Malformed'):
        VisitHierarchy(data)


def test_nonfixed_route_with_no_observed_transitions_is_not_converged():
    data = data_fixture()
    alternative = copy.deepcopy(data['programs'][0]['routes'][0])
    alternative['id'] = 'alternative'
    data['programs'][0]['routes'].append(alternative)
    model = VisitHierarchy(data, Config(population_size=16))
    states = np.zeros((4, 8, model.layout.size))
    report = model.report(states, np.zeros((4, 8, 1), dtype=int), np.zeros((4, 8)))
    for key in ('J__P:route:simple', 'J__P:route:alternative'):
        assert key in report['diagnostics_flagged']
        assert report['diagnostics'][key]['rhat'] is None


def test_per_cycle_report_can_cover_multiple_rounds_without_changing_parent():
    e, v, s, d, p, audit = hypothesis_inputs()
    v['measurements'][0]['operators'][0]['visits'] = 'all_completed_by_observation'
    op = audit['measurements'][0]['hypotheses'][0]['operator']
    op['visits'] = 'all_completed_by_observation'
    original = copy.deepcopy((v, audit))
    validate_hypotheses(audit, e, v, d)
    assert (v, audit) == original
