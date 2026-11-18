"""Generate toy world W0: cases, structured evidence, held-out cases, truth.

  python -m pipeline.procbench.toy_statute.generate --out runs/toy_statute_20260926/W0

Writes evidence/ (what the fitter and the LLM may read), truth/ and heldout/
(scorer only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from . import grid, spec
from .truth_world import W0, WORLDS

EPOCH = date(2025, 1, 1)


def simulate_case(rng, world, town):
    s = world["structure"][town]
    k = int(rng.choice(spec.MAX_LOOPS + 1, p=grid.truncated_geometric(world["p_incomplete"][town], spec.MAX_LOOPS)))
    h = int(rng.random() < world["q_objection"][town]) if spec.hearing_possible(s) else 0
    seq = spec.chain(s, k, h)
    t = 0
    events = {"submitted": 0}
    durs = []
    for step, evs in seq:
        med, sig = world["step_days"][step]
        if step in spec.TOWN_SCALED:
            med *= world["town_speed"][town]
        d = grid.sample_rounded_lognormal(rng, med, sig, grid.L_DAYS)
        durs.append((step, d))
        t += d
        for e in evs:
            events.setdefault(e, t)
    hq = 0
    hour_parts = []
    for j, n in enumerate(spec.hour_counts(s, k, h)):
        step = spec.HOUR_STEPS[j]
        for _ in range(n):
            q = grid.sample_rounded_lognormal(rng, world["hours_median"][step], world["hours_sigma"], grid.L_HOURS, grid.HOUR_UNIT)
            hour_parts.append((step, q * grid.HOUR_UNIT))
            hq += q
    fees = world["fees"][town]
    dollars = sum(fees.get(item, 0) for item in spec.fee_items(s))
    return {"structure": s, "k": k, "h": h, "events": events, "durations": durs,
            "total_days": events["decision"], "hours_idx": hq, "hours": hq * grid.HOUR_UNIT,
            "hour_parts": hour_parts, "dollars": dollars}


def _maybe_contaminate(rng, x, c):
    return grid.sample_contamination_days(rng) if rng.random() < c else x


def make_report(rng, world, town, case, rid):
    obs = world["obs"]
    des = world["design"]
    s = case["structure"]
    post_day = int(rng.integers(des["post_day_range"][0], des["post_day_range"][1] + 1))
    if post_day < case["total_days"]:
        return {"report_id": rid, "town": town, "status": "pending", "days_since_submission": post_day}
    occ = spec.occurrence(s, case["k"], case["h"])
    mentions = {}
    for m in spec.MENTIONABLE:
        p = obs["mention_detect"] if occ[m] else obs["mention_false"]
        mentions[m] = bool(rng.random() < p)
    ev_for = {m: e for m, e in spec.MENTION_EVENT.items() if e}
    timed = ["submitted"]
    if rng.random() >= des["p_total_only"]:
        for m, e in ev_for.items():
            if occ[m] and mentions[m] and e in case["events"] and rng.random() < des["p_time_mentioned_event"]:
                timed.append(e)
    timed.append("decision")
    order = {e: i for i, e in enumerate(spec.EVENT_ORDER)}
    timed = sorted(set(timed), key=lambda e: (case["events"][e], order[e]))
    gaps = []
    for a, b in zip(timed[:-1], timed[1:]):
        x = case["events"][b] - case["events"][a]
        x = _maybe_contaminate(rng, x, obs["contamination"])
        v, unit = grid.report_days(rng, x, obs["sigma_report_days"])
        gaps.append({"from": a, "to": b, "value": v, "unit": unit})
    rep = {"report_id": rid, "town": town, "status": "decided", "mentions": mentions, "gaps": gaps}
    if rng.random() < des["p_report_hours"]:
        rep["hours_total"] = grid.report_hours(rng, case["hours_idx"], obs["sigma_report_hours"])
    if rng.random() < des["p_report_fees"]:
        rep["fees_paid_total"] = case["dollars"]
    return rep


def make_webpage(rng, world, town):
    s = world["structure"][town]
    obs = world["obs"]
    forced = set(world["design"]["forced_web_omissions"].get(town, []))
    listed = {}
    for step in spec.LISTABLE:
        present = spec.has_step(s, step) or (step == "hearing" and spec.hearing_possible(s))
        p = obs["web_list"] if present else obs["web_false"]
        listed[step] = bool(rng.random() < p) and step not in forced
    fees = world["fees"][town]
    # Fixed D1 items (including a kitchen course) are always exposed; optional
    # middle-step items are exposed only when that step is listed.
    fee_list = {item: fees[item] for step, item in spec.FEE_STEPS.items()
                if item in fees and (listed.get(step, False) or step in spec.D1_STEPS())}
    return {"town": town, "listed_steps": listed, "fee_schedule": fee_list}


def generate(out: Path, world=W0):
    out = Path(out)
    if any((out / d).exists() for d in ("evidence", "truth", "heldout", "generation_manifest.json")):
        raise FileExistsError(f"world artifacts already exist at {out}; use a new versioned output directory")
    if world.get("package_path"):
        spec.load_package(json.loads(Path(world["package_path"]).read_text()))
    elif world.get("design_space"):
        spec.use_design_space(world["design_space"])
    rng = np.random.default_rng(world["seed"])
    des = world["design"]
    admin, reports, webpages, latents = [], [], {}, []
    for town in world["towns"]:
        if town in des["admin_towns"]:
            for i in range(des["admin_n"]):
                c = simulate_case(rng, world, town)
                total = _maybe_contaminate(rng, c["total_days"], world["obs"]["contamination"])
                sub = EPOCH + timedelta(days=int(rng.integers(0, 300)))
                cid = f"{town[0]}A{i:03d}"
                rec = {"case_id": cid, "town": town, "submitted": sub.isoformat(),
                       "decided": (sub + timedelta(days=total)).isoformat()}
                if des.get("admin_milestones"):
                    # milestone records are exact status-change logs (no contamination); same RNG stream as W0
                    total = c["total_days"]
                    rec["decided"] = (sub + timedelta(days=total)).isoformat()
                    ms = {}
                    for field, e in spec.ADMIN_MILESTONES.items():
                        if e in c["events"]:
                            ms[field] = c["events"][e]
                    rec["milestones"] = {k: (sub + timedelta(days=v)).isoformat() for k, v in ms.items()}
                admin.append(rec)
                latents.append({"case_id": cid, **_latent(c), "recorded_total": total})
        for i in range(des["reports_per_town"]):
            c = simulate_case(rng, world, town)
            rid = f"{town[0]}R{i:03d}"
            reports.append(make_report(rng, world, town, c, rid))
            latents.append({"case_id": rid, **_latent(c)})
        webpages[town] = make_webpage(rng, world, town)
    heldout = {}
    for town in world["towns"]:
        cs = [simulate_case(rng, world, town) for _ in range(des["heldout_n"])]
        heldout[town] = {"total_days": [c["total_days"] for c in cs],
                         "hours": [c["hours"] for c in cs],
                         "dollars": [c["dollars"] for c in cs]}

    ev = out / "evidence"
    tr = out / "truth"
    ho = out / "heldout"
    for d in (ev, tr, ho):
        d.mkdir(parents=True, exist_ok=True)
    _dump(ev / "admin_records.json", admin)
    _dump(ev / "reports.json", reports)
    _dump(ev / "webpages.json", webpages)
    _dump(ev / "public_spec.json", {
        "statute": spec.STATUTE_TEXT, "d_steps": spec.D_STEPS, "p_steps": spec.P_STEPS,
        "structures": spec.STRUCTURE_TEXT, "towns": world["towns"], "notes": spec.PUBLIC_MODEL_NOTES,
        "observation_schema": "toy-process-v2",
        "fee_policy": "catalog-one-time-items-v2",
        "reporting": {"p_total_only": des["p_total_only"],
                      "p_time_mentioned_event": des["p_time_mentioned_event"]},
        "posting": {"post_day_range": list(des["post_day_range"]),
                    "note": "each applicant report is posted a uniformly random number of days after submission, in this range, independent of the case; it is pending if no decision had arrived by then"}})
    if "outcomes" in world:
        obs_out, lat_out = generate_outcomes(world)
        _dump(ev / "outcomes.json", obs_out)
        _dump(tr / "outcome_latents.json", lat_out)
    _dump(tr / "world.json", world)
    _dump(tr / "case_latents.json", latents)
    _dump(ho / "heldout_cases.json", heldout)
    manifest = {"world_id": world["world_id"], "files": {}}
    for d in (ev, tr, ho):
        for f in sorted(d.glob("*.json")):
            manifest["files"][str(f.relative_to(out))] = hashlib.sha256(f.read_bytes()).hexdigest()
    _dump(out / "generation_manifest.json", manifest)
    return manifest


OUTCOME_NOTES = """Outcome evidence (per town, over the study period):
- applications: permit applications received; denials: applications denied.
- complaints_permitted / complaints_unpermitted: coops at permitted / unpermitted addresses that drew at least one neighbour complaint, split by whether code enforcement verified a nuisance (verified) or not (unfounded). Enforcement finds out about unpermitted coops only through complaints.
- survey: households sampled with replacement from all households in town; keepers = sampled households keeping hens (permitted or not).
Assumed model: would-be keepers arrive at random; each coop is a nuisance or not; burden deters applications; every safeguard in a town's process (desk review, site inspection, neighbour comment period) can flag a coop, and any flag means denial; people who do not apply or are denied may keep hens anyway; complaints and verification depend only on whether the coop is a nuisance."""


def generate_outcomes(world):
    """Outcome layer (externalities); separate RNG stream so process evidence is unchanged."""
    from . import outcomes as O
    from .truth_eval import truth_burden
    o = world["outcomes"]
    rng = np.random.default_rng(world["seed"] + o["seed_offset"])
    B = truth_burden(world)
    obs = {"period_years": o["period_years"], "notes": OUTCOME_NOTES, "towns": {}}
    lat = {"burden_index": B, "towns": {}}
    for town in world["towns"]:
        s = world["structure"][town]
        p_apply = float(1 / (1 + np.exp(-(o["alpha"] - o["beta"] * (B[town][s] - O.B_REF)))))
        M = int(rng.poisson(o["m"][town]))
        z = rng.random(M) < o["pi"][town]
        apply_ = rng.random(M) < p_apply
        flagged = np.zeros(M, bool)
        for g in O.safeguards(s):
            pr = np.where(z, o["d"][g], o["f"][g])
            flagged |= rng.random(M) < pr
        denied = apply_ & flagged
        permitted = apply_ & ~flagged
        keeps = permitted | (~permitted & (rng.random(M) < o["u"]))
        complained = keeps & (rng.random(M) < np.where(z, o["k1"], o["k0"]))
        K = int(keeps.sum())
        H = o["households"][town]
        keepers_sampled = int(rng.binomial(o["survey_n"], K / H))
        obs["towns"][town] = {
            "applications": int(apply_.sum()), "denials": int(denied.sum()),
            "complaints_permitted": {"verified": int((complained & permitted & z).sum()),
                                     "unfounded": int((complained & permitted & ~z).sum())},
            "complaints_unpermitted": {"verified": int((complained & ~permitted & z).sum()),
                                       "unfounded": int((complained & ~permitted & ~z).sum())},
            "survey": {"n": o["survey_n"], "households": H, "keepers": keepers_sampled},
        }
        lat["towns"][town] = {"would_be_keepers": M, "p_apply": p_apply, "nuisance": int(z.sum()),
                              "keepers": K, "unpermitted": int((keeps & ~permitted).sum()),
                              "operating_nuisance": int((keeps & z).sum())}
    return obs, lat


def _latent(c):
    return {"structure": c["structure"], "k": c["k"], "h": c["h"], "total_days": c["total_days"],
            "events": c["events"], "durations": c["durations"], "hours": c["hours"], "dollars": c["dollars"]}


def _dump(p, obj):
    p.write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="W0", choices=sorted(WORLDS) + ["W4"])
    ap.add_argument("--package", default=None, help="statute package with a truth block (round 5+); overrides --world")
    ap.add_argument("--agencies", default=None, help="shared agencies json (round 6 linked worlds)")
    ap.add_argument("--world-id", default=None)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    if a.package:
        from .truth_package import make_world
        world = make_world(a.package, seed=a.seed, agencies_path=a.agencies, world_id=a.world_id)
    elif a.world == "W4":
        from .truth_w4 import make_w4
        world = make_w4()
    else:
        world = WORLDS[a.world]
    m = generate(Path(a.out), world)
    print(json.dumps(m, indent=1))


if __name__ == "__main__":
    main()
