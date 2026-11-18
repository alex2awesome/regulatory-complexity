#!/usr/bin/env python3
"""Stage A of the solar leg: build the tidy panel. READ-ONLY on all inputs.

Follows `docs/2026-09-20-solar-leg-plan-for-claude.md` stage A exactly.

Starts from Codex's corrected owner-consolidated coverage matrix rather than the
raw long CSV, because plan section 2c established that the two interconnection
phases are utility-level values repeated once per served authority (identical in
100% of multi-authority strata). Rebuilding from the raw rows would double count.

The raw CSV is read for two things only, neither of which the coverage matrix
carries: the installation count in each cell, and which utility serves an
authority. Installation counts enter as an EXPOSURE and as an upper BOUND on the
unknown denominator. They are never the sample size behind a median; the source
packet's `not_established_by_joined_installs_count` disposition is carried through
to every row.

    python3 -m pipeline.procbench.solar_panel.build_panel
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import unicodedata
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
COVERAGE = ROOT / 'runs/three_family_20260920/solar_full_panel_admission_v1/full_owner_phase_stratum_coverage.csv'
RAW = ROOT / 'runs/rw_parse_20260918/solar_permit/source/solartrace_dataset_2025-09-09__ahj_utility_timelines__ca_long.csv'
COVARIATES = ROOT / 'corpus/counties/ca_counties_covariates.csv'
SRC = ROOT / 'runs/rw_parse_20260918/solar_permit/source'
AHJ_REQS = SRC / 'solartrace_dataset_2025-09-09__ahj_permits_reqs.csv'
UTIL_REQS = SRC / 'solartrace_dataset_2025-09-09__utility_ix_reqs.csv'
INFORMATION = SRC / 'solartrace_dataset_2025-09-09__information.csv'

# The source's own variable descriptions, read from its information sheet. These
# settle three questions the plan left open and are recorded per cell so no
# downstream step has to guess an endpoint.
PHASE_DEFINITIONS = {
    'permit_review': ('Median business days between first permit submission to the AHJ and final '
                      'permit approval. Permits that require changes and resubmission are counted '
                      'from the original submittal date. Same-day approvals are reported as 0 days. '
                      'A minimum of 10 projects at that AHJ for that year were required.'),
    'inspection': ('Median business days between inspection complete and last passed inspection. '
                   'A minimum of 10 projects at that AHJ were required. NOTE: as written this '
                   'endpoint pair is self-referential; the dataset\'s own quartile sheet defines the '
                   'inspection phase as install complete to last completed inspection. The endpoint '
                   'is therefore AMBIGUOUS IN THE SOURCE and must not be silently resolved.'),
    'pre_install_ix': ('Median business days between pre-install interconnection application to the '
                       'utility (approval to build) and approval. Not all utilities require '
                       'pre-install approval; projects at utilities without an ATB requirement were '
                       'set to 0 days if no data were provided. Minimum 10 projects at that utility.'),
    'final_ix_pto': ('Median business days between final interconnection request to the utility and '
                     'granting of permission to operate. Minimum 10 projects at that utility.'),
}
DENOMINATOR_FLOOR = 10
CROSSWALK_FILES = ['corpus/counties/apr_permit_timing.csv',
                   'corpus/counties/apr_applicant_clock.csv',
                   'corpus/counties/apr_discretion_by_jurisdiction.csv']
OUT = ROOT / 'runs/solar_panel_20260920'
# The panel now spans the full source range. The 2017-2022 sub-window is where
# the load-elasticity estimand is identified, because the April 2023 tariff
# change and the September 2023/2024 automation deadlines sit outside it. The
# later years are retained for one reason: 119 of the 139 solar forum documents
# post-date 2022, so a reporting-offset comparison has no contemporaneous
# administrative counterpart inside the sub-window. Each row carries a flag.
WINDOW = [str(y) for y in range(2017, 2025)]
ELASTICITY_WINDOW = [str(y) for y in range(2017, 2023)]
HOLDOUT_SALT = 'solar-panel-holdout-2026-09-20'

# Naming variants the housing crosswalk spells differently. Each is the SAME
# place under two spellings, verified against the crosswalk's own key list; none
# is a guess about which county a place sits in. Places still unmatched after
# this are carried as missing, never assigned.
NAME_ALIASES = {
    'EL PASO DE ROBLES (PASO ROBLES)': 'PASO ROBLES',
    'SAN BUENAVENTURA (VENTURA)': 'VENTURA',
    'ANGELS': 'ANGELS CAMP',
}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _accentless(name: str) -> str:
    text = unicodedata.normalize('NFKD', name)
    return ''.join(c for c in text if not unicodedata.combining(c)).strip().upper()


def fold_crosswalk(name: str) -> str:
    """Crosswalk keys carry no place-type suffix, so only accents are folded."""
    return _accentless(name)


def fold(name: str) -> str:
    """Panel owner names carry a place-type suffix; strip exactly one.

    "Daly City city" must become "DALY CITY", not "DALY", so the suffix is
    removed from the panel side only and never from the crosswalk side.
    """
    text = re.sub(r'\s+(city|town|CDP)$', '', _accentless(name), flags=re.I).strip()
    return NAME_ALIASES.get(text, text)


def held_out(owner_id: str) -> bool:
    digest = hashlib.sha256((owner_id + '|' + HOLDOUT_SALT).encode()).digest()
    return int.from_bytes(digest, 'big') % 5 == 0


def load_crosswalk():
    """jurisdiction -> county, from the housing annual-progress-report tables."""
    crosswalk = {}
    for name in CROSSWALK_FILES:
        path = ROOT / name
        if not path.exists():
            continue
        with path.open(encoding='utf-8', errors='replace') as handle:
            for row in csv.DictReader(handle):
                j, c = (row.get('jurisdiction') or '').strip(), (row.get('county') or '').strip()
                if j and c:
                    crosswalk.setdefault(fold_crosswalk(j), c)
    return crosswalk


def load_covariates():
    rows = {}
    with COVARIATES.open(encoding='utf-8', errors='replace') as handle:
        for row in csv.DictReader(handle):
            rows[row['county'].strip().upper()] = row
    return rows


def load_requirements():
    """Per-authority requirement flags and per-utility interconnection rules.

    These carry the step-count and money channels the timing panel lacks, and the
    approval-to-build flag is what resolves the ambiguous pre-install zeros.
    """
    ahj = {}
    with AHJ_REQS.open(encoding='utf-8', errors='replace') as handle:
        for row in csv.DictReader(handle):
            if row.get('state') != 'CA':
                continue
            ahj[row['geo_id']] = row
            ahj.setdefault('name:' + row['ahj'], row)
    util = {}
    with UTIL_REQS.open(encoding='utf-8', errors='replace') as handle:
        for row in csv.DictReader(handle):
            if row.get('State') != 'CA':
                continue
            util[row['EIA ID']] = row
            util['name:' + row['Utility']] = row
    return ahj, util


def clean(value):
    value = (value or '').strip()
    return '' if value in ('NA', 'nan', 'None') else value


def load_raw():
    """Installs per (geo_id, year, size, tech) and serving utilities per geo_id."""
    installs, utilities, by_name = defaultdict(int), defaultdict(Counter), defaultdict(int)
    with RAW.open(encoding='utf-8', errors='replace') as handle:
        for row in csv.DictReader(handle):
            key = (row['geo_id'], row['year'], row['size_class'], row['technology'])
            if row['metric'] == 'Installs':
                try:
                    value = int(row['value'])
                except ValueError:
                    continue
                installs[key] += value
                by_name[(row['ahj'], row['year'], row['size_class'], row['technology'])] += value
                utilities[row['geo_id']][row['utility']] += value
            else:
                utilities[row['geo_id']].setdefault(row['utility'], 0)
    return installs, utilities, by_name


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT))
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    crosswalk, covariates = load_crosswalk(), load_covariates()
    installs, utilities, installs_by_name = load_raw()
    ahj_reqs, util_reqs = load_requirements()

    panel, unmatched_county, skipped = [], Counter(), Counter()
    with COVERAGE.open(encoding='utf-8', errors='replace') as handle:
        for row in csv.DictReader(handle):
            # DEFECT IN THE SOURCE MATRIX, handled here and reported, not edited
            # there: for utility-scoped owners the `state` column carries the
            # EIA utility id (e.g. "16609") rather than a state code. Filtering
            # on state alone silently drops every utility-phase row. The source
            # CSV is California-only, so utility-scoped rows are admitted on
            # their scope and authority-scoped rows still require CA.
            if row['owner_scope'] == 'ahj' and row['state'] != 'CA':
                skipped['ahj_not_california'] += 1
                continue
            if row['owner_scope'] != 'ahj':
                skipped['utility_scope_admitted_on_scope_not_state'] += 1
            if row['year'] not in WINDOW:
                skipped['outside_window'] += 1
                continue
            try:
                native = json.loads(row['owner_native_id']) if row['owner_native_id'] else []
            except json.JSONDecodeError:
                native = []
            if not isinstance(native, list):
                native = [native]
            stratum = (row['year'], row['size_class'], row['technology'])
            volume = sum(installs.get((g,) + stratum, 0) for g in native)
            if not native:
                volume = installs_by_name.get((row['owner_name'],) + stratum, 0)
            serving = Counter()
            for g in native:
                serving.update(utilities.get(g, {}))
            # County only for authority-scoped owners; a utility is not in a county.
            county = county_pop = rurality = ''
            if row['owner_kind'] == 'ahj':
                name = row['owner_name']
                if name.endswith('County'):
                    county = name[:-len('County')].strip()
                else:
                    county = crosswalk.get(fold(name), '')
                if not county:
                    unmatched_county[name] += 1
                cov = covariates.get(county.upper(), {}) if county else {}
                county_pop = cov.get('pop_2023', '')
                rurality = cov.get('rucc_2023', '')
            req = {}
            for g in native:
                if g in ahj_reqs:
                    req = ahj_reqs[g]
                    break
            if not req:
                req = ahj_reqs.get('name:' + row['owner_name'], {})
            dominant = (serving.most_common(1)[0][0] if serving and serving.most_common(1)[0][1] else '')
            urow = util_reqs.get('name:' + dominant, {}) if dominant else {}
            if row['owner_kind'] != 'ahj':
                urow = util_reqs.get('name:' + row['owner_name'], {}) or urow
            atb = clean(urow.get('Approval to Build required from utility before install', ''))
            # A pre-install zero at a utility that requires no approval to build is
            # a step that does not exist, not a step that took no time. The source
            # says so directly; this resolves the hold rather than guessing.
            zero_resolved = ''
            if row['phase'] == 'pre_install_ix' and row['reported_zero'] == 'true':
                zero_resolved = ('no_atb_requirement_step_absent' if atb == 'No'
                                 else 'atb_required_zero_is_a_measured_duration' if atb == 'Yes'
                                 else 'unresolved_atb_requirement_unknown')
            panel.append(dict(
                stable_owner_id=row['stable_owner_id'], owner_name=row['owner_name'],
                owner_kind=row['owner_kind'], owner_scope=row['owner_scope'],
                owner_identified=row['owner_identified'], geo_ids=';'.join(str(g) for g in native),
                phase=row['phase'], year=row['year'], size_class=row['size_class'],
                technology=row['technology'], present=row['present'],
                disposition=row['disposition'], metric=row['metric'],
                median_business_days=row['value'], unit=row['unit'],
                reported_zero=row['reported_zero'], zero_semantics=row['zero_semantics'],
                sample_size_status=row['sample_size_status'],
                source_row_count=row['source_row_count'],
                installs_same_cell=volume,
                installs_role='exposure_and_upper_bound_on_unknown_denominator_never_sample_size',
                serving_utilities=';'.join(sorted(u for u in serving if u)),
                dominant_utility=(serving.most_common(1)[0][0] if serving and serving.most_common(1)[0][1] else ''),
                n_serving_utilities=len([u for u in serving if u]),
                county=county, county_pop_2023=county_pop, county_rucc_2023=rurality,
                holdout_authority=held_out(row['stable_owner_id']),
                holdout_forward_year=(row['year'] == '2022'),
                phase_level=('authority' if row['phase'] in ('permit_review', 'inspection') else 'utility'),
                in_elasticity_window=(row['year'] in ELASTICITY_WINDOW),
                phase_definition=PHASE_DEFINITIONS.get(row['phase'], ''),
                denominator_floor=DENOMINATOR_FLOOR,
                pre_install_zero_resolution=zero_resolved,
                utility_atb_required=atb,
                utility_response_time_requirement=clean(urow.get('IX Application Response Time Requirement', '')),
                req_number_of_inspections=clean(req.get('Number of Inspections Required', '')),
                req_median_permit_cost=clean(req.get('Median Permit Cost', '')),
                req_structural_review=clean(req.get('Structural Review Required', '')),
                req_electrical_review=clean(req.get('Electrical Review Required', '')),
                req_rough_in_inspection=clean(req.get('Rough-In Inspection Required', '')),
                req_third_party_review=clean(req.get('Third-Party Permit Review', '')),
                req_solsmart=clean(req.get('SolSmart Awardee', '')),
                req_solsmart_3day_target=clean(req.get('SolSmart 3-Day Permit Target', '')),
                req_online_permitting_2019=clean(req.get('Online Permitting in 2019', '')),
                req_online_permitting_2022=clean(req.get('Online Permitting - 2022', '')),
                req_online_instant_2022=clean(req.get('Online Instant Permitting - 2022', '')),
                req_same_day_in_person=clean(req.get('Same Day In-Person Permitting Available', ''))))

    fields = list(panel[0].keys())
    target = out / 'panel_v1.csv'
    with target.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(panel)

    manifest = dict(
        schema_version='solar-panel-build/1', stage='A', plan='docs/2026-09-20-solar-leg-plan-for-claude.md',
        estimands='runs/solar_panel_20260920/estimands_frozen_v1.json',
        window=WINDOW, elasticity_window=ELASTICITY_WINDOW, rows=len(panel), present=sum(1 for r in panel if r['present'] == 'true'),
        inputs={
            'coverage_matrix': dict(path=str(COVERAGE.relative_to(ROOT)), sha256=sha(COVERAGE)),
            'raw_long_csv': dict(path=str(RAW.relative_to(ROOT)), sha256=sha(RAW),
                                 used_for='installation counts and serving utilities only'),
            'county_covariates': dict(path=str(COVARIATES.relative_to(ROOT)), sha256=sha(COVARIATES)),
            'ahj_requirements': dict(path=str(AHJ_REQS.relative_to(ROOT)), sha256=sha(AHJ_REQS)),
            'utility_requirements': dict(path=str(UTIL_REQS.relative_to(ROOT)), sha256=sha(UTIL_REQS)),
            'information_sheet': dict(path=str(INFORMATION.relative_to(ROOT)), sha256=sha(INFORMATION)),
            'crosswalk_files': [n for n in CROSSWALK_FILES if (ROOT / n).exists()]},
        county_crosswalk_unmatched=dict(unmatched_county),
        skipped_rows=dict(skipped),
        holdout=dict(salt=HOLDOUT_SALT, rule='sha256(owner_id|salt) mod 5 == 0',
                     authorities_held_out=len({r['stable_owner_id'] for r in panel if r['holdout_authority']}),
                     authorities_total=len({r['stable_owner_id'] for r in panel})),
        declarations=dict(reads_benchmark_truth=False, network_used=False, model_calls=0,
                          modifies_inputs=False,
                          installs_are_not_sample_size=True),
        source_stated_denominator_floor=DENOMINATOR_FLOOR,
        phase_definitions=PHASE_DEFINITIONS)
    (out / 'panel_build_manifest.json').write_text(json.dumps(manifest, indent=1))
    print('wrote %s  rows=%d present=%d' % (target, len(panel), manifest['present']))
    print('authorities: %d, held out: %d' % (manifest['holdout']['authorities_total'],
                                             manifest['holdout']['authorities_held_out']))
    if unmatched_county:
        print('county unmatched owners: %d  %s' % (len(unmatched_county), list(unmatched_county)[:6]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
