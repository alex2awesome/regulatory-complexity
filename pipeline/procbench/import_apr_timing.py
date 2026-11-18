#!/usr/bin/env python3
"""Turn California's APR housing-permit timing tables into a V6 model input.

WHY A DETERMINISTIC IMPORTER, NOT AN EXTRACTION. HCD's Annual Progress Reports
publish, per jurisdiction, year and unit category, the median, p25, p75 and p90
of three permit milestones, each with its own denominator:
`corpus/counties/apr_permit_timing.csv` (13,008 group rows over 534
jurisdictions, built by `pipeline/recon/apr_permit_timing.py` from the 922,104
unit records of Table A2) and `corpus/counties/apr_applicant_clock.csv` (8,457
group rows over 514 jurisdictions, from the Table A join). Asking a language
model to read 21,465 rows would spend an enormous amount of context to
reproduce, imperfectly, a mapping that is exact arithmetic. Prose extraction is
for prose. A table gets code, and the row itself becomes the quote.

WHY IT MATTERS. This is the second real cross-jurisdiction dataset in the
project and the only one carrying a published **delay tail for housing
permits**, which is the pilot statute's own domain. Five hundred-odd separate
permitting authorities measured the same way is what a synthetic world cannot
teach and what the hierarchy exists to estimate, and the p90 column is what
makes delay risk -- one of the project's three stated priorities -- an
observable rather than an extrapolation from a median.

ROUTE. The milestones the columns name, in the order the source documents them,
`edges: null` for serial. Four published timestamps bound three consecutive
intervals, and each interval is one operation:

    complete application  ->  entitlement approved   intake_to_entitlement
    entitlement approved  ->  building permit        entitlement_to_permit
    building permit       ->  certificate of occ.    permit_to_occupancy

No dependency, branch or extra step is invented. `submit_to_building_permit`
and `ent_to_co` are the two spans the files publish over *pairs* of these
operations; they enter as `first_to_last_activity_span` operators over the two
operations they cover, not as separate milestones, because no column evidences
a fourth process step.

THE SAMPLE-SIZE DECISION, AND WHY IT GOES THE SOLARTRACE WAY. Every percentile
here carries its own denominator (`n_ent_to_bp`, `n_bp_to_co`, ...), so a
finite-cohort contract looks available. It is not, and this file's own
arithmetic is the proof. V6 admits a denominator only through the explicit
`quantile_cohorts` contract, whose declaration includes **non-overlap with
other evidence**. In this dataset the milestones of one jurisdiction-year cell
demonstrably stand behind the same projects:

  * `n_ent_to_co <= min(n_ent_to_bp, n_bp_to_co)` in 1,958 of the 2,098 cells
    that report all three, which is the arithmetic signature of an
    intersection of one project register, not of three separate draws;
  * in 445 of those cells all three denominators are *exactly equal* -- one
    project set measured three ways;
  * and the median and the p90 of a single span are two order statistics of
    one sample, so they are not independent of each other either.

Declaring any of these a cohort would assert an independence the data plainly
violates. So no observation carries `sample_size`, every denominator is
preserved in provenance, and `n` stays in the record without buying precision
it has not earned. The alternative that would be legitimate -- promoting
exactly one span per cell to a `quantile_cohorts` factor and *deleting* every
other span of that cell so the declared non-overlap holds -- trades roughly
four fifths of the rows for a joint order-statistic likelihood on the rest; it
is not offered here because that trade has not been argued, only noticed.

THE MILESTONES DO NOT TILE A TOTAL, AND THE MEDIANS DO NOT ADD. Measured, not
assumed (`--additivity-report` prints it):

  * The cohorts are not the same cohort. Only 445 of 2,098 three-span cells
    share a denominator. Los Angeles ADU 2025 has 198 entitlement-to-permit
    spans, 5,332 permit-to-occupancy spans and 22 entitlement-to-occupancy
    spans, because each span needs both of its endpoint dates and the
    entitlement date is present on 18.6% of records.
  * On the clean subset -- equal denominators, all three medians positive,
    n >= 10, 39 cells -- the published aggregate median exceeds the sum of the
    component medians in 17 cells and falls short in 11, mean **+18.7 days**.
    Right skew makes the median of a sum exceed the sum of medians, but the
    size and even the sign are jurisdiction-specific.
  * The same subset in the tail runs the other way: the aggregate p90 is
    *below* the sum of the component p90s in 27 of 39 cells, median **-43.9
    days**. Two heavy tails rarely peak in the same project.
  * On the 1,653 cells whose denominators differ, the discrepancy is dominated
    by composition rather than skew: mean **-15.2 days** on the median and
    **-161.7 days** on the p90, with San Joaquin County SFD 2019 publishing a
    0-day aggregate against components summing to 211 days.

So the aggregate is neither a check on the components nor a redundant
restatement of them: it is a fourth and fifth measurement on a different subset
of projects. It is carried as a span operator for that reason, and
`--components-only` drops both aggregates for the non-nested sensitivity input.
Under no circumstances may these medians be added and the shortfall read as
unexplained process time.

THE OTHER LIMITS, each recorded in the output rather than smoothed over:

1. **A median is not a case.** These are population summaries over projects,
   not observed applicant journeys. Nothing here identifies one applicant.
2. **p25 and p75 have no home in the contract.** V6 accepts `median`, `mean`
   and `p90`. Both interquartile columns are read, carried in provenance and
   left unmodelled; they are not silently dropped and they are not coerced.
3. **A zero median is data, and this importer still skips it.** 963 cells
   publish a median entitlement-to-permit span of exactly 0 days, meaning the
   permit issued the same day as the entitlement. A log-duration model has no
   representation for it, so non-positive values are skipped, never zeroed --
   and the skip is *informative missingness*: the discarded cells are
   disproportionately the ministerial same-day processes, so what remains is
   biased toward the slower half. The count is in the report.
4. **The application clock starts late.** HCD defines `APP_SUBMIT_DT` as the
   application date *or* the date the jurisdiction found the application
   complete. `intake_to_entitlement` is therefore a lower bound that excludes
   the completeness back-and-forth, by an unknown, jurisdiction-varying amount.
5. **Permit-to-occupancy is mostly construction.** It is elapsed calendar time
   in which the builder builds; it is not agency review and it is not payer
   paperwork. Its operation declares `agency_work=False, payer_work=False` --
   an explicit statement that the modelled effort channels do not apply, which
   is different from asserting zero elapsed time.
6. **Year and unit category are pooled inside a programme.** One jurisdiction
   is one programme, so the variation between an ADU and a 5+ building, and
   between 2018 and 2025, is absorbed as reporting dispersion rather than
   estimated. Both are preserved per row in provenance; `--unit-cat` and
   `--year` restrict the pool.
7. **The two files are different cohorts.** Only 41% of Table A2 rows matched
   an application, so `intake_to_entitlement` and `submit_to_building_permit`
   describe the matched subset while the other three spans describe all of
   Table A2. Row counts for both are in the report.
8. **The register is not one row per project.** 202,999 of 537,504 distinct
   APNs appear more than once upstream, so denominators are project-record
   counts, not distinct projects. Another reason `n` is not a cohort size.
9. `sampling` is declared `unselected` because the model requires a
   declaration. Filing an APR is mandatory, but what a jurisdiction chooses to
   date is not, and the entitlement-date propensity is a per-jurisdiction
   reporting habit. The declaration is an assumption.

    python3 -m pipeline.procbench.import_apr_timing --top 12 \\
        --out runs/rw_apr_timing_20260919
    python3 -m pipeline.procbench.import_apr_timing --additivity-report
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import statistics

from .infra.manifest import RunManifest, digest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TIMING_CSV = ROOT / 'corpus/counties/apr_permit_timing.csv'
CLOCK_CSV = ROOT / 'corpus/counties/apr_applicant_clock.csv'

# The three consecutive intervals the four published timestamps bound, in the
# order the source documents them. Nothing else is a milestone here.
#   id, actor side, task type, whether the agency/payer work channels apply
OPERATIONS = [
    ('intake_to_entitlement', 'review', False, True,
     'Complete application on file through entitlement approval'),
    ('entitlement_to_permit', 'review', False, True,
     'Entitlement approval through building-permit issue'),
    ('permit_to_occupancy', 'inspection', False, False,
     'Building-permit issue through certificate of occupancy'),
]

# Published span -> (source file, column suffix, the operations it covers).
# A one-operation span is a single visit cycle; a two-operation span is the
# first-to-last span across them, which is what the aggregate column measures.
SPANS = [
    ('submit_to_entitlement', 'clock', 'submit_to_entitlement',
     ['intake_to_entitlement'],
     'Complete application to entitlement approval'),
    ('ent_to_bp', 'timing', 'ent_to_bp',
     ['entitlement_to_permit'],
     'Entitlement approval to building-permit issue'),
    ('bp_to_co', 'timing', 'bp_to_co',
     ['permit_to_occupancy'],
     'Building-permit issue to certificate of occupancy'),
    ('submit_to_building_permit', 'clock', 'submit_to_building_permit',
     ['intake_to_entitlement', 'entitlement_to_permit'],
     'Complete application to building-permit issue'),
    ('ent_to_co', 'timing', 'ent_to_co',
     ['entitlement_to_permit', 'permit_to_occupancy'],
     'Entitlement approval to certificate of occupancy'),
]
AGGREGATE_SPANS = {name for name, _f, _c, ops, _l in SPANS if len(ops) > 1}

# V6 accepts median, mean and p90. p25 and p75 have no statistic in the
# contract: they are read, carried in provenance and left unmodelled.
MODELLED_STATISTICS = ('median', 'p90')
CARRIED_STATISTICS = ('p25', 'p75')
# A percentile printed to a tenth of a day is a half-tenth interval either way;
# the builder rounds every quantile to one decimal (pipeline/recon).
QUANTILE_ROUNDING = 0.05
CELL_KEY = ('jurisdiction', 'county', 'year', 'unit_cat', 'jurisdiction_kind')
SOURCE_FAMILY = 'agency_dashboard'
DATASET = ('California HCD Annual Progress Report, Table A2 permit milestones '
           'and the Table A application join')


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', str(text).lower()).strip('_')


def number(value):
    value = (value or '').strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_cells(timing_path, clock_path):
    """Both files keyed by the same cell identity; neither one is authoritative."""
    cells = collections.defaultdict(dict)
    counts = collections.Counter()
    for label, path in (('timing', timing_path), ('clock', clock_path)):
        with open(path, newline='') as handle:
            for row in csv.DictReader(handle):
                counts[label] += 1
                cells[tuple(row[k] for k in CELL_KEY)][label] = row
    return cells, counts


def cell_value(cells_row, file_label, column):
    row = cells_row.get(file_label)
    return None if row is None else number(row.get(column))


def jurisdiction_rank(cells, unit_cats, years):
    """Total measured spans behind a jurisdiction's published figures.

    The selection denominator, deliberately independent of the value filter:
    it counts what was measured, not what survived the non-positive skip.
    """
    ranked = collections.Counter()
    for key, row in cells.items():
        juris, _county, year, unit_cat, _kind = key
        if unit_cats and unit_cat not in unit_cats:
            continue
        if years and year not in years:
            continue
        for _name, file_label, column, _ops, _label in SPANS:
            ranked[juris] += int(cell_value(row, file_label, 'n_' + column) or 0)
    return ranked


def build(timing_path, clock_path, top, unit_cats=(), years=(), components_only=False):
    cells, file_rows = read_cells(timing_path, clock_path)
    ranked = jurisdiction_rank(cells, set(unit_cats), set(years))
    available = [j for j, n in ranked.items() if n > 0]
    chosen = [j for j, _n in sorted(ranked.items(), key=lambda kv: (-kv[1], kv[0]))
              if _n > 0][:top]
    spans = [s for s in SPANS if not (components_only and s[0] in AGGREGATE_SPANS)]

    skipped = collections.Counter()
    carried_unmodelled = 0
    programs, dropped = [], []
    for juris in chosen:
        jid = slug(juris)
        operations = [dict(
            id='apr__%s__%s' % (jid, name),
            actor_id='apr__%s' % jid, actor_role='agency', task_type=task, markers=[],
            payer_work=payer, agency_work=agency, fee=None)
            for name, task, payer, agency, _label in OPERATIONS]

        observations = []
        for key in sorted(k for k in cells if k[0] == juris):
            _j, county, year, unit_cat, kind = key
            if unit_cats and unit_cat not in unit_cats:
                continue
            if years and year not in years:
                continue
            row = cells[key]
            for name, file_label, column, covered, label in spans:
                denominator = cell_value(row, file_label, 'n_' + column)
                carried = {stat: cell_value(row, file_label, stat + '_' + column)
                           for stat in CARRIED_STATISTICS}
                carried_unmodelled += sum(1 for v in carried.values() if v is not None)
                for stat in MODELLED_STATISTICS:
                    value = cell_value(row, file_label, stat + '_' + column)
                    if value is None:
                        skipped['%s_%s_missing' % (name, stat)] += 1
                        continue
                    if value <= 0:
                        # Never zeroed: a log-duration model cannot represent a
                        # same-day span, and pretending otherwise would invent
                        # a positive delay the source denies.
                        skipped['%s_%s_non_positive' % (name, stat)] += 1
                        continue
                    activity_ids = ['apr__%s__%s' % (jid, op) for op in covered]
                    single = len(activity_ids) == 1
                    operator = dict(
                        basis='single_visit_cycle' if single else 'first_to_last_activity_span',
                        activity_ids=activity_ids,
                        visits='one_unspecified' if single else 'all_in_completed_case',
                        censoring='none',
                        notes=('%s, published %s for this jurisdiction, year and unit '
                               'category.%s' % (label, stat, '' if single else
                                                ' Spans %d consecutive operations; it is a '
                                                'separately measured aggregate, not the sum '
                                                'of their published %ss.'
                                                % (len(activity_ids), stat))))
                    if single:
                        operator.update(start='single_visit_start', end='single_visit_end')
                    quote = ('%s | %s | %s | %s | %s | %s_%s = %g (n_%s = %s)'
                             % (juris, county, year, unit_cat, kind, stat, column,
                                value, column,
                                '' if denominator is None else '%g' % denominator))
                    observations.append(dict(
                        id='apr__%s__%s__%s__%s__%s' % (jid, name, year, slug(unit_cat), stat),
                        case_id=None, source_family=SOURCE_FAMILY,
                        sampling='unselected', statistic=stat,
                        lower=max(value - QUANTILE_ROUNDING, 0.0),
                        upper=value + QUANTILE_ROUNDING,
                        operators=[operator], operator_weights=[1.0],
                        provenance=dict(
                            dataset=DATASET, source_file=file_label, row=quote,
                            span=name, column='%s_%s' % (stat, column),
                            year=year, unit_category=unit_cat, county=county,
                            jurisdiction_kind=kind,
                            projects_behind_this_figure=denominator,
                            interquartile_carried_unmodelled={
                                k: v for k, v in carried.items() if v is not None},
                            interquartile_note=('p25/p75 are read from the source and '
                                                'preserved here; V6 has no statistic for '
                                                'them, so they are carried, not modelled '
                                                'and not coerced into a median.'),
                            covers_operations=covered,
                            sample_size_withheld_because=(
                                'the spans of one jurisdiction-year cell stand behind '
                                'overlapping projects (n_ent_to_co <= min of the other two '
                                'in 1,958 of 2,098 cells; all three exactly equal in 445), '
                                'and a cell\'s median and p90 are two order statistics of '
                                'one sample, so V6\'s joint finite-cohort contract -- which '
                                'declares non-overlap -- would assert an independence the '
                                'data violates; n is recorded, not used'))))
        if not observations:
            dropped.append(dict(jurisdiction=juris,
                                reason='no positive published percentile in any retained cell'))
            continue
        programs.append(dict(
            id='apr__%s' % jid,
            routes=[dict(id='published_milestone_order', prior_weight=1.0,
                         operations=operations,
                         blocks=[dict(id='permit_milestones',
                                      operations=[o['id'] for o in operations],
                                      edges=None, repeat_key=None)])],
            observations=observations))

    report = dict(
        jurisdictions_available=len(available),
        jurisdictions_selected=len(programs),
        selection_rule=('the %d jurisdictions with the most measured milestone spans, '
                        'summed over every retained cell and every published span '
                        '(the n_* denominators, not the surviving percentiles); ties '
                        'broken by jurisdiction name' % top),
        jurisdictions_dropped=dropped,
        unit_categories=sorted(unit_cats) or 'all',
        years=sorted(years) or 'all',
        programs=len(programs), operations_per_program=len(OPERATIONS),
        spans_modelled=[s[0] for s in spans],
        aggregate_spans_modelled=sorted(AGGREGATE_SPANS & {s[0] for s in spans}),
        aggregate_spans_withheld=sorted(AGGREGATE_SPANS - {s[0] for s in spans}),
        components_only=components_only,
        observations=sum(len(p['observations']) for p in programs),
        source_rows_read=dict(file_rows),
        percentiles_skipped=dict(sorted(skipped.items())),
        percentiles_skipped_total=sum(skipped.values()),
        interquartile_values_carried_unmodelled=carried_unmodelled)
    return dict(programs=programs), report


# --------------------------------------------------------------------------
# The additivity test. Reported, never assumed, and never used to repair a row.
# --------------------------------------------------------------------------
AGGREGATE_TESTS = [
    ('ent_to_co', 'timing', ('ent_to_bp', 'timing'), ('bp_to_co', 'timing')),
    ('submit_to_building_permit', 'clock', ('submit_to_entitlement', 'clock'),
     ('ent_to_bp', 'timing')),
]


def _spread(diffs):
    ordered = sorted(diffs)
    return dict(cells=len(ordered),
                aggregate_above_sum=sum(1 for d in ordered if d > .5),
                aggregate_below_sum=sum(1 for d in ordered if d < -.5),
                agree_within_half_day=sum(1 for d in ordered if abs(d) <= .5),
                median_difference_days=round(statistics.median(ordered), 1),
                mean_difference_days=round(statistics.fmean(ordered), 1),
                p10_difference_days=round(ordered[len(ordered) // 10], 1),
                p90_difference_days=round(ordered[(9 * len(ordered)) // 10], 1))


def additivity_report(timing_path=TIMING_CSV, clock_path=CLOCK_CSV, min_n=10):
    """Do the milestones tile a total, and do the published medians add?"""
    cells, _rows = read_cells(timing_path, clock_path)
    out = {}
    for aggregate, agg_file, first, second in AGGREGATE_TESTS:
        equal_n, unequal_n = {}, {}
        matched = intersectionish = equal_cells = 0
        for _key, row in cells.items():
            parts = [(aggregate, agg_file), first, second]
            n = [cell_value(row, f, 'n_' + c) for c, f in parts]
            if any(v is None or v <= 0 for v in n):
                continue
            matched += 1
            if n[0] <= min(n[1], n[2]):
                intersectionish += 1
            same = n[0] == n[1] == n[2]
            equal_cells += same
            bucket = equal_n if same else unequal_n
            for stat in MODELLED_STATISTICS:
                v = [cell_value(row, f, stat + '_' + c) for c, f in parts]
                if any(x is None for x in v):
                    continue
                bucket.setdefault(stat, []).append(
                    (v[0] - (v[1] + v[2]), min(v), n[1]))
        entry = dict(aggregate=aggregate, components=[first[0], second[0]],
                     cells_reporting_all_three=matched,
                     cells_with_equal_denominators=equal_cells,
                     aggregate_denominator_no_larger_than_components=intersectionish)
        for stat in MODELLED_STATISTICS:
            for label, bucket, clean in (('equal_denominators', equal_n, True),
                                         ('unequal_denominators', unequal_n, False)):
                rows = bucket.get(stat, [])
                if rows:
                    entry['%s_%s' % (stat, label)] = _spread([d for d, _m, _n in rows])
                clean_rows = [d for d, m, n in rows if clean and m > 0 and n >= min_n]
                if clean_rows:
                    entry['%s_equal_denominators_positive_n%d' % (stat, min_n)] = _spread(clean_rows)
        entry['reading'] = (
            'The milestones do not tile a shared cohort: each span needs both of its '
            'endpoint dates, so the denominators differ cell by cell. Where they do not '
            'differ and every median is positive, the aggregate median exceeds the sum of '
            'the component medians more often than not -- the median of a sum is not the '
            'sum of medians for right-skewed components -- while the aggregate p90 falls '
            'below the sum of component p90s, because two heavy tails rarely peak in the '
            'same project. Neither direction is a data error and neither shortfall is '
            'unexplained process time.')
        out[aggregate] = entry
    out['method'] = ('Per cell, published aggregate minus the sum of its two published '
                     'components, split by whether the three denominators agree. No value '
                     'is imputed, repaired or dropped from the import on the strength of '
                     'this test.')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--timing', default=str(TIMING_CSV))
    ap.add_argument('--clock', default=str(CLOCK_CSV))
    ap.add_argument('--top', type=int, default=12,
                    help='jurisdictions to keep, ranked by measured milestone spans')
    ap.add_argument('--unit-cat', action='append', default=[],
                    help='restrict to these HCD unit categories (repeatable); default all')
    ap.add_argument('--year', action='append', default=[],
                    help='restrict to these report years (repeatable); default all')
    ap.add_argument('--components-only', action='store_true',
                    help='drop the two aggregate spans, which nest the component spans '
                         'over partly the same projects; the non-nested sensitivity input')
    ap.add_argument('--additivity-report', action='store_true',
                    help='print the tiling / median-addition test and exit')
    ap.add_argument('--out')
    args = ap.parse_args(argv)

    if args.additivity_report:
        print(json.dumps(additivity_report(pathlib.Path(args.timing),
                                           pathlib.Path(args.clock)), indent=1))
        return 0
    if not args.out:
        ap.error('--out is required unless --additivity-report is given')

    timing, clock = pathlib.Path(args.timing), pathlib.Path(args.clock)
    data, report = build(timing, clock, args.top,
                         tuple(args.unit_cat), tuple(args.year), args.components_only)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # The house run contract: input hashes, a source snapshot and an explicit
    # hidden-truth declaration. Imported directly from infra, not via a fitter.
    record = RunManifest(out, {}, operation='apr_timing.import', inputs=[timing, clock],
                         config=vars(args), seeds={}, hidden_truth_read=False,
                         source_root=pathlib.Path(__file__).parent,
                         sources=['import_apr_timing.py'])
    payload = json.dumps(data, indent=1)
    (out / 'data.json').write_text(payload)
    report.update(
        schema_version='procbench-run/1',
        operation='apr_timing.import',
        sources=[str(args.timing), str(args.clock)],
        input_sha256={str(p): hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
                      for p in (args.timing, args.clock)},
        data_sha256=hashlib.sha256(payload.encode()).hexdigest(),
        hidden_truth_read=False, model_calls=0,
        additivity_test=additivity_report(pathlib.Path(args.timing), pathlib.Path(args.clock)),
        limits=[
            'milestone spans of one cell overlap in projects, so no sample_size is '
            'asserted and no quantile_cohorts factor is declared',
            'the milestones do not tile a shared cohort: only 445 of 2,098 cells give '
            'all three spans the same denominator',
            'published medians do not add and published p90s do not add; the aggregate '
            'spans are separate measurements, not sums, and a shortfall is not '
            'unexplained process time',
            'the aggregate spans nest their components over partly the same projects, so '
            'V6 row-conditional independence overstates the evidence; --components-only '
            'builds the non-nested sensitivity input',
            'p25 and p75 have no statistic in the V6 contract: carried in provenance, '
            'unmodelled, not coerced',
            'non-positive published percentiles are skipped, never zeroed, and the skip '
            'is informative missingness biased against same-day ministerial processes',
            'a median is a population summary, not an observed applicant case',
            'the application clock starts at completeness determination, so '
            'intake_to_entitlement is a lower bound on applicant-experienced waiting',
            'permit_to_occupancy is dominated by construction, not agency review; its '
            'operation declares both work channels inapplicable rather than zero',
            'year and unit category are pooled inside a jurisdiction programme and '
            'absorbed as reporting dispersion',
            'the two source files cover different cohorts: only 41% of Table A2 rows '
            'matched an application record',
            'denominators count project records, not distinct projects; 202,999 of '
            '537,504 upstream APNs recur',
            'sampling is declared unselected because the model requires a declaration, '
            'and entitlement-date recording is a per-jurisdiction reporting habit'])
    (out / 'import_report.json').write_text(json.dumps(report, indent=1))
    record.complete(model_calls=0, hidden_truth_read=False,
                    observations=report['observations'],
                    jurisdictions_selected=report['jurisdictions_selected'],
                    data_sha256=report['data_sha256'],
                    report_sha256=digest((out / 'import_report.json').read_bytes()))
    print('programmes %d of %d available | observations %d | skipped percentiles %d | %s'
          % (report['jurisdictions_selected'], report['jurisdictions_available'],
             report['observations'], report['percentiles_skipped_total'], out / 'data.json'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
