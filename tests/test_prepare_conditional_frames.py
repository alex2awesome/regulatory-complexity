"""Finite compiler checks; no LLM calls, real-source edits, or model sampling."""
import copy
import hashlib
import json

import pytest

from pipeline.procbench import prepare_conditional_frames as compiler
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy


def fixture(tmp_path, monkeypatch):
    source = tmp_path/'source.md'
    source.write_text('I waited 20 minutes, then the line disconnected.\nStill waiting after 30 minutes.\n')
    code = tmp_path/'compiler.py'
    code.write_text('source-free compiler-path fixture\n')
    monkeypatch.setattr(compiler, '__file__', str(code))
    claims = []
    for index, (kind, lower, upper, quote) in enumerate([
        ('completed_interval', 19.5/1440, 20.5/1440, 'I waited 20 minutes, then the line disconnected.'),
        ('pending_right_censored', 29.5/1440, None, 'Still waiting after 30 minutes.')]):
        claims.append(dict(id=f'obs{index}', registry_label_id=f'label{index}', case_id=f'case{index}',
            observation_kind=kind, lower=lower, upper=upper,
            interpretation='Source-free half-minute coarsening; elapsed time, not active labor.',
            logical_threads=[f'thread{index}'], sources=[dict(path='source.md',
                sha256=hashlib.sha256(source.read_bytes()).hexdigest(), quote_segments=[quote])]))
    spec = dict(schema_version=compiler.SCHEMA, id='contact',
        target='Elapsed time until the reported phone attempt ends, any ending',
        source_family='fixture', eligibility='Two source-free example reports',
        generalization_limit='No population generalization or source calibration',
        elapsed_time_unit='calendar_days',
        coarsening_assumption=dict(kind='assumed_ignorable_within_report_frame',
            rationale='Fixture assumption', sensitivity_plan='Completed-only comparison',
            informative_posting_unmodeled=True),
        claims=claims,
        registry_rows=[dict(registry_label_id=c['registry_label_id'], status='included',
            case_id=c['case_id'], reason=c['interpretation']) for c in claims] + [
            dict(registry_label_id='advice', status='excluded', case_id=None, reason='Prospective advice only')],
        input_bindings=[], conditions=[dict(id='mixed', observation_ids=['obs0','obs1'],
            config_overrides=dict(draws=8, warmup=0, chains=1, population_size=16,
                elapsed_prior_median=30/1440), subset_reason='All two fixture reports'),
            dict(id='completed', observation_ids=['obs0'], config_overrides={},
                subset_reason='Reported attempts with an observed ending only')])
    return spec


def invoke(spec, tmp_path):
    path = tmp_path/'spec.json'
    path.write_text(json.dumps(spec))
    return compiler.prepare(path, tmp_path/'prepared', tmp_path)


def test_builds_consumable_existing_v6_inputs_and_keeps_all_dispositions(tmp_path, monkeypatch):
    spec = fixture(tmp_path, monkeypatch)
    result = invoke(spec, tmp_path)
    assert result['claims'] == 2 and not result['sampling_started']
    out = tmp_path/'prepared'
    data = json.loads((out/'mixed_data.json').read_text())
    config = json.loads((out/'mixed_config.json').read_text())
    model = VisitHierarchy(data, Config(**config))
    assert len(model.programs[0]['cases']) == 2
    assert data['programs'][0]['routes'][0]['operations'][0]['actor_id'] is None
    assert data['conditional_case_frames'][0]['registry_label_denominator'] == 3
    other = json.loads((out/'completed_data.json').read_text())
    assert other['conditional_case_frames'][0]['ledger']['rows'][1]['status'] == 'excluded'
    plan = json.loads((out/'plan.json').read_text())
    assert not plan['automatic_continuation']
    assert '--elapsed-prior-median' in plan['conditions'][0]['argv']
    assert not (out/'fit_mixed').exists()
    manifest = json.loads((out/'manifest.json').read_text())
    for item in manifest['inputs'] + manifest['outputs']:
        assert hashlib.sha256((tmp_path/item['path']).read_bytes()).hexdigest() == item['sha256']
    with pytest.raises(FileExistsError):
        compiler.prepare(tmp_path/'spec.json', out, tmp_path)


def test_v2_compiles_neutral_bound_but_excludes_it_from_completed_only(tmp_path, monkeypatch):
    spec = fixture(tmp_path, monkeypatch)
    spec['schema_version'] = compiler.TERMINAL_NEUTRAL_SCHEMA
    spec['claims'][1]['observation_kind'] = 'terminal_neutral_lower_bound'
    spec['conditions'][0]['observation_set_kind'] = 'explicit_mixed'
    spec['conditions'][1]['observation_set_kind'] = 'completed_only'
    invoke(spec, tmp_path)
    packet = tmp_path/'prepared'
    mixed = json.loads((packet/'mixed_data.json').read_text())
    completed = json.loads((packet/'completed_data.json').read_text())
    assert mixed['conditional_case_frames'][0]['schema_version'] == 'declared-conditional-case-frame/3'
    assert [o['id'] for o in completed['programs'][0]['observations']] == ['obs0']
    plan = json.loads((packet/'plan.json').read_text())
    by_id = {row['id']:row for row in plan['conditions']}
    assert by_id['mixed']['terminal_neutral_cases'] == 1
    assert by_id['mixed']['pending_cases'] == 0
    assert by_id['completed']['terminal_neutral_cases'] == 0


def test_v2_completed_only_rejects_neutral_or_pending_members(tmp_path, monkeypatch):
    spec = fixture(tmp_path, monkeypatch)
    spec['schema_version'] = compiler.TERMINAL_NEUTRAL_SCHEMA
    spec['claims'][1]['observation_kind'] = 'terminal_neutral_lower_bound'
    spec['conditions'][0]['observation_set_kind'] = 'explicit_mixed'
    spec['conditions'][1].update(observation_ids=['obs0','obs1'],
        observation_set_kind='completed_only')
    with pytest.raises(ValueError, match='exactly every completed-status'):
        invoke(spec, tmp_path)


@pytest.mark.parametrize('defect', ['quote', 'hash', 'case', 'registry', 'dropped',
    'config', 'negative', 'pending_point', 'escape', 'fractional_draws'])
def test_rejects_bad_translation_without_creating_output(tmp_path, monkeypatch, defect):
    spec = fixture(tmp_path, monkeypatch)
    if defect == 'quote': spec['claims'][0]['sources'][0]['quote_segments'] = ['invented']
    elif defect == 'hash': spec['claims'][0]['sources'][0]['sha256'] = '0'*64
    elif defect == 'case': spec['claims'][1]['case_id'] = spec['claims'][0]['case_id']
    elif defect == 'registry': spec['registry_rows'][0]['case_id'] = 'wrong'
    elif defect == 'dropped': spec['conditions'][0]['observation_ids'] = ['obs0']
    elif defect == 'config': spec['conditions'][0]['config_overrides']['selection_width'] = 4
    elif defect == 'negative': spec['claims'][0]['lower'] = -1
    elif defect == 'pending_point': spec['claims'][1]['upper'] = spec['claims'][1]['lower']
    elif defect == 'escape': spec['claims'][0]['sources'][0]['path'] = '../source.md'
    else: spec['conditions'][0]['config_overrides']['draws'] = 8.5
    with pytest.raises(ValueError):
        invoke(spec, tmp_path)
    assert not (tmp_path/'prepared').exists()
