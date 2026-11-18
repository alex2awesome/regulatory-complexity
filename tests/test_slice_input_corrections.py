"""Offline checks for approved corrections and immutable review provenance."""
from copy import deepcopy
import json
from random import Random

import pytest

from benchmark.synth.generator import local_rules, processes, specs, statutes, world
from benchmark.synth.render import complete_slice as completion
from benchmark.synth.render.correct_slice_inputs import leaf_changes, rewrite_labels


def test_labels_follow_explicit_process_attribution_and_leave_numbers_alone():
    name = 'Attend the mandatory pre-submittal consultation'
    original = dict(name=name, optional=True, p_occurs=0.35, timing=dict(median_days=4.7),
        contamination=[dict(about='C01__S03', value=name),
                       dict(about='C08__S03', value=name)])
    changed = rewrite_labels(original, 'C02__S03')
    assert changed['name'] == 'Attend an optional pre-submittal consultation'
    assert changed['contamination'][0] == original['contamination'][0]
    assert changed['contamination'][1]['value'] == changed['name']
    assert changed['timing'] == original['timing']
    assert changed['p_occurs'] == original['p_occurs'] and changed['optional'] is True
    assert all(isinstance(d['before'], str) for d in leaf_changes(original, changed))


def test_dashboard_publication_uses_cutoff_without_rng_drift():
    w = dict(knobs=dict(as_of='2026-09-15', p_stale=0.25))
    rule = dict(adopted='2024-01-01')
    proc = dict(prior_version=None)
    actual, old = Random(42), Random(42)
    old.randrange(60)  # The prior implementation's date draw.
    assert specs._artifact_date(actual, 'official_stats', w, rule, proc, {}) == ('2026-09-15', False)
    assert actual.getstate() == old.getstate()


def test_optional_label_fix_preserves_every_other_generated_field(monkeypatch):
    changes = 0
    # Seed 43 contains an optional step with the contradictory canonical name;
    # the others exercise unchanged paths and ordinary local-name variation.
    for seed in [0, 1, 2, 3, 43]:
        w = world.build_world('WLABELTEST', seed, dict(
            only_jurisdictions=['J1', 'J3'], only_domains=['sidewalk_vending'],
            neighbor_state=False))
        st = statutes.build_statutes(w)
        with monkeypatch.context() as patch:
            patch.setattr(local_rules, 'optional_consultation_label', lambda name: name)
            old_rules = local_rules.build_local_rules(w, st)
            old_processes = processes.build_processes(w, st, old_rules)
        new_rules = local_rules.build_local_rules(w, st)
        new_processes = processes.build_processes(w, st, new_rules)
        for before, after in ((old_rules, new_rules), (old_processes, new_processes)):
            for change in leaf_changes(before, after):
                assert isinstance(change['before'], str)
                assert local_rules.optional_consultation_label(change['before']) == change['after']
                changes += 1
    assert changes, 'The fixture must exercise the contradictory-label branch'


def minimal_packet():
    return dict(specs=[dict(artifact_id='a', kind='form', jur='C02', reveals=[], links_to=[])],
                render_context={'C02': {'name': 'County'}}, states=['State'],
                brief_text='Verify without invented obligations.', style_guides={'form': 'Style'},
                hidden_elements={'a': []}, artifacts={'a': '---\nartifact_id: a\n---\nbody'})


def test_context_hash_binds_legal_fields_not_batch_neighbors():
    packet = minimal_packet()
    original = completion.context_digests(packet)['a']
    packet['specs'].append(dict(artifact_id='b', kind='news', jur='C99'))
    packet['render_context']['C99'] = {'name': 'Other county'}
    packet['style_guides']['news'] = 'Other style'
    packet['artifacts']['a'] = 'Different bytes are separately artifact-hashed.'
    assert completion.context_digests(packet)['a'] == original
    packet['specs'][0]['legal_truth'] = dict(fee=210)
    assert completion.context_digests(packet)['a'] != original


def test_old_review_context_comes_from_actual_saved_packet(tmp_path):
    stem = tmp_path / 'job'
    packet = minimal_packet()
    (tmp_path / 'job.input.json').write_text(json.dumps(packet))
    record = dict(provenance=str(stem))
    assert completion.reviewed_context(record, 'a') == completion.context_digests(packet)['a']
    assert completion.reviewed_context({}, 'a') is None


def test_review_refuses_spec_changed_during_call(tmp_path, monkeypatch):
    wd, out = tmp_path / 'world', tmp_path / 'run'
    (wd / 'specs').mkdir(parents=True)
    (wd / 'artifacts').mkdir()
    source = minimal_packet()
    spec = wd / 'specs/a.json'
    spec.write_text(json.dumps(source['specs'][0]))
    (wd / 'artifacts/a.md').write_text(source['artifacts']['a'])
    monkeypatch.setattr(completion, 'packet', lambda *args: deepcopy(source))
    def fake_call(prompt, schema, directory, **kwargs):
        spec.write_text(json.dumps(dict(source['specs'][0], changed=True)))
        return json.dumps(dict(artifacts=[dict(artifact_id='a')]))
    monkeypatch.setattr(completion, 'run_codex', fake_call)
    monkeypatch.setattr(completion, 'event_audit', lambda path: [{}])
    with pytest.raises(ValueError, match='Specification/context changed'):
        completion.invoke(wd, out, ['a'], 'verify', 'fake', 'xhigh')
    assert not (out / 'reviews.jsonl').exists()
    assert not (wd / 'verify_log.jsonl').exists()


def repair_review_fixture(tmp_path, monkeypatch):
    wd, out = tmp_path / 'world', tmp_path / 'run'
    wd.mkdir()
    out.mkdir()
    context = completion.context_digests(minimal_packet())['a']
    record = dict(artifact_id='a', artifact_sha256='document', spec_sha256='spec',
                  context_sha256=context, **{'pass': False}, fix='Remove the invented rule.')
    monkeypatch.setattr(completion, 'packet', lambda *args: minimal_packet())
    (out / 'reviews.jsonl').write_text(json.dumps(record) + '\n')
    return wd, out, record


def test_repair_uses_bound_local_review_after_unbound_global_summary(tmp_path, monkeypatch):
    wd, out, record = repair_review_fixture(tmp_path, monkeypatch)
    (wd / 'verify_log.jsonl').write_text('{"artifact_id":"a","pass":false}\n')
    chosen = completion.repair_reviews(wd, out, ['a'], {'a': 'document'}, {'a': 'spec'})
    assert chosen == {'a': record}


@pytest.mark.parametrize('field', ['artifact_sha256', 'spec_sha256', 'context_sha256'])
def test_repair_rejects_stale_review_even_with_actionable_fix(tmp_path, monkeypatch, field):
    wd, out, record = repair_review_fixture(tmp_path, monkeypatch)
    record[field] = 'stale'
    (out / 'reviews.jsonl').write_text(json.dumps(record) + '\n')
    with pytest.raises(ValueError, match='No actionable review bound to current'):
        completion.repair_reviews(wd, out, ['a'], {'a': 'document'}, {'a': 'spec'})


def test_repair_does_not_override_new_current_pass_with_older_failure(tmp_path, monkeypatch):
    wd, out, record = repair_review_fixture(tmp_path, monkeypatch)
    (wd / 'verify_log.jsonl').write_text(json.dumps(dict(record, **{'pass': True})) + '\n')
    with pytest.raises(ValueError, match='Current bound review passes'):
        completion.repair_reviews(wd, out, ['a'], {'a': 'document'}, {'a': 'spec'})


@pytest.mark.parametrize('value', ['2026-09-15', '"2026-09-15"', "'2026-09-15'"])
def test_render_preserves_approved_publication_date(value):
    completion.validate_publication_date('artifact_id: a\ndate: ' + value,
                                        dict(artifact_id='a', date='2026-09-15'))


@pytest.mark.parametrize('header', [
    'artifact_id: a',
    'artifact_id: a\ndate: 2026-09-16',
    'artifact_id: a\ndate: 2026-09-15\ndate: 2026-09-16',
])
def test_prose_repair_cannot_authorize_new_publication_date(header):
    with pytest.raises(ValueError, match='Publication date must match'):
        completion.validate_publication_date(header, dict(artifact_id='a', date='2026-09-15'))


def test_source_index_includes_only_explicit_membership_and_checks_hashes(tmp_path):
    from pipeline.procbench.infra.manifest import digest
    from pipeline.procbench.reconcile_evidence import public_documents
    ids = ['C02__S03__page', 'C02__departments_index', 'S03__statute_text', 'C02__statute_text']
    documents = []
    for ident in ids:
        text = 'Public document ' + ident
        (tmp_path / (ident + '.md')).write_text(text)
        documents.append(dict(document_id=ident, sha256=digest(text.encode())))
    index = tmp_path / 'index.json'
    index.write_text(json.dumps(dict(schema_version='artifact-only-index/1',
        documents=documents, programs={'C02__S03': ids[:3]})))
    selected = public_documents(tmp_path, 'C02__S03', index)
    assert [d['id'] for d in selected] == ids[:3]
    with pytest.raises(ValueError, match='explicit membership'):
        public_documents(tmp_path, 'C02__S12', index)
    (tmp_path / (ids[1] + '.md')).write_text('Changed after the freeze')
    with pytest.raises(ValueError, match='hash mismatch'):
        public_documents(tmp_path, 'C02__S03', index)


def test_source_index_rejects_path_traversal(tmp_path):
    from pipeline.procbench.reconcile_evidence import public_documents
    index = tmp_path / 'index.json'
    index.write_text(json.dumps([{'id': '../truth/process'}]))
    with pytest.raises(ValueError, match='plain filenames'):
        public_documents(tmp_path, 'C02__S03', index)


def test_export_does_not_upgrade_unbound_legacy_verdicts(tmp_path):
    with pytest.raises(ValueError, match='current bytes/context'):
        completion.export(tmp_path, tmp_path, {},
            dict(slice_complete_by_counts=True, all_verdicts_hash_bound=False))
    assert not (tmp_path / 'source_only').exists()


def test_export_cannot_hide_upstream_conflicts_behind_passing_reviews(tmp_path):
    with pytest.raises(ValueError, match='upstream consistency/scope'):
        completion.export(tmp_path, tmp_path, {}, dict(
            slice_complete_by_counts=True, all_verdicts_hash_bound=True,
            release_holds=[dict(id='contradictory_appeal_body', status='open')]))
    assert not (tmp_path / 'source_only').exists()


@pytest.mark.parametrize('verdict', [True, False])
def test_count_gate_is_selected_lane_not_global_backlog_or_pass_rate(tmp_path, monkeypatch, verdict):
    from benchmark.synth.render import status
    (tmp_path / 'artifacts').mkdir()
    text = '---\nartifact_id: selected\n---\n' + 'Public text. ' * 40
    (tmp_path / 'artifacts/selected.md').write_text(text)
    (tmp_path / 'artifacts/unrelated.md').write_text(text.replace('selected', 'unrelated'))
    (tmp_path / 'render_selection.txt').write_text('selected\n')
    (tmp_path / 'verify_log.jsonl').write_text(json.dumps(
        {'artifact_id': 'selected', 'pass': verdict}) + '\n')
    monkeypatch.setattr(status, '_sample', lambda wd: (3, False))
    observed = status.observe(tmp_path)
    assert observed['complete_by_counts'] is True
    assert observed['all_rendered_have_verdicts'] is False
    assert observed['artifacts_unverified'] == 1
    assert observed['selected_counts']['unverified'] == 0
    assert observed['selected_counts']['failed_verification'] == int(not verdict)


@pytest.mark.parametrize('selected', ['', 'missing\n'])
def test_count_gate_rejects_empty_selection_or_missing_selected_artifacts(tmp_path, monkeypatch, selected):
    from benchmark.synth.render import status
    (tmp_path / 'render_selection.txt').write_text(selected)
    (tmp_path / 'verify_log.jsonl').write_text('{"artifact_id":"missing","pass":true}\n')
    monkeypatch.setattr(status, '_sample', lambda wd: (1, False))
    observed = status.observe(tmp_path)
    assert observed['complete_by_counts'] is False
    assert observed['selected_counts']['verified'] == 0
