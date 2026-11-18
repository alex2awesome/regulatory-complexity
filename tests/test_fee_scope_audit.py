"""The fee-scope check must catch amounts whose words contradict their scope.

The error this guards is specific and has a history in this project: an amount
recorded as process-scoped compiles as the whole-case path total, so a yearly
overhead figure or a setup estimate that bundles insurance becomes the price of
the permit. `burden_channels.fee_compilation()` cannot catch it, because it
trusts the scope field.

The other half of the job is not crying wolf. A first version flagged every
"renewal fee" as recurring, which was 24 false positives out of 44, and a check
that noisy gets ignored. That case is pinned below.
"""
import pytest

from pipeline.procbench.audit_fee_scope import audit


def _m(ident, quote, metric='fee', scope='process', value=100.0):
    return {'id': ident, 'metric': metric, 'scope': scope, 'quote': quote, 'value': value,
            'lower': None, 'upper': None, 'statistic': 'individual', 'case_id': None,
            'doc_id': 'd1'}


def _ev(measurements):
    return {'program_id': 'p', 'measurements': measurements}


def _flags(quote, **kw):
    hits = audit(_ev([_m('m', quote, **kw)]))
    return [f.split(':')[0] for f in hits[0]['flags']] if hits else []


@pytest.mark.parametrize('quote', [
    'commissaries in LA run like $800-2,000/month',
    'The health permit itself is $605-$1,235/year',
    'California has an $800/year LLC franchise tax',
    'the permit fee is between $400 to $1000 annually',
    'Dealer Inspection Program Annual Fee',
    'it was around $75 for a month and it helped me pass the test'])
def test_a_repeating_amount_is_flagged(quote):
    assert 'recurrence' in _flags(quote)


def test_a_renewal_fee_is_not_a_recurrence():
    """A renewal is a separate run of the process, not an amount repeating in one."""
    assert _flags('Renewal Fee Paid upon the submission of your application $178.00') == []
    assert _flags('Renewal Fee $158.00 includes $93 DOJ Processing Fee plus a $40 '
                  'administration fee') == []


def test_a_total_bundling_non_process_costs_is_flagged():
    assert 'bundling' in _flags('~ $55K but that includes CSLB fees, liability insurance, bonding')
    assert 'bundling' in _flags('a lot of little fees that they throw in plus the school fees')


def test_a_fee_itemised_into_other_process_fees_is_not_bundling():
    """Sub-fees of the same process are a legitimate breakdown, not contamination."""
    assert _flags('Renewal Fee $249.00 Inc. DOJ Livescan Fee - $93.00+ Sheriff Fee - $156.00') == []
    assert _flags('$809.00 includes the DOJ fee and the Sheriff processing fee') == []


def test_money_lost_while_waiting_is_flagged_as_consequential():
    flags = _flags('I was probably out about $25,000/year in over head costs')
    assert 'consequential' in flags and 'recurrence' in flags


def test_only_fee_measurements_on_a_path_scope_are_examined():
    assert audit(_ev([_m('m', 'it cost $800/year', metric='elapsed')])) == []
    assert audit(_ev([_m('m', 'it cost $800/year', scope='standing')])) == []


@pytest.mark.parametrize('scope', ['process', 'segment', 'step'])
def test_every_path_scope_is_examined(scope):
    assert 'recurrence' in _flags('it cost $800/year', scope=scope)


def test_an_ordinary_one_time_fee_is_not_flagged():
    assert _flags('Amnesty Program applicants will be required to pay a $590 fee') == []
    assert _flags('I paid approximately $8,000 in July for permits and applications') == []


def test_a_hit_carries_what_a_reviewer_needs():
    hits = audit(_ev([_m('m1', 'the permit is $400 annually', value=400.0)]))
    assert hits[0]['measurement_id'] == 'm1'
    assert hits[0]['value'] == 400.0
    assert hits[0]['doc_id'] == 'd1'
    assert hits[0]['quote'] == 'the permit is $400 annually'


def test_the_audit_changes_nothing():
    import copy
    evidence = _ev([_m('m', 'it cost $800/year')])
    before = copy.deepcopy(evidence)
    audit(evidence)
    assert evidence == before


def test_a_column_header_in_a_long_table_extract_is_not_a_recurrence():
    """Fee schedules extract as table blocks whose headers say "Annual Volume"."""
    quote = ('Estimated Average Labor Annual Estimated Time Per Estimated Annual Estimated Fee '
             'Cost of Service Per Current Fee / Existing Cost Revenues at Full Notes Fee Name '
             'Fee Type Activity (hours) Volume of Revenues at No. Activity Deposit Recovery % '
             'Cost Recovery Activity Current Fee Fee Well & Septic $ 250 Well & Septic Services '
             'new Well & Septic Staff Consultation Fee (1 hr. minimum) hourly 1.00 $ 250 new % - '
             '$ - $ - Septic Site Evaluation Soil Profile Evaluation 4.00 $ 1,000 $ 511 51% 326')
    assert _flags(quote) == []


def test_a_period_stated_next_to_its_amount_is_still_caught_in_a_long_quote():
    quote = ('Some preamble about the programme that goes on for a while and describes the '
             'permit and its conditions in general terms, and then says the health permit '
             'itself is $605-$1,235/year and takes 3-6 weeks to process, and continues.')
    assert 'recurrence' in _flags(quote)


def test_a_short_caption_naming_a_recurring_fee_is_caught_without_an_amount():
    assert 'recurrence' in _flags('Dealer Inspection Program Annual Fee:')


def test_a_charge_that_names_its_own_period_is_caught_whatever_the_padding():
    """PDF table extracts pad a caption to hundreds of characters."""
    quote = 'Dealer Inspection Program Annual Fee:' + ' ' * 150 + '$95.00'
    assert 'recurrence' in _flags(quote)
    assert 'recurrence' in _flags('SP920 STORMWATER ANNUAL FEE-INSP FREQ EVERY 2 YRS $192.00')


def test_the_named_period_rule_needs_the_noun_not_just_the_word_annual():
    """"Annual Volume" is a column header, not a charge that recurs."""
    quote = ('Estimated Annual Volume of Activity ' + 'column header text ' * 12
             + 'Soil Profile Evaluation $511 per site')
    assert _flags(quote) == []
