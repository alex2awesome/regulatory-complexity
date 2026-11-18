"""Compile reviewed single-clock case records into existing V6 fit packets.

This is a translator, not an extractor, identity resolver, or new model. The
caller supplies the complete candidate ledger, reviewed intervals, case links,
source quotations, and every comparison condition before fitting. Nothing is
automatically dropped, guessed from a department name, or sampled here.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import sys

from .bayes_trace_hierarchy import Config, VisitHierarchy
from .conditional_case_frames import canonical_sha256
from .infra.manifest import write
from .run_visit_hierarchy import SENSITIVITY_FIELDS, preflight_report


SCHEMA = 'reviewed-conditional-frame-input/1'
TERMINAL_NEUTRAL_SCHEMA = 'reviewed-conditional-frame-input/2'
INTEGER_FIELDS = ('chains', 'warmup', 'draws', 'population_size',
                  'cohort_quadrature_size', 'seed')
OVERRIDE_FIELDS = set(SENSITIVITY_FIELDS) | set(INTEGER_FIELDS)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fields(value, required, kind):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError(f'{kind} requires exactly {sorted(required)}')


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Packet and condition IDs need filename-safe names')
    return value


def _text(value, kind):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Nonempty {kind} is required')
    return value


def _binding(item, root):
    _fields(item, {'path', 'sha256'}, 'Source binding')
    relative = Path(item['path'])
    path = (root / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(root):
        raise ValueError('Inputs must be explicit repository-relative paths')
    if _sha(path) != item['sha256']:
        raise ValueError('Changed source binding: ' + str(relative))
    return path


def prepare(spec_path: Path, out: Path, root: Path, *, workers=2):
    root, out, spec_path = root.resolve(), out.resolve(), spec_path.resolve()
    if out.exists():
        raise FileExistsError(out)
    if not out.is_relative_to(root) or not spec_path.is_relative_to(root):
        raise ValueError('Prepared packets and specifications must be inside the repository')
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError('A positive worker count is required')
    spec = json.loads(spec_path.read_text())
    _fields(spec, {'schema_version', 'id', 'target', 'source_family', 'eligibility',
        'generalization_limit', 'elapsed_time_unit', 'coarsening_assumption',
        'registry_rows', 'claims', 'conditions', 'input_bindings'}, 'Reviewed input')
    if spec['schema_version'] not in {SCHEMA, TERMINAL_NEUTRAL_SCHEMA}:
        raise ValueError('Unknown reviewed conditional-frame input schema')
    terminal_neutral_version = spec['schema_version'] == TERMINAL_NEUTRAL_SCHEMA
    _name(spec['id'])
    for field in ('target', 'source_family', 'eligibility', 'generalization_limit'):
        _text(spec[field], field)
    if not isinstance(spec['claims'], list) or not spec['claims']:
        raise ValueError('At least one reviewed case observation is required')
    if not isinstance(spec['conditions'], list) or not spec['conditions']:
        raise ValueError('At least one predeclared condition is required')
    if not isinstance(spec['input_bindings'], list):
        raise ValueError('input_bindings must be an explicit list')
    inputs = {spec_path, Path(__file__).resolve()}
    inputs.update(_binding(item, root) for item in spec['input_bindings'])
    observations, lineage, labels, case_ids, ids = [], [], set(), set(), set()
    for claim in spec['claims']:
        _fields(claim, {'id', 'registry_label_id', 'case_id', 'observation_kind',
            'lower', 'upper', 'interpretation', 'sources', 'logical_threads'}, 'Reviewed claim')
        for field in ('id', 'registry_label_id', 'case_id', 'interpretation'):
            _text(claim[field], field)
        if claim['id'] in ids or claim['case_id'] in case_ids or claim['registry_label_id'] in labels:
            raise ValueError('One distinct observation and representative registry label per case is required')
        ids.add(claim['id']); case_ids.add(claim['case_id']); labels.add(claim['registry_label_id'])
        if (not isinstance(claim['logical_threads'], list) or not claim['logical_threads']
                or any(not isinstance(x, str) or not x for x in claim['logical_threads'])):
            raise ValueError('Every claim needs explicit logical source identities')
        if not isinstance(claim['sources'], list) or not claim['sources']:
            raise ValueError('Every claim needs source-bound quotation support')
        for source in claim['sources']:
            _fields(source, {'path', 'sha256', 'quote_segments'}, 'Claim source')
            path = _binding({key: source[key] for key in ('path', 'sha256')}, root)
            quotes = source['quote_segments']
            if (not isinstance(quotes, list) or not quotes
                    or any(not isinstance(q, str) or not q.strip() for q in quotes)):
                raise ValueError('Every supporting source needs nonempty literal quote segments')
            # Exact source strings may contain CRLF. Universal-newline decoding
            # changes their bytes/character slices and falsely rejects them.
            text = path.read_bytes().decode('utf-8')
            if any(q not in text for q in quotes):
                raise ValueError('Quote is not a literal source slice: ' + str(path))
            inputs.add(path)
        if (claim['observation_kind'] == 'terminal_neutral_lower_bound'
                and not terminal_neutral_version):
            raise ValueError('Terminal-neutral lower bounds require reviewed input schema version2')
        observation = dict(id=claim['id'], case_id=claim['case_id'],
            source_family=spec['source_family'], sampling='census_within_declared_conditional_frame',
            statistic='individual', lower=claim['lower'], upper=claim['upper'],
            time_unit=spec['elapsed_time_unit'], observation_kind=claim['observation_kind'],
            operators=[dict(basis='single_visit_cycle', activity_ids=['reported_phase'])],
            operator_weights=[1.], provenance=dict(clock_id=claim['id'],
                evidence_cell_ids=[claim['registry_label_id']],
                date_resolution_rule=claim['interpretation']))
        observations.append(observation)
        primary = claim['sources'][0]
        lineage.append(dict(observation_id=claim['id'], case_id=claim['case_id'],
            source_claim_id=claim['registry_label_id'], artifact=primary['path'],
            artifact_sha256=primary['sha256'], supporting_sources=claim['sources'],
            logical_threads=claim['logical_threads'], observation_kind=claim['observation_kind'],
            bounds=[claim['lower'], claim['upper']], elapsed_time_unit=spec['elapsed_time_unit'],
            interpretation=claim['interpretation']))
    registry = spec['registry_rows']
    if not isinstance(registry, list) or not registry:
        raise ValueError('A complete candidate registry is required')
    # Validate the complete registry even when a condition uses only a subset.
    included = {row.get('registry_label_id'): row.get('case_id')
                for row in registry if isinstance(row, dict) and row.get('status') == 'included'}
    if included != {c['registry_label_id']: c['case_id'] for c in spec['claims']}:
        raise ValueError('Included registry labels must exactly bind the supplied claims')
    operation = dict(id='reported_phase', actor_id=None, actor_role='unknown',
        task_type='reported_phase', markers=[], payer_work=False, agency_work=False)
    frame_schema = ('declared-conditional-case-frame/3' if terminal_neutral_version
                    else 'declared-conditional-case-frame/2')
    base_frame = dict(schema_version=frame_schema, id=spec['id'],
        target=spec['target'], source_family=spec['source_family'], eligibility=spec['eligibility'],
        generalization_limit=spec['generalization_limit'], registry_label_denominator=len(registry),
        included_case_ids=[c['case_id'] for c in spec['claims']],
        coarsening_assumption=spec['coarsening_assumption'],
        ledger=dict(schema_version='conditional-case-frame-ledger/1', rows=registry))
    base_frame['ledger_sha256'] = canonical_sha256(base_frame['ledger'])
    base_program = dict(id=spec['id'], conditional_frame_id=spec['id'],
        inventory_granularity='aggregate_phases', clock_estimand=spec['target'],
        time_unit=spec['elapsed_time_unit'], observations=observations,
        routes=[dict(id='single', prior_weight=1., operations=[operation],
            blocks=[dict(id='reported_phase', operations=['reported_phase'])])])
    base_data = dict(elapsed_time_unit=spec['elapsed_time_unit'],
        conditional_case_frames=[base_frame], programs=[base_program])
    defaults = dict(modeled_channels=('elapsed',), agency_sd=0., task_sd=0.,
        operation_sd=0., common_case_sd=0., source_sd=0., selection_sd=0.,
        elapsed_time_unit=spec['elapsed_time_unit'], population_size=256)
    VisitHierarchy(base_data, Config(**defaults))
    files = {'claim_dispositions.json': registry, 'model_input_lineage.json': lineage}
    conditions, names, covered = [], set(), set()
    for condition in spec['conditions']:
        condition_fields = {'id', 'observation_ids', 'config_overrides', 'subset_reason'}
        if terminal_neutral_version:
            condition_fields.add('observation_set_kind')
        _fields(condition, condition_fields, 'Condition')
        name = _name(condition['id'])
        if name in names:
            raise ValueError('Condition IDs must be distinct')
        names.add(name)
        subset = condition['observation_ids']
        if (not isinstance(subset, list) or not subset or any(not isinstance(x, str) for x in subset)
                or len(set(subset)) != len(subset) or not set(subset) <= ids):
            raise ValueError('Condition must name a nonempty distinct subset of reviewed observations')
        if terminal_neutral_version:
            selection = condition['observation_set_kind']
            if selection not in {'explicit_mixed', 'completed_only'}:
                raise ValueError('Version2 conditions require explicit_mixed or completed_only observation_set_kind')
            if selection == 'completed_only':
                completed = {claim['id'] for claim in spec['claims'] if
                    claim['observation_kind'] in {'completed_interval', 'completed_lower_bound'}}
                if set(subset) != completed:
                    raise ValueError('completed_only must include exactly every completed-status observation')
        _text(condition['subset_reason'], 'condition subset reason')
        covered.update(subset)
        overrides = condition['config_overrides']
        if not isinstance(overrides, dict) or set(overrides) - OVERRIDE_FIELDS:
            raise ValueError('Unsupported configuration override; no silently ignored CLI fields')
        for field in set(overrides) & set(INTEGER_FIELDS):
            if isinstance(overrides[field], bool) or not isinstance(overrides[field], int):
                raise ValueError('Sampling counts and seeds must be integers')
        cfg = Config(**(defaults | overrides))
        data = copy.deepcopy(base_data)
        frame, program = data['conditional_case_frames'][0], data['programs'][0]
        frame['id'] = program['id'] = program['conditional_frame_id'] = spec['id'] + '_' + name
        program['observations'] = [o for o in observations if o['id'] in subset]
        frame['included_case_ids'] = [o['case_id'] for o in program['observations']]
        frame['eligibility'] += ' Condition: ' + condition['subset_reason']
        for row in frame['ledger']['rows']:
            if row['status'] == 'included' and row['case_id'] not in frame['included_case_ids']:
                row.update(status='excluded', case_id=None,
                    reason=row['reason'] + ' Condition exclusion: ' + condition['subset_reason'])
        frame['ledger_sha256'] = canonical_sha256(frame['ledger'])
        model = VisitHierarchy(data, cfg)
        files[name + '_data.json'] = data
        files[name + '_config.json'] = asdict(cfg)
        files[name + '_preflight.json'] = preflight_report(model)
        argv = [sys.executable, '-m', 'pipeline.procbench.run_visit_hierarchy',
            '--data', str((out / (name + '_data.json')).relative_to(root)),
            '--out', str((out / ('fit_' + name)).relative_to(root)),
            '--observed-channels-only', '--elapsed-time-unit', cfg.elapsed_time_unit,
            '--workers', str(workers)]
        for field in (*SENSITIVITY_FIELDS, *INTEGER_FIELDS):
            argv += ['--' + field.replace('_', '-'), str(getattr(cfg, field))]
        prepared_condition = dict(id=name, config=asdict(cfg), argv=argv,
            cases=len(program['observations']),
            pending_cases=sum(o['observation_kind'] == 'pending_right_censored' for o in program['observations']),
            dimensions=model.layout.size)
        if terminal_neutral_version:
            prepared_condition.update(observation_set_kind=condition['observation_set_kind'],
                terminal_neutral_cases=sum(o['observation_kind'] == 'terminal_neutral_lower_bound'
                                           for o in program['observations']))
        conditions.append(prepared_condition)
    if covered != ids:
        raise ValueError('Every admitted claim must enter at least one predeclared condition')
    # All semantic/schema/source validation precedes creation of the new packet.
    out.mkdir(parents=True)
    for name, value in files.items():
        write(out / name, value)
    for condition in conditions:
        condition['data_sha256'] = _sha(out / (condition['id'] + '_data.json'))
    write(out / 'plan.json', dict(conditions=conditions, automatic_continuation=False))
    outputs = list(files) + ['plan.json']
    prepared_schema = 'prepared-conditional-frame/2' if terminal_neutral_version else 'prepared-conditional-frame/1'
    write(out / 'manifest.json', dict(schema_version=prepared_schema,
        hidden_truth_read=False, truth_access_check='caller declaration, not filesystem enforcement',
        inputs=[dict(path=str(p.relative_to(root)), sha256=_sha(p)) for p in sorted(inputs)],
        outputs=[dict(path=str((out / name).relative_to(root)), sha256=_sha(out / name)) for name in outputs],
        sampling_started=False, qualification='Mechanical translation of supplied reviewed semantics; not source or population certification'))
    return dict(packet=str(out), claims=len(observations), conditions=len(conditions), sampling_started=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(prepare(args.spec, args.out, Path.cwd(), workers=args.workers)))


if __name__ == '__main__':
    main()
