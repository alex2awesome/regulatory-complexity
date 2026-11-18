"""The three dependence types stay apart.

This is the plan's most consequential correctness requirement, because a fitter
that treats copies as independent observations contracts its posterior by a
factor of sqrt(n) it has not earned. The tests therefore check the *distinction*
rather than the counts: that copied text does not imply agreeing facts, that
agreeing facts do not imply copied text, and that each kind carries its own
deduplication rule.

No network, no paid calls, no benchmark truth.
"""
from __future__ import annotations

import pytest

from benchmark.synth.generator import lineage as lin
from benchmark.synth.generator.counties import build_counties


@pytest.fixture(scope="module")
def counties():
    return build_counties(101)


def test_the_three_kinds_are_distinct_and_named():
    assert set(lin.LINK_KINDS) == {lin.SAME_CASE, lin.SAME_COHORT, lin.COPIED_TEXT}
    assert len(lin.LINK_KINDS) == 3


def test_a_copied_text_link_must_name_its_mechanism():
    """The mechanism predicts what was copied and what was localised, which is
    what an extractor can actually exploit. An unnamed mechanism would make the
    link an inert 'related documents' field."""
    with pytest.raises(ValueError):
        lin.link(lin.COPIED_TEXT, "A", "B")
    ok = lin.link(lin.COPIED_TEXT, "A", "B", mechanism="peer_adoption")
    assert ok["mechanism"] == "peer_adoption"
    assert ok["localises"] and ok["preserves"]


def test_unknown_kinds_and_mechanisms_are_refused():
    with pytest.raises(ValueError):
        lin.link("related", "A", "B")
    with pytest.raises(ValueError):
        lin.link(lin.COPIED_TEXT, "A", "B", mechanism="osmosis")


def test_copied_text_does_not_imply_agreeing_facts():
    """Two counties can share prose while genuinely running different
    procedures: the real anchor is the CCW vendor pages and the shared
    eligibility-consortium templates, where the fee and the local practice are
    overridden underneath identical narrative."""
    for mech in ("consortium_template", "vendor_boilerplate", "peer_adoption"):
        l = lin.link(lin.COPIED_TEXT, "A", "B", mechanism=mech)
        assert l["facts_agree"] is False, mech
        assert l["localises"], "%s must name what does NOT travel" % mech


def test_agreeing_facts_do_not_imply_copied_prose():
    """Two publications can use different prose for the same case or cohort:
    the hearings reports restating one closed-case mean across an annual and a
    quarterly document."""
    l = lin.link(lin.SAME_COHORT, "claim1", "claim1/restated/1",
                 mechanism="restated_publication")
    assert l["facts_agree"] is True
    assert "framing" in l["localises"], "the wording changes, the aggregate does not"


def test_each_kind_carries_its_own_deduplication_rule():
    """The asymmetry is the point: copied prose must NOT have its facts
    deduplicated, because a locally overridden number is real information."""
    rep = lin.independence_report([
        lin.link(lin.SAME_CASE, "a", "b"),
        lin.link(lin.SAME_COHORT, "c", "d", mechanism="restated_publication"),
        lin.link(lin.COPIED_TEXT, "e", "f", mechanism="consortium_template"),
    ])
    rules = rep["deduplication_rule"]
    assert len(set(rules.values())) == 3, "three kinds, three different remedies"
    assert "NOT" in rules[lin.COPIED_TEXT], (
        "copied text must warn against deduplicating its facts")
    assert "one observation" in rules[lin.SAME_CASE]
    assert "no information" in rules[lin.SAME_COHORT]


# ------------------------------------------------------------ the panel graph

def test_consortium_copying_forms_a_star_not_a_chain(counties):
    """Every member descends from one template, not from each other. A chain
    would let a solver recover the adoption order, which the real data does not
    reveal."""
    links = lin.build_lineage(101, counties, {"p_template_lineage": 1.0})
    cons = [l for l in links if l["mechanism"] == "consortium_template"]
    assert cons
    for l in cons:
        assert l["source"].startswith("TEMPLATE:"), (
            "a consortium member must copy the template, never a sibling")
    derived = [l["derived"] for l in cons]
    assert len(derived) == len(set(derived)), "each county descends once"


def test_peer_adoption_is_acyclic(counties):
    """A county copies an earlier adopter, so the graph cannot contain a cycle."""
    links = lin.build_lineage(101, counties, {"p_template_lineage": 1.0})
    order = {c["id"]: i for i, c in enumerate(counties)}
    for l in links:
        if l["mechanism"] == "peer_adoption":
            assert order[l["source"]] < order[l["derived"]]


def test_the_single_county_consortium_copies_nobody(counties):
    """The real split is 39 / 18 / 1 and the lone county has no sibling to copy.
    A generator that gave it a template would invent a lineage."""
    links = lin.build_lineage(101, counties, {"p_template_lineage": 1.0})
    lone = [c["id"] for c in counties
            if sum(1 for o in counties if o["consortium"] == c["consortium"]) == 1]
    assert len(lone) == 1
    assert not [l for l in links
                if l["derived"] == lone[0] and l["mechanism"] == "consortium_template"]


def test_copying_can_be_switched_off_as_a_control(counties):
    assert lin.build_lineage(101, counties, {"p_template_lineage": 0.0}) == []


def test_lineage_is_deterministic(counties):
    knobs = {"p_template_lineage": 0.4}
    assert lin.build_lineage(101, counties, knobs) == lin.build_lineage(101, counties, knobs)
    assert lin.build_lineage(101, counties, knobs) != lin.build_lineage(202, counties, knobs)


def test_restatements_never_add_an_independent_measurement():
    claims = [dict(claim_id="c%d" % i, statistic="median") for i in range(40)]
    links = lin.restatements(101, claims, {"p_restate_aggregate": 1.0})
    assert links
    for l in links:
        assert l["kind"] == lin.SAME_COHORT
        assert l["facts_agree"] is True
        assert "NOT an independent measurement" in l["note"]


def test_restatements_skip_claims_without_a_statistic():
    """A structural statement is not an aggregate, so it cannot be restated as
    one; missing statement is not a negative fact."""
    claims = [dict(claim_id="c1", statistic=None), dict(claim_id="c2")]
    assert lin.restatements(101, claims, {"p_restate_aggregate": 1.0}) == []


def test_case_links_collapse_to_one_observation_per_case():
    claims = [dict(claim_id="a", case_id="A1"), dict(claim_id="b", case_id="A1"),
              dict(claim_id="c", case_id="A2")]
    links = lin.case_links(101, claims)
    assert len(links) == 1, "one case with two documents makes one link"
    assert links[0]["kind"] == lin.SAME_CASE
    assert links[0]["facts_agree"] is True


def test_lineage_is_private_truth(counties):
    """Lineage must be inferable from the text, not handed to the solver, so it
    carries no field that would leak it into a rendered artifact."""
    for l in lin.build_lineage(101, counties, {"p_template_lineage": 1.0}):
        assert set(l) == {"kind", "source", "derived", "mechanism", "facts_agree",
                          "localises", "preserves", "note"}
