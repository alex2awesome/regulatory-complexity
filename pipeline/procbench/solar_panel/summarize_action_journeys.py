"""Summarize actual shared-case V6 traces, not independent phase marginals.

The compiler's occurrence IDs and its actor/action concepts are different
counts. Neither is the total number of steps in an incompletely reported
installation. In particular, an unobserved step is not a zero-duration step.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

from ..bayes_trace_hierarchy import (
    CHANNELS, COUNT_BASES, MONEY_BASES, Config, VisitHierarchy,
    duration_report_log_probability,
)
from ..compact_visit_trace import UnavailableTraceQuantity
from ..latent_gaussian import diagnostics, summary


ACTUAL_CASE_THRESHOLDS = dict(max_rhat=1.01, min_bulk_ess=400., min_tail_ess=200.)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summarize(values, shape):
    array = np.asarray(values, dtype=float)
    result = summary(array)
    if len(array) == int(np.prod(shape)):
        result['diagnostics'] = diagnostics(array.reshape(shape))
    else:
        result['conditional_on_included_route'] = True
        result['posterior_probability_included'] = len(array) / int(np.prod(shape))
    return result


def _actual_case_gate(cases, posterior):
    """Gate only reported observed-case trace quantities, never new-population QMC."""
    quantities = []
    for case_id, case in cases.items():
        collections = [
            ("case_posterior", case["case_posterior"]),
            ("observed_clocks", case["observed_clocks"]),
            ("derived_clocks_not_additional_likelihood",
             case["derived_clocks_not_additional_likelihood"]),
            ("operation_cycle_days", {key: value["case_cycle_days"]
                                      for key, value in case["operations"].items()}),
        ]
        for collection, rows in collections:
            for name, value in rows.items():
                path = f"cases.{case_id}.{collection}.{name}"
                diagnostic = value.get("diagnostics")
                reasons = []
                if diagnostic is None:
                    reasons.append("conditional_or_unsupported_quantity_has_no_full_chain_diagnostics")
                else:
                    required = {"rhat", "ess_bulk", "ess_tail"}
                    if not required <= set(diagnostic) or any(
                            not isinstance(diagnostic.get(field), (int, float, np.number))
                            or not np.isfinite(diagnostic[field]) for field in required):
                        reasons.append("missing_or_nonfinite_diagnostics")
                    else:
                        if diagnostic["rhat"] > ACTUAL_CASE_THRESHOLDS["max_rhat"]:
                            reasons.append("rhat_above_threshold")
                        if diagnostic["ess_bulk"] < ACTUAL_CASE_THRESHOLDS["min_bulk_ess"]:
                            reasons.append("bulk_ess_below_threshold")
                        if diagnostic["ess_tail"] < ACTUAL_CASE_THRESHOLDS["min_tail_ess"]:
                            reasons.append("tail_ess_below_threshold")
                quantities.append(dict(quantity=path, passed=not reasons,
                    reasons=reasons, diagnostics=diagnostic,
                    conditional_on_included_route=bool(value.get("conditional_on_included_route"))))
    precision = posterior.get("precision")
    likelihood_acceptable = bool(isinstance(precision, dict)
                                 and precision.get("likelihood_acceptable") is True)
    prerequisites = dict(posterior_converged=posterior.get("posterior_converged") is True,
                         likelihood_precision_acceptable=likelihood_acceptable,
                         all_reported_actual_case_quantities_have_passing_diagnostics=(
                             bool(quantities) and all(row["passed"] for row in quantities)))
    usable = all(prerequisites.values())
    return dict(actual_case_numerically_usable=usable,
        thresholds=dict(ACTUAL_CASE_THRESHOLDS), prerequisites=prerequisites,
        quantities_checked=len(quantities), quantities_passed=sum(row["passed"] for row in quantities),
        flagged_quantities=[row for row in quantities if not row["passed"]],
        meaning=("Numerical gate for posterior quantities calculated from the fitted observed-case traces only. "
                 "It does not certify population predictions, representativeness, source semantics, agency capability, "
                 "or conditional-route quantities lacking full-chain diagnostics."))


def _elapsed_task_type_baselines(model, data, states, cases):
    """Conditional task locations with agency/operation/source offsets fixed at zero."""
    support = defaultdict(lambda: dict(cases=set(), occurrences=0, clocks=set(),
                                       component_kinds=set()))
    for case_id, case in cases.items():
        for operation in case['operations'].values():
            task = operation['action_id']
            row = support[task]
            row['cases'].add(case_id)
            row['occurrences'] += 1
            row['clocks'].update((case_id, clock)
                                 for clock in operation['directly_named_in_clock_observations'])
            row['component_kinds'].add(operation['component_kind'])
    support_rows = {task: dict(distinct_canonical_cases=len(row['cases']),
        materialized_occurrences=row['occurrences'], directly_named_clock_rows=len(row['clocks']),
        component_kinds=sorted(row['component_kinds']),
        low_support=len(row['cases']) < 2,
        actor_action_type=row['component_kinds'] == {'action_cycle'})
        for task, row in sorted(support.items())}
    unavailable = []
    if model.cfg.agency_sd != 0:
        unavailable.append('agency_sd_nonzero')
    if model.cfg.source_sd != 0 or model.source_offset_hierarchy is not None:
        unavailable.append('source_effect_not_fixed_zero')
    if model.operation_location_design is not None:
        unavailable.append('operation_location_design_present')
    if model.cfg.elapsed_task_prior_medians:
        unavailable.append('elapsed_task_prior_offsets_present')
    scope = ('exp(global elapsed location + elapsed task effect), conditional on agency, '
             'operation-occurrence and source offsets equal to zero in this report frame')
    if unavailable:
        return dict(status='unavailable', unavailable_reasons=unavailable,
            quantity_scope=scope, support=support_rows, task_types={})
    task_positions = {task: i for i, task in enumerate(model.tasks)}
    flat = states.reshape(-1, states.shape[-1])
    samples = {task: [] for task in support_rows}
    for z in flat:
        parameters = model.parameters(z)
        for task in samples:
            samples[task].append(float(np.exp(
                parameters['location'][0] + parameters['task'][0, task_positions[task]])))
    task_types = {}
    for task, values in samples.items():
        task_types[task] = dict(support=support_rows[task],
            conditional_location_median_days=_summarize(values, states.shape[:2]),
            quantity_scope=scope,
            interpretation=('Task-type posterior location in the declared elapsed unit. Not an intrinsic '
                            'agency service time, active-work duration, or applicant-population average.'))
    return dict(status='available', unavailable_reasons=[], quantity_scope=scope,
        support=support_rows, task_types=task_types,
        identification_qualification=('Posterior concentration may reflect hierarchy pooling and priors; '
            'support counts and diagnostics do not by themselves establish separate identification. '
            'actor_action_type is a semantic tag, not headline eligibility; singleton or numerically '
            'unsupported task baselines must not be promoted as established cross-case timings.'))


def _spread_comparison(posterior, prior):
    """A marginal spread diagnostic, not a fraction of information learned."""
    posterior, prior = np.asarray(posterior), np.asarray(prior)
    if (posterior.ndim != 1 or prior.ndim != 1 or min(len(posterior), len(prior)) < 2
            or not np.isfinite(posterior).all() or not np.isfinite(prior).all()):
        raise ValueError('Spread comparison requires finite one-dimensional samples')
    prior_sd, posterior_sd = float(np.std(prior, ddof=1)), float(np.std(posterior, ddof=1))
    ratio = posterior_sd / prior_sd if prior_sd > 0 else None
    return dict(prior_sd=prior_sd, posterior_sd=posterior_sd,
        posterior_to_prior_sd_ratio=ratio,
        posterior_mean_minus_prior_mean=float(np.mean(posterior)-np.mean(prior)),
        width_label=('constant_under_declared_prior' if ratio is None else
                     'prior_width_or_wider' if ratio >= .8 else 'narrower_than_prior'),
        prior_width_threshold=.8)


def _fixed_serial_prior_comparison(model, program, raw, operation_values, prior_states):
    """Compare case totals and component shares under exactly the fitted prior.

    Restricted to fixed serial realized journeys; no invented structural prior,
    no independent resampling of correlated posterior component marginals.
    """
    from .audit_journey_information import _serial_operations
    try:
        order = _serial_operations(raw)
    except (KeyError, ValueError) as error:
        return dict(status='unsupported', reason=str(error))
    index = program['case_index'][program['cases'][0]]
    prior_values = {ident: [] for ident in order}
    for z in prior_states:
        trace = model.trace(program, z, model.parameters(z), 0)
        for oi, operation in enumerate(trace.operations):
            if int(trace.visits[index, oi]) != 1:
                return dict(status='unsupported', reason='Not one realized occurrence per component')
            prior_values[operation.id].append(float(trace.durations[index, oi]))
    prior = np.column_stack([prior_values[ident] for ident in order])
    posterior = np.column_stack([operation_values[ident] for ident in order])
    if (not np.isfinite(prior).all() or not np.isfinite(posterior).all()
            or np.any(prior <= 0) or np.any(posterior <= 0)):
        return dict(status='unsupported', reason='Nonpositive or nonfinite duration samples')
    components = {}
    for oi, ident in enumerate(order):
        item = dict(log_case_duration=_spread_comparison(np.log(posterior[:, oi]), np.log(prior[:, oi])))
        if len(order) > 1:
            # logit(component / total) = log(component) - log(all other components).
            # Summing the complement directly avoids catastrophic subtraction.
            others = [j for j in range(len(order)) if j != oi]
            item['logit_share_of_scoped_total'] = _spread_comparison(
                np.log(posterior[:, oi])-np.log(posterior[:, others].sum(axis=1)),
                np.log(prior[:, oi])-np.log(prior[:, others].sum(axis=1)))
        else:
            item['logit_share_of_scoped_total'] = None  # Structural constant, not learned.
        components[ident] = item
    return dict(status='compared', prior_draws=len(prior), posterior_draws=len(posterior),
        log_scoped_total=_spread_comparison(np.log(posterior.sum(axis=1)), np.log(prior.sum(axis=1))),
        components=components,
        qualification=('Conditional on the supplied fixed serial journey and hierarchy. '
            'Marginal SD reduction can arise through pooling and prior dependencies; it does not '
            'establish likelihood identification or measure total information. A mean shift can '
            'carry evidence even when width does not shrink. Composite interiors remain unknown.'))


def _elapsed_report_check(observation, values, *, scale, contamination):
    """Conditional in-sample reproduction under the *native* Student-t kernel.

    The broad component is relative to the same latent duration. Its posterior
    responsibility is not the probability that the author is lying or mistaken.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError('Report checks require finite positive elapsed samples')
    intervals = observation.get('report_intervals') or [
        [observation['lower'], observation['upper']]]
    inside = np.zeros(len(values), dtype=bool)
    for lower, upper in intervals:
        inside |= (values >= lower) & (values <= (np.inf if upper is None else upper))
    mixed = duration_report_log_probability(observation, values, scale=scale,
                                             contamination=contamination)
    if contamination:
        broad = duration_report_log_probability(observation, values, scale=2., contamination=0.)
        responsibility = float(np.exp(np.log(contamination) + broad - mixed).mean())
    else:
        responsibility = 0.
    return dict(status='checked', observation_id=observation['id'],
        observation_kind=observation.get('observation_kind'), report_intervals=intervals,
        posterior_draws=len(values), report_log_scale=float(scale),
        contamination_prior=float(contamination), source_log_offset=0.,
        median_latent_days=float(np.median(values)),
        latent_ci90=np.quantile(values, [.05, .95]).tolist(),
        posterior_probability_latent_within_stated_bounds=float(inside.mean()),
        mean_probability_of_reproducing_stated_report=float(np.exp(mixed).mean()),
        mean_broad_component_responsibility=responsibility)


def _case_report_checks(model, program, report_values, expected_draws):
    """Scoped to the independent, single-operator elapsed case reports we fit.

    Do not silently reuse this calculation for shared report errors, uncertain
    operators, unsupported paths, or nonzero source effects.
    """
    grouped = {o['id'] for group in program.get('joint_duration_reports', [])
               for o in group['members']}
    results = {}
    excluded_bases = COUNT_BASES | set(MONEY_BASES) | set(CHANNELS[1:]) | {'unmodeled_duration'}
    for observation in program['observations']:
        ident = observation['id']
        reasons = []
        if model.cfg.source_sd != 0 or model.source_offset_hierarchy is not None:
            reasons.append('source_effect_not_fixed_zero')
        if observation['case_id'] is None or observation['statistic'] != 'individual':
            reasons.append('not_individual_case_report')
        if ident in grouped:
            reasons.append('shared_reporting_error_requires_joint_check')
        if len(observation['operators']) != 1:
            reasons.append('operator_mixture_requires_mixture_check')
        elif observation['operators'][0]['basis'] in excluded_bases:
            reasons.append('not_supported_elapsed_operator')
        samples = report_values.get(ident, [])
        if len(samples) != expected_draws:
            reasons.append('latent_quantity_not_available_on_every_draw')
        if samples and (not np.isfinite(samples).all() or np.any(np.asarray(samples) <= 0)):
            reasons.append('nonpositive_or_nonfinite_elapsed_quantity')
        if reasons:
            results[ident] = dict(status='unsupported', reasons=reasons)
        else:
            results[ident] = _elapsed_report_check(observation, samples,
                scale=model._report_scale_for_operator(observation, observation['operators'][0]),
                contamination=model.cfg.contamination)
    return dict(reports=results,
        qualification=('In-sample conditional report reproduction, not held-out accuracy, '
            'calibration or a new convergence gate. Noisy bounds are not hard constraints. '
            'Broad-component responsibility is not a probability of source dishonesty. '
            'Probabilities depend on interval width and cannot rank sources by trust.'))


def summarize(run: Path, *, prior_draws: int = 0, prior_seed: int = 20260929,
              report_checks: bool = False, domain: str = 'solar') -> dict:
    if domain not in {'solar', 'adu'}:
        raise ValueError('Journey domain must be solar or adu')
    if prior_draws < 0 or prior_draws == 1:
        raise ValueError('Use zero to disable prior comparison, or at least two prior draws')
    data_path, posterior_path, draws_path = (run / name for name in
        ('data.json', 'posterior.json', 'draws.npz'))
    data = json.loads(data_path.read_text())
    if domain == 'adu' and any(not p['id'].startswith('adu_action_journey__')
                               for p in data['programs']):
        raise ValueError('ADU reporting requires ADU-namespaced compiled input')
    posterior = json.loads(posterior_path.read_text())
    model = VisitHierarchy(data, Config(**posterior['config']))
    prior_states = (np.random.default_rng(prior_seed).normal(size=(prior_draws, model.layout.size))
                    if prior_draws else None)
    with np.load(draws_path, allow_pickle=False) as saved:
        states = saved['z']
        structures = saved['structures']
        likelihood = saved['log_likelihood']
    if states.ndim != 3 or states.shape[2] != model.layout.size:
        raise ValueError('Draw layout no longer matches this model')
    shape = states.shape[:2]
    flat = states.reshape(-1, states.shape[-1])
    routes = structures.reshape(-1, len(model.programs))
    # A bounded saved-target replay, not a second evidence-verification pass.
    for i in np.linspace(0, len(flat)-1, min(3, len(flat)), dtype=int):
        if not np.isclose(model.log_likelihood(flat[i], routes[i]), likelihood.ravel()[i],
                          rtol=0, atol=1e-8):
            raise ValueError('Saved likelihood differs from the current implementation')
    cases = {}
    for pi, (program, raw) in enumerate(zip(model.programs, data['programs'])):
        if any('paths' in r for r in program['routes']):
            raise ValueError('This report needs an explicit joint case-path mixture extension')
        if len(program['cases']) != 1:
            raise ValueError('Reviewed journey compiler must declare exactly one case per program')
        case_id = program['cases'][0]
        index = program['case_index'][case_id]
        reviewed = raw.get('journey_context', {}).get('reviewed_operation_declarations', [])
        kinds = {op['operation_id']:op['component_kind'] for op in reviewed}
        values = defaultdict(list)
        operation_values = defaultdict(list)
        operation_meta = {}
        report_values = defaultdict(list)
        reconstructed_values = defaultdict(list)
        reconstructed = [o for o in raw.get('journey_context', {}).get('reviewed_observation_declarations', [])
                         if o.get('evidence_relation') == 'derived_reconstruction' and o.get('operation_ids')]
        for z, route_vector in zip(flat, routes):
            route_index = int(route_vector[pi])
            trace = model.trace(program, z, model.parameters(z), route_index)
            values['modeled_path_elapsed_days'].append(float(trace.modeled_end[index]))
            values['modeled_occurrence_count'].append(int(trace.visits[index].sum()))
            action_indices = [i for i,op in enumerate(trace.operations)
                              if kinds.get(op.id, 'action_cycle') == 'action_cycle']
            concepts = {(trace.operations[i].actor_role, trace.operations[i].actor_id,
                         trace.operations[i].task_type) for i in action_indices}
            action_occurrences = int(trace.visits[index, action_indices].sum())
            values['unique_actor_action_concepts'].append(len(concepts))
            values['modeled_action_occurrences'].append(action_occurrences)
            values['residual_or_coordination_components'].append(len(trace.operations)-len(action_indices))
            # Distinct materialized IDs may be repeat occurrences of one action.
            values['extra_occurrences_beyond_first_of_each_concept'].append(
                action_occurrences - len(concepts))
            for oi, operation in enumerate(trace.operations):
                operation_meta[operation.id] = dict(action_id=operation.task_type,
                    actor_role=operation.actor_role, actor_id=operation.actor_id,
                    component_kind=kinds.get(operation.id, 'action_cycle'))
                operation_values[operation.id].append(float(trace.durations[index, oi]))
            for observation in program['observations']:
                if len(observation['operators']) != 1:
                    continue  # A report mixture is not an averaged latent duration.
                operator = observation['operators'][0]
                if operator['basis'] == 'unmodeled_duration':
                    continue
                try:
                    quantity = trace.values(operator)[index]
                except (KeyError, UnavailableTraceQuantity):
                    # Native likelihood treats an absent action interpretation as
                    # unavailable. Keep conditional support visible in the report.
                    continue
                report_values[observation['id']].append(float(quantity))
            for declaration in reconstructed:
                ids = declaration['operation_ids']
                operator = dict(basis='activity_event_interval',
                    start=dict(activity_id=ids[0], event='start', occurrence='first'),
                    end=dict(activity_id=ids[-1], event='end', occurrence='last'))
                try:
                    quantity = trace.values(operator)[index]
                except (KeyError, UnavailableTraceQuantity):
                    continue
                reconstructed_values[declaration['observation_id']].append(float(quantity))
        operation_results = {}
        for ident, samples in operation_values.items():
            associated = []
            for observation in program['observations']:
                for operator in observation['operators']:
                    ids = operator.get('activity_ids', [])
                    if operator['basis'] == 'activity_event_interval':
                        ids = [operator['start']['activity_id'], operator['end']['activity_id']]
                    if ident in ids:
                        associated.append(observation['id'])
            operation_results[ident] = dict(operation_meta[ident],
                case_cycle_days=_summarize(samples, shape),
                directly_named_in_clock_observations=sorted(set(associated)),
                active_work_hours=None, intrinsic_actor_capability=None)
        weights = np.asarray([r['prior_weight'] for r in program['routes']], dtype=float)
        weights /= weights.sum()
        cases[case_id] = dict(program_id=program['id'],
            context=raw.get('journey_context', {}),
            case_posterior={name:_summarize(samples, shape) for name, samples in values.items()},
            operations=operation_results,
            observed_clocks={name:_summarize(samples, shape) for name, samples in report_values.items()},
            derived_clocks_not_additional_likelihood={name:_summarize(samples, shape)
                for name,samples in reconstructed_values.items()},
            reviewed_operation_declarations=reviewed,
            inventory_hypotheses=[dict(route_id=r['id'], prior_probability=float(weights[ri]),
                posterior_probability=float((structures[:,:,pi] == ri).mean()))
                for ri,r in enumerate(program['routes'])],
            full_installation_step_count=None,
            population_probability_of_any_rework=None,
            count_interpretation='Only declared actor/action occurrences within this reported journey; not an exhaustive installation inventory or a county requirement count.')
        if prior_states is not None:
            cases[case_id]['conditional_prior_spread_comparison'] = _fixed_serial_prior_comparison(
                model, program, raw, operation_values, prior_states)
        if report_checks:
            cases[case_id]['in_sample_report_checks'] = _case_report_checks(
                model, program, report_values, len(flat))
    actual_case_gate = _actual_case_gate(cases, posterior)
    task_baselines = _elapsed_task_type_baselines(model, data, states, cases)
    precision = posterior.get('precision') if isinstance(posterior.get('precision'), dict) else {}
    return dict(schema_version=domain + '-shared-action-journey-posterior/1',
        inputs={str(p):_sha(p) for p in (data_path, posterior_path, draws_path)},
        fit_numerically_usable=posterior['numerically_usable'],
        fit_posterior_converged=posterior['posterior_converged'],
        fit_diagnostics_flagged=posterior.get('diagnostics_flagged'),
        population_predictions_numerically_acceptable=(
            precision.get('predictions_acceptable') is True),
        actual_case_numerically_usable=actual_case_gate['actual_case_numerically_usable'],
        actual_case_numerical_gate=actual_case_gate,
        prior_spread_comparison=dict(enabled=bool(prior_draws), draws=prior_draws,
            seed=prior_seed if prior_draws else None,
            input_distribution='Independent standard-normal whitened coordinates of the fitted V6 model',
            scope='Case log total, component log duration and logit component share; not population task-mean block coordinates from the toy model',
            posterior_results_require_actual_case_gate=True),
        in_sample_report_checks_enabled=report_checks,
        pooled_elapsed_task_type_baselines=task_baselines,
        cases=cases,
        qualifications=[
            'Intervals describe these reported cases conditional on reviewed action boundaries and the supplied hierarchy, not all applicants.',
            'A modeled cycle can include waiting, handoffs and unreported interior work; it is not a pure service time.',
            'Materialized repeats are counted as repeated occurrences, not new unique action concepts.',
            'No report of rework does not mean zero rework. No installation-wide completeness assumption is made.',
            'Only supplied structural hypotheses receive probabilities; missing unseen steps remain unknown.',
            'County geography and utility identity are separate; no unknown actor is assigned a named department.',
            'The source offset is a report-frame convention, not a learned correction for forum selection.',
            'Unconverged fits are provisional regardless of how plausible any one interval looks.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prior-draws', type=int, default=0,
                        help='Optional prior spread comparison; zero preserves legacy reporting')
    parser.add_argument('--prior-seed', type=int, default=20260929)
    parser.add_argument('--report-checks', action='store_true',
                        help='Optional native-kernel in-sample report reproduction, not held-out scoring')
    parser.add_argument('--domain', choices=('solar', 'adu'), default='solar',
                        help='Report namespace; does not change posterior calculations')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    result = summarize(args.run, prior_draws=args.prior_draws, prior_seed=args.prior_seed,
                       report_checks=args.report_checks, domain=args.domain)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(cases=len(result['cases']), numerically_usable=result['fit_numerically_usable'])))


if __name__ == '__main__':
    main()
