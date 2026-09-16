"""Outcome-stratified extension of the v5 process measurement channel.

Approval/denial durations share a within-outcome spread but have different latent
locations. Public decided-cohort counts inform prevalence; mixed pending/issued
counts do not. Known-outcome anecdotes condition on outcome, not its frequency.
"""
from dataclasses import dataclass
import copy
import math

import numpy as np
from scipy.special import expit,logsumexp,ndtr,ndtri

from .audit_case_outcomes import SCHEMA
from .audit_measurement_semantics import eligible
from .bayes_process_measurement import Config as BaseConfig,ProcessMeasurementModel,log_selection_weight
from .latent_gaussian import diagnostics,summary


@dataclass(frozen=True)
class Config(BaseConfig):
    outcome_contrast_sd: float = .7
    outcome_posting_sd: float = 1.5
    admin_logit_sd: float = .35


def mixture_quantile(probability,locations,sigma,approval_probability):
    """Quantile of two normals on log duration, not a weighted mean of medians."""
    locations=np.asarray(locations)
    lo,hi=float(locations.min()-10*sigma),float(locations.max()+10*sigma)
    for _ in range(45):
        middle=(lo+hi)/2
        cdf=approval_probability*ndtr((middle-locations[0])/sigma)+(1-approval_probability)*ndtr((middle-locations[1])/sigma)
        if cdf<probability:
            lo=middle
        else:
            hi=middle
    return (lo+hi)/2


def shifted_selection_normalizer(shift,strength,width):
    """E[N(shift,1)] of the normalized reference-population selection weight."""
    threshold=ndtri(.75)*math.sqrt(1+width*width)
    tail=ndtr((shift-threshold)/math.sqrt(1+width*width))
    tail=np.clip(tail,1e-300,1-1e-15)
    return np.logaddexp(math.log1p(-tail),strength+math.log(tail)) - np.logaddexp(math.log(.75),math.log(.25)+strength)


class OutcomeMeasurementModel(ProcessMeasurementModel):
    def __init__(self,evidences,audits,outcomes,cfg=Config()):
        import jsonschema
        outcomes=copy.deepcopy(outcomes)
        if min(cfg.outcome_contrast_sd,cfg.outcome_posting_sd,cfg.admin_logit_sd)<0:
            raise ValueError('Outcome scales must be nonnegative')
        if len(outcomes)!=len(evidences) or {a['program_id'] for a in outcomes}!={e['program_id'] for e in evidences}:
            raise ValueError('Outcome-audit programs must match exactly')
        by_program={a['program_id']:a for a in outcomes}
        for audit in outcomes:
            jsonschema.validate(audit,SCHEMA)
            for row in audit['cases']:
                if row['outcome'] in {'approved','denied'} and row['initial_decision_status']!='completed':
                    raise ValueError('Approved/denied requires a completed initial decision')
            for row in audit['population_counts']:
                if row['denominator_interpretation']=='same_decision_cohort' and (
                        row['approved'] is None or row['denied'] is None):
                    raise ValueError('Decided denominator requires both approved and denied counts')
        resolved=copy.deepcopy(audits)
        resolutions=[]
        for audit in resolved:
            eid={m['id']:m for e in evidences if e['program_id']==audit['program_id'] for m in e['measurements']}
            cases={c['case_id']:c for c in by_program[audit['program_id']]['cases']}
            for row in audit['measurements']:
                case=cases.get(eid[row['measurement_id']]['case_id'],{})
                if (row['end_event']=='ongoing' and row['censoring']=='right'
                        and case.get('initial_decision_status')=='ongoing'):
                    row['end_event']='initial_decision'
                    row['evidence']+=case['evidence']
                    row['notes']+=' Outcome audit explicitly identifies an unfinished INITIAL decision; use right censoring, not completion.'
                    resolutions.append(dict(program=audit['program_id'],measurement=row['measurement_id'],
                        action='right-censor initial-decision clock using independent outcome-audit support'))
        super().__init__(evidences,resolved,cfg)
        self.semantic_resolutions=resolutions
        self._program_cache={}
        self.posting_index=self.layout.add('shared:denial_posting',1)
        self.blocks.append(self.posting_index)
        for p,e in zip(self.programs,self.evidences):
            audit=by_program[p['id']]
            jsonschema.validate(audit,SCHEMA)
            ids=[r['case_id'] for r in audit['cases']]
            if len(ids)!=len(set(ids)) or set(ids)!={m['case_id'] for m in eligible(e) if m['case_id'] is not None}:
                raise ValueError('Outcome audit must cover eligible cases exactly once')
            p['outcomes']={r['case_id']:r['outcome'] for r in audit['cases']}
            abandoned={cid for cid,outcome in p['outcomes'].items() if outcome=='abandoned'}
            for m in p['observations']:
                if m['measurement']['case_id'] in abandoned:
                    p['excluded'].append(dict(id=m['measurement']['id'],reason='abandoned case is not a completed initial decision'))
            p['observations']=[m for m in p['observations'] if m['measurement']['case_id'] not in abandoned]
            p['cases']={k:v for k,v in p['cases'].items() if k not in abandoned}
            p['summaries']=[m for m in p['observations'] if not m['individual']]
            p['outcome_index']=self.layout.add(p['id']+':outcome_contrast_and_prevalence',2)
            p['counts'],p['excluded_counts']=[],[]
            seen=set()
            for row in audit['population_counts']:
                if (row['denominator_interpretation']!='same_decision_cohort' or
                    row['population_scope']!='all_cases' or row['temporal_scope']=='historical' or
                    row['approved'] is None or row['denied'] is None or row['approved']+row['denied']==0):
                    p['excluded_counts'].append(dict(id=row['id'],reason='not an explicit current same-population decided denominator'))
                    continue
                key=(row['source_family'],row['approved'],row['denied'])
                if key in seen:
                    p['excluded_counts'].append(dict(id=row['id'],reason='duplicate decided-cohort count'))
                    continue
                seen.add(key)
                p['counts'].append(row)
            p['admin_bias']=self.layout.add(p['id']+':administrative_cohort_logit_offsets',len(p['counts']))
            self.blocks.extend([p['outcome_index']])
            if len(p['admin_bias']):
                self.blocks.append(p['admin_bias'])
            p['cache_indices']=np.concatenate([p[k] for k in ['main','source','cohort','clock','selection',
                'completion','progress','outcome_index','admin_bias']]+[self.posting_index])

    def parameters(self,p,z):
        par=super().parameters(p,z)
        contrast=self.cfg.outcome_contrast_sd*z[p['outcome_index'][0]]
        par['locations']=par['mu']+np.array([.5,-.5])*contrast
        par['approval_probability']=np.clip(ndtr(z[p['outcome_index'][1]]),1e-15,1-1e-15)
        par['denial_posting']=self.cfg.outcome_posting_sd*abs(z[self.posting_index[0]])
        par['admin_bias']=self.cfg.admin_logit_sd*z[p['admin_bias']]
        return par

    def log_likelihood(self,z):
        total=0.
        for p in self.programs:
            key=tuple(z[p['cache_indices']])
            cached=self._program_cache.get(p['id'])
            if cached is not None and cached[0]==key:
                total+=cached[1]
                continue
            subtotal=total
            par=self.parameters(p,z)
            pi=par['approval_probability']
            locations=par['locations']
            logmix=np.log([pi,1-pi])
            shifts=(locations-par['mu'])/par['sigma']
            normalizers=np.array([shifted_selection_normalizer(s,par['strength'],self.cfg.selection_width) for s in shifts])
            outcome_post=np.array([0.,par['denial_posting']])
            global_selection=logsumexp(logmix+outcome_post+normalizers)
            for case,rows in p['cases'].items():
                known=p['outcomes'][case]
                branches=[0] if known=='approved' else [1] if known=='denied' else [0,1]
                selected=any(m['audit']['reporting_sample']=='forum_selected' for m in rows)
                terms=[]
                for branch in branches:
                    base=locations[branch]+par['sigma']*self.nodes
                    contributions=sum(self.observation_probability(m,base,par) for m in rows)
                    weight=log_selection_weight(self.nodes+shifts[branch],par['strength'],self.cfg.selection_width) if selected else 0.
                    term=float(logsumexp(self.log_weights+contributions+weight))
                    if len(branches)==1:
                        # Conditional sampling: three stated denials are not a binomial survey.
                        if selected:
                            term-=normalizers[branch]
                    else:
                        term+=logmix[branch]
                        if selected:
                            term+=outcome_post[branch]-global_selection
                    terms.append(term)
                total+=float(logsumexp(terms))
            if p['summaries']:
                med=mixture_quantile(.5,locations,par['sigma'],pi)
                for m in p['summaries']:
                    stat=m['audit']['statistic_interpretation']
                    if stat=='population_mean':
                        base=float(logsumexp(logmix+locations))
                    elif stat=='population_p90':
                        base=mixture_quantile(.9,locations,par['sigma'],pi)-ndtri(.9)*par['sigma']
                    else:
                        base=med
                    total+=float(self.observation_probability(m,base,par))
            for row,bias in zip(p['counts'],par['admin_bias']):
                logit=math.log(pi)-math.log1p(-pi)+bias
                total+=row['approved']*(-np.logaddexp(0.,-logit))+row['denied']*(-np.logaddexp(0.,logit))
            self._program_cache[p['id']]=(key,total-subtotal)
        return float(total)

    def report(self,chains,likelihood):
        # Reuse provenance/observation summaries, replacing all population functionals.
        result=super().report(chains,likelihood)
        result['model']='outcome-process-measurement/5-development'
        result['semantic_resolutions']=self.semantic_resolutions
        flat=chains.reshape(-1,self.layout.size)
        for p in self.programs:
            parameters=[self.parameters(p,z) for z in flat]
            medians=np.exp([mixture_quantile(.5,v['locations'],v['sigma'],v['approval_probability']) for v in parameters])
            p90=np.exp([mixture_quantile(.9,v['locations'],v['sigma'],v['approval_probability']) for v in parameters])
            result['programs'][p['id']].update(median_days=summary(medians),p90_days=summary(p90),
                process_median_draws=medians.tolist(),approval_probability=summary([v['approval_probability'] for v in parameters]),
                approved_median_days=summary(np.exp([v['locations'][0] for v in parameters])),
                denied_median_days=summary(np.exp([v['locations'][1] for v in parameters])),
                used_population_counts=p['counts'],excluded_population_counts=p['excluded_counts'])
            result['diagnostics'][p['id']+':log_median']=diagnostics(np.log(medians).reshape(chains.shape[:2]))
            result['diagnostics'][p['id']+':log_p90']=diagnostics(np.log(p90).reshape(chains.shape[:2]))
        result['shared_denial_log_relative_posting_rate']=summary(self.cfg.outcome_posting_sd*np.abs(flat[:,self.posting_index[0]]))
        result['diagnostics_flagged']={k:v for k,v in result['diagnostics'].items() if v['rhat'] is None or
            v['rhat']>1.01 or v['ess_bulk']<400 or v['ess_tail']<200}
        result['posterior_converged']=not result['diagnostics_flagged']
        result['limitations']=[s for s in result['limitations'] if not s.startswith('No outcome-specific')]
        result['limitations'].extend(['Known-outcome anecdotes condition on outcome; their counts do not identify prevalence.',
            'Unlabeled forum cases use a selected outcome mixture; selective outcome disclosure remains unmodeled.',
            'Approval/denial mixture has shared within-outcome spread; it is not a full route/visit model.'])
        return result
