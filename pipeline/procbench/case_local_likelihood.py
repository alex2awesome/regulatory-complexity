"""One-case views of the existing compiled V6 path likelihood.

These are computational views, not new evidence, priors, or an approximate
likelihood. Only that case's latent-coordinate block may use the view. Global
updates and saved likelihoods retain the complete target. No fitted values are
cached: the existing trace caches remain parameter-keyed and view-local.
"""
from copy import copy
import math

import numpy as np


def case_view(program, case):
    if case not in program['case_index']:
        raise ValueError('Unknown case for a local likelihood view')
    if not all('paths' in route for route in program['routes']):
        raise ValueError('Case-local views require explicit case paths in every inventory')
    view = copy(program)
    view['cases'] = [case]
    view['case_index'] = {case: 0}
    view['case_coordinates'] = program['case_coordinates'][[program['case_index'][case]]].copy()
    view['selected_cases'] = {case} if case in program['selected_cases'] else set()
    view['cache'] = {}
    view['selection_population_cache'] = {}
    # These factors depend on global parameters, never this case's noises.
    view['quantile_cohorts'] = []
    view['histogram_cohorts'] = []
    view['rates'] = []
    columns = [j for j, observation in enumerate(program['observations'])
               if observation['case_id'] == case]
    view['observations'] = [program['observations'][j] for j in columns]
    view['case_path_scope'] = {case: program['case_path_scope'][case]} if case in program['case_path_scope'] else {}
    if 'case_path_priors' in program:
        view['case_path_priors'] = {case: program['case_path_priors'][case]} if case in program['case_path_priors'] else {}
    if 'absent_event_censoring' in program:
        ids = {row['id'] for row in view['observations']}
        view['absent_event_censoring'] = {key: value for key, value in program['absent_event_censoring'].items() if key in ids}
    remap = {old: new for new, old in enumerate(columns)}
    view['joint_duration_reports'] = []
    for group in program.get('joint_duration_reports', []):
        if group['declaration']['case_id'] == case:
            local = copy(group)
            local['columns'] = [remap[j] for j in group['columns']]
            view['joint_duration_reports'].append(local)
    compiled = program['compiled']
    entries, groups, indices = [], [], []
    for column in columns:
        ident, start, end = compiled['groups'][column]
        if ident != program['observations'][column]['id']:
            raise ValueError('Compiled observation ordering changed')
        local_start = len(entries)
        entries.extend(compiled['entries'][start:end])
        indices.extend(range(start, end))
        groups.append((ident, local_start, len(entries)))
    view['compiled'] = dict(entries=entries, groups=groups)
    for key, array in compiled.items():
        if key in ('entries', 'groups'):
            continue
        if not isinstance(array, np.ndarray) or array.shape != (len(compiled['entries']),):
            raise ValueError('Unknown compiled field shape for a local view: ' + key)
        view['compiled'][key] = array[np.asarray(indices, dtype=int)].copy()
    return view


def case_update_views(model):
    """Map case chunks to an exact case view or legacy program-local factor."""
    views = {}
    for pi, program in enumerate(model.programs):
        explicit_paths = all('paths' in route for route in program['routes'])
        for case in program['cases']:
            row = program['case_coordinates'][program['case_index'][case]]
            if not len(row):
                continue
            size = model.cfg.case_update_block_size or len(row)
            # A legacy route has one program trace rather than compiled per-case
            # paths. Updating one case chunk leaves every other program factor
            # constant, so the exact owning program likelihood is a safe fallback.
            view = case_view(program, case) if explicit_paths else None
            for start in range(0, len(row), size):
                block = tuple(int(j) for j in row[start:start+size])
                if block:
                    if block in views:
                        raise ValueError('Case-coordinate blocks must be disjoint')
                    views[block] = (pi, view)
    return views


def case_log_likelihood(model, view, z, route_index):
    """Reuse the full path/group/selection calculation for this one case."""
    try:
        parts = model._case_path_likelihood(view, z, model.parameters(z), route_index)
        expected = view['id'] + ':case:' + view['cases'][0]
        if set(parts) != {expected}:
            raise ValueError('Local view unexpectedly contains non-case factors')
        return float(parts[expected])
    except (FloatingPointError, OverflowError):
        return -math.inf


def refresh_full_likelihood(model, z, structural, accumulated):
    full = model.log_likelihood(z, structural)
    if not math.isfinite(full) or not math.isclose(accumulated, full, rel_tol=1e-10, abs_tol=1e-8):
        raise RuntimeError('Case-local update disagrees with the complete target')
    return full
