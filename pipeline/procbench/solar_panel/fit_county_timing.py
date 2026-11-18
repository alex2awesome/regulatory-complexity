"""County/AHJ administrative timing component of the solar process model.

Each phase models reported *cell medians*, not individual durations. Municipal
AHJs nest in geographic counties; utility owners do not. Unknown cell sample
sizes are not replaced with install counts. The residual combines unexplained
cell variation and unknown median sampling error. This cannot identify either
intrinsic agency capability or a source-selection correction on its own.

Conditional Gaussian AHJ effects are analytically integrated in the county /
fixed-effect update, then redrawn before scale updates (partially collapsed
Gibbs). Positive scales have Normal priors on their LOGS: the scalar sampler
targets log-scale density directly, with no missing change-of-variable factor.
Separate phase blocks are conditionally independent; their medians must not be
summed into a whole-process duration. Draws retain the actual authority layer.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.stats import truncnorm

from pipeline.procbench.latent_gaussian import diagnostics, summary

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "runs/solar_forum_20260922/county_model/evidence_v1.json"


@dataclass(frozen=True)
class Config:
    draws: int = 1000
    warmup: int = 1000
    chains: int = 4
    seed: int = 20260922
    zero_cap: float = 1.0
    scale_prior_median: float = .5
    scale_prior_log_sd: float = .7
    residual_prior_median: float = .7
    reference_year: int = 2024
    train_max_year: int | None = None


def slice_log(current, density, rng, width=.5, steps=50):
    """Stepping-out slice transition on an unconstrained LOG scale."""
    height = density(current) + math.log(max(rng.random(), 1e-300))
    left = current - width*rng.random()
    right = left + width
    j = int(rng.integers(steps))
    k = steps - 1 - j
    while j and density(left) > height:
        left -= width
        j -= 1
    while k and density(right) > height:
        right += width
        k -= 1
    for _ in range(1000):
        proposed = rng.uniform(left, right)
        if density(proposed) >= height:
            return proposed
        if proposed < current:
            left = proposed
        else:
            right = proposed
    raise RuntimeError("Log-scale slice bracket failed to close")


def scale_draw(current, values, median, log_sd, rng):
    ss = float(np.dot(values, values))
    n = len(values)
    def density(s):
        if abs(s) > 100:
            return -math.inf  # only a numerical guard, far outside prior mass
        return -n*s - .5*ss*math.exp(-2*s) - .5*((s-math.log(median))/log_sd)**2
    return math.exp(slice_log(math.log(current), density, rng))


def prepare(evidence, *, holdouts="exclude", train_max_year=None):
    groups, routes = {}, []
    for row in evidence["administrative_observations"]:
        reason = None
        if train_max_year is not None and row["year"] > train_max_year:
            reason = "post_training_cutoff_not_used"
        elif row["units"] != "business_days" or row["value"] < 0:
            reason = "invalid_unit_or_negative_duration"
        elif holdouts == "exclude" and (row["holdout_authority"] or row["holdout_forward_year"]):
            reason = "frozen_holdout_not_used_in_training"
        elif row["owner_kind"] == "unknown_utility":
            reason = "unresolved_utility_identity_retained_outside_owner_fit"
        elif row["phase"] == "pre_install_ix" and row["value"] == 0 and row["original"].get(
                "pre_install_zero_resolution") != "atb_required_zero_is_a_measured_duration":
            reason = ("pre_install_step_explicitly_not_required" if row["original"].get(
                "pre_install_zero_resolution") == "no_atb_requirement_step_absent" else
                "zero_ambiguous_no_requirement_or_subday_duration")
        if reason:
            routes.append({"row_id": row["row_id"], "reason": reason})
        else:
            groups.setdefault(row["phase"], []).append(row)
    return groups, routes


def design(rows, counties, config):
    ahj = rows[0]["owner_kind"] == "ahj"
    if any((r["owner_kind"] == "ahj") != ahj for r in rows):
        raise ValueError("A phase cannot mix county-nested AHJs and utilities")
    names = ["intercept", "large_system", "storage"]
    years = sorted({r["year"] for r in rows} | {config.reference_year})
    names += [f"year:{y}" for y in years if y != config.reference_year]
    fixed = len(names)
    if ahj:
        names += ["county:"+c for c in counties]
    owners = sorted({r["owner_id"] for r in rows})
    owner_idx = {v: i for i, v in enumerate(owners)}
    column_idx = {v: i for i, v in enumerate(names)}
    z = np.zeros((len(rows), len(names)))
    g = np.array([owner_idx[r["owner_id"]] for r in rows])
    for i, row in enumerate(rows):
        z[i, :3] = [1, row["size_class"] == "10-20kW", row["technology"] == "PV+Storage"]
        if row["year"] != config.reference_year:
            z[i, column_idx[f"year:{row['year']}"]] = 1
        if ahj:
            if row["county"] in counties:
                z[i, column_idx["county:"+row["county"]]] = 1
            elif row["owner_name"] != "CA Dept of Housing & Community Development (HCD)":
                raise ValueError("AHJ county missing: cannot silently drop or guess")
            # HCD is a statewide authority, not an unknown city. It has an owner
            # effect but no county effect. This is declared in the manifest.
    prior_mean = np.zeros(len(names))
    prior_mean[0] = math.log(10)
    prior_sd = np.full(len(names), .7)
    prior_sd[0] = 1.5
    prior_sd[1:3] = .5
    sums = np.zeros((len(owners), len(names)))
    np.add.at(sums, g, z)
    return dict(z=z, group=g, owners=owners, names=names, fixed=fixed,
                counts=np.bincount(g, minlength=len(owners)), sums=sums,
                ztz=z.T@z, mean=prior_mean, sd=prior_sd, ahj=ahj)


def collapsed_conditional(d, y, sigma, tau_owner, tau_county):
    """Exact b|y after integrating owner effects; useful for small exact checks."""
    sd = d["sd"].copy()
    sd[d["fixed"]:] = tau_county
    p0 = 1/sd**2
    w = 1/sigma**2
    precision_a = 1/tau_owner**2 + w*d["counts"]
    gw = d["sums"]*w
    sy = np.bincount(d["group"], weights=y, minlength=len(d["owners"]))
    q = np.diag(p0) + w*d["ztz"] - gw.T@(gw/precision_a[:, None])
    rhs = p0*d["mean"] + w*(d["z"].T@y) - gw.T@(w*sy/precision_a)
    return q, rhs, precision_a


def sample_chain(job):
    phase, rows, counties, cfg, chain = job
    rng = np.random.default_rng(cfg.seed+chain*100003+sum(map(ord, phase)))
    d = design(rows, counties, cfg)
    z, g = d["z"], d["group"]
    y = np.log(np.array([r["value"] if r["value"] > 0 else cfg.zero_cap for r in rows]))
    zero = np.array([r["value"] == 0 for r in rows])
    b = d["mean"] + rng.normal(0, .5, z.shape[1])
    a = rng.normal(0, .5, len(d["owners"]))
    sigma, tau_owner, tau_county = np.exp(rng.normal(math.log(.6), .25, 3))
    stored_b = np.zeros((cfg.draws, len(b)))
    stored_a = np.zeros((cfg.draws, len(a)))
    stored_s = np.zeros((cfg.draws, 3 if d["ahj"] else 2))
    start = time.monotonic()
    for it in range(cfg.draws+cfg.warmup):
        if zero.any():
            mu = z[zero]@b + a[g[zero]]
            y[zero] = truncnorm.rvs(-np.inf, (math.log(cfg.zero_cap)-mu)/sigma,
                                   loc=mu, scale=sigma, random_state=rng)
        q, rhs, precision_a = collapsed_conditional(d, y, sigma, tau_owner, tau_county)
        cf = cho_factor(q, lower=True, check_finite=False)
        b = cho_solve(cf, rhs, check_finite=False) + solve_triangular(
            cf[0].T, rng.normal(size=len(b)), lower=False, check_finite=False)
        residual = y-z@b
        mean_a = np.bincount(g, weights=residual, minlength=len(a))/sigma**2/precision_a
        a = mean_a + rng.normal(size=len(a))/np.sqrt(precision_a)
        sigma = scale_draw(sigma, residual-a[g], cfg.residual_prior_median, cfg.scale_prior_log_sd, rng)
        tau_owner = scale_draw(tau_owner, a, cfg.scale_prior_median, cfg.scale_prior_log_sd, rng)
        if d["ahj"]:
            # Counties without readings are sampled from their population prior,
            # not claimed as independent direct evidence about the scale.
            tau_county = scale_draw(tau_county, b[d["fixed"]:], cfg.scale_prior_median,
                                   cfg.scale_prior_log_sd, rng)
        if it >= cfg.warmup:
            j = it-cfg.warmup
            stored_b[j], stored_a[j] = b, a
            stored_s[j] = [sigma, tau_owner, tau_county] if d["ahj"] else [sigma, tau_owner]
    return phase, chain, stored_b, stored_a, stored_s, time.monotonic()-start


def summarize_phase(rows, counties, config, b, a, scales):
    d = design(rows, counties, config)
    scale_names = ["residual_scale", "owner_scale"] + (["county_scale"] if d["ahj"] else [])
    values = np.concatenate([b, a, scales], axis=2)
    names = d["names"] + ["owner:"+o for o in d["owners"]] + scale_names
    diag = {name: diagnostics(values[:, :, k]) for k, name in enumerate(names)}
    passed = all(v["rhat"] is not None and v["rhat"] <= 1.01 and
                 v["ess_bulk"] >= 400 and v["ess_tail"] >= 400 for v in diag.values())
    county_results = []
    if d["ahj"]:
        for k, county in enumerate(counties):
            direct = [r for r in rows if r["county"] == county]
            effect = b[:, :, d["fixed"]+k]
            # Conditional-normal prior z remains interpretable under random tau.
            whitened = effect/scales[:, :, 2]
            county_results.append(dict(county=county, administrative_cells=len(direct),
                observed_ahjs=len({r["owner_id"] for r in direct}),
                evidence_status="direct_panel_readings" if direct else "hierarchical_prediction_no_direct_readings",
                log_relative_effect=summary(effect), relative_factor=summary(np.exp(effect)),
                standardized_cell_median_business_days=summary(np.exp(b[:, :, 0]+effect)),
                whitened_marginal_variance_contraction=float(1-np.var(whitened, ddof=1)),
                intrinsic_capability_identified=False))
    owner_results = []
    by_owner = {r["owner_id"]: r for r in rows}
    for k, owner in enumerate(d["owners"]):
        row = by_owner[owner]
        location = b[:, :, 0] + a[:, :, k]
        if d["ahj"] and row["county"] in counties:
            location = location + b[:, :, d["fixed"]+counties.index(row["county"])]
        owner_results.append(dict(owner_id=owner, owner_name=row["owner_name"],
            county=row["county"] if d["ahj"] else None,
            standardized_cell_median_business_days=summary(np.exp(location))))
    return dict(observations=len(rows), zero_censored=sum(r["value"] == 0 for r in rows),
                parameter_count=len(names), convergence_passed=passed,
                max_rhat=max(x["rhat"] or math.inf for x in diag.values()),
                min_ess_bulk=min(x["ess_bulk"] for x in diag.values()),
                min_ess_tail=min(x["ess_tail"] for x in diag.values()),
                diagnostics=diag, counties=county_results, owners=owner_results,
                scales={name: summary(scales[:, :, k]) for k, name in enumerate(scale_names)},
                parameter_names=dict(b=d["names"], owner=d["owners"], scales=scale_names))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", type=Path, default=DEFAULT)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--zero-cap", type=float, default=1.)
    ap.add_argument("--holdouts", choices=["exclude", "include"], default="exclude")
    ap.add_argument("--train-max-year", type=int, default=None,
                    help="Optional inclusive training-year cutoff; later rows are typed routes before design construction")
    args = ap.parse_args()
    cfg = Config(draws=args.draws, warmup=args.warmup, chains=args.chains, zero_cap=args.zero_cap,
                 train_max_year=args.train_max_year)
    if cfg.zero_cap <= 0 or cfg.draws < 8 or cfg.chains < 2:
        ap.error("positive zero cap, at least 8 draws and at least 2 chains required")
    if args.out.exists() and any(args.out.iterdir()):
        ap.error("Use a new output directory; existing results are never overwritten")
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.evidence.read_bytes()
    evidence = json.loads(raw)
    counties = sorted(r["county"] for r in evidence["county_frame"])
    groups, routes = prepare(evidence, holdouts=args.holdouts, train_max_year=cfg.train_max_year)
    manifest = dict(schema_version="solar-county-timing/1", component="administrative_cell_median_timing",
        input_path=str(args.evidence), input_sha256=hashlib.sha256(raw).hexdigest(), config=vars(cfg),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), holdouts=args.holdouts,
        reference=dict(year=cfg.reference_year, size="0-10kW", technology="PV Only"),
        source_phase_definitions={p: sorted({r["original"]["phase_definition"] for r in rs})
                                  for p, rs in groups.items()},
        assumptions=["Lognormal distribution of cell medians, not of individual completion times",
            "Additive phase-specific year/size/storage effects; AHJ effects static over 2017–2024",
            "County denotes geography, not county-government responsibility for city permits",
            "Statewide HCD receives an authority effect without a county effect",
            "Utility owners separate from counties; ambiguous zero pre-install requirements routed out",
            "Install counts not treated as sample size; residual conflates median sampling error and heterogeneity",
            "Conditional independence of source cells; shared source and serial dependence not separately estimated",
            "Independent phase blocks; do not add phase medians or equate outputs with whole-process burden",
            "Inspection column has inconsistent source endpoint definitions; fit describes that column, not a resolved clock",
            "No causal or intrinsic-capability interpretation; no learned forum selection adjustment"],
        consumption=dict(administrative_input=len(evidence["administrative_observations"]),
            fitted=sum(map(len, groups.values())), routes=routes,
            forum_input=len(evidence["forum_observations"]), forum_used_here=0,
            forum_route="retained_in_evidence_and_conditional_report_model; joint_source_alignment_pending"))
    (args.out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    jobs = [(phase, rows, counties, cfg, c) for phase, rows in groups.items() for c in range(cfg.chains)]
    results = {phase: {} for phase in groups}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for phase, chain, b, a, s, elapsed in pool.map(sample_chain, jobs):
            results[phase][chain] = b, a, s
            print(json.dumps(dict(phase=phase, chain=chain, seconds=round(elapsed, 2))), flush=True)
    reports = {}
    for phase, rows in groups.items():
        b, a, s = [np.stack([results[phase][c][i] for c in range(cfg.chains)]) for i in range(3)]
        np.savez_compressed(args.out/(phase+"_draws.npz"), b=b, owner=a, scales=s)
        reports[phase] = summarize_phase(rows, counties, cfg, b, a, s)
        print(json.dumps(dict(phase=phase, **{k: reports[phase][k] for k in
              ("observations", "convergence_passed", "max_rhat", "min_ess_bulk", "min_ess_tail")})), flush=True)
    (args.out/"summary.json").write_text(json.dumps(dict(manifest=manifest, phases=reports), indent=2)+"\n")


if __name__ == "__main__":
    main()
