"""Joint-inventory summaries and a dimensionally explicit shared output table.

This first-pass handoff contains presence only. Unknown quantities stay null;
zero would assert no burden. Inventory masks preserve joint posterior dependence
but are NOT executable V6 routes without order/lifecycle/identity reconciliation.
"""
from __future__ import annotations

import numpy as np

from ..latent_gaussian import diagnostics, summary
from .step_burden import conditional_step_burden
from .occupancy import joint_count_summary


TABLE_SCHEMA = "step-burden-table/1"


def linked_draw_table(model, states, routes, step_metadata):
    """Diagnostic burden table from aligned V6 draws, never marginal products.

    This adapter does not confer scientific validation or invent missing
    quantities. A complete supplied joint state is used for every calculation;
    uncertainty in inventory, participation, repeats and resource parameters is
    propagated together. All draws are retained. Metadata is a separate reviewed
    description, not a likelihood or an independent measurement of stringency.
    """
    states = np.asarray(states, dtype=float)
    routes = np.asarray(routes)
    if (states.ndim != 3 or states.shape[0] < 2 or states.shape[1] < 8
            or states.shape[2] != model.layout.size or not np.isfinite(states).all()
            or routes.shape != (*states.shape[:2], len(model.programs))
            or routes.dtype.kind not in 'iu'):
        raise ValueError('Need aligned finite chains x draws V6 states and integer route indices')
    if set(step_metadata) != {p['id'] for p in model.programs}:
        raise ValueError('Metadata must cover every program, without omissions or additions')
    for pi, program in enumerate(model.programs):
        ids = {op.id for route in program['routes'] for op in route['operations']}
        if (not isinstance(step_metadata[program['id']], dict)
                or set(step_metadata[program['id']]) != ids
                or any(not isinstance(v, dict) for v in step_metadata[program['id']].values())):
            raise ValueError('Metadata must cover the full operation union of every program')
        if np.any(routes[:,:,pi] < 0) or np.any(routes[:,:,pi] >= len(program['routes'])):
            raise ValueError('Unknown route index in linked draws')
    flat_routes = routes.reshape(-1, len(model.programs))
    if model.joint_inventory_prior is not None:
        for route_vector in np.unique(flat_routes, axis=0):
            model.joint_inventory_prior.index(route_vector)
    flat = states.reshape(-1, states.shape[-1])
    all_diagnostics = {}

    def summarize(values, key):
        defined = np.array([value is not None for value in values], dtype=bool)
        if not defined.all():
            return dict(status='unavailable' if not defined.any() else 'partially_unavailable',
                        posterior=None, defined_draw_fraction=float(defined.mean()),
                        qualification='Undefined states were not discarded or imputed as zero.')
        x = np.asarray(values, dtype=float).reshape(states.shape[:2])
        if not np.isfinite(x).all():
            raise ValueError('Nonfinite derived burden; do not emit a truncated posterior')
        all_diagnostics[key] = diagnostics(x)
        return dict(status='conditional_model_output_not_validated', posterior=summary(x.reshape(-1)),
                    defined_draw_fraction=1.)

    fields = ('participation_probability', 'expected_visits', 'expected_extra_visits',
              'elapsed_exposure', 'waiting_elapsed', 'service_elapsed', 'dwell_before',
              'payer_hours', 'agency_hours', 'fee_total', 'modeled_end_clock_contribution')
    share_fields = ('elapsed_exposure', 'dwell_before', 'payer_hours', 'agency_hours',
                    'fee_total', 'modeled_end_clock_contribution')
    rows, programs = [], {}
    # Bound peak working memory to one program; no cached draws x all-program
    # resource tensor. Calculating parameters again costs time, not accuracy.
    for pi, program in enumerate(model.programs):
        pid = program['id']
        ids = list(step_metadata[pid])
        values = {aid: {key: [] for key in ('inventory_available', *fields)} for aid in ids}
        shares = {aid: {key: [] for key in share_fields} for aid in ids}
        totals = {key: [] for key in fields}
        available_counts, serial = [], []
        for z, route_vector in zip(flat, flat_routes):
            result = conditional_step_burden(model, program, z, model.parameters(z), int(route_vector[pi]))
            serial.append(result['clock_attribution'] == 'serial_modeled_work_end')
            available_counts.append(sum(row['inventory_available'] for row in result['steps'].values()))
            for key in fields:
                totals[key].append(result['totals'][key])
            for aid in ids:
                for key in values[aid]:
                    values[aid][key].append(result['steps'][aid][key])
                for key in share_fields:
                    shares[aid][key].append(result['steps'][aid]['shares_of_population_mean'][key])
        count_summary = summarize(available_counts, pid+':available_action_count')
        count_summary['posterior'] = joint_count_summary(
            np.asarray(available_counts).reshape(states.shape[:2]), len(ids))
        programs[pid] = dict(
            inventory_available_action_count=count_summary,
            totals={key: summarize(vals, pid+':total:'+key) for key, vals in totals.items()},
            serial_schedule_draw_fraction=float(np.mean(serial)),
            interpretation='Available action types are not required actions per applicant; totals are population expectations conditional on each linked model draw.')
        for aid in ids:
            prefix = pid+':'+aid+':'
            outputs = {key: summarize(vals, prefix+key) for key, vals in values[aid].items()}
            meta = step_metadata[pid][aid]
            rows.append(dict(
                jurisdiction_id=pid, step_id=aid, step_metadata=meta,
                presence_probability=float(np.mean(values[aid]['inventory_available'])),
                presence_interpretation='implementation_contains_action_not_every_applicant_required',
                mandatory_or_conditional_status='not_inferred_from_inventory_presence',
                case_participation_probability=outputs['participation_probability'],
                expected_rounds=dict(outputs['expected_visits'], estimand='population_mean_visits_including_zero_for_absent_or_unvisited_steps'),
                expected_additional_rounds=outputs['expected_extra_visits'],
                elapsed_time=dict(outputs['elapsed_exposure'], unit=model.cfg.elapsed_time_unit,
                                  estimand='population_mean_additive_elapsed_exposure_not_parallel_process_clock'),
                waiting_elapsed=dict(outputs['waiting_elapsed'], unit=model.cfg.elapsed_time_unit),
                service_elapsed=dict(outputs['service_elapsed'], unit=model.cfg.elapsed_time_unit),
                dwell_before=dict(outputs['dwell_before'], unit=model.cfg.elapsed_time_unit),
                active_applicant_time=dict(outputs['payer_hours'], unit='person_hours'),
                agency_service_time=dict(outputs['agency_hours'], unit='person_hours',
                                         qualification='Active labor, not the service-elapsed phase.'),
                cost_and_payee=dict(outputs['fee_total'], currency=meta.get('currency'),
                                    payees=meta.get('payees'),
                                    qualification='Per-visit modeled schedule fees only; no inferred opportunity cost or payee.'),
                stringency_features=dict(status='metadata_only_not_fitted', features=meta.get('stringency_features')),
                obstacle_count=None,
                burden_shares_by_channel={key: summarize(vals, prefix+'share:'+key)
                                          for key, vals in shares[aid].items()},
                modeled_end_clock_contribution=dict(outputs['modeled_end_clock_contribution'], unit=model.cfg.elapsed_time_unit),
                scalar_total_burden=None,
                completion_status='linked_draw_diagnostic_not_scientific_release'))
    flags = {key: d for key, d in all_diagnostics.items() if d['rhat'] is None
             or d['rhat'] > 1.01 or d['ess_bulk'] < 400 or d['ess_tail'] < 200}
    return dict(schema_version=TABLE_SCHEMA, rows=rows, programs=programs,
                draw_shape=list(states.shape[:2]), draw_alignment='one_original_joint_state_per_calculation_no_marginal_recombination',
                diagnostics=all_diagnostics, diagnostics_flagged=flags,
                scientific_release_eligible=False,
                source_validation='not_conferred_by_reporting_adapter',
                identification='not_conferred_by_reporting_adapter; prior-determined values require an external per-block/estimand report',
                scope='Conditional on the supplied executable route, participation and observation model; not an end-to-end extraction validation.',
                cautions=['Nontransitioning inventory indicators can have deceptively good scalar diagnostics; inspect upstream route mixing/support.',
                          'All-unknown fees, omitted labor and nonsummable parallel clock shares remain unavailable.',
                          'Ratios are computed within each draw before summarizing, not ratios of posterior means.',
                          'No agency-capability, source calibration, causal attribution or scalar burden claim follows from this table.'])


def inventory_distribution(joint_presence, step_ids):
    """All empirical inventory masses for ONE jurisdiction, without truncation."""
    z = np.asarray(joint_presence)
    if (z.ndim != 3 or z.shape[-1] != len(step_ids) or z.shape[0] < 1 or z.shape[1] < 1
            or not np.isin(z, [0, 1]).all() or len(set(step_ids)) != len(step_ids)):
        raise ValueError("Expected chains x retained draws x distinct binary steps")
    unique, counts = np.unique(z.reshape(-1, z.shape[-1]), axis=0, return_counts=True)
    return [{"present_step_ids": [step for step, present in zip(step_ids, mask) if present],
             "posterior_mass": float(n / counts.sum()), "retained_draw_count": int(n),
             "v6_route_validated": False}
            for mask, n in zip(unique, counts)]


def presence_only_table(posterior, step_metadata):
    if (posterior.get("schema_version") != "process-occupancy-posterior/1"
            or not posterior.get("numerically_usable")
            or posterior.get("scientific_validation_complete") is not True
            or posterior.get("scientific_release_eligible") is not True):
        raise ValueError("A failed, unvalidated or unreleased posterior cannot populate a scientific burden table")
    if set(step_metadata) != set(posterior["steps"]):
        raise ValueError("Every modeled step needs metadata; do not silently drop unknown steps")
    probability = np.asarray(posterior["presence_probability"], dtype=float)
    if (probability.shape != (len(posterior["jurisdictions"]), len(posterior["steps"]))
            or not np.isfinite(probability).all() or np.any(probability < 0) or np.any(probability > 1)):
        raise ValueError("Invalid presence probabilities")
    rows = []
    for j, jurisdiction in enumerate(posterior["jurisdictions"]):
        for s, step in enumerate(posterior["steps"]):
            rows.append({
                "jurisdiction_id": jurisdiction, "step_id": step, "scope": posterior["scope"],
                "step_metadata": step_metadata[step],
                "presence_probability": float(probability[j, s]),
                "presence_interpretation": "implementation_contains_action_not_every_applicant_required",
                "mandatory_or_conditional_status": "not_inferred_by_binary_occupancy",
                "expected_rounds": None,
                "elapsed_time": {"status": "unestimated", "unit": None, "posterior": None},
                "active_applicant_time": {"status": "unestimated", "unit": None, "posterior": None},
                "agency_service_time": {"status": "unestimated", "unit": None, "posterior": None},
                "cost_and_payee": {"status": "unestimated", "components": None},
                "stringency_features": {"status": "uncompiled", "features": None},
                "obstacle_count": None,
                "burden_shares_by_channel": None,
                "scalar_total_burden": None,
                "completion_status": "presence_only_not_complete_burden_posterior",
            })
    return {"schema_version": TABLE_SCHEMA, "rows": rows,
            "cross_family_schema_agreement": "proposed_pending_claude_confirmation",
            "rules": [
                "Time, money, document requirements and obstacles are separate dimensions.",
                "Expected products/shares require linked joint draws, not products of marginal means.",
                "Elapsed phase shares require an explicit serial/parallel clock attribution; parallel durations cannot simply be summed.",
                "Observed source layers do not establish legal authority or prove a county added a requirement.",
                "No scalar aggregate without explicit valuation weights and uncertainty/sensitivity.",
            ]}
