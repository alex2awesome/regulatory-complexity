#!/usr/bin/env python3
"""Process-layer models for a rule: build per-jurisdiction graphs from
declared steps, compute process metrics, check coverage of the statute's
mandated elements, and compare across jurisdictions.

  python3 process_model.py --declared ../corpus/ab2533/process/declared_processes.json \
      [--skeleton ../examples/ab2533/process/skeleton.json] --out ../examples/ab2533/process
"""
import argparse, json, pathlib, re, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import load

CANON = {"applicant": "applicant", "third_party": "third_party", "planning": "planning",
         "building": "building", "inspector": "inspector", "county": "county",
         "planning/building": "building", "other": "official"}

# heuristic keyword map: statute-mandated element -> declared-step cue words
ELEMENT_CUES = {
    "checklist_publication": ["checklist"],
    "notice": ["inform", "notif", "option", "may obtain"],
    "third_party_option": ["third-party", "third party", "licensed contractor"],
    "application": ["submit", "apply", "application"],
    "inspection": ["inspect"],
    "correction_permits": ["correct", "corrective", "violation"],
    "fee_waiver": ["fee", "impact"],
    "decision": ["approve", "approval", "decision", "recogniz"],
    "terminal_issuance": ["issue", "certificate", "permit"],
}


def norm_actor(a):
    a = a.lower()
    if "or" in a and "third" in a:
        return "inspector|third_party"
    for k, v in CANON.items():
        if a.startswith(k):
            return v
    return re.sub(r"[^a-z_]", "_", a.split()[0])


def declared_to_model(j):
    steps = sorted(j["steps"], key=lambda s: s["order"])
    acts, edges = [], []
    for s in steps:
        aid = f"a{s['order']}"
        text = s["step"].lower()
        acts.append({"id": aid, "name": s["step"][:140], "actor": norm_actor(s["actor"]),
                     "artifacts_out": [s.get("artifact", "")] if s.get("artifact") else [],
                     "optional": bool(re.search(r"\bmay\b|optional|if used|if required", text)),
                     "mandated_elements": [k for k, cues in ELEMENT_CUES.items()
                                           if any(c in text for c in cues)]})
    for a in acts:  # primary element: correction outranks inspection (a correction step mentions re-inspection)
        els = a["mandated_elements"]
        a["mandated_element"] = ("correction_permits" if "correction_permits" in els
                                 else els[0] if els else None)
    for a, b in zip(acts, acts[1:]):
        edges.append({"from": a["id"], "to": b["id"],
                      "type": "handoff" if a["actor"] != b["actor"] else "sequence"})
    # rework: a correction step loops back to the nearest EARLIER inspection step
    for i, a in enumerate(acts):
        if "correction_permits" not in a["mandated_elements"]:
            continue
        earlier = [b for b in acts[:i] if "inspection" in b["mandated_elements"]]
        if earlier:
            edges.append({"from": a["id"], "to": earlier[-1]["id"], "type": "rework",
                          "condition": "violations found -> correct -> re-inspect"})
    # jurisdiction-level credits: a published checklist / an offered third-party option count
    # even when no step text spells them out
    extra = []
    if j.get("checklist_url"):
        extra.append("checklist_publication")
    if j.get("third_party_inspection_offered") is True:
        extra += ["third_party_option", "notice"]
    if any(k in str(j.get("fees", "")).lower() for k in ("impact", "exempt", "waiv", "connection")):
        extra.append("fee_waiver")
    if extra:
        acts.append({"id": "j0", "name": "Jurisdiction-level: published checklist / third-party option notice",
                     "actor": "local_agency", "artifacts_out": [], "optional": False,
                     "mandated_elements": extra, "mandated_element": extra[0]})
    terminal = next((a["artifacts_out"][0] for a in reversed(acts) if a["artifacts_out"]), "")
    return {"model_id": f"declared_{re.sub(r'[^a-z]', '_', j['jurisdiction'].lower())[:24]}",
            "source": "declared", "jurisdiction": j["jurisdiction"], "citation_or_url": j.get("url", ""),
            "actors": sorted({a["actor"] for a in acts}), "activities": acts, "edges": edges,
            "terminal_artifact": terminal,
            "notes": f"third_party_inspection_offered={j.get('third_party_inspection_offered')}; fees={str(j.get('fees'))[:80]}"}


def metrics(m):
    acts, edges = m["activities"], m["edges"]
    return {"n_activities": len(acts), "n_actors": len(m["actors"]),
            "n_handoffs": sum(1 for e in edges if e["type"] == "handoff"),
            "n_rework_loops": sum(1 for e in edges if e["type"] == "rework"),
            "n_optional": sum(1 for a in acts if a.get("optional")),
            "n_artifacts": len({x for a in acts for x in a.get("artifacts_out", []) if x}),
            "elements_present": sorted({e for a in acts for e in a.get("mandated_elements", []) or ([a["mandated_element"]] if a.get("mandated_element") else [])}),
            "terminal_artifact": m.get("terminal_artifact", "")}


def coverage(model, skeleton):
    """Which statute-mandated elements does a declared process instantiate?"""
    mandated = sorted({a["mandated_element"] for a in skeleton["activities"] if a.get("mandated_element")})
    present = set(metrics(model)["elements_present"])
    return {"mandated": mandated, "present": sorted(present & set(mandated)),
            "missing": sorted(set(mandated) - present),
            "coverage": round(len(present & set(mandated)) / max(len(mandated), 1), 2)}


def mermaid(m):
    lines = ["flowchart TD"]
    for a in m["activities"]:
        label = f"{a['actor']}: {a['name'][:48]}".replace('"', "'")
        shape = f'{a["id"]}([\"{label}\"])' if a.get("optional") else f'{a["id"]}["{label}"]'
        lines.append("  " + shape)
    for e in m["edges"]:
        arrow = {"sequence": "-->", "handoff": "==>", "rework": "-.->", "optional": "-.->"}[e["type"]]
        lbl = f"|{e.get('condition','')}|" if e.get("condition") else ""
        lines.append(f"  {e['from']} {arrow}{lbl} {e['to']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--declared", required=True)
    ap.add_argument("--skeleton", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    d = load(args.declared)
    juris = d if isinstance(d, list) else list(d.get("jurisdictions", d.values()))
    skeleton = load(args.skeleton) if args.skeleton else None
    report = {"models": {}, "cross_jurisdiction": {}}
    for j in juris:
        m = declared_to_model(j)
        (out / f"{m['model_id']}.json").write_text(json.dumps(m, indent=2))
        (out / f"{m['model_id']}.mmd").write_text(mermaid(m))
        entry = {"metrics": metrics(m)}
        if skeleton:
            entry["coverage_of_statute"] = coverage(m, skeleton)
        report["models"][m["jurisdiction"]] = entry
        print(f"{m['jurisdiction'][:28]:28} acts={entry['metrics']['n_activities']} actors={entry['metrics']['n_actors']} "
              f"handoffs={entry['metrics']['n_handoffs']} rework={entry['metrics']['n_rework_loops']} "
              f"optional={entry['metrics']['n_optional']} terminal='{entry['metrics']['terminal_artifact'][:40]}'"
              + (f" coverage={entry['coverage_of_statute']['coverage']}" if skeleton else ""))
    if skeleton:
        (out / "skeleton.mmd").write_text(mermaid(skeleton))
    terms = {j: e["metrics"]["terminal_artifact"] for j, e in report["models"].items()}
    report["cross_jurisdiction"] = {
        "distinct_terminal_artifacts": len({t[:30] for t in terms.values()}),
        "activity_count_range": [min(e["metrics"]["n_activities"] for e in report["models"].values()),
                                 max(e["metrics"]["n_activities"] for e in report["models"].values())],
        "handoff_range": [min(e["metrics"]["n_handoffs"] for e in report["models"].values()),
                          max(e["metrics"]["n_handoffs"] for e in report["models"].values())],
    }
    (out / "process_report.json").write_text(json.dumps(report, indent=2))
    print("cross-jurisdiction:", report["cross_jurisdiction"])


if __name__ == "__main__":
    main()
