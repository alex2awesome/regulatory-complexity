"""Freeze and route completed Solar reading packets without changing the originals.

This is an adapter, not another parser or model. Every extracted field gets an
explicit route. Only observed elapsed reports enter the existing duration model;
missing county is never a duration exclusion. Ambiguous labels remain visible.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
BULK = ROOT / "runs/solar_forum_20260922/parse/claude_bulk"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def within_packet_case_links(episodes):
    """Resolve explicit same-installation declarations, including cycles.

    Username matches and candidate/uncertain links are never inferred as merges.
    The stable representative is only an ID, not the preferred evidence row.
    """
    ids = [ep['decision_case_id'] for ep in episodes]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate decision_case_id in packet')
    parent = {ident: ident for ident in ids}
    def find(ident):
        while parent[ident] != ident:
            parent[ident] = parent[parent[ident]]
            ident = parent[ident]
        return ident
    for ep in episodes:
        alias = ep.get('same_installation_as')
        alias = alias[0] if isinstance(alias, list) and len(alias) == 1 else alias
        if not isinstance(alias, str) or alias not in parent:
            continue
        left, right = find(ep['decision_case_id']), find(alias)
        parent[max(left, right)] = min(left, right)
    return {ident: find(ident) for ident in ids}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def freeze(index_path, out):
    if out.exists():
        raise FileExistsError(out)
    index = json.loads(index_path.read_bytes())
    packets, changed = [], []
    for item in index["packets"]:
        packet = {"packet_id": item["packet_id"], "files": {}, "input_hashes": {}}
        names = ["reservation", "decisions", "coverage", "manifest"]
        # Preserve the reader's geography sidecar when it was bound by the
        # receipt index. Never import an unbound newer sidecar into an old freeze.
        timing_relative = item["packet_dir"] + "/timing_staged.json"
        if timing_relative in item["input_files_sha256"]:
            names.append("timing_staged")
        for name in names:
            relative = item["packet_dir"] + "/" + name + ".json"
            raw = (ROOT / relative).read_bytes()
            actual = digest(raw)
            expected = item["input_files_sha256"][relative]
            if actual != expected:
                changed.append({"packet_id": item["packet_id"], "file": relative,
                                "expected": expected, "actual": actual})
            packet["files"][name] = json.loads(raw)
            packet["input_hashes"][relative] = actual
        if not any(x["packet_id"] == item["packet_id"] for x in changed):
            packets.append(packet)
    cw_path = BULK / "censoring_crosswalk.json"
    record = {"schema_version": "solar-bulk-frozen-input/1",
              "frozen_index": str(index_path.relative_to(ROOT)),
              "frozen_index_sha256": digest(index_path.read_bytes()),
              "packets": packets, "changed_since_check_excluded": changed,
              "censoring_crosswalk": json.loads(cw_path.read_bytes()),
              "censoring_crosswalk_sha256": digest(cw_path.read_bytes())}
    write(out, record)
    print(json.dumps({"frozen_packets": len(packets), "changed_packets": changed,
                      "out": str(out)}, indent=2))


STATUSES = {"completed_observed", "range_reported", "single_milestone_no_duration",
            "pending_lower_bound", "upper_bound_only", "future_scheduled_not_observed",
            "forecast_not_observation", "policy_deadline_not_observation"}


def classify_status(timing, crosswalk):
    raw = str(timing.get("censoring", ""))
    parts = raw.split("|")
    if parts[0] in STATUSES:
        return parts[0], parts[1] if len(parts) > 1 else "unspecified", "explicit_status"
    # Some completed reader packets use the conventional survival term with
    # the canonical pipe-delimited precision. Preserve its pending meaning;
    # do not infer completion from a numeric value or drop the precision.
    explicit_aliases = {"right_censored": "pending_lower_bound",
                        "completed_lower_bound": "completed_observed",
                        "completed_upper_bound": "upper_bound_only"}
    if parts[0] in explicit_aliases:
        return explicit_aliases[parts[0]], parts[1] if len(parts) > 1 else "unspecified", "explicit_" + parts[0] + "_alias"
    if raw in {"right", "right_bound_uncertain", "left", "left_interval", "interval",
               "completed_lower_bound"}:
        return {"right": "pending_lower_bound", "right_bound_uncertain": "pending_lower_bound",
                "left": "upper_bound_only", "left_interval": "upper_bound_only",
                "interval": "range_reported", "completed_lower_bound": "completed_observed"}[raw], "unspecified", "legacy_model_status"
    row = crosswalk.get(raw)
    if row and row["observation_status"] not in {"varies_by_entry", "unclassified", "genuinely_indeterminate"}:
        return row["observation_status"], row.get("precision", "unspecified"), "frozen_claude_crosswalk"
    # These are precision-only labels, not projected or professional summaries.
    # Do not infer observation status from the mere existence of a number.
    if raw in {"month_only_approximate", "year_only", "derived_from_two_dates_reader_computed"}:
        if timing.get("value") is not None:
            status = "completed_observed"
        elif timing.get("lower") is not None and timing.get("upper") is not None:
            status = "range_reported"
        elif timing.get("lower") is not None:
            return "unclassified", "unspecified", "lower_bound_completion_unknown"
        elif timing.get("upper") is not None:
            status = "upper_bound_only"
        else:
            status = "single_milestone_no_duration"
        return status, {"month_only_approximate": "month_only", "year_only": "year_only"}.get(raw, "unspecified"), "precision_only_field_shape"
    return "unclassified", "unspecified", "unmapped_censoring_label"


def duration_bounds(timing, status, precision):
    unit = timing.get("unit")
    factors = {"calendar_days": 1., "days": 1., "weeks": 7., "months": 365.25 / 12.,
               "years": 365.25, "business_days": 1.}
    if unit not in factors:
        return None, "unit_requires_elapsed_or_effort_clarification"
    numeric = {k: timing.get(k) for k in ("value", "lower", "upper")}
    if not any(v is not None for v in numeric.values()):
        return None, "milestone_without_numeric_duration"
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
           for v in numeric.values() if v is not None):
        return None, "invalid_numeric_duration"
    factor = factors[unit]
    value, lo, hi = (None if numeric[k] is None else numeric[k] * factor
                     for k in ("value", "lower", "upper"))
    target_unit = "business_days" if unit == "business_days" else "calendar_days"
    notes = ["Original reported values retained; verbal months=365.25/12 days and years=365.25 days."]
    if unit == "days":
        notes.append("Bare days interpreted as calendar days; no business-day conversion.")
    if (status in {"completed_observed", "range_reported"} and value is None
            and lo is not None and hi is not None and lo == hi):
        value, lo, hi = lo, None, None
        notes.append("Equal completed lower/upper bounds encode a point report; apply the same rounding rule as a value field.")
    if status == "pending_lower_bound":
        bound = lo if lo is not None else value
        if bound is None or bound <= 0:
            return None, "pending_without_positive_lower_bound"
        # An uncertain pending range gives a conservative lower bound, NOT a
        # completion interval. Precision affects the observed censoring bound.
        if lo is None:
            width = max(1., .15 * bound) if precision == "approximate" else 1.
            if precision == "month_only": width = max(width, 365.25 / 24.)
            if precision == "year_only": width = max(width, 365.25 / 2.)
            bound = max(.01, bound - width)
        return {"lower": bound, "upper": None, "observation_kind": "pending_right_censored",
                "time_unit": target_unit, "rounding_assumptions": notes}, None
    if status == "upper_bound_only":
        if hi is None:
            return None, "upper_bound_without_upper"
        lo = 0.
    elif lo is not None and hi is None and value is None:
        return {"lower": lo, "upper": None, "observation_kind": "completed_lower_bound",
                "time_unit": target_unit, "rounding_assumptions": notes}, None
    elif lo is not None and hi is not None:
        pass
    elif hi is not None and value is None:
        # A completed report such as "under a week" is a real upper bound,
        # even when the parser called it completed rather than upper_bound_only.
        lo = 0.
    elif value is not None:
        width = max(1., .15 * value) if precision == "approximate" or timing.get("approximate") else 1.
        if precision == "month_only": width = max(width, 365.25 / 24.)
        if precision == "year_only": width = max(width, 365.25 / 2.)
        lo, hi = max(0., value - width), value + width
        notes.append("Point reports use +/-1 day; approximate +/-max(1 day,15%); month/year precision at least half its stated unit.")
    else:
        return None, "incomplete_duration_bounds"
    if lo is None or hi is None or hi <= lo:
        return None, "invalid_or_degenerate_duration_interval"
    return {"lower": lo, "upper": hi, "observation_kind": "completed_interval",
            "time_unit": target_unit, "rounding_assumptions": notes}, None


def episode_geography(episode, staged_episode=None):
    """Preserve both supported reader layouts without guessing a location.

    Some packets keep geography beside the episode and others inside location.
    Top-level fields, when present, remain authoritative; disagreements are
    exposed, not silently merged or interpreted as evidence of absence.
    """
    nested = episode.get("location")
    nested = nested if isinstance(nested, dict) else {}
    staged = staged_episode if isinstance(staged_episode, dict) else {}
    result, sources, conflicts = {}, {}, []
    for key, default in (("county_weights", {}), ("unassigned_geography_mass", None)):
        if key in episode:
            result[key], sources[key] = episode[key], "episode"
            if key in nested and episode[key] != nested[key]:
                conflicts.append({"field": key, "episode": episode[key], "location": nested[key]})
        elif key in nested:
            result[key], sources[key] = nested[key], "location"
        else:
            result[key], sources[key] = default, "not_recorded"
        if key in staged:
            if sources[key] == "not_recorded":
                result[key], sources[key] = staged[key], "timing_staged"
            elif result[key] != staged[key]:
                conflicts.append({"field": key, "decisions": result[key], "timing_staged": staged[key]})
    result["geography_field_sources"] = sources
    result["geography_field_conflicts"] = conflicts
    return result


def geo_scope(episode, geography=None):
    scope = str(episode.get("inference_scope", "")).lower()
    # Preserve parser geography and candidate mass. These broad tags are only
    # for reporting; the first pooled model does not infer county capability.
    if episode.get("out_of_california") or re.search(r"out[_ -]of[_ -](california|state)|outside[_ -]california|non[_ -]california", scope):
        return "outside_california_reported"
    if "california" in scope and not re.search(r"(not|no)[_ -]california", scope):
        return "california_supported_by_parser"
    geography = episode_geography(episode) if geography is None else geography
    if geography["county_weights"] and not geography["geography_field_conflicts"]:
        return "county_candidates_provided"
    return "unresolved_or_other_scope"


def matching_staged_episode(episode, decisions, staged):
    """Exact within-packet geography link, never a cross-project author merge."""
    identity = episode.get('decision_case_id')
    candidates = [(i, row) for i, row in enumerate(staged)
                  if identity and row.get('decision_case_id') == identity]
    method = 'exact_decision_case_id'
    pair = (episode.get('thread'), episode.get('author'))
    if not candidates:
        # Older sidecars lack IDs. A pair is safe only when it is unique in both
        # files and no different explicit sidecar case ID contradicts the link.
        if not all(pair) or sum((row.get('thread'), row.get('author')) == pair for row in decisions) != 1:
            return None, dict(status='unresolved', reason='missing_or_nonunique_thread_author')
        candidates = [(i, row) for i, row in enumerate(staged)
                      if not row.get('decision_case_id') and (row.get('thread'), row.get('author')) == pair]
        method = 'unique_thread_author_without_sidecar_case_id'
    if len(candidates) != 1:
        return None, dict(status='unresolved', reason='missing_or_ambiguous_staged_episode')
    index, matched = candidates[0]
    if (matched.get('thread'), matched.get('author')) != pair:
        return None, dict(status='unresolved', reason='case_id_thread_author_conflict')
    return matched, dict(status='matched', method=method, json_path=f'$.episodes[{index}]')


def claim_content_sha256(claim):
    """Stable binding for an entry-level interpretation; not a semantic check."""
    return digest(json.dumps(claim, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode())


def resolve_clock_mapping(claim_id, claim, crosswalk):
    """A reviewed entry can disambiguate a label that varies across reports.

    Overrides never change the evidence, censoring, values or geography. Bind
    them to the complete claim so a reordered/edited ledger fails visibly.
    Absence of an override preserves the existing exact-label behavior.
    """
    override = crosswalk.get("claim_mappings", {}).get(claim_id)
    if override is None:
        return crosswalk.get("mappings", {}).get(claim.get("clock", ""), {})
    if override.get("claim_content_sha256") != claim_content_sha256(claim):
        raise ValueError(f"Stale entry-level clock mapping: {claim_id}")
    if override.get("raw_clock") != claim.get("clock"):
        raise ValueError(f"Entry-level raw clock mismatch: {claim_id}")
    if not override.get("reviewed_by") or not override.get("rationale"):
        raise ValueError(f"Entry-level clock mapping needs reviewer and rationale: {claim_id}")
    route, canonical = override.get("route"), override.get("canonical_clock")
    if route == "alias":
        if not canonical or canonical not in crosswalk.get("canonical_clocks", {}):
            raise ValueError(f"Entry-level alias needs a defined clock: {claim_id}")
    elif route not in {"varies_by_entry", "descriptive_other", "descriptive_single_milestone", "retain_raw_clock"} or canonical is not None:
        raise ValueError(f"Unsupported entry-level clock mapping: {claim_id}")
    if "observation_status" in override:
        if override["observation_status"] not in STATUSES:
            raise ValueError(f"Entry-level reading needs a canonical observation status: {claim_id}")
        if "precision" in override and override["precision"] not in {"exact_as_stated", "approximate", "month_only", "year_only", "unspecified"}:
            raise ValueError(f"Unsupported entry-level precision reading: {claim_id}")
    return {**override, "mapping_scope": "reviewed_claim"}


def validate_action_additions(readings, episodes):
    """Validate explicit, additive contextual readings without changing originals."""
    for key, reading in readings.items():
        if key not in episodes:
            raise ValueError(f"Action reading has no input episode: {key}")
        episode = episodes[key]
        if reading.get("episode_content_sha256") != claim_content_sha256(episode):
            raise ValueError(f"Stale action reading: {key}")
        if not reading.get("reviewed_by") or not reading.get("rationale"):
            raise ValueError(f"Action reading needs reviewer and rationale: {key}")
        existing = {claim_content_sha256(a) for a in episode.get("non_registry_actions") or []}
        actions = reading.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError(f"Action reading needs an explicit nonempty list: {key}")
        for action in actions:
            if (not action.get("actor") or not action.get("action") or not action.get("quote")
                    or not isinstance(action.get("refs"), list) or not action["refs"]
                    or action.get("status") not in {"performed", "refused_by_actor", "explicit_negative",
                                                    "explicit_not_required", "pending", "planned_not_performed"}):
                raise ValueError(f"Incomplete typed action reading: {key}")
            content = claim_content_sha256(action)
            if content in existing:
                raise ValueError(f"Duplicate action addition: {key}")
            existing.add(content)


def compile_input(frozen_path, check_log, aliases_path, out, action_readings_path=None):
    if out.exists():
        raise FileExistsError(out)
    frozen = json.loads(frozen_path.read_bytes())
    crosswalk = json.loads(aliases_path.read_bytes()) if aliases_path else {}
    action_readings = json.loads(action_readings_path.read_bytes())["episodes"] if action_readings_path else {}
    # Validate all requested overrides before producing any output, including
    # entries later retained as forecasts or summaries rather than fitted.
    timing_claims, all_episodes = {}, {}
    for packet in frozen["packets"]:
        for episode in packet["files"]["decisions"].get("episodes", []):
            episode_key = f"{packet['packet_id']}:{episode['decision_case_id']}"
            if episode_key in all_episodes:
                raise ValueError(f"Duplicate episode ID: {episode_key}")
            all_episodes[episode_key] = episode
            for ti, claim in enumerate(episode.get("timing") or []):
                key = f"{packet['packet_id']}:{episode['decision_case_id']}:timing:{ti}"
                if key in timing_claims:
                    raise ValueError(f"Duplicate timing claim ID: {key}")
                timing_claims[key] = claim
    for key in crosswalk.get("claim_mappings", {}):
        if key not in timing_claims:
            raise ValueError(f"Entry-level clock mapping has no input claim: {key}")
        resolve_clock_mapping(key, timing_claims[key], crosswalk)
    validate_action_additions(action_readings, all_episodes)
    # Cached checks may include explicitly qualified earlier-version receipts;
    # do not treat them as current-version PASS. A bad cost/action locator need
    # not erase unrelated timing. Current raw hashes/claim locators are below.
    blocks = re.split(r"(?:\A|\n)=== (\S+) === ", check_log.read_text())
    errors = {blocks[i]: blocks[i + 1] for i in range(1, len(blocks), 2)}
    candidates, routes, episodes_out, packet_accounting = [], [], [], []
    counts, clock_counts = Counter(), Counter()
    for packet in frozen["packets"]:
        pid = packet["packet_id"]
        files = packet["files"]
        dec, res, coverage = files["decisions"], files["reservation"], files["coverage"]
        log = errors.get(pid, "MISSING CHECK")
        fatal = "MISSING CHECK" in log or any(x in log for x in (
            "SHA-256 mismatch", "source missing:", "schema_version=", "coverage/reservation thread mismatch"))
        # Resolve only sources actually present in a completed packet. No
        # title-only geography guessing and no global comment-ID fallback.
        source_map, source_hashes = {}, {}
        for s in res.get("sources", []):
            path = ROOT / s["source_path"]
            source_hashes[s["thread_id"]] = {"path": s["source_path"], "sha256": s["sha256"]}
            # A prior checker receipt does not bind subsequently changed raw
            # bytes. Compilation already reads these sources for quote replay;
            # validate that same read before attributing the frozen hash to it.
            source_bytes = path.read_bytes()
            if digest(source_bytes) != s["sha256"]:
                raise ValueError(f"Frozen raw source changed since reservation: {s['source_path']}")
            if path.suffix != ".json":
                continue
            data = json.loads(source_bytes)
            if "post" not in data:
                continue
            post = data["post"]
            fields = {"post": [{"text": post.get("selftext") or "", "json_path": "$.post.selftext", "author": post.get("author")},
                               {"text": post.get("title") or "", "json_path": "$.post.title", "author": post.get("author")}]}
            for i, c in enumerate(data.get("comments", [])):
                fields[c.get("id")] = [{"text": c.get("body") or "", "json_path": f"$.comments[{i}].body", "author": c.get("author")}]
            source_map[s["thread_id"]] = fields
        rows = coverage.get("rows", coverage.get("threads", [])) if isinstance(coverage, dict) else coverage
        packet_accounting.append({"packet_id": pid, "threads": len(rows),
                                  "read_comments": sum(r.get("read_comments", 0) for r in rows),
                                  "check_pass": log.startswith("PASS"), "fatal_for_timing": fatal})
        case_links = within_packet_case_links(dec.get("episodes", []))
        staged_episodes = files.get('timing_staged', {}).get('episodes', [])
        for ei, ep in enumerate(dec.get("episodes", [])):
            episode_out = {"packet_id": pid, "original": ep}
            episodes_out.append(episode_out)
            cid = ep["decision_case_id"]
            canonical_case = f"{pid}:{case_links[cid]}"
            author = str(ep.get("author") or "").casefold()
            staged_ep, staged_link = matching_staged_episode(ep, dec.get('episodes', []), staged_episodes)
            geography = episode_geography(ep, staged_ep)
            # Deleted accounts are not all one person. No fuzzy username merges.
            group = ("reddit:" + author) if author not in {"", "[deleted]", "none", "automoderator"} else canonical_case
            for field in ("timing", "costs", "effort", "non_registry_actions"):
                for ti, t in enumerate(ep.get(field) or []):
                    key = f"{pid}:{cid}:{field}:{ti}"
                    row = {"claim_id": key, "packet_id": pid, "case_id": canonical_case,
                           "contributor_group": group, "field": field, "original": t,
                           "source_decisions_json_path": f"$.episodes[{ei}].{field}[{ti}]"}
                    if ep.get('same_installation_candidate') or ep.get('linkage_uncertainty'):
                        row['unresolved_case_linkage'] = {name: ep[name] for name in
                            ('same_installation_candidate', 'linkage_uncertainty') if name in ep}
                    counts[field] += 1
                    if field != "timing":
                        row["route"] = {"costs": "retained_monetary_evidence_not_elapsed", "effort": "retained_effort_evidence_not_elapsed",
                                        "non_registry_actions": "retained_structure_evidence_not_duration_likelihood"}[field]
                        routes.append(row)
                        continue
                    row.update(raw_clock=t.get("clock"), refs=t.get("refs", []), quote=t.get("quote"),
                               utility=ep.get("utility"), location=ep.get("location"),
                               location_evidence=ep.get("location_evidence"), **geography,
                               geography_staged_link=staged_link,
                               geography_scope=geo_scope(ep, geography), inference_scope=ep.get("inference_scope"),
                               thread=ep.get("thread"))
                    status, precision, status_method = classify_status(t, frozen["censoring_crosswalk"]["map"])
                    mapping = resolve_clock_mapping(key, t, crosswalk)
                    if mapping.get("mapping_scope") == "reviewed_claim" and "observation_status" in mapping:
                        row.update(unreviewed_observation_status=status, unreviewed_precision=precision,
                                   reviewed_claim_interpretation=mapping)
                        status = mapping["observation_status"]
                        precision = mapping.get("precision", precision)
                        status_method = "reviewed_claim_status"
                    row.update(observation_status=status, precision=precision, status_adapter=status_method)
                    if fatal:
                        row["route"] = "held_packet_integrity_error"
                    elif status not in {"completed_observed", "range_reported", "upper_bound_only", "pending_lower_bound"}:
                        row["route"] = "retained_" + status
                    else:
                        text_scope = " ".join(str(x or "") for x in (ep.get("inference_scope"), t.get("censoring")))
                        if re.search(r"professional[_ -]aggregate|general[_ -]estimate|not[_ -]own[_ -]case|projected|hypothetical|warranty|payback|typical|habitual|aggregate", text_scope, re.I):
                            row["route"] = "retained_non_individual_or_projected_summary"
                        else:
                            bounds, error = duration_bounds(t, status, precision)
                            if error:
                                row["route"] = "retained_" + error
                            else:
                                row.update(bounds)
                                raw_clock = t.get("clock", "")
                                canonical = mapping.get("canonical_clock")
                                row["clock"] = canonical or raw_clock
                                row["clock_alias"] = mapping if canonical or mapping.get("mapping_scope") == "reviewed_claim" else None
                                row["clock_pooling_status"] = mapping.get("route", "exact_label_unreviewed")
                                row["eligible_for_shared_clock_fit"] = mapping.get("route") not in {"varies_by_entry", "descriptive_other", "descriptive_single_milestone"}
                                refs = source_map.get(ep.get("thread"), {})
                                supporting = [dict(s, ref=ref) for ref in t.get("refs", []) for s in refs.get(ref, [])]
                                quote = t.get("quote") or ""
                                # Literal replay; normalized typography is accepted with a
                                # visible receipt, matching the bounded checker convention.
                                norm = lambda x: re.sub(r"\s+", " ", x).strip().casefold().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
                                matched = [s for s in supporting if quote and norm(quote) in norm(s["text"])]
                                if not matched:
                                    row["route"] = "held_quote_or_external_locator_adapter"
                                else:
                                    row["supporting_sources"] = [dict(source_hashes[ep["thread"]], **s) for s in matched]
                                    row["source_hashes"] = {source_hashes[ep["thread"]]["path"]: source_hashes[ep["thread"]]["sha256"]}
                                    row["quote_replay"] = "literal" if any(quote in s["text"] for s in matched) else "whitespace_typography_case_normalized"
                                    row["route"] = "eligible_elapsed_candidate"
                                    candidates.append(row)
                    routes.append(row)
            addition = action_readings.get(f"{pid}:{cid}")
            if addition:
                if fatal:
                    raise ValueError(f"Action additions need usable packet lineage: {pid}:{cid}")
                episode_out["reviewed_action_additions"] = addition
                episode_out["effective_non_registry_actions"] = [*(ep.get("non_registry_actions") or []), *addition["actions"]]
                for ai, action in enumerate(addition["actions"]):
                    supporting = [dict(s, ref=ref) for ref in action["refs"]
                                  for s in source_map.get(ep.get("thread"), {}).get(ref, [])]
                    matched = [s for s in supporting if action["quote"] in s["text"]
                               and str(s.get("author") or "").casefold() == author]
                    if not matched:
                        raise ValueError(f"Action addition quote/author does not replay: {pid}:{cid}:{ai}")
                    counts["non_registry_actions"] += 1
                    routes.append({
                        "claim_id": f"{pid}:{cid}:reviewed_action:{ai}", "packet_id": pid,
                        "case_id": canonical_case, "contributor_group": group,
                        "field": "non_registry_actions", "original": action,
                        "source_decisions_json_path": None,
                        "source_reviewed_actions_json_path": f"$.episodes[{json.dumps(f'{pid}:{cid}')}].actions[{ai}]",
                        "reviewed_by": addition["reviewed_by"], "rationale": addition["rationale"],
                        "supporting_sources": [dict(source_hashes[ep["thread"]], **s) for s in matched],
                        "route": "retained_structure_evidence_not_duration_likelihood",
                        "quote_replay": "literal",
                    })
    grouped = defaultdict(list)
    for row in candidates:
        grouped[(row["contributor_group"], row["clock"], row["time_unit"])].append(row)
    observations = []
    for key, values in sorted(grouped.items()):
        # Bound-independent selection avoids favoring short/completed outcomes.
        values.sort(key=lambda r: digest(("solar-bulk-one-report/1\0" + r["claim_id"]).encode()))
        chosen = values[0]
        chosen["route"] = "adopted_elapsed_observation"
        chosen["dependence_policy"] = "one_hash_selected_report_per_exact_username_clock_unit_not_one_claim_per_post"
        observations.append(chosen)
        clock_counts[chosen["clock"] + "|" + chosen["time_unit"]] += 1
        for row in values[1:]:
            row["route"] = "retained_same_contributor_clock_not_independent"
            row["selected_claim_id"] = chosen["claim_id"]
    implementation = Path(__file__).read_bytes()
    report = {"schema_version": "solar-bulk-adoption-accounting/1",
              "compiler": {"module": "pipeline.procbench.solar_panel.adopt_bulk_forum",
                           "source_sha256": digest(implementation),
                           "snapshot": "compiler_snapshot.py"},
              "inputs": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in [frozen_path, check_log, *([aliases_path] if aliases_path else []), *([action_readings_path] if action_readings_path else [])]},
              "packets": packet_accounting, "counts": dict(counts), "episodes": len(episodes_out),
              "reviewed_entry_clock_mappings": len(crosswalk.get("claim_mappings", {})),
              "reviewed_action_additions": sum(len(r["actions"]) for r in action_readings.values()),
              "routes": dict(Counter(r["route"] for r in routes)), "adopted_observations": len(observations),
              "distinct_contributor_groups": len({o["contributor_group"] for o in observations}),
              "clock_support": dict(clock_counts.most_common()),
              "geography": dict(Counter(o["geography_scope"] for o in observations)),
              "scope": "Selected national forum reports, unresolved geography retained. Not a representative California population or identified intrinsic agency capability.",
              "dependence": "At most one bound-independent hash-selected observation per exact author+clock+unit; no claim of independent overlapping clocks, no sum across phase fits.",
              "fit_status": "prepared_not_fitted"}
    write(out / "observations.json", observations)
    (out / "compiler_snapshot.py").write_bytes(implementation)
    if aliases_path:
        write(out / "clock_aliases_snapshot.json", json.loads(aliases_path.read_bytes()))
    write(out / "claim_routes.json", routes)
    write(out / "episodes.json", episodes_out)
    if action_readings_path:
        write(out / "action_readings_snapshot.json", json.loads(action_readings_path.read_bytes()))
    write(out / "adoption_accounting.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in {"packets", "clock_support", "inputs"}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--index", type=Path, required=True)
    f.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("compile")
    c.add_argument("--frozen", type=Path, required=True)
    c.add_argument("--check-log", type=Path, required=True)
    c.add_argument("--clock-aliases", type=Path)
    c.add_argument("--action-readings", type=Path, help="Optional exact-episode-bound additive action readings; originals stay unchanged.")
    c.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("report")
    r.add_argument("--adopted", type=Path, required=True)
    r.add_argument("--model", type=Path, action="append", required=True)
    r.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.index.resolve(), args.out.resolve())
    elif args.command == "compile":
        compile_input(args.frozen.resolve(), args.check_log.resolve(),
                      args.clock_aliases.resolve() if args.clock_aliases else None, args.out.resolve(),
                      args.action_readings.resolve() if args.action_readings else None)
    else:
        report(args.adopted.resolve(), [p.resolve() for p in args.model], args.out.resolve())


def report(adopted, models, out):
    """Join routing to completed fit receipts, never count preparation as fitting."""
    if out.exists():
        raise FileExistsError(out)
    routes = json.loads((adopted / "claim_routes.json").read_bytes())
    consumption = {r["claim_id"]: {"claim_id": r["claim_id"], "field": r["field"],
        "adoption_route": r["route"], "model_routes": {}, "fitted_in": []} for r in routes}
    if len(consumption) != len(routes):
        raise ValueError("Claim accounting must be one-to-one")
    results = []
    for model in models:
        plan = json.loads((model / "fit_plan.json").read_bytes())
        if plan["input_sha256"] != digest((adopted / "observations.json").read_bytes()):
            raise ValueError("Fit and adopted input hashes differ")
        completed = json.loads((model / "fit_results.json").read_bytes())
        if len(completed) != len(plan["queue"]):
            raise ValueError("Fit queue is unfinished; do not publish a final result")
        model_routes = json.loads((model / "route_accounting.json").read_bytes())["rows"]
        valid_frames = {}
        for frame in completed:
            posterior_path = model / frame["fit"] / "posterior.json"
            posterior = json.loads(posterior_path.read_bytes())
            program = next(iter(posterior["programs"].values()))
            frame_id = model.name + ":" + frame["frame"]
            valid_frames[frame["frame"]] = frame_id if posterior["numerically_usable"] else None
            results.append({"frame_id": frame_id, "scope": plan.get("scope", "all"),
                "clock": frame["clock"], "time_unit": frame["time_unit"],
                "contributors": frame["contributors"], "geography": frame["geography"],
                "completed_intervals": frame["completed_intervals"],
                "completed_lower_bounds": frame["completed_lower_bounds"],
                "pending_right_censored": frame["pending_right_censored"],
                "numerically_usable": posterior["numerically_usable"],
                "median_duration_posterior": program["metrics"]["modeled_work_end_median_days"],
                "p90_duration_posterior": program["metrics"]["modeled_work_end_p90_days"],
                "max_rhat": max(v["rhat"] for v in posterior["diagnostics"].values()),
                "min_bulk_ess": min(v["ess_bulk"] for v in posterior["diagnostics"].values()),
                "quadrature_pass": posterior["precision"]["likelihood_acceptable"],
                "identification": posterior["identification"],
                "posterior_path": str(posterior_path.relative_to(ROOT)),
                "posterior_sha256": digest(posterior_path.read_bytes())})
        for row in model_routes:
            target = consumption[row["claim_id"]]
            target["model_routes"][model.name] = row["route"]
            frame_id = valid_frames.get(row.get("frame"))
            if row["route"] == "modeled" and frame_id:
                target["fitted_in"].append(frame_id)
    final = {"schema_version": "solar-bulk-fit-result/1", "results": results,
             "all_extracted_entries": len(consumption),
             "entries_in_at_least_one_usable_fit": sum(bool(r["fitted_in"]) for r in consumption.values()),
             "adoption_routes": dict(Counter(r["adoption_route"] for r in consumption.values())),
             "qualification": "Credible intervals describe uncertainty in a selected-report-frame median, not the range for an individual applicant. California subset overlaps pooled sample. No intrinsic agency, process-structure, source-selection calibration or LLM superiority claim."}
    write(out / "claim_consumption.json", list(consumption.values()))
    write(out / "results.json", final)
    print(json.dumps({k: v for k, v in final.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
