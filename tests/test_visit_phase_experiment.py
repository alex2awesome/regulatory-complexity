import copy
import math
from pathlib import Path

import numpy as np
import pytest

from pipeline.procbench.audit_visit_likelihood import frozen_reference
from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy
from pipeline.procbench.compare_visit_phases import score
from pipeline.procbench.generate_visit_phases import generate
from pipeline.procbench.reconcile_evidence import digest
from statistics import NormalDist


def test_phase_generator_preserves_matched_cycle_claims_and_is_replayable():
    cycle,mixed,truth=generate()
    assert (cycle,mixed,truth)==generate()
    original=copy.deepcopy((cycle,mixed,truth))
    a,b=cycle['programs'][0],mixed['programs'][0]
    assert a['routes']==b['routes']
    assert len(a['observations'])==10 and len(b['observations'])==30
    assert a['observations']==[o for o in b['observations'] if o['operators'][0]['basis']=='single_visit_cycle']
    assert truth['mean_wait_days']+truth['mean_service_elapsed_days']==pytest.approx(truth['mean_cycle_days'])
    assert truth['fraction_integral_error']<1e-12
    for data in (cycle,mixed):
        model=VisitHierarchy(data,Config(population_size=16,within_visit_phases=True))
        assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))
    assert (cycle,mixed,truth)==original


def test_reference_audit_uses_frozen_dependencies_and_rejects_tampering(tmp_path):
    source=Path('pipeline/procbench')
    names=['bayes_trace_hierarchy.py','compact_visit_trace.py','bayes_hierarchy.py',
           'latent_gaussian.py','visit_clocks.py','evidence_contract.py','schedule_kernel.py']
    directory=tmp_path/'source'
    directory.mkdir()
    hashes={}
    for name in names:
        content=(source/name).read_bytes()
        (directory/name).write_bytes(content)
        hashes[name]=digest(content)
    manifest={'source_sha256':hashes}
    frozen=frozen_reference(tmp_path,manifest)
    assert frozen.CompactTrace is not __import__('pipeline.procbench.compact_visit_trace',fromlist=['CompactTrace']).CompactTrace
    assert '_frozen_visit_' in frozen.CompactTrace.__module__
    data=generate()[0]
    cfg=Config(population_size=16,within_visit_phases=True)
    current=VisitHierarchy(data,cfg)
    reference=frozen.VisitHierarchy(data,frozen.Config(**cfg.__dict__))
    z=np.random.default_rng(234).normal(size=current.layout.size)
    assert current.log_likelihood(z,[0])==reference.log_likelihood(z,[0])
    with (directory/'compact_visit_trace.py').open('a') as stream:
        stream.write('\n# changed reference\n')
    with pytest.raises(ValueError,match='Saved reference source changed'):
        frozen_reference(tmp_path,manifest)


def test_phase_scores_keep_population_means_quantiles_and_days_distinct():
    truth=generate()[2]
    def estimate(value):
        return dict(median=value,ci90=[value/2,value*2])
    report=dict(programs={'J__appointment':dict(metrics={
        'initial_decision_median_days':estimate(truth['cycle_median_days']),
        'initial_decision_p90_days':estimate(truth['cycle_median_days']*
            math.exp(truth['cycle_log_sd']*NormalDist().inv_cdf(.9)))})},
        agencies={'J:Appointments':{
            'inventory_mean_cycle_days':estimate(truth['mean_cycle_days']),
            'inventory_mean_wait_days':estimate(truth['mean_wait_days']),
            'inventory_mean_service_elapsed_days':estimate(truth['mean_service_elapsed_days'])}})
    result=score(report,truth)
    assert len(result)==5
    for row in result.values():
        assert row['absolute_error']==pytest.approx(0.,abs=1e-14)
        assert row['interval_score_90']==pytest.approx(math.log(4))
        assert row['covered_90']
