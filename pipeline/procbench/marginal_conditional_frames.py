"""Integrate independent case durations in the existing guarded V6 frame.

This is the marginal target of VisitHierarchy, not another process model. The
ordinary frame validator is mandatory: one report per independent case, one
operation, zero shared/source effects. Richer V6 inputs must use the full model.
Student-t(4) reporting is retained via its Gamma normal-precision mixture.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import math
import multiprocessing
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr, ndtri, roots_legendre

from .approximation_checks import likelihood_weight_check
from .bayes_trace_hierarchy import Config, VisitHierarchy, duration_log_probability
from .infra.manifest import RunManifest, digest, write
from .latent_gaussian import diagnostics, elliptical_slice, information_report, summary


INTEGRATION_KIND = 'v6-independent-conditional-cases/1'
LOG_PRECISION_LIMITS = (-36., 8.)


class MarginalConditionalFrame:
    """Same V6 prior/likelihood with nuisance case Gaussians integrated out."""

    def __init__(self, data, cfg: Config, quadrature_size=128):
        if (isinstance(quadrature_size, bool) or not isinstance(quadrature_size, int)
                or quadrature_size < 32):
            raise ValueError('Case quadrature requires an integer size of at least32')
        full = VisitHierarchy(data, cfg)
        if len(full.conditional_case_frames) != 1:
            raise ValueError('Case marginalization requires the guarded conditional-case frame')
        self.data, self.cfg = data, cfg
        self.conditional_case_frames = full.conditional_case_frames
        self.programs = full.programs
        self.full_dimensions = full.layout.size
        self.full_coordinate_indices = [int(full.location[0])]
        if cfg.case_log_sd_prior:
            self.full_coordinate_indices.append(int(full.sigma[0]))
        self.layout = SimpleNamespace(size=len(self.full_coordinate_indices))
        self.quadrature_size = quadrature_size
        nodes, weights = roots_legendre(quadrature_size)
        lo, hi = LOG_PRECISION_LIMITS
        log_precision = (lo + hi)/2 + (hi-lo)/2 * nodes
        # lambda ~ Gamma(2, rate=2), d lambda = exp(ell) d ell.
        self.weights = weights*(hi-lo)/2 * np.exp(
            math.log(4.) + 2*log_precision - 2*np.exp(log_precision))
        self.inverse_precision = np.exp(-log_precision)
        observations = self.programs[0]['observations']
        self.lower = np.array([math.log(o['lower']) if o['lower'] > 0
                               else -math.inf for o in observations])
        self.upper = np.array([math.log(o['upper']) if o['upper'] is not None
                               else math.inf for o in observations])
        self.inference = dict(kind=INTEGRATION_KIND, quadrature_size=quadrature_size,
            log_precision_limits=list(LOG_PRECISION_LIMITS),
            case_latents='integrated_not_imputed',
            inactive_priors='integrated_not_fixed_as_learned_effects',
            sampler='standard_normal_joint_and_coordinate_elliptical_slice',
            predictions='analytic_lognormal_conditional_frame_quantiles')

    def parameters(self, z):
        z = np.asarray(z, dtype=float)
        if z.shape != (self.layout.size,) or not np.isfinite(z).all():
            raise ValueError('Marginal state must match its finite whitened coordinates')
        with np.errstate(over='ignore', invalid='ignore'):
            mu = math.log(self.cfg.elapsed_prior_median) + self.cfg.location_sd*z[0]
        if not math.isfinite(mu):
            raise FloatingPointError('Numerically nonfinite marginal log location')
        spread_coordinate = z[1] if self.cfg.case_log_sd_prior else 0.
        sigma = math.exp(math.log(self.cfg.case_log_sd_median)
                         + self.cfg.case_log_sd_prior*spread_coordinate)
        return float(mu), sigma

    def _component_probabilities(self, mu, sigma, scale):
        sd = np.sqrt(sigma*sigma + scale*scale*self.inverse_precision)
        lo, hi = (self.lower[:, None]-mu)/sd, (self.upper[:, None]-mu)/sd
        # Preserve both tails without subtracting two CDF values near one.
        probabilities = np.where(lo > 0, ndtr(-lo)-ndtr(-hi), ndtr(hi)-ndtr(lo))
        return np.clip(probabilities, 0., 1.) @ self.weights

    def log_likelihood(self, z, structures=None, parts=False):
        if structures is not None and (np.shape(structures) != (1,)
                or np.asarray(structures)[0] != 0):
            raise ValueError('The guarded marginal frame has exactly one fixed route')
        try:
            mu, sigma = self.parameters(z)
            if not math.isfinite(sigma) or sigma*sigma == math.inf:
                raise FloatingPointError('Numerically nonfinite marginal case variance')
            probabilities = self._component_probabilities(mu, sigma, self.cfg.report_sd)
            if self.cfg.contamination:
                broad = self._component_probabilities(mu, sigma, 2.)
                probabilities = ((1-self.cfg.contamination)*probabilities
                                 + self.cfg.contamination*broad)
            values = np.log(np.clip(probabilities, 1e-300, 1.))
            if parts:
                p = self.programs[0]
                return {p['id']+':'+o['id']: float(value)
                        for o, value in zip(p['observations'], values)}
            return float(values.sum())
        except (OverflowError, FloatingPointError):
            if parts:
                raise
            return -math.inf

    def reference_log_likelihood(self, z):
        """Independent adaptive integral of V6's original case-report kernel.

        Uses Gaussian-case integration, NOT the Gamma precision representation.
        The omitted standard-normal mass beyond +/-12 is below4e-33 per case.
        This finite reference check is not a uniform relative-error certificate.
        """
        mu, sigma = self.parameters(z)
        result = 0.
        for o, lo, hi in zip(self.programs[0]['observations'], self.lower, self.upper):
            points = sorted({float((bound-mu)/sigma) for bound in (lo, hi)
                             if math.isfinite(bound) and abs((bound-mu)/sigma) < 12})

            def integrand(case_z):
                ll = duration_log_probability(o['lower'], o['upper'],
                    math.exp(mu + sigma*case_z), scale=self.cfg.report_sd,
                    contamination=self.cfg.contamination)
                return math.exp(float(ll)-case_z*case_z/2)/math.sqrt(2*math.pi)

            value, _ = quad(integrand, -12., 12., points=points, epsabs=1e-12,
                            epsrel=1e-9, limit=200)
            result += math.log(max(value, 1e-300))
        return result

    def sample_chain(self, chain_index, progress=None):
        cfg = self.cfg
        rng = np.random.default_rng(cfg.seed+104729*chain_index)
        state = rng.normal(size=self.layout.size)
        value = self.log_likelihood(state)
        states = np.empty((cfg.draws, self.layout.size))
        likelihood = np.empty(cfg.draws)
        blocks = [np.arange(self.layout.size)]
        if self.layout.size > 1:
            blocks.extend(np.array([i]) for i in range(self.layout.size))
        calls = 1
        for iteration in range(cfg.warmup+cfg.draws):
            for block in blocks:
                state, value, used = elliptical_slice(
                    state, block, self.log_likelihood, value, rng)
                calls += used
            if iteration >= cfg.warmup:
                states[iteration-cfg.warmup] = state
                likelihood[iteration-cfg.warmup] = value
            if progress and (iteration == 0 or (iteration+1) % 500 == 0):
                progress(dict(chain=chain_index+1, iteration=iteration+1,
                              calls=calls, log_likelihood=value))
        return states, likelihood, calls

    def report(self, states, likelihood):
        cfg = self.cfg
        mu = math.log(cfg.elapsed_prior_median) + cfg.location_sd*states[:, :, 0]
        sigma = cfg.case_log_sd_median*np.exp(cfg.case_log_sd_prior*states[:, :, 1]) \
            if cfg.case_log_sd_prior else np.full(mu.shape, cfg.case_log_sd_median)
        median, p90 = np.exp(mu), np.exp(mu+ndtri(.9)*sigma)
        quantities = {'log_likelihood': likelihood, 'elapsed:log_location': mu,
                      'modeled_work_end_median_days': median,
                      'modeled_work_end_p90_days': p90}
        if cfg.case_log_sd_prior:
            quantities['elapsed:case_log_sd'] = sigma
        quantities.update({f'coordinate:{i}': states[:, :, i]
                           for i in range(self.layout.size)})
        diags = {name: diagnostics(values) for name, values in quantities.items()}
        flagged = {name: row for name, row in diags.items() if row['rhat'] is None
                   or row['rhat'] > 1.01 or row['ess_bulk'] < 400 or row['ess_tail'] < 200}
        p = self.programs[0]
        return dict(config=asdict(cfg), inference=self.inference,
            dimensions=self.layout.size, original_sampled_dimensions=self.full_dimensions,
            posterior_converged=not flagged, diagnostics=diags, diagnostics_flagged=flagged,
            fixed_quantities=({} if cfg.case_log_sd_prior else
                {'elapsed:case_log_sd': dict(value=cfg.case_log_sd_median,
                    mcmc_diagnostics='not_applicable_fixed_by_declared_config')}),
            identification=self.information_report(states, sampling_converged=not flagged),
            programs={p['id']: dict(clock_estimand=p['clock_estimand'],
                conditional_case_frame=self.conditional_case_frames[p['id']],
                metrics={'modeled_work_end_median_days': summary(median),
                         'modeled_work_end_p90_days': summary(p90)},
                log_location=summary(mu), case_log_sd=summary(sigma))},
            qualification='Same conditional report-frame V6 target after independent-case '
                'marginalization; not population transport, calibrated selection, source '
                'trust or intrinsic agency delay. No individual-case posterior is reported.')

    def information_report(self, states, sampling_converged=None):
        blocks = {'location': [0]}
        if self.layout.size == 2:
            blocks['case_sigma'] = [1]
        return information_report(states, blocks, sampling_converged=sampling_converged)


def _worker(data, cfg, nodes, index):
    model = MarginalConditionalFrame(data, cfg, nodes)
    return model.sample_chain(index)


def run_marginal_frame(data, cfg, out, inputs, *, quadrature_size=128, workers=2,
                       preflight=False):
    """Existing V6 runner's explicit marginal path; immutable fresh outputs."""
    out = Path(out)
    if out.exists() or workers < 1:
        raise ValueError('Choose a fresh marginal run directory and positive workers')
    model = MarginalConditionalFrame(data, cfg, quadrature_size)
    record = RunManifest(out, dict(config=asdict(cfg), inference=model.inference,
        dimensions=model.layout.size, input_sha256={str(p): digest(Path(p).read_bytes())
                                                  for p in inputs}),
        operation='v6.marginal_frame_preflight' if preflight else 'v6.marginal_frame_fit',
        inputs=inputs, config=dict(model=asdict(cfg), inference=model.inference),
        seeds=dict(seed=cfg.seed, chain_stride=104729), hidden_truth_read=False,
        source_root=Path(__file__).parent, sources=['run_visit_hierarchy.py'])
    write(out/'data.json', data)
    if preflight:
        result = dict(sampling_performed=False, dimensions=model.layout.size,
            original_sampled_dimensions=model.full_dimensions, inference=model.inference,
            conditional_case_frames=model.conditional_case_frames,
            cases=len(model.programs[0]['observations']),
            log_likelihood_at_prior_mean=model.log_likelihood(np.zeros(model.layout.size)))
        write(out/'preflight.json', result)
        record.complete(sampling_performed=False,
                        report_sha256=digest((out/'preflight.json').read_bytes()))
        return result
    with ProcessPoolExecutor(max_workers=workers,
            mp_context=multiprocessing.get_context('spawn')) as pool:
        results = list(pool.map(_worker, [data]*cfg.chains, [cfg]*cfg.chains,
                                [quadrature_size]*cfg.chains, range(cfg.chains)))
    states = np.stack([r[0] for r in results])
    likelihood = np.stack([r[1] for r in results])
    structures = np.zeros((*states.shape[:2], 1), dtype=int)
    np.savez_compressed(out/'draws.npz', z=states, structures=structures,
                        log_likelihood=likelihood)
    report = model.report(states, likelihood)
    finer = MarginalConditionalFrame(data, cfg, quadrature_size*2)
    flat = states.reshape(-1, model.layout.size)
    checked = np.linspace(0, len(flat)-1, min(256, len(flat)), dtype=int)
    changes = [finer.log_likelihood(flat[i])-model.log_likelihood(flat[i]) for i in checked]
    reference_indices = np.linspace(0, len(flat)-1, min(8, len(flat)), dtype=int)
    reference_changes = [model.reference_log_likelihood(flat[i])
                         - model.log_likelihood(flat[i]) for i in reference_indices]
    precision = likelihood_weight_check(changes)
    reference = likelihood_weight_check(reference_changes)
    reference['max_absolute_difference_gate'] = 1e-5
    reference['acceptable'] = (reference['acceptable']
                              and reference['max_absolute_log_likelihood_change'] <= 1e-5)
    report['precision'] = dict(posterior_weight_check=precision,
        independent_gaussian_case_reference=reference,
        base_quadrature_size=quadrature_size, refined_quadrature_size=quadrature_size*2,
        likelihood_acceptable=precision['acceptable'] and reference['acceptable'],
        predictions_acceptable=True,
        prediction_qualification='Analytic lognormal functionals; no population grid.')
    report['numerically_usable'] = (report['posterior_converged']
                                   and report['precision']['likelihood_acceptable'])
    write(out/'posterior.json', report)
    record.complete(calls=[r[2] for r in results],
        posterior_sha256=digest((out/'posterior.json').read_bytes()),
        draws_sha256=digest((out/'draws.npz').read_bytes()))
    return report
