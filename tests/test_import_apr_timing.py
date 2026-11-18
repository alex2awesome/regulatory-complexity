"""Pin the APR housing-permit importer's contract decisions.

Source-only: everything here runs off small fixture CSVs written into tmp_path,
so no corpus file, network call or paid backend is needed. The two tests that
do read `corpus/counties/*.csv` exist to keep the module docstring's measured
claims honest, and they skip when those working files are absent.
"""
import csv
import json

import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.import_apr_timing import (
    CLOCK_CSV, TIMING_CSV, additivity_report, build, main)

TIMING_COLUMNS = ['jurisdiction', 'county', 'year', 'unit_cat', 'jurisdiction_kind',
                  'n_projects', 'n_with_entitlement_date', 'n_with_bp_date', 'n_with_co_date',
                  'n_flagged_no_entitlement', 'n_flagged_no_building_permit',
                  'n_ent_to_bp', 'median_ent_to_bp', 'p25_ent_to_bp', 'p75_ent_to_bp', 'p90_ent_to_bp',
                  'n_bp_to_co', 'median_bp_to_co', 'p25_bp_to_co', 'p75_bp_to_co', 'p90_bp_to_co',
                  'n_ent_to_co', 'median_ent_to_co', 'p25_ent_to_co', 'p75_ent_to_co', 'p90_ent_to_co']
CLOCK_COLUMNS = ['jurisdiction', 'county', 'year', 'unit_cat', 'jurisdiction_kind',
                 'n_joined', 'n_ministerial', 'n_discretionary', 'n_unlabelled_project_type',
                 'n_approved', 'n_pending', 'n_withdrawn', 'n_disapproved',
                 'n_submit_to_building_permit', 'median_submit_to_building_permit',
                 'p25_submit_to_building_permit', 'p75_submit_to_building_permit',
                 'p90_submit_to_building_permit',
                 'n_submit_to_entitlement', 'median_submit_to_entitlement',
                 'p25_submit_to_entitlement', 'p75_submit_to_entitlement',
                 'p90_submit_to_entitlement']


def _cell(columns, **values):
    row = {column: '' for column in columns}
    row.update({key: str(value) for key, value in values.items()})
    return row


def _write(path, columns, rows):
    with open(path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def sources(tmp_path):
    """Two jurisdictions. ALPHA is the large one and carries every defect."""
    timing = [
        # A complete cell: three spans, all percentiles present and positive.
        _cell(TIMING_COLUMNS, jurisdiction='ALPHA', county='Alpha', year='2024',
              unit_cat='ADU', jurisdiction_kind='city', n_projects=500,
              n_ent_to_bp=200, median_ent_to_bp=30, p25_ent_to_bp=10, p75_ent_to_bp=70,
              p90_ent_to_bp=120,
              n_bp_to_co=200, median_bp_to_co=180, p25_bp_to_co=120, p75_bp_to_co=260,
              p90_bp_to_co=400,
              # Deliberately NOT 30+180: the aggregate is its own measurement.
              n_ent_to_co=200, median_ent_to_co=240, p25_ent_to_co=150, p75_ent_to_co=330,
              p90_ent_to_co=460),
        # A same-day entitlement decision and an absent occupancy span.
        _cell(TIMING_COLUMNS, jurisdiction='ALPHA', county='Alpha', year='2023',
              unit_cat='SFD', jurisdiction_kind='city', n_projects=400,
              n_ent_to_bp=150, median_ent_to_bp=0, p25_ent_to_bp=0, p75_ent_to_bp=0,
              p90_ent_to_bp=45,
              n_bp_to_co=0, n_ent_to_co=0),
        _cell(TIMING_COLUMNS, jurisdiction='BETA COUNTY', county='Beta', year='2024',
              unit_cat='ADU', jurisdiction_kind='unincorporated', n_projects=20,
              n_ent_to_bp=10, median_ent_to_bp=55, p25_ent_to_bp=20, p75_ent_to_bp=90,
              p90_ent_to_bp=140,
              n_bp_to_co=0, n_ent_to_co=0),
    ]
    clock = [
        _cell(CLOCK_COLUMNS, jurisdiction='ALPHA', county='Alpha', year='2024',
              unit_cat='ADU', jurisdiction_kind='city', n_joined=400,
              n_submit_to_entitlement=180, median_submit_to_entitlement=90,
              p25_submit_to_entitlement=40, p75_submit_to_entitlement=150,
              p90_submit_to_entitlement=260,
              n_submit_to_building_permit=190, median_submit_to_building_permit=150,
              p25_submit_to_building_permit=70, p75_submit_to_building_permit=240,
              p90_submit_to_building_permit=380),
        _cell(CLOCK_COLUMNS, jurisdiction='BETA COUNTY', county='Beta', year='2024',
              unit_cat='ADU', jurisdiction_kind='unincorporated', n_joined=15,
              n_submit_to_entitlement=8, median_submit_to_entitlement=12,
              p25_submit_to_entitlement=4, p75_submit_to_entitlement=25,
              p90_submit_to_entitlement=40),
    ]
    return (_write(tmp_path / 'apr_permit_timing.csv', TIMING_COLUMNS, timing),
            _write(tmp_path / 'apr_applicant_clock.csv', CLOCK_COLUMNS, clock))


def rows_of(data):
    return [o for p in data['programs'] for o in p['observations']]


def test_one_programme_per_jurisdiction_over_the_published_milestone_order(sources):
    data, report = build(*sources, top=10)
    assert [p['id'] for p in data['programs']] == ['apr__alpha', 'apr__beta_county']
    assert report['jurisdictions_available'] == 2 and report['jurisdictions_selected'] == 2
    for program in data['programs']:
        route, = program['routes']
        assert route['id'] == 'published_milestone_order'
        # The three intervals the four published timestamps bound, in order.
        assert [o['id'].rsplit('__', 1)[1] for o in route['operations']] == [
            'intake_to_entitlement', 'entitlement_to_permit', 'permit_to_occupancy']
        block, = route['blocks']
        assert block['edges'] is None and block['repeat_key'] is None
        assert block['operations'] == [o['id'] for o in route['operations']]
        # Every cell of one jurisdiction shares that jurisdiction's operations:
        # year and unit category are pooled, not turned into new milestones.
        assert {a for o in program['observations'] for op in o['operators']
                for a in op['activity_ids']} <= set(block['operations'])


def test_each_percentile_becomes_its_own_observation_with_its_own_statistic(sources):
    data, _report = build(*sources, top=10)
    cell = {o['id']: o for o in rows_of(data)
            if o['provenance']['year'] == '2024' and o['provenance']['unit_category'] == 'ADU'
            and o['id'].startswith('apr__alpha__ent_to_bp')}
    assert sorted(cell) == ['apr__alpha__ent_to_bp__2024__adu__median',
                            'apr__alpha__ent_to_bp__2024__adu__p90']
    median = cell['apr__alpha__ent_to_bp__2024__adu__median']
    p90 = cell['apr__alpha__ent_to_bp__2024__adu__p90']
    assert median['statistic'] == 'median' and p90['statistic'] == 'p90'
    assert (median['lower'], median['upper']) == (29.95, 30.05)
    assert (p90['lower'], p90['upper']) == (119.95, 120.05)
    assert median['case_id'] is None and median['sampling'] == 'unselected'
    # p25 and p75 have no statistic in the V6 contract. They are carried in
    # provenance, not coerced into one that exists and not silently dropped.
    assert {o['statistic'] for o in rows_of(data)} == {'median', 'p90'}
    assert median['provenance']['interquartile_carried_unmodelled'] == {'p25': 10.0, 'p75': 70.0}
    assert all('p25' in o['provenance']['interquartile_carried_unmodelled']
               for o in rows_of(data) if o['provenance']['span'] == 'ent_to_bp')


def test_a_one_operation_span_is_a_cycle_and_an_aggregate_is_a_two_operation_span(sources):
    data, report = build(*sources, top=10)
    by_span = {}
    for o in rows_of(data):
        by_span.setdefault(o['provenance']['span'], []).append(o)
    component, = [op for o in by_span['bp_to_co'] for op in o['operators']
                  if o['statistic'] == 'median']
    assert component['basis'] == 'single_visit_cycle'
    assert component['activity_ids'] == ['apr__alpha__permit_to_occupancy']
    aggregate, = [op for o in by_span['ent_to_co'] for op in o['operators']
                  if o['statistic'] == 'median']
    assert aggregate['basis'] == 'first_to_last_activity_span'
    assert aggregate['activity_ids'] == ['apr__alpha__entitlement_to_permit',
                                         'apr__alpha__permit_to_occupancy']
    # The aggregate is a separate measurement, kept at its published value: the
    # importer neither reconciles it to 30+180 nor treats the gap as process time.
    published = [o for o in by_span['ent_to_co'] if o['statistic'] == 'median']
    assert [o['lower'] for o in published] == [239.95]
    # ...and it can be dropped wholesale for the non-nested sensitivity input.
    only, lean = build(*sources, top=10, components_only=True)
    assert lean['aggregate_spans_withheld'] == ['ent_to_co', 'submit_to_building_permit']
    assert not {o['provenance']['span'] for o in rows_of(only)} & {'ent_to_co',
                                                                   'submit_to_building_permit'}
    assert lean['observations'] < report['observations']


def test_no_percentile_asserts_a_sample_size_and_the_denominator_survives_in_provenance(sources):
    data, report = build(*sources, top=10)
    for o in rows_of(data):
        assert 'sample_size' not in o
        assert o['provenance']['projects_behind_this_figure'] is not None
        assert 'overlapping projects' in o['provenance']['sample_size_withheld_because']
    assert not any('quantile_cohorts' in p for p in data['programs'])
    assert report['jurisdictions_dropped'] == []
    # The denominator is kept, and it is the source's own.
    ent = next(o for o in rows_of(data) if o['id'].endswith('ent_to_bp__2024__adu__median'))
    assert ent['provenance']['projects_behind_this_figure'] == 200.0
    # And the decision is forced, not stylistic: V6 refuses a population
    # summary that names an n outside the joint finite-cohort contract, whose
    # declaration includes the non-overlap these milestones do not have.
    VisitHierarchy(data, Config(modeled_channels=('elapsed',)))
    asserted = json.loads(json.dumps(data))
    asserted['programs'][0]['observations'][0]['sample_size'] = 200
    with pytest.raises(ValueError, match='Finite-cohort'):
        VisitHierarchy(asserted, Config(modeled_channels=('elapsed',)))


def test_missing_or_non_positive_percentiles_are_skipped_rather_than_zeroed(sources):
    data, report = build(*sources, top=10)
    ids = {o['id'] for o in rows_of(data)}
    # median_ent_to_bp is exactly 0 in ALPHA/2023/SFD: a same-day entitlement.
    # It is real, it has no representation in a log-duration model, and it is
    # skipped rather than entered as a zero or nudged to a positive floor.
    assert 'apr__alpha__ent_to_bp__2023__sfd__median' not in ids
    assert 'apr__alpha__ent_to_bp__2023__sfd__p90' in ids       # 45 days survives
    assert report['percentiles_skipped']['ent_to_bp_median_non_positive'] == 1
    # BETA COUNTY publishes no occupancy span, and neither it nor ALPHA's 2023
    # cell appears in the clock file at all: absence is a skip, never a zero.
    assert report['percentiles_skipped']['bp_to_co_median_missing'] == 2
    assert report['percentiles_skipped']['submit_to_building_permit_p90_missing'] == 2
    assert report['percentiles_skipped_total'] == sum(report['percentiles_skipped'].values())
    for o in rows_of(data):
        assert o['lower'] >= 0 and o['upper'] > o['lower']
        assert o['upper'] > 0.1        # nothing arrived as a zeroed duration
    assert not any(o['provenance']['span'] == 'bp_to_co' for o in rows_of(data)
                   if o['id'].startswith('apr__beta_county'))


def test_selection_ranks_by_measured_spans_and_records_the_rule(sources):
    data, report = build(*sources, top=1)
    assert [p['id'] for p in data['programs']] == ['apr__alpha']
    assert report['jurisdictions_available'] == 2 and report['jurisdictions_selected'] == 1
    assert 'most measured milestone spans' in report['selection_rule']
    assert report['source_rows_read'] == dict(timing=3, clock=2)
    # A restriction narrows the pool it ranks over, and is recorded.
    _adu, adu = build(*sources, top=2, unit_cats=('ADU',))
    assert adu['unit_categories'] == ['ADU'] and adu['years'] == 'all'


def test_the_additivity_test_measures_the_gap_and_never_repairs_a_row(sources):
    measured = additivity_report(*sources)
    entry = measured['ent_to_co']
    assert entry['components'] == ['ent_to_bp', 'bp_to_co']
    assert entry['cells_reporting_all_three'] == 1
    assert entry['cells_with_equal_denominators'] == 1
    # 240 published against 30+180 = 210: the median of a sum is not the sum of
    # medians, and the 30-day excess is not extra process time.
    equal = entry['median_equal_denominators']
    assert equal['aggregate_above_sum'] == 1 and equal['mean_difference_days'] == 30.0
    # 460 published against 120+400 = 520: the tail is sub-additive.
    assert entry['p90_equal_denominators']['mean_difference_days'] == -60.0
    assert 'not the sum of medians' in entry['reading']
    assert 'is imputed, repaired or dropped' in measured['method']


def test_cli_writes_a_run_report_with_hashes_and_declared_limits(sources, tmp_path, capsys):
    out = tmp_path / 'run'
    assert main(['--timing', str(sources[0]), '--clock', str(sources[1]),
                 '--top', '2', '--out', str(out)]) == 0
    report = json.loads((out / 'import_report.json').read_text())
    assert report['schema_version'] == 'procbench-run/1'
    assert report['hidden_truth_read'] is False and report['model_calls'] == 0
    assert set(report['input_sha256']) == {str(sources[0]), str(sources[1])}
    assert all(len(h) == 64 for h in report['input_sha256'].values())
    limits = ' | '.join(report['limits'])
    for claim in ('no sample_size is asserted', 'do not tile a shared cohort',
                  'p25 and p75', 'skipped, never zeroed', 'not an observed applicant case',
                  'lower bound', 'construction, not agency review'):
        assert claim in limits
    assert report['additivity_test']['ent_to_co']['cells_reporting_all_three'] == 1
    assert 'programmes 2 of 2 available' in capsys.readouterr().out
    # The written input is the one the report hashed, and V6 accepts it.
    data = json.loads((out / 'data.json').read_text())
    VisitHierarchy(data, Config(modeled_channels=('elapsed',)))


corpus = pytest.mark.skipif(not (TIMING_CSV.exists() and CLOCK_CSV.exists()),
                            reason='APR working CSVs are not present in this checkout')


@corpus
def test_docstring_overlap_numbers_still_describe_the_real_files():
    """The sample-size refusal rests on measured overlap; keep the numbers true."""
    entry = additivity_report()['ent_to_co']
    assert entry['cells_reporting_all_three'] == 2098
    assert entry['aggregate_denominator_no_larger_than_components'] == 1958
    assert entry['cells_with_equal_denominators'] == 445
    clean = entry['median_equal_denominators_positive_n10']
    assert (clean['cells'], clean['aggregate_above_sum'], clean['aggregate_below_sum']) == (39, 17, 11)
    assert clean['mean_difference_days'] == 18.7
    assert entry['p90_equal_denominators_positive_n10']['median_difference_days'] == -43.9


@corpus
def test_the_real_import_builds_one_contract_valid_programme_per_jurisdiction():
    data, report = build(TIMING_CSV, CLOCK_CSV, top=4)
    assert report['jurisdictions_available'] == 531
    assert len(data['programs']) == 4 == report['jurisdictions_selected']
    assert len({p['id'] for p in data['programs']}) == 4
    assert all(len(p['routes'][0]['operations']) == 3 for p in data['programs'])
    assert report['observations'] > 0 and report['percentiles_skipped_total'] > 0
    assert not any('sample_size' in o for o in rows_of(data))
    VisitHierarchy(data, Config(modeled_channels=('elapsed',)))
