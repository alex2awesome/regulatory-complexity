"""Source-free fixture pinning bridge rules j (agency identity) and k (fees).

Every ledger here is invented for mechanics checks; the names only imitate the
shape of the W2 corpus. No benchmark truth, source document, saved run output
or fitted output is read, and no model is called.
"""
import copy
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.bridge_structural_routes import (BridgeError, bridge_program,
                                                          canonical_agency_identity, main)
from test_bridge_structural_routes import compilation, evidence, handoff, ref

STATE_BOARD = 'Marisol Contractors State License Board'
REVENUE = 'Auditor-Controller, Revenue Division'
HEALTH = 'county health department'


def actor(ident, name, role, docs=('C00__page',)):
    return dict(id=ident, name=name, role=role, aliases=[],
                evidence=[ref(d, f'{name} appears in {d}') for d in docs])


def fee(ident, activity_ids, value, doc, quote, statistic='individual', case=None,
        scope='step', qualitative=False, unit='USD'):
    return dict(id=ident, metric='fee', scope=scope, activity_ids=list(activity_ids),
                start='unspecified', end='unspecified', statistic=statistic, value=value,
                lower=None, upper=None, unit=unit, qualitative=qualitative, n=None,
                case_id=case, cohort=None, source_family=doc, doc_id=doc, quote=quote,
                interpretation='fixture')


def programme(pid, actors, fees=(), namespace=False):
    """The rule-a..i fixture re-namespaced to one county/statute, with actors."""
    e, h, c = copy.deepcopy(evidence()), copy.deepcopy(handoff()), copy.deepcopy(compilation())
    for payload in (e, h, c):
        payload['program_id'] = pid
    e['actors'] = [copy.deepcopy(a) for a in actors]
    e['measurements'] = e['measurements'] + [copy.deepcopy(f) for f in fees]
    if namespace:  # ledger ids really are programme-scoped in the corpus
        prefix = pid.split('__')[0] + '__'
        for a in e['actors']:
            a['id'] = prefix + a['id']
        for a in e['activities']:
            a['actor_id'] = prefix + a['actor_id']
    return e, h, c


def county_actors(county, agency_name=REVENUE, review_name='Review unit', docs=('C00__page',)):
    return [actor('payer', 'Contractor / applicant', 'payer'),
            actor('AG', agency_name, 'agency', docs),
            actor('REV', f'{county} County Review Unit' if review_name is None else review_name, 'agency'),
            actor('UNK', 'Unidentified responsible actor', 'unknown'),
            actor('TP', 'Neighbourhood Vendors Collective', 'third_party')]


def bridge(pid, actors, peers=(), fees=(), namespace=False, **kw):
    e, h, c = programme(pid, actors, fees, namespace)
    peer_ledgers = [programme(p, a, namespace=namespace)[0] for p, a in peers]
    return bridge_program(e, h, c, peer_evidence=peer_ledgers, **kw)


def actor_ids(program):
    return {o['id']: o['actor_id'] for o in program['routes'][0]['operations']}


# ------------------------------------------------------------------- tier one
def test_state_level_body_gets_one_global_id_across_programmes():
    """Recurrence across counties plus a statute-scope quote, and no county word."""
    c29 = county_actors('Drummond', agency_name=STATE_BOARD, docs=('C29__ordinance',))
    c44 = county_actors('Ulverston', agency_name=STATE_BOARD, docs=('S12__statute_text',))
    left, left_report = bridge('C29__S12', c29, peers=[('C44__S12', c44)], pool_agencies=True)
    right, _ = bridge('C44__S12', c44, peers=[('C29__S12', c29)], pool_agencies=True)
    assert actor_ids(left)['notice'] == actor_ids(right)['notice'] == 'state:marisol_contractors_state_license_board'
    row = next(a for a in left_report['agency_identity']['assignments'] if a['ledger_actor_id'] == 'AG')
    assert row['tier'] == 'state_level_body' and row['pooled'] is True
    assert row['counties_naming_this_actor'] == ['C29', 'C44']
    # The statute quote that carried the decision came from the peer ledger.
    assert [q['doc_id'] for q in row['statute_scope_evidence']] == ['S12__statute_text']
    assert row['statute_scope_evidence'][0]['program_id'] == 'C44__S12'


def test_a_county_body_named_by_the_statute_is_still_a_county_body():
    """The county health department recurs and the statute names it; it is not one body."""
    a = county_actors('Northcote', agency_name=HEALTH, docs=('S03__statute_text',))
    b = county_actors('Crowmarsh', agency_name=HEALTH, docs=('S03__statute_text',))
    left, report = bridge('C38__S03', a, peers=[('C50__S03', b)], pool_agencies=True)
    right, _ = bridge('C50__S03', b, peers=[('C38__S03', a)], pool_agencies=True)
    assert actor_ids(left)['notice'] == 'county:C38:county_health_department'
    assert actor_ids(right)['notice'] == 'county:C50:county_health_department'
    row = next(x for x in report['agency_identity']['assignments'] if x['ledger_actor_id'] == 'AG')
    assert row['tier'] == 'county_office' and row['self_described_county_body'] is True
    assert 'describes a county body' in row['basis']


# ------------------------------------------------------------------- tier two
def test_the_same_county_in_two_statutes_pools():
    ulverston = county_actors('Ulverston', agency_name='Ulverston County')
    s12, _ = bridge('C44__S12', ulverston, peers=[('C44__S03', ulverston)], pool_agencies=True)
    s03, _ = bridge('C44__S03', ulverston, peers=[('C44__S12', ulverston)], pool_agencies=True)
    assert actor_ids(s12)['notice'] == actor_ids(s03)['notice'] == 'county:C44:ulverston_county'


# ----------------------------------------------------------------- tier three
def test_same_named_offices_in_different_counties_do_not_pool():
    """Recurrence alone is not identity: seven Revenue Divisions are seven offices."""
    c29 = county_actors('Drummond')
    c44 = county_actors('Ulverston')
    left, report = bridge('C29__S12', c29, peers=[('C44__S12', c44), ('C41__S12', county_actors('Ravensden'))],
                          pool_agencies=True)
    right, _ = bridge('C44__S12', c44, peers=[('C29__S12', c29)], pool_agencies=True)
    assert actor_ids(left)['notice'] == 'county:C29:auditor_controller_revenue_division'
    assert actor_ids(right)['notice'] == 'county:C44:auditor_controller_revenue_division'
    assert actor_ids(left)['notice'] != actor_ids(right)['notice']
    row = next(x for x in report['agency_identity']['assignments'] if x['ledger_actor_id'] == 'AG')
    assert row['counties_naming_this_actor'] == ['C29', 'C41', 'C44'] and row['tier'] == 'county_office'
    assert 'no statute-scope document names it' in row['basis']


def test_payer_third_party_and_unknown_actors_never_pool():
    c29 = county_actors('Drummond')
    c44 = county_actors('Ulverston')
    left, report = bridge('C29__S12', c29, peers=[('C44__S12', c44)], pool_agencies=True, namespace=True)
    right, _ = bridge('C44__S12', c44, peers=[('C29__S12', c29)], pool_agencies=True, namespace=True)
    # The applicants share a name across the two counties, yet keep distinct
    # identities; only the model's own role bucket merges them downstream, and
    # that is not a claim that one agency serves both.
    assert actor_ids(left)['file'] == 'C29__payer' and actor_ids(right)['file'] == 'C44__payer'
    assert actor_ids(left)['screen'] is None and actor_ids(right)['screen'] is None
    rows = {a['ledger_actor_id']: a for a in report['agency_identity']['assignments']}
    for ident in ('C29__payer', 'C29__UNK', 'C29__TP'):
        assert rows[ident]['tier'] == 'programme_scoped' and rows[ident]['pooled'] is False
        assert rows[ident]['actor_id'] == ident and 'never pooled' in rows[ident]['basis']
    assert sorted(report['agency_identity']['never_pooled']) == ['C29__TP', 'C29__UNK', 'C29__payer']


def test_canonicalisation_refuses_to_merge_two_distinct_ledger_actors():
    clashing = county_actors('Drummond')
    clashing[2]['name'] = REVENUE  # REV and AG would collapse to one county id
    with pytest.raises(BridgeError, match='keeps them apart'):
        bridge('C29__S12', clashing, pool_agencies=True)


def test_a_programme_id_without_a_county_namespace_is_refused():
    with pytest.raises(BridgeError, match='county namespace'):
        bridge('T__P', county_actors('Drummond'), pool_agencies=True)


def test_peer_ledgers_are_only_read_for_the_pooling_rule():
    with pytest.raises(BridgeError, match='Peer ledgers'):
        bridge('C29__S12', county_actors('Drummond'), peers=[('C44__S12', county_actors('Ulverston'))])
    # Without peers nothing can recur across counties, so everything is county tier.
    _, report = bridge('C29__S12', county_actors('Drummond', agency_name=STATE_BOARD), pool_agencies=True)
    assert report['agency_identity']['state_level_ids'] == []
    assert report['agency_identity']['peer_program_ids'] == []


def test_canonical_agency_identity_is_the_single_documented_rule():
    doc = canonical_agency_identity.__doc__
    assert 'Tier 1' in doc and 'Tier 2' in doc and 'Tier 3' in doc
    e = programme('C29__S12', county_actors('Drummond', agency_name=STATE_BOARD))[0]
    peer = programme('C44__S12', county_actors('Ulverston', agency_name=STATE_BOARD,
                                               docs=('S12__statute_text',)))[0]
    decision = canonical_agency_identity(e, [peer, peer])
    assert decision['peer_program_ids'] == ['C44__S12']  # a repeated peer is counted once
    assert decision['actor_ids']['AG'] == 'state:marisol_contractors_state_license_board'
    assert decision['actor_ids']['payer'] == 'payer'


# ------------------------------------------------------------ default is current
def test_the_flag_defaults_to_current_behaviour_and_changes_only_actor_identity():
    c29 = county_actors('Drummond', agency_name=STATE_BOARD)
    peer = [('C44__S12', county_actors('Ulverston', agency_name=STATE_BOARD, docs=('S12__statute_text',)))]
    off, off_report = bridge('C29__S12', c29)
    on, on_report = bridge('C29__S12', c29, peers=peer, pool_agencies=True)
    assert set(actor_ids(off).values()) == {'payer', 'AG', 'REV', None}
    assert 'state:marisol_contractors_state_license_board' in set(actor_ids(on).values())
    blind_off, blind_on = copy.deepcopy(off), copy.deepcopy(on)
    for program in (blind_off, blind_on):
        for route in program['routes']:
            for operation in route['operations']:
                operation.pop('actor_id')
    assert blind_off == blind_on  # nothing but agency identity moved
    assert off_report['agency_identity']['enabled'] is False
    assert off_report['agency_identity']['assignments'] == []
    assert on_report['agency_identity']['enabled'] is True


def test_default_cli_output_carries_ledger_actor_ids_and_no_fee_field(tmp_path):
    e, h, c = programme('C29__S12', county_actors('Drummond'), fees=[
        fee('f1', ['pay'], 190., 'C29__fee_schedule', '| Registration | $190 |')])
    for name, payload in (('evidence', e), ('handoff', h), ('compilation', c)):
        (tmp_path / f'{name}.json').write_text(json.dumps(payload))
    args = ['program', '--evidence', str(tmp_path / 'evidence.json'), '--handoff', str(tmp_path / 'handoff.json'),
            '--compilation', str(tmp_path / 'compilation.json'), '--out']
    main(args + [str(tmp_path / 'plain')])
    plain = (tmp_path / 'plain' / 'data.json').read_bytes()
    operations = json.loads(plain)['programs'][0]['routes'][0]['operations']
    assert all('fee' not in o for o in operations)
    assert {o['actor_id'] for o in operations} <= {'payer', 'AG', 'REV', None}
    main(args + [str(tmp_path / 'again')])
    assert (tmp_path / 'again' / 'data.json').read_bytes() == plain
    main(args + [str(tmp_path / 'flags'), '--pool-agencies', '--operation-fees'])
    flagged = json.loads((tmp_path / 'flags' / 'data.json').read_text())['programs'][0]
    assert flagged != json.loads(plain)['programs'][0]
    report = json.loads((tmp_path / 'flags' / 'bridge_report.json').read_text())
    assert report['agency_identity']['enabled'] and report['operation_fees']['enabled']
    manifest = json.loads((tmp_path / 'flags' / 'manifest.json').read_text())
    assert manifest['provenance']['config']['pool_agencies'] is True
    assert manifest['provenance']['config']['operation_fees'] is True
    assert manifest['hidden_truth_read'] is False


# -------------------------------------------------------------------- rule k
FEES = [
    fee('f_pay_page', ['pay'], 190., 'C29__program_page', 'The registration fee is $190, due at submittal.'),
    fee('f_pay_sched', ['pay'], 190., 'C29__fee_schedule', '| Registration | $190 | at submittal |'),
    fee('f_file_form', ['file'], 180., 'C29__form', '| Filing | $180 |'),
    fee('f_file_sched', ['file'], 225., 'C29__fee_schedule', '| Filing | $225 | at issuance |'),
    fee('f_typical', ['issue'], 155., 'C29__ordinance', 'The issuance fee is $155', statistic='typical'),
    fee('f_case', ['resubmit'], 265., 'C29__reddit_1', 'resubmitting cost me $265', case='c9'),
    fee('f_estimate', ['resubmit'], 200., 'C29__staff_report', 'The recommended fee is $200', statistic='estimate'),
    fee('f_cap', ['resubmit'], None, 'C29__ordinance', 'No fee shall exceed the reasonable cost.',
        statistic='statutory_cap', qualitative=True),
    fee('f_total', ['pay', 'file'], 370., 'C29__news', 'All in, the programme costs $370.', scope='process'),
    fee('f_pair', ['side', 'review'], 90., 'C29__news', 'Those two steps come to $90 together.'),
]


@pytest.fixture(scope='module')
def feed():
    return bridge('C29__S12', county_actors('Drummond'), fees=FEES, operation_fees=True)


def test_a_fee_attaches_only_on_a_quote_naming_that_step(feed):
    program, report = feed
    fees = {o['id']: o['fee'] for o in program['routes'][0]['operations']}
    assert fees['pay'] == 190. and fees['issue'] == 155.
    attached = {a['operation_id']: a for a in report['operation_fees']['operations_with_quoted_fee']}
    assert sorted(attached) == ['issue', 'pay']
    assert [q['measurement_id'] for q in attached['pay']['quotes']] == ['f_pay_page', 'f_pay_sched']
    assert all(q['quote'] for q in attached['pay']['quotes'])
    assert attached['issue']['quotes'][0]['statistic'] == 'typical'


def test_a_step_that_tenders_nothing_is_zero_by_recorded_judgement(feed):
    program, report = feed
    fees = {o['id']: o['fee'] for o in program['routes'][0]['operations']}
    assert fees['screen'] == 0. and fees['notice'] == 0. and fees['approve'] == 0. and fees['appeal'] == 0.
    zeros = {a['operation_id']: a for a in report['operation_fees']['operations_zero_by_judgement']}
    assert sorted(zeros) == ['appeal', 'approve', 'deny', 'notice', 'screen']
    assert all(z['fee'] == 0. and z['judgement_not_a_reading'] for z in zeros.values())
    assert 'agency-side internal work' in zeros['notice']['judgement']
    assert 'unresolved performer' in zeros['screen']['judgement']
    assert 'not a payment' in zeros['appeal']['judgement']
    assert 'a recorded judgement' in report['operation_fees']['zero_is_a_judgement']


def test_an_unstated_fee_is_none_and_never_zero(feed):
    program, report = feed
    fees = {o['id']: o['fee'] for o in program['routes'][0]['operations']}
    unstated = {a['operation_id']: a for a in report['operation_fees']['operations_with_unstated_fee']}
    assert sorted(unstated) == ['file', 'resubmit', 'review', 'side']
    assert all(fees[k] is None and v['fee'] is None and v['missing'] for k, v in unstated.items())
    assert report['operation_fees']['counts'] == dict(quoted=2, zero_by_judgement=5, unstated=4)
    assert 'rather than counting it as zero' in report['operation_fees']['none_is_not_zero']
    # a charge is only plausible where a claim links one, or the step is a payment
    assert 'a fee measurement links a charge to this step' in unstated['resubmit']['reason']


def test_a_payment_step_with_no_published_amount_stays_unknown():
    lean = [f for f in FEES if f['id'] not in ('f_pay_page', 'f_pay_sched')]
    program, report = bridge('C29__S12', county_actors('Drummond'), fees=lean, operation_fees=True)
    fees = {o['id']: o['fee'] for o in program['routes'][0]['operations']}
    assert fees['pay'] is None
    row = next(a for a in report['operation_fees']['operations_with_unstated_fee']
               if a['operation_id'] == 'pay')
    assert row['task_type'] == 'payment' and 'purpose is to tender money' in row['missing']


def test_conflicting_published_amounts_leave_the_step_unstated(feed):
    _, report = feed
    row = next(a for a in report['operation_fees']['operations_with_unstated_fee']
               if a['operation_id'] == 'file')
    assert row['fee'] is None and '180' in row['missing'] and '225' in row['missing']
    assert 'does not choose between conflicting quoted amounts' in row['reason']
    assert {q['measurement_id'] for q in row['quotes']} == {'f_file_form', 'f_file_sched'}


def test_case_reports_estimates_caps_and_totals_are_not_route_inputs(feed):
    _, report = feed
    rejected = {r['measurement_id']: r['reason'] for r in
                report['operation_fees']['fee_measurements_not_used_as_route_input']}
    assert 'reported by a case' in rejected['f_case']
    assert 'proposal, budget or ceiling' in rejected['f_estimate']
    assert 'no quoted amount' in rejected['f_cap']
    assert 'not attributable to one step' in rejected['f_total']
    assert 'never spread across steps' in rejected['f_pair']
    row = next(a for a in report['operation_fees']['operations_with_unstated_fee']
               if a['operation_id'] == 'resubmit')
    assert sorted(row['fee_claims_not_usable']) == ['f_cap', 'f_case', 'f_estimate']


def test_the_report_says_plainly_which_routes_have_no_fee_total(feed):
    _, report = feed
    availability = report['operation_fees']['fee_total_availability']
    assert availability['available_on_every_route'] is False
    assert availability['routes_without_a_fee_total'] == [r['route_id'] for r in availability['routes']]
    assert 'UNAVAILABLE' in availability['note']
    route = availability['routes'][0]
    assert 'file' in route['operations_without_a_stated_fee']
    assert route['paths_without_a_fee_total'] == [p['path_id'] for p in route['paths']]
    assert all(set(p['operations_without_a_stated_fee']) <= set(route['operations_without_a_stated_fee'])
               for p in route['paths'])


def test_a_fully_priced_programme_keeps_its_fee_total():
    priced = [f for f in FEES if f['id'] in ('f_pay_page', 'f_pay_sched', 'f_typical')]
    program, report = bridge('C29__S12', county_actors('Drummond'), fees=priced, operation_fees=True)
    assert all(o['fee'] is not None for r in program['routes'] for o in r['operations'])
    availability = report['operation_fees']['fee_total_availability']
    assert availability['available_on_every_route'] is True and availability['routes_without_a_fee_total'] == []
    assert 'available throughout' in availability['note']
    assert all(p['fee_total_available'] for r in availability['routes'] for p in r['paths'])


def test_fees_are_off_by_default_and_the_flag_adds_only_the_fee_field():
    off, off_report = bridge('C29__S12', county_actors('Drummond'), fees=FEES)
    on, _ = bridge('C29__S12', county_actors('Drummond'), fees=FEES, operation_fees=True)
    assert all('fee' not in o for r in off['routes'] for o in r['operations'])
    assert off_report['operation_fees'] == dict(
        enabled=False, operations_with_quoted_fee=[], operations_zero_by_judgement=[],
        operations_with_unstated_fee=[],
        note='--operation-fees not given; no operation carries a fee field')
    stripped = copy.deepcopy(on)
    for route in stripped['routes']:
        for operation in route['operations']:
            operation.pop('fee')
    assert stripped == off


def test_pooled_identity_and_fees_still_construct_a_finite_visit_hierarchy():
    peer = [('C44__S12', county_actors('Ulverston', agency_name=STATE_BOARD, docs=('S12__statute_text',)))]
    program, _ = bridge('C29__S12', county_actors('Drummond', agency_name=STATE_BOARD), peers=peer,
                        fees=FEES, pool_agencies=True, operation_fees=True)
    model = VisitHierarchy(dict(programs=[copy.deepcopy(program)]),
                           Config(population_size=16, modeled_channels=('elapsed',)))
    for route in range(len(program['routes'])):
        assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [route]))


# --- dated precedence between two published fee amounts -----------------------
# Refusing every disagreement was too blunt. Where the documents date themselves,
# the later amount supersedes and the earlier is a prior version -- which the
# benchmark separately scores as an error to predict (`stale_fee`). Recency may
# only settle a conflict the documents themselves date; undated disagreement
# still refuses, because then there is genuinely nothing to rank on.

def test_a_stated_currency_date_is_read_from_the_measurement_text():
    from pipeline.procbench.bridge_structural_routes import stated_currency_date
    assert stated_currency_date(
        {'cohort': 'Amount printed on the application created August 7, 2021.'}) == (2021, 8, 7)
    assert stated_currency_date(
        {'cohort': 'Schedule current as of March 30, 2026.'}) == (2026, 3, 30)
    assert stated_currency_date({'cohort': 'Registration reported as occurring in 2020.'}) == (2020, 0, 0)


def test_an_undated_or_ambiguously_dated_amount_yields_no_date():
    """Two years in one annotation cannot rank anything, so it must not pretend to."""
    from pipeline.procbench.bridge_structural_routes import stated_currency_date
    assert stated_currency_date({'cohort': None, 'interpretation': 'Published fee.'}) is None
    assert stated_currency_date({'cohort': 'Adopted 2019, amended 2024.'}) is None


def test_the_later_published_amount_supersedes_and_the_earlier_is_recorded():
    """C29's application fee: $180 on a 2021 form, $225 on a schedule current in 2026.

    Refusing here cost the whole programme its fee total, although the corpus
    dates both documents and a third source calls the $180 an explicitly
    historical payment. The current amount must win and the superseded one must
    stay visible, not vanish.
    """
    import json, pathlib
    report = json.loads((pathlib.Path('runs/w2_v6_bridge_burden_20260918/C29_recency')
                         / 'bridge_report.json').read_text())
    fees = report['operation_fees']
    resolved = [q for q in fees['operations_with_quoted_fee'] if q.get('resolved_by')]
    assert resolved, 'the dated conflict should have been resolved, not refused'
    row = next(q for q in resolved if q['operation_id'].endswith('a05'))
    assert row['fee'] == 225.0
    assert row['superseded_amounts'] == [180.0]
    assert '2026' in str(row['current_as_of'])
    assert not fees['operations_with_unstated_fee'], 'no operation should be left unpriced'
    assert fees['fee_total_availability']['routes_without_a_fee_total'] == []


def test_an_undated_disagreement_still_refuses_to_choose():
    """Recency settles only what the documents date. Bare numbers still refuse."""
    from pipeline.procbench.bridge_structural_routes import stated_currency_date
    rows = [{'cohort': 'Published fee.', 'interpretation': ''},
            {'cohort': None, 'interpretation': 'Another published amount.'}]
    assert all(stated_currency_date(r) is None for r in rows)
