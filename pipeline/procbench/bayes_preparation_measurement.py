"""Partial preparation clocks in the outcome-aware process measurement model.

Pre-filing reports observe uncertain portions of preparation, not its entirety.
Only source-supported disjoint groups share an additive budget. All other spans
may overlap; neither serial nor parallel scheduling is asserted for them.
This is a bounded-clock observation model, not an agency/task duration hierarchy.
"""
from dataclasses import dataclass
import copy
import math

import numpy as np
from scipy.special import betaincinv,ndtr

from .audit_preparation_clocks import validate_preparation
from .bayes_outcome_measurement import Config as OutcomeConfig,OutcomeMeasurementModel
from .bayes_process_measurement import observed_log_probability,rounded_interval
from .latent_gaussian import diagnostics,summary
from .measurement_kernel import observation_native


@dataclass(frozen=True)
class Config(OutcomeConfig):
    preparation_report_sd: float = .35
    preparation_span_alpha: float = 1.
    preparation_remainder_alpha: float = 1.


def budget_fractions(z,span_alpha=1.,remainder_alpha=1.):
    """Dirichlet portions plus an unobserved remainder, using normal coordinates.

    Each group with k measurements uses k independent normals. Their transformed
    fractions have Dirichlet(span_alpha,...,span_alpha,remainder_alpha) law;
    the final unobserved remainder is implicit and strictly nonnegative.
    A singleton is a Beta portion, not a claim to observe all preparation.
    """
    if min(span_alpha,remainder_alpha)<=0:
        raise ValueError('Budget concentration parameters must be positive')
    uniforms=np.clip(ndtr(np.asarray(z)),1e-15,1-1e-15)
    count=len(uniforms)
    remainder=1.
    fractions=[]
    for i,u in enumerate(uniforms):
        stick=betaincinv(span_alpha,(count-i-1)*span_alpha+remainder_alpha,u)
        fractions.append(remainder*stick)
        remainder*=1-stick
    return np.asarray(fractions)


class PreparationMeasurementModel(OutcomeMeasurementModel):
    def __init__(self,evidences,audits,outcomes,preparations,cfg=Config()):
        if not all(math.isfinite(x) and x>0 for x in (cfg.preparation_report_sd,
                cfg.preparation_span_alpha,cfg.preparation_remainder_alpha)):
            raise ValueError('Preparation scales and concentrations must be finite and positive')
        if len(preparations)!=len(evidences) or {p['program_id'] for p in preparations}!={e['program_id'] for e in evidences}:
            raise ValueError('Preparation-audit programs must match exactly')
        preparations=copy.deepcopy(preparations)
        for audit in preparations:
            evidence=next(e for e in evidences if e['program_id']==audit['program_id'])
            validate_preparation(audit,evidence)
        super().__init__(evidences,audits,outcomes,cfg)
        semantic={a['program_id']:{r['measurement_id']:copy.deepcopy(r) for r in a['measurements']} for a in audits}
        for p,e in zip(self.programs,self.evidences):
            audit=next(a for a in preparations if a['program_id']==p['id'])
            measurements={m['id']:m for m in e['measurements']}
            included={m['measurement']['id'] for m in p['observations']}
            anchors,excluded,seen=[],[],set()
            for row in audit['measurements']:
                mid=row['measurement_id']
                m=measurements[mid]
                a=semantic[p['id']][mid]
                reason=None
                if row['phase']!='before_first_submission':
                    reason='not explicitly wholly before first submission'
                elif row['basis'] in {'service_only','single_visit'}:
                    reason='short service/visit channel kept separate from generic preparation-span allocation'
                elif m['case_id'] is None or a['population_scope']!='individual':
                    reason='population subspan needs a distribution-specific observation operator'
                elif p['outcomes'][m['case_id']]=='abandoned':
                    reason='abandoned cases are outside the completed-decision population model'
                elif a['censoring']!='none':
                    reason='unfinished preparation span needs its own censoring/ascertainment operator'
                elif mid in included:
                    raise ValueError('Preparation claim already entered as a whole-case observation')
                interval=rounded_interval(m,a)
                key=(m['case_id'],m['source_family'],tuple(m['activity_ids']),
                     row['start_event'],row['end_event'],interval)
                if reason is None and key in seen:
                    reason='duplicate source/case/component/clock claim'
                if reason:
                    excluded.append(dict(id=mid,reason=reason))
                    continue
                seen.add(key)
                anchors.append(dict(measurement=m,audit=a,interval=interval,individual=True,
                    source=m['source_family'],cohort_index=-1,progress_index=-1,
                    preparation_anchor=True,preparation_clock=row,
                    full_preparation=row['start_event']=='process_start' and row['end_event']=='first_submission'))
            by_id={m['measurement']['id']:m for m in anchors}
            new_sources=sorted({m['source'] for m in anchors}-set(p['sources']))
            extra_sources=self.layout.add(p['id']+':preparation_only_source_offsets',len(new_sources))
            if len(extra_sources):
                p['source']=np.concatenate((p['source'],extra_sources))
                p['sources']+=new_sources
                self.blocks.append(extra_sources)
            for i,m in enumerate(anchors):
                m['source_index']=p['sources'].index(m['source'])
                m['anchor_index']=i
                p['cases'].setdefault(m['measurement']['case_id'],[]).append(m)
            groups=[]
            assigned=set()
            for group in audit['serial_groups']:
                # A subset of a disjoint group stays disjoint. Dropped microservice
                # is part of the unobserved budget, never silently equal to zero.
                ids=[mid for mid in group['measurement_ids'] if mid in by_id]
                if len(ids)>=2:
                    groups.append(dict(indices=[by_id[mid]['anchor_index'] for mid in ids],support=group))
                    assigned.update(ids)
            for mid,m in by_id.items():
                if mid not in assigned and not m['full_preparation']:
                    groups.append(dict(indices=[m['anchor_index']],support=None))
            allocated=0
            for group in groups:
                group['coordinates']=np.arange(allocated,allocated+len(group['indices']))
                allocated+=len(group['indices'])
            p['anchors']=anchors
            p['preparation_groups']=groups
            p['excluded_preparation']=excluded
            p['preparation_fractions']=self.layout.add(p['id']+':partial_preparation_spans',allocated)
            if allocated:
                self.blocks.append(p['preparation_fractions'])
            p['cache_indices']=np.concatenate((p['cache_indices'],extra_sources,p['preparation_fractions']))
            p['observations']+=anchors
            p['excluded']=[r for r in p['excluded'] if r['id'] not in by_id]

    def parameters(self,p,z):
        par=super().parameters(p,z)
        fractions=np.ones(len(p['anchors']))
        for group in p['preparation_groups']:
            ids=group['indices']
            fractions[ids]=budget_fractions(z[p['preparation_fractions'][group['coordinates']]],
                self.cfg.preparation_span_alpha,self.cfg.preparation_remainder_alpha)
        par['preparation_spans']=fractions
        return par

    def observation_probability(self,m,base,par,use_native=True):
        if not m.get('preparation_anchor'):
            return super().observation_probability(m,base,par,use_native=use_native)
        fraction=par['preparation_spans'][m['anchor_index']]
        offset=par['source'][m['source_index']]
        shift=math.log(max(par['prep']*fraction,1e-300))
        if use_native and self.cfg.accelerate and observation_native is not None:
            result=observation_native(*m['interval'],np.atleast_1d(base).astype(float),float(offset),
                np.array([shift]),np.array([1.]),self.cfg.preparation_report_sd,self.cfg.contamination,1.,1.)
            return float(result[0]) if np.ndim(base)==0 else result
        return observed_log_probability(m['interval'],base+offset+shift,
            self.cfg.preparation_report_sd,self.cfg.contamination)

    def report(self,chains,likelihood):
        result=super().report(chains,likelihood)
        result['model']='preparation-outcome-process-measurement/5-development'
        flat=chains.reshape(-1,self.layout.size)
        for p in self.programs:
            pars=[self.parameters(p,z) for z in flat]
            prep=np.array([v['prep'] for v in pars])
            total=np.asarray(result['programs'][p['id']]['process_median_draws'])
            result['programs'][p['id']].update(preparation_median_days=summary(prep*total),
                first_filing_to_decision_median_days=summary((1-prep)*total),
                preparation_observations=[dict(id=m['measurement']['id'],clock=m['preparation_clock']) for m in p['anchors']],
                preparation_disjoint_groups=[g['support'] for g in p['preparation_groups'] if g['support']],
                excluded_preparation=p['excluded_preparation'])
            for name,values in [('log_preparation_median',np.log(prep*total)),
                                ('log_first_filing_median',np.log((1-prep)*total))]:
                result['diagnostics'][p['id']+':'+name]=diagnostics(values.reshape(chains.shape[:2]))
        result['diagnostics_flagged']={k:v for k,v in result['diagnostics'].items() if v['rhat'] is None or
            v['rhat']>1.01 or v['ess_bulk']<400 or v['ess_tail']<200}
        result['posterior_converged']=not result['diagnostics_flagged']
        result['limitations'].extend([
            'Preparation fractions are learned from partial spans; coverage priors remain consequential.',
            'Common preparation fraction across cases is a simplifying assumption, not a visit-based phase model.',
            'Reported-preparation-clock coverage can omit earlier preparation; its remainder is not fixed to zero.',
            'Unsupported overlap is unresolved; separate partial spans are not summed or declared parallel.',
            'This channel does not pool task times by agency and does not estimate work hours.'])
        return result
