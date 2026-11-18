"""Case panels: raw situations drawn by the domain's generators."""
import numpy as np

from .compile import legal_set, UNDEFINED


def candidate_actions(spec, situation):
    return spec.domain['candidate_actions'](spec, situation)


def settled(spec, rung, situation):
    """Every admissible reading gives the same defined verdict on every candidate action."""
    for action in candidate_actions(spec, situation):
        values = set(legal_set(spec, rung, action.get('_situation', situation), action).values())
        if len(values) != 1 or UNDEFINED in values:
            return False
    return True


def sample_panel(spec, which, n=None, seed=None, params=None, max_tries=500):
    cfg = spec.raw['cases'][which]
    n = cfg['n'] if n is None else n
    seed = cfg['seed'] if seed is None else seed
    gen = spec.domain['generators'][cfg['generator']]
    merged = {**cfg.get('params', {}), **(params or {})}
    panel = []
    for i in range(n):
        for attempt in range(max_tries):
            rng = np.random.default_rng([seed, i, attempt])
            situation = gen(rng, i, merged, spec)
            # Controls must be decided alike by every reading at the open rung.
            if which != 'controls' or settled(spec, cfg.get('rung', 'open'), situation):
                break
        else:
            raise ValueError(f'no settled control found for case {i} in {max_tries} tries')
        panel.append(dict(case_id=f'{which}_{i:03d}', which=which, is_control=which == 'controls',
                          situation=situation))
    return panel


def visible(situation):
    """Strip hidden ground truth (keys starting with '_') before an agent sees it."""
    if isinstance(situation, dict):
        return {k: visible(v) for k, v in situation.items() if not k.startswith('_')}
    if isinstance(situation, list):
        return [visible(v) for v in situation]
    return situation
