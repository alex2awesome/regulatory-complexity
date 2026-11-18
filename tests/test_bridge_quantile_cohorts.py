"""Source-free compiler -> structural bridge -> V6 finite-cohort integration."""
import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.bridge_structural_routes import BridgeError, bridge_program, combine_programs, main
from pipeline.procbench.compile_visit_durations import compile_durations
from test_bridge_structural_routes import P, compilation, evidence, handoff
from test_cohort_quantiles import cohort_fixture, compiler_inputs
from test_source_precision import declaration


def compiled_cohort():
    compiled = compilation()
    compiled['observations'] = []
    compiled['quantile_cohorts'] = [cohort_fixture()]
    return compiled


def test_reviewed_compiler_cohort_and_precision_reach_v6_verbatim_as_one_factor():
    e, visits, semantics, docs, policy, bindings = compiler_inputs()
    policy['source_type_report_scales'] = declaration(.37, 'agency_dashboard')
    compiled = compile_durations(e, visits, semantics, docs, policy,
        cohort_bindings=bindings, source_family_kinds={'document': 'official_stats'})
    # Compose the two invented fixtures in one namespace; no real source is read.
    compiled['program_id'] = P
    before = copy.deepcopy(compiled)
    program, report = bridge_program(evidence(), handoff(), compiled)
    assert compiled == before
    assert program['observations'] == []
    assert program['quantile_cohorts'] == before['quantile_cohorts']
    cohort = program['quantile_cohorts'][0]
    assert cohort['report_log_scale'] == .37
    assert len(cohort['reports']) == 2
    assert report['quantile_cohorts']['independent_factors'] == 1
    assert report['quantile_cohorts']['joint_report_rows'] == 2
    assert report['quantile_cohorts']['sample_sizes'] == {cohort['id']: cohort['sample_size']}
    model = VisitHierarchy(dict(programs=[program]), Config(population_size=16,
        modeled_channels=('elapsed',), cohort_quadrature_size=16))
    z = np.zeros(model.layout.size)
    terms = model.log_likelihood(z, [0], parts=True)
    assert list(terms) == [P + ':quantile_cohort:' + cohort['id']]
    assert np.isfinite(next(iter(terms.values())))
    assert model.log_likelihood(z, [0]) == pytest.approx(
        model.log_likelihood_reference(z, [0]), abs=1e-12)
    assert model.source_support_report()['source_families']['document']['report_log_scales'] == [.37]


def test_bridge_does_not_mutate_input_or_invent_individuals_from_denominator():
    compiled = compiled_cohort()
    before = copy.deepcopy(compiled)
    program, _ = bridge_program(evidence(), handoff(), compiled)
    assert compiled == before
    assert not program['observations'] and not program['case_path_scope']
    program['quantile_cohorts'][0]['reports'][0]['lower'] = 999.
    assert compiled == before


@pytest.mark.parametrize('mutation', [
    lambda c: c.update(sample_size=None),
    lambda c: c.update(sample_size=True),
    lambda c: c.update(sampling='unknown'),
    lambda c: c.update(independent_of_other_evidence=False),
    lambda c: c['reports'][0].update(statistic='mean'),
])
def test_invalid_compiled_cohorts_fail_instead_of_being_silently_dropped(mutation):
    compiled = compiled_cohort()
    mutation(compiled['quantile_cohorts'][0])
    with pytest.raises(ValueError):
        bridge_program(evidence(), handoff(), compiled)


def test_null_cohort_container_fails_instead_of_becoming_empty():
    compiled = compilation()
    compiled['quantile_cohorts'] = None
    with pytest.raises(BridgeError, match='explicit list'):
        bridge_program(evidence(), handoff(), compiled)


@pytest.mark.parametrize('alias_kind', ['report_id', 'measurement_ids', 'cohort_id'])
def test_explicit_overlap_with_ordinary_evidence_is_rejected(alias_kind):
    compiled = compilation()
    cohort = cohort_fixture()
    compiled['quantile_cohorts'] = [cohort]
    if alias_kind == 'report_id':
        cohort['reports'][0]['id'] = compiled['observations'][0]['id']
    elif alias_kind == 'measurement_ids':
        cohort['reports'][0]['measurement_ids'] = ['same_source_claim']
        compiled['observations'][0]['measurement_ids'] = ['same_source_claim']
    else:
        compiled['observations'][0]['cohort_id'] = cohort['cohort_id']
    with pytest.raises(ValueError, match='overlap'):
        bridge_program(evidence(), handoff(), compiled)


def test_duplicate_cohort_under_another_factor_id_fails():
    compiled = compiled_cohort()
    other = copy.deepcopy(compiled['quantile_cohorts'][0])
    other['id'] = 'second_factor'
    compiled['quantile_cohorts'].append(other)
    with pytest.raises(ValueError, match='overlap'):
        bridge_program(evidence(), handoff(), compiled)


def test_one_measurement_cannot_be_reused_as_two_different_cohort_statistics():
    compiled = compiled_cohort()
    for r in compiled['quantile_cohorts'][0]['reports']:
        r['measurement_ids'] = ['same_claim']
    with pytest.raises(BridgeError, match='overlaps another factor'):
        bridge_program(evidence(), handoff(), compiled)


def test_ordinary_observation_cannot_collide_with_generated_cohort_likelihood_key():
    compiled = compilation()
    compiled['observations'][0]['id'] = 'quantile_cohort:dashboard'
    compiled['quantile_cohorts'] = [cohort_fixture()]
    with pytest.raises(BridgeError, match='generated cohort likelihood key'):
        bridge_program(evidence(), handoff(), compiled)


def test_reports_from_one_cohort_are_not_split_in_report_group_audit():
    compiled = compiled_cohort()
    groups = dict(schema_version='fixture', groups=[dict(id='joint', measurement_ids=['median', 'p90'])])
    _, report = bridge_program(evidence(), handoff(), compiled, report_groups=groups)
    assert report['report_groups']['consistent_with_compilation']
    assert report['report_groups']['groups_split_across_compiled_factors'] == []


def test_cohort_operator_unsupported_by_a_merge_is_reported_not_erased():
    compiled = compiled_cohort()
    cohort = compiled['quantile_cohorts'][0]
    cohort['operators'] = [dict(basis='single_visit_cycle', activity_ids=['record'], visits='first'),
                           dict(basis='unmodeled_duration', median_days=7., log_scale=3.)]
    cohort['operator_weights'] = [.8, .2]
    cohort['population_condition'] = 'first_visit'
    program, report = bridge_program(evidence(), handoff(), compiled)
    assert program['quantile_cohorts'] == compiled['quantile_cohorts']
    for route in report['routes']:
        missing = route['compiled_operators_referencing_non_route_activities']
        assert missing['count'] == 1
        assert missing['operators'][0]['observation_id'] == 'quantile_cohort:dashboard'
        assert missing['operators'][0]['missing_activity_ids'] == ['record']


@pytest.mark.parametrize('basis,channel,phase', [
    ('agency_hours', 'agency_hours', False),
    ('payer_hours', 'payer_hours', False),
    ('service_elapsed', 'elapsed', True),
])
def test_cohort_operators_participate_in_construction_channel_and_phase_checks(basis, channel, phase):
    compiled = compiled_cohort()
    operator = dict(basis=basis)
    if phase:
        operator['activity_ids'] = ['review']
        operator['visits'] = 'first'
    compiled['quantile_cohorts'][0]['operators'] = [operator]
    _, report = bridge_program(evidence(), handoff(), compiled)
    assert channel in report['visit_hierarchy_constructed']['modeled_channels']
    assert report['visit_hierarchy_constructed']['within_visit_phases'] is phase


def test_business_day_cohort_is_preserved_without_calendar_conversion():
    compiled = compiled_cohort()
    compiled['quantile_cohorts'][0]['time_unit'] = 'business_days'
    program, _ = bridge_program(evidence(), handoff(), compiled)
    assert program['quantile_cohorts'][0]['time_unit'] == 'business_days'
    other = copy.deepcopy(compiled['quantile_cohorts'][0])
    other.update(id='other', cohort_id='other', time_unit='calendar_days')
    for r in other['reports']:
        r['id'] += '_other'
    compiled['quantile_cohorts'].append(other)
    with pytest.raises(BridgeError, match='time units must agree'):
        bridge_program(evidence(), handoff(), compiled)


def test_business_day_cohort_cannot_reinterpret_unitless_legacy_calendar_rows():
    compiled = compilation()
    compiled['quantile_cohorts'] = [dict(cohort_fixture(), time_unit='business_days')]
    with pytest.raises(BridgeError, match='time units must agree'):
        bridge_program(evidence(), handoff(), compiled)


@pytest.mark.parametrize('basis', ['visit_count', 'payer_fee_total', 'payer_hours', 'agency_hours'])
def test_nonelapsed_rows_do_not_impose_calendar_units_on_business_cohort(basis):
    compiled = compiled_cohort()
    compiled['quantile_cohorts'][0]['time_unit'] = 'business_days'
    row = copy.deepcopy(compilation()['observations'][0])
    row.update(operators=[dict(basis=basis)], operator_weights=[1.])
    compiled['observations'] = [row]
    program, report = bridge_program(evidence(), handoff(), compiled)
    assert program['observations'] == [row]
    assert report['visit_hierarchy_constructed']['elapsed_time_unit'] == 'business_days'


@pytest.mark.parametrize('other_kind', ['quantile', 'histogram', 'individual'])
def test_combining_programs_rejects_globally_overlapping_cohorts(other_kind):
    program, _ = bridge_program(evidence(), handoff(), compiled_cohort())
    other = copy.deepcopy(program)
    other['id'] = 'different'
    if other_kind == 'histogram':
        other['histogram_cohorts'] = other.pop('quantile_cohorts')
    elif other_kind == 'individual':
        identity = other.pop('quantile_cohorts')[0]['cohort_id']
        other['observations'] = [dict(compilation()['observations'][0], cohort_id=identity)]
    with pytest.raises(BridgeError, match='overlapping cohort identity'):
        combine_programs([dict(programs=[program]), dict(programs=[other])])


def test_business_day_cli_output_and_combination_keep_top_level_time_unit(tmp_path):
    import json
    compiled = compiled_cohort()
    compiled['quantile_cohorts'][0]['time_unit'] = 'business_days'
    for name, value in [('evidence', evidence()), ('handoff', handoff()), ('compilation', compiled)]:
        (tmp_path / (name + '.json')).write_text(json.dumps(value))
    out = tmp_path / 'bridge'
    main(['program', '--evidence', str(tmp_path / 'evidence.json'),
          '--handoff', str(tmp_path / 'handoff.json'),
          '--compilation', str(tmp_path / 'compilation.json'), '--out', str(out)])
    data = json.loads((out / 'data.json').read_text())
    assert data['elapsed_time_unit'] == 'business_days'
    assert combine_programs([data]) == data
    VisitHierarchy(data, Config(population_size=16, modeled_channels=('elapsed',),
                                elapsed_time_unit='business_days'))
    other = copy.deepcopy(data)
    other['programs'][0]['id'] = 'different'
    other['programs'][0]['quantile_cohorts'][0]['cohort_id'] = 'distinct_cohort'
    other['elapsed_time_unit'] = 'calendar_days'
    with pytest.raises(BridgeError, match='one elapsed time unit'):
        combine_programs([data, other])
