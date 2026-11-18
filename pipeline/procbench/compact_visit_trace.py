"""Repeated-block traces with exact clocks without enumerating every visit.

Blocks are sequential unless every block declares an explicit predecessor DAG;
operations within a block follow an explicitly supplied DAG. Missing order
defaults to serial, NOT independence. Each repeat
replays the entire block; visit durations for an operation are perfectly correlated
within a case. This is a declared model assumption, not a claim extracted from text.
No finite maximum repeat count or renormalized count tail is introduced.

A block may additionally declare inter-operation dwells: elapsed time immediately
before a named operation during which NO operation is working. A dwell is queue
time, not a visit and not work, so it moves the clock and nothing else. Absent a
declaration, operations stay adjacent exactly as before; the primitive is opt-in
per gap, and its waiting times are supplied by the caller, never defaulted.
"""
from dataclasses import dataclass
import math

import numpy as np

from .bayes_hierarchy import topological_order
from .visit_clocks import Trace, Visit
# Kept as a local import inside population_quantile to avoid importing the
# histogram contract for ordinary deterministic trace users.


class UnavailableTraceQuantity(ValueError):
    """A valid observation refers to an event absent/impossible on this route.

    Distinct from malformed operator syntax, which must fail validation rather
    than silently becoming an impossible interpretation.
    """


CLOCK_EVENTS = frozenset({'process_start', 'modeled_work_end', 'end_of_modeled_work',
    'first_submission', 'first_complete_submission', 'initial_decision',
    'final_decision', 'last_decision', 'legal_closeout'})

# Shared by execution and structural coverage diagnostics. A missing marker is
# absent model support, not evidence that the corresponding text reading is false.
CLOCK_EVENT_MARKERS = {
    'first_submission': ('submission', 'first'),
    'first_complete_submission': ('complete_submission', 'first'),
    'initial_decision': ('decision', 'first'),
    'final_decision': ('decision', 'last'),
    'last_decision': ('decision', 'last'),
    'legal_closeout': ('legal_closeout', 'last'),
}

# Money is a path functional, NOT a fourth resource channel. A published fee is an
# input, not a random quantity: it needs no agency/task/operation hierarchy and
# allocates no coordinate. All of its uncertainty is the path and repeat
# uncertainty the model already carries, so a case that stops at the first gate
# never pays for the inspection and a case that repeats a correction block pays
# that block's fees again. Handled like COUNT_BASES in `bayes_trace_hierarchy`:
# it may not mix with duration or count operators, and it is an individual report.
MONEY_BASES = ('payer_fee_total',)


def validate_operator(operator):
    """Check syntax independently of which operations/events a route contains."""
    basis = operator.get('basis')
    activity_bases = {'single_visit_cycle', 'sum_visit_cycles', 'first_to_last_activity_span',
                      'wait_elapsed', 'service_elapsed'}
    other_bases = ({'visit_count', 'operation_count', 'agency_count', 'payer_hours', 'agency_hours'}
                   | set(MONEY_BASES))
    selection = operator.get('activity_selection')
    if selection is not None and (selection != 'first_present' or basis != 'single_visit_cycle'
                                  or operator.get('visits') != 'first'):
        raise ValueError('An activity union currently requires the first single-visit cycle')
    if basis == 'whole_case_clock':
        if operator.get('start') not in CLOCK_EVENTS or operator.get('end') not in CLOCK_EVENTS:
            raise ValueError('Malformed clock operator: unsupported or missing event')
    elif basis == 'activity_event_interval':
        if set(operator) != {'basis', 'start', 'end'}:
            raise ValueError('An activity interval needs exactly start and end selectors')
        for selector in (operator['start'], operator['end']):
            if (not isinstance(selector, dict)
                    or set(selector) != {'activity_id', 'event', 'occurrence'}
                    or not isinstance(selector['activity_id'], str)
                    or not selector['activity_id'].strip()
                    or selector['activity_id'] != selector['activity_id'].strip()
                    or selector['event'] not in {'start', 'end'}
                    or selector['occurrence'] not in {'first', 'last'}):
                raise ValueError('Activity interval endpoints need an action, start/end and first/last occurrence')
    elif basis == 'activity_event_clock':
        if (set(operator) != {'basis', 'start', 'activity_ids', 'event_occurrence'}
                or operator['start'] not in CLOCK_EVENTS
                or operator['event_occurrence'] not in {'first', 'last'}
                or not isinstance(operator['activity_ids'], list)
                or len(operator['activity_ids']) != 1
                or not isinstance(operator['activity_ids'][0], str)
                or not operator['activity_ids'][0]):
            raise ValueError('An activity event clock needs one endpoint operation, occurrence and explicit start')
    elif basis in activity_bases | other_bases:
        ids = operator.get('activity_ids', [])
        if not isinstance(ids, list) or any(not isinstance(a, str) or not a for a in ids) or len(ids) != len(set(ids)):
            raise ValueError('Malformed operator: activity IDs must be distinct nonempty strings')
        if basis in activity_bases and (not ids or (basis == 'single_visit_cycle'
                                                  and len(ids) != 1 and selection is None)):
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
    # Published applicant-paid amount in USD for one visit to this operation.
    # `None` means no fee is stated for this step and is NOT zero; only an
    # explicit 0. asserts that traversing this step costs the applicant nothing.
    fee: float | None = None

    def __post_init__(self):
        # Reuse the clock/actor validation contract; resource applicability is
        # explicit. An absent work field does not assert zero effort.
        Visit(self.id, self.id, 0., 1., self.actor_id, self.actor_role, self.markers)
        if not self.task_type or any(v is not None and not isinstance(v, bool)
                                     for v in (self.payer_work, self.agency_work)):
            raise ValueError('Need a task type and explicit true/false/unknown work applicability')
        if self.fee is not None and (isinstance(self.fee, bool) or not isinstance(self.fee, (int, float))
                                     or not math.isfinite(self.fee) or self.fee < 0):
            raise ValueError('A published fee must be an explicit finite nonnegative amount or absent')


@dataclass(frozen=True)
class Block:
    id: str
    operations: tuple[str, ...]
    edges: tuple[tuple[str, str], ...] | None = None
    repeat_key: str | None = None
    # Operations of this block that are preceded by an inter-operation dwell.
    # Naming a gap here declares that waiting happens there and that a duration
    # for it must be supplied; omitting an operation declares adjacency, which
    # is the historical model. An empty/absent tuple changes nothing.
    dwells: tuple[str, ...] | None = None
    # None on EVERY block preserves the historical serial block sequence.
    # Otherwise EVERY block must declare its predecessor block IDs (an empty
    # tuple is an explicit root). This is a supplied scheduling hypothesis,
    # never an inference that unreported dependencies mean parallel execution.
    predecessors: tuple[str, ...] | None = None


def unit_dwell_array(operations, blocks, rows=1):
    """One-day placeholder at each declared gap for structural validation only.

    Returns `None` when no block declares a dwell, so a dwell-free route builds
    through exactly the historical code path. This is never a modelled waiting
    time: it exists so a route's shape can be checked before anything is drawn.
    """
    declared = {aid for block in blocks for aid in (block.dwells or ())}
    if not declared:
        return None
    index = {op.id: i for i, op in enumerate(operations)}
    values = np.full((rows, len(operations)), math.nan)
    for aid in declared & index.keys():
        values[:, index[aid]] = 1.
    return values


class PopulationTraceMixture:
    """Finite case-path mixture, distinct from an inventory hypothesis.

    Each component uses the same population integration grid and shared hierarchy.
    A missing event in any positively weighted component is NOT silently dropped;
    an explicitly conditional population must select its paths first.
    """
    def __init__(self, traces, probabilities, path_ids):
        self.traces, self.path_ids = tuple(traces), tuple(path_ids)
        self.probabilities = np.asarray(probabilities, dtype=float)
        if (not self.traces or len(self.traces) != len(self.probabilities)
                or len(self.path_ids) != len(self.traces)
                or len(set(self.path_ids)) != len(self.path_ids)
                or not np.isfinite(self.probabilities).all()
                or np.any(self.probabilities <= 0)
                or not np.isclose(self.probabilities.sum(), 1., rtol=0., atol=1e-12)):
            raise ValueError('A population path mixture needs distinct IDs and positive normalized weights')
        self.weights = np.concatenate([np.full(len(t.durations), p/len(t.durations))
            for t,p in zip(self.traces,self.probabilities)])

    def select(self, path_ids):
        chosen = [i for i,ident in enumerate(self.path_ids) if ident in path_ids]
        if not chosen:
            raise UnavailableTraceQuantity('No case path satisfies the stated population scope')
        probabilities = self.probabilities[chosen]
        probabilities = probabilities/probabilities.sum()
        return PopulationTraceMixture([self.traces[i] for i in chosen], probabilities,
                                      [self.path_ids[i] for i in chosen])

    def values(self, operator):
        return np.concatenate([trace.values(operator) for trace in self.traces])

    def event(self, name):
        return np.concatenate([trace.event(name) for trace in self.traces])


def observation_population(trace, operator, observation):
    """Apply declared population conditions, never infer them from missing events.

    A first-visit summary samples one first visit per case containing the named
    operation (or operation union), not all repeat visits or all program cases.
    This does not model duration-dependent completion/recording selection.
    """
    scope = observation.get('population_path_scope')
    if scope:
        trace = trace.select(scope)
    condition = observation.get('population_condition')
    if condition is None:
        return trace
    if (condition != 'first_visit' or operator.get('basis') != 'single_visit_cycle'
            or operator.get('visits') != 'first'):
        raise ValueError('Unsupported population condition/operator combination')
    ids = set(operator['activity_ids'])
    def occurs(component):
        return (bool(ids & component.index.keys()) if operator.get('activity_selection') == 'first_present'
                else ids <= component.index.keys())
    if isinstance(trace, PopulationTraceMixture):
        return trace.select([ident for ident, component in zip(trace.path_ids, trace.traces)
                             if occurs(component)])
    if not occurs(trace):
        raise UnavailableTraceQuantity('The first-visit population is absent from this route')
    return trace


def _analytic_elapsed_parameters(trace, values):
    parameters=getattr(trace,'analytic_elapsed_log_parameters',None)
    # The exact law belongs to the elapsed column, not to arbitrary values a
    # caller might supply (counts, logs, squared durations, etc.).
    if parameters is not None and np.array_equal(np.asarray(values),trace.durations[:,0]):
        return parameters
    return None


def population_quantile(trace, values, quantile):
    parameters=_analytic_elapsed_parameters(trace,values)
    if parameters is not None:
        from .analytic_phase import phase_quantile
        return phase_quantile(*parameters, quantile)
    values = np.asarray(values, dtype=float)
    if not 0 <= quantile <= 1:
        raise ValueError('Invalid population quantile')
    if not isinstance(trace, PopulationTraceMixture) or len(trace.traces) == 1:
        return float(np.quantile(values, quantile))
    if values.shape != trace.weights.shape:
        raise ValueError('Population values and path integration weights must match')
    order = np.argsort(values, kind='stable')
    index = np.searchsorted(np.cumsum(trace.weights[order]), quantile)
    return float(values[order[min(index, len(order)-1)]])


def population_statistic(trace, values, statistic):
    """Population functional with explicit path weights; no equal-path shortcut.

    Legacy traces keep their original NumPy quantile convention. A multi-path
    population uses the inverse of its weighted empirical CDF. This is a finite
    integration approximation and remains subject to the runner's precision gate.
    """
    if statistic not in {'mean', 'median', 'p90'}:
        raise ValueError('Unknown population statistic')
    parameters=_analytic_elapsed_parameters(trace,values)
    if parameters is not None:
        if statistic == 'mean':
            location,scale=parameters
            return float(np.exp(location+.5*scale**2))
        return population_quantile(trace,values,.9 if statistic=='p90' else .5)
    values = np.asarray(values, dtype=float)
    if statistic == 'mean':
        return float(values @ trace.weights if isinstance(trace, PopulationTraceMixture) else np.mean(values))
    return population_quantile(trace, values, .9 if statistic == 'p90' else .5)


class CompactTrace:
    """Vectorized complete latent traces; each array row is one realized case."""
    def __init__(self, operations, blocks, durations, additional_rounds=None, resources=None,
                 service_fractions=None, dwells=None):
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
        # AN UNSTATED DWELL IS NOT ZERO, AND THESE REFUSALS MUST STAY HARD ERRORS.
        # `UnavailableTraceQuantity` describes one *observation* that names an event
        # this route cannot have, so the likelihood may drop that reading and keep
        # the others. A declared gap with no supplied waiting time is not a property
        # of any observation: it is caught while the route itself is being built,
        # before a single operator is evaluated, and it would corrupt every elapsed
        # quantity on the route rather than one reading of one claim. Softening it
        # would also recreate exactly the failure the audit measured below for
        # hours/counts/money: of two routes differing only in whether a gap's wait
        # was stated, the one that honestly declared the gap and left it unsupplied
        # would silently become the route with no waiting at all and out-compete
        # the honest encoding, with nothing reporting that it had.
        self.dwell_sites = []
        for block in self.blocks:
            names = tuple(block.dwells or ())
            if (len(set(names)) != len(names) or not set(names) <= set(block.operations)
                    or not set(names) <= self.index.keys()):
                raise ValueError('A declared dwell must precede a distinct operation of its own block')
            self.dwell_sites.extend(names)
        self.dwell_sites = tuple(self.dwell_sites)
        self.dwell_days = None
        if self.dwell_sites:
            if dwells is None:
                raise ValueError('A declared inter-operation dwell has no waiting time; an unstated dwell is not zero')
            gaps = np.asarray(dwells, dtype=float)
            if gaps.shape != durations.shape:
                raise ValueError('Inter-operation dwells must be a cases-by-operations array')
            declared = np.zeros(len(self.operations), dtype=bool)
            declared[[self.index[aid] for aid in self.dwell_sites]] = True
            if not np.isfinite(gaps[:, declared]).all() or np.any(gaps[:, declared] <= 0):
                raise ValueError('A declared inter-operation dwell needs a finite positive wait, never a silent zero')
            if not np.isnan(gaps[:, ~declared]).all():
                raise ValueError('An undeclared gap cannot carry dwell time; declare the dwell on its block')
            self.dwell_days = np.where(declared, gaps, 0.)
        elif dwells is not None:
            raise ValueError('Inter-operation dwell times supplied for a route that declares no dwell')
        n, k = durations.shape
        self.first_start, self.first_end = np.zeros((n,k)), np.zeros((n,k))
        self.last_start, self.last_end = np.zeros((n,k)), np.zeros((n,k))
        self.visits = np.ones((n,k), dtype=np.int64)
        self.rounds, self._block_states = {}, []
        cursor, seen, block_ids, keys = np.zeros(n), set(), set(), set()
        supplied = additional_rounds or {}
        explicit_block_graph = any(b.predecessors is not None for b in self.blocks)
        block_order = range(len(self.blocks))
        block_ends = {}
        if explicit_block_graph:
            positions = {b.id: i for i,b in enumerate(self.blocks)}
            if len(positions) != len(self.blocks) or any(not b.id for b in self.blocks):
                raise ValueError('Blocks require unique IDs')
            block_edges = []
            for block in self.blocks:
                parents = block.predecessors
                if not isinstance(parents, (list, tuple)):
                    raise ValueError('Explicit block scheduling requires predecessor lists on every block')
                if (any(not isinstance(p,str) or p not in positions for p in parents)
                        or len(set(parents)) != len(parents)):
                    raise ValueError('Block predecessors must be distinct known block IDs')
                block_edges.extend((positions[p],positions[block.id]) for p in parents)
            block_order = topological_order(len(self.blocks), block_edges)
        for block_index in block_order:
            block = self.blocks[block_index]
            if explicit_block_graph:
                cursor = (np.maximum.reduce([block_ends[p] for p in block.predecessors])
                          if block.predecessors else np.zeros(n))
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
                if self.dwell_days is not None:
                    # The dwell elapses after this operation's predecessors finish
                    # and before it starts, so it lengthens the block cycle (and
                    # therefore recurs on every repeat round) without touching the
                    # operation's own visit duration, its visit count or its work.
                    starts[:,j] = starts[:,j]+self.dwell_days[:,ids[j]]
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
            if explicit_block_graph:
                block_ends[block.id] = cursor
        if seen != self.index.keys() or set(supplied) != keys:
            raise ValueError('Route must cover every operation and supplied repeat key exactly once')
        self.modeled_end = np.maximum.reduce(list(block_ends.values())) if explicit_block_graph else cursor
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
        marker,which = CLOCK_EVENT_MARKERS.get(name,(None,None))
        if marker is None:
            raise ValueError('An explicitly modeled event is required: '+name)
        ids = [i for i,op in enumerate(self.operations) if marker in op.markers]
        if not ids:
            raise UnavailableTraceQuantity('Event is absent from this route: '+name)
        return self.first_end[:,ids].min(axis=1) if which=='first' else self.last_end[:,ids].max(axis=1)

    def values(self, operator):
        """A resolved operator only; ambiguity is mixed by the likelihood, not here.

        Counts/resources/fees cover the complete modeled route, not an implicit initial
        decision cutoff. A single visit is exchangeable under the repeated-duration
        assumption, so first/last/unspecified cycles are equal in this model only.
        """
        basis = operator['basis']
        if operator.get('activity_selection') == 'first_present':
            validate_operator(operator)
            ids = [self.index[aid] for aid in operator['activity_ids'] if aid in self.index]
            if not ids:
                raise UnavailableTraceQuantity('No member of the stated activity union occurs on this path')
            starts = self.first_start[:, ids]
            first = np.argmin(starts, axis=1)
            if np.any(np.sum(starts == starts.min(axis=1)[:, None], axis=1) != 1):
                raise UnavailableTraceQuantity('Simultaneous union members do not identify one first visit')
            return self.durations[:, ids][np.arange(len(self.durations)), first]
        ids = [self.index[aid] for aid in operator.get('activity_ids',[])]
        if basis=='whole_case_clock':
            value = self.event(operator['end'])-self.event(operator['start'])
            if np.any(value<0):
                raise UnavailableTraceQuantity('Clock endpoint precedes its start on this route')
            return value
        if basis=='activity_event_interval':
            validate_operator(operator)
            def endpoint(selector):
                aid = selector['activity_id']
                if aid not in self.index:
                    raise UnavailableTraceQuantity('Activity interval endpoint absent from route: '+aid)
                times = getattr(self, selector['occurrence']+'_'+selector['event'])
                return times[:, self.index[aid]]
            value = endpoint(operator['end'])-endpoint(operator['start'])
            if np.any(value < 0):
                raise UnavailableTraceQuantity('Activity interval endpoint precedes its origin on this route')
            # An interval uses the shared schedule, not a sum of endpoint task
            # durations: intervening waits, parallel branches and repetitions
            # contribute exactly when they move its declared endpoints.
            return value
        if basis=='activity_event_clock':
            validate_operator(operator)
            ends = self.first_end if operator['event_occurrence']=='first' else self.last_end
            value = ends[:, ids[0]]-self.event(operator['start'])
            if np.any(value<0):
                raise UnavailableTraceQuantity('Activity endpoint precedes its clock start on this route')
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
        # THESE THREE REFUSALS MUST STAY HARD ERRORS. On 2026-09-18 they were
        # briefly reclassified to `UnavailableTraceQuantity` on the theory that the
        # honest encoding of missing evidence (unknown applicability, an
        # unidentified actor) should fall to residual mass rather than crash the
        # sampler. That theory was wrong, and the audit that caught it measured
        # why: a resource-hours or count observation has NO residual alternative
        # (`bayes_trace_hierarchy` rejects mixing `agency_hours` with
        # `unmodeled_duration`, and count probabilities with duration densities),
        # so the caught exception made the whole observation -inf on that route.
        # With two routes differing only in whether an operation's applicability
        # was known, the unknown route's posterior probability went to exactly
        # zero: the encoding alone decided the inventory, and nothing reported it.
        # A loud failure at the first likelihood call is strictly better than a
        # silent structural inference. Until a process-independent hours/count
        # residual exists, an observation that needs a quantity this route cannot
        # supply is a construction error, not an unavailable quantity.
        #
        # A malformed or unrecognised operator is likewise a hard `ValueError`.
        # A money total below refuses on exactly the same grounds: an unstated
        # fee cannot silently become zero inside a sum, and `bayes_trace_hierarchy`
        # rejects mixing money with durations or counts, so a money observation
        # has no residual alternative to fall to either. Routing it to residual
        # would silently zero the posterior of whichever route honestly recorded
        # that a step's fee is unknown.
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
        if basis in MONEY_BASES:
            # The same sum-over-visits form as a resource channel, over published
            # amounts that nothing samples: repeating a block pays its fees again,
            # and an operation this path omits is never charged.
            fees = np.array([math.nan if self.operations[i].fee is None else self.operations[i].fee
                             for i in selected], dtype=float)
            if not np.isfinite(fees).all():
                raise ValueError('A fee total cannot silently omit steps with no stated fee')
            return (fees[None,:]*self.visits[:,selected]).sum(axis=1)
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
