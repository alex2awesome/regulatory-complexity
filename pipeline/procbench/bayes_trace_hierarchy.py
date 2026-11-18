"""Joint visit-clock, rework and agency/task hierarchy (experimental v6).

Unlike combining separately fitted posteriors, every claim enters one likelihood
and one prior. Totals, activity cycles, counts and independently supplied work hours
observe the SAME case visits. Finite inventory hypotheses are shared across a
program. Optional nested paths are instead drawn per case and marginalized jointly
over that case's reports; their population frequencies have separate priors.

Current limits: no abandonment/competing risks or nested/interleaved repeat blocks;
repeat-cycle durations are perfectly correlated within a case; no text compiler yet.
Source and operator hypotheses must be provided explicitly, never read from truth.
"""
from dataclasses import asdict, dataclass
from copy import deepcopy
import math
import json

import numpy as np
from scipy.linalg import cho_solve, helmert, solve_triangular
from scipy.special import betaincinv, expit, logsumexp, ndtr, ndtri, roots_hermitenorm, xlogy, xlog1py
from scipy.stats import qmc

from .bayes_hierarchy import Layout, log_interval
from .compact_visit_trace import (CLOCK_EVENTS, CLOCK_EVENT_MARKERS, MONEY_BASES, Block, CompactTrace, Operation,
                                  PopulationTraceMixture, UnavailableTraceQuantity,
                                  observation_population, population_quantile,
                                  population_statistic, unit_dwell_array, validate_operator)
from .latent_gaussian import diagnostics, elliptical_slice, information_report, summary
from .cohort_quantiles import CohortQuantileGrid, cohort_report_observations
from .cohort_histograms import (cohort_histogram_observations, histogram_log_probability,
                                population_bin_probabilities)
from .decision_scope_binding import validate_bound_observations
from .typical_range_reports import (typical_range_log_probability,
                                    validate_typical_range_observation)
from .analytic_phase import (phase_histogram_log_probability,
                             validate_collapsed_single_phase_program,
                             validate_single_phase_program, phase_spread_sensitive_factors)
from .source_comparisons import source_comparison_report
from .source_offset_hierarchy import SourceOffsetHierarchy
from .source_precision import (FALLBACK_KIND, FIXED_KIND,
                               elapsed_report_log_scale, precision_annotation)
from .conditional_case_frames import (SAMPLING_KIND as CONDITIONAL_FRAME_SAMPLING,
                                      validate_conditional_case_frames)
from .case_path_priors import validate_case_path_priors
from .joint_duration_reports import (validate_joint_duration_reports,
                                      shared_log_error_probability)
from .absent_event_censoring import (validate_absent_event_censoring,
                                    structural_survival_is_one)
from .case_local_likelihood import case_update_views, case_log_likelihood, refresh_full_likelihood
from .case_scale_interweave import (case_scale_interweave_update as _case_scale_interweave_update,
                                    transition_report as case_scale_transition_report)
from .joint_inventory_prior import JointInventoryPrior
from .positive_repeat_counts import (validate_positive_repeat_counts,
                                     log_probability as positive_repeat_log_probability)
from .operation_location_design import compile_operation_location_design
from .sampler_joint_blocks import compile_sampler_joint_blocks


CHANNELS = ('elapsed','payer_hours','agency_hours')
COUNT_BASES = {'additional_rounds','visit_count','operation_count','agency_count'}
# MONEY_BASES is imported, not a channel: a published fee adds no sampled
# coordinate. Like counts it carries no resource channel of its own, so it is
# excluded from the channel-unit check rather than declared in CHANNELS.
PHASE_BASES = {'wait_elapsed', 'service_elapsed'}
SOURCE_HIERARCHY_INTERWEAVE_STEP = .5


@dataclass(frozen=True)
class Config:
    seed: int = 2026092001
    chains: int = 4
    warmup: int = 1000
    draws: int = 2000
    population_size: int = 128
    population_seed: int = 301
    elapsed_prior_median: float = 7.
    elapsed_time_unit: str = 'calendar_days'
    population_integration: str = 'qmc'
    collapsed_case_quadrature_size: int = 64
    # Fixed task-specific log-location baselines in the declared elapsed unit of a complete
    # single visit (waiting + service), NOT hours of active work. Empty preserves
    # historical targets exactly. These inputs add no sampled coordinates.
    elapsed_task_prior_medians: tuple[tuple[str, float], ...] = ()
    work_prior_median: float = 1.
    location_sd: float = 2.
    agency_sd: float = 1.
    task_sd: float = .75
    operation_sd: float = .5
    case_log_sd_median: float = .6
    case_log_sd_prior: float = .4
    common_case_sd: float = .25
    source_sd: float = .25
    report_sd: float = .25
    # Ordinary population summaries with unresolved n, not finite cohorts or
    # explicitly modeled subjective typical ranges. A sensitivity assumption,
    # not a source-quality ranking or a learned effective sample size.
    unknown_n_report_sd_floor: float = .5
    count_error_scale: float = .5
    contamination: float = .05
    selection_sd: float = 0.
    selection_width: float = .35
    within_visit_phases: bool = False
    phase_location_sd: float = 3.
    phase_agency_sd: float = 1.
    phase_task_sd: float = 1.
    phase_operation_sd: float = 1.
    phase_case_sd: float = .75
    # Inter-operation dwell: elapsed time between operations during which nobody
    # is working. OFF by default, and a route may not declare a dwell unless it is
    # on, so every historical layout, coordinate and saved-seed replay is unchanged.
    # Waiting has its own two-level hierarchy (population + gap) and its own prior
    # scales: it must not inherit the operation duration parameters, and it has no
    # agency or task level because nobody is acting. The prior median deliberately
    # matches the elapsed one so the prior asserts nothing about whether waiting
    # dominates; `dwell_location_sd` is wide enough for a fit to say that it does.
    inter_operation_dwell: bool = False
    dwell_prior_median: float = 7.
    dwell_location_sd: float = 2.
    dwell_site_sd: float = 1.
    dwell_case_sd: float = .5
    # Keep historical saved targets/layouts unchanged unless a run explicitly
    # omits unobserved resource channels. Elapsed is always retained for clocks.
    modeled_channels: tuple[str, ...] = CHANNELS
    # Per-case paths are marginalized jointly across reports, not sampled as a
    # program-wide structural choice. Zero keeps the explicitly supplied weights.
    case_path_logit_sd: float = 1.5
    cohort_quadrature_size: int = 256
    cohort_seed: int = 811
    # A transition-kernel option, not a different likelihood or hierarchy.
    # Keep the historical transition sequence available for saved-seed replay.
    hierarchy_sampler: str = 'blocked'
    # Optional source-hierarchy transition only.  ``blocked`` preserves the
    # historical single ESS block and RNG sequence. ``interwoven`` splits the
    # independent-normal ESS blocks and adds fixed-actual-effect scale moves.
    source_hierarchy_sampler: str = 'blocked'
    # Optional case-spread/residual interweave. ``blocked`` is an exact legacy
    # transition-sequence/RNG replay; ``interwoven`` changes only the kernel.
    case_scale_sampler: str = 'blocked'
    # Transition blocking only. Zero preserves one ESS block per full case and
    # the historical RNG sequence; a positive value chunks each case row.
    case_update_block_size: int = 0

    def __post_init__(self):
        if self.elapsed_time_unit not in ('calendar_days', 'business_days'):
            raise ValueError('Elapsed time unit must be calendar_days or business_days')
        if self.population_integration not in ('qmc','analytic_single_phase',
                                                'collapsed_single_phase_quadrature'):
            raise ValueError('Unknown population integration method')
        if self.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') and (
                self.within_visit_phases or self.inter_operation_dwell):
            raise ValueError('Analytic single-phase integration forbids phase fractions and dwells')
        raw_task_priors = self.elapsed_task_prior_medians
        if not isinstance(raw_task_priors, (tuple, list)):
            raise ValueError('Elapsed task priors require distinct (task_type, median_days) pairs')
        task_priors = []
        for pair in raw_task_priors:
            if (not isinstance(pair, (tuple, list)) or len(pair) != 2
                    or not isinstance(pair[0], str) or not pair[0].strip()
                    or pair[0] != pair[0].strip() or isinstance(pair[1], bool)
                    or not isinstance(pair[1], (int, float))
                    or not math.isfinite(pair[1]) or pair[1] <= 0):
                raise ValueError('Elapsed task priors require named tasks and positive finite median days')
            task_priors.append((pair[0], float(pair[1])))
        if len({key for key, _ in task_priors}) != len(task_priors):
            raise ValueError('Elapsed task priors require distinct task names')
        object.__setattr__(self, 'elapsed_task_prior_medians', tuple(sorted(task_priors)))
        channels = tuple(self.modeled_channels)
        if (not channels or channels[0] != 'elapsed' or
                channels != tuple(ch for ch in CHANNELS if ch in channels)):
            raise ValueError('Modeled channels must be distinct, canonical-order channels including elapsed')
        object.__setattr__(self, 'modeled_channels', channels)
        if self.hierarchy_sampler not in ('blocked', 'operation_centered'):
            raise ValueError('Unknown hierarchy sampler')
        if self.source_hierarchy_sampler not in ('blocked', 'interwoven'):
            raise ValueError('Unknown source hierarchy sampler')
        if self.case_scale_sampler not in ('blocked', 'interwoven'):
            raise ValueError('Unknown case-scale sampler')
        if (isinstance(self.case_update_block_size, bool)
                or not isinstance(self.case_update_block_size, int)
                or self.case_update_block_size < 0):
            raise ValueError('case_update_block_size must be a nonnegative integer')
        positive = (self.elapsed_prior_median,self.work_prior_median,self.location_sd,
            self.case_log_sd_median,self.report_sd,self.count_error_scale,self.selection_width,
            self.phase_location_sd,self.dwell_prior_median,self.dwell_location_sd)
        nonnegative = (self.agency_sd,self.task_sd,self.operation_sd,self.case_log_sd_prior,
                       self.common_case_sd,self.source_sd,self.unknown_n_report_sd_floor,self.selection_sd,self.phase_agency_sd,
                       self.phase_task_sd,self.phase_operation_sd,self.phase_case_sd,
                       self.case_path_logit_sd,self.dwell_site_sd,self.dwell_case_sd)
        if any(not math.isfinite(x) or x<=0 for x in positive) or any(
                not math.isfinite(x) or x<0 for x in nonnegative):
            raise ValueError('Invalid hierarchy scales')
        if (self.chains<1 or self.warmup<0 or self.draws<8 or self.population_size<16
                or not 0<=self.contamination<1 or not isinstance(self.within_visit_phases,bool)
                or not isinstance(self.inter_operation_dwell,bool)):
            raise ValueError('Invalid sampling/contamination settings')
        if (isinstance(self.cohort_quadrature_size,bool) or not isinstance(self.cohort_quadrature_size,int)
                or self.cohort_quadrature_size<16 or self.cohort_quadrature_size & (self.cohort_quadrature_size-1)):
            raise ValueError('Cohort integration size must be a power of two of at least 16')
        if (isinstance(self.collapsed_case_quadrature_size,bool) or
                not isinstance(self.collapsed_case_quadrature_size,int) or
                self.collapsed_case_quadrature_size not in (16,32,64,128,256,512,1024)):
            raise ValueError('Collapsed-case quadrature size must be a supported power of two from 16 through 1024')


def repeat_quantiles(uniforms, probability_any, probability_continue):
    """Vector inverse of the unbounded hurdle-geometric law; no retry cap."""
    u=np.asarray(uniforms,dtype=float)
    q,r=float(probability_any),float(probability_continue)
    if np.any((u<0)|(u>=1)) or not 0<=q<=1 or not 0<=r<1:
        raise ValueError('Invalid normalized repeat law or uniform')
    result=np.zeros(u.shape,dtype=np.int64)
    active=u>1-q
    if q==1:
        active=np.ones(u.shape,dtype=bool)
    if q and active.any():
        if r==0:
            result[active]=1
        else:
            values=np.maximum(1,np.ceil((np.log1p(-u[active])-math.log(q))/math.log(r)))
            if np.any(values>=np.iinfo(np.int64).max):
                raise FloatingPointError('Repeat count exceeds numerical integer range')
            result[active]=values.astype(np.int64)
    return result


def count_log_probability(lower,upper,center,scale=.5,contamination=.05):
    """Normalized nonnegative discrete-Laplace reporting error + geometric outliers."""
    c=np.asarray(center,dtype=float)
    if np.any(c<0) or np.any(c!=np.floor(c)) or scale<=0:
        raise ValueError('The latent count must be a nonnegative integer')
    t=math.exp(-1/scale)
    normalizer=(1+t-np.power(t,c+1))/(1-t)
    def cdf(k):
        k=np.floor(np.asarray(k))
        left=np.power(t,np.maximum(c-k,0))*(1-t**(k+1))/(1-t)
        right=(1-np.power(t,c+1)+t*(1-np.power(t,np.maximum(k-c,0))))/(1-t)
        return np.where(k<0,0.,np.where(k<c,left,right)/normalizer)
    lo=np.maximum(0,np.ceil(lower))
    hi=np.floor(math.inf if upper is None else np.asarray(upper))
    regular=np.maximum(0,cdf(hi)-cdf(lo-1))
    broad=np.power(2.,-lo)-np.power(2.,-(hi+1))
    probability=np.where(hi<lo,0.,(1-contamination)*regular+contamination*broad)
    with np.errstate(divide='ignore'):
        return np.log(probability)


def duration_log_probability(lower,upper,values,offset=0.,scale=.25,contamination=.05):
    values=np.asarray(values)
    lower=np.asarray(lower,dtype=float)
    lo=np.full(lower.shape,-math.inf)
    np.log(lower,out=lo,where=lower>0)
    hi=np.log(math.inf if upper is None else np.asarray(upper))
    location=np.log(np.maximum(values,np.finfo(float).tiny))+offset
    regular=log_interval(lo,hi,location,scale)
    if not contamination:
        return regular
    return np.logaddexp(math.log1p(-contamination)+regular,
                       math.log(contamination)+log_interval(lo,hi,location,2.))


def duration_report_log_probability(observation,values,offset=0.,scale=.25,contamination=.05):
    """One reported event, optionally a union of disjoint numerical intervals.

    Split-unit alternatives in one phrase are not independent reports and their
    overlap must not be counted twice. Intervals are validated at model creation.
    """
    intervals=observation.get('report_intervals')
    if intervals is None:
        return duration_log_probability(observation['lower'],observation['upper'],values,
                                        offset,scale,contamination)
    return logsumexp(np.stack([duration_log_probability(lo,hi,values,offset,scale,contamination)
                              for lo,hi in intervals]),axis=0)


def unmodeled_duration_log_probability(lower,upper,operator,intervals=None):
    """Normalized absolute log-duration reference, independent of the process.

    A finite interpretation set may not contain the report's actual meaning.
    This is not the relative reporting-noise contamination around a latent clock.
    """
    observation=dict(lower=lower,upper=upper)
    if intervals is not None:
        observation['report_intervals']=intervals
    return duration_report_log_probability(observation,operator['median_days'],
                                          scale=operator['log_scale'],contamination=0.)


class VisitHierarchy:
    def __init__(self,data,cfg=Config()):
        self.data,self.cfg,self.layout=data,cfg,Layout()
        if cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') and cfg.modeled_channels!=('elapsed',):
            raise ValueError('Analytic single-phase integration requires elapsed-only modeled channels')
        if cfg.population_integration=='collapsed_single_phase_quadrature' and cfg.selection_sd:
            raise ValueError('Collapsed single-phase quadrature requires selection_sd=0')
        if data.get('elapsed_time_unit', 'calendar_days') != cfg.elapsed_time_unit:
            raise ValueError('Data and model elapsed time units must match; no calendar conversion is implicit')
        self.conditional_case_frames = validate_conditional_case_frames(data,cfg)
        # Validate optional review bindings before any sampling. This is a
        # design/provenance screen only and adds no likelihood or coordinates.
        self.source_comparisons = source_comparison_report(data)
        self.source_offset_hierarchy = None
        self.source_precision_active = False
        self.active_channels = tuple(CHANNELS.index(ch) for ch in cfg.modeled_channels)
        self.programs=[]
        self.operations=[]
        self.agencies=[]
        self.tasks=[]
        self.sources=[]
        # One dwell site per (program, operation) gap, pooled across route/path
        # hypotheses exactly as operation identities are: alternative inventories
        # describe the same waiting, so they must share its parameter.
        self.dwell_sites=[]
        self.dwell_index={}
        identities={}
        cohort_identities=set()
        self._likelihood_factor_keys={}
        pids=[p['id'] for p in data['programs']]
        if not pids or len(set(pids))!=len(pids):
            raise ValueError('Need distinct program IDs')
        count_other_cases, count_other_groups = set(), set()
        if any(p.get('positive_repeat_count_observations') for p in data['programs']):
            # Count-only v1 forbids a second likelihood for the same episode.
            # Inspect all programs first, including later programs and grouped
            # evidence declarations. Aliases still require upstream review.
            def collect_factor_identities(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key == 'positive_repeat_count_observations':
                            continue
                        if key in ('case_id', 'evidence_group_id') and isinstance(item, str):
                            (count_other_cases if key == 'case_id' else count_other_groups).add(item)
                        elif key in ('case_ids', 'evidence_group_ids') and isinstance(item, list):
                            target = count_other_cases if key == 'case_ids' else count_other_groups
                            target.update(i for i in item if isinstance(i, str))
                        else:
                            collect_factor_identities(item)
                elif isinstance(value, list):
                    for item in value:
                        collect_factor_identities(item)
            collect_factor_identities(data['programs'])
        for raw in data['programs']:
            if raw.get('absent_event_censoring') or raw.get('joint_duration_reports'):
                # Frozen declarations cover path structure as well as reports.
                # Dataclass fields can contain caller-owned lists (markers,
                # blocks, scopes); copying only observations is insufficient.
                raw=deepcopy(raw)
            if raw.get('time_unit', cfg.elapsed_time_unit) != cfg.elapsed_time_unit:
                raise ValueError('Every program must share the declared elapsed time unit')
            granularity = raw.get('inventory_granularity', 'detailed_operations')
            if granularity not in ('detailed_operations', 'aggregate_phases'):
                raise ValueError('Unknown inventory granularity')
            if granularity == 'aggregate_phases' and not (
                    isinstance(raw.get('clock_estimand'), str) and raw['clock_estimand'].strip()):
                raise ValueError('Aggregate phases require an explicit clock estimand, not an implied whole process')
            validate_bound_observations(raw)
            p=dict(id=raw['id'],routes=[],observations=raw.get('observations',[]),
                   rates=raw.get('rate_observations',[]),cache={},
                   case_path_scope=raw.get('case_path_scope',{}), quantile_cohorts=[],
                   quantile_report_scales={},
                   histogram_cohorts=[], inventory_granularity=granularity,
                   clock_estimand=raw.get('clock_estimand'),
                   conditional_case_frame=self.conditional_case_frames.get(raw['id']))
            if raw.get('joint_duration_reports') or raw.get('absent_event_censoring'):
                # The new digest-bound contract freezes its entire observation
                # view; later caller edits must not change compiled case groups.
                p['observations']=deepcopy(p['observations'])
            p['repeat_keys']=sorted({b['repeat_key'] for r in raw['routes']
                for path in r.get('paths',[r]) for b in path['blocks'] if b.get('repeat_key')})
            if 'positive_repeat_count_observations' in raw:
                counts = validate_positive_repeat_counts(
                    raw['positive_repeat_count_observations'], p['repeat_keys'],
                    count_other_cases, count_other_groups)
                if counts['rows']:
                    p['positive_repeat_counts'] = counts['rows']
                    p['count_only_repeat_families'] = counts['families']
                    count_other_cases.update(row['case_id'] for row in counts['rows'])
                    count_other_groups.update(row['evidence_group_id'] for row in counts['rows'])
            route_ids=set()
            for r in raw['routes']:
                if r['id'] in route_ids or not math.isfinite(r['prior_weight']) or r['prior_weight']<=0:
                    raise ValueError('Routes need unique identities and positive explicit prior weights')
                route_ids.add(r['id'])
                ops=tuple(Operation(**o) for o in r['operations'])
                if not ops or len({op.id for op in ops}) != len(ops):
                    raise ValueError('An inventory requires distinct operation identities')
                gi=[]
                for op in ops:
                    key=(p['id'],op.id,op.actor_id,op.actor_role,op.task_type,op.payer_work,op.agency_work)
                    if key not in identities:
                        identities[key]=len(self.operations)
                        actor=(op.actor_id if op.actor_role=='agency' and op.actor_id else
                               f"{p['id']}:{op.id}:unknown" if op.actor_role=='unknown' or op.actor_id is None else
                               'role:'+op.actor_role)
                        if actor not in self.agencies:
                            self.agencies.append(actor)
                        if op.task_type not in self.tasks:
                            self.tasks.append(op.task_type)
                        self.operations.append(dict(program=p['id'],op=op,agency=self.agencies.index(actor),
                                                    task=self.tasks.index(op.task_type)))
                    gi.append(identities[key])
                route=dict(id=r['id'],operations=ops,indices=np.array(gi),prior_weight=r['prior_weight'])
                if 'paths' in r:
                    if 'blocks' in r or not r['paths']:
                        raise ValueError('Declare either one complete route or explicit case paths, not both')
                    paths=[]
                    path_ids=set()
                    covered=set()
                    for path in r['paths']:
                        weight=path['probability_weight']
                        if (not isinstance(path['id'],str) or not path['id'] or path['id'] in path_ids or isinstance(weight,bool)
                                or not math.isfinite(weight) or weight<=0):
                            raise ValueError('Case paths need distinct IDs and positive declared probability weights')
                        path_ids.add(path['id'])
                        blocks=tuple(Block(**b) for b in path['blocks'])
                        ids={aid for block in blocks for aid in block.operations}
                        if not ids <= {op.id for op in ops}:
                            raise ValueError('A case path references operations outside its inventory')
                        positions=[i for i,op in enumerate(ops) if op.id in ids]
                        path_ops=tuple(ops[i] for i in positions)
                        repeat={b.repeat_key:np.array([0]) for b in blocks if b.repeat_key is not None}
                        p.setdefault('dwell_ops',set()).update(self._declare_dwells(p['id'],blocks))
                        CompactTrace(path_ops,blocks,np.ones((1,len(path_ops))),repeat,
                                     dwells=unit_dwell_array(path_ops,blocks))
                        paths.append(dict(id=path['id'],operations=path_ops,blocks=blocks,
                            indices=np.array(gi)[positions],probability_weight=weight))
                        covered.update(ids)
                    if covered != {op.id for op in ops}:
                        raise ValueError('Every modeled inventory operation must occur on at least one declared path')
                    route['paths']=paths
                else:
                    blocks=tuple(Block(**b) for b in r['blocks'])
                    repeat={b.repeat_key:np.array([0]) for b in blocks if b.repeat_key is not None}
                    p.setdefault('dwell_ops',set()).update(self._declare_dwells(p['id'],blocks))
                    CompactTrace(ops,blocks,np.ones((1,len(ops))),repeat,
                                 dwells=unit_dwell_array(ops,blocks))
                    route['blocks']=blocks
                p['routes'].append(route)
            p['dwell_ops']=sorted(p.get('dwell_ops',()))
            p['dwell_local']={self.dwell_index[(p['id'],aid)]:j for j,aid in enumerate(p['dwell_ops'])}
            if not p['routes']:
                raise ValueError('A program needs at least one explicit route hypothesis')
            self._validate_observations(p)
            cohort_reports=[]
            for ci,cohort in enumerate(raw.get('quantile_cohorts',[])):
                if cohort.get('time_unit', cfg.elapsed_time_unit) != cfg.elapsed_time_unit:
                    raise ValueError('Quantile cohort and model elapsed time units must match')
                reports=cohort_report_observations(cohort)
                self._validate_source_precision(cohort,cohort['operators'],cohort_context=True)
                if (cohort['cohort_id'] in cohort_identities or
                        any(c['id']==cohort['id'] for c in p['quantile_cohorts'])):
                    raise ValueError('An overlapping cohort cannot be supplied as independent factors')
                if any(o.get('cohort_id')==cohort['cohort_id'] for pp in data['programs']
                       for o in pp.get('observations',[])+pp.get('rate_observations',[])):
                    raise ValueError('A quantile cohort overlaps explicitly linked individual/rate evidence')
                cohort_identities.add(cohort['cohort_id'])
                cohort_reports.extend(reports)
                grid=CohortQuantileGrid(cohort['sample_size'],[r['statistic'] for r in reports],
                    cohort['quantile_method'],cfg.cohort_quadrature_size,
                    cfg.cohort_seed+104729*len(self.programs)+1009*ci)
                p['quantile_report_scales'][cohort['id']]=elapsed_report_log_scale(
                    cohort,cfg.report_sd)
                p['quantile_cohorts'].append(dict(cohort,grid=grid))
            if cohort_reports:
                self._validate_observations(dict(p,observations=p['observations']+cohort_reports))
            for cohort in raw.get('histogram_cohorts',[]):
                if cfg.elapsed_time_unit != 'calendar_days':
                    raise ValueError('Exact histogram cohorts currently require a calendar_days model')
                cohort_histogram_observations(cohort)
                if (cohort['cohort_id'] in cohort_identities or any(
                        c['id']==cohort['id'] for c in p['histogram_cohorts']+p['quantile_cohorts'])
                        or any(o['id']==cohort['id'] for o in p['observations'])):
                    raise ValueError('An overlapping cohort cannot be supplied as independent factors')
                if any(o.get('cohort_id')==cohort['cohort_id'] for pp in data['programs']
                       for o in pp.get('observations',[])+pp.get('rate_observations',[])):
                    raise ValueError('A histogram cohort overlaps explicitly linked individual/rate evidence')
                for op in cohort['operators']:
                    validate_operator(op)
                    if op['basis'] in PHASE_BASES and not cfg.within_visit_phases:
                        raise ValueError('Waiting/service histograms require the explicit within_visit_phases model')
                cohort_identities.add(cohort['cohort_id'])
                # Exact administrative counts do not allocate narrative-source
                # offsets or individual-case coordinates. Their provenance stays
                # in the cohort contract, not the reporting-error hierarchy.
                p['histogram_cohorts'].append(dict(cohort))
            p['cases']=sorted({o['case_id'] for o in p['observations'] if o['case_id'] is not None})
            p['case_index']={c:i for i,c in enumerate(p['cases'])}
            if cfg.population_integration=='analytic_single_phase':
                validate_single_phase_program(p)
            path_ids={path['id'] for r in p['routes'] for path in r.get('paths',[])}
            if set(p['case_path_scope']) - set(p['cases']):
                raise ValueError('Case-path conditioning requires a known observed case')
            for scope in list(p['case_path_scope'].values()) + [o['population_path_scope']
                    for o in p['observations']+p['rates']+p['quantile_cohorts']+p['histogram_cohorts'] if 'population_path_scope' in o]:
                if (not isinstance(scope,list) or not scope or len(set(scope))!=len(scope)
                        or not set(scope)<=path_ids):
                    raise ValueError('A path scope requires distinct known case-path IDs')
            if path_ids and (p['case_path_scope'] or any('population_path_scope' in o
                    for o in p['observations']+p['rates']+p['quantile_cohorts']+p['histogram_cohorts'])) and any('paths' not in r for r in p['routes']):
                raise ValueError('Path-conditioned evidence requires explicit paths in every inventory hypothesis')
            fixed_priors=(validate_case_path_priors(raw['case_path_priors'],p,cfg)
                          if 'case_path_priors' in raw else {})
            if fixed_priors:
                p['case_path_priors']=fixed_priors
            absent_events=(validate_absent_event_censoring(raw['absent_event_censoring'],p)
                           if 'absent_event_censoring' in raw else {})
            if absent_events:
                p['absent_event_censoring']=absent_events
            joint_groups=(validate_joint_duration_reports(raw['joint_duration_reports'],p)
                          if 'joint_duration_reports' in raw else [])
            if joint_groups:
                p['joint_duration_reports']=joint_groups
            if cfg.population_integration=='collapsed_single_phase_quadrature':
                if p['cases']:
                    p['collapsed_observation_ids']=validate_collapsed_single_phase_program(p)
                else:
                    validate_single_phase_program(p)
            p['global_indices']=sorted({int(i) for r in p['routes'] for i in r['indices']})
            p['local_indices']={i:j for j,i in enumerate(p['global_indices'])}
            p['selected_cases']=set()
            for case in p['cases']:
                sampling={o['sampling'] for o in p['observations'] if o['case_id']==case}
                if len(sampling)!=1:
                    raise ValueError('Same-case claims must share one ascertainment mechanism')
                if 'delay_selected' in sampling:
                    p['selected_cases'].add(case)
            if p['selected_cases'] and cfg.selection_sd:
                for route in p['routes']:
                    for path in route.get('paths',[]):
                        if not any('decision' in op.markers for op in path['operations']):
                            raise ValueError('Delay selection currently requires a decision clock on every case path')
            self._validate_likelihood_factor_keys(p)
            self.programs.append(p)
        if cfg.population_integration=='collapsed_single_phase_quadrature':
            counts={}
            for p in self.programs:
                for o in p['observations']:
                    if o['case_id'] is not None:
                        counts[o['case_id']]=counts.get(o['case_id'],0)+1
            repeated=sorted(case for case,count in counts.items() if count != 1)
            if repeated:
                raise ValueError('Collapsed cases require exactly one informative observation globally: '
                                 + ', '.join(repeated))
            self.collapsed_case_nodes,self.collapsed_case_weights=roots_hermitenorm(
                cfg.collapsed_case_quadrature_size)
            with np.errstate(divide='ignore'):
                self.collapsed_case_log_weights=np.where(self.collapsed_case_weights>0,
                    np.log(self.collapsed_case_weights)-.5*math.log(2*math.pi),-math.inf)
        declaration = data.get('joint_inventory_prior')
        self.joint_inventory_prior = (None if declaration is None else
                                      JointInventoryPrior(declaration, self.programs))
        L=self.layout
        def channel_coordinates(name, width):
            # -1 is an absent coordinate, NEVER a parameter to read from z.
            # Public channel axes remain stable; only active rows are sampled.
            result = np.full((len(CHANNELS), width), -1, dtype=int)
            result[list(self.active_channels)] = L.add(
                name, len(self.active_channels)*width).reshape(len(self.active_channels), width)
            return result
        self.location=channel_coordinates('location',1)[:,0]
        self.agency=channel_coordinates('agency',len(self.agencies))
        self.task=channel_coordinates('task',len(self.tasks))
        self.operation=channel_coordinates('operation',len(self.operations))
        design_declaration = data.get('operation_location_design')
        self.operation_location_design = None
        self.operation_location_design_coordinates = np.array([], dtype=int)
        if design_declaration is not None:
            if cfg.modeled_channels != ('elapsed',):
                raise ValueError('Operation location design v1 is bounded to elapsed-only models')
            self.operation_location_design = compile_operation_location_design(
                design_declaration, self.operations)
            self.operation_location_design_coordinates = L.add(
                'operation_location_design', len(self.operation_location_design['terms']))
        self.sigma=channel_coordinates('case_sigma',1)[:,0]
        hierarchy_declaration = data.get('source_offset_hierarchy')
        if hierarchy_declaration is None:
            self.source=channel_coordinates('source',len(self.sources))
        else:
            if cfg.modeled_channels != ('elapsed',):
                raise ValueError('Source offset hierarchy v1 is bounded to elapsed-only models')
            duration_sources=[]
            for p in self.programs:
                for o in p['observations'] + p['quantile_cohorts']:
                    if any(weight > 0 and operator['basis'] not in
                           COUNT_BASES | set(MONEY_BASES) | {'unmodeled_duration'}
                           for operator,weight in zip(o['operators'],o['operator_weights'])):
                        if o['source_family'] not in duration_sources:
                            duration_sources.append(o['source_family'])
            self.source=np.full((len(CHANNELS),len(self.sources)),-1,dtype=int)
            self.source_offset_hierarchy=SourceOffsetHierarchy(
                hierarchy_declaration,duration_sources,cfg.elapsed_time_unit,L,
                data.get('source_comparisons'), programs=data['programs'])
        self.blocks=[np.array([self.location[ch]]) for ch in self.active_channels]
        source_arrays=() if self.source_offset_hierarchy is not None else (self.source,)
        for array in (self.agency,self.task,self.operation)+source_arrays:
            self.blocks.extend(array[ch] for ch in self.active_channels if len(array[ch]))
        if len(self.operation_location_design_coordinates):
            self.blocks.append(self.operation_location_design_coordinates)
        if self.source_offset_hierarchy is not None:
            self.blocks.extend(self.source_offset_hierarchy.sampler_blocks(
                split=(cfg.source_hierarchy_sampler == 'interwoven')))
        self.blocks.extend(np.array([self.sigma[ch]]) for ch in self.active_channels)
        self.phase_coordinates = None
        if cfg.within_visit_phases:
            groups = [L.add('phase_location',1), L.add('phase_agency',len(self.agencies)),
                      L.add('phase_task',len(self.tasks)), L.add('phase_operation',len(self.operations))]
            self.phase_coordinates = np.concatenate(groups)
            self.blocks.extend(group for group in groups if len(group))
            self.phase_nodes, self.phase_weights = roots_hermitenorm(32)
            self.phase_weights /= math.sqrt(2*math.pi)
        # Two levels only, allocated solely for gaps some route actually declares:
        # a population waiting level and one effect per gap. There is no agency or
        # task level because a dwell is nobody working, so attributing it to an
        # actor would be a category error and would also make waiting compete with
        # the operation hierarchy for the same contrasts.
        self.dwell_coordinates = None
        if cfg.inter_operation_dwell and self.dwell_sites:
            groups = [L.add('dwell_location',1), L.add('dwell_site',len(self.dwell_sites))]
            self.dwell_coordinates = np.concatenate(groups)
            self.blocks.extend(groups)
        for pi,p in enumerate(self.programs):
            n=len(p['global_indices'])
            p['repeat']=L.add(p['id']+':repeat',2*len(p['repeat_keys'])).reshape(2,-1)
            p['selection']=L.add(p['id']+':selection',int(cfg.selection_sd>0))
            for ri,route in enumerate(p['routes']):
                if 'paths' in route:
                    size=len(route['paths'])
                    route['path_coordinates']=L.add(p['id']+':path_logits:'+route['id'],
                        size-1 if cfg.case_path_logit_sd else 0)
                    route['path_basis']=helmert(size).T/math.sqrt(2.) if size>1 else np.zeros((1,0))
                    if len(route['path_coordinates']):
                        self.blocks.append(route['path_coordinates'])
            p['noise_dimension']=len(self.active_channels)*(n+1)
            p['phase_offset']=p['noise_dimension']+len(p['repeat_keys'])
            p['dwell_offset']=p['phase_offset']+(n if cfg.within_visit_phases else 0)
            # A zero case spread allocates no per-case waiting latent, exactly as a
            # zero selection or path-logit scale allocates none: the gap then has
            # one population wait rather than an unidentified coordinate per case.
            p['case_dimension']=p['dwell_offset']+(len(p['dwell_ops'])
                if cfg.inter_operation_dwell and cfg.dwell_case_sd else 0)
            p['population_dimension']=p['case_dimension']
            if cfg.population_integration=='collapsed_single_phase_quadrature':
                p['uncollapsed_case_dimension']=p['case_dimension']
                p['case_dimension']=0
            p['case_coordinates']=L.add(p['id']+':cases',len(p['cases'])*p['case_dimension']).reshape(len(p['cases']),p['case_dimension'])
            self.blocks.extend(row for row in p['repeat'] if len(row))
            if len(p['selection']):
                self.blocks.append(p['selection'])
            for row in p['case_coordinates']:
                size = cfg.case_update_block_size
                if size:
                    self.blocks.extend(row[start:start+size] for start in range(0, len(row), size))
                else:
                    self.blocks.append(row)
            power=int(math.ceil(math.log2(cfg.population_size)))
            uniforms=qmc.Sobol(p['population_dimension'],scramble=True,seed=cfg.population_seed+104729*pi).random_base2(power)
            p['population_normals']=ndtri(np.clip(uniforms,np.nextafter(0.,1.),np.nextafter(1.,0.)))
        # Append optional count-only coordinates AFTER every historical program
        # coordinate. No hurdle, case, source-offset or duration parameter is
        # allocated for these ascertainment-conditioned count reports.
        for p in self.programs:
            for family in p.get('count_only_repeat_families', []):
                coordinate = L.add(p['id']+':positive_repeat:'+family['id'], 1)
                family['coordinate'] = int(coordinate[0])
                self.blocks.append(coordinate)
        self.agency_indices=np.array([o['agency'] for o in self.operations])
        self.task_indices=np.array([o['task'] for o in self.operations])
        task_priors = dict(cfg.elapsed_task_prior_medians)
        if set(task_priors) - set(self.tasks):
            raise ValueError('Elapsed task priors name tasks absent from this model: '
                             + ', '.join(sorted(set(task_priors) - set(self.tasks))))
        self.elapsed_task_prior_offsets = np.array([
            math.log(task_priors.get(o['op'].task_type, cfg.elapsed_prior_median))
            - math.log(cfg.elapsed_prior_median) for o in self.operations])
        self.hierarchy_coordinates=[np.r_[self.location[ch],self.agency[ch],self.task[ch],self.operation[ch]]
                                    if ch in self.active_channels else np.array([],dtype=int)
                                    for ch in range(3)]
        self.design=np.column_stack((np.full(len(self.operations),cfg.location_sd),
            cfg.agency_sd*np.eye(len(self.agencies))[self.agency_indices],
            cfg.task_sd*np.eye(len(self.tasks))[self.task_indices],
            cfg.operation_sd*np.eye(len(self.operations))))
        if self.operation_location_design is not None:
            self.hierarchy_coordinates[0] = np.r_[self.hierarchy_coordinates[0],
                                                  self.operation_location_design_coordinates]
            self.design = np.column_stack((self.design,
                                            self.operation_location_design['matrix']))
        self.duration_conditionals = None
        if cfg.hierarchy_sampler == 'operation_centered':
            # h ~ N(0,I), m=A h. Integrate the Gaussian hierarchy only for
            # proposing m, then retain/sample h|m exactly. No parameter is fixed
            # or deleted and all original case/population likelihoods are used.
            covariance=self.design@self.design.T
            if np.linalg.matrix_rank(covariance,hermitian=True) != len(covariance):
                raise ValueError('Operation-centered sampling requires a positive-definite '
                    'actual operation-mean covariance under configured hierarchy scales')
            try:
                factor=np.linalg.cholesky(covariance)
            except np.linalg.LinAlgError as error:
                raise ValueError('Operation-centered sampling requires a positive-definite '
                    'actual operation-mean covariance under configured hierarchy scales') from error
            precision=cho_solve((factor,True),np.eye(len(covariance)))
            regression=self.design.T@precision
            basis,_=np.linalg.qr(self.design.T,mode='complete')
            self.duration_null_basis=basis[:,len(self.operations):]
            self.duration_conditionals=[]
            for pi,p in enumerate(self.programs):
                indices=p['global_indices']
                conditional_factor=np.linalg.cholesky(precision[np.ix_(indices,indices)])
                conditional_scale=solve_triangular(conditional_factor.T,np.eye(len(indices)),lower=False)
                self.duration_conditionals.append((pi,indices,precision[indices],
                    conditional_factor,conditional_scale,regression[:,indices]))
            hierarchy=set(np.concatenate(self.hierarchy_coordinates))
            self.blocks=[block for block in self.blocks if not any(int(i) in hierarchy for i in block)]
        joint_block_declaration=data.get('sampler_joint_blocks')
        self.sampler_joint_blocks=(() if joint_block_declaration is None else
            compile_sampler_joint_blocks(joint_block_declaration,self))
        self.blocks.extend(block['coordinates'] for block in self.sampler_joint_blocks)
        if cfg.within_visit_phases:
            self.phase_design=np.column_stack((np.full(len(self.operations),cfg.phase_location_sd),
                cfg.phase_agency_sd*np.eye(len(self.agencies))[self.agency_indices],
                cfg.phase_task_sd*np.eye(len(self.tasks))[self.task_indices],
                cfg.phase_operation_sd*np.eye(len(self.operations))))
        for p in self.programs:
            entries,groups=[],[]
            p['report_scales']={}
            for o in p['observations']:
                start=len(entries)
                for operator,weight in zip(o['operators'],o['operator_weights']):
                    channel=operator['basis'] if operator['basis'] in CHANNELS else 'elapsed'
                    report_scale=self._report_scale_for_operator(o,operator)
                    entries.append(dict(observation=o,operator=operator,
                        signature=json.dumps(operator,sort_keys=True),weight=weight,
                        source=self.sources.index(o['source_family']),channel=CHANNELS.index(channel),
                        report_scale=report_scale))
                    if operator['basis']!='unmodeled_duration':
                        p['report_scales'][o['id']]=report_scale
                groups.append((o['id'],start,len(entries)))
            p['compiled']=dict(entries=entries,groups=groups,
                lower=np.array([x['observation']['lower'] for x in entries]),
                upper=np.array([math.inf if x['observation']['upper'] is None else x['observation']['upper'] for x in entries]),
                counts=np.array([x['operator']['basis'] in COUNT_BASES for x in entries],dtype=bool),
                money=np.array([x['operator']['basis'] in MONEY_BASES for x in entries],dtype=bool),
                residuals=np.array([x['operator']['basis']=='unmodeled_duration' for x in entries],dtype=bool),
                residual_ll=np.array([float(unmodeled_duration_log_probability(
                    x['observation']['lower'],x['observation']['upper'],x['operator'],
                    x['observation'].get('report_intervals')))
                    if x['operator']['basis']=='unmodeled_duration' else 0. for x in entries]),
                channels=np.array([x['channel'] for x in entries],dtype=int),
                sources=np.array([x['source'] for x in entries],dtype=int),
                report_scales=np.array([x['report_scale'] for x in entries]),
                logweights=np.log([x['weight'] for x in entries]))

    def _declare_dwells(self,program_id,blocks):
        """Register each declared gap as its own hierarchy site.

        Declaring a dwell without the flag is refused rather than ignored: a
        silently dropped declaration would model the route as gapless and report
        the waiting inside the step it precedes, which is the defect this exists
        to remove. Shape validation of the declaration itself stays in
        `CompactTrace`, which owns the block/operation contract.
        """
        names=[aid for block in blocks for aid in (block.dwells or ())]
        if names and not self.cfg.inter_operation_dwell:
            raise ValueError('Declared inter-operation dwells require the explicit inter_operation_dwell model')
        for aid in names:
            key=(program_id,aid)
            if key not in self.dwell_index:
                self.dwell_index[key]=len(self.dwell_sites)
                self.dwell_sites.append(key)
        return names

    def _validate_observations(self,p):
        seen=set()
        for o in p['observations']:
            elapsed = any(op['basis'] not in COUNT_BASES | set(MONEY_BASES) | set(CHANNELS[1:])
                          for op in o['operators'])
            if elapsed and o.get('time_unit', self.cfg.elapsed_time_unit) != self.cfg.elapsed_time_unit:
                raise ValueError('Observation and model elapsed time units must match')
            if p['inventory_granularity'] == 'aggregate_phases' and any(
                    op['basis'] in COUNT_BASES | set(MONEY_BASES) for op in o['operators']):
                raise ValueError('Aggregate phases do not establish operation counts, agency counts or fee inventories')
            if not o['id'] or o['id'] in seen or not o['source_family']:
                raise ValueError('Observations need distinct IDs and a source family')
            seen.add(o['id'])
            if o['source_family'] not in self.sources:
                self.sources.append(o['source_family'])
            allowed_sampling={'unselected','delay_selected'}
            if p.get('conditional_case_frame') is not None:
                allowed_sampling.add(CONDITIONAL_FRAME_SAMPLING)
            if o['sampling'] not in allowed_sampling:
                raise ValueError('Ascertainment must be explicit')
            report_only=o['statistic']=='report_only'
            if report_only and (o['case_id'] is not None or
                    any(op['basis']!='unmodeled_duration' for op in o['operators'])):
                raise ValueError('A report-only likelihood must be independent of every case and process operator')
            if (o['case_id'] is None and o['statistic'] not in {'median','mean','p90','typical_range','report_only'}) or (
                    o['case_id'] is not None and o['statistic']!='individual'):
                raise ValueError('Individual and population statistics must not be interchanged')
            validate_typical_range_observation(o)
            self._validate_source_precision(o,o['operators'],
                typical=(o['statistic']=='typical_range'))
            if o['case_id'] is None and o['sampling']!='unselected':
                raise ValueError('Selected population summaries require a separate sampling contract')
            if 'population_path_scope' in o and (o['case_id'] is not None or report_only):
                raise ValueError('Only informative population summaries may carry a population path scope')
            if 'population_condition' in o:
                if (o['case_id'] is not None or report_only or o['population_condition'] != 'first_visit'
                        or any(op['basis'] != 'unmodeled_duration' and
                               (op['basis'] != 'single_visit_cycle' or op.get('visits') != 'first')
                               for op in o['operators'])):
                    raise ValueError('First-visit population conditioning requires first-cycle population operators')
            if o['case_id'] is None and o.get('sample_size') is not None:
                raise ValueError('Finite-cohort summaries require the explicit joint quantile_cohorts contract')
            if not math.isfinite(o['lower']) or o['lower']<0 or (
                    o['upper'] is not None and (not math.isfinite(o['upper']) or o['upper']<o['lower'])):
                raise ValueError('Invalid nonnegative observation interval')
            operators=o['operators']
            if any(op['basis'] in PHASE_BASES for op in operators) and not self.cfg.within_visit_phases:
                raise ValueError('Waiting/service observations require the explicit within_visit_phases model')
            weights=np.asarray(o['operator_weights'],dtype=float)
            if not operators or len(weights)!=len(operators) or not np.isfinite(weights).all() or np.any(weights<=0):
                raise ValueError('Specify positive interpretation priors explicitly, not LLM confidence')
            if not np.isclose(weights.sum(),1.,atol=1e-12,rtol=0.):
                raise ValueError('Interpretation weights must sum to one')
            for op in operators:
                validate_operator(op)
                if op['basis']=='unmodeled_duration':
                    if set(op)!={'basis','median_days','log_scale'} or any(
                            isinstance(op[k],bool) or not isinstance(op[k],(int,float))
                            or not math.isfinite(op[k]) or op[k]<=0 for k in ('median_days','log_scale')):
                        raise ValueError('Unmodeled duration requires an explicit finite positive reference distribution')
            counts=[op['basis'] in COUNT_BASES for op in operators]
            money=[op['basis'] in MONEY_BASES for op in operators]
            # Checked before the count rule so a money/count mixture reports the
            # money contract rather than the count one. A fee total is a dollar
            # amount: no interpretation of one phrase can trade it against a
            # duration density, a count probability or an unmodeled-duration
            # residual, all of which are in other units.
            if any(money) and not all(money):
                raise ValueError('Cannot mix money amounts with durations or counts')
            if all(money) and o['case_id'] is None:
                # A published schedule is an input to the trace, not an
                # observation of it; only an applicant's reported total is.
                raise ValueError('Population money summaries are not individual fee-total reports')
            if any(counts) and not all(counts):
                raise ValueError('Cannot mix count probabilities and duration densities')
            if all(counts) and o['case_id'] is None:
                raise ValueError('Population count summaries are not individual count reports')
            if 'report_intervals' in o:
                intervals=o['report_intervals']
                if not isinstance(intervals,list) or not intervals or any(counts):
                    raise ValueError('Report interval unions require nonempty duration intervals')
                previous=-math.inf
                for bounds in intervals:
                    if not isinstance(bounds,list) or len(bounds)!=2:
                        raise ValueError('Each report interval requires two bounds')
                    lo,hi=bounds
                    if (isinstance(lo,bool) or not isinstance(lo,(int,float)) or not math.isfinite(lo)
                            or lo<0 or lo<=previous or (hi is not None and (isinstance(hi,bool)
                            or not isinstance(hi,(int,float)) or not math.isfinite(hi) or hi<=lo))):
                        raise ValueError('Report intervals must be sorted, disjoint and nonempty')
                    previous=math.inf if hi is None else hi
                if o['lower']!=intervals[0][0] or o['upper']!=intervals[-1][1]:
                    raise ValueError('Reported bounds must equal the interval-union envelope')
            # Counts and money carry no resource channel of their own and so pass
            # this check as 'elapsed' does: neither one can make an omitted
            # payer/agency-hours channel a modelling error.
            channels={op['basis'] if op['basis'] in CHANNELS[1:] else 'elapsed' for op in operators}
            if len(channels)!=1:
                raise ValueError('Alternative interpretations cannot change measurement units')
            if not channels <= set(self.cfg.modeled_channels):
                raise ValueError('Cannot omit a resource channel with supplied observations')
            # A fee total is continuous like a duration, so a point report ("$190")
            # must arrive as its rounding interval; only counts are discrete.
            if not any(counts) and o['upper']==o['lower']:
                raise ValueError('A rounded continuous report needs a nonzero observation interval')
        for r in p['rates']:
            if r['repeat_key'] not in p['repeat_keys'] or r['event']!='any_correction_per_case':
                raise ValueError('Only an explicitly linked any-correction cohort is currently supported')
            if r.get('cohort_scope')!='completed_cases_for_repeat_block':
                raise ValueError('An observed-by-date cohort is not an eventual complete-case correction risk')
            if (r.get('independent_cohort') is not True or not isinstance(r['successes'],int)
                    or not isinstance(r['trials'],int) or not 0<=r['successes']<=r['trials'] or r['trials']<1):
                raise ValueError('A real counted independent cohort is required; informal frequencies have no n')

    def _validate_likelihood_factor_keys(self,p):
        """Reserve every exact dict key before likelihood factors can overwrite.

        Factor IDs are an internal namespace, not merely display labels.  A
        collision used to let ``dict.update`` silently drop one likelihood term.
        Path and plain-route alternatives emit different key sets, so validate
        each mutually exclusive mode separately before reserving their union
        against every other program.
        """
        always=[]
        always.extend((p['id']+':positive_repeat_count:'+row['id'], 'positive_repeat_count')
                      for row in p.get('positive_repeat_counts', []))
        always.extend((p['id']+':quantile_cohort:'+c['id'],'quantile_cohort')
                      for c in p['quantile_cohorts'])
        always.extend((p['id']+':histogram_cohort:'+c['id'],'histogram_cohort')
                      for c in p['histogram_cohorts'])
        always.extend((p['id']+':cohort:'+str(i),'rate_cohort')
                      for i,_ in enumerate(p['rates']))
        modes=[]
        if any('paths' in route for route in p['routes']):
            path=[]
            path.extend((p['id']+':case:'+case,'path_case') for case in p['cases'])
            path.extend((p['id']+':'+o['id'],'path_population_observation')
                        for o in p['observations'] if o['case_id'] is None)
            modes.append(('path_route',path+always))
        if any('paths' not in route for route in p['routes']):
            grouped={o['id'] for g in p.get('joint_duration_reports',[]) for o in g['members']}
            plain=[(p['id']+':'+o['id'],'ordinary_observation') for o in p['observations']
                   if o['id'] not in grouped]
            plain.extend((p['id']+':report_group:'+g['declaration']['id'],'joint_duration_report')
                         for g in p.get('joint_duration_reports',[]))
            if p['selected_cases'] and self.cfg.selection_sd:
                plain.extend((p['id']+':selection:'+case,'selection_adjustment')
                             for case in p['selected_cases'])
            modes.append(('plain_route',plain+always))
        possible={}
        for mode,generated in modes:
            seen={}
            for key,kind in generated:
                if key in seen:
                    raise ValueError('Likelihood factor key collision in '
                        f"program {p['id']!r} {mode}: {key!r} is generated by "
                        f"{seen[key]} and {kind}")
                seen[key]=kind
                possible.setdefault(key,set()).add(mode+':'+kind)
        for key,kinds in possible.items():
            origin=f"program {p['id']!r} " + '/'.join(sorted(kinds))
            if key in self._likelihood_factor_keys:
                raise ValueError('Likelihood factor key collision: '
                    f"{key!r} is generated by {self._likelihood_factor_keys[key]} and {origin}")
            self._likelihood_factor_keys[key]=origin

    @staticmethod
    def _supports_source_precision(operators,*,typical=False):
        """Whether these operators use the ordinary elapsed report-error kernel."""
        bases={op['basis'] for op in operators if op['basis']!='unmodeled_duration'}
        excluded=COUNT_BASES | set(MONEY_BASES) | set(CHANNELS[1:])
        return bool(bases) and not typical and not bool(bases & excluded)

    def _validate_source_precision(self,record,operators,*,typical=False,cohort_context=False):
        """Allow fixed/fallback annotations only on ordinary elapsed report kernels."""
        annotation=precision_annotation(record)
        if annotation is None:
            return None
        if not self._supports_source_precision(operators,typical=typical):
            kind='finite cohort' if cohort_context else 'observation'
            raise ValueError('Source precision can annotate only an elapsed report kernel: '+kind)
        self.source_precision_active=True
        return annotation

    def _source_precision_diagnostic(self,record,*,unknown_n=False):
        """Describe a fixed/fallback elapsed scale without implying calibration review."""
        annotation=precision_annotation(record)
        base=(self.cfg.report_sd if annotation is None or
              annotation['report_log_scale'] is None else annotation['report_log_scale'])
        effective=elapsed_report_log_scale(record,self.cfg.report_sd,
            self.cfg.unknown_n_report_sd_floor if unknown_n else None)
        return dict(
            basis=('implicit_config_report_sd_fallback' if annotation is None else annotation['kind']),
            source_type=None if annotation is None else annotation['source_type'],
            declared_report_log_scale=(None if annotation is None else annotation['report_log_scale']),
            effective_report_log_scale=effective,
            config_report_sd=self.cfg.report_sd,
            unknown_n_floor_applied=bool(unknown_n and effective>base),
            fallback_reason=(None if annotation is None else annotation.get('reason')),
            calibration_id=(None if annotation is None else annotation.get('calibration_id')),
            calibration_provenance=(None if annotation is None else
                annotation['calibration_provenance']),
            learned=False)

    def _report_scale_for_operator(self,observation,operator):
        """Resolve once at construction; special and nonelapsed kernels stay legacy."""
        population=observation['case_id'] is None
        elapsed=(operator['basis'] not in
            COUNT_BASES | set(MONEY_BASES) | set(CHANNELS[1:]) | {'unmodeled_duration'})
        if elapsed and observation['statistic']!='typical_range':
            return elapsed_report_log_scale(observation,self.cfg.report_sd,
                self.cfg.unknown_n_report_sd_floor if population else None)
        return (max(self.cfg.report_sd,self.cfg.unknown_n_report_sd_floor)
                if population else self.cfg.report_sd)

    def parameters(self,z):
        c=self.cfg
        prior=np.log([c.elapsed_prior_median,c.work_prior_median,c.work_prior_median])
        active=list(self.active_channels)
        location=np.full(3,np.nan)
        agency=np.full(self.agency.shape,np.nan)
        task=np.full(self.task.shape,np.nan)
        mu=np.full((3,len(self.operations)),np.nan)
        sigma=np.full(3,np.nan)
        source=np.full(self.source.shape,np.nan)
        location[active]=prior[active]+c.location_sd*z[self.location[active]]
        agency[active]=c.agency_sd*z[self.agency[active]]
        task[active]=c.task_sd*z[self.task[active]]
        mu[active]=(location[active,None]+agency[active][:,self.agency_indices]
                    +task[active][:,self.task_indices]+c.operation_sd*z[self.operation[active]])
        if self.operation_location_design is not None:
            mu[0] += (self.operation_location_design['matrix'] @
                      z[self.operation_location_design_coordinates])
        if c.elapsed_task_prior_medians:
            mu[0] += self.elapsed_task_prior_offsets
        sigma[active]=np.exp(math.log(c.case_log_sd_median)+c.case_log_sd_prior*z[self.sigma[active]])
        if self.source_offset_hierarchy is None:
            source[active]=c.source_sd*z[self.source[active]]
        else:
            source[0]=self.source_offset_hierarchy.offsets_for_sources(z,self.sources)
        result=dict(mu=mu,sigma=sigma,location=location,agency=agency,task=task,
                    source=source)
        if c.within_visit_phases:
            result['phase_logit']=self.phase_design@z[self.phase_coordinates]
        if self.dwell_coordinates is not None:
            # Log-days of waiting per gap. Separate median and separate scales:
            # waiting is not distributed like work, so it borrows nothing from
            # `mu`, `sigma` or the operation design.
            result['dwell_log']=(math.log(c.dwell_prior_median)
                +c.dwell_location_sd*z[self.dwell_coordinates[0]]
                +c.dwell_site_sd*z[self.dwell_coordinates[1:]])
        return result

    def repeat_parameters(self,p,z):
        u=np.clip(ndtr(z[p['repeat']]),np.nextafter(0.,1.),np.nextafter(1.,0.))
        return u[0],betaincinv(2.,3.,u[1])

    def path_probabilities(self,route,z):
        """Population frequencies, not posterior probabilities of inventory truth."""
        logits=np.log([path['probability_weight'] for path in route['paths']])
        if len(route['path_coordinates']):
            logits=logits+self.cfg.case_path_logit_sd*(route['path_basis']@z[route['path_coordinates']])
        probabilities=np.exp(logits-logsumexp(logits))
        if not np.isfinite(probabilities).all() or np.any(probabilities<=0):
            raise FloatingPointError('Numerically extreme case-path probability proposal')
        return probabilities

    def case_path_prior_report(self):
        """Declared case sensitivities, explicitly separate from population rates."""
        result={}
        for p in self.programs:
            if not p.get('case_path_priors'):
                continue
            routes={r['id']:r for r in p['routes']}
            result[p['id']]={}
            for case,priors in p['case_path_priors'].items():
                result[p['id']][case]={}
                for route_id,entry in priors.items():
                    declaration=entry['declaration']
                    result[p['id']][case][route_id]=dict(
                        declaration=deepcopy(declaration),
                        normalized_prior_weights={path['id']:float(weight) for path,weight
                            in zip(routes[route_id]['paths'],np.exp(entry['log_prior']))},
                        learned_prior_coordinates=0,calibration_verified=False,
                        qualification=('Fixed declared sensitivity, applied once to this case and inventory. '
                            'Not learned population prevalence, calibrated LLM confidence or source certification. '
                            'Actor interpretation is conditional on the supplied equivalent-phase mapping; '
                            'unknown is a residual category, not a verified shared department. '
                            'Counterfactual case-duration noises remain latent; per-draw path weights may vary '
                            'even when actor effects are zero. Only their posterior marginal has attribution meaning.'))
        return result

    def trace(self,p,z,parameters,route_index,population=False,*,path_index=None,include_phases=True):
        route=p['routes'][route_index]
        if 'paths' in route:
            if path_index is None:
                if not population:
                    raise ValueError('Individual case paths must be marginalized jointly, not selected program-wide')
                return PopulationTraceMixture(
                    [self.trace(p,z,parameters,route_index,True,path_index=j,include_phases=include_phases)
                     for j in range(len(route['paths']))],
                    self.path_probabilities(route,z),[path['id'] for path in route['paths']])
            route=route['paths'][path_index]
        elif path_index is not None:
            raise ValueError('A legacy single route has no case-path index')
        indices=route['indices']
        local=[p['local_indices'][int(i)] for i in indices]
        n=len(p['global_indices'])
        normals=p['population_normals'] if population else z[p['case_coordinates']]
        q,r=self.repeat_parameters(p,z)
        key=(route_index,parameters['mu'][:,indices].tobytes(),parameters['sigma'].tobytes(),
             q.tobytes(),r.tobytes(),normals.tobytes() if not population else None)
        if self.cfg.within_visit_phases and include_phases:
            key+=(parameters['phase_logit'][indices].tobytes(),)
        if self.dwell_coordinates is not None:
            key+=(parameters['dwell_log'].tobytes(),)
        cache_slot=population if path_index is None else (population,route_index,path_index)
        if not include_phases:
            # Clock-only populations cannot answer a phase query; keep their
            # cache distinct from complete traces used by reports/phase factors.
            cache_slot=('without_phases',cache_slot)
        cached=p['cache'].get(cache_slot)
        if cached is not None and cached[0]==key:
            return cached[1]
        active=list(self.active_channels)
        noise=normals[:,:p['noise_dimension']].reshape(len(normals),len(active),n+1)
        logvalues=(parameters['mu'][active][:,indices][None,:,:]+parameters['sigma'][active][None,:,None]*noise[:,:,:n][:,:,local]
                   +self.cfg.common_case_sd*noise[:,:,n,None])
        if not np.isfinite(logvalues).all() or np.any(np.abs(logvalues)>650):
            raise FloatingPointError('Numerically extreme duration proposal')
        values=np.full((len(normals),3,len(indices)),np.nan)
        values[:,active,:]=np.exp(logvalues)
        resources={}
        for ch,field in ((1,'payer_work'),(2,'agency_work')):
            amounts=values[:,ch,:].copy()
            for j,op in enumerate(route['operations']):
                applicable=getattr(op,field)
                if ch in self.active_channels and applicable is not True:
                    amounts[:,j]=0. if applicable is False else np.nan
            resources[CHANNELS[ch]]=amounts
        uniforms=np.minimum(ndtr(normals[:,p['noise_dimension']:p['phase_offset']]),np.nextafter(1.,0.))
        repeat={}
        for b in route['blocks']:
            if b.repeat_key is not None:
                j=p['repeat_keys'].index(b.repeat_key)
                repeat[b.repeat_key]=repeat_quantiles(uniforms[:,j],q[j],r[j])
        fractions=None
        if self.cfg.within_visit_phases and include_phases:
            logits=(parameters['phase_logit'][indices][None,:]
                    +self.cfg.phase_case_sd*normals[:,p['phase_offset']:p['dwell_offset']][:,local])
            fractions=expit(logits)
        dwells=None
        declared={aid for b in route['blocks'] for aid in (b.dwells or ())}
        if declared:
            # NaN everywhere the route declares no gap, so `CompactTrace` refuses a
            # dwell it was never given rather than reading an accidental zero.
            dwells=np.full((len(normals),len(indices)),math.nan)
            for j,op in enumerate(route['operations']):
                if op.id not in declared:
                    continue
                site=self.dwell_index[(p['id'],op.id)]
                logwait=np.full(len(normals),parameters['dwell_log'][site])
                if self.cfg.dwell_case_sd:
                    logwait=logwait+self.cfg.dwell_case_sd*normals[:,p['dwell_offset']+p['dwell_local'][site]]
                if not np.isfinite(logwait).all() or np.any(np.abs(logwait)>650):
                    raise FloatingPointError('Numerically extreme inter-operation dwell proposal')
                dwells[:,j]=np.exp(logwait)
        result=CompactTrace(route['operations'],route['blocks'],values[:,0,:],repeat,resources,
                            service_fractions=fractions,dwells=dwells)
        if population and self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature'):
            result.analytic_elapsed_log_parameters=(float(parameters['mu'][0,indices[0]]),
                math.hypot(float(parameters['sigma'][0]),self.cfg.common_case_sd))
        p['cache'][cache_slot]=(key,result)
        return result

    def _likelihood_population(self,p,z,par,route_index):
        """Do not rebuild total clocks for a change that only reallocates phases.

        Full population phase arrays are still required whenever any population
        report or finite cohort can observe one. Case phase reports use their
        separate complete individual traces. This does not omit any coordinate
        or change the population grid, clock, selection model, or likelihood.
        """
        phases=any(op['basis'] in PHASE_BASES
            for o in p['observations'] if o['case_id'] is None for op in o['operators'])
        phases=phases or any(op['basis'] in PHASE_BASES
            for c in p['quantile_cohorts']+p['histogram_cohorts'] for op in c['operators'])
        return self.trace(p,z,par,route_index,True,include_phases=phases)

    def _selection_population_summary(self,p,population,strength,route_index):
        """Cache deterministic selection integrals, never a parameter-dependent likelihood.

        Compact traces are immutable after construction. Strong object references
        identify their full clock state (not reusable Python object IDs), while
        path probabilities and selection strength have their own cache keys.
        Each route retains only its latest population and normalizer pair.
        """
        mixture=isinstance(population,PopulationTraceMixture)
        traces=population.traces if mixture else (population,)
        weights=population.probabilities.tobytes() if mixture else None
        key=(traces,weights)
        cache=p.setdefault('selection_population_cache',{})
        entry=cache.get(route_index)
        if entry is None or entry['key']!=key:
            clocks=tuple(t.event('initial_decision') for t in traces)
            combined=np.concatenate(clocks) if mixture else clocks[0]
            threshold=(population_quantile(population,np.log(combined),.75) if mixture
                       else float(np.quantile(np.log(combined),.75)))
            entry=dict(key=key,clocks=clocks,threshold=threshold,strength=None)
            cache[route_index]=entry
        if entry['strength']!=strength:
            def logweight(values):
                h=expit((np.log(values)-entry['threshold'])/self.cfg.selection_width)
                return np.logaddexp(np.log1p(-h),strength+np.log(h))
            entry['normalizers']=np.array([logsumexp(logweight(values))-math.log(len(values))
                                            for values in entry['clocks']])
            entry['strength']=strength
        return entry['threshold'],entry['normalizers']

    def _report_offset(self,par,channel,source,money):
        """Source bias applies to a measurement, never to a published amount.

        A reported fee total is a relative-error report of a number the schedule
        already fixes: the error is the applicant's rounding, not a systematic
        per-source bias worth learning. Giving money a `par['source']` offset
        would quietly reintroduce the hierarchy this basis exists to avoid, and
        the offset would be identified only by how wrong applicants are about a
        published price. Money therefore reuses the duration report kernel on the
        log scale, with the same reporting scale and contamination mixture, at a
        zero offset.
        """
        return 0. if money else float(par['source'][channel,source])

    def _collapsed_observation_log_probability(self,p,row,par):
        """Integrate the existing Student-t4 report kernel over one normal case effect."""
        o=row['observation']
        operation=p['global_indices'][0]
        spread=math.hypot(float(par['sigma'][0]),self.cfg.common_case_sd)
        log_values=float(par['mu'][0,operation])+spread*self.collapsed_case_nodes
        conditional=duration_report_log_probability(o,np.exp(log_values),
            self._report_offset(par,row['channel'],row['source'],False),
            row['report_scale'],self.cfg.contamination)
        return float(logsumexp(conditional+self.collapsed_case_log_weights))

    def _observation_parts(self,p,trace,population,par,return_log_terms=False):
        """Batch reporting kernels; retain the scalar reference for target checks."""
        compiled=p['compiled']
        entries=compiled['entries']
        values=np.zeros(len(entries))
        scales=compiled['report_scales'].copy()
        supported=np.ones(len(entries),dtype=bool)
        structural_survival=np.zeros(len(entries),dtype=bool)
        typical_terms={}
        cache={}
        for j,row in enumerate(entries):
            o,operator=row['observation'],row['operator']
            if o['id'] in p.get('collapsed_observation_ids',()):
                typical_terms[j]=self._collapsed_observation_log_probability(p,row,par)
                continue
            if compiled['residuals'][j]:
                continue
            is_population=o['case_id'] is None
            if not is_population and structural_survival_is_one(p,o,trace):
                structural_survival[j]=True
                continue
            scope=tuple(o.get('population_path_scope',[]))
            key=(is_population,scope,o.get('population_condition'),row['signature'])
            try:
                source_trace=population if is_population else trace
                if is_population:
                    source_trace=observation_population(population,operator,o)
                if key not in cache:
                    cache[key]=source_trace.values(operator)
                predicted=cache[key]
                if is_population:
                    if o['statistic']=='typical_range':
                        typical_terms[j]=typical_range_log_probability(o,source_trace,predicted,
                            self._report_offset(par,row['channel'],row['source'],False),
                            self.cfg.contamination,duration_report_log_probability)
                        continue
                    stat_key=key+(o['statistic'],)
                    if stat_key not in cache:
                        cache[stat_key]=population_statistic(source_trace,predicted,o['statistic'])
                    values[j]=cache[stat_key]
                else:
                    values[j]=predicted[p['case_index'][o['case_id']]]
            except (KeyError, UnavailableTraceQuantity):
                supported[j]=False
        count=compiled['counts']
        likelihood=np.empty(len(entries))
        if count.any():
            likelihood[count]=count_log_probability(compiled['lower'][count],compiled['upper'][count],
                values[count],self.cfg.count_error_scale,self.cfg.contamination)
        duration=~count & ~compiled['residuals']
        for j,ll in typical_terms.items():
            likelihood[j]=ll
            duration[j]=False
        if duration.any():
            bias=np.where(compiled['money'][duration],0.,
                par['source'][compiled['channels'][duration],compiled['sources'][duration]])
            likelihood[duration]=duration_log_probability(compiled['lower'][duration],compiled['upper'][duration],
                values[duration],bias,scales[duration],self.cfg.contamination)
            for j in np.flatnonzero(duration):
                o=entries[j]['observation']
                if 'report_intervals' in o:
                    likelihood[j]=duration_report_log_probability(o,values[j],
                        self._report_offset(par,compiled['channels'][j],compiled['sources'][j],compiled['money'][j]),
                        scales[j],self.cfg.contamination)
        likelihood[compiled['residuals']]=compiled['residual_ll'][compiled['residuals']]
        likelihood[~supported]=-math.inf
        likelihood[structural_survival]=0.
        likelihood+=compiled['logweights']
        if return_log_terms:
            return likelihood
        return {p['id']+':'+ident:float(likelihood[start] if end==start+1 else logsumexp(likelihood[start:end]))
                for ident,start,end in compiled['groups']}

    def _scalar_observation_terms(self,p,trace,population,par):
        """Unbatched reporting reference, including explicitly weighted populations."""
        terms=[]
        for row in p['compiled']['entries']:
            o,operator=row['observation'],row['operator']
            if o['id'] in p.get('collapsed_observation_ids',()):
                ll=self._collapsed_observation_log_probability(p,row,par)
            elif o['case_id'] is not None and structural_survival_is_one(p,o,trace):
                ll=0.
            elif operator['basis']=='unmodeled_duration':
                ll=unmodeled_duration_log_probability(o['lower'],o['upper'],operator,o.get('report_intervals'))
            else:
                try:
                    source_trace=population if o['case_id'] is None else trace
                    if o['case_id'] is None:
                        source_trace=observation_population(population,operator,o)
                    values=source_trace.values(operator)
                    if o['case_id'] is None:
                        if o['statistic']=='typical_range':
                            ll=typical_range_log_probability(o,source_trace,values,
                                self._report_offset(par,row['channel'],row['source'],False),
                                self.cfg.contamination,duration_report_log_probability)
                            terms.append(math.log(row['weight'])+float(ll))
                            continue
                        value=population_statistic(source_trace,values,o['statistic'])
                    else:
                        value=values[p['case_index'][o['case_id']]]
                    scale=row['report_scale']
                    if operator['basis'] in COUNT_BASES:
                        ll=count_log_probability(o['lower'],o['upper'],value,
                            self.cfg.count_error_scale,self.cfg.contamination)
                    else:
                        ll=duration_report_log_probability(o,value,
                            self._report_offset(par,row['channel'],row['source'],
                                                operator['basis'] in MONEY_BASES),
                            scale,self.cfg.contamination)
                except (KeyError,UnavailableTraceQuantity):
                    ll=-math.inf
            terms.append(math.log(row['weight'])+float(ll))
        return np.asarray(terms)

    def _quantile_cohort_parts(self,p,population,par,vectorized=True,return_terms=False):
        """One factor and one interpretation per cohort, not per quantile.

        Joint order-statistic sampling is integrated before source reporting
        error. The residual candidate is the declared process-independent joint
        reference (product of its report references), not a sampled case cohort.
        """
        output,all_terms={},{}
        for cohort in p['quantile_cohorts']:
            terms=[]
            cohort_scale=p['quantile_report_scales'][cohort['id']]
            for operator,weight in zip(cohort['operators'],cohort['operator_weights']):
                if operator['basis']=='unmodeled_duration':
                    ll=sum(float(unmodeled_duration_log_probability(r['lower'],r['upper'],operator,
                        r.get('report_intervals'))) for r in cohort['reports'])
                else:
                    try:
                        selected=observation_population(population,operator,cohort)
                        values=cohort['grid'].values(selected.values(operator),getattr(selected,'weights',None))
                        channel=operator['basis'] if operator['basis'] in CHANNELS else 'elapsed'
                        offset=par['source'][CHANNELS.index(channel),self.sources.index(cohort['source_family'])]
                        if vectorized:
                            conditional=np.column_stack([duration_report_log_probability(r,values[:,j],
                                offset,cohort_scale,self.cfg.contamination)
                                for j,r in enumerate(cohort['reports'])]).sum(axis=1)
                        else:
                            conditional=[sum(float(duration_report_log_probability(r,value,
                                offset,cohort_scale,self.cfg.contamination))
                                for r,value in zip(cohort['reports'],row)) for row in values]
                        ll=float(logsumexp(conditional)-math.log(cohort['grid'].size))
                    except (KeyError,UnavailableTraceQuantity):
                        ll=-math.inf
                terms.append(math.log(weight)+ll)
            all_terms[cohort['id']]=np.asarray(terms)
            output[p['id']+':quantile_cohort:'+cohort['id']]=float(logsumexp(terms))
        return all_terms if return_terms else output

    def _histogram_cohort_parts(self,p,population,return_terms=False):
        """One exact multinomial per cohort, marginalized over one interpretation.

        Bin mass uses the finite population integration measure, not a smoothed
        report density. Zero support remains zero. This experimental path needs
        a population-grid refinement check before any fit can be accepted.
        """
        output,all_terms={},{}
        for cohort in p['histogram_cohorts']:
            terms=[]
            for operator,weight in zip(cohort['operators'],cohort['operator_weights']):
                if weight==0:
                    terms.append(-math.inf)
                    continue
                try:
                    selected=observation_population(population,operator,cohort)
                    if hasattr(selected,'analytic_elapsed_log_parameters'):
                        ll=phase_histogram_log_probability(cohort['bin_counts'],cohort['bin_edges'],
                            *selected.analytic_elapsed_log_parameters)
                    else:
                        probabilities=population_bin_probabilities(selected.values(operator),
                            cohort['bin_edges'],getattr(selected,'weights',None))
                        ll=histogram_log_probability(cohort['bin_counts'],probabilities)
                except (KeyError,UnavailableTraceQuantity):
                    ll=-math.inf
                terms.append(math.log(weight)+ll)
            all_terms[cohort['id']]=np.asarray(terms)
            output[p['id']+':histogram_cohort:'+cohort['id']]=float(logsumexp(terms))
        return all_terms if return_terms else output

    def absent_event_censoring_metadata(self):
        return {p['id']:dict(declarations=deepcopy(list(p['absent_event_censoring'].values())),
            extra_sampled_coordinates=0,
            qualification='Pending event times on explicitly absent paths contribute survival probability one; '
                'not missing-data imputation, a learned path frequency, censoring-selection correction '
                'or a population event-time estimate.')
            for p in self.programs if p.get('absent_event_censoring')}

    def joint_duration_report_metadata(self):
        return {p['id']:dict(groups=[deepcopy(g['declaration'])
                for g in p['joint_duration_reports']],
            member_observation_count=sum(len(g['members']) for g in p['joint_duration_reports']),
            integrated_error_coordinates=0, calibration_verified=False,
            report_log_scale=self.cfg.report_sd, contamination=self.cfg.contamination,
            qualification='One shared multiplicative Student-t error and broad-component indicator per group; '
                'relative timing is exact within supplied bounds. Declared sensitivity, not learned dependence '
                'or a conservative guarantee. A shared source-family label does not prove a shared artifact '
                'or reporting error. Distinct groups remain conditionally independent given the case.')
            for p in self.programs if p.get('joint_duration_reports')}

    def _joint_duration_group_parts(self,p,trace,par):
        output={}
        for group in p.get('joint_duration_reports',[]):
            members=[o for o in group['members'] if not structural_survival_is_one(p,o,trace)]
            try:
                if not members:
                    output[p['id']+':report_group:'+group['declaration']['id']]=0.
                    continue
                index=p['case_index'][group['declaration']['case_id']]
                values=[trace.values(o['operators'][0])[index] for o in members]
                source=self.sources.index(members[0]['source_family'])
                ll=shared_log_error_probability([o['lower'] for o in members],
                    [math.inf if o['upper'] is None else o['upper'] for o in members],values,
                    self._report_offset(par,0,source,False),self.cfg.report_sd,self.cfg.contamination)
            except (KeyError,UnavailableTraceQuantity):
                ll=-math.inf
            output[p['id']+':report_group:'+group['declaration']['id']]=float(ll)
        return output

    def _case_path_likelihood(self,p,z,par,ri,vectorized=True,details=False):
        """Integrate one path per case over the JOINT likelihood of its reports.

        Known path/outcome scope conditions the mixture; it is not a counted
        population observation. All reports of one case share a path and latent
        durations. Inventory alternatives remain the outer program-wide variable.
        """
        route=p['routes'][ri]
        probabilities=self.path_probabilities(route,z)
        paths=route['paths']
        need_population=any(o['case_id'] is None and o['statistic']!='report_only'
            for o in p['observations']) or bool(p['quantile_cohorts'] or p['histogram_cohorts']) or bool(p['selected_cases'] and self.cfg.selection_sd)
        population=self._likelihood_population(p,z,par,ri) if need_population else None
        traces=[self.trace(p,z,par,ri,path_index=j) if p['cases'] else None
                for j in range(len(paths))]
        terms=np.stack([self._observation_parts(p,t,population,par,return_log_terms=True)
                        if vectorized else self._scalar_observation_terms(p,t,population,par)
                        for t in traces])
        group_ll=np.stack([logsumexp(terms[:,start:end],axis=1)
                          for _,start,end in p['compiled']['groups']],axis=1) if p['observations'] else np.empty((len(paths),0))
        if p.get('joint_duration_reports'):
            for j,trace in enumerate(traces):
                joined=self._joint_duration_group_parts(p,trace,par)
                for group in p['joint_duration_reports']:
                    columns=group['columns']
                    # Replace, never add alongside the member report factors.
                    group_ll[j,columns]=0.
                    group_ll[j,columns[0]]=joined[p['id']+':report_group:'+group['declaration']['id']]
        output={}
        case_weights={}
        selection_values=selection_normalizers=None
        if p['selected_cases'] and self.cfg.selection_sd:
            strength=self.cfg.selection_sd*abs(float(z[p['selection'][0]]))
            threshold,selection_normalizers=self._selection_population_summary(p,population,strength,ri)
            def logweight(values):
                h=expit((np.log(values)-threshold)/self.cfg.selection_width)
                return np.logaddexp(np.log1p(-h),strength+np.log(h))
            selection_values=np.stack([logweight(t.event('initial_decision')) for t in traces])
        for case in p['cases']:
            scope=p['case_path_scope'].get(case)
            allowed=np.array([scope is None or path['id'] in scope for path in paths])
            if not allowed.any():
                output[p['id']+':case:'+case]=-math.inf
                case_weights[case]=np.zeros(len(paths))
                continue
            fixed=p.get('case_path_priors',{}).get(case,{}).get(route['id'])
            if fixed is None:
                logprior=np.full(len(paths),-math.inf)
                logprior[allowed]=np.log(probabilities[allowed])-math.log(probabilities[allowed].sum())
            else:
                # Apply one case-specific prior to the JOINT report likelihood,
                # never once per sentence and never to population path rates.
                logprior=fixed['log_prior']
            columns=[i for i,o in enumerate(p['observations']) if o['case_id']==case]
            joint=logprior+group_ll[:,columns].sum(axis=1)
            if case in p['selected_cases'] and self.cfg.selection_sd:
                joint=joint+selection_values[:,p['case_index'][case]]
                normalizer=logsumexp(logprior+selection_normalizers)
            else:
                normalizer=0.
            value=float(logsumexp(joint))
            output[p['id']+':case:'+case]=value-normalizer
            case_weights[case]=np.exp(joint-value) if math.isfinite(value) else np.zeros(len(paths))
        for i,o in enumerate(p['observations']):
            if o['case_id'] is None:
                output[p['id']+':'+o['id']]=float(group_ll[0,i])
        output.update(self._quantile_cohort_parts(p,population,par,vectorized))
        output.update(self._histogram_cohort_parts(p,population))
        q,_=self.repeat_parameters(p,z)
        for i,row in enumerate(p['rates']):
            scope=row.get('population_path_scope')
            selected=np.array([scope is None or path['id'] in scope for path in paths])
            if not selected.any():
                output[p['id']+':cohort:'+str(i)]=-math.inf
                continue
            weights=np.where(selected,probabilities,0.)
            weights=weights/weights.sum()
            available=np.array([any(b.repeat_key==row['repeat_key'] for b in path['blocks']) for path in paths])
            probability=q[p['repeat_keys'].index(row['repeat_key'])]*float(weights@available)
            k,n=row['successes'],row['trials']
            output[p['id']+':cohort:'+str(i)]=float(xlogy(k,probability)+xlog1py(n-k,-probability))
        if details:
            return output,dict(terms=terms,group_ll=group_ll,case_weights=case_weights,
                               probabilities=probabilities)
        return output

    def log_likelihood_reference(self,z,structures,parts=False):
        return self.log_likelihood(z,structures,parts,vectorized=False)

    def positive_repeat_count_parts(self,p,z):
        """Route-disjoint completed-positive counts, once per evidence unit."""
        families = {f['id']: f for f in p.get('count_only_repeat_families', [])}
        output = {}
        for row in p.get('positive_repeat_counts', []):
            r = float(betaincinv(2., 3., ndtr(z[families[row['family_id']]['coordinate']])))
            selection = row['severity_selection']
            output[p['id']+':positive_repeat_count:'+row['id']] = positive_repeat_log_probability(
                row['count'], r, selection['log_tilt'], selection['threshold'])
        return output

    def log_likelihood(self,z,structures,parts=False,vectorized=True,*,_program_index=None):
        if _program_index is not None and not 0 <= _program_index < len(self.programs):
            raise ValueError('Unknown program index for a conditional likelihood')
        par=self.parameters(z)
        output={}
        try:
            for pi,(p,ri) in enumerate(zip(self.programs,structures)):
                if _program_index is not None and pi != _program_index:
                    continue
                output.update(self.positive_repeat_count_parts(p,z))
                if 'paths' in p['routes'][ri]:
                    output.update(self._case_path_likelihood(p,z,par,ri,vectorized))
                    continue
                trace=(self.trace(p,z,par,ri) if p['cases'] and
                       self.cfg.population_integration!='collapsed_single_phase_quadrature' else None)
                need_pop=any(o['case_id'] is None and o['statistic']!='report_only' for o in p['observations']) or bool(p['quantile_cohorts'] or p['histogram_cohorts']) or (p['selected_cases'] and self.cfg.selection_sd)
                population=self._likelihood_population(p,z,par,ri) if need_pop else None
                output.update(self._quantile_cohort_parts(p,population,par,vectorized))
                output.update(self._histogram_cohort_parts(p,population))
                if vectorized:
                    output.update(self._observation_parts(p,trace,population,par))
                for o in ([] if vectorized else p['observations']):
                    terms=[]
                    channel=o['operators'][0]['basis']
                    ch=CHANNELS.index(channel) if channel in CHANNELS else 0
                    # One observation cannot mix money with anything else, so the
                    # first operator settles whether a source offset applies.
                    offset=self._report_offset(par,ch,self.sources.index(o['source_family']),
                                               channel in MONEY_BASES)
                    scale=p['report_scales'].get(o['id'],self.cfg.report_sd)
                    for operator,weight in zip(o['operators'],o['operator_weights']):
                        if o['id'] in p.get('collapsed_observation_ids',()):
                            row=next(row for row in p['compiled']['entries']
                                     if row['observation']['id']==o['id'])
                            terms.append(math.log(weight)+self._collapsed_observation_log_probability(p,row,par))
                            continue
                        if operator['basis']=='unmodeled_duration':
                            terms.append(math.log(weight)+float(unmodeled_duration_log_probability(
                                o['lower'],o['upper'],operator,o.get('report_intervals'))))
                            continue
                        try:
                            source_trace=(observation_population(population,operator,o)
                                          if o['case_id'] is None else trace)
                            values=source_trace.values(operator)
                            if o['case_id'] is None:
                                if o['statistic']=='typical_range':
                                    ll=typical_range_log_probability(o,source_trace,values,offset,
                                        self.cfg.contamination,duration_report_log_probability)
                                    terms.append(math.log(weight)+float(ll))
                                    continue
                                value=(population_statistic(source_trace,values,o['statistic'])
                                    if self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') else
                                    float(np.mean(values) if o['statistic']=='mean' else
                                          np.quantile(values,.9 if o['statistic']=='p90' else .5)))
                            else:
                                value=values[p['case_index'][o['case_id']]]
                            if operator['basis'] in COUNT_BASES:
                                ll=count_log_probability(o['lower'],o['upper'],value,self.cfg.count_error_scale,self.cfg.contamination)
                            else:
                                ll=duration_report_log_probability(o,value,offset,scale,self.cfg.contamination)
                            terms.append(math.log(weight)+float(ll))
                        except (KeyError, UnavailableTraceQuantity):
                            # An absent operation makes this interpretation impossible,
                            # not a zero-duration observation.
                            terms.append(-math.inf)
                    output[p['id']+':'+o['id']]=float(logsumexp(terms))
                if p.get('joint_duration_reports'):
                    for group in p['joint_duration_reports']:
                        for observation in group['members']:
                            del output[p['id']+':'+observation['id']]
                    output.update(self._joint_duration_group_parts(p,trace,par))
                if p['selected_cases'] and self.cfg.selection_sd:
                    strength=self.cfg.selection_sd*abs(float(z[p['selection'][0]]))
                    threshold,normalizers=self._selection_population_summary(p,population,strength,ri)
                    def logweight(durations):
                        from scipy.special import expit
                        h=expit((np.log(durations)-threshold)/self.cfg.selection_width)
                        return np.logaddexp(np.log1p(-h),strength+np.log(h))
                    normalizer=normalizers[0]
                    individual=logweight(trace.event('initial_decision'))
                    for case in p['selected_cases']:
                        output[p['id']+':selection:'+case]=float(individual[p['case_index'][case]]-normalizer)
                q,_=self.repeat_parameters(p,z)
                route_keys={b.repeat_key for b in p['routes'][ri]['blocks']}
                for i,row in enumerate(p['rates']):
                    probability=q[p['repeat_keys'].index(row['repeat_key'])] if row['repeat_key'] in route_keys else 0.
                    k,n=row['successes'],row['trials']
                    output[p['id']+':cohort:'+str(i)]=float(xlogy(k,probability)+xlog1py(n-k,-probability))
            return output if parts else sum(output.values())
        except (FloatingPointError,OverflowError):
            if parts:
                raise
            return -math.inf

    def operation_centered_duration_update(self,z,structures,current,rng):
        """Conditional-Gaussian ESS in operation means plus exact null refresh.

        For m=A h, m_G|m_-G is Gaussian with precision (AA')^-1_GG.
        An ESS update of its standardized residual uses the unchanged program
        likelihood. A' (AA')^-1 maps the change back to h without changing any
        other operation mean. Finally ker(A) is independent N(0,I) conditional
        on m and the data; refreshing it explores agency/task/operation ridges.
        """
        if self.duration_conditionals is None:
            raise ValueError('Operation-centered transitions are not configured')
        calls=0
        for ch in self.active_channels:
            coordinates=self.hierarchy_coordinates[ch]
            for pi,indices,precision_rows,factor,scale,regression in self.duration_conditionals:
                means=self.design@z[coordinates]
                residual=cho_solve((factor,True),precision_rows@means)
                # scale is inverse upper Cholesky, hence upper triangular.
                standardized=solve_triangular(scale,residual,lower=False)
                original=z.copy()
                def proposal(value):
                    trial=original.copy()
                    trial[coordinates]+=regression@(scale@value-residual)
                    return trial
                local=self.log_likelihood(z,structures,_program_index=pi)
                draw,value,used=elliptical_slice(standardized,np.arange(len(indices)),
                    lambda u:self.log_likelihood(proposal(u),structures,_program_index=pi),local,rng)
                z=proposal(draw)
                current+=value-local
                calls+=used+1
            # Proper priors resolve the decomposition probabilistically. These
            # directions should retain unit variance, not get stuck near initials.
            basis=self.duration_null_basis
            z[coordinates]+=basis@(rng.normal(size=basis.shape[1])-basis.T@z[coordinates])
        # Avoid accumulating round-off from local likelihood differences.
        return z,self.log_likelihood(z,structures),calls+1

    def centered_duration_update(self,z,structures,current,rng):
        """Exact Gaussian conditional at fixed latent case durations, plus MH.

        Jointly resample hierarchy and case noises conditional on every realized
        operation duration (including inactive route alternatives). This preserves
        their Gaussian prior conditional and the entire case-report likelihood.
        The likelihood correction is needed for population summaries/selection,
        which can change when population parameters move at fixed observed cases.
        No fitted posterior is used as a new prior or independent pseudo-observation.
        """
        trial=z.copy()
        sigma=self.parameters(z)['sigma']
        common=self.cfg.common_case_sd
        for ch,coordinates in enumerate(self.hierarchy_coordinates):
            if ch not in self.active_channels:
                continue
            precision=np.eye(len(coordinates))
            rhs=np.zeros(len(coordinates))
            retained=[]
            variance=sigma[ch]**2
            for p in self.programs:
                if not p['cases'] or not p['case_coordinates'].size:
                    continue
                n=len(p['global_indices'])
                design=self.design[p['global_indices']]
                channel_position=self.active_channels.index(ch)
                case_coordinates=p['case_coordinates'][:,channel_position*(n+1):(channel_position+1)*(n+1)]
                noise=z[case_coordinates]
                eta=(design@z[coordinates])[None,:]+sigma[ch]*noise[:,:n]+common*noise[:,n,None]
                weighted=design/variance-common**2*design.sum(axis=0)[None,:]/(variance*(variance+n*common**2))
                precision+=len(noise)*design.T@weighted
                rhs+=weighted.T@eta.sum(axis=0)
                retained.append((design,case_coordinates,eta,n))
            factor=np.linalg.cholesky(precision)
            location=cho_solve((factor,True),rhs)
            draw=location+solve_triangular(factor.T,rng.normal(size=len(coordinates)),lower=False)
            trial[coordinates]=draw
            for design,coordinates,eta,n in retained:
                residual=eta-(design@draw)[None,:]
                denominator=variance+n*common**2
                b=common*residual.sum(axis=1)/denominator+math.sqrt(variance/denominator)*rng.normal(size=len(eta))
                noise=(residual-common*b[:,None])/sigma[ch]
                trial[coordinates]=np.column_stack((noise,b))
        if self.cfg.within_visit_phases and self.cfg.phase_case_sd>0:
            # Same Gaussian conditional for phase logits, holding every realized
            # fraction fixed. Timing and work channels do not become phase priors.
            coordinates=self.phase_coordinates
            variance=self.cfg.phase_case_sd**2
            precision=np.eye(len(coordinates))
            rhs=np.zeros(len(coordinates))
            retained=[]
            for p in self.programs:
                if not p['cases'] or not p['case_coordinates'].size:
                    continue
                design=self.phase_design[p['global_indices']]
                case_coordinates=p['case_coordinates'][:,p['phase_offset']:p['dwell_offset']]
                eta=(design@z[coordinates])[None,:]+self.cfg.phase_case_sd*z[case_coordinates]
                precision+=len(eta)*design.T@design/variance
                rhs+=design.T@eta.sum(axis=0)/variance
                retained.append((design,case_coordinates,eta))
            factor=np.linalg.cholesky(precision)
            draw=cho_solve((factor,True),rhs)+solve_triangular(factor.T,rng.normal(size=len(coordinates)),lower=False)
            trial[coordinates]=draw
            for design,coordinates,eta in retained:
                trial[coordinates]=(eta-(design@draw)[None,:])/self.cfg.phase_case_sd
        value=self.log_likelihood(trial,structures)
        if math.log(max(rng.random(),np.finfo(float).tiny))<value-current:
            return trial,value
        return z,current

    def case_scale_interweave_update(self,z,structures,current,rng):
        """Exact spread/residual ESS move; ordinary full likelihood returned."""
        return _case_scale_interweave_update(self,z,structures,current,rng)

    def case_scale_transition_report(self):
        return case_scale_transition_report(self)

    def source_location_update(self,z,structures,current,rng):
        """Prior-conditional scale/offset move; MH covers numerical edge cases."""
        if self.source_offset_hierarchy is not None:
            # The legacy direction assumes independent fixed-SD document
            # offsets.  It is not a prior-preserving direction through the
            # learned-scale, centered hierarchy.
            return z,current
        if not self.cfg.source_sd or not len(self.sources):
            return z,current
        trial=z.copy()
        direction=np.r_[1/self.cfg.location_sd,np.full(len(self.sources),-1/self.cfg.source_sd)]
        direction/=np.linalg.norm(direction)
        for ch in self.active_channels:
            coordinates=np.r_[self.location[ch],self.source[ch]]
            trial[coordinates]+=direction*(rng.normal()-direction@trial[coordinates])
        value=self.log_likelihood(trial,structures)
        if math.log(max(rng.random(),np.finfo(float).tiny))<value-current:
            return trial,value
        return z,current

    def source_hierarchy_interweave_update(self,z,structures,current,rng):
        """Optional MH scale moves at fixed actual source offsets.

        Each proposal includes the Gaussian-coordinate prior ratio and the
        non-volume-preserving ``-K * log_sd * epsilon`` Jacobian.  The full
        likelihood difference is evaluated even though actual offsets should
        be invariant, making numerical or future wiring errors rejectable.
        """
        hierarchy = self.source_offset_hierarchy
        if hierarchy is None or self.cfg.source_hierarchy_sampler != 'interwoven':
            return z,current,0
        calls=0
        for level in hierarchy.interweave_levels:
            epsilon=float(rng.normal(scale=SOURCE_HIERARCHY_INTERWEAVE_STEP))
            proposal=hierarchy.interweave_proposal(z,level,epsilon)
            if proposal is None:
                continue
            trial=proposal['state']
            value=self.log_likelihood(trial,structures)
            calls+=1
            if not math.isfinite(value):
                continue
            log_ratio=value-current+proposal['correction']
            if (math.isfinite(log_ratio) and
                    math.log(max(rng.random(),np.finfo(float).tiny)) < log_ratio):
                z,current=trial,value
        return z,current,calls

    def expected_burden(self,p,z,parameters,route_index,*,path_index=None):
        """Exact population means for counts/resources, not averages of QMC cases."""
        route=p['routes'][route_index]
        if 'paths' in route:
            if path_index is None:
                probabilities=self.path_probabilities(route,z)
                values=[self.expected_burden(p,z,parameters,route_index,path_index=j)
                        for j in range(len(route['paths']))]
                # Unknown work/agency identity on any positive-mass path remains
                # unknown, rather than being dropped and called zero burden.
                common=set.intersection(*(set(value) for value in values))
                result={key:float(sum(weight*value[key] for weight,value in zip(probabilities,values)))
                        for key in common if key!='fee_total_case_sd'}
                if 'fee_total_case_sd' in common:
                    second=sum(weight*(value['fee_total_case_sd']**2+value['mean_fee_total']**2)
                               for weight,value in zip(probabilities,values))
                    result['fee_total_case_sd']=math.sqrt(max(0.,second-result['mean_fee_total']**2))
                return result
            route=route['paths'][path_index]
        operations=route['operations']
        q,r=self.repeat_parameters(p,z)
        multiplicity={op.id:1. for op in operations}
        for block in route['blocks']:
            if block.repeat_key is not None:
                j=p['repeat_keys'].index(block.repeat_key)
                for aid in block.operations:
                    multiplicity[aid]=1+q[j]/(1-r[j])
        result=dict(mean_visit_count=float(sum(multiplicity.values())),mean_operation_count=float(len(operations)))
        # Applicant participation is a declared proxy, not inferred from elapsed
        # time. Unknown flags/roles must not turn an unreported step into zero.
        applicant=[True if op.actor_role=='payer' or op.payer_work is True else
                   False if op.actor_role!='unknown' and op.payer_work is False else None
                   for op in operations]
        if all(value is not None for value in applicant):
            result['mean_applicant_visit_count']=float(sum(multiplicity[op.id]
                for op,present in zip(operations,applicant) if present))
            result['mean_applicant_operation_count']=float(sum(applicant))
        if all(op.fee is not None for op in operations):
            result['mean_fee_total']=float(sum(multiplicity[op.id]*op.fee for op in operations))
            # Fees repeat according to the existing per-visit fee contract.
            # Shared repeat keys induce shared multiplicities, not independent
            # fee draws. Case-path variance is combined above by total variance.
            fees={op.id:op.fee for op in operations}
            fees_by_repeat={}
            for block in route['blocks']:
                if block.repeat_key is not None:
                    fees_by_repeat[block.repeat_key]=fees_by_repeat.get(block.repeat_key,0.)+sum(fees[a] for a in block.operations)
            variance=0.
            for key,amount in fees_by_repeat.items():
                j=p['repeat_keys'].index(key)
                variance+=amount**2*q[j]*(1+r[j]-q[j])/(1-r[j])**2
            result['fee_total_case_sd']=math.sqrt(variance)
        if not any(op.actor_role=='unknown' or (op.actor_role=='agency' and op.actor_id is None) for op in operations):
            result['mean_agency_count']=float(len({op.actor_id for op in operations if op.actor_role=='agency'}))
        for ch,field in ((1,'payer_work'),(2,'agency_work')):
            if ch not in self.active_channels:
                continue
            if any(getattr(op,field) is None for op in operations):
                continue
            total=0.
            for idx,op in zip(route['indices'],operations):
                if getattr(op,field):
                    total+=multiplicity[op.id]*math.exp(parameters['mu'][ch,idx]
                              +.5*(parameters['sigma'][ch]**2+self.cfg.common_case_sd**2))
            result['mean_'+CHANNELS[ch]]=total
        return result

    def phase_means(self, parameters, nodes=None, weights=None):
        """Population per-cycle phase means; conditional cycle/fraction independence.

        Logistic-normal moments use deterministic Gaussian integration, NOT a
        conversion from elapsed service to labor. Return waiting and service days.
        """
        if not self.cfg.within_visit_phases:
            raise ValueError('Phase expectations require an enabled phase model')
        nodes=self.phase_nodes if nodes is None else nodes
        weights=self.phase_weights if weights is None else weights
        logits=parameters['phase_logit'][:,None]+self.cfg.phase_case_sd*nodes[None,:]
        cycle=np.exp(parameters['mu'][0]+.5*(parameters['sigma'][0]**2+self.cfg.common_case_sd**2))
        return cycle*(expit(-logits)@weights),cycle*(expit(logits)@weights)

    def hierarchy_design_audit(self):
        """Necessary design check, NOT a claim that source data identify effects.

        Even if every operation mean were known, two agencies in disconnected
        actor/task components cannot have their relative effects distinguished
        from task-mix differences without distributional prior assumptions.
        Operation random effects and unknown means only add uncertainty. The
        union of route hypotheses is an optimistic screen, not observed staffing.
        """
        design=np.column_stack((np.eye(len(self.agencies))[self.agency_indices],
                                np.eye(len(self.tasks))[self.task_indices]))
        _,singular,right=np.linalg.svd(design,full_matrices=False)
        threshold=max(design.shape)*np.finfo(float).eps*singular[0]
        row_basis=right[singular>threshold]
        public=sorted({op['op'].actor_id for op in self.operations
                       if op['op'].actor_role=='agency' and op['op'].actor_id is not None})
        contrasts=[]
        for i,a in enumerate(public):
            for b in public[i+1:]:
                contrast=np.zeros(design.shape[1])
                contrast[self.agencies.index(a)]=1.
                contrast[self.agencies.index(b)]=-1.
                residual=contrast-row_basis.T@(row_basis@contrast)
                contrasts.append(dict(agencies=[a,b],potentially_separable_from_task_mix=bool(np.linalg.norm(residual)<1e-8)))
        return dict(agency_contrasts=contrasts,
            warning='This is an optimistic actor/task design screen, assuming operation means were known. Passing is not evidence that the supplied claims identify an effect.',
            prior_dependent_contrasts=[r['agencies'] for r in contrasts if not r['potentially_separable_from_task_mix']],
            interpretation='Agency-associated differences conditional on task/operation priors, not intrinsic causal agency delay')

    def _finite_initial_routes(self,z,structures,rng,attempts=16):
        """Find a supported start, without changing the target or saved checkpoints.

        Given the continuous state, programs' route likelihoods factor. Search
        each supplied finite route set separately, not their Cartesian product.
        An absent observed operation can rule out a route exactly; unlucky route
        initialization must not be mistaken for an incompatible evidence set.
        Gaussian retries are bounded and only initialize fresh chains.
        """
        unsupported=[]
        for attempt in range(attempts):
            if attempt:
                z=rng.normal(size=self.layout.size)
            if self.joint_inventory_prior is not None:
                try:
                    candidate,value,_=self.joint_inventory_prior.update(self,z,rng)
                except ValueError as error:
                    if 'No supported joint inventory' not in str(error):
                        raise
                    continue
                return z,candidate,value
            candidate=structures.copy()
            unsupported=[]
            for pi,p in enumerate(self.programs):
                terms=[]
                for ri,route in enumerate(p['routes']):
                    candidate[pi]=ri
                    value=self.log_likelihood(z,candidate,_program_index=pi)
                    terms.append(value+math.log(route['prior_weight']))
                finite=np.flatnonzero(np.isfinite(terms))
                if not len(finite):
                    unsupported.append(p['id'])
                    continue
                weights=np.asarray(terms)[finite]
                candidate[pi]=rng.choice(finite,p=np.exp(weights-logsumexp(weights)))
            if not unsupported:
                value=self.log_likelihood(z,candidate)
                if math.isfinite(value):
                    return z,candidate,value
        raise ValueError('No finite initial state after checking every supplied route at '
            +str(attempts)+' prior states; inspect observation/route support for '
            +', '.join(unsupported or [p['id'] for p in self.programs]))

    def sample(self,progress=None,initial=None,*,case_local_updates=False):
        if not isinstance(case_local_updates,bool):
            raise ValueError('case_local_updates must be an explicit boolean')
        local_views=case_update_views(self) if case_local_updates else {}
        c=self.cfg
        states=np.empty((c.chains,c.draws,self.layout.size))
        routes=np.empty((c.chains,c.draws,len(self.programs)),dtype=int)
        likelihood=np.empty((c.chains,c.draws))
        calls=[]
        if initial is not None:
            zi,si=map(np.asarray,initial)
            if (not np.issubdtype(zi.dtype,np.number) or not np.isrealobj(zi)
                    or np.issubdtype(zi.dtype,np.bool_)):
                raise ValueError('Checkpoint states must be real numeric values')
            try:
                zi=np.asarray(zi,dtype=np.float64)
                initial_finite=bool(np.isfinite(zi).all())
            except (TypeError,ValueError,OverflowError) as error:
                raise ValueError('Checkpoint states must be finite float64 values') from error
            if (zi.shape!=(c.chains,self.layout.size) or si.shape!=(c.chains,len(self.programs))
                    or not initial_finite or not np.issubdtype(si.dtype,np.integer)
                    or any(np.any((si[:,i]<0)|(si[:,i]>=len(p['routes']))) for i,p in enumerate(self.programs))):
                raise ValueError('Checkpoint must have finite matching states and valid integer route indices')
        for chain in range(c.chains):
            rng=np.random.default_rng(c.seed+104729*chain)
            z=rng.normal(size=self.layout.size) if initial is None else zi[chain].copy()
            structural=(np.array([rng.integers(len(p['routes'])) for p in self.programs])
                        if initial is None else si[chain].copy())
            if self.joint_inventory_prior is not None:
                if initial is None:
                    structural=self.joint_inventory_prior.draw_prior(rng)
                else:
                    self.joint_inventory_prior.index(structural)
            value=self.log_likelihood(z,structural)
            evaluations=0
            if not math.isfinite(value):
                if initial is not None:
                    raise ValueError('Checkpoint latent route cannot explain the supplied observation contract')
                z,structural,value=self._finite_initial_routes(z,structural,rng)
            for iteration in range(c.warmup+c.draws):
                local_delta_dirty=False
                for block in self.blocks:
                    local=local_views.get(tuple(int(j) for j in block))
                    if local is None:
                        if local_delta_dirty:
                            value=refresh_full_likelihood(self,z,structural,value)
                            evaluations+=1
                            local_delta_dirty=False
                        z,value,used=elliptical_slice(z,block,lambda zz:self.log_likelihood(zz,structural),value,rng)
                    else:
                        pi,view=local
                        likelihood_fn=(
                            (lambda zz: self.log_likelihood(
                                zz, structural, _program_index=pi))
                            if view is None else
                            (lambda zz: case_log_likelihood(
                                self, view, zz, int(structural[pi]))))
                        before=likelihood_fn(z)
                        if not math.isfinite(before):
                            raise ValueError('Finite full state has a nonfinite local case factor')
                        z,after,used=elliptical_slice(z,block,likelihood_fn,before,rng)
                        value+=after-before
                        local_delta_dirty=True
                        evaluations+=1
                    evaluations+=used
                if local_delta_dirty:
                    # Check locality and reset roundoff before any global move.
                    value=refresh_full_likelihood(self,z,structural,value)
                    evaluations+=1
                if self.cfg.hierarchy_sampler == 'operation_centered':
                    z,value,used=self.operation_centered_duration_update(z,structural,value,rng)
                    evaluations+=used
                # Collapsed case programs retain case identities for provenance,
                # but have no sampled duration residuals to hold fixed or
                # re-center. Shared operation-centered transitions still run.
                has_sampled_case_durations=any(p['case_coordinates'].size for p in self.programs)
                if self.cfg.hierarchy_sampler == 'blocked' or has_sampled_case_durations:
                    z,value=self.centered_duration_update(z,structural,value,rng)
                    evaluations+=1
                # This follows the case-local full refresh and the centered
                # duration move, both of which return the ordinary full target.
                # Default blocked executes no branch and consumes no RNG.
                if self.cfg.case_scale_sampler == 'interwoven':
                    z,value,used=self.case_scale_interweave_update(
                        z,structural,value,rng)
                    evaluations+=used
                z,value=self.source_location_update(z,structural,value,rng)
                evaluations+=1
                z,value,used=self.source_hierarchy_interweave_update(
                    z,structural,value,rng)
                evaluations+=used
                if self.joint_inventory_prior is not None:
                    structural,value,used=self.joint_inventory_prior.update(self,z,rng)
                    evaluations+=used
                for pi,p in (enumerate(self.programs) if self.joint_inventory_prior is None else ()):
                    if len(p['routes'])<2:
                        continue
                    weights,values=[],[]
                    for ri,r in enumerate(p['routes']):
                        structural[pi]=ri
                        ll=self.log_likelihood(z,structural)
                        values.append(ll)
                        weights.append(ll+math.log(r['prior_weight']))
                    probabilities=np.exp(weights-logsumexp(weights))
                    structural[pi]=rng.choice(len(probabilities),p=probabilities)
                    value=values[structural[pi]]
                    evaluations+=len(values)
                if iteration>=c.warmup:
                    j=iteration-c.warmup
                    states[chain,j],routes[chain,j],likelihood[chain,j]=z,structural,value
                if progress and (iteration==0 or (iteration+1)%100==0):
                    progress(dict(chain=chain+1,iteration=iteration+1,log_likelihood=float(value),calls=evaluations))
            calls.append(evaluations)
        return states,routes,likelihood,calls

    def information_report(self, states, sampling_converged=None):
        blocks = dict(self.layout.slices)
        groups=[('location', self.location[:, None]), ('agency', self.agency),
                ('task', self.task), ('operation', self.operation)]
        if len(self.operation_location_design_coordinates):
            blocks['operation_location_design:elapsed'] = self.operation_location_design_coordinates
            for group in sorted({term['group'] for term in self.operation_location_design['terms']}):
                positions=[i for i,term in enumerate(self.operation_location_design['terms'])
                           if term['group'] == group]
                blocks['operation_location_design:'+group+':elapsed'] = (
                    self.operation_location_design_coordinates[positions])
        if self.source_offset_hierarchy is None:
            groups.append(('source',self.source))
        for name, coordinates in groups:
            for channel, row in zip(CHANNELS, coordinates):
                if channel in self.cfg.modeled_channels:
                    blocks[name+':'+channel] = row
        report=information_report(states, blocks, sampling_converged=sampling_converged)
        coarse=[p['id'] for p in self.programs if p['inventory_granularity']=='aggregate_phases']
        if coarse:
            for name,row in report['blocks'].items():
                component=name.split(':')[0]
                if component in ('agency','task','operation'):
                    row['statistical_contraction_gate_passed']=row['headline_eligible']
                    row['headline_eligible']=False
                    row['headline_exclusion']='Aggregate-phase effects are not recovered primitive-task or intrinsic-agency effects'
                elif component=='location':
                    row['estimand_qualification']='Shared log-location of represented inventories, including aggregate phases; not a primitive-step rate'
            report['aggregate_phase_programs']=coarse
        if self.operation_location_design is not None:
            report['operation_location_design']=dict(
                schema_version='operation-location-design/1',
                interpretation=self.operation_location_design['interpretation'],
                unlisted_operations=self.operation_location_design['unlisted_operations'],
                listed_rows=self.operation_location_design['listed_rows'],
                terms=self.operation_location_design['terms'],
                learned_hyper_scales=False,
                qualification='Whitened fixed-scale additive priors on elapsed operation log locations; labels do not establish geography or population prevalence.')
        if self.sampler_joint_blocks:
            report['sampler_joint_blocks']={block['id']:dict(
                coordinates=len(block['coordinates']),rationale=block['rationale'],
                selectors=block['selectors'],target_changed=False,
                overlap_policy='sequential_invariant_kernels')
                for block in self.sampler_joint_blocks}
        return report

    def scheduling_report(self):
        """Expose supplied block schedules without claiming learned overlap."""
        rows=[]
        for p in self.programs:
            for route in p['routes']:
                for path in route.get('paths',[route]):
                    explicit=any(b.predecessors is not None for b in path['blocks'])
                    rows.append(dict(program_id=p['id'],inventory_id=route['id'],
                        path_id=path.get('id'),mode='explicit_block_dag' if explicit else 'legacy_serial_blocks',
                        blocks=[dict(id=b.id,predecessors=(list(b.predecessors) if explicit else None),
                                     repeat_key=b.repeat_key) for b in path['blocks']]))
        return dict(paths=rows,overlap_learned=False,
            interpretation='Supplied scheduling hypotheses. Missing block predecessors retain serial defaults; explicit roots do not establish actual parallelism or shared-resource availability.')

    def source_support_report(self,states=None):
        """Audit supplied source support, not source truth or causal identification.

        A non-residual duration candidate can inform an offset, but its presence
        does not prove that an inventory supports the operator or another source
        measures the same estimand. Exact histogram sources have provenance only.
        No taxonomy, reference source or cross-source matching is guessed here.
        """
        flat=None
        if states is not None:
            states=np.asarray(states,dtype=float)
            if (states.ndim!=3 or states.shape[-1]!=self.layout.size
                    or states.shape[0]*states.shape[1]<2 or not np.isfinite(states).all()):
                raise ValueError('Need finite chains-by-draws-by-model-coordinates with at least two draws')
            flat=states.reshape(-1,self.layout.size)
        families={}
        def entry(name):
            if name not in families:
                families[name]=dict(program_ids=set(),observation_rows=0,
                    observation_rows_with_duration_candidates=0,residual_only_rows=0,
                    mixed_duration_residual_rows=0,count_rows=0,money_rows=0,
                    finite_quantile_cohorts=0,exact_histogram_cohorts=0,
                    exact_histogram_cases=0,duration_candidate_rows_by_channel={ch:0 for ch in CHANNELS},
                    duration_candidate_selected_case_ids=set(),
                    duration_candidate_unselected_case_ids=set(),report_log_scales=set())
                if self.conditional_case_frames:
                    families[name]['duration_candidate_conditional_frame_case_ids']=set()
                if self.source_precision_active:
                    families[name]['source_precision']=dict(fixed_declared_factors=0,
                        config_fallback_factors=0,implicit_fallback_factors=0,
                        unknown_n_floor_factors=0,unknown_n_floor_raised_factors=0,
                        source_types=set(),calibration_references=set())
            return families[name]
        for p in self.programs:
            for o in p['observations']:
                row=entry(o['source_family'])
                row['program_ids'].add(p['id'])
                row['observation_rows']+=1
                bases={op['basis'] for op,w in zip(o['operators'],o['operator_weights']) if w>0}
                duration=bases.difference(COUNT_BASES,MONEY_BASES,{'unmodeled_duration'})
                row['residual_only_rows']+=int(bases=={'unmodeled_duration'})
                row['count_rows']+=int(bool(bases & COUNT_BASES))
                row['money_rows']+=int(bool(bases.intersection(MONEY_BASES)))
                if not duration:
                    continue
                row['observation_rows_with_duration_candidates']+=1
                row['mixed_duration_residual_rows']+=int('unmodeled_duration' in bases)
                channel=next((ch for ch in CHANNELS[1:] if ch in duration),'elapsed')
                row['duration_candidate_rows_by_channel'][channel]+=1
                scale=(o['typical_range_model']['report_log_scale'] if o['statistic']=='typical_range'
                       else elapsed_report_log_scale(o,self.cfg.report_sd,
                            self.cfg.unknown_n_report_sd_floor if o['case_id'] is None else None)
                       if channel=='elapsed' else
                       max(self.cfg.report_sd,self.cfg.unknown_n_report_sd_floor)
                       if o['case_id'] is None else self.cfg.report_sd)
                row['report_log_scales'].add(float(scale))
                if self.source_precision_active and channel=='elapsed' and o['statistic']!='typical_range':
                    detail=self._source_precision_diagnostic(o,unknown_n=o['case_id'] is None)
                    precision=row['source_precision']
                    if detail['basis']==FIXED_KIND:
                        precision['fixed_declared_factors']+=1
                    elif detail['basis']==FALLBACK_KIND:
                        precision['config_fallback_factors']+=1
                    else:
                        precision['implicit_fallback_factors']+=1
                    precision['unknown_n_floor_factors']+=int(o['case_id'] is None)
                    precision['unknown_n_floor_raised_factors']+=int(detail['unknown_n_floor_applied'])
                    if detail['source_type'] is not None:
                        precision['source_types'].add(detail['source_type'])
                    if detail['calibration_id'] is not None:
                        precision['calibration_references'].add((detail['source_type'],
                            detail['calibration_id'],detail['calibration_provenance']))
                if o['case_id'] is not None:
                    field=('duration_candidate_selected_case_ids' if o['sampling']=='delay_selected' else
                           'duration_candidate_conditional_frame_case_ids'
                           if o['sampling']==CONDITIONAL_FRAME_SAMPLING else
                           'duration_candidate_unselected_case_ids')
                    row[field].add((p['id'],o['case_id']))
            for c in p['quantile_cohorts']:
                row=entry(c['source_family'])
                row['program_ids'].add(p['id'])
                row['finite_quantile_cohorts']+=1
                bases={op['basis'] for op,w in zip(c['operators'],c['operator_weights']) if w>0}
                duration=bases-{'unmodeled_duration'}
                if duration:
                    channel=next((ch for ch in CHANNELS[1:] if ch in duration),'elapsed')
                    row['duration_candidate_rows_by_channel'][channel]+=len(c['reports'])
                    scale=(elapsed_report_log_scale(c,self.cfg.report_sd)
                           if channel=='elapsed' else self.cfg.report_sd)
                    row['report_log_scales'].add(float(scale))
                    if self.source_precision_active and channel=='elapsed':
                        detail=self._source_precision_diagnostic(c)
                        precision=row['source_precision']
                        if detail['basis']==FIXED_KIND:
                            precision['fixed_declared_factors']+=1
                        elif detail['basis']==FALLBACK_KIND:
                            precision['config_fallback_factors']+=1
                        else:
                            precision['implicit_fallback_factors']+=1
                        if detail['source_type'] is not None:
                            precision['source_types'].add(detail['source_type'])
                        if detail['calibration_id'] is not None:
                            precision['calibration_references'].add((detail['source_type'],
                                detail['calibration_id'],detail['calibration_provenance']))
            for c in p['histogram_cohorts']:
                row=entry(c['source_family'])
                row['program_ids'].add(p['id'])
                row['exact_histogram_cohorts']+=1
                row['exact_histogram_cases']+=c['sample_size']
        hierarchy_report=None
        if self.source_offset_hierarchy is not None:
            support={name: row['duration_candidate_rows_by_channel']['elapsed']
                     for name,row in families.items()}
            hierarchy_report=self.source_offset_hierarchy.report(flat,support)
        for name,row in families.items():
            row['program_ids']=sorted(row['program_ids'])
            row['report_log_scales']=sorted(row['report_log_scales'])
            if self.source_precision_active:
                precision=row['source_precision']
                precision['source_types']=sorted(precision['source_types'])
                precision['calibration_references']=[dict(source_type=source_type,
                    calibration_id=calibration_id,calibration_provenance=provenance,
                    calibration_verified=False)
                    for source_type,calibration_id,provenance in sorted(
                        precision['calibration_references'])]
            case_fields=['duration_candidate_selected_case_ids','duration_candidate_unselected_case_ids']
            if self.conditional_case_frames:
                case_fields.append('duration_candidate_conditional_frame_case_ids')
            for key in case_fields:
                row[key]=[dict(program_id=p,case_id=c) for p,c in sorted(row[key])]
            hierarchy_member=(self.source_offset_hierarchy is not None and
                              name in self.source_offset_hierarchy.documents)
            allocated=(name in self.sources if self.source_offset_hierarchy is None else
                       hierarchy_member and self.source_offset_hierarchy.document_has_free_offset(name))
            row['duration_offset_coordinates_allocated']=allocated
            row['duration_offset_hierarchy_member']=hierarchy_member
            conditional_source=any(frame['source_family']==name
                                   for frame in self.conditional_case_frames.values())
            row['duration_offset_fixed_zero']=(conditional_source or
                                                hierarchy_member and not allocated)
            if self.source_offset_hierarchy is not None:
                anchors=[a for a in self.source_offset_hierarchy.reference_histogram_cohorts
                         if a['source_family']==name]
                if anchors:
                    row['reference_histogram_support']=dict(
                        reference_type=self.source_offset_hierarchy.reference_type,
                        exact_histogram_factors=len(anchors),
                        recorded_cases=sum(a['sample_size'] for a in anchors),
                        exact_histogram_reporting_offset='not_applicable',
                        noisy_report_offset_flags_apply_to_histogram=False,
                        noisy_report_document_also_present=hierarchy_member,
                        substantive_review_verified=False,
                        matched_comparison_established=False)
            if conditional_source:
                row['duration_offset_effect_enabled']=False
            row['offset_prior_sd_log']=(0. if conditional_source else self.cfg.source_sd if allocated and
                self.source_offset_hierarchy is None else None)
            row['duration_contamination_probability']=(self.cfg.contamination
                if any(row['duration_candidate_rows_by_channel'].values()) else None)
            row['offsets']={}
            for ch in self.active_channels:
                if not allocated and not hierarchy_member:
                    continue
                support=row['duration_candidate_rows_by_channel'][CHANNELS[ch]]
                info=dict(duration_report_candidates=support,
                    no_direct_duration_support=(support==0),
                    posterior_log_offset=None,posterior_multiplier=None,
                    marginal_variance_contraction=None)
                if conditional_source:
                    info['fixed_zero_report_frame_convention']=True
                if flat is not None:
                    if conditional_source:
                        fixed=dict(median=0.,mean=0.,ci90=[0.,0.])
                        info.update(posterior_log_offset=fixed,
                            posterior_multiplier=dict(median=1.,mean=1.,ci90=[1.,1.]))
                    elif self.source_offset_hierarchy is None:
                        z=flat[:,self.source[ch,self.sources.index(name)]]
                        info.update(posterior_log_offset=summary(self.cfg.source_sd*z),
                            posterior_multiplier=summary(np.exp(self.cfg.source_sd*z)),
                            marginal_variance_contraction=float(1.-np.var(z,ddof=1)))
                    else:
                        transformed=hierarchy_report['documents'][name]
                        effective=transformed['effective_log_offset']
                        info.update(posterior_log_offset=effective['posterior'],
                            posterior_multiplier=transformed['effective_multiplier']['posterior'],
                            marginal_variance_contraction=effective['marginal_variance_contraction'])
                row['offsets'][CHANNELS[ch]]=info
        result=dict(source_families=families,
            posterior_draws_summarized=0 if flat is None else len(flat),
            case_count_scope='Distinct cases on duration-candidate observation rows only, not count/money-only cases.',
            candidate_count_scope='Observation-row counter excludes finite-cohort report rows; per-channel candidate counts include quantile reports, not histogram cases.',
            offset_parameterization=('Independent zero-centered Gaussian offsets; no reference type or nested type/document hierarchy.'
                if self.source_offset_hierarchy is None else
                'Reference-anchored type effects plus exactly centered nested document residuals with learned positive shared spreads.'),
            source_offset_hierarchy=hierarchy_report,
            unknown_n_report_sd_floor=self.cfg.unknown_n_report_sd_floor,
            unknown_n_floor_policy='Declared sensitivity parameter for ordinary population summaries; not a calibrated source ranking. Known-n cohorts and subjective typical ranges use their own contracts.',
            reviewed_same_estimand_overlap='Not established by this report; matching source names or clock labels is insufficient.',
            declared_source_comparisons=self.source_comparisons,
            count_source_policy=dict(offset=False,error_scale=self.cfg.count_error_scale,
                contamination=self.cfg.contamination,per_type_reliability=False,
                qualification='Shared report kernel is a modeling restriction, not equal source trustworthiness.'),
            money_source_policy='No source offset; shared rounding/report-error kernel for individual totals. A published schedule is an input, not a noisy timing report.',
            exact_histogram_source_policy='Provenance only: no offset, report noise or contamination; sampling/population and reporting assumptions must be reviewed separately.',
            selection_policy='Declared case ascertainment is separate from reporting offsets; institutions can also be selected in ways this case mechanism does not model.',
            qualification='Candidate counts are not independent observations or a proof of identification. Offset contraction is marginal variance contraction, not total information. Prior-only offsets must not be presented as learned source reliability.')
        if self.conditional_case_frames:
            result['conditional_case_frames']=self.conditional_case_frames
            result['conditional_frame_policy']=('Cases are a census only within the hash-bound artifact frame. '
                'The single source offset is fixed at zero as a report-frame convention; no source bias, selection correction, '
                'county-applicant distribution, agency-only delay, or semantic certification is learned here.')
        if self.source_precision_active:
            result['source_precision_policy']=dict(kind='fixed_optional_source_type_report_scale',
                learned_coordinates=0,calibration_verified=False,
                calibration_qualification=('calibration_id is an unverified declared reference; '
                    'this model does not establish empirical calibration, source ranking or trust.'),
                separation_qualification=('Sampling variation, population spread, source bias, '
                    'contamination and selection remain separate from the elapsed report scale.'))
        return result

    def clock_support_report(self):
        """Exact event-presence checks, without durations, draws or source guesses.

        This deliberately does not infer markers from operation names. Positive
        marker coverage is necessary, not sufficient: temporal ordering and joint
        compatibility with other same-case observations are checked by likelihood.
        """
        paths, alternatives = [], []
        for p in self.programs:
            observations = list(p['observations'])
            for cohort in p['quantile_cohorts']:
                observations.extend(cohort_report_observations(
                    {k: v for k, v in cohort.items() if k != 'grid'}))
            for cohort in p['histogram_cohorts']:
                observations.extend(cohort_histogram_observations(cohort))
            for route in p['routes']:
                route_paths = []
                for path in route.get('paths', [route]):
                    providers = {event: [op.id for op in path['operations'] if marker in op.markers]
                                 for event, (marker, _) in CLOCK_EVENT_MARKERS.items()}
                    absent = [event for event, ids in providers.items() if not ids]
                    decisions = providers['initial_decision']
                    repeated = {aid for block in path['blocks'] if block.repeat_key is not None
                                for aid in block.operations}
                    row = dict(program_id=p['id'], inventory_id=route['id'], path_id=path['id'],
                        marker_providers=providers, absent_events=sorted(absent),
                        available_events=sorted(CLOCK_EVENTS - set(absent)),
                        initial_final_guaranteed_same_event=(len(decisions) == 1 and
                                                           decisions[0] not in repeated))
                    route_paths.append(row)
                    paths.append(row)
                for observation in observations:
                    case = observation['case_id']
                    scope = (p['case_path_scope'].get(case) if case is not None else
                             observation.get('population_path_scope'))
                    eligible = [path for path in route_paths if scope is None or path['path_id'] in scope]
                    for oi, (operator, weight) in enumerate(zip(
                            observation['operators'], observation['operator_weights'])):
                        if operator['basis'] != 'whole_case_clock':
                            continue
                        required = {operator['start'], operator['end']}
                        missing = [dict(path_id=path['path_id'],
                                        missing_events=sorted(required & set(path['absent_events'])))
                                   for path in eligible]
                        supported = [row['path_id'] for row in missing if not row['missing_events']]
                        # Population summaries cannot silently condition on paths
                        # that happen to have an event; individual cases can mix.
                        coverage = bool(eligible) and (len(supported) == len(eligible)
                                                     if case is None else bool(supported))
                        alternatives.append(dict(program_id=p['id'], inventory_id=route['id'],
                            observation_id=observation['id'], case_id=case, operator_index=oi,
                            operator=operator, declared_operator_weight=float(weight),
                            path_scope=scope, eligible_path_count=len(eligible),
                            supported_path_ids=supported, path_checks=missing,
                            event_presence_requirement_satisfied=coverage,
                            event_presence_requirement=('all_declared_population_paths' if case is None
                                                        else 'at_least_one_allowed_case_path')))
        unavailable = [row for row in alternatives if not row['event_presence_requirement_satisfied']]
        return dict(schema_version='clock-boundary-support/1', paths=paths, alternatives=alternatives,
            clock_alternatives_by_inventory=len(alternatives),
            unsupported_clock_alternatives_by_inventory=len(unavailable),
            affected_observations=sorted({row['program_id'] + ':' + row['observation_id'] for row in unavailable}),
            inference_changed=False,
            qualification='Structural event presence only, not source truth, semantic confidence, '
                'temporal-order feasibility or posterior learning. A zero posterior interpretation '
                'weight may be caused by a missing marker, not contrary evidence. No marker, prior, '
                'operator or observation is modified; residual alternatives remain separately declared.')

    def duration_prior_report(self):
        """Describe supplied task baselines, never imply data calibrated them."""
        supplied = dict(self.cfg.elapsed_task_prior_medians)
        return dict(
            elapsed_time_unit=self.cfg.elapsed_time_unit,
            elapsed_clock=f'single_visit_cycle_{self.cfg.elapsed_time_unit}_including_wait_and_service',
            task_baselines_enabled=bool(supplied),
            global_fallback_median_days=self.cfg.elapsed_prior_median,
            tasks={task: dict(median_days=supplied.get(task, self.cfg.elapsed_prior_median),
                             origin='supplied_fixed_task_baseline' if task in supplied else 'global_fallback')
                   for task in self.tasks},
            added_sampled_coordinates=0,
            inferred_from_this_fit=False,
            qualification='Baselines locate operation log-duration priors; shared location, agency, task, '
                'operation and case variation remain. They are not predicted population means, '
                'observed timings, active labor, learned waiting fractions or calibrated priors by default.')

    def report(self,states,routes,likelihood,progress=None):
        flat=states.reshape(-1,states.shape[-1])
        structural=routes.reshape(-1,len(self.programs))
        if progress is not None:
            progress(dict(stage='posterior_coordinate_diagnostics', total_draws=len(flat)))
        diags={'log_likelihood':diagnostics(likelihood)}
        for j in range(states.shape[-1]):
            diags['coordinate:'+str(j)]=diagnostics(states[:,:,j])
        positive_count_report = {}
        for p in self.programs:
            for family in p.get('count_only_repeat_families', []):
                r = betaincinv(2., 3., ndtr(states[:,:,family['coordinate']]))
                conditional_mean = 1. / (1. - r)
                key = p['id']+':'+family['id']
                diags['positive_repeat:'+key+':continuation'] = diagnostics(r)
                diags['positive_repeat:'+key+':conditional_mean'] = diagnostics(conditional_mean)
                positive_count_report[key] = dict(
                    family=deepcopy(family), prior=dict(continuation_beta=[2., 3.]),
                    continuation_probability=summary(r.reshape(-1)),
                    mean_additional_rounds_given_positive=summary(conditional_mean.reshape(-1)),
                    positive_event_probability=None, unconditional_mean_additional_rounds=None,
                    executable_block_attached=False, burden_headline_eligible=False,
                    qualification='Completed-positive reporting frame with declared fixed severity selection; '
                        'no zero-case denominator, no inferred hurdle risk, no executable step identity, '
                        'and no timing, labor, fee or county-capability contribution.')
        joint_inventory_report = None
        if self.joint_inventory_prior is not None:
            prior = self.joint_inventory_prior
            indices = np.array([prior.index(row) for row in structural]).reshape(routes.shape[:2])
            masses = []
            for hi,name in enumerate(prior.names):
                indicator = (indices == hi).astype(float)
                diagnostic = diagnostics(indicator)
                if len(prior.names)>1 and np.ptp(indicator)==0:
                    diagnostic = dict(rhat=None,ess_bulk=0.,ess_tail=0.,
                        reason='No transitions observed for a non-fixed joint inventory; convergence is unverified')
                diags['joint_inventory:'+name] = diagnostic
                masses.append(dict(id=name,prior_probability=float(prior.probabilities[hi]),
                                   posterior_probability=float(indicator.mean())))
            joint_inventory_report = dict(hypotheses=masses,
                feedback_policy=prior.declaration['feedback_policy'],
                evidence_partition_note=prior.declaration['evidence_partition_note'],
                qualification='Finite supplied joint support; no factorization across programs, no discarded mass by this sampler. External inventory/order/participation semantics and any upstream Monte Carlo approximation remain separate validation obligations.')
        # Marginal coordinate mixing does not establish mixing of their sum:
        # weakly identified effects can cancel along highly correlated ridges.
        # Check each actual operation location without materializing a second
        # chains x draws x operations tensor for the whole fit.
        report_sources={}
        for p in self.programs:
            for observation in p['observations']+p['quantile_cohorts']:
                for operator in observation['operators']:
                    if operator['basis'] in COUNT_BASES or operator['basis'] in MONEY_BASES or operator['basis']=='unmodeled_duration':
                        continue
                    channel=CHANNELS.index(operator['basis']) if operator['basis'] in CHANNELS[1:] else 0
                    ids=set(operator.get('activity_ids',[]))
                    for oi in p['global_indices']:
                        if not ids or self.operations[oi]['op'].id in ids:
                            report_sources.setdefault((oi,channel),set()).add(self.sources.index(observation['source_family']))
        hierarchy_source_offsets=(None if self.source_offset_hierarchy is None else
            self.source_offset_hierarchy.offsets_for_sources(states,self.sources))
        if self.source_offset_hierarchy is not None:
            transformed=self.source_offset_hierarchy.transformed(states)
            total_draws=float(states.shape[0]*states.shape[1])
            fixed_diagnostic=dict(rhat=1.,ess_bulk=total_draws,ess_tail=total_draws,
                fixed=True,reason='Deterministic zero under the reference/centering convention')
            diags['source_hierarchy:tau_type']=diagnostics(transformed['type_scale'])
            if transformed['document_scale'] is not None:
                diags['source_hierarchy:tau_document']=diagnostics(
                    transformed['document_scale'])
            for source_type,values in transformed['type_effects'].items():
                key='source_hierarchy:type_effect:'+source_type
                diags[key]=(dict(fixed_diagnostic) if source_type ==
                    self.source_offset_hierarchy.reference_type else diagnostics(values))
            for document,values in transformed['document_residuals'].items():
                key='source_hierarchy:document_residual:'+document
                source_type=self.source_offset_hierarchy.document_type[document]
                fixed=source_type not in self.source_offset_hierarchy.document_coordinates
                diags[key]=dict(fixed_diagnostic) if fixed else diagnostics(values)
            for document,values in transformed['document_offsets'].items():
                key='source_hierarchy:effective_offset:'+document
                source_type=self.source_offset_hierarchy.document_type[document]
                fixed=(source_type == self.source_offset_hierarchy.reference_type and
                       source_type not in self.source_offset_hierarchy.document_coordinates)
                diags[key]=dict(fixed_diagnostic) if fixed else diagnostics(values)
        for oi,operation in enumerate(self.operations):
            for ch in self.active_channels:
                values=(self.cfg.location_sd*states[:,:,self.location[ch]]
                    +self.cfg.agency_sd*states[:,:,self.agency[ch,operation['agency']]]
                    +self.cfg.task_sd*states[:,:,self.task[ch,operation['task']]]
                    +self.cfg.operation_sd*states[:,:,self.operation[ch,oi]])
                if ch == 0 and self.operation_location_design is not None:
                    values += np.einsum('...t,t->...',
                        states[:,:,self.operation_location_design_coordinates],
                        self.operation_location_design['matrix'][oi])
                key='operation:'+operation['program']+':'+operation['op'].id+':'+CHANNELS[ch]+':log_location'
                diags[key]=diagnostics(values)
                for source in sorted(report_sources.get((oi,ch),())):
                    offset=(self.cfg.source_sd*states[:,:,self.source[ch,source]]
                            if hierarchy_source_offsets is None else
                            hierarchy_source_offsets[:,:,source])
                    diags[key+':report_offset:'+self.sources[source]]=diagnostics(
                        values+offset)
        draws={p['id']:{} for p in self.programs}
        interpretation_draws={p['id']:{o['id']:[] for o in p['observations'] if len(o['operators'])>1}
                              for p in self.programs}
        cohort_interpretations={p['id']:{c['id']:[] for c in p['quantile_cohorts']}
                                for p in self.programs}
        histogram_interpretations={p['id']:{c['id']:[] for c in p['histogram_cohorts']}
                                   for p in self.programs}
        case_path_draws={p['id']:{case:{route_id:[] for route_id in priors}
                                for case,priors in p.get('case_path_priors',{}).items()}
                         for p in self.programs}
        agency={name:[] for name in self.agencies if not name.startswith('role:') and not name.endswith(':unknown')}
        phases={name:{'wait':[], 'service_elapsed':[]} for name in agency} if self.cfg.within_visit_phases else {}
        if progress is not None:
            progress(dict(stage='posterior_predictions', completed_draws=0, total_draws=len(flat)))
        for draw_index,(z,ss) in enumerate(zip(flat,structural)):
            par=self.parameters(z)
            represented={name:[] for name in agency}
            represented_phases={name:{'wait':[], 'service_elapsed':[]} for name in phases}
            phase_values=self.phase_means(par) if self.cfg.within_visit_phases else None
            for pi,p in enumerate(self.programs):
                ri=int(ss[pi])
                route=p['routes'][ri]
                trace=self.trace(p,z,par,ri,True)
                for ident,terms in self._quantile_cohort_parts(p,trace,par,return_terms=True).items():
                    probabilities=np.exp(terms-logsumexp(terms))
                    if not np.isfinite(probabilities).all():
                        raise ValueError('Saved draw cannot explain a finite quantile cohort')
                    cohort_interpretations[p['id']][ident].append(probabilities)
                for ident,terms in self._histogram_cohort_parts(p,trace,return_terms=True).items():
                    probabilities=np.exp(terms-logsumexp(terms))
                    if not np.isfinite(probabilities).all():
                        raise ValueError('Saved draw cannot explain an exact histogram cohort')
                    histogram_interpretations[p['id']][ident].append(probabilities)
                if interpretation_draws[p['id']] or p.get('case_path_priors'):
                    if 'paths' in route:
                        _,detail=self._case_path_likelihood(p,z,par,ri,details=True)
                        terms=detail['terms']
                        for case,by_route in case_path_draws[p['id']].items():
                            weights=detail['case_weights'][case]
                            if not np.isfinite(weights).all() or not np.isclose(weights.sum(),1.):
                                raise ValueError('Saved draw cannot explain a fixed-prior case')
                            by_route[route['id']].append(weights)
                    else:
                        individual=self.trace(p,z,par,ri) if p['cases'] else None
                        terms=self._observation_parts(p,individual,trace,par,return_log_terms=True)
                    for oi,(ident,start,end) in enumerate(p['compiled']['groups']):
                        if ident in interpretation_draws[p['id']]:
                            if 'paths' in route:
                                case=p['observations'][oi]['case_id']
                                if case is None:
                                    conditional=np.exp(terms[0,start:end]-logsumexp(terms[0,start:end]))
                                else:
                                    conditional=np.zeros(end-start)
                                    for j,weight in enumerate(detail['case_weights'][case]):
                                        if weight>0:
                                            conditional+=weight*np.exp(terms[j,start:end]
                                                -logsumexp(terms[j,start:end]))
                            else:
                                conditional=np.exp(terms[start:end]-logsumexp(terms[start:end]))
                            if not np.isfinite(conditional).all() or not np.isclose(conditional.sum(),1.):
                                raise ValueError('Saved draw cannot explain an observation under any interpretation')
                            interpretation_draws[p['id']][ident].append(conditional)
                metrics={}
                for event in ('initial_decision','final_decision','modeled_work_end'):
                    try:
                        values=trace.event(event)
                        metrics[event+'_median_days']=population_statistic(trace,values,'median')
                        metrics[event+'_p90_days']=population_statistic(trace,values,'p90')
                    except ValueError:
                        pass
                metrics.update(self.expected_burden(p,z,par,ri))
                if p['inventory_granularity'] == 'aggregate_phases':
                    # A computational phase is not a recovered task inventory.
                    for key in ('mean_visit_count', 'mean_operation_count', 'mean_agency_count',
                                'mean_applicant_visit_count', 'mean_applicant_operation_count',
                                'mean_fee_total', 'fee_total_case_sd'):
                        metrics.pop(key, None)
                if self.dwell_coordinates is not None:
                    # Population mean waiting at each declared gap of this program.
                    # Route-independent by construction: it is the gap's parameter,
                    # not an average over the sampled route's traversals.
                    for site in p['dwell_local']:
                        metrics['mean_dwell_days:'+self.dwell_sites[site][1]]=float(
                            math.exp(par['dwell_log'][site]+.5*self.cfg.dwell_case_sd**2))
                if 'paths' in route:
                    for path,probability in zip(route['paths'],self.path_probabilities(route,z)):
                        metrics['case_path_probability:'+route['id']+':'+path['id']]=float(probability)
                q,r=self.repeat_parameters(p,z)
                for j,key in enumerate(p['repeat_keys']):
                    metrics['repeat_any:'+key]=float(q[j])
                    metrics['repeat_continue:'+key]=float(r[j])
                for key,value in metrics.items():
                    draws[p['id']].setdefault(key,[]).append(value)
                for idx,op in zip(route['indices'],route['operations']):
                    if op.actor_role=='agency' and op.actor_id in represented:
                        mean=math.exp(par['mu'][0,idx]+.5*(par['sigma'][0]**2+self.cfg.common_case_sd**2))
                        represented[op.actor_id].append(mean)
                        if phase_values is not None:
                            represented_phases[op.actor_id]['wait'].append(float(phase_values[0][idx]))
                            represented_phases[op.actor_id]['service_elapsed'].append(float(phase_values[1][idx]))
            for name,values in represented.items():
                agency[name].append(float(np.mean(values)) if values else None)
            for name, channels in represented_phases.items():
                for channel, values in channels.items():
                    phases[name][channel].append(float(np.mean(values)) if values else None)
            if progress is not None and (draw_index == 0 or (draw_index+1)%250 == 0 or draw_index+1 == len(flat)):
                progress(dict(stage='posterior_predictions', completed_draws=draw_index+1, total_draws=len(flat)))
        if progress is not None:
            progress(dict(stage='posterior_summary_diagnostics', total_draws=len(flat)))
        programs={}
        for pi,p in enumerate(self.programs):
            metrics={}
            for key,values in draws[p['id']].items():
                if len(values)==len(flat):
                    metrics[key]=summary(values)
                    diags[p['id']+':'+key]=diagnostics(np.asarray(values).reshape(states.shape[:2]))
                else:
                    # Presence in only some structural hypotheses must stay visible.
                    metrics[key]=dict(conditional_on_defined=summary(values),probability_defined=len(values)/len(flat))
            resource_evidence={channel:sum(any(op['basis']==channel for op in o['operators'])
                for pp in self.programs for o in pp['observations']+pp['quantile_cohorts']) for channel in CHANNELS[1:]}
            programs[p['id']]=dict(metrics=metrics,resource_channel_claims_across_hierarchy=resource_evidence,
                elapsed_time_unit=self.cfg.elapsed_time_unit,
                inventory_granularity=p['inventory_granularity'], clock_estimand=p['clock_estimand'],
                resource_channels_without_direct_evidence=[ch for ch,n in resource_evidence.items() if not n],
                omitted_resource_channels=[ch for ch in CHANNELS[1:] if ch not in self.cfg.modeled_channels],
                route_probabilities={r['id']:float(np.mean(routes[:,:,pi]==ri)) for ri,r in enumerate(p['routes'])})
            if p.get('collapsed_observation_ids'):
                programs[p['id']]['collapsed_single_phase_cases']=dict(
                    observation_ids=list(p['collapsed_observation_ids']),case_ids=list(p['cases']),
                    sampled_case_duration_coordinates=0,
                    coordinates_removed=len(p['cases'])*p['uncollapsed_case_dimension'],
                    integration='deterministic_gauss_hermite_over_normal_case_effect',
                    quadrature_size=self.cfg.collapsed_case_quadrature_size,
                    report_kernel='existing_student_t_df4_mixture',
                    qualification='Same priors and Student-t4 report likelihood; numerical marginalization, not Gaussian convolution.')
            programs[p['id']]['case_path_scope']=p['case_path_scope']
            if p.get('case_path_priors'):
                assignments=self.case_path_prior_report()[p['id']]
                for case,by_route in case_path_draws[p['id']].items():
                    for route_id,values in by_route.items():
                        record=assignments[case][route_id]
                        path_ids=list(record['normalized_prior_weights'])
                        probabilities=np.asarray(values)
                        record.update(draws_given_inventory=len(values),
                            inventory_posterior_probability=len(values)/len(flat),
                            posterior_mean_weights_given_inventory=(
                                dict(zip(path_ids,probabilities.mean(axis=0).tolist())) if len(values) else None))
                        if len(values)==len(flat):
                            for j,path_id in enumerate(path_ids):
                                diags[p['id']+':case_assignment:'+case+':'+route_id+':'+path_id]=diagnostics(
                                    probabilities[:,j].reshape(states.shape[:2]))
                programs[p['id']]['fixed_case_path_assignments']=assignments
            programs[p['id']]['burden_metric_scope']=dict(
                inventory_granularity=p['inventory_granularity'],
                aggregate_phase_warning=('Clock outputs describe only the declared aggregate phases. '
                    'The computational operation count is not an applicant step count; counts and fee totals '
                    'are suppressed. Phase means do not identify intrinsic agency task speed.'
                    if p['inventory_granularity']=='aggregate_phases' else None),
                path='Complete modeled paths, including repeated and post-decision work; not a decision-truncated count.',
                applicant='Operation counts as applicant-facing when actor_role=payer or payer_work=true; unresolved applicability suppresses totals. This proxy need not equal benchmark visibility.',
                fees='USD per traversed visit under declared fee objects; an unstated fee is unknown, not zero. fee_total_case_sd is modeled between-case path/repeat spread, not uncertainty in the mean.',
                unavailable_metrics=[key for key in ('mean_applicant_visit_count','mean_applicant_operation_count','mean_fee_total','fee_total_case_sd') if key not in metrics])
            median_only=(bool(p['observations']) and not p['histogram_cohorts'] and not p['quantile_cohorts']
                and all(o['case_id'] is None and o['statistic'] in ('median','report_only') for o in p['observations']))
            programs[p['id']]['population_tail_support']=dict(
                only_unknown_n_medians=median_only,
                tail_headline_eligible=False,
                spread_sensitive_factors_in_this_program=(phase_spread_sensitive_factors(p)
                    if self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') else None),
                qualification=('A single lognormal phase median does not identify case spread. Its p90 and '
                    'population mean are prior-sensitive extrapolations, not measured tails.'
                    if median_only and self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') else
                    'This flag is not calibration or identifiability; tail estimates still require evidence and prior sensitivity.'))
            selection_enabled=bool(p['selected_cases'] and self.cfg.selection_sd)
            programs[p['id']]['ascertainment']=dict(selected_case_count=len(p['selected_cases']),
                unselected_case_count=len(p['cases'])-len(p['selected_cases']),
                likelihood_adjustment_enabled=selection_enabled,
                log_high_vs_low_weight_ratio=(summary(self.cfg.selection_sd*np.abs(flat[:,p['selection'][0]]))
                                             if selection_enabled else None),
                qualification='Smooth relative inclusion weighting around the model population 75th percentile; not absolute posting probabilities or a generator-identical mechanism.')
            if p['conditional_case_frame'] is not None:
                frame=p['conditional_case_frame']
                programs[p['id']]['conditional_case_frame']=frame
                programs[p['id']]['ascertainment'].update(
                    unselected_case_count=0,
                    conditional_frame_case_count=len(p['cases']),
                    conditional_frame_id=frame['id'],
                    qualification=("No selection correction: the likelihood is explicitly conditional on the "
                        "hash-bound completed-report frame. This is not unselected sampling or a county-applicant population."))
                if 'coarsening_assumption' in frame:
                    if frame['observation_kind_counts'].get('terminal_neutral_lower_bound', 0):
                        qualification=("No selection correction: completed, pending, and terminal-neutral "
                            "elapsed reports condition on the hash-bound frame with explicitly assumed "
                            "ignorable coarsening. Terminal-neutral bounds make no endpoint-status claim. "
                            "Informative posting/coarsening is not modeled. This is not unselected sampling "
                            "or a county-applicant population.")
                    else:
                        qualification=("No selection correction: completed and pending reports condition on the hash-bound "
                            "frame with explicitly assumed ignorable coarsening. Informative posting/censoring "
                            "is not modeled. This is not unselected sampling or a county-applicant population.")
                    programs[p['id']]['ascertainment']['qualification']=qualification
                    programs[p['id']]['ascertainment']['observation_kind_counts']=frame['observation_kind_counts']
                    programs[p['id']]['conditional_duration_headline_eligible']=(
                        not frame['all_observations_lower_bounds'])
            programs[p['id']]['path_qualification']=(
                'Nested paths are marginalized per case across all its reports; known path scopes condition '
                'the likelihood and are not population-frequency counts. Inventory uncertainty stays program-wide.')
            programs[p['id']]['quantile_cohorts']={c['id']:dict(cohort_id=c['cohort_id'],
                sample_size=c['sample_size'],quantile_method=c['quantile_method'],
                report_ids=[r['id'] for r in c['reports']],sampling=c['sampling'],
                operators=c['operators'],prior_weights=c['operator_weights'],
                posterior_mean_weights=np.asarray(cohort_interpretations[p['id']][c['id']]).mean(axis=0).tolist(),
                **({} if not (self.source_precision_active and
                    self._supports_source_precision(c['operators'])) else dict(
                    source_precision=self._source_precision_diagnostic(c))),
                qualification='Joint finite-sample quantiles of one declared population and clock; '
                    'IID sampling, non-overlap with other evidence and conditional reporting independence '
                    'are supplied assumptions, not inferred facts. Cutoff/recording selection is not modeled.')
                for c in p['quantile_cohorts']}
            programs[p['id']]['histogram_cohorts']={c['id']:dict(cohort_id=c['cohort_id'],
                sample_size=c['sample_size'],bin_edges=c['bin_edges'],bin_counts=c['bin_counts'],
                source_family=c['source_family'],population=c['population'],clock=c['clock'],
                time_unit=c['time_unit'],bin_convention=c['bin_convention'],sampling=c['sampling'],
                integration=self.cfg.population_integration,
                population_path_scope=c.get('population_path_scope'),
                population_condition=c.get('population_condition'),
                operators=c['operators'],prior_weights=c['operator_weights'],
                posterior_mean_weights=np.asarray(histogram_interpretations[p['id']][c['id']]).mean(axis=0).tolist(),
                qualification='One exact-count multinomial with no narrative-source offset or report noise. '
                    'IID sampling and non-overlap are declared assumptions. '
                    + ('Single-phase lognormal bin masses are integrated analytically. '
                       if self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature') else
                       'Finite-grid bin mass is discontinuous and requires numerical refinement. ')
                    + 'Suppression, reporting zeros, calendar conversion and completion selection are not modeled.')
                for c in p['histogram_cohorts']}
            interpretations={}
            for o in p['observations']:
                if o['id'] not in interpretation_draws[p['id']]:
                    continue
                probabilities=np.asarray(interpretation_draws[p['id']][o['id']])
                interpretations[o['id']]=dict(operators=o['operators'],prior_weights=o['operator_weights'],
                    posterior_mean_weights=probabilities.mean(axis=0).tolist(),
                    qualification='Conditional on declared candidates and residual reference; not calibrated semantic confidence')
                for j in range(probabilities.shape[1]):
                    diags[p['id']+':interpretation:'+o['id']+':'+str(j)]=diagnostics(
                        probabilities[:,j].reshape(states.shape[:2]))
            programs[p['id']]['interpretations']=interpretations
            for ri,r in enumerate(p['routes']):
                indicator=(routes[:,:,pi]==ri).astype(float)
                diagnostic=diagnostics(indicator)
                if len(p['routes'])>1 and np.ptp(indicator)==0:
                    diagnostic=dict(rhat=None,ess_bulk=0.,ess_tail=0.,
                        reason='No transitions observed for a non-fixed route indicator; convergence is unverified')
                diags[p['id']+':route:'+r['id']]=diagnostic
        agency_reports={name:dict(probability_represented=sum(v is not None for v in values)/len(values),
            elapsed_time_unit=self.cfg.elapsed_time_unit,
            inventory_mean_cycle_days=(summary([v for v in values if v is not None]) if any(v is not None for v in values) else None),
            estimand='Equal-weight represented inventory (possibly aggregate phases), conditional on presence; '
                f'includes wait in {self.cfg.elapsed_time_unit}, not labor productivity')
            for name,values in agency.items()}
        for name,values in agency.items():
            if all(v is not None for v in values):
                diags['agency:'+name+':inventory_mean_cycle_days']=diagnostics(
                    np.asarray(values).reshape(states.shape[:2]))
            else:
                diags['agency:'+name+':inventory_presence']=diagnostics(
                    np.asarray([v is not None for v in values],dtype=float).reshape(states.shape[:2]))
                agency_reports[name]['conditional_cycle_diagnostic_warning']=(
                    'Cycle mean is conditional on presence; no unconditional continuous-chain diagnostic is asserted.')
        for name,channels in phases.items():
            for channel,values in channels.items():
                present=[v for v in values if v is not None]
                key='inventory_mean_'+channel+'_days'
                agency_reports[name][key]=summary(present) if present else None
                # Route-conditional summaries need explicit presence diagnostics;
                # an absent operation/agency is never imputed a zero-duration phase.
                if len(present)==len(values):
                    diags['agency:'+name+':'+key]=diagnostics(np.asarray(present).reshape(states.shape[:2]))
                else:
                    diags['agency:'+name+':phase_presence']=diagnostics(
                        np.array([v is not None for v in values],dtype=float).reshape(states.shape[:2]))
                    chains=np.asarray(values,dtype=object).reshape(states.shape[:2])
                    conditional=[np.array([v for v in row if v is not None],dtype=float) for row in chains]
                    length=min(map(len,conditional))
                    if length>=8:
                        diags['agency:'+name+':conditional:'+key]=diagnostics(
                            np.stack([row[:length] for row in conditional]))
                    else:
                        diags['agency:'+name+':conditional:'+key]=dict(rhat=None,ess_bulk=0.,ess_tail=0.)
            agency_reports[name]['phase_qualification']='Conditional on represented inventory and independent cycle/fraction noise; service elapsed is not person-hours.'
        flagged={k:v for k,v in diags.items() if not v.get('fixed') and (
            v['rhat'] is None or v['rhat']>1.01 or v['ess_bulk']<400 or v['ess_tail']<200)}
        information=self.information_report(states, sampling_converged=not flagged)
        coarse_programs={p['id'] for p in self.programs if p['inventory_granularity']=='aggregate_phases'}
        for name,report in agency_reports.items():
            coarse=any(o['program'] in coarse_programs and o['op'].actor_id==name for o in self.operations)
            report['contains_aggregate_phases']=coarse
            report['intrinsic_agency_effect_headline_eligible']=(not coarse and
                information['blocks']['agency:elapsed']['headline_eligible'])
            report['identification_warning']='Agency/task effects may be confounded; an inventory mean is not an intrinsic agency effect.'
        spread_support={p['id']:phase_spread_sensitive_factors(p) for p in self.programs} if (
            self.cfg.population_integration in ('analytic_single_phase','collapsed_single_phase_quadrature')) else None
        for report in programs.values():
            tail=report['population_tail_support']
            if spread_support is not None:
                tail['spread_sensitive_factors_across_hierarchy']=spread_support
                tail['tail_headline_eligible']=(any(spread_support.values()) and
                    information['blocks']['case_sigma']['headline_eligible'])
                tail['qualification']=('Only a necessary information screen: spread-sensitive evidence and '
                    'case-scale contraction across the hierarchy. A median alone or one all-duration bin '
                    'contains no spread information. Other programs can inform the shared scale; source '
                    'calibration, tail-shape and transport assumptions still need external checks.')
            report['unmeasured_resource_headline_eligible']={
                channel: channel not in report['resource_channels_without_direct_evidence'] for channel in CHANNELS[1:]}
        if progress is not None:
            progress(dict(stage='posterior_report_complete', total_draws=len(flat)))
        return dict(model='joint-visit-hierarchy/6-development',config=asdict(self.cfg),programs=programs,
            **(dict(positive_repeat_counts=positive_count_report) if positive_count_report else {}),
            **(dict(joint_inventory_prior=joint_inventory_report) if joint_inventory_report is not None else {}),
            **(dict(absent_event_censoring=self.absent_event_censoring_metadata())
               if any(p.get('absent_event_censoring') for p in self.programs) else {}),
            **(dict(joint_duration_reports=self.joint_duration_report_metadata())
               if any(p.get('joint_duration_reports') for p in self.programs) else {}),
            elapsed_time_unit=self.cfg.elapsed_time_unit,
            population_integration=self.cfg.population_integration,
            elapsed_unit_qualification='All elapsed metrics ending in _days use the declared elapsed_time_unit; '
                'no business/calendar-day conversion is performed. Labor remains in person-hours.',
            scheduling=self.scheduling_report(),
            clock_boundary_support=self.clock_support_report(),
            duration_priors=self.duration_prior_report(),
            source_support=self.source_support_report(states),
            identification=information,
            agencies=agency_reports,hierarchy_design=self.hierarchy_design_audit(),
            phase_channel=dict(enabled=self.cfg.within_visit_phases,
                direct_claims=sum(any(op['basis'] in PHASE_BASES for op in o['operators'])
                                 for p in self.programs for o in p['observations']),
                conditional_cycle_fraction_independence=True,case_fraction_spread_learned=False),
            diagnostics=diags,diagnostics_flagged=flagged,posterior_converged=not flagged,
            external_validation=dict(synthetic_truth_evaluation='not_performed_by_fitter',
                synthetic_posterior_quotable_as_validated=False,
                reason='Convergence and numerical precision do not establish recovery; synthetic claims require a separate hash-bound evaluation.'),
            scope='Joint conditional route/visit model, not yet an end-to-end text-pipeline result',
            limitations=['Route hypotheses and normalized interpretation priors are supplied, not extracted by this module.',
                'Explicitly omitted resource channels are marginalized out of this fit, not estimated as zero; their burden outputs are absent.',
                'Independent timing and work hierarchies share visit counts, but no time-to-labor conversion is assumed.',
                'Case-path frequencies use explicitly declared base weights and a configured logistic-normal prior; source labels are not independent prevalence counts.',
                'No competing-risk abandonment, nested loops, partial-recording process or unknown unseen-operation inventory.',
                'Within-case cycles of one operation have perfectly correlated durations.',
                'Explicit block dependency graphs schedule entire repeat blocks without interleaving; they do not model shared-staff resource constraints or learn overlap from silence.',
                'Enabled waiting/service phases assume independent cycle/fraction noise and fixed case-fraction spread; not labor or causal queue effects.',
                'Unmodeled-duration alternatives are explicit process-independent report references, not identified missing operations.',
                'Population quadrature and selection normalization require a separate precision check.']
                +(['Conditional-frame hashing binds the supplied registry and cases but does not certify source semantics, '
                   'representativeness, unbiased reporting, or a universal process order. The zero source offset is a report-frame convention.']
                  if self.conditional_case_frames else [])
                +(['Declared inter-operation dwells are elapsed waiting only, with their own two-level prior and '
                   'no agency/task level; they are identified only through clocks and spans that cross the gap, '
                   'since no observation operator reports a dwell directly.']
                  if self.cfg.inter_operation_dwell else []))
