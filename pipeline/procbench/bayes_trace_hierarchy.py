"""Joint visit-clock, rework and agency/task hierarchy (experimental v6).

Unlike combining separately fitted posteriors, every claim enters one likelihood
and one prior. Totals, activity cycles, counts and independently supplied work hours
observe the SAME case visits. Finite route hypotheses are shared across a program;
uncertainty over a structural interpretation is not a per-case branch frequency.

Current limits: no abandonment/competing risks or nested/interleaved repeat blocks;
repeat-cycle durations are perfectly correlated within a case; no text compiler yet.
Source and operator hypotheses must be provided explicitly, never read from truth.
"""
from dataclasses import asdict, dataclass
import math
import json

import numpy as np
from scipy.linalg import cho_solve, solve_triangular
from scipy.special import betaincinv, expit, logsumexp, ndtr, ndtri, roots_hermitenorm, xlogy, xlog1py
from scipy.stats import qmc

from .bayes_hierarchy import Layout, log_interval
from .compact_visit_trace import (Block, CompactTrace, Operation,
                                  UnavailableTraceQuantity, validate_operator)
from .latent_gaussian import diagnostics, elliptical_slice, information_report, summary


CHANNELS = ('elapsed','payer_hours','agency_hours')
COUNT_BASES = {'additional_rounds','visit_count','operation_count','agency_count'}
PHASE_BASES = {'wait_elapsed', 'service_elapsed'}


@dataclass(frozen=True)
class Config:
    seed: int = 2026092001
    chains: int = 4
    warmup: int = 1000
    draws: int = 2000
    population_size: int = 128
    population_seed: int = 301
    elapsed_prior_median: float = 7.
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

    def __post_init__(self):
        positive = (self.elapsed_prior_median,self.work_prior_median,self.location_sd,
            self.case_log_sd_median,self.report_sd,self.count_error_scale,self.selection_width,
            self.phase_location_sd)
        nonnegative = (self.agency_sd,self.task_sd,self.operation_sd,self.case_log_sd_prior,
                       self.common_case_sd,self.source_sd,self.selection_sd,self.phase_agency_sd,
                       self.phase_task_sd,self.phase_operation_sd,self.phase_case_sd)
        if any(not math.isfinite(x) or x<=0 for x in positive) or any(
                not math.isfinite(x) or x<0 for x in nonnegative):
            raise ValueError('Invalid hierarchy scales')
        if (self.chains<1 or self.warmup<0 or self.draws<8 or self.population_size<16
                or not 0<=self.contamination<1 or not isinstance(self.within_visit_phases,bool)):
            raise ValueError('Invalid sampling/contamination settings')


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


def unmodeled_duration_log_probability(lower,upper,operator):
    """Normalized absolute log-duration reference, independent of the process.

    A finite interpretation set may not contain the report's actual meaning.
    This is not the relative reporting-noise contamination around a latent clock.
    """
    return duration_log_probability(lower,upper,operator['median_days'],
                                    scale=operator['log_scale'],contamination=0.)


class VisitHierarchy:
    def __init__(self,data,cfg=Config()):
        self.data,self.cfg,self.layout=data,cfg,Layout()
        self.programs=[]
        self.operations=[]
        self.agencies=[]
        self.tasks=[]
        self.sources=[]
        identities={}
        pids=[p['id'] for p in data['programs']]
        if not pids or len(set(pids))!=len(pids):
            raise ValueError('Need distinct program IDs')
        for raw in data['programs']:
            p=dict(id=raw['id'],routes=[],observations=raw.get('observations',[]),
                   rates=raw.get('rate_observations',[]),cache={})
            p['repeat_keys']=sorted({b['repeat_key'] for r in raw['routes'] for b in r['blocks'] if b.get('repeat_key')})
            route_ids=set()
            for r in raw['routes']:
                if r['id'] in route_ids or not math.isfinite(r['prior_weight']) or r['prior_weight']<=0:
                    raise ValueError('Routes need unique identities and positive explicit prior weights')
                route_ids.add(r['id'])
                ops=tuple(Operation(**o) for o in r['operations'])
                blocks=tuple(Block(**b) for b in r['blocks'])
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
                repeat={b.repeat_key:np.array([0]) for b in blocks if b.repeat_key is not None}
                CompactTrace(ops,blocks,np.ones((1,len(ops))),repeat)  # validate structural contract now
                p['routes'].append(dict(id=r['id'],operations=ops,blocks=blocks,
                                        indices=np.array(gi),prior_weight=r['prior_weight']))
            if not p['routes']:
                raise ValueError('A program needs at least one explicit route hypothesis')
            self._validate_observations(p)
            p['cases']=sorted({o['case_id'] for o in p['observations'] if o['case_id'] is not None})
            p['case_index']={c:i for i,c in enumerate(p['cases'])}
            p['global_indices']=sorted({int(i) for r in p['routes'] for i in r['indices']})
            p['local_indices']={i:j for j,i in enumerate(p['global_indices'])}
            p['selected_cases']=set()
            for case in p['cases']:
                sampling={o['sampling'] for o in p['observations'] if o['case_id']==case}
                if len(sampling)!=1:
                    raise ValueError('Same-case claims must share one ascertainment mechanism')
                if 'delay_selected' in sampling:
                    p['selected_cases'].add(case)
            self.programs.append(p)
        L=self.layout
        self.location=L.add('location',3)
        self.agency=L.add('agency',3*len(self.agencies)).reshape(3,-1)
        self.task=L.add('task',3*len(self.tasks)).reshape(3,-1)
        self.operation=L.add('operation',3*len(self.operations)).reshape(3,-1)
        self.sigma=L.add('case_sigma',3)
        self.source=L.add('source',3*len(self.sources)).reshape(3,-1)
        self.blocks=[np.array([i]) for i in self.location]
        for array in (self.agency,self.task,self.operation,self.source):
            self.blocks.extend(row for row in array if len(row))
        self.blocks.extend(np.array([i]) for i in self.sigma)
        self.phase_coordinates = None
        if cfg.within_visit_phases:
            groups = [L.add('phase_location',1), L.add('phase_agency',len(self.agencies)),
                      L.add('phase_task',len(self.tasks)), L.add('phase_operation',len(self.operations))]
            self.phase_coordinates = np.concatenate(groups)
            self.blocks.extend(group for group in groups if len(group))
            self.phase_nodes, self.phase_weights = roots_hermitenorm(32)
            self.phase_weights /= math.sqrt(2*math.pi)
        for pi,p in enumerate(self.programs):
            n=len(p['global_indices'])
            p['repeat']=L.add(p['id']+':repeat',2*len(p['repeat_keys'])).reshape(2,-1)
            p['selection']=L.add(p['id']+':selection',int(cfg.selection_sd>0))
            p['phase_offset']=3*(n+1)+len(p['repeat_keys'])
            p['case_dimension']=p['phase_offset']+(n if cfg.within_visit_phases else 0)
            p['case_coordinates']=L.add(p['id']+':cases',len(p['cases'])*p['case_dimension']).reshape(len(p['cases']),p['case_dimension'])
            self.blocks.extend(row for row in p['repeat'] if len(row))
            if len(p['selection']):
                self.blocks.append(p['selection'])
            self.blocks.extend(row for row in p['case_coordinates'])
            power=int(math.ceil(math.log2(cfg.population_size)))
            uniforms=qmc.Sobol(p['case_dimension'],scramble=True,seed=cfg.population_seed+104729*pi).random_base2(power)
            p['population_normals']=ndtri(np.clip(uniforms,np.nextafter(0.,1.),np.nextafter(1.,0.)))
        self.agency_indices=np.array([o['agency'] for o in self.operations])
        self.task_indices=np.array([o['task'] for o in self.operations])
        self.hierarchy_coordinates=[np.r_[self.location[ch],self.agency[ch],self.task[ch],self.operation[ch]]
                                    for ch in range(3)]
        self.design=np.column_stack((np.full(len(self.operations),cfg.location_sd),
            cfg.agency_sd*np.eye(len(self.agencies))[self.agency_indices],
            cfg.task_sd*np.eye(len(self.tasks))[self.task_indices],
            cfg.operation_sd*np.eye(len(self.operations))))
        if cfg.within_visit_phases:
            self.phase_design=np.column_stack((np.full(len(self.operations),cfg.phase_location_sd),
                cfg.phase_agency_sd*np.eye(len(self.agencies))[self.agency_indices],
                cfg.phase_task_sd*np.eye(len(self.tasks))[self.task_indices],
                cfg.phase_operation_sd*np.eye(len(self.operations))))
        for p in self.programs:
            entries,groups=[],[]
            for o in p['observations']:
                start=len(entries)
                for operator,weight in zip(o['operators'],o['operator_weights']):
                    channel=operator['basis'] if operator['basis'] in CHANNELS else 'elapsed'
                    entries.append(dict(observation=o,operator=operator,
                        signature=json.dumps(operator,sort_keys=True),weight=weight,
                        source=self.sources.index(o['source_family']),channel=CHANNELS.index(channel)))
                groups.append((o['id'],start,len(entries)))
            p['compiled']=dict(entries=entries,groups=groups,
                lower=np.array([x['observation']['lower'] for x in entries]),
                upper=np.array([math.inf if x['observation']['upper'] is None else x['observation']['upper'] for x in entries]),
                counts=np.array([x['operator']['basis'] in COUNT_BASES for x in entries],dtype=bool),
                residuals=np.array([x['operator']['basis']=='unmodeled_duration' for x in entries],dtype=bool),
                residual_ll=np.array([float(unmodeled_duration_log_probability(
                    x['observation']['lower'],x['observation']['upper'],x['operator']))
                    if x['operator']['basis']=='unmodeled_duration' else 0. for x in entries]),
                channels=np.array([x['channel'] for x in entries],dtype=int),
                sources=np.array([x['source'] for x in entries],dtype=int),
                logweights=np.log([x['weight'] for x in entries]))

    def _validate_observations(self,p):
        seen=set()
        for o in p['observations']:
            if not o['id'] or o['id'] in seen or not o['source_family']:
                raise ValueError('Observations need distinct IDs and a source family')
            seen.add(o['id'])
            if o['source_family'] not in self.sources:
                self.sources.append(o['source_family'])
            if o['sampling'] not in {'unselected','delay_selected'}:
                raise ValueError('Ascertainment must be explicit')
            report_only=o['statistic']=='report_only'
            if report_only and (o['case_id'] is not None or
                    any(op['basis']!='unmodeled_duration' for op in o['operators'])):
                raise ValueError('A report-only likelihood must be independent of every case and process operator')
            if (o['case_id'] is None and o['statistic'] not in {'median','mean','p90','report_only'}) or (
                    o['case_id'] is not None and o['statistic']!='individual'):
                raise ValueError('Individual and population statistics must not be interchanged')
            if o['case_id'] is None and o['sampling']!='unselected':
                raise ValueError('Selected population summaries require a separate sampling contract')
            if o['case_id'] is None and o.get('sample_size') is not None:
                raise ValueError('Finite-cohort population uncertainty is not implemented in this candidate')
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
            if any(counts) and not all(counts):
                raise ValueError('Cannot mix count probabilities and duration densities')
            if all(counts) and o['case_id'] is None:
                raise ValueError('Population count summaries are not individual count reports')
            channels={op['basis'] if op['basis'] in CHANNELS[1:] else 'elapsed' for op in operators}
            if len(channels)!=1:
                raise ValueError('Alternative interpretations cannot change measurement units')
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

    def parameters(self,z):
        c=self.cfg
        prior=np.log([c.elapsed_prior_median,c.work_prior_median,c.work_prior_median])
        location=prior+c.location_sd*z[self.location]
        agency=c.agency_sd*z[self.agency]
        task=c.task_sd*z[self.task]
        mu=location[:,None]+agency[:,self.agency_indices]+task[:,self.task_indices]+c.operation_sd*z[self.operation]
        sigma=np.exp(math.log(c.case_log_sd_median)+c.case_log_sd_prior*z[self.sigma])
        result=dict(mu=mu,sigma=sigma,location=location,agency=agency,task=task,
                    source=c.source_sd*z[self.source])
        if c.within_visit_phases:
            result['phase_logit']=self.phase_design@z[self.phase_coordinates]
        return result

    def repeat_parameters(self,p,z):
        u=np.clip(ndtr(z[p['repeat']]),np.nextafter(0.,1.),np.nextafter(1.,0.))
        return u[0],betaincinv(2.,3.,u[1])

    def trace(self,p,z,parameters,route_index,population=False):
        route=p['routes'][route_index]
        indices=route['indices']
        local=[p['local_indices'][int(i)] for i in indices]
        n=len(p['global_indices'])
        normals=p['population_normals'] if population else z[p['case_coordinates']]
        q,r=self.repeat_parameters(p,z)
        key=(route_index,parameters['mu'][:,indices].tobytes(),parameters['sigma'].tobytes(),
             q.tobytes(),r.tobytes(),normals.tobytes() if not population else None)
        if self.cfg.within_visit_phases:
            key+=(parameters['phase_logit'][indices].tobytes(),)
        cached=p['cache'].get(population)
        if cached is not None and cached[0]==key:
            return cached[1]
        noise=normals[:,:3*(n+1)].reshape(len(normals),3,n+1)
        logvalues=(parameters['mu'][:,indices][None,:,:]+parameters['sigma'][None,:,None]*noise[:,:,:n][:,:,local]
                   +self.cfg.common_case_sd*noise[:,:,n,None])
        if not np.isfinite(logvalues).all() or np.any(np.abs(logvalues)>650):
            raise FloatingPointError('Numerically extreme duration proposal')
        values=np.exp(logvalues)
        resources={}
        for ch,field in ((1,'payer_work'),(2,'agency_work')):
            amounts=values[:,ch,:].copy()
            for j,op in enumerate(route['operations']):
                applicable=getattr(op,field)
                if applicable is not True:
                    amounts[:,j]=0. if applicable is False else np.nan
            resources[CHANNELS[ch]]=amounts
        uniforms=np.minimum(ndtr(normals[:,3*(n+1):p['phase_offset']]),np.nextafter(1.,0.))
        repeat={}
        for b in route['blocks']:
            if b.repeat_key is not None:
                j=p['repeat_keys'].index(b.repeat_key)
                repeat[b.repeat_key]=repeat_quantiles(uniforms[:,j],q[j],r[j])
        fractions=None
        if self.cfg.within_visit_phases:
            logits=(parameters['phase_logit'][indices][None,:]
                    +self.cfg.phase_case_sd*normals[:,p['phase_offset']:][:,local])
            fractions=expit(logits)
        result=CompactTrace(route['operations'],route['blocks'],values[:,0,:],repeat,resources,
                            service_fractions=fractions)
        p['cache'][population]=(key,result)
        return result

    def _observation_parts(self,p,trace,population,par,return_log_terms=False):
        """Batch reporting kernels; retain the scalar reference for target checks."""
        compiled=p['compiled']
        entries=compiled['entries']
        values=np.zeros(len(entries))
        scales=np.full(len(entries),self.cfg.report_sd)
        supported=np.ones(len(entries),dtype=bool)
        cache={}
        for j,row in enumerate(entries):
            o,operator=row['observation'],row['operator']
            if compiled['residuals'][j]:
                continue
            is_population=o['case_id'] is None
            key=(is_population,row['signature'])
            try:
                if key not in cache:
                    cache[key]=(population if is_population else trace).values(operator)
                predicted=cache[key]
                if is_population:
                    stat_key=key+(o['statistic'],)
                    if stat_key not in cache:
                        cache[stat_key]=float(np.mean(predicted) if o['statistic']=='mean' else
                            np.quantile(predicted,.9 if o['statistic']=='p90' else .5))
                    values[j]=cache[stat_key]
                    scales[j]=max(scales[j],.5)
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
        if duration.any():
            bias=par['source'][compiled['channels'][duration],compiled['sources'][duration]]
            likelihood[duration]=duration_log_probability(compiled['lower'][duration],compiled['upper'][duration],
                values[duration],bias,scales[duration],self.cfg.contamination)
        likelihood[compiled['residuals']]=compiled['residual_ll'][compiled['residuals']]
        likelihood[~supported]=-math.inf
        likelihood+=compiled['logweights']
        if return_log_terms:
            return likelihood
        return {p['id']+':'+ident:float(likelihood[start] if end==start+1 else logsumexp(likelihood[start:end]))
                for ident,start,end in compiled['groups']}

    def log_likelihood_reference(self,z,structures,parts=False):
        return self.log_likelihood(z,structures,parts,vectorized=False)

    def log_likelihood(self,z,structures,parts=False,vectorized=True):
        par=self.parameters(z)
        output={}
        try:
            for p,ri in zip(self.programs,structures):
                trace=self.trace(p,z,par,ri) if p['cases'] else None
                need_pop=any(o['case_id'] is None and o['statistic']!='report_only' for o in p['observations']) or (p['selected_cases'] and self.cfg.selection_sd)
                population=self.trace(p,z,par,ri,True) if need_pop else None
                if vectorized:
                    output.update(self._observation_parts(p,trace,population,par))
                for o in ([] if vectorized else p['observations']):
                    terms=[]
                    channel=o['operators'][0]['basis']
                    ch=CHANNELS.index(channel) if channel in CHANNELS else 0
                    offset=par['source'][ch,self.sources.index(o['source_family'])]
                    for operator,weight in zip(o['operators'],o['operator_weights']):
                        if operator['basis']=='unmodeled_duration':
                            terms.append(math.log(weight)+float(unmodeled_duration_log_probability(
                                o['lower'],o['upper'],operator)))
                            continue
                        try:
                            values=(population if o['case_id'] is None else trace).values(operator)
                            scale=self.cfg.report_sd
                            if o['case_id'] is None:
                                value=float(np.mean(values) if o['statistic']=='mean' else
                                            np.quantile(values,.9 if o['statistic']=='p90' else .5))
                                # Unknown cohort n remains unknown; no invented effective n.
                                scale=max(scale,.5)
                            else:
                                value=values[p['case_index'][o['case_id']]]
                            if operator['basis'] in COUNT_BASES:
                                ll=count_log_probability(o['lower'],o['upper'],value,self.cfg.count_error_scale,self.cfg.contamination)
                            else:
                                ll=duration_log_probability(o['lower'],o['upper'],value,offset,scale,self.cfg.contamination)
                            terms.append(math.log(weight)+float(ll))
                        except (KeyError, UnavailableTraceQuantity):
                            # An absent operation makes this interpretation impossible,
                            # not a zero-duration observation.
                            terms.append(-math.inf)
                    output[p['id']+':'+o['id']]=float(logsumexp(terms))
                if p['selected_cases'] and self.cfg.selection_sd:
                    pop=population.event('initial_decision')
                    threshold=float(np.quantile(np.log(pop),.75))
                    strength=self.cfg.selection_sd*abs(float(z[p['selection'][0]]))
                    def logweight(durations):
                        from scipy.special import expit
                        h=expit((np.log(durations)-threshold)/self.cfg.selection_width)
                        return np.logaddexp(np.log1p(-h),strength+np.log(h))
                    normalizer=logsumexp(logweight(pop))-math.log(len(pop))
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
            precision=np.eye(len(coordinates))
            rhs=np.zeros(len(coordinates))
            retained=[]
            variance=sigma[ch]**2
            for p in self.programs:
                if not p['cases']:
                    continue
                n=len(p['global_indices'])
                design=self.design[p['global_indices']]
                case_coordinates=p['case_coordinates'][:,ch*(n+1):(ch+1)*(n+1)]
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
                if not p['cases']:
                    continue
                design=self.phase_design[p['global_indices']]
                case_coordinates=p['case_coordinates'][:,p['phase_offset']:]
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

    def source_location_update(self,z,structures,current,rng):
        """Prior-conditional scale/offset move; MH covers numerical edge cases."""
        if not self.cfg.source_sd or not len(self.sources):
            return z,current
        trial=z.copy()
        direction=np.r_[1/self.cfg.location_sd,np.full(len(self.sources),-1/self.cfg.source_sd)]
        direction/=np.linalg.norm(direction)
        for ch in range(3):
            coordinates=np.r_[self.location[ch],self.source[ch]]
            trial[coordinates]+=direction*(rng.normal()-direction@trial[coordinates])
        value=self.log_likelihood(trial,structures)
        if math.log(max(rng.random(),np.finfo(float).tiny))<value-current:
            return trial,value
        return z,current

    def expected_burden(self,p,z,parameters,route_index):
        """Exact population means for counts/resources, not averages of QMC cases."""
        route=p['routes'][route_index]
        operations=route['operations']
        q,r=self.repeat_parameters(p,z)
        multiplicity={op.id:1. for op in operations}
        for block in route['blocks']:
            if block.repeat_key is not None:
                j=p['repeat_keys'].index(block.repeat_key)
                for aid in block.operations:
                    multiplicity[aid]=1+q[j]/(1-r[j])
        result=dict(mean_visit_count=float(sum(multiplicity.values())),mean_operation_count=float(len(operations)))
        if not any(op.actor_role=='unknown' or (op.actor_role=='agency' and op.actor_id is None) for op in operations):
            result['mean_agency_count']=float(len({op.actor_id for op in operations if op.actor_role=='agency'}))
        for ch,field in ((1,'payer_work'),(2,'agency_work')):
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

    def sample(self,progress=None,initial=None):
        c=self.cfg
        states=np.empty((c.chains,c.draws,self.layout.size))
        routes=np.empty((c.chains,c.draws,len(self.programs)),dtype=int)
        likelihood=np.empty((c.chains,c.draws))
        calls=[]
        if initial is not None:
            zi,si=map(np.asarray,initial)
            if (zi.shape!=(c.chains,self.layout.size) or si.shape!=(c.chains,len(self.programs))
                    or not np.isfinite(zi).all() or not np.issubdtype(si.dtype,np.integer)
                    or any(np.any((si[:,i]<0)|(si[:,i]>=len(p['routes']))) for i,p in enumerate(self.programs))):
                raise ValueError('Checkpoint must have finite matching states and valid integer route indices')
        for chain in range(c.chains):
            rng=np.random.default_rng(c.seed+104729*chain)
            z=rng.normal(size=self.layout.size) if initial is None else zi[chain].copy()
            structural=(np.array([rng.integers(len(p['routes'])) for p in self.programs])
                        if initial is None else si[chain].copy())
            value=self.log_likelihood(z,structural)
            evaluations=0
            if not math.isfinite(value):
                raise ValueError('Initial latent route cannot explain the supplied observation contract')
            for iteration in range(c.warmup+c.draws):
                for block in self.blocks:
                    z,value,used=elliptical_slice(z,block,lambda zz:self.log_likelihood(zz,structural),value,rng)
                    evaluations+=used
                z,value=self.centered_duration_update(z,structural,value,rng)
                z,value=self.source_location_update(z,structural,value,rng)
                evaluations+=2
                for pi,p in enumerate(self.programs):
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
        for name, coordinates in (('location', self.location[:, None]), ('agency', self.agency),
                ('task', self.task), ('operation', self.operation), ('source', self.source)):
            for channel, row in zip(CHANNELS, coordinates):
                blocks[name+':'+channel] = row
        return information_report(states, blocks, sampling_converged=sampling_converged)

    def report(self,states,routes,likelihood):
        flat=states.reshape(-1,states.shape[-1])
        structural=routes.reshape(-1,len(self.programs))
        diags={'log_likelihood':diagnostics(likelihood)}
        for j in range(states.shape[-1]):
            diags['coordinate:'+str(j)]=diagnostics(states[:,:,j])
        draws={p['id']:{} for p in self.programs}
        interpretation_draws={p['id']:{o['id']:[] for o in p['observations'] if len(o['operators'])>1}
                              for p in self.programs}
        agency={name:[] for name in self.agencies if not name.startswith('role:') and not name.endswith(':unknown')}
        phases={name:{'wait':[], 'service_elapsed':[]} for name in agency} if self.cfg.within_visit_phases else {}
        for z,ss in zip(flat,structural):
            par=self.parameters(z)
            represented={name:[] for name in agency}
            represented_phases={name:{'wait':[], 'service_elapsed':[]} for name in phases}
            phase_values=self.phase_means(par) if self.cfg.within_visit_phases else None
            for pi,p in enumerate(self.programs):
                ri=int(ss[pi])
                route=p['routes'][ri]
                trace=self.trace(p,z,par,ri,True)
                if interpretation_draws[p['id']]:
                    individual=self.trace(p,z,par,ri) if p['cases'] else None
                    terms=self._observation_parts(p,individual,trace,par,return_log_terms=True)
                    for ident,start,end in p['compiled']['groups']:
                        if ident in interpretation_draws[p['id']]:
                            conditional=terms[start:end]-logsumexp(terms[start:end])
                            if not np.isfinite(np.exp(conditional)).all():
                                raise ValueError('Saved draw cannot explain an observation under any interpretation')
                            interpretation_draws[p['id']][ident].append(np.exp(conditional))
                metrics={}
                for event in ('initial_decision','final_decision','modeled_work_end'):
                    try:
                        values=trace.event(event)
                        metrics[event+'_median_days']=float(np.median(values))
                        metrics[event+'_p90_days']=float(np.quantile(values,.9))
                    except ValueError:
                        pass
                metrics.update(self.expected_burden(p,z,par,ri))
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
                for pp in self.programs for o in pp['observations']) for channel in CHANNELS[1:]}
            programs[p['id']]=dict(metrics=metrics,resource_channel_claims_across_hierarchy=resource_evidence,
                resource_channels_without_direct_evidence=[ch for ch,n in resource_evidence.items() if not n],
                route_probabilities={r['id']:float(np.mean(routes[:,:,pi]==ri)) for ri,r in enumerate(p['routes'])})
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
            inventory_mean_cycle_days=(summary([v for v in values if v is not None]) if any(v is not None for v in values) else None),
            estimand='Equal-weight represented operation inventory, conditional on presence; includes calendar wait, not labor productivity')
            for name,values in agency.items()}
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
        flagged={k:v for k,v in diags.items() if v['rhat'] is None or v['rhat']>1.01 or v['ess_bulk']<400 or v['ess_tail']<200}
        information=self.information_report(states, sampling_converged=not flagged)
        for report in agency_reports.values():
            report['intrinsic_agency_effect_headline_eligible']=information['blocks']['agency:elapsed']['headline_eligible']
            report['identification_warning']='Agency/task effects may be confounded; an inventory mean is not an intrinsic agency effect.'
        for report in programs.values():
            report['unmeasured_resource_headline_eligible']={
                channel: channel not in report['resource_channels_without_direct_evidence'] for channel in CHANNELS[1:]}
        return dict(model='joint-visit-hierarchy/6-development',config=asdict(self.cfg),programs=programs,
            identification=information,
            agencies=agency_reports,hierarchy_design=self.hierarchy_design_audit(),
            phase_channel=dict(enabled=self.cfg.within_visit_phases,
                direct_claims=sum(any(op['basis'] in PHASE_BASES for op in o['operators'])
                                 for p in self.programs for o in p['observations']),
                conditional_cycle_fraction_independence=True,case_fraction_spread_learned=False),
            diagnostics=diags,diagnostics_flagged=flagged,posterior_converged=not flagged,
            scope='Joint conditional route/visit model, not yet an end-to-end text-pipeline result',
            limitations=['Route hypotheses and normalized interpretation priors are supplied, not extracted by this module.',
                'Independent timing and work hierarchies share visit counts, but no time-to-labor conversion is assumed.',
                'No competing-risk abandonment, nested loops, partial-recording process or unknown unseen-operation inventory.',
                'Within-case cycles of one operation have perfectly correlated durations.',
                'Enabled waiting/service phases assume independent cycle/fraction noise and fixed case-fraction spread; not labor or causal queue effects.',
                'Unmodeled-duration alternatives are explicit process-independent report references, not identified missing operations.',
                'Population quadrature and selection normalization require a separate precision check.'])
