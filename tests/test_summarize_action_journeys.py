from dataclasses import asdict
import json

import numpy as np

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.solar_panel.summarize_action_journeys import (
    _actual_case_gate, _spread_comparison, _fixed_serial_prior_comparison,
    _elapsed_report_check, _case_report_checks, summarize,
)


def test_repeated_occurrences_are_not_distinct_action_concepts(tmp_path):
    operations = [dict(id=name, task_type='submit' if name.startswith('submit') else 'review',
                       actor_role='unknown', actor_id=None)
                  for name in ('submit1', 'review', 'submit2')]
    data = dict(programs=[dict(id='j', journey_context=dict(canonical_case_id='c',
        reviewed_observation_declarations=[dict(observation_id='derived_total',
            evidence_relation='derived_reconstruction',
            operation_ids=['submit1', 'review', 'submit2'])]),
        routes=[dict(id='r', prior_weight=1., operations=operations,
                     blocks=[dict(id='b', operations=[o['id'] for o in operations])])],
        observations=[dict(id='clock', case_id='c', source_family='forum',
            statistic='individual', sampling='unselected', lower=4., upper=30.,
            operators=[dict(basis='sum_visit_cycles', activity_ids=[o['id'] for o in operations])],
            operator_weights=[1.])])])
    config = Config(modeled_channels=('elapsed',), population_size=16,
                    agency_sd=0., source_sd=0.)
    model = VisitHierarchy(data, config)
    z = np.zeros((2, 8, model.layout.size))
    structures = np.zeros((2, 8, 1), dtype=int)
    ll = np.full((2, 8), model.log_likelihood(z[0,0], [0]))
    (tmp_path/'data.json').write_text(json.dumps(data))
    (tmp_path/'posterior.json').write_text(json.dumps(dict(config=asdict(config),
        numerically_usable=False, posterior_converged=False, diagnostics_flagged=['fixture'])))
    np.savez(tmp_path/'draws.npz', z=z, structures=structures, log_likelihood=ll)
    result = summarize(tmp_path, report_checks=True)
    case = result['cases']['c']
    assert case['case_posterior']['modeled_occurrence_count']['median'] == 3
    assert case['case_posterior']['unique_actor_action_concepts']['median'] == 2
    assert case['case_posterior']['extra_occurrences_beyond_first_of_each_concept']['median'] == 1
    assert case['full_installation_step_count'] is None
    assert case['population_probability_of_any_rework'] is None
    assert result['fit_numerically_usable'] is False
    assert result['actual_case_numerically_usable'] is False
    assert result['population_predictions_numerically_acceptable'] is False
    assert 'derived_total' in case['derived_clocks_not_additional_likelihood']
    assert 'derived_total' not in case['observed_clocks']
    baselines = result['pooled_elapsed_task_type_baselines']
    assert baselines['status'] == 'available'
    submit = baselines['task_types']['submit']
    assert submit['support']['distinct_canonical_cases'] == 1
    assert submit['support']['materialized_occurrences'] == 2
    assert submit['support']['low_support'] is True
    assert submit['conditional_location_median_days']['diagnostics']['rhat'] == 1.
    assert 'intrinsic agency service time' in submit['interpretation']
    checks = case['in_sample_report_checks']['reports']
    assert checks['clock']['status'] == 'checked'
    assert 0 < checks['clock']['mean_probability_of_reproducing_stated_report'] <= 1
    assert 'derived_total' not in checks
    import pytest
    with pytest.raises(ValueError, match='ADU-namespaced'):
        summarize(tmp_path, domain='adu')
    data['programs'][0]['id'] = 'adu_action_journey__fixture'
    (tmp_path/'data.json').write_text(json.dumps(data))
    adu = summarize(tmp_path, report_checks=True, domain='adu')
    assert adu['schema_version'] == 'adu-shared-action-journey-posterior/1'
    assert adu['cases']['c']['case_posterior'] == case['case_posterior']
    assert adu['cases']['c']['in_sample_report_checks'] == case['in_sample_report_checks']


def test_actual_case_gate_requires_complete_threshold_diagnostics_and_likelihood_precision():
    passing = dict(diagnostics=dict(rhat=1.01, ess_bulk=400., ess_tail=200.))
    case = dict(case_posterior={'count': passing}, observed_clocks={'clock': passing},
        derived_clocks_not_additional_likelihood={},
        operations={'op': {'case_cycle_days': passing}})
    posterior = dict(posterior_converged=True,
                     precision={'likelihood_acceptable': True, 'predictions_acceptable': False})
    gate = _actual_case_gate({'case': case}, posterior)
    assert gate['actual_case_numerically_usable'] is True
    assert gate['prerequisites']['likelihood_precision_acceptable'] is True
    conditional = dict(conditional_on_included_route=True, posterior_probability_included=.5)
    case['observed_clocks']['conditional'] = conditional
    gate = _actual_case_gate({'case': case}, posterior)
    assert gate['actual_case_numerically_usable'] is False
    flagged = gate['flagged_quantities']
    assert flagged[0]['quantity'].endswith('.observed_clocks.conditional')
    assert flagged[0]['reasons'] == [
        'conditional_or_unsupported_quantity_has_no_full_chain_diagnostics']
    case['observed_clocks']['conditional'] = dict(
        diagnostics=dict(rhat=None, ess_bulk=500., ess_tail=300.))
    gate = _actual_case_gate({'case': case}, posterior)
    assert gate['actual_case_numerically_usable'] is False
    assert gate['flagged_quantities'][0]['reasons'] == ['missing_or_nonfinite_diagnostics']


def test_spread_comparison_distinguishes_width_from_mean_shift():
    prior = np.arange(10, dtype=float)
    shifted = _spread_comparison(prior+20, prior)
    assert shifted['posterior_to_prior_sd_ratio'] == 1.
    assert shifted['posterior_mean_minus_prior_mean'] == 20.
    assert shifted['width_label'] == 'prior_width_or_wider'
    assert _spread_comparison(.5*prior, prior)['width_label'] == 'narrower_than_prior'
    assert _spread_comparison(np.ones(10), np.ones(10))['posterior_to_prior_sd_ratio'] is None


def test_fixed_serial_comparison_preserves_total_share_dependence():
    from types import SimpleNamespace
    raw = dict(routes=[dict(operations=[dict(id='a'), dict(id='b')],
        blocks=[dict(id='ba', operations=['a'], predecessors=[]),
                dict(id='bb', operations=['b'], predecessors=['ba'])])])
    program = dict(cases=['c'], case_index={'c': 0})
    class TraceFixture:
        def parameters(self, z):
            return None
        def trace(self, p, z, parameters, route):
            return SimpleNamespace(operations=[SimpleNamespace(id='a'), SimpleNamespace(id='b')],
                visits=np.ones((1, 2)), durations=np.asarray([z]))
    prior = np.asarray([[1., 3.], [2., 2.], [3., 1.], [4., 4.]])
    result = _fixed_serial_prior_comparison(TraceFixture(), program, raw,
        {'a': prior[:, 0], 'b': prior[:, 1]}, prior)
    assert result['status'] == 'compared'
    assert result['log_scoped_total']['posterior_to_prior_sd_ratio'] == 1.
    assert result['components']['a']['logit_share_of_scoped_total']['posterior_to_prior_sd_ratio'] == 1.
    raw['routes'].append(raw['routes'][0])
    assert _fixed_serial_prior_comparison(TraceFixture(), program, raw, {}, prior)['status'] == 'unsupported'


def test_report_reproduction_uses_student_t_and_union_not_envelope():
    from scipy.stats import t
    values = np.array([1.5, 5., 15.])
    observation = dict(id='clock', lower=1., upper=20.,
                       report_intervals=[[1., 2.], [10., 20.]])
    result = _elapsed_report_check(observation, values, scale=.4, contamination=.05)
    def probabilities(scale):
        return sum(t.cdf((np.log(hi)-np.log(values))/scale, 4)
                   - t.cdf((np.log(lo)-np.log(values))/scale, 4)
                   for lo, hi in observation['report_intervals'])
    regular, broad = probabilities(.4), probabilities(2.)
    mixed = .95*regular+.05*broad
    assert np.isclose(result['mean_probability_of_reproducing_stated_report'], mixed.mean())
    assert np.isclose(result['mean_broad_component_responsibility'], (.05*broad/mixed).mean())
    assert result['posterior_probability_latent_within_stated_bounds'] == 2/3
    no_contamination = _elapsed_report_check(observation, values, scale=.4, contamination=0.)
    assert no_contamination['mean_broad_component_responsibility'] == 0.
    assert np.isclose(no_contamination['mean_probability_of_reproducing_stated_report'], regular.mean())


def test_report_checks_keep_unsupported_conditions_explicit():
    from types import SimpleNamespace
    observation = dict(id='clock', case_id='c', statistic='individual',
                       operators=[dict(basis='sum_visit_cycles')])
    model = SimpleNamespace(cfg=SimpleNamespace(source_sd=.25), source_offset_hierarchy=None)
    program = dict(observations=[observation], joint_duration_reports=[dict(members=[observation])])
    result = _case_report_checks(model, program, {'clock': [1., 2.]}, 3)
    row = result['reports']['clock']
    assert row['status'] == 'unsupported'
    assert set(row['reasons']) == {'source_effect_not_fixed_zero',
        'shared_reporting_error_requires_joint_check', 'latent_quantity_not_available_on_every_draw'}
