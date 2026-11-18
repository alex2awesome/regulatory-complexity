"""Validate a generated world against benchmark/synth/schemas/ and print counts.

    python3 benchmark/synth/schemas/validate.py --world benchmark/synth/worlds/W1
    python3 benchmark/synth/schemas/validate.py --world ... --quiet   # counts only

Standalone (no imports from the generator, stdlib only). It contains a small
JSON-Schema-subset validator -- type (including type unions), required,
properties, items, enum -- plus the structural invariants that a schema cannot
express and that actually matter for this benchmark:

  * activities 8-20, actors 4-11 (DESIGN bounds);
  * every edge and every `rework.back_to` resolves, and rework points *backwards*
    in the activity order (a forward "rework" edge is a modelling bug);
  * `element_ref` resolves to the statute skeleton (E*) or the local rule (L*);
  * `must_not_reveal` contains only staff-only activities and never intersects
    the same artifact's `reveals` (no leakage in the spec itself);
  * every `links_to` target exists (the mock web's link graph is closed);
  * ceiling ⊆ truth: the four recoverability buckets partition the activity ids
    exactly, and nothing in `hidden` is revealed by any artifact about the process;
  * log paths only visit activities that exist, and elapsed times are >= 0.

Exit code 0 = valid, 1 = errors found.
"""
from __future__ import annotations

import argparse
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

# --------------------------------------------------------------- validator --


def _types_ok(value, t) -> bool:
    if isinstance(t, list):
        return any(_types_ok(value, x) for x in t)
    return {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }[t](value)


def validate(node, schema: dict, path: str, errors: list):
    if "enum" in schema:
        if node not in schema["enum"]:
            errors.append("%s: %r not in enum %s" % (path, node, schema["enum"]))
        return
    if "type" in schema and not _types_ok(node, schema["type"]):
        errors.append("%s: expected %s, got %s" % (path, schema["type"], type(node).__name__))
        return
    if isinstance(node, dict):
        for key in schema.get("required", []):
            if key not in node:
                errors.append("%s: missing required key %r" % (path, key))
        for key, sub in schema.get("properties", {}).items():
            if key in node:
                validate(node[key], sub, "%s.%s" % (path, key), errors)
    elif isinstance(node, list) and "items" in schema:
        for i, item in enumerate(node):
            validate(item, schema["items"], "%s[%d]" % (path, i), errors)


def load_schema(name: str) -> dict:
    return json.loads((HERE / (name + ".schema.json")).read_text())


def read(p: pathlib.Path):
    return json.loads(p.read_text())


def read_jsonl(p: pathlib.Path):
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# ------------------------------------------------------------------ checks --

BASE_PROCESS_REQUIRED = ["model_id", "source", "actors", "activities", "edges"]   # base schema


def check_world(root: pathlib.Path, quiet=False) -> int:
    errors: list[str] = []
    warn: list[str] = []
    world = read(root / "world.json")
    schemas = {n: load_schema(n) for n in ("statute_truth", "local_rule_truth", "process_truth",
                                          "artifact_spec", "ceiling", "tasks")}

    statutes = {p.stem: read(p) for p in sorted((root / "truth/statutes").glob("*.json"))}
    rules = {p.stem: read(p) for p in sorted((root / "truth/local_rules").glob("*.json"))}
    procs = {p.stem: read(p) for p in sorted((root / "truth/processes").glob("*.json"))}
    specs = {p.stem: read(p) for p in sorted((root / "specs").glob("*.json"))}
    ceiling = read(root / "ceiling.json")
    tasks = read(root / "tasks.json")

    for sid, s in statutes.items():
        validate(s, schemas["statute_truth"], "statute[%s]" % sid, errors)
    for mid, r in rules.items():
        validate(r, schemas["local_rule_truth"], "local_rule[%s]" % mid, errors)
    validate(ceiling, schemas["ceiling"], "ceiling", errors)
    validate(tasks, schemas["tasks"], "tasks", errors)

    vis_counts = {"applicant_facing": 0, "applicant_inferable": 0, "staff_only": 0}
    for mid, p in procs.items():
        validate(p, schemas["process_truth"], "process[%s]" % mid, errors)
        for k in BASE_PROCESS_REQUIRED:                      # base-schema compatibility
            if k not in p:
                errors.append("process[%s]: missing base-schema key %r" % (mid, k))
        acts = p["activities"]
        ids = [a["id"] for a in acts]
        order = {a["id"]: i for i, a in enumerate(acts)}
        if not 8 <= len(acts) <= 20:
            errors.append("process[%s]: %d activities (DESIGN bound 8-20)" % (mid, len(acts)))
        if not 4 <= len(p["actors"]) <= 11:
            errors.append("process[%s]: %d actors (DESIGN bound 4-11)" % (mid, len(p["actors"])))
        actor_ids = {a["id"] for a in p["actors"]}
        skel = {e["element_id"] for e in statutes[p["stat_id"]]["skeleton"]}
        local = {e["element_id"] for e in rules[mid]["added_elements"]}
        for a in acts:
            vis_counts[a["visibility"]] += 1
            if a["actor"] not in actor_ids:
                errors.append("process[%s].%s: actor %r not in actors" % (mid, a["id"], a["actor"]))
            if a["element_ref"] and a["element_ref"] not in skel | local:
                errors.append("process[%s].%s: element_ref %s resolves to neither statute nor local rule"
                              % (mid, a["id"], a["element_ref"]))
            if a["timing"]["p90_days"] < a["timing"]["median_days"]:
                errors.append("process[%s].%s: p90 < median" % (mid, a["id"]))
            if a["rework"]:
                bt = a["rework"]["back_to"]
                if bt not in order:
                    errors.append("process[%s].%s: rework back_to %s does not exist" % (mid, a["id"], bt))
                elif order[bt] >= order[a["id"]]:
                    errors.append("process[%s].%s: rework points forward to %s" % (mid, a["id"], bt))
        for e in p["edges"]:
            if e["from"] not in order or e["to"] not in order:
                errors.append("process[%s]: edge %s->%s references a missing activity"
                              % (mid, e["from"], e["to"]))
            elif e["type"] == "rework" and order[e["to"]] >= order[e["from"]]:
                errors.append("process[%s]: rework edge %s->%s is not backwards"
                              % (mid, e["from"], e["to"]))
        if p["terminal_artifact"] not in {x for a in acts for x in a["artifacts_out"]}:
            warn.append("process[%s]: terminal artifact %r is not produced by any activity"
                        % (mid, p["terminal_artifact"]))
        # decision layer (decision.py): predicates attach to real activities, readings
        # are well-formed, corrections point backwards
        dm = p.get("decision_model")
        if dm:
            pids = [e["pred_id"] for e in dm["predicates"]]
            if len(pids) != len(set(pids)):
                errors.append("process[%s]: duplicate predicate ids" % mid)
            by_id = {a["id"]: a for a in acts}
            for e in dm["predicates"]:
                if e["evaluated_at"] not in by_id:
                    errors.append("process[%s]: predicate %s evaluated at unknown activity %s"
                                  % (mid, e["pred_id"], e["evaluated_at"]))
                elif e["pred_id"] not in (by_id[e["evaluated_at"]].get("evaluates") or []):
                    errors.append("process[%s]: activity %s does not list predicate %s"
                                  % (mid, e["evaluated_at"], e["pred_id"]))
                r = e.get("reading")
                if e["kind"] not in ("crisp", "standard", "delegated", "local", "capped"):
                    errors.append("process[%s]: predicate %s has unknown kind %r"
                                  % (mid, e["pred_id"], e["kind"]))
                # A capped dimension must record the statutory bound and every
                # lawful reading must respect it (plan section 12).
                if e["kind"] == "capped":
                    bound = e.get("bound")
                    val = (e.get("reading") or {}).get("value")
                    op = (e.get("reading") or {}).get("op")
                    if bound is None:
                        errors.append("process[%s]: capped predicate %s records no statutory bound"
                                      % (mid, e["pred_id"]))
                    elif isinstance(val, (int, float)) and not isinstance(val, bool):
                        if op in ("ge", "gt") and val > bound:
                            errors.append("process[%s]: capped predicate %s demands %s, above its bound %s"
                                          % (mid, e["pred_id"], val, bound))
                        if op in ("le", "lt") and val > bound:
                            errors.append("process[%s]: capped predicate %s allows %s, above its bound %s"
                                          % (mid, e["pred_id"], val, bound))
                if not r or r.get("op") not in ("lt", "le", "gt", "ge", "eq", "ne", "in", "not_in", "always", "bern"):
                    errors.append("process[%s]: predicate %s has no valid reading" % (mid, e["pred_id"]))
                if e["fixable"] and (e["correction_back_to"] not in order
                                     or order[e["correction_back_to"]] >= order[e["evaluated_at"]]):
                    errors.append("process[%s]: predicate %s correction target does not point backwards"
                                  % (mid, e["pred_id"]))
        # log
        logp = root / ("truth/log/%s.jsonl" % mid)
        if not logp.exists():
            errors.append("process[%s]: no simulated log" % mid)
            continue
        recs = read_jsonl(logp)
        summ = read(root / ("truth/log/%s.summary.json" % mid))
        if summ["n_applicants"] != len(recs):
            errors.append("log[%s]: summary n=%d but %d records" % (mid, summ["n_applicants"], len(recs)))
        for rec in recs[:50]:
            if rec["elapsed_days"] < 0:
                errors.append("log[%s] %s: negative elapsed" % (mid, rec["applicant_id"]))
            for step in rec["path"]:
                if step["a"] not in order:
                    errors.append("log[%s] %s: unknown activity %s" % (mid, rec["applicant_id"], step["a"]))
                    break

    # ---- specs -----------------------------------------------------------
    by_kind: dict[str, list[int]] = {}
    for aid, s in specs.items():
        validate(s, schemas["artifact_spec"], "spec[%s]" % aid, errors)
        row = by_kind.setdefault(s["kind"], [0, 0])
        row[0 if s["target"] else 1] += 1
        for l in s["links_to"]:
            if l not in specs:
                errors.append("spec[%s]: links_to unknown artifact %s" % (aid, l))
        # process-qualified hidden ids on shared (multi-process) artifacts
        for q in [x for x in s["must_not_reveal"] if ":" in x]:
            qm, qa = q.split(":", 1)
            if qm not in procs:
                errors.append("spec[%s]: must_not_reveal names unknown process %s" % (aid, qm))
            elif qa not in {a["id"] for a in procs[qm]["activities"]
                            if a["visibility"] == "staff_only"}:
                errors.append("spec[%s]: %s is not a staff-only activity of %s" % (aid, qa, qm))
            else:
                shown = {r["ref"] for r in s["reveals"] if r.get("process") == qm}
                if qa in shown:
                    errors.append("spec[%s]: reveals %s of %s although it is hidden" % (aid, qa, qm))
        mid = None
        if s.get("jur") and s.get("stat_id"):
            mid = "%s__%s" % (s["jur"], s["stat_id"])
        if mid in procs:
            proc = procs[mid]
            staff = {a["id"] for a in proc["activities"] if a["visibility"] == "staff_only"}
            revealed = {r["ref"] for r in s["reveals"]}
            bad = {x for x in s["must_not_reveal"] if ":" not in x} - staff
            if bad:
                errors.append("spec[%s]: must_not_reveal contains non-staff ids %s" % (aid, sorted(bad)))
            overlap = {x for x in s["must_not_reveal"] if ":" not in x} & revealed
            if overlap:
                errors.append("spec[%s]: reveals and must_not_reveal overlap on %s" % (aid, sorted(overlap)))
            unknown = {r for r in revealed
                       if r not in {a["id"] for a in proc["activities"]}
                       and r not in ("process", "statute", "prior_version")
                       and not r.startswith(("E", "L", "P", "Q"))}
            if unknown:
                errors.append("spec[%s]: reveals unknown refs %s" % (aid, sorted(unknown)))
            pids = {e["pred_id"] for e in (proc.get("decision_model") or {}).get("predicates", [])}
            crit = {r["ref"] for r in s["reveals"] if r.get("field") == "criterion"}
            if crit - pids:
                errors.append("spec[%s]: criterion reveals name unknown predicates %s" % (aid, sorted(crit - pids)))
            mnc = set(s.get("must_not_reveal_criteria", []))
            if mnc - pids:
                errors.append("spec[%s]: must_not_reveal_criteria names unknown predicates %s" % (aid, sorted(mnc - pids)))
            if mnc & crit:
                errors.append("spec[%s]: criterion reveals and must_not_reveal_criteria overlap on %s"
                              % (aid, sorted(mnc & crit)))

    # ---- ceiling ⊆ truth --------------------------------------------------
    cov = []
    for c in ceiling:
        mid = c["model_id"]
        if mid not in procs:
            errors.append("ceiling[%s]: no such process" % mid)
            continue
        ids = {a["id"] for a in procs[mid]["activities"]}
        buckets = c["recoverable_exact"] + c["recoverable_approx"] + c["only_wrong"] + c["hidden"]
        if sorted(buckets) != sorted(ids):
            errors.append("ceiling[%s]: buckets do not partition the %d activity ids (got %d, dups=%s, extra=%s)"
                          % (mid, len(ids), len(buckets), len(buckets) - len(set(buckets)),
                             sorted(set(buckets) - ids)))
        if c["elements_total"] != len(ids):
            errors.append("ceiling[%s]: elements_total %d != %d activities" % (mid, c["elements_total"], len(ids)))
        # nothing in `hidden` may be revealed by any artifact about this process
        about = [s for s in specs.values() if s["artifact_id"] in c["artifacts_about_process"]]
        revealed = {r["ref"] for s in about for r in s["reveals"]
                    if not r.get("process") or r.get("process") == mid}
        leaked = set(c["hidden"]) & revealed
        if leaked:
            errors.append("ceiling[%s]: %s marked hidden but revealed" % (mid, sorted(leaked)))
        t = c["timing_ceiling"]
        if t["n_posts_with_timing"] == 0 and t["best_estimate_from_posts"] is not None:
            errors.append("ceiling[%s]: timing estimate without posts" % mid)
        dc = c.get("decision_ceiling")
        if dc:
            pids = {e["pred_id"] for e in (procs[mid].get("decision_model") or {}).get("predicates", [])}
            b = dc["recoverable_exact"] + dc["recoverable_approx"] + dc["only_wrong"] + dc["hidden"]
            if sorted(b) != sorted(pids):
                errors.append("ceiling[%s]: decision buckets do not partition the %d predicate ids" % (mid, len(pids)))
            revealed_c = {r["ref"] for s in about for r in s["reveals"] if r.get("field") == "criterion"
                          and (not r.get("process") or r.get("process") == mid)}
            if set(dc["hidden"]) & revealed_c:
                errors.append("ceiling[%s]: criteria %s marked hidden but revealed" % (mid, sorted(set(dc["hidden"]) & revealed_c)))
        cov.append(c)

    task_ids = {t["task_id"] for t in tasks}
    if task_ids != {c["task_id"] for c in ceiling}:
        errors.append("tasks and ceiling disagree on task ids")

    # ---- report ----------------------------------------------------------
    n_t = sum(v[0] for v in by_kind.values())
    n_d = sum(v[1] for v in by_kind.values())
    if not quiet:
        print("world %s (seed %s), %s" % (world["world"], world["seed"], root))
        print("  statutes            %3d  (%d Marisol, %d Corvane look-alikes)"
              % (len(statutes), sum(1 for s in statutes.values() if s["state"] == "Marisol"),
                 sum(1 for s in statutes.values() if s["state"] != "Marisol")))
        print("  local rules         %3d  (%d with template lineage, %d with a prior version, %d retrofits)"
              % (len(rules), sum(1 for r in rules.values() if r["lineage_from"]),
                 sum(1 for r in rules.values() if r["prior_version"]),
                 sum(1 for r in rules.values() if r.get("retrofit"))))
        print("  processes           %3d  (%d target, %d look-alike)"
              % (len(procs), len(tasks), len(procs) - len(tasks)))
        print("  activities          %3d  applicant_facing=%d applicant_inferable=%d staff_only=%d"
              % (sum(vis_counts.values()), vis_counts["applicant_facing"],
                 vis_counts["applicant_inferable"], vis_counts["staff_only"]))
        print("  rework loops        %3d" % sum(1 for p in procs.values()
                                                for a in p["activities"] if a["rework"]))
        print("  log records         %3d" % sum(read(root / ("truth/log/%s.summary.json" % m))["n_applicants"]
                                                for m in procs))
        print("  specs               %3d  (target=%d distractor=%d ratio=%.2f, knob=%.1f)"
              % (len(specs), n_t, n_d, n_d / max(1, n_t), world["knobs"]["distractor_ratio"]))
        for kind in sorted(by_kind):
            print("      %-22s target=%-4d distractor=%-4d" % (kind, by_kind[kind][0], by_kind[kind][1]))
        print("  stale specs         %3d" % sum(1 for s in specs.values() if s.get("stale")))
        if cov:
            m = lambda f: sum(f(c) for c in cov) / len(cov)
            print("  ceiling (mean over %d tasks): exists_exact=%.2f exists_any=%.2f hidden=%.2f "
                  "staff_only_recovered=%.2f" % (len(cov), m(lambda c: c["coverage"]["exists_exact"]),
                                                 m(lambda c: c["coverage"]["exists_any"]),
                                                 m(lambda c: c["coverage"]["hidden_share"]),
                                                 m(lambda c: c["coverage"]["staff_only_recovered"])))
            withposts = [c for c in cov if c["timing_ceiling"]["n_posts_with_timing"]]
            if withposts:
                print("  timing ceiling: %d/%d tasks have user timing; mean log-ratio if believed=%.2f; "
                      "mean selection bias=%+.0f days"
                      % (len(withposts), len(cov),
                         sum(c["timing_ceiling"]["log_ratio_error_if_believed"] for c in withposts) / len(withposts),
                         sum(c["timing_ceiling"]["selection_bias_days"] for c in withposts) / len(withposts)))
            sd = sum(c["coverage"].get("staff_only_statutorily_disclosed", 0) for c in cov)
            cr = sum(c.get("statutorily_disclosed_credited", 0) for c in cov)
            print("  statutorily disclosed: %d staff-only steps implement a public mandate; %d credited "
                  "from the mandate alone (no document describes them)" % (sd, cr))
            print("  order recoverable:  %d/%d tasks exact"
                  % (sum(1 for c in cov if c.get("order_recoverable") == "exact"), len(cov)))
        print("  tasks               %3d" % len(tasks))
        for w in warn[:10]:
            print("  WARN %s" % w)
    if errors:
        print("\n%d ERROR(S):" % len(errors))
        for e in errors[:40]:
            print("  - %s" % e)
        if len(errors) > 40:
            print("  ... and %d more" % (len(errors) - 40))
        return 1
    print("\nOK: %d objects validated, 0 errors%s"
          % (len(statutes) + len(rules) + len(procs) + len(specs) + len(ceiling) + len(tasks),
             ", %d warning(s)" % len(warn) if warn else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a synthetic world directory.")
    ap.add_argument("--world", required=True, help="path to benchmark/synth/worlds/<W>")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    return check_world(pathlib.Path(args.world), args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
