"""Source-free correctness checks for optional V6 source-scale transitions."""
from dataclasses import replace
import json
import math

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import main as run_main
from procbench_fixtures import data_fixture
from test_source_offset_hierarchy import cfg, hierarchy_data


def hierarchy_model(mode='interwoven'):
    return VisitHierarchy(hierarchy_data(), replace(
        cfg(), source_hierarchy_sampler=mode))


def source_blocks(model):
    coordinates=set(map(int, model.source_offset_hierarchy.coordinates))
    return [np.asarray(block, dtype=int) for block in model.blocks
            if len(block) and set(map(int, block)) <= coordinates]


def test_source_sampler_config_and_split_blocks_are_explicit():
    assert Config().source_hierarchy_sampler == 'blocked'
    with pytest.raises(ValueError, match='Unknown source hierarchy sampler'):
        Config(source_hierarchy_sampler='unsupported')
    blocked=hierarchy_model('blocked')
    interwoven=hierarchy_model('interwoven')
    assert len(source_blocks(blocked)) == 1
    split=source_blocks(interwoven)
    assert len(split) == 5
    np.testing.assert_array_equal(np.concatenate(split),
                                  interwoven.source_offset_hierarchy.coordinates)


@pytest.mark.parametrize('level', ['type', 'document'])
def test_fixed_effect_proposal_is_invertible_and_likelihood_invariant(level):
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    z=np.random.default_rng(31).normal(size=model.layout.size)
    current=model.log_likelihood(z,[0])
    before=hierarchy.transformed(z)
    proposal=hierarchy.interweave_proposal(z,level,.37)
    assert proposal is not None
    after=hierarchy.transformed(proposal['state'])
    for document in hierarchy.documents:
        assert after['document_offsets'][document] == pytest.approx(
            before['document_offsets'][document], abs=2e-15)
    changed=model.log_likelihood(proposal['state'],[0])
    assert changed == pytest.approx(current, abs=2e-12)
    reverse=hierarchy.interweave_proposal(proposal['state'],level,-.37)
    np.testing.assert_allclose(reverse['state'],z,rtol=0.,atol=2e-15)
    assert reverse['correction'] == pytest.approx(-proposal['correction'],abs=2e-15)
    assert reverse['log_jacobian'] == pytest.approx(-proposal['log_jacobian'])


@pytest.mark.parametrize('level', ['type', 'document'])
def test_zero_effect_conditional_has_negative_jacobian_sign(level):
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    z=np.zeros(model.layout.size)
    if level == 'type':
        scale=hierarchy.type_scale_coordinate
        log_sd=hierarchy.type_scale_prior['log_sd']
    else:
        scale=hierarchy.document_scale_coordinate
        log_sd=hierarchy.document_scale_prior['log_sd']
    z[scale]=.25
    epsilon=.4
    proposal=hierarchy.interweave_proposal(z,level,epsilon)
    k=proposal['dimension']
    expected=-.5*((z[scale]+epsilon)**2-z[scale]**2)-k*log_sd*epsilon
    assert proposal['correction'] == pytest.approx(expected)
    assert proposal['log_jacobian'] == pytest.approx(-k*log_sd*epsilon)
    # At actual effect zero this is the Normal(-K*log_sd, 1) conditional,
    # not Normal(0, 1) and not Normal(+K*log_sd, 1).
    assert -k*log_sd < 0


def test_nonfinite_interweave_rejects_without_mutation_or_likelihood_call():
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    z=np.random.default_rng(8).normal(size=model.layout.size)
    original=z.copy()
    assert hierarchy.interweave_proposal(z,'type',1e308) is None
    np.testing.assert_array_equal(z,original)

    class ExtremeRng:
        def normal(self, *, scale):
            assert scale == .5
            return 1e308
        def random(self):
            raise AssertionError('invalid proposals must reject before MH uniform')

    current=model.log_likelihood(z,[0])
    moved,value,calls=model.source_hierarchy_interweave_update(
        z,[0],current,ExtremeRng())
    np.testing.assert_array_equal(moved,original)
    assert value == current and calls == 0


def test_nonfinite_mh_difference_and_correction_reject_without_mutation(monkeypatch):
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    z=np.random.default_rng(82).normal(size=model.layout.size)
    original=z.copy()

    class RejectBeforeUniformRng:
        def normal(self, *, scale):
            assert scale == .5
            return .1
        def random(self):
            raise AssertionError('nonfinite MH ratios must reject before drawing a uniform')

    monkeypatch.setattr(model,'log_likelihood',lambda state,structures: 1e308)
    moved,value,calls=model.source_hierarchy_interweave_update(
        z,[0],-1e308,RejectBeforeUniformRng())
    np.testing.assert_array_equal(moved,original)
    assert value == -1e308 and calls == len(hierarchy.interweave_levels)

    finite_proposal=hierarchy.interweave_proposal
    def nonfinite_correction(state,level,epsilon):
        proposal=finite_proposal(state,level,epsilon)
        proposal['correction']=float('inf')
        return proposal
    monkeypatch.setattr(hierarchy,'interweave_proposal',nonfinite_correction)
    monkeypatch.setattr(model,'log_likelihood',lambda state,structures: 0.)
    moved,value,calls=model.source_hierarchy_interweave_update(
        z,[0],0.,RejectBeforeUniformRng())
    np.testing.assert_array_equal(moved,original)
    assert value == 0. and calls == len(hierarchy.interweave_levels)


def test_document_augmented_jacobian_matches_independent_finite_difference():
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    replicated=[name for name in hierarchy.types
                if len(hierarchy.documents_by_type[name]) >= 2]
    assert len(replicated) >= 2
    document_coordinates=np.concatenate([
        hierarchy.document_coordinates[name] for name in replicated])
    intrinsic_dimension=sum(len(hierarchy.documents_by_type[name])-1
                            for name in replicated)
    assert intrinsic_dimension == len(document_coordinates)
    base=np.random.default_rng(40).normal(size=model.layout.size)
    epsilon=.23
    point=np.r_[base[hierarchy.document_scale_coordinate],
                base[document_coordinates],epsilon]

    def augmented(values):
        state=base.copy()
        state[hierarchy.document_scale_coordinate]=values[0]
        state[document_coordinates]=values[1:-1]
        proposal=hierarchy.interweave_proposal(state,'document',values[-1])
        return np.r_[proposal['state'][hierarchy.document_scale_coordinate],
                     proposal['state'][document_coordinates],-values[-1]]

    step=1e-6
    jacobian=np.column_stack([(augmented(point+step*np.eye(len(point))[j])
                              -augmented(point-step*np.eye(len(point))[j]))/(2*step)
                             for j in range(len(point))])
    sign,log_abs_determinant=np.linalg.slogdet(jacobian)
    assert abs(sign) == 1.
    expected=-intrinsic_dimension*hierarchy.document_scale_prior['log_sd']*epsilon
    assert log_abs_determinant == pytest.approx(expected,abs=2e-9)


def test_interweaving_preserves_standard_normal_prior_ensemble():
    model=hierarchy_model()
    hierarchy=model.source_offset_hierarchy
    rng=np.random.default_rng(20260920)
    draws=[]
    accepted=0
    for _ in range(12000):
        z=np.zeros(model.layout.size)
        z[hierarchy.coordinates]=rng.normal(size=len(hierarchy.coordinates))
        for level in hierarchy.interweave_levels:
            proposal=hierarchy.interweave_proposal(z,level,rng.normal(scale=.5))
            if proposal is not None and math.log(rng.random()) < proposal['correction']:
                z=proposal['state']
                accepted+=1
        draws.append(z[hierarchy.coordinates])
    draws=np.asarray(draws)
    assert accepted > 5000
    assert np.max(np.abs(draws.mean(axis=0))) < .04
    assert np.max(np.abs(draws.var(axis=0)-1.)) < .06
    covariance=np.cov(draws,rowvar=False)
    off_diagonal=covariance-np.diag(np.diag(covariance))
    assert np.max(np.abs(off_diagonal)) < .05


def test_no_hierarchy_interwoven_mode_is_bitwise_default_noop():
    data=data_fixture()
    base=Config(chains=1,warmup=0,draws=8,population_size=16,seed=9182)
    default=VisitHierarchy(data,base).sample()
    optional=VisitHierarchy(data,replace(
        base,source_hierarchy_sampler='interwoven')).sample()
    for left,right in zip(default[:3],optional[:3]):
        np.testing.assert_array_equal(left,right)
    assert default[3] == optional[3]


def test_interwoven_hierarchy_sampler_produces_finite_fixture_draws():
    model=VisitHierarchy(hierarchy_data(),replace(cfg(),chains=1,warmup=0,
        draws=8,seed=881,source_hierarchy_sampler='interwoven'))
    states,routes,likelihood,calls=model.sample()
    assert states.shape == (1,8,model.layout.size)
    assert routes.shape == (1,8,1)
    assert likelihood.shape == (1,8)
    assert np.isfinite(states).all() and np.isfinite(likelihood).all()
    assert calls[0] > 0


def test_report_gates_named_transformed_source_diagnostics_and_allows_fixed_zero():
    model=hierarchy_model()
    rng=np.random.default_rng(19)
    states=rng.normal(size=(2,8,model.layout.size))
    routes=np.zeros((2,8,1),dtype=int)
    likelihood=np.array([[model.log_likelihood(z,[0]) for z in chain]
                         for chain in states])
    report=model.report(states,routes,likelihood)
    names={
        'source_hierarchy:tau_type',
        'source_hierarchy:tau_document',
        'source_hierarchy:type_effect:news',
        'source_hierarchy:document_residual:news_a',
        'source_hierarchy:effective_offset:news_a',
    }
    assert names <= set(report['diagnostics'])
    assert names <= set(report['diagnostics_flagged'])
    reference='source_hierarchy:type_effect:official'
    singleton='source_hierarchy:document_residual:forum_a'
    assert report['diagnostics'][reference]['fixed'] is True
    assert report['diagnostics'][singleton]['fixed'] is True
    assert reference not in report['diagnostics_flagged']
    assert singleton not in report['diagnostics_flagged']


def test_cli_records_interwoven_source_sampler_in_preflight(tmp_path):
    data=tmp_path/'data.json'
    data.write_text(json.dumps(hierarchy_data()))
    out=tmp_path/'preflight'
    run_main(['--data',str(data),'--out',str(out),'--preflight',
              '--observed-channels-only','--population-size','16',
              '--source-hierarchy-sampler','interwoven'])
    report=json.loads((out/'preflight.json').read_text())
    assert report['source_hierarchy_sampler'] == 'interwoven'
