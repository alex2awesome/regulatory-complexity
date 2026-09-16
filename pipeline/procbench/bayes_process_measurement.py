"""Bayesian whole-process measurement channel, independent of stage-span sums.

Only public ledgers and their source-only semantic audits enter this module.
This intentionally smaller channel does not estimate activity counts or labor.
Case durations are integrated out jointly within each known case. A normalized,
uncertain delay-selection model can account for overrepresented long forum cases.
All sampled coordinates have independent standard-normal priors.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import math

import numpy as np
from scipy.special import betaincinv, expit, logsumexp, ndtr, ndtri, roots_hermitenorm

from .audit_measurement_semantics import SCHEMA, eligible
from .bayes_hierarchy import Layout, log_interval, timing_interval
from .evidence_contract import validate
from .latent_gaussian import diagnostics, elliptical_slice, summary
from .measurement_kernel import observation_native


@dataclass(frozen=True)
class Config:
    chains: int = 4
    warmup: int = 1000
    draws: int = 2000
    thin: int = 1
    seed: int = 20260917
    quadrature: int = 128
    prior_median: float = 30.
    prior_log_sd: float = 2.
    source_sd: float = .35
    selection_sd: float = 0.
    selection_width: float = .35
    report_sd: float = .20
    contamination: float = .08
    prep_fraction: float = .10
    clock_logit_sd: float = 1.2
    include_ambiguous: bool = False
    accelerate: bool = True
    ridge_move: bool = True


def log_selection_weight(z, strength, width=.35):
    """Log p(z|posted)/phi(z); normalizer is exactly .75+.25*exp(strength).

    A soft upper-quartile flag has probability .25 under z~N(0,1).
    Its relative posting rate is exp(strength). This is an ascertainment model,
    not a calibrated claim that all forum bias is caused by elapsed duration.
    """
    z = np.asarray(z)
    if width <= 0 or strength < 0 or not np.isfinite(strength):
        raise ValueError('Selection needs positive width and finite nonnegative strength')
    threshold = ndtri(.75) * math.sqrt(1 + width * width)
    flag = ndtr((z - threshold) / width)
    with np.errstate(divide='ignore'):
        numerator = np.logaddexp(np.log1p(-flag), strength + np.log(flag))
    return numerator - np.logaddexp(math.log(.75), math.log(.25) + strength)


def rounded_interval(measurement, audit):
    """Preserve the original rounding unit even after canonical unit conversion."""
    bounds = timing_interval(measurement)
    if measurement['value'] is None or measurement['lower'] is not None or measurement['upper'] is not None:
        return bounds
    units = {'minutes': 1 / 1440, 'hours': 1 / 24, 'calendar_days': 1.,
             'business_days': 1., 'weeks': 7., 'months': 365.25 / 12}
    unit = audit['original_precision_unit']
    if unit not in units:
        return bounds
    factor = units[measurement['unit']]
    value = measurement['value'] * factor
    half = .5 * units[unit]
    lo, hi = max(value - half, 1e-8), value + half
    if unit == 'business_days':
        hi += 2 * math.ceil(hi / 5)
    return math.log(lo), math.log(max(hi, lo + 1e-8))


def observed_log_probability(bounds, location, scale, contamination, censoring='none'):
    lo, hi = bounds
    if censoring == 'right':
        # Rounding gives a conservative observed lower boundary, not a completion.
        hi = math.inf
    elif censoring == 'left':
        lo = -math.inf
    elif censoring != 'none':
        raise ValueError('Unresolved censoring cannot enter a completed-duration likelihood')
    core = log_interval(lo, hi, location, scale)
    broad = log_interval(lo, hi, location, 2.)
    if contamination == 0:
        return core
    return np.logaddexp(math.log1p(-contamination) + core, math.log(contamination) + broad)


class ProcessMeasurementModel:
    def __init__(self, evidences, audits, cfg=Config()):
        import jsonschema
        if cfg.quadrature < 32 or cfg.chains < 1 or cfg.draws < 8 or cfg.thin < 1 or cfg.warmup < 0:
            raise ValueError('Invalid numerical settings')
        if not 0 <= cfg.contamination < 1 or not 0 < cfg.prep_fraction < 1:
            raise ValueError('Invalid probability prior')
        if min(cfg.prior_median, cfg.prior_log_sd, cfg.report_sd, cfg.selection_width) <= 0:
            raise ValueError('Prior and observation scales must be positive')
        if min(cfg.source_sd, cfg.selection_sd, cfg.clock_logit_sd) < 0:
            raise ValueError('Prior scales cannot be negative')
        self.cfg = cfg
        self.evidences = [validate(copy.deepcopy(e)) for e in evidences]
        if len({e['program_id'] for e in evidences}) != len(evidences):
            raise ValueError('Repeated program identity')
        if len(audits) != len(evidences) or {a['program_id'] for a in audits} != {e['program_id'] for e in evidences}:
            raise ValueError('Audit/evidence programs must match exactly')
        by_program = {a['program_id']: copy.deepcopy(a) for a in audits}
        self.layout = Layout()
        self.programs, self.blocks = [], []
        self.nodes, weights = roots_hermitenorm(cfg.quadrature)
        self.nodes, weights = self.nodes[weights > 0], weights[weights > 0]
        self.log_weights = np.log(weights / math.sqrt(2 * math.pi))
        for evidence in self.evidences:
            pid = evidence['program_id']
            audit = by_program[pid]
            jsonschema.validate(audit, SCHEMA)
            mids = [r['measurement_id'] for r in audit['measurements']]
            if len(mids) != len(set(mids)) or set(mids) != {m['id'] for m in eligible(evidence)}:
                raise ValueError('Audit must cover eligible measurements exactly once')
            if any(r['statistic_interpretation']=='individual_censored' and r['censoring']=='none'
                   for r in audit['measurements']):
                raise ValueError('Censored statistic cannot have no censoring')
            rows = {r['measurement_id']: r for r in audit['measurements']}
            observations, excluded, seen = [], [], set()
            for m in evidence['measurements']:
                a = rows.get(m['id'])
                reason = None
                if a is None:
                    reason = 'not a current numerical elapsed observation'
                elif a['duration_basis'] not in {'whole_case', 'elapsed_so_far'}:
                    reason = 'stage/visit/wait observation retained for task channel, not added into whole-case duration'
                elif a['end_event'] == 'ongoing':
                    reason = 'ongoing endpoint does not establish whether initial decision has happened'
                elif a['end_event'] == 'step_end':
                    reason = 'step endpoint is not a whole-process endpoint'
                elif (a['censoring'] == 'uncertain' or a['statistic_interpretation'] == 'unresolved') and not (
                        cfg.include_ambiguous and a['duration_basis'] == 'whole_case'
                        and a['population_scope'] == 'individual' and m['case_id'] is not None):
                    reason = 'unresolved completion/statistic cannot be treated as completed duration'
                elif a['duration_basis'] == 'elapsed_so_far' and a['censoring'] == 'none':
                    reason = 'elapsed-so-far observation has no defined censoring event'
                elif a['start_event'] in {'step_start', 'after_milestone'}:
                    reason = 'unresolved intermediate start requires event/visit channel'
                if reason:
                    excluded.append({'id': m['id'], 'reason': reason})
                    continue
                interval = rounded_interval(m, a)
                key = (m['source_family'], m['case_id'], interval,
                       tuple(a[k] for k in ('start_event', 'end_event', 'censoring', 'statistic_interpretation')))
                if key in seen:
                    excluded.append({'id': m['id'], 'reason': 'duplicate within source/case/clock/statistic'})
                    continue
                seen.add(key)
                individual = a['statistic_interpretation'].startswith('individual_') or (
                    a['population_scope'] == 'individual' and m['case_id'] is not None)
                if individual and m['case_id'] is None:
                    raise ValueError(f'{pid}/{m["id"]}: individual needs stable case identity')
                observations.append(dict(measurement=m, audit=a, interval=interval,
                    individual=individual, source=m['source_family']))
            sources = sorted({m['source'] for m in observations})
            cohorts = sorted({m['measurement']['cohort'] or m['source'] for m in observations
                if not m['individual'] and m['audit']['population_scope'] == 'selected_cohort'})
            p = dict(id=pid, observations=observations, excluded=excluded, sources=sources, cohorts=cohorts)
            p['main'] = self.layout.add(pid + ':median_and_spread', 2)
            p['source'] = self.layout.add(pid + ':source_offsets', len(sources))
            p['cohort'] = self.layout.add(pid + ':selected_cohort_offsets', len(cohorts))
            p['clock'] = self.layout.add(pid + ':clock_fractions', 3)
            p['selection'] = self.layout.add(pid + ':forum_selection', int(cfg.selection_sd > 0))
            cases = {}
            for m in observations:
                m['source_index'] = sources.index(m['source'])
                m['cohort_index'] = (cohorts.index(m['measurement']['cohort'] or m['source'])
                    if not m['individual'] and m['audit']['population_scope'] == 'selected_cohort' else -1)
                if m['individual']:
                    cases.setdefault(m['measurement']['case_id'], []).append(m)
            p['cases'] = cases
            uncertain_cases = sorted({m['measurement']['case_id'] for m in observations
                if m['individual'] and (m['audit']['censoring'] == 'uncertain'
                                        or m['audit']['statistic_interpretation'] == 'unresolved')})
            p['completion'] = self.layout.add(pid + ':ambiguous_completion_probability', int(bool(uncertain_cases)))
            p['progress'] = self.layout.add(pid + ':ambiguous_case_progress', len(uncertain_cases))
            for m in observations:
                m['progress_index'] = (uncertain_cases.index(m['measurement']['case_id'])
                    if m['measurement']['case_id'] in uncertain_cases else -1)
            p['summaries'] = [m for m in observations if not m['individual']]
            for i,m in enumerate(observations):
                m['row_index'] = i
            p['arrays'] = self.compile_observations(p)
            self.programs.append(p)
            self.blocks.extend([p['main'], p['source'], p['cohort'], p['clock'], p['selection'],
                                p['completion'], p['progress']])
        self.blocks = [b for b in self.blocks if len(b)]

    @staticmethod
    def compile_observations(p):
        rows=p['observations']
        lower=np.array([m['interval'][0] for m in rows])
        upper=np.array([m['interval'][1] for m in rows])
        for i,m in enumerate(rows):
            if m['audit']['censoring']=='right':
                upper[i]=np.inf
            elif m['audit']['censoring']=='left':
                lower[i]=-np.inf
        stats=[m['audit']['statistic_interpretation'] for m in rows]
        scales=np.array([.45 if s=='typical_range' else .7 if s=='informal_forecast' else 0. for s in stats])
        sampling=np.array([math.pi/(2*m['measurement']['n']) if m['measurement']['n']
            and s in {'population_median','population_mean'} else 0. for m,s in zip(rows,stats)])
        return dict(lower=lower,upper=upper,scales=scales,sampling=sampling,
            individual=np.array([m['individual'] for m in rows],dtype=bool),
            is_mean=np.array([s=='population_mean' for s in stats],dtype=bool),
            is_p90=np.array([s=='population_p90' for s in stats],dtype=bool),
            source=np.array([m['source_index'] for m in rows],dtype=int),
            cohort=np.array([m['cohort_index'] for m in rows],dtype=int),
            ambiguous=np.array([m['audit']['censoring']=='uncertain' or s=='unresolved'
                                 for m,s in zip(rows,stats)],dtype=bool))

    def parameters(self, p, z):
        cfg = self.cfg
        mu = math.log(cfg.prior_median) + cfg.prior_log_sd * z[p['main'][0]]
        sigma = math.exp(np.clip(math.log(.6) + .7 * z[p['main'][1]], -10, 5))
        clock = z[p['clock']]
        prep = expit(math.log(cfg.prep_fraction / (1 - cfg.prep_fraction)) + cfg.clock_logit_sd * clock[0])
        complete = expit(math.log(.15 / .85) + cfg.clock_logit_sd * clock[1])
        closeout = math.exp(np.clip(math.log(.20) + clock[2], -20, 20))
        strength = cfg.selection_sd * abs(z[p['selection'][0]]) if len(p['selection']) else 0.
        completion = math.sqrt(ndtr(z[p['completion'][0]])) if len(p['completion']) else 1.
        progress = betaincinv(2., 2., ndtr(z[p['progress']]))
        return dict(mu=mu, sigma=sigma, prep=prep, complete=complete, closeout=closeout,
                    strength=strength, source=cfg.source_sd*z[p['source']], cohort=.6*z[p['cohort']],
                    completion=completion, progress=progress)

    @staticmethod
    def clock_options(audit, par):
        """First filing never removes the span of repeated correction submissions."""
        filing = math.log(max(1 - par['prep'], 1e-15))
        complete = filing + math.log(max(1 - par['complete'], 1e-15))
        start = audit['start_event']
        options = {'preparation_start': [(0., 1.)], 'first_submission': [(filing, 1.)],
                   'complete_submission': [(complete, 1.)], 'unspecified': [(0., .5), (filing, .5)]}[start]
        endpoint = audit['end_event']
        end_options = ([(0., 1.)] if endpoint == 'initial_decision' else
                       [(par['closeout'], 1.)] if endpoint == 'closeout' else
                       [(0., .75), (par['closeout'], .25)])
        # closeout is a fraction of full pre-decision duration, not the shortened clock.
        return [(math.log(math.exp(offset) + extra), weight * end_weight)
                for offset, weight in options for extra, end_weight in end_options]

    def observation_probability(self, m, base, par, use_native=True):
        a, raw = m['audit'], m['measurement']
        offset = par['source'][m['source_index']]
        if m['cohort_index'] >= 0:
            offset += par['cohort'][m['cohort_index']]
        stat = a['statistic_interpretation']
        scale = self.cfg.report_sd
        if stat == 'population_mean':
            base = base + .5 * par['sigma'] ** 2
        elif stat == 'population_p90':
            base = base + ndtri(.9) * par['sigma']
        elif stat == 'typical_range':
            scale = .45
        elif stat == 'informal_forecast':
            scale = .7
        if not m['individual'] and raw['n'] and stat in {'population_median', 'population_mean'}:
            # Summary sampling error is not zero even with many quoted observations.
            sampling = par['sigma'] * math.sqrt(math.pi / (2 * raw['n']))
            scale = math.hypot(scale, sampling)
        ambiguous = a['censoring'] == 'uncertain' or a['statistic_interpretation'] == 'unresolved'
        censoring = 'none' if ambiguous else a['censoring']
        if use_native and self.cfg.accelerate and observation_native is not None:
            lo,hi=m['interval']
            if censoring=='right':
                hi=math.inf
            elif censoring=='left':
                lo=-math.inf
            options=self.clock_options(a,par)
            base_array=np.atleast_1d(base).astype(float)
            progress=par['progress'][m['progress_index']] if ambiguous else 1.
            completion=float(np.clip(par['completion'],1e-15,1-1e-15)) if ambiguous else 1.
            result=observation_native(lo,hi,base_array,float(offset),np.array([o[0] for o in options]),
                np.array([o[1] for o in options]),scale,self.cfg.contamination,progress,completion)
            return float(result[0]) if np.ndim(base)==0 else result
        terms = [math.log(weight) + observed_log_probability(m['interval'], base + offset + shift,
                     scale, self.cfg.contamination, censoring)
                 for shift, weight in self.clock_options(a, par)]
        completed = logsumexp(terms, axis=0)
        if not ambiguous:
            return completed
        # A mixture of two *interval probabilities*, never interval mass + survival.
        # For an unfinished report, its observed elapsed time is fraction U of its
        # eventual duration, U~Beta(2,2). The uncertain completion rate has Beta(2,1)
        # prior. These explicit, unvalidated ascertainment priors need sensitivity.
        fraction = max(par['progress'][m['progress_index']], 1e-15)
        ongoing_terms = [math.log(weight) + observed_log_probability(m['interval'],
            base + offset + shift + math.log(fraction), scale, self.cfg.contamination, 'none')
            for shift, weight in self.clock_options(a, par)]
        probability = np.clip(par['completion'], 1e-15, 1-1e-15)
        return np.logaddexp(math.log(probability) + completed,
                           math.log1p(-probability) + logsumexp(ongoing_terms, axis=0))

    def log_likelihood_reference(self, z, native=False):
        total = 0.
        for p in self.programs:
            par = self.parameters(p, z)
            for rows in p['cases'].values():
                base = par['mu'] + par['sigma'] * self.nodes
                contributions = sum(self.observation_probability(m, base, par,use_native=native) for m in rows)
                selected = any(m['audit']['reporting_sample'] == 'forum_selected' for m in rows)
                logw = log_selection_weight(self.nodes, par['strength'], self.cfg.selection_width) if selected else 0.
                total += float(logsumexp(self.log_weights + logw + contributions))
            for m in p['summaries']:
                total += float(self.observation_probability(m, par['mu'], par,use_native=native))
        return total

    def log_likelihood(self,z):
        """Vectorized same likelihood; the scalar implementation is an audit oracle."""
        if self.cfg.accelerate and observation_native is not None:
            return self.log_likelihood_reference(z,native=True)
        total=0.
        for p in self.programs:
            if not p['observations']:
                continue
            par=self.parameters(p,z)
            a=p['arrays']
            count=len(p['observations'])
            shifts=np.zeros((count,4))
            logweights=np.full((count,4),-np.inf)
            for i,m in enumerate(p['observations']):
                options=self.clock_options(m['audit'],par)
                shifts[i,:len(options)]=[o[0] for o in options]
                logweights[i,:len(options)]=np.log([o[1] for o in options])
            # An appended zero maps cohort index -1 to no offset.
            offset=par['source'][a['source']]+np.append(par['cohort'],0.)[a['cohort']]
            base=(par['mu']+offset+.5*par['sigma']**2*a['is_mean']+
                  ndtri(.9)*par['sigma']*a['is_p90'])[:,None]
            base=base+par['sigma']*a['individual'][:,None]*self.nodes[None,:]
            scale=np.where(a['scales']>0,a['scales'],self.cfg.report_sd)
            scale=np.sqrt(scale**2+a['sampling']*par['sigma']**2)[:,None,None]
            lower,upper=a['lower'][:,None,None],a['upper'][:,None,None]
            def probabilities(location):
                core=log_interval(lower,upper,location,scale)
                if self.cfg.contamination==0:
                    return core
                broad=log_interval(lower,upper,location,2.)
                return np.logaddexp(math.log1p(-self.cfg.contamination)+core,
                                   math.log(self.cfg.contamination)+broad)
            location=base[:,:,None]+shifts[:,None,:]
            completed=logsumexp(logweights[:,None,:]+probabilities(location),axis=2)
            if a['ambiguous'].any():
                progress=np.array([par['progress'][m['progress_index']] if m['progress_index']>=0 else 1.
                                   for m in p['observations']])
                ongoing=logsumexp(logweights[:,None,:]+probabilities(location+
                    np.log(np.maximum(progress,1e-15))[:,None,None]),axis=2)
                probability=np.clip(par['completion'],1e-15,1-1e-15)
                mixed=np.logaddexp(math.log(probability)+completed,math.log1p(-probability)+ongoing)
                completed=np.where(a['ambiguous'][:,None],mixed,completed)
            selected_weight=log_selection_weight(self.nodes,par['strength'],self.cfg.selection_width)
            for rows in p['cases'].values():
                indices=[m['row_index'] for m in rows]
                selected=any(m['audit']['reporting_sample']=='forum_selected' for m in rows)
                total+=float(logsumexp(self.log_weights+completed[indices].sum(axis=0)+
                                      (selected_weight if selected else 0.)))
            total+=sum(float(completed[m['row_index'],0]) for m in p['summaries'])
        return total

    def source_location_move(self,z,rng):
        """Exact Gaussian-prior Gibbs move along a likelihood-invariant ridge."""
        if self.cfg.source_sd<=0:
            return z
        moved=z.copy()
        for p in self.programs:
            if not len(p['source']):
                continue
            indices=np.concatenate((p['main'][:1],p['source']))
            direction=np.concatenate(([1/self.cfg.prior_log_sd],np.full(len(p['source']),-1/self.cfg.source_sd)))
            norm=float(direction@direction)
            current=float(direction@moved[indices])/norm
            draw=rng.normal()/math.sqrt(norm)
            moved[indices]+=(draw-current)*direction
        return moved

    def sample(self, progress=None, initial=None):
        cfg = self.cfg
        chains = np.empty((cfg.chains, cfg.draws, self.layout.size))
        values = np.empty((cfg.chains, cfg.draws))
        calls = []
        if initial is not None and (np.shape(initial)!=(cfg.chains,self.layout.size) or not np.all(np.isfinite(initial))):
            raise ValueError('Initial chain states have wrong shape or nonfinite values')
        for chain in range(cfg.chains):
            rng = np.random.default_rng(cfg.seed + 104729 * chain)
            z = rng.normal(size=self.layout.size) if initial is None else np.asarray(initial[chain],dtype=float).copy()
            ll = self.log_likelihood(z)
            count = 0
            for iteration in range(cfg.warmup + cfg.draws * cfg.thin):
                for block in self.blocks:
                    z, ll, used = elliptical_slice(z, block, self.log_likelihood, ll, rng)
                    count += used
                if cfg.ridge_move:
                    moved=self.source_location_move(z,rng)
                    updated=self.log_likelihood(moved)
                    count+=1
                    if abs(updated-ll)>1e-7:
                        raise ValueError('Location/source Gibbs move changed the likelihood')
                    z,ll=moved,updated
                if iteration >= cfg.warmup and (iteration - cfg.warmup) % cfg.thin == 0:
                    i = (iteration - cfg.warmup) // cfg.thin
                    chains[chain, i], values[chain, i] = z, ll
                if progress and (iteration == 0 or (iteration + 1) % 250 == 0):
                    progress(dict(chain=chain+1, iteration=iteration+1, log_likelihood=ll, calls=count))
            calls.append(count)
        return chains, values, calls

    def report(self, chains, likelihood):
        flat = chains.reshape(-1, self.layout.size)
        results, diags = {}, {}
        for i in range(self.layout.size):
            diags[f'coordinate:{i}'] = diagnostics(chains[:, :, i])
        diags['log_likelihood'] = diagnostics(likelihood)
        for p in self.programs:
            parameters = [self.parameters(p, z) for z in flat]
            medians = np.exp([v['mu'] for v in parameters])
            p90 = np.exp([v['mu'] + ndtri(.9)*v['sigma'] for v in parameters])
            diags[p['id']+':log_median'] = diagnostics(np.log(medians).reshape(chains.shape[:2]))
            diags[p['id']+':log_p90'] = diagnostics(np.log(p90).reshape(chains.shape[:2]))
            results[p['id']] = dict(median_days=summary(medians), p90_days=summary(p90),
                process_median_draws=medians.tolist(),
                log_case_sd=summary([v['sigma'] for v in parameters]),
                forum_log_relative_posting_rate=summary([v['strength'] for v in parameters]),
                prep_fraction=summary([v['prep'] for v in parameters]),
                ambiguous_completion_probability=summary([v['completion'] for v in parameters]),
                source_log_offsets={name: summary([v['source'][i] for v in parameters])
                    for i, name in enumerate(p['sources'])},
                observations=[dict(id=m['measurement']['id'], audit=m['audit'], interval=m['interval'])
                              for m in p['observations']], excluded=p['excluded'],
                n_independent_cases=len(p['cases']), n_population_claims=len(p['summaries']))
        flagged = {k: v for k, v in diags.items() if v['rhat'] is None or v['rhat'] > 1.01
                   or v['ess_bulk'] < 400 or v['ess_tail'] < 200}
        return dict(model='process-measurement/5-development', programs=results, diagnostics=diags,
            diagnostics_flagged=flagged, posterior_converged=not flagged,
            scope='whole-process timing only; agency/task hierarchy, counts and labor remain separate',
            limitations=['Conditional on source-only semantic audit and fixed source/case identities.',
                'No outcome-specific ascertainment; delay selection does not correct all selection biases.',
                'Summary range/forecast relates noisily to location; it is not an observed measured median.',
                'Uncertain preparation and closeout fractions use explicit priors, not task-span subtraction.',
                'When enabled, ambiguous case completion/progress is latent with unvalidated Beta priors.',
                'No whole-case evidence leaves a prior, not an invented sum of overlapping stage spans.'])
