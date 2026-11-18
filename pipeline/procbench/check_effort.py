"""Audit a separately fitted work-hour hierarchy without converting elapsed time.

Adds hyperparameter/source/step diagnostics to the original aggregate-hours check.
Original artifacts remain unchanged. A two-hour typical-cost estimate does not
identify a precise arithmetic workload mean or its allocation across agencies.
"""
import argparse
import hashlib
import json
import pathlib

import numpy as np
from scipy.special import expit

from .bayes_hierarchy import Config, HierarchicalModel
from .evidence_support import burden_support
from .latent_gaussian import diagnostics, summary
from .infra.manifest import write


def expected_work_by_activity(model, process, z, params=None):
    """Exact initial-route first moment under the fitted independence model.

    Linearity of expectation needs no independence between activity durations.
    Gates/outcomes are independent of duration residuals in this implementation.
    This computes work, never an elapsed critical-path expectation.
    """
    if model.cfg.channel not in {'payer_work','agency_work'} or model.cfg.max_unseen:
        raise ValueError('Analytic work summary requires a represented-work model without hidden stages')
    params = model.parameters(z) if params is None else params
    inclusion = process.pre.astype(float)
    gate_p = expit(1.5*z[process.zg])
    for i,g in enumerate(process.gates):
        if g>=0:
            inclusion[i] *= gate_p[g]
    inclusion[process.decisions] = process.outcome_probabilities(z,model.cfg)
    log_means = params['mu'][process.global_indices]+.5*(params['sigma']**2+params['common']**2)
    with np.errstate(over='raise',invalid='raise'):
        return inclusion*process.channel_mask*np.exp(log_means)


def effort_diagnostics(model,z,structures,likelihood):
    flat = z.reshape((-1,z.shape[-1]))
    shape = z.shape[:2]
    params = [model.parameters(x) for x in flat]
    values = {'log_likelihood':likelihood}
    for key in ('location','agency_sd','task_sd','step_sd','sigma','common'):
        values[f'hyper:{key}'] = np.array([p[key] for p in params]).reshape(shape)
    for i,name in enumerate(model.sources):
        values[f'source_bias:{name}'] = np.array([p['source_bias'][i] for p in params]).reshape(shape)
    for i,name in enumerate(model.agency_names):
        values[f'actor_effect:{name}'] = np.array([p['agency'][i] for p in params]).reshape(shape)
    for i,(pid,activity) in enumerate(model.activities):
        values[f'step:{pid}:{activity["id"]}'] = np.array([p['mu'][i] for p in params]).reshape(shape)
    for pi,process in enumerate(model.processes):
        for gi in range(len(process.graphs)):
            values[f'graph:{process.id}:{gi}'] = (structures[:,:,pi,0]==gi).astype(float)
        for i,key in enumerate(process.gate_keys):
            values[f'gate_logit:{process.id}:{key}'] = z[:,:,process.zg[i]]
        for i in range(len(process.zo)):
            values[f'outcome_logit_coordinate:{process.id}:{i}'] = z[:,:,process.zo[i]]
    return {name:diagnostics(x) for name,x in values.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--out',required=True)
    args = ap.parse_args(argv)
    root,out = pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh work-hour diagnostic directory')
    posterior = json.loads((root/'posterior.json').read_text())
    evidence = json.loads((root/'evidence.json').read_text())
    support = burden_support(evidence)
    reports = {}
    for channel in ('payer_work','agency_work'):
        report = posterior.get('effort',{}).get(channel,{})
        if not report.get('has_work_hour_evidence'):
            reports[channel] = dict(status='no fitted work-hour likelihood',reported=report)
            continue
        cfg = Config(**report['config'])
        model = HierarchicalModel(evidence,cfg)
        raw = np.load(root/f'{channel}.npz')
        z,s,ll = raw['z'],raw['structure'],raw['log_likelihood']
        selected = np.unique(np.linspace(0,z.shape[1]-1,50).astype(int))
        error = max(abs(model.log_likelihood(z[c,i],s[c,i])-ll[c,i])
                    for c in range(len(z)) for i in selected)
        if not np.isfinite(error) or error > 1e-7:
            raise ValueError('Work-hour likelihood changed: cannot check this saved fit')
        diags = effort_diagnostics(model,z,s,ll)
        flat = z.reshape((-1,z.shape[-1]))
        programs = {}
        for process in model.processes:
            pid = process.id
            original = report['programs'][pid]
            work = np.array([expected_work_by_activity(model,process,x) for x in flat])
            totals = work.sum(axis=1)
            diag = diagnostics(np.log(np.maximum(totals,1e-12)).reshape(z.shape[:2]))
            diags[f'expected_hours:{pid}'] = diag
            by_agency = {}
            for actor in process.actor.values():
                if actor['role']=='agency':
                    ids = [i for i,a in enumerate(process.activities) if a['actor_id']==actor['id']]
                    if ids:
                        amounts = work[:,ids].sum(axis=1)
                        by_agency[actor['name']] = summary(amounts)
                        if channel=='agency_work':
                            diags[f'expected_agency_hours:{pid}:{actor["id"]}'] = diagnostics(
                                np.log(np.maximum(amounts,1e-12)).reshape(z.shape[:2]))
            unassigned = [i for i,a in enumerate(process.activities) if process.actor[a['actor_id']]['role']!='agency']
            programs[pid] = dict(original,expected_hours_per_initial_case=summary(totals),
                hours_by_agency=by_agency if channel=='agency_work' else {},
                agency_hours_without_resolved_owner=summary(work[:,unassigned].sum(axis=1)) if channel=='agency_work' else None,
                diagnostics=diag,direct_evidence_support=support[pid][channel],
                original_quadrature_expected_hours=original['expected_hours_per_initial_case'],
                aggregation='Analytic conditional mean: sum of route-weighted lognormal means; likelihood and posterior draws unchanged')
        flagged = {k:v for k,v in diags.items() if v['rhat'] is None or v['rhat']>1.01
                   or v['ess_bulk']<400 or v['ess_tail']<200}
        reports[channel] = dict(status='fitted',diagnostics=diags,diagnostics_flagged=flagged,
            monitored_converged=not flagged,saved_likelihood_max_error=error,
            programs=programs,
            qualification='Conditional numerical convergence is not identification of labor; observed typical hours do not precisely identify arithmetic means or agency allocations')
    write(out/'checks.json',reports)
    source = pathlib.Path(__file__).parent
    write(out/'manifest.json',dict(base_run=str(root),
        posterior_sha256=hashlib.sha256((root/'posterior.json').read_bytes()).hexdigest(),
        source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest()
                       for n in ('check_effort.py','bayes_hierarchy.py','latent_gaussian.py','evidence_support.py')}))
    for channel,r in reports.items():
        print(json.dumps(dict(channel=channel,status=r['status'],
            converged=r.get('monitored_converged'),flagged=r.get('diagnostics_flagged'))),flush=True)


if __name__ == '__main__':
    main()
