import copy
import math

import numpy as np
import pytest

from pipeline.procbench.process_structure.occupancy import (
    Config, Evidence, conditional_presence, fit, joint_count_summary,
)


def fixture(observations=()):
    refs = [{"path": "source_free_fixture", "sha256": "0" * 64, "locator": "test"}]
    rows = [dict(jurisdiction_id="A", step_id="interview", source_type="forum",
                 unit_id=f"case{i}", dependence_group_id=f"case{i}",
                 detected=value, reviewed_scope=True,
                 evidence_refs=[dict(refs[0], locator=f"reading_{i}")])
            for i, value in enumerate(observations)]
    return dict(schema_version="process-occupancy-evidence/1", scope="source-free test only",
                jurisdictions=["A"], steps=["interview"], source_types=["forum"],
                source_models={"forum": {"detection_beta": [2., 2.],
                                          "false_positive_probability": .1}},
                opportunity_frame="reviewed_units_not_selected_for_step_mentions",
                conditional_independence="assumed_given_presence_and_source_type_detection",
                assumption_note="Source-free independent reading opportunities.",
                observations=rows, known_presence=[])


def test_missing_source_is_no_evidence_not_nondetection():
    e = Evidence(fixture())
    logit = math.log(.7/.3)
    assert conditional_presence([[logit]], [[.9]], e)[0, 0] == pytest.approx(.7)
    assert e.support_report()["reading_opportunities"] == 0


def test_nondetection_uses_detection_probability_not_hard_absence():
    e = Evidence(fixture([False]))
    for p in [.1, .8]:
        expected = .5*(1-p) / (.5*(1-p) + .5*.9)
        assert conditional_presence([[0]], [[p]], e)[0, 0] == pytest.approx(expected)
        assert expected > 0


def test_positive_detection_is_not_certain_with_false_positive_error():
    e = Evidence(fixture([True]))
    assert conditional_presence([[0]], [[.8]], e)[0, 0] == pytest.approx(.8/.9)


def test_zero_error_positive_detection_implies_presence():
    data = fixture([True])
    data["source_models"]["forum"]["false_positive_probability"] = 0.
    assert conditional_presence([[0]], [[.8]], Evidence(data))[0, 0] == 1.


def test_repeated_opportunities_multiply_only_after_dependency_check():
    data = fixture([True, False])
    assert conditional_presence([[0]], [[.8]], Evidence(data))[0, 0] == pytest.approx(.16/(.16+.09))
    data["observations"][1]["dependence_group_id"] = "case0"
    with pytest.raises(ValueError, match="Dependent"):
        Evidence(data)


def test_anchors_require_independent_explicit_support():
    data = fixture([True])
    data["known_presence"] = [dict(jurisdiction_id="A", step_id="interview", unit_id="independent_inventory",
                                    present=False, basis="explicit_absence",
                                    evidence_refs=[dict(data["observations"][0]["evidence_refs"][0], locator="independent_truth")])]
    assert conditional_presence([[0]], [[.8]], Evidence(data))[0, 0] == 0
    data["source_models"]["forum"]["false_positive_probability"] = 0.
    with pytest.raises(ValueError, match="contradicts"):
        Evidence(data)
    data["source_models"]["forum"]["false_positive_probability"] = .1
    data["known_presence"][0]["unit_id"] = "case0"
    with pytest.raises(ValueError, match="reused"):
        Evidence(data)


def test_anchor_cannot_reuse_same_source_under_new_unit_id():
    data = fixture([True])
    data["known_presence"] = [dict(jurisdiction_id="A", step_id="interview", unit_id="new_id_same_source",
                                    present=True, basis="explicit_presence",
                                    evidence_refs=data["observations"][0]["evidence_refs"])]
    with pytest.raises(ValueError, match="reuse detection source"):
        Evidence(data)


def test_changing_group_name_cannot_duplicate_reading_unit():
    data = fixture([True, False])
    data["observations"][1]["unit_id"] = "case0"
    with pytest.raises(ValueError, match="cannot change"):
        Evidence(data)


def test_renaming_unit_and_group_cannot_duplicate_quote_support():
    data = fixture([True, True])
    data["observations"][1]["evidence_refs"] = data["observations"][0]["evidence_refs"]
    with pytest.raises(ValueError, match="renamed reading units"):
        Evidence(data)


@pytest.mark.parametrize("field,value", [("jurisdiction_id", None), ("step_id", "unmapped"),
                                         ("detected", 1), ("reviewed_scope", False)])
def test_unresolved_or_unreviewed_observation_rejected(field, value):
    data = fixture([True])
    data["observations"][0][field] = value
    with pytest.raises(ValueError):
        Evidence(data)


def test_one_shared_document_cannot_multiply_across_counties():
    data = fixture([True])
    data["jurisdictions"].append("B")
    other = copy.deepcopy(data["observations"][0])
    other["jurisdiction_id"] = "B"
    data["observations"].append(other)
    with pytest.raises(ValueError, match="replicated"):
        Evidence(data)


@pytest.mark.parametrize("kw", [dict(chains=1), dict(draws=7), dict(warmup=True),
                              dict(step_logit_sd=0), dict(jurisdiction_scale_log_sd=-1)])
def test_invalid_sampler_configuration(kw):
    with pytest.raises(ValueError):
        Config(**kw)


def test_gibbs_ess_matches_exact_one_cell_marginal_and_retains_joint_counts():
    # Symmetric Gaussian logits imply prior Pr(z=1)=1/2 even with a random
    # jurisdiction scale. Integrating p~Beta(2,2), E[p(1-p)]=1/5. Thus two
    # readings (one positive, one negative) give P(z=1)=.2/(.2+.1*.9).
    data = fixture([True, False])
    expected = .2/(.2+.09)
    result, draws = fit(data, Config(warmup=250, draws=1200, seed=483))
    assert result["presence_probability"][0][0] == pytest.approx(expected, abs=.035)
    assert draws["presence"].mean() == pytest.approx(expected, abs=.035)
    np.testing.assert_array_equal(draws["step_count"], draws["presence"].sum(axis=-1))
    assert np.isfinite(draws["detection"]).all()
    assert result["support"]["reviewed_nondetections"] == 1
    assert not result.get("scientific_validation_complete", False)


def test_deterministic_seed_and_hard_anchor():
    data = fixture([False])
    data["known_presence"] = [dict(jurisdiction_id="A", step_id="interview", unit_id="independent_inventory",
                                    present=True, basis="explicit_presence",
                                    evidence_refs=[dict(data["observations"][0]["evidence_refs"][0], locator="independent_truth")])]
    cfg = Config(chains=2, warmup=4, draws=8)
    first, a = fit(data, cfg)
    second, b = fit(data, cfg)
    assert first == second
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
    assert np.all(a["presence"] == 1)
    assert not first["numerically_usable"]  # Tiny unit-test draw budget, no waived gate.


def test_count_intervals_stay_integer_and_probability_mass_is_joint():
    result = joint_count_summary([[0, 2], [0, 2]], 2)
    assert result["mean"] == 1
    assert result["median"] == 0
    assert result["ci90"] == [0, 2]
    assert result["empirical_posterior_count_mass"] == {"0": .5, "1": 0., "2": .5}
