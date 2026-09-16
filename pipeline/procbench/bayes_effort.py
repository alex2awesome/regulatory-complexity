"""Separate work-hour hierarchies; waiting-time evidence never supplies labor.

Hours and elapsed days are distinct likelihoods. This is deliberately a modular
extension: no uncalibrated deterministic conversion or cross-channel correlation.
"""
from dataclasses import asdict, replace
import numpy as np

from .bayes_hierarchy import HierarchicalModel
from .latent_gaussian import diagnostics, summary


def fit_effort(evidences, config, progress=None):
    result, arrays = {}, {}
    for channel in ('payer_work', 'agency_work'):
        if not any(m['metric'] == channel and m['statistic'] not in {'statutory_cap', 'target'}
                   and m['scope'] != 'standing' for e in evidences for m in e['measurements']):
            result[channel] = {'identified': False, 'hours': None, 'reason': 'no eligible work-hour measurements'}
            continue
        # Hours have their own stated weak prior, not the seven-day timing prior.
        cfg = replace(config, channel=channel, global_median=.5, max_unseen=0, unseen_mean=0.)
        model = HierarchicalModel(evidences, cfg)
        if not model.observations:
            result[channel] = {'identified': False, 'hours': None,
                               'reason': 'work descriptions have no eligible numerical observations'}
            continue
        z, structure, ll, _ = model.sample(progress)
        flat, ss = z.reshape((-1, z.shape[-1])), structure.reshape((-1, len(evidences), 2))
        params = [model.parameters(x) for x in flat]
        programs = {}
        for pi, p in enumerate(model.processes):
            per_case, per_agency, unattributed = [], {}, []
            for draw, (x, par) in enumerate(zip(flat, params)):
                dur, mask, _, _, _ = model.process_state(p, x, par, ss[draw, pi], population=True)
                work = dur[:, :p.n] * mask * p.channel_mask
                per_case.append(float(np.mean(work.sum(axis=1))))
                if channel == 'agency_work':
                    for actor in {a['actor_id'] for a in p.activities if p.actor[a['actor_id']]['role'] == 'agency'}:
                        indices = [i for i, a in enumerate(p.activities) if a['actor_id'] == actor]
                        per_agency.setdefault(p.actor[actor]['name'], []).append(float(np.mean(work[:, indices].sum(axis=1))))
                    unassigned = [i for i, a in enumerate(p.activities) if p.actor[a['actor_id']]['role'] != 'agency']
                    unattributed.append(float(np.mean(work[:, unassigned].sum(axis=1))))
            programs[p.id] = {'expected_hours_per_initial_case': summary(per_case),
                'hours_by_agency': {name: summary(v) for name, v in per_agency.items()},
                'agency_hours_without_resolved_owner': summary(unattributed) if channel == 'agency_work' else None,
                'diagnostics': diagnostics(np.log(np.maximum(per_case, 1e-12)).reshape(z.shape[:2])),
                'scope': 'represented route to initial decision; standing overhead, rework, post-decision labor not included'}
        result[channel] = {'has_work_hour_evidence': True, 'config': asdict(cfg), 'programs': programs,
                           'qualification': 'conditional on work-hour model; thin tasks borrow within this channel, never from waiting times'}
        arrays[channel] = {'z': z, 'structure': structure, 'log_likelihood': ll}
    return result, arrays
