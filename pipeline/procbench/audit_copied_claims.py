#!/usr/bin/env python3
"""Find claims that one source copied from another, across cases, in a ledger.

WHY THIS EXISTS. The corpus deliberately plants copied claims: one forum poster
restating another's figures, in a different thread, as if it were their own case.
The extraction contract asks for same case, copied claim and overlapping cohort
to be kept as three different links, but the compiler can only group repeated
wording WITHIN one `case_id` -- a report group spanning two cases is correctly
refused, because a report group is one report restated, not two cases merged.
So nothing downstream can currently express "this claim is a copy of that one",
and two copies of one duration can enter a fit as two independent factors.

That is a double count of evidence, and it inflates confidence in whatever the
copied figure says.

WHAT COUNTS AS A COPY, AND WHAT DOES NOT. A single shared number proves nothing.
Small integers and vague phrasings recur honestly: "1 week", "2 to 4 weeks" and
"a couple of months" appear across unrelated cases constantly, and two cases can
legitimately share one figure on different activities or in different units. The
signature of a copy is AGREEMENT ON SEVERAL DISTINCT ACTIVITIES AT ONCE --
the same step carrying the same value in the same unit, two or three steps over,
between cases in different source documents. Three exact agreements between two
posters is not a coincidence any plausible process produces.

Distinctiveness decides strength, because agreement alone is not enough. A step
that two cases both report as "same day or next business day" tells us nothing:
that is what a portal account creation takes, and any number of applicants would
report it identically. A step two cases both report as 369 days is another
matter. So an agreement counts toward a copy only if its value is RARE in the
programme -- shared by no third case. A figure appearing in three or more cases
is a common figure, not a fingerprint, and clusters resting only on such values
are reported as `common_values` rather than as copies.

Agreements are counted PER ACTIVITY, not per row. A ledger routinely records one
claim in two units -- "same day or next business day" becomes both a 0-1
calendar-day range and a 1-business-day value -- and counting those as two
agreements would turn one shared trivially-short step into fake evidence of
copying. Both forms are kept inside the single agreement as its `values`.

So clusters are reported with their strength, and only `strong` ones (two or
more agreeing quantities) are treated as copies. Weak ones are listed so a
reader can judge them, never acted on.

WHAT THE EXIT CODE MEANS. Given a compilation, this reports whether each side of
a strong cluster reaches an INFORMATIVE row or stays residual-only. A
residual-only row is a process-independent constant, so a copy that stayed
residual cannot reinforce its twin and costs nothing. The failure case is a
strong cluster with informative rows on BOTH sides: there the same evidence
enters the likelihood twice. That exits 1, because such a fit must not be
published until the duplication is declared.

    python3 pipeline/procbench/audit_copied_claims.py \
        --evidence runs/.../C35__S03/evidence.json \
        --compilation runs/.../C35__S03_compile/compilation.json
    python3 pipeline/procbench/audit_copied_claims.py --evidence a.json b.json --out report.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict

# Two or more agreeing quantities between two cases. One is not evidence of a copy.
STRONG_MIN_AGREEMENTS = 2


def _value(measurement):
    """A comparable value, keeping the unit: 1 week and 1 day are not the same claim."""
    value, unit = measurement.get('value'), measurement.get('unit')
    if value is None:
        lower, upper = measurement.get('lower'), measurement.get('upper')
        if lower is None and upper is None:
            return None
        value = ('range', lower, upper)
    return json.dumps([value, unit])


def _activity(measurement):
    ids = measurement.get('activity_ids') or ([measurement['activity_id']]
                                              if measurement.get('activity_id') else [])
    return json.dumps(sorted(ids)) if ids else 'whole_case'


def informative_ids(compilation):
    """Rows with at least one modelled operator. A residual-only row informs nothing."""
    out = set()
    for row in compilation.get('observations') or []:
        operators = row.get('operators') or []
        if any(op.get('basis') != 'unmodeled_duration' for op in operators):
            out.add(row['id'])
    return out


def clusters(evidence, informative=None):
    """Cases agreeing on one or more (activity, value, unit) quantities."""
    informative = informative or set()
    by_quantity = defaultdict(list)
    for measurement in evidence.get('measurements') or []:
        if measurement.get('metric') != 'elapsed':
            continue
        case, value = measurement.get('case_id'), _value(measurement)
        if not case or value is None:
            continue
        by_quantity[(_activity(measurement), value)].append(measurement)

    # Group agreeing rows by (case pair, activity). One activity is one agreement,
    # however many unit variants of the same claim the ledger happens to store.
    per_activity = defaultdict(lambda: defaultdict(lambda: ([], [], [])))
    for (activity, value), rows in by_quantity.items():
        by_case = defaultdict(list)
        for row in rows:
            by_case[row['case_id']].append(row)
        cases = sorted(by_case)
        for i, left in enumerate(cases):
            for right in cases[i + 1:]:
                values, left_ids, right_ids = per_activity[(left, right)][activity]
                values.append(dict(value=json.loads(value)[0], unit=json.loads(value)[1]))
                left_ids.extend(r['id'] for r in by_case[left])
                right_ids.extend(r['id'] for r in by_case[right])

    # How many distinct cases report each (activity, value)? A value three or more
    # cases share is a common figure, not a fingerprint.
    spread = {key: len({row['case_id'] for row in rows}) for key, rows in by_quantity.items()}

    out = []
    for (left, right), activities in sorted(per_activity.items()):
        shared = []
        for activity, (values, left_ids, right_ids) in sorted(activities.items()):
            forms = sorted(values, key=lambda x: json.dumps(x, sort_keys=True))
            cases_sharing = max(spread[(activity, json.dumps([v['value'], v['unit']]))]
                                for v in forms)
            shared.append(dict(
                activity=json.loads(activity) if activity != 'whole_case' else 'whole_case',
                values=forms, cases_sharing_value=cases_sharing,
                distinctive=cases_sharing == 2,
                left_ids=sorted(set(left_ids)), right_ids=sorted(set(right_ids))))
        distinctive = [s for s in shared if s['distinctive']]
        left_rows = {i for s in shared for i in s['left_ids']}
        right_rows = {i for s in shared for i in s['right_ids']}
        strength = ('strong' if len(distinctive) >= STRONG_MIN_AGREEMENTS
                    else 'common_values' if len(shared) >= STRONG_MIN_AGREEMENTS
                    else 'weak')
        out.append(dict(
            cases=[left, right], agreements=len(shared),
            distinctive_agreements=len(distinctive), strength=strength,
            shared=shared,
            left_informative=sorted(left_rows & informative),
            right_informative=sorted(right_rows & informative),
            both_sides_informative=bool(left_rows & informative) and bool(right_rows & informative)))
    return sorted(out, key=lambda c: (-c['agreements'], c['cases']))


def report(evidence, compilation=None):
    informative = informative_ids(compilation) if compilation else set()
    found = clusters(evidence, informative)
    strong = [c for c in found if c['strength'] == 'strong']
    common = [c for c in found if c['strength'] == 'common_values']
    double = [c for c in strong if c['both_sides_informative']]
    return dict(
        schema_version='copied-claim-audit/1',
        program_id=evidence.get('program_id'),
        compilation_supplied=compilation is not None,
        cases=len({m.get('case_id') for m in (evidence.get('measurements') or []) if m.get('case_id')}),
        strong_clusters=len(strong), common_value_clusters=len(common),
        weak_clusters=len(found) - len(strong) - len(common),
        double_counted_clusters=len(double),
        verdict=('a strong cluster has informative rows on both sides: the same evidence '
                 'enters the likelihood twice' if double else
                 'no strong cluster is informative on both sides' if compilation else
                 'no compilation supplied, so informativeness was not assessed'),
        strong=strong, common_values=common,
        weak=[c for c in found if c['strength'] == 'weak'],
        method=('A copy is agreement on %d or more distinct ACTIVITIES between two cases, '
                'each on the same value and unit. Unit variants of one claim count once. A '
                'single shared activity is reported as weak and never treated as a copy: small '
                'integers and vague ranges recur honestly. Residual-only rows are '
                'process-independent constants and cannot reinforce a twin.'
                % STRONG_MIN_AGREEMENTS))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--evidence', nargs='+', required=True)
    parser.add_argument('--compilation', nargs='*', default=[],
                        help='matched to --evidence by program_id where supplied')
    parser.add_argument('--out')
    args = parser.parse_args(argv)

    compilations = {}
    for path in args.compilation:
        loaded = json.loads(pathlib.Path(path).read_text())
        compilations[loaded['program_id']] = loaded

    reports, failed = [], False
    for path in args.evidence:
        evidence = json.loads(pathlib.Path(path).read_text())
        current = report(evidence, compilations.get(evidence.get('program_id')))
        reports.append(current)
        print('%-12s cases %-3d strong %-2d common-value %-2d weak %-3d %s'
              % (current['program_id'], current['cases'], current['strong_clusters'],
                 current['common_value_clusters'], current['weak_clusters'], current['verdict']))
        for cluster in current['strong']:
            mark = 'DOUBLE COUNTED' if cluster['both_sides_informative'] else 'one side only'
            print('   %d distinctive of %d agreements  %s  vs  %s  [%s]'
                  % (cluster['distinctive_agreements'], cluster['agreements'],
                     cluster['cases'][0], cluster['cases'][1], mark))
            for shared in cluster['shared']:
                forms = ', '.join('%s %s' % (v['value'], v['unit'] or '') for v in shared['values'])
                name = shared['activity'] if shared['activity'] != 'whole_case' else 'whole_case'
                print('      %-30s %-38s %s' % (name if isinstance(name, str) else ','.join(name),
                                                forms, 'distinctive' if shared['distinctive']
                                                else 'shared by %d cases' % shared['cases_sharing_value']))
        failed = failed or current['double_counted_clusters'] > 0

    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(
            dict(schema_version='copied-claim-audit/1', programs=reports), indent=1))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
