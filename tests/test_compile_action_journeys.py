import json
import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.case_local_likelihood import case_update_views
from pipeline.procbench.solar_panel.compile_action_journeys import compile_packets


def event(ident, date):
    return {"event_id": ident, "event_type": ident, "occurrence": 1, "date": date,
            "date_lower": None, "date_upper": None,
            "actor": {"kind": "unknown", "id": None}, "refs": [ident]}


def operation(ident, action, start, end, occurrence, predecessors=()):
    return {"operation_id": ident, "action_id": action, "occurrence": occurrence,
            "actor": {"kind": "ahj", "id": "example_ahj"},
            "start_event_id": start, "end_event_id": end, "status": "performed",
            "component_kind": "action_cycle",
            "predecessor_operation_ids": list(predecessors), "refs": [ident]}


def observation(ident, operations, relation="independent_report"):
    return {"observation_id": ident, "start_event_id": "submitted",
            "end_event_id": "passed", "lower": 4, "upper": 6,
            "time_unit": "calendar_days", "observation_kind": "completed_interval",
            "operation_ids": operations, "evidence_relation": relation,
            "refs": [ident], "interpretation": "reviewed fixture"}


def write_packet(path, journeys):
    path.write_text(json.dumps({"schema_version": "solar-reviewed-action-journeys/1",
        "adoption_state": "staged", "source_bindings": [], "journeys": journeys}))


def test_adu_namespace_reuses_graph_and_likelihood_without_solar_provenance(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("passed", None)],
        "operations": [operation("review", "plan_review", "submitted", "passed", 1)],
        "observations": [observation("measured", ["review"])], "route_alternatives": None}
    path = tmp_path / "packet.json"
    write_packet(path, [journey])
    solar, _ = compile_packets([path])
    packet = json.loads(path.read_text())
    packet["schema_version"] = "adu-reviewed-action-journeys/1"
    path.write_text(json.dumps(packet))
    with pytest.raises(ValueError, match="schema"):
        compile_packets([path])
    adu, receipt = compile_packets([path], domain="adu")
    assert receipt["schema_version"] == "adu-action-journey-compilation/1"
    assert adu["programs"][0]["id"].startswith("adu_action_journey__")
    assert adu["programs"][0]["observations"][0]["source_family"] == "adu_reviewed_action_journeys"
    left = VisitHierarchy(solar, Config(modeled_channels=("elapsed",)))
    right = VisitHierarchy(adu, Config(modeled_channels=("elapsed",)))
    assert left.layout.size == right.layout.size
    state, routes = np.zeros(left.layout.size), np.zeros(1, dtype=int)
    assert left.log_likelihood_reference(state, routes) == right.log_likelihood_reference(state, routes)


def test_linked_packets_merge_same_day_events_and_materialized_repeats(tmp_path):
    base = {"journey_id": "j1", "canonical_case_id": "case_a",
        "same_installation_aliases": ["case_alias"], "lifecycle_stage": "completed",
        "source_threads": ["thread1"], "geography": {"scope": "county_candidates_provided",
            "county_weights": [{"county": "Example", "weight": .5, "basis": "reviewed"}],
            "unassigned_mass": .5, "basis": "reviewed fixture"},
        "events": [event("submitted", "2025-01-01"), event("notice", "2025-01-01")],
        "operations": [operation("review_1", "plan_review", "submitted", "notice", 1)],
        "observations": [], "route_alternatives": None}
    later = {"journey_id": "j2", "canonical_case_id": "case_alias",
        "same_installation_aliases": [], "lifecycle_stage": "completed",
        "source_threads": ["thread2"], "geography": {"scope": "unresolved_or_other_scope",
            "county_weights": [], "unassigned_mass": 1., "basis": "unknown"},
        "events": [event("resubmitted", "2025-01-02"), event("passed", "2025-01-05")],
        "operations": [
            operation("resubmit_1", "plan_resubmission", "notice", "resubmitted", 1, ["review_1"]),
            operation("review_2", "plan_review", "resubmitted", "passed", 2, ["resubmit_1"])],
        "observations": [observation("elapsed", ["review_1", "resubmit_1", "review_2"])],
        "route_alternatives": None}
    later["observations"][0]["measurement_basis"] = "sum_of_cycle_times"
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    write_packet(first, [base]); write_packet(second, [later])
    data, receipt = compile_packets([first, second])
    assert receipt["compiled_programs"] == 1
    program = data["programs"][0]
    assert program["journey_context"]["canonical_case_id"] == "case_a"
    assert len(program["routes"][0]["operations"]) == 3
    assert {o["task_type"] for o in program["routes"][0]["operations"]} == {
        "plan_review", "plan_resubmission"}
    assert program["observations"][0]["operators"][0]["basis"] == "sum_visit_cycles"
    assert len(program["journey_context"]["geography_evidence"]) == 2
    assert len(program["journey_context"]["reviewed_event_declarations"]) == 4
    assert {x["status"] for x in program["journey_context"]["reviewed_operation_declarations"]} == {"performed"}


def test_reconstruction_routes_without_duplicate_likelihood(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", "2025-01-01"), event("passed", "2025-01-02")],
        "operations": [operation("review", "plan_review", "submitted", "passed", 1)],
        "observations": [observation("measured", ["review"]),
            observation("total_reconstructed", ["review"], "derived_reconstruction")],
        "route_alternatives": None}
    path = tmp_path / "packet.json"; write_packet(path, [journey])
    data, receipt = compile_packets([path])
    assert [o["id"] for o in data["programs"][0]["observations"]] == ["measured"]
    assert any(r["route"] == "derived_reconstruction" for r in receipt["routes"])


def test_explicit_activity_event_interval_is_emitted_without_endpoint_inference(tmp_path):
    row = observation("span", ["review", "issue"])
    row["activity_event_interval"] = {
        "start": {"operation_id": "review", "event": "start", "occurrence": "first"},
        "end": {"operation_id": "issue", "event": "end", "occurrence": "last"}}
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", "2025-01-01"), event("reviewed", "2025-01-02"),
                   event("passed", "2025-01-05")],
        "operations": [operation("review", "plan_review", "submitted", "reviewed", 1),
                       operation("issue", "permit_issuance", "reviewed", "passed", 1, ["review"])],
        "observations": [row], "route_alternatives": None}
    path = tmp_path / "packet.json"; write_packet(path, [journey])
    data, _ = compile_packets([path])
    operator = data["programs"][0]["observations"][0]["operators"][0]
    assert operator == {"basis": "activity_event_interval",
        "start": {"activity_id": "review", "event": "start", "occurrence": "first"},
        "end": {"activity_id": "issue", "event": "end", "occurrence": "last"}}


def test_shared_event_requires_native_predecessor_binding(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("reviewed", None), event("passed", None)],
        "operations": [operation("review", "plan_review", "submitted", "reviewed", 1),
                       operation("issue", "permit_issuance", "reviewed", "passed", 1)],
        "observations": [observation("span", ["review"])], "route_alternatives": None}
    path = tmp_path / "bad.json"; write_packet(path, [journey])
    import pytest
    with pytest.raises(ValueError, match="predecessors must exactly bind"):
        compile_packets([path])


def test_multi_operation_duration_requires_explicit_sum_basis(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("reviewed", None), event("passed", None)],
        "operations": [operation("review", "plan_review", "submitted", "reviewed", 1),
                       operation("issue", "permit_issuance", "reviewed", "passed", 1, ["review"])],
        "observations": [observation("span", ["review", "issue"])], "route_alternatives": None}
    path = tmp_path / "bad_sum.json"; write_packet(path, [journey])
    import pytest
    with pytest.raises(ValueError, match="sum_of_cycle_times"):
        compile_packets([path])


def test_multiple_producers_cannot_claim_one_completion_event(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("start_a", None), event("start_b", None), event("joined", None)],
        "operations": [operation("a", "private_work", "start_a", "joined", 1),
                       operation("b", "utility_work", "start_b", "joined", 1)],
        "observations": [observation("a_time", ["a"])], "route_alternatives": None}
    path = tmp_path / "bad_join.json"; write_packet(path, [journey])
    import pytest
    with pytest.raises(ValueError, match="one producer per semantic completion event"):
        compile_packets([path])


def test_mixed_elapsed_residual_cannot_be_attributed_to_actor(tmp_path):
    residual = operation("gap", "permit_to_install_unallocated_gap", "submitted", "passed", 1)
    residual["component_kind"] = "mixed_elapsed_residual"
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("passed", None)],
        "operations": [residual], "observations": [observation("gap_time", ["gap"])],
        "route_alternatives": None}
    path = tmp_path / "bad_residual.json"; write_packet(path, [journey])
    with pytest.raises(ValueError, match="unknown actor attribution"):
        compile_packets([path])


def test_compiled_legacy_journey_uses_exact_program_local_case_chunks(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("passed", None)],
        "operations": [operation("review", "plan_review", "submitted", "passed", 1)],
        "observations": [observation("elapsed", ["review"])], "route_alternatives": None}
    path = tmp_path / "legacy.json"; write_packet(path, [journey])
    data, _ = compile_packets([path])
    cfg = Config(modeled_channels=("elapsed",), population_size=16, chains=1,
                 warmup=1, draws=8, seed=991, case_update_block_size=1)
    model = VisitHierarchy(data, cfg)
    views = case_update_views(model)
    assert views and all(pi == 0 and view is None for pi, view in views.values())
    initial = (np.zeros((1, model.layout.size)), np.zeros((1, 1), dtype=int))
    states, routes, likelihood, _ = model.sample(initial=initial, case_local_updates=True)
    for j in range(cfg.draws):
        assert likelihood[0, j] == pytest.approx(
            model.log_likelihood_reference(states[0, j], routes[0, j]), abs=2e-11)


def test_reviewed_identity_aliases_change_native_pooling_not_original_declarations(tmp_path):
    journey = {"journey_id": "j", "canonical_case_id": "case", "same_installation_aliases": [],
        "lifecycle_stage": "completed", "source_threads": ["t"], "geography": None,
        "events": [event("submitted", None), event("passed", None)],
        "operations": [operation("review", "review_permit_application", "submitted", "passed", 1)],
        "observations": [observation("elapsed", ["review"])], "route_alternatives": None}
    packet = tmp_path / "journey.json"; write_packet(packet, [journey])
    aliases = tmp_path / "aliases.json"
    aliases.write_text(json.dumps({"schema_version": "solar-action-identity-aliases/1",
        "rationale": "reviewed equivalent actor/actions only",
        "action_ids": {"review_permit_application": "permit_plan_review"},
        "actor_ids": {"example_ahj": "ahj__example"}}))
    data, receipt = compile_packets([packet], aliases)
    native = data["programs"][0]["routes"][0]["operations"][0]
    assert native["task_type"] == "permit_plan_review" and native["actor_id"] == "ahj__example"
    original = data["programs"][0]["journey_context"]["reviewed_operation_declarations"][0]
    assert original["action_id"] == "review_permit_application"
    assert original["actor"]["id"] == "example_ahj"
    assert receipt["identity_aliases_binding"]["sha256"]
    assert {(x["identity_type"], x["original"], x["canonical"])
            for x in receipt["identity_alias_transformations"]} == {
                ("action_id", "review_permit_application", "permit_plan_review"),
                ("actor_id", "example_ahj", "ahj__example")}
