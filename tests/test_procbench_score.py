#!/usr/bin/env python3
"""Tests for the process-benchmark scorer (pipeline/procbench).

Run: python3 -m pytest tests/test_procbench_score.py -q
 or: python3 tests/test_procbench_score.py
Offline alignment only — no LLM calls, no network.
"""

import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from procbench import align as A            # noqa: E402
from procbench import score as S            # noqa: E402

# --------------------------------------------------------------- tiny fixtures

GOLD = {
    "model_id": "J9__S01", "source": "designed", "jurisdiction": "City of Testville",
    "stat_id": "S01", "version": 2, "version_date": "2025-04-01",
    "actors": [{"id": "applicant", "name": "Applicant"},
               {"id": "permit_center", "name": "Permit Services Counter"},
               {"id": "building_division", "name": "Building Division"},
               {"id": "inspector", "name": "City Inspector"}],
    "activities": [
        {"id": "A1", "name": "Submit application", "local_name": "File amnesty application",
         "actor": "applicant", "visibility": "applicant_facing", "element_ref": "E1",
         "occasion": "online", "timing": {"dist": "lognormal", "median_days": 1, "p90_days": 3},
         "fee": {"amount": 430, "when": "at submittal"}},
        {"id": "A2", "name": "Intake completeness check", "local_name": "Application screening",
         "actor": "permit_center", "visibility": "applicant_inferable", "element_ref": "E2",
         "occasion": "internal", "timing": {"median_days": 4, "p90_days": 12}},
        {"id": "A3", "name": "Internal routing to plan check queue", "actor": "permit_center",
         "visibility": "staff_only", "element_ref": None, "occasion": "internal",
         "timing": {"median_days": 3}},
        {"id": "A4", "name": "Site inspection of the unit", "local_name": "Field inspection",
         "actor": "inspector", "visibility": "applicant_facing", "element_ref": "E3",
         "occasion": "site_visit", "timing": {"median_days": 10},
         "fee": {"amount": 120, "when": "at inspection"},
         "rework": {"p_trigger": 0.3, "back_to": "A1", "reason": "violations found"}},
        {"id": "A5", "name": "Fee reconciliation and records archiving",
         "actor": "building_division", "visibility": "staff_only", "element_ref": None,
         "occasion": "internal", "timing": {"median_days": 6}},
        {"id": "A6", "name": "Issue certificate of compliance", "actor": "building_division",
         "visibility": "applicant_facing", "element_ref": "E4", "occasion": "mail",
         "timing": {"median_days": 5}},
    ],
    "edges": [{"from": "A1", "to": "A2", "type": "sequence"},
              {"from": "A2", "to": "A3", "type": "handoff"},
              {"from": "A3", "to": "A4", "type": "handoff"},
              {"from": "A4", "to": "A5", "type": "handoff"},
              {"from": "A5", "to": "A6", "type": "sequence"},
              {"from": "A4", "to": "A1", "type": "rework", "condition": "violations found"}],
    "terminal_artifact": "Certificate of Compliance", "denial_rate": 0.08,
    "prior_version": {"changes": ["fee was $390", "no pre-application meeting",
                                  "Planning ran intake"]},
}

CEILING = {"task_id": "W9__J9__S01", "elements_total": 6,
           "recoverable_exact": ["A1", "A4", "A6"], "recoverable_approx": ["A2"],
           "only_wrong": [], "hidden": ["A3", "A5"],
           "timing_ceiling": {"true_median_days": 29, "best_estimate_from_posts": 41,
                              "n_posts_with_timing": 5},
           "distractor_count": 12}

DISTRACTOR = {
    "model_id": "J9__S07", "source": "designed", "jurisdiction": "City of Testville",
    "actors": [{"id": "applicant"}, {"id": "finance"}],
    "activities": [
        {"id": "B1", "name": "Register the short-term rental unit", "actor": "applicant",
         "visibility": "applicant_facing"},
        {"id": "B2", "name": "Remit transient occupancy tax to the Finance Department",
         "actor": "applicant", "visibility": "applicant_facing"},
        {"id": "B3", "name": "Annual short-term rental registration renewal",
         "actor": "applicant", "visibility": "applicant_facing"},
    ],
    "edges": [{"from": "B1", "to": "B2", "type": "sequence"},
              {"from": "B2", "to": "B3", "type": "sequence"}],
}

PERFECT = {
    "model_id": "pred_perfect", "source": "declared", "jurisdiction": "City of Testville",
    "actors": ["applicant", "permit_center", "building", "inspector"],
    "activities": [
        {"id": "P1", "name": "File the amnesty application", "actor": "applicant",
         "timing": {"median_days": 1}, "fee": {"amount": 430}, "confidence": 0.9,
         "evidence": ["https://testville.gov/amnesty"]},
        {"id": "P2", "name": "Application screening for completeness", "actor": "permit_center",
         "timing": {"median_days": 4}, "confidence": 0.7, "evidence": []},
        {"id": "P3", "name": "Internal routing to the plan check queue", "actor": "permit_center",
         "timing": {"median_days": 3}, "confidence": 0.4},
        {"id": "P4", "name": "Inspection of the unit (site visit)", "actor": "inspector",
         "timing": {"median_days": 10}, "fee": {"amount": 120}, "confidence": 0.85},
        {"id": "P5", "name": "Fee reconciliation and records archiving", "actor": "building",
         "timing": {"median_days": 6}, "confidence": 0.3},
        {"id": "P6", "name": "Grant the certificate of compliance", "actor": "building",
         "timing": {"median_days": 5}, "confidence": 0.9},
    ],
    "edges": [{"from": "P1", "to": "P2", "type": "sequence"},
              {"from": "P2", "to": "P3", "type": "sequence"},
              {"from": "P3", "to": "P4", "type": "handoff"},
              {"from": "P4", "to": "P5", "type": "handoff"},
              {"from": "P5", "to": "P6", "type": "sequence"},
              {"from": "P4", "to": "P1", "type": "rework"}],
    "terminal_artifact": "certificate of compliance",
}


def _mod(base, **kw):
    out = json.loads(json.dumps(base))
    out.update(kw)
    return out


def run_score(pred, tmp, name="score.json", **flags):
    d = pathlib.Path(tmp)
    (d / "pred.json").write_text(json.dumps(pred))
    (d / "gold.json").write_text(json.dumps(GOLD))
    (d / "ceiling.json").write_text(json.dumps(CEILING))
    (d / "distractor.json").write_text(json.dumps(DISTRACTOR))
    argv = ["--pred", str(d / "pred.json"), "--gold", str(d / "gold.json"),
            "--ceiling", str(d / "ceiling.json"), "--task", "W9__J9__S01",
            "--distractors", str(d / "distractor.json"),
            "--align", flags.pop("align", "offline"), "--out", str(d / name)]
    for k, v in flags.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    return S.main(argv)


# ------------------------------------------------------------------- the tests

def test_perfect_prediction():
    with tempfile.TemporaryDirectory() as tmp:
        r = run_score(PERFECT, tmp, condition="oracle_docs")
        m = r["metrics"]
        assert m["activity"]["precision"]["value"] == 1.0, m["activity"]["precision"]
        assert m["activity"]["recall_all"]["value"] == 1.0, m["activity"]["missed_gold"]
        assert m["activity"]["f1"] == 1.0
        assert m["activity"]["recall_visible"]["value"] == 1.0
        assert m["activity"]["recall_ceiling"]["value"] == 1.0
        assert m["order_agreement"]["value"] == 1.0, m["order_agreement"]
        assert m["order_agreement"]["den"] == 15          # 6-activity chain closure
        assert m["actor_accuracy"]["value"] == 1.0, m["actor_accuracy"]["wrong"]
        assert m["rework"]["recall"]["value"] == 1.0
        assert m["hallucination"]["value"] == 0.0
        assert m["fee"]["mean_abs_err"] == 0.0 and m["fee"]["n_compared"] == 2
        assert m["timing"]["mean_abs_log_ratio"] == 0.0
        assert m["disentanglement"]["failures"]["num"] == 0
        assert m["staleness"]["total_stale_facts"] == 0
        # the alignment table is written next to score.json and is human-checkable
        al = json.loads((pathlib.Path(tmp) / "score.alignment.json").read_text())
        assert len(al["pairs"]) == 6 and all(p["score"] > 0.9 for p in al["pairs"])


def test_canonical_edges_and_explicit_payer_roles_are_not_lost():
    normalized = A.load_model({'activities': [
        {'id': 'a', 'name': 'File', 'actor': 'Private mobile food merchant', 'actor_role': 'payer'},
        {'id': 'b', 'name': 'Review', 'actor': 'Agency'},
        {'id': 'c', 'name': 'Check', 'actor': 'Agency'}],
        'edges': [{'source': 'a', 'target': 'b', 'kind': 'precedes'},
                  {'source': 'b', 'target': 'c', 'kind': 'parallel'}]})
    assert normalized['by_id']['a']['actor'] == 'applicant'
    assert A.closure(normalized['activities'], normalized['edges']) == {('a', 'b')}
    assert normalized['edges'][1]['kind'] == 'parallel'


def test_missing_staff_only_hits_recall_but_not_ceiling_recall():
    """(ii) the two staff_only activities are below the information ceiling:
    recall(all) < 1 while ceiling-relative recall stays 1.0."""
    pred = _mod(PERFECT, activities=[a for a in PERFECT["activities"]
                                     if a["id"] not in ("P3", "P5")],
                edges=[{"from": "P1", "to": "P2", "type": "sequence"},
                       {"from": "P2", "to": "P4", "type": "handoff"},
                       {"from": "P4", "to": "P6", "type": "handoff"},
                       {"from": "P4", "to": "P1", "type": "rework"}])
    with tempfile.TemporaryDirectory() as tmp:
        m = run_score(pred, tmp, condition="declared_only")["metrics"]
        act = m["activity"]
        assert act["recall_all"]["num"] == 4 and act["recall_all"]["den"] == 6
        assert act["recall_all"]["value"] < 1.0
        assert act["recall_ceiling"]["value"] == 1.0, act["recall_ceiling"]
        assert act["recall_ceiling"]["den"] == 4
        assert sorted(act["missed_gold_staff_only"]) == ["A3", "A5"]
        assert act["precision"]["value"] == 1.0 and m["hallucination"]["value"] == 0.0
        assert m["order_agreement"]["value"] == 1.0


def test_distractor_contamination_counted():
    """(iii) a predicted activity copied from the distractor process."""
    pred = _mod(PERFECT, activities=PERFECT["activities"] + [
        {"id": "P7", "name": "Remit transient occupancy tax to the Finance Department",
         "actor": "applicant"}])
    with tempfile.TemporaryDirectory() as tmp:
        m = run_score(pred, tmp, condition="search")["metrics"]
        dis = m["disentanglement"]
        assert dis["failures"]["num"] == 1, dis["detail"]
        assert dis["failures"]["den"] == 7
        assert dis["detail"][0]["pred"] == "P7"
        assert dis["detail"][0]["best_distractor"].startswith("J9__S07:B2")
        assert dis["detail"][0]["distractor_score"] > dis["detail"][0]["best_gold_score"]
        assert dis["among_unmatched"] == 1
        assert m["hallucination"]["num"] == 1        # it also matched no gold activity
        assert m["activity"]["recall_all"]["value"] == 1.0


def test_stale_fee_counted():
    """(iv) the prior version's $390 fee, reported as current."""
    acts = json.loads(json.dumps(PERFECT["activities"]))
    acts[0]["fee"] = {"amount": 390}
    pred = _mod(PERFECT, activities=acts)
    with tempfile.TemporaryDirectory() as tmp:
        m = run_score(pred, tmp)["metrics"]
        st = m["staleness"]
        assert st["prior_version_present"] is True
        assert st["stale_fee"]["num"] == 1, st
        assert st["stale_fee"]["detail"][0]["fee"] == 390.0
        assert st["total_stale_facts"] == 1
        assert m["fee"]["mean_abs_err"] == 20.0     # (|390-430| + |120-120|)/2


def test_granularity_one_pred_covers_two_gold():
    """(v) many-to-one: one predicted activity is matched to BOTH gold
    activities it covers, and both count toward recall."""
    acts = [a for a in json.loads(json.dumps(PERFECT["activities"]))
            if a["id"] not in ("P2", "P3")]
    acts.insert(1, {"id": "P23", "actor": "permit_center", "timing": {"median_days": 7},
                    "name": "Staff screen the application for completeness and route it "
                            "to the plan check queue"})
    pred = _mod(PERFECT, activities=acts,
                edges=[{"from": "P1", "to": "P23", "type": "sequence"},
                       {"from": "P23", "to": "P4", "type": "handoff"},
                       {"from": "P4", "to": "P5", "type": "handoff"},
                       {"from": "P5", "to": "P6", "type": "sequence"},
                       {"from": "P4", "to": "P1", "type": "rework"}])
    with tempfile.TemporaryDirectory() as tmp:
        r = run_score(pred, tmp)
        m, al = r["metrics"], json.loads((pathlib.Path(tmp) / "score.alignment.json").read_text())
        covered = sorted(p["gold"] for p in al["pairs"] if p["pred"] == "P23")
        assert covered == ["A2", "A3"], al["pairs"]
        assert r["alignment"]["n_many_to_one"] >= 1
        assert m["activity"]["recall_all"]["value"] == 1.0
        assert m["activity"]["precision"]["value"] == 1.0
        assert m["hallucination"]["value"] == 0.0
        # the merged pair has no internal order: reported as conflated, not a violation
        assert m["order_agreement"]["conflated"] == 1
        assert m["order_agreement"]["value"] == 1.0


def test_aggregate_decomposition_and_reliability():
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        thin = _mod(PERFECT, activities=[a for a in PERFECT["activities"]
                                         if a["id"] in ("P1", "P4")])
        for sub, pred, cond in (("r1", PERFECT, "oracle_docs"), ("r2", PERFECT, "oracle_docs"),
                                ("r3", thin, "search")):
            (d / sub).mkdir()
            run_score(pred, tmp, name=f"{sub}/score.json", condition=cond)
        summ = S.main(["aggregate", "--runs", str(d / "*" / "score.json"),
                       "--out", str(d / "summary.json")])
        assert summ["n_runs"] == 3
        assert summ["by_condition"]["oracle_docs"]["n_runs"] == 2
        assert summ["by_condition"]["oracle_docs"]["means"]["f1"] == 1.0
        assert summ["by_condition"]["oracle_docs"]["pooled"]["recall_all"]["den"] == 12
        dec = summ["decomposition"]["per_task"][0]
        assert dec["availability"] == round(1 - 4 / 6, 4)     # ceiling 4 of 6 truth elements
        assert dec["reconciliation"] == 0.0                   # oracle recovers the whole ceiling
        assert dec["retrieval"] == 0.5                        # 1.0 - 0.5 under search
        rel = summ["reliability"]["per_task_condition"][0]
        assert rel["n_runs"] == 2 and rel["matched_gold_jaccard"] == 1.0
        assert summ["reliability"]["mean_pred_signature_jaccard"] == 1.0


STATUTE = {"stat_id": "S01", "state": "Testonia", "cite": "Test Gov. Code § 1",
           "skeleton": [{"element_id": "E1", "kind": "application", "name": "Submit application"},
                        {"element_id": "E2", "kind": "checklist_publication",
                         "name": "Completeness review", "optional": False},
                        {"element_id": "E3", "kind": "inspection", "name": "Inspection"},
                        {"element_id": "E4", "kind": "decision", "name": "Issue certificate"},
                        {"element_id": "E5", "kind": "appeal", "name": "Appeal", "optional": True}]}


def test_statute_element_coverage():
    with tempfile.TemporaryDirectory() as tmp:
        (pathlib.Path(tmp) / "statute.json").write_text(json.dumps(STATUTE))
        r = run_score(PERFECT, tmp, statute=str(pathlib.Path(tmp) / "statute.json"))
        ec = r["metrics"]["element_coverage"]
        assert ec["mode"] == "statute_truth.skeleton"
        assert ec["mandated"] == ["E1", "E2", "E3", "E4"]        # E5 is optional
        assert ec["coverage"]["value"] == 1.0 and ec["missing"] == []
        # a prediction that misses the inspection loses E3
        thin = _mod(PERFECT, activities=[a for a in PERFECT["activities"] if a["id"] != "P4"])
        r2 = run_score(thin, tmp, name="score2.json",
                       statute=str(pathlib.Path(tmp) / "statute.json"))
        assert r2["metrics"]["element_coverage"]["missing"] == ["E3"]


def test_llm_kvote_alignment_with_stubbed_backend():
    """The k-vote path (crosswalk_eval pattern) without touching a backend:
    pairs need ceil(k/2) votes, and `both` reports offline-vs-LLM agreement."""
    calls = {"n": 0}
    real = A._llm_json_inline

    def fake(user, model=None, max_tokens=16000):
        calls["n"] += 1
        pairs = [{"pred": f"P{i}", "gold": f"A{i}"} for i in range(1, 7)]
        if calls["n"] == 2:                       # one dissenting run: 1 vote only, dropped
            pairs = pairs[:-1] + [{"pred": "P6", "gold": "A5"}]
        return {"pairs": pairs}

    A._llm_json_inline = fake
    try:
        pred, gold = A.load_model(PERFECT), A.load_model(GOLD)
        pairs, info = A.llm_align(pred, gold, k=3)
        assert calls["n"] == 3 and info["votes_needed"] == 2
        assert sorted((p["pred"], p["gold"]) for p in pairs) == \
            [(f"P{i}", f"A{i}") for i in range(1, 7)]
        assert all(p["votes"] >= 2 for p in pairs)      # P6->A5 had 1 vote: dropped
        ag = A.agreement(A.offline_align(pred, gold), pairs)
        assert ag["jaccard"] == 1.0
        with tempfile.TemporaryDirectory() as tmp:            # --align both end-to-end
            r = run_score(PERFECT, tmp, name="both.json", align="both")
            assert r["alignment"]["mode_used"] == "llm"
            assert r["alignment"]["offline_vs_llm_agreement"]["jaccard"] == 1.0
            assert r["alignment"]["llm"]["votes_needed"] == 2
            assert r["metrics"]["activity"]["f1"] == 1.0
    finally:
        A._llm_json_inline = real


def test_synonym_and_actor_canonicalization():
    """Alignment-noise guards: the synonym table and the lane-name map."""
    assert A.toks("Plan check") == A.toks("plan review") == {"review"}
    assert A.toks("site visit") == A.toks("Inspection") == {"inspect"}
    assert A.toks("submit") == A.toks("apply") == A.toks("file") == {"submit"}
    assert A.toks("issue") == A.toks("grant") == A.toks("approve") == {"issue"}
    assert A.canon_actor("Building Division") == A.canon_actor("building_official") == "building"
    assert A.canon_actor("homeowner") == A.canon_actor("Property Owner") == "applicant"
    assert A.actor_compat("building", "building") == 1.0
    assert A.actor_compat("building", "applicant") == 0.0
    assert 0 < A.actor_compat("building", "inspector") < 1      # both city-side lanes


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as e:                              # noqa: BLE001
                fails += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    print("all passed" if not fails else f"{fails} failure(s)")
    sys.exit(1 if fails else 0)
