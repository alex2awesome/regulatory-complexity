"""Compile reviewed Solar or ADU journeys into native multi-operation V6 data.

This module performs no text, date, actor, path, or geography inference.  Every
modeled operation and every observation-to-operation relation must be declared
by a reviewer. Dates are event attributes, never event identities.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

from ..bayes_trace_hierarchy import Config, VisitHierarchy


SCHEMA = "solar-reviewed-action-journeys/1"
KINDS = {"completed_interval", "completed_lower_bound", "pending_right_censored"}
RELATIONS = {"independent_report", "derived_reconstruction", "overlapping_not_jointly_admitted"}
ACTOR_ROLES = {"payer", "agency", "third_party", "unknown"}


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return result or hashlib.sha256(value.encode()).hexdigest()[:12]


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _actor(raw: dict) -> tuple[str | None, str]:
    if not isinstance(raw, dict) or set(raw) != {"kind", "id"}:
        raise ValueError("Actors require exactly kind and id")
    kind, actor_id = raw["kind"], raw["id"]
    roles = {"applicant": "payer", "installer": "third_party", "private": "third_party",
             "hoa": "third_party", "utility": "agency", "ahj": "agency",
             "ahj_inspector": "agency", "fire_department_inspector": "agency",
             "unknown": "unknown"}
    if kind not in roles or (actor_id is not None and (not isinstance(actor_id, str) or not actor_id)):
        raise ValueError("Unsupported actor kind or id")
    return actor_id, roles[kind]


def _union_find(journeys: list[dict]) -> dict[str, str]:
    # Aliases point to a reviewer-selected canonical ID. Do not choose the
    # lexicographically smallest username or packet-local identifier.
    identities, target = set(), {}
    for journey in journeys:
        canonical = journey.get("canonical_case_id")
        aliases = journey.get("same_installation_aliases", [])
        if not isinstance(canonical, str) or not canonical or not isinstance(aliases, list):
            raise ValueError("Each journey needs canonical_case_id and an alias list")
        identities.add(canonical)
        for alias in aliases:
            if not isinstance(alias, str) or not alias:
                raise ValueError("Case aliases must be nonempty strings")
            identities.add(alias)
            if alias in target and target[alias] != canonical:
                raise ValueError("One case alias cannot point to multiple canonical installations")
            target[alias] = canonical

    def resolve(case):
        seen = set()
        while case in target:
            if case in seen:
                raise ValueError("Case aliases cannot form a cycle")
            seen.add(case); case = target[case]
        return case

    return {case: resolve(case) for case in identities}


def _merge_unique(target: dict, rows: list[dict], key: str, kind: str) -> None:
    for row in rows:
        ident = row.get(key)
        if not isinstance(ident, str) or not ident:
            raise ValueError(f"{kind} requires {key}")
        if ident in target and target[ident] != row:
            raise ValueError(f"Conflicting linked-case {kind}: {ident}")
        target[ident] = row


def _acyclic(operations: dict[str, dict]) -> None:
    graph = {key: list(value.get("predecessor_operation_ids", [])) for key, value in operations.items()}
    if any(not isinstance(xs, list) or any(x not in graph for x in xs) for xs in graph.values()):
        raise ValueError("Operation predecessors must name declared operations")
    state = {}

    def visit(node):
        if state.get(node) == 1:
            raise ValueError("Operation predecessor graph contains a cycle")
        if state.get(node) == 2:
            return
        state[node] = 1
        for predecessor in graph[node]:
            visit(predecessor)
        state[node] = 2

    for node in graph:
        visit(node)


def _validate_event_dependencies(operations: dict[str, dict]) -> None:
    """Bind shared semantic events to the native schedule, not just metadata."""
    producers = defaultdict(set)
    for ident, row in operations.items():
        producers[row["end_event_id"]].add(ident)
    reused = {event: sorted(ids) for event, ids in producers.items() if len(ids) > 1}
    if reused:
        raise ValueError("Initial journey compiler requires one producer per semantic completion "
                         "event; parallel branches need distinct completion events and an explicit "
                         f"reviewed join operation: {reused}")
    for ident, row in operations.items():
        declared = set(row["predecessor_operation_ids"])
        event_producers = producers[row["start_event_id"]] - {ident}
        if declared != event_producers:
            raise ValueError(
                "Operation predecessors must exactly bind every operation ending at its "
                f"shared start event; explicit gap operations need distinct events ({ident})")


def _compile_group(case_id: str, declarations: list[tuple[str, dict]],
                   identity_aliases: dict, domain: str = "solar") -> tuple[dict | None, list[dict], list[dict]]:
    events, operations, observations = {}, {}, {}
    geography, source_threads, lifecycle = [], set(), set()
    alternatives = None
    routes, transformations = [], []
    for packet_name, journey in declarations:
        _merge_unique(events, journey.get("events", []), "event_id", "event")
        _merge_unique(operations, journey.get("operations", []), "operation_id", "operation")
        _merge_unique(observations, journey.get("observations", []), "observation_id", "observation")
        source_threads.update(journey.get("source_threads", []))
        lifecycle.add(journey.get("lifecycle_stage"))
        geography.append({"source_packet": packet_name, "value": journey.get("geography")})
        declared = journey.get("route_alternatives")
        if declared is not None:
            if alternatives is not None and alternatives != declared:
                raise ValueError("Linked declarations conflict on route_alternatives")
            alternatives = declared
    if None in lifecycle or len(lifecycle) != 1:
        raise ValueError("Linked journey declarations need one consistent lifecycle_stage")
    event_ids = set(events)
    for row in operations.values():
        required = {"operation_id", "action_id", "occurrence", "actor", "start_event_id",
                    "end_event_id", "status", "component_kind",
                    "predecessor_operation_ids", "refs"}
        if set(row) != required:
            raise ValueError("Operations require exact reviewed action-journey fields")
        if row["start_event_id"] not in event_ids or row["end_event_id"] not in event_ids:
            raise ValueError("Operation endpoints must name semantic reviewed events")
        if row["start_event_id"] == row["end_event_id"]:
            raise ValueError("Operation needs distinct semantic events; same dates are allowed")
        if not isinstance(row["occurrence"], int) or isinstance(row["occurrence"], bool) or row["occurrence"] < 1:
            raise ValueError("Operation occurrence must be a positive integer")
        if row["status"] not in {"performed", "pending", "unknown"}:
            raise ValueError("Unsupported operation status")
        if row["component_kind"] not in {
                "action_cycle", "mixed_elapsed_residual", "coordination_interval"}:
            raise ValueError("Unsupported operation component_kind")
        if (row["component_kind"] == "mixed_elapsed_residual"
                and row["actor"] != {"kind": "unknown", "id": None}):
            raise ValueError("mixed_elapsed_residual must retain unknown actor attribution")
        _actor(row["actor"])
    _acyclic(operations)
    _validate_event_dependencies(operations)
    origins = {o["start_event_id"] for o in operations.values()
               if not o["predecessor_operation_ids"]}
    if len(origins) > 1:
        # Distinct unlinked origins are not simultaneous parallel branches.
        # Keep the entire declaration available for a reviewed connector or a
        # deliberately scoped window, rather than silently aligning its roots.
        return None, [{"case_id": case_id,
                       "route": "unlinked_time_origins_require_reviewed_alignment",
                       "origin_event_ids": sorted(origins)}], transformations

    admitted, route_rows, units = [], [], set()
    for row in observations.values():
        relation = row.get("evidence_relation")
        base = {"observation_id": row.get("observation_id"), "case_id": case_id,
                "source_refs": row.get("refs", [])}
        if relation not in RELATIONS:
            raise ValueError("Unknown observation evidence_relation")
        if relation != "independent_report":
            route_rows.append(base | {"route": relation})
            continue
        kind, lower, upper = row.get("observation_kind"), row.get("lower"), row.get("upper")
        if kind not in KINDS or not _finite(lower) or lower < 0:
            raise ValueError("Independent observations need supported censoring and finite lower")
        if kind == "completed_interval":
            if not _finite(upper) or upper <= lower:
                raise ValueError("Completed interval needs upper > lower")
        elif upper is not None or lower <= 0:
            raise ValueError("Lower-bound observations need positive lower and null upper")
        ids = row.get("operation_ids")
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or any(x not in operations for x in ids):
            raise ValueError("Every independent observation needs explicit distinct operation_ids")
        unit = row.get("time_unit")
        if unit != "calendar_days":
            route_rows.append(base | {"route": "unsupported_unit_no_silent_conversion", "time_unit": unit})
            continue
        units.add(unit)
        event_interval = row.get("activity_event_interval")
        if event_interval is None:
            if len(ids) > 1 and row.get("measurement_basis") != "sum_of_cycle_times":
                raise ValueError("Multi-operation elapsed spans require activity_event_interval; "
                                 "sum_visit_cycles requires explicit measurement_basis=sum_of_cycle_times")
            operator = {"basis": "single_visit_cycle" if len(ids) == 1 else "sum_visit_cycles",
                        "activity_ids": ids}
        else:
            if not isinstance(event_interval, dict) or set(event_interval) != {"start", "end"}:
                raise ValueError("activity_event_interval requires exact start/end endpoints")
            endpoints = {}
            for label in ("start", "end"):
                endpoint = event_interval[label]
                if (not isinstance(endpoint, dict)
                        or set(endpoint) != {"operation_id", "event", "occurrence"}
                        or endpoint["operation_id"] not in operations
                        or endpoint["event"] not in {"start", "end"}
                        or endpoint["occurrence"] not in {"first", "last"}):
                    raise ValueError("Reviewed activity-event endpoints are invalid")
                endpoints[label] = {"activity_id": endpoint["operation_id"],
                                    "event": endpoint["event"],
                                    "occurrence": endpoint["occurrence"]}
            operator = {"basis": "activity_event_interval", **endpoints}
            endpoint_ids = {event_interval[x]["operation_id"] for x in ("start", "end")}
            if not endpoint_ids <= set(ids):
                raise ValueError("activity event endpoints must be included in reviewed operation_ids")
        admitted.append((row, ids, operator))
    if len(units) > 1:
        return None, route_rows + [{"case_id": case_id, "route": "mixed_units_require_separate_reviewed_journey"}], transformations
    if not admitted:
        return None, route_rows + [{"case_id": case_id, "route": "no_independent_supported_observations"}], transformations

    def operation_payload(ident):
        row = operations[ident]
        actor_id, actor_role = _actor(row["actor"])
        action_id = identity_aliases["action_ids"].get(row["action_id"], row["action_id"])
        canonical_actor = identity_aliases["actor_ids"].get(actor_id, actor_id)
        if action_id != row["action_id"]:
            transformations.append({"case_id": case_id, "operation_id": ident,
                "identity_type": "action_id", "original": row["action_id"],
                "canonical": action_id})
        if canonical_actor != actor_id:
            transformations.append({"case_id": case_id, "operation_id": ident,
                "identity_type": "actor_id", "original": actor_id,
                "canonical": canonical_actor})
        return {"id": ident, "actor_id": actor_id, "actor_role": actor_role,
            "task_type": action_id, "markers": [],
            "payer_work": True if actor_role == "payer" else None,
            "agency_work": True if actor_role == "agency" else None} | {
                "actor_id": canonical_actor}

    all_ids = list(operations)
    if alternatives is None:
        alternatives = [{"route_id": "reviewed_realized_journey", "prior_weight": 1.,
                         "operation_ids": all_ids, "assumption": "fixed reviewed realized structure"}]
    if not isinstance(alternatives, list) or not alternatives:
        raise ValueError("route_alternatives must be a nonempty list")
    native_routes = []
    invalid_alternatives = []
    for alternative in alternatives:
        ids = alternative.get("operation_ids")
        if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
                or any(x not in operations for x in ids)):
            raise ValueError("Route alternatives need distinct declared operation IDs")
        weight = alternative.get("prior_weight")
        if not _finite(weight) or weight <= 0:
            raise ValueError("Route prior weights must be fixed positive numbers")
        # An admitted report must remain defined under every unresolved route.
        missing = sorted({x for _, observed, _ in admitted for x in observed} - set(ids))
        if missing:
            invalid_alternatives.append({"case_id": case_id, "route": "route_alternative_not_encoded",
                "route_id": alternative.get("route_id"), "missing_observed_operations": missing})
            continue
        missing_predecessors = {ident: sorted(set(operations[ident]["predecessor_operation_ids"]) - set(ids))
                                for ident in ids}
        missing_predecessors = {key: value for key, value in missing_predecessors.items() if value}
        if missing_predecessors:
            invalid_alternatives.append({"case_id": case_id,
                "route": "route_alternative_not_predecessor_closed",
                "route_id": alternative.get("route_id"),
                "missing_predecessors": missing_predecessors})
            continue
        blocks = [{"id": "block__" + ident, "operations": [ident],
                   "predecessors": ["block__" + x for x in operations[ident]["predecessor_operation_ids"]]}
                  for ident in ids]
        native_routes.append({"id": alternative["route_id"], "prior_weight": float(weight),
            "operations": [operation_payload(x) for x in ids], "blocks": blocks})
    if invalid_alternatives:
        return None, route_rows + invalid_alternatives + [{"case_id": case_id,
            "route": "program_not_compiled_preserve_all_declared_route_prior_mass"}], transformations
    if not native_routes:
        return None, route_rows + [{"case_id": case_id, "route": "no_representable_route_alternative"}], transformations
    total_weight = sum(x["prior_weight"] for x in native_routes)
    if not math.isclose(total_weight, 1., rel_tol=0., abs_tol=1e-12):
        raise ValueError("Declared route prior weights must sum to one; compiler will not renormalize")

    native_observations = []
    for row, ids, operator in admitted:
        native_observations.append({"id": row["observation_id"], "case_id": case_id,
            "source_family": domain + "_reviewed_action_journeys",
            # V6's literal token means the likelihood applies no ascertainment
            # correction. The enclosing context explicitly limits inference to
            # the selected reviewed-forum journey frame.
            "sampling": "unselected", "statistic": "individual",
            "lower": float(row["lower"]), "upper": None if row["upper"] is None else float(row["upper"]),
            "time_unit": row["time_unit"], "observation_kind": row["observation_kind"],
            "operators": [operator], "operator_weights": [1.], "provenance": {
                "source_refs": row.get("refs", []), "interpretation": row.get("interpretation"),
                "reviewed_event_endpoints": [row.get("start_event_id"), row.get("end_event_id")]}})
    program = {"id": domain + "_action_journey__" + _slug(case_id),
        # The generic V6 report must not count a mixed elapsed residual as a
        # recovered action. The journey-specific summary uses component_kind
        # to count reviewed actions while retaining these untimed interiors.
        "time_unit": next(iter(units)), "inventory_granularity": (
            "detailed_operations" if all(o["component_kind"] == "action_cycle"
                                         for o in operations.values()) else "aggregate_phases"),
        "clock_estimand": "Reviewer-declared endpoint spans over explicit action operations; unreported gaps are not zero",
        "journey_context": {"canonical_case_id": case_id, "source_threads": sorted(source_threads),
            "lifecycle_stage": next(iter(lifecycle)), "geography_evidence": geography,
            "selection_qualification": "Conditional on a selected reviewed forum journey; not applicant-population sampling",
            "reviewed_event_declarations": list(events.values()),
            "reviewed_operation_declarations": list(operations.values()),
            "reviewed_observation_declarations": list(observations.values())},
        "routes": native_routes, "observations": native_observations}
    # Alternative routes may call operation_payload repeatedly. The receipt is
    # an identity ledger, not a route multiplicity count.
    unique = {(x["case_id"], x["operation_id"], x["identity_type"]): x
              for x in transformations}
    return program, route_rows, [unique[key] for key in sorted(unique)]


def _load_identity_aliases(path: Path | None) -> tuple[dict, dict | None]:
    empty = {"action_ids": {}, "actor_ids": {}}
    if path is None:
        return empty, None
    payload = json.loads(path.read_bytes())
    if (not isinstance(payload, dict)
            or set(payload) != {"schema_version", "rationale", "action_ids", "actor_ids"}
            or payload["schema_version"] != "solar-action-identity-aliases/1"
            or not isinstance(payload["rationale"], str) or not payload["rationale"].strip()):
        raise ValueError("Identity aliases require the exact reviewed version-1 schema")
    for kind in ("action_ids", "actor_ids"):
        mapping = payload[kind]
        if (not isinstance(mapping, dict)
                or any(not isinstance(source, str) or not source or not isinstance(target, str)
                       or not target or source == target for source, target in mapping.items())):
            raise ValueError("Identity alias maps require distinct nonempty string labels")
        if set(mapping) & set(mapping.values()):
            raise ValueError("Identity aliases must resolve directly, not through chains")
    return {kind: dict(payload[kind]) for kind in ("action_ids", "actor_ids")}, {
        "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "schema_version": payload["schema_version"], "rationale": payload["rationale"]}


def compile_packets(paths: list[Path], identity_aliases: Path | None = None,
                    *, domain: str = "solar") -> tuple[dict, dict]:
    if domain not in {"solar", "adu"}:
        raise ValueError("Journey domain must be solar or adu")
    aliases, alias_binding = _load_identity_aliases(identity_aliases)
    packets, declarations = [], []
    for path in paths:
        packet = json.loads(path.read_bytes())
        if packet.get("schema_version") != domain + "-reviewed-action-journeys/1":
            raise ValueError("Unknown reviewed action-journey schema")
        if packet.get("adoption_state") not in {"staged", "adopted"}:
            raise ValueError("Declaration adoption_state must be staged or adopted")
        packets.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "adoption_state": packet["adoption_state"],
                        "source_bindings": packet.get("source_bindings", [])})
        declarations.extend((str(path), row) for row in packet.get("journeys", []))
    alias = _union_find([row for _, row in declarations])
    grouped = defaultdict(list)
    for source, row in declarations:
        grouped[alias[row["canonical_case_id"]]].append((source, row))
    programs, routes, transformations = [], [], []
    for case_id, rows in sorted(grouped.items()):
        program, dispositions, applied = _compile_group(case_id, rows, aliases, domain)
        routes.extend(dispositions)
        transformations.extend(applied)
        if program is not None:
            programs.append(program)
    data = {"elapsed_time_unit": "calendar_days", "programs": programs}
    # Native validation is the final compiler contract; no sampling occurs.
    if programs:
        VisitHierarchy(data, Config(modeled_channels=("elapsed",)))
    component_counts = defaultdict(int)
    for program in programs:
        for operation in program["journey_context"]["reviewed_operation_declarations"]:
            component_counts[operation["component_kind"]] += 1
    receipt = {"schema_version": domain + "-action-journey-compilation/1", "input_packets": packets,
        "identity_aliases_binding": alias_binding,
        "identity_alias_transformations": transformations,
        "canonical_cases": len(grouped), "compiled_programs": len(programs),
        "modeled_observations": sum(len(p["observations"]) for p in programs),
        "modeled_operations": sum(len({o["id"] for r in p["routes"] for o in r["operations"]})
                                  for p in programs),
        "component_kind_counts": dict(sorted(component_counts.items())),
        "actor_action_counting_rule": "Only component_kind=action_cycle is eligible for unique actor-action counts; coordination intervals and mixed elapsed residuals are reported separately.",
        "routes": routes,
        "qualification": "Fixed or explicitly weighted reviewer-declared journey structures. Materialized repeat occurrences are timed operations; silence supplies no zero-repeat trial or population repeat frequency."}
    return data, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--declarations", type=Path, action="append", required=True)
    parser.add_argument("--identity-aliases", type=Path,
                        help="Reviewed exact action/actor identity aliases; no inferred matching")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--domain", choices=("solar", "adu"), default="solar",
                        help="Evidence/provenance namespace only; same V6 model and graph rules")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    data, receipt = compile_packets([p.resolve() for p in args.declarations],
        args.identity_aliases.resolve() if args.identity_aliases else None, domain=args.domain)
    args.out.mkdir(parents=True)
    _write(args.out / "data.json", data)
    _write(args.out / "compilation_receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("canonical_cases", "compiled_programs",
                                              "modeled_observations", "modeled_operations")}, indent=2))


if __name__ == "__main__":
    main()
