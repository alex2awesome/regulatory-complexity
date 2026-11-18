#!/usr/bin/env python3
"""Score frozen SolarTRACE holdouts against an administrative timing fit.

Scores the reported log-cell-median outcome.  This is selected-holdout
evaluation, not population validation and not a whole-process calculation.
"""
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path

import numpy as np
from scipy.special import log_ndtr, logsumexp, ndtr, ndtri

from pipeline.procbench.solar_panel.fit_county_timing import Config, prepare

ROOT=Path(__file__).resolve().parents[3]
EVIDENCE=ROOT/"runs/solar_forum_20260922/county_model/evidence_v1.json"
FIT=ROOT/"runs/solar_forum_20260922/county_model/timing_training001"
OUT=FIT/"heldout_scores_v2.json"

def _eligible(row):
    if row["units"]!="business_days" or row["value"]<0: return False,"invalid_unit_or_negative_duration"
    if row["owner_kind"]=="unknown_utility": return False,"unresolved_utility_identity"
    if row["phase"]=="pre_install_ix" and row["value"]==0:
        meaning=row["original"].get("pre_install_zero_resolution")
        if meaning=="no_atb_requirement_step_absent": return False,"pre_install_step_explicitly_not_required"
        if meaning!="atb_required_zero_is_a_measured_duration": return False,"zero_ambiguous_requirement"
    return True,None

def _baseline(training, cap):
    positive=np.log([r["value"] for r in training if r["value"]>0])
    n=len(training); z=sum(r["value"]==0 for r in training)
    p0=(z+.5)/(n+1.0)
    mean=float(np.mean(positive)); sd=max(float(np.std(positive,ddof=1)),.05)
    coarsened=p0+(1-p0)*float(ndtr((math.log(cap)-mean)/sd))
    return {"raw_zero_probability":p0,"coarsened_event_probability":coarsened,"logpositive_mean":mean,"logpositive_sd":sd,
            "training_rows":n,"training_zeros":z,"zero_smoothing":"Jeffreys_half_count"}

def _base_score(row, base, cap):
    if row["value"]<=cap: return math.log(base["coarsened_event_probability"])
    y=math.log(row["value"]); s=base["logpositive_sd"]
    return math.log1p(-base["raw_zero_probability"])-math.log(s)-.5*math.log(2*math.pi)-.5*((y-base["logpositive_mean"])/s)**2

def _base_interval(base, cap):
    p0=base["raw_zero_probability"]; pc=base["coarsened_event_probability"]; m=base["logpositive_mean"]; s=base["logpositive_sd"]
    def q(p):
        if p<=pc: return 0.0
        return math.exp(m+s*ndtri((p-p0)/(1-p0)))
    return [q(.05),q(.95)]

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence",type=Path,default=EVIDENCE); ap.add_argument("--fit",type=Path,default=FIT); ap.add_argument("--out",type=Path,default=OUT); args=ap.parse_args(argv)
    raw=args.evidence.read_bytes(); evidence=json.loads(raw); manifest=json.loads((args.fit/"manifest.json").read_text())
    evidence_sha=hashlib.sha256(raw).hexdigest()
    if manifest.get("input_sha256") != evidence_sha:
        ap.error("Fit/evidence hash mismatch; heldout truth must come from the exact frozen fit input")
    cfg=Config(**manifest["config"]); training,_=prepare(evidence,holdouts="exclude",train_max_year=cfg.train_max_year)
    future_max_eval_year=(cfg.train_max_year+1 if cfg.train_max_year is not None else None)
    held=[]; excluded=[]
    for r in evidence["administrative_observations"]:
        if not (r["holdout_authority"] or r["holdout_forward_year"]): continue
        if future_max_eval_year is not None and r["year"]>future_max_eval_year:
            excluded.append({"row_id":r["row_id"],"reason":"post_declared_future_eval_horizon","year":r["year"]}); continue
        ok,reason=_eligible(r)
        (held if ok else excluded).append(r if ok else {"row_id":r["row_id"],"reason":reason})
    phase_names={p:json.loads((args.fit/"summary.json").read_text())["phases"][p]["parameter_names"] for p in training}
    rng=np.random.default_rng(20260922)
    row_scores=[]; baselines={p:_baseline(rows,cfg.zero_cap) for p,rows in training.items()}
    for phase in sorted(training):
        npz=np.load(args.fit/(phase+"_draws.npz")); b=npz["b"].reshape(-1,npz["b"].shape[-1]); owner=npz["owner"].reshape(-1,npz["owner"].shape[-1]); scales=npz["scales"].reshape(-1,npz["scales"].shape[-1])
        names=phase_names[phase]; bi={x:i for i,x in enumerate(names["b"])}; oi={x:i for i,x in enumerate(names["owner"])}
        ahj=bool(any(x.startswith("county:") for x in bi)); sigma=scales[:,0]; tau_owner=scales[:,1]; tau_county=scales[:,2] if ahj else np.zeros(len(scales))
        for r in [x for x in held if x["phase"]==phase]:
            mu=b[:,bi["intercept"]].copy(); extra=np.zeros(len(mu))
            if r["size_class"]=="10-20kW": mu+=b[:,bi["large_system"]]
            if r["technology"]=="PV+Storage": mu+=b[:,bi["storage"]]
            yname=f"year:{r['year']}"
            if r["year"]==cfg.reference_year: year_state="reference_year"
            elif yname in bi: mu+=b[:,bi[yname]]; year_state="posterior_known_year"
            else: extra+=.7**2; year_state="new_year_integrated_N0_0.7"
            cname="county:"+str(r.get("county"))
            if ahj and cname in bi: mu+=b[:,bi[cname]]; county_state="posterior_known_county"
            elif ahj and r["owner_name"]=="CA Dept of Housing & Community Development (HCD)": county_state="statewide_HCD_no_county_effect"
            elif ahj: extra+=tau_county**2; county_state="unseen_or_unknown_county_integrated_model_prior"
            else: county_state="utility_phase_no_county_effect"
            oname=r["owner_id"]
            if oname in oi: mu+=owner[:,oi[oname]]; owner_state="posterior_known_owner"
            else: extra+=tau_owner**2; owner_state="unseen_owner_integrated_owner_scale"
            pred_sd=np.sqrt(sigma**2+extra); cap=math.log(cfg.zero_cap)
            if r["value"]<=cfg.zero_cap:
                comp=log_ndtr((cap-mu)/pred_sd); observed="left_censored_at_or_below_cap"
            else:
                y=math.log(r["value"]); comp=-np.log(pred_sd)-.5*math.log(2*math.pi)-.5*((y-mu)/pred_sd)**2; observed="positive_log_cell_median"
            log_score=float(logsumexp(comp)-math.log(len(comp)))
            # One deterministic predictive realization per posterior draw gives
            # the mixture quantiles while retaining draw-specific integrated variance.
            latent=mu+pred_sd*rng.normal(size=len(mu)); predictive=np.where(latent<=cap,0.0,np.exp(latent))
            interval=np.quantile(predictive,[.05,.95]).tolist(); raw_value=float(r["value"]); value=0.0 if raw_value<=cfg.zero_cap else raw_value
            base=baselines[phase]; bint=_base_interval(base,cfg.zero_cap)
            if cfg.train_max_year is not None:
                subset=("overlap" if r["year"]==future_max_eval_year and r["holdout_authority"] else
                        "forward_year" if r["year"]==future_max_eval_year else "authority")
            else:
                subset="overlap" if r["holdout_authority"] and r["holdout_forward_year"] else "authority" if r["holdout_authority"] else "forward_year"
            row_scores.append({"row_id":r["row_id"],"phase":phase,"subset":subset,
                "truth":{"raw_value":raw_value,"coarsened_value":value,"coarsening_rule":f"reported_value <= {cfg.zero_cap} business_days maps to censor event 0","units":"business_days","observed_kind":observed},"model":{"log_score":log_score,"predictive_interval_90":interval,"covered_90":interval[0]<=value<=interval[1],"owner_state":owner_state,"county_state":county_state,"year_state":year_state},
                "baseline":{"log_score":_base_score(r,base,cfg.zero_cap),"predictive_interval_90":bint,"covered_90":bint[0]<=value<=bint[1]}})
    def aggregate(rows):
        if not rows: return {"n":0,"mean_log_score":None,"baseline_mean_log_score":None,"mean_log_score_difference":None,"coverage_90":None,"baseline_coverage_90":None}
        return {"n":len(rows),"raw_zeros":sum(x["truth"]["raw_value"]==0 for x in rows),"coarsened_events":sum(x["truth"]["coarsened_value"]==0 for x in rows),
            "mean_log_score":float(np.mean([x["model"]["log_score"] for x in rows])),"baseline_mean_log_score":float(np.mean([x["baseline"]["log_score"] for x in rows])),
            "mean_log_score_difference":float(np.mean([x["model"]["log_score"]-x["baseline"]["log_score"] for x in rows])),
            "coverage_90":float(np.mean([x["model"]["covered_90"] for x in rows])),"baseline_coverage_90":float(np.mean([x["baseline"]["covered_90"] for x in rows]))}
    subsets={s:aggregate([x for x in row_scores if x["subset"]==s]) for s in ("authority","forward_year","overlap")}; subsets["all_selected_holdouts"]=aggregate(row_scores)
    if cfg.train_max_year is not None:
        subsets["future_year_all_including_authority_overlap"]=aggregate([x for x in row_scores if x["truth"]["raw_value"] is not None and any(r["row_id"]==x["row_id"] and r["year"]==future_max_eval_year for r in held)])
    by_phase={p:aggregate([x for x in row_scores if x["phase"]==p]) for p in sorted(training)}
    counts_by_phase={p:{"n":len(rr),"raw_zero":sum(x["truth"]["raw_value"]==0 for x in rr),"coarsened_at_or_below_cap":sum(x["truth"]["coarsened_value"]==0 for x in rr)} for p in sorted(training) for rr in [[x for x in row_scores if x["phase"]==p]]}
    scope=(f"Frozen selected authority holdouts through {cfg.train_max_year} and genuine one-year-ahead {future_max_eval_year} holdouts from a through-{cfg.train_max_year} fit; later years outside evaluation scope."
           if cfg.train_max_year is not None else "Frozen selected authority and year-flag administrative cell holdouts; year-flag score is interpolation when later years were trained, not forward extrapolation.")
    out={"schema_version":"solar-county-heldout-score/1","scope":scope+" Not a random population sample or whole-process validation.",
        "input":{"evidence_path":str(args.evidence),"evidence_sha256":evidence_sha,"fit_path":str(args.fit),"fit_manifest_sha256":hashlib.sha256((args.fit/"manifest.json").read_bytes()).hexdigest(),"scorer_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "method":{"outcome":"common coarsened reported log cell median in business days","coarsening":f"all reported values <= {cfg.zero_cap} map to one censor event; raw values retained","posterior_draws":"all draws; no thinning","positive_score":"posterior-mixture Normal density on log reported median above cap","zero_score":"posterior-mixture left-censor event probability at configured cap","new_owner":"integrated Normal(0,owner_scale^2)","new_year":"integrated Normal(0,0.7^2); reference year 2024 fixed at zero by design","unknown_county":"integrated Normal(0,county_scale^2); known counties use shared posterior county draw; statewide HCD has no county effect exactly as trained","baseline":"phase-only Jeffreys-smoothed raw-zero mass plus Normal mean/spread fitted to raw positive training log medians; coarsened mass is p0+(1-p0)*Phi(log(cap))","interval":"deterministic-seed one posterior predictive realization per posterior draw, coarsened at cap; central 90 percent"},
        "evaluation_horizon":{"train_max_year":cfg.train_max_year,"future_max_eval_year":future_max_eval_year,"later_years_excluded":cfg.train_max_year is not None},
        "baseline_by_phase":baselines,"accounting":{"eligible_heldouts":len(held),"scored":len(row_scores),"excluded":excluded,"counts_by_phase":counts_by_phase},"subsets":subsets,"by_phase":by_phase,"rows":row_scores}
    args.out.write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps({"subsets":subsets,"by_phase":by_phase},indent=2))

if __name__=="__main__": main()
