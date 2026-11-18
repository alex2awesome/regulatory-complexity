"""Bounded entry-level clock routing checks; no corpus or sampler runs."""
from copy import deepcopy
import hashlib
import json

import pytest

from pipeline.procbench.solar_panel.adopt_bulk_forum import (
    claim_content_sha256, resolve_clock_mapping, classify_status, duration_bounds,
    episode_geography, geo_scope, matching_staged_episode,
    within_packet_case_links,
)


def test_pending_status_alias_preserves_precision_and_never_becomes_completion():
    report = {"censoring": "right_censored|approximate|self_reported",
              "value": 1, "unit": "months"}
    original = deepcopy(report)
    status, precision, method = classify_status(report, {})
    assert (status, precision, method) == (
        "pending_lower_bound", "approximate", "explicit_right_censored_alias")
    bounds, error = duration_bounds(report, status, precision)
    assert error is None
    assert bounds["observation_kind"] == "pending_right_censored"
    assert bounds["upper"] is None
    assert bounds["lower"] == pytest.approx((365.25 / 12) * .85)
    assert report == original
    assert classify_status({"censoring": "unknown|approximate"}, {})[0] == "unclassified"
    assert classify_status({"censoring": "forecast_not_observation|approximate"}, {})[0] == "forecast_not_observation"
    assert classify_status({"censoring": "completed_lower_bound|approximate|self_reported"}, {})[:2] == ("completed_observed", "approximate")
    assert classify_status({"censoring": "completed_upper_bound|exact_as_stated|self_reported"}, {})[:2] == ("upper_bound_only", "exact_as_stated")
    # A naked range/approximation still does not establish completion.
    assert classify_status({"censoring": "range|self_reported"}, {})[0] == "unclassified"


def test_reviewed_actions_are_consumed_with_lineage_without_changing_originals(tmp_path, monkeypatch):
    from pipeline.procbench.solar_panel import adopt_bulk_forum as adapter
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    source = tmp_path / "source.json"
    body = "I signed the contract. Installation took 7 days."
    source.write_text(json.dumps({"post": {"title": "My project", "selftext": body, "author": "one"}, "comments": []}))
    timing = {"clock": "physical_installation_duration", "value": 7, "unit": "days",
              "censoring": "completed_observed|exact_as_stated", "quote": "Installation took 7 days.", "refs": ["post"]}
    episode = {"decision_case_id": "case", "author": "one", "thread": "thread",
               "timing": [timing], "non_registry_actions": []}
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"censoring_crosswalk": {"map": {}}, "packets": [{
        "packet_id": "packet", "files": {
            "reservation": {"sources": [{"source_path": "source.json", "thread_id": "thread",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]},
            "coverage": {"rows": []}, "decisions": {"episodes": [episode]}}}]}))
    log = tmp_path / "check.log"
    log.write_text("=== packet === PASS\n")
    action = {"actor": "applicant", "action": "signed installation contract", "status": "performed",
              "refs": ["post"], "quote": "I signed the contract."}
    reading = {"episode_content_sha256": claim_content_sha256(episode), "reviewed_by": "test",
               "rationale": "Existing description omitted a concrete act.", "actions": [action]}
    additions = tmp_path / "actions.json"
    additions.write_text(json.dumps({"episodes": {"packet:case": reading}}))
    adapter.compile_input(frozen, log, None, tmp_path / "base")
    adapter.compile_input(frozen, log, None, tmp_path / "added", additions)
    assert (tmp_path / "base/observations.json").read_bytes() == (tmp_path / "added/observations.json").read_bytes()
    rows = json.loads((tmp_path / "added/claim_routes.json").read_bytes())
    extra = [r for r in rows if r["field"] == "non_registry_actions"]
    assert len(extra) == 1 and extra[0]["claim_id"] == "packet:case:reviewed_action:0"
    assert extra[0]["source_decisions_json_path"] is None
    assert extra[0]["supporting_sources"][0]["json_path"] == "$.post.selftext"
    result_episode = json.loads((tmp_path / "added/episodes.json").read_bytes())[0]
    assert result_episode["original"] == episode
    assert result_episode["effective_non_registry_actions"] == [action]
    assert json.loads((tmp_path / "added/adoption_accounting.json").read_bytes())["reviewed_action_additions"] == 1
    bad = deepcopy(reading)
    bad["episode_content_sha256"] = "wrong"
    with pytest.raises(ValueError, match="Stale action"):
        adapter.validate_action_additions({"packet:case": bad}, {"packet:case": episode})
    bad = deepcopy(reading)
    bad["actions"][0]["quote"] = "A made-up quotation."
    additions.write_text(json.dumps({"episodes": {"packet:case": bad}}))
    with pytest.raises(ValueError, match="quote/author does not replay"):
        adapter.compile_input(frozen, log, None, tmp_path / "invalid", additions)
    assert not (tmp_path / "invalid").exists()


def test_explicit_case_links_resolve_cycles_and_chains_without_username_merges():
    rows = [dict(decision_case_id='b', same_installation_as='c', author='one'),
            dict(decision_case_id='c', same_installation_as=['b'], author='one'),
            dict(decision_case_id='a', same_installation_as='b', author='one'),
            dict(decision_case_id='d', author='one', same_installation_candidate='a'),
            dict(decision_case_id='e', same_installation_as=['a', 'd']),
            dict(decision_case_id='f', same_installation_as='outside_packet')]
    original = deepcopy(rows)
    assert within_packet_case_links(rows) == dict(a='a', b='a', c='a', d='d', e='e', f='f')
    assert within_packet_case_links(rows[::-1]) == within_packet_case_links(rows)
    assert rows == original
    with pytest.raises(ValueError, match='Duplicate decision_case_id'):
        within_packet_case_links([rows[0], rows[0]])


def test_entry_mapping_overrides_only_its_bound_claim():
    claim = {"clock": "inspection_to_pto", "value": 7, "unit": "calendar_days",
             "censoring": "completed_observed|approximate", "quote": "a week after final inspection"}
    original = deepcopy(claim)
    ambiguous = {"canonical_clock": None, "route": "varies_by_entry"}
    crosswalk = {"canonical_clocks": {"final_inspection_to_pto": {
                    "start": "final inspection passed", "end": "PTO granted"}},
                 "mappings": {"inspection_to_pto": ambiguous},
                 "claim_mappings": {"one": {
                     "raw_clock": claim["clock"], "claim_content_sha256": claim_content_sha256(claim),
                     "canonical_clock": "final_inspection_to_pto", "route": "alias",
                     "reviewed_by": "test_fixture", "rationale": "Explicit final-inspection endpoint."}}}
    mapped = resolve_clock_mapping("one", claim, crosswalk)
    assert mapped["canonical_clock"] == "final_inspection_to_pto"
    assert mapped["mapping_scope"] == "reviewed_claim"
    assert resolve_clock_mapping("two", claim, crosswalk) == ambiguous
    assert claim == original
    for changed in ({**claim, "value": 8}, {**claim, "quote": "after inspection"}):
        with pytest.raises(ValueError, match="Stale entry-level"):
            resolve_clock_mapping("one", changed, crosswalk)
    crosswalk["claim_mappings"]["one"]["canonical_clock"] = "undefined_clock"
    with pytest.raises(ValueError, match="defined clock"):
        resolve_clock_mapping("one", claim, crosswalk)


def test_status_only_reading_is_explicit_and_hash_bound_without_forcing_a_clock():
    claim = {"clock": "unusual_clock", "censoring": "range|self_reported",
             "lower": 3, "upper": 5, "unit": "months"}
    reading = {"raw_clock": "unusual_clock", "claim_content_sha256": claim_content_sha256(claim),
               "route": "retain_raw_clock", "canonical_clock": None,
               "observation_status": "range_reported", "precision": "approximate",
               "reviewed_by": "test", "rationale": "Completed endpoint was read in its source context."}
    mappings = {"claim_mappings": {"one": reading}}
    actual = resolve_clock_mapping("one", claim, mappings)
    assert actual["canonical_clock"] is None
    assert actual["observation_status"] == "range_reported"
    assert claim["censoring"] == "range|self_reported"
    reading["observation_status"] = "maybe completed"
    with pytest.raises(ValueError, match="canonical observation status"):
        resolve_clock_mapping("one", claim, mappings)


def test_equal_completed_bounds_are_a_point_report_not_lost_evidence():
    equal, error = duration_bounds({"lower": 38, "upper": 38, "unit": "days"}, "completed_observed", "exact_as_stated")
    point, point_error = duration_bounds({"value": 38, "unit": "days"}, "completed_observed", "exact_as_stated")
    assert error is None and point_error is None
    assert (equal["lower"], equal["upper"]) == (point["lower"], point["upper"]) == (37, 39)
    pending, error = duration_bounds({"lower": 38, "upper": 38, "unit": "days"}, "pending_lower_bound", "exact_as_stated")
    assert error is None and pending["lower"] == 38 and pending["upper"] is None
    invalid, error = duration_bounds({"lower": 39, "upper": 38, "unit": "days"}, "range_reported", "exact_as_stated")
    assert invalid is None and error == "invalid_or_degenerate_duration_interval"


def test_unresolved_override_can_prevent_overbroad_label_pooling():
    claim = {"clock": "install_to_pto", "lower": 30, "unit": "days"}
    crosswalk = {"mappings": {"install_to_pto": {
        "canonical_clock": "installation_to_pto", "route": "alias"}},
        "claim_mappings": {"uncertain": {
            "raw_clock": claim["clock"], "claim_content_sha256": claim_content_sha256(claim),
            "canonical_clock": None, "route": "varies_by_entry", "reviewed_by": "test_fixture",
            "rationale": "This particular report does not fix the starting milestone."}}}
    assert resolve_clock_mapping("uncertain", claim, crosswalk)["canonical_clock"] is None
    assert resolve_clock_mapping("unreviewed", claim, crosswalk)["canonical_clock"] == "installation_to_pto"


@pytest.mark.parametrize('geography_layout', ['nested', 'timing_staged'])
def test_compile_reads_first_log_header_and_uses_bound_override(tmp_path, monkeypatch, geography_layout):
    from pipeline.procbench.solar_panel import adopt_bulk_forum as adapter
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    body = "It took 7 days from installation to PTO."
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"post": {"title": "My timeline", "selftext": body, "author": "one"},
                                  "comments": []}))
    claim = {"clock": "my_project_clock", "value": 7, "unit": "days",
             "censoring": "approximate|self_reported", "refs": ["post"], "quote": body}
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"censoring_crosswalk": {"map": {}}, "packets": [{
        "packet_id": "packet", "files": {
            "reservation": {"sources": [{"source_path": "source.json", "thread_id": "thread",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]},
            "coverage": {"rows": []}, "decisions": {"episodes": [{
                "decision_case_id": "case", "author": "one", "thread": "thread", "timing": [claim],
                "location": {"county_weights": {"Alameda": 1.0}, "unassigned_geography_mass": 0.0}}]}}}]}))
    if geography_layout == 'timing_staged':
        fixture = json.loads(frozen.read_text())
        files = fixture['packets'][0]['files']
        location = files['decisions']['episodes'][0].pop('location')
        files['timing_staged'] = {'episodes': [dict(decision_case_id='case',
            thread='thread', author='one', **location)]}
        frozen.write_text(json.dumps(fixture))
    log = tmp_path / "check.log"
    log.write_text("=== packet === PASS\n")  # No leading blank line.
    aliases = tmp_path / "aliases.json"
    crosswalk = {"canonical_clocks": {"installation_to_pto": {"start": "installation", "end": "PTO"}},
                 "claim_mappings": {"packet:case:timing:0": {
                     "raw_clock": claim["clock"], "claim_content_sha256": claim_content_sha256(claim),
                     "canonical_clock": "installation_to_pto", "route": "alias", "reviewed_by": "test",
                     "observation_status": "completed_observed", "precision": "exact_as_stated",
                     "rationale": "Explicit endpoints in fixture."}}}
    aliases.write_text(json.dumps(crosswalk))
    adapter.compile_input(frozen, log, aliases, tmp_path / "adopted")
    observations = json.loads((tmp_path / "adopted/observations.json").read_text())
    assert len(observations) == 1
    assert observations[0]["clock"] == "installation_to_pto"
    assert observations[0]["original"] == claim
    assert observations[0]["unreviewed_observation_status"] == "unclassified"
    assert observations[0]["status_adapter"] == "reviewed_claim_status"
    assert observations[0]["county_weights"] == {"Alameda": 1.0}
    assert observations[0]["unassigned_geography_mass"] == 0.0
    assert observations[0]["geography_scope"] == "county_candidates_provided"
    assert observations[0]['geography_field_sources']['county_weights'] == (
        'location' if geography_layout == 'nested' else 'timing_staged')
    # Mistyped IDs must not silently leave all requested overrides unused.
    crosswalk["claim_mappings"]["missing"] = crosswalk["claim_mappings"].pop("packet:case:timing:0")
    aliases.write_text(json.dumps(crosswalk))
    with pytest.raises(ValueError, match="no input claim"):
        adapter.compile_input(frozen, log, aliases, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()
    # Even an innocuous byte change leaving the quoted text intact cannot be
    # reported as the old hash-bound capture merely because its receipt passed.
    crosswalk["claim_mappings"]["packet:case:timing:0"] = crosswalk["claim_mappings"].pop("missing")
    aliases.write_text(json.dumps(crosswalk))
    source.write_text(source.read_text() + "\n")
    with pytest.raises(ValueError, match="Frozen raw source changed"):
        adapter.compile_input(frozen, log, aliases, tmp_path / "stale_raw")
    assert not (tmp_path / "stale_raw").exists()


def test_staged_geography_link_is_exact_and_never_merges_two_installations():
    ep = dict(decision_case_id='one', thread='thread', author='person')
    staged = dict(thread='thread', author='person', county_weights={'Alameda': 1.},
                  unassigned_geography_mass=0.)
    match, link = matching_staged_episode(ep, [ep], [staged])
    assert link['status'] == 'matched'
    assert episode_geography(ep, match)['county_weights'] == {'Alameda': 1.}
    second = {**ep, 'decision_case_id': 'two'}
    assert matching_staged_episode(ep, [ep, second], [staged])[0] is None
    explicit = {**staged, 'decision_case_id': 'one'}
    assert matching_staged_episode(ep, [ep, second], [explicit])[0] == explicit
    assert matching_staged_episode(ep, [ep], [explicit, explicit])[0] is None
    assert matching_staged_episode(ep, [ep], [{**explicit, 'author': 'someone_else'}])[0] is None
    conflicting = episode_geography({**ep, 'county_weights': {'Orange': 1.}}, explicit)
    assert conflicting['county_weights'] == {'Orange': 1.}
    assert conflicting['geography_field_conflicts'][0]['timing_staged'] == {'Alameda': 1.}
    assert geo_scope(ep, conflicting) == 'unresolved_or_other_scope'


def test_geography_layout_conflicts_are_not_silently_merged():
    episode = {"county_weights": {"Alameda": 1.}, "unassigned_geography_mass": 0.,
               "location": {"county_weights": {"San Diego": 1.}, "unassigned_geography_mass": 0.}}
    original = deepcopy(episode)
    metadata = episode_geography(episode)
    assert metadata["county_weights"] == {"Alameda": 1.}
    assert metadata["geography_field_sources"]["county_weights"] == "episode"
    assert metadata["geography_field_conflicts"] == [
        {"field": "county_weights", "episode": {"Alameda": 1.}, "location": {"San Diego": 1.}}]
    assert geo_scope(episode) == "unresolved_or_other_scope"
    assert episode == original
