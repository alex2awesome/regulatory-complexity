"""Joint finite-sample quantiles for an explicitly declared IID cohort.

The population is the hierarchy's weighted integration grid, not a new fitted
distribution. Selected uniform order statistics are integrated jointly using
conditional Beta spacings, then transformed through that population's inverse
CDF. Linear interpolation is applied to durations, never their logarithms.
Reporting error is applied AFTER forming the sample summaries by the caller.

This integrates sampling uncertainty without allocating n applicant latents.
It does not justify IID sampling, independent cohorts, unobserved denominators,
or a quantile convention. Those must be supplied and qualified upstream.
"""
import math

import numpy as np
from scipy.special import betaincinv
from scipy.stats import qmc


QUANTILES = {'median': .5, 'p90': .9}
QUANTILE_METHODS = {'linear', 'inverted_cdf'}


def cohort_report_observations(cohort):
    """Validate the explicit cohort contract and expose reports for unit checks.

    Returned rows are for validation/coverage, NOT independent likelihood terms.
    Shared-clock/interpretation assumptions occur once at the cohort level.
    """
    required = {'id', 'cohort_id', 'sample_size', 'quantile_method', 'sampling',
                'independent_of_other_evidence', 'conditional_report_independence',
                'source_family', 'operators', 'operator_weights', 'reports'}
    # source_type/report_log_scale are optional compiler-resolved annotations.
    # Their strict provenance and applicability are validated by V6's shared
    # source-precision resolver, not by this sampling-only module.
    optional = {'population_condition', 'population_path_scope', 'provenance', 'time_unit',
                'source_type', 'report_log_scale'}
    if not required <= cohort.keys() or set(cohort)-required-optional:
        raise ValueError('Finite quantile cohorts require an explicit sampling/report contract')
    if any(not isinstance(cohort[k], str) or not cohort[k].strip()
           for k in ('id', 'cohort_id', 'source_family')):
        raise ValueError('Cohort, factor and source identities must be nonempty strings')
    if (cohort['sampling'] != 'iid_within_declared_population'
            or cohort['independent_of_other_evidence'] is not True
            or cohort['conditional_report_independence'] is not True):
        raise ValueError('Declare IID cohort sampling and conditional report/other-evidence independence')
    n = cohort['sample_size']
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError('A cohort requires a positive integer observed sample size')
    if cohort['quantile_method'] not in QUANTILE_METHODS:
        raise ValueError('Declare a supported sample quantile convention')
    if not isinstance(cohort['reports'], list) or not cohort['reports']:
        raise ValueError('A quantile cohort needs its reported summaries')
    reports, identities, statistics = [], set(), set()
    for report in cohort['reports']:
        required_report = {'id', 'statistic', 'lower', 'upper'}
        if (not required_report <= report.keys()
                or set(report)-required_report-{'report_intervals', 'measurement_ids', 'provenance'}):
            raise ValueError('Cohort reports require explicit identities, statistics and intervals')
        if report['id'] in identities or report['statistic'] in statistics:
            raise ValueError('Repeated cohort summaries must be reconciled as reports, not independent evidence')
        if report['statistic'] not in QUANTILES:
            raise ValueError('Finite-cohort support is for medians/percentiles, not means')
        identities.add(report['id'])
        statistics.add(report['statistic'])
        row = dict(report, case_id=None, sampling='unselected', source_family=cohort['source_family'],
                   operators=cohort['operators'], operator_weights=cohort['operator_weights'])
        row.update({k: cohort[k] for k in ('population_condition', 'population_path_scope', 'time_unit') if k in cohort})
        reports.append(row)
    return reports


class CohortQuantileGrid:
    def __init__(self, sample_size, statistics, method, size=256, seed=811):
        if (isinstance(sample_size, bool) or not isinstance(sample_size, int)
                or sample_size < 1):
            raise ValueError('A cohort requires a positive integer observed sample size')
        if method not in QUANTILE_METHODS:
            raise ValueError('Declare a supported sample quantile convention')
        if not statistics or any(stat not in QUANTILES for stat in statistics):
            raise ValueError('Finite-cohort support is for medians/percentiles, not means')
        if isinstance(size, bool) or not isinstance(size, int) or size < 16 or size & (size-1):
            raise ValueError('Cohort integration size must be a power of two of at least 16')
        self.sample_size, self.statistics, self.method = sample_size, tuple(statistics), method
        self.size, self.seed = size, seed
        interpolations = []
        for statistic in statistics:
            q = QUANTILES[statistic]
            if method == 'inverted_cdf':
                rank = max(1, math.ceil(q*sample_size))
                interpolations.append((rank, rank, 0.))
            else:
                position = (sample_size-1)*q
                lower = math.floor(position)+1
                fraction = position-math.floor(position)
                interpolations.append((lower, lower+int(fraction > 0), fraction))
        self.ranks = tuple(sorted({rank for lo, hi, _ in interpolations for rank in (lo, hi)}))
        self.interpolations = tuple((self.ranks.index(lo), self.ranks.index(hi), weight)
                                    for lo, hi, weight in interpolations)
        uniforms = qmc.Sobol(len(self.ranks), scramble=True, seed=seed).random_base2(size.bit_length()-1)
        uniforms = np.clip(uniforms, np.nextafter(0., 1.), np.nextafter(1., 0.))
        self.uniform_order_statistics = np.empty_like(uniforms)
        previous_rank, previous = 0, np.zeros(size)
        for column, rank in enumerate(self.ranks):
            # Given U_(previous_rank), the remaining observations are uniform
            # above it. This dependence is essential for a median+p90 pair.
            fraction = betaincinv(rank-previous_rank, sample_size-rank+1, uniforms[:, column])
            previous = previous+(1-previous)*fraction
            self.uniform_order_statistics[:, column] = previous
            previous_rank = rank

    def values(self, population, weights=None):
        population = np.asarray(population, dtype=float)
        if (population.ndim != 1 or not len(population) or not np.isfinite(population).all()
                or np.any(population < 0)):
            raise ValueError('Cohort population must contain finite nonnegative durations')
        if weights is None:
            weights = np.full(len(population), 1./len(population))
        weights = np.asarray(weights, dtype=float)
        if (weights.shape != population.shape or not np.isfinite(weights).all()
                or np.any(weights < 0) or not np.isclose(weights.sum(), 1., atol=1e-12, rtol=0.)):
            raise ValueError('Cohort population weights must match and sum to one')
        order = np.argsort(population, kind='stable')
        cumulative = np.cumsum(weights[order])
        cumulative[-1] = 1.  # Numerical summation only; not a tail truncation policy.
        indices = np.minimum(np.searchsorted(cumulative, self.uniform_order_statistics), len(order)-1)
        sampled = population[order[indices]]
        return np.column_stack([(1-weight)*sampled[:, lo]+weight*sampled[:, hi]
                                for lo, hi, weight in self.interpolations])
