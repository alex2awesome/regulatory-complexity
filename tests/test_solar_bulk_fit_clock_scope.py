"""Small checks of estimand routing, without running a sampler."""
import json

import pytest

from pipeline.procbench.solar_panel.fit_bulk_forum import prepare


def test_explicit_clock_scope_retains_nontarget_evidence(tmp_path):
    observations = tmp_path / "observations.json"
    rows = [{"claim_id": clock, "clock": clock, "time_unit": "calendar_days",
             "observation_kind": "completed_interval", "lower": 5, "upper": 7,
             "packet_id": "packet1", "contributor_group": "speaker1", "refs": ["post"],
             "source_hashes": ["abc"]}
            for clock in ("installation_to_pto", "installation_to_report_age")]
    observations.write_text(json.dumps({"adoption_state": "adopted", "observations": rows}))
    out = tmp_path / "explicit"
    receipt = prepare(observations, out, min_contributors=15, chains=2,
                      warmup=1, draws=1, seed=1, clocks=("installation_to_pto",))
    routes = {r["claim_id"]: r["route"] for r in json.loads((out / "route_accounting.json").read_text())["rows"]}
    assert receipt["input_claims"] == 2
    assert receipt["selected_claims"] == 1
    assert receipt["declared_clocks"] == ["installation_to_pto"]
    assert routes["installation_to_report_age"] == "retained_outside_declared_fit_estimands"
    assert routes["installation_to_pto"] == "retained_below_minimum_contributors"
    # Backwards compatibility: no hidden change to old fit specifications.
    legacy = prepare(observations, tmp_path / "legacy", min_contributors=15,
                     chains=2, warmup=1, draws=1, seed=1)
    assert legacy["selected_claims"] == 2
    assert legacy["declared_clocks"] is None


def test_empty_declared_clock_scope_fails_before_writes(tmp_path):
    with pytest.raises(ValueError, match="Declared fit clocks"):
        prepare(tmp_path / "missing.json", tmp_path / "out", min_contributors=15,
                chains=2, warmup=1, draws=1, seed=1, clocks=())
    assert not (tmp_path / "out").exists()


def test_adu_reuses_model_with_explicit_domain_provenance(tmp_path):
    observations = tmp_path / "observations.json"
    rows = [{"claim_id": f"claim{i}", "clock": "filing_to_permit",
             "time_unit": "calendar_days", "observation_kind": "completed_interval",
             "lower": 90, "upper": 120, "packet_id": "adu1",
             "contributor_group": f"speaker{i}", "refs": ["post"],
             "source_hashes": {"source.json": "abc"}} for i in range(5)]
    observations.write_text(json.dumps({"adoption_state": "adopted", "observations": rows}))
    plans = {domain: prepare(observations, tmp_path / domain, min_contributors=5,
                            chains=2, warmup=1, draws=8, seed=1, domain=domain)
             for domain in ("solar", "adu")}
    assert plans["adu"]["schema_version"] == "adu-bulk-forum-fit-plan/1"
    assert plans["adu"]["eligible_frames"] == 1
    configs = []
    for domain, plan in plans.items():
        frame = plan["queue"][0]
        data = json.loads((tmp_path / domain / frame["data"]).read_text())
        configs.append(json.loads((tmp_path / domain / frame["config"]).read_text()))
        assert data["conditional_case_frames"][0]["source_family"] == f"{domain}_bulk_forum"
        assert data["programs"][0]["id"].startswith(f"{domain}_bulk_")
        assert all(o["source_family"] == f"{domain}_bulk_forum"
                   for o in data["programs"][0]["observations"])
    assert configs[0] == configs[1]
