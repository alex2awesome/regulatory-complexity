"""Compile reviewed Solar timelines into shared-case V6 journey programs.

Each program is one canonical installation.  Dated endpoint intervals become
elapsed segments; a broader report reuses a path of those segments when the
reviewed endpoints form one.  Thus overlapping clocks are not independent
people and gaps inside a reported interval are not silently set to zero.

This prepares data only.  It does not fit, infer geography, or reinterpret a
utility/private segment as county-authority work.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
UNIT = {"calendar_days": 1., "days": 1., "business_days": 7 / 5,
        "weeks": 7., "months": 365.25 / 12, "years": 365.25}


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _case(ep):
    return ep.get("same_installation_as") or ep.get("decision_case_id") or (
        str(ep.get("thread")) + "__" + str(ep.get("author")))


def _bounds(row):
    if row.get("censoring", "completed") not in {"completed", "completed_approximate"}:
        return None
    if row.get("start_date") and row.get("end_date"):
        n = (dt.date.fromisoformat(row["end_date"]) -
             dt.date.fromisoformat(row["start_date"])).days
        return max(0., n - 1.), n + 1., float(n), row["start_date"], row["end_date"]
    value = row.get("value")
    unit = row.get("unit", "calendar_days")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or unit not in UNIT:
        return None
    value *= UNIT[unit]
    width = max(1., .15 * value) if row.get("approximate") or row.get("censoring") == "completed_approximate" else 1.
    clock = row.get("clock", "")
    if "_to_" not in clock:
        return None
    start, end = clock.split("_to_", 1)
    return max(0., value - width), value + width, float(value), start, end


def _actor(start, end, utility):
    text = start + " " + end
    utility_words = ("pto", "interconnection", "meter", "utility")
    ahj_words = ("permit", "inspection", "ahj", "city", "county")
    private_words = ("order", "design", "site_assessment", "installation", "invoice", "contract")
    kinds = {"utility" if any(x in text for x in utility_words) else None,
             "ahj" if any(x in text for x in ahj_words) else None,
             "private" if any(x in text for x in private_words) else None} - {None}
    if kinds == {"utility"}:
        return utility, "agency"
    if kinds == {"ahj"}:
        return None, "agency"
    if kinds == {"private"}:
        return None, "third_party"
    return None, "unknown"


def _alternate_path(edges, start, end, skip):
    graph = defaultdict(list)
    for i, edge in enumerate(edges):
        if i != skip:
            graph[edge["start"]].append((edge["end"], i))
    queue = deque([(start, [])]); seen = {start}
    while queue:
        node, path = queue.popleft()
        for nxt, i in graph[node]:
            if nxt == end:
                return path + [i]
            if nxt not in seen:
                seen.add(nxt); queue.append((nxt, path + [i]))
    return None


def _compile_episode(ep, packet):
    rows = []
    for timing in ep.get("timing", []):
        bounds = _bounds(timing)
        if bounds:
            lo, hi, value, start, end = bounds
            if start != end:
                clock = timing.get("clock", "")
                semantic = clock.split("_to_", 1) if "_to_" in clock else ("unknown_start", "unknown_end")
                rows.append(dict(timing=timing, lower=lo, upper=hi, value=value,
                                 start=start, end=end, semantic_start=semantic[0], semantic_end=semantic[1]))
    if len(rows) < 2:
        return None, "fewer_than_two_supported_completed_intervals"

    # An edge is atomic only when the other reviewed intervals do not provide a
    # complete endpoint path across it.  The value check prevents a merely
    # topological path with contradictory elapsed totals from replacing it.
    atomic = []
    for i, row in enumerate(rows):
        path = _alternate_path(rows, row["start"], row["end"], i)
        if path is None or not math.isclose(sum(rows[j]["value"] for j in path),
                                            row["value"], abs_tol=max(2., .03 * row["value"])):
            atomic.append(i)
    atomic_edges = [rows[i] for i in atomic]
    operations = []
    for i, edge in zip(atomic, atomic_edges):
        aid = "segment_%02d_%s_to_%s" % (i, _slug(edge["start"]), _slug(edge["end"]))
        edge["activity_id"] = aid
        actor_id, actor_role = _actor(edge["semantic_start"], edge["semantic_end"], ep.get("utility"))
        operations.append(dict(id=aid, actor_id=actor_id, actor_role=actor_role,
            task_type="elapsed_segment__" + _slug(edge["semantic_start"]) + "__to__" + _slug(edge["semantic_end"]),
            markers=[], payer_work=None, agency_work=None))

    # Find paths only through atomic edges for every report.
    def atomic_path(start, end):
        graph = defaultdict(list)
        for edge in atomic_edges:
            graph[edge["start"]].append(edge)
        queue = deque([(start, [])]); seen = {start}
        while queue:
            node, path = queue.popleft()
            for edge in graph[node]:
                if edge["end"] == end:
                    return path + [edge]
                if edge["end"] not in seen:
                    seen.add(edge["end"]); queue.append((edge["end"], path + [edge]))
        return None

    case_id = _case(ep)
    observations, reconstructions = [], []
    for j, row in enumerate(rows):
        path = atomic_path(row["start"], row["end"])
        if not path:
            return None, "endpoint_graph_not_representable"
        ids = [x["activity_id"] for x in path]
        # A wider interval that is exactly reconstructed from reviewed increments
        # is provenance/posterior output, not another likelihood factor.  Shared
        # case identity alone would not prevent algebraic double counting.
        if len(ids) > 1:
            reconstructions.append(dict(original_clock=row["timing"].get("clock"),
                endpoints=[row["start"], row["end"]], activity_ids=ids,
                reported_value_calendar_days=row["value"], refs=row["timing"].get("refs", []),
                likelihood_status="exact_reconstruction_not_independent_factor"))
            continue
        operator = ({"basis": "single_visit_cycle", "activity_ids": ids}
                    if len(ids) == 1 else
                    {"basis": "sum_visit_cycles", "activity_ids": ids})
        raw = row["timing"]
        oid = "journey_" + hashlib.sha256(
            (packet + case_id + str(j) + raw.get("clock", "")).encode()).hexdigest()[:16]
        observations.append(dict(id=oid, case_id=case_id,
            source_family="solar_forum_reviewed_journey", sampling="unselected",
            statistic="individual", lower=row["lower"], upper=row["upper"],
            time_unit="calendar_days", observation_kind="completed_interval",
            operators=[operator], operator_weights=[1.], provenance=dict(
                source_packet=packet, source_thread=ep.get("thread"), author=ep.get("author"),
                refs=raw.get("refs", []), original_clock=raw.get("clock"),
                original_timing=raw, endpoints=[row["start"], row["end"]])))

    predecessors = defaultdict(list)
    for edge in atomic_edges:
        predecessors[edge["activity_id"]] = [other["activity_id"] for other in atomic_edges
                                              if other["end"] == edge["start"]]
    blocks = [dict(id="block_" + op["id"], operations=[op["id"]],
                   predecessors=["block_" + x for x in predecessors[op["id"]]]) for op in operations]
    context = {k: ep[k] for k in ("thread", "author", "location", "utility",
        "candidate_counties", "county_assignment_probabilities", "unassigned_geography_mass",
        "unresolved_geography_mass", "report_date") if k in ep}
    return dict(id="solar_journey__" + _slug(case_id), time_unit="calendar_days",
        inventory_granularity="detailed_operations",
        clock_estimand="reviewed endpoint-to-endpoint elapsed calendar time; segment includes unreported waiting within its endpoints",
        journey_context=context, derived_reconstructions=reconstructions,
        routes=[dict(id="reviewed_endpoint_graph", prior_weight=1., operations=operations, blocks=blocks)],
        observations=observations), None


def compile_packets(paths):
    programs, routes, seen = [], [], set()
    for path in paths:
        packet = json.loads(path.read_bytes())
        for ep in packet.get("episodes", []):
            case_id = _case(ep)
            if case_id in seen:
                routes.append(dict(case_id=case_id, source_packet=str(path),
                                   route="duplicate_canonical_case_across_input_packets"))
                continue
            seen.add(case_id)
            program, reason = _compile_episode(ep, str(path))
            if program is None:
                routes.append(dict(case_id=case_id, source_packet=str(path), route=reason,
                                   geography={k: ep.get(k) for k in ("location", "candidate_counties",
                                   "unassigned_geography_mass", "unresolved_geography_mass") if k in ep}))
            else:
                programs.append(program)
    return {"schema_version":"solar-shared-case-journeys/1",
            "elapsed_time_unit":"calendar_days", "programs":programs}, routes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decisions", type=Path, action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    data, routes = compile_packets([p.resolve() for p in args.decisions])
    args.out.mkdir(parents=True)
    (args.out / "data.json").write_text(json.dumps(data, indent=2) + "\n")
    accounting = dict(input_packets=[str(p.resolve()) for p in args.decisions],
        programs=len(data["programs"]), observations=sum(len(p["observations"]) for p in data["programs"]),
        atomic_segments=sum(len(p["routes"][0]["operations"]) for p in data["programs"]),
        routes=routes,
        limitations=[
          "Value-only intervals compile when clock names provide explicit A_to_B endpoints; otherwise they route, never disappear.",
          "An elapsed segment may contain private, AHJ, utility, or idle time; mixed segments are not attributed to one agency.",
          "Unknown AHJ remains unknown even when county candidates exist; geography is metadata, not a point assignment.",
          "Independent report errors remain the V6 default. joint_duration_reports requires a separately reviewed shared-error sensitivity declaration.",
          "Current collapsed_single_phase_quadrature is ineligible for repeated same-case observations; ordinary native case coordinates are required."
        ])
    (args.out / "route_accounting.json").write_text(json.dumps(accounting, indent=2) + "\n")


if __name__ == "__main__":
    main()
