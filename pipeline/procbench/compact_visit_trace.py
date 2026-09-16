"""Repeated-block traces with exact clocks without enumerating every visit.

Blocks are sequential; operations within a block follow an explicitly supplied
DAG. Missing within-block order defaults to serial, NOT independence. Each repeat
replays the entire block; visit durations for an operation are perfectly correlated
within a case. This is a declared model assumption, not a claim extracted from text.
No finite maximum repeat count or renormalized count tail is introduced.
"""
from dataclasses import dataclass
import math

import numpy as np

from .bayes_hierarchy import topological_order
from .visit_clocks import Trace, Visit


class UnavailableTraceQuantity(ValueError):
    """A valid observation refers to an event absent/impossible on this route.

    Distinct from malformed operator syntax, which must fail validation rather
    than silently becoming an impossible interpretation.
    """


CLOCK_EVENTS = frozenset({'process_start', 'modeled_work_end', 'end_of_modeled_work',
    'first_submission', 'first_complete_submission', 'initial_decision',
    'final_decision', 'last_decision', 'legal_closeout'})


def validate_operator(operator):
    """Check syntax independently of which operations/events a route contains."""
    basis = operator.get('basis')
    activity_bases = {'single_visit_cycle', 'sum_visit_cycles', 'first_to_last_activity_span',
                      'wait_elapsed', 'service_elapsed'}
    other_bases = {'visit_count', 'operation_count', 'agency_count', 'payer_hours', 'agency_hours'}
    if basis == 'whole_case_clock':
        if operator.get('start') not in CLOCK_EVENTS or operator.get('end') not in CLOCK_EVENTS:
            raise ValueError('Malformed clock operator: unsupported or missing event')
    elif basis in activity_bases | other_bases:
        ids = operator.get('activity_ids', [])
        if not isinstance(ids, list) or any(not isinstance(a, str) or not a for a in ids) or len(ids) != len(set(ids)):
            raise ValueError('Malformed operator: activity IDs must be distinct nonempty strings')
        if basis in activity_bases and (not ids or (basis == 'single_visit_cycle' and len(ids) != 1)):
            raise ValueError('Malformed cycle/span operator: explicit activity linkage required')
        if basis in {'wait_elapsed', 'service_elapsed'}:
            if operator.get('visits') not in {'first', 'last', 'one_unspecified', 'all_in_completed_case'}:
                raise ValueError('Malformed phase operator: explicit supported visit scope required')
            if operator['visits'] != 'all_in_completed_case' and len(ids) != 1:
                raise ValueError('Malformed phase operator: a single visit requires one activity')
    elif basis == 'additional_rounds':
        if not isinstance(operator.get('repeat_key'), str) or not operator['repeat_key']:
            raise ValueError('Malformed repeat operator: repeat_key required')
    elif basis != 'unmodeled_duration':
        raise ValueError('Malformed operator: unknown basis ' + str(basis))


@dataclass(frozen=True)
class Operation:
    id: str
    actor_id: str | None
    actor_role: str
    task_type: str
    markers: tuple[str, ...] = ()
    payer_work: bool | None = None
    agency_work: bool | None = None

    def __post_init__(self):
        # Reuse the clock/actor validation contract; resource applicability is
        # explicit. An absent work field does not assert zero effort.
        Visit(self.id, self.id, 0., 1., self.actor_id, self.actor_role, self.markers)
        if not self.task_type or any(v is not None and not isinstance(v, bool)
                                     for v in (self.payer_work, self.agency_work)):
            raise ValueError('Need a task type and explicit true/false/unknown work applicability')


@dataclass(frozen=True)
class Block:
    id: str
    operations: tuple[str, ...]
    edges: tuple[tuple[str, str], ...] | None = None
    repeat_key: str | None = None


class CompactTrace:
    """Vectorized complete latent traces; each array row is one realized case."""
    def __init__(self, operations, blocks, durations, additional_rounds=None, resources=None,
                 service_fractions=None):
        self.operations, self.blocks = tuple(operations), tuple(blocks)
        self.index = {op.id: i for i, op in enumerate(self.operations)}
        if len(self.index) != len(self.operations) or not self.operations:
            raise ValueError('A route requires distinct operation identities')
        durations = np.asarray(durations, dtype=float)
        if durations.ndim != 2 or durations.shape[1] != len(self.operations) or (
                not np.isfinite(durations).all() or np.any(durations <= 0)):
            raise ValueError('Visit durations must be finite positive cases-by-operations')
        self.durations, self.resources = durations, resources or {}
        self.service_fractions = None
        if service_fractions is not None:
            fractions = np.asarray(service_fractions, dtype=float)
            if fractions.shape != durations.shape or not np.isfinite(fractions).all() or (
                    np.any(fractions < 0) or np.any(fractions > 1)):
                raise ValueError('Service fractions must be finite cases-by-operations proportions')
            self.service_fractions = fractions
        n, k = durations.shape
        self.first_start, self.first_end = np.zeros((n,k)), np.zeros((n,k))
        self.last_start, self.last_end = np.zeros((n,k)), np.zeros((n,k))
        self.visits = np.ones((n,k), dtype=np.int64)
        self.rounds, self._block_states = {}, []
        cursor, seen, block_ids, keys = np.zeros(n), set(), set(), set()
        supplied = additional_rounds or {}
        for block in self.blocks:
            if not block.id or block.id in block_ids or not block.operations or (
                    len(set(block.operations)) != len(block.operations)):
                raise ValueError('Blocks require unique IDs and nonempty distinct operation lists')
            block_ids.add(block.id)
            if not set(block.operations) <= self.index.keys() or seen & set(block.operations):
                raise ValueError('Each operation must occur in exactly one route block')
            seen.update(block.operations)
            ids = np.array([self.index[aid] for aid in block.operations])
            local = {aid: j for j,aid in enumerate(block.operations)}
            edges = tuple(zip(block.operations[:-1],block.operations[1:])) if block.edges is None else block.edges
            if any(a not in local or b not in local for a,b in edges):
                raise ValueError('An edge must be within its repeat block')
            local_edges = [(local[a],local[b]) for a,b in edges]
            order = topological_order(len(ids),local_edges)
            starts, ends = np.zeros((n,len(ids))), np.zeros((n,len(ids)))
            for j in order:
                parents = [a for a,b in local_edges if b==j]
                starts[:,j] = ends[:,parents].max(axis=1) if parents else 0.
                ends[:,j] = starts[:,j]+durations[:,ids[j]]
            cycle = ends.max(axis=1)
            counts = np.zeros(n,dtype=np.int64)
            if block.repeat_key is not None:
                if not block.repeat_key or block.repeat_key in keys:
                    raise ValueError('Repeat keys must be distinct within a route')
                keys.add(block.repeat_key)
                if block.repeat_key not in supplied:
                    raise ValueError('Every repeat block needs its realized additional-round count')
                raw = np.asarray(supplied[block.repeat_key])
                if raw.shape != (n,) or not np.issubdtype(raw.dtype,np.integer) or np.any(raw<0):
                    raise ValueError('Additional rounds must be nonnegative integer case counts')
                counts = raw.astype(np.int64)
                self.rounds[block.repeat_key] = counts
            self.first_start[:,ids] = cursor[:,None]+starts
            self.first_end[:,ids] = cursor[:,None]+ends
            self.last_start[:,ids] = cursor[:,None]+counts[:,None]*cycle[:,None]+starts
            self.last_end[:,ids] = cursor[:,None]+counts[:,None]*cycle[:,None]+ends
            self.visits[:,ids] = counts[:,None]+1
            self._block_states.append((block,ids,cursor.copy(),starts,ends,cycle,counts))
            cursor = cursor+(counts+1)*cycle
        if seen != self.index.keys() or set(supplied) != keys:
            raise ValueError('Route must cover every operation and supplied repeat key exactly once')
        self.modeled_end = cursor
        for channel, amounts in self.resources.items():
            if channel not in {'payer_hours','agency_hours'}:
                raise ValueError('Unknown resource channel')
            a = np.asarray(amounts)
            if a.shape != durations.shape or np.any(a[np.isfinite(a)]<0) or np.isinf(a).any():
                raise ValueError('Resource arrays must match visits, with NaN for missing amounts')

    def event(self,name):
        if name=='process_start':
            return np.zeros(len(self.durations))
        if name in {'modeled_work_end','end_of_modeled_work'}:
            return self.modeled_end
        marker,which = {
            'first_submission':('submission','first'),
            'first_complete_submission':('complete_submission','first'),
            'initial_decision':('decision','first'),
            'final_decision':('decision','last'),
            'last_decision':('decision','last'),
            'legal_closeout':('legal_closeout','last'),
        }.get(name,(None,None))
        if marker is None:
            raise ValueError('An explicitly modeled event is required: '+name)
        ids = [i for i,op in enumerate(self.operations) if marker in op.markers]
        if not ids:
            raise UnavailableTraceQuantity('Event is absent from this route: '+name)
        return self.first_end[:,ids].min(axis=1) if which=='first' else self.last_end[:,ids].max(axis=1)

    def values(self, operator):
        """A resolved operator only; ambiguity is mixed by the likelihood, not here.

        Counts/resources cover the complete modeled route, not an implicit initial
        decision cutoff. A single visit is exchangeable under the repeated-duration
        assumption, so first/last/unspecified cycles are equal in this model only.
        """
        basis = operator['basis']
        ids = [self.index[aid] for aid in operator.get('activity_ids',[])]
        if basis=='whole_case_clock':
            value = self.event(operator['end'])-self.event(operator['start'])
            if np.any(value<0):
                raise UnavailableTraceQuantity('Clock endpoint precedes its start on this route')
            return value
        if basis in {'single_visit_cycle','sum_visit_cycles','first_to_last_activity_span'}:
            if not ids or (basis=='single_visit_cycle' and len(ids)!=1):
                raise ValueError('Cycle/span operator requires linked operations; one for a single visit')
            if basis=='single_visit_cycle':
                return self.durations[:,ids[0]]
            if basis=='sum_visit_cycles':
                return (self.durations[:,ids]*self.visits[:,ids]).sum(axis=1)
            return self.last_end[:,ids].max(axis=1)-self.first_start[:,ids].min(axis=1)
        if basis in {'wait_elapsed', 'service_elapsed'}:
            if self.service_fractions is None:
                raise ValueError('Within-visit waiting/service phases are unmodeled, not zero or a whole cycle')
            if not ids:
                raise ValueError('A phase operator requires explicitly linked operations')
            scope = operator.get('visits')
            if scope in {'first', 'last', 'one_unspecified'}:
                if len(ids) != 1:
                    raise ValueError('A single-visit phase requires one operation')
                multiplicity = 1
            elif scope == 'all_in_completed_case':
                multiplicity = self.visits[:, ids]
            else:
                raise ValueError('Phase visit coverage requires a complete case or one explicit visit scope')
            fraction = self.service_fractions[:, ids]
            fraction = fraction if basis == 'service_elapsed' else 1 - fraction
            return (self.durations[:, ids] * fraction * multiplicity).sum(axis=1)
        if basis=='additional_rounds':
            key = operator['repeat_key']
            if key not in self.rounds:
                raise UnavailableTraceQuantity('No such repeat block on this route')
            return self.rounds[key]
        selected = ids or list(range(len(self.operations)))
        if basis=='visit_count':
            return self.visits[:,selected].sum(axis=1)
        if basis=='operation_count':
            return np.full(len(self.durations),len(selected))
        if basis=='agency_count':
            ops = [self.operations[i] for i in selected]
            if any(op.actor_role=='unknown' or (op.actor_role=='agency' and op.actor_id is None) for op in ops):
                raise ValueError('Unknown agency identities cannot become an exact zero or count')
            return np.full(len(self.durations),len({op.actor_id for op in ops if op.actor_role=='agency'}))
        if basis in {'payer_hours','agency_hours'}:
            if basis not in self.resources:
                raise ValueError('Resource channel is unmeasured/unmodeled, not zero')
            values = self.resources[basis][:,selected]
            if not np.isfinite(values).all():
                raise ValueError('A total cannot silently omit unknown work amounts')
            return (values*self.visits[:,selected]).sum(axis=1)
        raise ValueError('Unsupported observation operator: '+basis)

    def materialize(self,case=0,max_visits=10000):
        """Independent reference/display path; the inference path has no visit cap."""
        if int(self.visits[case].sum())>max_visits:
            raise ValueError('Reference expansion too large; use the uncapped compact operators')
        rows=[]
        for block,ids,cursor,starts,ends,cycle,counts in self._block_states:
            for round_number in range(int(counts[case])+1):
                offset=cursor[case]+round_number*cycle[case]
                for j,i in enumerate(ids):
                    op=self.operations[i]
                    def resource(channel):
                        a=self.resources.get(channel)
                        return float(a[case,i]) if a is not None and math.isfinite(a[case,i]) else None
                    rows.append(Visit(f'{block.id}:{op.id}:{round_number}',op.id,
                        float(offset+starts[case,j]),float(offset+ends[case,j]),
                        op.actor_id,op.actor_role,op.markers,
                        service_start=(None if self.service_fractions is None else
                            float(offset+starts[case,j]+self.durations[case,i]*(1-self.service_fractions[case,i]))),
                        payer_hours=resource('payer_hours'),agency_hours=resource('agency_hours')))
        return Trace(tuple(rows))
