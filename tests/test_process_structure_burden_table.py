import numpy as np
import pytest

from pipeline.procbench.process_structure.burden_table import inventory_distribution, presence_only_table


def test_joint_inventory_is_not_product_of_marginals():
    z = np.array([[[0, 0], [1, 1]], [[0, 0], [1, 1]]])
    result = inventory_distribution(z, ["filing", "interview"])
    assert len(result) == 2
    assert [x["posterior_mass"] for x in result] == [.5, .5]
    assert [x["present_step_ids"] for x in result] == [[], ["filing", "interview"]]
    assert all(not x["v6_route_validated"] for x in result)


def test_unknown_burden_is_null_not_zero():
    posterior = {"schema_version": "process-occupancy-posterior/1", "numerically_usable": True,
                 "scientific_validation_complete": True, "scientific_release_eligible": True,
                 "steps": ["interview"], "jurisdictions": ["A"], "scope": "initial@2024",
                 "presence_probability": [[.8]]}
    row = presence_only_table(posterior, {"interview": {"layers": ["applicant"]}})["rows"][0]
    assert row["presence_probability"] == .8
    assert row["expected_rounds"] is None
    assert row["burden_shares_by_channel"] is None
    assert row["elapsed_time"]["posterior"] is None
    posterior["numerically_usable"] = False
    with pytest.raises(ValueError):
        presence_only_table(posterior, {"interview": {}})


def test_missing_step_metadata_cannot_drop_an_uncomfortable_step():
    posterior = {"schema_version": "process-occupancy-posterior/1", "numerically_usable": True,
                 "scientific_validation_complete": True, "scientific_release_eligible": True,
                 "steps": ["interview"], "jurisdictions": ["A"], "scope": "initial@2024",
                 "presence_probability": [[.8]]}
    with pytest.raises(ValueError):
        presence_only_table(posterior, {})
