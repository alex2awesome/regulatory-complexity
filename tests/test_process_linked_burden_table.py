import copy
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.process_structure.burden_table import linked_draw_table
from pipeline.procbench.process_structure.step_burden import conditional_step_burden
from test_case_paths import path_data, cfg


def fixture():
    data = path_data()
    for op in data['programs'][0]['routes'][0]['operations']:
        op['fee'] = 10. if op['id'] == 'approve' else 0.
    model = VisitHierarchy(data, cfg())
    states = np.random.default_rng(117).normal(scale=.2, size=(2,8,model.layout.size))
    routes = np.zeros((2,8,1), dtype=int)
    metadata = {'J__P': {op.id: {} for op in model.programs[0]['routes'][0]['operations']}}
    return model, states, routes, metadata


def test_table_preserves_linked_products_shares_and_conditional_path_participation():
    model, states, routes, meta = fixture()
    path_coordinates = model.programs[0]['routes'][0]['path_coordinates']
    # Deliberately correlate route probability and duration in the retained
    # array: this is a mechanics example, not draws from a validated fit.
    states[:,:,path_coordinates] = np.arange(16).reshape(2,8,1)/3-2
    states[:,:,model.location[0]] = np.arange(16).reshape(2,8)/10-1
    got = linked_draw_table(model, states, routes, meta)
    reference = [conditional_step_burden(model, model.programs[0], z, model.parameters(z), 0)
                 for z in states.reshape(-1,model.layout.size)]
    by_step = {row['step_id']:row for row in got['rows']}
    approval = by_step['approve']
    assert approval['presence_probability'] == 1.
    assert approval['case_participation_probability']['posterior']['mean'] < 1.
    assert approval['elapsed_time']['posterior']['mean'] == pytest.approx(
        np.mean([r['steps']['approve']['elapsed_exposure'] for r in reference]))
    for channel in ('elapsed_exposure', 'fee_total', 'modeled_end_clock_contribution'):
        expected = np.mean([r['steps']['approve']['shares_of_population_mean'][channel] for r in reference])
        assert approval['burden_shares_by_channel'][channel]['posterior']['mean'] == pytest.approx(expected)
    ratio_of_means = (np.mean([r['steps']['approve']['elapsed_exposure'] for r in reference])
                      / np.mean([r['totals']['elapsed_exposure'] for r in reference]))
    assert approval['burden_shares_by_channel']['elapsed_exposure']['posterior']['mean'] != pytest.approx(ratio_of_means, abs=1e-3)
    assert got['scientific_release_eligible'] is False
    assert approval['active_applicant_time']['posterior']['mean'] == 0.
    assert by_step['file']['active_applicant_time']['posterior'] is None
    json.dumps(got, allow_nan=False)


def test_unknown_fee_states_not_dropped_when_other_inventory_has_known_zero():
    data = dict(programs=[dict(id='P', observations=[], routes=[
        dict(id='one', prior_weight=1., operations=[dict(id='a', actor_id='payer', actor_role='payer', task_type='a', fee=0.)],
             blocks=[dict(id='a', operations=['a'])]),
        dict(id='two', prior_weight=1., operations=[dict(id='b', actor_id='payer', actor_role='payer', task_type='b', fee=None),
                                                 dict(id='c', actor_id='payer', actor_role='payer', task_type='c', fee=0.)],
             blocks=[dict(id='b', operations=['b','c'])])])])
    model = VisitHierarchy(data, Config(population_size=16, modeled_channels=('elapsed',)))
    states = np.zeros((2,8,model.layout.size))
    routes = np.tile(np.array([0,1]*4), (2,1))[:,:,None]
    table = linked_draw_table(model, states, routes, {'P':{'a':{}, 'b':{}, 'c':{}}})
    row = next(row for row in table['rows'] if row['step_id'] == 'b')
    assert row['presence_probability'] == .5
    assert row['cost_and_payee']['posterior'] is None
    assert row['cost_and_payee']['status'] == 'partially_unavailable'
    assert row['cost_and_payee']['defined_draw_fraction'] == .5
    count = table['programs']['P']['inventory_available_action_count']['posterior']
    assert count['mean'] == 1.5
    assert count['median'] == 1
    assert count['ci90'] == [1,2]
    assert count['empirical_posterior_count_mass'] == {'0':0., '1':.5, '2':.5, '3':0.}


@pytest.mark.parametrize('mutation', ['wrong_shape', 'nonfinite', 'float_routes', 'unknown_route', 'drop_metadata', 'extra_metadata'])
def test_invalid_or_unlinked_inputs_fail_closed(mutation):
    model, states, routes, meta = fixture()
    if mutation == 'wrong_shape':
        states = states[:,:,:-1]
    elif mutation == 'nonfinite':
        states[0,0,0] = np.nan
    elif mutation == 'float_routes':
        routes = routes.astype(float)
    elif mutation == 'unknown_route':
        routes[0,0,0] = 100
    elif mutation == 'drop_metadata':
        del meta['J__P']['review']
    else:
        meta['J__P']['invented'] = {}
    with pytest.raises(ValueError):
        linked_draw_table(model, states, routes, meta)


def test_parallel_elapsed_exposure_is_not_labeled_an_additive_process_clock():
    model, states, routes, meta = fixture()
    data = copy.deepcopy(model.data)
    for path in data['programs'][0]['routes'][0]['paths']:
        path['blocks'][0]['edges'] = []
    parallel = VisitHierarchy(data, cfg())
    table = linked_draw_table(parallel, states, routes, meta)
    assert table['programs']['J__P']['serial_schedule_draw_fraction'] == 0.
    for row in table['rows']:
        assert row['elapsed_time']['posterior'] is not None
        assert row['modeled_end_clock_contribution']['posterior'] is None
        assert row['burden_shares_by_channel']['modeled_end_clock_contribution']['posterior'] is None
