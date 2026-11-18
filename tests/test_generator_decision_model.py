"""Decision layer (benchmark/synth/generator/decision.py): statute -> decision
function -> jurisdiction readings -> process -> simulated outcomes -> artifacts.

Guards: the legacy (version 1) path is byte-identical to the pre-decision-layer
generator; version 2 worlds validate, attach every predicate to a real activity,
drive corrections and denials from predicate evaluations, disclose readings at
the right places, and give a decision ceiling that partitions the predicates.
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import pathlib
import random
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.synth.generator import decision, simulate  # noqa: E402
from benchmark.synth.generator.build import build  # noqa: E402
from benchmark.synth.generator.test_generator import TINY_KNOBS  # noqa: E402

# Captured on 2026-09-16 from the generator *before* the decision layer existed
# (same TINY_KNOBS, seed 3). Processes must hash identically under version 1.
V1_SUMMARIES = {"J1__S01": [83.5, 112.8, 0.25, 0.6], "J1__S03": [63.0, 81.8, 0.05, 1.0],
                "J1__S07": [16.5, 31.9, 0.0, 1.0], "J3__S01": [152.5, 226.0, 0.06, 1.8],
                "J3__S03": [81.5, 105.8, 0.0, 0.3], "J3__S07": [19.5, 51.0, 0.11, 2.75]}
V1_PROCESSES_SHA256 = "bb62658e53fd0dd023e5e87504ca2d296fd5b6517ae5efc4225701e3a6ead8aa"


@pytest.fixture(scope="module")
def v2_world():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="decision_v2_"))
    build("WTEST", 3, str(tmp), dict(TINY_KNOBS))
    return tmp


def _load_all(root: pathlib.Path, sub: str) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in sorted((root / sub).glob("*.json"))}


def test_legacy_version_is_byte_identical_to_the_pre_decision_generator():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="decision_v1_"))
    knobs = dict(TINY_KNOBS)
    knobs["decision_model_version"] = 1
    build("WTEST", 3, str(tmp), knobs)
    h = hashlib.sha256()
    for p in sorted((tmp / "truth/processes").glob("*.json")):
        h.update(p.read_bytes())
    assert h.hexdigest() == V1_PROCESSES_SHA256
    for p in sorted((tmp / "truth/log").glob("*.summary.json")):
        s = json.loads(p.read_text())
        assert [s["elapsed_days"]["median"], s["elapsed_days"]["p90"], s["denial_rate"],
                s["mean_rework_rounds"]] == V1_SUMMARIES[s["model_id"]]
        assert "predicate_summary" not in s
    procs = _load_all(tmp, "truth/processes")
    assert all("decision_model" not in p for p in procs.values())
    stats = _load_all(tmp, "truth/statutes")
    assert all("decision_function" not in s for s in stats.values())


def test_v2_world_validates_and_attaches_every_predicate(v2_world):
    r = subprocess.run([sys.executable, str(ROOT / "benchmark/synth/schemas/validate.py"),
                        "--world", str(v2_world), "--quiet"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    world = json.loads((v2_world / "world.json").read_text())
    assert world["decision_model_version"] == 2
    procs = _load_all(v2_world, "truth/processes")
    rules = _load_all(v2_world, "truth/local_rules")
    stats = _load_all(v2_world, "truth/statutes")
    for mid, p in procs.items():
        dm = p["decision_model"]
        acts = {a["id"]: a for a in p["activities"]}
        assert len(dm["predicates"]) >= 3
        kinds = {e["kind"] for e in dm["predicates"]}
        assert {"crisp", "standard"} <= kinds
        for e in dm["predicates"]:
            host = acts[e["evaluated_at"]]
            assert e["pred_id"] in host["evaluates"]
            assert e["attribute"] in host["inputs_required"]
            assert e["reading"] == rules[mid]["readings"][e["pred_id"]]
            if e["fixable"]:
                order = [a["id"] for a in p["activities"]]
                assert order.index(e["correction_back_to"]) < order.index(e["evaluated_at"])
        # the statute fixes crisp tests, states no number for standards, delegates the rest
        df = {d["pred_id"]: d for d in stats[p["stat_id"]]["decision_function"]}
        for e in dm["predicates"]:
            if e["kind"] == "crisp":
                assert df[e["pred_id"]]["statutory_reading"]["label"] == e["reading"]["label"] \
                    or e["reading"]["misimplemented"]
            if e["kind"] == "standard":
                assert df[e["pred_id"]]["standard"]
                assert e["reading"]["label"] in {r["label"] for r in df[e["pred_id"]]["reading_space"]}
            if e["kind"] == "delegated":
                assert df[e["pred_id"]]["choice_id"] in rules[mid]["choices"]
        assert "state NO numeric threshold" in stats[p["stat_id"]]["sections"][1]["content_spec"]
        # the free denial parameter became a derived quantity
        assert p["denial_rate"] == pytest.approx(max(0.005, dm["expected_fatal_fail_rate"]))


def test_simulated_outcomes_follow_the_predicates(v2_world):
    procs = _load_all(v2_world, "truth/processes")
    for mid, p in procs.items():
        recs = [json.loads(l) for l in (v2_world / ("truth/log/%s.jsonl" % mid)).read_text().splitlines() if l.strip()]
        summ = json.loads((v2_world / ("truth/log/%s.summary.json" % mid)).read_text())
        fixable = {e["pred_id"] for e in p["decision_model"]["predicates"] if e["fixable"]}
        for r in recs:
            assert set(r["case_attributes"]) >= {e["attribute"] for e in p["decision_model"]["predicates"]}
            basis = r["decision_basis"]
            outcome = r["provisional_outcome"] or r["outcome"]
            if outcome == "denied":
                assert basis["fatal_failures"] or basis["unresolved_fixable"]
            if outcome == "approved":
                assert not basis["fatal_failures"] and not basis["unresolved_fixable"]
            for pid in basis["fatal_failures"]:
                assert pid not in fixable
        assert set(summ["predicate_summary"]) == {e["pred_id"] for e in p["decision_model"]["predicates"]}


def _fixture_process(reading_value: float):
    base = dict(optional=False, p_occurs=None, actor="agency", per_case=True, flow_gate="always",
                blocking=True, occasion="online", fee=None, element_ref=None, visibility="applicant_facing",
                artifacts_out=[], rework=None, timing=dict(median_days=5, p90_days=10), evaluates=[],
                inputs_required=[])
    acts = [dict(copy.deepcopy(base), id=aid) for aid in ["file", "inspect", "decide"]]
    acts[0].update(actor="applicant")
    acts[2].update(element_ref="E1", artifacts_out=["permit"])
    acts[1]["evaluates"] = ["P2"]
    acts[1]["inputs_required"] = ["ceiling_height_ft"]
    entry = dict(pred_id="P2", name="ceiling", kind="standard", attribute="ceiling_height_ft", unit="feet",
                 element_ref="E2", evaluated_at="inspect", evaluated_by="agency",
                 evaluation_visibility="applicant_facing", fallback_to_decision=False, fixable=True,
                 correction_back_to="file", question="?", statute_text=None, standard="substandard",
                 choice_id=None, reading=dict(label="x", op="ge", value=reading_value, strictness=1),
                 case_attribute_dist=["normal", 7.25, 0.45], expected_fail_rate=None)
    proc = dict(model_id="test__permit", activities=acts, terminal_artifact="permit", denial_rate=0.5,
                p_appeal_if_denied=0,
                decision_model=dict(version=2, predicates=[entry], strictness_index=1, expected_fatal_fail_rate=0))
    return proc


def _run(reading_value, p_cure=0.0, version=2, n=300):
    knobs = dict(as_of="2026-09-15", p_abandon_total=0, max_rework_rounds=2, sim_window_days=760,
                 decision_model_version=version, p_cure=p_cure, visit_accounting_version=2)
    world = dict(seed=11, knobs=knobs)
    recs, summ = simulate.simulate_process(world, _fixture_process(reading_value), dict(effective="2026-01-01"), n)
    return recs, summ


def test_stricter_reading_corrects_and_denies_more_and_cure_resolves():
    lenient, _ = _run(6.5)
    strict, _ = _run(7.5)
    fail = lambda recs: sum(1 for r in recs if r["predicate_results"]["P2"]["failed_first"]) / len(recs)
    denied = lambda recs: sum(1 for r in recs if (r["provisional_outcome"] or r["outcome"]) == "denied") / len(recs)
    assert fail(strict) > fail(lenient) + 0.3
    assert denied(strict) > denied(lenient)
    # no cure: every first failure exhausts the retry cap and becomes a denial
    assert all(r["total_rework_rounds"] == 2 for r in strict if r["predicate_results"]["P2"]["failed_first"])
    cured, _ = _run(7.5, p_cure=1.0)
    assert all(r["predicate_results"]["P2"]["passed_ever"] for r in cured)
    assert denied(cured) == 0
    # the same case facts are drawn regardless of the reading
    assert [r["case_attributes"] for r in lenient] == [r["case_attributes"] for r in strict]


def test_legacy_version_ignores_the_decision_model():
    recs, summ = _run(7.5, version=1, n=50)
    assert "predicate_results" not in recs[0] and "predicate_summary" not in summ


def test_readings_are_disclosed_where_real_documents_state_them(v2_world):
    specs = _load_all(v2_world, "specs")
    procs = _load_all(v2_world, "truth/processes")
    by_kind: dict[str, list] = {}
    for s in specs.values():
        for r in s["reveals"]:
            if r.get("field") == "criterion":
                by_kind.setdefault(s["kind"], []).append((s, r))
    # statute text states the crisp test exactly and the standard without a number
    stat_specs = [s for s in specs.values() if s.get("subkind") == "statute_text"]
    assert stat_specs
    for s in stat_specs:
        crit = [r for r in s["reveals"] if r.get("field") == "criterion"]
        assert any(r["criterion_kind"] == "crisp" and r["fidelity"] == "exact" and r["must_quote"] for r in crit)
        assert all(r["fidelity"] == "vague" for r in crit if r["criterion_kind"] == "standard")
    assert "checklist" in by_kind and "ordinance" in by_kind
    assert all(r["fidelity"] == "exact" for _, r in by_kind["checklist"])
    # a poster describes the criterion they failed on, from their own case
    from_case = [r for s in specs.values() for r in s["reveals"] if r.get("from_case")]
    assert from_case and all(r["ref"].startswith(("P", "Q")) for r in from_case)
    # no spec states a criterion it must hide, and hidden criteria are staff-side
    for s in specs.values():
        crit = {r["ref"] for r in s["reveals"] if r.get("field") == "criterion"}
        assert not (crit & set(s.get("must_not_reveal_criteria", [])))
        mid = "%s__%s" % (s.get("jur"), s.get("stat_id")) if s.get("jur") and s.get("stat_id") else None
        if mid in procs:
            entries = {e["pred_id"]: e for e in procs[mid]["decision_model"]["predicates"]}
            for pid in s.get("must_not_reveal_criteria", []):
                assert entries[pid]["evaluation_visibility"] == "staff_only"


def test_decision_ceiling_partitions_predicates_and_never_hides_the_statute(v2_world):
    ceiling = json.loads((v2_world / "ceiling.json").read_text())
    procs = _load_all(v2_world, "truth/processes")
    tasks = json.loads((v2_world / "tasks.json").read_text())
    for c in ceiling:
        dc = c["decision_ceiling"]
        entries = {e["pred_id"]: e for e in procs[c["model_id"]]["decision_model"]["predicates"]}
        buckets = dc["recoverable_exact"] + dc["recoverable_approx"] + dc["only_wrong"] + dc["hidden"]
        assert sorted(buckets) == sorted(entries)
        for pid in dc["hidden"]:
            assert entries[pid]["kind"] != "crisp"      # the statute text is public
        assert set(dc["by_kind"]) == {e["kind"] for e in entries.values()}
    assert all("decision_model" in t["gold"] and "criteria" in t["prompt"] for t in tasks)


def test_reading_phrase_fidelities_and_cure():
    entry = dict(pred_id="P2", name="Ceiling height", attribute="h", unit="feet", standard="substandard condition",
                 question="What is the ceiling height?", kind="standard",
                 reading_space=[dict(label="at least 7 feet", op="ge", value=7.0),
                                dict(label="at least 6 feet 8 inches", op="ge", value=6.67)])
    reading = dict(label="at least 7 feet", op="ge", value=7.0, approx="about seven feet")
    rng = random.Random(1)
    assert decision.reading_phrase(entry, reading, "exact") == "at least 7 feet"
    assert decision.reading_phrase(entry, reading, "approximate") == "about seven feet"
    assert "standard" in decision.reading_phrase(entry, reading, "vague")
    assert decision.reading_phrase(entry, reading, "wrong", rng) == "at least 6 feet 8 inches"
    attrs = {"h": 6.0}
    assert not decision.evaluate(entry, reading, attrs)
    decision.cure(entry, reading, attrs)
    assert decision.evaluate(entry, reading, attrs)


# ---------------------------------------------------------------- capped ----
# Welf. & Inst. Code 17001.5 bounds each permitted restriction and leaves the
# rest open, and the counties pile onto the bounds: five verified at exactly the
# permitted 15 days, nine of eleven at exactly three months, against 3.2x-40x
# variance on the uncapped grant. Plan section 12 calls that the project's
# cleanest identification of statutory silence, because every county-level
# confounder is held fixed across the two families of dimension.

def test_capped_predicates_exist_and_respect_their_statutory_bound(v2_world):
    procs = _load_all(v2_world, "truth/processes")
    stats = _load_all(v2_world, "truth/statutes")
    seen = 0
    for mid, p in procs.items():
        for e in p["decision_model"]["predicates"]:
            if e["kind"] != "capped":
                continue
            seen += 1
            assert e["bound"] is not None, "a capped predicate must record its bound"
            value, op = e["reading"]["value"], e["reading"]["op"]
            assert value <= e["bound"], (
                "%s demands %s, beyond the statutory bound %s" % (e["pred_id"], value, e["bound"]))
            # the bound is in the statute, so the statute record carries it too
            df = {d["pred_id"]: d for d in stats[p["stat_id"]]["decision_function"]}
            assert df[e["pred_id"]]["bound"] == e["bound"]
            assert df[e["pred_id"]]["kind"] == "capped"
        assert all(e.get("bound") is None for e in p["decision_model"]["predicates"]
                   if e["kind"] != "capped"), "only a capped dimension has a bound"
    assert seen, "the tiny world should contain at least one capped predicate"


def test_the_statute_publishes_the_bound_but_not_the_local_choice(v2_world):
    """A bound is legislated, so it is always public; which value the jurisdiction
    picked under it is a local fact and must not be disclosed at statute level."""
    specs = _load_all(v2_world, "specs")
    procs = _load_all(v2_world, "truth/processes")
    capped = {e["pred_id"] for p in procs.values() for e in p["decision_model"]["predicates"]
              if e["kind"] == "capped"}
    statute_reveals = [r for s in specs.values() for r in s["reveals"]
                       if r.get("field") == "criterion" and r.get("level") == "statute"
                       and r["ref"] in capped]
    assert statute_reveals, "the statute text should disclose every bound"
    for r in statute_reveals:
        assert r["criterion_kind"] == "capped"
        # approximate, not exact: the bound is certain, the local choice is not
        assert r["fidelity"] == "approximate"
        assert "lesser" in r["value"]


def test_capped_dimensions_concentrate_and_uncapped_ones_spread():
    """The signature that makes the contrast a test: a bounded dimension piles
    onto its cap while an unbounded one disperses, under identical draws."""
    from benchmark.synth.generator import decision
    rng = random.Random(4)
    capped = decision._capped("PX", "Residency", "days_resident", "E1", ("lognormal", 400, 3000),
                              "15 days", "ge", 15, [("10 days", 10, .18), ("5 days", 5, .12)],
                              "How long resident?", "days")
    standard = decision._standard("PY", "Condition", "score", "E2", ("normal", .5, .2), "adequate",
                                  [decision._r("lenient", "ge", .3, 0, .34),
                                   decision._r("middling", "ge", .5, 1, .33),
                                   decision._r("strict", "ge", .7, 2, .33)],
                                  "What score?", "")
    def draws(spec, n=400):
        space = [dict(label=r["label"], op=r["op"], value=r["value"], strictness=r["strictness"],
                      weight=r["weight"]) for r in spec["readings"]]
        return [decision.weighted(rng, [(r, r["weight"]) for r in space])["label"] for _ in range(n)]
    cap_share = max(collections.Counter(draws(capped)).values()) / 400
    std_share = max(collections.Counter(draws(standard)).values()) / 400
    assert cap_share > 0.6, "a capped dimension should concentrate on its bound"
    assert std_share < 0.5, "an unbounded standard should disperse"
    assert cap_share > std_share + 0.2


def test_the_contrast_metric_refuses_to_reward_predicting_the_mode_everywhere():
    """Entropy recovery is trivially satisfiable when one reading holds most of
    the mass. The capped-versus-uncapped contrast must not be."""
    from pipeline.procbench.decision_metrics import cross

    def gold(mid, cap_value, std_value):
        def entry(pid, kind, attr, op, value, **extra):
            return dict(pred_id=pid, name=pid, kind=kind, attribute=attr, unit="", element_ref="E1",
                        evaluated_at="A01", evaluated_by="agency", evaluation_visibility="applicant_facing",
                        fallback_to_decision=False, fixable=True, correction_back_to=None, question="?",
                        statute_text=None, standard=None, choice_id=None,
                        reading=dict(label=str(value), op=op, value=value, strictness=1),
                        case_attribute_dist=["normal", 1, 1], **extra)
        return dict(model_id=mid, stat_id="S01", activities=[dict(id="A01", name="check")],
                    decision_model=dict(version=2, strictness_index=1, expected_fatal_fail_rate=0,
                                        predicates=[entry("P1", "capped", "a", "ge", cap_value, bound=15),
                                                    entry("P2", "standard", "b", "ge", std_value)]))
    # planted: everyone on the cap for P1, all different for P2
    golds = [gold("J%d" % i, 15, v) for i, v in enumerate((0.3, 0.5, 0.7, 0.9))]

    def truthful(g):
        return {"criteria": [{"name": e["pred_id"], "attribute": e["attribute"], "op": e["reading"]["op"],
                              "value": e["reading"]["value"]} for e in g["decision_model"]["predicates"]]}

    def modal(g):
        c = truthful(g)
        for x in c["criteria"]:
            x["value"] = 15 if x["attribute"] == "a" else 0.5
        return c

    good = cross([(truthful(g), g) for g in golds])
    lazy = cross([(modal(g), g) for g in golds])
    assert good["by_family"]["capped"]["planted_spread"] == 0.0
    assert good["by_family"]["uncapped"]["planted_spread"] > 0.5
    assert good["capped_vs_uncapped"]["direction_correct"] is True
    # the lazy predictor collapses the uncapped family it was supposed to spread
    assert lazy["by_family"]["uncapped"]["recovered_spread"] == 0.0
    assert lazy["capped_vs_uncapped"]["direction_correct"] is False
    # The gap is the scored statistic precisely because it stays defined when the
    # capped family behaves ideally: a ratio would be 0/0 there.
    assert good["capped_vs_uncapped"]["planted_gap"] > 0.5
    assert good["capped_vs_uncapped"]["recovered_gap"] > 0.5
    assert good["capped_vs_uncapped"]["gap_error"] < 0.05
    assert lazy["capped_vs_uncapped"]["recovered_gap"] == 0.0
    assert lazy["capped_vs_uncapped"]["gap_error"] > 0.5
