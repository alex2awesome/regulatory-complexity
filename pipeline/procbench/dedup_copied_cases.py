#!/usr/bin/env python3
"""Build a sensitivity variant of a V6 input that treats a copied case as one case.

WHY. `audit_copied_claims.py` finds pairs of cases that agree on several
distinctive quantities at once -- one source restating another's figures as its
own case. Where both sides reach an informative row, the same evidence enters
the likelihood twice, and no contract field can currently declare the
dependency: a report group may not span two `case_id`s, by design.

The honest response is not to pick a number and hope. It is to fit twice: once
with every case the ledger supplies, and once treating each copied pair as the
single case it probably is, and then to report how far the posterior moved. A
conclusion that survives both is not resting on the duplication. One that does
not survive was never a measurement.

This builds the second input. For each strong, double-counted cluster it drops
every observation belonging to ONE member, because a copy is not a case with
some bad rows -- it is not an independent case at all. Nothing is edited: the
dropped rows are listed in the record, and the ledger and compilation are
untouched.

WHICH CASES ARE DROPPED follows one rule: the FEWEST cases whose removal leaves
no double-counted pair. Duplication is a graph over cases, and dropping a case
removes every pair it belongs to, so this is a vertex cover, computed greedily by
repeatedly dropping the case in the most unresolved pairs. That matters where one
source is the copy in several pairs: dropping that hub once resolves all of them,
whereas dropping its partners one by one discards several cases to save one and
throws away evidence the duplication never touched.

Ties are broken toward keeping evidence -- fewer informative rows dropped first,
then case id -- so the choice is deterministic and reproducible rather than
tuned. Pass `--keep` to force a case to survive. Dropping the other side of a
pair instead is itself a sensitivity worth running, and `--report-only` lists the
choices without writing anything.

    python3 pipeline/procbench/dedup_copied_cases.py --data <bridged>/data.json \\
        --audit <bridge>/copied_claim_audit.json --program C29__S12 --out <dir>
"""
from __future__ import annotations

import argparse
import json
import pathlib

from .infra.manifest import RunManifest, digest, write


def informative_rows(program):
    out = set()
    for row in program.get('observations') or []:
        if any(op.get('basis') != 'unmodeled_duration' for op in (row.get('operators') or [])):
            out.add(row['id'])
    return out


def choose_dropped(cluster, informative):
    """Which side of a single pair to drop: the one carrying less evidence."""
    left, right = cluster['cases']
    counts = {left: len(cluster['left_informative']), right: len(cluster['right_informative'])}
    if counts[left] != counts[right]:
        return min(counts, key=lambda case: (counts[case], case))
    return max(left, right)


def cover(pairs, evidence_count, keep=()):
    """Fewest cases whose removal leaves no pair intact (greedy vertex cover).

    Dropping a case resolves every pair it appears in, so a case that is the copy
    in several pairs should be dropped once instead of taking each partner with it.
    Ties prefer dropping the case with less evidence, then the later id.
    """
    remaining, dropped = [tuple(p) for p in pairs], []
    while remaining:
        degree = {}
        for left, right in remaining:
            for case in (left, right):
                if case not in keep:
                    degree[case] = degree.get(case, 0) + 1
        if not degree:                      # every remaining pair is pinned by --keep
            break
        pick = max(degree, key=lambda case: (degree[case], -evidence_count.get(case, 0), case))
        dropped.append(pick)
        remaining = [p for p in remaining if pick not in p]
    return dropped


def plan(data, audit, program_id, keep=()):
    report = next((r for r in audit['programs'] if r['program_id'] == program_id), None)
    if report is None:
        raise SystemExit('no copied-claim report for %s in the audit' % program_id)
    program = next((p for p in data['programs'] if p['id'] == program_id), None)
    if program is None:
        raise SystemExit('%s is not in this input' % program_id)

    informative = informative_rows(program)
    decisions = []
    double = [c for c in report['strong'] if c['both_sides_informative']]
    for cluster in report['strong']:
        if cluster not in double:
            decisions.append(dict(cases=cluster['cases'], action='kept both',
                                  reason='only one side is informative, so a residual copy '
                                         'cannot reinforce its twin'))

    evidence_count = {}
    for cluster in double:
        left, right = cluster['cases']
        evidence_count[left] = len(cluster['left_informative'])
        evidence_count[right] = len(cluster['right_informative'])
    dropped_cases = set(cover([c['cases'] for c in double], evidence_count, set(keep)))

    for cluster in double:
        hit = [c for c in cluster['cases'] if c in dropped_cases]
        decisions.append(dict(
            cases=cluster['cases'], distinctive_agreements=cluster['distinctive_agreements'],
            action=('dropped ' + hit[0]) if hit else 'UNRESOLVED (pinned by --keep)',
            reason=('both sides informative; the copy is not an independent case' if hit
                    else 'both members pinned by --keep, so the duplication remains')))
    return program, dropped_cases, decisions, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', required=True)
    parser.add_argument('--audit', required=True)
    parser.add_argument('--program', action='append', required=True,
                        help='programme id to deduplicate; repeatable')
    parser.add_argument('--keep', action='append', default=[],
                        help='case id that must be retained, overriding the default choice')
    parser.add_argument('--out')
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args(argv)

    data_path = pathlib.Path(args.data)
    data = json.loads(data_path.read_text())
    audit = json.loads(pathlib.Path(args.audit).read_text())

    record, total_dropped_rows = [], 0
    for program_id in args.program:
        program, dropped_cases, decisions, report = plan(data, audit, program_id, args.keep)
        rows = program.get('observations') or []
        dropped_rows = [r for r in rows if r.get('case_id') in dropped_cases]
        program['observations'] = [r for r in rows if r.get('case_id') not in dropped_cases]
        scope = program.get('case_path_scope') or {}
        program['case_path_scope'] = {k: v for k, v in scope.items() if k not in dropped_cases}
        total_dropped_rows += len(dropped_rows)
        print('%-12s dropped %d cases, %d of %d observation rows'
              % (program_id, len(dropped_cases), len(dropped_rows), len(rows)))
        for decision in decisions:
            print('   %s: %s' % (' vs '.join(decision['cases']), decision['action']))
        record.append(dict(program_id=program_id, dropped_cases=sorted(dropped_cases),
                           dropped_rows=[r['id'] for r in dropped_rows],
                           retained_rows=len(program['observations']),
                           original_rows=len(rows), decisions=decisions))

    if args.report_only or not args.out:
        return 0

    out = pathlib.Path(args.out)
    manifest = RunManifest(out, dict(
        schema_version='copied-case-dedup/1',
        WHAT_THIS_IS=('A sensitivity variant. Each strong double-counted copied pair is '
                      'treated as one case by dropping one member entirely. Compare its '
                      'posterior with the full-input fit; a conclusion that moves was '
                      'resting on duplicated evidence.'),
        source_input=str(data_path), source_input_sha256=digest(data_path.read_bytes()),
        audit=str(args.audit), dropped_observation_rows=total_dropped_rows,
        which_side_dropped=('the fewest cases whose removal leaves no double-counted pair '
                            '(greedy vertex cover); ties prefer dropping less evidence, then '
                            'the later case id, so the choice is deterministic, not tuned'),
        programs=record), operation='v6.dedup_copied_cases',
        inputs=[data_path, pathlib.Path(args.audit)], config={},
        seeds={}, hidden_truth_read=False,
        source_root=pathlib.Path(__file__).parent, sources=['dedup_copied_cases.py'])
    write(out / 'data.json', data)
    write(out / 'dedup_record.json', dict(schema_version='copied-case-dedup/1', programs=record))
    manifest.complete(dropped_observation_rows=total_dropped_rows)
    print('wrote %s' % (out / 'data.json'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
