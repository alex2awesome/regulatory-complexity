"""Solar phase 5: the step-level burden table, and what stringency costs in time.

Two outputs.

The burden table. For each step in the solar process: how likely it is to be
part of an authority's process, what phase it sits in and how long that phase
takes, what it costs and who pays, how many rounds it takes, what it demands of
the applicant, and its share of the total burden with an interval.

Time is fitted at the phase level, not the step level, because the SolarTRACE
metric clocks a phase from its start to its end and no source times the steps
inside it. Splitting a phase time across its steps would invent a number, so
the table reports phase time against every step in the phase and says so. That
is a real limit of the evidence, not of the model.

The stringency cross, which the solar leg has owed since Stage A. The fitted
timing model gives a posterior for each authority's own speed after year, phase
and stratum are removed. Regressing that posterior on the authority's
requirement flags, once per draw, says whether authorities that demand more
take longer, with the uncertainty carried through rather than asserted.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json

import numpy as np

from . import solar_sources as S

PHASE1 = S.ROOT / "runs/process_structure_20260921/solar_phase1"
PHASE3 = S.ROOT / "runs/process_structure_20260921/solar_phase3"
OUT = S.ROOT / "runs/process_structure_20260921/solar_phase5"
FIT = S.ROOT / "runs/solar_panel_20260920/fit_primary.json"
DRAWS = S.ROOT / "runs/solar_panel_20260920/draws_primary.npz"

# Which fitted phase clock covers each step. A step whose phase is None is
# outside the measured clocks and carries no time, which is stated rather than
# filled in.
STEP_PHASE = {
    "solar_permit__ahj_permit_application_submission": "permit_review",
    "solar_permit__ahj_completeness_determination": "permit_review",
    "solar_permit__ahj_plan_review": "permit_review",
    "solar_permit__ahj_structural_review": "permit_review",
    "solar_permit__ahj_electrical_review": "permit_review",
    "solar_permit__ahj_third_party_plan_review": "permit_review",
    "solar_permit__ahj_correction_resubmittal": "permit_review",
    "solar_permit__ahj_permit_fee_payment": "permit_review",
    "solar_permit__ahj_permit_issuance": "permit_review",
    "solar_permit__ahj_online_permit_submission": "permit_review",
    "solar_permit__ahj_in_person_counter_permitting": "permit_review",
    "solar_permit__solarapp_automated_compliance_review": "permit_review",
    "solar_permit__fire_department_review": "permit_review",
    "solar_permit__ahj_rough_inspection": "inspection",
    "solar_permit__ahj_final_inspection": "inspection",
    "solar_permit__ahj_reinspection": "inspection",
    "solar_permit__ahj_final_approval": "inspection",
    "solar_permit__inspection_scheduling_request": "inspection",
    "solar_permit__utility_preinstall_approval_to_build": "pre_install_ix",
    "solar_permit__utility_pto_review": "final_ix_pto",
    "solar_permit__utility_pto_grant": "final_ix_pto",
    "solar_permit__utility_meter_exchange": "final_ix_pto",
}

# What the applicant side actually has to do at a step, over and above waiting.
# Absent from this table means no applicant action is evidenced at that step.
APPLICANT_ACTION = {
    "solar_permit__design_and_permit_preparation": "prepare drawings and application",
    "solar_permit__structural_engineering_stamp": "obtain a licensed engineer's stamp",
    "solar_permit__customer_authorization_signature": "sign an authorisation",
    "solar_permit__ahj_permit_application_submission": "submit the application",
    "solar_permit__ahj_online_permit_submission": "submit through the portal",
    "solar_permit__ahj_in_person_counter_permitting": "attend the counter in person",
    "solar_permit__ahj_correction_resubmittal": "correct and resubmit",
    "solar_permit__ahj_permit_fee_payment": "pay the permit fee",
    "solar_permit__inspection_scheduling_request": "schedule the inspection",
    "solar_permit__ahj_appeal": "file an appeal",
    "solar_permit__smoke_detector_certification": "certify smoke detectors",
    "solar_permit__ix_application_submission": "submit the interconnection application",
    "solar_permit__final_inspection_clearance_submission": "submit clearance to the utility",
}

TERM = {
    "structural_review": ("Structural Review Required", "flag"),
    "rough_in_inspection": ("Rough-In Inspection Required", "flag"),
    "third_party_review": ("Third-Party Permit Review", "flag"),
    "same_day_in_person": ("Same Day In-Person Permitting Available", "flag"),
    "online_instant_permitting": ("PV Online Instant Permitting - 2025", "flag"),
    "inspections_required": ("Number of Inspections Required", "count"),
}

# Two specifications, because requiring every question to be answered leaves
# only a handful of authorities. The wide one uses every requirement and pays
# for it in sample size; the reduced one drops the two questions most
# authorities left blank and keeps far more of them. Both are reported. If they
# disagree, the disagreement is the finding.
SPECIFICATIONS = {
    "all_requirements": ["structural_review", "rough_in_inspection", "third_party_review",
                         "same_day_in_person", "online_instant_permitting",
                         "inspections_required"],
    "well_answered_only": ["structural_review", "rough_in_inspection",
                           "same_day_in_person", "online_instant_permitting"],
}


def phase_time_posterior(fit):
    """Median business days per phase at the reference stratum, from the fit."""
    beta = fit["parameters"]
    intercept = beta["intercept"]["median"]
    out = {}
    for phase in ("permit_review", "inspection", "pre_install_ix", "final_ix_pto"):
        key = f"phase:{phase}"
        if key in beta:
            offset, ci = beta[key]["median"], beta[key]["ci90"]
        elif phase == "inspection":
            offset, ci = 0.0, [0.0, 0.0]      # the model's reference phase
        else:
            out[phase] = None
            continue
        out[phase] = {
            "median_business_days": float(np.exp(intercept + offset)),
            "ci90_business_days": [float(np.exp(intercept + ci[0])),
                                   float(np.exp(intercept + ci[1]))],
            "log_offset_from_reference": offset,
        }
    return out


def _one_specification(terms, a, owner_to_slug, names, reqs):
    design, kept = [], []
    for index, owner in enumerate(names):
        slug = owner_to_slug.get(owner)
        row = reqs.get(slug) if slug else None
        if row is None:
            continue
        values, ok = [], True
        for term in terms:
            column, kind = TERM[term]
            if kind == "flag":
                flag = S.present_flag(row.get(column))
                if flag is None:
                    ok = False
                    break
                values.append(float(flag))
            else:
                count = S.count_value(row.get(column))
                if count is None:
                    ok = False
                    break
                values.append(float(np.log(max(count, .5))))
        if not ok:
            continue
        design.append([1.0] + values)
        kept.append(index)

    if len(kept) < 30:
        return {"authorities": len(kept), "status": "not_estimated",
                "reason": ("Fewer than thirty authorities answered every question in this "
                           "specification and also appear in the fitted timing model. Reported "
                           "as unestimable rather than run on a residue.")}

    X = np.asarray(design)
    Y = a[:, kept]
    coefficients = Y @ X @ np.linalg.pinv(X.T @ X).T
    out = {}
    for index, label in enumerate(["intercept"] + list(terms)):
        column = coefficients[:, index]
        lo, hi = np.quantile(column, [.05, .95])
        out[label] = {
            "percent_effect_median": float((np.exp(np.median(column)) - 1) * 100),
            "percent_effect_ci90": [float((np.exp(lo) - 1) * 100), float((np.exp(hi) - 1) * 100)],
            "excludes_zero": bool(lo > 0 or hi < 0),
        }
    residual = Y - coefficients @ X.T
    explained = 1 - residual.var(axis=1) / Y.var(axis=1)
    return {"authorities": len(kept), "status": "estimated", "terms": out,
            "variance_of_authority_speed_explained_median": float(np.median(explained))}


def stringency_regression():
    """Regress each posterior draw of an authority's own speed on what it demands."""
    draws = np.load(DRAWS, allow_pickle=False)
    a, names = draws["a"], [str(x) for x in draws["authorities"]]
    owner_to_slug = {}
    for row in S.read_panel():
        if row["owner_scope"] == "ahj":
            owner_to_slug.setdefault(row["stable_owner_id"], S.slug(row["owner_name"]))
    reqs = S.read_requirements()
    results = {name: _one_specification(terms, a, owner_to_slug, names, reqs)
               for name, terms in SPECIFICATIONS.items()}
    agree = {}
    wide, reduced = results["all_requirements"], results["well_answered_only"]
    if wide.get("status") == "estimated" and reduced.get("status") == "estimated":
        for term in SPECIFICATIONS["well_answered_only"]:
            agree[term] = {
                "sign_agrees": bool(
                    (wide["terms"][term]["percent_effect_median"] >= 0)
                    == (reduced["terms"][term]["percent_effect_median"] >= 0)),
                "both_exclude_zero": bool(wide["terms"][term]["excludes_zero"]
                                          and reduced["terms"][term]["excludes_zero"]),
            }
    return {
        "specifications": results,
        "agreement_between_specifications": agree,
        "interpretation": (
            "The outcome is an authority's own log speed after year, phase, size and technology "
            "are already removed by the timing model. A positive effect means authorities with "
            "that requirement are slower. The regression runs once per posterior draw, so the "
            "intervals carry the timing model's uncertainty. It is a cross-sectional association "
            "across authorities and identifies no causal effect of adding a requirement to a "
            "given authority; an authority that outsources review or staffs a same-day counter "
            "may differ in ways no column here records."),
    }


def observed_presence(universe):
    """Presence read straight off the evidence, with no model in between.

    Used when the occupancy posterior is unavailable or did not converge. For a
    step the survey asks about, the fraction of authorities answering Yes is a
    direct measurement and needs no model. For every other step it is honestly
    unknown, and is left as None rather than filled with a prior.
    """
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    tally = collections.defaultdict(lambda: [0, 0])
    for row in data["observations"]:
        tally[row["step_id"]][0 if row["detected"] else 1] += 1
    for anchor in data["known_presence"]:
        tally[anchor["step_id"]][0 if anchor["present"] else 1] += 1
    out = {}
    for step_id in universe:
        yes, no = tally.get(step_id, (0, 0))
        total = yes + no
        out[step_id] = {
            "step_id": step_id,
            "mean_presence_across_authorities": (yes / total) if total else None,
            "authorities_above_half": yes if total else None,
            "has_any_reading_opportunity": bool(total),
            "basis": "observed_fraction_of_readings" if total else "no_evidence",
        }
    return out, {"source": "direct_evidence_no_model",
                 "why": ("The occupancy posterior was unavailable or failed its convergence "
                         "gate, so presence here is the fraction of readings that detected the "
                         "step. That is a measurement of what sources say, not an estimate of "
                         "what is true: it makes no correction for a source failing to mention "
                         "a step that is present, which is exactly what the occupancy model "
                         "exists to do. Steps no source asks about are left unknown.")}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    fit = json.loads(FIT.read_text())
    universe = {json.loads(line)["step_id"]: json.loads(line)
                for line in (PHASE1 / "step_universe.jsonl").read_text().splitlines()}

    report_path = PHASE3 / "presence_report.json"
    presence_basis = None
    if report_path.exists():
        presence_report = json.loads(report_path.read_text())
        if presence_report.get("numerically_usable"):
            presence = {row["step_id"]: row for row in presence_report["steps"]}
            presence_basis = {"source": "occupancy_posterior",
                              "worst_rhat": presence_report.get("worst_rhat"),
                              "min_ess_bulk": presence_report.get("min_ess_bulk")}
        else:
            presence, presence_basis = observed_presence(universe)
            presence_basis["occupancy_fit_rejected"] = {
                "worst_rhat": presence_report.get("worst_rhat"),
                "min_ess_bulk": presence_report.get("min_ess_bulk")}
    else:
        presence, presence_basis = observed_presence(universe)

    stringency = [json.loads(line) for line in
                  (PHASE1 / "stringency_features.jsonl").read_text().splitlines()]
    inspections = [r["inspections_required"] for r in stringency if r["inspections_required"] is not None]
    costs = [r["median_permit_cost_usd"] for r in stringency if r["median_permit_cost_usd"] is not None]

    phases = phase_time_posterior(fit)

    rows = []
    for step_id, step in sorted(universe.items()):
        phase = STEP_PHASE.get(step_id)
        clock = phases.get(phase) if phase else None
        post = presence.get(step_id, {})
        rounds = None
        if phase == "inspection" and inspections:
            rounds = {"expected": float(np.mean(inspections)),
                      "median": float(np.median(inspections)),
                      "range": [float(np.min(inspections)), float(np.max(inspections))],
                      "basis": "Number of Inspections Required, answered by "
                               f"{len(inspections)} authorities"}
        cost = None
        if step_id == "solar_permit__ahj_permit_fee_payment" and costs:
            cost = {"median_usd": float(np.median(costs)), "mean_usd": float(np.mean(costs)),
                    "p90_usd": float(np.quantile(costs, .9)),
                    "payee": "authority having jurisdiction",
                    "payer": "applicant, normally through the installer",
                    "authorities_reporting": len(costs)}
        rows.append({
            "step_id": step_id,
            "label": step.get("label"),
            "layer": step.get("layer_label"),
            "actor": step.get("actor"),
            "phase_clock": phase,
            "presence_probability_mean": post.get("mean_presence_across_authorities"),
            "authorities_above_half": post.get("authorities_above_half"),
            "measured": bool(post.get("has_any_reading_opportunity")),
            "phase_median_business_days": clock["median_business_days"] if clock else None,
            "phase_ci90_business_days": clock["ci90_business_days"] if clock else None,
            "expected_rounds": rounds,
            "cost": cost,
            "applicant_action": APPLICANT_ACTION.get(step_id),
        })

    # ---- burden share, computed at the phase level because time is a phase clock
    #
    # CORRECTED after audit. The first version multiplied the inspection phase
    # time by the mean number of inspections required. That double-counts: the
    # source's inspection clock runs from installation complete to the LAST
    # completed inspection, so it already spans every required inspection. The
    # inspection count is reported beside the phase as a stringency feature and
    # is not applied to the clock.
    #
    # The source also flags its own inspection endpoint as ambiguous: the
    # published definition is self-referential and the dataset's quartile sheet
    # gives a different one. That ambiguity is carried on the row rather than
    # resolved here.
    phase_rows = collections.defaultdict(list)
    for row in rows:
        if row["phase_clock"] and row["presence_probability_mean"] is not None:
            phase_rows[row["phase_clock"]].append(row)
    share = {}
    total = 0.0
    for phase, members in phase_rows.items():
        clock = phases.get(phase)
        if not clock:
            continue
        weight = clock["median_business_days"]
        share[phase] = {
            "median_business_days": clock["median_business_days"],
            "ci90_business_days": clock["ci90_business_days"],
            "inspections_required_mean": (float(np.mean(inspections))
                                          if phase == "inspection" and inspections else None),
            "rounds_applied_to_clock": 1.0,
            "steps_in_phase": len(members),
            "steps_present_above_half": sum(
                1 for m in members if (m["presence_probability_mean"] or 0) > .5),
            "applicant_actions_in_phase": sum(1 for m in members if m["applicant_action"]),
            "endpoint_ambiguous_in_source": phase == "inspection",
        }
        total += weight
    for phase in share:
        share[phase]["share_of_measured_elapsed_time"] = (
            share[phase]["median_business_days"] / total if total else None)

    report = {
        "schema_version": "solar-step-burden/1",
        "packet": "solar_phase5",
        "timing_model": {"path": str(FIT.relative_to(S.ROOT)), "sha256": S.sha256(FIT)},
        "presence_basis": presence_basis,
        "phase_clocks": phases,
        "burden_by_phase": share,
        "stringency_against_authority_speed": stringency_regression(),
        "stringency_distribution": {
            "authorities_with_a_permit_cost": len(costs),
            "median_permit_cost_usd": float(np.median(costs)) if costs else None,
            "authorities_with_an_inspection_count": len(inspections),
            "median_inspections_required": float(np.median(inspections)) if inspections else None,
        },
        "steps": rows,
        "qualifications": [
            "Time is a phase clock, not a step clock. Every step in a phase carries that phase's "
            "time because no source times the steps inside a phase. Do not read the same days "
            "several times over by summing steps within a phase.",
            "Permit resubmission is inside the permit clock by the source's own definition, which "
            "measures from the original submittal, so the permit phase has no separate round count "
            "and its rounds are not zero but unmeasured. Likewise the inspection clock runs to the "
            "LAST completed inspection and already spans every required one; the inspection count "
            "is a stringency feature and is not multiplied into the clock.",
            "The source's inspection endpoint is ambiguous: its published definition is "
            "self-referential and its quartile sheet gives a different one. The share attributed "
            "to inspection inherits that ambiguity and is a range in spirit even where it is one "
            "number on the page.",
            "Burden share covers measured elapsed time only. Applicant effort in hours, and the "
            "cost of an engineer's stamp, are not in any solar source and are absent here rather "
            "than assumed to be small.",
            "Read presence_basis before using any presence number here. If it says the "
            "occupancy posterior was used, the numbers inherit its held-out validation. If it "
            "says direct evidence, they are the fraction of sources that mentioned the step and "
            "carry no correction for sources that stayed silent.",
        ],
    }
    (OUT / "burden_table.json").write_text(json.dumps(report, indent=2))
    with (OUT / "burden_table.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["step_id", "label", "layer", "phase", "presence_mean",
                         "authorities_above_half", "phase_median_business_days",
                         "expected_rounds", "cost_median_usd", "applicant_action"])
        for row in rows:
            writer.writerow([
                row["step_id"], row["label"], row["layer"], row["phase_clock"],
                "" if row["presence_probability_mean"] is None else round(row["presence_probability_mean"], 4),
                row["authorities_above_half"] or "",
                "" if row["phase_median_business_days"] is None else round(row["phase_median_business_days"], 2),
                "" if not row["expected_rounds"] else round(row["expected_rounds"]["expected"], 2),
                "" if not row["cost"] else round(row["cost"]["median_usd"], 2),
                row["applicant_action"] or ""])
    return report


def main():
    argparse.ArgumentParser().parse_args()
    report = build()
    print(json.dumps({k: report[k] for k in
                      ("phase_clocks", "burden_by_phase", "stringency_against_authority_speed",
                       "stringency_distribution")}, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
