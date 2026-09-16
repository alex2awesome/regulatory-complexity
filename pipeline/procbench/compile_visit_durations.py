"""Compile quote-checked elapsed claims to the joint visit model's observations.

This is the duration boundary of the source compiler, not a complete text-to-route
pipeline. Every input claim receives an explicit disposition. Unknown operators,
unsupported populations and incomplete alternative sets are never silently dropped
or coerced into more convenient measurements. No truth or fitted outputs are read.
"""
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import json
import math
import pathlib

from .audit_measurement_semantics import eligible, validate_audit
from .audit_visit_observations import STARTS, ENDS, validate_visit_audit
from .audit_visit_hypotheses import fully_specified, validate_hypotheses
from .evidence_contract import validate
from .reconcile_evidence import digest, write
from .compact_visit_trace import CLOCK_EVENTS
from .semantic_calibration import operator_weights as calibrated_operator_weights


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
            if len(operator['activity_ids']) != 1:
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


def compile_durations(evidence, visit_audit, semantic_audit, documents, policy=None, hypothesis_audit=None,
                      calibration=None):
    """Policy declares modeling assumptions; it cannot override semantic evidence.

    case_sampling: case ID -> unselected/delay_selected. We cannot infer sampling
    probabilities from a forum's existence. interpretation_priors: measurement ID
    -> positive normalized weights in the unchanged audit's alternative order.
    These are user/model priors, never LLM confidence or benchmark-tuned weights.
    """
    validate(evidence, documents)
    validate_visit_audit(visit_audit, evidence, documents)
    validate_audit(semantic_audit, evidence, documents)
    if hypothesis_audit is not None:
        validate_hypotheses(hypothesis_audit, evidence, visit_audit, documents)
    policy = policy or {}
    if set(policy) - {'case_sampling', 'interpretation_priors', 'hypothesis_prior',
                      'default_case_sampling', 'calendar', 'event_aliases', 'rounding_fallback',
                      'retain_unsupported', 'residual_reference', 'calibration_context', 'calibrated_readings'}:
        raise ValueError('Unsupported compiler policy; semantic overrides are not allowed')
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
    measurements = {m['id']: m for m in eligible(evidence)}
    readings = policy.get('calibrated_readings', {})
    if set(readings) - measurements.keys():
        raise ValueError('Calibrated readings reference unknown measurements')
    if readings and (calibration is None or not retain or not policy.get('calibration_context')):
        raise ValueError('Calibrated mixtures require calibration, its world/extractor context and residual retention')
    if set(sampling) - cases or any(v not in {'unselected', 'delay_selected'} for v in sampling.values()):
        raise ValueError('Sampling assumptions require known case IDs and supported mechanisms')
    if set(priors) - measurements.keys():
        raise ValueError('Interpretation priors reference unknown eligible measurements')
    visits = {r['measurement_id']: r for r in visit_audit['measurements']}
    semantics = {r['measurement_id']: r for r in semantic_audit['measurements']}
    contexts = {r['measurement_id']: r for r in evidence.get('observation_contexts', [])}
    hypotheses = ({r['measurement_id']: r for r in hypothesis_audit['measurements']}
                  if hypothesis_audit is not None else {})
    observations, dispositions = [], []
    for m in evidence['measurements']:
        mid = m['id']
        if mid not in measurements:
            dispositions.append(dict(measurement_id=mid, status='outside_elapsed_compiler',
                reasons=['non_elapsed_or_not_current_empirical_timing'], source=m))
            continue
        row, semantic = visits[mid], semantics[mid]
        reasons = []
        context = contexts.get(mid, {})
        if (context.get('required_activity_ids') or context.get('excluded_activity_ids') or
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
                reasons.append('finite_cohort_summary_likelihood_not_implemented')
            if semantic['population_scope'] != 'all_cases':
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
            hypothesis_audit=hypothesis, unresolved_reasons=original_reasons, prior_origin=prior_origin))
        if reasons:
            continue
        obs = dict(id=mid, case_id=None if residual_only else m['case_id'], source_family=m['source_family'],
            sampling=ascertainment, statistic=statistic, lower=interval[0], upper=interval[1],
            operators=[dict(op) for op in operators], operator_weights=list(weights),
            provenance=dict(doc_id=m['doc_id'], quote=m['quote'], visit_support=row['evidence'],
                statistic_support=semantic['evidence'], original_value=m['value'],
                original_lower=m['lower'], original_upper=m['upper'], original_unit=m['unit']))
        obs['provenance'].update(prior_origin=prior_origin, residual_only=residual_only,
            original_case_id=m['case_id'], original_statistic=semantic['statistic_interpretation'],
            unresolved_reasons=original_reasons)
        if mid in readings:
            obs['provenance']['calibration'] = dict(reading=readings[mid],
                artifact_sha256=digest(json.dumps(calibration, sort_keys=True)),
                promotion_status='Development routing only; paired timing/count validation still required')
        if hypothesis is not None and hypothesis['disposition'] == 'hypotheses':
            obs['provenance']['interpretation_hypotheses'] = hypothesis
        observations.append(obs)
    reason_counts = Counter(reason for row in dispositions for reason in row.get('unresolved_reasons', row['reasons']))
    return dict(schema_version='joint-visit-duration-compilation/2' if retain else 'joint-visit-duration-compilation/1', program_id=evidence['program_id'],
        observations=observations, dispositions=dispositions, policy=policy,
        required_model_features=(['within_visit_phases'] if any(
            op['basis'] in {'wait_elapsed', 'service_elapsed'} for o in observations for op in o['operators']) else [])
            + (['unmodeled_report_alternative'] if any(op['basis'] == 'unmodeled_duration'
                for o in observations for op in o['operators']) else []),
        coverage=dict(all_measurements=len(evidence['measurements']), eligible_elapsed=len(measurements),
                      compiled_elapsed=len(observations),
                      informative_elapsed=sum(not o['provenance']['residual_only'] for o in observations),
                      residual_only_elapsed=sum(o['provenance']['residual_only'] for o in observations),
                      accounted_elapsed=sum(r['measurement_id'] in measurements for r in dispositions),
                      compiled_with_interpretation_assumptions=sum('interpretation_hypotheses' in o['provenance']
                                                                  for o in observations),
                      reasons=dict(sorted(reason_counts.items()))),
        complete_elapsed_coverage=len(observations) == len(measurements),
        complete_informative_coverage=sum(not o['provenance']['residual_only'] for o in observations) == len(measurements),
        ready_for_full_burden_fit=False,
        assumptions=['Calendar-month conversion is 365.25/12 days; weeks are seven calendar days.',
                     'Single-visit ordinal is exchangeable only under the current perfect repeat-duration correlation model.',
                     'Compiled operators still require quote-supported route/actor reconciliation and event availability.',
                     'Elapsed claims only: counts, money and person-hours are not discarded from the source ledger.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('evidence', 'visit-audit', 'semantic-audit', 'inputs', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--policy', help='Explicit case-sampling and alternative-prior assumptions')
    parser.add_argument('--hypothesis-audit', help='Separate source-only modeling hypotheses; original audit stays intact')
    parser.add_argument('--calibration', help='Measured per-world interpretation calibration; not generator truth rows')
    parser.add_argument('--assume-case-sampling', choices=['unselected', 'delay_selected'],
                        help='Declare the same sampling assumption for all known cases; never inferred from forum membership')
    parser.add_argument('--uniform-existing-interpretations', action='store_true',
                        help='Explicit equal priors on original-audit alternatives not replaced by hypotheses')
    parser.add_argument('--hypothesis-residual-weight', type=float,
                        help='Declare family-balanced priors and log-t(4)(log 7, 3) residual report reference')
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
    report = compile_durations(values['evidence'], values['visit_audit'], values['semantic_audit'],
                               values['inputs']['documents'], values.get('policy'), values.get('hypothesis_audit'),
                               values.get('calibration'))
    write(out / 'compilation.json', report)
    source = pathlib.Path(__file__).parent
    names = ['compile_visit_durations.py', 'audit_visit_observations.py', 'audit_visit_hypotheses.py',
             'audit_measurement_semantics.py', 'evidence_contract.py', 'reconcile_evidence.py',
             'semantic_calibration.py', 'compact_visit_trace.py']
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
        hidden_truth_read=False, fitted_outputs_read=False))
    print(json.dumps(dict(program=report['program_id'], coverage=report['coverage'])), flush=True)


if __name__ == '__main__':
    main()
