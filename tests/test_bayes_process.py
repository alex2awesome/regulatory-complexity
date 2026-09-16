"""Offline mathematical/regression tests; no gold enters inference."""
import copy
import math
import random

import pytest

from pipeline.procbench import align, metrics
from pipeline.procbench.bayes_evidence import flatten, duration_claim, tokens
from pipeline.procbench.bayes_process import (Config, StructurePosterior, fit, normal_logpdf,
                                             probabilities, simulate_case, timing_grid, topological,
                                             point_actor, summarize_burden, sample_relations)
from pipeline.procbench.run_bayes_synth import crps


def evidence():
    docs = []
    for i in range(3):
        doc = {"id": f"d{i}", "kind": "staff_report", "source_family": f"source{i}", "claims": []}
        for j, name in enumerate(("Submit packet", "Inspect site")):
            doc["claims"].append({"claim_id": f"d{i}:{j}", "doc_id": doc["id"],
                                  "source_family": doc["source_family"], "source_kind": doc["kind"],
                                  "name": name, "actor": "applicant" if j == 0 else "building office",
                                  "precedes": ["Inspect site"] if j == 0 else [], "measurements": []})
        docs.append(doc)
    return {"documents": docs}


def measurement(value, kind="observed", source="s", **extra):
    return {"value": value, "kind": kind, "source": source,
            "source_kind": "official_stats", "field": "elapsed_days", **extra}


def mean_log_mu(grid):
    return sum(mu * w for (mu, sigma), w in zip(grid["states"], grid["weights"]))


def variance_log_mu(grid):
    m = mean_log_mu(grid)
    return sum((mu - m) ** 2 * w for (mu, sigma), w in zip(grid["states"], grid["weights"]))


def node(days, **extra):
    return {"mu": math.log(days), "sigma": 0., "actor": "building office",
            "p_occurs": 1., **extra}


def test_scorer_reads_actual_process_prediction_and_not_targets():
    pred = align.load_model({"process_timing": {"median_days": 240}, "activities": [
        {"id": "a", "name": "review", "timing": {"value_days": 30, "kind": "statutory_cap"}},
        {"id": "b", "name": "inspect", "timing": {"value_days": 8, "kind": "observed"}}]})
    assert pred["end_to_end"] == 240
    assert pred["by_id"]["a"]["median_days"] is None
    assert pred["by_id"]["b"]["median_days"] == 8


def test_scorer_never_substitutes_a_sum_of_medians():
    model = align.load_model({"activities": [{"id": "a", "name": "review", "timing": {"median_days": 10}}]})
    result = metrics.timing_metrics(model, model, [])
    assert result["end_to_end"]["pred_median_days"] is None
    assert result["end_to_end"]["gold_median_days"] is None
    result = metrics.timing_metrics(model, model, [], log_summary={"median_days": 25})
    assert result["end_to_end"]["gold_median_days"] == 25


def test_cache_adapter_keeps_clock_types_separate():
    doc = {"id": "d", "kind": "ordinance", "source_family": "d"}
    cap = duration_claim({"value_days": 30, "kind": "statutory_cap"}, doc)
    assert not cap["usable"]
    business = duration_claim({"value_days": 1, "kind": "observed", "quote": "one business day"}, doc)
    assert not business["usable"] and business["units"] == "business_days"
    interval = duration_claim({"value_days": 21, "kind": "observed", "quote": "2 to 4 weeks"}, doc)
    assert interval["interval"] == [14, 28]


def test_alias_and_literal_name_have_identical_features():
    assert tokens("Submit application") == tokens("File application") == ["file"]


def test_ambiguous_actor_point_estimate_abstains():
    assert point_actor(["applicant", "building office"], [.5, .5]) == "unknown"
    assert point_actor(["applicant", "building office"], [.1, .9]) == "building office"


def test_count_posterior_is_normalized_and_respects_represented_count():
    p = StructurePosterior(evidence(), Config(max_steps=30))
    ns, weights = p.count_distribution(4)
    assert min(ns) == 4 and max(ns) == 30
    assert sum(weights) == pytest.approx(1)
    assert 0 < p.q0 < 1


def test_more_source_exposure_reduces_unseen_count_conditionally():
    e = evidence()
    p1 = StructurePosterior(e)
    for i in range(15):
        e["documents"].append({"id": f"empty{i}", "kind": "sop", "claims": []})
    p2 = StructurePosterior(e)
    n1, w1 = p1.count_distribution(2); n2, w2 = p2.count_distribution(2)
    assert sum(n*w for n, w in zip(n2, w2)) < sum(n*w for n, w in zip(n1, w1))


def test_exact_copies_in_known_source_family_do_not_increase_evidence():
    e = evidence()
    p1 = StructurePosterior(e)
    copied = copy.deepcopy(e["documents"][0]); copied["id"] = "copy"
    for c in copied["claims"]:
        c["claim_id"] = "copy:" + c["claim_id"]
        c["doc_id"] = "copy"
    e["documents"].append(copied)
    p2 = StructurePosterior(e)
    assert len(p1.claims) == len(p2.claims)
    assert p1.q0 == p2.q0


def test_document_order_is_irrelevant_to_fixed_seed_posterior():
    e = evidence()
    cfg = Config(chains=2, sweeps=20, burn=5, thin=5)
    p1 = StructurePosterior(e, cfg).sample()[0]
    e["documents"].reverse()
    p2 = StructurePosterior(e, cfg).sample()[0]
    assert p1 == p2


def test_explicit_precedence_prevents_collapsing_two_activities():
    p = StructurePosterior(evidence())
    assert p.cluster_log(frozenset((0, 1))) == -math.inf
    assert math.isfinite(p.cluster_log(frozenset((0, 2))))


def test_deadlines_do_not_change_duration_posterior():
    prior = timing_grid([])
    cap = timing_grid([measurement(365, "statutory_cap")])
    assert cap["weights"] == prior["weights"]
    assert cap["n_observations"] == 0


def test_process_summaries_and_business_days_are_not_step_calendar_durations():
    prior = timing_grid([])
    excluded = timing_grid([measurement(365, "median", scope="process"),
                            measurement(30, "observed", units="business_days")])
    assert excluded["weights"] == prior["weights"]
    assert len(excluded["excluded"]) == 2


def test_zero_waits_are_not_discarded():
    grid = timing_grid([measurement(0)])
    assert grid["n_observations"] == 1
    assert mean_log_mu(grid) < mean_log_mu(timing_grid([]))


def test_many_cases_median_is_not_one_individual_wait():
    individual = timing_grid([measurement(12)])
    median = timing_grid([measurement(12, "median", n=10000)])
    assert variance_log_mu(median) < variance_log_mu(individual)


def test_duplicated_timing_claim_is_not_an_independent_observation():
    claim = measurement(12)
    assert timing_grid([claim])["weights"] == timing_grid([claim, claim])["weights"]


def test_parallel_work_uses_critical_path_not_sum():
    nodes = [node(1), node(10), node(20), node(1, is_decision=True)]
    result = simulate_case(nodes, [(0,1), (0,2), (1,3), (2,3)], [], random.Random(1))
    assert result["elapsed_to_decision_days"] == pytest.approx(22)
    assert result["agency_hours"] is None  # days are not staff hours
    assert result["agency_step_executions"] == 4


def test_separate_applicant_and_agency_work_hours():
    nodes = [node(3, actor="applicant", applicant_hours=(math.log(2), 0.)),
             node(30, agency_hours=(math.log(1), 0.), is_decision=True)]
    result = simulate_case(nodes, [(0,1)], [], random.Random(1))
    assert result["elapsed_to_decision_days"] == pytest.approx(33)
    assert result["applicant_hours"] == pytest.approx(2)
    assert result["agency_hours"] == pytest.approx(1)


def test_rework_repeats_path_but_not_flat_fee():
    nodes = [node(1, fee=100), node(2), node(1, is_decision=True)]
    result = simulate_case(nodes, [(0,1), (1,2)], [(1,0,1.)], random.Random(1), max_repeats=2)
    assert result["step_executions"] == 7
    assert result["repeat_executions"] == 4
    assert result["elapsed_to_decision_days"] == pytest.approx(10)
    assert result["documented_fees"] == 100
    nodes[0]["fee_per_visit"] = True
    result = simulate_case(nodes, [(0,1), (1,2)], [(1,0,1.)], random.Random(1), max_repeats=2)
    assert result["documented_fees"] == 300


def test_shared_transaction_and_encounter_are_counted_once():
    nodes = [node(1, fee=25, transaction_id="payment", occasion="counter", encounter_id="trip"),
             node(1, fee=25, transaction_id="payment", occasion="counter", encounter_id="trip")]
    result = simulate_case(nodes, [(0,1)], [], random.Random(1))
    assert result["documented_fees"] == 25
    assert result["encounter_upper_proxy"] == 1


def test_base_graph_cycles_are_rejected():
    assert topological([0,1], [(0,1),(1,0)]) is None
    with pytest.raises(ValueError, match="acyclic"):
        simulate_case([node(1),node(1)], [(0,1),(1,0)], [], random.Random(1))


def test_conflicting_relation_evidence_yields_a_valid_dag():
    observed = {(0, 1): {"a": .99}, (1, 2): {"a": .99}, (2, 0): {"a": .99},
                (1, 0): {"b": .99}}
    for seed in range(5):
        edges = sample_relations(3, observed, random.Random(seed))
        assert topological(range(3), edges) is not None


def test_conditional_means_do_not_drop_partially_defined_graph_draws():
    batches = [[{"elapsed": 2}, {"elapsed": None}], [{"elapsed": 8}, {"elapsed": 12}]]
    result = summarize_burden(batches)["elapsed"]
    assert result["posterior_expected"]["mean"] == 6
    assert result["posterior_expected"]["n"] == 2
    assert result["status"] == "conditional_on_defined"


def test_missing_work_hours_cannot_be_reported_as_zero_burden():
    result = summarize_burden([[{"applicant_hours": 0}, {"applicant_hours": None}]])["applicant_hours"]
    assert result["case_predictive"]["median"] is None
    assert result["posterior_expected"]["median"] is None
    assert result["fraction_defined"] == .5
    assert result["status"] == "unmeasured"


def test_small_fit_is_reproducible_and_serializable():
    import json
    cfg = Config(chains=2, sweeps=12, burn=6, thin=3, cases_per_draw=2)
    a, ds, cs = fit(evidence(), cfg)
    b, _, _ = fit(evidence(), cfg)
    assert a == b
    json.dumps(a, allow_nan=False)
    assert a["diagnostics"]["n_draws"] == 4
    assert a["unseen_step_count"]["median"] >= 0


def test_crps_matches_direct_pairwise_formula():
    xs = [1, 2, 5, 8]; y = 3
    expected = sum(abs(x-y) for x in xs)/len(xs) - sum(abs(x-z) for x in xs for z in xs)/(2*len(xs)**2)
    assert crps(xs, y) == pytest.approx(expected)
