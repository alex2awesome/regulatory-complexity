"""Source/claim posterior checks from saved draws, with no benchmark access.

These are in-sample diagnostics, not held-out predictive validation. They expose
which observations the robust likelihood regards as contradictory and which
source offsets the posterior uses to reconcile the evidence.
"""
import argparse
import hashlib
import json
import math
import pathlib

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel, log_interval
from .latent_gaussian import summary
from .infra.manifest import write


def clock_alternative_probability(bounds, prediction, alternative, scale, contamination):
    """Conditional probability of the second clock in the fitted equal mixture.

    This diagnoses an existing posterior; it neither selects a new clock nor
    refits the model. Both clocks integrate the same reporting-contamination model.
    """
    scores = [np.logaddexp(math.log1p(-contamination) +
                          log_interval(bounds[:,0],bounds[:,1],location,scale),
                          math.log(contamination) +
                          log_interval(bounds[:,0],bounds[:,1],location,2.))
              for location in (prediction,alternative)]
    return np.exp(scores[1]-np.logaddexp(*scores))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--stride', type=int, default=24)
    args = ap.parse_args(argv)
    if args.stride < 1:
        raise ValueError('Stride must be positive')
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving prior check; use a fresh directory')
    manifest = json.loads((root / 'manifest.json').read_text())
    cfg = Config(**manifest['config'])
    model = HierarchicalModel(json.loads((root / 'evidence.json').read_text()), cfg)
    draws = np.load(root / 'draws.npz')
    selected = draws['z'][:, ::args.stride]
    flat = selected.reshape((-1, selected.shape[-1]))
    ss = draws['structure'][:, ::args.stride].reshape((-1, len(model.processes), 2))
    saved = draws['log_likelihood'][:, ::args.stride].reshape(-1)
    checked = np.unique(np.linspace(0,len(flat)-1,min(200,len(flat))).astype(int))
    differences = [abs(model.log_likelihood(flat[i],ss[i])-saved[i]) for i in checked]
    error = max(differences)
    if not np.all(np.isfinite(differences)) or error > 1e-7:
        raise ValueError('Saved likelihood disagrees: cannot check a different posterior target')
    probs, centers, alternate_centers, clock_probs, source = [], [], [], [], []
    for x, s in zip(flat, ss):
        pred, scale, alt = model.predictions(x, s, include_alternatives=True)
        bounds = model.bounds
        usual = np.logaddexp(log_interval(bounds[:,0], bounds[:,1], pred, scale),
                             log_interval(bounds[:,0], bounds[:,1], alt, scale)) - math.log(2.)
        unusual = np.logaddexp(log_interval(bounds[:,0], bounds[:,1], pred, 2.),
                               log_interval(bounds[:,0], bounds[:,1], alt, 2.)) - math.log(2.)
        numerator = math.log(cfg.outlier_probability) + unusual
        denominator = np.logaddexp(math.log1p(-cfg.outlier_probability) + usual, numerator)
        probs.append(np.exp(numerator - denominator))
        centers.append(np.exp(pred))
        alternate_centers.append(np.exp(alt))
        clock_probs.append(clock_alternative_probability(bounds,pred,alt,scale,cfg.outlier_probability))
        source.append(np.exp(model.parameters(x)['source_bias']))
    probs, centers, source = np.asarray(probs), np.asarray(centers), np.asarray(source)
    alternate_centers, clock_probs = np.asarray(alternate_centers), np.asarray(clock_probs)
    rows = []
    for i, (pid, m) in enumerate(model.observations):
        ambiguous = cfg.channel=='elapsed' and m['scope']=='process' and m['start']=='unspecified'
        rows.append({'program_id': pid, 'measurement_id': m['id'], 'source_family': m['source_family'],
            'case_id': m['case_id'], 'scope': m['scope'], 'statistic': m['statistic'],
            'clock_start':m['start'],'clock_end':m['end'],
            'observed_calendar_days_interval': np.exp(m['interval']).tolist(),
            'mean_posterior_contamination_probability': float(probs[:,i].mean()),
            'fitted_report_center_days': summary(centers[:,i]),
            'alternate_submission_start_center_days':summary(alternate_centers[:,i]) if ambiguous else None,
            'mean_posterior_submission_start_probability':float(clock_probs[:,i].mean()) if ambiguous else None,
            'quote': m['quote'], 'interpretation': m['interpretation']})
    result = {'run': str(root), 'n_draws_used': len(flat),
        'claims': sorted(rows, key=lambda r: -r['mean_posterior_contamination_probability']),
        'source_multipliers': {name: summary(source[:,i]) for i, name in enumerate(model.sources)},
        'qualification': 'In-sample posterior checks, not a refit. High contamination probability is a model diagnostic, not proof the source is false. Centers include source offsets. Ambiguous starts report both fitted clock centers and their conditional posterior probability under the unchanged equal-prior mixture; unspecified endpoints still lack an explicit completion/censoring model.'}
    write(out / 'checks.json', result)
    write(out / 'manifest.json', {'base_run':str(root),'saved_likelihood_max_error':error,
        'evidence_sha256':hashlib.sha256((root/'evidence.json').read_bytes()).hexdigest(),
        'source_sha256':{name:hashlib.sha256((pathlib.Path(__file__).parent/name).read_bytes()).hexdigest()
                         for name in ('check_hierarchy.py','bayes_hierarchy.py','evidence_contract.py','schedule_kernel.py')}})
    print(json.dumps({'largest_conflicts': [{k: r[k] for k in ('program_id','measurement_id','mean_posterior_contamination_probability')}
                                            for r in result['claims'][:10]],
                      'source_multipliers': result['source_multipliers']}), flush=True)


if __name__ == '__main__':
    main()
