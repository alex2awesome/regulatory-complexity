"""Optional float64 accelerator for the sole process likelihood.

Consumes a compiled public-evidence Model. No truth, package-author rules or
saved scores. Positive convolutions and the exact joint selected-report kernel.
"""
import math
from types import SimpleNamespace

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import jax.scipy.special as jsp
import numpy as np

from pipeline.procbench.toy_statute import grid, spec, estimands


def safe_log(x):
    # Log structural zeros without a NaN derivative on an unselected branch.
    return jnp.where(x > 0, jnp.log(jnp.where(x > 0, x, 1.)), -jnp.inf)


def safe_lse(x, axis):
    valid = jnp.any(jnp.isfinite(x), axis=axis, keepdims=True)
    value = jsp.logsumexp(jnp.where(valid, x, 0.), axis=axis)
    return jnp.where(jnp.squeeze(valid, axis=axis), value, -jnp.inf)


def discretized(mu, log_sigma, length, unit=1.):
    # Do not differentiate (-inf-mu)/sigma at the zero boundary.
    edges = np.maximum((np.arange(length+1)-.5)*unit, 1e-300)
    z = (jnp.asarray(np.log(edges))[None]-mu[:, None])/jnp.exp(log_sigma[:, None])
    lower, upper = z[:, :-1], z[:, 1:]
    reflected = lower > 0
    a = jsp.log_ndtr(jnp.where(reflected, -lower, upper))
    b = jsp.log_ndtr(jnp.where(reflected, -upper, lower))
    valid = b < a
    difference = jnp.where(valid, b-a, -1.)
    logp = jnp.where(valid, a+jnp.log(-jnp.expm1(difference)), -jnp.inf)
    # Exact zero lower edge, without differentiating an infinite z-score.
    logp = logp.at[:, 0].set(jsp.log_ndtr(upper[:, 0]))
    return jnp.exp(logp-jsp.logsumexp(logp, axis=1, keepdims=True))


class ConvolutionPlan:
    """Count-vector DAG, batched by depth; preserves positive direct arithmetic."""
    def __init__(self, counts, pmf_length, length):
        counts = np.asarray(counts, int)
        zero = tuple([0]*counts.shape[1])
        keys = {zero}
        def add(key):
            if key in keys:
                return
            j = next(i for i in reversed(range(len(key))) if key[i])
            parent = list(key)
            parent[j] -= 1
            add(tuple(parent))
            keys.add(key)
        for row in counts:
            add(tuple(row))
        layers = [[zero]]
        for depth in range(1, max(map(sum, keys))+1):
            layers.append(sorted(k for k in keys if sum(k) == depth))
        self.recipes = []
        self.locations = {zero: (0, 0)}
        for depth, layer in enumerate(layers[1:], 1):
            parents, steps = [], []
            for i, key in enumerate(layer):
                j = next(i for i in reversed(range(len(key))) if key[i])
                parent = list(key)
                parent[j] -= 1
                parents.append(self.locations[tuple(parent)][1])
                steps.append(j)
                self.locations[key] = (depth, i)
            self.recipes.append((np.array(parents), np.array(steps), min(length, depth*(pmf_length-1)+1)))
        self.outputs = [self.locations[tuple(row)] for row in counts]
        self.length = length

    def __call__(self, pmfs):
        values = [jnp.ones((1, 1), dtype=jnp.float64)]
        for depth, (parents, steps, end) in enumerate(self.recipes, 1):
            b = pmfs[steps, :self.length]
            if depth == 1:
                result = b[:, :end]
            else:
                a = values[-1][parents]
                result = jax.vmap(lambda x, y: jnp.convolve(x, y, mode="full")[:end])(a, b)
            values.append(result)
        return jnp.stack([jnp.pad(values[depth][i], (0, self.length-values[depth].shape[1]))
                          for depth, i in self.outputs])


def report_kernel(bounds, sigma, length, unit=1.):
    """Bounds are fixed public reported bins; use finite branches for autodiff."""
    lo, hi, zero, valid = (jnp.asarray(a) for a in bounds)
    x = jnp.log(jnp.arange(1, length)*unit)[None]
    zl = (jnp.log(jnp.where(lo > 0, lo, 1.))[:, None]-x)/sigma
    zh = (jnp.log(jnp.where(jnp.isfinite(hi) & (hi > 0), hi, 1.))[:, None]-x)/sigma
    lower = jnp.where(jnp.asarray(lo > 0)[:, None], jsp.ndtr(zl), 0.)
    upper = jnp.where(jnp.isfinite(hi)[:, None], jsp.ndtr(zh), 1.)
    tails = jnp.where(jnp.asarray(valid)[:, None], jnp.maximum(upper-lower, 0.), 0.)
    return jnp.concatenate((jnp.asarray(zero, dtype=jnp.float64)[:, None], tails), axis=1)


def day_bounds(gaps):
    rows = []
    for value, unit in gaps:
        if unit == "interval":
            lo, hi = value
            zero = lo <= 0 <= hi
        else:
            mult, ulo, uhi = grid.UNITS[unit]
            lo, hi = max((value-.5)*mult, ulo), min((value+.5)*mult, uhi)
            zero = value == 0 and unit == "day"
        rows.append((lo, hi, float(zero), hi > lo))
    return tuple(np.asarray(a) for a in zip(*rows))


class JaxModel:
    def __init__(self, model, bucket_towns=True):
        self.reference = model
        self.config = model.config
        self.names = list(model.names)
        self.idx = {n: i for i, n in enumerate(model.base_names)}
        self.nd = len(spec.STRUCTURE_IDS)
        self.towns = list(model.towns)
        self.day_names, self.hour_names = list(spec.DAY_STEPS), list(spec.HOUR_STEPS)
        self.day_i = np.array([self.idx[f"mu_{s}"] for s in self.day_names])
        self.sig_i = np.array([self.idx[f"lsig_{s}"] for s in self.day_names])
        self.hour_i = np.array([self.idx[f"muh_{s}"] for s in self.hour_names])
        self.town_i = np.array([self.idx[f"la_{t}"] for t in self.towns])
        self.scaled = np.array([s in spec.TOWN_SCALED for s in self.day_names])
        self.prior_terms = [(self.idx[n], kind, a, b) for n, (kind, a, b) in model.pspec.items()]
        self.compiled = [self._compile_town(t) for t in self.towns]
        self.local_i = np.array([[self.idx[f"{n}_{t}"] for n in ("la", "lpinc", "lqobj")]
                                 for t in self.towns])
        self.buckets = self._make_buckets(bucket_towns)
        self.loglik = jax.jit(self._loglik)
        self.logprior = jax.jit(self._logprior)
        self.logpost = jax.jit(lambda x: self._logprior(x)+self._loglik(x))
        self.value_grad = jax.jit(jax.value_and_grad(lambda x: self._logprior(x)+self._loglik(x)))
        self.batch_loglik = jax.jit(jax.vmap(self._loglik))
        self.batch_value_grad = jax.jit(jax.vmap(jax.value_and_grad(lambda x: self._logprior(x)+self._loglik(x))))
        self.town_logliks = jax.jit(self._town_logliks)

    def _base(self, theta):
        x = theta
        for ia, ib, sa, sb in self.reference._bidx:
            total, fraction = theta[ia], theta[ib]
            x = x.at[ia].set(total-jnp.logaddexp(0., -fraction)-jnp.exp(2*theta[sa])/2)
            x = x.at[ib].set(total-jnp.logaddexp(0., fraction)-jnp.exp(2*theta[sb])/2)
        return x

    def _logprior(self, theta):
        x = self._base(theta)
        terms = []
        for i, kind, a, b in self.prior_terms:
            v = x[i]
            if kind == "normal":
                terms.append(-.5*((v-a)/b)**2-math.log(b)-.5*math.log(2*math.pi))
            elif kind == "mixnormal":
                terms.append(jsp.logsumexp(jnp.stack([math.log(w)-.5*((v-m)/s)**2-math.log(s)-.5*math.log(2*math.pi) for w, m, s in a])))
            else:
                terms.append(-a*jnp.logaddexp(0., -v)-b*jnp.logaddexp(0., v)-math.lgamma(a)-math.lgamma(b)+math.lgamma(a+b))
        return jnp.sum(jnp.stack(terms))

    def _compile_town(self, town):
        d = self.reference.data[town]
        length = max(self.reference.Lc, int(d.admin_x.max(initial=0))+1, int(d.agap_x.max(initial=0))+1, int(d.pend_N.max(initial=0))+1)
        if len(d.pend_N):
            length = max(length, estimands.total_support_length(self.config))
        hlength = int(d.hseg_counts.sum(axis=1).max())*(self.config.hour_grid_size-1)+1
        dp = ConvolutionPlan(d.seg_counts, self.config.day_grid_size, length)
        hp = ConvolutionPlan(d.hseg_counts, self.config.hour_grid_size, hlength) if len(d.hours_rep) else None
        unique = list(dict.fromkeys(d.gaps))
        gap_index = {g: i for i, g in enumerate(unique)}
        # Group complete report kernels by number of gaps, vectorizing paths and
        # reports together. Scatter back to every original case's own column.
        buckets = {}
        for gis, ri, representatives, inverse in d.timing_groups:
            G = len(gis)
            bucket = buckets.setdefault(G, {"segments": [], "kernels": [], "rows": [], "cols": [], "source": []})
            start = len(bucket["segments"])
            for ci in representatives:
                bucket["segments"].append(d.gap_seg[ci, gis])
                bucket["kernels"].append([gap_index[d.gaps[gi]] for gi in gis])
            for r in ri:
                bucket["rows"].extend(range(len(d.combos)))
                bucket["cols"].extend([r]*len(d.combos))
                bucket["source"].extend(start+inverse)
        for bucket in buckets.values():
            for k in bucket:
                bucket[k] = np.asarray(bucket[k], int)
        hb = (np.maximum(d.hours_unique-.25, 0), d.hours_unique+.25,
              d.hours_unique == 0, np.ones(len(d.hours_unique), bool))
        return dict(data=d, days=dp, hours=hp, hlength=hlength, length=length, buckets=buckets,
                    bounds=day_bounds(unique) if unique else None, hour_bounds=hb,
                    mask=self.reference.timing_mask_loglik(d),
                    has_hearing=np.array([spec.hearing_possible(s) for s, _, _ in d.combos]),
                    rows=[np.flatnonzero(d.combo_struct == si) for si in range(self.nd)],
                    contamination=grid.contamination_pmf_days(length=max(length, self.config.contamination_max_days+1),
                                                           xmax=self.config.contamination_max_days))

    @staticmethod
    def _runtime(c):
        # Arrays vary by town; control-flow dimensions and convolution topology
        # are bucket-static. No observations become static compiler constants.
        return {"data": {k: v for k, v in vars(c["data"]).items() if isinstance(v, np.ndarray)},
                **{k: c[k] for k in ("bounds", "hour_bounds", "mask", "buckets")}}

    def _make_buckets(self, enabled):
        groups = {}
        for ti, c in enumerate(self.compiled):
            runtime = self._runtime(c)
            leaves, tree = jax.tree_util.tree_flatten(runtime)
            signature = (str(tree), tuple((np.shape(v), str(np.asarray(v).dtype)) for v in leaves),
                         c["length"], c["hlength"], c["data"].n_ms,
                         c["data"].seg_counts.tobytes(), c["data"].hseg_counts.tobytes())
            if not enabled:
                signature = (ti, signature)
            groups.setdefault(signature, []).append((ti, runtime))
        out = []
        for members in groups.values():
            ids = np.array([i for i, _ in members])
            stacked = jax.tree_util.tree_map(lambda *v: jnp.asarray(np.stack(v)),
                                              *[v for _, v in members])
            out.append((ids, self.compiled[int(ids[0])], stacked))
        return out

    def _town(self, p, local, c, runtime, hour_pmfs):
        d = SimpleNamespace(**(vars(c["data"]) | runtime["data"]))
        ncombo = len(d.combos)
        mu = p[self.day_i]+self.scaled*local[0]
        step = discretized(mu, p[self.sig_i], self.config.day_grid_size)
        seg = c["days"](step)
        contam = self.config.contamination_probability
        case_ll = []
        if len(d.admin_x):
            likelihood = (1-contam)*seg[d.total_seg][:, d.admin_x]+contam*jnp.asarray(c["contamination"])[d.admin_x][None]
            case_ll.append(jnp.log(likelihood+grid.TINY))
        if d.n_ms:
            values = jnp.where(d.agap_seg >= 0, seg[jnp.maximum(d.agap_seg, 0), d.agap_x[None]], 0.)
            if self.config.milestone_contamination:   # opt-in; see ModelConfig
                values = jnp.where(d.agap_seg >= 0, (1-contam)*values+contam*jnp.asarray(c["contamination"])[d.agap_x][None], 0.)
            logs = safe_log(values)
            ms = jnp.zeros((ncombo, d.n_ms)).at[:, d.agap_case].add(logs)
            case_ll.append(ms)
        if d.n_dec:
            ref = self.reference
            Lc = ref.Lc
            R = report_kernel(runtime["bounds"], jnp.exp(p[self.idx["lsig_r"]]), max(Lc, len(ref.contam_days)))
            reference = R[:, :len(ref.contam_days)] @ jnp.asarray(ref.contam_days)
            kernels = (1-contam)*R[:, :Lc]+contam*reference[:, None]
            rep = jnp.zeros((ncombo, d.n_dec))
            for G, bucket in runtime["buckets"].items():
                gs, ki = bucket["segments"], bucket["kernels"]
                factors = seg[jnp.maximum(gs, 0), :Lc]*kernels[ki]
                factors = jnp.where(gs[:, :, None] >= 0, factors, 0.)
                if not self.config.completion_selection:
                    probability = jnp.prod(jnp.sum(factors, axis=2), axis=1)
                elif G == 1:
                    probability = factors[:, 0] @ jnp.asarray(ref.surv_post)
                else:
                    first = factors[:, 0]
                    for g in range(1, G-1):
                        first = jax.vmap(lambda a, b: jnp.convolve(a, b)[:Lc])(first, factors[:, g])
                    twice = jnp.cumsum(jnp.cumsum(factors[:, -1], axis=1), axis=1)
                    lo = ref.post_range[0]-1-np.arange(Lc)
                    hi = ref.post_range[1]-np.arange(Lc)
                    integrated = twice[:, hi]-jnp.where(lo[None] >= 0, twice[:, np.maximum(lo, 0)], 0.)
                    probability = jnp.sum(first*integrated, axis=1)/(ref.post_range[1]-ref.post_range[0]+1)
                ll = safe_log(jnp.maximum(probability, 0.))
                rep = rep.at[bucket["rows"], bucket["cols"]].set(ll[bucket["source"]])
            rep += runtime["mask"]
            a1 = d.mentions*(-jax.nn.softplus(-p[self.idx["ldelta"]]))+(1-d.mentions)*(-jax.nn.softplus(p[self.idx["ldelta"]]))
            a0 = d.mentions*(-jax.nn.softplus(-p[self.idx["leps"]]))+(1-d.mentions)*(-jax.nn.softplus(p[self.idx["leps"]]))
            rep += d.occ @ a1.T+(1-d.occ) @ a0.T
            if len(d.hours_rep):
                hseg = c["hours"](hour_pmfs)
                RH = report_kernel(runtime["hour_bounds"], jnp.exp(p[self.idx["lsig_rh"]]), c["hlength"], grid.HOUR_UNIT)
                QH = (hseg @ RH.T)[:, d.hours_inverse]
                rep = rep.at[:, d.hours_rep].add(jnp.log(QH[d.hseg]+grid.TINY))
            case_ll.append(rep)
        if len(d.pend_N):
            total = seg[d.total_seg]
            tail = jnp.concatenate([jnp.cumsum(total[:, ::-1], axis=1)[:, ::-1],
                                    jnp.zeros((len(total), 1))], axis=1)
            model_surv = tail[:, jnp.minimum(d.pend_N+1, total.shape[1])]
            if self.config.pending_contamination:   # opt-in; see ModelConfig
                cd = np.asarray(c["contamination"]); ctail = np.concatenate([np.cumsum(cd[::-1])[::-1], [0.0]])
                surv = (1-contam)*model_surv+contam*jnp.asarray(ctail)[jnp.minimum(d.pend_N+1, len(ctail)-1)][None]
                case_ll.append(jnp.log(jnp.maximum(surv, 0.)+grid.TINY))
            else:
                case_ll.append(jnp.log(model_surv+grid.TINY))
        all_cases = jnp.concatenate(case_ll, axis=1) if case_ll else jnp.zeros((ncombo, 0))
        lp = -jax.nn.softplus(-local[1])
        k = jnp.arange(self.config.max_loops+1)
        logpk = k*lp-jsp.logsumexp(k*lp)
        lq = -jax.nn.softplus(-local[2])
        lnotq = -jax.nn.softplus(local[2])
        lw = logpk[d.combo_k]+jnp.where(c["has_hearing"], jnp.where(d.combo_h, lq, lnotq), 0.)
        out = jnp.stack([(safe_lse(all_cases[rows]+lw[rows, None], axis=0)*d.case_weights).sum() for rows in c["rows"]])
        wl, present, wo = d.web_listed[None], d.web_present, d.web_observed[None]
        out += (wo*(present*(wl*(-jax.nn.softplus(-p[self.idx["llam"]]))+(1-wl)*(-jax.nn.softplus(p[self.idx["llam"]])))+
                    (1-present)*(wl*(-jax.nn.softplus(-p[self.idx["lepsw"]]))+(1-wl)*(-jax.nn.softplus(p[self.idx["lepsw"]]))))).sum(axis=1)
        return out

    def _town_logliks(self, theta):
        p = self._base(theta)
        if self.reference.center_towns:
            p = p.at[self.town_i].add(-p[self.town_i].mean())
        hour_pmfs = discretized(p[self.hour_i], jnp.full(len(self.hour_i), p[self.idx["lsigh"]]), self.config.hour_grid_size, grid.HOUR_UNIT)
        result = jnp.zeros((len(self.towns), self.nd))
        for ids, template, runtime in self.buckets:
            values = jax.vmap(lambda local, data: self._town(p, local, template, data, hour_pmfs))(
                p[self.local_i[ids]], runtime)
            result = result.at[ids].set(values)
        return result

    def _loglik(self, theta):
        values = self._town_logliks(theta)
        priors = np.stack([self.reference.log_struct_prior_town[t] for t in self.towns])
        return safe_lse(values+jnp.asarray(priors), axis=1).sum()
