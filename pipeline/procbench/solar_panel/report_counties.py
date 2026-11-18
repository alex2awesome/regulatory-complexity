"""Render typed county summaries without relabeling geography as agency capacity."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from pipeline.procbench.latent_gaussian import summary

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/"runs/solar_forum_20260922/county_model"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fit", type=Path, default=BASE/"timing_full001")
    ap.add_argument("--evidence", type=Path, default=BASE/"evidence_v1.json")
    ap.add_argument("--out", type=Path, default=BASE/"county_report001")
    args = ap.parse_args()
    raw = args.evidence.read_bytes()
    data = json.loads(raw)
    result = json.loads((args.fit/"summary.json").read_bytes())
    if hashlib.sha256(raw).hexdigest() != result["manifest"]["input_sha256"]:
        ap.error("Use the exact evidence bound to this fit")
    if args.out.exists():
        ap.error("Choose a new report path, preserving previous reports")
    args.out.mkdir(parents=True)
    records = []
    for phase, report in result["phases"].items():
        if not report["counties"]:
            continue  # Utilities have a separate table, never a county proxy.
        draws = np.load(args.fit/(phase+"_draws.npz"))
        bi = {n: i for i, n in enumerate(report["parameter_names"]["b"])}
        oi = {n: i for i, n in enumerate(report["parameter_names"]["owner"])}
        by_county = {c["county"]: c for c in report["counties"]}
        for county in sorted(by_county):
            c = by_county[county]
            owner_ids = sorted({r["owner_id"] for r in report["owners"] if r["county"] == county})
            common = draws["b"][:, :, bi["intercept"]] + draws["b"][:, :, bi["county:"+county]]
            existing = None
            if owner_ids:
                # Equal-authority geometric mean of standardized cell medians.
                # This isn't an install-weighted county median or a sum of time.
                mean_owner = np.mean(draws["owner"][:, :, [oi[o] for o in owner_ids]], axis=-1)
                existing = summary(np.exp(common+mean_owner))
            records.append(dict(county=county, phase=phase,
                fitted_administrative_cells=c["administrative_cells"],
                fitted_authorities=len(owner_ids), reference=result["manifest"]["reference"],
                equal_authority_geometric_mean_of_standardized_cell_medians=existing,
                regional_typical_authority_cell_median=c["standardized_cell_median_business_days"],
                units="business_days", posterior_status=("numerically_usable" if report["convergence_passed"] else "numerical_gate_failed"),
                local_evidence_status=c["evidence_status"],
                county_effect_variance_contraction=c["whitened_marginal_variance_contraction"],
                county_effect_separately_informed=c["whitened_marginal_variance_contraction"] >= .25,
                timing_component_forum_observations=0,
                process_step_count_status="not_estimated_by_this_component",
                applicant_hours_status="not_estimated_by_this_component",
                intrinsic_capability_status="not_identified",
                boundary_status="source_endpoint_ambiguity_unresolved" if phase == "inspection" else "first_submission_to_final_permit_approval"))
    payload = dict(schema_version="solar-county-report/1", fit_path=str(args.fit),
        evidence_sha256=hashlib.sha256(raw).hexdigest(), records=records,
        qualifications=["Historical administrative performance, not current legal process or intrinsic agency capability",
            "Equal-authority geometric mean summarizes sampled authorities, not all applicants or install-weighted burden",
            "Regional typical-authority prediction is distinct from the estimate for authorities actually observed",
            "Zero-reading counties have no observed-authority estimate; their regional prediction comes from pooling",
            "Forum and process-structure likelihoods are not silently included in these timing results",
            "Changing zero censoring cap to half a day shifts permit levels by approximately 18–24%",
            "Inspection column has contradictory source endpoint descriptions; do not add phase medians"],
        utility_phases={p: r["owners"] for p, r in result["phases"].items() if not r["counties"]})
    (args.out/"county_results.json").write_text(json.dumps(payload, indent=2)+"\n")
    columns = ["county", "phase", "fitted_administrative_cells", "fitted_authorities", "local_evidence_status",
               "existing_authorities_median", "existing_authorities_lower90", "existing_authorities_upper90",
               "regional_typical_authority_median", "regional_typical_authority_lower90", "regional_typical_authority_upper90",
               "units", "boundary_status", "intrinsic_capability_status", "process_step_count_status"]
    with (args.out/"county_results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for r in records:
            row = {k: r[k] for k in columns if k in r}
            for name, key in [("existing_authorities", "equal_authority_geometric_mean_of_standardized_cell_medians"),
                              ("regional_typical_authority", "regional_typical_authority_cell_median")]:
                s = r[key]
                row.update({name+"_median": s["median"] if s else None,
                            name+"_lower90": s["ci90"][0] if s else None,
                            name+"_upper90": s["ci90"][1] if s else None})
            writer.writerow(row)
    print(json.dumps({"counties":len({r["county"] for r in records}), "county_phase_rows":len(records),
                      "out":str(args.out), "intrinsic_capability_identified":False}))


if __name__ == "__main__":
    main()
