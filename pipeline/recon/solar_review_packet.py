#!/usr/bin/env python3
"""Assemble root-authored solar forum decisions into the occupancy packet.

This is deliberately mechanical: it does not infer actions or locations. Root
decisions are the semantic input; this script only resolves their source
comments, computes explicitly dated intervals, and emits the packet contract.
"""
from __future__ import annotations
import datetime as dt
import argparse
import csv
import hashlib
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "runs/solar_forum_20260922/parse/root_decisions001.json"
OUT = ROOT / "runs/solar_forum_20260922/parse/reviewed_root001.json"
POSTS = ROOT / "corpus/realworld/solar_permit/reddit/posts"
ACQ_POSTS = ROOT / "runs/solar_forum_20260922/acquisition/forum/posts"
ACQ_RESPONSES = ROOT / "runs/solar_forum_20260922/acquisition/forum/responses"
WRAPPERS = ROOT / "corpus/realworld/solar_permit/reddit"
PANEL = ROOT / "runs/solar_panel_20260920/panel_v1.csv"
STEPS = [
    "solar_permit__ahj_permit_application_submission",
    "solar_permit__ahj_completeness_determination",
    "solar_permit__ahj_plan_review",
    "solar_permit__ahj_structural_review",
    "solar_permit__ahj_electrical_review",
    "solar_permit__ahj_correction_resubmittal",
    "solar_permit__ahj_permit_issuance",
    "solar_permit__inspection_scheduling_request",
    "solar_permit__ahj_final_inspection",
    "solar_permit__ahj_reinspection",
    "solar_permit__ahj_final_approval",
]
ACTION_STEP = {
    "ahj_permit_application_submission": STEPS[0],
    "ahj_completeness_determination": STEPS[1],
    "ahj_plan_review": STEPS[2],
    "ahj_structural_review": STEPS[3],
    "ahj_electrical_review": STEPS[4],
    "ahj_correction_resubmittal": STEPS[5],
    "ahj_permit_issuance": STEPS[6],
    "inspection_scheduling_request": STEPS[7],
    "ahj_final_inspection": STEPS[8],
    "ahj_reinspection": STEPS[9],
    "ahj_final_approval": STEPS[10],
}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def walk(value: Any, path: str, source: pathlib.Path, out: dict[str, dict]) -> None:
    if isinstance(value, dict):
        cid = value.get("id")
        body = value.get("body")
        if cid and isinstance(body, str):
            out.setdefault(str(cid), {"path": source, "json_path": path + ".body", "text": body, "author": value.get("author")})
        for key, child in value.items():
            walk(child, f"{path}.{key}", source, out)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk(child, f"{path}[{i}]", source, out)


def load_sources() -> tuple[dict[str, dict], dict[str, dict]]:
    comments: dict[str, dict] = {}
    posts: dict[str, dict] = {}
    # Prefer the refreshed canonical capture and its authoritative root comments.
    # Older embedded trees can omit updates and must not win a setdefault race.
    for path in sorted(ACQ_POSTS.glob("*.json")):
        value = json.loads(path.read_bytes().decode("utf-8"))
        posts[path.stem] = {"path": path, "value": value["post"], "prefix": "$.post"}
        walk(value["comments"], "$.comments", path, comments)
    for path in sorted(POSTS.glob("*.json")):
        value = json.loads(path.read_bytes().decode("utf-8"))
        rid = path.stem
        posts.setdefault(rid, {"path": path, "value": value, "prefix": "$"})
        walk(value, "$", path, comments)
    for path in sorted(WRAPPERS.glob("thread_*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")), "$", path, comments)
    for filename in ("venue_expansion001_posts.json", "independent_forum_batch002_posts_successor.json",
                     "independent_forum_batch003_posts.json"):
        external = ROOT / "runs/solar_forum_20260922/acquisition" / filename
        if not external.exists():
            continue
        for i, row in enumerate(json.loads(external.read_bytes())["posts"]):
            ref = "external_" + pathlib.Path(row["source"]).stem + "_" + row["post_id"]
            record = dict(path=external, json_path=f"$.posts[{i}].body",
                text=row["body"], author=row["author"],
                underlying_artifact=dict(path=row["source"], sha256=row["source_sha256"]))
            comments[ref] = record
            if row.get("forum"):
                symbolic = "external:" + row["forum"] + ":" + row["post_id"]
                if symbolic in comments and comments[symbolic]["text"] != record["text"]:
                    raise ValueError("Conflicting independent-forum post copies: " + symbolic)
                comments[symbolic] = record
    # The 2026-09-22 SolarPanelTalk capture uses a normalized partition schema
    # (source_path/body rather than source/body).  Register exact stable
    # locators so staged external timing packets can be replayed by the same
    # resolver without adding a second source-loading convention.
    partitioned = ROOT / "runs/solar_forum_20260922/acquisition/external_leads002_posts.json"
    if partitioned.exists():
        rows = json.loads(partitioned.read_bytes().decode("utf-8"))["posts"]
        for i, row in enumerate(rows):
            match = re.search(r"spt_(\d+)", row["source_path"])
            if not match:
                raise ValueError("Unrecognized SolarPanelTalk source path: " + row["source_path"])
            ref = f"external_solarpaneltalk_{match.group(1)}_{row['post_id']}"
            record = dict(path=partitioned, json_path=f"$.posts[{i}].body",
                          text=row["body"], author=row["author"],
                          underlying_artifact=dict(path=row["source_path"],
                                                   sha256=row["source_sha256"]))
            comments[ref] = record
            symbolic = "external:SolarPanelTalk:" + row["post_id"]
            comments[symbolic] = record
    # Own-author text is partitioned separately from quoted earlier posts.
    # Keep both the normalized string locator and its original HTML binding.
    partitioned003 = ROOT / "runs/solar_forum_20260922/acquisition/external_leads003/posts.json"
    if partitioned003.exists():
        for i, row in enumerate(json.loads(partitioned003.read_bytes())["posts"]):
            ref = "external003:" + str(row["post_id"])
            record = dict(path=partitioned003, json_path=f"$.posts[{i}].own_body",
                          text=row["own_body"], author=row["author"],
                          underlying_artifact=dict(path=row["source_path"],
                                                   sha256=row["source_sha256"]))
            if ref in comments and comments[ref]["text"] != record["text"]:
                raise ValueError("Conflicting external003 post identity: " + ref)
            comments[ref] = record
    partitioned004 = ROOT / "runs/solar_forum_20260922/parse/external_decisions004_luna.json"
    if partitioned004.exists():
        for i, row in enumerate(json.loads(partitioned004.read_bytes())["posts"]):
            ref = "external004:" + row["thread_id"] + ":" + str(row["post_id"])
            record = dict(path=partitioned004, json_path=f"$.posts[{i}].body_text",
                          text=row["body_text"], author=row["author"],
                          underlying_artifact=dict(path=row["source_path"],
                                                   sha256=row["source_sha256"]))
            if ref in comments and comments[ref]["text"] != record["text"]:
                raise ValueError("Conflicting external004 post identity: " + ref)
            comments[ref] = record
    # Later public post edits are explicit versioned evidence. Do not overwrite
    # an older archive or let a new revision silently change an already-bound ref.
    revisions = ROOT / "runs/solar_forum_20260922/acquisition/forum/post_revisions"
    for path in sorted(revisions.glob("*.json")):
        row = json.loads(path.read_bytes())
        if row.get("schema_version") != "solar-explicit-post-revision/1":
            raise ValueError("Unrecognized explicit post revision: " + str(path))
        ref = row["ref"]
        if not ref.startswith("revision:") or ref in comments:
            raise ValueError("Conflicting explicit source revision: " + ref)
        comments[ref] = dict(path=path, json_path="$.body", text=row["body"],
                             author=row["author"])
    return comments, posts


def quote_ref(item: dict, *, full: bool = True) -> dict:
    text = item["text"]
    result = {
        "path": str(item["path"].relative_to(ROOT)),
        "sha256": sha(item["path"]),
        "json_path": item["json_path"],
        "char_start": 0,
        "char_end": len(text),
        "quote": text,
        "quote_replay": "UTF-8 decoded JSON string field; exact [char_start:char_end] replay",
    }
    if "underlying_artifact" in item:
        result["underlying_artifact"] = item["underlying_artifact"]
    return result


def resolve_ref(thread: str, ref: str, comments: dict, posts: dict) -> dict:
    if ref.endswith("__post"):
        # Explicitly linked multithread journeys can cite another held OP.
        # This is a source locator, not an automatic same-author case merge.
        return resolve_ref(ref[:-6], "post", comments, posts)
    if ref.startswith("post:"):
        field=ref.partition(":")[2]
        if field not in {"title", "selftext", "author_flair_text", "link_flair_text", "subreddit"}:
            raise ValueError("Unsupported explicit post text field: " + field)
        source=posts[thread]
        value=source["value"].get(field)
        if not isinstance(value,str) or not value:
            raise ValueError("Explicit post text field is missing: " + thread + ":" + field)
        return {"path":source["path"], "json_path":f"{source['prefix']}.{field}",
                "text":value, "author":source["value"].get("author")}
    if ref == "post":
        if thread not in posts:
            raise RuntimeError(f"missing post for thread={thread}")
        value = posts[thread]["value"]
        text = value.get("selftext") or value.get("title") or ""
        field = "selftext" if value.get("selftext") else "title"
        if not text:
            raise RuntimeError(f"post has no title/selftext: {thread}")
        return {"path": posts[thread]["path"], "json_path": f"{posts[thread]['prefix']}.{field}", "text": text, "author": value.get("author")}
    if ref not in comments:
        raise RuntimeError(f"missing comment id={ref} in thread={thread}")
    return comments[ref]


def dated_timing(t: dict) -> dict:
    out = dict(t)
    if out.get("start_date") and out.get("end_date"):
        start = dt.date.fromisoformat(out["start_date"])
        end = dt.date.fromisoformat(out["end_date"])
        out["calendar_days_elapsed"] = (end - start).days
        out["date_difference_semantics"] = "calendar-day subtraction; source wording retained"
    return out


def decision_case_id(source: dict) -> str:
    key = source["thread"] + "__" + source["author"]
    if source.get("installation_key"):
        key += "__" + source["installation_key"]
    return key


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decisions", type=pathlib.Path, default=DECISIONS)
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    args = ap.parse_args()
    decision_path, output_path = args.decisions.resolve(), args.out.resolve()
    decisions = json.loads(decision_path.read_text(encoding="utf-8"))
    adoption_state = decisions.get("adoption_state", "adopted")
    adopted = adoption_state == "adopted"
    comments, posts = load_sources()
    base_path = ROOT / "runs/process_structure_20260921/solar_phase1/occupancy_evidence.json"
    all_ahj = json.loads(base_path.read_bytes())["jurisdictions"]
    ahj = set(all_ahj)
    county_ahj = {}
    with PANEL.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["owner_kind"] == "ahj" and slug(row["owner_name"]) in ahj:
                county_ahj.setdefault(row["county"], set()).add(slug(row["owner_name"]))
    utility_terms = {
        "PGE": "Pacific Gas & Electric Co. (PG&E)",
        "SCE": "Southern California Edison Co (SCE)",
        "SDGE": "San Diego Gas & Electric Co (SDGE)",
    }
    episodes = []
    descriptive = list(decisions.get("descriptive_episodes", []))
    for n, source in enumerate(decisions["episodes"], 1):
        if (source.get("inference_scope", "").startswith("descriptive_only") or
                source.get("observation_role", "").startswith("descriptive_") or
                source.get("lifecycle_stage") == "considering_only"):
            descriptive.append({**source, "route": "retained_without_occupancy_likelihood",
                "routing_basis": "Explicit semantic scope/lifecycle label; not a geographic keyword exclusion or an observed absence."})
            continue
        thread, author = source["thread"], source["author"]
        refs = []
        for ref_list in source.get("actions", {}).values():
            refs.extend(ref_list)
        for timing in source.get("timing", []):
            refs.extend(timing.get("refs", []))
        for field in ("qualitative_timing", "non_registry_actions", "cost_claims", "effort_claims"):
            for item in source.get(field, []):
                refs.extend(item.get("refs", []))
        refs.extend(source.get("context", []))
        refs = list(dict.fromkeys(refs))
        resolved = {ref: resolve_ref(thread, ref, comments, posts) for ref in refs}
        identity = f"reddit:{thread}:{author}"
        if source.get("installation_key"):
            identity += ":" + source["installation_key"]
        utility = source.get("utility")
        named = [slug(x) for x in source.get("ahj_names", [])]
        exact = [x for x in named if x in ahj]
        regional = sorted(set().union(*(county_ahj.get(c, set()) for c in source.get("candidate_counties", []))))
        if source.get("candidate_counties") and not regional:
            raise ValueError("County clues do not match the panel: " + str(source["candidate_counties"]))
        if exact:
            candidates = [{"jurisdiction_id": x, "prior_weight": 1.0 / len(exact)} for x in exact]
            prior_kind = "reviewed_candidate_weights"
            prior_basis = "Exact root-authored AHJ name mapped through solar_sources.slug; no semantic remapping."
        elif regional:
            candidates = [{"jurisdiction_id": x, "prior_weight": 1.0 / len(regional)} for x in regional]
            prior_kind = "reviewed_candidate_weights"
            prior_basis = "Reviewed county/region context; uniform within panel AHJs in " + ", ".join(source["candidate_counties"]) + ". This is an assumed geographic prior, not a learned identity."
        else:
            candidates = [{"jurisdiction_id": x, "prior_weight": 1.0 / len(all_ahj)} for x in all_ahj]
            prior_kind = "reviewed_candidate_weights"
            prior_basis = "Root decision has no exact panel AHJ slug; complete 440-AHJ frame, conditional on California context."
        readings = []
        for step in STEPS:
            refs_for = []
            for action, action_refs in source.get("actions", {}).items():
                if ACTION_STEP.get(action) == step:
                    refs_for.extend(action_refs)
            readings.append({"step_id": step, "detected": bool(refs_for), "quotes": [quote_ref(resolved[r]) for r in dict.fromkeys(refs_for)]})
        quote_context = [{**quote_ref(resolved[r]), "source_ref": r} for r in source.get("context", [])]
        retained = {field: [{**item, "evidence": [quote_ref(resolved[r]) for r in item.get("refs", [])]}
                            for item in source.get(field, [])]
                    for field in ("qualitative_timing", "non_registry_actions", "cost_claims", "effort_claims")}
        retained["unmapped_action_labels"] = [
            {"action": action, "route": "retained_outside_fixed_action_universe",
             "evidence": [quote_ref(resolved[r]) for r in action_refs]}
            for action, action_refs in source.get("actions", {}).items() if action not in ACTION_STEP]
        locator = f"$case[{author!r}]"
        if source.get("installation_key"):
            locator += f"[{source['installation_key']!r}]"
        episodes.append({
            "episode_id": f"{source.get('source_namespace', 'reddit')}_{thread}__{slug(author)}__installation_{source.get('installation_key', n)}",
            "dependence_group_id": identity,
            "identity_scope_id": identity,
            "identity_scope_refs": [{"path": str(resolved[refs[0]]["path"].relative_to(ROOT)), "sha256": sha(resolved[refs[0]]["path"]), "locator": locator}] if refs else [],
            "root_adopted": adopted, "complete_capture_read": True, "actor_and_lifecycle_reviewed": True, "occurrence_reviewed": True,
            "statistic": "individual", "reading_scope_kind": "complete_fixed_universe", "reviewed_step_ids": STEPS,
            "jurisdiction_id": exact[0] if len(exact) == 1 else None, "assignment_prior_kind": prior_kind, "assignment_prior_basis": prior_basis,
            "identity_context_quotes": quote_context, "county_quotes": quote_context if exact else [], "candidates": candidates, "readings": readings,
            "review_metadata": {"thread_id": thread, "author": author, "installation_key": source.get("installation_key"), "observation_role": source.get("observation_role", "firsthand_applicant"), "source_comment_ids": refs, "california_basis": source.get("location") or source.get("inherited_context") or "root decision context", "utility": utility_terms.get(utility, utility), "timing": [dated_timing(t) for t in source.get("timing", [])], **retained, "note": source.get("note", "")}
        })
    packet = {"schema_version": "reviewed-forum-occupancy-episodes/1", "packet_id": decisions.get("packet_id", "solar_forum_root_adopted_001"), "root_adopted": adopted, "dependence_reviewed": adopted and "pending_cross_batch_case_linkage" not in adoption_state, "dependence_qualification": "One unit per root-authored author-installation episode; all linked comments share one identity scope. Staged packets do not assert completed dependence review. Cross-packet links must be applied before joint fitting.", "selected_thread_count": len(decisions["threads"]), "threads": decisions["threads"], "adoption_state": adoption_state, "jurisdictions": all_ahj, "episodes": episodes}
    from pipeline.procbench.process_structure.forum import quoted_reference
    for ep in episodes:
        # Preserve semantic fields outside this fixed likelihood contract too.
        # Costs, roles or lifecycle context must not disappear through schema drift.
        ep["review_metadata"]["semantic_decision"] = next(
            source for source in decisions["episodes"]
            if source["thread"] == ep["review_metadata"]["thread_id"] and
            source["author"] == ep["review_metadata"]["author"] and
            source.get("installation_key") == ep["review_metadata"].get("installation_key"))
        for q in ep["identity_context_quotes"] + [q for r in ep["readings"] for q in r["quotes"]]:
            quoted_reference(q, ROOT)
    packet["decision_source"] = {"path": str(decision_path.relative_to(ROOT)), "sha256": sha(decision_path)}
    packet["capture_limits"] = decisions.get("capture_limits", {})
    packet["descriptive_episodes"] = descriptive
    packet["other_dispositions"] = decisions.get("other_dispositions", [])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"episodes": len(episodes), "ahj_frame": len(all_ahj), "comments_indexed": len(comments), "output": str(output_path)}))


if __name__ == "__main__":
    main()
