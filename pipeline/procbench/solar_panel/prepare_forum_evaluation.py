"""Create a contributor-grouped heldout split for one frozen Solar timing frame."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from ..conditional_case_frames import canonical_sha256


SALT = "solar-forum-eval001"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def author_group(case_id):
    """Normalize the author component, not thread or installation suffix."""
    parts = case_id.split("__")
    author = parts[1] if len(parts) > 1 else parts[0]
    return re.sub(r"[^a-z0-9]", "", author.casefold())


def is_test(group):
    digest = hashlib.sha256((SALT + "\0" + group).encode()).digest()
    return int.from_bytes(digest[:8], "big") % 5 == 0


def _label(observation, lineage, include_evidence=False):
    row = lineage[observation["id"]]
    result = dict(observation_id=observation["id"], case_id=observation["case_id"],
        contributor_group=author_group(observation["case_id"]),
        observation_kind=observation["observation_kind"], lower=observation["lower"],
        upper=observation["upper"], time_unit=observation.get("time_unit", "calendar_days"),
        statistic=observation["statistic"], sampling=observation["sampling"],
        interpretation=row.get("interpretation"), logical_threads=row.get("logical_threads", []),
        source_claim_id=row.get("source_claim_id"), source_artifact_sha256=row.get("artifact_sha256"))
    if include_evidence:
        result["supporting_sources"] = [{"sha256": s.get("sha256"),
            "quote_segments": s.get("quote_segments", [])} for s in row.get("supporting_sources", [])]
    return result


def prepare(data_path, config_path, lineage_path, out):
    raw = json.loads(data_path.read_bytes()); train = copy.deepcopy(raw)
    config = json.loads(config_path.read_bytes())
    lineage_rows = json.loads(lineage_path.read_bytes())
    lineage = {row["observation_id"]: row for row in lineage_rows}
    observations = [o for p in raw["programs"] for o in p.get("observations", [])]
    missing = sorted(o["id"] for o in observations if o["id"] not in lineage)
    if missing:
        raise ValueError("Every observation requires source-bound lineage: " + ", ".join(missing))
    groups = {author_group(o["case_id"]) for o in observations}
    test_groups = {g for g in groups if is_test(g)}
    heldout = [o for o in observations if author_group(o["case_id"]) in test_groups]
    if not heldout or len(heldout) == len(observations):
        raise ValueError("Deterministic split must contain train and test observations")
    heldout_cases = {o["case_id"] for o in heldout}

    for program in train["programs"]:
        program["observations"] = [o for o in program.get("observations", [])
                                   if author_group(o["case_id"]) not in test_groups]
    # Remove the entire heldout contributor group from frame membership and its
    # ledger, including non-clock registry rows.  A generic excluded placeholder
    # would itself leak heldout membership.
    for frame in train.get("conditional_case_frames", []):
        frame["included_case_ids"] = [c for c in frame["included_case_ids"]
                                      if author_group(c) not in test_groups]
        ledger = frame.get("ledger", {}).get("rows", [])
        frame["ledger"]["rows"] = [r for r in ledger
            if author_group(r.get("registry_label_id", "")) not in test_groups]
        frame["registry_label_denominator"] = len(frame["ledger"]["rows"])
        frame["ledger_sha256"] = canonical_sha256(frame["ledger"])
        frame["generalization_limit"] += " Evaluation training split excludes deterministic contributor-heldout groups."

    train_ids = {o["id"] for p in train["programs"] for o in p["observations"]}
    serialized = json.dumps(train, sort_keys=True)
    if any(o["id"] in serialized or o["case_id"] in serialized for o in heldout):
        raise AssertionError("Heldout observation or case identity leaked into training data")

    labels = [_label(o, lineage) for o in heldout]
    train_labels = [_label(o, lineage) for o in observations if o["id"] in train_ids]
    kind_counts = {}
    for row in labels:
        kind_counts[row["observation_kind"]] = kind_counts.get(row["observation_kind"], 0) + 1
    out.mkdir(parents=True)
    (out / "train_data.json").write_text(json.dumps(train, indent=2) + "\n")
    (out / "train_config.json").write_text(json.dumps(config, indent=2) + "\n")
    (out / "heldout_labels.json").write_text(json.dumps({
        "schema_version":"solar-forum-heldout-labels/1", "salt_id":SALT,
        "selection_rule":"uint64_be(SHA256(salt + NUL + normalized_author)[:8]) modulo 5 equals 0",
        "estimand":"individual final-inspection-to-PTO report interval in the pooled selected-forum conditional frame",
        "labels":labels}, indent=2) + "\n")
    # This packet deliberately contains training labels only.  It is a future
    # prompt/evaluation resource, not an LLM run and not a copy of heldout text.
    (out / "llm_training_packet.json").write_text(json.dumps({
        "schema_version":"solar-forum-llm-training/1", "clock":"final_inspection_to_pto",
        "qualification":"Selected-forum report frame; no population, county, or agency transport claim.",
        "examples":[_label(o, lineage, include_evidence=True) for o in observations if o["id"] in train_ids]}, indent=2) + "\n")
    accounting = {"schema_version":"solar-forum-evaluation-split/1", "salt_id":SALT,
        "source_hashes":{"data":sha(data_path),"config":sha(config_path),"lineage":sha(lineage_path)},
        "observations_total":len(observations),"contributor_groups_total":len(groups),
        "training_observations":len(train_ids),"training_contributor_groups":len(groups-test_groups),
        "heldout_observations":len(labels),"heldout_contributor_groups":len(test_groups),
        "heldout_kind_counts":kind_counts,
        "heldout_bounds":{"exact_or_rounded_intervals":sum(x["upper"] is not None for x in labels),
                          "right_censored":sum(x["upper"] is None for x in labels)},
        "heldout_case_ids":sorted(heldout_cases),
        "leakage_checks":{"heldout_ids_absent_from_train_data":True,
                          "heldout_ids_absent_from_llm_training_packet":True,
                          "heldout_frame_membership_removed":True},
        "qualification":"Exploratory pooled selected-report-frame prediction; not county/agency, structure, or population validation."}
    (out / "split_accounting.json").write_text(json.dumps(accounting, indent=2) + "\n")
    return accounting


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data",type=Path,required=True);ap.add_argument("--config",type=Path,required=True)
    ap.add_argument("--lineage",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--refresh-llm-only",action="store_true")
    args=ap.parse_args()
    if args.refresh_llm_only:
        train=json.loads((args.out/"train_data.json").read_bytes())
        lineage_rows=json.loads(args.lineage.read_bytes());lineage={x["observation_id"]:x for x in lineage_rows}
        observations=[o for p in train["programs"] for o in p["observations"]]
        packet={"schema_version":"solar-forum-llm-training/1","clock":"final_inspection_to_pto",
          "qualification":"Selected-forum report frame; no population, county, or agency transport claim.",
          "examples":[_label(o,lineage,include_evidence=True) for o in observations]}
        (args.out/"llm_training_packet.json").write_text(json.dumps(packet,indent=2)+"\n")
        print(json.dumps({"examples":len(observations),"out":str(args.out/"llm_training_packet.json")},indent=2));return
    if args.out.exists(): raise FileExistsError(args.out)
    print(json.dumps(prepare(args.data.resolve(),args.config.resolve(),args.lineage.resolve(),args.out.resolve()),indent=2))


if __name__=="__main__": main()
