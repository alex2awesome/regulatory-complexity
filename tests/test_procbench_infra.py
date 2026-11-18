from dataclasses import asdict
import importlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pytest

from pipeline.procbench.infra import codex_runner
from pipeline.procbench.infra.manifest import RunManifest, digest, source_closure, write
from pipeline.procbench.infra.scoring import absolute_log_error, interval_score, log_interval_score


def test_gneiting_raftery_score_has_width_and_correct_tail_penalty():
    assert interval_score(1, 3, 2) == 2
    assert interval_score(1, 3, 0) == 22
    assert interval_score(1, 3, 4) == 22
    assert interval_score(1, 3, 0, alpha=.2) == 12
    assert interval_score(2, 2, 2) == 0
    assert log_interval_score(math.e, math.e**3, 1) == pytest.approx(22)
    assert log_interval_score(1, 4, 5) == pytest.approx(log_interval_score(10, 40, 50))
    assert absolute_log_error(2, 4) == pytest.approx(math.log(2))


@pytest.mark.parametrize('bounds', [(2, 1, 1), (1, 2, float('nan')), (1, float('inf'), 2)])
def test_bad_intervals_are_not_scored(bounds):
    with pytest.raises(ValueError):
        interval_score(*bounds)


@pytest.mark.parametrize('alpha', [0, 1, -1, float('nan')])
def test_invalid_interval_mass_fails(alpha):
    with pytest.raises(ValueError):
        interval_score(1, 2, 1, alpha=alpha)


def test_scores_match_previous_evaluators_numerically():
    from pipeline.procbench.compare_evidence_runs import score_baseline
    from pipeline.procbench.compare_visit_integration import interval_score as visit_score
    from pipeline.procbench.run_hierarchical import posterior_timing_score
    rng = np.random.default_rng(431)
    for _ in range(20):
        draws = np.exp(rng.normal(size=100))
        logs = np.log(np.sort(draws))
        lo, hi = np.quantile(logs, [.05, .95])
        target = float(rng.normal())
        expected = hi-lo+20*max(lo-target, 0)+20*max(target-hi, 0)
        estimate = dict(median=float(np.exp(np.median(logs))), ci90=np.exp([lo, hi]).tolist())
        assert visit_score(estimate, math.exp(target), True)['interval_score_90'] == pytest.approx(expected)
        baseline = dict(median_days=estimate['median'], median_lower90_days=estimate['ci90'][0],
                        median_upper90_days=estimate['ci90'][1])
        assert score_baseline(baseline, math.exp(target))['interval_score90_log_median'] == pytest.approx(expected)
        assert posterior_timing_score(draws, math.exp(target))['interval_score90_log_median'] == pytest.approx(expected)


def test_json_serialization_failure_preserves_existing_file(tmp_path):
    path = tmp_path/'good.json'
    write(path, dict(valid=True))
    original = path.read_bytes()
    with pytest.raises(ValueError):
        write(path, dict(bad=float('nan')))
    assert path.read_bytes() == original


def test_legacy_helper_imports_are_compatibility_exports():
    from pipeline.procbench import reconcile_evidence, run_hierarchical, run_bayes_synth
    assert reconcile_evidence.digest is digest
    for module in (reconcile_evidence, run_hierarchical, run_bayes_synth):
        assert module.write is write


def test_manifest_preserves_inputs_and_snapshots_transitive_sources(tmp_path):
    source = tmp_path/'package'
    (source/'nested').mkdir(parents=True)
    (source/'__init__.py').write_text('')
    (source/'kernel.py').write_text('value = 17\n')
    (source/'nested/__init__.py').write_text('')
    (source/'nested/main.py').write_text('from .. import kernel\nraise RuntimeError("do not execute")\n')
    input_file = tmp_path/'input.json'
    write(input_file, dict(synthetic=True))
    out = tmp_path/'run'
    arguments = dict(operation='test', inputs=[input_file], config={'x': 1}, seeds={'seed': 4},
                     hidden_truth_read=False, source_root=source, sources=['nested/main.py'])
    record = RunManifest(out, {'legacy_field': 17, 'source_sha256': 'legacy-script-hash'}, **arguments)
    assert record.data['status'] == 'running'
    assert record.data.get('completed_utc') is None
    expected = {'__init__.py', 'kernel.py', 'nested/__init__.py', 'nested/main.py'}
    assert record.data['source_sha256'] == 'legacy-script-hash'
    assert set(record.data['provenance']['source_sha256']) == expected
    for name, expected_digest in record.data['provenance']['source_sha256'].items():
        assert digest((out/'source'/name).read_bytes()) == expected_digest
    record.complete(posterior_sha256='synthetic-not-a-real-posterior')
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['legacy_field'] == 17
    assert manifest['status'] == 'completed' and manifest['seconds'] >= 0
    assert manifest['provenance']['hidden_truth_read'] is False
    assert manifest['provenance']['seeds'] == {'seed': 4}
    assert manifest['provenance']['input_sha256'] == {str(input_file): digest(input_file.read_bytes())}
    with pytest.raises(ValueError, match='existing manifest'):
        RunManifest(out, {}, **arguments)
    with pytest.raises(ValueError, match='already complete'):
        record.complete()
    with pytest.raises(ValueError, match='escapes'):
        source_closure(source, ['../input.json'])


def test_extraction_repairs_and_content_addressed_cache_remain_valid(tmp_path, fake_codex, monkeypatch):
    from pipeline.procbench import reconcile_evidence as extraction
    from test_compile_visit_durations import inputs
    evidence, _, _, documents, _ = inputs()
    monkeypatch.setattr(extraction, 'cli_version', lambda: 'fake-codex/1')
    fake_codex.push(raw='{invalid JSON')
    fake_codex.push(evidence)
    out = tmp_path/'extraction'
    answer = extraction.interpret(documents, evidence['program_id'], out, model='test-model')
    assert answer == evidence and len(fake_codex.calls) == 2
    assert 'previous output failed validation' in fake_codex.calls[1]['prompt']
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['status'] == 'completed' and len(manifest['validation_repairs']) == 1
    assert manifest['provenance']['source_sha256']['prompts/reconcile_evidence_v2.md']
    assert extraction.interpret(documents, evidence['program_id'], out, model='test-model') == answer
    assert len(fake_codex.calls) == 2
    with pytest.raises(ValueError, match='Cache differs'):
        extraction.interpret(documents, evidence['program_id'], out, model='different-model')
    write(out/'evidence.json', dict(evidence, program_id='changed'))
    with pytest.raises(ValueError, match='Cached evidence changed'):
        extraction.interpret(documents, evidence['program_id'], out, model='test-model')


def test_baseline_completes_common_manifest_without_changing_input_scope(tmp_path, fake_codex):
    from pipeline.procbench import evidence_baseline
    from test_compile_visit_durations import inputs
    evidence, _, _, _, _ = inputs()
    answer = dict(programs=[dict(program_id=evidence['program_id'], median_days=10., p90_days=None,
        median_lower90_days=5., median_upper90_days=20., evidence_ids=['m1'], reasoning='fixture')], caveats=[])
    fake_codex.push(answer)
    evidence_path, out = tmp_path/'evidence.json', tmp_path/'baseline'
    write(evidence_path, evidence)
    evidence_baseline.main(['--evidence', str(evidence_path), '--out', str(out), '--repeats', '1'])
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['status'] == 'completed'
    assert manifest['input_sha256'] == {str(evidence_path): digest(evidence_path.read_bytes())}
    assert manifest['hidden_truth_provided'] is False and manifest['bayesian_predictions_provided'] is False
    assert json.loads((out/'estimates.json').read_text()) == [answer]


@pytest.mark.parametrize('observed_only', [False, True])
def test_v6_fit_extend_diagnose_roundtrip_preserves_target_and_provenance(tmp_path, visit_data, monkeypatch, observed_only):
    from concurrent.futures import Future
    from pipeline.procbench import run_visit_hierarchy, extend_visit_hierarchy
    from pipeline.procbench.compare_evidence_runs import input_hashes

    class ImmediatePool:
        # Exercise real worker, sampler and artifact paths without subprocess startup.
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def submit(self, fn, *args, **kwargs):
            future = Future()
            future.set_result(fn(*args, **kwargs))
            return future

    monkeypatch.setattr(run_visit_hierarchy, 'ProcessPoolExecutor', ImmediatePool)
    monkeypatch.setattr(extend_visit_hierarchy, 'ProcessPoolExecutor', ImmediatePool)
    path, fit, extension, diagnostic = (tmp_path/name for name in ('data.json', 'fit', 'extension', 'diagnostic'))
    write(path, visit_data)
    run_visit_hierarchy.main(['--data', str(path), '--out', str(fit), '--chains', '1',
        '--warmup', '0', '--draws', '8', '--workers', '1', '--population-size', '16']
        + (['--observed-channels-only'] if observed_only else []))
    fitted = json.loads((fit/'manifest.json').read_text())
    assert fitted['status'] == 'completed' and fitted['seconds'] >= 0
    assert fitted['provenance']['config'] == fitted['config']
    assert fitted['config']['modeled_channels'] == (
        ['elapsed', 'agency_hours'] if observed_only else ['elapsed', 'payer_hours', 'agency_hours'])
    assert not json.loads((fit/'posterior.json').read_text())['posterior_converged']
    extend_visit_hierarchy.main(['--run', str(fit), '--out', str(extension),
                                '--extra-draws', '8', '--workers', '1', '--seed', '1234'])
    extended = json.loads((extension/'manifest.json').read_text())
    assert extended['status'] == 'completed' and extended['config']['draws'] == 16
    assert extended['provenance']['seeds']['seed'] == 1234
    assert input_hashes(extended) == input_hashes(fitted)
    with np.load(fit/'draws.npz') as original, np.load(extension/'draws.npz') as continued:
        np.testing.assert_array_equal(original['z'], continued['z'][:, :8])
    run_visit_hierarchy.main(['--diagnose-run', str(extension), '--out', str(diagnostic)])
    diagnostics = json.loads((diagnostic/'manifest.json').read_text())
    assert diagnostics['status'] == 'completed' and diagnostics['max_likelihood_difference'] < 1e-8
    assert diagnostics['provenance']['operation'] == 'v6.diagnose_saved_draws'


@pytest.mark.parametrize('observed_only', [False, True])
def test_v6_preflight_reports_coverage_without_sampling(tmp_path, visit_data, monkeypatch, observed_only):
    from pipeline.procbench import run_visit_hierarchy

    def forbidden(*args, **kwargs):
        raise AssertionError('A preflight must not sample or launch chains')

    monkeypatch.setattr(run_visit_hierarchy, 'ProcessPoolExecutor', forbidden)
    monkeypatch.setattr(run_visit_hierarchy.VisitHierarchy, 'sample', forbidden)
    path, out = tmp_path/'input.json', tmp_path/'preflight'
    write(path, visit_data)
    run_visit_hierarchy.main(['--data', str(path), '--out', str(out), '--preflight',
        '--chains', '1', '--draws', '8', '--population-size', '16']
        + (['--observed-channels-only'] if observed_only else []))
    report = json.loads((out/'preflight.json').read_text())
    assert report['sampling_performed'] is False
    assert report['observation_rows'] == report['rows_with_modeled_operators'] == 4
    assert report['count_observations'] == 1
    assert report['direct_resource_observations'] == dict(elapsed=2, payer_hours=0, agency_hours=1)
    assert report['channels_without_direct_observations'] == ['payer_hours']
    assert report['omitted_resource_channels'] == (['payer_hours'] if observed_only else [])
    assert report['dimensions'] == sum(report['coordinates_by_block'].values())
    assert len(report['likelihood_probes']) == 3 and report['finite_at_all_probe_points']
    assert not (out/'posterior.json').exists() and not (out/'draws.npz').exists()
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['provenance']['operation'] == 'v6.preflight'
    assert manifest['provenance']['input_sha256'] == {str(path): digest(path.read_bytes())}


def test_current_v6_frozen_source_is_self_contained(tmp_path, visit_data):
    from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
    from pipeline.procbench.audit_visit_likelihood import frozen_reference
    cfg = Config(population_size=16)
    write(tmp_path/'input.json', visit_data)
    out = tmp_path/'run'
    record = RunManifest(out, {'config': asdict(cfg)}, operation='test.freeze',
        inputs=[tmp_path/'input.json'], config=asdict(cfg), seeds={}, hidden_truth_read=False,
        source_root=Path('pipeline/procbench'), sources=['run_visit_hierarchy.py'])
    frozen = frozen_reference(out, record.data)
    assert Path(frozen.__file__).is_relative_to(out)
    reference, current = frozen.VisitHierarchy(visit_data, frozen.Config(**asdict(cfg))), VisitHierarchy(visit_data, cfg)
    for state in np.random.default_rng(919).normal(size=(5, current.layout.size)):
        assert reference.log_likelihood(state, [0]) == current.log_likelihood(state, [0])


def test_codex_transport_preserves_exact_prompt_response_and_isolation(tmp_path, fake_codex):
    fake_codex.push({'ok': True})
    prompt, schema = 'Literal supplied source; do not use tools.', {'type': 'object'}
    raw = codex_runner.run_codex(prompt, schema, tmp_path, stem='attempt_0', model='test-model')
    assert json.loads(raw) == {'ok': True}
    assert (tmp_path/'attempt_0.raw.txt').read_text() == raw
    assert (tmp_path/'attempt_0.prompt.txt').read_text() == prompt
    call = fake_codex.calls[0]
    assert call['schema'] == schema and call['prompt'] == prompt
    assert not Path(call['cwd']).exists()
    status = json.loads((tmp_path/'attempt_0.transport.json').read_text())
    assert status['status'] == 'completed' and status['seconds'] >= 0
    assert status['response_sha256'] == digest(raw)
    with pytest.raises(ValueError, match='previous attempt'):
        codex_runner.run_codex(prompt, schema, tmp_path, stem='attempt_0', model='test-model')
    assert len(fake_codex.calls) == 1


@pytest.mark.parametrize('failure', ['missing', 'nonzero', 'timeout'])
def test_codex_failure_cannot_reuse_an_earlier_response(tmp_path, fake_codex, failure):
    fake_codex.push({'old': True})
    codex_runner.run_codex('first', {}, tmp_path, stem='attempt_0', model='test-model')
    fake_codex.push(raw='partial' if failure != 'missing' else None,
                    returncode=1 if failure == 'nonzero' else 0, timeout=failure == 'timeout')
    with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):
        codex_runner.run_codex('second', {}, tmp_path, stem='attempt_1', model='test-model')
    assert fake_codex.calls[0]['cwd'] != fake_codex.calls[1]['cwd']
    status = json.loads((tmp_path/'attempt_1.transport.json').read_text())
    assert status['status'] == 'failed'
    if failure != 'missing':
        assert (tmp_path/'attempt_1.raw.txt').read_text() == 'partial'
    assert json.loads((tmp_path/'attempt_0.raw.txt').read_text()) == {'old': True}


def test_malformed_json_and_source_only_events_are_retained(tmp_path, fake_codex):
    from pipeline.procbench.audit_visit_hypotheses import check_source_only_events
    fake_codex.push(raw='{bad json')
    raw = codex_runner.run_codex('source', {}, tmp_path, stem='invalid', model='test-model', events=True)
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    check = check_source_only_events(tmp_path/'invalid.events.jsonl')
    assert check['tool_events'] == 0 and check['final_message'] == raw


@pytest.mark.parametrize('name', ['audit_burden_counts', 'audit_case_outcomes', 'audit_clocks',
    'audit_context', 'audit_granularity', 'audit_measurement_semantics', 'audit_preparation_clocks',
    'audit_visit_observations', 'audit_visit_hypotheses', 'evidence_baseline', 'reconcile_evidence'])
def test_all_evidence_callers_use_one_transport(name):
    module = importlib.import_module('pipeline.procbench.' + name)
    assert module.run_codex is codex_runner.run_codex


def test_source_audit_retries_with_unchanged_validation_and_saves_provenance(tmp_path, fake_codex):
    from pipeline.procbench import audit_visit_observations as audit
    from test_compile_visit_durations import inputs
    evidence, visit, _, documents, _ = inputs()
    evidence_path, inputs_path = tmp_path/'evidence.json', tmp_path/'inputs.json'
    write(evidence_path, evidence)
    write(inputs_path, dict(documents=documents))
    invalid = dict(visit, program_id='wrong')
    fake_codex.push(invalid)
    fake_codex.push(visit)
    out = tmp_path/'audit'
    audit.main(['--evidence', str(evidence_path), '--inputs', str(inputs_path), '--out', str(out)])
    assert json.loads((out/'audit.json').read_text()) == visit
    assert len(fake_codex.calls) == 2
    assert 'Program identity changed' in fake_codex.calls[1]['prompt']
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['manifest_version'] == 'procbench-run/1'
    assert manifest['provenance']['input_sha256'][str(inputs_path)] == digest(inputs_path.read_bytes())
    assert manifest['provenance']['hidden_truth_read'] is False
