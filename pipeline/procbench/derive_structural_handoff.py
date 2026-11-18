"""Derive a default `source-only-structural-handoff/1` from an accepted ledger.

WHY THIS EXISTS. `bridge_structural_routes.py` will not turn a ledger into a V6
input without a structural handoff, and the only handoffs that exist were hand
authored one process at a time: solar_permit's is roughly six hundred lines of
per-activity prose. Nine real ledgers are parsed and one can reach the model.
Hand authoring does not scale, and the user has already named that scaling wall
once, for per-document ceilings.

Most of a handoff is not judgement. The ledger already records, per activity, a
scope (core / conditional / standing / out_of_scope), a stage, a task type, an
actor with a role, and its own verbatim quotations; it already records rework
relations, parallel relations and case identities. This module reads those and
writes the handoff they imply, attaching the ledger's own quotes unchanged.

WHAT IT DOES NOT DO, AND SAYS SO IN THE OUTPUT. It does not invent merge
hypotheses, clock boundary markers, agency identity judgements or the prose
`judgment` field that a human author writes after reading the documents. Those
come out empty, and `derivation.not_derived` names each one. The output declares
`variant: "derived_default"` and `reviewed: false` so it can never be mistaken
for an authored handoff. A derived handoff is a starting point for review, and
a fit on one is a diagnostic, not a result.

THE ONE JUDGEMENT IT MAKES is the classification map below, and it is stated
rather than hidden: the ledger's own scope decides it, because the ledger's
scope field was assigned by a parser who had the documents and this module does
not. Where the ledger says `unknown`, the activity is classified unclassified
and the bridge will exclude it, which is the safe direction: an excluded
activity loses information, an invented operation fabricates it.

MEASURED AGAINST THE ONE AUTHORED HANDOFF. On solar_permit, the only process
with a hand-authored handoff, the derived classification agrees with the author
on whether an activity is an operation for 43 of 45 activities (95.6%). Both
disagreements are the same kind and they matter: `nem2_extension_request` and
`utility_detailed_study` are ledger-`conditional` activities the author excluded
because they sit on a DIFFERENT ROUTE (a superseded tariff, and a
non-residential scale). Route membership is not a ledger field, so this module
cannot see it.

The error direction is over-inclusion, and over-inclusion INFLATES modelled
burden by putting operations on a path that does not traverse them.

AND THE LABEL COMPARISON IS THE EASY TEST. Bridging solar_permit with the
authored handoff and with the derived one, against the same compilation, gives
identical observations and very different structure:

    authored   3 routes   35 operations   8 case paths   repeat block: correction round
    derived    1 route    37 operations   3 case paths   repeat block: NONE

The derived input loses the repeat block (solar's rework forms three groups and
the model carries one, so this module refuses to pick), every optional toggle
(conditional path groups are judgement), and two of three routes (identity-merge
hypotheses are judgement). In the derived model EVERY CASE TRAVERSES EVERY
OPERATION EXACTLY ONCE: nobody skips a conditional step, nobody goes round a
correction loop, and no two activities may be the same thing.

So a derived handoff produces a structurally degenerate model. It answers
whether a ledger can reach V6 at all, and it must not be fitted for a burden
result, because the structure it drops IS the burden heterogeneity the project
measures.

Its real value is as a review checklist. Everything mechanical is done, and what
a reviewer must supply is exactly three things this module cannot know: which
rework group is the repeat block, which conditional groups are optional toggles,
and which activities are identity-merge candidates.

    python3 -m pipeline.procbench.derive_structural_handoff \
        --evidence runs/.../evidence.json --documents runs/.../artifacts \
        --out runs/.../structural_handoff.derived.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib

from .evidence_contract import normalized_quote, validate

HANDOFF_VERSION = 'source-only-structural-handoff/1'

# The ledger's scope field decides the classification. `performed_operation` is
# the only class the bridge admits as an operation; everything else is recorded
# so the exclusion is visible rather than silent.
SCOPE_CLASSIFICATION = {
    'core': 'performed_operation',
    'conditional': 'performed_operation',
    'standing': 'standing_obligation',
    'out_of_scope': 'out_of_scope_not_an_operation_of_the_route',
}

DECISION_TASK_TYPES = {'decision'}
DECISION_STAGES = {'decision'}
MAX_QUOTES = 3


def _quotes(item, texts, limit=MAX_QUOTES):
    """The ledger's own supporting quotations, re-verified against the documents."""
    out = []
    for entry in (item.get('evidence') or [])[:limit]:
        doc_id, quote = entry.get('doc_id'), entry.get('quote')
        if doc_id is None or quote is None:
            continue
        if texts is not None and normalized_quote(quote) not in texts.get(doc_id, ''):
            raise ValueError('NON-VERBATIM quote on %r in %s' % (item.get('id'), doc_id))
        out.append(dict(doc_id=doc_id, quote=quote))
    return out


def derive(evidence, documents=None):
    texts = ({d['id']: normalized_quote(d['text']) for d in documents}
             if documents is not None else None)
    activities = {a['id']: a for a in evidence['activities']}
    actors = {a['id']: a for a in evidence['actors']}

    classifications, unclassified = [], []
    for act in evidence['activities']:
        scope = act.get('scope')
        classification = SCOPE_CLASSIFICATION.get(scope)
        if classification is None:
            unclassified.append(act['id'])
            classification = 'unclassified_ledger_scope_%s' % scope
        actor = actors.get(act.get('actor_id')) or {}
        classifications.append(dict(
            activity_id=act['id'], name=act.get('name'), classification=classification,
            judgment=('DERIVED, NOT AUTHORED. The accepted ledger records scope %r, stage %r, '
                      'task type %r and actor %r (role %r); the classification follows from the '
                      'scope alone. No document was read to write this sentence.'
                      % (scope, act.get('stage'), act.get('task_type'),
                         act.get('actor_id'), actor.get('role'))),
            ledger_scope=scope, ledger_stage=act.get('stage'),
            ledger_task_type=act.get('task_type'), ledger_actor_role=actor.get('role'),
            evidence=_quotes(act, texts)))

    # Adjudications: the ledger's own decision-typed or decision-staged activities.
    decisions = [a for a in evidence['activities']
                 if a.get('scope') in ('core', 'conditional')
                 and (a.get('task_type') in DECISION_TASK_TYPES
                      or a.get('stage') in DECISION_STAGES)]
    conditional_paths = []
    if decisions:
        conditional_paths.append(dict(
            id='derived_terminal_adjudication',
            activity_ids=[a['id'] for a in decisions],
            decision_scope='per_decision_occasion',
            judgment=('DERIVED, NOT AUTHORED. Every core or conditional activity the ledger types '
                      'or stages as a decision, grouped as one adjudication occasion. No source '
                      'says these dispositions are alternatives of a single occasion; that is the '
                      'assumption this group makes, and it is the first thing a reviewer should '
                      'check, because grouping two genuinely sequential decisions here would '
                      'collapse a two-decision process into one.'),
            evidence=[q for a in decisions for q in _quotes(a, texts, 1)]))

    # Repeat links. V6 carries AT MOST ONE repeat block per programme: the bridge
    # raises on the second one. The real ledgers record several rework relations
    # each, so picking which repetition the model gets is a judgement about which
    # loop dominates burden, and this module will not make it silently. It emits
    # a repeat link only when the ledger's rework relations form exactly ONE
    # connected group; otherwise it emits none and reports every one of them.
    rework = [r for r in evidence['relations'] if r['kind'] == 'rework']
    groups = []
    for rel in rework:
        pair = {rel['source'], rel['target']}
        touching = [g for g in groups if g['members'] & pair]
        merged = dict(members=set(pair), relations=[rel])
        for g in touching:
            merged['members'] |= g['members']
            merged['relations'] += g['relations']
            groups.remove(g)
        groups.append(merged)

    repeat_links, unencoded_rework = [], []
    if len(groups) == 1:
        group = groups[0]
        members = sorted(group['members'])
        repeat_links.append(dict(
            id='derived_rework_loop',
            activity_ids=members,
            explicit=('The ledger records %d rework relation(s) joining these activities, and they '
                      'form a single connected group.' % len(group['relations'])),
            interpretation=('DERIVED, NOT AUTHORED. The ledger\'s rework relations form exactly one '
                            'group, so no choice was made about which repetition to model. Whether '
                            'the bridge encodes it still depends on whether the target has a '
                            'precedes predecessor.'),
            evidence=[q for rel in group['relations'] for q in _quotes(rel, texts, 1)]))
    else:
        for group in groups:
            unencoded_rework.append(dict(
                activity_ids=sorted(group['members']),
                relations=[dict(source=r['source'], target=r['target']) for r in group['relations']],
                reason=('NOT SUBMITTED AS A REPEAT LINK. The ledger records %d separate groups of '
                        'rework and the trace model carries one repeat block per programme, so '
                        'submitting these would make the bridge refuse. Choosing among them is a '
                        'judgement about which repetition dominates applicant burden, and this '
                        'handoff was derived, not authored. Every group is listed here so the '
                        'repetition is visible rather than dropped.' % len(groups)),
                evidence=[q for r in group['relations'] for q in _quotes(r, texts, 1)]))

    # Repeated-wording groups: measurements that share a source family are one
    # report until someone shows otherwise. This is the copied-claim guard.
    families = collections.defaultdict(list)
    for m in evidence['measurements']:
        families[m.get('source_family') or m['doc_id']].append(m['id'])
    same_report = [dict(id='derived_family__%s' % family, measurement_ids=sorted(ids),
                        judgment=('DERIVED, NOT AUTHORED. These measurements declare the same '
                                  'source family, so they are one report unless review separates '
                                  'them. Treating them as independent would double-count.'))
                   for family, ids in sorted(families.items()) if len(ids) > 1]

    parallel_pairs = [dict(source=r['source'], target=r['target'], evidence=_quotes(r, texts))
                      for r in evidence['relations'] if r['kind'] == 'parallel']

    handoff = dict(
        schema_version=HANDOFF_VERSION,
        program_id=evidence['program_id'],
        variant='derived_default',
        reviewed=False,
        diagnostic_only=True,
        changes_accepted_evidence=False,
        new_model_calls=0,
        hidden_truth_read=False,
        numerical_probabilities_assigned=False,
        fitted_estimates_provided=False,
        author_context=('Derived mechanically from the accepted ledger by '
                        'pipeline/procbench/derive_structural_handoff.py. No document was read '
                        'beyond re-verifying the ledger\'s own quotations. Not reviewed.'),
        interpretation_status=('DERIVED DEFAULT. Every classification follows from a ledger field. '
                               'No interpretation was added and none of the judgement-bearing '
                               'sections of an authored handoff are populated. A fit on this '
                               'handoff is a diagnostic about reachability, not a result.'),
        classification_semantics=('performed_operation is asserted here on the strength of the '
                                  'ledger scope alone. It does not assert that the operation '
                                  'occurs in every case, nor that it is the applicant\'s work.'),
        jurisdiction_scoping=dict(derived=True, note=('Not derived. The ledger does not record a '
                                                      'jurisdiction scoping decision.')),
        clock_boundary_markers={},
        clock_boundary_note=('Not derived. No submission, complete-submission or legal-closeout '
                             'marker is declared, so the bridge will emit none. Declaring one '
                             'requires reading what a source means by the start of the clock.'),
        activity_classifications=classifications,
        conditional_paths_and_outcomes=conditional_paths,
        inventory_identity_hypotheses=[],
        repeat_links=repeat_links,
        same_report_measurement_groups=same_report,
        distinct_case_warnings=[],
        agency_identity_notes=[],
        other_rework_relations_not_submitted_as_repeat_links=unencoded_rework,
        parallel_relations_in_ledger=parallel_pairs,
        derivation=dict(
            builder='pipeline/procbench/derive_structural_handoff.py',
            scope_classification_map=SCOPE_CLASSIFICATION,
            unclassified_activities=unclassified,
            not_derived=['inventory_identity_hypotheses (merge judgements)',
                         'clock_boundary_markers (what a source means by the clock starting)',
                         'agency_identity_notes (which bodies are one agency)',
                         'distinct_case_warnings (which reports describe the same case)',
                         'jurisdiction_scoping (which jurisdictions are on the route)',
                         'the per-activity judgment prose of an authored handoff'],
            counts=dict(activities=len(classifications),
                        performed_operations=sum(1 for c in classifications
                                                 if c['classification'] == 'performed_operation'),
                        standing=sum(1 for c in classifications
                                     if c['classification'] == 'standing_obligation'),
                        out_of_scope=sum(1 for c in classifications
                                         if c['classification'].startswith('out_of_scope')),
                        unclassified=len(unclassified),
                        decisions_grouped=len(decisions),
                        repeat_links=len(repeat_links),
                        rework_relations=len(rework),
                        rework_groups=len(groups),
                        rework_groups_not_encoded=len(unencoded_rework),
                        same_report_groups=len(same_report),
                        parallel_relations=len(parallel_pairs))),
        provenance=dict(
            evidence_schema=evidence['schema_version'],
            evidence_sha256=hashlib.sha256(
                json.dumps(evidence, sort_keys=True).encode()).hexdigest(),
            documents_available=len(documents) if documents is not None else 0,
            quotes_reverified=documents is not None))
    return handoff


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--documents', help='Directory of <doc_id>.md artifacts, for quote re-verification')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)

    evidence = json.loads(pathlib.Path(args.evidence).read_text())
    documents = None
    if args.documents:
        documents = [dict(id=p.stem, text=p.read_text(errors='replace'))
                     for p in sorted(pathlib.Path(args.documents).glob('*.md'))]
        evidence = validate(evidence, documents)
    handoff = derive(evidence, documents)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(handoff, indent=1))
    counts = handoff['derivation']['counts']
    print('%-46s ops=%-4d standing=%-3d oos=%-3d uncl=%-3d decisions=%-3d rework=%-3d families=%d'
          % (evidence['program_id'][:46], counts['performed_operations'], counts['standing'],
             counts['out_of_scope'], counts['unclassified'], counts['decisions_grouped'],
             counts['repeat_links'], counts['same_report_groups']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
