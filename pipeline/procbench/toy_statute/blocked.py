"""Exact town-local likelihood caching and same-target blocked MH sweeps.

Centered speeds use equal/opposite raw-coordinate moves. A separate conditional
prior update moves the likelihood-invariant raw grand mean, so no prior direction
is frozen. Global proposals still evaluate every town. Geometry is frozen for
each SMC mutation stage; this module performs no within-sweep adaptation.
"""
import math

import numpy as np
from scipy.special import logsumexp

from .model import log_prior


def indices(model):
    speed = np.array([model.idx[f"la_{t}"] for t in model.towns])
    local = np.array([[model.idx[f"lpinc_{t}"], model.idx[f"lqobj_{t}"]] for t in model.towns])
    town_indices = set(speed) | set(local.ravel())
    shared = np.array([i for i in range(len(model.names)) if i not in town_indices])
    return speed, local, shared


def proposal_geometry(model, particles):
    """O(N*T + N*G^2), not a dense (3T+G)^3 Cholesky."""
    speed, local, shared = indices(model)
    X = np.asarray(particles)
    global_cov = np.atleast_2d(np.cov(X[:, shared].T))+1e-9*np.eye(len(shared))
    local_chol = []
    for row in local:
        cov = np.atleast_2d(np.cov(X[:, row].T))+1e-9*np.eye(2)
        local_chol.append(np.linalg.cholesky(cov))
    return {"shared_chol": np.linalg.cholesky(global_cov),
            "local_chol": np.array(local_chol),
            "speed_sd": np.maximum(X[:, speed].std(axis=0, ddof=1), 1e-4)}


class TownCache:
    def __init__(self, model, theta):
        self.model = model
        self.x = np.array(theta, float).copy()
        self.p = model.param_dict(self.x)
        self.speed, self.local, self.shared = indices(model)
        self.names = np.asarray(model.base_names)
        self.towns = np.asarray(model.towns)
        self.lp = model.logprior(self.x)
        self.values = np.array([self._town(t) for t in self.towns])
        self.ll = float(self.values.sum())
        self.evaluations = len(self.towns)

    def _town(self, town):
        m = self.model
        return float(logsumexp(m.town_struct_loglik_from_params(self.p, town)+m.log_struct_prior_town[town]))

    def local_move(self, coordinate_indices, changes, town_indices, beta, log_u):
        """Sparse symmetric proposal; caller supplies exactly its changed towns.

        Coordinates must be town coordinates, with speed changes summing to zero
        when centered. No full-vector copy, full prior, or all-town summation.
        """
        ids = np.asarray(coordinate_indices, int)
        change = np.asarray(changes, float)
        affected = np.asarray(town_indices, int)
        names = self.names[ids]
        # Guard the only nonlocal transform. Never silently reuse other towns
        # after a single centered-speed change.
        speed_mask = np.char.startswith(names.astype(str), "la_")
        if self.model.center_towns and abs(change[speed_mask].sum()) > 1e-14:
            raise ValueError("centered-speed local moves must be zero sum")
        allowed = {f"{prefix}{self.towns[i]}" for i in affected for prefix in ("la_", "lpinc_", "lqobj_")}
        if any(n not in allowed for n in names):
            raise ValueError("local coordinate not in affected towns")
        old = self.x[ids].copy()
        old_p = [self.p[n] for n in names]
        prior_before = log_prior(old, names, self.model.pspec)
        prior_after = log_prior(old+change, names, self.model.pspec)
        delta_prior = prior_after-prior_before
        if not np.isfinite(prior_after):
            return False
        self.x[ids] = old+change
        for n, v, d in zip(names, old_p, change):
            self.p[n] = v+d
        try:
            new_values = np.array([self._town(self.towns[i]) for i in affected])
            self.evaluations += len(affected)
            delta_ll = float((new_values-self.values[affected]).sum())
            accept = bool(np.isfinite(new_values).all() and delta_prior+beta*delta_ll >= log_u)
        except Exception:
            self.x[ids] = old
            self.p.update(zip(names, old_p))
            raise
        if accept:
            self.values[affected] = new_values
            self.lp += delta_prior
            self.ll += delta_ll
        else:
            self.x[ids] = old
            self.p.update(zip(names, old_p))
        return accept

    def shared_move(self, changes, beta, log_u):
        old = self.x[self.shared].copy()
        old_p = self.p
        self.x[self.shared] += changes
        lp = self.model.logprior(self.x)
        if not np.isfinite(lp):
            self.x[self.shared] = old
            return False
        self.p = self.model.param_dict(self.x)
        try:
            values = np.array([self._town(t) for t in self.towns])
            self.evaluations += len(self.towns)
            ll = float(values.sum())
            accept = bool(np.isfinite(ll) and lp-self.lp+beta*(ll-self.ll) >= log_u)
        except Exception:
            self.x[self.shared] = old
            self.p = old_p
            raise
        if accept:
            self.lp, self.ll, self.values = lp, ll, values
        else:
            self.x[self.shared] = old
            self.p = old_p
        return accept

    def refresh_grand_mean(self, rng):
        """Exact conditional normal draw, or symmetric prior-only MH fallback.

        The likelihood sees a_t - mean(a). For independent N(m_t,s_t^2)
        priors, conditional mean precision is sum(1/s_t^2), including overrides.
        Common shifts have no likelihood/Jacobian change, only the raw prior.
        """
        if not self.model.center_towns:
            return
        names = self.names[self.speed]
        raw = self.x[self.speed]
        current = raw.mean()
        contrast = raw-current
        terms = [self.model.pspec[n] for n in names]
        if all(k == "normal" for k, _, _ in terms):
            means = np.array([a for _, a, _ in terms])
            precision = 1/np.array([b for _, _, b in terms])**2
            mean = np.sum((means-contrast)*precision)/precision.sum()
            candidate = mean+rng.normal()/math.sqrt(precision.sum())
        else:
            candidate = current+rng.normal(0, .1/math.sqrt(len(raw)))
        before = log_prior(raw, names, self.model.pspec)
        proposed = contrast+candidate
        after = log_prior(proposed, names, self.model.pspec)
        if all(k == "normal" for k, _, _ in terms) or after-before >= math.log(rng.random()):
            self.x[self.speed] = proposed
            self.lp += after-before
        # p and town likelihoods stay unchanged: only the nuisance mean moved.

    def sweep(self, rng, beta, geometry, scale=1.):
        start = self.evaluations
        accepted, proposed = 0, 0
        global_step = scale*2.38/math.sqrt(len(self.shared))*(geometry["shared_chol"] @ rng.standard_normal(len(self.shared)))
        accepted += self.shared_move(global_step, beta, math.log(rng.random())); proposed += 1
        order = rng.permutation(len(self.towns))
        for i in order:
            step = scale*2.38/math.sqrt(2)*(geometry["local_chol"][i] @ rng.standard_normal(2))
            accepted += self.local_move(self.local[i], step, [i], beta, math.log(rng.random())); proposed += 1
        if self.model.center_towns:
            # A random spanning path spans the complete zero-sum subspace.
            for i, j in zip(order[:-1], order[1:]):
                sd = min(geometry["speed_sd"][i], geometry["speed_sd"][j])
                delta = scale*sd*rng.normal()
                accepted += self.local_move(self.speed[[i,j]], [delta,-delta], [i,j], beta, math.log(rng.random())); proposed += 1
            self.refresh_grand_mean(rng)
        else:
            for i in order:
                delta = scale*geometry["speed_sd"][i]*rng.normal()
                accepted += self.local_move([self.speed[i]], [delta], [i], beta, math.log(rng.random())); proposed += 1
        # O(T) once per sweep, not per local proposal; removes sum drift.
        self.ll = float(self.values.sum())
        self.lp = self.model.logprior(self.x)
        return {"accepted": int(accepted), "proposals": proposed, "town_evaluations": self.evaluations-start}
