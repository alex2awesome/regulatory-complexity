from copy import deepcopy

from pipeline.procbench.solar_panel.evaluate_same_evidence import choose_queries, prediction_schema


def test_query_selection_never_uses_outcomes_and_groups_owners():
    evidence, rows = {}, []
    for subset in ['authority', 'forward_year']:
        for i in range(8):
            for j in range(2):
                rid = f'{subset}_{i}_{j}'
                evidence[rid] = dict(owner_id=f'{subset}_owner{i}')
                rows.append(dict(row_id=rid, phase='permit_review', subset=subset,
                                 truth={'coarsened_value': i * 10 + j}))
    a = choose_queries(rows, evidence, 4)
    changed = deepcopy(rows)
    for r in changed:
        r['truth']['coarsened_value'] = 10000 - r['truth']['coarsened_value']
    b = choose_queries(changed, evidence, 4)
    assert [r['row_id'] for r in a] == [r['row_id'] for r in b]
    assert len({evidence[r['row_id']]['owner_id'] for r in a}) == 8


def test_response_contract_is_predictive_quantiles_not_median_uncertainty():
    fields = prediction_schema()['properties']['predictions']['items']['properties']
    assert {'lower90', 'median', 'upper90'} <= set(fields)
    assert 'median_lower90_days' not in fields
