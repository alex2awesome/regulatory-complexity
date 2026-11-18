from pipeline.procbench.process_structure.occupancy import Evidence
import pytest

from pipeline.procbench.process_structure.solar_forum_bridge import BLOCK, compile_bridge, compile_reviewed_packet


def test_bridge_is_positive_only_and_keeps_weak_rows_in_coverage():
    data, report = compile_bridge()
    assert data["steps"] == BLOCK
    assert report["nondetections_emitted"] == 0
    assert report["rows_by_route"]["ahj_positive_weak_or_unlocalized_retained_in_duration_evidence"] > 0
    forum = data["uncertain_jurisdiction_units"]
    assert forum and all(r["detected"] for unit in forum for r in unit["readings"])
    assert all(unit["reading_scope_kind"] == "reviewed_fixed_subset" for unit in forum)
    Evidence(data)


def test_bridge_never_uses_utility_context_as_ahj_identity():
    data, report = compile_bridge()
    assert report["rows_by_route"]["utility_scoped_timing_only"] > 0
    assert all("utility_volume_weighted" not in unit["assignment_prior_basis"]
               for unit in data["uncertain_jurisdiction_units"])
    assert all(unit["assignment_prior_kind"] == "reviewed_candidate_weights"
               for unit in data["uncertain_jurisdiction_units"])


def test_production_packet_requires_occurrence_review():
    with pytest.raises(ValueError, match="performed/experienced occurrence"):
        compile_reviewed_packet({"episodes": [{}]})
