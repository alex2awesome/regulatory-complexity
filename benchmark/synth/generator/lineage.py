"""Three kinds of dependence between documents, kept apart.

The plan's section 5 requirement, verbatim: *"For source dependencies, retain
three separate links: same underlying case, same aggregate/cohort, and copied
document/template. Each creates a different dependence. Repeating a statistic
across a report, FAQ and newspaper must not generate three independent
measurements."*

That is the single most consequential correctness requirement in the corpus,
because a fitter that treats copies as independent observations contracts its
posterior by a factor of sqrt(n) it has not earned. So the three links are
distinct types here, never one "related documents" field:

    SAME_CASE       two documents describe one applicant's one case
    SAME_COHORT     two documents report one aggregate over one population
    COPIED_TEXT     one document's prose descends from another's

The last is the one that carries the plan's warning in both directions:

  * **Two counties can share prose while genuinely having different
    procedures.** The real anchor is the eligibility consortia (39 / 18 / 1
    counties on three legacy platforms) and the CCW vendor boilerplate, where
    counties publish near-identical pages over materially different local
    practice. A solver that reads shared text as shared procedure is wrong.
  * **Two publications can use different prose for the same case.** The real
    anchor is the state hearings data, where an annual report and its quarterly
    predecessor restate one closed-case mean in different words, and the APR
    panel, where one project appears under two jurisdiction spellings.

`COPIED_TEXT` therefore says nothing about whether the underlying facts agree,
and `SAME_COHORT` says nothing about whether the prose matches. Keeping them
orthogonal is what lets the benchmark score "did the solver notice these are
not two measurements" separately from "did the solver notice these two pages
describe different procedures."

Lineage is private truth. It is written to the private bundle only, and never
appears in a rendered artifact's front matter -- the solver is supposed to infer
copying from the text, which is the actual task.
"""
from __future__ import annotations

from .rng import chance, pick, sub_rng

SAME_CASE = "same_case"
SAME_COHORT = "same_cohort"
COPIED_TEXT = "copied_text"
LINK_KINDS = (SAME_CASE, SAME_COHORT, COPIED_TEXT)

# How a copy came about. The mechanism matters because it predicts *what* was
# copied and what was localised, which is what a good extractor can exploit.
COPY_MECHANISMS = {
    "consortium_template": dict(
        note="counties on a shared eligibility platform publish the platform's prose. "
             "Real anchor: three legacy consortia split 39/18/1 across 58 counties.",
        localises=("office address", "phone", "hours", "local grant amount"),
        preserves=("procedure narrative", "statutory citation", "form numbers"),
        facts_agree=False),
    "vendor_boilerplate": dict(
        note="a licensing vendor supplies the application page; the county overrides "
             "parts of it. Real anchor: CCW vendor pages across 58 sheriffs, with "
             "local overrides on fee, training and appointment practice.",
        localises=("fee", "appointment method", "training referral"),
        preserves=("eligibility recitation", "processing-time claim"),
        facts_agree=False),
    "peer_adoption": dict(
        note="one county adopts a neighbour's ordinance. Real anchor: General "
             "Assistance policy text with visible copied lineage between counties.",
        localises=("jurisdiction name", "board resolution number", "effective date"),
        preserves=("substantive standard", "appeal route"),
        facts_agree=False),
    "own_prior_version": dict(
        note="a county's current page descends from its own superseded one; the "
             "superseded numbers survive in the prose.",
        localises=("effective date",),
        preserves=("everything else"),
        facts_agree=False),
    "restated_publication": dict(
        note="the same body republishes one statistic in a different document. Real "
             "anchor: state hearings annual and quarterly reports restating one "
             "closed-case mean, and APR aggregates repeated across tables.",
        localises=("framing", "rounding", "period label"),
        preserves=("the underlying aggregate"),
        facts_agree=True),
}


def link(kind: str, a: str, b: str, *, mechanism: str = "", note: str = "",
         facts_agree: bool | None = None) -> dict:
    """One directed dependence record, a -> b ("b descends from / shares with a").

    `facts_agree` is deliberately separate from `kind`. A copied page may state
    a different fee than its source (the county localised it) and two
    differently-worded reports may state the same mean. Collapsing these would
    destroy the distinction the plan asks for.
    """
    if kind not in LINK_KINDS:
        raise ValueError("unknown link kind %r; have %s" % (kind, list(LINK_KINDS)))
    if mechanism and mechanism not in COPY_MECHANISMS:
        raise ValueError("unknown copy mechanism %r" % mechanism)
    if kind == COPIED_TEXT and not mechanism:
        raise ValueError("a copied_text link must name its mechanism: %s"
                         % list(COPY_MECHANISMS))
    spec = COPY_MECHANISMS.get(mechanism, {})
    if facts_agree is None:
        facts_agree = spec.get("facts_agree", False) if mechanism else (kind != COPIED_TEXT)
    return dict(kind=kind, source=a, derived=b, mechanism=mechanism or None,
                facts_agree=bool(facts_agree),
                localises=list(spec.get("localises", ())),
                preserves=list(spec.get("preserves", ())),
                note=note or spec.get("note", ""))


def build_lineage(seed: int, counties: list[dict], knobs: dict) -> list[dict]:
    """Copied-text links across the county panel.

    Two generators, matching the two real mechanisms we measured:

    1.  **Within-consortium copying.** Counties sharing a platform label copy
        from the platform's own template, so the links form a star rather than a
        chain: every member descends from one template, not from each other.
        That shape matters, because a chain would let a solver recover the order
        of adoption, which the real data does not reveal.
    2.  **Peer adoption between neighbours**, which does form chains, and which
        therefore supplies the harder case.

    Both are capped by `p_template_lineage` so a world can be built with no
    copying at all as a control.
    """
    p_copy = knobs.get("p_template_lineage", 0.4)
    out: list[dict] = []
    by_consortium: dict[str, list[dict]] = {}
    for c in counties:
        by_consortium.setdefault(c["consortium"], []).append(c)

    for label, members in sorted(by_consortium.items()):
        if len(members) < 2:
            continue                       # the single-county consortium copies nobody
        template = "TEMPLATE:%s" % label
        for c in members:
            rng = sub_rng(seed, "lineage_consortium", c["id"])
            if chance(rng, p_copy):
                out.append(link(COPIED_TEXT, template, c["id"],
                                mechanism="consortium_template",
                                note="%s is on the %s platform; its eligibility prose "
                                     "descends from the platform template while its "
                                     "local grant amount and office details do not"
                                     % (c["name"], label)))

    # Peer adoption: a county copies an *earlier-adopting* peer, so the chain is
    # acyclic by construction. Ordered by id, which stands in for adoption order.
    for i, c in enumerate(counties):
        if i == 0:
            continue
        rng = sub_rng(seed, "lineage_peer", c["id"])
        if not chance(rng, p_copy * 0.5):
            continue
        donor = pick(rng, counties[:i])
        out.append(link(COPIED_TEXT, donor["id"], c["id"], mechanism="peer_adoption",
                        note="%s adopted %s's ordinance; the substantive standard "
                             "survives, the resolution number and effective date do not"
                             % (c["name"], donor["name"])))
    return out


def restatements(seed: int, claims: list[dict], knobs: dict) -> list[dict]:
    """`same_cohort` links for one aggregate republished in several documents.

    This is the dependence that actually inflates a naive posterior, because the
    restatements look like independent measurements of the same quantity and
    differ only by rounding and period label. Real anchor: 82 of 193
    jurisdictions reporting the same zero, and the hearings reports restating a
    closed-case mean across annual and quarterly publications.
    """
    p = knobs.get("p_restate_aggregate", 0.35)
    out: list[dict] = []
    for claim in claims:
        cid = claim.get("claim_id")
        if not cid or claim.get("statistic") is None:
            continue
        rng = sub_rng(seed, "restate", cid)
        n = 0
        while n < 2 and chance(rng, p / (n + 1)):
            n += 1
            out.append(link(SAME_COHORT, cid, "%s/restated/%d" % (cid, n),
                            mechanism="restated_publication", facts_agree=True,
                            note="the same aggregate republished; rounding and period "
                                 "label differ, the underlying cohort does not. NOT an "
                                 "independent measurement."))
    return out


def case_links(seed: int, claims: list[dict]) -> list[dict]:
    """`same_case` links: several documents about one applicant's one case."""
    by_case: dict[str, list[str]] = {}
    for claim in claims:
        case = claim.get("case_id")
        if case and claim.get("claim_id"):
            by_case.setdefault(case, []).append(claim["claim_id"])
    out: list[dict] = []
    for case, ids in sorted(by_case.items()):
        for other in sorted(ids)[1:]:
            out.append(link(SAME_CASE, sorted(ids)[0], other,
                            note="one case, several documents: a register row and a "
                                 "forum post about the same application are one "
                                 "observation of the underlying duration, not two"))
    return out


def independence_report(links: list[dict]) -> dict:
    """What a fitter would over-count if it ignored each link type.

    Reported per kind, because the three have different remedies: `same_case`
    calls for one observation per case, `same_cohort` for one per aggregate, and
    `copied_text` for NO deduplication of facts at all -- copied prose can still
    carry independently localised numbers, so collapsing those would lose real
    information. That asymmetry is why the kinds stay separate.
    """
    by_kind: dict[str, int] = {k: 0 for k in LINK_KINDS}
    agree = {k: 0 for k in LINK_KINDS}
    mechs: dict[str, int] = {}
    for l in links:
        by_kind[l["kind"]] += 1
        agree[l["kind"]] += bool(l["facts_agree"])
        if l["mechanism"]:
            mechs[l["mechanism"]] = mechs.get(l["mechanism"], 0) + 1
    return {
        "n_links": len(links),
        "by_kind": by_kind,
        "facts_agree_by_kind": agree,
        "mechanisms": mechs,
        "deduplication_rule": {
            SAME_CASE: "one observation per case; the documents are not independent",
            SAME_COHORT: "one observation per aggregate; restatements add no information",
            COPIED_TEXT: "do NOT deduplicate the facts: copied prose carries locally "
                         "overridden numbers, and two counties sharing text may run "
                         "different procedures",
        },
    }
