import math

import pytest
from scipy.optimize import linprog

from pipeline.procbench.event_constraints import (
    InconsistentEventConstraints, propagate_event_bounds,
)


def bound(result, start, end):
    return next(row for row in result['bounds']
                if row['start'] == start and row['end'] == end)


def row(ident, start, end, lower, upper, group='source'):
    return dict(id=ident, start=start, end=end, lower=lower, upper=upper,
                report_group_id=group)


def test_joint_pending_phase_bound_is_derived_not_new_report():
    inputs = [row('interview', 'application', 'interview', 1, 3),
              row('pending', 'application', 'decision', 30, None)]
    result = propagate_event_bounds(['application', 'interview', 'decision'], inputs)
    phase = bound(result, 'interview', 'decision')
    assert (phase['lower'], phase['upper']) == (27, None)
    assert set(phase['lower_support']) == {'interview:upper', 'pending:lower'}
    assert not phase['independent_observation']
    assert result['input_constraint_ids'] == ['interview', 'pending']
    assert result['report_group_ids'] == ['source']


def test_completed_shared_origin_difference_interval():
    result = propagate_event_bounds(['a', 'i', 'd'],
        [row('i', 'a', 'i', 3.5, 10.5), row('d', 'a', 'd', 30, 34)])
    phase = bound(result, 'i', 'd')
    assert (phase['lower'], phase['upper']) == (19.5, 30.5)


def test_explicit_order_tightens_but_missing_order_is_not_guessed():
    rows = [row('i', 'a', 'i', 0, 2), row('b', 'a', 'b', 0, 2)]
    without = propagate_event_bounds(['a', 'i', 'b'], rows)
    assert bound(without, 'i', 'b')['lower'] == -2
    with_order = propagate_event_bounds(['a', 'i', 'b'],
        rows + [row('order', 'i', 'b', 0, None)])
    assert bound(with_order, 'i', 'b')['lower'] == 0


def test_disconnected_event_has_no_imputed_zero_or_order():
    result = propagate_event_bounds(['a', 'b', 'c'], [row('ab', 'a', 'b', 1, 2)])
    assert bound(result, 'a', 'c')['lower'] is None
    assert bound(result, 'a', 'c')['upper'] is None
    assert result['automatic_ordering'] is False
    assert result['latent_time_origin_fixed'] is False


def test_inconsistency_exposes_input_support():
    with pytest.raises(InconsistentEventConstraints) as caught:
        propagate_event_bounds(['a', 'b', 'c'],
            [row('ab', 'a', 'b', 2, None), row('bc', 'b', 'c', 2, None),
             row('ac', 'a', 'c', None, 3)])
    assert caught.value.gap < 0
    assert {s.split(':')[0] for s in caught.value.support} == {'ab', 'bc', 'ac'}


def test_self_constraint_nonzero_is_inconsistent():
    with pytest.raises(InconsistentEventConstraints):
        propagate_event_bounds(['a'], [row('self', 'a', 'a', 1, 2)])


@pytest.mark.parametrize('bad', [True, math.inf, -math.inf, math.nan, '3'])
def test_bad_bound_rejected(bad):
    with pytest.raises(ValueError):
        propagate_event_bounds(['a', 'b'], [row('ab', 'a', 'b', bad, None)])


def test_duplicate_ids_unknown_endpoints_and_empty_bounds_rejected():
    for events, rows in [(['a', 'a'], []),
                        (['a'], [row('x', 'a', 'b', 0, 1)]),
                        (['a', 'b'], [row('x', 'a', 'b', None, None)]),
                        (['a', 'b'], [row('x', 'a', 'b', 2, 1)]),
                        (['a', 'b'], [row('x', 'a', 'b', 0, 1)] * 2)]:
        with pytest.raises(ValueError):
            propagate_event_bounds(events, rows)


def test_closure_extrema_agree_with_independent_linear_programs():
    events = ['a', 'b', 'c', 'd']
    rows = [row('ab', 'a', 'b', 1, 4), row('ac', 'a', 'c', 5, 10),
            row('bc', 'b', 'c', 2, None), row('bd', 'b', 'd', 0, 7),
            row('dc', 'd', 'c', -2, 3)]
    result = propagate_event_bounds(events, rows)
    matrix, upper = [], []
    for r in rows:
        vector = [0.] * len(events)
        vector[events.index(r['end'])] += 1
        vector[events.index(r['start'])] -= 1
        if r['upper'] is not None:
            matrix.append(vector); upper.append(r['upper'])
        if r['lower'] is not None:
            matrix.append([-v for v in vector]); upper.append(-r['lower'])
    for r in result['bounds']:
        obj = [0.] * len(events)
        obj[events.index(r['end'])] += 1
        obj[events.index(r['start'])] -= 1
        lo = linprog(obj, A_ub=matrix, b_ub=upper, bounds=[(None, None)]*4)
        hi = linprog([-v for v in obj], A_ub=matrix, b_ub=upper,
                     bounds=[(None, None)]*4)
        assert lo.success and hi.success
        assert r['lower'] == pytest.approx(lo.fun)
        assert r['upper'] == pytest.approx(-hi.fun)


def test_decimal_equalities_close_without_roundoff_cycles_or_inverted_bounds():
    result = propagate_event_bounds(['a', 'b', 'c'], [
        row('ab', 'a', 'b', .1, .1), row('bc', 'b', 'c', .2, .2),
        row('ac', 'a', 'c', .3, .3)])
    assert bound(result, 'a', 'c')['lower'] == .3
    assert bound(result, 'a', 'c')['upper'] == .3
    assert all(r['lower'] == r['upper'] for r in result['bounds'])


def test_small_real_contradiction_is_not_tolerated():
    rows = [row('ab', 'a', 'b', 1, None),
            row('ba', 'b', 'a', -.9999999999, None)]
    with pytest.raises(InconsistentEventConstraints):
        propagate_event_bounds(['a', 'b'], rows)
    with pytest.raises(ValueError, match='tolerance must be zero'):
        propagate_event_bounds(['a', 'b'], rows, tolerance=1e-9)


@pytest.mark.parametrize('bad', [None, True, -1, 1e-15, math.inf, math.nan])
def test_unsupported_tolerance_rejected(bad):
    with pytest.raises(ValueError):
        propagate_event_bounds(['a', 'b'], [], tolerance=bad)


def test_huge_integer_rejected_with_contract_error():
    huge = 10**10000
    with pytest.raises(ValueError):
        propagate_event_bounds(['a', 'b'], [row('ab', 'a', 'b', huge, None)])
    with pytest.raises(ValueError):
        propagate_event_bounds(['a', 'b'], [], tolerance=huge)


def test_derived_output_overflow_is_explicit():
    with pytest.raises(ValueError, match='Derived event bound'):
        propagate_event_bounds(['a', 'b', 'c'], [
            row('ab', 'a', 'b', 1e308, None),
            row('bc', 'b', 'c', 1e308, None)])


def test_huge_inconsistent_cycle_preserves_typed_witness():
    with pytest.raises(InconsistentEventConstraints) as caught:
        propagate_event_bounds(['a', 'b'], [
            row('ab', 'a', 'b', 1e308, None),
            row('ba', 'b', 'a', 1e308, None)])
    assert caught.value.gap is None
    assert caught.value.exact_gap.startswith('-2')
    assert set(caught.value.support) == {'ab:lower', 'ba:lower'}
