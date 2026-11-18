from pipeline.procbench.process_structure.solar_forum_bridge import BLOCK, _route_reviewed_packet


def _episode(episode_id, scope_kind, reviewed, detected):
    return {
        "episode_id": episode_id,
        "occurrence_reviewed": True,
        "statistic": "individual",
        "reading_scope_kind": scope_kind,
        "reviewed_step_ids": reviewed,
        "step_scope_reviewed": True,
        "step_scope_rationale": "Reviewer explicitly checked only the declared action support.",
        "readings": [
            {"step_id": step, "detected": step in detected,
             "quotes": [{"quote": "held"}] if step in detected else []}
            for step in reviewed
        ],
    }


def test_legacy_full_and_reviewed_subset_keep_only_declared_opportunities():
    subset = [BLOCK[0], BLOCK[2], BLOCK[6]]
    packet = {"episodes": [
        _episode("full", "complete_fixed_universe", BLOCK, {BLOCK[6]}),
        _episode("subset", "reviewed_fixed_subset", subset, {BLOCK[2]}),
    ]}
    filtered, routes = _route_reviewed_packet(packet)
    assert [row["episode_id"] for row in filtered["episodes"]] == ["full", "subset"]
    assert [row["reviewed_step_ids"] for row in routes] == [BLOCK, subset]
    assert [row["reason"] for row in routes] == [
        "legacy_complete_fixed_universe", "explicit_reviewed_fixed_subset"]
    assert sum(len(row["readings"]) for row in filtered["episodes"]) == len(BLOCK) + len(subset)


def test_positive_only_episode_is_descriptive_not_an_occupancy_trial():
    episode = _episode("positive", "positive_only_descriptive", [BLOCK[6]], {BLOCK[6]})
    filtered, routes = _route_reviewed_packet({"episodes": [episode]})
    assert filtered["episodes"] == []
    assert routes == [{
        "episode_id": "positive",
        "disposition": "descriptive_only",
        "reason": "positive_only_or_nonopportunity_scope_no_occupancy_likelihood",
        "reviewed_step_ids": [BLOCK[6]],
        "explicit_unresolved_jurisdiction_mass": None,
    }]


def test_explicit_unresolved_geography_mass_is_not_renormalized_away():
    episode = _episode("unknown_mass", "reviewed_fixed_subset", [BLOCK[6]], {BLOCK[6]})
    episode["candidate_unresolved_mass"] = 0.35
    filtered, routes = _route_reviewed_packet({"episodes": [episode]})
    assert filtered["episodes"] == []
    assert routes[0]["reason"] == "explicit_unresolved_geography_mass_not_representable_without_silent_normalization"
    assert routes[0]["explicit_unresolved_jurisdiction_mass"] == 0.35

    fully_unresolved = _episode("fully_unknown", "reviewed_fixed_subset", [BLOCK[6]], {BLOCK[6]})
    fully_unresolved["candidate_unresolved_mass"] = 1.0
    filtered, routes = _route_reviewed_packet({"episodes": [fully_unresolved]})
    assert filtered["episodes"] == []
    assert routes[0]["explicit_unresolved_jurisdiction_mass"] == 1.0


def _fallback(candidates):
    return {
        "schema_version": "unresolved-identity-fallback/1",
        "assumption_label": "declared regional sensitivity q; not inferred from this episode",
        "independence_declaration": "source_independent_of_episode_action_and_timing",
        "source_refs": [{"path": "held/frame.json", "sha256": "a" * 64,
                         "locator": "$.declared_fallback_q"}],
        "candidates": candidates,
    }


def test_opt_in_unresolved_mixture_preserves_named_and_unknown_mass():
    episode = _episode("mixed", "reviewed_fixed_subset", [BLOCK[6]], {BLOCK[6]})
    episode.update(
        candidate_unresolved_mass=.5,
        candidates=[{"jurisdiction_id": "named", "prior_weight": 1}],
        unresolved_identity_fallback=_fallback([
            {"jurisdiction_id": "fallback_a", "prior_weight": 1},
            {"jurisdiction_id": "fallback_b", "prior_weight": 3},
        ]),
    )
    filtered, routes = _route_reviewed_packet({"episodes": [episode]})
    weights = {row["jurisdiction_id"]: row["prior_weight"]
               for row in filtered["episodes"][0]["candidates"]}
    assert weights == {"fallback_a": .125, "fallback_b": .375, "named": .5}
    assert routes[0]["reason"] == "explicit_unresolved_identity_mixture"
    assert filtered["episodes"][0]["unresolved_identity_mixture"]["named_mass"] == .5


def test_fully_unresolved_uses_only_declared_fallback_not_point_default():
    episode = _episode("unknown", "reviewed_fixed_subset", [BLOCK[6]], {BLOCK[6]})
    episode.update(
        candidate_unresolved_mass=1.0,
        candidates=[],
        unresolved_identity_fallback=_fallback([
            {"jurisdiction_id": "a", "prior_weight": 2},
            {"jurisdiction_id": "b", "prior_weight": 1},
        ]),
    )
    filtered, routes = _route_reviewed_packet({"episodes": [episode]})
    weights = {row["jurisdiction_id"]: row["prior_weight"]
               for row in filtered["episodes"][0]["candidates"]}
    assert weights == {"a": 2 / 3, "b": 1 / 3}
    assert routes[0]["explicit_unresolved_jurisdiction_mass"] == 1.0
