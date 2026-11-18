#!/usr/bin/env python3
"""Prepare SolarTRACE phase evidence, with an archived legacy model importer.

Use --panel-only --definitions <information.csv> for the corrected evidence
panel. It preserves business-day units and zero medians, resolves the documented
owner of repeated joined summaries, and does NOT invent process graphs or cohort
denominators. This panel is evidence preparation, not yet a compiled V6 fit.

WARNING: The older build()/default model export below is preserved only for
historical replay and now requires --legacy-unsafe. Its original rationale is
retained below for provenance, NOT endorsed: it misses documented duplication,
units, zeros, phase scope and true utility identity. See
docs/2026-09-19-solartrace-input-and-sampler-audit.md.

WHY A DETERMINISTIC IMPORTER, NOT AN EXTRACTION. SolarTRACE publishes, per
authority-having-jurisdiction and utility, the median days for four phases of a
residential solar project, per year and system-size class, alongside the number
of installs behind each figure. The California slice is 59,022 long-form rows
across 536 jurisdictions and eight years. Asking a language model to read that
would spend an enormous amount of context to reproduce, imperfectly, a mapping
that is exact arithmetic. Prose extraction is for prose. A table gets code, and
the row itself becomes the quote.

WHY IT MATTERS. This is the only real evidence in the project that carries
genuine cross-agency variation: 536 separate permitting authorities measured the
same way, which is precisely what a synthetic world cannot teach and what the
hierarchy exists to estimate. It is also the only real source with a published
delay distribution rather than a single average.

THE THREE HONEST LIMITS, each recorded in the output rather than smoothed over:

1. **The phase cohorts overlap.** Within one jurisdiction-year-size cell, the
   same installs stand behind the permit median and the inspection median. V6's
   joint finite-cohort likelihood requires cohorts that do not overlap, so
   declaring each phase a cohort with its install count as `n` would assert an
   independence the data plainly violates. Instead each median enters as an
   ordinary population summary with no `sample_size`, and the install count is
   preserved in provenance. That keeps `n` in the record without letting it
   buy precision it has not earned. The alternative -- one phase as a cohort and
   the rest residual -- is available with `--cohort-phase`.
2. **A median is not a case.** These are population summaries over installs, not
   observed applicant journeys, so nothing here identifies a single applicant's
   total, and the four phase medians of one cell must not be added: a project
   does not pass through all four in a way this dataset establishes.
3. **The dataset is installer-reported.** It describes projects that reached the
   installers feeding SolarTRACE, which is not a random sample of applications
   and certainly not of intentions. `sampling` is declared `unselected` because
   the model requires a declaration, and that declaration is an assumption.

Route structure is fixed by the dataset's own phase definitions, in the order it
describes them, with `edges: null` for serial order. No dependency is invented.

    python3 -m pipeline.procbench.import_solartrace \\
        --long runs/rw_parse_20260918/solar_permit/source/solartrace_..._ca_long.csv \\
        --top 12 --out runs/rw_solartrace_20260918
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import re

# The dataset's own phase names, in the order its documentation lists them.
PHASES = [
    ('permit_review', 'Median AHJ Permit Time', 'ahj', 'review',
     'Authority-having-jurisdiction permit review'),
    ('pre_install_ix', 'Median Pre-Install IX Time', 'utility', 'review',
     'Utility pre-installation interconnection review'),
    ('inspection', 'Median Inspection Time', 'ahj', 'inspection',
     'Jurisdiction inspection'),
    ('final_ix_pto', 'Median Final IX to PTO', 'utility', 'decision',
     'Final interconnection through permission to operate'),
]
INSTALLS = 'Installs'
MEDIAN_ROUNDING = 0.5   # a median printed to whole days is a half-day interval


def build_phase_panel(long_path, definitions_path):
    """Deduplicate documented marginal summaries without inventing a fit contract.

    The adjacent installs cell belongs to an AHJ-utility join, not necessarily
    the AHJ- or utility-wide timing sample. Retain it only in row provenance.
    All time/size/technology strata remain separate, and unknown utility IDs
    remain specific to their joined AHJ rather than pooling every NA actor.
    """
    rows=read_long(long_path)
    with open(definitions_path,newline='') as handle:
        definitions={row[1]:row[2] for row in csv.reader(handle) if len(row)>2 and row[1]}
    definition_keys={metric:metric for _,metric,_,_,_ in PHASES}
    definition_keys['Median Pre-Install IX Time']='Median Pre-Install IX (Interconnection) Time'
    for metric,key in definition_keys.items():
        if key not in definitions or 'business days' not in definitions[key].lower():
            raise ValueError('Missing explicit business-day phase definition: '+metric)
    permit_definition=definitions['Median AHJ Permit Time']
    if not all(text in permit_definition for text in
               ('AHJ-only level','utility-only level','duplicated','Same-day approvals')):
        raise ValueError('Source does not supply the expected ownership/zero contract')
    by_metric={metric:(phase,side) for phase,metric,side,_,_ in PHASES}
    # Validate duplicate raw cells instead of silently accepting the last value.
    raw_cells={}
    for row in rows:
        key=tuple(row[field] for field in ('state','geo_id','ahj','utility','eia_id',
                                          'year','size_class','technology','metric'))
        value=float(row['value'])
        if not math.isfinite(value) or value<0:
            raise ValueError('Invalid nonnegative finite SolarTRACE value')
        if key in raw_cells and raw_cells[key]!=value:
            raise ValueError('Contradictory duplicate SolarTRACE row')
        raw_cells[key]=value
    grouped={}
    for line,row in enumerate(rows,2):
        if row['metric'] not in by_metric:
            continue
        phase,side=by_metric[row['metric']]
        if side=='ahj':
            owner=('ahj',row['state'],row['geo_id'])
            owner_name=row['ahj']
            identified=row['geo_id'] not in ('','NA')
            if not identified:
                owner+=('name',row['ahj'])
        elif row['eia_id'] not in ('','NA'):
            owner=('utility',row['eia_id'])
            owner_name=row['utility']
            identified=True
        else:
            owner=('unknown_utility',row['state'],row['geo_id'],row['ahj'],row['utility'])
            owner_name=row['utility']
            identified=False
        key=owner+(row['year'],row['size_class'],row['technology'],phase)
        value=float(row['value'])
        definition=definitions[definition_keys[row['metric']]]
        zero_semantics=(None if value else
            'same_day_approval' if phase=='permit_review' else
            'may_mean_no_pre_install_requirement_or_zero_reported_time' if phase=='pre_install_ix' else
            'reported_zero_business_days_not_missing')
        if key not in grouped:
            ident=hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest()[:20]
            grouped[key]=dict(id='solartrace_phase__'+ident,owner_key=list(owner),
                owner_names=[],owner_identified=identified,phase=phase,metric=row['metric'],
                year=int(row['year']),size_class=row['size_class'],technology=row['technology'],
                statistic='median',value=value,unit='business_days',
                zero_semantics=zero_semantics,phase_definition=definition,
                modeled_as_primitive_visit=False,source_rows=[],
                sample_size=None,sample_size_status='not_established_by_joined_installs_count')
        record=grouped[key]
        if record['value']!=value:
            raise ValueError('Contradictory values within documented timing-owner scope')
        if owner_name not in record['owner_names']:
            record['owner_names'].append(owner_name)
        install_key=tuple(row[field] for field in ('state','geo_id','ahj','utility','eia_id',
                                                  'year','size_class','technology'))+('Installs',)
        record['source_rows'].append(dict(csv_line=line,fields=dict(row),
            joined_install_count=raw_cells.get(install_key)))
    records=[grouped[key] for key in sorted(grouped)]
    if len({r['id'] for r in records})!=len(records):
        raise ValueError('Phase-record identity collision')
    inputs={str(path):hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
            for path in (long_path,definitions_path)}
    report=dict(schema_version='solartrace-phase-panel/1',input_sha256=inputs,
        input_rows=len(rows),timing_rows=sum(len(r['source_rows']) for r in records),
        unique_timing_cells=len(records),repeated_timing_rows=sum(len(r['source_rows'])-1 for r in records),
        unique_zero_cells=sum(r['value']==0 for r in records),
        unidentified_owner_cells=sum(not r['owner_identified'] for r in records),
        graph_compiled=False,finite_cohort_bindings_created=False,fit_ready=False,
        hidden_truth_read=False,model_calls=0,
        remaining_contracts=['Business-to-calendar observation model for mixing with calendar-day cases.',
            'Temporal/system-size/technology target and hierarchy before pooling strata.',
            'Cohort denominators and dependence are not established by adjacent installs.',
            'Distinguish no-required-step zeros from measured same-day performed steps.',
            'Aggregate phases are not primitive operations or complete applicant routes.'])
    return dict(schema_version='solartrace-phase-panel/1',unit='business_days',
                input_sha256=inputs,records=records),report


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', str(text).lower()).strip('_')


def read_long(path):
    with open(path, newline='') as handle:
        return list(csv.DictReader(handle))


def cells(rows):
    """Group long rows back into (ahj, utility, year, size, tech) cells."""
    out = collections.defaultdict(dict)
    for row in rows:
        key = (row['ahj'], row['utility'], row['year'], row['size_class'], row['technology'])
        try:
            out[key][row['metric']] = float(row['value'])
        except (TypeError, ValueError):
            continue
    return out


def build(long_path, top, cohort_phase=None):
    if cohort_phase is not None:
        raise ValueError('--cohort-phase was never implemented; joined installs do not establish timing cohort n')
    rows = read_long(long_path)
    grouped = cells(rows)

    installs_by_ahj = collections.Counter()
    for (ahj, _u, _y, _s, _t), metrics in grouped.items():
        installs_by_ahj[ahj] += metrics.get(INSTALLS, 0.0)
    ranked = [a for a, n in installs_by_ahj.most_common() if n > 0]
    chosen = ranked[:top]

    programs, skipped = [], []
    for ahj in chosen:
        ahj_id = slug(ahj)
        utilities = sorted({k[1] for k in grouped if k[0] == ahj and k[1] not in ('NA', '')})
        agency = 'solartrace__%s' % ahj_id
        utility_actor = 'solartrace__%s__utility' % ahj_id
        operations, observations = [], []
        for name, _metric, side, task, _label in PHASES:
            operations.append(dict(
                id='solartrace__%s__%s' % (ahj_id, name),
                actor_id=agency if side == 'ahj' else utility_actor,
                actor_role='agency', task_type=task, markers=[],
                payer_work=False, agency_work=True, fee=0.0))

        count = 0
        for (cell_ahj, utility, year, size, tech), metrics in sorted(grouped.items()):
            if cell_ahj != ahj:
                continue
            installs = metrics.get(INSTALLS)
            for name, metric, _side, _task, label in PHASES:
                value = metrics.get(metric)
                if value is None or value <= 0:
                    continue
                count += 1
                operation = 'solartrace__%s__%s' % (ahj_id, name)
                row_quote = ('%s | %s | %s | %s | %s | %s = %g'
                             % (cell_ahj, utility, year, size, tech, metric, value))
                observations.append(dict(
                    # The utility belongs in the identity: one jurisdiction can be served by
                    # several, and the same phase-year-size cell recurs once per utility.
                    id='solartrace__%s__%s__%s__%s__%s__%s'
                       % (ahj_id, name, slug(utility), year, slug(size), slug(tech)),
                    case_id=None, source_family='agency_dashboard',
                    sampling='unselected', statistic='median',
                    lower=max(value - MEDIAN_ROUNDING, 0.0), upper=value + MEDIAN_ROUNDING,
                    operators=[dict(basis='single_visit_cycle', activity_ids=[operation],
                                    start='single_visit_start', end='single_visit_end',
                                    visits='one_unspecified', censoring='none',
                                    notes=('%s, published median for this jurisdiction, '
                                           'utility, year and system size.' % label))],
                    operator_weights=[1.0],
                    provenance=dict(dataset='SolarTRACE Permitting, Inspection and '
                                            'Interconnection cycletimes',
                                    row=row_quote, metric=metric, year=year,
                                    size_class=size, technology=tech, utility=utility,
                                    installs_behind_this_median=installs,
                                    sample_size_withheld_because=(
                                        'the four phase medians of one cell stand behind the '
                                        'same installs, so treating each as an independent '
                                        'finite cohort would assert non-overlap the data '
                                        'violates; n is recorded, not used'))))
        if not observations:
            skipped.append(dict(ahj=ahj, reason='no positive phase median in any cell'))
            continue
        programs.append(dict(
            id='solartrace__%s' % ahj_id,
            routes=[dict(id='published_phase_order', prior_weight=1.0,
                         operations=operations,
                         blocks=[dict(id='phases', operations=[o['id'] for o in operations],
                                      edges=None, repeat_key=None)])],
            observations=observations,
            utilities=utilities))
    return dict(programs=programs), dict(
        jurisdictions_available=len(ranked), jurisdictions_selected=len(programs),
        selection_rule='the %d California jurisdictions with the most installs' % top,
        observations=sum(len(p['observations']) for p in programs),
        skipped=skipped, cohort_phase=cohort_phase)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--long', required=True)
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--panel-only',action='store_true',
                    help='Prepare unique source-bound phase evidence, not a process graph or fit input')
    ap.add_argument('--definitions',help='Frozen Information-sheet CSV; required for --panel-only')
    ap.add_argument('--legacy-unsafe',action='store_true',
                    help='Replay the known-invalid historical model export, for diagnostics only')
    ap.add_argument('--cohort-phase', default=None,
                    help='Unsupported historical option; raises rather than pretending to bind a cohort')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    if args.panel_only:
        if not args.definitions or args.legacy_unsafe or args.cohort_phase:
            ap.error('--panel-only requires --definitions and cannot use legacy/cohort flags')
        out=pathlib.Path(args.out)
        if out.exists():
            raise FileExistsError('Choose a fresh phase-panel output directory')
        panel,report=build_phase_panel(args.long,args.definitions)
        out.mkdir(parents=True)
        (out/'phase_panel.json').write_text(json.dumps(panel,indent=2,allow_nan=False)+'\n')
        report['phase_panel_sha256']=hashlib.sha256((out/'phase_panel.json').read_bytes()).hexdigest()
        (out/'import_report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps(report,indent=2))
        return 0
    if not args.legacy_unsafe:
        ap.error('Use --panel-only with --definitions. Historical model export requires --legacy-unsafe')
    data, report = build(args.long, args.top, args.cohort_phase)
    out = pathlib.Path(args.out)
    if out.exists():
        raise FileExistsError('Choose a fresh legacy diagnostic output directory')
    out.mkdir(parents=True)
    payload = json.dumps(data, indent=1)
    (out / 'data.json').write_text(payload)
    source = pathlib.Path(args.long).read_bytes()
    report.update(schema_version='solartrace-import/1',
                  known_invalid_for_substantive_inference=True,
                  diagnostic_replay_only=True,
                  source=str(args.long),
                  source_sha256=hashlib.sha256(source).hexdigest(),
                  data_sha256=hashlib.sha256(payload.encode()).hexdigest(),
                  hidden_truth_read=False, model_calls=0,
                  limits=['phase cohorts overlap, so no sample_size is asserted',
                          'a median is a population summary, not an observed case',
                          'phase medians of one cell must not be summed into a total',
                          'installer-reported, so the sampling declaration is an assumption'])
    (out / 'import_report.json').write_text(json.dumps(report, indent=1))
    print('programmes %d of %d available | observations %d | %s'
          % (report['jurisdictions_selected'], report['jurisdictions_available'],
             report['observations'], out / 'data.json'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
