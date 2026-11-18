"""The visibility model: truth -> what any public artifact is allowed to say.

This module is the benchmark's instrument, so it is deliberately explicit: no
artifact "just knows" a fact; every fact in every artifact is a `reveals` entry
produced here, with a `ref` (activity, or statute element for state-level
documents), a `field`, a `fidelity`, and the literal `value` a renderer must
state. What is *not* revealed by any artifact is the information ceiling's
complement, so the rules below are the availability error (plan §1 row 1).

Rules, by artifact kind
-----------------------
A `staff_only` activity flagged `statutorily_disclosed` is dropped from
`must_not_reveal` for the law-restating kinds (ordinance, fee resolution, staff
report, bill analysis, council minutes) and kept for every other kind.

Standing obligations (`per_case: false` -- publishing the checklist, maintaining a
registry, translating the handout) may be revealed as facts (the ordinance and the
checklist name them) but never appear in a `process`-level `order` reveal, because
no applicant walks through them.

program_page        applicant_facing activities: `exists` exact, one `order`
                    entry giving the published sequence; end-to-end `timing`
                    approximate (optimistic) with p=0.45, otherwise vague or
                    absent; `fee` exact unless a fee schedule carries it;
                    lead department `actor` exact; terminal `artifact` exact.
                    applicant_inferable: `exists` vague with p=0.25. staff_only:
                    never (goes to must_not_reveal).
generic_permits_page  the *machinery*, not the program: portal, counter hours,
                    plan-check/resubmittal loop (`rework` vague). Names the
                    program only when no program page exists (then `exists`
                    vague for 2-3 steps). One page per jurisdiction, so its
                    reveals carry an explicit `process` field.
form                the application activity `exists` exact and its
                    `artifacts_in` exact; `fee` exact when due at submittal;
                    with p=0.3 an "office use only" box leaks one back-office
                    step at `vague` (the real leak channel, style/forms.md).
checklist           the inspection `exists` exact + inspected artifact, the
                    third-party option exact where it exists, corrections exact
                    with p=0.4.
faq                 `timing` approximate for 2-4 steps, one `rework` loop
                    approximate, 1-2 applicant_inferable steps vague.
fee_schedule        every fee in the jurisdiction `exact` (or `wrong` when the
                    page is stale); lead department exact.
fee_resolution      fees exact plus the "supersedes Resolution No. X" hook, so
                    the prior fee is recoverable as a *prior version* fact.
ordinance           local-rule choices and added elements exact (`exists`,
                    `actor`, `fee`, appeal), statute elements by reference; no
                    timing; never a staff-only step.
staff_report        30-60% of staff_only activities exact (`exists` + `actor`),
                    the fee derivation, expected volumes, and up to 2 timing
                    facts approximate. The designed tier: this is what raises
                    the ceiling.
council_minutes     one or two facts, usually a council question answered with
                    a timing approximation.
sop                 everything, exact (order, actor, staff steps), timing
                    approximate ("within 3 business days").
audit_excerpt       observed timing (2-4 steps) approximate-to-exact plus 1-3
                    staff_only steps exact.
news                adoption: fee, department, date, program name exact, 1-2
                    steps vague. backlog: end-to-end timing approximate, volumes,
                    and with p=0.4 one staff_only bottleneck vague.
third_party_guide   a law firm / expediter / installer explainer on a private
                    host: every applicant_facing step exact and in order, timing
                    approximate from experience, fee approximate or wrong, and
                    with p=0.3 one applicant_inferable step exact. Frequently the
                    most complete public description -- and 1.5x more likely to
                    be stale.
bill_analysis       state level, per statute: the *intended* skeleton
                    (`ref` = element id) exact, shot clocks exact, cost
                    estimates, and the workflow the committee expected at vague.
official_stats      end-to-end `timing` approximate (volumes, median, backlog)
                    and denial rate approximate; no per-step facts.
reddit_thread       drawn from the simulated log through the complaint-selection
                    function; the OP reports *their* timeline with user noise
                    (rounding, exaggeration at `p_wrong_fact_user`); comments add
                    other personas, contamination from other
                    jurisdictions/processes, stale advice, and with
                    `p_reveal_backoffice_in_comments` an insider revealing one
                    staff_only step.
forum_thread        older, politer, higher contamination, 1-2 facts vague/wrong.
"""
from __future__ import annotations

from . import capacity
from .decision import criterion_reveals, persona_failed_criteria, reading_phrase
from .rng import chance, ddiff, pick, pick_n, sub_rng
from .world import jur_by_id

FIDELITIES = ("exact", "approximate", "vague", "wrong")

# Kinds that restate public law, so a staff-only step implementing a public
# mandate (`statutorily_disclosed`) is NOT a leak for them: an ordinance or a
# bill analysis that recites "the agency shall verify the licence" necessarily
# discloses that someone verifies licences. Every other kind (program page, FAQ,
# form, checklist, news, third-party guide, reddit/forum thread) must still keep
# those steps out -- there a disclosure is a genuine leak.
LAW_RESTATING_KINDS = {"ordinance", "fee_resolution", "staff_report", "bill_analysis",
                       "council_minutes"}

# --------------------------------------------------------------- phrasing --


def days_phrase(days: float, fidelity: str, rng=None) -> str:
    d = max(0.0, float(days))
    if fidelity == "exact":
        return "%d days" % round(d)
    if fidelity == "approximate":
        if d < 3:
            return "same day or next business day"
        if d < 12:
            return "about %d week%s" % (max(1, round(d / 7)), "" if round(d / 7) == 1 else "s")
        if d < 70:
            w = round(d / 7)
            return "%d to %d weeks" % (max(1, w - 1), w + 1)
        return "about %d months" % max(2, round(d / 30))
    if fidelity == "vague":
        if d < 5:
            return "a few days"
        if d < 25:
            return "a couple of weeks"
        if d < 70:
            return "several weeks"
        return "a few months"
    # wrong
    f = pick(rng, [0.4, 0.5, 0.6, 1.7, 2.2, 2.8]) if rng else 0.5
    return "%d days" % max(1, round(d * f))


def fee_phrase(amount: float, fidelity: str, rng=None) -> str:
    a = float(amount)
    if fidelity == "exact":
        return "$%s" % ("{:,.0f}".format(a))
    if fidelity == "approximate":
        step = 50 if a >= 200 else 10
        return "about $%s" % "{:,.0f}".format(round(a / step) * step)
    if fidelity == "vague":
        if a < 100:
            return "under $100"
        if a < 600:
            return "a few hundred dollars"
        return "over a thousand dollars"
    f = pick(rng, [0.55, 0.7, 1.35, 1.8]) if rng else 1.4
    return "$%s" % "{:,.0f}".format(round(a * f / 5) * 5)


def act_label(a: dict) -> str:
    return a.get("local_name") or a["name"]


def _rev(ref, field, fidelity, value, must_quote=False, **extra):
    d = {"ref": ref, "field": field, "fidelity": fidelity, "value": value, "must_quote": must_quote}
    d.update(extra)
    return d


def decision_clock(summary, statistic="median"):
    """The legacy scalar's actual estimand, not a renderer-invented intake clock."""
    return {"start": "beginning_preparation_or_filing", "end": "last_recorded_decision",
            "population": "uncensored_approved_or_denied", "statistic": statistic,
            "sample_size": summary["elapsed_days"]["n"]}


def visit_clock(statistic="median", population="first_activity_visits"):
    return {"start": "first_activity_visit_start", "end": "first_activity_visit_end",
            "basis": "single_visit_cycle", "population": population, "statistic": statistic}


def first_visit_timing(summary,activity,statistic="median"):
    """Use actually observed visits when available; no observations means forecast."""
    observed=summary.get('observed_first_visit_clocks')
    if observed is not None:
        row=observed['activities'].get(activity['id'])
        if row and row['n']:
            clock=visit_clock(statistic,'first_visits_completed_by_observation_date')
            clock.update(sample_size=row['n'],as_of=observed['as_of'])
            return row['median'],clock
        return activity['timing']['median_days'],visit_clock('forecast','planned_single_visits')
    return summary['per_activity_median_days'].get(activity['id'],activity['timing']['median_days']),visit_clock(statistic)


# ------------------------------------------------------------ the plan -----

# kind -> (knob name or None, audience, register, length_words)
KIND_META = {
    "program_page": ("p_publish_program_page", "applicant", "municipal_web", [250, 620]),
    "generic_permits_page": (None, "applicant", "municipal_web", [250, 550]),
    "form": ("p_publish_form", "applicant", "municipal_web", [300, 900]),
    "checklist": ("p_publish_checklist", "applicant", "municipal_web", [400, 1100]),
    "faq": ("p_publish_faq", "applicant", "municipal_web", [300, 700]),
    "fee_schedule": ("p_publish_fee_schedule", "public", "legal", [200, 600]),
    "fee_resolution": ("p_publish_fee_resolution", "council", "legal", [300, 800]),
    "ordinance": ("p_publish_ordinance", "public", "legal", [500, 1200]),
    "staff_report": ("p_publish_staff_report", "council", "bureaucratic_memo", [800, 1700]),
    "council_minutes": ("p_publish_council_minutes", "council", "bureaucratic_memo", [150, 450]),
    "sop": ("p_publish_sop", "staff", "bureaucratic_memo", [600, 1500]),
    "audit_excerpt": ("p_publish_audit", "public", "bureaucratic_memo", [400, 900]),
    "news": ("p_publish_news", "public", "news", [400, 800]),
    "third_party_guide": ("p_third_party_guide", "applicant", "municipal_web", [400, 900]),
    "bill_analysis": ("p_bill_analysis", "council", "bureaucratic_memo", [500, 1100]),
    "official_stats": ("p_official_stats", "public", "municipal_web", [150, 450]),
    "reddit_thread": (None, "public", "reddit_casual", [250, 900]),
    "forum_thread": ("p_publish_forum_thread", "public", "reddit_casual", [180, 500]),
}

PER_JURISDICTION = {"generic_permits_page", "fee_schedule"}
PER_STATUTE = {"bill_analysis"}


def plan_artifacts(world: dict, proc: dict, rule: dict, statutes: dict) -> list[dict]:
    """Which per-process artifact kinds exist, with the draw that decided it."""
    knobs = world["knobs"]
    stat = statutes[proc["stat_id"]]
    rng = sub_rng(world["seed"], "plan", proc["model_id"])
    out = []
    mandates_checklist = any(e["kind"] == "checklist_publication" for e in stat["skeleton"])
    for kind in ("program_page", "form", "checklist", "faq", "ordinance", "fee_resolution",
                 "staff_report", "council_minutes", "sop", "audit_excerpt", "news",
                 "third_party_guide", "official_stats"):
        knob = KIND_META[kind][0]
        p = knobs[knob]
        note = "%s=%.2f" % (knob, p)
        if kind == "checklist" and mandates_checklist:
            p, note = 0.97, "statute mandates checklist publication (%s)" % stat["cite"]
        if kind in ("ordinance", "fee_resolution") and rule["instrument"] == "admin_policy":
            p, note = 0.12, "no legislative instrument: the program is an administrative policy"
        if kind in ("staff_report", "council_minutes") and rule["instrument"] == "admin_policy":
            p, note = 0.08, "administrative program: no council record (the Hayward case)"
        if kind == "fee_resolution" and rule["instrument"] == "resolution":
            p, note = min(0.95, p + 0.3), "the adopting instrument is itself a fee resolution"
        if kind == "news" and (rule["retrofit"] or proc["denial_rate"] > 0.12):
            p, note = min(0.85, p + 0.25), "newsworthy: retrofit of an existing program or a contested program"
        draw = rng.random()
        if draw < p:
            out.append({"kind": kind, "why": "visibility model: %s drew %.2f" % (note, draw)})
    return out


# ----------------------------------------------------------- reveal builders

def _applicant_steps(proc: dict) -> list[dict]:
    return [a for a in proc["activities"] if a["visibility"] == "applicant_facing" and a.get("per_case", True)]


def _inferable(proc: dict) -> list[dict]:
    return [a for a in proc["activities"] if a["visibility"] == "applicant_inferable"]


def _staff(proc: dict) -> list[dict]:
    return [a for a in proc["activities"] if a["visibility"] == "staff_only"]


def _fee_acts(proc: dict) -> list[dict]:
    return [a for a in proc["activities"] if a["fee"] and a["fee"].get("amount")]


def _decision(proc: dict) -> dict | None:
    return next((a for a in proc["activities"]
                 if proc["terminal_artifact"] in (a["artifacts_out"] or [])), None)


def reveals_for(kind: str, world: dict, proc: dict, rule: dict, statutes: dict, summary: dict,
                rng, stale: bool, fee_schedule_exists: bool) -> tuple[list, list, list]:
    """-> (reveals, must_not_reveal, extra_notes). Pure function of the truth +
    the artifact kind + the draws in `rng`."""
    knobs = world["knobs"]
    stat = statutes[proc["stat_id"]]
    med = summary["elapsed_days"]["median"]
    prior = proc["prior_version"]
    R: list[dict] = []
    notes: list[str] = []
    steps = _applicant_steps(proc)
    dec = _decision(proc)

    def stale_fee(a):
        """A stale artifact states the previous fee: fidelity `wrong` vs truth."""
        if stale and prior and prior.get("fee_amount"):
            return _rev(a["id"], "fee", "wrong", fee_phrase(prior["fee_amount"], "exact"),
                        stale_of="fee", describes_prior=True)
        return _rev(a["id"], "fee", "exact", "%s %s" % (fee_phrase(a["fee"]["amount"], "exact"),
                                                        a["fee"]["when"]))

    if kind == "program_page":
        for a in steps:
            R.append(_rev(a["id"], "exists", "exact", act_label(a)))
        if len(steps) > 1:
            R.append(_rev("process", "order", "exact",
                          " -> ".join(act_label(a) for a in steps)))
        if chance(rng, 0.45):
            R.append(_rev("process", "timing", "approximate",
                          "the time from beginning preparation/filing through the last recorded approval or denial is usually %s"
                          % days_phrase(med * (0.55 + 0.25 * rng.random()), "approximate"),
                          optimistic=True,measurement_clock=decision_clock(summary,"optimistic_typical")))
        elif chance(rng, 0.5):
            R.append(_rev("process", "timing", "vague",
                          "from beginning preparation/filing to the last recorded decision takes " + days_phrase(med, "vague"),
                          measurement_clock=decision_clock(summary,"typical")))
        for a in _fee_acts(proc):
            if not fee_schedule_exists or chance(rng, 0.6):
                R.append(stale_fee(a))
        if dec:
            R.append(_rev(dec["id"], "actor", "exact", proc["lead_department"] if not (stale and rule.get("prior_lead_role"))
                          else prior["changes"][0]))
            R.append(_rev(dec["id"], "artifact", "exact", proc["terminal_artifact"]))
        for a in _inferable(proc):
            if chance(rng, 0.25):
                R.append(_rev(a["id"], "exists", "vague", "staff review the file internally"))
    elif kind == "generic_permits_page":
        R.append(_rev("process", "artifact", "exact", "applications are filed through %s" % proc["permit_system"]))
        rw = next((a for a in proc["activities"] if a["rework"]), None)
        if rw:
            R.append(_rev(rw["id"], "rework", "vague",
                          "incomplete submittals receive correction comments and must be resubmitted"))
        for a in steps[:3]:
            R.append(_rev(a["id"], "exists", "vague", act_label(a)))
    elif kind == "form":
        app = next((a for a in steps if a["occasion"] in ("counter", "online")), steps[0] if steps else None)
        if app:
            R.append(_rev(app["id"], "exists", "exact", act_label(app)))
            R.append(_rev(app["id"], "artifact", "exact", "; ".join(app["artifacts_in"] or [proc["form_name"]])))
            if app["fee"]:
                R.append(stale_fee(app))
        for a in _fee_acts(proc):
            if a["fee"]["when"] == "at submittal" and not any(r["ref"] == a["id"] and r["field"] == "fee" for r in R):
                R.append(stale_fee(a))
        if chance(rng, 0.3) and _staff(proc):
            leak = pick(rng, _staff(proc))
            R.append(_rev(leak["id"], "exists", "vague",
                          "a \"for office use only\" box shows the file is routed internally (%s)"
                          % (leak.get("backoffice_tag") or "internal routing"),
                          channel="office_use_box"))
            notes.append("form leaks one back-office step through the office-use box")
    elif kind == "checklist":
        insp = next((a for a in proc["activities"]
                     if a["element_ref"] and any(e["element_id"] == a["element_ref"] and e["kind"] == "inspection"
                                                 for e in stat["skeleton"])), None)
        if insp:
            R.append(_rev(insp["id"], "exists", "exact", act_label(insp)))
            R.append(_rev(insp["id"], "artifact", "exact", proc["checklist_name"]))
            R.append(_rev(insp["id"], "actor", "exact", _actor_name(proc, insp)))
        tp = next((a for a in proc["activities"] if a["actor"] == "third_party"), None)
        if tp:
            R.append(_rev(tp["id"], "exists", "exact", act_label(tp)))
        corr = next((a for a in proc["activities"]
                     if a["element_ref"] and any(e["element_id"] == a["element_ref"] and e["kind"] == "correction"
                                                 for e in stat["skeleton"])), None)
        if corr and chance(rng, 0.4):
            R.append(_rev(corr["id"], "exists", "exact", act_label(corr)))
    elif kind == "faq":
        for a in pick_n(rng, steps, min(4, max(2, len(steps) // 2))):
            t,clock = first_visit_timing(summary,a)
            R.append(_rev(a["id"], "timing", "approximate", days_phrase(t, "approximate"),
                          measurement_clock=clock))
        rw = next((a for a in proc["activities"] if a["rework"]), None)
        if rw:
            R.append(_rev(rw["id"], "rework", "approximate",
                          "if corrections are required you will receive a notice and must resubmit; "
                          "the planning estimate is about %g percent of eligible visits to this checkpoint "
                          "triggering a correction, before the retry limit is reached; "
                          "this is not the share of applications needing any correction"
                          % round(100 * rw["rework"]["p_trigger"], 1),
                          count_observation=dict(measure='correction_probability_per_eligible_visit',
                              statistic='planning_probability', population='eligible_visits_at_this_checkpoint')))
        for a in pick_n(rng, _inferable(proc), 2):
            R.append(_rev(a["id"], "exists", "vague", "the file moves to internal review"))
    elif kind in ("fee_schedule", "fee_resolution"):
        for a in _fee_acts(proc):
            if kind == "fee_schedule":
                R.append(stale_fee(a))
            else:
                # the cost-recovery derivation belongs to the program fee itself; a
                # deposit or re-inspection line is set by the same resolution without one
                basis = (rule["fee"]["derivation"] if a["fee"]["amount"] == rule["fee"]["amount"]
                         else "%s, set by the same resolution" % a["fee"]["label"])
                R.append(_rev(a["id"], "fee", "exact",
                              "%s (%s)" % (fee_phrase(a["fee"]["amount"], "exact"), basis)))
            R.append(_rev(a["id"], "actor", "exact", proc["lead_department"]))
        if kind == "fee_resolution" and prior:
            R.append(_rev("prior_version", "fee", "exact",
                          "supersedes %s, which set the fee at %s"
                          % (prior["cite"], fee_phrase(prior["fee_amount"], "exact")),
                          describes_prior=True))
            notes.append("carries the prior-version hook (supersedes clause)")
    elif kind == "ordinance":
        for a in proc["activities"]:
            if a["element_ref"] and a["element_ref"].startswith("L"):
                R.append(_rev(a["id"], "exists", "exact", act_label(a)))
                R.append(_rev(a["id"], "actor", "exact", _actor_name(proc, a)))
        for a in steps + [x for x in proc["activities"]
                          if not x.get("per_case", True) and x["element_ref"]]:
            if not any(r["ref"] == a["id"] for r in R):
                R.append(_rev(a["id"], "exists", "exact", act_label(a)))
        app = next((a for a in proc["activities"] if a["element_ref"] and
                    any(e["element_id"] == a["element_ref"] and e["kind"] == "appeal" for e in stat["skeleton"])), None)
        if app:
            R.append(_rev(app["id"], "timing", "exact", "appeal must be filed within the period in the ordinance"))
        R.append(_rev("process", "actor", "exact", "%s administers the program" % proc["lead_department"]))
        if rule["fee"]["adopted_by"].startswith("the "):
            for a in _fee_acts(proc)[:1]:
                R.append(_rev(a["id"], "fee", "vague", "fees are set by %s" % rule["fee"]["adopted_by"]))
    elif kind == "staff_report":
        staff = _staff(proc)
        share = 0.3 + 0.3 * rng.random()
        for a in pick_n(rng, staff, max(1, round(len(staff) * share))):
            R.append(_rev(a["id"], "exists", "exact", act_label(a)))
            R.append(_rev(a["id"], "actor", "exact", _actor_name(proc, a)))
        if steps:
            R.append(_rev("process", "order", "exact",
                          "proposed workflow: " + " -> ".join(
                              act_label(a) for a in proc["activities"]
                              if a["visibility"] != "staff_only" and a.get("per_case", True))))
        for a in pick_n(rng, proc["activities"], 2):
            R.append(_rev(a["id"], "timing", "approximate", days_phrase(a["timing"]["median_days"], "approximate"),
                          measurement_clock=visit_clock("forecast","planned_single_visits")))
        for a in _fee_acts(proc)[:1]:
            R.append(_rev(a["id"], "fee", "exact", "%s, derived as %s"
                          % (fee_phrase(a["fee"]["amount"], "exact"), rule["fee"]["derivation"])))
        R.append(_rev("process", "exists", "exact",
                      "staff anticipate %d to %d applications in the first year and request %.1f FTE"
                      % (18 + rng.randrange(60), 70 + rng.randrange(120), pick(rng, [0.25, 0.5, 0.5, 1.0]))))
        if rule["lineage_from"]:
            R.append(_rev("process", "exists", "exact",
                          "comparison table with neighbouring jurisdictions, including %s"
                          % rule["lineage_from"], lineage_hint=True))
    elif kind == "council_minutes":
        cand = pick_n(rng, proc["activities"], 2)
        for a in cand[:1]:
            R.append(_rev(a["id"], "timing", "approximate",
                          "in answer to a council question, the director said this step takes %s"
                          % days_phrase(a["timing"]["median_days"], "approximate"),
                          measurement_clock=visit_clock("forecast","planned_single_visits")))
        if _staff(proc) and chance(rng, 0.4):
            a = pick(rng, _staff(proc))
            R.append(_rev(a["id"], "exists", "vague", "the director described an internal review step"))
    elif kind == "sop":
        # an SOP is the ceiling-raising artifact, but it is not an oracle: it is a
        # revision behind (each step is missing with p=0.15) and states staff-side
        # durations as service targets rather than observed times.
        for i, a in enumerate(proc["activities"], start=1):
            if chance(rng, 0.15):
                notes.append("SOP predates %s: step not described" % a["id"])
                continue
            R.append(_rev(a["id"], "exists", "exact", "%d. %s" % (i, act_label(a))))
            R.append(_rev(a["id"], "actor", "exact", _actor_name(proc, a)))
            R.append(_rev(a["id"], "timing", "approximate",
                          "within %s" % days_phrase(a["timing"]["median_days"], "approximate"),
                          measurement_clock=visit_clock("service_target","single_visits")))
            if a["rework"]:
                R.append(_rev(a["id"], "rework", "exact",
                              "if %s, return to step %s" % (a["rework"]["reason"], a["rework"]["back_to"])))
        shown = {r["ref"] for r in R}
        R.append(_rev("process", "order", "exact",
                      "; ".join("%s %s" % (a["id"], act_label(a)) for a in proc["activities"]
                                if a["id"] in shown and a.get("per_case", True))))
    elif kind == "audit_excerpt":
        for a in pick_n(rng, proc["activities"], 3):
            t,clock = first_visit_timing(summary,a)
            description=("estimated first-visit duration %s (no completed first visits yet)" if clock['statistic']=='forecast'
                         else "median %s from case files")
            R.append(_rev(a["id"], "timing", "exact", description % days_phrase(t, "exact"),
                          measurement_clock=clock))
        for a in pick_n(rng, _staff(proc), 2):
            R.append(_rev(a["id"], "exists", "exact", act_label(a)))
        if summary["elapsed_days"]["n"]:
            R.append(_rev("process", "timing", "exact",
                          "from beginning preparation/filing through the last recorded approval or denial: "
                          "median %d days and 90th percentile %d days among %d decided cases"
                          % (round(med), round(summary["elapsed_days"]["p90"]),summary["elapsed_days"]["n"]),
                          measurement_clock=decision_clock(summary,"median_and_p90")))
    elif kind == "news":
        angle = "backlog" if chance(rng, 0.45) else "adoption"
        notes.append("angle: " + angle)
        if angle == "adoption":
            for a in _fee_acts(proc)[:1]:
                R.append(stale_fee(a))
            R.append(_rev("process", "actor", "exact", proc["lead_department"]))
            for a in pick_n(rng, steps, 2):
                R.append(_rev(a["id"], "exists", "vague", act_label(a)))
        else:
            R.append(_rev("process", "timing", "approximate",
                          "reported time from beginning preparation/filing through the last recorded approval or denial "
                          "is around %s; the department has received %d applications and issued %d permits"
                          % (days_phrase(med * (1.0 + 0.4 * rng.random()), "approximate"),
                             60 + rng.randrange(180), 10 + rng.randrange(60)),
                          measurement_clock=decision_clock(summary,"typical")))
            if _staff(proc) and chance(rng, 0.4):
                a = pick(rng, _staff(proc))
                R.append(_rev(a["id"], "exists", "vague",
                              "files sit in one internal queue handled by a single staff member"))
    elif kind == "third_party_guide":
        for a in steps:
            R.append(_rev(a["id"], "exists", "exact", act_label(a)))
        if steps:
            R.append(_rev("process", "order", "exact",
                          " -> ".join(act_label(a) for a in steps)))
        for a in pick_n(rng, steps, min(3, len(steps))):
            t,clock = first_visit_timing(summary,a,"typical")
            R.append(_rev(a["id"], "timing", "approximate", days_phrase(t * (0.9 + 0.4 * rng.random()), "approximate"),
                          measurement_clock=clock))
        for a in _fee_acts(proc)[:1]:
            if stale and prior and prior.get("fee_amount"):
                # the guide quotes the superseded fee, confidently and exactly
                R.append(_rev(a["id"], "fee", "wrong", fee_phrase(prior["fee_amount"], "exact"),
                              stale_of="fee", describes_prior=True))
            elif chance(rng, 0.3):
                R.append(_rev(a["id"], "fee", "wrong", fee_phrase(a["fee"]["amount"], "wrong", rng)))
            else:
                R.append(_rev(a["id"], "fee", "approximate", fee_phrase(a["fee"]["amount"], "approximate")))
        if _inferable(proc) and chance(rng, 0.3):
            a = pick(rng, _inferable(proc))
            R.append(_rev(a["id"], "exists", "exact", act_label(a), insider_knowledge=True))
        R.append(_rev("process", "timing", "approximate",
                      "in our experience the time from beginning preparation/filing through the last recorded "
                      "approval or denial runs %s" % days_phrase(med, "approximate"),
                      measurement_clock=decision_clock(summary,"typical")))
    elif kind == "bill_analysis":
        for el in stat["skeleton"]:
            R.append(_rev(el["element_id"], "exists", "exact", el["name"], level="statute"))
            if el["shot_clock_days"]:
                R.append(_rev(el["element_id"], "timing", "exact",
                              "%d-day clock" % el["shot_clock_days"], level="statute"))
        R.append(_rev("statute", "order", "exact",
                      " -> ".join(e["element_id"] for e in stat["skeleton"]), level="statute"))
        R.append(_rev("statute", "exists", "vague",
                      "the committee expected agencies to screen applications at a counter, route them to an "
                      "inspector, and issue the decision without new staff", level="statute"))
        R.append(_rev("statute", "fee", "vague",
                      "cost estimate: minor annual costs to local agencies, reimbursable if a state-mandated "
                      "local program", level="statute"))
    elif kind == "official_stats":
        if summary["elapsed_days"]["n"]:
            R.append(_rev("process", "timing", "approximate",
                          "median time from beginning preparation/filing through the last recorded approval or denial: "
                          "%s (dashboard, %d decided cases; withdrawn and still-in-progress cases excluded; "
                          "not a clock through later closeout)"
                          % (days_phrase(med, "approximate"), summary["elapsed_days"]["n"]),
                          measurement_clock=decision_clock(summary)))
        else:
            R.append(_rev("process", "exists", "exact",
                          "No decided cases are available for a processing-time median; no duration is reported."))
        rework = summary.get('observed_rework')
        if rework and rework['n_cases']:
            R.append(_rev("process", "rework", "approximate",
                          "as of %s, %d of %d received applications (about %d percent) have had at least "
                          "one observed correction round at any stage, including after a decision; "
                          "the cohort includes open and withdrawn cases, so this is not an eventual-risk estimate"
                          % (rework['as_of'], rework['cases_with_observed_rework'], rework['n_cases'],
                             round(100 * rework['share_with_observed_rework'])),
                          count_observation=dict(measure='cases_with_observed_correction',
                              statistic='observed_cohort_fraction', population=rework['population'],
                              stage_scope=rework['stage_scope'], as_of=rework['as_of'],
                              numerator=rework['cases_with_observed_rework'], sample_size=rework['n_cases'])))
        R.append(_rev("process", "exists", "approximate",
                      "%d applications received, %d permits issued, %d denied"
                      % (summary["n_applicants"], summary["outcomes"].get("approved", 0),
                         summary["outcomes"].get("denied", 0))))
    # eligibility / compliance criteria as this jurisdiction applies them (decision.py)
    R += criterion_reveals(kind, proc, rule, rng, knobs, stale)
    if not summary['elapsed_days']['n']:
        R=[row for row in R if not (row.get('measurement_clock') or {}).get('population')=='uncensored_approved_or_denied']
    must_not = [a["id"] for a in _staff(proc)
                if not any(r["ref"] == a["id"] for r in R)
                and not (kind in LAW_RESTATING_KINDS and a.get("statutorily_disclosed"))]
    return R, must_not, notes


def _actor_name(proc: dict, act: dict) -> str:
    return next((x["name"] for x in proc["actors"] if x["id"] == act["actor"]), act["actor"])


# --------------------------------------------------------------- personas --

WORDS = ["oakland", "fog", "burrito", "bluejay", "tinker", "quarry", "mossy", "latte", "granite",
         "hammer", "pelican", "sprocket", "cedar", "roamer", "kettle", "marlin", "juniper", "waffle"]


def _author(rng) -> str:
    return "u_%s%d" % (pick(rng, WORDS), 10 + rng.randrange(9000))


def select_personas(world: dict, proc: dict, log: list[dict], summary: dict) -> list[dict]:
    """Complaint-selection function: who posts about their case.

    At world_model_version 1 this is a pure filter, so a 200-case process always
    yields posters and the thread count follows caseload. That conflates two
    different things the register measured separately: WHO posts (complaint
    selection, the parameter the plan calls kappa) and HOW MANY post at all
    (channel availability, which is a property of the county, not the case mix).

    At version 2 the filter still decides the ORDER -- delayed and denied
    applicants first, which is the planted selection -- but the COUNT comes from
    `capacity.post_volume`, calibrated to the measured median of 13 distinct
    posts per county-programme cell. The consequence is the one the measurement
    demands: 38% of county-programme cells produce no user evidence at all, and
    a small county with a busy process still produces almost none.
    """
    cs = world["knobs"]["complaint_selection"]
    p75 = summary["elapsed_days"]["p75"]
    posters = []
    for rec in log:
        if rec["censored"]:
            continue            # people post when their case has concluded
        rng = sub_rng(world["seed"], "post", rec["applicant_id"])
        outcome = rec["provisional_outcome"] or rec["outcome"]
        if outcome == "denied":
            cls, p = "denied", cs["denied"]
        elif outcome == "abandoned":
            cls, p = "abandoned", cs["abandoned"]
        elif rec["elapsed_days"] > p75:
            cls, p = "delayed", cs["delayed"]
        else:
            cls, p = "normal", cs["normal"]
        if rng.random() < p:
            posters.append((cls, rec, rng))
    order = {"denied": 0, "delayed": 1, "abandoned": 2, "normal": 3}
    posters.sort(key=lambda t: (order[t[0]], t[1]["applicant_id"]))
    if world["knobs"].get("world_model_version", 1) < 2:
        return posters                    # version 1 is a pure filter; unchanged
    jur = jur_by_id(world).get(proc["jur_id"])
    if not jur or jur["id"] not in {c["id"] for c in world.get("county_panel", [])}:
        return posters                    # hand-written jurisdictions keep v1 behaviour
    _u, v_c = capacity.county_effects(jur, world["seed"])
    # The UNION of the two user channels, because the sweep deduplicated a post
    # to one county whichever venue carried it. Using county_sub alone would
    # charge the counties with no forum of their own with having no user
    # evidence at all, which is exactly the overstatement the rural-commons
    # argument turns on.
    scenario = world["knobs"].get("availability_scenario", "reference")
    # The county's standardised process delay, so the V_DELAY scenarios actually
    # bite. Codex's review found that `post_volume` accepts `delay_z` but nothing
    # in the build path ever passed it, so every delay scenario produced an
    # IDENTICAL volume vector: the knob was decorative. My unit test passed only
    # because it supplied `delay_z` by hand, which tested the function and not
    # the wiring — a distinction worth keeping in mind for the other scenarios.
    #
    # Standardised against the 1.15 centre and 0.37 log spread that
    # capacity.speed_factor realises, so delay_z is comparable across worlds.
    import math as _m
    speed = capacity.speed_factor(
        jur, world["seed"], scenario=world["knobs"].get("speed_scenario", "reference"))
    delay_z = _m.log(speed / 1.15) / 0.37
    n_posts = sum(
        capacity.post_volume(jur, channel, world["seed"], scenario=scenario,
                             volume_effect=v_c, delay_z=delay_z,
                             programme=proc["domain"])
        for channel in ("county_sub", "statewide_sub"))
    if not n_posts:
        # An existing channel with zero volume, or no channel at all. Both are
        # real and the ceiling must report `n_posts_with_timing: 0` rather than
        # a small positive number.
        return []
    if n_posts >= len(posters):
        return posters
    # WEIGHTED SAMPLING WITHOUT REPLACEMENT, not a slice of the sorted list.
    #
    # The list above is sorted denied -> delayed -> abandoned -> normal so that
    # the ORDER expresses complaint propensity. Taking `posters[:n_posts]` off
    # that list looks like selection but is truncation: whenever the volume
    # quota is small against the eligible pool, the first class simply consumes
    # the whole quota. Codex's review measured the consequence in the first
    # development world -- 14,713 of 16,908 rendered OPs (87%) were `denied`,
    # which is a mechanical artifact of the quota and not a posting rate anyone
    # measured.
    #
    # The fix keeps the two mechanisms independent, which is what the plan asks
    # for: `complaint_selection` already decided WHO is eligible to post (the
    # probabilistic filter above), and `post_volume` decides HOW MANY do. Once a
    # case is eligible, which eligible cases get drawn must not re-apply the
    # outcome weighting a second time. So the draw is uniform over the eligible
    # pool, seeded per process for determinism.
    #
    # Efraimidis-Spirakis one-pass weighted sampling, with every weight equal:
    # each item gets a key u^(1/w) and the top n_posts keys win. Written in the
    # weighted form rather than as a plain shuffle so that giving a class a
    # deliberate second-stage weight later is a one-line change with a visible
    # place to declare it.
    draw = sub_rng(world["seed"], "poster_sample", proc["model_id"])
    keyed = sorted(
        ((draw.random(), cls, rec, rng) for cls, rec, rng in posters),
        key=lambda t: t[0])
    chosen = [(cls, rec, rng) for _k, cls, rec, rng in keyed[:n_posts]]
    # Restore complaint order within the sample, so downstream code that assumes
    # the strongest complaint is first still holds.
    chosen.sort(key=lambda t: (order[t[0]], t[1]["applicant_id"]))
    return chosen


def persona_from(world: dict, proc: dict, cls: str, rec: dict, rng) -> dict:
    """The OP's true vs reported timeline (user noise: rounding + exaggeration)."""
    knobs = world["knobs"]
    by_act: dict[str, int] = {}
    for step in rec["path"]:
        if step['e']>knobs['as_of']:
            continue  # A future completion is not an observed personal duration.
        by_act[step["a"]] = by_act.get(step["a"], 0) + max(0, ddiff(step["e"], step["s"]))
    labelled = []
    for a in proc["activities"]:
        if a["id"] in by_act and a["visibility"] != "staff_only":
            labelled.append((a, by_act[a["id"]]))
    remembered = labelled[:6]
    wrong = chance(rng, knobs["p_wrong_fact_user"])
    infl = pick(rng, [1.15, 1.3, 1.6]) if wrong else 1.0
    reported_steps = []
    for a, d in remembered:
        reported_steps.append({"ref": a["id"], "label": act_label(a),
                               "reported": days_phrase(d * infl, "approximate" if not wrong else "wrong", rng),
                               "true_days": d,
                               "measurement_clock": {"start":"each_activity_visit_start",
                                   "end":"each_activity_visit_end","basis":"sum_visit_cycles",
                                   "population":"this_case_visits_completed_by_observation_date",
                                   "statistic":"individual_completion","as_of":knobs['as_of']}})
    total = rec["elapsed_days"]
    decisions={a["id"] for a in proc["activities"] if a.get("element_ref")
        and a["element_ref"].startswith("E") and a["visibility"]=="applicant_facing"
        and proc["terminal_artifact"] in a.get("artifacts_out",[])}
    has_decision=any(step["a"] in decisions for step in rec["path"])
    actual_outcome=rec.get("provisional_outcome") or rec["outcome"]
    endpoint="last_recorded_decision" if has_decision else "case_abandonment" if actual_outcome=="abandoned" else "last_path_activity_end"
    clock={"start":"beginning_preparation_or_filing","end":endpoint,"basis":"whole_case",
           "population":"individual","statistic":"individual_completion"}
    why = {
        "denied": "posting after a denial decision",
        "delayed": "the decision eventually arrived after a long wait, with long stretches without updates",
        "abandoned": "gave up on the case; an earlier decision, if present, is a separate event from withdrawal",
        "normal": "sharing my timeline for anyone searching later; it went fine",
    }[cls]
    failed = persona_failed_criteria(proc, rec)
    return {
        "applicant_id": rec["applicant_id"],
        "outcome": cls,
        "case_outcome": actual_outcome,
        "failed_criteria": [{"pred_id": f["pred_id"], "name": f["name"], "resolved": f["resolved"],
                             "reading": f["reading"]["label"]} for f in failed],
        "true_timeline": {"total_days": total, "arrived": rec["arrived"],
                          "rework_rounds": rec["total_rework_rounds"],
                          "fees_paid": rec.get("fees_paid_by_observation",rec["fees_paid"]),
                          "steps": [{"ref": a["id"], "days": d} for a, d in labelled]},
        "reported_timeline": {"total": days_phrase(total * infl, "approximate" if not wrong else "wrong", rng),
                              "total_days_reported": round(total * infl),
                              "exaggerated": wrong, "steps": reported_steps,"measurement_clock":clock},
        "why_posting": why,
    }


def build_thread(world: dict, proc: dict, rule: dict, persona: dict, others: list[dict],
                 contamination_pool: list[tuple[str, dict]], rng) -> tuple[list[dict], list[dict]]:
    """OP + comments. Returns (thread, contamination) per DESIGN artifact_spec."""
    knobs = world["knobs"]
    op_reveals = [_rev("process", "timing", "approximate" if not persona["reported_timeline"]["exaggerated"] else "wrong",
                       "total elapsed: %s" % persona["reported_timeline"]["total"],
                       measurement_clock=persona["reported_timeline"].get("measurement_clock"))]
    for s in persona["reported_timeline"]["steps"]:
        op_reveals.append(_rev(s["ref"], "exists", "exact", s["label"]))
        op_reveals.append(_rev(s["ref"], "timing", "approximate", s["reported"],
                              measurement_clock=s.get("measurement_clock")))
    if persona["true_timeline"]["fees_paid"]:
        fid = "wrong" if chance(rng, knobs["p_wrong_fact_user"]) else "approximate"
        op_reveals.append(_rev("process", "fee", fid,
                               fee_phrase(persona["true_timeline"]["fees_paid"], fid, rng)))
    op_wrong = ["timeline exaggerated by the poster"] if persona["reported_timeline"]["exaggerated"] else []
    # the criterion the OP failed on, as they remember it (decision.py)
    entries = {e["pred_id"]: e for e in (proc.get("decision_model") or {}).get("predicates", [])}
    for fc in persona.get("failed_criteria", [])[:2]:
        entry = entries.get(fc["pred_id"])
        if not entry or not entry.get("reading"):
            continue
        fid = "wrong" if chance(rng, knobs["p_wrong_fact_user"]) else "approximate"
        phrase = reading_phrase(entry, entry["reading"], fid, rng)
        op_reveals.append(_rev(fc["pred_id"], "criterion", fid,
                               "they %s me on %s: %s" % ("initially failed" if fc["resolved"] else "denied",
                                                         entry["name"].lower(), phrase),
                               criterion_kind=entry["kind"], from_case=True))
        if fid == "wrong":
            op_wrong.append("misstates the criterion %s" % fc["pred_id"])
    thread = [{"role": "op", "author": _author(rng), "reveals": op_reveals, "contamination": [],
               "wrong": op_wrong,
               "is_staff_insider": False}]
    contamination: list[dict] = []

    for other in others[:2]:
        revs = [_rev("process", "timing", "approximate", other["reported_timeline"]["total"],
                     measurement_clock=other["reported_timeline"].get("measurement_clock"))]
        st = other["reported_timeline"]["steps"][:2]
        for s in st:
            revs.append(_rev(s["ref"], "timing", "approximate", s["reported"],
                             measurement_clock=s.get("measurement_clock")))
        thread.append({"role": "comment", "author": _author(rng), "reveals": revs,
                       "contamination": [], "wrong": [], "is_staff_insider": False,
                       "persona_ref": other["applicant_id"]})

    if contamination_pool and chance(rng, 0.75):
        about, fact = pick(rng, contamination_pool)
        contamination.append({"about": about, "value": fact["value"]})
        thread.append({"role": "comment", "author": _author(rng), "reveals": [],
                       "contamination": [{"about": about, "value": fact["value"]}],
                       "wrong": [], "is_staff_insider": False})
    if chance(rng, knobs["p_stale"]) and proc["prior_version"]:
        pv = proc["prior_version"]
        thread.append({"role": "comment", "author": _author(rng),
                       "reveals": [_rev("prior_version", "fee", "wrong",
                                        "I did this in %s and it was %s"
                                        % (pv["version_date"][:4], fee_phrase(pv["fee_amount"], "exact")),
                                        describes_prior=True)],
                       "contamination": [], "wrong": ["describes the superseded version"],
                       "is_staff_insider": False})
    staff = _staff(proc)
    if staff and chance(rng, knobs["p_reveal_backoffice_in_comments"]):
        a = pick(rng, staff)
        thread.append({"role": "comment", "author": _author(rng),
                       "reveals": [_rev(a["id"], "exists", "exact", act_label(a), insider=True),
                                   _rev(a["id"], "actor", "exact", _actor_name(proc, a), insider=True)],
                       "contamination": [], "wrong": [], "is_staff_insider": True})
    if chance(rng, knobs["p_wrong_fact_user"]):
        a = pick(rng, _applicant_steps(proc) or proc["activities"])
        thread.append({"role": "comment", "author": _author(rng),
                       "reveals": [_rev(a["id"], "exists", "wrong",
                                        "you don't need %s at all, my cousin skipped it" % act_label(a))],
                       "contamination": [], "wrong": ["asserts a required step is optional"],
                       "is_staff_insider": False})
    return thread, contamination
