"""Exact-computation checks; no new sampler, priors or reduced population grid."""
import numpy as np
import pytest
from scipy.special import expit,logsumexp

from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy
from pipeline.procbench.compact_visit_trace import PopulationTraceMixture,population_quantile
from procbench_fixtures import data_fixture,observation
from test_case_paths import path_data


class UncachedPopulationReference(VisitHierarchy):
    def _likelihood_population(self,p,z,par,route_index):
        return self.trace(p,z,par,route_index,True)

    def _selection_population_summary(self,p,population,strength,route_index):
        mixture=isinstance(population,PopulationTraceMixture)
        values=population.event('initial_decision')
        threshold=(population_quantile(population,np.log(values),.75) if mixture
                   else float(np.quantile(np.log(values),.75)))
        traces=population.traces if mixture else (population,)
        normalizers=[]
        for trace in traces:
            h=expit((np.log(trace.event('initial_decision'))-threshold)/self.cfg.selection_width)
            normalizers.append(logsumexp(np.logaddexp(np.log1p(-h),strength+np.log(h)))
                               -np.log(len(trace.durations)))
        return threshold,np.asarray(normalizers)


def model_data(paths):
    data=path_data() if paths else data_fixture()
    data['programs'][0]['observations']=[o for o in data['programs'][0]['observations']
        if all(op['basis'] not in {'payer_hours','agency_hours'} for op in o['operators'])]
    for observation_row in data['programs'][0]['observations']:
        observation_row['sampling']='delay_selected'
    return data


@pytest.mark.parametrize('paths',[False,True])
def test_population_clock_cache_reused_across_phase_case_and_source_changes(paths):
    model=VisitHierarchy(model_data(paths),Config(population_size=32,
        modeled_channels=('elapsed',),within_visit_phases=True,selection_sd=2.))
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    first=model._likelihood_population(p,z,model.parameters(z),0)
    components=lambda pop:pop.traces if paths else (pop,)
    for coordinates in (model.phase_coordinates,p['case_coordinates'][0],model.source[0]):
        z[coordinates]+=.3
        current=model._likelihood_population(p,z,model.parameters(z),0)
        assert components(current)==components(first)
        assert all(t.service_fractions is None for t in components(current))
    full=model.trace(p,z,model.parameters(z),0,True)
    assert all(t.service_fractions is not None for t in components(full))
    np.testing.assert_array_equal(first.event('initial_decision'),full.event('initial_decision'))


def test_population_phase_report_still_updates_its_fractions():
    data=path_data()
    data['programs'][0]['observations'].append(
        observation('service_mean','service_elapsed',1.,5.,case=None,activities=['file']))
    data['programs'][0]['observations'][-1]['operators'][0]['visits']='first'
    model=VisitHierarchy(data,Config(population_size=16,within_visit_phases=True))
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    first=model._likelihood_population(p,z,model.parameters(z),0)
    z[model.phase_coordinates]+=.2
    second=model._likelihood_population(p,z,model.parameters(z),0)
    assert first.traces!=second.traces
    assert all(t.service_fractions is not None for t in second.traces)
    assert not np.array_equal(first.traces[0].service_fractions,second.traces[0].service_fractions)


@pytest.mark.parametrize('paths',[False,True])
@pytest.mark.parametrize('phases',[False,True])
def test_matches_uncached_full_population_reference_across_parameter_updates(paths,phases):
    data=model_data(paths)
    cfg=Config(population_size=32,modeled_channels=('elapsed',),
               within_visit_phases=phases,selection_sd=2.)
    cached=VisitHierarchy(data,cfg)
    reference=UncachedPopulationReference(data,cfg)
    rng=np.random.default_rng(884)
    z=np.zeros(cached.layout.size)
    for _ in range(25):
        block=cached.blocks[int(rng.integers(len(cached.blocks)))]
        z[block]+=rng.normal(scale=.3,size=len(block))
        actual=cached.log_likelihood(z,[0],parts=True)
        expected=reference.log_likelihood(z,[0],parts=True)
        assert actual.keys()==expected.keys()
        for key in actual:
            assert actual[key]==pytest.approx(expected[key],abs=1e-12)


def test_selection_cache_invalidation_covers_strength_path_weights_and_durations():
    model=VisitHierarchy(model_data(True),Config(population_size=32,
        modeled_channels=('elapsed',),selection_sd=2.))
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    def get(strength):
        pop=model._likelihood_population(p,z,model.parameters(z),0)
        return model._selection_population_summary(p,pop,strength,0)
    get(1.)
    entry=p['selection_population_cache'][0]
    old_norm=entry['normalizers']
    get(1.)
    assert p['selection_population_cache'][0] is entry
    assert entry['normalizers'] is old_norm
    get(2.)
    assert p['selection_population_cache'][0] is entry
    assert entry['normalizers'] is not old_norm
    z[p['routes'][0]['path_coordinates']]+=.5
    get(2.)
    assert p['selection_population_cache'][0] is not entry
    entry=p['selection_population_cache'][0]
    z[model.hierarchy_coordinates[0]]+=.1
    get(2.)
    assert p['selection_population_cache'][0] is not entry
