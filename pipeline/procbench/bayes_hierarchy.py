"""Joint Bayesian agency/task/step timing and case-report model (v4).

Interpretation is an auditable upstream instrument, not this model's truth.
Continuous inference uses blocked elliptical slice sampling; finite structural
variables use exact conditional categorical updates. No benchmark imports.

Individual step reports AND totals observe the same latent case durations.
Population summaries use deterministic quadrature over new cases. Changing the
quadrature seed/size is an approximation check, not extra observed data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import re
import time

import numpy as np
from scipy.special import expit, logsumexp, ndtr, ndtri, stdtr, softmax
from scipy.linalg import helmert
from scipy.stats import qmc

from .evidence_contract import validate
from .latent_gaussian import diagnostics, elliptical_slice, information_report, summary
from .schedule_kernel import schedule_native


@dataclass(frozen=True)
class Config:
    seed: int = 20260916
    chains: int = 4
    warmup: int = 1000
    draws: int = 1000
    thin: int = 2
    population_size: int = 128
    population_seed: int = 817
    global_median: float = 7.
    global_log_sd: float = 2.
    agency_scale: float = 1.
    task_scale: float = 1.
    step_scale: float = 1.
    source_bias_sd: float = .35
    outcome_logit_sd: float = 1.5
    report_sd: float = .25
    outlier_probability: float = .08
    unseen_mean: float = 2.
    max_unseen: int = 8
    graph_variants: int = 6
    use_process_claims: bool = True
    use_hierarchy: bool = True
    channel: str = "elapsed"

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.global_median, self.global_log_sd,
                self.agency_scale, self.task_scale, self.step_scale, self.source_bias_sd,
                self.report_sd, self.outlier_probability, self.unseen_mean, self.outcome_logit_sd)):
            raise ValueError('Configuration numbers must be finite')
        if self.chains < 1 or self.draws < 8 or self.warmup < 0 or self.thin < 1:
            raise ValueError('Need positive chains/thinning, nonnegative warmup, and at least eight retained draws')
        if self.population_size < 16 or self.graph_variants < 1 or self.max_unseen < 0 or self.unseen_mean < 0:
            raise ValueError('Invalid quadrature or structural-prior configuration')
        if self.global_median <= 0 or self.global_log_sd <= 0 or self.report_sd <= 0:
            raise ValueError('Timing location/scale settings must be positive')
        if min(self.agency_scale, self.task_scale, self.step_scale, self.source_bias_sd, self.outcome_logit_sd) < 0:
            raise ValueError('Scale settings must be nonnegative')
        if not 0 < self.outlier_probability < 1 or self.channel not in {'elapsed', 'payer_work', 'agency_work'}:
            raise ValueError('Invalid contamination probability or measurement channel')


def norm(value):
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def agency_registry(evidences):
    """Unify explicit, distinctive aliases within a jurisdiction, never generic staff.

    The registry is conditional on interpretation. It does not infer that a parent
    department and every division are interchangeable organizations.
    """
    entries = []
    generic = {"staff", "city", "county", "local authority", "agency", "department",
               "cashier", "city staff", "county staff", "officials", "the city", "they",
               "legalizing agency", "local agency", "permitting agency", "licensing authority", "section"}
    for e in evidences:
        for a in e['actors']:
            if a['role'] == 'agency':
                aliases = {norm(s) for s in [a['name'], *a['aliases']]}
                aliases = {s for s in aliases if s and s not in generic and not s.startswith('city of ')}
                entries.append((e['program_id'], a['id'], norm(a['name']), aliases))
    parent = list(range(len(entries)))
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i, a in enumerate(entries):
        for j, b in enumerate(entries[:i]):
            if a[0] != b[0] and a[0].split('__')[0] == b[0].split('__')[0] and a[3] & b[3]:
                parent[root(i)] = root(j)
    names = {}
    for i, e in enumerate(entries):
        r = root(i)
        if r not in names or len(e[2]) > len(names[r]):
            names[r] = e[2]
    # Distinct union-find roots can still have the same generic display name.
    # Using that name as the identifier would accidentally pool them anyway.
    roots_by_name, anchors = {}, {}
    for i,e in enumerate(entries):
        r = root(i)
        key = f"{e[0].split('__')[0]}:{names[r]}"
        roots_by_name.setdefault(key,set()).add(r)
        anchors[r] = min(anchors.get(r,(e[0],e[1])),(e[0],e[1]))
    registry = {}
    for i,e in enumerate(entries):
        r = root(i)
        key = f"{e[0].split('__')[0]}:{names[r]}"
        if len(roots_by_name[key]) > 1:
            key += ':program_local:' + ':'.join(anchors[r])
        registry[(e[0],e[1])] = key
    return registry


def log_interval(lower, upper, location, scale, df=4.):
    """Log Student-t interval probability, stable in either tail (log units)."""
    lo = (lower - location) / scale
    hi = (upper - location) / scale
    # Evaluate survival probabilities in the positive tail to avoid cancellation.
    prob = np.where(lo > 0, stdtr(df, -lo) - stdtr(df, -hi),
                    stdtr(df, hi) - stdtr(df, lo))
    return np.log(np.maximum(prob, 1e-300))


def timing_interval(m):
    """Rounded reports are intervals; legal targets never call this function."""
    factor = {"calendar_days": 1., "business_days": 1., "weeks": 7.,
              "months": 365.25 / 12, "hours": 1 / 24 if m["metric"] == "elapsed" else 1.}[m["unit"]]
    if m["lower"] is not None or m["upper"] is not None:
        lo = 0. if m["lower"] is None else m["lower"] * factor
        hi = float("inf") if m["upper"] is None else m["upper"] * factor
    elif m["value"] is not None:
        value = m["value"] * factor
        # Numerical precision of a report is not certainty about the true duration.
        half = min(.5 * factor, max(.05, value * .05))
        lo, hi = max(0., value - half), value + half
    else:
        return None
    if m["unit"] == "business_days":
        # Unknown start weekday: envelope over a five-day week, no holidays.
        # Retain, do not equate to calendar days or silently discard.
        hi = hi + 2 * math.ceil(hi / 5) if math.isfinite(hi) else hi
    if hi <= lo:
        hi = lo + .1
    return math.log(max(lo, 1e-8)), math.log(max(hi, 1e-8))


class Layout:
    def __init__(self):
        self.size = 0
        self.slices = {}

    def add(self, name, count):
        indices = np.arange(self.size, self.size + count)
        self.size += count
        self.slices[name] = indices
        return indices


def topological_order(n, edges, rank=None):
    done, order = set(), []
    parents = [set(i for i, j in edges if j == k) for k in range(n)]
    rank = list(range(n)) if rank is None else rank
    for _ in range(n):
        ready = [i for i in range(n) if i not in done and parents[i] <= done]
        if not ready:
            raise ValueError("Contradictory precedence cycle in reconciled evidence")
        nxt = min(ready, key=lambda i: (rank[i], i))
        done.add(nxt)
        order.append(nxt)
    return order


def reachable(n, edges):
    reach = np.zeros((n, n), dtype=bool)
    for i, j in edges:
        reach[i, j] = True
    for k in range(n):
        reach |= reach[:, k, None] & reach[None, k, :]
    return reach


class Process:
    def __init__(self, evidence, cfg):
        self.id = evidence["program_id"]
        self.evidence = evidence
        self.activities = [a for a in evidence["activities"] if a["scope"] != "out_of_scope"]
        self.n = len(self.activities)
        self.index = {a["id"]: i for i, a in enumerate(self.activities)}
        self.actor = {a["id"]: a for a in evidence["actors"]}
        self.decisions = [i for i, a in enumerate(self.activities) if a["stage"] == "decision" and a['task_type'] == 'decision']
        if not self.decisions:
            raise ValueError(f"{self.id}: no identified terminal decision operation")
        self.decision = self.decisions[0]  # compatibility; case clock uses selected outcome
        self.outcome_dimension = int(len(self.decisions) > 1)
        # Exchangeable logistic-normal proportions. For two outcomes the logit
        # has the stated SD; uncertainty is not a fixed population 50/50 split.
        self.outcome_basis = helmert(len(self.decisions)).T / math.sqrt(2.) if self.outcome_dimension else np.zeros((1,0))
        self.pre = np.array([a["stage"] in {"preparation", "submission", "intake", "review", "decision", "unknown"}
                             and a["scope"] in {"core", "conditional"} for a in self.activities])
        self.pre[self.decision] = True
        for i, a in enumerate(self.activities):
            if a['stage'] == 'decision' and i not in self.decisions:
                self.pre[i] = False  # Decision-phase notices are not prerequisites of deciding.
        self.prepare = np.array([a["stage"] in {"preparation", "submission"}
                                 and a['task_type'] in {'preparation', 'filing'} for a in self.activities])
        # The completed-case clock cannot silently include withdrawal, correction,
        # or another conditional closeout route. Those require a route likelihood.
        self.closeout = np.array([a['stage'] == 'closeout' and a['scope'] == 'core'
                                  for a in self.activities])
        role = {'payer_work': 'payer', 'agency_work': 'agency'}.get(cfg.channel)
        self.channel_mask = np.array([role is None or self.actor[a['actor_id']]['role'] == role
                                      for a in self.activities])
        self.gate_keys = []
        self.gates = []
        for a in self.activities:
            condition = norm(a["condition"] or a["id"])
            if re.search(r"\b(food|health)\b", condition):
                condition = "food"
            if a["scope"] == "conditional" and self.pre[self.index[a["id"]]] and self.index[a['id']] not in self.decisions:
                if condition not in self.gate_keys:
                    self.gate_keys.append(condition)
                self.gates.append(self.gate_keys.index(condition))
            else:
                self.gates.append(-1)
        self.gates = np.array(self.gates)
        self.graphs, self.graph_notes = self._graphs(cfg)
        self.contexts = {c['measurement_id']: c for c in evidence.get('observation_contexts', [])}
        historical_cases = {m['case_id'] for m in evidence['measurements'] if m['case_id'] is not None
            and m['scope'] == 'process' and self.contexts.get(m['id'], {}).get('temporal_scope') == 'historical'}
        for m in evidence['measurements']:
            if m['case_id'] in historical_cases and self.contexts.get(m['id'], {}).get('temporal_scope') == 'current':
                raise ValueError(f"{self.id}/{m['case_id']}: contradictory historical/current case contexts")
        self.measurements = []
        self.excluded = []
        seen = set()
        for m in evidence["measurements"]:
            context = self.contexts.get(m['id'], {})
            period = 'historical' if m['case_id'] in historical_cases else context.get('temporal_scope')
            if period in {'historical', 'hypothetical'}:
                self.excluded.append({'id': m['id'], 'reason':
                    'explicitly ' + period + '; not an observation of the current static process'})
                continue
            if m["metric"] != cfg.channel or m["statistic"] in {"statutory_cap", "target"} or m["scope"] == "standing":
                self.excluded.append({"id": m["id"], "reason": "different metric or normative/standing (retained separately)"})
                continue
            if not cfg.use_process_claims and m["scope"] != "step":
                self.excluded.append({"id": m["id"], "reason": "prespecified step-only ablation"})
                continue
            interval = timing_interval(m)
            if interval is None:
                self.excluded.append({"id": m["id"], "reason": "no interpretable numerical interval"})
                continue
            if any(a not in self.index for a in m["activity_ids"]):
                self.excluded.append({"id": m["id"], "reason": "out-of-scope activity"})
                continue
            route = self.route_context(context)
            clock_after = tuple(sorted(self.index[a] for a in context.get('clock_start_after_activity_ids', []) if a in self.index))
            segment_mode = context.get('segment_mode', 'performed_operations')
            if m['scope'] == 'segment' and segment_mode == 'not_segment':
                raise ValueError(f"{self.id}/{m['id']}: realized segment requires an explicit segment mode")
            if m['scope'] == 'segment' and not context and sum(self.index[a] in self.decisions for a in m['activity_ids']) > 1:
                segment_mode = 'branch_union'
            if m['scope'] == 'segment' and segment_mode == 'branch_union' and any(not self.pre[self.index[a]] for a in m['activity_ids']):
                self.excluded.append({'id': m['id'], 'reason': 'post-initial alternative-route segment requires a separate route model'})
                continue
            if m['scope'] in {'step', 'segment'} and segment_mode != 'branch_union' and set(m['activity_ids']) & set(context.get('excluded_activity_ids', [])):
                raise ValueError(f"{self.id}/{m['id']}: performed operation excluded by its own context")
            key = (m["source_family"], m["case_id"], m["metric"], m["scope"],
                   tuple(m["activity_ids"]), m["start"], m["end"], m["statistic"], interval, route, segment_mode, clock_after)
            if key in seen:
                self.excluded.append({"id": m["id"], "reason": "duplicate within known source/case"})
                continue
            seen.add(key)
            self.measurements.append({**m, "interval": interval,
                "indices": [self.index[a] for a in m["activity_ids"]],
                'route_context': route, 'segment_mode': segment_mode, 'clock_after': clock_after})
        # Explicit work on an operation with a differently named owner is retained
        # but must not be attributed to that owner (e.g. staff handling a filing).
        for m in self.measurements:
            if m['scope'] in {'step', 'segment'}:
                self.channel_mask[m['indices']] = True
        self.cases = sorted({m["case_id"] for m in self.measurements if m["case_id"] is not None})
        self.case_index = {c: i for i, c in enumerate(self.cases)}
        self.case_use = np.zeros((len(self.cases), self.n + cfg.max_unseen), dtype=bool)
        self.active = np.zeros(self.n + cfg.max_unseen, dtype=bool)
        for m in self.measurements:
            used = np.zeros(self.n + cfg.max_unseen, dtype=bool)
            if m['scope'] == 'step' or (m['scope'] == 'segment' and m['indices']):
                used[m['indices']] = True
            else:
                used[:self.n] = self.pre & self.channel_mask
                used[self.n:] = True
                if m['end'] == 'closeout':
                    for i, a in enumerate(self.activities):
                        if self.closeout[i] and self.channel_mask[i]:
                            used[i] = True
            self.active |= used
            if m['case_id'] is not None:
                self.case_use[self.case_index[m['case_id']]] |= used
        # A directly measured conditional step proves that this case visited it.
        self.known_gates = np.full((len(self.cases), len(self.gate_keys)), -1)
        self.known_decisions = np.full(len(self.cases), -1, dtype=int)
        self.case_required = [set() for _ in self.cases]
        self.case_excluded = [set() for _ in self.cases]
        # Case facts cross measurement channels even though their numerical
        # likelihoods do not: an elapsed report's known denial also conditions a
        # same-case staff-hours report. Do not convert days into labor evidence.
        for raw in evidence['measurements']:
            if raw['case_id'] not in self.case_index:
                continue
            context = self.contexts.get(raw['id'], {})
            if context.get('temporal_scope') in {'historical', 'hypothetical'}:
                continue
            required, excluded, decision = self.route_context(context)
            ci = self.case_index[raw['case_id']]
            self.case_required[ci].update(required)
            self.case_excluded[ci].update(excluded)
            if decision >= 0:
                self.case_required[ci].add(decision)
        for m in self.measurements:
            if m["case_id"] is None:
                continue
            c = self.case_index[m["case_id"]]
            required, excluded, decision = m['route_context']
            self.case_required[c].update(required)
            self.case_excluded[c].update(excluded)
            if m['scope'] == 'step' or (m['scope'] == 'segment' and m['segment_mode'] == 'performed_operations'):
                self.case_required[c].update(m['indices'])
            if decision >= 0:
                self.case_required[c].add(decision)
            cohort = norm(m["cohort"] or "")
            if "food" in self.gate_keys and cohort:
                g = self.gate_keys.index("food")
                if any(word in cohort for word in ("non food", "nonfood", "merchandise")):
                    self.case_excluded[c].update(np.flatnonzero(self.gates == g))
                elif "food" in cohort:
                    self.case_required[c].update(np.flatnonzero(self.gates == g))
        for c, (required, excluded) in enumerate(zip(self.case_required, self.case_excluded)):
            if required & excluded:
                raise ValueError(f'{self.id}/{self.cases[c]}: contradictory same-case route contexts')
            if set(self.decisions) <= excluded:
                raise ValueError(f'{self.id}/{self.cases[c]}: all terminal outcomes excluded; abandonment is not fitted')
            outcomes = required & set(self.decisions)
            if len(outcomes) > 1:
                raise ValueError(f'{self.id}/{self.cases[c]}: mutually exclusive observed decisions')
            if outcomes:
                self.known_decisions[c] = outcomes.pop()
            for a, value in [(a, 1) for a in required] + [(a, 0) for a in excluded]:
                g = self.gates[a]
                if g >= 0:
                    if self.known_gates[c, g] not in {-1, value}:
                        raise ValueError(f'{self.id}/{self.cases[c]}: contradictory shared gate constraints')
                    self.known_gates[c, g] = value
        power = int(math.ceil(math.log2(max(16, cfg.population_size))))
        dim = self.n + cfg.max_unseen + len(self.gate_keys) + 2
        salt = int(hashlib.sha256(self.id.encode()).hexdigest()[:8], 16)
        self.quad = qmc.Sobol(dim, scramble=True, seed=cfg.population_seed ^ salt).random_base2(power)
        self.quad = np.clip(self.quad, 1e-9, 1 - 1e-9)
        self.quad_z = ndtri(self.quad)

    def route_context(self, context):
        """Immutable route conditioning, never an estimate of population frequency."""
        required = tuple(sorted(self.index[a] for a in context.get('required_activity_ids', []) if a in self.index))
        excluded = tuple(sorted(self.index[a] for a in context.get('excluded_activity_ids', []) if a in self.index))
        decision = self.index.get(context.get('decision_activity_id'), -1)
        req_gates = {self.gates[i] for i in required if self.gates[i] >= 0}
        ex_gates = {self.gates[i] for i in excluded if self.gates[i] >= 0}
        if req_gates & ex_gates or (decision >= 0 and decision in excluded):
            raise ValueError(f'{self.id}: contradictory observation route context')
        if set(self.decisions) <= set(excluded):
            raise ValueError(f'{self.id}: all terminal outcomes excluded; abandonment is not fitted')
        outcomes = set(required) & set(self.decisions)
        if decision >= 0:
            outcomes.add(decision)
        if len(outcomes) > 1:
            raise ValueError(f'{self.id}: mutually exclusive observation outcomes')
        if outcomes:
            decision = outcomes.pop()
        return required, excluded, decision

    def segment_mask(self, mask, measurement):
        """A measured executed segment exists even off the initial permit route."""
        segment = np.zeros_like(mask)
        ids = measurement['indices']
        segment[:, ids] = mask[:, ids] if measurement['segment_mode'] == 'branch_union' else True
        if measurement['segment_mode'] == 'performed_operations' and len(set(ids) & set(self.decisions)) > 1:
            raise ValueError(f"{self.id}/{measurement['id']}: executed segment lists mutually exclusive decisions")
        return segment

    def segment_values(self, durations, mask, measurement, graph):
        segment = self.segment_mask(mask, measurement)
        ends = self.scheduled(durations, segment, graph)
        values = ends[:, measurement['indices']].max(axis=1)
        if measurement['clock_after']:
            values = np.maximum(1e-8, values - ends[:, list(measurement['clock_after'])].max(axis=1))
        return values

    def outcome_probabilities(self, z, cfg, excluded=()):
        logits = cfg.outcome_logit_sd * (self.outcome_basis @ z[self.zo])
        if not np.all(np.isfinite(logits)):
            raise FloatingPointError('numerically extreme outcome proposal')
        for k, decision in enumerate(self.decisions):
            if decision in excluded:
                logits[k] = -np.inf
        if np.all(np.isneginf(logits)):
            raise ValueError('all terminal outcomes excluded')
        return softmax(logits)

    def _graphs(self, cfg):
        edges, soft, parallel = set(), set(), set()
        for r in self.evidence["relations"]:
            if r["source"] not in self.index or r["target"] not in self.index:
                continue
            i, j = self.index[r["source"]], self.index[r["target"]]
            if r["kind"] == "precedes":
                (edges if r["support"] == "explicit" else soft).add((i, j))
            elif r["kind"] == "parallel":
                parallel.add(frozenset((i, j)))
        # Endpoint definition: every on-route pre-decision operation finishes
        # before the decision. This is not an evidential claim about its ordering
        # relative to another prerequisite. Inactive conditional steps take zero.
        closure_edges = {(i, d) for i in range(self.n) for d in self.decisions if self.pre[i] and i not in self.decisions}
        edges |= closure_edges
        topological_order(self.n, edges)
        required_reach = reachable(self.n, edges)
        if any(required_reach[a,b] or required_reach[b,a] for pair in parallel for a,b in [tuple(pair)]):
            raise ValueError('Reconciled parallel relation contradicts required precedence')
        stage_rank = {s: i for i, s in enumerate(("preparation", "submission", "intake", "review",
                                                 "unknown", "decision", "closeout", "enforcement", "appeal", "standing"))}
        base_rank = [stage_rank[a["stage"]] for a in self.activities]
        rng = np.random.default_rng(9721)
        graphs, signatures = [], set()
        for k in range(cfg.graph_variants):
            candidate = set(edges)
            for i, j in sorted(soft):
                if (k == 0 or (k > 1 and rng.random() < .5)) and not reachable(self.n, candidate)[j, i]:
                    proposed = candidate | {(i, j)}
                    reach = reachable(self.n, proposed)
                    if not any(reach[a,b] or reach[b,a] for pair in parallel for a,b in [tuple(pair)]):
                        candidate = proposed
            order = topological_order(self.n, candidate, np.array(base_rank) + rng.uniform(0, .9, self.n))
            # Candidate 0 completes unknown comparisons serially; candidate 1
            # allows overlap; intermediate candidates sample missing comparisons.
            # No unsupported root-decision shortcut survives either candidate.
            for pos, i in enumerate(order):
                for j in order[pos + 1:]:
                    if not (self.pre[i] and self.pre[j]) or frozenset((i, j)) in parallel or (i in self.decisions and j in self.decisions):
                        continue
                    if (k == 0 or (k > 1 and rng.random() < .5)) and not reachable(self.n, candidate)[i, j]:
                        # Never introduce indirect serialization of an explicitly parallel pair.
                        proposed = candidate | {(i, j)}
                        reach = reachable(self.n, proposed)
                        if not any(reach[a, b] or reach[b, a] for pair in parallel for a, b in [tuple(pair)]):
                            candidate = proposed
            signature = tuple(sorted(candidate))
            if signature not in signatures:
                signatures.add(signature)
                # Transitive parents do not change a nonnegative-duration DAG
                # schedule. Keep original edges for provenance; reduce only the
                # numerical max operations (especially dense completion graphs).
                reach = reachable(self.n, candidate)
                parents = [[i for i, j in sorted(candidate) if j == target] for target in range(self.n)]
                parents = [[i for i in pp if not any(reach[i, j] for j in pp if j != i)] for pp in parents]
                order = topological_order(self.n, candidate)
                graphs.append({"edges": candidate, "order": order, "parents": parents,
                    'order_array': np.array(order, dtype=np.int64),
                    'parent_ptr': np.concatenate(([0], np.cumsum([len(pp) for pp in parents]))).astype(np.int64),
                    'parent_index': np.array([i for pp in parents for i in pp], dtype=np.int64)})
        return graphs, {"endpoint_closure": sorted(closure_edges - {
            (self.index[r['source']], self.index[r['target']]) for r in self.evidence['relations']
            if r['kind'] == 'precedes' and r['source'] in self.index and r['target'] in self.index}),
            "candidate_count": len(graphs), "missing_order": "finite completion uncertainty, not automatic independence"}

    def scheduled(self, durations, mask, graph):
        g = self.graphs[graph]
        if schedule_native is not None:
            return schedule_native(durations[:, :self.n], mask, g['order_array'], g['parent_ptr'], g['parent_index'])
        return self.scheduled_numpy(durations, mask, graph)

    def scheduled_numpy(self, durations, mask, graph):
        durations = durations[:, :self.n] * mask
        ends = np.zeros_like(durations)
        g = self.graphs[graph]
        for i in g["order"]:
            parents = g["parents"][i]
            begin = (ends[:, parents[0]] if len(parents) == 1 else
                     ends[:, parents].max(axis=1) if parents else 0.)
            # A skipped gate is a zero-duration pass-through, not deletion of
            # its upstream dependencies (which would create an accidental root).
            ends[:, i] = begin + durations[:, i]
        return ends

    def decision_time(self, ends, mask):
        return (ends[:, self.decisions] * mask[:, self.decisions]).max(axis=1)

    def start_offset(self, ends, start):
        ids = [i for i, a in enumerate(self.activities) if self.prepare[i]]
        if start == 'complete_application':
            ids += [i for i, a in enumerate(self.activities) if a['task_type'] == 'completeness' and self.pre[i]]
        return ends[:, ids].max(axis=1) if ids else np.zeros(len(ends))


class HierarchicalModel:
    def __init__(self, evidences, cfg=None):
        self.cfg = cfg or Config()
        self.processes = [Process(validate(e), self.cfg) for e in evidences]
        self.layout = Layout()
        registry = agency_registry(evidences)
        self.activities, self.agency_names, self.task_names, self.sources = [], [], [], []
        self.agencies, self.tasks, self.program_index = [], [], []
        for pi, p in enumerate(self.processes):
            p.global_indices = []
            jur = p.id.split("__")[0]
            for a in p.activities:
                p.global_indices.append(len(self.activities))
                self.activities.append((p.id, a))
                actor = p.actor[a["actor_id"]]
                agency = (registry[(p.id, a['actor_id'])] if actor["role"] == "agency"
                          else f"role:{actor['role']}")
                for value, names, dest in ((agency, self.agency_names, self.agencies),
                                            (a["task_type"], self.task_names, self.tasks)):
                    if value not in names:
                        names.append(value)
                    dest.append(names.index(value))
                self.program_index.append(pi)
            for m in p.measurements:
                if m["source_family"] not in self.sources:
                    self.sources.append(m["source_family"])
                m["source_index"] = self.sources.index(m["source_family"])
        self.agencies, self.tasks = np.array(self.agencies), np.array(self.tasks)
        self.program_index = np.array(self.program_index)
        L = self.layout
        self.hyper = L.add("hyper", 6)  # location, agency/task/step SD, case SD, common-case SD
        self.za = L.add("agency", len(self.agency_names))
        self.zt = L.add("task", len(self.task_names))
        self.zp = L.add("program", len(self.processes)) if len(self.processes) > 1 else np.array([], dtype=int)
        self.zi = L.add("step", len(self.activities))
        self.zs = L.add("source", len(self.sources))
        # Do not trap a weakly identified scale in a joint block with a tightly
        # measured location: that throttles its slice angle and ruins mixing.
        self.blocks = [np.array([h]) for h in self.hyper] + [self.za, self.zt, self.zp, self.zi, self.zs]
        for p in self.processes:
            p.zg = L.add(f"{p.id}:gate_prevalence", len(p.gate_keys))
            p.zo = L.add(f'{p.id}:outcome_prevalence', len(p.decisions)-1)
            p.zh = L.add(f"{p.id}:hidden_step", self.cfg.max_unseen)
            p.zcase = L.add(f"{p.id}:cases", len(p.cases) * (p.n + self.cfg.max_unseen + 1 + len(p.gate_keys) + p.outcome_dimension))
            p.case_shape = (len(p.cases), p.n + self.cfg.max_unseen + 1 + len(p.gate_keys) + p.outcome_dimension)
            self.blocks += [p.zg, p.zo, p.zh]
            self.blocks += list(p.zcase.reshape(p.case_shape))
        self.blocks = [b for b in self.blocks if len(b)]
        self.observations = [(p.id, m) for p in self.processes for m in p.measurements]
        offset = 0
        for p in self.processes:
            p.prediction_groups = {}
            for j, m in enumerate(p.measurements):
                population = m['case_id'] is None
                group_key = (population, m['route_context'] if population else ((), (), -1))
                p.prediction_groups.setdefault(group_key, []).append((offset + j, m))
            p.prediction_cache = {}
            offset += len(p.measurements)
        self.bounds = np.array([m["interval"] for _, m in self.observations])
        self.active_steps = np.concatenate([np.array(p.global_indices)[p.active[:p.n]] for p in self.processes]).astype(int)
        self.active_agencies = np.unique(self.agencies[self.active_steps])
        self.active_tasks = np.unique(self.tasks[self.active_steps])

    def parameters(self, z):
        c = self.cfg
        h = z[self.hyper]
        location = math.log(c.global_median) + c.global_log_sd * h[0]
        sa, st, si = abs(h[1]) * c.agency_scale, abs(h[2]) * c.task_scale, abs(h[3]) * c.step_scale
        sigma, common = .10 + .75 * abs(h[4]), .35 * abs(h[5])
        agency = sa * z[self.za] if c.use_hierarchy else np.zeros(len(self.za))
        task = st * z[self.zt] if c.use_hierarchy else np.zeros(len(self.zt))
        program = .5 * z[self.zp] if len(self.zp) else np.zeros(len(self.processes))
        mu = location + agency[self.agencies] + task[self.tasks] + si * z[self.zi] + program[self.program_index]
        return {"mu": mu, "sigma": sigma, "common": common, "location": location,
                "agency": agency, "task": task, "program": program, "step_sd": si,
                "agency_sd": sa, "task_sd": st, "source_bias": c.source_bias_sd * z[self.zs]}

    def process_state(self, p, z, params, structure, population=False, context=((), (), -1)):
        c = self.cfg
        mu = params["mu"][p.global_indices]
        hidden_mu = params["location"] + params["step_sd"] * z[p.zh]
        mu = np.concatenate((mu, hidden_mu))
        if population:
            noise = p.quad_z[:, :len(mu)]
            common_noise = p.quad_z[:, len(mu)]
            uniforms = p.quad[:, len(mu) + 1:len(mu) + 1 + len(p.gate_keys)]
        else:
            zz = z[p.zcase].reshape(p.case_shape)
            noise, common_noise = zz[:, :len(mu)], zz[:, len(mu)]
            uniforms = ndtr(zz[:, len(mu) + 1:len(mu) + 1 + len(p.gate_keys)])
        logdur = mu[None, :] + params["sigma"] * noise + params["common"] * common_noise[:, None]
        # Reject extreme proposals in likelihood, never silently clamp a duration.
        if not np.all(np.isfinite(logdur)) or np.any(np.abs(logdur) > 650):
            raise FloatingPointError("numerically extreme duration proposal")
        durations = np.exp(logdur)
        gate_p = expit(1.5 * z[p.zg])
        visited = uniforms < gate_p[None, :]
        if not population:
            visited = np.where(p.known_gates >= 0, p.known_gates, visited)
        else:
            for ids, value in ((context[0], True), (context[1], False)):
                for i in ids:
                    if p.gates[i] >= 0:
                        visited[:, p.gates[i]] = value
        mask = np.tile(p.pre, (len(durations), 1))
        for i, g in enumerate(p.gates):
            if g >= 0:
                mask[:, i] &= visited[:, g].astype(bool)
        if p.outcome_dimension:
            column = len(mu) + 1 + len(p.gate_keys)
            u = p.quad[:, column] if population else ndtr(zz[:, column])
            u = np.clip(u, np.nextafter(0.,1.), np.nextafter(1.,0.))
            probs = p.outcome_probabilities(z, c, context[1] if population else ())
            chosen = np.minimum(np.searchsorted(np.cumsum(probs), u, side='right'), len(p.decisions) - 1)
            if population and context[2] >= 0:
                chosen[:] = p.decisions.index(context[2])
            elif not population:
                for ci, decision in enumerate(p.known_decisions):
                    if decision >= 0:
                        chosen[ci] = p.decisions.index(decision)
                    elif p.case_excluded[ci] & set(p.decisions):
                        conditional = p.outcome_probabilities(z, c, p.case_excluded[ci])
                        chosen[ci] = min(np.searchsorted(np.cumsum(conditional), u[ci], side='right'), len(p.decisions)-1)
            mask[:, p.decisions] = False
            mask[np.arange(len(mask)), np.array(p.decisions)[chosen]] = True
        if population:
            required = [i for i in context[0] if p.pre[i]]
            mask[:, required] = True
            mask[:, list(context[1])] = False
        for row, (required, excluded) in enumerate(zip(p.case_required, p.case_excluded) if not population else []):
            # Non-initial segments have their own mask; they do not become
            # prerequisites of the first permit merely because they were observed.
            for i in required:
                if p.pre[i]:
                    mask[row, i] = True
            for i in excluded:
                mask[row, i] = False
        # Standing and post-decision tasks have separate durations/inventory;
        # they never become prerequisites of the first decision.
        ends = p.scheduled(durations, mask, structure[0])
        hidden = durations[:, p.n:p.n + structure[1]].sum(axis=1)
        return durations, mask, ends, hidden, gate_p

    def predictions(self, z, structures, include_alternatives=False):
        """Cache only mathematically unchanged process/mode computations.

        Case blocks affect one process's cases, not population quadrature or
        another process; source blocks affect no latent duration. Keys contain
        every transformed parent. A slow reference implementation is retained
        below and regression-tested against this path, including cache changes.
        """
        params = self.parameters(z)
        pred, scales, alt = (np.empty(len(self.observations)) for _ in range(3))
        for p, structure in zip(self.processes, structures):
            base = (params['mu'][p.global_indices].tobytes(),
                    (params['location'] + params['step_sd'] * z[p.zh]).tobytes(),
                    params['sigma'], params['common'], z[p.zg].tobytes(), tuple(structure))
            base += (z[p.zo].tobytes(),)
            for group_key, group in p.prediction_groups.items():
                population, context = group_key
                key = base + (None if population else z[p.zcase].tobytes(),)
                cached = p.prediction_cache.get(group_key)
                if cached is None or cached[0] != key:
                    dur, mask, ends, hidden, _ = self.process_state(p, z, params, structure, population, context)
                    values_cache, summaries_cache, entries = {}, {}, []
                    for slot, m in group:
                        footprint = (m['scope'], tuple(m['indices']), m['start'], m['end'], m['segment_mode'], m['clock_after'])
                        if footprint not in values_cache:
                            if m['scope'] == 'step':
                                values = dur[:, m['indices'][0]]
                            elif self.cfg.channel != 'elapsed':
                                selected = m['indices'] if m['scope'] == 'segment' and m['indices'] else range(p.n)
                                work_mask = (p.segment_mask(mask, m) if m['scope'] == 'segment' and m['indices'] else mask) & p.channel_mask
                                if m['end'] == 'closeout':
                                    work_mask |= p.closeout & p.channel_mask
                                values = (dur[:, :p.n] * work_mask)[:, selected].sum(axis=1)
                            elif m['scope'] == 'segment' and m['indices']:
                                values = p.segment_values(dur, mask, m, structure[0])
                            else:
                                values = p.decision_time(ends, mask) + hidden
                                if m['end'] == 'closeout':
                                    values = values + dur[:, :p.n][:, p.closeout].sum(axis=1)
                                if m['start'] in {'submission', 'complete_application'}:
                                    values = np.maximum(1e-8, values - p.start_offset(ends, m['start']))
                            other = values
                            if m['scope'] == 'process' and m['start'] == 'unspecified' and self.cfg.channel == 'elapsed':
                                other = np.maximum(1e-8, values - p.start_offset(ends, 'submission'))
                            values_cache[footprint] = values, other
                        values, other = values_cache[footprint]
                        if population:
                            kind = footprint + (m['statistic'], m['qualitative'], m['n'])
                            if kind not in summaries_cache:
                                stat = m['statistic']
                                if stat == 'mean':
                                    value, alternate = np.mean(values), np.mean(other)
                                elif stat == 'p90':
                                    value, alternate = np.quantile(values, .9), np.quantile(other, .9)
                                else:
                                    value, alternate = np.median(values), np.median(other)
                                reporting = .65 if m['qualitative'] else (.5 if m['n'] is None else self.cfg.report_sd)
                                if m['n'] is not None:
                                    sampling = float(np.var(np.log(np.maximum(values, 1e-8)))) / m['n']
                                    if stat in {'median', 'typical', 'estimate'}:
                                        sampling *= math.pi / 2
                                    elif stat == 'p90':
                                        density = math.exp(-.5 * ndtri(.9) ** 2) / math.sqrt(2 * math.pi)
                                        sampling *= .9 * .1 / density ** 2
                                    elif stat == 'mean':
                                        sampling = float(np.var(values) / max(np.mean(values) ** 2, 1e-16)) / m['n']
                                    reporting = math.sqrt(reporting ** 2 + sampling)
                                summaries_cache[kind] = value, alternate, reporting
                            value, alternate, reporting = summaries_cache[kind]
                        else:
                            ci = p.case_index[m['case_id']]
                            value, alternate, reporting = values[ci], other[ci], self.cfg.report_sd
                        entries.append((slot, math.log(max(float(value), 1e-8)),
                                        math.log(max(float(alternate), 1e-8)), reporting, m['source_index']))
                    cached = key, entries
                    p.prediction_cache[group_key] = cached
                for slot, value, alternate, reporting, source in cached[1]:
                    bias = params['source_bias'][source]
                    pred[slot], alt[slot], scales[slot] = value + bias, alternate + bias, reporting
        return (pred, scales, alt) if include_alternatives else (pred, scales)

    def predictions_reference(self, z, structures, include_alternatives=False):
        params = self.parameters(z)
        predictions, scales, alternatives = [], [], []
        for p, structure in zip(self.processes, structures):
            states = {}
            for m in p.measurements:
                population = m["case_id"] is None
                context = m['route_context'] if population else ((), (), -1)
                state_key = population, context
                if state_key not in states:
                    states[state_key] = self.process_state(p, z, params, structure, population, context)
                dur, mask, ends, hidden, _ = states[state_key]
                if m["scope"] == "step":
                    values = dur[:, m["indices"][0]]
                elif self.cfg.channel != 'elapsed':
                    # Work is additive, even where elapsed time overlaps.
                    selected = m['indices'] if m['scope'] == 'segment' and m['indices'] else range(p.n)
                    work_mask = (p.segment_mask(mask, m) if m['scope'] == 'segment' and m['indices'] else mask) & p.channel_mask
                    if m['end'] == 'closeout':
                        work_mask |= p.closeout & p.channel_mask
                    values = (dur[:, :p.n] * work_mask)[:, selected].sum(axis=1)
                elif m["scope"] == "segment" and m["indices"]:
                    # Elapsed segment span follows its induced schedule, not a
                    # sum that double-counts parallel branches or a free parameter.
                    values = p.segment_values(dur, mask, m, structure[0])
                else:
                    values = p.decision_time(ends, mask) + hidden
                    if m["end"] == "closeout":
                        values = values + dur[:, :p.n][:, p.closeout].sum(axis=1)
                    if m["start"] in {"submission", "complete_application"}:
                        # A combined preparation/filing activity ends at submission.
                        values = np.maximum(1e-8, values - p.start_offset(ends, m['start']))
                alternate = values
                if m['scope'] == 'process' and m['start'] == 'unspecified' and self.cfg.channel == 'elapsed':
                    alternate = np.maximum(1e-8, values - p.start_offset(ends, 'submission'))
                if population:
                    stat = m["statistic"]
                    if stat == "mean":
                        value = float(np.mean(values))
                        alternate_value = float(np.mean(alternate))
                    elif stat == "p90":
                        value = float(np.quantile(values, .9))
                        alternate_value = float(np.quantile(alternate, .9))
                    else:
                        value = float(np.median(values))
                        alternate_value = float(np.median(alternate))
                    reporting = .65 if m["qualitative"] else (.5 if m["n"] is None else self.cfg.report_sd)
                    # Median sampling uncertainty. Unknown n is not infinite n.
                    if m["n"] is not None:
                        logs = np.log(np.maximum(values, 1e-8))
                        sampling = float(np.var(logs)) / m["n"]
                        if stat in {"median", "typical", "estimate"}:
                            sampling *= math.pi / 2
                        elif stat == 'p90':
                            density = math.exp(-.5 * ndtri(.9) ** 2) / math.sqrt(2 * math.pi)
                            sampling *= .9 * .1 / density ** 2
                        elif stat == 'mean':
                            sampling = float(np.var(values) / max(np.mean(values) ** 2, 1e-16)) / m['n']
                        reporting = math.sqrt(reporting ** 2 + sampling)
                else:
                    value = values[p.case_index[m["case_id"]]]
                    alternate_value = alternate[p.case_index[m['case_id']]]
                    reporting = self.cfg.report_sd
                predictions.append(math.log(max(float(value), 1e-8)) + params["source_bias"][m["source_index"]])
                alternatives.append(math.log(max(float(alternate_value), 1e-8)) + params['source_bias'][m['source_index']])
                scales.append(reporting)
        result = np.array(predictions), np.array(scales)
        return (*result, np.array(alternatives)) if include_alternatives else result

    def log_likelihood(self, z, structures, parts=False):
        if not self.observations:
            return np.array([]) if parts else 0.
        try:
            pred, scale, alternative = self.predictions(z, structures, include_alternatives=True)
            bounds = self.bounds
            regular = log_interval(bounds[:, 0], bounds[:, 1], pred, scale)
            # Explicit contamination model for contradictory/noisy claims, not
            # a hidden likelihood weight selected to improve benchmark scores.
            unusual = log_interval(bounds[:, 0], bounds[:, 1], pred, 2.)
            eps = self.cfg.outlier_probability
            likelihood = np.logaddexp(math.log1p(-eps) + regular, math.log(eps) + unusual)
            alt_regular = log_interval(bounds[:, 0], bounds[:, 1], alternative, scale)
            alt_unusual = log_interval(bounds[:, 0], bounds[:, 1], alternative, 2.)
            alt_likelihood = np.logaddexp(math.log1p(-eps) + alt_regular, math.log(eps) + alt_unusual)
            likelihood = np.logaddexp(likelihood, alt_likelihood) - math.log(2.)
            return likelihood if parts else float(likelihood.sum())
        except (FloatingPointError, OverflowError, ValueError):
            if parts:
                raise
            return -float("inf")

    def hidden_log_prior(self, count):
        if self.cfg.unseen_mean == 0:
            return 0. if count == 0 else -float("inf")
        # Truncated geometric is a sensitivity assumption, not learned coverage.
        r = self.cfg.unseen_mean / (1 + self.cfg.unseen_mean)
        return count * math.log(r)

    def source_location_update(self, z, structures, current, rng):
        """Explore the common time-scale/source-offset ambiguity coherently.

        Adding delta to every log duration and subtracting it from every source
        offset preserves homogeneous timing summaries. Resample the projection
        onto that direction from its exact Gaussian-prior conditional. An MH
        likelihood correction covers numerical floors, without assuming exact
        invariance at pathological durations.
        """
        if not len(self.zs) or self.cfg.source_bias_sd < 1e-8:
            return z, current
        coords = np.concatenate(([self.hyper[0]], self.zs))
        direction = np.r_[1 / self.cfg.global_log_sd,
                          np.full(len(self.zs), -1 / self.cfg.source_bias_sd)]
        direction /= np.linalg.norm(direction)
        trial = z.copy()
        trial[coords] += direction * (rng.normal() - direction @ z[coords])
        value = self.log_likelihood(trial, structures)
        if math.log(rng.random()) < value - current:
            return trial, value
        return z, current

    def centered_step_update(self, z, structures, current, rng):
        """ASIS-style centered update: condition on actual latent case durations.

        Gaussian conditional proposal includes the step prior and ALL latent-case
        Normal densities. Case-report likelihood stays fixed. Only population
        summary likelihood changes, handled by the MH correction. The reverse
        proposal has the same fixed case durations, so no omitted Jacobian.
        """
        par = self.parameters(z)
        tau, sigma = par['step_sd'], par['sigma']
        if tau < 1e-7:
            return z, current
        trial = z.copy()
        for pi, p in enumerate(self.processes):
            gi = p.global_indices
            base = par['mu'][gi] - tau * z[self.zi[gi]]
            means = np.concatenate((par['mu'][gi], par['location'] + tau * z[p.zh]))
            bases = np.concatenate((base, np.full(len(p.zh), par['location'])))
            case = z[p.zcase].reshape(p.case_shape)
            # Subtract common-case effects; they are held fixed in this move.
            centered = means[None, :] + sigma * case[:, :len(means)]
            use = p.case_use
            precision = 1 / tau ** 2 + use.sum(axis=0) / sigma ** 2
            location = (bases / tau ** 2 + (centered * use).sum(axis=0) / sigma ** 2) / precision
            proposed = location + rng.normal(size=len(means)) / np.sqrt(precision)
            trial[self.zi[gi]] = (proposed[:p.n] - bases[:p.n]) / tau
            trial[p.zh] = (proposed[p.n:] - bases[p.n:]) / tau
            new_case = case.copy()
            new_case[:, :len(means)] = np.where(use, (centered - proposed[None, :]) / sigma, case[:, :len(means)])
            trial[p.zcase] = new_case.ravel()
        value = self.log_likelihood(trial, structures)
        if math.log(rng.random()) < value - current:
            return trial, value
        return z, current

    def decomposition_update(self, z, rng):
        """Exact Gaussian conditional attribution, keeping every step mean fixed."""
        par = self.parameters(z)
        tau = par['step_sd']
        if tau < 1e-7:
            return z
        h = self.hyper
        coords = [h[0]] + list(self.za) + list(self.zt) + list(self.zp)
        active = self.active_steps
        nr = len(active) + sum(np.sum(p.active[p.n:]) for p in self.processes)
        design = np.zeros((nr, len(coords)))
        design[:, 0] = self.cfg.global_log_sd
        rows = np.arange(len(active))
        if self.cfg.use_hierarchy:
            design[rows, 1 + self.agencies[active]] = par['agency_sd']
            design[rows, 1 + len(self.za) + self.tasks[active]] = par['task_sd']
        if len(self.zp):
            design[rows, 1 + len(self.za) + len(self.zt) + self.program_index[active]] = .5
        means = np.concatenate([par['mu'][active]] + [par['location'] + tau * z[p.zh[p.active[p.n:]]] for p in self.processes])
        precision = np.eye(len(coords)) + design.T @ design / tau ** 2
        chol = np.linalg.cholesky(precision)
        rhs = design.T @ (means - math.log(self.cfg.global_median)) / tau ** 2
        mean = np.linalg.solve(chol.T, np.linalg.solve(chol, rhs))
        draw = mean + np.linalg.solve(chol.T, rng.normal(size=len(coords)))
        trial = z.copy()
        trial[coords] = draw
        new_base = math.log(self.cfg.global_median) + design @ draw
        residual = (means - new_base) / tau
        trial[self.zi[active]] = residual[:len(active)]
        pos = len(active)
        for p in self.processes:
            used = p.zh[p.active[p.n:]]
            trial[used] = residual[pos:pos + len(used)]
            pos += len(used)
        return trial

    def centered_scale_update(self, z, rng):
        """Half-normal scale MH conditionals, with effects held fixed (log proposal)."""
        for hi, coords, scale in ((1, self.za[self.active_agencies], self.cfg.agency_scale),
                                  (2, self.zt[self.active_tasks], self.cfg.task_scale),
                                  (3, np.concatenate([self.zi[self.active_steps]] + [p.zh[p.active[p.n:]] for p in self.processes]), self.cfg.step_scale)):
            if not len(coords) or (hi < 3 and not self.cfg.use_hierarchy):
                continue
            current = abs(z[self.hyper[hi]]) * scale
            if current < 1e-7:
                continue
            proposed = current * math.exp(rng.normal(scale=.5))
            if proposed < 1e-7:
                continue  # symmetric domain restriction for this MH kernel
            effects = current * z[coords]
            sse = effects @ effects
            def target(t):
                # Half-normal scale prior, Normal effects, log-scale Jacobian.
                return -.5 * (t / scale) ** 2 - (len(coords) - 1) * math.log(t) - .5 * sse / t ** 2
            if math.log(rng.random()) < target(proposed) - target(current):
                z = z.copy()
                z[self.hyper[hi]] = proposed / scale * rng.choice([-1, 1])
                z[coords] = effects / proposed
        return z

    def centered_case_update(self, z, structures, current, rng):
        """Joint case shocks and spread updates, preserving actual case durations."""
        par = self.parameters(z)
        sigma, common = par['sigma'], par['common']
        z = z.copy()
        # Exact Gaussian conditional for each common case shock.
        if common > 1e-8:
            for p in self.processes:
                width = p.n + self.cfg.max_unseen
                case = z[p.zcase].reshape(p.case_shape).copy()
                resid = sigma * case[:, :width] + common * case[:, width, None]
                var = 1 / (1 / common ** 2 + p.case_use.sum(axis=1) / sigma ** 2)
                shock = var * (resid * p.case_use).sum(axis=1) / sigma ** 2 + np.sqrt(var) * rng.normal(size=len(case))
                case[:, width] = shock / common
                case[:, :width] = np.where(p.case_use, (resid - shock[:, None]) / sigma, case[:, :width])
                z[p.zcase] = case.ravel()
        for hi, prior_scale, floor in ((4, .75, .10), (5, .35, 0.)):
            old_excess = abs(z[self.hyper[hi]]) * prior_scale
            if old_excess < 1e-8:
                continue
            old = floor + old_excess
            excess = old_excess * math.exp(rng.normal(scale=.4))
            if excess < 1e-8:
                continue  # the reverse kernel also skips below this threshold
            new = floor + excess
            noise = []
            for p in self.processes:
                width = p.n + self.cfg.max_unseen
                case = z[p.zcase].reshape(p.case_shape)
                noise.extend((case[:, :width][p.case_use] if hi == 4 else case[:, width]).tolist())
            actual = old * np.array(noise)
            sse, count = actual @ actual, len(actual)
            def target(s):
                sd = s + floor
                return -.5 * (s / prior_scale) ** 2 - count * math.log(sd) - .5 * sse / sd ** 2 + math.log(s)
            trial = z.copy()
            trial[self.hyper[hi]] = excess / prior_scale * rng.choice([-1, 1])
            for p in self.processes:
                width = p.n + self.cfg.max_unseen
                case = trial[p.zcase].reshape(p.case_shape).copy()
                if hi == 4:
                    case[:, :width] = np.where(p.case_use, case[:, :width] * old / new, case[:, :width])
                else:
                    case[:, width] *= old / new
                trial[p.zcase] = case.ravel()
            value = self.log_likelihood(trial, structures)
            if math.log(rng.random()) < value - current + target(excess) - target(old_excess):
                z, current = trial, value
        return z, current

    def exchange_unmeasured_steps(self, z, structures, current, rng):
        """Involutive whole-case swaps explore indistinguishable decompositions."""
        for pi, p in enumerate(self.processes):
            observed = {i for m in p.measurements if m['scope'] == 'step' for i in m['indices']}
            eligible = [i for i in range(p.n) if i not in observed and p.pre[i]]
            eligible += list(range(p.n, p.n + structures[pi][1]))
            if len(eligible) < 2:
                continue
            i, j = rng.choice(eligible, 2, replace=False)
            par = self.parameters(z)
            tau = par['step_sd']
            if tau < 1e-7:
                continue
            coordinates = np.concatenate((self.zi[p.global_indices], p.zh))
            means = np.concatenate((par['mu'][p.global_indices], par['location'] + tau * z[p.zh]))
            ii, jj = coordinates[i], coordinates[j]
            trial = z.copy()
            # Swap actual step means, not agency labels. Jacobian magnitude one.
            delta = (means[j] - means[i]) / tau
            trial[ii] += delta
            trial[jj] -= delta
            cases = trial[p.zcase].reshape(p.case_shape).copy()
            cases[:, [i, j]] = cases[:, [j, i]]
            trial[p.zcase] = cases.ravel()
            value = self.log_likelihood(trial, structures)
            prior_ratio = -.5 * (trial @ trial - z @ z)
            if math.log(rng.random()) < value - current + prior_ratio:
                z, current = trial, value
            # Move continuously along the ambiguous sum decomposition as well
            # as exchanging its labels. In log coordinates (logsumexp(x,y),x-y)
            # has determinant -1, so translating the ratio has unit Jacobian.
            trial = self.redistribute_pair(z, p, i, j, rng.normal(scale=1.), match_case_means=bool(rng.integers(2)))
            value = self.log_likelihood(trial, structures)
            prior_ratio = -.5 * (trial @ trial - z @ z)
            if math.log(rng.random()) < value - current + prior_ratio:
                z, current = trial, value
            # A case block also contains tightly observed steps. Moving only this
            # ambiguous pair avoids letting those observations freeze its ratio.
            if len(p.cases):
                case_id = int(rng.integers(len(p.cases)))
                trial = self.redistribute_pair(z, p, i, j, rng.normal(scale=1.5), case_id=case_id)
                value = self.log_likelihood(trial, structures)
                prior_ratio = -.5 * (trial @ trial - z @ z)
                if math.log(rng.random()) < value - current + prior_ratio:
                    z, current = trial, value
        return z, current

    def redistribute_pair(self, z, p, i, j, shift, match_case_means=False, case_id=None):
        par = self.parameters(z)
        tau, sigma, common = par['step_sd'], par['sigma'], par['common']
        if tau < 1e-7:
            return z.copy()
        coordinates = np.concatenate((self.zi[p.global_indices], p.zh))
        means = np.concatenate((par['mu'][p.global_indices], par['location'] + tau * z[p.zh]))
        ii, jj = coordinates[i], coordinates[j]
        old_mu = means[[i, j]]
        def move(pair):
            total = np.logaddexp(pair[..., 0], pair[..., 1])
            ratio = pair[..., 0] - pair[..., 1] + shift
            return np.stack((total - np.logaddexp(0, -ratio), total - np.logaddexp(0, ratio)), axis=-1)
        case = z[p.zcase].reshape(p.case_shape).copy()
        width = p.n + self.cfg.max_unseen
        shock = common * case[:, width, None]
        old_logs = old_mu[None, :] + sigma * case[:, [i, j]] + shock
        new_logs = move(old_logs)
        if case_id is not None:
            new_logs = old_logs.copy()
            new_logs[case_id] = move(old_logs[case_id])
            new_mu = old_mu
        elif match_case_means and len(case):
            # In (mu, case_log_duration) coordinates this is a shear after a
            # unit-Jacobian ratio translation; the inverse uses -shift exactly.
            new_mu = old_mu + (new_logs - old_logs).mean(axis=0)
        else:
            new_mu = move(old_mu)
        trial = z.copy()
        trial[[ii, jj]] += (new_mu - old_mu) / tau
        case[:, [i, j]] = (new_logs - new_mu[None, :] - shock) / sigma
        trial[p.zcase] = case.ravel()
        return trial

    def sample(self, progress=None, initial=None):
        cfg = self.cfg
        chains, structural, likelihoods, calls = [], [], [], []
        started = time.monotonic()
        for chain in range(cfg.chains):
            rng = np.random.default_rng(cfg.seed + 104729 * chain)
            if initial is None:
                z = rng.normal(size=self.layout.size)
                structures = [(rng.integers(len(p.graphs)), 0) for p in self.processes]
            else:
                z = np.array(initial[0][chain], dtype=float, copy=True)
                structures = [tuple(pair) for pair in initial[1][chain]]
                if z.shape != (self.layout.size,):
                    raise ValueError('Checkpoint dimension differs from current model')
            f = lambda zz: self.log_likelihood(zz, structures)
            value = f(z)
            retained, graphs, lls, n_calls = [], [], [], 0
            iterations = cfg.warmup + cfg.draws * cfg.thin
            for it in range(iterations):
                for block in self.blocks:
                    z, value, used = elliptical_slice(z, block, f, value, rng)
                    n_calls += used
                z, value = self.source_location_update(z, structures, value, rng)
                z, value = self.centered_step_update(z, structures, value, rng)
                z, value = self.centered_case_update(z, structures, value, rng)
                z = self.decomposition_update(z, rng)
                z = self.centered_scale_update(z, rng)
                # Invariant updates preserve the likelihood up to roundoff.
                value = f(z)
                z, value = self.exchange_unmeasured_steps(z, structures, value, rng)
                # Exact finite conditionals, independently of Gaussian priors.
                # Update less often than each block; still leaves the joint target invariant.
                if it % 2 == 0:
                    for pi, p in enumerate(self.processes):
                        for coordinate, choices in ((0, range(len(p.graphs))),
                                                     (1, range(cfg.max_unseen + 1) if cfg.unseen_mean else range(1))):
                            vals, opts = [], []
                            for choice in choices:
                                trial = list(structures[pi])
                                trial[coordinate] = choice
                                structures[pi] = tuple(trial)
                                ll = f(z)
                                vals.append(ll + (self.hidden_log_prior(choice) if coordinate == 1 else 0.))
                                opts.append((tuple(trial), ll))
                            logp = np.array(vals)
                            chosen = rng.choice(len(opts), p=np.exp(logp - logsumexp(logp)))
                            structures[pi], value = opts[chosen]
                if it >= cfg.warmup and (it - cfg.warmup) % cfg.thin == 0:
                    retained.append(z.copy())
                    graphs.append(list(structures))
                    lls.append(value)
                if progress and (it == 0 or (it + 1) % 100 == 0):
                    progress({"chain": chain + 1, "iteration": it + 1, "iterations": iterations,
                              "log_likelihood": value, "seconds": time.monotonic() - started})
            chains.append(retained)
            structural.append(graphs)
            likelihoods.append(lls)
            calls.append(n_calls)
        return np.array(chains), np.array(structural), np.array(likelihoods), calls

    def report(self, chains, structures, likelihoods):
        cfg = self.cfg
        flat = chains.reshape((-1, chains.shape[-1]))
        flat_s = structures.reshape((-1, len(self.processes), 2))
        parameters = [self.parameters(z) for z in flat]
        mus = np.array([p["mu"] for p in parameters])
        sig = np.array([p["sigma"] for p in parameters])
        common = np.array([p["common"] for p in parameters])
        medians = np.exp(mus)
        means = np.exp(mus + .5 * (sig ** 2 + common ** 2)[:, None])
        diag_values = {"log_likelihood": likelihoods}
        for key in ('location', 'agency_sd', 'task_sd', 'step_sd', 'sigma', 'common'):
            diag_values[f'hyper:{key}'] = np.array([p[key] for p in parameters]).reshape(chains.shape[:2])
        for si, source in enumerate(self.sources):
            diag_values[f'source_bias:{source}'] = np.array([p['source_bias'][si] for p in parameters]).reshape(chains.shape[:2])
        for i, (pid, a) in enumerate(self.activities):
            diag_values[f"step:{pid}:{a['id']}"] = mus[:, i].reshape(chains.shape[:2])
        agency_reports = []
        for ai, name in enumerate(self.agency_names):
            effect = np.array([p["agency"][ai] for p in parameters])
            diag_values[f"actor_effect:{name}"] = effect.reshape(chains.shape[:2])
            if name.startswith("role:"):
                continue
            ids = np.flatnonzero(self.agencies == ai)
            direct = sum(m['scope'] == 'step' and p.global_indices[m['indices'][0]] in ids
                         for p in self.processes for m in p.measurements)
            constrained = len(set(ids) & set(self.active_steps))
            # Observed-inventory arithmetic mean of case-duration expectations;
            # separately report standardized task-mix effect (not labor productivity).
            diag_values[f'agency_inventory_mean:{name}'] = np.log(means[:, ids].mean(axis=1)).reshape(chains.shape[:2])
            agency_reports.append({"agency": name, "n_represented_tasks": len(ids),
                "inventory_mean_elapsed_days": summary(means[:, ids].mean(axis=1)),
                "task_adjusted_time_ratio": summary(np.exp(effect)),
                "direct_step_claims": int(direct), "activities_constrained_by_timing": constrained,
                "borrowed_only": constrained == 0,
                "work_hours": None,
                "estimand": "equal-weight represented task inventory; elapsed time includes waiting, not agency labor"})
        reports = {}
        for pi, p in enumerate(self.processes):
            process_medians, process_p90, closeout, submission, case_steps, agency_tasks, conditional, agency_counts = [], [], [], [], [], [], [], []
            for draw, (z, params, st) in enumerate(zip(flat, parameters, flat_s)):
                dur, mask, ends, hidden, gp = self.process_state(p, z, params, st[pi], population=True)
                elapsed = p.decision_time(ends, mask) + hidden
                process_medians.append(float(np.median(elapsed)))
                process_p90.append(float(np.quantile(elapsed, .9)))
                submission.append(float(np.median(np.maximum(1e-8, elapsed - p.start_offset(ends, 'submission')))))
                closeout.append(float(np.median(elapsed + dur[:, :p.n][:, p.closeout].sum(axis=1))))
                case_steps.append(float(np.mean(mask.sum(axis=1) + st[pi][1])))
                amask = np.array([p.actor[a["actor_id"]]["role"] == "agency" for a in p.activities])
                agency_tasks.append(float(np.mean((mask * amask).sum(axis=1))))
                ids = {a['actor_id'] for a in p.activities if p.actor[a['actor_id']]['role'] == 'agency'}
                involved = np.zeros(len(mask))
                for actor in ids:
                    involved += np.any(mask[:, [i for i, a in enumerate(p.activities) if a['actor_id'] == actor]], axis=1)
                agency_counts.append(float(np.mean(involved)))
                conditional.append(gp.tolist())
            process_medians = np.array(process_medians)
            diag_values[f"process:{p.id}"] = np.log(process_medians).reshape(chains.shape[:2])
            diag_values[f'process_p90:{p.id}'] = np.log(process_p90).reshape(chains.shape[:2])
            diag_values[f'core_closeout:{p.id}'] = np.log(closeout).reshape(chains.shape[:2])
            diag_values[f'initial_case_operations:{p.id}'] = np.array(case_steps).reshape(chains.shape[:2])
            for k, key in enumerate(p.gate_keys):
                diag_values[f'conditional_prevalence:{p.id}:{key}'] = np.array(conditional)[:, k].reshape(chains.shape[:2])
            outcomes = np.array([p.outcome_probabilities(z, cfg) for z in flat])
            if p.outcome_dimension:
                for k, decision in enumerate(p.decisions):
                    diag_values[f'outcome_prevalence:{p.id}:{p.activities[decision]["id"]}'] = outcomes[:,k].reshape(chains.shape[:2])
            hidden_counts = flat_s[:, pi, 1]
            diag_values[f"unseen:{p.id}"] = structures[:, :, pi, 1]
            for gi in range(len(p.graphs)):
                diag_values[f"graph:{p.id}:{gi}"] = (structures[:, :, pi, 0] == gi).astype(float)
            activities = []
            for i, a in enumerate(p.activities):
                idx = p.global_indices[i]
                timing = summary(medians[:, idx])
                direct = [m for m in p.measurements if m["scope"] == "step" and i in m["indices"]]
                activities.append({"id": a["id"], "name": a["name"],
                    "actor": p.actor[a["actor_id"]]["name"], "actor_role": p.actor[a["actor_id"]]["role"],
                    "stage": a["stage"], "scope": a["scope"], "task_type": a["task_type"],
                    "timing": {"median_days": timing["median"], "median_ci90": timing["ci90"],
                               "mean_days": summary(means[:, idx]), "direct_claims": len(direct),
                               "learned_via_hierarchy_or_total": not bool(direct)},
                    "evidence": a["evidence"]})
            probs = np.bincount(flat_s[:, pi, 0], minlength=len(p.graphs)) / len(flat)
            point_graph = p.graphs[int(np.argmax(probs))]
            model = {"model_id": f"bayes_v4_{p.id}", "activities": activities,
                "edges": [{"source": p.activities[i]["id"], "target": p.activities[j]["id"], "kind": "precedes"}
                          for i, j in sorted(point_graph["edges"])],
                "process_timing": {"median_days": float(np.median(process_medians)),
                    "median_ci90": np.quantile(process_medians, [.05, .95]).tolist(),
                    "p90_days": float(np.median(process_p90)), "p90_ci90": np.quantile(process_p90, [.05, .95]).tolist(),
                    "scope": "preparation/filing through first decision, includes modeled undocumented stages"}}
            reports[p.id] = {"model": model,
                "step_count": summary(p.n + hidden_counts),
                "represented_count": p.n, "unseen_count": summary(hidden_counts),
                "probability_at_unseen_cap": float(np.mean(hidden_counts == cfg.max_unseen)) if cfg.max_unseen else None,
                "count_caveat": "conditional on semantic inventory; undocumented count/time tradeoff is weakly identified and prior-sensitive",
                "graph_probabilities": probs.tolist(), "graph_notes": p.graph_notes,
                "submission_to_decision_median": summary(submission), "closeout_median": summary(closeout),
                "closeout_scope": "initial decision plus serial core closeout operations; conditional closeout routes not identified",
                "conditional_closeout_not_fitted": [a['id'] for a in p.activities if a['stage'] == 'closeout' and a['scope'] == 'conditional'],
                "expected_steps_per_case": summary(case_steps), "represented_agency_tasks_per_case": summary(agency_tasks),
                "case_count_scope": "distinct modeled operations through initial decision, not a count of repeat visits",
                "expected_agencies_executing_work_per_case": summary(agency_counts),
                "agency_count_represented": len({a["actor_id"] for a in p.activities if p.actor[a["actor_id"]]["role"] == "agency"}),
                "gate_prevalence": {key: summary(np.array(conditional)[:, k]) for k, key in enumerate(p.gate_keys)},
                'outcome_prevalence': {p.activities[i]['id']: summary(outcomes[:,k]) for k,i in enumerate(p.decisions)},
                "work_hours": {"payer": None, "agency": None, "reason": "no work-hour likelihood in elapsed model; never convert waiting days to labor"},
                "measurements_used": len(p.measurements), "excluded_from_elapsed_likelihood": p.excluded,
                'evidence_schema': p.evidence['schema_version'],
                'observation_contexts': list(p.contexts.values()),
                "process_median_draws": process_medians.tolist()}
        diags = {name: diagnostics(values) for name, values in diag_values.items()}
        problematic = {k: v for k, v in diags.items() if v['rhat'] is None or v['rhat'] > 1.01 or v['ess_bulk'] < 400 or v['ess_tail'] < 200}
        return {"version": "bayesian-process/4", "config": asdict(cfg), "programs": reports,
                "identification": information_report(chains, self.layout.slices, sampling_converged=not problematic),
                "agencies": agency_reports, "diagnostics": diags, "diagnostics_flagged": problematic,
                "posterior_converged": not problematic,
                "limitations": ["Semantic inventory and actor aliases conditional on LLM interpretation; repeat extraction is a sensitivity check, not calibrated error probabilities",
                    "Graph posterior conditional on finite candidate completions; not all DAGs",
                    "Undocumented stage count depends on explicit geometric prior; source coverage is not identified",
                    "No representative case sampling frame: community-report selection bias is not identified",
                    "Conditional case prevalence prior is not calibrated from biased forum frequencies",
                    "Known outcomes and selected cohorts condition claims; population outcome proportions have an exchangeable logistic-normal prior, not representative anecdote counts",
                    "Historical/hypothetical reports excluded from the static current-process likelihood, not modeled dynamically",
                    "Population-summary likelihood uses fixed Sobol quadrature; validate size/seed sensitivity",
                    "Same source/thread shares a bias; unknown copying across sources remains unidentified",
                    "No calendar-specific holidays, abandonment, time trends, or explicit rework routing in this version",
                    "Step elapsed time is not hands-on work or agency productivity"]}
