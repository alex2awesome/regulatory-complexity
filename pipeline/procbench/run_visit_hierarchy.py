"""Immutable independent-chain runner for the experimental joint visit hierarchy."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import multiprocessing
import pathlib
import sys
import time

import numpy as np
import scipy
from scipy.special import roots_hermitenorm

from .bayes_trace_hierarchy import CHANNELS, COUNT_BASES, Config,VisitHierarchy
from .infra.manifest import RunManifest, digest, write
from .approximation_checks import likelihood_weight_check
from .compact_visit_trace import population_quantile
from .cohort_quantiles import cohort_report_observations
from .cohort_histograms import cohort_histogram_observations
from .case_local_likelihood import case_update_views


# Explicit opt-in experimental assumptions; omitted values retain Config defaults.
# Shared by argument creation and the saved-draw refusal guard.
SENSITIVITY_FIELDS = ('unknown_n_report_sd_floor', 'agency_sd', 'operation_sd',
                      'elapsed_prior_median', 'location_sd', 'task_sd',
                      'source_sd', 'common_case_sd', 'case_log_sd_median',
                      'case_log_sd_prior', 'report_sd', 'contamination')


def make_progress_logger(out):
    """Append operational progress, never alter draws or scientific reports."""
    path=pathlib.Path(out)/'run_progress.jsonl'
    with path.open('x'):
        pass
    started=time.monotonic()

    def progress(event):
        row=dict(event, utc=datetime.now(timezone.utc).isoformat(),
                 elapsed_seconds=time.monotonic()-started)
        line=json.dumps(row,allow_nan=False)
        with path.open('a') as stream:
            stream.write(line+'\n')
        print(line,flush=True)
    return progress


def positive_repeat_source_paths(model):
    """Check the optional count contract against literal captured bytes."""
    paths = set()
    for program in model.programs:
        for row in program.get('positive_repeat_counts', []):
            for ref in row['source_bound']:
                path = pathlib.Path(ref['path'])
                raw = path.read_bytes()
                if digest(raw) != ref['sha256']:
                    raise ValueError('Changed positive-repeat source binding: '+str(path))
                text = raw.decode('utf-8')
                if any(quote not in text for quote in ref['quote_segments']):
                    raise ValueError('Positive-repeat quote absent from captured source: '+str(path))
                paths.add(path)
    return sorted(paths, key=str)


def preflight_report(model):
    """Cheap computational/coverage diagnostics, not sampling or identification."""
    observations=[o for p in model.programs for o in p['observations']]
    cohorts=[c for p in model.programs for c in p['quantile_cohorts']]
    histograms=[c for p in model.programs for c in p['histogram_cohorts']]
    observations += [o for c in cohorts for o in cohort_report_observations(
        {k:v for k,v in c.items() if k!='grid'})]
    observations += [o for c in histograms for o in cohort_histogram_observations(c)]
    modeled=[o for o in observations if any(op['basis']!='unmodeled_duration' for op in o['operators'])]
    channel_counts={channel:0 for channel in CHANNELS}
    count_reports=0
    for observation in modeled:
        bases={op['basis'] for op in observation['operators']} - {'unmodeled_duration'}
        if bases & COUNT_BASES:
            count_reports+=1
        else:
            channel=next((ch for ch in CHANNELS[1:] if ch in bases),'elapsed')
            channel_counts[channel]+=1
    # Fixed, reproducible evaluation points; these are NOT posterior draws.
    rng=np.random.default_rng(model.cfg.seed)
    routes=np.zeros(len(model.programs),dtype=int)
    if model.joint_inventory_prior is not None:
        routes=model.joint_inventory_prior.states[0].copy()
    timings=[]
    for z in (np.zeros(model.layout.size), rng.normal(size=model.layout.size),
              rng.normal(size=model.layout.size)):
        started=time.perf_counter()
        ll=float(model.log_likelihood(z,routes))
        timings.append(dict(seconds=time.perf_counter()-started,finite=bool(np.isfinite(ll)),
                            log_likelihood=ll if np.isfinite(ll) else None))
    cfg=model.cfg
    one_copy=cfg.chains*cfg.draws*8*(model.layout.size+len(model.programs)+1)
    report=dict(mode='preflight_only',sampling_performed=False,
        scheduling=model.scheduling_report(),
        clock_boundary_support=model.clock_support_report(),
        duration_priors=model.duration_prior_report(),
        source_support=model.source_support_report(),
        programs=len(model.programs),operations=len(model.operations),
        cases=sum(len(p['cases']) for p in model.programs),sources=len(model.sources),
        delay_selected_cases=sum(len(p['selected_cases']) for p in model.programs),
        selection_adjustment_enabled=bool(model.cfg.selection_sd),
        selection_disabled_warning=('Delay-selected cases are declared, but selection_sd=0 disables the correction.'
            if any(p['selected_cases'] for p in model.programs) and not model.cfg.selection_sd else None),
        case_paths_by_inventory={p['id']:{r['id']:len(r['paths']) for r in p['routes'] if 'paths' in r}
                                 for p in model.programs if any('paths' in r for r in p['routes'])},
        cases_with_explicit_path_scope=sum(len(p['case_path_scope']) for p in model.programs),
        dimensions=model.layout.size,
        elapsed_time_unit=model.cfg.elapsed_time_unit,
        population_integration=model.cfg.population_integration,
        inventory_granularity={p['id']:p['inventory_granularity'] for p in model.programs},
        clock_estimands={p['id']:p['clock_estimand'] for p in model.programs},
        coordinates_by_block={name:len(indices) for name,indices in model.layout.slices.items()},
        observation_rows=len(observations),rows_with_modeled_operators=len(modeled),
        residual_only_rows=len(observations)-len(modeled),
        direct_resource_observations=channel_counts,count_observations=count_reports,
        independent_correction_cohorts=sum(len(p['rates']) for p in model.programs),
        independent_quantile_cohorts=len(cohorts),
        quantile_cohort_report_rows=sum(len(c['reports']) for c in cohorts),
        independent_histogram_cohorts=len(histograms),
        histogram_observed_cases=sum(c['sample_size'] for c in histograms),
        effective_population_sizes={p['id']:len(p['population_normals']) for p in model.programs},
        cohort_quadrature_size=model.cfg.cohort_quadrature_size,
        source_hierarchy_sampler=model.cfg.source_hierarchy_sampler,
        case_scale_sampler=model.cfg.case_scale_sampler,
        channels_without_direct_observations=[c for c,n in channel_counts.items() if not n],
        modeled_channels=list(model.cfg.modeled_channels),
        omitted_resource_channels=[c for c in CHANNELS[1:] if c not in model.cfg.modeled_channels],
        likelihood_probes=timings,probed_route_indices=routes.tolist(),
        finite_at_all_probe_points=all(t['finite'] for t in timings),
        planned_draw_array_bytes_uncompressed=one_copy,
        planned_chain_plus_combined_array_bytes_uncompressed=2*one_copy,
        caveats=['Three first-route evaluations are a cost/syntax probe, not convergence, '
                 'posterior information, complete route support, or a fit-time forecast.',
                 'Coverage describes supplied compiled rows only, not extraction recall or '
                 'unsupported claims in the wider evidence ledger.',
                 'Storage excludes snapshots, predictive/report arrays and peak sampler memory.',
                 'Only declared channels are allocated. Omitted independent resource channels '
                 'are marginalized, not zero burden; active-channel case latents remain sampled.',
                 'Changing channel dimension changes the finite population QMC grid; '
                 'the usual population-integration precision check still applies.'])
    if model.conditional_case_frames:
        report.update(
            conditional_frame_cases=sum(frame['included_case_count']
                                        for frame in model.conditional_case_frames.values()),
            conditional_case_frames=model.conditional_case_frames,
            conditional_frame_qualification=('Hash-bound census within the declared artifact frame only; '
                'not unselected applicants, semantic certification, source-bias learning, or agency-only delay.'))
    if model.joint_inventory_prior is not None:
        prior=model.joint_inventory_prior
        report['joint_inventory_prior']=dict(hypotheses=len(prior.names),
            unique_program_route_likelihoods_per_update=sum(len(np.unique(prior.states[:,pi]))
                                                          for pi in range(len(model.programs))),
            feedback_policy=prior.declaration['feedback_policy'],
            evidence_partition_note=prior.declaration['evidence_partition_note'],
            qualification='Exact finite joint-support Gibbs block, not independent per-program routes; preflight does not certify upstream inventory, ordering, or evidence separation.')
    fixed_priors=model.case_path_prior_report()
    if fixed_priors:
        report['fixed_case_path_priors']=fixed_priors
    joint_reports=model.joint_duration_report_metadata()
    if joint_reports:
        report['joint_duration_reports']=joint_reports
    absent_events=model.absent_event_censoring_metadata()
    if absent_events:
        report['absent_event_censoring']=absent_events
    if any(p.get('positive_repeat_counts') for p in model.programs):
        report['positive_repeat_counts'] = dict(
            rows=sum(len(p.get('positive_repeat_counts', [])) for p in model.programs),
            families={p['id']:p['count_only_repeat_families'] for p in model.programs
                      if p.get('count_only_repeat_families')},
            verified_source_paths=[str(p) for p in positive_repeat_source_paths(model)],
            qualification='Completed-positive count-only likelihood; no q or executable visits. '
                'Byte verification does not certify semantics, independence or selection assumptions.')
    return report


def sampling_model(data,cfg,*,histogram_ridge=False,ridge_step=.05):
    if histogram_ridge:
        from .histogram_ridge_sampler import HistogramRidgeHierarchy
        return HistogramRidgeHierarchy(data,cfg,ridge_step=ridge_step)
    return VisitHierarchy(data,cfg)


def load_source_initialization(path, model, chains):
    """Validate an explicit per-chain start without broadcasting or resuming."""
    path=pathlib.Path(path)
    try:
        with np.load(path,allow_pickle=False) as saved:
            if len(saved.files)!=2 or set(saved.files)!={'z','structures'}:
                raise ValueError('Initial-state NPZ requires exactly z and structures arrays')
            z=np.array(saved['z'],copy=True)
            structures=np.array(saved['structures'],copy=True)
    except ValueError:
        raise
    except (OSError,KeyError) as error:
        raise ValueError('Cannot read initial-state NPZ') from error
    expected_z=(chains,model.layout.size)
    expected_structures=(chains,len(model.programs))
    if (not np.issubdtype(z.dtype,np.number) or not np.isrealobj(z)
            or np.issubdtype(z.dtype,np.bool_)):
        raise ValueError('Initial states must be finite real numeric arrays')
    try:
        z=np.asarray(z,dtype=np.float64)
        finite=bool(np.isfinite(z).all())
    except (TypeError,ValueError,OverflowError) as error:
        raise ValueError('Initial states must be finite numeric arrays') from error
    if (z.shape!=expected_z or structures.shape!=expected_structures or not finite
            or not np.issubdtype(structures.dtype,np.integer)):
        raise ValueError('Initial-state arrays must exactly match chains by dimensions/programs, '
                         'with finite states and integer route indices')
    if any(np.any((structures[:,i]<0)|(structures[:,i]>=len(program['routes'])))
           for i,program in enumerate(model.programs)):
        raise ValueError('Initial-state structures contain an invalid route index')
    if model.joint_inventory_prior is not None:
        for structure in structures:
            model.joint_inventory_prior.index(structure)
    likelihood=[]
    for chain in range(chains):
        try:
            value=float(model.log_likelihood(z[chain],structures[chain]))
        except (FloatingPointError,OverflowError,TypeError,ValueError) as error:
            raise ValueError('Every supplied initial full likelihood must be finite') from error
        if not np.isfinite(value):
            raise ValueError('Every supplied initial full likelihood must be finite')
        likelihood.append(value)
    metadata=dict(schema_version='v6-source-initialization/1',path=str(path),
        sha256=digest(path.read_bytes()),chains=chains,dimensions=model.layout.size,
        programs=len(model.programs),initial_full_log_likelihood=likelihood,
        semantics=('Per-chain explicit computational start only; finite likelihood does not '
                   'certify source feasibility, and this is not draws, resume state, prior data, or evidence.'))
    return (z,structures),metadata


def chain_initial(initial,index):
    """Return one explicit chain row, retaining the sampler's one-chain shape."""
    if initial is None:
        return None
    return (initial[0][index:index+1].copy(),initial[1][index:index+1].copy())


def submit_chains(pool,data,cfg,out,initial,*,histogram_ridge=False,ridge_step=.05,
                  case_local_updates=False):
    """Submit independent chains with no implicit initial-state broadcasting."""
    futures=[]
    for index in range(cfg.chains):
        options=dict(histogram_ridge=histogram_ridge,ridge_step=ridge_step,
                     case_local_updates=case_local_updates)
        if initial is not None:
            options['initial']=chain_initial(initial,index)
        futures.append(pool.submit(worker,data,cfg,index,str(out),**options))
    return futures


def worker(data,cfg,index,out,initial=None,*,histogram_ridge=False,ridge_step=.05,case_local_updates=False):
    if not isinstance(case_local_updates,bool) or (histogram_ridge and case_local_updates):
        raise ValueError('Case-local updates require a boolean and are not combined with histogram ridge')
    model=sampling_model(data,replace(cfg,chains=1,seed=cfg.seed+104729*index),
                         histogram_ridge=histogram_ridge,ridge_step=ridge_step)
    out=pathlib.Path(out)
    with (out/f'chain_{index}.progress.jsonl').open('w') as stream:
        def progress(row):
            row['chain']=index+1
            stream.write(json.dumps(row)+'\n')
            stream.flush()
            if row['iteration']==1 or row['iteration']%500==0:
                print(json.dumps(row),flush=True)
        if case_local_updates:
            z,structures,ll,calls=model.sample(progress,initial=initial,case_local_updates=True)
        else:
            z,structures,ll,calls=model.sample(progress,initial=initial)
    path=out/f'chain_{index}.npz'
    np.savez_compressed(path,z=z,structures=structures,log_likelihood=ll)
    if case_local_updates:
        write(out/f'chain_{index}.transition.json',dict(
            schema_version='case-local-likelihood-transition/1', enabled=True,
            target_changed=False, approximate_likelihood=False,
            full_target_refreshed_before_nonlocal_moves=True,
            default_sampling_unchanged=True,
            qualification='Exact case-coordinate blocks use the existing single-case path likelihood; no new prior or observation.'))
    if cfg.case_scale_sampler == 'interwoven':
        write(out/f'chain_{index}.case_scale_transition.json',
              model.case_scale_transition_report())
    if histogram_ridge:
        write(out/f'chain_{index}.transition.json',dict(model.transition_report(),
            attempts=model.ridge_attempts,accepts=model.ridge_accepts,
            acceptance_fraction=model.ridge_accepts/max(1,model.ridge_attempts)))
    return str(path),calls[0]


def precision_check(model,finer,states,structures):
    flat=states.reshape(-1,states.shape[-1])
    routes=structures.reshape(-1,len(model.programs))
    chosen=np.linspace(0,len(flat)-1,min(256,len(flat)),dtype=int)
    prediction_chosen=set(np.linspace(0,len(flat)-1,min(32,len(flat)),dtype=int))
    chosen=np.unique(np.r_[chosen,list(prediction_chosen)])
    likelihood_changes=[]
    relative_changes=[]
    phase_changes=[]
    phase_nodes,phase_weights=roots_hermitenorm(64)
    phase_weights/=np.sqrt(2*np.pi)
    for i in chosen:
        z,ss=flat[i],routes[i]
        likelihood_changes.append(finer.log_likelihood(z,ss)-model.log_likelihood(z,ss))
        if i not in prediction_chosen:
            continue
        a,b=model.parameters(z),finer.parameters(z)
        if model.cfg.within_visit_phases:
            base_phases=model.phase_means(a)
            fine_phases=model.phase_means(a,phase_nodes,phase_weights)
            phase_changes.extend(float(np.max(np.abs(x-y)/np.maximum(y,np.finfo(float).tiny)))
                                 for x,y in zip(base_phases,fine_phases))
        for pi,(p,pf) in enumerate(zip(model.programs,finer.programs)):
            first=model.trace(p,z,a,int(ss[pi]),True)
            second=finer.trace(pf,z,b,int(ss[pi]),True)
            for event in ('initial_decision','final_decision','modeled_work_end'):
                try:
                    x,y=first.event(event),second.event(event)
                except ValueError:
                    continue
                for q in (.5,.9):
                    relative_changes.append(abs(float(population_quantile(first,x,q)/population_quantile(second,y,q))-1))
    weights=likelihood_weight_check(likelihood_changes)
    max_ll=weights['max_absolute_log_likelihood_change']
    max_prediction=max(relative_changes,default=0.)
    max_phase=max(phase_changes,default=0.)
    cohort_refined=(not any(p['quantile_cohorts'] for p in model.programs)
                    or finer.cfg.cohort_quadrature_size>model.cfg.cohort_quadrature_size)
    base_sizes={p['id']:len(p['population_normals']) for p in model.programs}
    finer_sizes={p['id']:len(p['population_normals']) for p in finer.programs}
    histogram_refined=all((model.cfg.population_integration==finer.cfg.population_integration=='analytic_single_phase')
                          or finer_sizes[p['id']]>base_sizes[p['id']]
                          for p in model.programs if p['histogram_cohorts'])
    collapsed_refined=(model.cfg.population_integration!='collapsed_single_phase_quadrature' or
        (finer.cfg.population_integration=='collapsed_single_phase_quadrature' and
         finer.cfg.collapsed_case_quadrature_size>model.cfg.collapsed_case_quadrature_size))
    return dict(states_checked=len(chosen),base_population_size=model.cfg.population_size,
        population_integration=model.cfg.population_integration,
        population_approximation_check=('analytic_by_contract_grid_independent'
            if model.cfg.population_integration==finer.cfg.population_integration=='analytic_single_phase'
            else ('collapsed_case_gauss_hermite_refinement'
                if model.cfg.population_integration==finer.cfg.population_integration=='collapsed_single_phase_quadrature'
                else 'finite_population_grid_refinement')),
        analytic_formula_independently_validated_by_this_check=False,
        analytic_check_qualification='Equal exact-formula results at different grid sizes do not validate '
            'the formula or source-to-operator binding. Separate reference tests and source review are required.',
        refined_population_size=finer.cfg.population_size,max_absolute_log_likelihood_change=max_ll,
        base_effective_population_sizes=base_sizes,refined_effective_population_sizes=finer_sizes,
        base_cohort_quadrature_size=model.cfg.cohort_quadrature_size,
        refined_cohort_quadrature_size=finer.cfg.cohort_quadrature_size,
        base_collapsed_case_quadrature_size=model.cfg.collapsed_case_quadrature_size,
        refined_collapsed_case_quadrature_size=finer.cfg.collapsed_case_quadrature_size,
        max_relative_clock_quantile_change=max_prediction,
        max_relative_phase_mean_change=max_phase,
        posterior_weight_check=weights, checked_draw_fraction=len(chosen)/len(flat),
        prediction_states_checked=len(prediction_chosen),
        cohort_integration_refined_or_unused=cohort_refined,
        histogram_integration_refined_or_unused=histogram_refined,
        collapsed_case_integration_strictly_refined_or_unused=collapsed_refined,
        likelihood_acceptable=weights['acceptable'] and cohort_refined and histogram_refined and collapsed_refined,
        predictions_acceptable=max_prediction<.02 and max_phase<1e-6 and collapsed_refined,
        caveat='Finite checked posterior states, not a uniform error bound or full calibration')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--data')
    mode.add_argument('--diagnose-run', help='Information report on saved V6 draws; no sampling or score changes')
    parser.add_argument('--draws-file', help='Saved draws when a prediction-only run references another directory')
    parser.add_argument('--out',required=True)
    parser.add_argument('--preflight',action='store_true',
                        help='Validate compiled inputs and report dimensions/cost/coverage; no sampling')
    parser.add_argument('--initial-state',
                        help='NPZ with exact per-chain z and structures arrays; computational start only, never resume')
    parser.add_argument('--case-local-updates',action='store_true',
                        help='Exact target-preserving single-case likelihood updates where guarded views exist; off by default')
    parser.add_argument('--case-update-block-size',type=int,default=0,
                        help='Chunk per-case ESS coordinate blocks; zero preserves the historical full-case block')
    parser.add_argument('--marginalize-conditional-cases',action='store_true',
                        help='Integrate independent case durations in the guarded one-phase report-frame contract; same V6 target')
    parser.add_argument('--case-quadrature-size',type=int,default=128,
                        help='Log-Gamma precision quadrature nodes for explicit conditional-case marginalization')
    parser.add_argument('--histogram-ridge-moves',action='store_true',
                        help='Add target-preserving joint spread/location moves for guarded analytic one-phase histograms; off by default')
    parser.add_argument('--histogram-ridge-step',type=float,default=.05,
                        help='Fixed log-spread proposal scale for --histogram-ridge-moves')
    parser.add_argument('--within-visit-phases',action='store_true',
                        help='Explicitly enable a weak logistic-normal service-fraction hierarchy')
    parser.add_argument('--inter-operation-dwell',action='store_true',
                        help='Explicitly enable declared between-operation waiting with its own prior; routes may not declare dwells without it')
    parser.add_argument('--observed-channels-only',action='store_true',
                        help='Keep elapsed clocks and directly observed labor channels; marginalize unused independent labor priors')
    parser.add_argument('--dwell-case-sd',type=float,default=.5,
                        help='Per-case log spread of a declared dwell; zero allocates no per-case waiting latent')
    parser.add_argument('--case-path-logit-sd',type=float,default=1.5,
                        help='Logistic-normal scale for per-case path frequencies; zero fixes declared base weights')
    parser.add_argument('--hierarchy-sampler',choices=('blocked','operation_centered'),default='blocked',
                        help='Transition kernel only; operation_centered retains the same prior, likelihood and coordinates')
    parser.add_argument('--source-hierarchy-sampler',choices=('blocked','interwoven'),default='blocked',
                        help='Source transition only; interwoven splits Gaussian ESS blocks and adds Jacobian-correct fixed-offset scale moves')
    parser.add_argument('--case-scale-sampler',choices=('blocked','interwoven'),default='blocked',
                        help='Case-spread transition only; interwoven fixes realized operation effects with exact prior/Jacobian correction')
    parser.add_argument('--selection-sd',type=float,default=0.,
                        help='Half-normal scale for log relative inclusion weight of declared delay-selected cases; zero disables correction')
    parser.add_argument('--elapsed-task-priors',
                        help='JSON elapsed-task-priors/1 specification: fixed median declared elapsed units per complete visit, with rationale; not labor hours')
    parser.add_argument('--elapsed-time-unit',choices=('calendar_days','business_days'),default='calendar_days',
                        help='Native elapsed unit; must match data declaration. No calendar conversion is performed')
    parser.add_argument('--population-integration',choices=('qmc','analytic_single_phase','collapsed_single_phase_quadrature'),default='qmc',
                        help='Exact lognormal population functionals only for validated single coarse phases; default preserves historical QMC targets')
    for field in SENSITIVITY_FIELDS:
        parser.add_argument('--'+field.replace('_','-'),type=float,default=None,
                            help='Explicit sensitivity override; omitted retains the Config default, not empirical calibration')
    for name,default in [('chains',4),('warmup',1000),('draws',2000),('workers',2),
                         ('population-size',256),('cohort-quadrature-size',256),
                         ('collapsed-case-quadrature-size',64),('seed',2026092001)]:
        parser.add_argument('--'+name,type=int,default=default)
    args=parser.parse_args(argv)
    if args.preflight and args.diagnose_run:
        parser.error('--preflight requires --data, not --diagnose-run')
    if args.diagnose_run and (args.initial_state or args.case_local_updates):
        parser.error('Saved-draw diagnostics cannot use source initialization or case-local updates')
    if args.diagnose_run and args.marginalize_conditional_cases:
        parser.error('Saved-draw diagnostics cannot change case integration')
    if args.marginalize_conditional_cases and (args.initial_state or args.case_local_updates):
        parser.error('Conditional-case marginalization does not accept source initialization or case-local updates')
    if args.histogram_ridge_moves and (args.diagnose_run or args.marginalize_conditional_cases):
        parser.error('Histogram ridge sampling requires ordinary --data mode, not saved diagnostics or conditional-case integration')
    if args.histogram_ridge_moves and (args.initial_state or args.case_local_updates):
        parser.error('Histogram ridge sampling does not combine with source initialization or case-local updates')
    if args.case_scale_sampler == 'interwoven' and (args.diagnose_run
            or args.marginalize_conditional_cases or args.histogram_ridge_moves):
        parser.error('Case-scale interweaving requires ordinary V6 mode without histogram-ridge moves')
    if not args.histogram_ridge_moves and args.histogram_ridge_step != .05:
        parser.error('--histogram-ridge-step requires --histogram-ridge-moves')
    if not args.marginalize_conditional_cases and args.case_quadrature_size != 128:
        parser.error('--case-quadrature-size requires --marginalize-conditional-cases')
    if args.observed_channels_only and args.diagnose_run:
        parser.error('Saved-draw diagnostics must retain their original channel layout')
    if args.elapsed_task_priors and args.diagnose_run:
        parser.error('Saved-draw diagnostics must retain their original timing priors')
    sensitivity_fields=SENSITIVITY_FIELDS
    if args.diagnose_run and any(getattr(args,key) is not None for key in sensitivity_fields):
        parser.error('Saved-draw diagnostics cannot override their original sensitivity assumptions')
    out=pathlib.Path(args.out)
    if out.exists() or args.workers<1:
        raise ValueError('Choose a fresh directory and positive worker count')
    if args.diagnose_run:
        run=pathlib.Path(args.diagnose_run)
        posterior=json.loads((run/'posterior.json').read_text())
        data=json.loads((run/'data.json').read_text())
        if posterior.get('inference'):
            from .marginal_conditional_frames import INTEGRATION_KIND, MarginalConditionalFrame
            if posterior['inference'].get('kind') != INTEGRATION_KIND:
                raise ValueError('Unknown saved inference contract')
            model=MarginalConditionalFrame(data,Config(**posterior['config']),
                posterior['inference']['quadrature_size'])
            if model.inference != posterior['inference']:
                raise ValueError('Saved marginal integration settings differ from implementation')
        else:
            model=VisitHierarchy(data,Config(**posterior['config']))
        draws_path=pathlib.Path(args.draws_file) if args.draws_file else run/'draws.npz'
        with np.load(draws_path) as saved:
            states,structures,ll=saved['z'],saved['structures'],saved['log_likelihood']
        if states.shape[-1]!=model.layout.size:
            raise ValueError('Saved parameterization differs from the current layout')
        flat=states.reshape(-1,states.shape[-1])
        routes=structures.reshape(-1,len(model.programs))
        chosen=np.linspace(0,len(flat)-1,min(8,len(flat)),dtype=int)
        difference=max(abs(model.log_likelihood(flat[i],routes[i])-ll.ravel()[i]) for i in chosen)
        if not np.isfinite(difference) or difference>1e-8:
            raise ValueError('Saved target does not match; use its frozen source for information diagnostics')
        report=model.information_report(states, sampling_converged=posterior['posterior_converged'])
        record=RunManifest(out, {}, operation='v6.diagnose_saved_draws',
            inputs=[run/'data.json',run/'posterior.json',draws_path],
            config=asdict(model.cfg), seeds={}, hidden_truth_read=False,
            source_root=pathlib.Path(__file__).parent, sources=['run_visit_hierarchy.py'])
        write(out/'identification.json',report)
        record.complete(**dict(mode='saved_draw_information_only', original_run=str(run),
            input_sha256={str(p):digest(p.read_bytes()) for p in (run/'data.json',run/'posterior.json',draws_path)},
            saved_likelihood_states_checked=len(chosen),max_likelihood_difference=difference,
            no_sampling=True,no_scores_changed=True,hidden_truth_read=False))
        print(json.dumps(dict(coordinates=report['coordinates'],
            below_10_percent=report['coordinates_below_10_percent'],
            blocks={name:row['mean_variance_contraction'] for name,row in report['blocks'].items()})),flush=True)
        return
    if args.draws_file:
        raise ValueError('--draws-file is only for --diagnose-run')
    path=pathlib.Path(args.data)
    data=json.loads(path.read_text())
    inputs=[path]
    cfg=Config(**{key:getattr(args,key) for key in ('chains','warmup','draws','population_size','seed',
                                                 'within_visit_phases','inter_operation_dwell',
                                                 'dwell_case_sd','case_path_logit_sd',
                                                 'cohort_quadrature_size','hierarchy_sampler',
                                                 'collapsed_case_quadrature_size',
                                                 'source_hierarchy_sampler','case_scale_sampler','selection_sd',
                                                 'case_update_block_size',
                                                 'elapsed_time_unit','population_integration')})
    cfg=replace(cfg,**{key:getattr(args,key) for key in sensitivity_fields if getattr(args,key) is not None})
    if args.elapsed_task_priors:
        prior_path=pathlib.Path(args.elapsed_task_priors)
        specification=json.loads(prior_path.read_text())
        if (not isinstance(specification,dict)
                or specification.get('schema_version')!='elapsed-task-priors/1'
                or specification.get('clock')!=f'single_visit_cycle_{cfg.elapsed_time_unit}_including_wait_and_service'
                or not isinstance(specification.get('rationale'),str)
                or not specification['rationale'].strip()
                or not isinstance(specification.get('medians_days'),dict)
                or not specification['medians_days']):
            raise ValueError('Elapsed task prior file requires schema, complete-visit clock, nonempty median map and rationale')
        cfg=replace(cfg,elapsed_task_prior_medians=tuple(specification['medians_days'].items()))
        inputs.append(prior_path)
    if args.observed_channels_only:
        bases={op['basis'] for p in data['programs'] for o in p.get('observations',[])+p.get('quantile_cohorts',[])
               for op in o['operators']}
        cfg=replace(cfg,modeled_channels=tuple(ch for ch in CHANNELS if ch=='elapsed' or ch in bases))
    if args.marginalize_conditional_cases:
        from .marginal_conditional_frames import run_marginal_frame
        report=run_marginal_frame(data,cfg,out,inputs,
            quadrature_size=args.case_quadrature_size,workers=args.workers,
            preflight=args.preflight)
        print(json.dumps(report),flush=True)
        return
    model=sampling_model(data,cfg,histogram_ridge=args.histogram_ridge_moves,
                         ridge_step=args.histogram_ridge_step)
    inputs.extend(path for path in positive_repeat_source_paths(model) if path not in inputs)
    initial,initial_metadata=None,None
    if args.initial_state:
        initial_path=pathlib.Path(args.initial_state)
        initial,initial_metadata=load_source_initialization(initial_path,model,cfg.chains)
        inputs.append(initial_path)
    case_local_metadata=None
    if args.case_local_updates:
        views=case_update_views(model)
        case_local_metadata=dict(enabled=True,case_coordinate_blocks=len(views),
            target_changed=False,approximate_likelihood=False,
            qualification='Exact case-coordinate views only; full target is refreshed before every nonlocal move.')
    source=pathlib.Path(__file__).parent
    if args.preflight:
        legacy={}
        if initial_metadata is not None:
            legacy['source_initialization']=initial_metadata
        if case_local_metadata is not None:
            legacy['case_local_updates']=case_local_metadata
        record=RunManifest(out, legacy, operation='v6.preflight', inputs=inputs, config=asdict(cfg),
            seeds=dict(seed=cfg.seed,population_seed=cfg.population_seed,cohort_seed=cfg.cohort_seed),hidden_truth_read=False,
            source_root=source,sources=['run_visit_hierarchy.py'])
        report=preflight_report(model)
        if initial_metadata is not None:
            report['source_initialization']=initial_metadata
        if case_local_metadata is not None:
            report['case_local_updates']=case_local_metadata
        if cfg.case_scale_sampler == 'interwoven':
            report['case_scale_transition']=model.case_scale_transition_report()
        if args.histogram_ridge_moves:
            report['transition_kernel']=model.transition_report()
        write(out/'data.json',data)
        if args.elapsed_task_priors:
            write(out/'elapsed_task_priors.json',specification)
        write(out/'preflight.json',report)
        record.complete(sampling_performed=False,
                        report_sha256=digest((out/'preflight.json').read_bytes()))
        print(json.dumps(report),flush=True)
        return
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),config=asdict(cfg),
        input_sha256={str(p):digest(p.read_bytes()) for p in inputs},
        hidden_truth_read_during_inference=False,dimensions=model.layout.size,
        scope='Joint visit/agency/task development; no text-pipeline or LLM-superiority claim',
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__))
    if initial_metadata is not None:
        manifest['source_initialization']=initial_metadata
    if case_local_metadata is not None:
        manifest['case_local_updates']=case_local_metadata
    if args.histogram_ridge_moves:
        manifest['transition_kernel']=model.transition_report()
    if cfg.case_scale_sampler == 'interwoven':
        manifest['case_scale_transition']=model.case_scale_transition_report()
    record=RunManifest(out, manifest, operation='v6.fit', inputs=inputs, config=asdict(cfg),
        seeds=dict(seed=cfg.seed, population_seed=cfg.population_seed, cohort_seed=cfg.cohort_seed,
                   chain_stride=104729), hidden_truth_read=False,
        source_root=source, sources=['run_visit_hierarchy.py'])
    progress=make_progress_logger(out)
    write(out/'data.json',data)
    if args.elapsed_task_priors:
        write(out/'elapsed_task_priors.json',specification)
    progress(dict(stage='sampling', chains=cfg.chains, draws_per_chain=cfg.draws,
                  warmup_per_chain=cfg.warmup))
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=submit_chains(pool,data,cfg,out,initial,
            histogram_ridge=args.histogram_ridge_moves,ridge_step=args.histogram_ridge_step,
            case_local_updates=args.case_local_updates)
        completed=[future.result() for future in futures]
    progress(dict(stage='saving_combined_draws'))
    arrays=[np.load(path) for path,_ in completed]
    z=np.concatenate([a['z'] for a in arrays])
    structures=np.concatenate([a['structures'] for a in arrays])
    ll=np.concatenate([a['log_likelihood'] for a in arrays])
    np.savez_compressed(out/'draws.npz',z=z,structures=structures,log_likelihood=ll)
    report=model.report(z,structures,ll,progress=progress)
    if args.case_local_updates:
        report['case_local_updates']=dict(case_local_metadata,
            chains=[json.loads((out/f'chain_{index}.transition.json').read_text())
                    for index in range(cfg.chains)])
    if cfg.case_scale_sampler == 'interwoven':
        report['case_scale_transition']=dict(model.case_scale_transition_report(),
            chains=[json.loads((out/f'chain_{index}.case_scale_transition.json').read_text())
                    for index in range(cfg.chains)])
    if args.histogram_ridge_moves:
        report['transition_kernel']=dict(model.transition_report(),
            chains=[json.loads((out/f'chain_{index}.transition.json').read_text())
                    for index in range(cfg.chains)])
    progress(dict(stage='integration_precision_check'))
    finer=VisitHierarchy(data,replace(cfg,population_size=cfg.population_size*4,
                                     cohort_quadrature_size=cfg.cohort_quadrature_size*4,
                                     collapsed_case_quadrature_size=min(1024,cfg.collapsed_case_quadrature_size*2)))
    report['precision']=precision_check(model,finer,z,structures)
    report['numerically_usable']=(report['posterior_converged'] and report['precision']['likelihood_acceptable']
                                   and report['precision']['predictions_acceptable'])
    progress(dict(stage='saving_posterior_report'))
    write(out/'posterior.json',report)
    record.complete(calls=[c for _,c in completed],
                    posterior_sha256=digest((out/'posterior.json').read_bytes()),
                    draws_sha256=digest((out/'draws.npz').read_bytes()))
    progress(dict(stage='completed', numerically_usable=report['numerically_usable']))
    print(json.dumps(dict(numerically_usable=report['numerically_usable'],precision=report['precision'],
                         flagged=len(report['diagnostics_flagged']),programs=report['programs'])),flush=True)


if __name__=='__main__':
    main()
