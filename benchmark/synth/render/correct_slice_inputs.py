#!/usr/bin/env python3
"""Versioned, explicitly approved S12/S03 metadata/label corrections.

Construction utility only: reads development truth, never an extractor input.
Stage is non-mutating for the world; apply requires the completion worker lock.
It does not regenerate a world, redraw cases, change numeric parameters or mark
documents passing. The original manifest and every changed file are retained.
"""
import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, latest, lock, read, save, sha, stamp)

MODELS = {county + '__S03' for county in
          ('C02', 'C08', 'C11', 'C23', 'C33', 'C36', 'C37', 'C38', 'C42', 'C45', 'C52', 'C58')}
DATES = {
    'C02__S03__official_stats': '2026-07-24',
    'C08__S03__official_stats': '2026-07-31',
    'C22__S12__official_stats': '2026-07-23',
    'C25__S03__official_stats': '2026-07-25',
    'C38__S03__official_stats': '2026-08-25',
    'C46__S03__official_stats': '2026-08-11',
    'C50__S03__official_stats': '2026-08-07',
    'C55__S12__official_stats': '2026-08-13',
    'C57__S03__official_stats': '2026-09-08',
}
CUTOFF = '2026-09-15'
LABEL = re.compile(r'\bthe mandatory pre-submittal consultation\b', re.I)


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def rewrite_labels(value, model):
    """Explicitly attributed contamination follows its own model, not its host."""
    if isinstance(value, dict):
        context = value.get('about', model)
        ref = value.get('ref')
        if isinstance(ref, str) and ':' in ref:
            context = ref.split(':', 1)[0]
        return {key: rewrite_labels(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_labels(item, model) for item in value]
    if isinstance(value, str) and model in MODELS:
        return LABEL.sub('an optional pre-submittal consultation', value)
    return value


def leaf_changes(before, after, path=()):
    if type(before) is not type(after):
        raise ValueError('Correction changed a value type: ' + repr(path))
    if isinstance(before, dict):
        if before.keys() != after.keys():
            raise ValueError('Correction changed object keys')
        return [d for k in before for d in leaf_changes(before[k], after[k], path + (k,))]
    if isinstance(before, list):
        if len(before) != len(after):
            raise ValueError('Correction changed array size')
        return [d for i, (a, b) in enumerate(zip(before, after))
                for d in leaf_changes(a, b, path + (i,))]
    return [] if before == after else [dict(path=list(path), before=before, after=after)]


def target(wd, relative):
    result = wd / relative
    if result.resolve().parent != wd.resolve() and wd.resolve() not in result.resolve().parents:
        raise ValueError('Correction target escapes world directory')
    return result


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)


def stage(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing correction stage; choose a new directory')
    manifest = current_manifest(out)
    changes, labeled_specs = {}, set()
    for mid in sorted(MODELS):
        rule = read(wd / 'truth/local_rules' / (mid + '.json'))
        proc = read(wd / 'truth/processes' / (mid + '.json'))
        elements = [e for e in rule['added_elements'] if LABEL.search(e['name'])]
        if len(elements) != 1 or elements[0]['mandatory'] is not False:
            raise ValueError('Approved optional element no longer matches: ' + mid)
        activity = [a for a in proc['activities'] if a['element_ref'] == elements[0]['element_id']]
        if len(activity) != 1 or activity[0]['optional'] is not True:
            raise ValueError('Process optionality disagrees: ' + mid)
    for folder in ('truth/local_rules', 'truth/processes', 'verify_context', 'specs'):
        for path in sorted((wd / folder).glob('*.json')):
            before = read(path)
            model = (str(before.get('jur')) + '__' + str(before.get('stat_id'))
                     if folder == 'specs' else path.stem)
            # Specs outside the twelve models may contain explicitly attributed
            # references to one of them. Do not rewrite unrelated occurrences.
            after = rewrite_labels(before, model)
            if folder == 'specs' and path.stem in DATES:
                if before['date'] != DATES[path.stem]:
                    raise ValueError('Publication date changed before staging: ' + path.stem)
                cutoffs = [r['count_observation']['as_of'] for r in before['reveals']
                           if r.get('count_observation')]
                if not cutoffs or set(cutoffs) != {CUTOFF}:
                    raise ValueError('Unexpected observation cutoff: ' + path.stem)
                after['date'] = CUTOFF
            differences = leaf_changes(before, after)
            if not differences:
                continue
            for item in differences:
                is_date = folder == 'specs' and path.stem in DATES and item['path'] == ['date']
                if not is_date and (not isinstance(item['before'], str)
                        or LABEL.sub('an optional pre-submittal consultation', item['before']) != item['after']):
                    raise ValueError('Non-label/non-date mutation attempted')
            if folder == 'specs' and any(d['path'] != ['date'] for d in differences):
                labeled_specs.add(path.stem)
            relative = str(path.relative_to(wd))
            changes[relative] = (path.read_bytes(), (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode(), differences)
    for aid, old in DATES.items():
        path = wd / 'artifacts' / (aid + '.md')
        before = path.read_bytes()
        old_date, new_date = date.fromisoformat(old), date.fromisoformat(CUTOFF)
        old_label = f'{old_date:%B} {old_date.day}, {old_date.year}'
        new_label = f'{new_date:%B} {new_date.day}, {new_date.year}'
        text = before.decode()
        if text.count('date: ' + old) != 1:
            raise ValueError('Unexpected publication front matter: ' + aid)
        after = text.replace('date: ' + old, 'date: ' + CUTOFF).replace(old_label, new_label).encode()
        changes[str(path.relative_to(wd))] = (before, after, [dict(publication_date_before=old, publication_date_after=CUTOFF)])
    # Legal packets change even if their raw specification never named the step.
    impacted = set(labeled_specs)
    for path in (wd / 'specs').glob('*.json'):
        spec = read(path)
        mid = str(spec.get('jur')) + '__' + str(spec.get('stat_id'))
        if mid in MODELS and spec['kind'] in {'ordinance', 'fee_resolution', 'bill_analysis'}:
            impacted.add(path.stem)
    rendered_impacted = sorted(a for a in impacted if (wd / 'artifacts' / (a + '.md')).exists())
    fresh = sorted(set(rendered_impacted) | set(DATES) | (impacted & set(manifest['artifacts'])))
    protected_paths = [wd / 'world.json'] + sorted((wd / 'truth/log').glob('*'))
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths if p.is_file()}
    records = []
    for relative, (before, after, differences) in changes.items():
        write_new(dest / 'before' / relative, before)
        write_new(dest / 'after' / relative, after)
        records.append(dict(path=relative, before_sha256=sha(before), after_sha256=sha(after), changes=differences))
    for aid in rendered_impacted:
        path = Path('artifacts') / (aid + '.md')
        if not (dest / 'before' / path).exists():
            write_new(dest / 'before' / path, (wd / path).read_bytes())
    result = dict(schema_version='approved-corpus-correction/1', staged_utc=stamp(),
        world=wd.name, changes=records, protected_sha256=protected,
        optional_models=sorted(MODELS), date_artifacts=sorted(DATES),
        requires_rerender_ids=rendered_impacted, requires_fresh_review_ids=fresh,
        supplemental_correction_ids=sorted(set(fresh) - set(manifest['artifacts'])),
        unrendered_changed_spec_ids=sorted(impacted - set(rendered_impacted)),
        approval='Alex approved nine publication dates to data cutoff and twelve optional-consultation descriptions; preserve originals, figures, timings and case draws.',
        numerical_or_boolean_process_parameters_changed=False, sampled_cases_resimulated=False,
        parent_manifest_sha256=sha(json.dumps(manifest, sort_keys=True)))
    save(dest / 'plan.json', result)
    return result


def apply(wd, out, dest):
    plan = read(dest / 'plan.json')
    if (dest / 'applied.json').exists():
        raise ValueError('Correction already applied; preserve its receipt')
    with lock(out):
        manifest = current_manifest(out)
        if sha(json.dumps(manifest, sort_keys=True)) != plan['parent_manifest_sha256']:
            raise ValueError('Manifest changed after staging')
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected world/case file changed: ' + relative)
        for record in plan['changes']:
            if file_sha(target(wd, record['path'])) != record['before_sha256']:
                raise ValueError('Correction target changed after staging: ' + record['path'])
            if file_sha(dest / 'after' / record['path']) != record['after_sha256']:
                raise ValueError('Staged correction changed')
        for aid in plan['requires_rerender_ids']:
            relative = 'artifacts/' + aid + '.md'
            if file_sha(target(wd, relative)) != file_sha(dest / 'before' / relative):
                raise ValueError('Affected artifact changed after staging: ' + aid)
        revision_number = len(list((out / 'manifest_revisions').glob('*.json'))) + 1
        revision = f'{revision_number:04d}'
        revised = deepcopy(manifest)
        revised.update(correction_revision=revision, correction_plan=str(dest / 'plan.json'),
            requires_rerender_ids=plan['requires_rerender_ids'],
            requires_fresh_review_ids=plan['requires_fresh_review_ids'],
            supplemental_correction_ids=plan['supplemental_correction_ids'])
        verdicts = latest(wd / 'verify_log.jsonl')
        for aid in plan['supplemental_correction_ids']:
            revised['artifacts'][aid] = dict(
                spec_sha256=file_sha(wd / 'specs' / (aid + '.json')),
                artifact_sha256=file_sha(wd / 'artifacts' / (aid + '.md')),
                existing_verdict=verdicts.get(aid))
        for record in plan['changes']:
            path = target(wd, record['path'])
            # A bounded mechanical rewrite; original bytes already archived.
            path.write_bytes((dest / 'after' / record['path']).read_bytes())
            if record['path'].startswith('specs/') and path.stem in revised['artifacts']:
                revised['artifacts'][path.stem]['spec_sha256'] = record['after_sha256']
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected file changed during apply: ' + relative)
        save(out / 'manifest_revisions' / (revision + '.json'), revised)
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            plan_sha256=file_sha(dest / 'plan.json'), changed_files=len(plan['changes']),
            protected_files_unchanged=len(plan['protected_sha256']),
            numerical_or_boolean_process_parameters_changed=False,
            rerender_pending=len(plan['requires_rerender_ids']),
            fresh_reviews_required=len(plan['requires_fresh_review_ids']))
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_input_correction', **receipt,
            correction_archive=str(dest), no_cases_resimulated=True))
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['stage', 'apply'])
    parser.add_argument('--world', default='W2_DEV_001')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--correction', type=Path, required=True)
    args = parser.parse_args()
    wd = ROOT / 'benchmark/synth/worlds' / args.world
    result = (stage if args.action == 'stage' else apply)(wd, args.out, args.correction)
    print(json.dumps({k: v for k, v in result.items() if k not in {'changes', 'protected_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
