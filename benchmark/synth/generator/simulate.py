"""Monte-Carlo event log: the observed tier.

`n_applicants` synthetic applicants walk the designed graph. Each per-case
activity draws a cycle time from its lognormal (median, p90); optional
activities occur with `p_occurs`; `rework` sends the case back to `back_to`
(capped at `max_rework_rounds`); a denial is drawn at the decision activity with
`denial_rate`, inflated by the number of rework rounds; abandonment is a per
applicant-activity hazard calibrated so the overall share is `p_abandon_total`;
and flow gates (`if_denied`, `if_appealed`, `if_rework`) switch the denial,
appeal, and re-inspection tails on.

Arrivals are uniform over [program effective date .. as_of - 30d]. The legacy
`elapsed_days`/`censored` pair uses the last recorded decision (or abandonment),
not necessarily the first decision or the last modeled work. Explicit event
clocks additionally retain first decision, last decision and modeled-work end,
each with its own censoring status. Existing worlds without a visit-accounting
version retain their legacy values and RNG streams. New version-2 worlds count
actual repeated visits separately from loop triggers and charge base fees once.
"""
from __future__ import annotations

from .decision import cure, evaluate, sample_attributes
from . import capacity
from .rng import dadd, ddiff, median, next_workday, quantile, r2, sample_days, sub_rng

APPLICANT_ROLES = {"applicant", "third_party"}


def event_clock(arrived, end, outcome, as_of):
    """An absent event is not a zero-day completion; censoring is clock-specific."""
    if end is None:
        return {"end_date": None, "elapsed_days": None, "outcome": None,
                "provisional_outcome": None, "censored": None}
    censored = end > as_of
    return {"end_date": end, "elapsed_days": ddiff(end, arrived),
            "outcome": "in_progress" if censored else outcome,
            "provisional_outcome": outcome if censored else None, "censored": censored}


def event_timing_summary(records, name):
    clocks = [r.get("event_clocks", {}).get(name) for r in records]
    observed = [c for c in clocks if c is not None and c["end_date"] is not None and not c["censored"]]
    values = [c["elapsed_days"] for c in observed]
    counts = {}
    for c in observed:
        counts[c["outcome"]] = counts.get(c["outcome"], 0) + 1
    return {"n": len(values), "median": r2(median(values)) if values else None,
            "p90": r2(quantile(values, .9)) if values else None, "observed_outcomes": counts,
            "n_censored": sum(c is not None and c["censored"] is True for c in clocks),
            "n_no_event": sum(c is None or c["end_date"] is None for c in clocks)}


def simulate_process(world: dict, proc: dict, rule: dict, n: int) -> tuple[list[dict], dict]:
    knobs = world["knobs"]
    as_of = knobs["as_of"]
    acts = [a for a in proc["activities"] if a.get("per_case", True)]
    idx = {a["id"]: i for i, a in enumerate(acts)}
    n_applicant_steps = max(1, sum(1 for a in acts if a["actor"] in APPLICANT_ROLES))
    hazard = knobs["p_abandon_total"] / (n_applicant_steps * 2.4)
    max_rounds = knobs["max_rework_rounds"]
    accounting_version=knobs.get('visit_accounting_version',1)
    # 1 = legacy: an uncured fixable predicate denies the case.
    # 2 = it stalls the case instead, with no decision recorded, which is
    #     what the real outcome distribution shows.
    outcome_model_version = knobs.get('outcome_model_version', 1)
    # P(the applicant was pre-filtered against the hard eligibility tests).
    # 0.0 reproduces the legacy pool exactly; see decision.sample_attributes.
    p_self_select = float(knobs.get('p_self_select', 0.0))
    if accounting_version not in (1,2):
        raise ValueError('Unsupported visit-accounting version')
    # decision layer (decision.py): under version 2, outcomes and corrections follow
    # predicate evaluations over sampled case facts instead of free rates
    dm = proc.get("decision_model") if int(knobs.get("decision_model_version", 1)) >= 2 else None
    p_cure = float(knobs.get("p_cure", 0.8))
    evaluates: dict[str, list[dict]] = {}
    if dm:
        for e in dm["predicates"]:
            evaluates.setdefault(e["evaluated_at"], []).append(e)

    start_floor = rule["effective"]
    window_start = max(start_floor, dadd(as_of, -knobs["sim_window_days"]))
    # leave room for a typical case to finish before as_of, so censoring stays modest
    est = sum(a["timing"]["median_days"] for a in acts if a.get("blocking", True))
    window_end = dadd(as_of, -int(max(30, 1.5 * est)))
    span = max(ddiff(window_end, window_start), 30)

    records: list[dict] = []
    for k in range(n):
        rng = sub_rng(world["seed"], "sim", proc["model_id"], k)
        arrived = next_workday(dadd(window_start, rng.randrange(span)))
        occurs = {a["id"]: (rng.random() < (a["p_occurs"] or 0.35)) if a["optional"] else True
                  for a in acts}
        cursor = arrived            # the case clock (blocking steps only)
        last_end = arrived          # including parallel back-office work
        path, rounds, rework_events = [], {}, []
        visits,charged_base_fees = {},set()
        fees = 0.0
        decision_end = None
        first_decision_end = first_decision_outcome = last_decision_outcome = None
        stalled = False
        u_deny = rng.random()       # one denial draw per applicant (no compounding on rework)
        attrs = (sample_attributes(dm["predicates"],
                                   sub_rng(world["seed"], "case_attrs", proc["model_id"], k),
                                   p_self_select=p_self_select)
                 if dm else None)
        pred_results: dict = {}
        fatal_fail = False
        open_fixable: dict[str, dict] = {}
        denied = appealed = abandoned = False
        had_rework = False
        i, guard = 0, 0
        while i < len(acts) and guard < 400:
            guard += 1
            a = acts[i]
            gate = a["flow_gate"]
            fire = (gate == "always" or (gate == "if_denied" and denied)
                    or (gate == "if_appealed" and appealed) or (gate == "if_rework" and had_rework))
            if not (fire and occurs[a["id"]]):
                i += 1
                continue
            loop_count=rounds.get(a['id'],0)
            visit_index=visits.get(a['id'],0)
            rnd = visit_index if accounting_version==2 else loop_count
            dur = sample_days(rng, a["timing"]["median_days"], a["timing"]["p90_days"])
            if rnd:                                  # repeats are faster than first passes
                dur = max(0, int(dur * 0.7))
            begin = cursor
            end = dadd(begin, dur)
            if a["occasion"] in ("counter", "hearing", "site_visit"):
                end = next_workday(end)
            path.append({"a": a["id"], "s": begin, "e": end, "r": rnd,
                         "b": bool(a.get("blocking", True))})
            visits[a['id']]=visit_index+1
            if accounting_version==2:
                path[-1].update(visit_index=visit_index,loop_triggers_before=loop_count,fee_charged_dollars=0.)
            if a.get("blocking", True):
                cursor = end        # the case waits
            last_end = max(last_end, end)
            if a["fee"] and a["fee"].get("amount") and not a["fee"].get("refundable"):
                # base fees are charged once; inspection fees are charged per visit
                per_visit = "inspection" in (a["fee"].get("label") or "").lower()
                charge=(a['id'] not in charged_base_fees or per_visit) if accounting_version==2 else (rnd==0 or per_visit)
                if charge:
                    amount=float(a['fee']['amount'])
                    fees += amount
                    charged_base_fees.add(a['id'])
                    if accounting_version==2:
                        path[-1]['fee_charged_dollars']=r2(amount)
            # predicate evaluation at this checkpoint (decision layer)
            if dm and a["id"] in evaluates:
                for e in evaluates[a["id"]]:
                    ok = evaluate(e, e["reading"], attrs)
                    res = pred_results.setdefault(e["pred_id"], {"at": a["id"], "first_pass": ok, "visits": 0,
                                                                  "passed_ever": False, "failed_first": not ok})
                    res["visits"] += 1
                    if ok:
                        res["passed_ever"] = True
                        open_fixable.pop(e["pred_id"], None)
                    elif e["fixable"] and e["correction_back_to"] in idx and idx[e["correction_back_to"]] < i:
                        open_fixable[e["pred_id"]] = e
                    else:
                        fatal_fail = True
                        res["fatal"] = True
            # a fixable failure found at the decision step itself gets its correction
            # round before any decision is recorded
            deferred = bool(dm and a["id"] in evaluates and loop_count < max_rounds
                            and any(e["pred_id"] in open_fixable for e in evaluates[a["id"]]))
            # decision
            if a["element_ref"] and a["element_ref"].startswith("E") and a["visibility"] == "applicant_facing" \
                    and proc["terminal_artifact"] in a["artifacts_out"] and not deferred:
                decision_end = end
                if dm:
                    # An UNCURED CORRECTION IS NOT A DENIAL. This clause used to
                    # read `fatal_fail or bool(open_fixable)`, which denied every
                    # application still carrying an open fixable predicate after
                    # the rework rounds ran out. That single `or` is what put the
                    # development world's outcomes at 32.4% denied and 6.1%
                    # pending, against a real APR distribution of 0.09% denied
                    # and 34.8% pending over 247,326 status-stated applications:
                    # the two states were swapped in magnitude.
                    #
                    # Real applications with outstanding corrections do not get
                    # refused; they sit, undecided, and show up in a published
                    # pending count. The plan requires those to be separate
                    # latent outcomes -- "approval/denial, withdrawal, quiet
                    # abandonment and ongoing processing are separate latent
                    # outcomes" -- so an open fixable predicate now STALLS the
                    # case with no decision recorded, and only a genuinely
                    # non-curable failure denies it.
                    if outcome_model_version >= 2:
                        deny_now = fatal_fail
                        if not fatal_fail and open_fixable:
                            stalled = True
                            break            # no decision is ever recorded
                    else:
                        deny_now = fatal_fail or bool(open_fixable)
                else:
                    p_deny = min(0.6, proc["denial_rate"] * (1 + 0.25 * sum(rounds.values())))
                    deny_now = u_deny < p_deny
                last_decision_outcome = "denied" if deny_now else "approved"
                if first_decision_end is None:
                    first_decision_end, first_decision_outcome = end, last_decision_outcome
                if deny_now:
                    denied = True
                    appealed = rng.random() < proc["p_appeal_if_denied"]
            # abandonment
            if a["actor"] in APPLICANT_ROLES and not denied:
                if rng.random() < hazard * (1 + 0.4 * sum(rounds.values())):
                    abandoned = True
                    break
            # rework
            rw = a["rework"]
            trigger = False
            back_to = rw["back_to"] if rw else None
            if dm and a["id"] in evaluates:
                # predicate-driven: an unresolved fixable failure at this checkpoint
                # sends the case back; the correction cures it with p_cure
                failing = [e for e in evaluates[a["id"]] if e["pred_id"] in open_fixable]
                if failing and loop_count < max_rounds:
                    trigger = True
                    back_to = failing[0]["correction_back_to"]
                    for e in failing:
                        if rng.random() < p_cure:
                            cure(e, e["reading"], attrs)
            elif rw and loop_count < max_rounds and rng.random() < rw["p_trigger"]:
                trigger = True
            if trigger and back_to in idx:
                rounds[a["id"]] = loop_count + 1
                rework_events.append(dict(activity_id=a['id'], back_to=back_to,
                    triggered_at=end, round_at_checkpoint=loop_count+1))
                had_rework = True
                if accounting_version == 2:
                    # A nonblocking checkpoint can finish after the case cursor.
                    # Its correction cannot begin before the triggering result.
                    cursor = max(cursor, end)
                i = idx[back_to]
                continue
            i += 1

        # `stalled` is a fourth latent outcome, distinct from all three others: the
        # applicant has not given up (that is `abandoned`), the agency has not
        # refused (that is `denied`), and nothing has been granted. It is what a
        # published pending count is mostly made of, and a report that shows it
        # as a denial or as an abandonment is making a claim the register denies.
        outcome = ("abandoned" if abandoned else
                   "stalled" if stalled else
                   ("denied" if denied else "approved"))
        # the benchmark's elapsed time: arrival -> decision (or -> giving up)
        end_of_interest = decision_end or (path[-1]["e"] if path else arrived)
        # A stalled case is still open at the cutoff by definition: there is no
        # decision date, so it cannot be a completed observation.
        censored = end_of_interest > as_of or (stalled and outcome_model_version >= 2)
        rec = {
            "applicant_id": "%s#%04d" % (proc["model_id"], k + 1),
            "arrived": arrived,
            "outcome": "in_progress" if censored else outcome,
            "provisional_outcome": outcome if censored else None,
            "elapsed_days": ddiff(end_of_interest, arrived),
            "total_span_days": ddiff(last_end, arrived),
            "fees_paid": r2(fees),
            "rework_rounds": rounds,
            "total_rework_rounds": sum(rounds.values()),
            "rework_events": rework_events,
            "appealed": appealed,
            "censored": censored,
            "path": path,
            "event_clocks": {
                "initial_decision": event_clock(arrived, first_decision_end, first_decision_outcome, as_of),
                "last_decision": event_clock(arrived, decision_end, last_decision_outcome, as_of),
                "modeled_work_end": event_clock(arrived, last_end, outcome, as_of),
            },
        }
        if accounting_version==2:
            rec['fees_paid_by_observation']=r2(sum(s['fee_charged_dollars'] for s in path if s['e']<=as_of))
        if dm:
            rec["case_attributes"] = {key: val for key, val in attrs.items() if not key.startswith("_")}
            rec["predicate_results"] = pred_results
            rec["decision_basis"] = {
                "fatal_failures": sorted(p for p, r in pred_results.items() if r.get("fatal")),
                "unresolved_fixable": sorted(open_fixable)}
        records.append(rec)

    return records, summarize(proc, records, as_of)


def observed_first_visit_summaries(records,as_of):
    """Only first visits completed by observation date can be observed durations."""
    durations={}
    for record in records:
        seen=set()
        for step in record['path']:
            if step['a'] in seen:
                continue
            seen.add(step['a'])
            if step['e']<=as_of:
                durations.setdefault(step['a'],[]).append(ddiff(step['e'],step['s']))
    return {aid:{'n':len(values),'median':r2(median(values)),'p90':r2(quantile(values,.9))}
            for aid,values in sorted(durations.items())}


def observed_rework_summary(records, as_of):
    """Observed corrections, not future or eventual rework risk.

    The cohort includes open and abandoned cases that arrived by the observation
    date. A correction at any modeled stage counts, including after a decision.
    Do not substitute un-timestamped lifetime totals from old saved records.
    """
    cohort = [r for r in records if r['arrived'] <= as_of]
    if any('rework_events' not in r for r in cohort):
        raise ValueError('Observed rework requires timestamped events, not lifetime totals')
    counts = [sum(event['triggered_at'] <= as_of for event in r['rework_events']) for r in cohort]
    successes = sum(count > 0 for count in counts)
    return dict(as_of=as_of, population='arrived_cases_including_open_and_abandoned',
        stage_scope='all_modeled_stages_including_after_decision', n_cases=len(cohort),
        cases_with_observed_rework=successes, observed_correction_rounds=sum(counts),
        share_with_observed_rework=successes/len(cohort) if cohort else None)


def summarize(proc: dict, records: list[dict], as_of=None) -> dict:
    done = [r for r in records if not r["censored"]]
    elapsed = [r["elapsed_days"] for r in done if r["outcome"] != "abandoned"]
    per_act_days: dict[str, list[int]] = {}     # first-visit duration of the activity
    per_act_stage: dict[str, list[int]] = {}    # whole stage, repeats included
    per_act_seen: dict[str, int] = {}
    for r in records:
        firsts: dict[str, int] = {}
        spans: dict[str, tuple[str, str]] = {}
        for step in r["path"]:
            if step["a"] not in firsts:
                firsts[step["a"]] = ddiff(step["e"], step["s"])
            prev = spans.get(step["a"], (step["s"], step["e"]))
            spans[step["a"]] = (min(prev[0], step["s"]), max(prev[1], step["e"]))
        for aid, d in firsts.items():
            per_act_days.setdefault(aid, []).append(d)
            per_act_seen[aid] = per_act_seen.get(aid, 0) + 1
        for aid, (s, e) in spans.items():
            per_act_stage.setdefault(aid, []).append(ddiff(e, s))
    counts: dict[str, int] = {}
    for r in records:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    n_dec = sum(1 for r in done if r["outcome"] in ("approved", "denied"))
    result = {
        "model_id": proc["model_id"],
        "n_applicants": len(records),
        "n_completed": len(done),
        "n_censored": len(records) - len(done),
        "outcomes": counts,
        "elapsed_days": {
            "median": r2(median(elapsed)), "p75": r2(quantile(elapsed, 0.75)),
            "p90": r2(quantile(elapsed, 0.90)), "min": min(elapsed) if elapsed else 0,
            "max": max(elapsed) if elapsed else 0, "n": len(elapsed),
        },
        "event_clock_summaries": {name: event_timing_summary(records, name)
                                  for name in ("initial_decision", "last_decision", "modeled_work_end")},
        "clock_definitions": {
            "elapsed_days": "legacy: arrival to last decision among uncensored cases finally approved/denied; abandonment excluded",
            "initial_decision": "arrival to first decision, among observed first-decision events, regardless of later case status",
            "last_decision": "arrival to last decision, among observed last-decision events, regardless of later case status",
            "modeled_work_end": "arrival to last modeled work, including parallel work; not necessarily a legal closeout event",
        },
        # `denial_rate` is the statistic a real (right-censored) permit extract yields;
        # `denial_rate_all` uses the provisional outcome of in-flight cases too and is
        # the unbiased comparison against process_truth.denial_rate.
        "denial_rate": r2(sum(1 for r in done if r["outcome"] == "denied") / n_dec) if n_dec else 0.0,
        "denial_rate_all": r2(sum(1 for r in records
                                  if (r["provisional_outcome"] or r["outcome"]) == "denied")
                              / max(1, sum(1 for r in records
                                           if (r["provisional_outcome"] or r["outcome"]) != "abandoned"))),
        "abandon_rate": r2(sum(1 for r in records if r["outcome"] == "abandoned") / max(1, len(records))),
        "mean_rework_rounds": r2(sum(r["total_rework_rounds"] for r in records) / max(1, len(records))),
        "share_with_rework": r2(sum(1 for r in records if r["total_rework_rounds"]) / max(1, len(records))),
        "appeal_rate": r2(sum(1 for r in records if r["appealed"]) / max(1, len(records))),
        "fees_paid": {"median": r2(median([r["fees_paid"] for r in records])),
                      "p90": r2(quantile([r["fees_paid"] for r in records], 0.9))},
        "per_activity_median_days": {aid: r2(median(v)) for aid, v in sorted(per_act_days.items())},
        "per_activity_median_stage_days": {aid: r2(median(v)) for aid, v in sorted(per_act_stage.items())},
        "per_activity_occurrence_rate": {aid: r2(c / max(1, len(records)))
                                         for aid, c in sorted(per_act_seen.items())},
        "arrivals": {"first": min(r["arrived"] for r in records) if records else None,
                     "last": max(r["arrived"] for r in records) if records else None},
    }
    if as_of is not None:
        result['observed_first_visit_clocks']={'as_of':as_of,'activities':observed_first_visit_summaries(records,as_of)}
        result['observed_rework'] = observed_rework_summary(records, as_of)
    if records and "predicate_results" in records[0]:
        pids = sorted({p for r in records for p in r["predicate_results"]})
        summary = {}
        for pid in pids:
            seen = [r for r in records if pid in r["predicate_results"]]
            summary[pid] = {
                "n_evaluated": len(seen),
                "first_pass_rate": r2(sum(1 for r in seen if r["predicate_results"][pid]["first_pass"]) / max(1, len(seen))),
                "eventual_pass_rate": r2(sum(1 for r in seen if r["predicate_results"][pid]["passed_ever"]) / max(1, len(seen))),
                "fatal_denials": sum(1 for r in records if pid in r["decision_basis"]["fatal_failures"]),
                "unresolved_denials": sum(1 for r in records if pid in r["decision_basis"]["unresolved_fixable"]),
            }
        result["predicate_summary"] = summary
    return result


def simulate_all(world: dict, processes: dict, rules: dict) -> tuple[dict, dict]:
    """Simulate every process. At world_model_version 2 the caseload SCALES.

    A constant applicant count across 58 counties is the wrong shape twice over.
    It is unrealistic -- the APR panel's project counts scale with population at
    a log-log slope of 0.989, i.e. per-capita constant, from 61 projects in the
    smallest county to 195,483 in the largest. And it silently truncates the
    user-evidence gradient, because a forum post has to come from a case: a
    county whose availability draw asks for 500 posts can only supply as many
    posters as it has applicants, so a flat caseload flattened the realised
    volume slope to 0.50 against the measured 0.75.

    So `n_applicants` becomes the caseload of a MEDIAN county and each county
    scales from it. The knob keeps its meaning for version 1 and for the
    hand-written jurisdictions.
    """
    logs, summaries = {}, {}
    n_target = world["knobs"]["n_applicants"]
    n_neigh = world["knobs"]["n_applicants_neighbor"]
    v2 = world["knobs"].get("world_model_version", 1) >= 2
    panel = {c["id"]: c for c in world.get("county_panel", [])}
    for mid, proc in sorted(processes.items()):
        n = n_target if proc["state"] == "Marisol" else n_neigh
        county = panel.get(proc["jur_id"]) if v2 else None
        if county is not None:
            n = capacity.caseload(county, n_target)
        logs[mid], summaries[mid] = simulate_process(world, proc, rules[mid], n)
    return logs, summaries
