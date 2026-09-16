import numpy as np
import hashlib
import json
import pytest

from pipeline.procbench.calibrate_hierarchy import inference_seed
from pipeline.procbench.summarize_calibration import apply_rng_repairs
from pipeline.procbench.extend_hierarchy import check_fresh_seed
from pipeline.procbench.extend_validation import main as extend_recovery


def test_calibration_inference_is_independent_of_generated_truth_including_zero():
    for seed in (68210, 93267):
        streams = set()
        for rep in range(48):
            inferred = inference_seed(seed,rep)
            assert inferred == inference_seed(seed,rep)
            assert inferred not in streams
            streams.add(inferred)
            truth = np.random.default_rng(np.random.SeedSequence([seed,rep])).normal(size=10)
            for chain in range(2):
                initial = np.random.default_rng(inferred+104729*chain).normal(size=10)
                assert not np.array_equal(truth,initial)


def test_chain_extension_refuses_reused_streams_including_prior_extensions():
    original = {'config':{'seed':11,'chains':4}}
    extension = {'config':{'seed':11,'chains':4},
                 'continuation_config':{'seed':22,'chains':4},'base_manifest':original}
    check_fresh_seed(extension,33,4)
    for seed in (11,22,11+104729,22+104729):
        with pytest.raises(ValueError,match='previously used chain stream'):
            check_fresh_seed(extension,seed,4)


@pytest.mark.parametrize('problem',['seed','evidence'])
def test_recovery_extension_checks_rng_and_data_before_sampling(tmp_path,problem):
    run,out = tmp_path/'recovery',tmp_path/'extension'
    run.mkdir()
    (run/'comparison.json').write_text(json.dumps({'config':{'seed':20260916,'chains':4}}))
    manifest = {'config':{'seed':20260916,'chains':4}}
    if problem=='seed':
        manifest['continuation_config'] = {'seed':625933,'chains':4}
        message = 'previously used chain stream'
    else:
        manifest['generated_evidence_sha256'] = 'changed'
        message = 'Generated evidence differs'
    (run/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match=message):
        extend_recovery(['--run',str(run),'--out',str(out),'--no-totals'])
    assert not out.exists()


def test_rng_correction_keeps_original_rows_and_checks_provenance(tmp_path):
    batch = tmp_path/'batch'
    rep = batch/'replicate_000'
    rep.mkdir(parents=True)
    (rep/'evidence.json').write_text('{}')
    repair = tmp_path/'repair'
    repair.mkdir()
    old = {'global_location': {'rank_fraction': .2}}
    new = {'global_location': {'rank_fraction': .3}}
    batches = [{'seed': 1, 'runs': [old]}]
    (repair/'result.json').write_text(json.dumps(new))
    manifest = dict(base_run=str(batch),replicate=0,batch_seed=1,original_result=old,
        evidence_sha256=hashlib.sha256((rep/'evidence.json').read_bytes()).hexdigest(),
        result_sha256=hashlib.sha256((repair/'result.json').read_bytes()).hexdigest())
    (repair/'manifest.json').write_text(json.dumps(manifest))
    corrected,provenance = apply_rng_repairs(batches,[str(batch)],[str(repair)])
    assert corrected == [[new]]
    assert batches[0]['runs'] == [old]
    assert provenance[0]['original_result'] == old
    with pytest.raises(ValueError,match='Duplicate'):
        apply_rng_repairs(batches,[str(batch)],[str(repair),str(repair)])
    (repair/'result.json').write_text('{}')
    with pytest.raises(ValueError,match='incomplete or its result changed'):
        apply_rng_repairs(batches,[str(batch)],[str(repair)])
