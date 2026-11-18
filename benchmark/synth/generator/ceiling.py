"""ceiling.json + tasks.json: what the public corpus provably permits.

For each target process we take every artifact *about* that process (its own
artifacts, the shared per-jurisdiction pages whose reveals name it, and the
state-level statute text / bill analysis for its statute) and reduce the
`reveals` entries to a best fidelity per (activity, field):

    exact > approximate > vague > wrong        (missing = hidden)

Two mapping rules:

* a **statute-level** reveal (``level: "statute"``, ``ref`` = element id) credits
  the activity implementing that element at **approximate** -- the statute proves
  the step exists but not how this jurisdiction runs it;
* a reveal whose value describes the superseded version (``describes_prior``) is
  counted as **wrong** for the current truth, which is what makes staleness a
  scoreable error rather than an invisible one;
* a ``staff_only`` activity flagged ``statutorily_disclosed`` (it implements a
  statute or public-ordinance element) is credited at **approximate** for
  ``exists`` even when no artifact names it -- any document restating the mandate
  discloses the step, so scoring it as hidden would penalise a solver that
  correctly infers it. Its actor and timing stay hidden unless an artifact reveals
  them. The count is reported per task as ``statutorily_disclosed_credited``
  (DESIGN.md "Wave-2/3 finding: statutory mandates cannot be hidden").

`timing_ceiling` compares the true log median with the best estimate an agent
could form from the *reported* timelines in user posts -- the complaint-selection
bias, measurable by construction (plan §1 row 7).
"""
from __future__ import annotations

from .decision import decision_ceiling
from .rng import median, r2

RANK = {"exact": 3, "approximate": 2, "vague": 1, "wrong": 0}
NAME = {3: "exact", 2: "approximate", 1: "vague", 0: "wrong"}
PUBLIC_KINDS = None      # every emitted spec is public: an `sop` spec exists only
                         # when the publication draw succeeded (records request/audit)


def _about(spec: dict, proc: dict) -> bool:
    mid = proc["model_id"]
    if spec.get("stat_id") == proc["stat_id"] and spec.get("jur") == proc["jur_id"]:
        return True
    if spec.get("stat_id") == proc["stat_id"] and spec.get("jur") is None:
        return True          # statute text / bill analysis
    return any(r.get("process") == mid for r in spec.get("reveals", []))


def build_ceiling(world: dict, statutes: dict, processes: dict, summaries: dict,
                  specs: list[dict]) -> tuple[list[dict], list[dict]]:
    ceilings, tasks = [], []
    by_mid_specs: dict[str, list[dict]] = {}
    for mid, proc in sorted(processes.items()):
        if proc["state"] != "Marisol":
            continue
        by_mid_specs[mid] = [s for s in specs if _about(s, proc)]

    for mid, proc in sorted(processes.items()):
        if proc["state"] != "Marisol":
            continue
        summ = summaries[mid]
        stat = statutes[proc["stat_id"]]
        mine = by_mid_specs[mid]
        el_to_act = {a["element_ref"]: a["id"] for a in proc["activities"] if a["element_ref"]}
        best: dict[str, dict[str, tuple[int, str, str]]] = {}   # act -> field -> (rank, artifact, value)
        from_artifact: set[str] = set()   # refs a *document* describes (not merely mandated)

        for s in mine:
            for r in s.get("reveals", []):
                if r.get("process") and r["process"] != mid:
                    continue
                ref, field = r["ref"], r["field"]
                fid = RANK[r["fidelity"]]
                if r.get("describes_prior"):
                    fid = 0                       # stale fact = wrong for the current version
                if r.get("level") == "statute":
                    aid = el_to_act.get(ref)
                    if not aid:
                        continue
                    fid = min(fid, RANK["approximate"])
                    ref = aid
                elif ref in ("process", "statute", "prior_version"):
                    ref = "process"
                if ref != "process" and ref not in {a["id"] for a in proc["activities"]}:
                    continue
                if r.get("level") != "statute":
                    from_artifact.add(ref)
                slot = best.setdefault(ref, {})
                cur = slot.get(field)
                if cur is None or fid > cur[0]:
                    slot[field] = (fid, s["artifact_id"], str(r["value"])[:160])

        acts = proc["activities"]
        rec_exact, rec_approx, only_wrong, hidden = [], [], [], []
        credited: list[str] = []   # staff-only steps credited by public law, not by a document
        for a in acts:
            slot = best.get(a["id"], {})
            ex = slot.get("exists")
            score = ex[0] if ex else max([v[0] for v in slot.values()], default=None)
            if score is None:
                # A mandated step is inferable from the statute/ordinance even when no
                # artifact names it: credit its *existence* at `approximate` only --
                # its actor and timing stay hidden (DESIGN.md Wave-2/3 finding).
                if a.get("statutorily_disclosed"):
                    rec_approx.append(a["id"])      # inferable from the mandate alone
                else:
                    hidden.append(a["id"])
            elif score == 3:
                rec_exact.append(a["id"])
            elif score >= 1:
                rec_approx.append(a["id"])
            else:
                only_wrong.append(a["id"])

        # audit: staff-only mandated steps whose credit rests on public law only --
        # either the statute text/bill analysis reveals the element (level="statute")
        # or nothing does and the mandate itself carries it.
        credited = [a["id"] for a in acts
                    if a.get("statutorily_disclosed") and a["id"] not in from_artifact]

        # process-level facts (end-to-end timing, the published sequence, volumes)
        proc_level = {f: {"fidelity": NAME[v[0]], "artifact": v[1], "value": v[2]}
                      for f, v in sorted(best.get("process", {}).items())}
        field_cov = {}
        for field in ("actor", "timing", "fee", "rework", "artifact"):
            rel = [a for a in acts if (field != "fee" or (a["fee"] and a["fee"].get("amount")))]
            got = {"exact": 0, "approximate": 0, "vague": 0, "wrong": 0, "hidden": 0}
            for a in rel:
                v = best.get(a["id"], {}).get(field)
                got[NAME[v[0]] if v else "hidden"] += 1
            field_cov[field] = {"relevant": len(rel), **got}

        # ---- timing ceiling from user posts ---------------------------------
        posts = [s for s in mine if s["kind"] in ("reddit_thread", "forum_thread") and s.get("persona")]
        reported = [s["persona"]["reported_timeline"]["total_days_reported"] for s in posts]
        true_of_posters = [s["persona"]["true_timeline"]["total_days"] for s in posts]
        doc_timing = [{"artifact_id": s["artifact_id"], "kind": s["kind"], "fidelity": r["fidelity"],
                       "value": r["value"]}
                      for s in mine for r in s.get("reveals", [])
                      if r["ref"] in ("process",) and r["field"] == "timing"]
        true_med = summ["elapsed_days"]["median"]
        timing = {
            "true_median_days": true_med,
            "true_p90_days": summ["elapsed_days"]["p90"],
            "best_estimate_from_posts": r2(median(reported)) if reported else None,
            "n_posts_with_timing": len(reported),
            "poster_true_median_days": r2(median(true_of_posters)) if true_of_posters else None,
            "selection_bias_days": r2(median(true_of_posters) - true_med) if true_of_posters else None,
            "report_bias_days": r2(median(reported) - median(true_of_posters)) if reported else None,
            "log_ratio_error_if_believed": r2((median(reported) / true_med) if reported and true_med else 0.0),
            "document_timing_facts": doc_timing,
        }

        n = len(acts)
        dc = decision_ceiling(proc, mine)
        ceilings.append({
            "task_id": "%s__%s" % (world["world"], mid),
            "model_id": mid,
            "elements_total": n,
            "activities_by_visibility": {
                v: sum(1 for a in acts if a["visibility"] == v)
                for v in ("applicant_facing", "applicant_inferable", "staff_only")},
            "recoverable_exact": rec_exact,
            "recoverable_approx": rec_approx,
            "only_wrong": only_wrong,
            "hidden": hidden,
            "coverage": {
                "exists_exact": r2(len(rec_exact) / n), "exists_any": r2((n - len(hidden) - len(only_wrong)) / n),
                "hidden_share": r2(len(hidden) / n),
                "staff_only_recovered": sum(1 for a in acts if a["visibility"] == "staff_only"
                                            and a["id"] in rec_exact + rec_approx),
                "staff_only_recovered_from_artifacts": sum(
                    1 for a in acts if a["visibility"] == "staff_only" and a["id"] in from_artifact),
                "staff_only_statutorily_disclosed": sum(
                    1 for a in acts if a.get("statutorily_disclosed")),
            },
            "statutorily_disclosed_credited": len(credited),
            "statutorily_disclosed_ids": credited,
            "field_coverage": field_cov,
            "process_level_facts": proc_level,
            "order_recoverable": proc_level.get("order", {}).get("fidelity", "hidden"),
            "timing_ceiling": timing,
            "decision_ceiling": dc,
            "artifacts_about_process": sorted(s["artifact_id"] for s in mine),
            "artifact_kinds": sorted({s["kind"] for s in mine}),
            "raising_artifacts": sorted({v[1] for slot in best.values() for v in slot.values()
                                         if v[0] == 3}),
            "distractor_count": len(specs) - len(mine),
            "why": ("ceiling computed from %d public artifacts (%s); %d of %d activities exact, %d approximate, "
                    "%d only-wrong, %d hidden; %d staff-only steps recovered%s%s"
                    % (len(mine), ", ".join(sorted({s["kind"] for s in mine})), len(rec_exact), n,
                       len(rec_approx), len(only_wrong), len(hidden),
                       sum(1 for a in acts if a["visibility"] == "staff_only" and a["id"] in rec_exact + rec_approx),
                       "; an SOP was published (records request), which raises the ceiling"
                       if any(s["kind"] == "sop" for s in mine) else "",
                       ("; %d staff-only step(s) credited from the public mandate alone, no document "
                        "describes them (%s)" % (len(credited), ", ".join(credited))) if credited else "")),
        })

        prompt = ("Construct the process model and expected timeline for the %s in %s, under %s. "
                  "Give every activity (who does it, on what occasion, producing what), the order and "
                  "rework loops, the fees, and the median and p90 elapsed time, with per-element "
                  "confidence and the evidence you used."
                  % (proc["program_name"], proc["jurisdiction"], stat["cite"]))
        gold = {"process_truth": "truth/processes/%s.json" % mid,
                "log_summary": "truth/log/%s.summary.json" % mid,
                "ceiling": "ceiling.json#%s" % mid}
        if proc.get("decision_model"):
            prompt += (" Also state the eligibility and compliance criteria as this jurisdiction applies "
                       "them: for each criterion give the case fact it tests, the threshold or standard "
                       "used here, whether a failure can be corrected or is a denial, and which step "
                       "checks it.")
            gold["decision_model"] = "truth/processes/%s.json#decision_model" % mid
        tasks.append({
            "task_id": "%s__%s" % (world["world"], mid),
            "world": world["world"],
            "jur": proc["jur_id"],
            "jurisdiction": proc["jurisdiction"],
            "stat_id": proc["stat_id"],
            "program_name": proc["program_name"],
            "prompt": prompt,
            "conditions": ["search", "oracle_docs", "oracle_no_distractors", "declared_only", "declared_plus_users"],
            "gold": gold,
            "n_activities": n,
            "n_actors": len(proc["actors"]),
        })
    return ceilings, tasks
