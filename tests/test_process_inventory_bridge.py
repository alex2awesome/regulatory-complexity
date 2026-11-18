import copy
import json

import numpy as np
import pytest

from pipeline.procbench.joint_inventory_prior import (
    JointInventoryPrior,
    empirical_joint_inventory,
    replay_upstream_indices,
)
from pipeline.procbench.process_structure.inventory_bridge import (
    build_inventory_bridge,
    inventory_fingerprints,
    replay_inventory_bridge,
)


def empirical_fixture():
    state_a = [[0, 0]]
    state_b = [[0, 1]]
    state_c = [[1, 1]]
    draws = np.array([
        [state_a, state_b, state_b],
        [state_a, state_c, state_b],
    ])
    return empirical_joint_inventory(draws, ["county_a"], ["step_1", "step_2"])


def reviewed_vectors(empirical):
    rows = []
    for record, inventory in zip(
        inventory_fingerprints(empirical), empirical["joint_inventories"]
    ):
        # The first two distinct JxS inventories intentionally compile to the
        # same downstream route. This decision is fixture input, not inferred
        # by the bridge.
        route = "route_1" if int(np.asarray(inventory).sum()) == 2 else "route_0"
        rows.append({
            **record,
            "route_ids": [route],
            "route_vector_reviewed": True,
            "review_note": "Source-free explicit fixture route decision.",
            "review_refs": [{"path": "source-free/routes.json", "locator": f"$[{record['raw_inventory_index']}]"}],
            "review_metadata": {"reviewer": "independent_fixture", "real_source": False},
        })
    return rows


def build(empirical=None, vectors=None, **kwargs):
    empirical = empirical_fixture() if empirical is None else empirical
    vectors = reviewed_vectors(empirical) if vectors is None else vectors
    return build_inventory_bridge(
        empirical,
        vectors,
        ["county_program"],
        evidence_partition_reviewed=True,
        evidence_partition_note="Source-free disjoint fixture evidence.",
        route_semantics_reviewed=True,
        route_semantics_note="Every raw fixture inventory was manually assigned a route.",
        **kwargs,
    )


def test_many_to_one_bridge_aggregates_routes_and_preserves_every_draw():
    empirical = empirical_fixture()
    bridge = build(empirical)

    assert bridge["raw_inventory_count"] == 3
    assert bridge["downstream_hypothesis_count"] == 2
    assert bridge["original_inventory_to_downstream"] == [0, 0, 1]
    assert [row["supplied_draw_count"] for row in bridge["hypotheses"]] == [5, 1]
    assert [row["prior_weight"] for row in bridge["joint_inventory_prior"]["hypotheses"]] == [5, 1]
    remapped = np.asarray(bridge["remapped_upstream_draw_to_hypothesis"])
    np.testing.assert_array_equal(
        remapped,
        np.asarray(bridge["original_inventory_to_downstream"])[
            empirical["upstream_draw_to_inventory"]
        ],
    )
    assert remapped.size == empirical["upstream_draw_to_inventory"].size
    assert bridge["retained_mass"] == 1
    assert bridge["scientific_validation_complete"] is False
    assert bridge["raw_inventories"][0]["review_note"].startswith("Source-free")
    assert bridge["raw_inventories"][0]["reviewed_route_mapping"]["review_refs"][0][
        "path"
    ] == "source-free/routes.json"
    assert bridge["raw_inventories"][0]["reviewed_route_mapping"][
        "review_metadata"
    ] == {"reviewer": "independent_fixture", "real_source": False}
    json.dumps(bridge, allow_nan=False)
    compiled = JointInventoryPrior(
        bridge["joint_inventory_prior"],
        [{
            "id": "county_program",
            "routes": [
                {"id": "route_0", "prior_weight": 1.0},
                {"id": "route_1", "prior_weight": 1.0},
            ],
        }],
    )
    assert compiled.names == bridge["hypothesis_ids"]
    np.testing.assert_allclose(compiled.probabilities, [5 / 6, 1 / 6])


def compiled_prior(bridge):
    return JointInventoryPrior(
        bridge["joint_inventory_prior"],
        [{
            "id": "county_program",
            "routes": [
                {"id": "route_0", "prior_weight": 1.0},
                {"id": "route_1", "prior_weight": 1.0},
            ],
        }],
    )


def test_replay_must_use_compiler_remapped_membership_after_many_to_one_mapping():
    empirical = empirical_fixture()
    bridge = build(empirical)
    raw = empirical["upstream_draw_to_inventory"]
    mapped = np.asarray(bridge["remapped_upstream_draw_to_hypothesis"])
    selected = np.zeros((2, 2000), dtype=int)

    wrong = replay_upstream_indices(raw, selected, np.random.default_rng(101))
    correct = replay_upstream_indices(mapped, selected, np.random.default_rng(101))

    # Raw index zero represents only one of the two inventories that compile to
    # route_0, so direct replay silently excludes raw inventory one.
    assert set(raw.ravel()[wrong].ravel()) == {0}
    assert set(raw.ravel()[correct].ravel()) == {0, 1}
    assert set(mapped.ravel()[correct].ravel()) == {0}


def test_supplied_downstream_order_controls_exact_hypothesis_indices():
    empirical = empirical_fixture()
    declaration = {
        "schema_version": "v6-joint-inventory-prior/1",
        "program_ids": ["county_program"],
        "feedback_policy": "downstream_evidence_updates_joint_inventory",
        "evidence_partition_reviewed": True,
        "evidence_partition_note": "Source-free disjoint fixture evidence.",
        "route_semantics_reviewed": True,
        "hypotheses": [
            {"id": "rare_route", "prior_weight": 1, "route_ids": ["route_1"]},
            {"id": "common_route", "prior_weight": 5, "route_ids": ["route_0"]},
        ],
    }
    bridge = build(empirical, downstream_declaration=declaration)

    assert bridge["hypothesis_ids"] == ["rare_route", "common_route"]
    assert bridge["original_inventory_to_downstream"] == [1, 1, 0]
    assert [row["supplied_draw_count"] for row in bridge["hypotheses"]] == [1, 5]
    assert bridge["joint_inventory_prior"] == declaration


def test_scaled_supplied_weights_are_validated_without_overflow():
    empirical = empirical_fixture()
    declaration = build(empirical)["joint_inventory_prior"]
    declaration["hypotheses"][0]["prior_weight"] = 1e308
    declaration["hypotheses"][1]["prior_weight"] = 2e307

    bridge = build(empirical, downstream_declaration=declaration)

    assert bridge["joint_inventory_prior"]["hypotheses"][0]["prior_weight"] == 1e308
    np.testing.assert_allclose(compiled_prior(bridge).probabilities, [5 / 6, 1 / 6])


def test_weight_normalization_fails_closed_if_positive_support_underflows():
    empirical = empirical_fixture()
    declaration = build(empirical)["joint_inventory_prior"]
    declaration["hypotheses"][0]["prior_weight"] = 1e308
    declaration["hypotheses"][1]["prior_weight"] = np.nextafter(0.0, 1.0)
    with pytest.raises(ValueError, match="lose positive support"):
        build(empirical, downstream_declaration=declaration)


def test_safe_replay_uses_mapped_memberships_and_one_full_upstream_particle():
    empirical = empirical_fixture()
    bridge = build(empirical)
    prior = compiled_prior(bridge)
    structures = np.broadcast_to(prior.states[0], (2, 1000, 1)).copy()

    replay = replay_inventory_bridge(bridge, prior, structures, np.random.default_rng(771))

    raw = empirical["upstream_draw_to_inventory"].ravel()
    indices = replay["upstream_flat_indices"]
    assert set(raw[indices].ravel()) == {0, 1}
    np.testing.assert_array_equal(replay["downstream_hypothesis_indices"], 0)
    report = replay["empirical_bridge_report"]
    assert report["downstream_visited_joint_inventory_count"] == 1
    assert report["upstream_mass_on_unvisited_inventories"] == pytest.approx(1 / 6)


def test_safe_replay_respects_permuted_declaration_order():
    empirical = empirical_fixture()
    declaration = {
        "schema_version": "v6-joint-inventory-prior/1",
        "program_ids": ["county_program"],
        "feedback_policy": "downstream_evidence_updates_joint_inventory",
        "evidence_partition_reviewed": True,
        "evidence_partition_note": "Source-free disjoint fixture evidence.",
        "route_semantics_reviewed": True,
        "hypotheses": [
            {"id": "rare_route", "prior_weight": 1, "route_ids": ["route_1"]},
            {"id": "common_route", "prior_weight": 5, "route_ids": ["route_0"]},
        ],
    }
    bridge = build(empirical, downstream_declaration=declaration)
    prior = compiled_prior(bridge)
    structures = np.array([[prior.states[0], prior.states[1], prior.states[0]]])

    replay = replay_inventory_bridge(bridge, prior, structures, np.random.default_rng(8))

    np.testing.assert_array_equal(replay["downstream_hypothesis_indices"], [[0, 1, 0]])
    raw = empirical["upstream_draw_to_inventory"].ravel()
    selected_raw = raw[replay["upstream_flat_indices"]].ravel()
    assert selected_raw[0] == 2
    assert selected_raw[2] == 2
    assert selected_raw[1] in {0, 1}


@pytest.mark.parametrize("mutation,match", [
    ("membership_mass", "masses/order"),
    ("declared_count", "masses/order"),
    ("declaration", "declaration and ordered"),
    ("hypothesis_ids", "declaration and ordered"),
])
def test_safe_replay_rejects_tampered_bridge_mass_or_declaration(mutation, match):
    bridge = build()
    prior = compiled_prior(bridge)
    broken = copy.deepcopy(bridge)
    if mutation == "membership_mass":
        broken["remapped_upstream_draw_to_hypothesis"][0][0] = 1
    elif mutation == "declared_count":
        broken["hypotheses"][0]["supplied_draw_count"] -= 1
    elif mutation == "declaration":
        broken["joint_inventory_prior"]["hypotheses"][0]["id"] = "changed"
    else:
        broken["hypothesis_ids"][0] = "changed"
    structures = np.broadcast_to(prior.states[0], (1, 3, 1)).copy()
    with pytest.raises(ValueError, match=match):
        replay_inventory_bridge(broken, prior, structures, np.random.default_rng(9))


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing_mapping", "exactly one"),
        ("duplicate_mapping", "fingerprint-bound"),
        ("bad_fingerprint", "fingerprint-bound"),
        ("unreviewed_mapping", "fingerprint-bound"),
        ("empty_review_note", "fingerprint-bound"),
    ],
)
def test_route_mapping_must_cover_each_raw_inventory_once(mutation, match):
    empirical = empirical_fixture()
    rows = reviewed_vectors(empirical)
    if mutation == "missing_mapping":
        rows.pop()
    elif mutation == "duplicate_mapping":
        rows[-1]["raw_inventory_index"] = rows[0]["raw_inventory_index"]
    elif mutation == "bad_fingerprint":
        rows[0]["raw_inventory_sha256"] = "0" * 64
    elif mutation == "unreviewed_mapping":
        rows[0]["route_vector_reviewed"] = False
    else:
        rows[0]["review_note"] = ""
    with pytest.raises(ValueError, match=match):
        build(empirical, rows)


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("program_order", "mismatched program order"),
        ("missing_support", "missing or extra"),
        ("extra_support", "missing or extra"),
        ("duplicate_support", "aggregate duplicate"),
        ("wrong_weights", "weights"),
        ("boolean_weight", "positive finite"),
    ],
)
def test_supplied_declaration_must_exactly_match_aggregated_support(mutation, match):
    empirical = empirical_fixture()
    declaration = build(empirical)["joint_inventory_prior"]
    declaration = copy.deepcopy(declaration)
    if mutation == "program_order":
        declaration["program_ids"] = ["other_program"]
    elif mutation == "missing_support":
        declaration["hypotheses"].pop()
    elif mutation == "extra_support":
        declaration["hypotheses"].append(
            {"id": "extra", "prior_weight": 1, "route_ids": ["route_2"]}
        )
    elif mutation == "duplicate_support":
        declaration["hypotheses"].append(
            {"id": "duplicate", "prior_weight": 1, "route_ids": ["route_0"]}
        )
    elif mutation == "wrong_weights":
        declaration["hypotheses"][0]["prior_weight"] = 4
    else:
        declaration["hypotheses"][0]["prior_weight"] = True
    with pytest.raises(ValueError, match=match):
        build(empirical, downstream_declaration=declaration)


def test_empirical_probabilities_and_metadata_are_replayed_not_trusted():
    empirical = empirical_fixture()
    bad_probability = copy.deepcopy(empirical)
    bad_probability["probabilities"] = np.array([0.2, 0.3, 0.5])
    with pytest.raises(ValueError, match="draw frequencies"):
        build(bad_probability, reviewed_vectors(empirical))

    bad_scope = copy.deepcopy(empirical)
    bad_scope["retained_mass_scope"] = "continuous_posterior"
    with pytest.raises(ValueError, match="complete unreviewed supplied draw"):
        build(bad_scope, reviewed_vectors(empirical))


@pytest.mark.parametrize(
    "field,value",
    [
        ("evidence_partition_reviewed", False),
        ("evidence_partition_note", ""),
        ("route_semantics_reviewed", False),
        ("route_semantics_note", ""),
    ],
)
def test_review_attestations_are_explicit_but_labeled_as_nonproof(field, value):
    kwargs = dict(
        evidence_partition_reviewed=True,
        evidence_partition_note="Source-free disjoint fixture evidence.",
        route_semantics_reviewed=True,
        route_semantics_note="Every raw fixture inventory was manually assigned a route.",
    )
    kwargs[field] = value
    empirical = empirical_fixture()
    with pytest.raises(ValueError, match="attestations"):
        build_inventory_bridge(
            empirical,
            reviewed_vectors(empirical),
            ["county_program"],
            **kwargs,
        )

    bridge = build(empirical)
    assert "does not inspect sources" in bridge["attestations"]["attestation_scope"]
    assert "external" in bridge["qualification"]
