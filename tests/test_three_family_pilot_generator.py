"""Contract tests for the bounded fictional CCW/CalFresh pilot generator.

The tests inspect development fixtures constructed in memory.  For a complete
world they inspect only public manifests, non-sensitive counts, paths, and byte
hashes; they do not open reserved private truth after it has been generated.
No network, LLM, paid service, extractor, or inference code is used.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter

import pytest

from benchmark.synth.generator import three_family_pilot as pilot


@pytest.fixture(scope="module")
def design():
    config, split = pilot.frozen_design()
    return config, split, pilot._jurisdictions()


@pytest.fixture(scope="module")
def built_world(tmp_path_factory):
    root = tmp_path_factory.mktemp("three_family_pilot") / pilot.WORLD_ID
    counts = pilot.build(root)
    return root, counts


def test_config_and_whole_jurisdiction_split_are_frozen_before_draws(design):
    config, split, jurisdictions = design
    assert config["generation_order"][:2] == ["freeze_config", "freeze_split"]
    assert config["route_and_outcome_shares_frozen"] is True
    assert config["episodes_per_jurisdiction"] == 1000
    assert len(config["months"]) == 24
    assert config["artifact_quota"] == {"per_jurisdiction_max": 12, "shared_per_family_max": 3}
    assert config["empirical_calibration"] is None
    for family in ("ccw", "calfresh"):
        assert len(jurisdictions[family]) == 12
        assert Counter(split["families"][family].values()) == {
            "calibration": 4, "development": 4, "reserved": 4,
        }


def test_complete_build_has_the_approved_bounded_size(built_world):
    root, counts = built_world
    assert counts["episodes"] == 24_000
    assert counts["jurisdictions_per_family"] == 12
    assert counts["artifacts_by_family"] == {"ccw": 123, "calfresh": 123}
    assert counts["artifacts_per_jurisdiction"] == 10 <= 12
    assert counts["shared_artifacts_per_family"] == 3
    assert counts["ceilings"] == 24
    assert counts["rendered_artifacts"] == counts["independently_verified_artifacts"] == 0
    # Counts are the safe post-build inspection surface; do not open private
    # reserved episode files here.
    assert (root / "private/evaluation/split_manifest.json").is_file()
    boundary = (root / "BOUNDARY.md").read_text()
    assert "extractors and fitters must not receive" in boundary
    assert "no claimed empirical calibration" in boundary
    assert len(list((root / "private/truth/cases/ccw").glob("*.jsonl.gz"))) == 12
    assert len(list((root / "private/truth/cases/calfresh").glob("*.jsonl.gz"))) == 12


def test_public_manifest_contains_specs_not_a_claimed_prose_corpus(built_world):
    root, _ = built_world
    manifest = json.loads((root / "public/artifact_manifest.json").read_text())
    assert len(manifest) == 246
    assert {row["status"] for row in manifest} == {"structured_render_spec_not_rendered"}
    by_family = Counter(row["family"] for row in manifest)
    assert by_family == {"ccw": 123, "calfresh": 123}
    assert not (root / "artifacts").exists()
    receipt = json.loads((root / "construction_receipt.json").read_text())
    assert receipt["frozen_before_draws"] is True
    assert receipt["validation"] == "passed_in_memory_before_release"
    assert any("no prose corpus" in x.lower() for x in receipt["limitations"])
    assert any("independent verification" in x.lower() for x in receipt["limitations"])


def test_ccw_development_fixture_covers_routes_stages_outcomes_and_distinct_roles(design):
    _config, split, jurisdictions = design
    jur = jurisdictions["ccw"][4]
    assert split["families"]["ccw"][jur["id"]] == "development"
    cases, process = pilot._generate_ccw_cases(pilot.SEED, jur)
    assert {c["route"] for c in cases} == {"initial", "renewal"}
    assert {c["decision_outcome"] for c in cases} >= {"approved", "denied", "withdrawn", None}
    stages = {e["stage"] for c in cases for e in c["latent_eventual_path"]}
    assert set(pilot.CCW_STAGES) <= stages
    assert any(c["latent_repeat_count"] for c in cases)
    assert any(c["decision_right_censored"] for c in cases)
    orgs = process["organizations"]
    assert orgs["issuer"] != orgs["training_provider"]
    assert orgs["issuer"] != orgs["fingerprint_provider"]


def test_calfresh_development_fixture_has_origins_dependent_stats_and_schema_break(design):
    _config, split, jurisdictions = design
    jur = jurisdictions["calfresh"][4]
    assert split["families"]["calfresh"][jur["id"]] == "development"
    cases, process = pilot._generate_calfresh_cases(pilot.SEED, jur)
    assert {c["route"] for c in cases} == {"normal", "expedited"}
    assert {c["latent_service_clock_origin"] for c in cases} == {"application", "eligibility_discovery"}
    assert {c["decision_outcome"] for c in cases} >= {"approved", "denied", "withdrawn", None}
    assert any(c["latent_repeat_count"] for c in cases)
    assert process["organizations"]["agency"] != process["organizations"]["issuance_provider"]
    summary = pilot._summarize_calfresh(cases, jur)
    assert len(summary["receipt_cohorts"]) == len(summary["completion_cohorts"]) == 24
    assert summary["report_gaps"]
    assert {r["schema_era"] for r in summary["receipt_cohorts"]} == {"CF18_A", "CF18_B"}
    old = [s["over_30_field"] for r in summary["receipt_cohorts"] if r["schema_era"] == "CF18_A"
           for s in r["timing_strata"]]
    new = [s["over_30_field"] for r in summary["receipt_cohorts"] if r["schema_era"] == "CF18_B"
           for s in r["timing_strata"]]
    assert {x["field_id"] for x in old} == {"A_OVER30"}
    assert {x["field_id"] for x in new} == {"B_CTY_OVER30"}
    assert "county delay" in new[0]["definition"]
    statuses = {
        cell["status"]
        for row in summary["receipt_cohorts"] for stratum in row["timing_strata"]
        for cell in [row["workload"]["denied_decisions"],
                     row["workload"]["decision_pending_at_cutoff"],
                     *stratum["approval_bins"].values()]
    }
    assert "suppressed" in statuses


@pytest.fixture(scope="module")
def development_cases(design):
    _config, split, jurisdictions = design
    out = {}
    for family, fn in (("ccw", pilot._generate_ccw_cases),
                       ("calfresh", pilot._generate_calfresh_cases)):
        jur = jurisdictions[family][4]
        assert split["families"][family][jur["id"]] == "development"
        out[family] = (jur, fn(pilot.SEED, jur)[0])
    return out


def test_cutoff_projection_never_exposes_future_completion(development_cases):
    cutoff = (pilot._iso_day(pilot.WINDOW_END) - pilot._iso_day(pilot.WINDOW_START)).days
    for _family, (_jur, cases) in development_cases.items():
        assert any(c["in_progress_event"] for c in cases)
        for case in cases:
            assert all(event["end_day"] <= cutoff for event in case["observed_path"])
            active = case["in_progress_event"]
            if active:
                assert set(active) == {"stage", "visit_index", "start_day", "observed_through_day",
                                       "elapsed_lower_bound_days", "status"}
                assert active["status"] == "right_censored"
                assert active["observed_through_day"] == cutoff


def test_withdrawal_checkpoint_is_single_terminal_nondecision_draw(development_cases):
    for _family, (_jur, cases) in development_cases.items():
        withdrawn = [c for c in cases if c["planned_outcome"] == "withdrawn"]
        assert withdrawn
        assert all(c["withdrawal_after_stage"] not in {None, "decision"} for c in withdrawn)
        assert all(not any(e["stage"] == "decision" for e in c["latent_eventual_path"])
                   for c in withdrawn)


def test_known_approval_survives_pending_fulfillment_and_enters_decision_summary(development_cases):
    jur, cases = development_cases["ccw"]
    pending_pickup = [c for c in cases if c["decision_outcome"] == "approved" and
                      c["fulfillment_status"] == "pending"]
    assert pending_pickup
    assert all(c["decision_status"] == "completed" and c["decision_days_from_application"] is not None
               for c in pending_pickup)
    summary = pilot._summarize_ccw(cases, jur)
    assert sum(r["approved_decisions"] for r in summary["monthly_receipt_cohorts"]) == sum(
        c["decision_outcome"] == "approved" for c in cases)
    assert sum(r["pickup_completed"] for r in summary["monthly_receipt_cohorts"]) == sum(
        c["fulfillment_status"] == "completed" for c in cases)


def test_renewal_inventory_is_exact_and_has_no_interview(development_cases):
    jur, cases = development_cases["ccw"]
    renewals = [c for c in cases if c["route"] == "renewal"]
    assert renewals and all(not any(e["stage"] == "interview" for e in c["latent_eventual_path"])
                            for c in renewals)
    _cases, process = pilot._generate_ccw_cases(pilot.SEED, jur)
    assert process["route_stage_inventory"]["renewal"] == [
        "application_received", "background_check", "training_review", "decision", "credential_pickup"]


def test_calfresh_clocks_are_explicit_and_issuance_is_application_origin(development_cases):
    _jur, cases = development_cases["calfresh"]
    discovery = [c for c in cases if c["approval_service_clock_origin"] == "eligibility_discovery" and
                 c["approval_days_from_application"] is not None]
    assert discovery and any(c["approval_days_from_application"] > c["approval_days_from_service_clock"]
                             for c in discovery)
    issued = [c for c in cases if c["issuance_days_from_application"] is not None]
    assert issued
    assert all(c["issuance_days_from_application"] ==
               c["approval_days_from_application"] + c["decision_to_issuance_days"] for c in issued)
    assert not any("issuance_days" in c or "approval_days" in c for c in cases)


def test_calfresh_timing_rows_are_route_and_origin_stratified(development_cases):
    jur, cases = development_cases["calfresh"]
    summary = pilot._summarize_calfresh(cases, jur)
    expected = {"normal_application", "expedited_application", "expedited_eligibility_discovery"}
    for row in summary["receipt_cohorts"] + summary["completion_cohorts"]:
        assert {s["stratum_id"] for s in row["timing_strata"]} == expected
        for stratum in row["timing_strata"]:
            assert stratum["duration_definition"] == f"{stratum['clock_origin']}-to-approval"
            assert stratum["stratum_id"] == f"{stratum['route']}_{stratum['clock_origin']}"
        if "workload" in row:
            assert "received" in row["workload"]
            assert all("received" not in stratum for stratum in row["timing_strata"])


def test_forums_name_only_observed_endpoint_or_censored_age(development_cases):
    provenance, links = [], []
    for family, (jur, cases) in development_cases.items():
        summary = (pilot._summarize_ccw(cases, jur) if family == "ccw"
                   else pilot._summarize_calfresh(cases, jur))
        specs = (pilot._ccw_specs(pilot.SEED, jur, cases, summary, provenance, links) if family == "ccw"
                 else pilot._calfresh_specs(pilot.SEED, jur, cases, summary, provenance, links))
        forum_kind = "forum_thread" if family == "ccw" else "applicant_forum"
        forum = next(s for s in specs if s["kind"] == forum_kind)
        for claim in forum["content_blocks"][0]["claims"]:
            qualifiers = set(claim["qualifiers"])
            assert any(q.startswith("endpoint=") for q in qualifiers)
            assert qualifiers & {"censor_status=completed", "censor_status=right_censored"}


@pytest.mark.parametrize("seed", [20260920, 20260921, 20260922, 20260937, 20261021])
def test_five_development_seeds_bind_origins_repeats_and_denials_to_paths(design, seed):
    _config, _split, jurisdictions = design
    for family, generator in (("ccw", pilot._generate_ccw_cases),
                              ("calfresh", pilot._generate_calfresh_cases)):
        cases, _process = generator(seed, jurisdictions[family][4])
        assert any(c["latent_repeat_count"] > c["observed_repeat_count"] for c in cases)
        assert any(c["decision_outcome"] == "denied" for c in cases)
        for case in cases:
            assert case["latent_repeat_count"] == sum(
                e["visit_index"] > 1 for e in case["latent_eventual_path"])
            assert case["observed_repeat_count"] == sum(
                e["visit_index"] > 1 for e in case["observed_path"])
            assert "repeat_count" not in case
            if case["decision_outcome"] == "denied":
                observation = pilot._forum_observation(case, family)
                assert observation["endpoint"] == "application_to_denial"
                assert observation["censor_status"] == "completed"
                assert observation["duration_days"] == case["decision_days_from_application"]
        if family == "calfresh":
            forced_discovery = [c for c in cases
                                if c["latent_service_clock_origin"] == "eligibility_discovery"
                                and c["observed_service_clock_origin"] is None]
            assert forced_discovery
            assert all(c["in_progress_event"]["stage"] == "eligibility_discovery"
                       for c in forced_discovery)
            for case in cases:
                state = pilot._calfresh_service_clock_state(
                    case["latent_eventual_path"], case["observed_path"],
                    (pilot._iso_day(case["application_date"]) - pilot._iso_day(pilot.WINDOW_START)).days)
                assert all(case[key] == value for key, value in state.items())


def test_forced_discovery_origin_is_latent_until_discovery_completes():
    class ChooseFirst:
        def randrange(self, _n):
            return 0

    cutoff = 20
    path = [pilot._event("application_received", 5, 0, "application"),
            pilot._event("eligibility_discovery", 5, 1, "eligibility_discovery"),
            pilot._event("interview", 6, 2, "eligibility_discovery")]
    pilot._force_pending_at_cutoff(ChooseFirst(), path, cutoff)
    observed, active = pilot._observed_path(path, cutoff)
    state = pilot._calfresh_service_clock_state(path, observed, 5)
    assert path[-1]["stage"] == active["stage"] == "eligibility_discovery"
    assert path[-1]["end_day"] > cutoff
    assert state == {
        "latent_service_clock_origin": "eligibility_discovery",
        "latent_service_clock_origin_day": path[-1]["end_day"],
        "observed_service_clock_origin": None,
        "observed_service_clock_origin_day": None,
    }


def test_forced_pending_truncation_rederives_repeat_counts_from_retained_paths():
    class ChooseFirst:
        def randrange(self, _n):
            return 0

    path = [pilot._event("application_received", 1, 0, "application"),
            pilot._event("interview", 1, 2, "application"),
            pilot._event("interview", 3, 2, "application", visit=2),
            pilot._event("decision", 5, 2, "application")]
    pilot._force_pending_at_cutoff(ChooseFirst(), path, 10)
    observed, _active = pilot._observed_path(path, 10)
    assert [e["visit_index"] for e in path] == [1, 1]
    assert pilot._repeat_counts(path, observed) == (0, 0)


def test_forum_corner_claims_match_source_case_status_endpoint_and_value(development_cases):
    selectors = {
        "fulfilled": lambda c: c["fulfillment_status"] == "completed",
        "approved_pending": lambda c: (c["decision_outcome"] == "approved" and
                                        c["fulfillment_status"] == "pending"),
        "denied": lambda c: c["decision_outcome"] == "denied",
        "withdrawn": lambda c: c["decision_outcome"] == "withdrawn",
        "pending": lambda c: c["decision_status"] == "pending",
    }
    for family, (jur, cases) in development_cases.items():
        summary = (pilot._summarize_ccw(cases, jur) if family == "ccw"
                   else pilot._summarize_calfresh(cases, jur))
        for status_name, selector in selectors.items():
            case = next(c for c in cases if selector(c))
            provenance, links = [], []
            specs = (pilot._ccw_specs(pilot.SEED, jur, [case], summary, provenance, links)
                     if family == "ccw" else
                     pilot._calfresh_specs(pilot.SEED, jur, [case], summary, provenance, links))
            kind = "forum_thread" if family == "ccw" else "applicant_forum"
            forum = next(s for s in specs if s["kind"] == kind)
            claim = next(c for c in forum["content_blocks"][0]["claims"]
                         if c["topic"] == "poster_1_timeline")
            source = next(p for p in provenance if p["claim_id"] == claim["claim_id"])
            observation = pilot._forum_observation(case, family)
            divisor = 14 if family == "ccw" else 7
            multiplier = 2 if family == "ccw" else 1
            expected = int(math.ceil(observation["duration_days"] / divisor) * multiplier)
            assert source["source_id"] == case["case_id"], status_name
            assert claim["value"] == expected
            assert set(claim["qualifiers"]) == {
                f"endpoint={observation['endpoint']}",
                f"censor_status={observation['censor_status']}",
            }
            if status_name == "denied":
                assert claim["qualifiers"] == [
                    "endpoint=application_to_denial", "censor_status=completed"]


def test_forum_denial_ranking_uses_observed_decision_duration(development_cases):
    jur, cases = development_cases["calfresh"]
    denied = [c for c in cases if c["decision_outcome"] == "denied"]
    expected = [c["case_id"] for c in sorted(
        denied, key=lambda c: (c["decision_days_from_application"], c["case_id"]), reverse=True)[:3]]
    provenance, links = [], []
    specs = pilot._calfresh_specs(
        pilot.SEED, jur, denied, pilot._summarize_calfresh(cases, jur), provenance, links)
    forum = next(s for s in specs if s["kind"] == "applicant_forum")
    primaries = [c for c in forum["content_blocks"][0]["claims"] if c["topic"].startswith("poster_")
                and c["topic"].endswith("_timeline")]
    sources = [next(p["source_id"] for p in provenance if p["claim_id"] == c["claim_id"])
               for c in primaries]
    assert sources == expected
    assert all(c["qualifiers"] == ["endpoint=application_to_denial", "censor_status=completed"]
               for c in primaries)


def test_exact_stage_lists_declare_through_decision_scope(development_cases):
    provenance, links = [], []
    for family, (jur, cases) in development_cases.items():
        summary = (pilot._summarize_ccw(cases, jur) if family == "ccw"
                   else pilot._summarize_calfresh(cases, jur))
        specs = (pilot._ccw_specs(pilot.SEED, jur, cases, summary, provenance, links)
                 if family == "ccw" else
                 pilot._calfresh_specs(pilot.SEED, jur, cases, summary, provenance, links))
        topics = {"initial_stages", "renewal_stages"} if family == "ccw" else {"normal_route_stages"}
        claims = [c for spec in specs for block in spec["content_blocks"]
                  for c in block.get("claims", []) if c["topic"] in topics]
        assert {c["topic"] for c in claims} == topics
        assert all(any("through decision" in q for q in c["qualifiers"]) for c in claims)


def test_development_specs_have_private_provenance_and_all_three_lineage_kinds(design):
    _config, _split, jurisdictions = design
    provenance, links = [], []
    cj = jurisdictions["ccw"][4]
    ccases, _ = pilot._generate_ccw_cases(pilot.SEED, cj)
    cs = pilot._summarize_ccw(ccases, cj)
    ccw_specs = pilot._ccw_specs(pilot.SEED, cj, ccases, cs, provenance, links)
    fj = jurisdictions["calfresh"][4]
    fcases, _ = pilot._generate_calfresh_cases(pilot.SEED, fj)
    fs = pilot._summarize_calfresh(fcases, fj)
    cf_specs = pilot._calfresh_specs(pilot.SEED, fj, fcases, fs, provenance, links)
    pilot._assert_public_boundary(ccw_specs + cf_specs, [pilot._context(cj), pilot._context(fj)])
    claims = {c["claim_id"] for spec in ccw_specs + cf_specs
              for block in spec["content_blocks"] for c in block.get("claims", [])}
    assert claims == {p["claim_id"] for p in provenance}
    assert {p["reporting_mechanism"] for p in provenance} >= {
        "faithful", "optimistic_summary", "delay_selected_forum", "linked_update",
    }
    assert {row["kind"] for row in links} == {
        pilot.SAME_CASE, pilot.SAME_COHORT, pilot.COPIED_TEXT,
    }
    assert any(row["mechanism"] in {"vendor_boilerplate", "consortium_template"} for row in links)


def _tree_hash(root):
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def test_complete_build_is_byte_deterministic_without_opening_reserved_labels(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    pilot.build(a)
    pilot.build(b)
    # Byte hashes compare the generated bundles without parsing private labels.
    assert _tree_hash(a) == _tree_hash(b)


def test_refuses_to_overwrite_even_an_empty_destination(tmp_path):
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    with pytest.raises(ValueError, match="must not exist"):
        pilot.build(occupied)
