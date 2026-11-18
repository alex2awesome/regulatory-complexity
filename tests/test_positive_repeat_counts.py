import copy
import math

import numpy as np
import pytest
from scipy.integrate import quad

from pipeline.procbench.positive_repeat_counts import (
    log_probability,
    validate_positive_repeat_counts,
)


def source():
    return {
        "path": "captured/source.md",
        "sha256": "a" * 64,
        "quote_segments": ["redoing paperwork THREE times"],
    }


def row(**changes):
    result = {
        "id": "count-1",
        "family_id": "paperwork_redo_or_resubmission",
        "family_definition": "Additional paperwork redo or resubmission actions in one completed episode.",
        "attachment": "count_only",
        "count": 3,
        "case_id": "case-1",
        "evidence_group_id": "episode-1",
        "source_family": "forum_completed_positive",
        "episode_complete": True,
        "exact_count_assumption": True,
        "ascertainment": "completed_positive_episode",
        "reporting_assumption": "Fixed sensitivity within positive completed forum reports; no population denominator.",
        "source_bound": [source()],
        "severity_selection": {
            "id": "threshold3-no-tilt",
            "threshold": 3,
            "log_tilt": 0.0,
            "fixed_not_estimated": True,
        },
    }
    result.update(changes)
    return result


def test_positive_law_normalizes_independently_of_hurdle_probability():
    for r in (0.0, 0.01, 0.2, 0.8, 0.99):
        probabilities = np.exp([log_probability(k, r) for k in range(1, 20001)])
        assert probabilities.sum() == pytest.approx(1.0, abs=2e-12)
    # The function has no q argument: conditioning has removed the hurdle.
    assert log_probability(3, 0.4) == pytest.approx(math.log(0.6) + 2 * math.log(0.4))


def test_boundaries_are_exact_and_not_clipped():
    assert log_probability(1, 0.0) == 0.0
    assert log_probability(2, 0.0) == -math.inf
    assert log_probability(1, 1.0) == -math.inf
    assert log_probability(100, 1.0, 1e300, 3) == -math.inf
    # With threshold one, all positive counts receive the same tilt, so it cancels.
    assert log_probability(1, 0.0, 1e300, 1) == 0.0
    assert log_probability(4, 0.3, 1e300, 1) == pytest.approx(log_probability(4, 0.3))


@pytest.mark.parametrize("relative_rate", [1.0, 2.0, 10.0])
def test_fixed_threshold_three_severity_sensitivities_normalize(relative_rate):
    tilt = math.log(relative_rate)
    for r in (0.05, 0.4, 0.9):
        mass = sum(math.exp(log_probability(k, r, tilt, 3)) for k in range(1, 10000))
        assert mass == pytest.approx(1.0, abs=2e-12)
        expected_log_z = math.log1p((relative_rate - 1.0) * r**2)
        observed_correction = (math.log1p(-r) + 2 * math.log(r) + tilt
                               - log_probability(3, r, tilt, 3))
        assert observed_correction == pytest.approx(expected_log_z)


def test_large_finite_tilt_stays_finite_on_supported_counts():
    for r in (1e-12, 0.2, 1 - 1e-12):
        values = [log_probability(k, r, 1e300, 3) for k in (1, 2, 3, 10)]
        assert all(math.isfinite(value) for value in values)
        assert all(value <= 0 for value in values)


def test_k3_with_beta_2_3_prior_recovers_beta_4_4_posterior():
    # Independent numerical integration: prior r^(2-1)(1-r)^(3-1) times the
    # K=3 positive likelihood (1-r)r^2 has Beta(4,4) moments.
    def unnormalized(r):
        return r ** (2 - 1) * (1 - r) ** (3 - 1) * math.exp(log_probability(3, r))

    normalizer = quad(unnormalized, 0, 1, epsabs=1e-13)[0]
    mean = quad(lambda r: r * unnormalized(r), 0, 1, epsabs=1e-13)[0] / normalizer
    second = quad(lambda r: r * r * unnormalized(r), 0, 1, epsabs=1e-13)[0] / normalizer
    assert mean == pytest.approx(4 / 8)
    assert second - mean**2 == pytest.approx(4 * 4 / (8**2 * 9))


def test_validator_returns_deep_copy_and_documented_family_summary():
    original = row()
    result = validate_positive_repeat_counts([original], [], [], [])
    assert result["schema_version"] == "positive-repeat-count-observations/1"
    assert result["rows"][0] == original
    assert result["rows"][0] is not original
    assert result["rows"][0]["source_bound"] is not original["source_bound"]
    assert result["families"] == [{
        "id": "paperwork_redo_or_resubmission",
        "attachment": "count_only",
        "definition": original["family_definition"],
        "source_family": original["source_family"],
        "reporting_assumption": original["reporting_assumption"],
        "severity_selection": original["severity_selection"],
        "row_ids": ["count-1"],
        "case_ids": ["case-1"],
        "evidence_group_ids": ["episode-1"],
    }]
    original["source_bound"][0]["quote_segments"][0] = "mutated"
    assert result["rows"][0]["source_bound"][0]["quote_segments"][0] != "mutated"


def test_validator_accepts_multiple_distinct_rows_only_under_same_family_contract():
    second = row(id="count-2", case_id="case-2", evidence_group_id="episode-2",
                 source_bound=[dict(source(), quote_segments=["redo twice"])])
    result = validate_positive_repeat_counts([row(), second], [], [], [])
    assert len(result["rows"]) == 2
    assert result["families"][0]["row_ids"] == ["count-1", "count-2"]


@pytest.mark.parametrize("field,value", [
    ("count", True),
    ("count", 0),
    ("count", 1.5),
    ("episode_complete", False),
    ("exact_count_assumption", False),
    ("ascertainment", "unselected"),
    ("attachment", "route_backed"),
])
def test_validator_rejects_nonpositive_inexact_or_wrongly_selected_rows(field, value):
    with pytest.raises(ValueError):
        validate_positive_repeat_counts([row(**{field: value})], [], [], [])


@pytest.mark.parametrize("option", [
    "sampling", "duration_selected", "report_error", "count_error_scale", "lower",
    "operator", "repeat_key",
])
def test_validator_rejects_duration_selection_reporting_error_and_route_options(option):
    candidate = row()
    candidate[option] = "forbidden"
    with pytest.raises(ValueError, match="forbids selection/report-error"):
        validate_positive_repeat_counts([candidate], [], [], [])


def test_validator_rejects_executable_family_and_any_cross_factor_overlap():
    with pytest.raises(ValueError, match="executable repeat key"):
        validate_positive_repeat_counts([row()], ["paperwork_redo_or_resubmission"], [], [])
    with pytest.raises(ValueError, match="case overlaps"):
        validate_positive_repeat_counts([row()], [], ["case-1"], [])
    with pytest.raises(ValueError, match="group overlaps"):
        validate_positive_repeat_counts([row()], [], [], ["episode-1"])


def test_validator_rejects_duplicate_case_group_or_row_identity():
    for changes, match in (
        ({"id": "count-1", "case_id": "case-2", "evidence_group_id": "episode-2"}, "IDs"),
        ({"id": "count-2", "case_id": "case-1", "evidence_group_id": "episode-2"}, "case overlaps"),
        ({"id": "count-2", "case_id": "case-2", "evidence_group_id": "episode-1"}, "group overlaps"),
    ):
        with pytest.raises(ValueError, match=match):
            validate_positive_repeat_counts([row(), row(**changes)], [], [], [])


def test_family_rows_must_share_definition_provenance_and_fixed_sensitivity():
    changes = (
        {"family_definition": "different"},
        {"source_family": "different-source"},
        {"reporting_assumption": "different assumption"},
        {"severity_selection": dict(row()["severity_selection"], log_tilt=math.log(2))},
    )
    for change in changes:
        second = row(id="count-2", case_id="case-2", evidence_group_id="episode-2", **change)
        with pytest.raises(ValueError, match="share definition and provenance"):
            validate_positive_repeat_counts([row(), second], [], [], [])


def test_source_and_fixed_severity_declarations_are_fail_closed():
    bad_source = source()
    bad_source["sha256"] = "not-a-digest"
    with pytest.raises(ValueError, match="SHA-256"):
        validate_positive_repeat_counts([row(source_bound=[bad_source])], [], [], [])
    with pytest.raises(ValueError, match="fixed and not estimated"):
        validate_positive_repeat_counts([row(severity_selection={
            "id": "learned", "threshold": 3, "log_tilt": 0.0,
            "fixed_not_estimated": False,
        })], [], [], [])


@pytest.mark.parametrize("arguments", [
    (0, 0.2, 0.0, 3),
    (True, 0.2, 0.0, 3),
    (1, -0.1, 0.0, 3),
    (1, 1.1, 0.0, 3),
    (1, 0.2, -1.0, 3),
    (1, 0.2, math.inf, 3),
    (1, 0.2, 0.0, 0),
])
def test_log_probability_rejects_invalid_inputs(arguments):
    with pytest.raises(ValueError):
        log_probability(*arguments)


def test_empty_optional_contract_is_well_formed():
    assert validate_positive_repeat_counts([], [], [], []) == {
        "schema_version": "positive-repeat-count-observations/1",
        "rows": [],
        "families": [],
    }
