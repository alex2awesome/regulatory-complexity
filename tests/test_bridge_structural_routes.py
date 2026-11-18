"""Source-free fixture pinning the structural bridge rules a-h.

Every input here is invented for mechanics checks. No benchmark truth, source
document or fitted output is read; no model is called.
"""
import copy
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.bridge_structural_routes import (BASE_ROUTE_ID, BridgeError, bridge_program,
                                                          combine_programs, main)

P = 'T__P'
ACTORS = [dict(id='payer', name='Applicant', role='payer'), dict(id='AG', name='Records desk', role='agency'),
          dict(id='REV', name='Review unit', role='agency'), dict(id='UNK', name='Unspecified', role='unknown')]
# (id, actor, task_type, stage, scope, classification)
ACTIVITIES = [
    ('side', 'payer', 'preparation', 'preparation', 'core', 'performed_operation'),
    ('file', 'payer', 'filing', 'submission', 'core', 'performed_operation'),
    ('pay', 'payer', 'payment', 'submission', 'core', 'performed_operation'),
    ('screen', 'UNK', 'completeness', 'intake', 'core', 'performed_operation'),
    ('notice', 'AG', 'notification', 'intake', 'conditional', 'performed_operation'),
    ('resubmit', 'payer', 'filing', 'submission', 'conditional', 'performed_operation'),
    ('review', 'REV', 'technical_review', 'review', 'core', 'performed_operation'),
    ('record', 'AG', 'records', 'review', 'core', 'metadata_or_record_work_boundary_unresolved'),
    ('approve', 'REV', 'decision', 'decision', 'conditional', 'legal_transition_or_outcome_event'),
    ('deny', 'REV', 'decision', 'decision', 'conditional', 'legal_transition_or_outcome_event'),
    ('deemed', 'REV', 'decision', 'decision', 'conditional', 'legal_transition_or_outcome_event'),
    ('issue', 'AG', 'records', 'closeout', 'conditional', 'performed_operation'),
    ('appeal', 'payer', 'filing', 'appeal', 'conditional', 'performed_operation'),
    ('renew', 'AG', 'technical_review', 'standing', 'standing', 'standing_obligation'),
    ('forecast', 'UNK', 'other', 'unknown', 'core', 'unresolved_reference_or_work_boundary'),
]
PERFORMED = [a for a, *_, c in ACTIVITIES if c == 'performed_operation']


def ref(doc='page', quote='Quoted text'):
    return dict(doc_id=doc, quote=quote)


def relation(source, target, kind='precedes', support='explicit', doc='page', condition=None):
    return dict(source=source, target=target, kind=kind, support=support, condition=condition,
                evidence=[ref(doc)])


def measurement(ident, case, activity_ids, doc='forum', scope='step', start='activity_start', end='activity_end'):
    return dict(id=ident, metric='elapsed', scope=scope, activity_ids=activity_ids, start=start, end=end,
                statistic='individual', value=3., lower=None, upper=None, unit='calendar_days',
                qualitative=False, n=None, case_id=case, cohort=None, source_family=doc, doc_id=doc,
                quote='Quoted text', interpretation='fixture')


def context(mid, temporal_scope='current', decision=None, excluded=()):
    return dict(measurement_id=mid, temporal_scope=temporal_scope, required_activity_ids=[],
                excluded_activity_ids=list(excluded), decision_activity_id=decision,
                segment_mode='not_segment', evidence=[ref('forum', 'outcome quote')], notes='')


def evidence():
    return dict(schema_version='process-evidence/3', program_id=P, actors=ACTORS,
        activities=[dict(id=a, name=a, actor_id=actor, task_type=task, stage=stage, scope=scope,
                         condition=None, existence='explicit', evidence=[ref()], notes='')
                    for a, actor, task, stage, scope, _ in ACTIVITIES],
        relations=[
            relation('side', 'file', kind='parallel'),
            relation('file', 'screen'),
            relation('pay', 'screen', doc='forum'),
            relation('review', 'pay', doc='bill', condition='Proposed sequence'),
            relation('screen', 'notice', support='inferred'),
            relation('notice', 'resubmit'),
            relation('resubmit', 'screen', kind='rework', support='inferred'),
            relation('screen', 'review'), relation('resubmit', 'review'),
            relation('review', 'approve'), relation('review', 'deny'),
            relation('approve', 'issue'), relation('deny', 'appeal'),
            relation('review', 'renew'),
        ],
        measurements=[measurement('m1', 'c1', ['screen']), measurement('m2', None, ['forecast'], doc='bill'),
                      measurement('m3', 'c1', [], scope='process', start='unspecified', end='decision'),
                      measurement('m4', 'c2', ['resubmit'])],
        ambiguities=[], excluded=[],
        observation_contexts=[context('m2', 'hypothetical'), context('m3', decision='approve'),
                              context('m4', excluded=('approve', 'deny'))])


def hypothesis(ident, ids):
    return dict(id=ident, activity_ids=ids, status='unweighted_source_compatible_inventory_interpretation',
                judgment='fixture', evidence=[ref()])


def handoff():
    return dict(schema_version='source-only-structural-handoff/1', program_id=P, diagnostic_only=True,
        changes_accepted_evidence=False, new_model_calls=0,
        activity_classifications=[dict(activity_id=a, name=a, classification=c, judgment='fixture',
                                       evidence=[ref('page', f'{a} quote')]) for a, *_, c in ACTIVITIES],
        conditional_paths_and_outcomes=[
            dict(id='dispositions', activity_ids=['approve', 'deny', 'deemed'],
                 decision_scope='per_decision_occasion', judgment='fixture', evidence=[ref()]),
            dict(id='optional_appeal', activity_ids=['deny', 'appeal'],
                 decision_scope='per_case_after_adverse_decision', judgment='fixture', evidence=[ref()])],
        inventory_identity_hypotheses=[hypothesis('h1', ['screen', 'review']), hypothesis('h2', ['file', 'resubmit']),
                                       hypothesis('h3', ['notice', 'screen']), hypothesis('h4', ['issue', 'record', 'appeal']),
                                       hypothesis('h5', ['pay', 'file']), hypothesis('h6', ['approve', 'deny']),
                                       hypothesis('h7', ['issue', 'appeal'])],
        repeat_links=[dict(id='corrections', activity_ids=['screen', 'notice', 'resubmit'], explicit='fixture',
                           interpretation='fixture', evidence=[ref()]),
                      dict(id='later_renewal', activity_ids=['review', 'renew'], explicit='fixture',
                           interpretation='later occasion', evidence=[ref()])],
        same_report_measurement_groups=[], distinct_case_warnings=[], agency_identity_notes=[])


RESIDUAL = dict(basis='unmodeled_duration', median_days=7., log_scale=3.)


def observation(ident, operators, weights, lower, upper, case=None, statistic=None, **extra):
    row = dict(id=ident, case_id=case, source_family='forum', sampling='unselected',
               statistic=statistic or ('individual' if case else 'median'), lower=lower, upper=upper,
               operators=operators, operator_weights=weights)
    row.update(extra)
    return row


def compilation():
    return dict(schema_version='joint-visit-duration-compilation/3', program_id=P, observations=[
        observation('o1', [dict(basis='single_visit_cycle', activity_ids=['screen'], visits='one_unspecified'),
                           copy.deepcopy(RESIDUAL)], [.8, .2], 2., 5., case='c1'),
        observation('o2', [dict(basis='whole_case_clock', start='process_start', end='initial_decision')],
                    [1.], 20., 40., case='c1'),
        observation('o3', [dict(basis='single_visit_cycle', activity_ids=['approve', 'deny'], visits='first',
                                activity_selection='first_present')], [1.], 3., 9.,
                    population_condition='first_visit'),
        observation('o4', [dict(basis='single_visit_cycle', activity_ids=['resubmit'], visits='one_unspecified'),
                           copy.deepcopy(RESIDUAL)], [.5, .5], 1., 4., case='c2'),
        observation('o5', [copy.deepcopy(RESIDUAL)], [1.], 5., 90., statistic='report_only'),
    ], coverage=dict(likelihood_factors=5))


@pytest.fixture(scope='module')
def bridged():
    return bridge_program(evidence(), handoff(), compilation())


def blocks_of(route):
    return [b for p in route.get('paths', [route]) for b in p['blocks']]


def test_rule_a_operations_are_performed_plus_dispositions_and_everything_else_is_listed(bridged):
    program, report = bridged
    ops = {o['id'] for o in program['routes'][0]['operations']}
    assert ops == set(PERFORMED) | {'approve', 'deny'}
    excluded = {e['activity_id']: e for e in report['excluded_activities']}
    assert set(excluded) == {'record', 'deemed', 'renew', 'forecast'}
    assert ops | set(excluded) == {a for a, *_ in ACTIVITIES}
    assert all(e['classification'] and e['evidence'][0]['quote'] for e in excluded.values())
    assert [u['activity_id'] for u in report['unrepresented_outcomes']] == ['deemed']


def test_rule_b_serial_default_and_no_empty_edges_anywhere(bridged):
    program, report = bridged
    for route in program['routes']:
        for block in blocks_of(route):
            assert block['edges'] != []
            if block['edges'] is not None:
                assert {'side', 'file'} <= set(block['operations'])
                assert all(a in block['operations'] and b in block['operations'] for a, b in block['edges'])
    base = program['routes'][0]
    parallel = [b for b in blocks_of(base) if b['edges'] is not None]
    assert parallel and all(len(b['edges']) >= 1 for b in parallel)
    assert not any(['side', 'file'] in b['edges'] or ['file', 'side'] in b['edges'] for b in parallel)
    serial = [b for b in blocks_of(base) if b['edges'] is None and b['repeat_key'] is None]
    assert all(len(b['operations']) == 1 for b in serial)
    assert [r['source'] for r in report['order']['relations_excluded_hypothetical_documents']] == ['review']


def test_rule_c_applicability_from_actor_role_and_unknown_stays_none(bridged):
    program, report = bridged
    ops = {o['id']: o for o in program['routes'][0]['operations']}
    assert (ops['file']['payer_work'], ops['file']['agency_work']) == (True, False)
    assert (ops['review']['payer_work'], ops['review']['agency_work']) == (False, True)
    assert (ops['screen']['payer_work'], ops['screen']['agency_work']) == (None, None)
    assert ops['screen']['actor_role'] == 'unknown' and ops['screen']['actor_id'] is None
    assert report['applicability']['none_applicability_operation_count_base_route'] == 1


def test_rule_d_markers_only_from_handoff_keys(bridged):
    program, report = bridged
    ops = {o['id']: o for o in program['routes'][0]['operations']}
    assert ops['approve']['markers'] == ['decision'] and ops['deny']['markers'] == ['decision']
    assert all(o['markers'] == [] for i, o in ops.items() if i not in ('approve', 'deny'))
    assert report['markers']['decision']['handoff_key'] == 'conditional_paths_and_outcomes[dispositions]'
    assert report['markers']['submission']['activity_ids'] == [] and report['markers']['submission']['handoff_key'] is None
    paths = report['clock_boundary_support']['paths']
    assert paths and all('first_submission' in p['absent_events'] for p in paths)
    assert all(p['initial_final_guaranteed_same_event'] for p in paths)


def test_bridge_reports_unavailable_clock_without_dropping_the_reading():
    compiled = compilation()
    compiled['observations'].append(observation('submission_clock', [
        dict(basis='whole_case_clock', start='first_submission', end='initial_decision'), RESIDUAL],
        [.8, .2], 2., 9., case='c1'))
    before = copy.deepcopy(compiled['observations'])
    program, report = bridge_program(evidence(), handoff(), compiled)
    assert program['observations'] == before
    assert report['clock_boundary_support']['affected_observations'] == [P + ':submission_clock']
    assert report['clock_boundary_support']['unsupported_clock_alternatives_by_inventory'] == len(program['routes'])


def test_rule_e_repeat_block_from_rework_joined_link_only(bridged):
    program, report = bridged
    loops = [b for b in blocks_of(program['routes'][0]) if b['repeat_key']]
    assert {b['repeat_key'] for b in loops} == {'corrections'}
    assert loops[0]['operations'] == ['screen', 'notice', 'resubmit'] and loops[0]['edges'] is None
    assert report['repeat_block']['handoff_key'] == 'repeat_links[corrections]'
    assert [x['id'] for x in report['repeat_links_not_encoded']] == ['later_renewal']


def test_rule_f_route_cap_uniform_prior_and_unrepresented_hypotheses(bridged):
    program, report = bridged
    routes = program['routes']
    assert len(routes) == 4 and routes[0]['id'] == BASE_ROUTE_ID
    assert [r['id'] for r in routes[1:]] == ['merge:h1', 'merge:h2', 'merge:h3']
    assert all(r['prior_weight'] == pytest.approx(.25) for r in routes)
    assert 'declared assumption' in report['route_prior_weight']['basis']
    reasons = {u['id']: u['reason'] for u in report['unrepresented_hypotheses']}
    assert 'not an operation' in reasons['h4'] and 'membership' in reasons['h5'] and 'cap' in reasons['h7']
    assert [h['id'] for h in report['hypotheses_encoded_as_case_paths']] == ['h6']
    merged = {o['id'] for o in routes[2]['operations']}
    assert 'file' not in merged and 'resubmit' in merged
    residual = {r['id']: r['compiled_operators_referencing_non_route_activities']['count'] for r in report['routes']}
    assert residual == {BASE_ROUTE_ID: 0, 'merge:h1': 0, 'merge:h2': 0, 'merge:h3': 0}
    program2, report2 = bridge_program(evidence(), handoff(), compilation(), max_routes=2)
    assert len(program2['routes']) == 2


def test_rule_g_paths_hold_exactly_one_disposition_and_quoted_outcomes_scope_cases(bridged):
    program, report = bridged
    for route in program['routes']:
        assert 'blocks' not in route
        for path in route['paths']:
            members = [o for b in path['blocks'] for o in b['operations']]
            assert len({'approve', 'deny'} & set(members)) == 1
            assert 'deemed' not in members
            assert ('issue' in members) == ('approve' in members)
            assert ('appeal' in members) == (path['id'] == 'deny+optional_appeal')
            assert path['probability_weight'] == pytest.approx(1 / 3)
    assert program['case_path_scope'] == {'c1': ['approve']}
    assert report['case_path_scope'][0]['ledger_key'] == ['observation_contexts[m3].decision_activity_id']
    assert report['case_path_scope'][0]['evidence'][0]['quote'] == 'outcome quote'
    assert [c['case_id'] for c in report['cases_without_representable_outcome']] == ['c2']


def test_rule_h_observations_verbatim_and_no_invented_sidecars(bridged):
    program, report = bridged
    assert program['observations'] == compilation()['observations']
    assert program['rate_observations'] == [] and program['quantile_cohorts'] == []
    assert report['observations']['copied_verbatim'] and report['rate_observations']['count'] == 0


def test_output_constructs_visit_hierarchy_with_finite_likelihood(bridged):
    program, _ = bridged
    model = VisitHierarchy(dict(programs=[copy.deepcopy(program)]),
                           Config(population_size=16, modeled_channels=('elapsed',)))
    for route in range(len(program['routes'])):
        assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [route]))


def test_contradictory_order_without_hypothetical_contexts_is_refused():
    e = evidence()
    e['schema_version'] = 'process-evidence/2'
    del e['observation_contexts']
    with pytest.raises(BridgeError, match='cycle'):
        bridge_program(e, handoff(), compilation())


def test_deemed_and_withdrawal_are_not_silently_promoted():
    h = handoff()
    for c in h['activity_classifications']:
        if c['activity_id'] == 'deemed':
            c['classification'] = 'performed_operation'
    program, report = bridge_program(evidence(), h, compilation())
    ops = {o['id'] for o in program['routes'][0]['operations']}
    assert 'deemed' in ops
    assert 'deemed' not in report['operations']['admitted_dispositions']
    assert all(len({'approve', 'deny'} & {o for b in p['blocks'] for o in b['operations']}) == 1
               for r in program['routes'] for p in r['paths'])


def test_cli_writes_manifest_data_and_report_then_combines(tmp_path):
    for name, payload in (('evidence', evidence()), ('handoff', handoff()), ('compilation', compilation())):
        (tmp_path / f'{name}.json').write_text(json.dumps(payload))
    out = tmp_path / 'bridge'
    main(['program', '--evidence', str(tmp_path / 'evidence.json'), '--handoff', str(tmp_path / 'handoff.json'),
          '--compilation', str(tmp_path / 'compilation.json'), '--out', str(out)])
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['manifest_version'] == 'procbench-run/1' and manifest['status'] == 'completed'
    assert manifest['provenance']['hidden_truth_read'] is False and manifest['hidden_truth_read'] is False
    assert set(manifest['provenance']['input_sha256']) == {str(tmp_path / f'{n}.json') for n in ('evidence', 'handoff', 'compilation')}
    data = json.loads((out / 'data.json').read_text())
    report = json.loads((out / 'bridge_report.json').read_text())
    assert data['programs'][0]['id'] == P and report['program_id'] == P and report['model_calls'] == 0
    second = copy.deepcopy(data)
    second['programs'][0]['id'] = 'T__Q'
    (tmp_path / 'second.json').write_text(json.dumps(second))
    combined = tmp_path / 'combined'
    main(['combine', '--inputs', str(out / 'data.json'), str(tmp_path / 'second.json'), '--out', str(combined)])
    assert [p['id'] for p in json.loads((combined / 'data.json').read_text())['programs']] == [P, 'T__Q']
    with pytest.raises(BridgeError):
        combine_programs([data, data])
