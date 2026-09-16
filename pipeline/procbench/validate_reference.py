"""Independent importance-integration reference for a weak-data posterior.

The reference draws from the prior and directly evaluates a scalar Student-t
interval probability, without invoking the model's likelihood or MCMC kernels.
Useful complement to recovery/SBC; not a calibration claim for the full system.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import pathlib

import numpy as np
from scipy.stats import t as student_t

from .bayes_hierarchy import Config, HierarchicalModel
from .latent_gaussian import diagnostics
from .run_hierarchical import write
from .validate_hierarchy import generated_evidence


def quantities(z, model):
    cfg = model.cfg
    p = model.processes[0]
    gi = p.global_indices[0]
    h = z[:, model.hyper]
    location = np.log(cfg.global_median) + cfg.global_log_sd * h[:,0]
    agency = np.abs(h[:,1]) * cfg.agency_scale * z[:, model.za[model.agencies[gi]]]
    task = np.abs(h[:,2]) * cfg.task_scale * z[:, model.zt[model.tasks[gi]]]
    mu = location + agency + task + np.abs(h[:,3]) * cfg.step_scale * z[:, model.zi[gi]]
    sigma, common = .1 + .75 * np.abs(h[:,4]), .35 * np.abs(h[:,5])
    case = z[:, p.zcase].reshape((len(z), *p.case_shape))[:,0,:]
    source = cfg.source_bias_sd * z[:, model.zs[0]]
    reported = mu + sigma * case[:,0] + common * case[:,p.n] + source
    return {'global_location': location, 'step_log_median': mu, 'agency_effect': agency,
            'source_offset': source, 'case_sigma': sigma}, reported


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--prior-draws', type=int, default=300000)
    ap.add_argument('--draws', type=int, default=6000)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    e, _ = generated_evidence(n_cases=1, with_totals=False)
    e['measurements'] = e['measurements'][:1]
    e['measurements'][0].update(value=12., lower=None, upper=None)
    cfg = Config(chains=4, warmup=1000, draws=args.draws, thin=1,
                 max_unseen=0, unseen_mean=0, population_size=16, seed=56119)
    model = HierarchicalModel([e], cfg)
    rng = np.random.default_rng(851017)
    prior = rng.normal(size=(args.prior_draws, model.layout.size))
    reference, location = quantities(prior, model)
    def interval(sd):
        return student_t.cdf((np.log(12.5)-location)/sd,df=4) - student_t.cdf((np.log(11.5)-location)/sd,df=4)
    weight = (1-cfg.outlier_probability)*interval(cfg.report_sd) + cfg.outlier_probability*interval(2.)
    weight /= weight.sum()
    ess = float(1 / np.sum(weight**2))
    source = pathlib.Path(__file__).parent
    names = ('validate_reference.py','bayes_hierarchy.py','latent_gaussian.py','evidence_contract.py','schedule_kernel.py')
    write(out/'manifest.json', dict(config=asdict(cfg), prior_draws=args.prior_draws,
        source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names}))
    for name in names:
        path = out/'source'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((source/name).read_bytes())
    z,s,ll,_ = model.sample()
    sampled,_ = quantities(z.reshape((-1,z.shape[-1])),model)
    result = {}
    for name, v in reference.items():
        mean = float(weight @ v)
        se = float(np.sqrt(np.sum(weight**2*(v-mean)**2)))
        values = sampled[name]
        diag = diagnostics(values.reshape(z.shape[:2]))
        mcse = float(values.std(ddof=1) / np.sqrt(diag['ess_bulk']))
        result[name] = dict(reference_mean=mean, reference_mcse=se, mcmc_mean=float(values.mean()),
            mcmc_mcse_approx=mcse, standardized_difference=float((values.mean()-mean)/np.hypot(se,mcse)),
            diagnostics=diag)
    write(out/'reference.json', dict(prior_importance_ess=ess, comparisons=result,
        caveat='Weak-data independent integration; Monte Carlo SE approximations, not full-model calibration'))
    np.savez_compressed(out/'draws.npz', z=z,structure=s,log_likelihood=ll)
    print(json.dumps({'importance_ess':ess,'comparisons':result},indent=2))


if __name__ == '__main__':
    main()
