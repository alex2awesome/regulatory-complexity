#!/usr/bin/env python3
"""Pack one batch into a single self-contained input file for a renderer (or verifier) agent.

  python3 benchmark/synth/render/prepare_batch.py --world W1 --batch T00            # -> batches/T00.input.json
  python3 benchmark/synth/render/prepare_batch.py --world W1 --batch T00 --verify   # -> batches/T00.verify_input.json
Render input: {batch_id, style_guides: {kind: path}, render_context: {jur: {...}}, specs: [full spec...]}.
Verify input: adds artifacts: {id: text} and hidden_elements: {id: [...]} (from verify_context, only the
must_not_reveal ids of each spec) — the verifier sees hidden descriptions, the renderer never does.
"""
import re
import argparse, copy, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
STYLE = {"program_page": "municipal_pages.md", "generic_permits_page": "municipal_pages.md", "faq": "municipal_pages.md",
         "form": "forms.md", "checklist": "forms.md", "fee_schedule": "legal_text.md", "fee_resolution": "legal_text.md",
         "ordinance": "legal_text.md", "bill_analysis": "staff_reports.md", "staff_report": "staff_reports.md",
         "sop": "staff_reports.md", "audit_excerpt": "staff_reports.md", "council_minutes": "staff_reports.md",
         "official_stats": "municipal_pages.md", "news": "news_and_forums.md", "third_party_guide": "news_and_forums.md",
         "forum_thread": "reddit_style.md", "reddit_thread": "reddit_style.md"}


def renderer_spec(spec):
    """A renderer gets noisy reported amounts, never the persona's exact log values.

    Full specs remain available to the independent verifier. This copy does not
    alter the world/specification or substitute true amounts for noisy reports.
    """
    result=copy.deepcopy(spec)
    persona=result.get('persona')
    if persona:
        persona.pop('true_timeline',None)
        reported=persona.get('reported_timeline',{})
        # This internal numeric helper can differ from the deliberately noisy
        # rendered phrase; it is not a second public numerical claim.
        reported.pop('total_days_reported',None)
        for step in reported.get('steps',[]):
            step.pop('true_days',None)
    return result



# ---------------------------------------------------------------- projections
# The plan's named pre-W2 blocker: "The existing render preparation currently
# supplies full statute/local-rule objects to legal kinds. Replace that with a
# public-field projection before W2: legal content is licensed, private
# sampling/lineage/decision annotations are not automatically public."
#
# These are ALLOWLISTS, not denylists, and that choice is the point: a private
# field added to the truth schema later is excluded by default instead of
# leaking silently into every renderer packet from then on. A field that belongs
# in a published ordinance is listed here; a field that records how the
# generator DECIDED something is not.
STATUTE_PUBLIC = (
    # A statute is a published document, so its operative content is public.
    "stat_id", "state", "domain", "cite", "title", "bill", "committee",
    "enacted", "operative", "version", "applicability", "state_agency",
    "legislative_history", "sections", "text", "skeleton", "open_choices",
)
# `shape` is a generator design label. `decision_function` is projected field by
# field below rather than dropped, because its `statute_text` IS the statutory
# wording the renderer must reproduce -- while its `statutory_reading`,
# strictness and weights are the planted answer to the decision-model task.
PREDICATE_PUBLIC = (
    "pred_id", "name", "kind", "element_ref", "question", "statute_text",
    "attribute", "unit", "standard", "bound", "bound_text", "choice_id",
)

LOCAL_RULE_PUBLIC = (
    # An adopted ordinance is published: its chosen values, fee and added steps
    # are all on the page.
    "model_id", "jur", "stat_id", "domain", "cite", "instrument", "program_name",
    "adopted", "effective", "first_adopted", "version", "choices", "fee",
    "added_elements", "stricter_standards", "terminal_artifact", "lead_role",
    "text_spec",
)
# Withheld, each for a stated reason:
#   readings      the jurisdiction's planted interpretation of each predicate --
#                 the answer to the discretion-recovery task
#   lineage_from  which jurisdiction this was copied from; the solver is meant to
#                 infer copying FROM THE TEXT, which is the whole point of the
#                 lineage design
#   retrofit      a generator design label, not a fact on any page
#   prior_version the superseded values; what a stale document must say is
#                 already carried by the spec's own reveals and
#                 `describes_version`, so handing over the diff would let a
#                 renderer state a staleness the text should only imply


def _project(obj, allow):
    return {k: obj[k] for k in allow if k in obj}


def public_statute(st: dict) -> dict:
    out = _project(st, STATUTE_PUBLIC)
    if isinstance(st.get("decision_function"), list):
        out["decision_function"] = [_project(p, PREDICATE_PUBLIC)
                                    for p in st["decision_function"]]
    return out


# `text_spec` is the renderer's drafting instruction and it has to be public --
# without it a legal kind cannot be written. But it is PROSE assembled from the
# same truth the allowlist withholds, and in 192 of this world's local rules it
# ends with a sentence of the form
#
#   "Note the lineage: adapted from Zellwood County (Ordinance No. 2021-11);
#    the ordinance carries a tell: one subdivision still cross-references
#    Zellwood Municipal Code."
#
# So withholding `lineage_from` achieved nothing: the packet told the renderer
# the source jurisdiction AND instructed it to say so. A verifier caught the
# result in C53__S09__ordinance, whose findings recited "this chapter is based
# upon the model ordinance adopted by Granthorpe County". That defeats the whole
# point of the lineage design, which is that a solver must INFER copying from
# the text.
#
# The tell itself must survive, because the tell is the inference channel. Only
# the explicit attribution is removed, so the renderer still plants a stale
# cross-reference without being told whose it is.
# In every one of this world's 192 records the lineage clause happens to sit at
# the end of `text_spec`, so a greedy match would have worked here and broken
# silently on the first world where it does not. Scrubbing is therefore
# SENTENCE-SCOPED: drop only the sentences that carry the attribution, keep
# every other drafting instruction wherever it sits.
_TELL_WORD = "carries a tell"
_LINEAGE_MARK = "Note the lineage"


def _sentences(spec: str) -> list[str]:
    """Split on sentence ends, protecting the "Ordinance No. 2021-11" abbreviation."""
    guarded = spec.replace("No. ", "No.\u0000")
    parts = re.split(r"(?<=[.;])\s+", guarded)
    return [s.replace("No.\u0000", "No. ") for s in parts if s.strip()]


def scrub_text_spec(spec: str) -> str:
    """Remove the explicit copied-from attribution, keep the planted tell."""
    if not spec or _LINEAGE_MARK not in spec:
        return spec
    kept, had_tell = [], False
    for s in _sentences(spec):
        if _LINEAGE_MARK in s or _TELL_WORD in s:
            had_tell = had_tell or _TELL_WORD in s
            continue
        kept.append(s.strip())
    out = " ".join(kept)
    if had_tell:
        # The tell is the INFERENCE CHANNEL: a solver is meant to notice a stale
        # cross-reference and conclude the text was copied. So the instruction to
        # plant one survives; only the name of the source jurisdiction goes.
        out = (out.rstrip() + " The ordinance must carry one small tell that its text was "
               "adapted from another jurisdiction: leave exactly one subdivision "
               "cross-referencing a municipal code that is not this jurisdiction's, and "
               "do not explain or flag it.")
    return " ".join(out.split())


# LINEAGE, third channel. `style.template_lineage` carries the source
# jurisdiction's world ID, and 434 renderer specs have one. Two earlier fixes
# closed `local_rule.lineage_from` (withheld) and `text_spec` (scrubbed), and
# verifiers then found the same fact arriving here: footers reading "adapted
# from Crowmarsh County form DS-SOL-1", a staff report reciting "used Crowmarsh
# County's Ordinance No. 2024-39 as the drafting model", and -- worst -- body
# text printing the internal id, "Crowmarsh County (C50)".
#
# The right fix is NOT to strip it. The designed tell is an unexplained
# cross-reference to the source's municipal code, and a renderer cannot plant
# that without knowing whose code to cite; a solver infers copying precisely
# from that stray citation. So the source stays, and two things change:
#
#   * the renderer receives the jurisdiction's NAME, never its world id, so an
#     id cannot reach document text even by accident; and
#   * the field is renamed to say what to DO with it, because a field called
#     `template_lineage` reads like a fact to state, and several renderers
#     stated it.
def public_style(style: dict, jur_names: dict) -> dict:
    out = dict(style or {})
    src = out.pop("template_lineage", None)
    if src:
        out["copied_from_plant_an_unexplained_tell"] = {
            "source_jurisdiction_name": jur_names.get(src, "another county in this state"),
            "how": ("Leave exactly ONE unexplained trace that this text was adapted from "
                    "that jurisdiction -- typically a single subdivision or footnote still "
                    "cross-referencing ITS municipal code or ITS form number. Do not "
                    "explain, flag, footnote or apologise for it, and never write that this "
                    "document was adapted, modelled on, or based upon anything. A reader "
                    "must be able to NOTICE the trace; nobody may be TOLD about it."),
            "never": ("Never write a world identifier such as C50 or S07 in document text. "
                      "Real county documents contain no such codes."),
        }
    return out


# STRICTNESS, a fourth channel of the same kind. A choice VALUE is public -- an
# adopted ordinance states "English, Spanish, and Tagalog" -- but 39 of this
# world's values carry a trailing generator annotation that also states the
# comparison: "(three languages, exceeding the statutory minimum)", "(exceeds
# the state minimum)". A verifier caught the result in an ordinance reading "which
# exceeds the two languages the state law requires", handing over exactly the
# local-versus-state comparison a solver is meant to infer from the statute plus
# the local value.
#
# This is the third time the same shape has appeared: lineage_from was withheld
# and then leaked through text_spec, then through style.template_lineage, and now
# strictness leaks through choices. The lesson is general enough to state here:
# an allowlist over FIELD NAMES does not protect anything, because the private
# fact travels inside the prose of a public field. Any new public field needs
# checking for what its text says, not just for what it is called.
_STRICTNESS_PAREN = re.compile(
    r"\s*\((?=[^)]*(?:exceed|stricter|more stringent|statutory minimum|"
    r"than (?:the )?state|above the stat|beyond the stat))[^)]*\)")


# The same annotation also appears as a trailing comma clause rather than a
# parenthetical: "a hand-wash sink with 5 gallons of warm water, exceeding the
# state minimum". The STANDARD is public; the comparison is not.
_STRICTNESS_CLAUSE = re.compile(
    r",\s*(?:which\s+)?(?:exceed\w*|stricter\b|more stringent\b|above the stat\w*|"
    r"beyond the stat\w*)[^.;]*", re.I)


def scrub_choice(value):
    """Keep the adopted value, drop a comparison-to-state annotation."""
    if not isinstance(value, str):
        return value
    out = _STRICTNESS_CLAUSE.sub("", _STRICTNESS_PAREN.sub("", value))
    return out.strip().rstrip(",") or value


def public_local_rule(lr: dict) -> dict:
    out = _project(lr, LOCAL_RULE_PUBLIC)
    if "text_spec" in out:
        out["text_spec"] = scrub_text_spec(out["text_spec"])
    if isinstance(out.get("choices"), dict):
        out["choices"] = {k: scrub_choice(v) for k, v in out["choices"].items()}
    if isinstance(out.get("stricter_standards"), list):
        # The standards themselves are published; a note comparing them to state
        # law is not.
        out["stricter_standards"] = [scrub_choice(s) for s in out["stricter_standards"]]
    return out


def build_packet(wd, b, *, verify=False):
    """Build the existing packet without writing shared/live batch files.

    Scoped completion jobs use this same public projection and leakage policy.
    The ordinary CLI below retains its previous on-disk interface.
    """
    wd = pathlib.Path(wd)
    specs = [json.load(open(wd / "specs" / f"{sid}.json")) for sid in b["spec_ids"]]
    jurs = sorted({s.get("jur") for s in specs if s.get("jur")})
    rc = {}
    for j in jurs:
        f = wd / "render_context" / f"{j}.json"
        if f.exists():
            rc[j] = json.load(open(f))
    kinds = sorted({s["kind"] for s in specs})
    # Legal-text kinds are public documents whose *content* is the truth: give the renderer the statute /
    # local-rule truth files (never the process truth) plus state-level context.
    # ARTIFACT-SCOPED, not batch-scoped. This used to be one dict at the top of
    # the packet, handed to every renderer in the batch, so a renderer drafting a
    # faq whose only fee reveal is "vague" still received the sibling ordinance's
    # exact fee.amount and its full choices. Nothing structural stopped an exact
    # figure reaching an artifact licensed only for a hedge. A verifier flagged
    # the channel on batch D09 before anything had exploited it. Each legal spec
    # now carries only its OWN statute and local rule, under `legal_truth` on the
    # spec itself, and non-legal specs get none at all.
    LEGAL = {"ordinance", "bill_analysis", "fee_resolution"}
    LAW_RESTATING = LEGAL | {"staff_report", "council_minutes"}
    legal_truth = {"statutes": {}, "local_rules": {}}
    per_spec_legal: dict[str, dict] = {}
    for s in specs:
        if s["kind"] in LAW_RESTATING:
            st = s.get("stat_id")
            if st and st not in legal_truth["statutes"]:
                f = wd / "truth/statutes" / f"{st}.json"
                if f.exists():
                    legal_truth["statutes"][st] = public_statute(json.load(open(f)))
            if s["kind"] in LEGAL and s.get("jur") and st and s.get("subkind") != "statute_text":
                key = f"{s['jur']}__{st}"
                f = wd / "truth/local_rules" / f"{key}.json"
                if f.exists() and key not in legal_truth["local_rules"]:
                    legal_truth["local_rules"][key] = public_local_rule(json.load(open(f)))
    # Build each legal spec's own slice.
    for s in specs:
        if s["kind"] not in LEGAL:
            continue
        st = s.get("stat_id")
        mine = {"statutes": {}, "local_rules": {}}
        if st and st in legal_truth["statutes"]:
            mine["statutes"][st] = legal_truth["statutes"][st]
        key = "%s__%s" % (s.get("jur"), st)
        if key in legal_truth["local_rules"]:
            mine["local_rules"][key] = legal_truth["local_rules"][key]
        per_spec_legal[s["artifact_id"]] = mine

    world = json.load(open(wd / "world.json"))
    out = {"batch_id": b["batch_id"], "world": wd.name, "group": b["group"],
           "style_guides": {k: str((ROOT / "benchmark/synth/style" / STYLE.get(k, "municipal_pages.md")).relative_to(ROOT)) for k in kinds},
           "brief": "benchmark/synth/briefs/RENDER_BRIEF.md", "artifacts_dir": str((wd / "artifacts").relative_to(ROOT)),
           "render_context": rc, "states": world.get("states"),
           "legal_truth_note": ("Each legal-kind spec carries its OWN statute and local "
                                "rule under spec['legal_truth']. There is deliberately no "
                                "batch-wide legal_truth: an artifact must not see the "
                                "adopted figures of a sibling it is not licensed to "
                                "restate."),
           "specs": specs if verify else [renderer_spec(s) for s in specs]}
    jur_names = {j["id"]: j.get("short") or j.get("name") for j in world.get("jurisdictions", [])}
    full_jur_names = {j['id']: j['name'] for j in world.get('jurisdictions', [])}
    for s in out["specs"]:
        # A licensed neighboring-jurisdiction comparison sometimes names only an
        # internal ID. Supply its public display name, not its programs/fees or
        # private lineage. Requiring the code in prose would leak an answer key.
        comparison_ids = {ident for reveal in s.get('reveals', [])
            if reveal.get('lineage_hint') and 'neighbouring jurisdictions' in reveal.get('value', '')
            for ident in re.findall(r'\b[CJK]\d+\b', reveal['value']) if ident in full_jur_names}
        if comparison_ids:
            s['public_comparison_names'] = {ident: full_jur_names[ident] for ident in sorted(comparison_ids)}
        slice_ = per_spec_legal.get(s.get("artifact_id"))
        if slice_:
            s["legal_truth"] = slice_
        elif s["kind"] in LAW_RESTATING and s.get("stat_id") in legal_truth["statutes"]:
            # DESIGN.md permits these documents to restate public mandates.
            # Supply ONLY their own projected statute, not adopted local amounts,
            # hidden implementation actors, private readings, or adjacent laws.
            s["public_statutory_context"] = legal_truth["statutes"][s["stat_id"]]
        if s.get("style"):
            s["style"] = public_style(s["style"], jur_names)
    if verify:
        out["brief"] = "benchmark/synth/briefs/VERIFY_BRIEF.md"
        out["artifacts"], out["hidden_elements"] = {}, {}
        vc_cache = {}
        for s in specs:
            f = wd / "artifacts" / f"{s['artifact_id']}.md"
            out["artifacts"][s["artifact_id"]] = f.read_text() if f.exists() else None
            hidden = []
            for hid in s.get("must_not_reveal") or []:
                mid, _, aid = hid.rpartition(":") if ":" in hid else (f"{s.get('jur')}__{s.get('stat_id')}", "", hid)
                if mid not in vc_cache:
                    vf = wd / "verify_context" / f"{mid}.json"
                    vc_cache[mid] = {h["id"]: h for h in json.load(open(vf))["hidden_elements"]} if vf.exists() else {}
                if aid in vc_cache[mid]:
                    hidden.append(dict(vc_cache[mid][aid], process=mid))
            out["hidden_elements"][s["artifact_id"]] = hidden
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--world", default="W1"); ap.add_argument("--batch", required=True)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    wd = ROOT / "benchmark/synth/worlds" / a.world
    b = json.load(open(wd / "batches" / f"{a.batch}.json"))
    out = build_packet(wd, dict(b, batch_id=a.batch), verify=a.verify)
    name = f"{a.batch}.verify_input.json" if a.verify else f"{a.batch}.input.json"
    p = wd / "batches" / name
    p.write_text(json.dumps(out, indent=1))
    print(f"{p.relative_to(ROOT)}: {len(out['specs'])} specs, {len(out['render_context'])} jurisdictions, kinds={sorted(out['style_guides'])}, {p.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
