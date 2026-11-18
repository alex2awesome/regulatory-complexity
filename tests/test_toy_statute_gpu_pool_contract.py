"""GPU pool control-flow regression using a CPU fake; no accelerator required."""
import importlib.util
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal

from pipeline.procbench.toy_statute import smc


def test_nonfinite_proposals_preserve_rng_consumption(monkeypatch):
    path=Path(__file__).parents[1]/"runs/toy_jax_pilot_20260930/equivalence.py"
    # Experimental adapter is deliberately not a required production dependency.
    if not path.exists():
        import pytest
        pytest.skip("optional GPU experiment adapter is not archived here")
    module_spec=importlib.util.spec_from_file_location("gpu_equivalence_contract",path)
    module=importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
    class Target:
        def logprior(self,x): return -.5*float(x@x) if x[1]<.6 else -np.inf
        def loglik(self,x): return -float((x-.1)@(x-.1)) if x[0]<.2 else -np.inf
    target=Target(); monkeypatch.setattr(smc,"_MODEL",target)
    pool=object.__new__(module.GpuPool)
    pool.model=target; pool.fallbacks=0
    pool.eval=lambda X:np.array([[target.logprior(x),target.loglik(x)] for x in X])
    X=np.zeros((8,2)); LP=np.array([target.logprior(x) for x in X]); LL=np.array([target.loglik(x) for x in X])
    call=(X,LP,LL,.6,np.eye(2),.4,8,392)
    expected=smc._move_chunk(call); actual=pool.map(smc._move_chunk,[call])[0]
    assert pool.fallbacks>0
    for a,b in zip(actual,expected): assert_array_equal(a,b)
