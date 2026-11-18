"""Likelihood and priors for the toy statute model.

Discrete structure (S1..S6 per town) and case paths (correction loops k,
hearing h) are enumerated exactly. Step durations are handled by exact
discretized convolutions, so there are no per-case latent variables. Only
the continuous parameters theta are sampled.

Never imports truth_world (enforced by tests).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.special import expit, gammaln, logsumexp

from . import estimands, grid, spec
from .config import ModelConfig, ParameterDict
from .compression import compress_admin, multiplicity

CONTAM = 0.02  # declared fixed contamination probability per reported gap / admin total
TARGET_VERSION = "toy-process-v3-20261002"
# Declared legacy assumption, not inferred from hidden world files. New corpora
# publish these observation-design settings. They are not agency capability.
LEGACY_REPORTING = {"p_total_only": 0.2, "p_time_mentioned_event": 0.7}

# ---------------------------------------------------------------- parameters


def param_names(towns):
    names = []
    names += [f"mu_{s}" for s in spec.DAY_STEPS]
    names += [f"lsig_{s}" for s in spec.DAY_STEPS]
    names += [f"la_{t}" for t in towns]
    names += [f"lpinc_{t}" for t in towns]
    names += [f"lqobj_{t}" for t in towns]
    names += [f"muh_{s}" for s in spec.HOUR_STEPS]
    names += ["lsigh", "lsig_r", "lsig_rh", "ldelta", "leps", "llam", "lepsw"]
    return names


# (kind, a, b): normal(mean, sd) on the unconstrained value, or beta(a, b) on
# expit(value) with the logit Jacobian.
def prior_spec(towns):
    p = {}
    for s in spec.DAY_STEPS:
        p[f"mu_{s}"] = ("normal", math.log(7.0), 1.0)
        p[f"lsig_{s}"] = ("normal", math.log(0.4), 0.8)
    for t in towns:
        p[f"la_{t}"] = ("normal", 0.0, 0.3)
        p[f"lpinc_{t}"] = ("beta", 1.0, 3.0)
        p[f"lqobj_{t}"] = ("beta", 1.0, 3.0)
    for s in spec.HOUR_STEPS:
        p[f"muh_{s}"] = ("normal", math.log(2.0), 1.0)
    p["lsigh"] = ("normal", math.log(0.5), 0.5)
    p["lsig_r"] = ("normal", math.log(0.2), 0.5)
    p["lsig_rh"] = ("normal", math.log(0.3), 0.5)
    p["ldelta"] = ("beta", 2.0, 1.0)
    p["leps"] = ("beta", 1.0, 20.0)
    p["llam"] = ("beta", 2.0, 1.0)
    p["lepsw"] = ("beta", 1.0, 20.0)
    return p


def log_prior(theta, names, pspec):
    lp = 0.0
    for v, n in zip(theta, names):
        kind, a, b = pspec[n]
        if kind == "normal":
            lp += -0.5 * ((v - a) / b) ** 2 - math.log(b) - 0.5 * math.log(2 * math.pi)
        elif kind == "mixnormal":
            # a = [(weight, mean, sd), ...]
            comps = [math.log(w) - 0.5 * ((v - m) / sd) ** 2 - math.log(sd) - 0.5 * math.log(2 * math.pi)
                     for w, m, sd in a]
            mx = max(comps)
            lp += mx + math.log(sum(math.exp(c - mx) for c in comps))
        else:
            # beta on p = expit(v), plus log|dp/dv| = log p + log(1-p)
            lp_ = -np.logaddexp(0.0, -v)
            lq_ = -np.logaddexp(0.0, v)
            lp += (a * lp_ + b * lq_) - (gammaln(a) + gammaln(b) - gammaln(a + b))
    return lp


def sample_prior(rng, names, pspec):
    out = []
    for n in names:
        kind, a, b = pspec[n]
        if kind == "normal":
            out.append(rng.normal(a, b))
        elif kind == "mixnormal":
            ws = np.array([c[0] for c in a])
            w, m, sd = a[rng.choice(len(a), p=ws / ws.sum())]
            out.append(rng.normal(m, sd))
        else:
            p = rng.beta(a, b)
            while not 0 < p < 1:  # no clipping atoms in a continuous prior
                p = rng.beta(a, b)
            out.append(math.log(p / (1 - p)))
    return np.array(out)


def unpack(theta, names):
    return dict(zip(names, theta))


def _log_sigmoid_pair(x):
    """(log expit(x), log(1 - expit(x))): the original math.log/log1p expressions whenever expit(x)
    is strictly inside (0, 1) (bit-identical), the stable log-sigmoid form only when it rounds to
    exactly 0 or 1 (real-data fits reached |x| > 37; 2026-10-01)."""
    q = expit(x)
    if 0.0 < q < 1.0:
        return math.log(q), math.log1p(-q)
    return -float(np.logaddexp(0.0, -x)), -float(np.logaddexp(0.0, x))


# ---------------------------------------------------------------- compiled data


@dataclass
class TownData:
    town: str
    combos: list                       # [(s, k, h)]
    combo_struct: np.ndarray           # structure index per combo
    combo_k: np.ndarray
    combo_h: np.ndarray
    seg_counts: np.ndarray             # (nseg, n_day_types)
    total_seg: np.ndarray              # per combo -> seg idx (submitted->decision)
    hseg_counts: np.ndarray            # (nhseg, n_hour_types)
    hseg: np.ndarray                   # per combo -> hour seg idx
    admin_x: np.ndarray                # admin totals (days)
    gaps: list                         # [(value, unit)]
    gap_seg: np.ndarray                # (ncombo, ngap) seg idx or -1
    rep_of_gap: np.ndarray             # (ngap,) decided-report index
    n_dec: int
    mentions: np.ndarray               # (n_dec, 4)
    occ: np.ndarray                    # (ncombo, 4)
    hours_rep: np.ndarray              # decided-report indices with hours
    hours_val: np.ndarray
    pend_N: np.ndarray
    web_listed: np.ndarray             # (n_listable,)
    web_present: np.ndarray            # (nstruct, n_listable)
    timing_available: np.ndarray      # (ncombo, n_dec): mentioned, truly available events
    timing_observed: np.ndarray       # (n_dec,): number of internal timed events
    timing_compatible: np.ndarray     # (ncombo, n_dec): no false/untold timed event
    gaps_of_rep: list
    timing_groups: list               # identical whole timing observations + distinct combo spans
    hours_unique: np.ndarray
    hours_inverse: np.ndarray
    agap_x: np.ndarray = None           # admin milestone gaps: exact day values
    agap_seg: np.ndarray = None         # (ncombo, nagap) seg idx or -1 (event mismatch)
    agap_case: np.ndarray = None        # (nagap,) milestone-record index
    n_ms: int = 0
    web_fees: dict = field(default_factory=dict)
    fee_reports: list = field(default_factory=list)
    case_weights: np.ndarray = None
    web_observed: np.ndarray = None    # (n_listable,) 1 = page addresses the step, 0 = unobserved


def load_evidence(ev_dir: Path):
    ev_dir = Path(ev_dir)
    return {
        "admin": json.loads((ev_dir / "admin_records.json").read_text()),
        "reports": json.loads((ev_dir / "reports.json").read_text()),
        "webpages": json.loads((ev_dir / "webpages.json").read_text()),
        "public": json.loads((ev_dir / "public_spec.json").read_text()),
    }


def _days_between(a, b):
    from datetime import date
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def compile_town(ev, town, config=None, compress_administrative=True):
    config = ModelConfig.parse(config)
    combos = [(s, k, h) for s in spec.STRUCTURE_IDS
              for k in range(config.max_loops + 1)
              for h in ((0, 1) if spec.hearing_possible(s) else (0,))]
    seg_index, hseg_index = {}, {}

    def seg_id(counts):
        if counts is None:
            return -1
        if counts not in seg_index:
            seg_index[counts] = len(seg_index)
        return seg_index[counts]

    def hseg_id(counts):
        if counts not in hseg_index:
            hseg_index[counts] = len(hseg_index)
        return hseg_index[counts]

    chains = [spec.chain(s, k, h) for (s, k, h) in combos]
    total_seg = np.array([seg_id(spec.segment_counts(c, "submitted", "decision")) for c in chains])
    hseg = np.array([hseg_id(spec.hour_counts(s, k, h)) for (s, k, h) in combos])

    admin_all = [r for r in ev["admin"] if r["town"] == town]
    if compress_administrative:
        admin_all = compress_admin(admin_all)
    admin_x = np.array([_days_between(r["submitted"], r["decided"]) for r in admin_all if "milestones" not in r], int)
    # milestone records: exact segments between consecutive recorded events; the set of
    # recorded milestone events must equal the milestone events in the combo's chain.
    ms_name = dict(spec.ADMIN_MILESTONES)
    ms_types = set(ms_name.values())
    agx, agcase, agcols = [], [], []
    ms_recs = [r for r in admin_all if "milestones" in r]
    for ri, r in enumerate(ms_recs):
        evs = [("submitted", 0)] + [(ms_name[k], _days_between(r["submitted"], v)) for k, v in r["milestones"].items()]
        evs.append(("decision", _days_between(r["submitted"], r["decided"])))
        order = {e: i for i, e in enumerate(spec.EVENT_ORDER)}
        evs.sort(key=lambda e: (e[1], order[e[0]]))
        recorded = {e for e, _ in evs} & ms_types
        cols = []
        for a, b in zip(evs[:-1], evs[1:]):
            agx.append(b[1] - a[1])
            agcase.append(ri)
            col = []
            for c in chains:
                in_chain = set(spec.event_positions(c)) & ms_types
                if in_chain != recorded:
                    col.append(-1)
                else:
                    col.append(seg_id(spec.segment_counts(c, a[0], b[0])))
            agcols.append(col)
    dec = [r for r in ev["reports"] if r["town"] == town and r["status"] == "decided"]
    pend = [r for r in ev["reports"] if r["town"] == town and r["status"] == "pending"]
    gaps, rep_of_gap = [], []
    available = np.zeros((len(combos), len(dec)), int)
    observed = np.zeros(len(dec), int)
    compatible = np.zeros((len(combos), len(dec)), bool)
    gaps_of_rep = [[] for _ in dec]
    gap_seg_cols = []
    for ri, r in enumerate(dec):
        endpoints = [r["gaps"][0]["from"]] + [g["to"] for g in r["gaps"]] if r["gaps"] else []
        if (not endpoints or endpoints[0] != "submitted" or endpoints[-1] != "decision"
                or any(a["to"] != b["from"] for a, b in zip(r["gaps"], r["gaps"][1:]))
                or len(set(endpoints)) != len(endpoints)):
            raise ValueError(f"{town}/{r.get('report_id')}: timed gaps must partition submitted -> decision")
        timed = set(endpoints[1:-1])
        observed[ri] = len(timed)
        for ci, (s, k, h) in enumerate(combos):
            occ = spec.occurrence(s, k, h)
            allowed = {e for m, e in spec.MENTION_EVENT.items()
                       if e and occ[m] and r["mentions"][m] and e in spec.event_positions(chains[ci])}
            available[ci, ri] = len(allowed)
            compatible[ci, ri] = timed <= allowed
        for g in r["gaps"]:
            gaps_of_rep[ri].append(len(gaps))
            if "interval_days" in g:
                lo, hi = map(float, g["interval_days"])
                if not np.isfinite([lo, hi]).all() or not 0 <= lo < hi:
                    raise ValueError("interval_days must contain finite ordered nonnegative bounds")
                gaps.append(((lo, hi), "interval"))
            else:
                gaps.append((g["value"], g["unit"]))
            rep_of_gap.append(ri)
            gap_seg_cols.append([seg_id(spec.segment_counts(c, g["from"], g["to"])) for c in chains])
    gap_seg = np.array(gap_seg_cols, int).T if gap_seg_cols else np.zeros((len(combos), 0), int)
    mentions = np.array([[int(r["mentions"][m]) for m in spec.MENTIONABLE] for r in dec], float).reshape(len(dec), len(spec.MENTIONABLE))
    occ = np.array([[int(v) for v in spec.occurrence(s, k, h).values()] for (s, k, h) in combos], float)
    hours_rep = np.array([i for i, r in enumerate(dec) if "hours_total" in r], int)
    hours_val = np.array([r["hours_total"] for r in dec if "hours_total" in r], float)
    # A town without a published process page, or a step its page does not address
    # (listed value None/absent), is UNOBSERVED: masked out, not read as "not listed".
    # Existing worlds list every LISTABLE step, so their likelihood is unchanged.
    web = ev["webpages"].get(town, {"listed_steps": {}, "fee_schedule": {}})
    web_observed = np.array([web["listed_steps"].get(s) is not None for s in spec.LISTABLE], float)
    web_listed = np.array([int(bool(web["listed_steps"].get(s))) for s in spec.LISTABLE], float)
    web_present = np.array([[int(spec.has_step(S, st) or (st == "hearing" and spec.hearing_possible(S)))
                             for st in spec.LISTABLE] for S in spec.STRUCTURE_IDS], float)
    seg_counts = np.array(sorted(seg_index, key=seg_index.get), float)
    hseg_counts = np.array(sorted(hseg_index, key=hseg_index.get), float)
    # Reuse a JOINT timing calculation, never independent gap likelihoods. The
    # selection factor couples all gaps through their sum. Mentions, timing-mask
    # and hours remain separate case columns and are NOT merged by this key.
    timing_index = {}
    timing_groups = []
    for ri, gis in enumerate(gaps_of_rep):
        key = tuple((gaps[gi], gap_seg[:, gi].tobytes()) for gi in gis)
        if key not in timing_index:
            _, representatives, inverse = np.unique(gap_seg[:, gis], axis=0, return_index=True, return_inverse=True)
            timing_index[key] = len(timing_groups)
            timing_groups.append((gis, [], representatives, inverse))
        timing_groups[timing_index[key]][1].append(ri)
    hours_unique, hours_inverse = np.unique(hours_val, return_inverse=True)
    return TownData(
        town=town, combos=combos,
        combo_struct=np.array([spec.STRUCTURE_IDS.index(s) for s, _, _ in combos]),
        combo_k=np.array([k for _, k, _ in combos]), combo_h=np.array([h for _, _, h in combos]),
        seg_counts=seg_counts, total_seg=total_seg, hseg_counts=hseg_counts, hseg=hseg,
        admin_x=admin_x, gaps=gaps, gap_seg=gap_seg, rep_of_gap=np.array(rep_of_gap, int), n_dec=len(dec),
        mentions=mentions, occ=occ, hours_rep=hours_rep, hours_val=hours_val,
        pend_N=np.array([r["days_since_submission"] for r in pend], int),
        web_listed=web_listed, web_present=web_present, web_observed=web_observed,
        timing_available=available, timing_observed=observed,
        timing_compatible=compatible, gaps_of_rep=gaps_of_rep,
        timing_groups=timing_groups, hours_unique=hours_unique, hours_inverse=hours_inverse,
        agap_x=np.array(agx, int), agap_seg=(np.array(agcols, int).T if agcols else np.zeros((len(combos), 0), int)),
        agap_case=np.array(agcase, int), n_ms=len(ms_recs),
        web_fees=dict(web["fee_schedule"]),
        fee_reports=[r["fees_paid_total"] for r in dec if "fees_paid_total" in r],
        case_weights=np.array([multiplicity(r) for r in admin_all if "milestones" not in r]
                              + [multiplicity(r) for r in ms_recs] + [1] * (len(dec) + len(pend)), float),
    )


class Model:
    def __init__(self, ev_dir, center_towns=False, prior_overrides=None, struct_prior=None, blocks=None,
                 design_space=None, package_path=None, model_config=None, compress_administrative=True):
        if package_path:  # statute package (round 5+); must precede any use of spec below (also in workers)
            spec.load_package(json.loads(Path(package_path).read_text()))
        elif design_space:
            spec.use_design_space(design_space)
        """center_towns: town speed factors enter as deviations from their mean
        (sum-to-zero identifiability constraint; round 2). prior_overrides:
        {param: (kind, a, b)} replacing entries of prior_spec. struct_prior:
        {town: {S: prob}} replacing the uniform structure prior.
        blocks: [(step_a, step_b), ...] composite reparameterization (round 3): the
        sampled coordinates for each jointly-identified block are
          blkT = log(E_a + E_b)  (log block mean, E = exp(mu + sigma^2/2) at average speed)
          blkU = logit(E_a / (E_a + E_b))  (share of the first step)
        in place of mu_a, mu_b. The map (blkT, blkU) -> (mu_a, mu_b) has |Jacobian| = 1
        (mu_a = T + log p - s_a^2/2, mu_b = T + log(1-p) - s_b^2/2, p = expit(U)), so the
        prior on (mu, lsig) is evaluated unchanged: same model, straighter geometry."""
        self.ev = load_evidence(ev_dir)
        self.config = ModelConfig.parse(model_config)
        self.compress_administrative = bool(compress_administrative)
        self.towns = list(self.ev["public"]["towns"])
        self.base_names = param_names(self.towns)
        self.blocks = [tuple(b) for b in (blocks or [])]
        self.names = list(self.base_names)
        self._bidx = []
        for a, b in self.blocks:
            ia, ib = self.base_names.index(f"mu_{a}"), self.base_names.index(f"mu_{b}")
            sa, sb = self.base_names.index(f"lsig_{a}"), self.base_names.index(f"lsig_{b}")
            self.names[ia] = f"blkT_{a}+{b}"
            self.names[ib] = f"blkU_{a}+{b}"
            self._bidx.append((ia, ib, sa, sb))
        self.pspec = prior_spec(self.towns)
        self.center_towns = center_towns
        if prior_overrides:
            for k, v in prior_overrides.items():
                assert k in self.pspec, k
                self.pspec[k] = tuple(v)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.data = {t: compile_town(self.ev, t, self.config, compress_administrative) for t in self.towns}
        # completion selection (audit 2026-09-29, F2): a report is posted C ~ Uniform{a..b} days after
        # submission and is 'completed' iff C >= true total T; P(C >= T) enters the completed-report
        # likelihood inside the latent-duration sum. The posting window is part of the declared
        # observation process (public_spec['posting']); all worlds so far use [10, 150].
        a_, b_ = self.config.post_day_range or self.ev["public"].get("posting", {}).get("post_day_range", [10, 150])
        if int(a_) != a_ or int(b_) != b_ or not 0 <= a_ <= b_:
            raise ValueError("posting range must be nonnegative ordered integers")
        T = np.arange(int(b_) + 1)
        self.post_range = (int(a_), int(b_))
        self.surv_post = np.clip((b_ - T + 1) / (b_ - a_ + 1), 0.0, 1.0)   # P(C >= T)
        self.Lc = int(b_) + 1
        if not self.config.completion_selection:
            self.Lc = estimands.total_support_length(self.config)
            self.surv_post = np.ones(self.Lc)
        self.reporting = dict(LEGACY_REPORTING)
        self.reporting.update(self.ev["public"].get("reporting", {}))
        if any(not 0 <= self.reporting[k] <= 1 for k in LEGACY_REPORTING):
            raise ValueError("reporting probabilities must lie in [0, 1]")
        self.observation_metadata = {
            "target_version": TARGET_VERSION, "reporting": self.reporting,
            "assumed_legacy_reporting_keys": [k for k in LEGACY_REPORTING if k not in self.ev["public"].get("reporting", {})],
            "admin_milestones": "exact; impossible event sets have zero likelihood",
            "total_support": "uncapped sum of individually truncated steps",
            "fee_inference": "catalog plug-in; unlisted residual split is not a fee likelihood",
            "fee_evidence_policy": self.ev["public"].get("fee_policy", "legacy: generation policy not recorded"),
        }
        if self.config != ModelConfig():
            self.observation_metadata["scientific_config"] = self.config.to_dict()
        self.contam_days = grid.contamination_pmf_days(
            length=max(self.config.day_grid_size, self.config.contamination_max_days + 1),
            xmax=self.config.contamination_max_days)
        uni = np.full(len(spec.STRUCTURE_IDS), -math.log(len(spec.STRUCTURE_IDS)))
        self.log_struct_prior_town = {t: uni.copy() for t in self.towns}
        if struct_prior:
            for t, pr in struct_prior.items():
                v = np.array([float(pr[S]) for S in spec.STRUCTURE_IDS])
                self.log_struct_prior_town[t] = np.log(v / v.sum())
        self.log_struct_prior = uni  # kept for backward compatibility

    # ---- parameter helpers
    def to_base(self, theta):
        """Sampling coordinates -> original (mu, lsig, ...) coordinates."""
        x = np.array(theta, float).copy()
        for ia, ib, sa, sb in self._bidx:
            T, U = x[ia], x[ib]
            va, vb = math.exp(2 * x[sa]), math.exp(2 * x[sb])
            x[ia] = T - np.logaddexp(0.0, -U) - va / 2
            x[ib] = T - np.logaddexp(0.0, U) - vb / 2
        return x

    def from_base(self, base):
        x = np.array(base, float).copy()
        for ia, ib, sa, sb in self._bidx:
            la = base[ia] + math.exp(2 * base[sa]) / 2
            lb = base[ib] + math.exp(2 * base[sb]) / 2
            x[ia] = np.logaddexp(la, lb)
            x[ib] = la - lb
        return x

    def logprior(self, theta):
        return log_prior(self.to_base(theta), self.base_names, self.pspec)

    def sample_prior_theta(self, rng):
        return self.from_base(sample_prior(rng, self.base_names, self.pspec))

    def prior_only_names(self):
        """Independent coordinates absent from this evidence likelihood, not weak effects."""
        names = []
        if not any(len(d.hours_rep) for d in self.data.values()):
            names += [n for n in self.names if n.startswith("muh_") or n in ("lsigh", "lsig_rh")]
        if not any(np.any(d.web_observed) for d in self.data.values()):
            names += ["llam", "lepsw"]
        return names

    def param_dict(self, theta):
        """Effective parameter dict in original coordinates (blocks mapped back;
        town-centering constraint applied)."""
        p = ParameterDict(unpack(self.to_base(theta), self.base_names), self.config)
        if self.center_towns:
            m = sum(p[f"la_{t}"] for t in self.towns) / len(self.towns)
            for t in self.towns:
                p[f"la_{t}"] -= m
        return p

    def step_pmfs(self, p, town):
        return estimands.day_step_pmfs(p, town)

    def hour_pmfs(self, p):
        return estimands.hour_step_pmfs(p)

    def combo_logw(self, p, d: TownData):
        x_inc, x_obj = p[f"lpinc_{d.town}"], p[f"lqobj_{d.town}"]
        pinc = expit(x_inc)
        q = expit(x_obj)
        if pinc < 1.0:
            pk = grid.truncated_geometric(pinc, self.config.max_loops)
            lw = np.log(pk[d.combo_k])
        else:   # expit rounded to 1.0 (logit > ~37): same normalized p^k law in log space, as in jax_backend
            k = np.arange(self.config.max_loops + 1) * -np.logaddexp(0.0, -x_inc)
            lw = (k - logsumexp(k))[d.combo_k]
        if 0.0 < q < 1.0:
            lq, lnq = math.log(q), math.log1p(-q)
        else:   # expit rounded to 0 or 1: stable log-sigmoid (bit-identical branch above for all other values)
            lq, lnq = -np.logaddexp(0.0, -x_obj), -np.logaddexp(0.0, x_obj)
        hp = np.array([spec.hearing_possible(spec.STRUCTURE_IDS[i]) for i in d.combo_struct])
        lw = lw + np.where(hp, np.where(d.combo_h == 1, lq, lnq), 0.0)
        return lw

    # ---- likelihood
    def town_struct_loglik(self, theta, town):
        """log p(data_town | theta, s) for each structure s (length 6)."""
        p = self.param_dict(theta)
        return self.town_struct_loglik_from_params(p, town)

    def town_struct_loglik_from_params(self, p, town):
        """Same likelihood from already mapped/centered parameters.

        Internal cache entry point: avoid reconstructing O(towns) coordinates
        for a move that changes only one or two towns. No likelihood shortcut.
        """
        d = self.data[town]
        L = max(self.Lc, int(d.admin_x.max(initial=0)) + 1,
                int(d.agap_x.max(initial=0)) + 1, int(d.pend_N.max(initial=0)) + 1)
        if len(d.pend_N):
            L = max(L, estimands.total_support_length(self.config))
        step = self.step_pmfs(p, town)
        seg = grid.sum_pmfs(step, d.seg_counts, length=L)
        contam_days = grid.contamination_pmf_days(length=max(L, self.config.contamination_max_days + 1),
                                                xmax=self.config.contamination_max_days)
        c0 = self.config.contamination_probability
        ncombo = len(d.combos)
        ll = np.zeros(ncombo)  # summed over cases, per combo? no: per case per combo below

        case_ll = []  # list of (ncombo,) arrays, one per case
        # admin totals
        if len(d.admin_x):
            tot = seg[d.total_seg]                            # (ncombo, L)
            x = d.admin_x
            if np.any(x < 0):
                raise ValueError("negative administrative duration")
            lik = (1 - c0) * tot[:, x] + c0 * contam_days[x][None, :]
            case_ll.append(np.log(lik + grid.TINY))           # (ncombo, n_admin)
        # admin milestone records (exact segments)
        if d.n_ms:
            gs = d.agap_seg
            x = d.agap_x
            if np.any(x < 0):
                raise ValueError("negative milestone gap")
            val = np.where(gs >= 0, seg[np.clip(gs, 0, None), x[None, :]], 0.0)
            if self.config.milestone_contamination:   # opt-in: numeric value contaminated, event set exact
                val = np.where(gs >= 0, (1 - c0) * val + c0 * contam_days[x][None, :], 0.0)
            with np.errstate(divide="ignore"):
                gl = np.log(val)  # default: exact status logs, numeric contamination does not apply
            ms_ll = np.zeros((ncombo, d.n_ms))
            np.add.at(ms_ll.T, d.agap_case, gl.T)
            case_ll.append(ms_ll)
        # decided reports (audit F2): the gaps partition submitted -> decision, so their sum is the
        # true total T; likelihood = sum_T [q_1 * ... * q_G](T) P(C >= T), q_i(d) = seg_i(d) p(Y_i | d)
        sig_r = math.exp(p["lsig_r"])
        if d.n_dec:
            rep_ll = np.zeros((ncombo, d.n_dec))
            if d.gaps:
                rep_ll[:, :] = 0.0
                gl = self._completed_gap_loglik(seg, d, sig_r, c0)
                rep_ll += gl
            rep_ll += self.timing_mask_loglik(d)
            # mentions
            (ld1, ld0), (le1, le0) = _log_sigmoid_pair(p["ldelta"]), _log_sigmoid_pair(p["leps"])
            M = d.mentions
            a1 = M * ld1 + (1 - M) * ld0
            a0 = M * le1 + (1 - M) * le0
            rep_ll += d.occ @ a1.T + (1 - d.occ) @ a0.T
            # hours
            if len(d.hours_rep):
                hstep = self.hour_pmfs(p)
                hseg = grid.sum_pmfs(hstep, d.hseg_counts)
                sig_rh = math.exp(p["lsig_rh"])
                RH = np.stack([grid.report_lik_hours(v, sig_rh, length=hseg.shape[1]) for v in d.hours_unique])
                QH = (hseg @ RH.T)[:, d.hours_inverse]          # restore original case columns
                rep_ll[:, d.hours_rep] += np.log(QH[d.hseg] + grid.TINY)
            case_ll.append(rep_ll)
        # pending reports: no decision by day N
        if len(d.pend_N):
            tot = seg[d.total_seg]
            N = d.pend_N
            if np.any(N < 0):
                raise ValueError("negative pending age")
            if self.config.pending_contamination:   # opt-in: contamination mixture on the survival
                # 1 - cdf keeps the mass beyond the evidence length L; its far-tail rounding is
                # dominated by the contamination term, which keeps every open case finite.
                ctail = np.concatenate([np.cumsum(contam_days[::-1])[::-1], [0.0]])
                surv = ((1 - c0) * grid.survival_from_full_pmf(tot, N)
                        + c0 * ctail[np.minimum(N + 1, len(ctail) - 1)][None, :])
            else:
                surv = grid.survival_from_full_pmf(tot, N)
            case_ll.append(np.log(np.clip(surv, 0, None) + grid.TINY))
        allc = np.concatenate(case_ll, axis=1) if case_ll else np.zeros((ncombo, 0))
        lw = self.combo_logw(p, d)[:, None]
        out = np.zeros(len(spec.STRUCTURE_IDS))
        for si in range(len(spec.STRUCTURE_IDS)):
            rows = d.combo_struct == si
            out[si] = (logsumexp(allc[rows] + lw[rows], axis=0) * d.case_weights).sum()
        # web page
        (ll1, ll0), (lw1, lw0) = _log_sigmoid_pair(p["llam"]), _log_sigmoid_pair(p["lepsw"])
        Wl = d.web_listed[None, :]
        P = d.web_present
        Wo = d.web_observed[None, :] if d.web_observed is not None else 1.0
        out += (Wo * (P * (Wl * ll1 + (1 - Wl) * ll0)
                      + (1 - P) * (Wl * lw1 + (1 - Wl) * lw0))).sum(axis=1)
        return out

    def timing_mask_loglik(self, d):
        """Probability of choosing these timed boundaries, conditional on mentions.

        The total-only branch and the per-mentioned-event branch can both yield
        zero internal timestamps. An event label is never numerically contaminated.
        """
        if not getattr(self, "config", ModelConfig()).score_timing_mask:
            return np.where(d.timing_compatible, 0.0, -np.inf)
        pt = self.reporting["p_total_only"]
        pe = self.reporting["p_time_mentioned_event"]
        n, k = d.timing_available, d.timing_observed[None, :]
        mass = (1 - pt) * pe ** k * (1 - pe) ** np.maximum(n - k, 0)
        mass += np.where(k == 0, pt, 0.0)
        with np.errstate(divide="ignore"):
            return np.log(np.where(d.timing_compatible, mass, 0.0))

    def _completed_gap_loglik(self, seg, d, sig_r, c0):
        """(ncombo, n_dec) log-likelihood of each decided report's timed gaps, including the
        completion-selection factor P(C >= T) on the latent total T = sum of the gaps."""
        ncombo = len(d.combos)
        Lc = self.Lc
        S = self.surv_post[:Lc]
        out = np.zeros((ncombo, d.n_dec))
        kernels = {}
        for gis, report_indices, representatives, inverse in d.timing_groups:
            if not gis:
                continue
            factors = []
            possible = np.ones(len(representatives), bool)
            for gi in gis:
                v, u = d.gaps[gi]
                if (v, u) not in kernels:
                    R = grid.report_lik_days(v, u, sig_r, length=max(Lc, len(self.contam_days)))
                    ref = float(self.contam_days @ R[:len(self.contam_days)])
                    kernels[v, u] = (1 - c0) * R[:Lc] + c0 * ref
                gs = d.gap_seg[representatives, gi]             # distinct joint span signatures
                q = np.zeros((len(representatives), Lc))
                ok = gs >= 0
                q[ok] = seg[gs[ok], :Lc] * kernels[v, u][None, :]
                possible &= ok
                factors.append(q)
            if not self.config.completion_selection:
                value = np.prod([q.sum(axis=1) for q in factors], axis=0)
            elif len(factors) == 1:
                value = factors[0] @ S
            else:
                first = factors[0]
                for q in factors[1:-1]:
                    first = np.stack([np.convolve(a, b)[:Lc] for a, b in zip(first, q)])
                twice = np.cumsum(np.cumsum(factors[-1], axis=1), axis=1)
                x = np.arange(Lc)
                lo, hi = self.post_range[0] - 1 - x, self.post_range[1] - x
                integrated = twice[:, hi] - np.where(lo[None, :] >= 0, twice[:, np.maximum(lo, 0)], 0)
                value = np.sum(first * integrated, axis=1) / (self.post_range[1] - self.post_range[0] + 1)
            with np.errstate(divide="ignore"):
                joint = np.where(possible, np.log(np.maximum(value, 0)), -np.inf)
                out[:, report_indices] = joint[inverse, None]  # same order / multiplicity as before
        return out

    def loglik(self, theta):
        tot = 0.0
        for t in self.towns:
            tot += logsumexp(self.town_struct_loglik(theta, t) + self.log_struct_prior_town[t])
        return tot

    def logpost(self, theta):
        lp = self.logprior(theta)
        if not np.isfinite(lp):
            return -np.inf
        ll = self.loglik(theta)
        return lp + ll if np.isfinite(ll) else -np.inf

    def require_fit_target(self, manifest):
        """Reweighting/cut inference must not treat old-target draws as new-target draws."""
        version = manifest.get("observation_model", {}).get("target_version")
        if version != TARGET_VERSION:
            raise ValueError(f"process particles target {version!r}, current target is {TARGET_VERSION!r}; "
                             "refit under this target or replay using the original source snapshot")
        previous = manifest.get("observation_model", {}).get("scientific_config")
        if ModelConfig.parse(previous) != self.config:
            raise ValueError("scientific configuration differs from fitted target; refit or use its original settings")

    def struct_posterior(self, theta, town):
        v = self.town_struct_loglik(theta, town) + self.log_struct_prior_town[town]
        return np.exp(v - logsumexp(v))

    # ---- fees (deterministic rule, declared in the plan)
    def fee_table(self, town, s, rng=None):
        """Fee amounts per item for structure s. Unlisted fee-bearing items present in s
        share the residual (median reported total minus listed items). When several
        items share it, the split is unidentified: with rng (round-2 bug fix, addendum
        R2-B) it is drawn Dirichlet(1) per posterior draw; without rng, equal split (round 1)."""
        d = self.data[town]
        fees = {item: 0.0 for item in spec.FEE_STEPS.values()}
        needed = []
        for item in spec.fee_items(s):
            if item in d.web_fees:
                fees[item] = float(d.web_fees[item])
            else:
                needed.append(item)
        if needed and d.fee_reports:
            listed = sum(fees.values())
            resid = float(np.median(d.fee_reports)) - listed
            shares = rng.dirichlet(np.ones(len(needed))) if (rng is not None and len(needed) > 1) \
                else np.full(len(needed), 1.0 / len(needed))
            for i, sh in zip(needed, shares):
                fees[i] = max(resid, 0.0) * float(sh)
        return fees
