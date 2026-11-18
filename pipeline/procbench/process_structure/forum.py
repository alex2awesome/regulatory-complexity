"""Source-bound, root-adopted forum episodes for the occupancy contract.

Worker formats are not the contract. This adapter consumes a normalized review
with one whole checklist and one identity per episode. Unknown identity stays a
categorical variable; nondetection is never a truth anchor. A quote replay is a
mechanical check, not a substitute for the review of actor, scope and meaning.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re

from .identity import SCHEMA, _scope_overlap
from .occupancy import Evidence


def _bound_scope_refs(refs, source_root, label):
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{label} requires nonempty source-bound references")
    for ref in refs:
        if (not isinstance(ref, dict) or not isinstance(ref.get("path"), str)
                or not ref["path"] or not isinstance(ref.get("locator"), str)
                or not ref["locator"] or not isinstance(ref.get("sha256"), str)
                or len(ref["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in ref["sha256"])):
            raise ValueError(f"{label} references need path, SHA256 and reviewed locator")
        path = Path(source_root) / ref["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError(f"Changed {label} source")
    return copy.deepcopy(refs)


def quoted_reference(quote, source_root):
    """Replay a literal UTF-8 view or a bounded simple JSON-string quotation."""
    raw = (Path(source_root) / quote["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != quote["sha256"]:
        raise ValueError("Forum quote source hash changed")
    value = raw.decode("utf-8")
    location = quote.get("json_path")
    if location is not None:
        if not isinstance(location, str) or not location.startswith("$"):
            raise ValueError("Invalid reviewed JSON locator")
        value = json.loads(value)
        suffix = location[1:]
        while suffix:
            match = re.match(r"(?:\.([A-Za-z_][A-Za-z_0-9]*)|\[([0-9]+)\])", suffix)
            if match is None:
                raise ValueError("Unsupported JSON locator; do not silently search for the quote")
            value = value[match.group(1)] if match.group(1) else value[int(match.group(2))]
            suffix = suffix[match.end():]
    start, end, text = quote.get("char_start"), quote.get("char_end"), quote.get("quote")
    if (not isinstance(value, str) or type(start) is not int or type(end) is not int
            or not 0 <= start < end <= len(value) or not isinstance(text, str) or not text.strip()
            or value[start:end] != text):
        raise ValueError("Forum quotation does not replay at its exact reviewed offsets")
    return dict(path=quote["path"], sha256=quote["sha256"],
                locator=f"{location or 'captured_text'} chars [{start},{end})", quote=text)


def add_reviewed_episodes(base, packet, *, source_root, detection_beta=(2., 2.), false_positive=.02):
    """Add all adopted readings, including negative-only and uncertain units.

    The candidate universe is supplied explicitly. Candidate weights are
    sensitivity assumptions, not inferred from timing or other commenters.
    ``base`` and the worker packets remain unchanged.
    """
    if (packet.get("schema_version") != "reviewed-forum-occupancy-episodes/1"
            or packet.get("root_adopted") is not True
            or packet.get("dependence_reviewed") is not True
            or not isinstance(packet.get("dependence_qualification"), str)
            or not packet["dependence_qualification"].strip()):
        raise ValueError("Need an adopted, explicitly dependence-reviewed forum packet")
    data = copy.deepcopy(base)
    data["schema_version"] = SCHEMA
    county_ids = packet["jurisdictions"]
    if len(set(county_ids)) != len(county_ids) or not set(data["jurisdictions"]) <= set(county_ids):
        raise ValueError("Forum candidate universe must preserve every existing jurisdiction")
    data["jurisdictions"] = list(county_ids)
    kind = "forum_initial_episode"
    if kind in data["source_types"] or data.get("uncertain_jurisdiction_units"):
        raise ValueError("Add a normalized forum packet once, not incrementally duplicated")
    data["source_types"].append(kind)
    data["source_models"][kind] = dict(detection_beta=list(detection_beta), false_positive_probability=false_positive)
    data["uncertain_jurisdiction_units"] = []
    seen, seen_scopes = set(), {}
    for ep in packet["episodes"]:
        if (ep.get("root_adopted") is not True or ep.get("complete_capture_read") is not True
                or ep.get("actor_and_lifecycle_reviewed") is not True):
            raise ValueError("Every forum episode needs full-capture and actor/lifecycle adoption")
        uid = ep["episode_id"]
        if uid in seen:
            raise ValueError("Duplicate adopted episode")
        seen.add(uid)
        scope_kind = ep.get("reading_scope_kind", "complete_fixed_universe")
        reviewed_ids = ep.get("reviewed_step_ids")
        readings = ep.get("readings")
        if scope_kind == "complete_fixed_universe":
            if (reviewed_ids != data["steps"] or not isinstance(readings, list)
                    or len(readings) != len(data["steps"])
                    or {r.get("step_id") for r in readings} != set(data["steps"])):
                raise ValueError("Forum episode must review the whole fixed action checklist")
            subset = None
        elif scope_kind == "reviewed_fixed_subset":
            if (not isinstance(reviewed_ids, list) or not reviewed_ids
                    or any(not isinstance(step, str) or not step for step in reviewed_ids)
                    or len(set(reviewed_ids)) != len(reviewed_ids)
                    or not set(reviewed_ids) <= set(data["steps"])
                    or not isinstance(readings, list) or len(readings) != len(reviewed_ids)
                    or {r.get("step_id") for r in readings} != set(reviewed_ids)
                    or ep.get("step_scope_reviewed") is not True
                    or not isinstance(ep.get("step_scope_rationale"), str)
                    or not ep["step_scope_rationale"].strip()):
                raise ValueError("Reviewed fixed subset needs exact distinct step rows and reviewed scope metadata")
            subset = dict(
                reading_scope_kind=scope_kind,
                reviewed_step_ids=list(reviewed_ids),
                step_scope_reviewed=True,
                step_scope_rationale=ep["step_scope_rationale"],
                step_scope_refs=_bound_scope_refs(
                    ep.get("step_scope_refs"), source_root, "forum step scope"),
            )
        else:
            raise ValueError("Unknown forum reading_scope_kind")
        scope_refs = _bound_scope_refs(
            ep.get("identity_scope_refs"), source_root, "complete forum reading")
        scope_id = ep["identity_scope_id"]
        if (scope_id in seen_scopes or any(_scope_overlap(ref, old) for ref in scope_refs
                                          for refs in seen_scopes.values() for old in refs)):
            raise ValueError("Duplicate or overlapping canonical forum episode identity scope")
        seen_scopes[scope_id] = scope_refs
        rows = []
        for reading in readings:
            if type(reading.get("detected")) is not bool or reading["detected"] != bool(reading["quotes"]):
                raise ValueError("Explicit positives need quotes; nondetections cannot hide positive quotes")
            refs = [quoted_reference(q, source_root) for q in reading["quotes"]]
            rows.append(dict(step_id=reading["step_id"], detected=reading["detected"],
                             reviewed_scope=True, evidence_refs=refs + copy.deepcopy(scope_refs)))
        common = dict(unit_id=uid, dependence_group_id=ep["dependence_group_id"], source_type=kind,
                      identity_scope_id=ep["identity_scope_id"], identity_scope_reviewed=True,
                      identity_scope_refs=copy.deepcopy(scope_refs))
        if ep.get("jurisdiction_id") is not None:
            if ep["jurisdiction_id"] not in county_ids or not ep.get("county_quotes"):
                raise ValueError("Resolved county needs explicit reviewed applicant/representative evidence")
            county_refs = [quoted_reference(q, source_root) for q in ep["county_quotes"]]
            for row in rows:
                row.update(common, jurisdiction_id=ep["jurisdiction_id"],
                           lineage_reviewed=True, lineage_refs=copy.deepcopy(scope_refs),
                           identity_evidence_refs=county_refs)
                # County evidence is part of the byte closure too.
                row["evidence_refs"].extend(county_refs)
                if subset:
                    row.update(copy.deepcopy(subset))
                    # Resolved observations have no enclosing identity unit to
                    # bind these bytes, so retain the explicit metadata and add
                    # its refs to the ordinary evidence closure as well.
                    row["evidence_refs"].extend(copy.deepcopy(subset["step_scope_refs"]))
                row["evidence_refs"] = list({(r["path"], r["sha256"], r["locator"]): r
                                             for r in row["evidence_refs"]}.values())
            data["observations"].extend(rows)
        else:
            prior_refs = [quoted_reference(q, source_root) for q in ep["identity_context_quotes"]]
            mixture = ep.get("unresolved_identity_mixture")
            if mixture is not None:
                if (not isinstance(mixture, dict)
                        or mixture.get("independence_declaration") != "source_independent_of_episode_action_and_timing"
                        or not isinstance(mixture.get("assumption_label"), str)
                        or not mixture["assumption_label"].strip()):
                    raise ValueError("Invalid unresolved identity mixture metadata")
                prior_refs.extend(_bound_scope_refs(
                    mixture.get("source_refs"), source_root, "unresolved identity fallback"))
            unit = dict(
                **common, identity_reviewed=True, candidate_scope_complete=True,
                assignment_prior_basis=ep["assignment_prior_basis"],
                assignment_prior_kind=ep["assignment_prior_kind"], assignment_prior_refs=prior_refs,
                candidates=copy.deepcopy(ep["candidates"]), readings=rows,
                reviewed_step_ids=list(reviewed_ids))
            if mixture is not None:
                unit["unresolved_identity_mixture"] = copy.deepcopy(mixture)
            if subset:
                unit.update(copy.deepcopy(subset))
            data["uncertain_jurisdiction_units"].append(unit)
    data["assumption_note"] += (
        " Forum readings are complete captured narratives, not complete applicant journeys. "
        "Their effective detection probability combines step participation, observation before posting, "
        "and narration; these factors are not separately identified. Historical policy eras are pooled "
        "as a captured-source estimand, not a contemporary policy claim. " + packet["dependence_qualification"])
    data["forum_adoption"] = dict(packet_id=packet["packet_id"], episodes=len(seen),
                                  selected_thread_count=packet["selected_thread_count"],
                                  unresolved_identity_not_discarded=True)
    Evidence(data)
    return data
