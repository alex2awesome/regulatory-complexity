"""Bridge accepted source-only structure into a V6 `run_visit_hierarchy` input.

Inputs are the quote-checked evidence ledger (`process-evidence/2|3`), the
source-only structural handoff (`source-only-structural-handoff/1`) and the
compiled elapsed observations (`joint-visit-duration-compilation/*`). Nothing
here reads benchmark truth, generator specifications, scores, source documents
or fitted outputs, and nothing calls a model. The output is deterministic.

Every structural choice is either (a) read from a named handoff/ledger key or
(b) a declared assumption listed in `bridge_report.json`. Route prior weights
and case-path probability weights are uniform declared assumptions, not
evidence. Readings whose activity is absent from a route fall to the residual
alternative through `UnavailableTraceQuantity`; the report counts them per route.

Rules enforced in code (each pinned by tests/test_bridge_structural_routes.py):

a. Operations are activities the handoff classifies `performed_operation`,
   plus the adjudication dispositions of the handoff's `per_decision_occasion`
   outcome group that the ledger reaches from performed review-stage work.
   Every other ledger activity is listed in `excluded_activities`.
b. Within-block order is `edges: null` (serial, ledger `precedes` topological
   order). Explicit edges appear only in a block containing a quoted ledger
   `parallel` pair. `edges: []` is never emitted.
c. Applicability follows the ledger actor role: payer -> (True, False),
   agency -> (False, True), unknown/third_party -> (None, None).
d. Markers: `decision` only on admitted dispositions; `submission`,
   `complete_submission` and `legal_closeout` only when the handoff names a
   boundary activity under `clock_boundary_markers` (none does today).
e. A `repeat_links` entry whose members are joined by a ledger `rework`
   relation becomes one repeat block; other repeat links are reported, not encoded.
f. `inventory_identity_hypotheses` become merge routes (representative keeps its
   identity), capped at `max_routes` per programme; the rest are reported.
g. `per_decision_occasion` dispositions become case paths, each holding exactly
   one disposition; optional per-case groups toggle paths. Quoted case outcomes
   in the ledger's `observation_contexts` set `case_path_scope`.
h. `observations` and explicitly compiled `quantile_cohorts` are copied verbatim.
   Cohort sampling, denominators, precision and joint-report contracts are not
   inferred here. No rate observations are invented from planning rates.
i. A `procbench-run/1` manifest records input hashes and `hidden_truth_read=False`.
j. Agency identity is canonicalised by `canonical_agency_identity` when
   `--pool-agencies` is given: V6 pools `actor_id` literally, so that one
   function decides which programmes share an agency coordinate. Default off,
   so `data.json` is unchanged byte-for-byte without the flag.
k. With `--operation-fees` every operation gets a quoted amount, an explicit
   `0.` where the applicant tenders nothing (a recorded judgement), or `None`
   where a charge plausibly exists and no document states it. `None` is never
   zero: it makes `payer_fee_total` refuse, and the report names the routes it
   refuses on. Default off, for the same byte-identity reason.
"""
import argparse
import copy
import dataclasses
import json
import pathlib
import re

from .bayes_trace_hierarchy import CHANNELS, COUNT_BASES, PHASE_BASES, Config, VisitHierarchy
from .compact_visit_trace import MONEY_BASES, Operation
from .cohort_quantiles import cohort_report_observations
from .infra.manifest import RunManifest, digest, write

HANDOFF_VERSION = 'source-only-structural-handoff/1'
EVIDENCE_VERSIONS = ('process-evidence/2', 'process-evidence/3')
COMPILATION_PREFIX = 'joint-visit-duration-compilation/'
REPORT_VERSION = 'v6-structural-bridge-report/1'
PERFORMED = 'performed_operation'
OUTCOME_EVENT = 'legal_transition_or_outcome_event'
DISPOSITION_SCOPE = 'per_decision_occasion'
# Handoff scopes describing optional per-case work; each group toggles paths.
OPTIONAL_SCOPES = ('per_case_after_adverse_decision', 'per_case_post_decision_path',
                   'per_applicant_optional_action', 'per_case_changed_information')
ROLE_APPLICABILITY = {'payer': (True, False), 'agency': (False, True),
                      'unknown': (None, None), 'third_party': (None, None)}
STAGE_RANK = {s: i for i, s in enumerate(('preparation', 'submission', 'intake', 'review',
                                          'decision', 'closeout', 'enforcement', 'appeal',
                                          'standing', 'unknown'))}
OPTIONAL_MARKERS = ('submission', 'complete_submission', 'legal_closeout')
BASE_ROUTE_ID = 'ledger_distinct'
MAX_ROUTES = 4

# --- agency identity (rule j) ------------------------------------------------
# A county namespace: both programme ids and county-scoped document ids start
# with it. A document id outside every county namespace (`S12__statute_text`)
# is statute scope: one text shared by every county under that statute.
COUNTY_NAMESPACE = re.compile(r'^C\d')
# A body that calls itself a county body is a county body, whatever else names it.
COUNTY_WORD = re.compile(r'\bcount(y|ies)\b', re.IGNORECASE)
STATE_TIER, COUNTY_TIER, UNPOOLED_TIER = 'state_level_body', 'county_office', 'programme_scoped'
# Only an `agency` actor may pool. An applicant in one county is not an
# applicant in another, and an unresolved actor is not a shared organisation.
POOLABLE_ROLES = ('agency',)

# --- published fees (rule k) -------------------------------------------------
FEE_METRIC = 'fee'
FEE_UNIT = 'USD'
# A published charge is recorded either as the amount one applicant is charged
# (`individual`) or as the published rate for the step (`typical`); the ledgers
# use both for schedule/ordinance/form amounts. `estimate` is a proposal or a
# budget and `statutory_cap` is a ceiling with no amount: neither is a charge.
PUBLISHED_FEE_STATISTICS = ('individual', 'typical')

DECLARED_ASSUMPTIONS = [
    'Route prior weights are uniform across routes: a declared assumption, not evidence.',
    'Case-path probability weights are uniform across paths: a declared assumption, not evidence.',
    'Adjudication dispositions are members of the handoff per_decision_occasion group that '
    'the ledger reaches (precedes) from performed review-stage work; outcome members without '
    'such a predecessor (e.g. deemed approval by agency inaction) are not encoded as paths.',
    'Withdrawal/abandonment outcomes are not encoded as paths; withdrawn cases stay unscoped.',
    'Precedes relations whose every supporting document is uniformly marked hypothetical by the '
    "ledger's observation contexts describe a proposed/forecast sequence and are excluded from "
    'the current-route order.',
    'A precedes chain between a quoted parallel pair is relaxed by dropping its weakest edge '
    '(inferred, then conditioned, then first on the chain); the pair is left unordered.',
    'An operation with no quoted order relation is serialized at its ledger listing position, '
    'and no later than immediately before the first disposition when its ledger stage precedes '
    'decision.',
    'A repeat block replays all of its members each round (model limitation): the first pass '
    'already contains the notice/resubmission members of the correction loop.',
    'Appeal decisions are performed operations on the appeal path but carry no decision marker, '
    'because the handoff per_decision_occasion group does not name them; final_decision therefore '
    'equals initial_decision on every path.',
    'A merge route keeps the member most referenced by compiled operators as the representative; '
    'readings on the dropped members fall to the residual alternative on that route.',
    'Optional per-case groups toggle paths; a group naming a disposition attaches only to that '
    "disposition's paths even where the ledger also records reachability from another disposition.",
    'Only hypotheses whose every listed member is an operation are merge candidates; they are '
    'ranked for the route cap by a handoff rank if given, else by the number of members referenced '
    'by compiled operators, then handoff listing order.',
]


def load(path):
    return json.loads(pathlib.Path(path).read_text())


def short(activity_id):
    return activity_id.split('__')[-1]


def quotes(entry):
    return [dict(doc_id=e['doc_id'], quote=e['quote']) for e in entry.get('evidence', [])]


MONTHS = ('january february march april may june july august september october '
          'november december').split()


def stated_currency_date(measurement):
    """When a published amount speaks for, read off the document's own words.

    A fee schedule that says "current as of March 30, 2026" and a form that says
    "created August 7, 2021" are not two competing claims about today's price.
    One supersedes the other, and the corpus says so in the measurement's own
    `cohort`/`interpretation` text. Comparing bare numbers throws that away and
    turns an answerable question into a refusal.

    Returns a (year, month, day) tuple, or None when the text carries no
    unambiguous single year. Ambiguity stays ambiguous: two different years in
    one annotation means we cannot tell which one dates the amount.
    """
    text = ' '.join(str(measurement.get(k) or '') for k in ('cohort', 'interpretation'))
    years = sorted({int(m.group()) for m in re.finditer(r'\b(?:19|20)\d{2}\b', text)})
    if len(years) != 1:
        return None
    year = years[0]
    match = re.search(r'\b(%s)\b\s+(\d{1,2})\b' % '|'.join(MONTHS), text, re.I)
    if match:
        return (year, MONTHS.index(match.group(1).lower()) + 1, int(match.group(2)))
    return (year, 0, 0)


class BridgeError(ValueError):
    """Structural input the bridge refuses to reinterpret silently."""


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', str(text).casefold()).strip('_')


def county_of(program_id):
    """`C44__S12` -> `C44`. The county namespace is the programme id prefix."""
    county = str(program_id).split('__')[0]
    if not COUNTY_NAMESPACE.match(county):
        raise BridgeError('A programme id must start with its county namespace: ' + str(program_id))
    return county


def canonical_agency_identity(evidence, peers=()):
    """Assign each ledger actor the `actor_id` V6 will pool on (rule j).

    V6 pools actor ids literally, so this function alone decides whether two
    programmes share an agency coordinate. Three tiers, and only the first two
    pool; every decision below is returned with the ledger evidence for it.

    Tier 1, state-level body -> one global id `state:<slug>`. An `agency` actor
    qualifies only when all three hold over the supplied ledgers:
      (i)   its ledger name recurs in the ledgers of at least two distinct
            counties (it is not one county's office);
      (ii)  some ledger supports that name with a quote from a statute-scope
            document, i.e. a `doc_id` outside every county namespace, which is
            the state's own text naming the body; and
      (iii) the name does not describe itself as a county body.
    All three are load-bearing on this corpus. Dropping (ii) would pool the
    `Auditor-Controller, Revenue Division` that appears in six counties, and
    dropping (iii) would pool the `county health department` that the statute
    names. This is deliberately evidence, not a guess from the word `State`:
    `Marisol Department of Consumer Affairs` does not contain it.

    Tier 2, county office -> one id per county, `county:<county>:<slug>`. Every
    other `agency` actor. The same office in two statutes of one county
    (`Ulverston County` in C44__S12 and C44__S03) gets one id; the same-named
    office in another county does not, because the county is in the id.

    Tier 3 is not emitted: a `payer`, `third_party` or `unknown` actor keeps its
    programme-scoped ledger id. An applicant in one county is not an applicant
    in another, and an unresolved performer is not a shared organisation.

    `peers` are other programmes' ledgers, read only for (i) and (ii): no
    activity, relation or measurement of a peer is used. Without peers no name
    can recur across counties, so every agency falls to tier 2, which is the
    conservative direction.
    """
    ledgers, seen_programs = [evidence], {evidence['program_id']}
    for peer in peers:
        if peer['program_id'] in seen_programs:
            continue
        seen_programs.add(peer['program_id'])
        ledgers.append(peer)
    counties, statute_support, self_described_county = {}, {}, set()
    for ledger in ledgers:
        county = county_of(ledger['program_id'])
        for actor in ledger['actors']:
            if actor['role'] not in POOLABLE_ROLES:
                continue
            key = slug(actor['name'])
            counties.setdefault(key, set()).add(county)
            if COUNTY_WORD.search(actor['name']):
                self_described_county.add(key)
            for e in actor.get('evidence', []):
                if not COUNTY_NAMESPACE.match(e['doc_id']):
                    statute_support.setdefault(key, []).append(
                        dict(program_id=ledger['program_id'], actor_id=actor['id'],
                             doc_id=e['doc_id'], quote=e['quote']))
    county = county_of(evidence['program_id'])
    assignments, mapping, taken = [], {}, {}
    for actor in evidence['actors']:
        key = slug(actor['name'])
        recurs = sorted(counties.get(key, ()))
        statute = statute_support.get(key, [])
        named_county = key in self_described_county
        if actor['role'] not in POOLABLE_ROLES:
            tier, canonical = UNPOOLED_TIER, actor['id']
            basis = (f"role {actor['role']} is never pooled across programmes; the ledger id "
                     'stays programme-scoped')
        elif len(recurs) >= 2 and statute and not named_county:
            tier, canonical = STATE_TIER, 'state:' + key
            basis = ('named in a statute-scope document and recurring in '
                     f"{len(recurs)} counties {recurs}, and not self-described as a county body")
        else:
            tier, canonical = COUNTY_TIER, f'county:{county}:{key}'
            basis = ('county office: ' + '; '.join(filter(None, (
                None if len(recurs) >= 2 else f'named in one county only ({recurs})',
                None if statute else 'no statute-scope document names it',
                'the name describes a county body' if named_county else None))))
        clash = taken.get(canonical)
        if clash is not None:
            raise BridgeError(f'Agency canonicalisation would merge two distinct ledger actors '
                              f'{clash} and {actor["id"]} into {canonical}; the ledger keeps them apart')
        taken[canonical] = actor['id']
        mapping[actor['id']] = canonical
        assignments.append(dict(ledger_actor_id=actor['id'], name=actor['name'], role=actor['role'],
                                tier=tier, actor_id=canonical, pooled=tier != UNPOOLED_TIER,
                                basis=basis, counties_naming_this_actor=recurs,
                                self_described_county_body=named_county,
                                statute_scope_evidence=statute))
    return dict(program_id=evidence['program_id'], county=county, assignments=assignments,
                actor_ids=mapping,
                peer_program_ids=[l['program_id'] for l in ledgers[1:]],
                state_level_names=sorted({a['actor_id'] for a in assignments if a['tier'] == STATE_TIER}),
                rule=canonical_agency_identity.__doc__.strip().splitlines()[0])


def transitive_closure(nodes, edges):
    reach = {n: set() for n in nodes}
    for a, b in edges:
        reach[a].add(b)
    changed = True
    while changed:
        changed = False
        for n in nodes:
            extra = set()
            for m in reach[n]:
                extra |= reach[m]
            if not extra <= reach[n]:
                reach[n] |= extra
                changed = True
    return reach


def find_path(edges, start, goal):
    """One directed path start->goal over explicit edges (BFS), or None."""
    parents = {start: None}
    queue = [start]
    while queue:
        node = queue.pop(0)
        for a, b in edges:
            if a == node and b not in parents:
                parents[b] = a
                queue.append(b)
    if goal not in parents:
        return None
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = parents[node]
    return list(reversed(path))


def serial_order(nodes, closure, rank, loop_members):
    """Kahn order preferring ledger rank; a repeat block is emitted contiguously."""
    parents = {n: {p for p in nodes if n in closure[p]} for n in nodes}
    done, order, open_loop = set(), [], False
    while len(order) < len(nodes):
        ready = [n for n in nodes if n not in done and parents[n] <= done]
        if not ready:
            raise BridgeError('Contradictory precedes cycle among route operations: '
                              + ', '.join(sorted(set(nodes) - done)))
        if open_loop:
            loop_ready = [n for n in ready if n in loop_members]
            if not loop_ready:
                raise BridgeError('Repeat block members cannot be made contiguous in the ledger order')
            ready = loop_ready
        nxt = min(ready, key=lambda n: (rank[n], n))
        order.append(nxt)
        done.add(nxt)
        if nxt in loop_members:
            open_loop = not (loop_members <= done)
    return order


class ProgramBridge:
    def __init__(self, evidence, handoff, compilation, report_groups=None, max_routes=MAX_ROUTES,
                 pool_agencies=False, peer_evidence=(), operation_fees=False):
        self.evidence, self.handoff, self.compilation = evidence, handoff, compilation
        self.report_groups = report_groups
        self.max_routes = int(max_routes)
        if self.max_routes < 1:
            raise BridgeError('max_routes must be positive')
        self.pool_agencies = bool(pool_agencies)
        self.peer_evidence = list(peer_evidence)
        self.operation_fees = bool(operation_fees)
        if self.peer_evidence and not self.pool_agencies:
            raise BridgeError('Peer ledgers are read only for --pool-agencies; drop one of the two')
        self.notes = {}
        self._check_versions()
        self.pid = evidence['program_id']
        self.actors = {a['id']: a for a in evidence['actors']}
        self.activities = {a['id']: a for a in evidence['activities']}
        self.listing = {a['id']: i for i, a in enumerate(evidence['activities'])}
        self.classes = {c['activity_id']: c for c in handoff['activity_classifications']}
        missing = sorted(set(self.activities) - set(self.classes))
        unknown = sorted(set(self.classes) - set(self.activities))
        if missing or unknown:
            raise BridgeError(f'Handoff classifications must cover the ledger exactly; '
                              f'missing={missing} unknown={unknown}')
        self.observations = copy.deepcopy(compilation['observations'])
        self.quantile_cohorts = copy.deepcopy(compilation.get('quantile_cohorts', []))
        if not isinstance(self.quantile_cohorts, list):
            raise BridgeError('Compiled quantile_cohorts must be an explicit list')
        for cohort in self.quantile_cohorts:
            cohort_report_observations(cohort)
        self._check_cohort_claim_ownership()
        self.referenced = self._referenced_activities()
        self.resolve_actor_identity()

    # ------------------------------------------------------------------ inputs
    def _check_versions(self):
        if self.evidence.get('schema_version') not in EVIDENCE_VERSIONS:
            raise BridgeError('Unsupported evidence schema: ' + str(self.evidence.get('schema_version')))
        if self.handoff.get('schema_version') != HANDOFF_VERSION:
            raise BridgeError('Unsupported handoff schema: ' + str(self.handoff.get('schema_version')))
        if not str(self.compilation.get('schema_version', '')).startswith(COMPILATION_PREFIX):
            raise BridgeError('Unsupported compilation schema: ' + str(self.compilation.get('schema_version')))
        ids = {self.evidence['program_id'], self.handoff['program_id'], self.compilation['program_id']}
        if len(ids) != 1:
            raise BridgeError('Evidence, handoff and compilation must describe one program: ' + str(sorted(ids)))
        if self.handoff.get('changes_accepted_evidence') or self.handoff.get('new_model_calls', 0):
            raise BridgeError('The handoff must be diagnostic-only over the accepted ledger')

    def resolve_actor_identity(self):
        """Fix the `actor_id` each operation will carry, and record why (rule j)."""
        if not self.pool_agencies:
            self.actor_ids = {a: a for a in self.actors}
            self.notes['agency_identity'] = dict(
                enabled=False, pooled_actor_count=0, assignments=[], peer_program_ids=[],
                note='--pool-agencies not given; actor ids stay programme-scoped, so no agency '
                     'is shared with another programme except the model\'s own role:payer bucket')
            return
        for peer in self.peer_evidence:
            if peer.get('schema_version') not in EVIDENCE_VERSIONS:
                raise BridgeError('Unsupported peer evidence schema: ' + str(peer.get('schema_version')))
        decision = canonical_agency_identity(self.evidence, self.peer_evidence)
        self.actor_ids = decision['actor_ids']
        self.notes['agency_identity'] = dict(
            enabled=True, county=decision['county'], peer_program_ids=decision['peer_program_ids'],
            rule=canonical_agency_identity.__doc__,
            assignments=decision['assignments'],
            pooled_actor_count=sum(1 for a in decision['assignments'] if a['pooled']),
            state_level_ids=decision['state_level_names'],
            county_scoped_ids=sorted({a['actor_id'] for a in decision['assignments']
                                      if a['tier'] == COUNTY_TIER}),
            never_pooled=[a['ledger_actor_id'] for a in decision['assignments']
                          if a['tier'] == UNPOOLED_TIER])

    def _referenced_activities(self):
        counts = {}
        for o in self.operator_factors():
            for op in o['operators']:
                for aid in op.get('activity_ids', []):
                    counts[aid] = counts.get(aid, 0) + 1
        return counts

    def operator_factors(self):
        """One entry per likelihood factor, not per cohort member or report."""
        return self.observations + [dict(c, id='quantile_cohort:' + c['id'])
                                    for c in self.quantile_cohorts]

    def _check_cohort_claim_ownership(self):
        """Do not re-admit a cohort report under a different observation ID."""
        ordinary_keys = {o['id'] for o in self.observations}
        cohort_keys = {'quantile_cohort:' + c['id'] for c in self.quantile_cohorts}
        if ordinary_keys & cohort_keys:
            raise BridgeError('Compiled observation collides with generated cohort likelihood key: ' +
                              ', '.join(sorted(ordinary_keys & cohort_keys)))
        owners = {}
        for o in self.observations:
            for mid in [o['id']] + list(o.get('measurement_ids', [])):
                owners.setdefault(mid, set()).add(('observation', o['id']))
        for c in self.quantile_cohorts:
            for r in c['reports']:
                owner = ('quantile_cohort', c['id'], r['id'])
                for mid in [r['id']] + list(r.get('measurement_ids', [])):
                    if owners.get(mid, set()) - {owner}:
                        raise BridgeError('Compiled cohort report overlaps another factor: ' + mid)
                    owners.setdefault(mid, set()).add(owner)

    # -------------------------------------------------------------- operations
    def classify(self):
        performed = [a for a in self.activities if self.classes[a]['classification'] == PERFORMED]
        groups = [g for g in self.handoff.get('conditional_paths_and_outcomes', [])
                  if g.get('decision_scope') == DISPOSITION_SCOPE]
        if len(groups) > 1:
            raise BridgeError('More than one per_decision_occasion group is not supported')
        self.disposition_group = groups[0] if groups else None
        self.dispositions, unrepresented = [], []
        if self.disposition_group:
            for member in self.disposition_group['activity_ids']:
                if member not in self.activities:
                    raise BridgeError('Outcome group names an unknown activity: ' + member)
                classification = self.classes[member]['classification']
                predecessor = self._review_predecessor(member)
                admitted = (classification in (PERFORMED, OUTCOME_EVENT)
                            and self.activities[member]['task_type'] == 'decision'
                            and predecessor is not None)
                if admitted:
                    self.dispositions.append(member)
                else:
                    unrepresented.append(dict(activity_id=member, classification=classification,
                        reason=('no performed review-stage predecessor in ledger precedes relations; '
                                'a legal outcome without a modelled adjudication occasion'
                                if predecessor is None else 'not an adjudication decision'),
                        handoff_key=f'conditional_paths_and_outcomes[{self.disposition_group["id"]}]',
                        judgment=self.classes[member]['judgment'], evidence=quotes(self.classes[member])))
        self.notes['unrepresented_outcomes'] = unrepresented
        self.operations = sorted(set(performed) | set(self.dispositions), key=self.listing.get)
        self.excluded = [dict(activity_id=a, name=self.activities[a]['name'],
                              classification=self.classes[a]['classification'],
                              ledger_scope=self.activities[a]['scope'],
                              handoff_key=f'activity_classifications[{a}]',
                              evidence=quotes(self.classes[a]))
                         for a in self.activities if a not in self.operations]

    def _review_predecessor(self, member):
        for r in self.evidence['relations']:
            if r['kind'] == 'precedes' and r['target'] == member:
                source = r['source']
                if (self.classes[source]['classification'] == PERFORMED
                        and self.activities[source]['stage'] == 'review'):
                    return source
        return None

    def build_operation(self, aid):
        activity = self.activities[aid]
        actor = self.actors[activity['actor_id']]
        role = actor['role']
        if role not in ROLE_APPLICABILITY:
            raise BridgeError('Unknown ledger actor role: ' + role)
        payer, agency = ROLE_APPLICABILITY[role]
        markers = []
        if aid in self.dispositions:
            markers.append('decision')
        for marker, target in self.boundary_markers.items():
            if target == aid:
                markers.append(marker)
        op = dict(id=aid, actor_id=self.actor_ids[actor['id']] if role in ('payer', 'agency') else None,
                  actor_role=role, task_type=activity['task_type'], markers=markers,
                  payer_work=payer, agency_work=agency)
        if self.operation_fees:
            op['fee'] = self.fees.get(aid)
        return op

    # -------------------------------------------------------------------- fees
    def _fee_disqualification(self, measurement):
        """Why a `fee` measurement is not a published charge on one step, or None."""
        m = measurement
        if m.get('case_id'):
            return ('reported by a case: an observation of what one applicant was charged, '
                    'not a published schedule amount')
        if m.get('qualitative') or m.get('value') is None:
            return 'no quoted amount; a qualitative fee ceiling states no charge'
        if m.get('unit') != FEE_UNIT:
            return 'amount is not in ' + FEE_UNIT + ': ' + str(m.get('unit'))
        if m.get('statistic') not in PUBLISHED_FEE_STATISTICS:
            return (f"statistic {m.get('statistic')!r} is a proposal, budget or ceiling, "
                    'not a published charge')
        if m.get('scope') != 'step':
            return 'not step-scoped: a process total is not attributable to one step'
        ids = m.get('activity_ids') or []
        if len(ids) != 1:
            return (f'names {len(ids)} activities; a fee is attached only on a quoted amount '
                    'naming one step, and a total is never spread across steps')
        if ids[0] not in self.operations:
            return 'names an activity that is not an operation on any route'
        return None

    def resolve_fees(self):
        """Give every operation a quoted fee, an explicit 0., or `None` (rule k).

        Three dispositions, because `payer_fee_total` sums the whole path and a
        single `None` anywhere on it makes the total refuse rather than shrink:

        * **quoted** - one published schedule amount names this step. Attached
          verbatim. Two published amounts that disagree are settled by their
          own stated currency dates where they carry them, the later superseding
          the earlier; undated disagreement still does not attach.
        * **zero by judgement** - the step is not an occasion on which the
          applicant tenders money, so traversing it costs nothing. This is a
          judgement, not a reading: it is recorded per operation with the role
          and task that carried it. Agency-side internal work (screening,
          verification, notices, decisions, records, hearings) is the strongest
          case; an applicant step that is not a payment is the softer one.
        * **unstated (`None`)** - a charge plausibly exists here and no document
          states it. That is either a `payment` task, whose whole purpose is to
          tender money, or a step some fee measurement names without settling an
          amount. `None` is NOT zero: the model refuses a fee total covering it,
          which is the intended behaviour, and the report names the routes that
          therefore have no fee total.
        """
        self.fees, by_activity, disqualified = {}, {}, []
        named_by_a_fee_claim = set()
        for m in self.evidence.get('measurements', []):
            if m.get('metric') != FEE_METRIC:
                continue
            named_by_a_fee_claim |= {a for a in (m.get('activity_ids') or []) if a in self.operations}
            reason = self._fee_disqualification(m)
            if reason:
                disqualified.append(dict(measurement_id=m['id'], activity_ids=list(m.get('activity_ids') or []),
                                         statistic=m.get('statistic'), value=m.get('value'),
                                         case_id=m.get('case_id'), doc_id=m.get('doc_id'),
                                         quote=m.get('quote'), reason=reason))
                continue
            by_activity.setdefault(m['activity_ids'][0], []).append(m)
        quoted_rows, zero_rows, unstated_rows = [], [], []
        for aid in self.operations:
            activity = self.activities[aid]
            role = self.actors[activity['actor_id']]['role']
            quoted = [dict(measurement_id=m['id'], value=float(m['value']), doc_id=m['doc_id'],
                           quote=m['quote'], statistic=m['statistic'], cohort=m.get('cohort'))
                      for m in by_activity.get(aid, [])]
            amounts = sorted({q['value'] for q in quoted})
            entry = dict(operation_id=aid, name=activity['name'], actor_role=role,
                         task_type=activity['task_type'])
            claims = sorted({d['measurement_id'] for d in disqualified if aid in d['activity_ids']})
            if len(amounts) == 1:
                self.fees[aid] = amounts[0]
                quoted_rows.append(dict(entry, fee=amounts[0], unit=FEE_UNIT, quotes=quoted))
            elif len(amounts) > 1:
                # Two published amounts need not be a conflict. Where the documents
                # date themselves, the later one supersedes and the earlier is a
                # prior version, which the benchmark scores as an error to predict.
                dated = {}
                for q in quoted:
                    row = next(m for m in by_activity[aid] if m['id'] == q['measurement_id'])
                    when = stated_currency_date(row)
                    if when is not None:
                        dated.setdefault(q['value'], []).append((when, q))
                latest = None
                if len(dated) == len(amounts):
                    ranked = sorted(((max(w for w, _ in v), a) for a, v in dated.items()),
                                    reverse=True)
                    if len(ranked) < 2 or ranked[0][0] > ranked[1][0]:
                        latest = ranked[0]
                if latest is not None:
                    when, amount = latest
                    self.fees[aid] = amount
                    superseded = sorted(a for a in amounts if a != amount)
                    quoted_rows.append(dict(entry, fee=amount, unit=FEE_UNIT, quotes=quoted,
                        resolved_by='most recent stated currency date',
                        current_as_of='-'.join(str(x) for x in when if x) or str(when[0]),
                        superseded_amounts=superseded,
                        basis=('the documents date themselves and the later amount supersedes; '
                               'the earlier is a prior version, not a competing current price')))
                else:
                    self.fees[aid] = None
                    unstated_rows.append(dict(entry, fee=None,
                        missing='a single published amount: the documents disagree (' +
                                ', '.join(f'{a:g}' for a in amounts) + ')',
                        reason=('the bridge does not choose between conflicting quoted amounts '
                                'that do not date themselves; recency can only settle a conflict '
                                'the documents themselves date'),
                        quotes=quoted))
            elif activity['task_type'] == 'payment':
                self.fees[aid] = None
                unstated_rows.append(dict(entry, fee=None,
                    missing='a published amount for a step whose purpose is to tender money',
                    reason='payment task with no published schedule amount; a charge plausibly '
                           'exists and no document states it',
                    fee_claims_not_usable=claims))
            elif aid in named_by_a_fee_claim:
                self.fees[aid] = None
                unstated_rows.append(dict(entry, fee=None,
                    missing='a usable published amount for a step a fee claim names',
                    reason='a fee measurement links a charge to this step but none of them settles '
                           'a published amount',
                    fee_claims_not_usable=claims))
            else:
                self.fees[aid] = 0.
                judgement = ('agency-side internal work: the applicant does not perform it and no '
                             'document charges the applicant for the agency\'s own step'
                             if role == 'agency' else
                             'internal processing step with an unresolved performer; it is not an '
                             'occasion on which the applicant tenders money'
                             if role in ('unknown', 'third_party') else
                             'applicant step that is not a payment; this corpus prices payment '
                             'steps and no schedule prices this one')
                zero_rows.append(dict(entry, fee=0., judgement=judgement,
                                      judgement_not_a_reading=True))
        self.notes['operation_fees'] = dict(
            enabled=True, unit=FEE_UNIT,
            rule=self.resolve_fees.__doc__,
            published_statistics=list(PUBLISHED_FEE_STATISTICS),
            operations_with_quoted_fee=quoted_rows,
            operations_zero_by_judgement=zero_rows,
            operations_with_unstated_fee=unstated_rows,
            counts=dict(quoted=len(quoted_rows), zero_by_judgement=len(zero_rows),
                        unstated=len(unstated_rows)),
            fee_measurements_not_used_as_route_input=disqualified,
            none_is_not_zero='fee=None states no fee for that step; the model refuses a fee total '
                             'covering such an operation rather than counting it as zero',
            zero_is_a_judgement='fee=0. asserts the applicant tenders nothing at that step; it is '
                                'a recorded judgement about the step, not a quoted amount')

    def record_fee_availability(self, program):
        """Say plainly which routes and paths can produce a `payer_fee_total`."""
        routes = []
        for route in program['routes']:
            unstated = sorted(o['id'] for o in route['operations'] if o.get('fee') is None)
            paths = []
            for path in route.get('paths', []):
                members = [o for b in path['blocks'] for o in b['operations']]
                blocked = [o for o in members if o in unstated]
                paths.append(dict(path_id=path['id'], fee_total_available=not blocked,
                                  operations_without_a_stated_fee=blocked))
            routes.append(dict(route_id=route['id'],
                               fee_total_available=not unstated,
                               operations_without_a_stated_fee=unstated,
                               paths_without_a_fee_total=[p['path_id'] for p in paths
                                                          if not p['fee_total_available']],
                               paths=paths))
        blocked_routes = [r['route_id'] for r in routes if not r['fee_total_available']]
        self.notes['operation_fees']['fee_total_availability'] = dict(
            available_on_every_route=not blocked_routes,
            routes_without_a_fee_total=blocked_routes,
            note=('every route carries a stated fee on every operation, so a payer_fee_total is '
                  'available throughout' if not blocked_routes else
                  'a payer_fee_total is UNAVAILABLE on ' + ', '.join(blocked_routes) +
                  ': each contains an operation whose fee no document states, and an unstated fee '
                  'must not become a silent zero inside a sum'),
            routes=routes)

    def resolve_markers(self):
        declared = self.handoff.get('clock_boundary_markers') or {}
        if not isinstance(declared, dict) or any(k not in OPTIONAL_MARKERS for k in declared):
            raise BridgeError('clock_boundary_markers must map submission/complete_submission/'
                              'legal_closeout to activity ids')
        self.boundary_markers = {}
        for marker, target in declared.items():
            if target not in self.operations:
                raise BridgeError(f'Boundary marker {marker} names a non-operation: {target}')
            self.boundary_markers[marker] = target
        record = {'decision': dict(activity_ids=list(self.dispositions),
            handoff_key=(f'conditional_paths_and_outcomes[{self.disposition_group["id"]}]'
                         if self.disposition_group else None),
            rule='adjudication dispositions of the per_decision_occasion group reached from '
                 'performed review-stage work')}
        for marker in OPTIONAL_MARKERS:
            record[marker] = dict(activity_ids=[self.boundary_markers[marker]] if marker in self.boundary_markers else [],
                handoff_key='clock_boundary_markers' if marker in self.boundary_markers else None,
                note=None if marker in self.boundary_markers else
                     'handoff names no boundary activity; marker omitted, so clock events on it are unavailable')
        self.notes['markers'] = record

    # ------------------------------------------------------------------- order
    def build_order(self):
        ops = set(self.operations)
        contexts = self.evidence.get('observation_contexts', [])
        measurements = {m['id']: m for m in self.evidence['measurements']}
        scopes = {}
        for c in contexts:
            scopes.setdefault(measurements[c['measurement_id']]['doc_id'], set()).add(c['temporal_scope'])
        hypothetical_docs = sorted(d for d, s in scopes.items() if s == {'hypothetical'})
        self.notes['hypothetical_only_documents'] = hypothetical_docs
        kept, excluded, self.parallel = [], [], []
        for r in self.evidence['relations']:
            if r['source'] not in ops or r['target'] not in ops:
                continue
            docs = {e['doc_id'] for e in r['evidence']}
            if r['kind'] == 'parallel':
                self.parallel.append(r)
                continue
            if r['kind'] != 'precedes':
                continue
            if docs and docs <= set(hypothetical_docs):
                excluded.append(dict(source=r['source'], target=r['target'], support=r['support'],
                    condition=r.get('condition'), evidence=quotes(r),
                    reason='every supporting document is uniformly hypothetical in the ledger contexts'))
                continue
            kept.append(r)
        self.notes['relations_excluded_hypothetical_documents'] = excluded
        relaxed = []
        edges = [(r['source'], r['target']) for r in kept]
        by_edge = {(r['source'], r['target']): r for r in kept}
        for r in self.parallel:
            u, v = r['source'], r['target']
            for a, b in ((u, v), (v, u)):
                while True:
                    path = find_path(edges, a, b)
                    if path is None:
                        break
                    chain = list(zip(path[:-1], path[1:]))
                    def weakness(edge):
                        rel = by_edge[edge]
                        return (0 if rel['support'] == 'inferred' else 1,
                                0 if rel.get('condition') else 1, chain.index(edge))
                    victim = min(chain, key=weakness)
                    edges.remove(victim)
                    relaxed.append(dict(source=victim[0], target=victim[1],
                        support=by_edge[victim]['support'], condition=by_edge[victim].get('condition'),
                        evidence=quotes(by_edge[victim]),
                        reason=f'lies on a precedes chain between the quoted parallel pair {u} || {v}',
                        parallel_evidence=quotes(r)))
        self.notes['precedes_relations_relaxed_for_quoted_parallel'] = relaxed
        self.edges = edges
        self.closure = transitive_closure(self.operations, edges)
        for a, b in edges:
            if a in self.closure[b]:
                raise BridgeError(f'Contradictory precedes cycle through {a} and {b}; '
                                  'the bridge does not choose between conflicting quoted orders')
        related = {x for e in edges for x in e} | {x for r in self.parallel for x in (r['source'], r['target'])}
        first_disposition = min((self.listing[d] for d in self.dispositions), default=None)
        self.rank, placed = {}, []
        for aid in self.operations:
            rank = self.listing[aid]
            if aid not in related:
                stage = STAGE_RANK.get(self.activities[aid]['stage'], STAGE_RANK['unknown'])
                if first_disposition is not None and stage < STAGE_RANK['decision']:
                    rank = min(rank, first_disposition - .5)
                placed.append(dict(activity_id=aid, ledger_stage=self.activities[aid]['stage'], rank=rank))
            self.rank[aid] = rank
        self.notes['unrelated_operations_placed_by_listing_rank'] = placed

    # ------------------------------------------------------------- repeat loop
    def build_loop(self):
        rework = [(r['source'], r['target']) for r in self.evidence['relations'] if r['kind'] == 'rework']
        self.loop, self.loop_key, skipped = set(), None, []
        for link in self.handoff.get('repeat_links', []):
            members = [a for a in link['activity_ids'] if a in self.operations]
            joined = [(a, b) for a, b in rework if a in members and b in members]
            if not joined:
                skipped.append(dict(id=link['id'], activity_ids=link['activity_ids'],
                    interpretation=link.get('interpretation'),
                    reason='no ledger rework relation joins its members; not a within-case loop'))
                continue
            if self.loop:
                raise BridgeError('Nested or multiple repeat loops are not supported by the trace model')
            self.loop, self.loop_key = set(members), link['id']
            self.notes['repeat_block'] = dict(repeat_key=link['id'], operations=members,
                handoff_key=f'repeat_links[{link["id"]}]', rework_relations=joined,
                explicit=link.get('explicit'), evidence=quotes(link))
        self.notes.setdefault('repeat_block', None)
        self.notes['repeat_links_not_encoded'] = skipped

    # ------------------------------------------------------------------- paths
    def build_path_plan(self):
        D = self.dispositions
        reach_from = {x: {d for d in D if x in self.closure[d]} for x in self.operations}
        for x in self.loop:
            if reach_from[x]:
                raise BridgeError('A repeat-loop member cannot follow the adjudication: ' + x)
        toggles = []
        for g in self.handoff.get('conditional_paths_and_outcomes', []):
            if g.get('decision_scope') not in OPTIONAL_SCOPES:
                continue
            members = [a for a in g['activity_ids'] if a in self.operations]
            optional = [a for a in members if a not in D and a not in self.loop
                        and self.activities[a]['scope'] == 'conditional']
            if not optional:
                continue
            attached = [d for d in D if d in g['activity_ids']]
            toggles.append(dict(id=g['id'], operations=optional, attached_dispositions=attached,
                                handoff_key=f'conditional_paths_and_outcomes[{g["id"]}]',
                                decision_scope=g['decision_scope']))
        merged = []
        for t in toggles:
            hit = next((m for m in merged if set(m['operations']) & set(t['operations'])), None)
            if hit is None:
                merged.append(dict(t))
            else:
                hit['id'] = hit['id'] + '+' + t['id']
                hit['operations'] = sorted(set(hit['operations']) | set(t['operations']), key=self.listing.get)
                hit['attached_dispositions'] = sorted(set(hit['attached_dispositions']) | set(t['attached_dispositions']))
                hit['handoff_key'] = hit['handoff_key'] + ';' + t['handoff_key']
        self.toggles = merged
        optional_ops = {x for t in merged for x in t['operations']}
        self.membership = {}
        for x in self.operations:
            if x in D:
                self.membership[x] = ('disposition', [x])
            elif x in optional_ops:
                self.membership[x] = ('optional', None)
            elif reach_from[x]:
                self.membership[x] = ('after_disposition', sorted(reach_from[x]))
            else:
                self.membership[x] = ('common', None)
        self.notes['path_plan'] = dict(dispositions=D, optional_toggles=merged,
            after_disposition={x: v[1] for x, v in self.membership.items() if v[0] == 'after_disposition'})

    def enumerate_paths(self, route_ops):
        """Path specs (id, disposition, operation list) for one route's operations."""
        ops = [x for x in self.operations if x in route_ops]
        D = [d for d in self.dispositions if d in route_ops]
        if not D:
            return [dict(id=None, disposition=None, operations=ops)]
        paths = []
        for d in D:
            applicable = [t for t in self.toggles if not t['attached_dispositions'] or d in t['attached_dispositions']]
            for mask in range(2 ** len(applicable)):
                on = [t for i, t in enumerate(applicable) if mask >> i & 1]
                on_ops = {x for t in on for x in t['operations']}
                members = [x for x in ops if (self.membership[x][0] == 'common'
                           or (self.membership[x][0] == 'disposition' and x == d)
                           or (self.membership[x][0] == 'after_disposition' and d in self.membership[x][1])
                           or (self.membership[x][0] == 'optional' and x in on_ops))]
                paths.append(dict(id=d + ''.join('+' + t['id'] for t in on), disposition=d, operations=members))
        return paths

    # ------------------------------------------------------------------ blocks
    def build_blocks(self, members):
        members = [x for x in self.operations if x in members]
        loop = self.loop & set(members)
        order = serial_order(members, self.closure, self.rank, loop)
        parallel_pairs = [(r['source'], r['target']) for r in self.parallel
                          if r['source'] in members and r['target'] in members]
        position = {x: i for i, x in enumerate(order)}
        intervals = []
        for u, v in parallel_pairs:
            lo, hi = sorted((position[u], position[v]))
            intervals.append([lo, hi])
        intervals.sort()
        spans = []
        for lo, hi in intervals:
            if spans and lo <= spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], hi)
            else:
                spans.append([lo, hi])
        blocks, i = [], 0
        forced = []
        while i < len(order):
            span = next((s for s in spans if s[0] == i), None)
            if order[i] in loop:
                end = i + len(loop)
                blocks.append(dict(id='repeat:' + self.loop_key, operations=order[i:end],
                                   edges=None, repeat_key=self.loop_key))
                i = end
            elif span is not None:
                lo, hi = span
                start, block, edges, unordered = self._parallel_block(order, lo, hi, parallel_pairs, loop)
                if start < i:
                    blocks.pop()
                blocks.append(dict(id='parallel:' + '+'.join(short(x) for x in block),
                                   operations=block, edges=[list(e) for e in edges], repeat_key=None))
                forced.extend(unordered)
                i = start + len(block)
            else:
                blocks.append(dict(id='serial:' + short(order[i]), operations=[order[i]],
                                   edges=None, repeat_key=None))
                i += 1
        return blocks, forced

    def _parallel_block(self, order, lo, hi, parallel_pairs, loop):
        """Explicit partial order for the topological interval spanning a quoted parallel pair.

        Quoted precedes edges are kept; every other pair is serialized in ledger
        order unless doing so would order a quoted parallel pair. A bare pair is
        extended by one serial neighbour so the block never carries `edges: []`.
        """
        pairs = {frozenset(p) for p in parallel_pairs}

        def within(a, b):
            return b in self.closure[a]

        def attempt(members):
            edges = [(a, b) for a in members for b in members if a != b and within(a, b)]
            unordered = []
            for x in range(len(members)):
                for y in range(x + 1, len(members)):
                    a, b = members[x], members[y]
                    if within(a, b) or within(b, a) or frozenset((a, b)) in pairs:
                        continue
                    trial = edges + [(a, b)]
                    closure = transitive_closure(members, trial)
                    if any(v in closure[u] or u in closure[v] for u, v in parallel_pairs
                           if u in members and v in members):
                        unordered.append(dict(pair=[a, b],
                            reason='serializing would order a quoted parallel pair; left unordered'))
                    else:
                        edges = trial
            closure = transitive_closure(members, edges)
            reduced = [(a, b) for a, b in edges if not any(
                c not in (a, b) and c in closure[a] and b in closure[c] for c in members)]
            return reduced, unordered

        start, block = lo, order[lo:hi + 1]
        if len(block) < 2:
            raise BridgeError('A parallel block needs two members')
        edges, unordered = attempt(block)
        if not edges:
            if hi + 1 < len(order) and order[hi + 1] not in loop:
                block = order[lo:hi + 2]
            elif lo > 0 and order[lo - 1] not in loop:
                start, block = lo - 1, order[lo - 1:hi + 1]
            else:
                raise BridgeError('A quoted parallel pair has no serial neighbour to anchor explicit edges')
            edges, unordered = attempt(block)
            if not edges:
                raise BridgeError('Refusing to emit edges: [] for a quoted parallel pair')
        return start, block, edges, unordered

    # ------------------------------------------------------------------ routes
    def build_routes(self):
        candidates, other = [], []
        D = set(self.dispositions)
        for h in self.handoff.get('inventory_identity_hypotheses', []):
            members = [a for a in h['activity_ids'] if a in self.operations]
            if set(members) & D and len(members) > 1:
                other.append(dict(id=h['id'], activity_ids=h['activity_ids'],
                                  status='encoded_as_case_paths', handoff_key=f'inventory_identity_hypotheses[{h["id"]}]'))
                continue
            if len(members) < 2 or len(members) != len(h['activity_ids']):
                other.append(dict(id=h['id'], activity_ids=h['activity_ids'], status='unrepresented',
                                  reason=('fewer than two members are operations' if len(members) < 2 else
                                          'a listed member is not an operation; the hypothesis concerns an '
                                          "excluded activity's work boundary, not a merge of operations"),
                                  handoff_key=f'inventory_identity_hypotheses[{h["id"]}]'))
                continue
            referenced = sum(1 for a in members if self.referenced.get(a))
            candidates.append(dict(hypothesis=h, members=members, referenced=referenced, rank=h.get('rank')))
        ranked = [c for c in candidates if c['rank'] is not None]
        unranked = [c for c in candidates if c['rank'] is None]
        ranked.sort(key=lambda c: c['rank'])
        unranked.sort(key=lambda c: (-c['referenced'],
                                     self.handoff['inventory_identity_hypotheses'].index(c['hypothesis'])))
        seen_membership = {frozenset(self.operations)}
        kept, unrepresented = [], []
        for c in ranked + unranked:
            h = c['hypothesis']
            representative = max(c['members'], key=lambda a: (self.referenced.get(a, 0), -c['members'].index(a)))
            dropped = [a for a in c['members'] if a != representative]
            route_ops = frozenset(a for a in self.operations if a not in dropped)
            if route_ops in seen_membership:
                unrepresented.append(dict(id=h['id'], activity_ids=h['activity_ids'],
                    reason='same operation membership as a kept route', handoff_key=f'inventory_identity_hypotheses[{h["id"]}]'))
                continue
            if len(kept) + 1 >= self.max_routes:
                unrepresented.append(dict(id=h['id'], activity_ids=h['activity_ids'],
                    reason=f'route cap {self.max_routes} reached', handoff_key=f'inventory_identity_hypotheses[{h["id"]}]'))
                continue
            seen_membership.add(route_ops)
            kept.append(dict(hypothesis=h, representative=representative, dropped=dropped, route_ops=route_ops))
        routes, records = [], []
        specs = [dict(id=BASE_ROUTE_ID, ops=frozenset(self.operations), hypothesis=None, representative=None, dropped=[])]
        specs += [dict(id='merge:' + k['hypothesis']['id'], ops=k['route_ops'], hypothesis=k['hypothesis'],
                       representative=k['representative'], dropped=k['dropped']) for k in kept]
        weight = 1. / len(specs)
        for spec in specs:
            route, record = self.build_route(spec, weight)
            routes.append(route)
            records.append(record)
        self.notes['routes'] = records
        self.notes['unrepresented_hypotheses'] = unrepresented + [o for o in other if o['status'] == 'unrepresented']
        self.notes['hypotheses_encoded_as_case_paths'] = [o for o in other if o['status'] == 'encoded_as_case_paths']
        self.notes['route_prior_weight'] = dict(value=weight, basis='uniform declared assumption, not evidence')
        return routes

    def build_route(self, spec, weight):
        ops = [self.build_operation(a) for a in self.operations if a in spec['ops']]
        paths = self.enumerate_paths(spec['ops'])
        route = dict(id=spec['id'], prior_weight=weight, operations=ops)
        forced_all, path_records = [], []
        if paths[0]['id'] is None:
            blocks, forced = self.build_blocks(paths[0]['operations'])
            route['blocks'] = blocks
            forced_all.extend(forced)
        else:
            route['paths'] = []
            for path in paths:
                blocks, forced = self.build_blocks(path['operations'])
                route['paths'].append(dict(id=path['id'], probability_weight=1. / len(paths), blocks=blocks))
                forced_all.extend(forced)
                path_records.append(dict(id=path['id'], disposition=path['disposition'],
                                         operations=[b for blk in blocks for b in blk['operations']]))
        for block in (route.get('blocks') or [b for p in route['paths'] for b in p['blocks']]):
            if block['edges'] == []:
                raise BridgeError('Refusing to emit edges: [] (read as fully parallel)')
        unique, seen = [], set()
        for f in forced_all:
            key = tuple(f['pair'])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        forced_all = unique
        record = dict(id=spec['id'], operations=[o['id'] for o in ops],
                      hypothesis_id=spec['hypothesis']['id'] if spec['hypothesis'] else None,
                      handoff_key=(f'inventory_identity_hypotheses[{spec["hypothesis"]["id"]}]'
                                   if spec['hypothesis'] else 'activity_classifications'),
                      representative=spec['representative'], merged_away=spec['dropped'],
                      paths=path_records, path_probability_weight=(1. / len(paths) if paths[0]['id'] else None),
                      forced_unordered_pairs=forced_all,
                      compiled_operators_referencing_non_route_activities=self.residual_operators(spec['ops']))
        return route, record

    def residual_operators(self, route_ops):
        rows = []
        for o in self.operator_factors():
            for j, op in enumerate(o['operators']):
                ids = op.get('activity_ids', [])
                missing = [a for a in ids if a not in route_ops]
                if not missing:
                    continue
                unavailable = (len(missing) == len(ids)) if op.get('activity_selection') == 'first_present' else True
                rows.append(dict(observation_id=o['id'], operator_index=j, basis=op['basis'],
                                 missing_activity_ids=missing, reading_unavailable_on_route=unavailable))
        return dict(count=sum(1 for r in rows if r['reading_unavailable_on_route']), operators=rows)

    # --------------------------------------------------------------- scoping
    def build_case_scope(self, routes):
        cases = {o['case_id'] for o in self.observations if o.get('case_id')}
        measurements = {m['id']: m for m in self.evidence['measurements']}
        path_ids = [p['id'] for r in routes for p in r.get('paths', [])]
        scope, records, unrepresentable = {}, [], []
        D = set(self.dispositions)
        by_case = {}
        for c in self.evidence.get('observation_contexts', []):
            m = measurements[c['measurement_id']]
            if not m['case_id'] or m['case_id'] not in cases:
                continue
            decided = c.get('decision_activity_id')
            if decided in D:
                by_case.setdefault(m['case_id'], []).append((decided, c))
            elif decided is None and D and D <= set(c.get('excluded_activity_ids', [])):
                unrepresentable.append(dict(case_id=m['case_id'], measurement_id=c['measurement_id'],
                    reason='ledger context excludes every adjudication disposition (withdrawal); '
                           'no withdrawn path is encoded, the case stays unscoped', evidence=quotes(c)))
        for case, entries in by_case.items():
            outcomes = {d for d, _ in entries}
            if len(outcomes) != 1:
                raise BridgeError(f'Conflicting quoted outcomes for case {case}: {sorted(outcomes)}')
            d = outcomes.pop()
            chosen = sorted({p for p in path_ids if p == d or p.startswith(d + '+')})
            if not chosen:
                raise BridgeError('Quoted outcome has no path on the routes: ' + d)
            scope[case] = chosen
            records.append(dict(case_id=case, disposition=d, paths=chosen,
                ledger_key=[f'observation_contexts[{c["measurement_id"]}].decision_activity_id' for _, c in entries],
                evidence=[q for _, c in entries for q in quotes(c)]))
        self.notes['case_path_scope'] = records
        self.notes['cases_without_representable_outcome'] = unrepresentable
        return scope

    # ----------------------------------------------------------------- output
    def build(self):
        self.classify()
        if self.operation_fees:
            self.resolve_fees()
        else:
            self.fees = {}
            self.notes['operation_fees'] = dict(
                enabled=False, operations_with_quoted_fee=[], operations_zero_by_judgement=[],
                operations_with_unstated_fee=[],
                note='--operation-fees not given; no operation carries a fee field')
        self.resolve_markers()
        self.build_order()
        self.build_loop()
        self.build_path_plan()
        routes = self.build_routes()
        scope = self.build_case_scope(routes)
        program = dict(id=self.pid, routes=routes, observations=self.observations,
                       rate_observations=[], quantile_cohorts=self.quantile_cohorts, case_path_scope=scope)
        if self.operation_fees:
            self.record_fee_availability(program)
        self.check_model(program)
        return program, self.report(program)

    def check_model(self, program):
        bases = {op['basis'] for o in self.operator_factors() for op in o['operators']}
        # Legacy rows with no unit mean calendar days. A new business-day cohort
        # must not silently reinterpret those existing observations.
        nonelapsed = COUNT_BASES | set(MONEY_BASES) | set(CHANNELS[1:])
        time_units = {o.get('time_unit', 'calendar_days') for o in self.operator_factors()
                      if any(op['basis'] not in nonelapsed for op in o['operators'])}
        if len(time_units) > 1:
            raise BridgeError('Compiled elapsed time units must agree; the bridge does not convert clocks')
        cfg = Config(population_size=16, within_visit_phases=bool(bases & PHASE_BASES),
                     modeled_channels=tuple(ch for ch in CHANNELS if ch == 'elapsed' or ch in bases),
                     elapsed_time_unit=next(iter(time_units), 'calendar_days'))
        supported = 'fee' in {f.name for f in dataclasses.fields(Operation)}
        payload = dict(programs=[program])
        if cfg.elapsed_time_unit != 'calendar_days':
            payload['elapsed_time_unit'] = cfg.elapsed_time_unit
        if self.operation_fees:
            self.notes['operation_fees']['model_operation_fee_field_supported'] = supported
            if not supported:
                # The installed trace model predates the optional `Operation.fee`
                # this bridge populates. `data.json` keeps the fees; only this
                # construction check drops them, and says so.
                self.notes['operation_fees']['self_check_note'] = (
                    'compact_visit_trace.Operation has no `fee` field yet, so the bridge dropped '
                    'the fees for its own VisitHierarchy construction check only; data.json keeps '
                    'them and a run against this model will fail until the field lands')
                payload = copy.deepcopy(payload)
                for route in payload['programs'][0]['routes']:
                    for op in route['operations']:
                        op.pop('fee', None)
        model = VisitHierarchy(payload, cfg)
        self.notes['clock_boundary_support'] = model.clock_support_report()
        self.notes['visit_hierarchy_constructed'] = dict(dimensions=model.layout.size,
            operations=len(model.operations), within_visit_phases=cfg.within_visit_phases,
            modeled_channels=list(cfg.modeled_channels),
            **(dict(elapsed_time_unit=cfg.elapsed_time_unit)
               if cfg.elapsed_time_unit != 'calendar_days' else {}))

    def report(self, program):
        none_count = sum(1 for r in program['routes'] for o in r['operations']
                         if o['payer_work'] is None and o['agency_work'] is None)
        base_none = [o['id'] for o in program['routes'][0]['operations']
                     if o['payer_work'] is None and o['agency_work'] is None]
        groups = None
        if self.report_groups is not None:
            groups = self.check_report_groups()
        rows = self.observations
        return dict(schema_version=REPORT_VERSION, program_id=self.pid,
            hidden_truth_read=False, source_documents_read=False, model_calls=0,
            inputs=dict(evidence_schema=self.evidence['schema_version'], handoff_schema=self.handoff['schema_version'],
                        compilation_schema=self.compilation['schema_version'],
                        handoff_evidence_sha256=(self.handoff.get('provenance') or {}).get('evidence_sha256')),
            operations=dict(count=len(self.operations), ids=list(self.operations),
                            performed_operation_count=sum(1 for a in self.operations if self.classes[a]['classification'] == PERFORMED),
                            admitted_dispositions=list(self.dispositions)),
            excluded_activities=self.excluded,
            agency_identity=self.notes['agency_identity'],
            operation_fees=self.notes['operation_fees'],
            applicability=dict(rule=dict(ROLE_APPLICABILITY),
                               none_applicability_operations_base_route=base_none,
                               none_applicability_operation_count_base_route=len(base_none),
                               none_applicability_operation_count_all_routes=none_count),
            markers=self.notes['markers'],
            clock_boundary_support=self.notes['clock_boundary_support'],
            order=dict(precedes_edges_used=[list(e) for e in self.edges],
                       parallel_relations=[dict(source=r['source'], target=r['target'], support=r['support'],
                                                evidence=quotes(r)) for r in self.parallel],
                       hypothetical_only_documents=self.notes['hypothetical_only_documents'],
                       relations_excluded_hypothetical_documents=self.notes['relations_excluded_hypothetical_documents'],
                       precedes_relations_relaxed_for_quoted_parallel=self.notes['precedes_relations_relaxed_for_quoted_parallel'],
                       unrelated_operations_placed_by_listing_rank=self.notes['unrelated_operations_placed_by_listing_rank']),
            repeat_block=self.notes['repeat_block'],
            repeat_links_not_encoded=self.notes['repeat_links_not_encoded'],
            path_plan=self.notes['path_plan'],
            unrepresented_outcomes=self.notes['unrepresented_outcomes'],
            routes=self.notes['routes'],
            route_prior_weight=self.notes['route_prior_weight'],
            unrepresented_hypotheses=self.notes['unrepresented_hypotheses'],
            hypotheses_encoded_as_case_paths=self.notes['hypotheses_encoded_as_case_paths'],
            case_path_scope=self.notes['case_path_scope'],
            cases_without_representable_outcome=self.notes['cases_without_representable_outcome'],
            observations=dict(copied_verbatim=True, count=len(rows),
                              rows_with_modeled_operators=sum(1 for o in rows if any(op['basis'] != 'unmodeled_duration' for op in o['operators'])),
                              residual_only_rows=sum(1 for o in rows if all(op['basis'] == 'unmodeled_duration' for op in o['operators'])),
                              cases=sorted({o['case_id'] for o in rows if o.get('case_id')}),
                              phase_operators_present=bool({op['basis'] for o in rows for op in o['operators']} & PHASE_BASES),
                              compilation_coverage=self.compilation.get('coverage')),
            rate_observations=dict(count=0, reason='no source-derived rate sidecar exists in the V6 contract; '
                                   'a planning rate per eligible checkpoint visit is not a counted cohort'),
            quantile_cohorts=(dict(count=len(self.quantile_cohorts), copied_verbatim=True,
                joint_report_rows=sum(len(c['reports']) for c in self.quantile_cohorts),
                sample_sizes={c['id']: c['sample_size'] for c in self.quantile_cohorts},
                independent_factors=len(self.quantile_cohorts),
                denominator_basis='Explicit upstream compiled cohort contracts, not inferred by this bridge.',
                qualification='Same-cohort summaries remain one joint factor. Source semantics, '
                    'sampling and completeness remain upstream review obligations.')
                if self.quantile_cohorts else dict(count=0, reason='no compiled finite-quantile cohorts supplied')),
            report_groups=groups,
            visit_hierarchy_constructed=self.notes['visit_hierarchy_constructed'],
            declared_assumptions=list(DECLARED_ASSUMPTIONS))

    def check_report_groups(self):
        owners = {}
        for o in self.observations:
            for mid in [o['id']] + list(o.get('measurement_ids', [])):
                owners.setdefault(mid, set()).add(o['id'])
        for c in self.quantile_cohorts:
            for r in c['reports']:
                for mid in [r['id']] + list(r.get('measurement_ids', [])):
                    owners.setdefault(mid, set()).add('quantile_cohort:' + c['id'])
        inconsistent = []
        for g in self.report_groups.get('groups', []):
            hit = {oid for mid in g['measurement_ids'] for oid in owners.get(mid, ())}
            if len(hit) > 1:
                inconsistent.append(dict(group_id=g['id'], observation_ids=sorted(hit)))
        return dict(schema_version=self.report_groups.get('schema_version'),
                    groups=len(self.report_groups.get('groups', [])),
                    groups_split_across_compiled_factors=inconsistent,
                    consistent_with_compilation=not inconsistent)


def bridge_program(evidence, handoff, compilation, report_groups=None, max_routes=MAX_ROUTES,
                   pool_agencies=False, peer_evidence=(), operation_fees=False):
    return ProgramBridge(evidence, handoff, compilation, report_groups, max_routes,
                         pool_agencies, peer_evidence, operation_fees).build()


def combine_programs(datasets):
    programs = [p for d in datasets for p in d['programs']]
    ids = [p['id'] for p in programs]
    if len(set(ids)) != len(ids):
        raise BridgeError('Combined programmes must have distinct ids: ' + str(ids))
    cohort_ids = set()
    individual_cohort_ids = {o.get('cohort_id') for p in programs
                            for o in p.get('observations', []) + p.get('rate_observations', [])
                            if o.get('cohort_id') is not None}
    for p in programs:
        for c in p.get('quantile_cohorts', []) + p.get('histogram_cohorts', []):
            identity = c['cohort_id']
            if identity in cohort_ids or identity in individual_cohort_ids:
                raise BridgeError('Combined programmes contain overlapping cohort identity: ' + identity)
            cohort_ids.add(identity)
    units = {d.get('elapsed_time_unit', 'calendar_days') for d in datasets}
    if len(units) > 1:
        raise BridgeError('Combined programmes must use one elapsed time unit; no conversion is implicit')
    unit = next(iter(units), 'calendar_days')
    return dict(programs=programs,
                **(dict(elapsed_time_unit=unit) if unit != 'calendar_days' else {}))


def run_program(args):
    out = pathlib.Path(args.out)
    if out.exists():
        raise BridgeError('Choose a fresh output directory: ' + str(out))
    inputs = [pathlib.Path(args.evidence), pathlib.Path(args.handoff), pathlib.Path(args.compilation)]
    report_groups = None
    if args.report_groups:
        inputs.append(pathlib.Path(args.report_groups))
        report_groups = load(args.report_groups)
    evidence, handoff, compilation = (load(p) for p in inputs[:3])
    peer_paths = [pathlib.Path(p) for p in (args.peer_evidence or [])]
    inputs.extend(peer_paths)
    peer_evidence = [load(p) for p in peer_paths]
    record = RunManifest(out, {}, operation='v6.bridge_structural_routes', inputs=inputs,
        config=dict(max_routes=args.max_routes, pool_agencies=bool(args.pool_agencies),
                    operation_fees=bool(args.operation_fees),
                    peer_evidence=[str(p) for p in peer_paths],
                    declared_assumptions=DECLARED_ASSUMPTIONS),
        seeds={}, hidden_truth_read=False, source_root=pathlib.Path(__file__).parent,
        sources=['bridge_structural_routes.py'])
    program, report = bridge_program(evidence, handoff, compilation, report_groups, args.max_routes,
                                     pool_agencies=args.pool_agencies, peer_evidence=peer_evidence,
                                     operation_fees=args.operation_fees)
    data = dict(programs=[program])
    unit = report['visit_hierarchy_constructed'].get('elapsed_time_unit', 'calendar_days')
    if unit != 'calendar_days':
        data['elapsed_time_unit'] = unit
    write(out / 'data.json', data)
    write(out / 'bridge_report.json', report)
    record.complete(data_sha256=digest((out / 'data.json').read_bytes()),
                    report_sha256=digest((out / 'bridge_report.json').read_bytes()),
                    hidden_truth_read=False, model_calls=0,
                    routes=len(program['routes']), operations=len(program['routes'][0]['operations']),
                    pooled_agency_actors=report['agency_identity']['pooled_actor_count'],
                    operations_with_fee=len(report['operation_fees']['operations_with_quoted_fee']),
                    operations_with_unstated_fee=len(report['operation_fees']['operations_with_unstated_fee']),
                    paths_per_route=[len(r.get('paths', [])) for r in program['routes']])
    print(json.dumps(dict(program=program['id'], routes=len(program['routes']),
        operations=len(program['routes'][0]['operations']),
        paths_per_route=[len(r.get('paths', [])) for r in program['routes']],
        excluded_activities=len(report['excluded_activities']),
        none_applicability=report['applicability']['none_applicability_operation_count_base_route'],
        pooled_agency_actors=report['agency_identity']['pooled_actor_count'],
        operations_with_fee=len(report['operation_fees']['operations_with_quoted_fee']),
        operations_zero_by_judgement=len(report['operation_fees']['operations_zero_by_judgement']),
        operations_with_unstated_fee=len(report['operation_fees']['operations_with_unstated_fee']),
        fee_total_available=(report['operation_fees'].get('fee_total_availability') or {}).get(
            'available_on_every_route'),
        dimensions=report['visit_hierarchy_constructed']['dimensions'])), flush=True)


def run_combine(args):
    out = pathlib.Path(args.out)
    if out.exists():
        raise BridgeError('Choose a fresh output directory: ' + str(out))
    inputs = [pathlib.Path(p) for p in args.inputs]
    record = RunManifest(out, {}, operation='v6.bridge_combine_programs', inputs=inputs,
        config=dict(inputs=[str(p) for p in inputs]), seeds={}, hidden_truth_read=False,
        source_root=pathlib.Path(__file__).parent, sources=['bridge_structural_routes.py'])
    data = combine_programs([load(p) for p in inputs])
    write(out / 'data.json', data)
    record.complete(data_sha256=digest((out / 'data.json').read_bytes()),
                    programs=[p['id'] for p in data['programs']], hidden_truth_read=False)
    print(json.dumps(dict(programs=[p['id'] for p in data['programs']])), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('program', help='Bridge one programme to a V6 runner input')
    p.add_argument('--evidence', required=True)
    p.add_argument('--handoff', required=True)
    p.add_argument('--compilation', required=True)
    p.add_argument('--report-groups')
    p.add_argument('--out', required=True)
    p.add_argument('--max-routes', type=int, default=MAX_ROUTES)
    p.add_argument('--pool-agencies', action='store_true',
                   help='Canonicalise agency actor ids by the three-tier rule so genuinely shared '
                        'bodies pool across programmes. Default off: ids stay programme-scoped and '
                        'data.json is unchanged.')
    p.add_argument('--peer-evidence', nargs='*', default=[],
                   help='Other programmes evidence ledgers, read only to decide agency identity '
                        '(recurrence across counties and statute-scope naming). Needs --pool-agencies.')
    p.add_argument('--operation-fees', action='store_true',
                   help='Attach a published fee to each operation a quoted schedule amount names. '
                        'Default off: no operation carries a fee field.')
    p.set_defaults(run=run_program)
    c = sub.add_parser('combine', help='Concatenate bridged programmes into one runner input')
    c.add_argument('--inputs', nargs='+', required=True)
    c.add_argument('--out', required=True)
    c.set_defaults(run=run_combine)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == '__main__':
    main()
