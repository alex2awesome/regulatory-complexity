#!/usr/bin/env python3
"""Align predicted process activities to gold (`process_truth`) activities.

Two interchangeable aligners, both emitting the same human-checkable pair list:

* `offline_align` — deterministic: synonym-canonicalized token F1 + actor
  compatibility + order consistency, greedy 1-1 backbone then a granularity
  extension pass (so one predicted activity may cover several gold ones and
  vice versa). No network, no LLM; this is the default because the Codex
  backend takes minutes per call.
* `llm_align` — k independent matchings with both lists shuffled per run (the
  `crosswalk_eval.py` pattern), keeping pairs with >= ceil(k/2) votes.

Granularity/alignment noise is error source #8 in docs/2026-09-15-process-benchmarks-plan.md:
every pair carries its score/votes and `relation` so a human can audit it, and
`--align both` reports offline-vs-LLM agreement as an alignment-noise estimate.
"""

import json
import math
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------- vocabulary

PHRASES = [("site visit", "inspection"), ("site inspection", "inspection"),
           ("field visit", "inspection"), ("plan check", "review"),
           ("plan review", "review"), ("plans examination", "review"),
           ("pre-application", "preapplication"), ("pre application", "preapplication"),
           ("third-party", "third_party"), ("third party", "third_party"),
           ("sign-off", "signoff"), ("back-office", "internal")]

# token -> concept. Required groups: inspect / submit / issue / review.
SYN = {}
for _canon, _words in {
    "inspect": "inspect inspects inspection inspections inspected inspecting reinspect "
               "reinspection reinspections walkthrough",
    "submit": "submit submits submittal submittals submitted submitting apply applies "
              "application applications file files filing intake lodge",
    "issue": "issue issues issued issuance grant grants granted approve approves approved "
             "approval recognize recognizes recognition",
    "review": "review reviews reviewed reviewing check checks checked screening screen "
              "verify verifies verification completeness examine examination assess",
    "fee": "fee fees pay pays paid payment paying invoice billing",
    "correct": "correct corrects corrected correction corrections corrective repair repairs "
               "remediate remediation fix abate abatement",
    "notice": "notice notices notify notified notification notifying inform informs letter",
    "certificate": "certificate certificates cert certification compliance",
    "permit": "permit permits permitted",
    "eligible": "eligible eligibility qualify qualifies qualification screen_eligibility",
    "record": "record records recorded recording archive archives archiving file_record "
              "retention docket",
    "hearing": "hearing hearings public_hearing",
    "appeal": "appeal appeals appealed",
    "meeting": "meeting meetings consultation consult consults preapplication conference",
    "referral": "referral referrals refer refers referred route routes routing forward "
                "forwards handoff transfer",
    "decision": "decision decide decides determination determine determines adjudicate",
    "deed": "deed restriction covenant",
}.items():
    for _w in _words.split():
        SYN[_w] = _canon

STOP = set("the a an of to for and or with on in at by is are be been from if any all as "
           "that this its it must may shall will not no do does per via into onto out up "
           "then when where which who whom whose about after before during each other than "
           "step process new use used using upon so such".split())

ACTOR_FAMILIES = {
    "applicant": "applicant owner homeowner home_owner property_owner resident petitioner "
                 "business_owner operator customer public_member",
    "third_party": "third_party contractor licensed_contractor licensed_professional "
                   "private_inspector consultant engineer architect vendor",
    "building": "building building_division building_department building_official "
                "plan_check plans_examiner dsd development_services permits_division",
    "permit_center": "permit_center permit_services permit_counter counter front_counter "
                     "clerk intake_staff permit_technician records_clerk",
    "inspector": "inspector inspectors field_inspector code_inspector code_enforcement "
                 "housing_inspector building_inspector",
    "planning": "planning planning_division planning_department zoning zoning_administrator",
    "fire": "fire fire_marshal fire_department fire_prevention",
    "health": "health health_officer environmental_health health_department",
    "county": "county county_assessor assessor recorder county_clerk",
    "state": "state state_agency hcd department_of_state",
    "public": "public neighbors community",
    "agency": "agency local_agency city city_staff staff program_staff official department "
              "jurisdiction government municipality town",
}

# --- domain acronyms / phrases and extra actor families (added 2026-09-15 after the Benchmark-1 pilot) ---
_EXTRA_PHRASES = [
    ("firearm safety certificate", "fsc"), ("fsc test", "fsc"), ("dealer record of sale", "dros"),
    ("dros entry system", "des"), ("permission to operate", "pto"), ("private party transfer", "ppt"),
    ("private-party transfer", "ppt"), ("certificate of eligibility", "coe"), ("environmental health", "eh"),
    ("expedited service", "expedited"), ("field office", "fo"), ("plan check", "review"), ("plan review", "review"),
    ("safe handling demonstration", "safehandling demo"), ("safe-handling demonstration", "safehandling demo"), ("safe handling", "safehandling demo"),
    ("waiting period", "wait"), ("10-day", "wait"), ("ten-day", "wait"), ("background check", "backgroundcheck"),
    ("eligibility check", "backgroundcheck"), ("interconnection", "pto"), ("oath ceremony", "oath"),
    ("biometrics", "biometrics"), ("live scan", "livescan"), ("fingerprint", "livescan"),
    ("public records request", "records"), ("records request", "records"), ("ebt card", "ebt"),
]
try:
    PHRASES = list(PHRASES) + _EXTRA_PHRASES
except NameError:
    PHRASES = _EXTRA_PHRASES
ACTOR_FAMILIES.update({
    "applicant": ACTOR_FAMILIES.get("applicant", "applicant") + " purchaser buyer owner homeowner claimant requester requestor "
                 "installer licensee candidate vendor operator business_owner seller private_seller",
    "dealer": "dealer dealer_salesperson dealer_coe_holder ffl gun_store licensed_dealer",
    "instructor": "instructor certified_instructor doj_instructor proctor",
    "state": ACTOR_FAMILIES.get("state", "state") + " doj doj_bof bureau_of_firearms uscis officer adjudicator edd cslb cdss "
             "dpss caseworker eligibility_worker registrar board utility ioe records_unit cpra_unit",
    "records": "records records_unit cpra_unit custodian clerk city_clerk",
    "county": ACTOR_FAMILIES.get("county", "county") + " ssbs benefits_specialist eligibility_specialist eligibility_worker "
              "caseworker clerical central_support calsaws dpss ssa hsa county_worker intake_worker",
    "third_party": ACTOR_FAMILIES.get("third_party", "third_party") + " contractor licensed_contractor consultant expediter",
})
ACTOR_CANON = {w: fam for fam, ws in ACTOR_FAMILIES.items() for w in ws.split()}
CITY_SIDE = {"building", "permit_center", "inspector", "planning", "fire", "health", "agency"}

REWORK_WORDS = ("rework", "loop", "return", "revocation", "revoke", "reinspect", "resubmit",
                "back_to", "cycle")
VISIBLE = {"applicant_facing", "applicant_inferable"}

W_TEXT, W_ACTOR, W_ORDER = 0.72, 0.18, 0.10
# T_PRIMARY: accept a 1-1 pair. T_EXTEND (+ T_EXTEND_TEXT + a compatible actor):
# accept an extra pair that makes the alignment many-to-one / one-to-many — a
# granularity claim needs real content overlap, not just lane and position.
T_PRIMARY, T_EXTEND, T_EXTEND_TEXT, T_DISTRACTOR = 0.32, 0.40, 0.40, 0.32

# ------------------------------------------------------------- normalization

def canon_actor(a):
    if not a:
        return "unknown"
    a = re.sub(r"[^a-z0-9_ ]", " ", str(a).lower()).strip()
    a = re.sub(r"\s+", "_", a)
    if a in ACTOR_CANON:
        return ACTOR_CANON[a]
    for part in a.split("_or_") + a.split("_"):
        if part in ACTOR_CANON:
            return ACTOR_CANON[part]
    for w, fam in ACTOR_CANON.items():
        if len(w) >= 4 and (a.startswith(w) or w in a):
            return fam
    return a or "unknown"

def actor_compat(pa, ga):
    if pa == ga:
        return 1.0
    if "unknown" in (pa, ga) or "agency" in (pa, ga):
        return 0.6
    if pa in CITY_SIDE and ga in CITY_SIDE:
        return 0.35
    return 0.0

def toks(text):
    if not text:
        return set()
    t = str(text).lower()
    for a, b in PHRASES:
        t = t.replace(a, b)
    out = set()
    for w in re.split(r"[^a-z0-9_]+", t):
        if not w or w in STOP or len(w) < 3 and not w.isdigit():
            continue
        out.add(SYN.get(w, _stem(w)))
    return out


def _stem(w):
    """Crude suffix stripper so 'scheduled'/'schedule'/'scheduling' and
    'notices'/'notice' share a token (only applied to words not in SYN)."""
    if len(w) <= 4 or w.isdigit():
        return w
    for suf in ("ings", "ing", "ies", "ied", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            base = w[: -len(suf)]
            if suf == "ies" or suf == "ied":
                base += "y"
            return base
    return w

def f1(a, b):
    """Text similarity: max of Dice and a damped overlap coefficient, so a short
    predicted name ("Safe handling demonstration") still matches a long gold
    name that contains it."""
    if not a or not b:
        return 0.0
    hit = len(a & b)
    if not hit:
        return 0.0
    dice = 2 * hit / (len(a) + len(b))
    overlap = hit / min(len(a), len(b))
    # the overlap boost needs at least two shared concept tokens, else a single
    # shared word ("notice") would pair unrelated short names
    return max(dice, 0.85 * overlap if hit >= 2 else dice)

def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(x or ""))
    return float(m.group(0).replace(",", "")) if m else None

def _fee(a):
    f = a.get("fee")
    if f is None:
        return None
    return _num(f.get("amount") if isinstance(f, dict) else f)

def _median(a):
    t = a.get("timing") or {}
    if not isinstance(t, dict):
        t = {}
    # A legal clock or service promise is not a measured/estimated duration.
    if t.get("kind") in {"statutory_cap", "target", "deadline"}:
        return None
    for k in ("median_days", "median", "p50_days", "days", "median_business_days"):
        v = _num(t.get(k) if k in t else a.get(k))
        if v is not None:
            return v
    if t.get("kind") in {"observed", "reported", "individual", "median", "typical"}:
        return _num(t.get("value_days"))
    return None


def _end_to_end(m):
    for field in ("process_timing", "end_to_end"):
        value = m.get(field)
        if isinstance(value, dict):
            if str(value.get("kind", "")).strip().lower() in {"statutory_cap", "target", "deadline"}:
                continue
            value = _num(value.get("median_days"))
            if value is not None and math.isfinite(value) and value >= 0:
                return value
    if str(m.get("kind", "")).strip().lower() in {"statutory_cap", "target", "deadline"}:
        return None
    value = _num(m.get("end_to_end_median_days"))
    return value if value is not None and math.isfinite(value) and value >= 0 else None

def _edge_kind(e):
    t = str(e.get("type") or e.get("kind") or "sequence").lower()
    if any(w in t for w in REWORK_WORDS):
        return "rework"
    if 'parallel' in t or 'concurrent' in t:
        return 'parallel'
    return 'order'

def _rank(acts, edges):
    """Longest-path depth over order edges (cycle-safe), tie-broken by array order."""
    idx = {a["id"]: i for i, a in enumerate(acts)}
    preds = {a["id"]: [] for a in acts}
    for e in edges:
        if e["kind"] == "order" and e["to"] in preds and e["from"] in idx:
            preds[e["to"]].append(e["from"])
    depth, state = {}, {}

    def d(n):
        if n in depth:
            return depth[n]
        if state.get(n):            # cycle: break it
            return 0
        state[n] = 1
        depth[n] = 1 + max([d(p) for p in preds[n]], default=-1)
        state[n] = 0
        return depth[n]

    order = sorted((a["id"] for a in acts), key=lambda n: (d(n), idx[n]))
    n = max(len(order) - 1, 1)
    return {aid: i / n for i, aid in enumerate(order)}

def closure(acts, edges, kind="order"):
    """Transitive closure of `kind` edges: set of (u, v) with u before v."""
    adj = {a["id"]: set() for a in acts}
    for e in edges:
        if e["kind"] == kind and e["from"] in adj and e["to"] in adj:
            adj[e["from"]].add(e["to"])
    out = set()
    for s in adj:
        seen, stack = set(), list(adj[s])
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            stack += [w for w in adj.get(v, ()) if w not in seen]
        out |= {(s, v) for v in seen if v != s}
    return out

def load_model(path_or_obj):
    """Normalize a predicted model or a process_truth into one shape."""
    m = (json.loads(pathlib.Path(path_or_obj).read_text())
         if isinstance(path_or_obj, (str, pathlib.Path)) else dict(path_or_obj))
    acts = []
    for i, a in enumerate(m.get("activities") or []):
        aid = str(a.get("id") or f"X{i + 1:02d}")
        name, local = a.get("name") or "", a.get("local_name") or ""
        tk, tkl = toks(name), toks(local)
        lane = {'payer': 'applicant', 'third_party': 'third_party'}.get(a.get('actor_role'))
        acts.append({"id": aid, "name": name, "local_name": local, "idx": i,
                     "actor": lane or canon_actor(a.get("actor")), "actor_raw": a.get("actor"),
                     "toks": tk, "toks_local": tkl or tk,
                     "visibility": a.get("visibility"), "element_ref": a.get("element_ref"),
                     "mandated_element": a.get("mandated_element"),
                     "mandated_elements": a.get("mandated_elements") or [],
                     "fee": _fee(a), "median_days": _median(a),
                     "optional": bool(a.get("optional")), "rework": a.get("rework"),
                     "confidence": _num(a.get("confidence")),
                     "evidence": a.get("evidence") or [], "raw": a})
    edges = [{"from": str(e.get("from", e.get('source'))),
              "to": str(e.get("to", e.get('target'))), "kind": _edge_kind(e),
              "type": e.get("type", e.get('kind'))} for e in (m.get("edges") or [])]
    for a in acts:                      # activity-level rework (process_truth style)
        rw = a["rework"]
        if isinstance(rw, dict) and rw.get("back_to"):
            edges.append({"from": a["id"], "to": str(rw["back_to"]), "kind": "rework",
                          "type": "rework"})
    ranks = _rank(acts, edges)
    for a in acts:
        a["rank"] = ranks.get(a["id"], 0.0)
    return {"raw": m, "activities": acts, "edges": edges,
            "by_id": {a["id"]: a for a in acts},
            "model_id": m.get("model_id") or m.get("jurisdiction") or "model",
            "prior_version": m.get("prior_version"),
            "end_to_end": _end_to_end(m)}

# -------------------------------------------------------------- offline pass

def sim(p, g):
    text = max(f1(p["toks"], g["toks"]), f1(p["toks"], g["toks_local"]),
               f1(p["toks_local"], g["toks"]), f1(p["toks_local"], g["toks_local"]))
    order = 1.0 - abs(p["rank"] - g["rank"])
    return round(W_TEXT * text + W_ACTOR * actor_compat(p["actor"], g["actor"])
                 + W_ORDER * order, 4), round(text, 4)

def offline_align(pred, gold):
    """Greedy 1-1 backbone at T_PRIMARY, then a granularity extension pass at
    T_EXTEND that lets one predicted activity cover several gold activities
    (relation `split`) and several predicted activities cover one gold
    (relation `merge`)."""
    cand = []
    for p in pred["activities"]:
        for g in gold["activities"]:
            s, text = sim(p, g)
            cand.append((s, text, p, g))
    cand.sort(key=lambda c: (-c[0], c[2]["idx"], c[3]["idx"]))
    pairs, up, ug = [], set(), set()
    for s, text, p, g in cand:
        if s < T_PRIMARY or p["id"] in up or g["id"] in ug:
            continue
        pairs.append(_pair(p, g, s, text, "primary"))
        up.add(p["id"]); ug.add(g["id"])
    for s, text, p, g in cand:          # extension: many-to-one / one-to-many
        if s < T_EXTEND or text < T_EXTEND_TEXT or not actor_compat(p["actor"], g["actor"]):
            continue
        if (p["id"] in up) == (g["id"] in ug):
            continue                    # both used (1-1 already) or both free
        pairs.append(_pair(p, g, s, text, "split" if p["id"] in up else "merge"))
        up.add(p["id"]); ug.add(g["id"])
    pairs.sort(key=lambda d: (d["gold_idx"], d["pred_idx"]))
    return pairs

def _pair(p, g, s, text, relation, votes=None, k=None):
    return {"pred": p["id"], "gold": g["id"], "pred_name": p["name"][:110],
            "gold_name": (g["name"] or g["local_name"])[:110], "relation": relation,
            "score": s, "text_sim": text, "pred_actor": p["actor"], "gold_actor": g["actor"],
            "actor_match": p["actor"] == g["actor"],
            "actor_compat": actor_compat(p["actor"], g["actor"]),
            "pred_idx": p["idx"], "gold_idx": g["idx"],
            **({"votes": votes, "k": k} if votes is not None else {})}

# ------------------------------------------------------------------ LLM pass

PROMPT = """You are aligning two descriptions of the same government process.

PREDICTED activities (a model an agent reconstructed) and GOLD activities (the
true process) are listed below in random order. Match each predicted activity to
the gold activity/activities it describes.

Rules:
- Granularity differs on purpose. A predicted activity may cover SEVERAL gold
  activities (emit one pair per gold), and several predicted activities may cover
  ONE gold activity. Emit every such pair.
- Match on the ACT (who does what, producing what), not on wording. Local names
  differ ("plan check" = "plan review"; "site visit" = "inspection").
- Leave an activity unmatched if nothing corresponds. Do not force matches.
- Output JSON only: {"pairs": [{"pred": "<pred id>", "gold": "<gold id>",
  "why": "<<=12 words>"}]}
"""

def _llm_json_inline(user, model=None, max_tokens=16000):
    """llm.llm_json, but with the prompt inline (the scorer ships no file in
    pipeline/prompts/). Same backends, same one repair retry."""
    sys.path.insert(0, str(HERE.parent))
    import llm
    msgs = [{"role": "user", "content": user}]
    for attempt in range(2):
        raw = llm._complete(msgs, model, max_tokens)
        try:
            return llm.extract_json(raw)
        except Exception as e:                                  # noqa: BLE001
            if attempt == 1:
                raise
            msgs += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": f"Not parseable JSON ({e}). "
                                                 f"Emit the corrected full JSON only."}]

def _lines(acts):
    return [f"{a['id']} | {a['actor_raw'] or a['actor']} | "
            f"{a['name'] or a['local_name']}"
            + (f"  (local name: {a['local_name']})" if a['local_name'] and a['name'] else "")
            for a in acts]

def llm_align(pred, gold, k=3, model=None, seed=100):
    """k shuffled matchings; keep pairs with >= ceil(k/2) votes."""
    votes, runs = {}, []
    for i in range(k):
        rng = random.Random(seed + i)
        pl, gl = _lines(pred["activities"]), _lines(gold["activities"])
        rng.shuffle(pl); rng.shuffle(gl)
        user = (PROMPT + "\nPREDICTED:\n" + "\n".join(pl)
                + "\n\nGOLD:\n" + "\n".join(gl) + "\n")
        got = _llm_json_inline(user, model=model)
        seen = set()
        for pr in (got or {}).get("pairs", []):
            key = (str(pr.get("pred")), str(pr.get("gold")))
            if key in seen or key[0] not in pred["by_id"] or key[1] not in gold["by_id"]:
                continue
            seen.add(key)
            votes[key] = votes.get(key, 0) + 1
        runs.append(sorted(seen))
    need = math.ceil(k / 2)
    pairs = []
    for (pid, gid), v in votes.items():
        if v < need:
            continue
        p, g = pred["by_id"][pid], gold["by_id"][gid]
        s, text = sim(p, g)
        pairs.append(_pair(p, g, s, text, "llm", votes=v, k=k))
    for d in pairs:                     # relation from the vote pattern
        np_ = sum(1 for e in pairs if e["gold"] == d["gold"])
        ng = sum(1 for e in pairs if e["pred"] == d["pred"])
        d["relation"] = "merge" if np_ > 1 else "split" if ng > 1 else "primary"
    pairs.sort(key=lambda d: (d["gold_idx"], d["pred_idx"]))
    return pairs, {"votes_needed": need, "runs": runs,
                   "n_pairs_any_vote": len(votes), "n_pairs_kept": len(pairs)}

def agreement(a, b):
    """Jaccard of two pair sets — the alignment-noise estimate (error source #8)."""
    sa = {(d["pred"], d["gold"]) for d in a}
    sb = {(d["pred"], d["gold"]) for d in b}
    return {"n_a": len(sa), "n_b": len(sb), "n_both": len(sa & sb),
            "jaccard": round(len(sa & sb) / len(sa | sb), 4) if (sa | sb) else None,
            "only_a": sorted(sa - sb)[:25], "only_b": sorted(sb - sa)[:25]}
