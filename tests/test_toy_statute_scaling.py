"""Exact computational reuse: preserve every observation and joint case factor."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pipeline.procbench.toy_statute import model, readings, spec
from test_toy_statute_response_repairs import make_evidence
from toy_statute_reference import ReferenceModel


@pytest.fixture(autouse=True)
def reset_catalog():
    spec.use_design_space("menu6")
    yield
    spec.use_design_space("menu6")


def test_duplicate_timing_keeps_distinct_mentions_and_hours(tmp_path):
    ev = make_evidence(tmp_path)
    path = ev / "reports.json"
    reports = json.loads(path.read_text())
    first = next(copy.deepcopy(r) for r in reports if r["status"] == "decided")
    for i in range(4):
        r = copy.deepcopy(first)
        r["report_id"] = f"duplicate_fixture_{i}"
        r["hours_total"] = float(i+1)
        # Changed case evidence must survive reuse of the same timing kernel.
        r["mentions"]["neighbor_notice"] = bool(i % 2)
        reports.append(r)
    path.write_text(json.dumps(reports))
    fast, reference = model.Model(ev), ReferenceModel(ev)
    d = fast.data["Amber"]
    assert len(d.timing_groups) < d.n_dec
    assert sum(len(group[1]) for group in d.timing_groups) == d.n_dec
    for seed in (2, 8):
        x = fast.sample_prior_theta(np.random.default_rng(seed))
        assert_allclose(fast.town_struct_loglik(x, "Amber"), reference.town_struct_loglik(x, "Amber"), atol=1e-10, rtol=0)


def test_likelihood_cache_binds_particles_data_and_catalog(tmp_path):
    m = model.Model(make_evidence(tmp_path))
    X = np.stack([m.sample_prior_theta(np.random.default_rng(seed)) for seed in (2, 8)])
    L = readings.town_struct_logliks(m, X)
    path = tmp_path / "cache.npz"
    readings.save_likelihood_cache(path, m, X, L)
    assert_allclose(readings.load_likelihood_cache(path, m, X), L, atol=0, rtol=0)
    with pytest.raises(FileExistsError):
        readings.save_likelihood_cache(path, m, X, L)
    with pytest.raises(ValueError, match="provenance"):
        readings.load_likelihood_cache(path, m, X[::-1])
    m.center_towns = not m.center_towns
    with pytest.raises(ValueError, match="provenance"):
        readings.load_likelihood_cache(path, m, X)
    m.center_towns = not m.center_towns
    m.ev["public"]["unconsumed_test_field"] = True
    with pytest.raises(ValueError, match="provenance"):
        readings.load_likelihood_cache(path, m, X)


def test_likelihood_cache_detects_value_corruption(tmp_path):
    m = model.Model(make_evidence(tmp_path))
    X = np.array([m.sample_prior_theta(np.random.default_rng(2))])
    L = readings.town_struct_logliks(m, X)
    original = tmp_path / "original.npz"
    readings.save_likelihood_cache(original, m, X, L)
    with np.load(original, allow_pickle=False) as saved:
        metadata = saved["metadata"]
    changed = L.copy()
    changed.flat[0] += 1
    corrupt = tmp_path / "corrupt.npz"
    np.savez_compressed(corrupt, L=changed, metadata=metadata)
    with pytest.raises(ValueError, match="contents"):
        readings.load_likelihood_cache(corrupt, m, X)


def test_sampler_cache_output_does_not_change_transitions(tmp_path, monkeypatch):
    from pipeline.procbench.toy_statute import smc
    class Toy:
        names = ["a", "b"]
        towns = ["T"]
        blocks = []
        center_towns = False
        ev = {"note": "uninformative sampler mechanics fixture, no scientific fit"}
        observation_metadata = {"target_version": model.TARGET_VERSION}
        def __init__(self, *args, **kw): pass
        def sample_prior_theta(self, rng): return rng.normal(size=2)
        def logprior(self, x): return -.5*float(x@x)
        def loglik(self, x): return 0.
        def town_struct_loglik(self, x, town): return np.zeros(len(spec.STRUCTURE_IDS))
    class ImmediatePool:
        def __init__(self, max_workers, initializer, initargs): initializer(*initargs)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def map(self, fn, seq): return map(fn, seq)
    monkeypatch.setattr(smc, "Model", Toy)
    monkeypatch.setattr(smc, "ProcessPoolExecutor", ImmediatePool)
    common = dict(ev_dir="not-read", n=16, n_moves=2, workers=2, seed=27, log=lambda *x: None)
    plain = smc.run_smc(**common)
    path = tmp_path / "sampler_cache.npz"
    cached = smc.run_smc(**common, town_loglik_out=path)
    for a, b in zip(plain[:4], cached[:4]):
        assert_allclose(a, b, atol=0, rtol=0)
    assert_allclose(readings.load_likelihood_cache(path, Toy(), cached[0]), 0)


def test_equivalence_certificate_covers_current_likelihood_sources():
    import hashlib
    root = Path(model.__file__).parent
    cert = json.loads((root / "likelihood_compatibility.json").read_text())
    current = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
               for name in ("model.py", "grid.py", "spec.py")}
    assert cert["target_version"] == model.TARGET_VERSION
    assert current in cert["source_versions"]
