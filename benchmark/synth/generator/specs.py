"""artifact_spec: identity, URL, link graph, staleness, distractors, filler.

visibility.py decides *what* an artifact may say; this module decides *where it
lives and what links to it*, and generates the non-target half of the corpus:

* look-alike Corvane processes (full artifact sets, `target: false`);
* other, unmodelled programs in the same jurisdictions (encroachment permits,
  banner permits, ...) -- same artifact kinds, no truth behind them;
* generic city pages (home, departments, contact, agendas) that make the link
  graph navigable;
* off-topic threads in the same subreddits;
* filler, generated until the `distractor_ratio` knob is met or `filler_cap`
  binds (whichever comes first -- validate.py prints the achieved ratio).

The state statute text is emitted as `kind: "ordinance"` with
`subkind: "statute_text"` on a leginfo-style host: DESIGN's kind enum has no
`statute` member, and the renderer's legal-text style guide covers both.
"""
from __future__ import annotations

import re

from .rng import chance, dadd, pick, pick_n, random_date_between, sub_rng
from .visibility import (KIND_META, PER_JURISDICTION, act_label, days_phrase, fee_phrase,
                         build_thread, persona_from, plan_artifacts, reveals_for, select_personas)
from .world import JUR_BY_ID

THIRD_PARTY_HOSTS = [
    ("Brantley Land Use Group", "www.brantleyland.law", "/insights/%s"),
    ("PermitPath Partners", "permitpathpartners.com", "/guides/%s"),
    ("Sunridge Solar & Electric", "www.sunridgesolar.com", "/permits/%s"),
    ("Calder Valley Consulting", "caldervalleyconsulting.com", "/resources/%s"),
    ("HomeownerHQ", "www.homeownerhq.net", "/permits/%s"),
]

# Non-target programs in the same jurisdictions (no truth behind them).
FILLER_PROGRAMS = [
    ("Encroachment Permit", "encroachment-permit"), ("Banner and Sign Permit", "banner-sign-permit"),
    ("Garage Sale Permit", "garage-sale-permit"), ("Dog License", "dog-license"),
    ("Fence Height Exception", "fence-height-exception"), ("Driveway Approach Permit", "driveway-approach"),
    ("Block Party Closure", "block-party"), ("Parklet Program", "parklet-program"),
    ("Alarm System Permit", "alarm-permit"), ("Massage Establishment Permit", "massage-permit"),
    ("Film Permit", "film-permit"), ("Sidewalk Dining Permit", "sidewalk-dining"),
    ("Grading Permit", "grading-permit"), ("Demolition Permit", "demolition-permit"),
    ("Water Heater Express Permit", "water-heater-permit"), ("Fire Alarm Plan Review", "fire-alarm-plan-review"),
    ("Newsrack Permit", "newsrack-permit"), ("Oversize Load Permit", "oversize-load-permit"),
    ("Tobacco Retailer License", "tobacco-retailer-license"), ("Mobile Home Park Registration", "mobile-home-park"),
]

OFFTOPIC = [
    "pothole on Mercer has been there since March",
    "why is the water bill so high this quarter",
    "best taqueria in town, settle this",
    "parking ticket appeal actually worked",
    "school boundary change thread",
    "anyone else lose power last night",
    "recommend a handyman who answers the phone",
    "new bike lane on Third is a mess",
    "raccoons in the green bin again",
    "is the farmers market moving",
    "property tax reassessment after remodel",
    "noise complaint process, does it do anything",
    "moving here from out of state, neighborhoods?",
    "city budget meeting recap",
    "leaf blower ordinance enforcement",
]

GENERIC_PAGES = [
    ("home", "", "%(name)s | Official Website"),
    ("departments_index", "departments", "Departments and Divisions"),
    ("contact", "contact", "Contact Us"),
    ("agendas", "agendas-and-minutes", "Agendas and Minutes"),
    ("dept_page", "departments/%(dept_slug)s", "%(umbrella)s"),
    ("counter_hours", "services/permit-center-hours", "Permit Center Hours and Appointments"),
    ("how_to_pay", "finance/how-to-pay", "How to Pay a Fee or Deposit"),
    ("staff_directory", "directory", "Staff Directory"),
]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _url(jur: dict, path: str) -> str:
    return "https://%s/%s" % (jur["host"], path.lstrip("/"))


def _spec(world, **kw) -> dict:
    kw.setdefault("world", world["world"])
    kw.setdefault("links_to", [])
    kw.setdefault("reveals", [])
    kw.setdefault("must_not_reveal", [])
    kw.setdefault("contamination", [])
    kw.setdefault("persona", None)
    kw.setdefault("thread", None)
    kw.setdefault("stale", False)
    kw.setdefault("describes_version", 1)
    return kw


def _style(kind: str, lineage=None, **extra) -> dict:
    _, _, register, length = KIND_META[kind]
    d = {"register": register, "length_words": list(length), "template_lineage": lineage}
    d.update(extra)
    return d


def _artifact_date(rng, kind: str, world: dict, rule: dict, proc: dict, statutes: dict) -> tuple[str, bool]:
    """(date, stale). Stale = the artifact predates the current version."""
    as_of = world["knobs"]["as_of"]
    adopted, prior = rule["adopted"], proc["prior_version"]
    can_be_stale = bool(prior)
    want_stale = can_be_stale and chance(rng, world["knobs"]["p_stale"] * (1.5 if kind == "third_party_guide" else 1.0))
    early_lo = prior["version_date"] if prior else adopted
    early_hi = dadd(adopted, -5) if prior else adopted
    if kind in ("ordinance",):
        return adopted, False
    if kind == "fee_resolution":
        return dadd(adopted, rng.randrange(-30, 90)), False
    if kind == "staff_report":
        return dadd(adopted, -(14 + rng.randrange(28))), False
    if kind == "council_minutes":
        return adopted, False
    if kind == "bill_analysis":
        return dadd(statutes[proc["stat_id"]]["enacted"], -(60 + rng.randrange(120))), False
    if kind == "audit_excerpt":
        return random_date_between(rng, dadd(as_of, -420), dadd(as_of, -30)), False
    if kind == "official_stats":
        return dadd(as_of, -(7 + rng.randrange(60))), False
    if want_stale and early_hi > early_lo:
        return random_date_between(rng, early_lo, early_hi), True
    lo = dadd(adopted, 10)
    return (random_date_between(rng, lo, as_of) if as_of > lo else lo), False


def _url_for(kind: str, jur: dict, rule: dict, proc: dict, statutes: dict, rng, n: int = 1) -> tuple[str, str]:
    """(url, publisher)"""
    pslug = slug(proc["program_name"])
    dept_slug = slug(jur["umbrella"])
    if kind == "program_page":
        return _url(jur, "services/permits/%s" % pslug), jur["name"]
    if kind == "generic_permits_page":
        return _url(jur, "services/permits"), jur["name"]
    if kind == "form":
        return _url(jur, "sites/default/files/documents/%s.pdf" % slug(proc["form_name"])), jur["name"]
    if kind == "checklist":
        return _url(jur, "sites/default/files/documents/%s.pdf" % slug(proc["checklist_name"])), jur["name"]
    if kind == "faq":
        return _url(jur, "services/permits/%s/faq" % pslug), jur["name"]
    if kind == "fee_schedule":
        return _url(jur, "finance/master-fee-schedule"), jur["name"]
    if kind == "fee_resolution":
        return "https://%s/matters/%s.pdf" % (jur["legislative_host"], slug(rule["cite"])), jur["name"]
    if kind == "ordinance":
        return ("https://%s/codes/code_of_ordinances?nodeId=%s"
                % (jur["code_host"], slug(proc["program_name"]).upper().replace("-", "_")), jur["name"])
    if kind == "staff_report":
        return ("https://%s/matters/%s/attachment-I-staff-report.pdf"
                % (jur["legislative_host"], slug(rule["cite"])), jur["name"])
    if kind == "council_minutes":
        return "https://%s/minutes/%s-action-minutes.pdf" % (jur["legislative_host"], rule["adopted"]), jur["name"]
    if kind == "sop":
        if chance(rng, 0.5):
            return ("https://www.publicrecordsvault.org/requests/%d/responsive-documents.pdf" % (1000 + rng.randrange(8000)),
                    "PublicRecordsVault (records request response)")
        return _url(jur, "sites/default/files/documents/sop-%s.pdf" % pslug), jur["name"]
    if kind == "audit_excerpt":
        return _url(jur, "sites/default/files/audit/%s-performance-audit.pdf" % pslug), \
            "%s, Office of the %s Auditor" % (jur["name"], "County" if jur["kind"] == "county" else "City")
    if kind == "news":
        return "https://%s/%s/%s/" % (jur["news"][1], rule["adopted"][:7].replace("-", "/"), pslug), jur["news"][0]
    if kind == "third_party_guide":
        name, host, path = pick(rng, THIRD_PARTY_HOSTS)
        return "https://%s%s" % (host, path % ("%s-%s" % (slug(jur["short"]), pslug))), name
    if kind == "bill_analysis":
        stat = statutes[proc["stat_id"]]
        host = "leginfo.marisol.gov" if stat["state"] == "Marisol" else "legislature.corvane.gov"
        return ("https://%s/bills/%s/analyses/%s.pdf"
                % (host, slug(stat["bill"]), slug(stat["committee"])),
                "%s, %s" % (stat["state"] + " Legislature", stat["committee"]))
    if kind == "official_stats":
        return _url(jur, "departments/%s/performance-dashboard" % dept_slug), jur["name"]
    if kind == "reddit_thread":
        return ("https://www.reddit.com/%s/comments/%s/%s/"
                % (jur["subreddit"], _b36(rng), pslug[:40]), jur["subreddit"])
    if kind == "forum_thread":
        return ("https://www.citydataforum.net/%s/%d-%s.html"
                % (slug(jur["state"]), 100000 + rng.randrange(800000), pslug[:40]), "City-Data Forum")
    return _url(jur, pslug), jur["name"]


def _b36(rng) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(chars[rng.randrange(36)] for _ in range(6))


# ------------------------------------------------------------ contamination
def contamination_pool(processes: dict, rules: dict, mid: str) -> list[tuple[str, dict]]:
    """Facts about *other* processes that plausibly leak into this one's artifacts."""
    me = processes[mid]
    pool = []
    for other_mid, p in processes.items():
        if other_mid == mid:
            continue
        same_stat = p["stat_id"][-2:] == me["stat_id"][-2:]
        same_jur = p["jur_id"] == me["jur_id"]
        if not (same_stat or same_jur):
            continue
        r = rules[other_mid]
        if same_stat:
            pool.append((other_mid, {"value": "in %s the same program costs %s and %s"
                                     % (p["jurisdiction"], fee_phrase(r["fee"]["amount"], "exact"),
                                        "requires " + act_label(p["activities"][0]).lower())}))
            pool.append((other_mid, {"value": "%s calls it the %s and issues a %s"
                                     % (p["jurisdiction"], p["program_name"], p["terminal_artifact"])}))
        else:
            pool.append((other_mid, {"value": "the city's %s process is run by %s and took me %s"
                                     % (p["program_name"], p["lead_department"],
                                        days_phrase(p["activities"][-1]["timing"]["median_days"] * 3,
                                                    "vague"))}))
    return pool


# ------------------------------------------------------------------ builder
def build_specs(world: dict, statutes: dict, rules: dict, processes: dict,
                logs: dict, summaries: dict) -> list[dict]:
    specs: list[dict] = []
    seed = world["seed"]
    knobs = world["knobs"]

    # ---------- 1. statute text + bill analysis (state level) --------------
    for sid, stat in sorted(statutes.items()):
        rng = sub_rng(seed, "spec_statute", sid)
        host = "leginfo.marisol.gov" if stat["state"] == "Marisol" else "legislature.corvane.gov"
        reveals = [{"ref": e["element_id"], "field": "exists", "fidelity": "exact",
                    "value": e["name"], "must_quote": True, "level": "statute"} for e in stat["skeleton"]]
        reveals += [{"ref": e["element_id"], "field": "timing", "fidelity": "exact",
                     "value": "%d days" % e["shot_clock_days"], "must_quote": True, "level": "statute"}
                    for e in stat["skeleton"] if e["shot_clock_days"]]
        specs.append(_spec(
            world, artifact_id="%s__statute_text" % sid, kind="ordinance", subkind="statute_text",
            jur=None, stat_id=sid, target=stat["state"] == "Marisol",
            url="https://%s/codes/%s" % (host, slug(stat["cite"])),
            publisher="%s Legislature" % stat["state"], audience="public",
            date=stat["operative"], describes_version=1,
            reveals=reveals,
            style=_style("ordinance", None, sections=len(stat["sections"])),
            why="the statute itself: %s, %s (shape=%s)" % (stat["cite"], stat["bill"], stat["shape"])))
        if chance(rng, knobs["p_bill_analysis"]):
            # one analysis per statute; it describes the statute, not a jurisdiction
            proc_any = next((p for p in processes.values() if p["stat_id"] == sid), None)
            if proc_any:
                rv, _, _ = reveals_for("bill_analysis", world, proc_any, rules[proc_any["model_id"]],
                                       statutes, summaries[proc_any["model_id"]], rng, False, False)
                specs.append(_spec(
                    world, artifact_id="%s__bill_analysis" % sid, kind="bill_analysis", jur=None,
                    stat_id=sid, target=stat["state"] == "Marisol",
                    url=_url_for("bill_analysis", JUR_BY_ID["J1"], rules[proc_any["model_id"]], proc_any, statutes, rng)[0],
                    publisher="%s Legislature, %s" % (stat["state"], stat["committee"]),
                    audience="council", date=dadd(stat["enacted"], -(60 + rng.randrange(120))),
                    describes_version=1, reveals=rv, links_to=["%s__statute_text" % sid],
                    style=_style("bill_analysis"),
                    why="visibility model: p_bill_analysis=%.2f drew below threshold; state-level designed tier "
                        "(intended skeleton, shot clocks, cost estimate)" % knobs["p_bill_analysis"]))

    # ---------- 2. per-process artifacts -----------------------------------
    for mid, proc in sorted(processes.items()):
        rule, summ, log = rules[mid], summaries[mid], logs[mid]
        jur = JUR_BY_ID[proc["jur_id"]]
        is_target = proc["state"] == "Marisol"
        pool = contamination_pool(processes, rules, mid)
        plan = plan_artifacts(world, proc, rule, statutes)
        fee_sched_exists = chance(sub_rng(seed, "feesched", jur["id"]), knobs["p_publish_fee_schedule"])
        planned_kinds = {p["kind"] for p in plan}

        for item in plan:
            kind = item["kind"]
            rng = sub_rng(seed, "spec", mid, kind)
            date, stale = _artifact_date(rng, kind, world, rule, proc, statutes)
            rv, mnr, notes = reveals_for(kind, world, proc, rule, statutes, summ, rng, stale, fee_sched_exists)
            url, publisher = _url_for(kind, jur, rule, proc, statutes, rng)
            links = _links_for(kind, mid, jur, planned_kinds, proc)
            contam = []
            if kind in ("program_page", "faq", "third_party_guide") and pool and chance(rng, 0.35):
                about, fact = pick(rng, pool)
                contam = [{"about": about, "value": fact["value"]}]
            specs.append(_spec(
                world, artifact_id="%s__%s" % (mid, kind), kind=kind, jur=jur["id"],
                stat_id=proc["stat_id"], target=is_target, url=url, publisher=publisher,
                audience=KIND_META[kind][1], date=date,
                describes_version=1 if stale else proc["version"], stale=stale,
                reveals=rv, must_not_reveal=mnr, contamination=contam, links_to=links,
                style=_style(kind, rule["lineage_from"] if kind in ("program_page", "form", "ordinance") else None),
                why="; ".join([item["why"],
                               "stale: describes version 1 (page dated %s, current version adopted %s)" % (date, rule["adopted"])
                               if stale else "current version",
                               ("target process" if is_target else "distractor: Corvane look-alike of %s"
                                % statutes[proc["stat_id"]].get("lookalike_of", "?"))] + notes)))

        # ---------- reddit / forum threads from the log --------------------
        posters = select_personas(world, proc, log, summ)
        rng = sub_rng(seed, "threads", mid)
        n_threads = min(knobs["max_threads_per_process"], max(0, len(posters) // 3))
        if posters and n_threads == 0:
            n_threads = 1
        personas = [persona_from(world, proc, cls, rec, r) for cls, rec, r in posters[:12]]
        for t in range(n_threads):
            if not personas:
                break
            op = personas[t % len(personas)]
            others = [p for p in personas if p is not op][t::max(1, n_threads)][:2]
            thread, contam = build_thread(world, proc, rule, op, others, pool, rng)
            url, pub = _url_for("reddit_thread", jur, rule, proc, statutes, rng)
            date = dadd(op["true_timeline"]["arrived"], op["true_timeline"]["total_days"] + rng.randrange(1, 30))
            if date > knobs["as_of"]:
                date = knobs["as_of"]
            all_rev = [r for c in thread for r in c["reveals"]]
            specs.append(_spec(
                world, artifact_id="%s__reddit_%d" % (mid, t + 1), kind="reddit_thread", jur=jur["id"],
                stat_id=proc["stat_id"], target=is_target, url=url, publisher=jur["subreddit"],
                audience="public", date=date, describes_version=proc["version"],
                stale=any("describes_prior" in r for r in all_rev),
                reveals=all_rev,
                must_not_reveal=[a["id"] for a in proc["activities"]
                                 if a["visibility"] == "staff_only" and not any(r["ref"] == a["id"] for r in all_rev)],
                contamination=contam, thread=thread, persona=op,
                links_to=["%s__program_page" % mid] if "program_page" in planned_kinds and chance(rng, 0.4) else [],
                style=_style("reddit_thread", None, subreddit=jur["subreddit"]),
                why="complaint selection: OP outcome=%s (P(post)=%.2f), %d of %d applicants posted; "
                    "%d comments%s" % (op["outcome"], knobs["complaint_selection"].get(op["outcome"], 0.08),
                                       len(posters), summ["n_applicants"], len(thread) - 1,
                                       "; insider comment reveals a staff-only step"
                                       if any(c["is_staff_insider"] for c in thread) else "")))
        if chance(rng, knobs["p_publish_forum_thread"]) and personas:
            op = personas[-1]
            url, pub = _url_for("forum_thread", jur, rule, proc, statutes, rng)
            rv = [{"ref": "process", "field": "timing", "fidelity": "vague",
                   "value": "took me the better part of %s" % days_phrase(op["true_timeline"]["total_days"], "vague"),
                   "must_quote": False}]
            contam = []
            if pool:
                about, fact = pick(rng, pool)
                contam = [{"about": about, "value": fact["value"]}]
            specs.append(_spec(
                world, artifact_id="%s__forum_thread" % mid, kind="forum_thread", jur=jur["id"],
                stat_id=proc["stat_id"], target=is_target, url=url, publisher=pub, audience="public",
                date=random_date_between(rng, dadd(knobs["as_of"], -900), dadd(knobs["as_of"], -300)),
                describes_version=1 if proc["prior_version"] else proc["version"],
                stale=bool(proc["prior_version"]), reveals=rv, contamination=contam,
                must_not_reveal=[a["id"] for a in proc["activities"] if a["visibility"] == "staff_only"],
                style=_style("forum_thread"),
                why="older forum thread: polite, low-fidelity, high contamination (a natural carrier for "
                    "facts about other jurisdictions)"))

    # ---------- 3. per-jurisdiction shared pages ---------------------------
    for jur in world["jurisdictions"]:
        jmids = [m for m, p in sorted(processes.items()) if p["jur_id"] == jur["id"]]
        if not jmids:
            continue
        is_target = jur["state"] == "Marisol"
        rng = sub_rng(seed, "shared", jur["id"])
        for kind in sorted(PER_JURISDICTION):
            if kind == "fee_schedule" and not chance(sub_rng(seed, "feesched", jur["id"]), knobs["p_publish_fee_schedule"]):
                continue
            rv, mnr = [], []
            for mid in jmids:
                proc, rule, summ = processes[mid], rules[mid], summaries[mid]
                r2_, mnr2, _ = reveals_for(kind, world, proc, rule, statutes, summ,
                                           sub_rng(seed, "shared", jur["id"], kind, mid), False, True)
                for r in r2_:
                    r["process"] = mid
                rv += r2_
                # a shared page covers several programs, so hidden ids must be
                # process-qualified ("<model_id>:<activity_id>")
                mnr += ["%s:%s" % (mid, x) for x in mnr2]
            url, publisher = _url_for(kind, jur, rules[jmids[0]], processes[jmids[0]], statutes, rng)
            links = ["%s__program_page" % m for m in jmids] if kind == "generic_permits_page" else []
            specs.append(_spec(
                world, artifact_id="%s__%s" % (jur["id"], kind), kind=kind, jur=jur["id"], stat_id=None,
                target=is_target, url=url, publisher=publisher, audience=KIND_META[kind][1],
                date=random_date_between(rng, dadd(knobs["as_of"], -300), knobs["as_of"]),
                describes_version=1, reveals=rv, must_not_reveal=sorted(set(mnr)), links_to=links,
                style=_style(kind),
                why="one %s per jurisdiction; covers %d programs, so its reveals carry a `process` field"
                    % (kind, len(jmids))))

        # generic city pages (navigation scaffolding + distractors)
        for key, path, title in GENERIC_PAGES:
            p = path % {"dept_slug": slug(jur["umbrella"])}
            links = []
            if key == "home":
                links = ["%s__departments_index" % jur["id"], "%s__generic_permits_page" % jur["id"],
                         "%s__contact" % jur["id"]]
            elif key == "departments_index":
                links = ["%s__dept_page" % jur["id"]]
            elif key == "dept_page":
                links = ["%s__generic_permits_page" % jur["id"]] + \
                        ["%s__program_page" % m for m in jmids]
            specs.append(_spec(
                world, artifact_id="%s__%s" % (jur["id"], key), kind="generic_permits_page",
                subkind=key, jur=jur["id"], stat_id=None, target=False,
                url=_url(jur, p), publisher=jur["name"], audience="public",
                date=random_date_between(rng, dadd(knobs["as_of"], -500), knobs["as_of"]),
                describes_version=1, links_to=links, style=_style("generic_permits_page"),
                why="distractor + link-graph scaffolding: generic %s page (no process facts)" % key))

    # ---------- 4. non-target programs in target jurisdictions -------------
    for jur in world["jurisdictions"]:
        rng = sub_rng(seed, "filler_prog", jur["id"])
        for name, ps in FILLER_PROGRAMS[: 18 if jur["state"] == "Marisol" else 12]:
            kinds = (["program_page"] + (["form"] if chance(rng, 0.7) else [])
                     + (["faq"] if chance(rng, 0.4) else [])
                     + (["checklist"] if chance(rng, 0.25) else [])
                     + (["fee_schedule"] if chance(rng, 0.2) else []))
            for kind in kinds:
                path = {"program_page": "services/permits/%s" % ps,
                        "form": "sites/default/files/documents/%s-application.pdf" % ps,
                        "faq": "services/permits/%s/faq" % ps,
                        "checklist": "sites/default/files/documents/%s-checklist.pdf" % ps,
                        "fee_schedule": "finance/fees/%s" % ps}[kind]
                specs.append(_spec(
                    world, artifact_id="%s__%s__%s" % (jur["id"], ps.replace("-", "_"), kind),
                    kind=kind, jur=jur["id"], stat_id=None, target=False, about_program=name,
                    url=_url(jur, path), publisher=jur["name"], audience="applicant",
                    date=random_date_between(rng, dadd(knobs["as_of"], -700), knobs["as_of"]),
                    describes_version=1,
                    links_to=["%s__generic_permits_page" % jur["id"]],
                    style=_style(kind),
                    why="distractor: %s is a real-looking program in the same jurisdiction with no modelled "
                        "truth; retrieval must not confuse it with a target program" % name))

    # ---------- 5. off-topic threads in the same subreddits ----------------
    for jur in world["jurisdictions"]:
        rng = sub_rng(seed, "offtopic", jur["id"])
        subs = [jur["subreddit"], "r/%s" % jur["state"], "r/homeowners", "r/smallbusiness"]
        for i, topic in enumerate(pick_n(rng, OFFTOPIC, 5)):
            sub = pick(rng, subs)
            specs.append(_spec(
                world, artifact_id="%s__offtopic_%d" % (jur["id"], i + 1), kind="reddit_thread",
                jur=jur["id"], stat_id=None, target=False, url="https://www.reddit.com/%s/comments/%s/%s/"
                % (sub, _b36(rng), slug(topic)[:40]), publisher=sub, audience="public",
                date=random_date_between(rng, dadd(knobs["as_of"], -600), knobs["as_of"]),
                describes_version=1, thread=[{"role": "op", "author": "u_%s%d" % (slug(topic)[:6], rng.randrange(999)),
                                             "reveals": [], "contamination": [], "wrong": [], "is_staff_insider": False}],
                style=_style("reddit_thread", None, subreddit=sub, topic=topic),
                why="distractor: off-topic thread in a subreddit the solver will search (%s)" % sub))

    # ---------- 6. filler until distractor_ratio is met -------------------
    specs += _filler(world, specs)

    # ---------- 7. resolve the link graph ---------------------------------
    have = {s["artifact_id"] for s in specs}
    for s in specs:
        s["links_to"] = [l for l in s["links_to"] if l in have and l != s["artifact_id"]]
    return specs


def _links_for(kind: str, mid: str, jur: dict, planned: set, proc: dict) -> list[str]:
    sid = proc["stat_id"]
    prog = "%s__program_page" % mid
    out: list[str] = []
    if kind == "program_page":
        out = ["%s__%s" % (mid, k) for k in ("form", "checklist", "faq", "ordinance") if k in planned]
        out += ["%s__fee_schedule" % jur["id"], "%s__generic_permits_page" % jur["id"], "%s__statute_text" % sid]
    elif kind in ("form", "checklist", "faq", "official_stats", "news", "third_party_guide"):
        out = [prog] if "program_page" in planned else ["%s__generic_permits_page" % jur["id"]]
        if kind == "faq":
            out.append("%s__fee_schedule" % jur["id"])
        if kind == "third_party_guide":
            out += ["%s__form" % mid] if "form" in planned else []
    elif kind == "ordinance":
        out = ["%s__statute_text" % sid, "%s__fee_resolution" % mid]
    elif kind == "staff_report":
        out = ["%s__ordinance" % mid, "%s__fee_resolution" % mid, "%s__statute_text" % sid]
    elif kind == "council_minutes":
        out = ["%s__staff_report" % mid, "%s__ordinance" % mid]
    elif kind == "fee_resolution":
        out = ["%s__fee_schedule" % jur["id"]]
    elif kind == "sop":
        out = [prog] if "program_page" in planned else []
    elif kind == "audit_excerpt":
        out = [prog] if "program_page" in planned else []
    return out


def _filler(world: dict, specs: list[dict]) -> list[dict]:
    """Top up non-target artifacts until `distractor_ratio` is met (or the cap binds)."""
    knobs = world["knobs"]
    n_target = sum(1 for s in specs if s["target"])
    n_dist = len(specs) - n_target          # structured distractors built above
    need = int(round(knobs["distractor_ratio"] * n_target)) - n_dist
    # keep pure filler to at most `filler_share` of all distractors, so the
    # corpus stays mostly structured (look-alikes, sibling programs, city pages)
    share = knobs.get("filler_share", 0.6)
    need = max(0, min(need, knobs["filler_cap"], int(n_dist * share / max(1e-9, 1 - share))))
    out: list[dict] = []
    jurs = world["jurisdictions"]
    # a balanced mix, so the distractor corpus looks like the target corpus rather
    # than like 600 news stories: 8/20 municipal pages, 6/20 off-topic threads,
    # 3/20 news, 3/20 forum threads.
    MIX = (["page"] * 8) + (["offtopic"] * 6) + (["news"] * 3) + (["forum"] * 3)
    i = 0
    while len(out) < need:
        jur = jurs[i % len(jurs)]
        rng = sub_rng(world["seed"], "filler", i)
        mode = MIX[i % len(MIX)]
        i += 1
        name, ps = FILLER_PROGRAMS[(i // 2) % len(FILLER_PROGRAMS)]
        if mode == "news":
            year = 2021 + (i % 5)
            out.append(_spec(
                world, artifact_id="%s__fill%d__%s_news" % (jur["id"], i, ps.replace("-", "_")),
                kind="news", jur=jur["id"], stat_id=None, target=False, about_program=name,
                url="https://%s/%d/%02d/%s-%d/" % (jur["news"][1], year, 1 + (i % 12), ps, i),
                publisher=jur["news"][0], audience="public",
                date="%d-%02d-%02d" % (year, 1 + (i % 12), 1 + (i % 27)), describes_version=1,
                links_to=["%s__%s__program_page" % (jur["id"], ps.replace("-", "_"))],
                style=_style("news", None, length_words=[120, 250]),
                why="filler distractor (news about an unmodelled program) to meet distractor_ratio=%.1f"
                    % knobs["distractor_ratio"]))
        elif mode in ("offtopic", "forum"):
            topic = OFFTOPIC[i % len(OFFTOPIC)]
            if mode == "offtopic":
                sub = pick(rng, [jur["subreddit"], "r/%s" % jur["state"], "r/homeowners", "r/smallbusiness"])
                url = "https://www.reddit.com/%s/comments/%s/%s/" % (sub, _b36(rng), slug(topic)[:40])
                kind, publisher = "reddit_thread", sub
                style = _style("reddit_thread", None, subreddit=sub, topic=topic,
                               length_words=[60, 180], max_comments=3)
            else:
                url = "https://www.citydataforum.net/%s/%d-%s.html" % (
                    slug(jur["state"]), 100000 + rng.randrange(800000), slug(topic)[:40])
                kind, publisher = "forum_thread", "City-Data Forum"
                style = _style("forum_thread", None, topic=topic,
                               length_words=[60, 180], max_comments=3)
            out.append(_spec(
                world, artifact_id="%s__fill%d__%s" % (jur["id"], i, mode), kind=kind,
                jur=jur["id"], stat_id=None, target=False, url=url, publisher=publisher,
                audience="public",
                date=random_date_between(rng, dadd(knobs["as_of"], -800), knobs["as_of"]),
                describes_version=1,
                thread=([{"role": "op", "author": "u_%s%d" % (slug(topic)[:6], rng.randrange(999)),
                          "reveals": [], "contamination": [], "wrong": [], "is_staff_insider": False}]
                        + [{"role": "comment", "author": "u_%s%d" % (slug(topic)[3:9] or "anon", rng.randrange(999)),
                            "reveals": [], "contamination": [], "wrong": [], "is_staff_insider": False}
                           for _ in range(rng.randrange(3))]),
                style=style,
                why="filler distractor (%s thread, no process facts) to meet distractor_ratio=%.1f"
                    % (mode, knobs["distractor_ratio"])))
        else:
            kind = pick(rng, ["form", "faq", "program_page", "program_page", "checklist", "fee_schedule"])
            path = {"form": "sites/default/files/documents/%s-form-%d.pdf" % (ps, i),
                    "faq": "services/permits/%s/faq-%d" % (ps, i),
                    "program_page": "services/%s-%d" % (ps, i),
                    "checklist": "sites/default/files/documents/%s-checklist-%d.pdf" % (ps, i),
                    "fee_schedule": "finance/fee-schedule-%s-%d" % (ps, i)}[kind]
            out.append(_spec(
                world, artifact_id="%s__fill%d__%s_%s" % (jur["id"], i, ps.replace("-", "_"), kind),
                kind=kind, jur=jur["id"], stat_id=None, target=False, about_program=name,
                url=_url(jur, path), publisher=jur["name"], audience="applicant",
                date=random_date_between(rng, dadd(knobs["as_of"], -800), knobs["as_of"]),
                describes_version=1, links_to=["%s__generic_permits_page" % jur["id"]],
                style=_style(kind, None, length_words=[100, 220]),
                why="filler distractor (%s for an unmodelled program) to meet distractor_ratio=%.1f"
                    % (kind, knobs["distractor_ratio"])))
    return out
