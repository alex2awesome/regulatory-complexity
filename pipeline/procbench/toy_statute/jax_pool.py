"""Device-resident Metropolis/HMC moves for the shared adaptive SMC driver.

Random streams differ from NumPy. Targets do not. Geometry and step size are
fixed within each stage; only the shared SMC driver adapts between stages.
"""
from functools import partial
import time

import jax
import jax.numpy as jnp
import numpy as np

from .jax_backend import JaxModel


class JaxPool:
    def __init__(self, model, config):
        self.model, self.config = model, config
        self.jm = JaxModel(model, bucket_towns=config.bucket_towns)
        self.batch_size = config.batch_size
        self.evaluate = jax.jit(jax.vmap(self._densities))
        self.town_values = jax.jit(jax.vmap(self.jm._town_logliks))
        self.mutate = jax.jit(self._mutate, static_argnames=("moves",))
        self.last_stats = {}
        self.device = str(jax.devices()[0])

    def _densities(self, x):
        return jnp.stack((self.jm._logprior(x), self.jm._loglik(x)))

    def _target(self, x, beta):
        lp, ll = self._densities(x)
        return lp + beta * ll, (lp, ll)

    def _mutate(self, X, LP, LL, beta, chol, scale, key, valid, *, moves):
        vg = jax.vmap(jax.value_and_grad(self._target, has_aux=True), in_axes=(0, None))
        density = jax.vmap(self._densities)

        def step(_, state):
            X, LP, LL, key, accepted, bad = state
            key, nk, uk = jax.random.split(key, 3)
            noise = jax.random.normal(nk, X.shape, dtype=jnp.float64)
            if self.config.kernel == "hmc":
                (_, _), grad = vg(X, beta)
                momentum = noise + .5 * scale * (grad @ chol)

                def leapfrog(i, carry):
                    q, momentum, lp, ll = carry
                    q = q + scale * (momentum @ chol.T)
                    (_, (lp, ll)), grad = vg(q, beta)
                    amount = jnp.where(i == self.config.hmc_steps - 1, .5, 1.)
                    momentum = momentum + amount * scale * (grad @ chol)
                    return q, momentum, lp, ll

                proposal, momentum, lp, ll = jax.lax.fori_loop(
                    0, self.config.hmc_steps, leapfrog, (X, momentum, LP, LL))
                ratio = lp + beta * ll - LP - beta * LL
                ratio += .5 * jnp.sum(noise**2 - momentum**2, axis=1)
                divergent = ~jnp.isfinite(ratio) | (jnp.abs(ratio) > 1000.)
            else:
                proposal = X + scale * (noise @ chol.T)
                lp, ll = density(proposal).T
                ratio = lp + beta * ll - LP - beta * LL
                divergent = ~jnp.isfinite(lp) | ~jnp.isfinite(ll)
            yes = (jnp.isfinite(lp) & jnp.isfinite(ll) & jnp.isfinite(ratio)
                   & (jnp.log(jax.random.uniform(uk, LP.shape, dtype=jnp.float64)) <= ratio))
            # Diagnostic divergences are not an extra rejection/selection rule.
            X = jnp.where(yes[:, None], proposal, X)
            return (X, jnp.where(yes, lp, LP), jnp.where(yes, ll, LL), key,
                    accepted + jnp.sum(yes & valid), bad + jnp.sum(divergent & valid))

        X, LP, LL, _, accepted, bad = jax.lax.fori_loop(
            0, moves, step, (X, LP, LL, key, jnp.array(0), jnp.array(0)))
        return X, LP, LL, accepted, bad

    def factory(self, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _blocks(self, X):
        for begin in range(0, len(X), self.batch_size):
            part = X[begin:begin + self.batch_size]
            yield begin, len(part), np.pad(part, ((0, self.batch_size-len(part)), (0, 0)), mode="edge")

    def map(self, fn, items):
        from . import smc
        items = list(items)
        # Match by name, not identity: under `python -m ...toy_statute.smc` the driver's functions
        # live in __main__, a different module object from the imported smc (2026-10-01 fix).
        name = getattr(fn, "__name__", "")
        if name in ("_eval_chunk", "_town_loglik_chunk"):
            lengths = [len(x) for x in items]
            X = np.concatenate(items)
            evaluate = self.evaluate if name == "_eval_chunk" else self.town_values
            values = np.concatenate([np.asarray(evaluate(block))[:n] for _, n, block in self._blocks(X)])
            return np.split(values, np.cumsum(lengths)[:-1])
        if name != "_move_chunk":
            raise ValueError(f"unsupported accelerator operation: {fn.__name__}")
        start = time.perf_counter()
        # Logical worker chunks are combined; one call executes all mutations
        # for a particle batch without a host round-trip per proposal.
        lengths = [len(a[0]) for a in items]
        X = np.concatenate([a[0] for a in items])
        LP = np.concatenate([a[1] for a in items]); LL = np.concatenate([a[2] for a in items])
        _, _, _, beta, chol, scale, moves, _ = items[0]
        key = jax.random.PRNGKey(items[0][-1])
        for a in items[1:]:
            key = jax.random.fold_in(key, a[-1])
        output = []; accepted = bad = 0
        for begin, n, block in self._blocks(X):
            lp = np.pad(LP[begin:begin+n], (0, self.batch_size-n), mode="edge")
            ll = np.pad(LL[begin:begin+n], (0, self.batch_size-n), mode="edge")
            values = self.mutate(block, lp, ll, beta, chol, scale, jax.random.fold_in(key, begin),
                                 jnp.arange(self.batch_size) < n, moves=moves)
            x, lp, ll, acc, divergent = [np.asarray(v) for v in values]  # synchronize
            output.append((x[:n], lp[:n], ll[:n]))
            accepted += int(acc); bad += int(divergent)
        arrays = [np.concatenate([a[i] for a in output]) for i in range(3)]
        arrays = [np.split(a, np.cumsum(lengths)[:-1]) for a in arrays]
        rate = accepted / (len(X)*moves)
        self.last_stats = {"seconds": time.perf_counter()-start, "acceptance": rate,
                           "nonfinite_or_divergent_proposals": bad, "proposals": len(X)*moves,
                           "device": self.device, "town_buckets": len(self.jm.buckets)}
        return [(x, lp, ll, rate) for x, lp, ll in zip(*arrays)]
