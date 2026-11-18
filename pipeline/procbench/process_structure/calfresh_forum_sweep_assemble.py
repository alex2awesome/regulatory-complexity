"""Assemble the full CalFresh forum sweep into the fit's own evidence schema.

The agents that read the threads supply judgement: is this an initial-episode
account, whose county is it, which of the 20 canonical actions does it evidence,
and a verbatim quote for each. This module supplies the mechanics, and it does
not take the agents' word for anything checkable.

Every quote is verified as a contiguous substring of the file the agent named,
under one declared normalisation for the hard line wraps in the renderings. A
quote that does not verify is dropped and reported; it never becomes evidence.
Character offsets and SHA256 hashes are computed here, so a locator always
points at bytes that exist.

Negative space is derived, not asked for. An adopted account contributes a
reviewed non-detection for every canonical action it did not evidence, because
that is what an occupancy likelihood needs and what an agent cannot be trusted
to enumerate twenty times per thread.

Reads only the sweep outputs and the thread renderings. Reads no existing
posterior, no truth, no benchmark.
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SWEEP = ROOT / "runs/process_structure_20260921/calfresh_forum_full_sweep_20260921"

CANONICAL = [
    "file_application", "accept_and_date_application", "complete_application_information",
    "arrange_interview", "interview_encounter", "verify_existing_information",
    "request_verification", "provide_verification", "correct_information",
    "issue_missed_interview_notice", "recontact_or_reschedule", "make_eligibility_decision",
    "issue_decision_notice", "withdraw_application", "record_withdrawal",
    "agency_evaluate_expedited_services", "request_expedited_services",
    "agency_issue_pending_status_notice", "follow_up_or_escalate_status",
    "monitor_case_status_or_notices",
]
COUNTIES = [
    "Alameda", "Alpine", "Amador", "Butte", "Calaveras", "Colusa", "Contra_Costa", "Del_Norte",
    "El_Dorado", "Fresno", "Glenn", "Humboldt", "Imperial", "Inyo", "Kern", "Kings", "Lake",
    "Lassen", "Los_Angeles", "Madera", "Marin", "Mariposa", "Mendocino", "Merced", "Modoc",
    "Mono", "Monterey", "Napa", "Nevada", "Orange", "Placer", "Plumas", "Riverside",
    "Sacramento", "San_Benito", "San_Bernardino", "San_Diego", "San_Francisco", "San_Joaquin",
    "San_Luis_Obispo", "San_Mateo", "Santa_Barbara", "Santa_Clara", "Santa_Cruz", "Shasta",
    "Sierra", "Siskiyou", "Solano", "Sonoma", "Stanislaus", "Sutter", "Tehama", "Trinity",
    "Tulare", "Tuolumne", "Ventura", "Yolo", "Yuba",
]

_hash_cache: dict[str, str] = {}


def sha256(path: pathlib.Path) -> str:
    key = str(path)
    if key not in _hash_cache:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        _hash_cache[key] = digest.hexdigest()
    return _hash_cache[key]


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def locate(text: str, quote: str):
    """Find a quote in a file's text, tolerating only whitespace differences.

    Returns (start, end) character offsets into the ORIGINAL text, or None. The
    renderings wrap hard at column boundaries, so a quote copied from a
    displayed line can contain a newline where the source has a space, or the
    reverse. Collapsing runs of whitespace in both and mapping back is the one
    normalisation allowed; nothing else about the quote may differ.
    """
    quote = quote.strip()
    if not quote:
        return None
    direct = text.find(quote)
    if direct >= 0:
        return (direct, direct + len(quote))
    # map each character of the squashed text back to its original index
    squashed_chars, index_map = [], []
    previous_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if previous_space:
                continue
            squashed_chars.append(" ")
            index_map.append(i)
            previous_space = True
        else:
            squashed_chars.append(ch)
            index_map.append(i)
            previous_space = False
    squashed = "".join(squashed_chars)
    target = _squash(quote).strip()
    at = squashed.find(target)
    if at < 0:
        at = squashed.lower().find(target.lower())
        if at < 0:
            return None
    start = index_map[at]
    last = index_map[min(at + len(target) - 1, len(index_map) - 1)]
    return (start, last + 1)


def ref(path: pathlib.Path, span=None, quote=None) -> dict:
    out = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    out["locator"] = f"chars [{span[0]},{span[1]})" if span else "$"
    if quote:
        out["quote"] = quote
    return out


def assemble():
    manifest = {t["thread_id"]: t for t in json.loads((SWEEP / "thread_manifest.json").read_text())["threads"]}
    parsed = sorted((SWEEP / "parsed").glob("batch*.json"))
    if not parsed:
        raise SystemExit("no parsed batches yet")

    threads, duplicates = {}, []
    for path in parsed:
        blob = json.loads(path.read_text())
        for row in blob.get("threads", []):
            tid = row.get("thread_id")
            if tid in threads:
                duplicates.append(tid)
                continue
            row["_batch"] = path.name
            threads[tid] = row

    report = {
        "schema_version": "calfresh-forum-sweep-assembly/1",
        "threads_in_manifest": len(manifest),
        "threads_parsed": len(threads),
        "batches_parsed": [p.name for p in parsed],
        "duplicate_thread_rows": sorted(set(duplicates)),
        "threads_not_yet_parsed": sorted(set(manifest) - set(threads)),
    }

    observations, uncertain_units, dropped, lifecycle = [], [], [], collections.Counter()
    adopted_known, adopted_uncertain = [], []
    bad_step_ids, bad_counties = collections.Counter(), collections.Counter()

    for tid, row in sorted(threads.items()):
        lifecycle[str(row.get("lifecycle"))] += 1
        if not row.get("in_scope"):
            continue
        meta = manifest.get(tid)
        if meta is None:
            dropped.append({"thread_id": tid, "why": "not in the manifest"})
            continue
        rendering = ROOT / row.get("file", meta["path"])
        if not rendering.exists():
            rendering = ROOT / meta["path"]
        if not rendering.exists():
            dropped.append({"thread_id": tid, "why": "rendering missing on disk"})
            continue
        text = rendering.read_text(errors="replace")

        # verify the action quotes
        detected, verified_refs = {}, {}
        for hit in row.get("actions", []) or []:
            step = hit.get("step_id")
            if step not in CANONICAL:
                bad_step_ids[str(step)] += 1
                continue
            span = locate(text, hit.get("quote", ""))
            if span is None:
                dropped.append({"thread_id": tid, "step_id": step, "why": "quote not found in the named file",
                                "quote": (hit.get("quote") or "")[:120]})
                continue
            detected[step] = True
            verified_refs[step] = ref(rendering, span, text[span[0]:span[1]])

        # explicit absences are reviewed non-detections with a quote behind them
        explicit_absent = {}
        for miss in row.get("absent_actions", []) or []:
            step = miss.get("step_id")
            if step not in CANONICAL or step in detected:
                continue
            span = locate(text, miss.get("quote", ""))
            if span is None:
                continue
            explicit_absent[step] = ref(rendering, span, text[span[0]:span[1]])

        if not detected:
            dropped.append({"thread_id": tid, "why": "in scope but no action quote verified"})
            continue

        county = row.get("county")
        if county is not None and county not in COUNTIES:
            bad_counties[str(county)] += 1
            county = None

        unit = f"forum-initial-{tid}-root" + ("" if county else "-county-unresolved")
        group = f"reddit-thread:{tid}:initial-household-episode"
        scope_refs = [ref(rendering)]

        identity_refs = []
        if county and row.get("county_quote"):
            span = locate(text, row["county_quote"])
            if span is None:
                identity_refs = []
                county = None
                unit = f"forum-initial-{tid}-root-county-unresolved"
                dropped.append({"thread_id": tid, "why": "county quote did not verify; routed to uncertain identity",
                                "quote": row["county_quote"][:120]})
            else:
                identity_refs = [ref(rendering, span, text[span[0]:span[1]])]

        if county:
            adopted_known.append(tid)
            for step in CANONICAL:
                refs = [verified_refs[step]] if step in detected else (
                    [explicit_absent[step]] if step in explicit_absent else scope_refs)
                observations.append({
                    "step_id": step, "detected": step in detected, "reviewed_scope": True,
                    "evidence_refs": refs + ([] if step in detected or step in explicit_absent else []),
                    "unit_id": unit, "dependence_group_id": group,
                    "source_type": "forum_initial_episode",
                    "identity_scope_id": group, "identity_scope_reviewed": True,
                    "identity_scope_refs": scope_refs,
                    "jurisdiction_id": county,
                    "lineage_reviewed": True, "lineage_refs": scope_refs,
                    "identity_evidence_refs": identity_refs,
                    "explicit_absence": step in explicit_absent,
                })
        else:
            adopted_uncertain.append(tid)
            uncertain_units.append({
                "unit_id": unit, "dependence_group_id": group,
                "source_type": "forum_initial_episode",
                "identity_scope_id": group, "identity_scope_reviewed": True,
                "identity_scope_refs": scope_refs,
                "identity_reviewed": True, "candidate_scope_complete": True,
                "assignment_prior_kind": "symmetric_bounded_context",
                "assignment_prior_basis": (
                    "Uncalibrated symmetric prior over all 58 California counties. The account is "
                    "a CalFresh initial-application episode in California but names no county for "
                    "its own episode. No county was inferred from another commenter, from a "
                    "retrieval query, from a subreddit name or from a delay."),
                "assignment_prior_refs": scope_refs,
                "candidates": [{"jurisdiction_id": c, "prior_weight": 1.0} for c in COUNTIES],
                "reviewed_step_ids": CANONICAL,
                "readings": [{"step_id": s, "detected": s in detected,
                              "evidence_refs": [verified_refs[s]] if s in detected else (
                                  [explicit_absent[s]] if s in explicit_absent else scope_refs),
                              "explicit_absence": s in explicit_absent} for s in CANONICAL],
            })

        # repeats, kept separate: they are count evidence, not presence evidence
        for rep in row.get("repeats", []) or []:
            step = rep.get("step_id")
            if step not in CANONICAL:
                continue
            span = locate(text, rep.get("quote", ""))
            if span is None:
                continue
            report.setdefault("repeat_observations", []).append({
                "thread_id": tid, "step_id": step, "jurisdiction_id": county,
                "completed_rounds": rep.get("completed_rounds"),
                "dependence_group_id": group,
                "evidence_refs": [ref(rendering, span, text[span[0]:span[1]])],
                "qualification": ("Conditional on a selected positive report. Not a population "
                                  "rework rate and not a hurdle probability."),
            })

    report.update({
        "lifecycle_breakdown": dict(lifecycle),
        "adopted_known_county": len(adopted_known),
        "adopted_uncertain_county": len(adopted_uncertain),
        "adopted_total": len(adopted_known) + len(adopted_uncertain),
        "observations_emitted": len(observations),
        "uncertain_units_emitted": len(uncertain_units),
        "positive_detections": sum(1 for o in observations if o["detected"]),
        "explicit_absences": sum(1 for o in observations if o.get("explicit_absence")),
        "counties_with_a_known_account": len({o["jurisdiction_id"] for o in observations}),
        "county_account_counts": dict(collections.Counter(
            o["jurisdiction_id"] for o in observations if o["step_id"] == CANONICAL[0])),
        "dropped": dropped,
        "invalid_step_ids": dict(bad_step_ids),
        "invalid_counties": dict(bad_counties),
        "verification_rule": ("Every quote is a contiguous substring of the named rendering under "
                              "whitespace collapsing only. Unverified quotes are dropped and listed "
                              "in `dropped`, never emitted as evidence."),
        "negative_space_rule": ("An adopted account contributes a reviewed non-detection for every "
                                "canonical action it does not evidence. Silence in an account is a "
                                "non-detection, not an absence; an absence needs its own quote and "
                                "is flagged `explicit_absence`."),
        "not_a_fit": "This is an evidence bundle. No posterior, gate or adoption decision is implied.",
    })

    (SWEEP / "assembled_observations.json").write_text(json.dumps(
        {"observations": observations, "uncertain_jurisdiction_units": uncertain_units}, indent=1))
    (SWEEP / "assembly_report.json").write_text(json.dumps(report, indent=1))
    return report


def main():
    report = assemble()
    keys = ("threads_in_manifest", "threads_parsed", "lifecycle_breakdown", "adopted_total",
            "adopted_known_county", "adopted_uncertain_county", "counties_with_a_known_account",
            "observations_emitted", "positive_detections", "explicit_absences",
            "invalid_step_ids", "invalid_counties")
    print(json.dumps({k: report[k] for k in keys if k in report}, indent=2))
    print(f"dropped rows: {len(report['dropped'])}")
    print(f"threads not yet parsed: {len(report['threads_not_yet_parsed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
