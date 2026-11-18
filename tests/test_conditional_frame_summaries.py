import itertools

import pytest

from pipeline.procbench.summarize_conditional_frames import finite_sample_median_bounds


def test_even_sample_uses_two_middle_order_statistics():
    result = finite_sample_median_bounds([
        {'lower': 0, 'upper': 4}, {'lower': 2, 'upper': 8},
        {'lower': 3, 'upper': 5}, {'lower': 9, 'upper': 10}])
    assert (result['lower'], result['upper']) == (2.5, 6.5)


def test_censored_values_do_not_imply_unbounded_median_unless_central_rank_requires_it():
    rows = [{'lower': 1, 'upper': 2}, {'lower': 3, 'upper': 4},
            {'lower': 5, 'upper': None}]
    assert finite_sample_median_bounds(rows)['upper'] == 4
    rows[1]['upper'] = None
    assert finite_sample_median_bounds(rows)['upper'] is None


def test_endpoint_bounds_cover_all_small_sample_endpoint_combinations():
    rows = [{'lower': 0, 'upper': 10}, {'lower': 3, 'upper': 4},
            {'lower': 2, 'upper': 7}]
    result = finite_sample_median_bounds(rows)
    medians = [sorted(values)[1] for values in itertools.product(*[
        (row['lower'], row['upper']) for row in rows])]
    assert result['lower'] == min(medians)
    assert result['upper'] == max(medians)


def test_terminal_neutral_lower_bound_is_finite_lower_and_unbounded_upper():
    rows = [
        {'lower': 2, 'upper': 4, 'observation_kind':'completed_interval'},
        {'lower': 5, 'upper': None, 'observation_kind':'terminal_neutral_lower_bound'}]
    result = finite_sample_median_bounds(rows)
    assert result['lower'] == 3.5
    assert result['upper'] is None


@pytest.mark.parametrize('rows', [[], [{'lower': -1, 'upper': 1}],
    [{'lower': True, 'upper': 3}], [{'lower': 1, 'upper': 1}],
    [{'lower': float('nan'), 'upper': None}], [{'lower': 0, 'upper': float('inf')}],
    [{'lower': 1, 'upper': False}]])
def test_invalid_intervals_fail(rows):
    with pytest.raises(ValueError):
        finite_sample_median_bounds(rows)
