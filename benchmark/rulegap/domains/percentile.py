"""Percentile domain: raw request logs; readings differ on which samples count,
which of the nine Hyndman-Fan definitions is meant, and what 'exceeds' means."""
import math

import numpy as np

# Hyndman & Fan (1996) types 1-9 under numpy's method names.
METHODS = ['inverted_cdf', 'averaged_inverted_cdf', 'closest_observation',
           'interpolated_inverted_cdf', 'hazen', 'weibull', 'linear',
           'median_unbiased', 'normal_unbiased']
DESCRIBE = {
    'inverted_cdf': 'the smallest sample such that at least that share of samples is at or below it',
    'averaged_inverted_cdf': 'the inverse of the empirical distribution, averaging the two samples at a step',
    'closest_observation': 'the sample whose rank is nearest to n times p',
    'interpolated_inverted_cdf': 'the value at position n times p, interpolating between ranked samples',
    'hazen': 'the value at position n times p plus one half, interpolating between ranked samples',
    'weibull': 'the value at position (n + 1) times p, interpolating between ranked samples',
    'linear': 'the value at position (n - 1) times p plus 1, interpolating between ranked samples',
    'median_unbiased': 'the value at position (n + 1/3) times p plus 1/3, interpolating between ranked samples',
    'normal_unbiased': 'the value at position (n + 1/4) times p plus 3/8, interpolating between ranked samples',
}
Z90 = 1.2815515655446004


def numpy_methods():
    """Nine readings. Prior: half the mass on numpy/R's default (linear), the
    rest spread evenly (assumption recorded in the spec)."""
    out = []
    for i, m in enumerate(METHODS, 1):
        out.append(dict(id=m, prior=0.5 if m == 'linear' else 0.5 / 8,
            printed=f'{DESCRIBE[m]} (Hyndman-Fan type {i})',
            sources=[dict(kind='author_catalog', file='numpy_percentile.html', quote=NUMPY_LIST,
                          url='https://numpy.org/doc/stable/reference/generated/numpy.percentile.html',
                          note='Documents the calculation method; does not validate this whole interpretation.')],
            expr={'feature': 'percentile', 'args': {'xs': {'term': 'SAMPLES'},
                  'q': {'const': 'q'}, 'method': m}}))
    return out


def latencies(situation, action, which):
    reqs = situation['requests']
    if which == 'success':
        reqs = [r for r in reqs if r['status'] == 'ok']
    elif which == 'last_window':
        reqs = sorted(reqs, key=lambda r: r['ts'])[-situation['window_n']:]
    return [r['latency_ms'] for r in reqs]


def percentile(situation, action, xs, q, method):
    if not xs:
        return None
    return float(np.percentile(xs, q, method=method))


def abs_diff(situation, action, a, b):
    return None if a is None or b is None else abs(a - b)


def share_below(situation, action, xs, threshold):
    return None if not xs else sum(x < threshold for x in xs) / len(xs)


NUMPY_LIST = "‘inverted_cdf’ ‘averaged_inverted_cdf’ ‘closest_observation’ ‘interpolated_inverted_cdf’ ‘hazen’ ‘weibull’ ‘linear’ (default) ‘median_unbiased’ ‘normal_unbiased’"
DEFAULTS = {
    'linear': [dict(kind='software_default', file='numpy_percentile.html', quote="method = 'linear'"),
               dict(kind='software_default', file='r_quantile.html', quote='the default type = 7')],
    'weibull': [dict(kind='software_default', file='r_quantile.html', quote='This is used by Minitab and by SPSS.'),
                dict(kind='software_default', file='excel_percentile_exc.html',
                     quote='If k is not a multiple of 1/(n + 1), PERCENTILE.EXC interpolates')],
}


def slo_meets():
    """Readings of '90% of requests faster than T': the literal share count, and
    'the 90th percentile is below T' under each published percentile definition."""
    out = [dict(id='share_count', printed='at least that share of the requests, counted one by one, were faster than the threshold',
        expr={'>=': [{'feature': 'share_below', 'args': {'xs': {'term': 'SAMPLES'}, 'threshold': {'const': 'threshold_ms'}}}, {'const': 'share'}]},
        sources=[dict(kind='text_literal', file='sre_workbook_implementing_slos.html', quote='90% of requests faster than 450 ms'),
                 dict(kind='practice_verdict', file='sre_workbook_implementing_slos.html',
                      quote='The proportion of requests that were faster than some threshold.')])]
    for i, m in enumerate(METHODS, 1):
        out.append(dict(id=m, printed=f'the percentile at that level, computed as {DESCRIBE[m]}, is below the threshold',
            expr={'<': [{'feature': 'percentile', 'args': {'xs': {'term': 'SAMPLES'}, 'q': {'const': 'q'}, 'method': m}}, {'const': 'threshold_ms'}]},
            sources=[dict(kind='author_catalog', file='numpy_percentile.html', quote=NUMPY_LIST)] + DEFAULTS.get(m, [])))
    return out


def build_case(samples, true_p90, statuses=None, window_n=None):
    n = len(samples)
    return dict(requests=[dict(ts=i, latency_ms=float(x), status=(statuses or ['ok'] * n)[i])
                          for i, x in enumerate(samples)],
                window_n=window_n or n, _true_p90=float(true_p90))


def _draw(rng, i, params):
    ns = params.get('n_samples', 50)
    n = ns[i % len(ns)] if isinstance(ns, list) else ns
    median, sigma = params.get('median', 300), params.get('sigma', 0.5)
    if isinstance(median, list):          # vary the true service level across cases
        median = median[(i // 3) % len(median)]
    xs = np.round(rng.lognormal(math.log(median), sigma, n), 1)
    # Errors are likelier on slow requests (timeouts); marginal latencies stay lognormal.
    p_err = np.where(xs > 2 * median, params.get('p_error_slow', 0.3), params.get('p_error', 0.02))
    statuses = ['error' if u < p else 'ok' for u, p in zip(rng.random(n), p_err)]
    window = max(3, int(n * params.get('window_frac', 0.5)))
    return build_case(xs.tolist(), median * math.exp(sigma * Z90), statuses, window)


def lognormal_latencies(rng, i, params, spec):
    return _draw(rng, i, params)


def disagreeing_latencies(rng, i, params, spec):
    """Rejection-sample logs on which the nine definitions straddle the threshold."""
    thr, q = spec.raw['constants']['threshold_ms'], spec.raw['constants']['q']
    for _ in range(2000):
        s = _draw(rng, i, params)
        xs = [r['latency_ms'] for r in s['requests']]
        vals = [np.percentile(xs, q, method=m) for m in METHODS]
        if min(vals) <= thr < max(vals):
            return s
    raise ValueError('no disagreeing sample found')


def candidate_actions(spec, situation):
    return [dict(kind='report', p90_ms=None, verdict=v) for v in ('failing', 'passing')]


DOMAIN = dict(
    features=dict(latencies=latencies, percentile=percentile, abs_diff=abs_diff, share_below=share_below),
    generators=dict(lognormal_latencies=lognormal_latencies, disagreeing_latencies=disagreeing_latencies),
    reading_sets=dict(numpy_methods=numpy_methods, slo_meets=slo_meets),
    candidate_actions=candidate_actions, build_case=build_case,
)


ROLE = 'You are the on-call engineer preparing the weekly service health report.'
TOOLS = {
    'report': dict(desc='File the health report: the computed value in ms and the verdict.', args=dict(p90_ms='number', verdict='string')),
    'ask': dict(desc='Put a question to your team lead. The report then waits for their answer.', args=dict(question='string')),
    'done': dict(desc='Finish.', args={}),
}
DOMAIN.update(role=ROLE, tools=TOOLS, apply=lambda situation, action: situation,
              completed=lambda s0, s: None)
