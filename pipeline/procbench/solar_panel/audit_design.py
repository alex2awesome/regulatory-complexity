#!/usr/bin/env python3
"""Stage A design audit for the solar leg. READ-ONLY, no model is fitted.

Answers exactly the questions `docs/2026-09-20-solar-leg-plan-for-claude.md`
stage A asks, and evaluates its two gates plus the plan's kill criteria:

  * rank and confounding of the authority, year and phase contrasts;
  * how much within-authority volume variation survives the 2017-2022 window;
  * how many authorities have four or more usable years;
  * the reported zeros and their three distinct semantics;
  * whether same-day cells should be an interval of [0, 0.5] or [0, 1] days;
  * the share of admitted cells resting on a single source row.

Gate 1 fails if an authority effect is not separable from year and phase.
Gate 2 reports, before any estimate, if more than a quarter of cells rest on one
source row. Kill criterion: fewer than 200 authorities with four usable years
drops the load-elasticity estimand rather than weakening it.

    python3 -m pipeline.procbench.solar_panel.audit_design
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import statistics
from collections import Counter, defaultdict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'runs/solar_panel_20260920'
AUTHORITY_PHASES = ('permit_review', 'inspection')
USABLE_INSTALL_FLOORS = (1, 5, 10, 30)


def load(panel_path):
    with panel_path.open(encoding='utf-8') as handle:
        return [r for r in csv.DictReader(handle)]


def design_rank(rows):
    """Rank of the authority/year/phase/stratum design on the observed cells.

    Reference coding with a single intercept: one level of each factor is
    dropped. A rank equal to the column count means every retained contrast is
    estimable from this design, so an authority effect is separable from year
    and phase. Deficiency names how many contrasts are aliased.
    """
    authorities = sorted({r['stable_owner_id'] for r in rows})
    years = sorted({r['year'] for r in rows})
    phases = sorted({r['phase'] for r in rows})
    sizes = sorted({r['size_class'] for r in rows})
    techs = sorted({r['technology'] for r in rows})
    index = {('a', a): i for i, a in enumerate(authorities[1:])}
    offset = len(index)
    for j, y in enumerate(years[1:]):
        index[('y', y)] = offset + j
    offset = len(index)
    for j, p in enumerate(phases[1:]):
        index[('p', p)] = offset + j
    offset = len(index)
    for j, s in enumerate(sizes[1:]):
        index[('s', s)] = offset + j
    offset = len(index)
    for j, t in enumerate(techs[1:]):
        index[('t', t)] = offset + j
    width = len(index) + 1
    matrix = np.zeros((len(rows), width))
    matrix[:, -1] = 1.0
    for i, r in enumerate(rows):
        for key in (('a', r['stable_owner_id']), ('y', r['year']), ('p', r['phase']),
                    ('s', r['size_class']), ('t', r['technology'])):
            if key in index:
                matrix[i, index[key]] = 1.0
    rank = int(np.linalg.matrix_rank(matrix))
    return dict(observations=len(rows), columns=width, rank=rank, deficiency=width - rank,
                authorities=len(authorities), years=len(years), phases=len(phases),
                separable=bool(width - rank == 0),
                interpretation=('Every retained authority, year and phase contrast is estimable '
                                'from the observed cells.' if width - rank == 0 else
                                'Some contrast is aliased; an authority effect cannot be separated '
                                'from year and phase for at least one authority.'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--panel', default=str(OUT / 'panel_v1.csv'))
    ap.add_argument('--out', default=str(OUT / 'design_audit_v1.json'))
    args = ap.parse_args(argv)
    panel_path = pathlib.Path(args.panel)
    rows = load(panel_path)
    present = [r for r in rows if r['present'] == 'true']
    report = dict(schema_version='solar-panel-design-audit/1', stage='A',
                  plan='docs/2026-09-20-solar-leg-plan-for-claude.md',
                  estimands='runs/solar_panel_20260920/estimands_frozen_v1.json',
                  panel=dict(path=str(panel_path.relative_to(ROOT)),
                             sha256=hashlib.sha256(panel_path.read_bytes()).hexdigest()),
                  reads_benchmark_truth=False, network_used=False, model_fitted=False)

    # ---- coverage -------------------------------------------------------
    report['coverage'] = dict(
        slots=len(rows), present_cells=len(present),
        by_phase=dict(Counter(r['phase'] for r in present)),
        by_phase_level=dict(Counter(r['phase_level'] for r in present)),
        by_year=dict(Counter(r['year'] for r in present)),
        authorities_total=len({r['stable_owner_id'] for r in rows if r['owner_kind'] == 'ahj'}),
        authorities_with_any_cell=len({r['stable_owner_id'] for r in present if r['owner_kind'] == 'ahj'}),
        utility_owners_with_any_cell=len({r['stable_owner_id'] for r in present if r['owner_kind'] != 'ahj'}),
        county_unmatched_cells=sum(1 for r in present if r['owner_kind'] == 'ahj' and not r['county']))

    authority_cells = [r for r in present if r['phase'] in AUTHORITY_PHASES and r['owner_kind'] == 'ahj']
    report['authority_level_cells'] = len(authority_cells)

    # ---- gate 1: design rank -------------------------------------------
    report['design_rank'] = design_rank(authority_cells)

    # ---- gate 2: provenance thinness ------------------------------------
    counts = Counter(int(r['source_row_count'] or 0) for r in present)
    single = counts.get(1, 0)
    geo_counts = Counter((len(r['geo_ids'].split(';')) if r['geo_ids'] else 0,
                          int(r['source_row_count'] or 0)) for r in present)
    report['provenance'] = dict(
        source_row_count_distribution=dict(sorted(counts.items())[:10]),
        cells_on_one_source_row=single,
        share_on_one_source_row=round(single / len(present), 4),
        gate_threshold=0.25,
        exceeds_threshold=bool(single / len(present) > 0.25),
        gate_verdict_as_frozen=('EXCEEDS' if single / len(present) > 0.25 else 'within'),
        geo_id_by_source_row_pairs={str(k): v for k, v in sorted(geo_counts.items(), key=lambda kv: -kv[1])[:8]},
        what_the_field_actually_measures=(
            'Inspection after running the gate: source_row_count is the number of raw long-CSV rows '
            'consolidated into one owner cell, not a sample size and not a corroboration count. The '
            'dominant pair is one geographic id with one source row, which is simply an authority '
            'that needed no consolidation. The gate as frozen in the plan therefore tests a property '
            'that does not mean what the plan assumed.'),
        honest_reading=(
            'Reported as frozen because the plan froze it, and reported as uninformative because it '
            'is. The real provenance limitation is unchanged and separate: the number of projects '
            'behind each median is unknown and only bounded above by the installation count.'))

    # ---- usable years per authority and the elasticity kill criterion ----
    usable = {}
    for floor in USABLE_INSTALL_FLOORS:
        years_per = defaultdict(set)
        for r in authority_cells:
            if int(r['installs_same_cell'] or 0) >= floor:
                years_per[r['stable_owner_id']].add(r['year'])
        counts_ = [len(v) for v in years_per.values()]
        usable[str(floor)] = dict(
            authorities_with_any_year=len(counts_),
            authorities_with_4_or_more_years=sum(1 for c in counts_ if c >= 4),
            authorities_with_6_years=sum(1 for c in counts_ if c >= 6),
            median_years=statistics.median(counts_) if counts_ else 0)
    report['usable_years_by_install_floor'] = usable
    best = usable[str(USABLE_INSTALL_FLOORS[1])]['authorities_with_4_or_more_years']
    report['elasticity_kill_criterion'] = dict(
        threshold_authorities=200, at_install_floor=5,
        authorities_with_4_or_more_years=best,
        estimand_E2_survives=bool(best >= 200))

    # ---- within-authority volume variation ------------------------------
    volume = defaultdict(dict)
    for r in authority_cells:
        v = int(r['installs_same_cell'] or 0)
        if v > 0:
            key = (r['stable_owner_id'], r['size_class'], r['technology'])
            volume[key][r['year']] = v
    ratios = [max(d.values()) / min(d.values()) for d in volume.values()
              if len(d) >= 4 and min(d.values()) >= 5]
    report['within_authority_volume_variation'] = dict(
        strata_with_4_or_more_years_at_5_installs=len(ratios),
        max_over_min_median=round(statistics.median(ratios), 2) if ratios else None,
        max_over_min_quartiles=[round(sorted(ratios)[len(ratios) // 4], 2),
                                round(sorted(ratios)[3 * len(ratios) // 4], 2)] if ratios else None,
        log2_spread_median=round(statistics.median([math.log2(x) for x in ratios]), 2) if ratios else None,
        interpretation=('Exposure range available to identify a load elasticity, within an '
                        'authority and stratum, across the window.'))

    # ---- reported zeros and their semantics ------------------------------
    zeros = [r for r in present if r['reported_zero'] == 'true']
    report['reported_zeros'] = dict(
        total=len(zeros), by_semantics=dict(Counter(r['zero_semantics'] for r in zeros)),
        by_phase=dict(Counter(r['phase'] for r in zeros)),
        share_of_present=round(len(zeros) / len(present), 4),
        decision_required=('same_day_approval is a measured zero and belongs in the model as a '
                           'sub-day interval. may_mean_no_pre_install_requirement_or_zero_reported_time '
                           'is ambiguous between a step that does not exist and a step that took no '
                           'time, and those are different processes; it must be held or modelled as a '
                           'mixture, not silently treated as a fast step.'))

    # ---- same-day interval sensitivity ------------------------------------
    same_day = [r for r in present if r['zero_semantics'] == 'same_day_approval']
    nonzero = [float(r['median_business_days']) for r in present
               if r['median_business_days'] not in ('', None) and float(r['median_business_days']) > 0]
    report['same_day_interval_question'] = dict(
        same_day_cells=len(same_day),
        share_of_present=round(len(same_day) / len(present), 4),
        by_phase=dict(Counter(r['phase'] for r in same_day)),
        midpoint_under_0_to_0p5=0.25, midpoint_under_0_to_1=0.5,
        log_gap_between_conventions=round(math.log(0.5 / 0.25), 3),
        median_of_positive_cells=round(statistics.median(nonzero), 2) if nonzero else None,
        why_it_matters=('The two conventions differ by 0.693 on the log scale, which is larger than '
                        'most effects this study will estimate. With this share of cells affected the '
                        'convention must be a declared sensitivity, run both ways, not a default.'))

    # ---- held-out splits, as frozen in stage 0 ----------------------------
    report['held_out'] = dict(
        authorities_held_out=len({r['stable_owner_id'] for r in present if r['holdout_authority'] == 'True'}),
        authorities_total=len({r['stable_owner_id'] for r in present}),
        cells_held_out_by_authority=sum(1 for r in present if r['holdout_authority'] == 'True'),
        cells_held_out_forward_year=sum(1 for r in present if r['holdout_forward_year'] == 'True'),
        note='Assigned by the frozen rule in estimands_frozen_v1.json, not by inspection.')

    # ---- gates ------------------------------------------------------------
    report['gates'] = dict(
        gate_1_authority_separable=report['design_rank']['separable'],
        gate_2_provenance_reported=True,
        gate_2_exceeds_quarter_on_one_source_row=report['provenance']['exceeds_threshold'],
        estimand_E2_survives=report['elasticity_kill_criterion']['estimand_E2_survives'],
        stage_A_clears=bool(report['design_rank']['separable']))

    pathlib.Path(args.out).write_text(json.dumps(report, indent=1))
    c, d = report['coverage'], report['design_rank']
    print('present cells %d of %d slots | authority-level cells %d'
          % (c['present_cells'], c['slots'], report['authority_level_cells']))
    print('design: %d observations, %d columns, rank %d, deficiency %d -> separable=%s'
          % (d['observations'], d['columns'], d['rank'], d['deficiency'], d['separable']))
    print('provenance: %.1f%% of cells rest on one source row (gate 25%%) -> exceeds=%s'
          % (100 * report['provenance']['share_on_one_source_row'], report['provenance']['exceeds_threshold']))
    print('usable years at >=5 installs: %d authorities with 4+ years (kill threshold 200) -> E2 survives=%s'
          % (best, report['elasticity_kill_criterion']['estimand_E2_survives']))
    v = report['within_authority_volume_variation']
    print('within-authority volume swing: median %sx over %s strata'
          % (v['max_over_min_median'], v['strata_with_4_or_more_years_at_5_installs']))
    print('reported zeros: %d (%s)' % (report['reported_zeros']['total'],
                                       report['reported_zeros']['by_semantics']))
    print('same-day cells: %d (%.1f%% of present)'
          % (report['same_day_interval_question']['same_day_cells'],
             100 * report['same_day_interval_question']['share_of_present']))
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
