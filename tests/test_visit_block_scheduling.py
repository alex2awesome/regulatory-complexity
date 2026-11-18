"""Explicit block-level schedules retain repeats, resources and old defaults."""
import numpy as np
import pytest

from pipeline.procbench.compact_visit_trace import Block, CompactTrace, Operation


def fixture():
    operations=[Operation('a','payer','payer','filing',('submission',)),
                Operation('b','A','agency','review'),
                Operation('c','B','agency','review'),
                Operation('d','A','agency','decision',('decision',))]
    durations=np.array([[2.,3.,7.,1.],[5.,1.,2.,4.]])
    rounds={'repeat':np.array([2,0])}
    resources={'agency_hours':np.array([[0.,.5,.3,.1],[0.,.5,.3,.1]])}
    return operations,durations,rounds,resources


def test_explicit_fork_join_can_overlap_whole_repeat_block_without_interleaving():
    ops,durations,rounds,resources=fixture()
    blocks=[Block('cycle',('a','b'),repeat_key='repeat',predecessors=()),
            Block('other',('c',),predecessors=()),
            Block('end',('d',),predecessors=('cycle','other'))]
    trace=CompactTrace(ops,blocks,durations,rounds,resources)
    np.testing.assert_array_equal(trace.event('initial_decision'),[16.,10.])
    np.testing.assert_array_equal(trace.first_start[:,2],[0.,0.])
    np.testing.assert_array_equal(trace.last_end[:,1],[15.,6.])
    np.testing.assert_array_equal(trace.values(dict(basis='visit_count')),[8,4])
    np.testing.assert_allclose(trace.values(dict(basis='agency_hours')),[1.9,.9])
    for i in range(2):
        expanded=trace.materialize(i)
        assert expanded.event('initial_decision')==trace.event('initial_decision')[i]
        assert expanded.event('modeled_work_end')==trace.modeled_end[i]


def test_explicit_serial_schedule_is_bitwise_equal_to_legacy():
    ops,durations,rounds,resources=fixture()
    old=[Block('cycle',('a','b'),repeat_key='repeat'),Block('other',('c',)),Block('end',('d',))]
    new=[Block('cycle',('a','b'),repeat_key='repeat',predecessors=()),
         Block('other',('c',),predecessors=('cycle',)),Block('end',('d',),predecessors=('other',))]
    a=CompactTrace(ops,old,durations,rounds,resources)
    b=CompactTrace(ops,new,durations,rounds,resources)
    for field in ['first_start','first_end','last_start','last_end','visits','modeled_end']:
        np.testing.assert_array_equal(getattr(a,field),getattr(b,field))
    assert a.event('initial_decision')[0]==23.


def test_declared_graph_is_not_required_to_be_listed_topologically():
    ops,durations,rounds,resources=fixture()
    blocks=[Block('end',('d',),predecessors=('cycle','other')),
            Block('other',('c',),predecessors=()),
            Block('cycle',('a','b'),repeat_key='repeat',predecessors=())]
    t=CompactTrace(ops,blocks,durations,rounds,resources)
    np.testing.assert_array_equal(t.event('initial_decision'),[16.,10.])


def test_unrelated_long_block_does_not_change_decision_but_does_change_work_end():
    ops=[Operation('d','A','agency','decision',('decision',)),Operation('x','B','agency','review')]
    t=CompactTrace(ops,[Block('decision',('d',),predecessors=()),Block('other',('x',),predecessors=())],np.array([[1.,100.]]))
    assert t.event('initial_decision')[0]==1.
    assert t.event('modeled_work_end')[0]==100.
    assert t.materialize().event('modeled_work_end')==100.


@pytest.mark.parametrize('parents,error',[
    ([(),None],'every block'),
    ([(),('missing',)],'known block'),
    ([(),('a','a')],'distinct'),
    ([('a',),()],'cycle'),
    ([('b',),('a',)],'cycle'),
    ([(),'a'],'predecessor lists'),
    ([(),[3]],'known block'),
])
def test_invalid_or_partial_schedule_is_hard_error(parents,error):
    ops=[Operation('x','A','agency','review'),Operation('y','A','agency','review')]
    with pytest.raises(ValueError,match=error):
        CompactTrace(ops,[Block('a',('x',),predecessors=parents[0]),Block('b',('y',),predecessors=parents[1])],np.ones((1,2)))


def test_dwell_and_service_phases_survive_explicit_block_schedule():
    ops,durations,rounds,resources=fixture()
    blocks=[Block('cycle',('a','b'),repeat_key='repeat',dwells=('b',),predecessors=()),
            Block('other',('c',),predecessors=()),Block('end',('d',),predecessors=('cycle','other'))]
    dwells=np.full_like(durations,np.nan);dwells[:,1]=2.
    t=CompactTrace(ops,blocks,durations,rounds,resources,service_fractions=np.full_like(durations,.25),dwells=dwells)
    np.testing.assert_array_equal(t.event('initial_decision'),[22.,12.])
    np.testing.assert_array_equal(t.values(dict(basis='single_visit_cycle',activity_ids=['b'])),[3.,1.])
    for i in range(2):
        assert t.materialize(i).event('initial_decision')==t.event('initial_decision')[i]


def test_integrated_v6_accepts_explicit_schedule_without_changing_serial_likelihood():
    import copy
    from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy
    from pipeline.procbench.run_visit_hierarchy import preflight_report
    from procbench_fixtures import data_fixture
    data=data_fixture(); new=copy.deepcopy(data)
    for program in new['programs']:
        for route in program['routes']:
            for path in route.get('paths',[route]):
                previous=[]
                for block in path['blocks']:
                    block['predecessors']=previous
                    previous=[block['id']]
    cfg=Config(population_size=16)
    old=VisitHierarchy(data,cfg); current=VisitHierarchy(new,cfg)
    assert current.layout.size==old.layout.size
    rng=np.random.default_rng(20260920)
    for _ in range(8):
        z=rng.normal(size=old.layout.size)
        assert current.log_likelihood(z,[0])==old.log_likelihood(z,[0])
        assert current.log_likelihood_reference(z,[0])==pytest.approx(old.log_likelihood(z,[0]),abs=1e-10)
    report=preflight_report(current)
    assert all(r['mode']=='explicit_block_dag' for r in report['scheduling']['paths'])
    assert report['scheduling']['overlap_learned'] is False
    assert all(r['mode']=='legacy_serial_blocks' for r in old.scheduling_report()['paths'])
