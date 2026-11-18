"""`extend` must refuse to continue chains under a changed target or changed draws.

The audit measured two holes. Route `prior_weight` enters only the route Gibbs
step, never `log_likelihood`, so the saved-likelihood check could not see a
tampered `data.json`: priors changed from .5/.5 to .99/.01 were "EXTEND
ACCEPTED". And the fit manifest recorded no hash of `draws.npz`, so a replaced
or reordered draws file (per-state likelihoods still consistent) was accepted
too. `refine` already compared the saved data with the hashed original input;
`extend` now does the same, and both fit and extension record a draws hash that
the next extension verifies.

Offline: tiny fixture, one chain, a handful of draws, in a temporary directory.
"""
from __future__ import annotations

import json
from concurrent.futures import Future

import numpy as np
import pytest

from pipeline.procbench.infra.manifest import write


class ImmediatePool:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, fn, *args, **kwargs):
        future = Future()
        future.set_result(fn(*args, **kwargs))
        return future


def _fit(tmp_path, visit_data, monkeypatch):
    from pipeline.procbench import run_visit_hierarchy, extend_visit_hierarchy
    monkeypatch.setattr(run_visit_hierarchy, 'ProcessPoolExecutor', ImmediatePool)
    monkeypatch.setattr(extend_visit_hierarchy, 'ProcessPoolExecutor', ImmediatePool)
    path, fit = tmp_path / 'data.json', tmp_path / 'fit'
    write(path, visit_data)
    run_visit_hierarchy.main(['--data', str(path), '--out', str(fit), '--chains', '1',
                              '--warmup', '0', '--draws', '8', '--workers', '1', '--population-size', '16'])
    return path, fit


def _extend(fit, out, seed='1234'):
    from pipeline.procbench import extend_visit_hierarchy
    extend_visit_hierarchy.main(['--run', str(fit), '--out', str(out),
                                 '--extra-draws', '8', '--workers', '1', '--seed', seed])


def test_fit_and_extension_record_a_draws_hash_and_the_extension_verifies_it(tmp_path, visit_data, monkeypatch):
    from pipeline.procbench.infra.manifest import digest
    _, fit = _fit(tmp_path, visit_data, monkeypatch)
    fitted = json.loads((fit / 'manifest.json').read_text())
    assert fitted['draws_sha256'] == digest((fit / 'draws.npz').read_bytes())
    _extend(fit, tmp_path / 'extension')
    extended = json.loads((tmp_path / 'extension' / 'manifest.json').read_text())
    assert extended['saved_draws_hash_verified'] is True
    assert extended['saved_draws_sha256'] == fitted['draws_sha256']
    assert extended['draws_sha256'] == digest((tmp_path / 'extension' / 'draws.npz').read_bytes())


def test_extension_refuses_a_changed_route_prior_that_the_likelihood_cannot_see(tmp_path, visit_data, monkeypatch):
    _, fit = _fit(tmp_path, visit_data, monkeypatch)
    data = json.loads((fit / 'data.json').read_text())
    routes = data['programs'][0]['routes']
    routes[0]['prior_weight'] = routes[0]['prior_weight'] * 7  # not a likelihood term
    write(fit / 'data.json', data)
    with pytest.raises(ValueError, match='Saved data disagree'):
        _extend(fit, tmp_path / 'extension')


def test_extension_refuses_reordered_draws_whose_likelihoods_still_match(tmp_path, visit_data, monkeypatch):
    _, fit = _fit(tmp_path, visit_data, monkeypatch)
    with np.load(fit / 'draws.npz') as saved:
        z, s, ll = saved['z'], saved['structures'], saved['log_likelihood']
    # Reverse the draw order: every (state, likelihood) pair stays consistent, so
    # the saved-likelihood check passes; only the hash can tell.
    np.savez_compressed(fit / 'draws.npz', z=z[:, ::-1], structures=s[:, ::-1], log_likelihood=ll[:, ::-1])
    with pytest.raises(ValueError, match='Saved draws changed'):
        _extend(fit, tmp_path / 'extension')


def test_a_fit_recorded_before_draw_hashes_existed_still_extends_but_says_so(tmp_path, visit_data, monkeypatch):
    _, fit = _fit(tmp_path, visit_data, monkeypatch)
    manifest = json.loads((fit / 'manifest.json').read_text())
    del manifest['draws_sha256']  # a historical fit
    write(fit / 'manifest.json', manifest)
    _extend(fit, tmp_path / 'extension')
    extended = json.loads((tmp_path / 'extension' / 'manifest.json').read_text())
    assert extended['saved_draws_hash_verified'] is False
