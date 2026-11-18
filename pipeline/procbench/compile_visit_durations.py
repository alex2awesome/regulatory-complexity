"""Compile quote-checked source claims to the joint visit model's observations.

This is the claim boundary of the source compiler, not a complete text-to-route
pipeline. Every input claim receives an explicit disposition. Unknown operators,
unsupported populations and incomplete alternative sets are never silently dropped
or coerced into more convenient measurements. No truth or fitted outputs are read.

Durations are the ambiguous case and keep requiring their semantic audit. Fees,
applicant/agency effort and counts do not: a stated dollar amount has one
reading. Those channels are compiled only when explicitly requested, so every
compilation made before they existed reproduces byte for byte without them.
"""
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import json
import math
import pathlib

from .audit_burden_counts import validate_counts
from .audit_measurement_semantics import eligible, validate_audit
from .audit_visit_observations import STARTS, ENDS, validate_visit_audit
from .audit_visit_hypotheses import fully_specified, validate_hypotheses
from .burden_channels import (BURDEN_CHANNELS, EFFORT_BASES, EFFORT_UNIT_ASSUMPTION,
                              MONEY_REPORT_NOTE, ROUNDING_ASSUMPTION, SOURCE_FAMILY_GROUPINGS,
                              SOURCE_FAMILY_TYPES, document_type,
                              count_compilation, effort_compilation, fee_compilation,
                              ineligible_reasons, source_family)
from .evidence_contract import normalized_quote, validate
from .infra.manifest import digest, write
from .compact_visit_trace import CLOCK_EVENTS
from .cohort_quantiles import QUANTILE_METHODS, cohort_report_observations
from .decision_scope_binding import bind_decision_contexts
from .semantic_calibration import operator_weights as calibrated_operator_weights
from .typical_range_reports import validate_typical_range_model
from .effective_evidence import evidence_digest, materialize as materialize_review
from .source_precision import (FIXED_KIND, attach_precision_annotation,
                               precision_annotation, resolved_precision_annotation,
                               validate_source_type_report_scales)


EVENTS = {'process_start', 'first_submission', 'first_complete_submission',
          'initial_decision', 'final_decision', 'legal_closeout', 'end_of_modeled_work'}
# Recognize the complete source vocabulary; recognizing an event is not claiming
# the trace implements it. Aliases/unsupported events are explicit policy items.
AUDIT_EVENTS = set(STARTS) | set(ENDS)
STATISTICS = {'individual_completion': 'individual', 'individual_censored': 'individual',
              'population_mean': 'mean', 'population_median': 'median', 'population_p90': 'p90'}
UNITS = {'minutes': 1 / 1440, 'hours': 1 / 24, 'calendar_days': 1.,
         'weeks': 7., 'months': 365.25 / 12}


def operator_reasons(operator, mapping):
    basis = operator['basis']
    reasons = []
    if operator.get('censoring') == 'unresolved':
        reasons.append('unresolved_censoring')
    if basis == 'whole_case_clock':
        if operator['start'] not in EVENTS or operator['end'] not in EVENTS:
            reasons.append('unmodeled_or_unknown_clock_boundary')
    elif basis in {'single_visit_cycle', 'sum_visit_cycles', 'first_to_last_activity_span',
                   'wait_elapsed', 'service_elapsed'}:
        if mapping != 'supported' or not operator['activity_ids']:
            reasons.append('unresolved_activity_linkage')
        if basis in {'wait_elapsed', 'service_elapsed'}:
            supported_bounds = ((operator['start'] in {'appointment_request', 'single_visit_start'}
                                 and operator['end'] == 'service_start') if basis == 'wait_elapsed' else
                                (operator['start'] == 'service_start'
                                 and operator['end'] in {'service_end', 'single_visit_end'}))
            if not supported_bounds:
                reasons.append('unknown_or_partial_within_visit_phase_boundary')
            if operator['visits'] in {'first', 'last', 'one_unspecified'}:
                if len(operator['activity_ids']) != 1:
                    reasons.append('single_visit_phase_requires_one_operation')
            elif operator['visits'] != 'all_in_completed_case':
                reasons.append('partial_or_unknown_visit_coverage')
        elif basis == 'single_visit_cycle':
            if len(operator['activity_ids']) != 1 and operator.get('activity_selection') != 'first_present':
                reasons.append('single_visit_requires_one_operation')
            if operator['start'] == 'other_milestone' or operator['end'] == 'other_milestone':
                reasons.append('partial_activity_boundary_is_not_a_complete_cycle')
        elif operator['visits'] != 'all_in_completed_case':
            reasons.append('partial_or_unknown_visit_coverage')
        elif operator['start'] == 'other_milestone' or operator['end'] == 'other_milestone':
            reasons.append('partial_activity_boundary_is_not_a_complete_span_or_sum')
    elif basis == 'unmodeled_duration':
        pass  # Explicit normalized residual; not a process-duration operator.
    else:
        reasons.append('unmodeled_duration_basis:' + basis)
    return reasons


def report_interval(measurement, semantic, censoring, calendar=None, rounding_fallback=None):
    """Calendar intervals in the source's numerical precision, not fake point data.

    Business-day calendars need an explicit calendar model; this compiler does not
    silently assume a five-day week or the absence of holidays. A 'month' uses the
    declared average calendar-month conversion, retained in the output assumptions.
    """
    units = dict(UNITS)
    if calendar:
        units['business_days'] = calendar['calendar_days_per_business_day']
    if measurement['unit'] not in units:
        return None, ['unmodeled_calendar:' + measurement['unit']]
    factor = units[measurement['unit']]
    lo, hi = measurement['lower'], measurement['upper']
    if lo is None and hi is None:
        precision = semantic['original_precision_unit']
        if precision == 'unspecified' and rounding_fallback == 'reported_unit':
            precision = measurement['unit']
        if precision not in units:
            return None, ['unresolved_or_unsupported_rounding_precision']
        value, half = measurement['value'] * factor, .5 * units[precision]
        lo, hi = max(0., value - half), value + half
    else:
        lo = 0. if lo is None else lo * factor
        hi = None if hi is None else hi * factor
    if censoring == 'right':
        hi = None
    elif censoring == 'left':
        lo = 0.
    if hi is not None and hi <= lo:
        return None, ['zero_width_continuous_interval']
    return (lo, hi), []


def hypothesis_options(row, prior):
    """Declared prior over bases/readings, with positive unmodeled residual mass."""
    required = {'residual_weight', 'unmodeled_median_days', 'unmodeled_log_scale', 'allocation'}
    if set(prior) != required or prior['allocation'] != 'uniform_basis_then_reading':
        raise ValueError('Hypothesis prior needs explicit residual distribution and allocation')
    for key in required - {'allocation'}:
        value = prior[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Hypothesis prior numbers must be finite and positive')
    residual = prior['residual_weight']
    if residual >= 1:
        raise ValueError('Residual weight must lie strictly between zero and one')
    operators = [dict(h['operator']) for h in row['hypotheses']]
    if not operators:
        raise ValueError('A residual alone is not informative source compilation')
    families = Counter(op['basis'] for op in operators)
    weights = [(1-residual) / len(families) / families[op['basis']] for op in operators]
    operators.append(dict(basis='unmodeled_duration', median_days=prior['unmodeled_median_days'],
                          log_scale=prior['unmodeled_log_scale']))
    return operators, weights + [residual]


def validate_source_bindings(bindings, evidence, visit_audit, semantic_audit, documents):
    """Check separate quoted source-to-model bindings; never rewrite old audits.

    These are reviewable semantic judgments and declared selection assumptions,
    not measured calibration or permission to change a value, clock or identity.
    """
    if bindings is None:
        return {}
    if (set(bindings) != {'schema_version', 'program_id', 'measurements'} or
            bindings['schema_version'] != 'joint-visit-source-bindings/1' or
            bindings['program_id'] != evidence['program_id']):
        raise ValueError('Invalid source-binding contract or program')
    measurements = {m['id']: m for m in eligible(evidence)}
    visits = {r['measurement_id']: r for r in visit_audit['measurements']}
    semantics = {r['measurement_id']: r for r in semantic_audit['measurements']}
    texts = {d['id']: normalized_quote(d['text']) for d in documents}
    result = {}
    for row in bindings['measurements']:
        if set(row) != {'measurement_id', 'population_condition', 'operator_selections', 'evidence', 'assumptions'}:
            raise ValueError('Source bindings require explicit fields and selection assumptions')
        mid = row['measurement_id']
        if mid not in measurements or mid in result:
            raise ValueError('Source bindings require distinct eligible measurements')
        if not row['evidence'] or not row['assumptions'] or any(
                not isinstance(a, str) or not a.strip() for a in row['assumptions']):
            raise ValueError('Source bindings require quotes and nonempty assumptions')
        for ref in row['evidence']:
            quote = normalized_quote(ref['quote'])
            if not quote or quote not in texts.get(ref['doc_id'], ''):
                raise ValueError('Nonverbatim source-binding quotation')
        parent = visits[mid]
        condition = row['population_condition']
        if condition is not None:
            if (condition != 'first_visit' or measurements[mid]['case_id'] is not None or
                    semantics[mid]['population_scope'] not in {'all_cases', 'selected_cohort'} or
                    semantics[mid]['statistic_interpretation'] not in
                    {'population_mean', 'population_median', 'population_p90', 'typical_range'} or
                    any(op['basis'] != 'single_visit_cycle' or op['visits'] != 'first'
                        or op['censoring'] != 'none' for op in parent['operators'])):
                raise ValueError('First-visit binding cannot replace an unresolved statistic, clock or visit scope')
        seen = set()
        for selection in row['operator_selections']:
            if set(selection) != {'operator_index', 'mode'}:
                raise ValueError('An activity-union binding needs its unchanged parent operator index')
            index = selection['operator_index']
            if (isinstance(index, bool) or not isinstance(index, int) or index < 0 or
                    index >= len(parent['operators']) or index in seen):
                raise ValueError('Invalid/repeated source-binding operator index')
            seen.add(index)
            op = parent['operators'][index]
            if (selection['mode'] != 'first_present' or parent['activity_mapping'] != 'supported'
                    or op['basis'] != 'single_visit_cycle' or op['visits'] != 'first'
                    or len(op['activity_ids']) < 2):
                raise ValueError('An activity union must preserve a supported first-cycle multi-activity reference')
        result[mid] = row
    return result


def combine_report_groups(observations, dispositions, audit, evidence, documents):
    """Retain every claim but give identified repeated/disjunctive wording one factor.

    A group is a quoted semantic judgment, never inferred from equal numbers.
    Distinct cases and distinct components of one case must not be collapsed.
    Unimplemented cross-operator dependencies fail explicitly rather than being
    silently treated as independent or used to overwrite a factual audit.
    """
    if audit is None:
        return observations
    if (set(audit) != {'schema_version', 'program_id', 'groups'} or
            audit['schema_version'] != 'joint-visit-report-groups/1' or
            audit['program_id'] != evidence['program_id']):
        raise ValueError('Invalid report-group contract or program')
    original = {m['id']: m for m in evidence['measurements']}
    compiled = {o['id']: o for o in observations}
    disposition = {d['measurement_id']: d for d in dispositions}
    texts = {d['id']: normalized_quote(d['text']) for d in documents}
    consumed, names, replacements = set(), set(), {}
    for group in audit['groups']:
        if set(group) != {'id', 'measurement_ids', 'relationship', 'representative_id', 'evidence', 'assumptions'}:
            raise ValueError('Report groups need explicit identities, relationship, quotes and assumptions')
        mids, ident = group['measurement_ids'], group['id']
        if (not isinstance(ident, str) or not ident or ident in names or not isinstance(mids,list)
                or len(mids)<2 or len(set(mids))!=len(mids) or consumed & set(mids)
                or not set(mids)<=compiled.keys()):
            raise ValueError('Report groups require distinct compiled, non-overlapping claim IDs')
        if not group['evidence'] or not group['assumptions'] or any(
                not isinstance(a,str) or not a.strip() for a in group['assumptions']):
            raise ValueError('Report grouping requires source support and explicit assumptions')
        for ref in group['evidence']:
            quote=normalized_quote(ref['quote'])
            if not quote or quote not in texts.get(ref['doc_id'],''):
                raise ValueError('Nonverbatim report-group quotation')
        if len({original[mid]['case_id'] for mid in mids})!=1:
            raise ValueError('Distinct cases cannot be collapsed into one report')
        members=[compiled[mid] for mid in mids]
        def signature(o):
            return dict(case_id=o['case_id'],source_family=o['source_family'],sampling=o['sampling'],
                statistic=o['statistic'],operators=[{k:v for k,v in op.items() if k!='notes'} for op in o['operators']],
                weights=o['operator_weights'],population_condition=o.get('population_condition'),
                population_path_scope=o.get('population_path_scope'),sample_size=o.get('sample_size'),
                typical_range_model=o.get('typical_range_model'),
                source_type=o.get('source_type'),report_log_scale=o.get('report_log_scale'),
                report_scale_basis=o.get('provenance',{}).get('report_scale_basis'),
                cohort_id=o.get('cohort_id'), decision_context_binding=o.get('decision_context_binding'))
        if any(signature(o)!=signature(members[0]) for o in members[1:]):
            raise ValueError('Same-report claims need reconciled operator/source contracts before grouping: '+ident)
        if group['relationship']=='disjunctive_report':
            if group['representative_id'] is not None:
                raise ValueError('A disjunction retains all intervals, not a chosen representative')
            intervals=sorted([[o['lower'],o['upper']] for o in members],key=lambda x:x[0])
            merged=[]
            for lo,hi in intervals:
                if not merged or (merged[-1][1] is not None and lo>merged[-1][1]):
                    merged.append([lo,hi])
                elif merged[-1][1] is None or hi is None:
                    merged[-1][1]=None
                else:
                    merged[-1][1]=max(merged[-1][1],hi)
            joined=copy.deepcopy(members[0])
            joined.update(lower=merged[0][0],upper=merged[-1][1],report_intervals=merged)
        elif group['relationship']=='repeated_wording':
            representative=group['representative_id']
            if representative not in mids:
                raise ValueError('Repeated wording needs an explicitly identified representative claim')
            joined=copy.deepcopy(compiled[representative])
            upper=math.inf if joined['upper'] is None else joined['upper']
            if any(joined['lower']<o['lower'] or upper>(math.inf if o['upper'] is None else o['upper'])
                   for o in members):
                raise ValueError('A repeated-wording representative must satisfy every retained report interval')
        else:
            raise ValueError('Unsupported report-group relationship; same case does not mean same report')
        joined['measurement_ids']=list(mids)
        joined['provenance']['report_group']=copy.deepcopy(group)
        joined['provenance']['source_reports']=copy.deepcopy(members)
        for mid in mids:
            disposition[mid].update(shared_report_group=ident,likelihood_id=joined['id'])
        replacements[mids[0]]=joined
        consumed.update(mids)
        names.add(ident)
    return [replacements[o['id']] if o['id'] in replacements else o
            for o in observations if o['id'] not in consumed or o['id'] in replacements]


def validate_cohort_bindings(audit, evidence, semantic_audit, documents):
    """No n, independence, shared cohort identity or quantile method is inferred."""
    if audit is None:
        return {}
    if (set(audit) != {'schema_version', 'program_id', 'cohorts'}
            or audit['schema_version'] != 'joint-visit-cohort-bindings/1'
            or audit['program_id'] != evidence['program_id']):
        raise ValueError('Invalid finite-cohort source-binding contract')
    measurements = {m['id']:m for m in eligible(evidence)}
    semantics = {r['measurement_id']:r for r in semantic_audit['measurements']}
    texts = {d['id']:normalized_quote(d['text']) for d in documents}
    result, identities, cohorts = {}, set(), set()
    for row in audit['cohorts']:
        if set(row) != {'id', 'cohort_id', 'measurement_ids', 'quantile_method', 'sampling',
                'independent_of_other_evidence', 'conditional_report_independence', 'evidence', 'assumptions'}:
            raise ValueError('Cohort binding requires identities, method, sampling assumptions and quotes')
        mids = row['measurement_ids']
        if (not isinstance(mids,list) or not mids or len(set(mids)) != len(mids)
                or set(mids) & result.keys() or not set(mids) <= measurements.keys()
                or any(not isinstance(row[k],str) or not row[k].strip() for k in ('id','cohort_id'))
                or row['id'] in identities or row['cohort_id'] in cohorts):
            raise ValueError('Cohort bindings must partition distinct eligible measurements into named cohorts')
        members = [measurements[mid] for mid in mids]
        ns = [m['n'] for m in members]
        if (any(isinstance(n,bool) or not isinstance(n,int) or n<1 for n in ns)
                or len(set(ns)) != 1 or any(m['case_id'] is not None for m in members)
                or len({m['source_family'] for m in members}) != 1):
            raise ValueError('Cohort summaries must preserve the same explicit n and source, without case identities')
        if any(semantics[mid]['statistic_interpretation'] not in {'population_median','population_p90'} for mid in mids):
            raise ValueError('A finite cohort binding cannot turn a mean, forecast or typical range into a quantile')
        if (row['quantile_method'] not in QUANTILE_METHODS or row['sampling'] != 'iid_within_declared_population'
                or row['independent_of_other_evidence'] is not True
                or row['conditional_report_independence'] is not True):
            raise ValueError('Explicit quantile method and cohort/report sampling assumptions are required')
        if (not row['evidence'] or not row['assumptions']
                or any(not isinstance(a,str) or not a.strip() for a in row['assumptions'])):
            raise ValueError('Cohort binding requires source support and explicit assumptions')
        for ref in row['evidence']:
            quote = normalized_quote(ref['quote'])
            if (ref['doc_id'] not in {m['doc_id'] for m in members}
                    or not quote or quote not in texts.get(ref['doc_id'],'')):
                raise ValueError('Nonverbatim or unrelated finite-cohort source quotation')
        for mid in mids:
            result[mid] = dict(row, sample_size=ns[0])
        identities.add(row['id'])
        cohorts.add(row['cohort_id'])
    return result


def combine_quantile_cohorts(observations, dispositions, bindings):
    """Move same-cohort summaries into one shared-interpretation likelihood."""
    if not bindings:
        return observations, []
    groups = {row['id']:row for row in bindings.values()}
    consumed, cohorts = set(), []
    dispositions = {r['measurement_id']:r for r in dispositions}
    for binding in groups.values():
        mids = set(binding['measurement_ids'])
        members = [o for o in observations if mids & set(o.get('measurement_ids',[o['id']]))]
        represented = {mid for o in members for mid in o.get('measurement_ids',[o['id']])}
        if represented != mids:
            raise ValueError('Joint cohort needs every member numeric report, without cross-cohort grouping')
        def signature(o):
            return {k:([{a:b for a,b in op.items() if a!='notes'} for op in o[k]] if k=='operators' else o.get(k))
                for k in ('operators','operator_weights','source_family','population_condition','population_path_scope')}
        precision_signatures=[(o.get('source_type'),o.get('report_log_scale'),
            o.get('provenance',{}).get('report_scale_basis')) for o in members]
        if any(value != precision_signatures[0] for value in precision_signatures[1:]):
            raise ValueError('Same-cohort reports require one resolved source type and measurement scale')
        if any(signature(o) != signature(members[0]) for o in members):
            raise ValueError('Same-cohort clocks/interpretations must be reconciled jointly before compilation')
        first = members[0]
        cohort = {k:binding[k] for k in ('id','cohort_id','sample_size','quantile_method','sampling',
                    'independent_of_other_evidence','conditional_report_independence')}
        cohort.update({k:copy.deepcopy(first[k]) for k in
            ('source_family','operators','operator_weights','population_condition','population_path_scope') if k in first})
        cohort.update({k:copy.deepcopy(first[k]) for k in ('source_type','report_log_scale') if k in first})
        cohort['reports'] = []
        for observation in members:
            report = {k:copy.deepcopy(observation[k]) for k in
                ('id','lower','upper','report_intervals','measurement_ids','provenance') if k in observation}
            report.get('provenance',{}).pop('report_scale_basis',None)
            report['statistic'] = STATISTICS[observation['provenance']['original_statistic']]
            cohort['reports'].append(report)
            consumed.add(observation['id'])
        cohort['provenance'] = dict(source_binding=copy.deepcopy(binding),
            shared_interpretation=True, cohort_sampling_uncertainty_integrated=True)
        if 'report_scale_basis' in first.get('provenance',{}):
            cohort['provenance']['report_scale_basis']=copy.deepcopy(
                first['provenance']['report_scale_basis'])
        cohort_report_observations(cohort)
        cohorts.append(cohort)
        for mid in mids:
            dispositions[mid].update(shared_cohort=binding['cohort_id'],likelihood_id='quantile_cohort:'+binding['id'])
    return [o for o in observations if o['id'] not in consumed], cohorts


def source_precision_report(declaration, observations, quantile_cohorts):
    """Compiler coverage for an opt-in fixed declaration, never learned trust."""
    if declaration is None:
        return None
    rows={source_type:dict(report_log_scale=float(spec['report_log_scale']),
            calibration_id=spec['calibration_id'],
            calibration_provenance='declared_reference_unverified',
            ordinary_factors=0,ordinary_claim_rows=0,finite_quantile_cohorts=0,
            finite_quantile_report_rows=0,unknown_n_floor_eligible_factors=0)
          for source_type,spec in sorted(declaration['elapsed'].items())}
    fallback=dict(source_type_not_declared_factors=0,source_type_unresolved_factors=0,
                  unknown_n_floor_eligible_factors=0)
    used=set()
    for observation in observations:
        annotation=precision_annotation(observation)
        if annotation is None:
            continue
        claims=len(observation.get('measurement_ids',[observation['id']]))
        if annotation['kind']==FIXED_KIND:
            used.add(annotation['source_type'])
            row=rows[annotation['source_type']]
            row['ordinary_factors']+=1
            row['ordinary_claim_rows']+=claims
            row['unknown_n_floor_eligible_factors']+=int(observation['case_id'] is None)
        else:
            fallback[annotation['reason']+'_factors']+=1
            fallback['unknown_n_floor_eligible_factors']+=int(observation['case_id'] is None)
    for cohort in quantile_cohorts:
        annotation=precision_annotation(cohort)
        if annotation is None:
            continue
        if annotation['kind']==FIXED_KIND:
            used.add(annotation['source_type'])
            row=rows[annotation['source_type']]
            row['finite_quantile_cohorts']+=1
            row['finite_quantile_report_rows']+=len(cohort['reports'])
        else:
            fallback[annotation['reason']+'_factors']+=1
    return dict(schema_version=declaration['schema_version'],fallback=declaration['fallback'],
        fixed_declared_scales_by_type=rows,unused_declared_source_types=sorted(set(rows)-used),
        fallback_counts=fallback,learned_coordinates=0,
        calibration_qualification=('calibration_id is a declared reference only; this compiler did not '
            'hash-review or empirically verify the referenced calibration.'),
        separation_qualification=('The fixed scale changes elapsed reporting error only. Cohort sampling, '
            'population spread, source bias, contamination and selection remain separate.'))


def burden_observation(ident, case_id, family, ascertainment, row, channel, provenance):
    """One individual non-duration report: money, effort hours or a count.

    None of these has a residual alternative. A fee total, an hours total and a
    count are in their own units, so an unmodeled-duration reference cannot be
    mixed into them the way it can into an ambiguous duration reading; a claim
    that does not resolve keeps a disposition instead of a widened interval.
    """
    return dict(id=ident, case_id=case_id, source_family=family, sampling=ascertainment,
                statistic='individual', lower=row['interval'][0], upper=row['interval'][1],
                operators=[dict(row['operator'])], operator_weights=[1.],
                provenance=dict(provenance, channel=channel, units=row['units'],
                                residual_only=False, prior_origin='unambiguous_non_duration_claim',
                                unresolved_reasons=[]))


def compile_burden_claim(m, context, channels, ascertainment, family_of):
    """Disposition (and any observation) for a claim outside the elapsed audit.

    Returns the historical single-bucket disposition untouched when no burden
    channel is enabled. A published fee with no case is not an observation of
    the process: it is an input to the route, recorded for the bridge to read.
    """
    mid, metric = m['id'], m['metric']
    if 'fee' in channels and metric == 'fee':
        channel, row = 'fee', fee_compilation(m, context)
    elif 'effort' in channels and metric in EFFORT_BASES:
        channel, row = 'effort', effort_compilation(m, context)
    else:
        return dict(measurement_id=mid, status='outside_elapsed_compiler',
                    reasons=ineligible_reasons(m, context, channels), source=m), None
    if row['kind'] == 'route_input':
        return dict(measurement_id=mid, status='route_input_not_observation', reasons=row['reasons'],
                    source=m, channel=channel, route_input=row['route_input']), None
    reasons = list(row['reasons'])
    if row['kind'] == 'observation' and ascertainment is None:
        # A fee or effort report is still one person's report from a forum thread.
        reasons.append('case_sampling_assumption_not_declared')
    if reasons:
        return dict(measurement_id=mid, status='requires_model_extension_or_explicit_assumption',
                    reasons=sorted(set(reasons)), source=m, channel=channel), None
    provenance = dict(doc_id=m['doc_id'], quote=m['quote'], original_value=m['value'],
                      original_lower=m['lower'], original_upper=m['upper'], original_unit=m['unit'],
                      original_statistic=m['statistic'], original_case_id=m['case_id'],
                      original_source_family=m['source_family'], **row.get('provenance', {}))
    observation = burden_observation(mid, m['case_id'], family_of(m['source_family']),
                                     ascertainment, row, channel, provenance)
    return dict(measurement_id=mid, status='compiled', reasons=[], source=m,
                channel=channel, likelihood_id=mid), observation


def compile_counts(count_audit, sampling, policy, family_of, taken):
    """Individual count observations from the separate source-only count audit.

    The count likelihood has existed and been unused because these claims live
    in their own sidecar and no compiler read it. Claims that do not resolve to
    a countable thing on the route keep an explicit disposition here too.
    """
    observations, dispositions = [], []
    if count_audit is None:
        return observations, dispositions
    for claim in count_audit['count_claims']:
        if claim['id'] in taken:
            raise ValueError('Count-claim identity collides with a ledger claim: ' + claim['id'])
        taken.add(claim['id'])
        row = count_compilation(claim)
        ascertainment = sampling.get(claim['case_id'], policy.get('default_case_sampling'))
        reasons = list(row['reasons'])
        if row['kind'] == 'observation' and ascertainment is None:
            reasons.append('case_sampling_assumption_not_declared')
        if reasons:
            dispositions.append(dict(count_claim_id=claim['id'], status='retained_without_count_likelihood',
                                     reasons=sorted(set(reasons)), source=claim, channel='count'))
            continue
        provenance = dict(count_claim_id=claim['id'], counting_unit=claim['counting_unit'],
                          population=claim['population'], evidence=claim['evidence'],
                          count_basis=claim['basis'], original_value=claim['value'],
                          original_lower=claim['lower'], original_upper=claim['upper'],
                          original_case_id=claim['case_id'], original_source_family=claim['source_family'],
                          notes=claim['notes'])
        observations.append(burden_observation(claim['id'], claim['case_id'],
                                               family_of(claim['source_family']), ascertainment,
                                               row, 'count', provenance))
        dispositions.append(dict(count_claim_id=claim['id'], status='compiled', reasons=[],
                                 source=claim, channel='count', likelihood_id=claim['id']))
    return observations, dispositions


def burden_report(evidence, dispositions, count_dispositions, burden_observations,
                  channels, grouping, declared_types):
    """Coverage for the non-duration channels, kept separate from elapsed coverage.

    An observation and a route input are different outcomes and are counted
    separately: a published fee schedule is the most reliable document in the
    corpus, but it describes the process rather than reporting a case.
    """
    if not channels and grouping == 'document':
        return None
    rows = [r for r in dispositions if 'channel' in r] + list(count_dispositions)
    report = dict(channels=list(channels), source_family_grouping=grouping,
                  source_families=dict(sorted((name, source_family(name, grouping)[0])
                                              for name in declared_types)),
                  unclassified_document_ids=sorted(n for n, kind in declared_types.items()
                                                   if kind is None and grouping != 'document'))
    ledger = Counter(m['metric'] for m in evidence['measurements'])
    for channel in channels:
        claims = [r for r in rows if r['channel'] == channel]
        report[channel] = dict(
            claims=(len(count_dispositions) if channel == 'count' else
                    sum(ledger[metric] for metric in
                        (('fee',) if channel == 'fee' else tuple(EFFORT_BASES)))),
            observations=sum(1 for r in claims if r['status'] == 'compiled'),
            route_inputs=sum(1 for r in claims if r['status'] == 'route_input_not_observation'),
            retained_with_disposition=sum(1 for r in claims if r['status'] not in
                                          {'compiled', 'route_input_not_observation'}),
            reasons=dict(sorted(Counter(reason for r in claims for reason in r['reasons']).items())))
    report['observations_by_channel'] = dict(sorted(
        Counter(o['provenance']['channel'] for o in burden_observations).items()))
    report['notes'] = ([MONEY_REPORT_NOTE] if 'fee' in channels else []) + [
        'Source-family grouping pools report offsets; it does not change any claim, amount or case.']
    report['claim_accounting'] = dict(
        ledger_measurements=len(evidence['measurements']), ledger_dispositions=len(dispositions),
        every_ledger_claim_accounted=len(dispositions) == len(evidence['measurements'])
        and {r['measurement_id'] for r in dispositions} == {m['id'] for m in evidence['measurements']},
        count_claims=len(count_dispositions))
    return report


def declared_kinds(loaded):
    """Source name -> declared kind, from a plain map or a document register.

    A register records `saved_as` paths ("raw/S1_gov_7922_535.txt"), while a
    ledger names its source by the document id, so both the path stem and the
    source id are registered as keys. Returns None when nothing was supplied, so
    the taxonomy falls back to reading a type off the id.
    """
    if not loaded:
        return None
    if isinstance(loaded, dict) and isinstance(loaded.get('sources'), list):
        out = {}
        for entry in loaded['sources']:
            kind = entry.get('kind')
            if not kind:
                continue
            saved = entry.get('saved_as')
            if saved:
                out[pathlib.Path(str(saved)).stem] = kind
            if entry.get('source_id'):
                out[str(entry['source_id'])] = kind
        return out or None
    if isinstance(loaded, dict):
        return {str(k): v for k, v in loaded.items() if isinstance(v, str)}
    raise ValueError('Unsupported source-family kinds document')


def source_type_case_sampling(evidence, count_audit, policy, kinds=None):
    """Resolve a declared ascertainment assumption from sources, never case names.

    A forum label licenses testing selection, not claiming its strength is known.
    One case has one inclusion mechanism even when several reports describe it.
    Mixed source mechanisms require a reviewed explicit case override.
    """
    rules=policy.get('source_type_sampling')
    if not isinstance(rules,dict) or not rules or set(rules)-set(SOURCE_FAMILY_TYPES):
        raise ValueError('Source-type sampling needs declared recognized source types')
    if any(value not in {'unselected','delay_selected'} for value in rules.values()):
        raise ValueError('Unsupported source-type sampling mechanism')
    by_case={}
    def add(case,document,family,claim):
        if case is None:
            return
        # A declared document kind beats a synthetic naming convention; source
        # families are a fallback only when a count sidecar has no document key.
        kind=document_type(document,kinds) if document else document_type(family,kinds)
        mechanism=rules.get(kind,policy.get('default_case_sampling'))
        by_case.setdefault(case,[]).append(dict(claim_id=claim,doc_id=document,
            source_family=family,source_type=kind,proposed_sampling=mechanism))
    for m in evidence['measurements']:
        add(m['case_id'],m['doc_id'],m['source_family'],m['id'])
    for c in (count_audit or {}).get('count_claims',[]):
        for ref in c['evidence']:
            add(c['case_id'],ref['doc_id'],c['source_family'],c['id'])
    sampling=dict(policy.get('case_sampling',{}))
    decisions={}
    for case,support in by_case.items():
        mechanisms={r['proposed_sampling'] for r in support}
        if case in sampling:
            basis='explicit_case_override'
        elif len(mechanisms)>1:
            raise ValueError('Conflicting source ascertainment for case; explicit reviewed override required: '+case)
        else:
            value=next(iter(mechanisms))
            if value is not None:
                sampling[case]=value
            basis='source_type_policy' if value is not None else 'unresolved_source_type_without_default'
        decisions[case]=dict(sampling=sampling.get(case),basis=basis,sources=support)
    return sampling,dict(rules=rules,case_decisions=decisions,
        qualification='Declared selection sensitivity assumption, not measured inclusion probabilities; source-offset pooling is separate.')


def compile_durations(evidence, visit_audit, semantic_audit, documents, policy=None, hypothesis_audit=None,
                      calibration=None, source_bindings=None, report_groups=None, cohort_bindings=None,
                      count_audit=None, burden_channels=(), source_family_grouping='document',
                      source_family_kinds=None, structural_context=None,
                      effective_review=None, review_sidecar_bindings=None):
    """Policy declares modeling assumptions; it cannot override semantic evidence.

    case_sampling: case ID -> unselected/delay_selected. We cannot infer sampling
    probabilities from a forum's existence. source_type_sampling optionally maps
    declared source types to sampling mechanisms, exposing mixed-source conflicts.
    source_type_report_scales optionally maps reviewed source types to fixed
    elapsed report-kernel scales. Its calibration ids are unverified declared
    references, never proof of empirical calibration or a source ranking.
    interpretation_priors: measurement ID
    -> positive normalized weights in the unchanged audit's alternative order.
    These are user/model priors, never LLM confidence or benchmark-tuned weights.

    burden_channels enables the non-duration claims (fee/count/effort), which are
    off by default. source_family_grouping pools per-document offsets into the
    declared source taxonomy; 'document' keeps every document its own family.
    source_family_kinds maps a source name to a kind the corpus itself declares
    (statute, program_page, official_stats, reddit and so on). Without it the
    taxonomy can only read a type off an id, which works for the synthetic
    corpus's `<program>__<kind>` ids and fails for every real one -- the first
    real compile came back with 19 of 20 families unclassified, so the grouping
    pooled nothing exactly where pooling was the point.
    """
    review_report=None
    review_rows={}
    if effective_review is not None:
        evidence,review_report=materialize_review(evidence,effective_review,documents)
        # A corrected source ledger must not inherit an old semantic judgment
        # merely because measurement IDs happen to be unchanged. Bind every
        # supplied downstream judgment to the effective edition and exact bytes
        # under the shared canonical JSON hashing convention.
        sidecars=dict(visit_audit=visit_audit,semantic_audit=semantic_audit,
            hypothesis_audit=hypothesis_audit,source_bindings=source_bindings,
            report_groups=report_groups,cohort_bindings=cohort_bindings,
            structural_context=structural_context)
        expected=dict(schema_version='effective-evidence-sidecar-bindings/1',
            evidence_sha256=review_report['output_evidence_sha256'],
            sidecar_sha256={k:evidence_digest(v) for k,v in sidecars.items() if v is not None})
        if review_sidecar_bindings != expected:
            raise ValueError('Reviewed sidecars must bind the exact effective evidence and every supplied judgment')
        if count_audit is not None:
            raise ValueError('Count sidecars need their own effective-review contract; measurement review cannot admit them')
        review_rows={r['measurement_id']:r for r in review_report['dispositions']}
    elif review_sidecar_bindings is not None:
        raise ValueError('Reviewed-sidecar bindings require an effective review')
    validate(evidence, documents)
    validate_visit_audit(visit_audit, evidence, documents)
    validate_audit(semantic_audit, evidence, documents)
    decision_bindings = bind_decision_contexts(evidence, structural_context)
    bindings = validate_source_bindings(source_bindings, evidence, visit_audit, semantic_audit, documents)
    cohorts_by_measurement = validate_cohort_bindings(cohort_bindings,evidence,semantic_audit,documents)
    if hypothesis_audit is not None:
        validate_hypotheses(hypothesis_audit, evidence, visit_audit, documents)
    channels = tuple(burden_channels or ())
    if len(set(channels)) != len(channels) or set(channels) - set(BURDEN_CHANNELS):
        raise ValueError('Unsupported burden channel; declare a subset of ' + repr(BURDEN_CHANNELS))
    if ('count' in channels) != (count_audit is not None):
        raise ValueError('The count channel needs its separate source-only burden-count audit')
    if source_family_grouping not in SOURCE_FAMILY_GROUPINGS:
        raise ValueError('Unknown source-family grouping: ' + str(source_family_grouping))
    if count_audit is not None:
        validate_counts(count_audit, evidence, documents)
    declared_types = {}

    def family_of(name):
        emitted, kind = source_family(name, source_family_grouping, source_family_kinds)
        declared_types[name] = kind
        return emitted

    # Record the taxonomy over every source in the ledger and count audit, not
    # only the ones that reached an observation: a document the taxonomy does
    # not cover has to be visible whether or not it happened to be compiled.
    for name in ([m['source_family'] for m in evidence['measurements']]
                 + [c['source_family'] for c in (count_audit or {}).get('count_claims', [])]):
        family_of(name)

    policy = policy or {}
    if set(policy) - {'case_sampling', 'interpretation_priors', 'hypothesis_prior',
                      'default_case_sampling', 'calendar', 'event_aliases', 'rounding_fallback',
                      'retain_unsupported', 'residual_reference', 'calibration_context', 'calibrated_readings',
                      'source_type_sampling', 'source_type_report_scales', 'typical_range_model'}:
        raise ValueError('Unsupported compiler policy; semantic overrides are not allowed')
    precision_declaration=policy.get('source_type_report_scales')
    if precision_declaration is not None:
        validate_source_type_report_scales(precision_declaration,SOURCE_FAMILY_TYPES)
    typical_model=policy.get('typical_range_model')
    if typical_model is not None:
        validate_typical_range_model(typical_model)
    retain = policy.get('retain_unsupported', False)
    if not isinstance(retain, bool):
        raise ValueError('retain_unsupported must be a boolean')
    residual = dict(basis='unmodeled_duration', **policy.get('residual_reference', {}))
    if retain and (set(residual) != {'basis', 'median_days', 'log_scale'} or any(
            isinstance(residual[k], bool) or not isinstance(residual[k], (int, float))
            or not math.isfinite(residual[k]) or residual[k] <= 0 for k in ('median_days', 'log_scale'))):
        raise ValueError('Retention requires an explicit positive residual reference distribution')
    calendar = policy.get('calendar')
    if calendar is not None and (set(calendar) != {'calendar_days_per_business_day', 'description'}
            or not calendar['description'] or isinstance(calendar['calendar_days_per_business_day'], bool)
            or not isinstance(calendar['calendar_days_per_business_day'], (int, float))
            or not math.isfinite(calendar['calendar_days_per_business_day'])
            or calendar['calendar_days_per_business_day'] <= 0):
        raise ValueError('Calendar conversion requires a positive factor and an explicit convention')
    if policy.get('rounding_fallback') not in (None, 'reported_unit'):
        raise ValueError('Unknown rounding fallback')
    aliases = policy.get('event_aliases', {})
    if any(key not in AUDIT_EVENTS or key == 'unknown' or value not in CLOCK_EVENTS
           for key, value in aliases.items()):
        raise ValueError('Event aliases must translate known audit events into implemented clocks')
    if policy.get('default_case_sampling') not in (None, 'unselected', 'delay_selected'):
        raise ValueError('Invalid default sampling policy')
    if 'hypothesis_prior' in policy and hypothesis_audit is None:
        raise ValueError('A hypothesis prior requires a separately validated hypothesis audit')
    sampling = policy.get('case_sampling', {})
    priors = policy.get('interpretation_priors', {})
    cases = {m['case_id'] for m in evidence['measurements'] if m['case_id'] is not None}
    # validate_counts above already checked the versioned declarations and their
    # quotations. Count-only applicants need sampling policies without invented
    # timing or fee rows, just as any other observed case does.
    cases.update(c['case_id'] for c in (count_audit or {}).get('cases', []))
    measurements = {m['id']: m for m in eligible(evidence)}
    readings = policy.get('calibrated_readings', {})
    if set(readings) - measurements.keys():
        raise ValueError('Calibrated readings reference unknown measurements')
    if readings and (calibration is None or not retain or not policy.get('calibration_context')):
        raise ValueError('Calibrated mixtures require calibration, its world/extractor context and residual retention')
    if set(sampling) - cases or any(v not in {'unselected', 'delay_selected'} for v in sampling.values()):
        raise ValueError('Sampling assumptions require known case IDs and supported mechanisms')
    sampling_report=None
    if 'source_type_sampling' in policy:
        sampling_evidence=(evidence if review_report is None else dict(evidence,measurements=[
            m for m in evidence['measurements'] if review_rows[m['id']]['disposition']=='admitted']))
        sampling,sampling_report=source_type_case_sampling(sampling_evidence,count_audit,policy,source_family_kinds)
    if set(priors) - measurements.keys():
        raise ValueError('Interpretation priors reference unknown eligible measurements')
    visits = {r['measurement_id']: r for r in visit_audit['measurements']}
    semantics = {r['measurement_id']: r for r in semantic_audit['measurements']}
    contexts = {r['measurement_id']: r for r in evidence.get('observation_contexts', [])}
    hypotheses = ({r['measurement_id']: r for r in hypothesis_audit['measurements']}
                  if hypothesis_audit is not None else {})
    observations, dispositions, burden_observations = [], [], []
    for m in evidence['measurements']:
        mid = m['id']
        context = contexts.get(mid, {})
        review_row=review_rows.get(mid)
        if review_row is not None and review_row['disposition']!='admitted':
            residual_admissible=(review_row['disposition']=='residual_only' and mid in measurements and retain)
            if not residual_admissible:
                disposition=dict(measurement_id=mid,
                    status='review_'+review_row['disposition'],
                    reasons=['effective_review:'+review_row['reason']], source=m,
                    effective_review=review_row)
                if m['metric']=='fee' and 'fee' in channels:
                    disposition['channel']='fee'
                elif m['metric'] in EFFORT_BASES and 'effort' in channels:
                    disposition['channel']='effort'
                dispositions.append(disposition)
                continue
        if mid not in measurements:
            disposition, observation = compile_burden_claim(
                m, context, channels, sampling.get(m['case_id'], policy.get('default_case_sampling')), family_of)
            dispositions.append(disposition)
            if observation is not None:
                burden_observations.append(observation)
            continue
        row, semantic = visits[mid], semantics[mid]
        binding = bindings.get(mid)
        reasons = []
        if review_row is not None and review_row['disposition']=='residual_only':
            reasons.append('effective_review_requires_residual_only')
        if mid not in decision_bindings and (context.get('required_activity_ids') or context.get('excluded_activity_ids') or
                context.get('decision_activity_id') is not None or
                context.get('clock_start_after_activity_ids')):
            reasons.append('case_route_or_milestone_constraints_need_compilation')
        operators, weights = copy.deepcopy(row['operators']), priors.get(mid)
        prior_origin = 'single_upstream_reading' if len(operators) == 1 else 'declared_uncalibrated_prior'
        hypothesis = hypotheses.get(mid)
        if mid in readings:
            if mid in priors or 'hypothesis_prior' in policy:
                raise ValueError('Calibrated weights cannot be combined with guessed interpretation priors')
            calibration_context = policy['calibration_context']
            reading = readings[mid]
            candidate_weights = calibrated_operator_weights(calibration, reading,
                world_id=calibration_context['world_id'], extractor=calibration_context['extractor'])
            candidates = {'audit:'+str(i): op for i, op in enumerate(row['operators'])}
            if hypothesis is not None:
                candidates.update({'hypothesis:'+h['id']: h['operator'] for h in hypothesis['hypotheses']})
            if set(candidate_weights) - candidates.keys() - {'__residual__'}:
                raise ValueError('Calibrated reading names an unvalidated candidate: ' + mid)
            decision = calibration['classes'][reading['ambiguity_class']]['decision']
            if decision == 'top_reading':
                candidate = reading['label_to_candidate'].get(reading['top_label'], '__residual__')
                if candidate not in candidates and candidate != '__residual__':
                    raise ValueError('Top reading is not a validated candidate')
                candidate_weights = {candidate: 1.}
            operators, weights = [], []
            for candidate, weight in candidate_weights.items():
                operators.append(copy.deepcopy(residual if candidate == '__residual__' else candidates[candidate]))
                weights.append(weight)
            prior_origin = 'measured_calibration:' + decision
        elif hypothesis is not None and hypothesis['disposition'] == 'hypotheses':
            if mid in priors:
                raise ValueError('Do not apply old-audit weights to new hypothesis alternatives: ' + mid)
            if 'hypothesis_prior' not in policy:
                reasons.append('hypothesis_prior_not_declared')
            else:
                operators, weights = hypothesis_options(hypothesis, policy['hypothesis_prior'])
                prior_origin = 'declared_uncalibrated_hypothesis_prior'
                if any(not fully_specified(h['operator']) for h in hypothesis['hypotheses']):
                    reasons.append('unresolved_hypothesis_reading')
        for op in operators:
            if binding is not None:
                for selection in binding['operator_selections']:
                    parent = row['operators'][selection['operator_index']]
                    if all(op.get(key) == parent[key] for key in
                           ('basis', 'activity_ids', 'start', 'end', 'visits', 'censoring')):
                        op['activity_selection'] = selection['mode']
            for field in ('start', 'end'):
                if field in op and op[field] in aliases:
                    op[field] = aliases[op[field]]
        operator_issues = [operator_reasons(op, row['activity_mapping']) for op in operators]
        if not retain:
            reasons.extend(reason for issues in operator_issues for reason in issues)
        censoring = {op['censoring'] for op in operators if op['basis'] != 'unmodeled_duration'}
        if len(censoring) != 1:
            reasons.append('alternative_specific_censoring_not_implemented')
        if weights is None:
            weights = [1.] if len(operators) == 1 else None
        if weights is None:
            reasons.append('interpretation_prior_not_declared')
        elif (len(weights) != len(operators) or any(not math.isfinite(v) or v <= 0 for v in weights)
              or not math.isclose(sum(weights), 1., rel_tol=0., abs_tol=1e-12)):
            raise ValueError('Priors must cover every unchanged alternative with positive normalized weights: ' + mid)
        statistic = STATISTICS.get(semantic['statistic_interpretation'])
        if semantic['statistic_interpretation']=='typical_range' and typical_model is not None:
            statistic='typical_range'
            if (m['lower'] is None or m['upper'] is None or m['lower'] >= m['upper'] or
                    semantic['censoring'] != 'none' or censoring != {'none'}):
                reasons.append('typical_range_requires_explicit_uncensored_bounds')
        if statistic is None:
            reasons.append('unmodeled_statistic:' + semantic['statistic_interpretation'])
        ascertainment = None
        if statistic == 'individual':
            if m['case_id'] is None:
                reasons.append('unresolved_case_identity')
            ascertainment = sampling.get(m['case_id'], policy.get('default_case_sampling'))
            if ascertainment is None:
                reasons.append('case_sampling_assumption_not_declared')
        elif statistic is not None:
            if m['case_id'] is not None:
                reasons.append('population_statistic_with_individual_case_identity')
            if m['n'] is not None:
                if statistic=='typical_range':
                    reasons.append('typical_range_is_not_a_finite_cohort_statistic')
                elif statistic not in {'median','p90'}:
                    reasons.append('finite_cohort_mean_likelihood_not_implemented')
                elif mid not in cohorts_by_measurement:
                    reasons.append('finite_cohort_requires_explicit_joint_sampling_contract')
            if semantic['population_scope'] != 'all_cases' and not (
                    binding is not None and binding['population_condition'] == 'first_visit'):
                reasons.append('conditional_or_unknown_population_scope')
            ascertainment = 'unselected'
        interval, interval_reasons = report_interval(m, semantic, next(iter(censoring)) if len(censoring) == 1 else 'none',
            calendar, policy.get('rounding_fallback'))
        reasons.extend(interval_reasons)
        # Never discard an unsupported interpretation and renormalize the survivors.
        # That would make an unresolved source look more definite than it was.
        residual_only = False
        original_reasons = sorted(set(reasons + [reason for issues in operator_issues for reason in issues]))
        if retain:
            if interval is None:
                # Preserve the claim, but never invent a numeric observation or
                # relabel unknown native units as days simply to reach 100%.
                dispositions.append(dict(measurement_id=mid, status='retained_without_numeric_likelihood',
                    reasons=original_reasons, source=m, visit_audit=row, semantic_audit=semantic,
                    route_context=context, hypothesis_audit=hypothesis))
                continue
            if reasons:
                operators, weights = [copy.deepcopy(residual)], [1.]
            else:
                residual_weight, kept, kept_weights = 0., [], []
                for op, weight, issues in zip(operators, weights, operator_issues):
                    if issues or op['basis'] == 'unmodeled_duration':
                        residual_weight += weight
                    else:
                        kept.append(op)
                        kept_weights.append(weight)
                if residual_weight:
                    kept.append(copy.deepcopy(residual))
                    kept_weights.append(residual_weight)
                operators, weights = kept, kept_weights
            residual_only = all(op['basis'] == 'unmodeled_duration' for op in operators)
            if residual_only:
                statistic, ascertainment = 'report_only', 'unselected'
            status = 'residual_only' if residual_only else 'compiled'
            reasons = []
        else:
            status = 'requires_model_extension_or_explicit_assumption' if reasons else 'compiled'
        dispositions.append(dict(measurement_id=mid, status=status, reasons=sorted(set(reasons)),
            source=m, visit_audit=row, semantic_audit=semantic, route_context=context,
            hypothesis_audit=hypothesis, unresolved_reasons=original_reasons, prior_origin=prior_origin,
            source_binding=binding))
        if reasons:
            continue
        obs = dict(id=mid, case_id=None if residual_only else m['case_id'],
            source_family=family_of(m['source_family']),
            sampling=ascertainment, statistic=statistic, lower=interval[0], upper=interval[1],
            operators=[dict(op) for op in operators], operator_weights=list(weights),
            provenance=dict(doc_id=m['doc_id'], quote=m['quote'], visit_support=row['evidence'],
                statistic_support=semantic['evidence'], original_value=m['value'],
                original_lower=m['lower'], original_upper=m['upper'], original_unit=m['unit']))
        obs['provenance'].update(prior_origin=prior_origin, residual_only=residual_only,
            original_case_id=m['case_id'], original_statistic=semantic['statistic_interpretation'],
            unresolved_reasons=original_reasons)
        if statistic=='typical_range':
            obs['typical_range_model']=copy.deepcopy(typical_model)
        if mid in decision_bindings and not residual_only:
            obs['decision_context_binding'] = copy.deepcopy(decision_bindings[mid])
        if mid in cohorts_by_measurement:
            obs.update(sample_size=cohorts_by_measurement[mid]['sample_size'],
                       cohort_id=cohorts_by_measurement[mid]['cohort_id'])
        if binding is not None:
            obs['provenance']['source_binding'] = binding
            if not residual_only and binding['population_condition'] is not None:
                obs['population_condition'] = binding['population_condition']
        if mid in readings:
            obs['provenance']['calibration'] = dict(reading=readings[mid],
                artifact_sha256=digest(json.dumps(calibration, sort_keys=True)),
                promotion_status='Development routing only; paired timing/count validation still required')
        if hypothesis is not None and hypothesis['disposition'] == 'hypotheses':
            obs['provenance']['interpretation_hypotheses'] = hypothesis
        if (precision_declaration is not None and statistic!='typical_range'
                and any(op['basis']!='unmodeled_duration' for op in operators)):
            source_key=m['doc_id'] if m.get('doc_id') else m['source_family']
            source_type=document_type(source_key,source_family_kinds)
            attach_precision_annotation(obs,
                resolved_precision_annotation(source_type,precision_declaration))
        observations.append(obs)
    observations=combine_report_groups(observations,dispositions,report_groups,evidence,documents)
    observations, quantile_cohorts=combine_quantile_cohorts(observations,dispositions,cohorts_by_measurement)
    if review_report is not None:
        for disposition in dispositions:
            r=review_rows[disposition['measurement_id']]
            disposition.update(gate_id=r['gate_id'],review_disposition=r['disposition'])
        for o in observations+burden_observations+[r for c in quantile_cohorts for r in c['reports']]:
            mids=o.get('measurement_ids',[o['id']])
            o['provenance']['gate_ids']=[review_rows[mid]['gate_id'] for mid in mids]
    all_observations=observations+[o for c in quantile_cohorts for o in cohort_report_observations(c)]
    represented=lambda o: len(o.get('measurement_ids',[o['id']]))
    compiled_count=sum(represented(o) for o in all_observations)
    informative_count=sum(represented(o) for o in all_observations if not o['provenance']['residual_only'])
    informative_cohorts=sum(any(op['basis']!='unmodeled_duration' for op in c['operators']) for c in quantile_cohorts)
    reason_counts = Counter(reason for row in dispositions for reason in row.get('unresolved_reasons', row['reasons']))
    count_observations, count_dispositions = compile_counts(
        count_audit, sampling, policy, family_of, {m['id'] for m in evidence['measurements']})
    burden_observations += count_observations
    burden = burden_report(evidence, dispositions, count_dispositions, burden_observations,
                           channels, source_family_grouping, declared_types)
    emitted = observations + burden_observations
    precision_report=source_precision_report(precision_declaration,observations,quantile_cohorts)
    return dict(schema_version=('joint-visit-duration-compilation/6' if review_report is not None or
        any(o['statistic']=='typical_range' for o in observations) else
        'joint-visit-duration-compilation/5' if burden is not None else
        'joint-visit-duration-compilation/4' if cohort_bindings is not None else
        'joint-visit-duration-compilation/3' if report_groups is not None else
        'joint-visit-duration-compilation/2' if retain else 'joint-visit-duration-compilation/1'), program_id=evidence['program_id'],
        observations=emitted, quantile_cohorts=quantile_cohorts, dispositions=dispositions, policy=policy,
        **({} if review_report is None else dict(effective_review=review_report,
            review_sidecar_bindings=review_sidecar_bindings,
            effective_evidence=evidence)),
        **({} if sampling_report is None else dict(source_type_sampling=sampling_report)),
        **({} if precision_report is None else dict(source_precision=precision_report)),
        **({} if structural_context is None else dict(decision_context_bindings=decision_bindings)),
        required_model_features=(['within_visit_phases'] if any(
            op['basis'] in {'wait_elapsed', 'service_elapsed'} for o in all_observations for op in o['operators']) else [])
            + (['unmodeled_report_alternative'] if any(op['basis'] == 'unmodeled_duration'
                for o in all_observations for op in o['operators']) else [])
            + (['first_visit_population_conditioning'] if any(o.get('population_condition') for o in all_observations) else [])
            + (['first_activity_union'] if any(op.get('activity_selection') for o in all_observations for op in o['operators']) else [])
            + (['report_interval_union'] if any('report_intervals' in o for o in all_observations) else [])
            + (['joint_finite_cohort_quantiles'] if quantile_cohorts else [])
            + (['subjective_typical_range_reports'] if any(o['statistic']=='typical_range' for o in observations) else [])
            + sorted({'individual_' + o['provenance']['channel'] + '_observations' for o in burden_observations}),
        coverage=dict(all_measurements=len(evidence['measurements']), eligible_elapsed=len(measurements),
                      **({} if review_report is None else dict(review=review_report['counts'])),
                      compiled_elapsed=compiled_count,
                      informative_elapsed=informative_count,
                      residual_only_elapsed=compiled_count-informative_count,
                      likelihood_factors=len(observations)+len(quantile_cohorts),
                      finite_quantile_cohorts=len(quantile_cohorts),
                      informative_report_factors=sum(not o['provenance']['residual_only'] for o in observations)+informative_cohorts,
                      residual_only_report_factors=sum(o['provenance']['residual_only'] for o in observations)+len(quantile_cohorts)-informative_cohorts,
                      accounted_elapsed=sum(r['measurement_id'] in measurements for r in dispositions),
                      compiled_with_interpretation_assumptions=sum('interpretation_hypotheses' in o['provenance']
                                                                  for o in all_observations),
                      reasons=dict(sorted(reason_counts.items())),
                      **({} if burden is None else dict(burden=burden))),
        **({} if not count_dispositions else dict(count_dispositions=count_dispositions)),
        complete_elapsed_coverage=compiled_count == len(measurements),
        complete_informative_coverage=informative_count == len(measurements),
        ready_for_full_burden_fit=False,
        assumptions=['Calendar-month conversion is 365.25/12 days; weeks are seven calendar days.',
                     'Single-visit ordinal is exchangeable only under the current perfect repeat-duration correlation model.',
                     'Compiled operators still require quote-supported route/actor reconciliation and event availability.']
                    + (['Elapsed claims only: counts, money and person-hours are not discarded from the source ledger.']
                       if burden is None else
                       [ROUNDING_ASSUMPTION, EFFORT_UNIT_ASSUMPTION, MONEY_REPORT_NOTE,
                        'A published fee with no case is an input to the route, not an observation of it.',
                        'A reported fee total is compiled over the whole traversed path, not over the '
                        'operations the ledger happened to link, so a path that omits a step is not charged for it.',
                        'Money, hours and count reports have no unmodeled residual alternative, so an '
                        'unresolved one keeps a disposition instead of a widened interval.']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('evidence', 'visit-audit', 'semantic-audit', 'inputs', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--policy', help='Explicit case-sampling and alternative-prior assumptions')
    parser.add_argument('--hypothesis-audit', help='Separate source-only modeling hypotheses; original audit stays intact')
    parser.add_argument('--calibration', help='Measured per-world interpretation calibration; not generator truth rows')
    parser.add_argument('--source-bindings', help='Separate quote-backed first-visit population/activity-union bindings')
    parser.add_argument('--report-groups', help='Quote-backed repeated-wording and disjunctive-report groups')
    parser.add_argument('--cohort-bindings', help='Quote-backed joint finite-quantile cohorts and explicit sampling assumptions')
    parser.add_argument('--effective-review', help='Source-bound reviewed corrections and fail-closed measurement dispositions')
    parser.add_argument('--review-sidecar-bindings', help='Exact effective-edition and downstream semantic-sidecar hashes')
    parser.add_argument('--assume-case-sampling', choices=['unselected', 'delay_selected'],
                        help='Declare the same sampling assumption for all known cases; never inferred from forum membership')
    parser.add_argument('--uniform-existing-interpretations', action='store_true',
                        help='Explicit equal priors on original-audit alternatives not replaced by hypotheses')
    parser.add_argument('--hypothesis-residual-weight', type=float,
                        help='Declare family-balanced priors and log-t(4)(log 7, 3) residual report reference')
    parser.add_argument('--count-audit', help='Separate source-only burden-count audit; enables count observations')
    parser.add_argument('--compile-fees', action='store_true',
                        help='Compile fee claims; individual totals become money observations and published amounts route inputs')
    parser.add_argument('--compile-effort', action='store_true',
                        help='Compile payer_work/agency_work claims into the payer_hours/agency_hours channels')
    parser.add_argument('--source-family-kinds',
                        help='JSON declaring each source\'s kind, so the type grouping can pool '
                             'real documents whose ids carry no kind. Either a plain '
                             '{source_name: kind} object or a document register with a `sources` '
                             'list, whose `saved_as` paths name the documents.')
    parser.add_argument('--source-family-grouping', choices=list(SOURCE_FAMILY_GROUPINGS), default='document',
                        help='Pool report offsets by declared source type; the default keeps one family per document')
    parser.add_argument('--structural-context',
                        help='Source-only V6 structural data already encoding quoted individual decision scopes; '
                             'only exact decision-only bindings can release those context holds')
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    paths = {name: pathlib.Path(getattr(args, name)) for name in
             ('evidence', 'visit_audit', 'semantic_audit', 'inputs')}
    if args.policy:
        paths['policy'] = pathlib.Path(args.policy)
    if args.hypothesis_audit:
        paths['hypothesis_audit'] = pathlib.Path(args.hypothesis_audit)
    if args.calibration:
        paths['calibration'] = pathlib.Path(args.calibration)
    if args.source_bindings:
        paths['source_bindings'] = pathlib.Path(args.source_bindings)
    if args.report_groups:
        paths['report_groups'] = pathlib.Path(args.report_groups)
    if args.cohort_bindings:
        paths['cohort_bindings'] = pathlib.Path(args.cohort_bindings)
    if args.effective_review:
        paths['effective_review'] = pathlib.Path(args.effective_review)
    if args.review_sidecar_bindings:
        paths['review_sidecar_bindings'] = pathlib.Path(args.review_sidecar_bindings)
    if args.count_audit:
        paths['count_audit'] = pathlib.Path(args.count_audit)
    if args.source_family_kinds:
        paths['source_family_kinds'] = pathlib.Path(args.source_family_kinds)
    if args.structural_context:
        paths['structural_context'] = pathlib.Path(args.structural_context)
    values = {name: json.loads(path.read_text()) for name, path in paths.items()}
    assumptions = (args.assume_case_sampling or args.uniform_existing_interpretations
                   or args.hypothesis_residual_weight is not None)
    if args.policy and assumptions:
        raise ValueError('Supply either a policy file or command-line assumptions, not both')
    if assumptions:
        policy = {}
        if args.assume_case_sampling:
            policy['case_sampling'] = {m['case_id']: args.assume_case_sampling for m in values['evidence']['measurements']
                                       if m['case_id'] is not None}
        hypothesized = {r['measurement_id'] for r in values.get('hypothesis_audit', {}).get('measurements', [])
                        if r['disposition']=='hypotheses'}
        if args.uniform_existing_interpretations:
            policy['interpretation_priors'] = {r['measurement_id']: [1./len(r['operators'])]*len(r['operators'])
                for r in values['visit_audit']['measurements'] if len(r['operators'])>1 and r['measurement_id'] not in hypothesized}
        if args.hypothesis_residual_weight is not None:
            policy['hypothesis_prior'] = dict(residual_weight=args.hypothesis_residual_weight,
                unmodeled_median_days=7., unmodeled_log_scale=3., allocation='uniform_basis_then_reading')
        values['policy'] = policy
    channels = tuple(name for name, enabled in (('fee', args.compile_fees), ('count', bool(args.count_audit)),
                                                ('effort', args.compile_effort)) if enabled)
    report = compile_durations(values['evidence'], values['visit_audit'], values['semantic_audit'],
                               values['inputs']['documents'], values.get('policy'), values.get('hypothesis_audit'),
                               values.get('calibration'), values.get('source_bindings'), values.get('report_groups'),
                               values.get('cohort_bindings'), values.get('count_audit'), channels,
                               args.source_family_grouping, declared_kinds(values.get('source_family_kinds')),
                               structural_context=values.get('structural_context'),
                               effective_review=values.get('effective_review'),
                               review_sidecar_bindings=values.get('review_sidecar_bindings'))
    write(out / 'compilation.json', report)
    source = pathlib.Path(__file__).parent
    names = ['compile_visit_durations.py', 'audit_visit_observations.py', 'audit_visit_hypotheses.py',
             'audit_measurement_semantics.py', 'evidence_contract.py', 'reconcile_evidence.py',
             'semantic_calibration.py', 'compact_visit_trace.py', 'cohort_quantiles.py',
             'burden_channels.py', 'audit_burden_counts.py', 'decision_scope_binding.py',
             'typical_range_reports.py', 'effective_evidence.py']
    for name, value in values.items():
        write(out / 'inputs' / (name + '.json'), value)
    for name in names:
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
    write(out / 'manifest.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        input_sha256={str(path): digest(path.read_bytes()) for path in paths.values()},
        source_sha256={name: digest((source / name).read_bytes()) for name in names},
        compilation_sha256=digest((out / 'compilation.json').read_bytes()),
        command_line_assumptions=values.get('policy') if assumptions else None,
        burden_channels=list(channels), source_family_grouping=args.source_family_grouping,
        hidden_truth_read=False, fitted_outputs_read=False))
    print(json.dumps(dict(program=report['program_id'], coverage=report['coverage'])), flush=True)


if __name__ == '__main__':
    main()
