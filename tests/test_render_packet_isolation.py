"""A renderer packet must not carry private truth.

The plan names this as a blocker that must land before any W2 render: the
render preparation was handing legal kinds the FULL statute and local-rule truth
objects, including the planted per-predicate readings and the copied-from
lineage. Rendering at scale with that leak produces a corpus whose extraction
scores are meaningless, because the renderer was told the answer.

The projections are allowlists, so these tests check two different things: that
the named private fields are absent, and that a field NOT on the allowlist stays
out even when it is new. The second is what stops a later schema addition from
leaking silently.

No network, no paid calls.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from benchmark.synth.render.prepare_batch import (LOCAL_RULE_PUBLIC, PREDICATE_PUBLIC,
                                                  STATUTE_PUBLIC, public_local_rule,
                                                  public_statute)

WORLD = pathlib.Path(__file__).resolve().parents[1] / "benchmark/synth/worlds/W2_DEV_001"

# Each field with the task it would give away.
PRIVATE_LOCAL_RULE = {
    "readings": "the jurisdiction's planted reading of each predicate",
    "lineage_from": "which jurisdiction the text was copied from",
    "retrofit": "a generator design label",
    "prior_version": "the superseded values behind a stale document",
}
PRIVATE_STATUTE = {"shape": "a generator design label"}
PRIVATE_PREDICATE = {
    "statutory_reading": "the planted reading, including strictness and weight",
    "fixable": "whether a failed predicate can be cured",
}


def _sample(kind):
    d = WORLD / "truth" / kind
    if not d.exists():
        pytest.skip("no built world to project")
    return json.loads(sorted(d.glob("*.json"))[0].read_text())


def test_local_rule_projection_withholds_the_decision_answer():
    lr = _sample("local_rules")
    assert "readings" in lr, "the truth must still carry it; only the packet may not"
    out = public_local_rule(lr)
    for field, why in PRIVATE_LOCAL_RULE.items():
        assert field not in out, "%s leaks %s" % (field, why)


def test_statute_projection_keeps_statutory_wording_but_not_the_reading():
    st = _sample("statutes")
    out = public_statute(st)
    # the renderer needs the actual statutory text of each predicate
    if st.get("decision_function"):
        assert out["decision_function"], "the renderer must still get statutory wording"
        for p in out["decision_function"]:
            assert "statute_text" in p or "name" in p
            for field, why in PRIVATE_PREDICATE.items():
                assert field not in p, "%s leaks %s" % (field, why)
    for field, why in PRIVATE_STATUTE.items():
        assert field not in out, "%s leaks %s" % (field, why)


def test_projections_are_allowlists_so_new_fields_are_excluded_by_default():
    """The reason this is an allowlist. A field added to the truth schema later
    must not appear in a renderer packet until someone decides it is public."""
    assert public_statute({"stat_id": "S1", "a_field_invented_tomorrow": "secret"}) == {"stat_id": "S1"}
    assert public_local_rule({"jur": "C01", "another_new_private_field": 42}) == {"jur": "C01"}


def test_no_private_field_is_on_an_allowlist():
    for field in PRIVATE_LOCAL_RULE:
        assert field not in LOCAL_RULE_PUBLIC
    for field in PRIVATE_STATUTE:
        assert field not in STATUTE_PUBLIC
    for field in PRIVATE_PREDICATE:
        assert field not in PREDICATE_PUBLIC


def test_projection_of_a_real_world_packet_mentions_no_reading_label():
    """End-to-end string check: a reading's label is distinctive prose, so if it
    appears anywhere in the projected packet the projection missed a path."""
    lr = _sample("local_rules")
    labels = [r.get("label") for r in (lr.get("readings") or {}).values() if isinstance(r, dict)]
    blob = json.dumps(public_local_rule(lr))
    leaked = [l for l in labels if l and l in blob]
    # A reading label can legitimately coincide with an adopted choice value the
    # ordinance publishes; what must never appear is the readings STRUCTURE.
    assert "strictness" not in blob and "misimplemented" not in blob, leaked


def test_text_spec_does_not_leak_the_copied_from_lineage():
    """The allowlist withheld `lineage_from` and then handed the renderer the
    same fact in prose. 192 of this world's local rules carried a `text_spec`
    ending "Note the lineage: adapted from Zellwood County (Ordinance No.
    2021-11)", with an instruction to state it -- so the withholding achieved
    nothing, and a verifier caught the result in an ordinance that recited
    "based upon the model ordinance adopted by Granthorpe County".

    A field can be private in the schema and public in the prose assembled from
    it. That is the general lesson; this is the test that pins it down.
    """
    from benchmark.synth.render.prepare_batch import public_local_rule, scrub_text_spec

    spec = ("State the fee as $310. Note the lineage: adapted from Zellwood County "
            "(Ordinance No. 2021-11); the ordinance carries a tell: one subdivision "
            "still cross-references Zellwood Municipal Code. Close with the appeal route.")
    out = scrub_text_spec(spec)
    assert "Zellwood" not in out, "the source jurisdiction must not survive"
    assert "Note the lineage" not in out
    assert "$310" in out and "appeal route" in out, "the drafting instruction must survive"
    assert "tell" in out.lower(), "the planted tell is the INFERENCE channel and must survive"

    d = public_local_rule({"jur": "C01", "lineage_from": "C25", "text_spec": spec})
    assert "Zellwood" not in json.dumps(d)
    assert "lineage_from" not in d


def test_every_local_rule_with_lineage_is_scrubbed():
    """Swept across the whole built world, not just one example."""
    from benchmark.synth.render.prepare_batch import public_local_rule

    d = WORLD / "truth" / "local_rules"
    if not d.exists():
        pytest.skip("no built world")
    world = json.loads((WORLD / "world.json").read_text())
    shorts = {j["id"]: j["short"] for j in world["jurisdictions"]}
    leaking = []
    for f in d.glob("*.json"):
        lr = json.loads(f.read_text())
        src = lr.get("lineage_from")
        if not src:
            continue
        ts = public_local_rule(lr).get("text_spec", "")
        if "Note the lineage" in ts or str(src) in ts or shorts.get(src, "\0") in ts:
            leaking.append(f.stem)
    assert not leaking, "%d local rules still leak their source: %s" % (len(leaking), leaking[:5])


def test_legal_truth_is_artifact_scoped_not_batch_scoped():
    """A renderer must not see a sibling artifact's adopted figures.

    `legal_truth` used to be one dict at the top of the packet, shared by every
    renderer in the batch, so an artifact licensed only for a vague fee still
    received the sibling ordinance's exact `fee.amount` and full `choices`. A
    verifier flagged the channel on batch D09 before anything exploited it.
    """
    from benchmark.synth.render.prepare_batch import build_packet
    if not WORLD.exists():
        pytest.skip("no built world")
    batches = sorted((WORLD / "batches").glob("*.json"))
    batches = [b for b in batches if "input" not in b.name and b.stem != "index"]
    if not batches:
        pytest.skip("no batches built")
    # A test must never rewrite an input underneath an active render worker.
    batch = json.loads(batches[0].read_text())
    pkt = build_packet(WORLD, dict(batch, batch_id=batches[0].stem))
    assert "legal_truth" not in pkt, "no batch-wide legal_truth may exist"
    LEGAL = {"ordinance", "bill_analysis", "fee_resolution"}
    for s in pkt["specs"]:
        if s.get("kind") in LEGAL:
            own = s.get("legal_truth") or {}
            for key in own.get("local_rules", {}):
                assert key.startswith("%s__" % s.get("jur")), (
                    "%s received another jurisdiction's local rule: %s"
                    % (s["artifact_id"], key))
        else:
            assert "legal_truth" not in s, (
                "%s is not a legal kind and must receive no legal truth" % s["artifact_id"])


def test_choice_values_do_not_leak_the_strictness_comparison():
    """The FOURTH channel of the same kind, and the reason the pattern matters.

    `choices` and `stricter_standards` are legitimately public: an adopted
    ordinance states "English, Spanish, and Tagalog" and its own standards. But
    39 of this world's values carried a trailing generator annotation stating the
    COMPARISON too -- "(three languages, exceeding the statutory minimum)",
    "a hand-wash sink with 5 gallons of warm water, exceeding the state minimum".
    A verifier caught the result in an ordinance reading "which exceeds the two
    languages the state law requires", which hands over the local-versus-state
    comparison a solver is supposed to infer from the statute plus the value.

    Three channels leaked this way before it (lineage via text_spec, then via
    style.template_lineage, now strictness via choices), so the general lesson is
    asserted here too: an allowlist over FIELD NAMES protects nothing by itself,
    because the private fact travels inside a public field's prose.
    """
    from benchmark.synth.render.prepare_batch import public_local_rule, scrub_choice

    assert scrub_choice("English, Spanish, and Tagalog (three languages, exceeding "
                        "the statutory minimum)") == "English, Spanish, and Tagalog"
    assert scrub_choice("a 7-foot minimum ceiling height, exceeding the state "
                        "standard") == "a 7-foot minimum ceiling height"
    # an operative parenthetical, and an ordinary comma clause, must both survive
    assert scrub_choice("$75 (payable at submittal)") == "$75 (payable at submittal)"
    assert scrub_choice("two inspections, one before and one after occupancy") == \
        "two inspections, one before and one after occupancy"

    d = public_local_rule({"jur": "C01", "choices": {"C5": "A, B and C (exceeds the state minimum)"},
                           "stricter_standards": ["a 7-foot ceiling, exceeding the state standard"]})
    blob = json.dumps(d)
    assert "exceed" not in blob.lower() and "minimum)" not in blob


def test_no_public_field_carries_a_strictness_comparison_anywhere():
    """Swept across the whole built world, not just the examples."""
    import re
    from benchmark.synth.render.prepare_batch import public_local_rule

    d = WORLD / "truth" / "local_rules"
    if not d.exists():
        pytest.skip("no built world")
    pat = re.compile(r"exceed|stricter|more stringent|statutory minimum|"
                     r"than (the )?state law", re.I)
    leaking = []
    for f in d.glob("*.json"):
        out = public_local_rule(json.loads(f.read_text()))
        for v in (out.get("choices") or {}).values():
            if pat.search(str(v)):
                leaking.append((f.stem, str(v)[:60]))
        for s in (out.get("stricter_standards") or []):
            if pat.search(str(s)):
                leaking.append((f.stem, str(s)[:60]))
    assert not leaking, "%d public values still state the comparison: %s" % (
        len(leaking), leaking[:3])
