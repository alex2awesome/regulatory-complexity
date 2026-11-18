"""Blind process-model construction (docs/2026-09-30-toy-statute-blind-process-plan.md).

A builder (LLM) reads only the statute text and free-text documents and writes catalog.json
(steps, events, admin column map, fee items, candidate designs). This module turns that catalogue
into a statute package the model can fit, maps admin CSVs by the builder's column map, and checks
extracted evidence against the catalogue's vocabulary. The model conventions applied here are the
same ones the oracle package uses: fixed prepare/completeness-check/correction skeleton, one
objection-conditional step type (named 'hearing' internally), agency/board/inspector steps scaled
by town pace, no fee on the conditional or repeated steps.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROLE_ID = {"application_prep": "prepare", "completeness_check": "completeness_check",
           "correction": "correction", "decision_issue": "decision_issue"}
SCALED_ACTORS = {"agency", "board", "inspector"}


def compile_catalog(cat: dict, public_context: dict, statute_id: str = "blind") -> tuple[dict, dict]:
    """Return (package, rename) where rename maps builder step ids to package step ids."""
    steps = cat["steps"]
    rename, notes = {}, []
    for role, sid in ROLE_ID.items():
        hits = [s for s in steps if s.get("role") == role]
        if len(hits) != 1:
            raise ValueError(f"catalogue needs exactly one '{role}' step, found {len(hits)}")
        rename[hits[0]["id"]] = sid
    cond = [s for s in steps if s.get("role") == "middle" and s.get("only_if_objection")]
    if len(cond) > 1:
        raise ValueError("at most one objection-conditional step type is supported")
    for s in cond:
        rename[s["id"]] = "hearing"
    for s in steps:
        rename.setdefault(s["id"], s["id"])
    if len(set(rename.values())) != len(rename):
        raise ValueError(f"step id collision after renaming: {rename}")
    events = [e["name"] for e in cat["events"]]
    for need in ("submitted", "told_incomplete", "app_complete", "decision"):
        if need not in events:
            raise ValueError(f"event list must include {need}")
    p_steps = {}
    for s in steps:
        sid = rename[s["id"]]
        fee = s.get("fee_item")
        if sid in ("hearing", "correction") and fee:
            notes.append(f"dropped fee item {fee!r} on {sid} (conditional/repeated-step fees unsupported)")
            fee = None
        ev = [] if sid in ("prepare", "completeness_check", "correction") else ([s["event_at_end"]] if s.get("event_at_end") else [])
        if sid == "decision_issue":
            ev = ["decision"]
        p_steps[sid] = {"d_steps": list(s.get("serves") or ["D2"]), "actor": s.get("actor", "agency"),
                        "days": bool(s.get("takes_elapsed_days", sid != "prepare")) and sid != "prepare",
                        "hours": bool(s.get("applicant_hours")) or sid == "prepare",
                        "fee": fee, "applicant_facing": s.get("actor") == "applicant" or bool(s.get("applicant_hours")),
                        "events": ev, "synonyms": s.get("synonyms", []), "builder_id": s["id"]}
    p_steps["completeness_check"]["days"] = True
    p_steps["correction"]["days"] = True
    p_steps["decision_issue"]["days"] = True
    order = [rename[s["id"]] for s in steps]
    day_steps = [s for s in order if p_steps[s]["days"]]
    hour_steps = [s for s in order if p_steps[s]["hours"]]
    fee_steps = {s: p_steps[s]["fee"] for s in order if p_steps[s]["fee"]}
    town_scaled = [s for s in order if p_steps[s]["days"] and p_steps[s]["actor"] in SCALED_ACTORS]
    listable = [rename[s["id"]] for s in steps if s.get("web_pages_list_it") and rename[s["id"]] not in ("prepare", "correction")]
    mentionable = [rename[s["id"]] for s in steps if s.get("applicants_mention_it") and rename[s["id"]] not in ("prepare", "completeness_check", "decision_issue")]
    if "correction" not in mentionable and any(s.get("applicants_mention_it") for s in steps if rename[s["id"]] == "correction"):
        mentionable.append("correction")
    mention_event = {}
    for m in mentionable:
        mention_event[m] = "told_incomplete" if m == "correction" else (p_steps[m]["events"][0] if p_steps[m]["events"] else None)
    timeable = ["submitted"] + [e for e in events if e in set(mention_event.values()) - {None}] + ["decision"]
    timeable = list(dict.fromkeys(timeable))
    milestone_events = sorted({e for cols in cat.get("admin_columns", {}).values() for e in cols.values()
                               if e not in ("case_id", "submitted", "decision")})
    admin_milestones = {e: e for e in milestone_events if e in events}
    design_space, design_text = {}, {}
    for d in cat["designs"]:
        mids = []
        for raw in d["middle_steps"]:
            base = raw.rstrip("?")
            sid = rename.get(base)
            if sid is None:
                raise ValueError(f"design {d['id']} uses unknown step {base}")
            mids.append(sid + ("?" if (raw.endswith("?") or sid == "hearing") else ""))
        if not mids and d.get("decision_at_last_step"):
            raise ValueError(f"design {d['id']}: decision at the last middle step needs a middle step")
        design_space[d["id"]] = {"d2": mids, "shared_decision": bool(d.get("decision_at_last_step"))}
        design_text[d["id"]] = d.get("why", "")
    pkg = {"statute_id": statute_id, "SYNTHETIC": True, "text": public_context["statute"],
           "deadline_days": 30, "d_steps": public_context["d_steps"], "p_steps": p_steps,
           "day_steps": day_steps, "hour_steps": hour_steps, "fee_steps": fee_steps,
           "town_scaled": town_scaled, "listable": listable, "mentionable": mentionable,
           "timeable_events": timeable, "vague_dstep": "D2", "decision_step": "decision_issue",
           "mention_event": mention_event, "admin_milestones": admin_milestones, "event_order": events,
           "design_space": design_space, "design_text": design_text,
           "compiler_notes": notes, "fee_items": cat.get("fee_items", {})}
    return pkg, rename


def admin_from_csv(cat: dict, csv_dir: Path) -> list[dict]:
    """Admin CSVs -> admin records, using only the builder's column map."""
    out = []
    for town, cols in cat.get("admin_columns", {}).items():
        f = Path(csv_dir) / f"admin_{town}.csv"
        with f.open() as fh:
            for row in csv.DictReader(fh):
                rec, ms = {"town": town}, {}
                for lab, ev in cols.items():
                    v = (row.get(lab) or "").strip()
                    if ev == "case_id":
                        rec["case_id"] = v
                    elif ev == "submitted":
                        rec["submitted"] = v
                    elif ev == "decision":
                        rec["decided"] = v
                    elif v:
                        ms[ev] = v
                if "submitted" not in rec or "decided" not in rec:
                    raise ValueError(f"{f}: builder map lacks submitted/decision columns")
                if ms or any(ev not in ("case_id", "submitted", "decision") for ev in cols.values()):
                    rec["milestones"] = ms
                out.append(rec)
    return out


def check_extraction(pkg: dict, reports: list, webpages: dict) -> list[str]:
    """One mechanical check: every field uses the package vocabulary. Returns problems (empty = pass)."""
    bad = []
    ment, ev, lst = set(pkg["mentionable"]), set(pkg["timeable_events"]), set(pkg["listable"])
    for r in reports:
        if r.get("status") == "pending":
            if not isinstance(r.get("days_since_submission"), int):
                bad.append(f"{r.get('report_id')}: pending without integer days")
            continue
        if set(r.get("mentions", {})) != ment:
            bad.append(f"{r.get('report_id')}: mention keys {sorted(r.get('mentions', {}))} != {sorted(ment)}")
        gaps = r.get("gaps", [])
        if not gaps or gaps[0]["from"] != "submitted" or gaps[-1]["to"] != "decision":
            bad.append(f"{r.get('report_id')}: gaps must run submitted -> ... -> decision")
        for g in gaps:
            if g["from"] not in ev or g["to"] not in ev or g.get("unit") not in ("day", "week", "month") or not isinstance(g.get("value"), int):
                bad.append(f"{r.get('report_id')}: bad gap {g}")
        for a, b in zip(gaps[:-1], gaps[1:]):
            if a["to"] != b["from"]:
                bad.append(f"{r.get('report_id')}: gaps not chained")
    for town, pg in webpages.items():
        if set(pg.get("listed_steps", {})) != lst:
            bad.append(f"web {town}: listed keys {sorted(pg.get('listed_steps', {}))} != {sorted(lst)}")
    return bad


def write_evidence(out: Path, pkg: dict, admin: list, reports: list, webpages: dict, towns: list, posting: dict, reporting: dict | None = None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "admin_records.json").write_text(json.dumps(admin, indent=1) + "\n")
    (out / "reports.json").write_text(json.dumps(reports, indent=1) + "\n")
    (out / "webpages.json").write_text(json.dumps(webpages, indent=1) + "\n")
    (out / "public_spec.json").write_text(json.dumps({
        "statute": pkg["text"], "d_steps": pkg["d_steps"], "p_steps": pkg["p_steps"],
        "structures": pkg["design_text"], "towns": towns, "notes": "blind-built catalogue",
        "observation_schema": "toy-process-v2", "fee_policy": "catalog-one-time-items-v2",
        "posting": posting, **({"reporting": reporting} if reporting else {})}, indent=1) + "\n")
