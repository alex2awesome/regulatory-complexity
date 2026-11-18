"""Declared, hash-bound same-estimand source comparisons; no bias estimation.

This is a conservative design screen for ordinary elapsed population summaries.
It does not certify semantic reviews, infer source types, convert calendars,
equate individual cases with population statistics, or modify a likelihood.
The rank calculation concerns block locations plus reference-type contrasts,
NOT the full V6 hierarchy, document effects, selection, or reporting variance.
"""
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import re

import numpy as np


VERSION = 'source-comparison-review/1'
ELAPSED_BASES = {'single_visit_cycle', 'sum_visit_cycles',
                 'first_to_last_activity_span', 'whole_case_clock',
                 'wait_elapsed', 'service_elapsed'}
ESTIMAND_KEYS = {'program_id', 'jurisdiction_id', 'policy_era', 'window_start',
                 'window_end', 'population_id', 'outcome_condition', 'route_scope',
                 'clock_start', 'clock_end', 'time_unit'}
MEMBER_KEYS = {'observation_id', 'observation_sha256', 'source_type',
               'document_id', 'lineage_id', 'estimand', 'ascertainment'}
UNRESOLVED = {'unknown', 'unspecified', 'unresolved', 'tbd', 'not_reviewed'}


def comparison_digest(value):
    """Canonical JSON binding, including routes, provenance and report values."""
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{where}: unexpected or missing fields')


def _name(value, where):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f'{where}: require an explicit nonempty string')


def _hash(value, where):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError(f'{where}: require a SHA-256 binding')


def source_comparison_report(data):
    """Validate an optional review, then report conservative contrast support.

    Review artifact hashes are provenance declarations, not proof that a human
    or LLM performed a correct review. A member's estimand and ascertainment
    must each be explicitly reviewed. Different declarations stay held instead
    of being pooled. Shared/copy lineages cannot create independent support.
    Unmodeled/mixed operators and individual or subjective-range reports need
    a richer joint comparison model and are not used in this narrow rank screen.
    """
    total_rows = sum(len(p.get('observations', [])) for p in data['programs'])
    report = dict(schema_version='source-comparison-support/1',
        status='not_declared', blocks=[], reviewed_observation_rows=0,
        ordinary_observation_rows=total_rows, unreviewed_observation_rows=total_rows,
        contrast_candidate_blocks=0, bias_identification_established=False,
        likelihood_changed=False, design=None,
        limitations=[
            'Declared semantic review and lineage, not independently certified source truth.',
            'Rank is for additive block locations/type contrasts only; not the full hierarchy.',
            'No amount, interval width, source reputation or fitted result selects a comparison.',
            'Individual cases, typical ranges and exact cohorts need their own joint comparison design.',
            'Reference zero is a convention, not evidence of unbiased administrative data.',
            'Replication, reporting precision, selection, document effects and transport remain separate gates.'])
    review = data.get('source_comparisons')
    if review is None:
        return report
    _keys(review, {'schema_version', 'reference_type', 'blocks'}, 'source comparisons')
    if review['schema_version'] != VERSION:
        raise ValueError('Unsupported source comparison review version')
    _name(review['reference_type'], 'reference_type')
    if not isinstance(review['blocks'], list):
        raise ValueError('Source comparison blocks must be a list')
    programs = {p['id']: p for p in data['programs']}
    if len(programs) != len(data['programs']):
        raise ValueError('Repeated program identity in comparison input')
    seen_blocks, seen_rows, family_types, document_types = set(), set(), {}, {}
    lineages, prepared = defaultdict(set), []
    for block in review['blocks']:
        _keys(block, {'id', 'program_id', 'program_sha256', 'reviewer',
                      'review_artifact_sha256', 'members'}, 'comparison block')
        for key in ('id', 'program_id', 'reviewer'):
            _name(block[key], key)
        if block['id'] in seen_blocks:
            raise ValueError('Repeated comparison block identity')
        seen_blocks.add(block['id'])
        for key in ('program_sha256', 'review_artifact_sha256'):
            _hash(block[key], key)
        p = programs.get(block['program_id'])
        if p is None or comparison_digest(p) != block['program_sha256']:
            raise ValueError('Source comparison program binding is stale or missing')
        observations = {o['id']: o for o in p.get('observations', [])}
        if len(observations) != len(p.get('observations', [])):
            raise ValueError('Repeated observation identity in comparison input')
        if not isinstance(block['members'], list) or not block['members']:
            raise ValueError('Comparison blocks need observation members')
        signatures, scopes, reasons, types = [], [], set(), set()
        for member in block['members']:
            _keys(member, MEMBER_KEYS, 'comparison member')
            for key in MEMBER_KEYS - {'estimand', 'observation_sha256'}:
                _name(member[key], key)
            _hash(member['observation_sha256'], 'observation_sha256')
            key = (p['id'], member['observation_id'])
            if key in seen_rows:
                raise ValueError('An observation cannot supply repeated comparison evidence')
            seen_rows.add(key)
            o = observations.get(member['observation_id'])
            if o is None or comparison_digest(o) != member['observation_sha256']:
                raise ValueError('Source comparison observation binding is stale or missing')
            e = member['estimand']
            _keys(e, ESTIMAND_KEYS, 'member estimand')
            for key in ESTIMAND_KEYS:
                _name(e[key], 'estimand.' + key)
            if any(value.lower() in UNRESOLVED for value in
                   [*e.values(), member['ascertainment'], member['source_type']]):
                reasons.add('unresolved_review_scope_or_source_type')
            if e['program_id'] != p['id']:
                raise ValueError('Comparison estimand uses a different program')
            if not all(re.fullmatch(r'\d{4}-\d{2}-\d{2}', e[k])
                       for k in ('window_start', 'window_end')):
                raise ValueError('Comparison window requires YYYY-MM-DD ISO dates')
            try:
                start, end = date.fromisoformat(e['window_start']), date.fromisoformat(e['window_end'])
            except ValueError as error:
                raise ValueError('Comparison window requires ISO dates') from error
            if start > end:
                raise ValueError('Comparison window is reversed')
            unit = o.get('time_unit', p.get('time_unit', data.get('elapsed_time_unit', 'calendar_days')))
            if e['time_unit'] != unit:
                raise ValueError('Comparison calendar differs from observation; no implicit conversion')
            for mapping, identity in ((family_types, o['source_family']),
                                      (document_types, member['document_id'])):
                previous = mapping.setdefault(identity, member['source_type'])
                if previous != member['source_type']:
                    raise ValueError('Conflicting source-type assignments')
            lineages[member['lineage_id']].add(block['id'])
            types.add(member['source_type'])
            scopes.append(comparison_digest(dict(estimand=e, ascertainment=member['ascertainment'])))
            if o.get('case_id') is not None or o.get('statistic') not in {'median', 'mean', 'p90'}:
                reasons.add('requires_joint_case_range_or_other_statistic_comparison')
            if o.get('sample_size') is not None:
                reasons.add('requires_finite_cohort_comparison')
            if o.get('sampling', 'unselected') != 'unselected':
                reasons.add('requires_joint_selection_comparison')
            ops, weights = o.get('operators', []), o.get('operator_weights', [])
            if (len(ops) != 1 or weights != [1.] or ops[0].get('basis') not in ELAPSED_BASES):
                reasons.add('requires_unambiguous_elapsed_operator')
            signatures.append(comparison_digest({k: o.get(k) for k in
                ('statistic', 'operators', 'operator_weights', 'population_condition', 'population_path_scope')}))
        if len(set(scopes)) != 1:
            reasons.add('different_reviewed_estimands_or_ascertainment')
        if len(set(signatures)) != 1:
            reasons.add('different_statistics_operators_or_conditioned_populations')
        if len(types) < 2:
            reasons.add('only_one_source_type')
        own_lineages = [m['lineage_id'] for m in block['members']]
        if len(set(own_lineages)) != len(own_lineages):
            reasons.add('shared_or_copied_evidence_lineage')
        prepared.append((block, types, reasons))
    usable = []
    for block, types, reasons in prepared:
        if any(len(lineages[m['lineage_id']]) > 1 for m in block['members']):
            reasons.add('lineage_shared_across_comparison_blocks')
        eligible = not reasons
        report['blocks'].append(dict(id=block['id'], program_id=block['program_id'],
            observation_rows=len(block['members']), source_types=sorted(types),
            contrast_design_candidate=eligible, holds=sorted(reasons)))
        if eligible:
            usable.append((block, types))
    reference = review['reference_type']
    all_types = sorted({t for _, types in usable for t in types} | {reference})
    nonreference = [t for t in all_types if t != reference]
    # Replicate reports within one block/type do not add rank or independent
    # contrast replication. Every block location is a separate nuisance column.
    rows, type_documents = [], defaultdict(set)
    document_blocks = defaultdict(set)
    graph = {t: set() for t in all_types}
    for index, (_, types) in enumerate(usable):
        for t in sorted(types):
            rows.append([float(j == index) for j in range(len(usable))] +
                        [float(t == other) for other in nonreference])
            graph[t].update(types - {t})
    for block, _ in usable:
        for member in block['members']:
            type_documents[member['source_type']].add(member['document_id'])
            document_blocks[member['document_id']].add(block['id'])
    reached, pending = {reference}, [reference]
    while pending:
        for t in graph[pending.pop()] - reached:
            reached.add(t)
            pending.append(t)
    rank = int(np.linalg.matrix_rank(np.asarray(rows))) if rows else 0
    columns = len(usable) + len(nonreference)
    report.update(status='declared_review_screened',
        reviewed_observation_rows=len(seen_rows), contrast_candidate_blocks=len(usable),
        unreviewed_observation_rows=total_rows-len(seen_rows),
        design=dict(reference_type=reference, source_types=all_types,
            source_type_blocks=dict(sorted(Counter(t for _, ts in usable for t in ts).items())),
            distinct_documents_by_type={t: len(ds) for t, ds in sorted(type_documents.items())},
            documents_spanning_blocks={d: sorted(bs) for d, bs in sorted(document_blocks.items())
                                     if len(bs) > 1},
            document_dependence_adjusted=False,
            types_with_less_than_two_documents=sorted(t for t, ds in type_documents.items() if len(ds) < 2),
            block_type_cells=len(rows), columns=columns, rank=rank,
            nullity=columns-rank, connected_to_reference=sorted(reached - {reference}),
            disconnected_types=sorted(set(all_types)-reached),
            full_additive_contrast_rank=bool(nonreference and rank == columns)))
    return report
