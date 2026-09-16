"""Case-varying preparation fractions, with coherent population clock operators.

Development sensitivity model, not a visit/agency hierarchy. Total duration and
preparation fraction vary independently conditional on program/outcome parameters;
the same realized fraction is shared by every report from one known case.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.special import betaincinv, expit, logsumexp, ndtr, roots_hermitenorm

from .bayes_preparation_measurement import Config as PreparationConfig, PreparationMeasurementModel
from .bayes_process_measurement import observed_log_probability
from .latent_gaussian import diagnostics, summary
from .phase_mixture import quantile_density


@dataclass(frozen=True)
class Config(PreparationConfig):
    case_preparation_logit_sd: float = 1.
    preparation_budget_mode: str = 'coverage_partition'
    preparation_coverage_alpha: float = 1.
    preparation_coverage_beta: float = 1.
    fraction_quadrature: int = 64


def partitioned_budget(z, coverage_alpha=1., coverage_beta=1., partition_alpha=1.):
    """Total coverage has the SAME Beta prior regardless of segmentation count.

    Conditional on total covered fraction C, k disjoint spans have a symmetric
    Dirichlet partition. Uses k normals: one for C, k-1 for the partition.
    """
    if min(coverage_alpha, coverage_beta, partition_alpha) <= 0:
        raise ValueError('Coverage and partition concentrations must be positive')
    u = np.clip(ndtr(np.asarray(z)), 1e-15, 1-1e-15)
    if len(u) < 1:
        raise ValueError('At least one reported span is required')
    coverage = betaincinv(coverage_alpha, coverage_beta, u[0])
    remaining = coverage
    fractions = []
    for i in range(1, len(u)):
        fraction = betaincinv(partition_alpha, (len(u)-i)*partition_alpha, u[i])
        fractions.append(remaining * fraction)
        remaining *= 1-fraction
    fractions.append(remaining)
    return np.asarray(fractions)


class VariablePreparationModel(PreparationMeasurementModel):
    def __init__(self, evidences, audits, outcomes, preparations, cfg=Config()):
        if not math.isfinite(cfg.case_preparation_logit_sd) or cfg.case_preparation_logit_sd < 0:
            raise ValueError('Case-fraction spread must be finite and nonnegative')
        if cfg.preparation_budget_mode not in {'dirichlet', 'coverage_partition'}:
            raise ValueError('Unknown preparation budget model')
        if not all(math.isfinite(x) and x > 0 for x in
                   (cfg.preparation_coverage_alpha, cfg.preparation_coverage_beta)):
            raise ValueError('Coverage concentrations must be finite and positive')
        if cfg.fraction_quadrature < 16:
            raise ValueError('At least 16 fraction-quadrature nodes are required')
        super().__init__(evidences, audits, outcomes, preparations, cfg)
        nodes, weights = roots_hermitenorm(cfg.fraction_quadrature)
        keep = weights > 0
        self.fraction_nodes = nodes[keep]
        self.fraction_weights = weights[keep] / math.sqrt(2*math.pi)
        for p in self.programs:
            p['fraction_cases'] = sorted(p['cases'])
            count = len(p['fraction_cases']) if cfg.case_preparation_logit_sd > 0 else 0
            p['case_fraction_indices'] = self.layout.add(p['id']+':case_preparation_fractions', count)
            if count:
                self.blocks.append(p['case_fraction_indices'])
            p['cache_indices'] = np.concatenate((p['cache_indices'], p['case_fraction_indices']))

    def parameters(self, p, z):
        par = super().parameters(p, z)
        if self.cfg.preparation_budget_mode == 'coverage_partition':
            fractions = np.ones(len(p['anchors']))
            for group in p['preparation_groups']:
                fractions[group['indices']] = partitioned_budget(
                    z[p['preparation_fractions'][group['coordinates']]],
                    self.cfg.preparation_coverage_alpha, self.cfg.preparation_coverage_beta,
                    self.cfg.preparation_span_alpha)
            par['preparation_spans'] = fractions
        # Use the underlying logit, not logit(expit(.)), which can round to inf.
        location = math.log(self.cfg.prep_fraction/(1-self.cfg.prep_fraction))
        location += self.cfg.clock_logit_sd*z[p['clock'][0]]
        spread = self.cfg.case_preparation_logit_sd
        values = (expit(location + spread*z[p['case_fraction_indices']]) if spread > 0
                  else np.full(len(p['fraction_cases']), par['prep']))
        par['case_preparation'] = dict(zip(p['fraction_cases'], values))
        par['population_preparation'] = expit(location + spread*self.fraction_nodes)
        return par

    def clock_mixture(self, par, start, endpoint):
        fractions = par['population_preparation']
        if start == 'preparation_only':
            remaining = fractions
        elif start == 'preparation_start':
            remaining = np.ones_like(fractions)
        elif start == 'first_submission':
            remaining = 1-fractions
        elif start == 'complete_submission':
            remaining = (1-fractions)*(1-par['complete'])
        else:
            raise ValueError('An explicit clock is required for a population functional')
        if endpoint == 'closeout':
            remaining = remaining + par['closeout']
        elif endpoint != 'initial_decision':
            raise ValueError('An explicit endpoint is required for a population functional')
        locations = (par['locations'][:, None] + np.log(np.maximum(remaining, 1e-300))[None, :]).ravel()
        weights = (np.array([par['approval_probability'], 1-par['approval_probability']])[:, None]
                   * self.fraction_weights[None, :]).ravel()
        return locations, weights

    def population_summary(self, par, start, endpoint, statistic, sample_size=None, native=True):
        locations, weights = self.clock_mixture(par, start, endpoint)
        sigma = par['sigma']
        if statistic == 'population_mean':
            first = logsumexp(np.log(weights)+locations) + sigma*sigma/2
            second = logsumexp(np.log(weights)+2*locations) + 2*sigma*sigma
            # Moment-matched log-scale sampling error for an arithmetic mean.
            variance = math.expm1(max(0., min(700., second-2*first)))
            sampling = math.sqrt(math.log1p(variance/sample_size)) if sample_size else 0.
            return first, sampling
        probability = .9 if statistic == 'population_p90' else .5
        value, density = quantile_density(probability, locations, weights, sigma,
                                         native=native and self.cfg.accelerate)
        measured = statistic in {'population_median', 'population_p90'}
        sampling = (math.sqrt(probability*(1-probability)/sample_size)/max(density, 1e-300)
                    if sample_size and measured else 0.)
        return value, sampling

    def observation_probability(self, m, base, par, use_native=True):
        if m['individual']:
            conditional = dict(par)
            conditional['prep'] = par['case_preparation'][m['measurement']['case_id']]
            return super().observation_probability(m, base, conditional, use_native=use_native)
        audit, raw = m['audit'], m['measurement']
        starts = ([('preparation_start', .5), ('first_submission', .5)]
                  if audit['start_event'] == 'unspecified' else [(audit['start_event'], 1.)])
        ends = ([('initial_decision', .75), ('closeout', .25)]
                if audit['end_event'] == 'unspecified' else [(audit['end_event'], 1.)])
        offset = par['source'][m['source_index']]
        if m['cohort_index'] >= 0:
            offset += par['cohort'][m['cohort_index']]
        stat = audit['statistic_interpretation']
        scale = .45 if stat == 'typical_range' else .7 if stat == 'informal_forecast' else self.cfg.report_sd
        terms = []
        for start, start_weight in starts:
            for endpoint, end_weight in ends:
                value, sampling = self.population_summary(par, start, endpoint, stat, raw['n'], use_native)
                terms.append(math.log(start_weight*end_weight) + observed_log_probability(
                    m['interval'], value+offset, math.hypot(scale, sampling),
                    self.cfg.contamination, audit['censoring']))
        return float(logsumexp(terms))

    def report(self, chains, likelihood):
        result = super().report(chains, likelihood)
        result['model'] = 'variable-preparation-process-measurement/5-development'
        flat = chains.reshape(-1, self.layout.size)
        for p in self.programs:
            pars = [self.parameters(p, z) for z in flat]
            for start, field, diag in (
                    ('preparation_only', 'preparation_median_days', 'log_preparation_median'),
                    ('first_submission', 'first_filing_to_decision_median_days', 'log_first_filing_median')):
                values = np.array([self.population_summary(v, start, 'initial_decision', 'population_median')[0]
                                   for v in pars])
                result['programs'][p['id']][field] = summary(np.exp(values))
                result['diagnostics'][p['id']+':'+diag] = diagnostics(values.reshape(chains.shape[:2]))
            result['programs'][p['id']]['case_preparation_fractions'] = {
                case: summary([v['case_preparation'][case] for v in pars]) for case in p['fraction_cases']}
        result['diagnostics_flagged'] = {k: v for k, v in result['diagnostics'].items()
            if v['rhat'] is None or v['rhat'] > 1.01 or v['ess_bulk'] < 400 or v['ess_tail'] < 200}
        result['posterior_converged'] = not result['diagnostics_flagged']
        result['limitations'] = [s for s in result['limitations'] if not s.startswith('Common preparation fraction')]
        result['limitations'].extend([
            'Case preparation logit spread is fixed for sensitivity analysis, not established by the data.',
            'Preparation fraction is independent of total duration conditional on program/outcome parameters.',
            'Total reported coverage prior is segmentation-invariant when coverage_partition is enabled.',
            'Population summary sampling errors are asymptotic approximations, not raw-cohort likelihoods.'])
        return result
