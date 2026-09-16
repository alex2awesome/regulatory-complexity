"""A bounded, modular Bayesian process model (stdlib, no LLM/truth dependencies).

Structure: finite random set of steps, Gamma-Poisson document detection, a
Dirichlet-multinomial name likelihood, categorical actor noise, and a clutter
component. Collapsed Gibbs samples partitions; N includes undetected steps.
Timing: typed grid posterior for log-median and case dispersion, conditional on
each partition. This is a CUT posterior: duration does not drive name merging.
Burden: posterior case simulation, keeping elapsed time and labor separate.

See docs/2026-09-16-bayesian-process-v3.md for the likelihood, assumptions and limitations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
import json
import math
import pathlib
import random
import re
import statistics

from .bayes_evidence import flatten, norm, actor_name


@dataclass(frozen=True)
class Config:
    seed: int = 20260916
    chains: int = 4
    sweeps: int = 400
    burn: int = 150
    thin: int = 10
    max_steps: int = 100
    count_mean: float = 20.0
    count_shape: float = 2.0
    detection_shape: float = 0.8
    detection_rate: float = 1.0
    internal_prior: float = 0.3
    word_concentration: float = 25.0
    clutter_rate: float = 0.02
    timing_prior_median: float = 7.0
    timing_prior_log_sd: float = 1.5
    source_bias_sd: float = 0.35
    cases_per_draw: int = 30


def logsumexp(xs):
    xs = list(xs)
    m = max(xs, default=-math.inf)
    return m + math.log(sum(math.exp(x - m) for x in xs)) if math.isfinite(m) else m


def probabilities(logs):
    z = logsumexp(logs)
    if not math.isfinite(z):
        raise ValueError("No finite posterior mass; check evidence/configuration")
    return [math.exp(x - z) for x in logs]


def categorical(values, weights, rng):
    u, acc = rng.random() * sum(weights), 0.0
    for value, w in zip(values, weights):
        acc += w
        if u < acc:
            return value
    return values[-1]


def quantile(xs, p):
    values = sorted(xs)
    if not values:
        return None
    index = (len(values) - 1) * p
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def summary(xs):
    xs = list(xs)
    if not xs:
        return {"median": None, "mean": None, "ci90": None, "n": 0}
    return {"median": quantile(xs, .5), "mean": statistics.mean(xs),
            "ci90": [quantile(xs, .05), quantile(xs, .95)], "n": len(xs)}


def point_actor(actors, weights):
    """Abstain rather than report a uniform-prior tie as a resolved actor."""
    best = max(range(len(actors)), key=weights.__getitem__)
    return actors[best] if weights[best] > .5 else "unknown"


def summarize_burden(case_batches):
    """Separate predictive variation from uncertainty about conditional means.

    A missing decision is an undefined estimand, not a zero-duration case.
    Missing work-hours are unmeasured burden: suppress the total, rather than
    summarize the rare cases with no work events as evidence of zero burden.
    """
    cases = [c for batch in case_batches for c in batch]
    result = {}
    for key in cases[0]:
        values = [c[key] for c in cases if c[key] is not None]
        complete = len(values) == len(cases)
        unmeasured_labor = key in {"applicant_hours", "agency_hours"} and not complete
        per_draw = []
        for batch in case_batches:
            defined = [c[key] for c in batch if c[key] is not None]
            if defined:
                per_draw.append(statistics.mean(defined))
        result[key] = {
            "case_predictive": summary([] if unmeasured_labor else values),
            "posterior_expected": summary([] if unmeasured_labor else per_draw),
            "fraction_defined": len(values) / len(cases),
            "status": "unmeasured" if unmeasured_labor else "complete" if complete else "conditional_on_defined",
            "conditioning": "represented steps; defined cases within each posterior draw",
            "posterior_draws_with_defined_cases": len(per_draw),
        }
    return result


def source_accuracy(kind):
    return .70 if kind in {"reddit_thread", "forum_thread"} else .85


def exposure(kind, internal=False):
    public = {"sop": 1.0, "staff_report": .8, "audit_excerpt": 1.0,
              "checklist": .65, "form": .4, "program_page": .5,
              "ordinance": .3, "bill_analysis": .2, "reddit_thread": .35}
    private = {"sop": 1.0, "staff_report": .8, "audit_excerpt": 1.0,
               "reddit_thread": .10, "forum_thread": .10}
    return (private.get(kind, .03) if internal else public.get(kind, .3))


class StructurePosterior:
    def __init__(self, evidence, config=Config()):
        self.config = config
        self.documents, self.claims = flatten(evidence)
        if not self.claims:
            raise ValueError("Evidence must contain at least one claim")
        self.sources = {d.get("source_family") or d["id"]: d["kind"] for d in self.documents}
        self.vocab = Counter(w for c in self.claims for w in c["words"])
        total = sum(self.vocab.values())
        self.base = {w: n / total for w, n in self.vocab.items()}
        actors = {actor_name(c.get("actor")) for c in self.claims} - {None}
        self.actors = sorted(actors | {"applicant", "third_party", "unresolved_agency"})
        self.E = [sum(exposure(kind, internal) for kind in self.sources.values()) for internal in (False, True)]
        a, b = config.detection_shape, config.detection_rate
        self.q0 = sum(weight * (b / (b + e)) ** a for weight, e in
                      zip((1 - config.internal_prior, config.internal_prior), self.E))
        self.log_count_prior = [self.count_prior(n) for n in range(config.max_steps + 1)]
        self.logV = [logsumexp(self.n_logs(k)) for k in range(config.max_steps + 1)]
        self.background = [math.log(config.clutter_rate) +
                           sum(math.log(self.base[w]) for w in c["words"]) for c in self.claims]
        self.cannot_link = set()
        # Explicitly ordered mentions in one source describe different activities.
        lookup = {(c["doc_id"], norm(c["name"])): i for i, c in enumerate(self.claims)}
        for i, c in enumerate(self.claims):
            for target in (c.get("precedes") or []) + (c.get("follows") or []):
                j = lookup.get((c["doc_id"], norm(target)))
                if j is not None and i != j:
                    self.cannot_link.add(frozenset((i, j)))

    def count_prior(self, n):
        r = self.config.count_shape
        p = r / (r + self.config.count_mean)
        return math.lgamma(n + r) - math.lgamma(r) - math.lgamma(n + 1) + r * math.log(p) + n * math.log1p(-p)

    def n_logs(self, k):
        return [self.log_count_prior[n] + math.lgamma(n + 1) - math.lgamma(n - k + 1)
                + (n - k) * math.log(self.q0) for n in range(k, self.config.max_steps + 1)]

    def count_distribution(self, k):
        values = list(range(k, self.config.max_steps + 1))
        return values, probabilities(self.n_logs(k))

    @lru_cache(maxsize=50000)
    def actor_posterior(self, members):
        observations = {}
        for i in sorted(members):
            c = self.claims[i]
            actor = actor_name(c.get("actor"))
            if actor:
                observations.setdefault(c["source_family"], set()).add((actor, c["source_kind"]))
        logs = []
        for actor in self.actors:
            logp = -math.log(len(self.actors))
            for values in observations.values():
                # Contradictory claims from a single source are alternatives, not extra votes.
                likelihoods = []
                for value, kind in values:
                    r = source_accuracy(kind)
                    likelihoods.append(r if actor == value else (1 - r) / (len(self.actors) - 1))
                logp += math.log(sum(likelihoods) / len(likelihoods))
            logs.append(logp)
        return probabilities(logs), logsumexp(logs)

    @lru_cache(maxsize=100000)
    def cluster_log(self, members):
        if any(pair.issubset(members) for pair in self.cannot_link):
            return -math.inf
        cfg = self.config
        counts = Counter(w for i in members for w in self.claims[i]["words"])
        eta = cfg.word_concentration
        mark = math.lgamma(eta) - math.lgamma(eta + sum(counts.values()))
        for w, n in counts.items():
            alpha = eta * self.base[w]
            mark += math.lgamma(alpha + n) - math.lgamma(alpha)
        # Gamma-Poisson random-set likelihood, including zero detections in read sources.
        source_counts = Counter(self.claims[i]["source_family"] for i in members)
        n, a, b = len(members), cfg.detection_shape, cfg.detection_rate
        visibility_logs = []
        for internal, weight, E in zip((False, True), (1 - cfg.internal_prior, cfg.internal_prior), self.E):
            term = math.log(weight) + a * math.log(b) + math.lgamma(a + n) - math.lgamma(a)
            term -= (a + n) * math.log(b + E)
            term += sum(count * math.log(exposure(self.sources[src], internal)) for src, count in source_counts.items())
            visibility_logs.append(term)
        return mark + logsumexp(visibility_logs) + self.actor_posterior(members)[1]

    def state_log(self, groups, clutter):
        return self.logV[len(groups)] + sum(self.cluster_log(frozenset(g)) for g in groups) + sum(self.background[i] for i in clutter)

    def sample(self):
        cfg = self.config
        if cfg.burn >= cfg.sweeps or min(cfg.chains, cfg.thin, cfg.cases_per_draw) < 1:
            raise ValueError("Need positive chains/thin/cases and burn < sweeps")
        draws, chain_counts = [], []
        for chain in range(cfg.chains):
            rng = random.Random(cfg.seed + 1009 * chain)
            # Dispersed starts: singletons, exact-name clusters, or all clutter.
            if chain % 3 == 0:
                groups, clutter = [{i} for i in range(len(self.claims))], set()
            elif chain % 3 == 1:
                named = {}
                for i, c in enumerate(self.claims):
                    named.setdefault(norm(c["name"]), set()).add(i)
                groups, clutter = list(named.values()), set()
            else:
                groups, clutter = [], set(range(len(self.claims)))
            if len(groups) > cfg.max_steps:
                groups, clutter = [], set(range(len(self.claims)))
            counts = []
            for sweep in range(cfg.sweeps):
                order = list(range(len(self.claims))); rng.shuffle(order)
                for i in order:
                    if i in clutter:
                        clutter.remove(i)
                    else:
                        for g in groups:
                            if i in g:
                                g.remove(i); break
                        groups = [g for g in groups if g]
                    k = len(groups)
                    # Scores relative to the state with this mention removed.
                    logs = [self.background[i]]
                    logs += [self.cluster_log(frozenset(g | {i})) - self.cluster_log(frozenset(g)) for g in groups]
                    if k < cfg.max_steps:
                        logs.append(self.logV[k + 1] - self.logV[k] + self.cluster_log(frozenset((i,))))
                    choice = categorical(list(range(len(logs))), probabilities(logs), rng)
                    if choice == 0:
                        clutter.add(i)
                    elif choice <= k:
                        groups[choice - 1].add(i)
                    else:
                        groups.append({i})
                if sweep >= cfg.burn and (sweep - cfg.burn) % cfg.thin == 0:
                    values, weights = self.count_distribution(len(groups))
                    n = categorical(values, weights, rng)
                    counts.append(n)
                    draws.append({"chain": chain, "sweep": sweep, "n_steps": n,
                                  "groups": [sorted(g) for g in sorted(groups, key=min)],
                                  "clutter": sorted(clutter), "log_density": self.state_log(groups, clutter)})
            chain_counts.append(counts)
        return draws, chain_counts


def normal_logpdf(x, mean, variance):
    return -.5 * (math.log(2 * math.pi * variance) + (x - mean) ** 2 / variance)


def normal_cdf(x):
    return .5 * (1 + math.erf(x / math.sqrt(2)))


def timing_grid(measurements, config=Config(), field="elapsed_days"):
    """Typed likelihood; individual waits != medians != targets. Zero is rounded [0,.5]."""
    valid, excluded, seen = [], [], set()
    for m in measurements:
        if m.get("field", "elapsed_days") != field:
            continue
        # Segment/process summaries require their own schedule likelihood.
        units = "hours" if field.endswith("hours") else "calendar_days"
        if m.get("scope", "step") != "step" or m.get("units", units) != units:
            excluded.append({**m, "excluded_reason": "not a step-level measurement in the modeled units"})
            continue
        if not m.get("usable", True) or m.get("kind") in {"target", "statutory_cap", "deadline"}:
            excluded.append(m); continue
        value = m.get("value")
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            excluded.append(m); continue
        key = (m.get("source"), m.get("kind"), value, tuple(m.get("interval") or []))
        if key not in seen:
            valid.append(m); seen.add(key)
    # A fixed, documented quadrature grid. Upper/lower boundary mass is reported.
    mus = [math.log(.025) + j * (math.log(7300) - math.log(.025)) / 100 for j in range(101)]
    sigmas = [.15, .30, .50, .75, 1.0, 1.4]
    prior_mu = math.log(config.timing_prior_median if field == "elapsed_days" else 2.0)
    states, logs = [], []
    for mu in mus:
        for sigma in sigmas:
            logp = normal_logpdf(mu, prior_mu, config.timing_prior_log_sd ** 2) - .5 * (sigma / .8) ** 2
            by_source = {}
            for m in valid:
                by_source.setdefault(m.get("source", m.get("doc_id", "unknown")), []).append(m)
            for observations in by_source.values():
                # Shared source offset is integrated by quadrature, so repeats from
                # one source do not masquerade as independent corroboration.
                offsets, offset_weights = [-1.732, 0., 1.732], [1/6, 2/3, 1/6]
                source_logs = []
                for z, w in zip(offsets, offset_weights):
                    subtotal = math.log(w)
                    for m in observations:
                        kind = m.get("kind", "reported")
                        report_sd = .15 if m.get("source_kind") in {"official_stats", "audit_excerpt"} else .35
                        if kind in {"observed", "individual"}:
                            variance = sigma ** 2 + report_sd ** 2
                        elif kind in {"median", "p50"}:
                            n = m.get("n")
                            variance = report_sd ** 2 + (math.pi * sigma ** 2 / (2 * n) if isinstance(n, (int, float)) and n > 0 else .5 ** 2)
                        elif kind in {"reported", "typical"}:
                            variance = .7 ** 2  # ambiguous 'typical', not a case draw
                        else:
                            raise ValueError(f"Unsupported timing statistic: {kind}")
                        mean = mu + z * config.source_bias_sd
                        bounds = m.get("interval")
                        if m["value"] == 0 and not bounds:
                            bounds = [0, .5]
                        if bounds:
                            low, high = bounds
                            if high <= 0 or low < 0 or high < low:
                                raise ValueError("Invalid duration interval")
                            if high == low:
                                subtotal += normal_logpdf(math.log(max(high, .001)), mean, variance)
                            else:
                                lo = normal_cdf((math.log(low) - mean) / math.sqrt(variance)) if low > 0 else 0
                                hi = normal_cdf((math.log(high) - mean) / math.sqrt(variance))
                                subtotal += math.log(max(hi - lo, 1e-300))
                        else:
                            subtotal += normal_logpdf(math.log(m["value"]), mean, variance)
                    source_logs.append(subtotal)
                logp += logsumexp(source_logs)
            states.append((mu, sigma)); logs.append(logp)
    weights = probabilities(logs)
    return {"states": states, "weights": weights, "n_observations": len(valid),
            "n_sources": len({m.get('source') for m in valid}), "excluded": excluded,
            "boundary_mass": sum(w for (mu, _), w in zip(states, weights) if mu in (mus[0], mus[-1]))}


def categorical_field(claims, field, values, prior=None):
    if not values:
        return [], []
    logs = [math.log((prior or {}).get(value, 1 / len(values))) for value in values]
    grouped = {}
    for c in claims:
        value = c.get(field)
        if value is not None:
            grouped.setdefault(c["source_family"], []).append((value, c["source_kind"]))
    if len(values) == 1:
        return values, [1.0]
    for observed in grouped.values():
        for i, value in enumerate(values):
            terms = [source_accuracy(kind) if value == v else (1 - source_accuracy(kind)) / (len(values) - 1)
                     for v, kind in observed]
            logs[i] += math.log(sum(terms) / len(terms))
    return values, probabilities(logs)


def classify(name):
    """Transparent fallback for missing legacy scope labels, NOT learned truth."""
    s = norm(name)
    if re.search(r"\b(publish|adopt|introduce|promulgate|report aggregate|keep the permit|nightly|retain records)\b", s):
        return "standing"
    if re.search(r"\b(hearing|appeal|ability to pay|citation|fine|violation)\b", s):
        return "conditional"
    if re.search(r"\b(issue|grant|deny|approve)\b", s) and re.search(r"\b(permit|certificate|application|decision)\b", s):
        return "decision"
    return "ordinary"


def topological(nodes, edges):
    incoming = {n: set() for n in nodes}
    for u, v in edges:
        if u in incoming and v in incoming:
            incoming[v].add(u)
    order = []
    while incoming:
        ready = sorted(n for n, parents in incoming.items() if not parents)
        if not ready:
            return None
        order.extend(ready)
        for n in ready:
            del incoming[n]
        for parents in incoming.values():
            parents.difference_update(ready)
    return order


def relation_evidence(claims, groups):
    assignment = {i: k for k, group in enumerate(groups) for i in group}
    lookup = {}
    for i, c in enumerate(claims):
        if i in assignment:
            lookup.setdefault(norm(c["name"]), set()).add(assignment[i])
    order, rework = {}, {}
    for i, c in enumerate(claims):
        if i not in assignment:
            continue
        k = assignment[i]
        for direction, field in ((1, "precedes"), (-1, "follows")):
            for name in c.get(field) or []:
                target = lookup.get(norm(name), set())
                if len(target) != 1:
                    continue  # unresolved references are not guessed
                j = next(iter(target))
                if j != k:
                    pair = (k, j) if direction == 1 else (j, k)
                    order.setdefault(pair, {})[c["source_family"]] = source_accuracy(c["source_kind"])
        rw = c.get("rework") or {}
        targets = lookup.get(norm(rw.get("back_to", "")), set())
        if len(targets) == 1:
            j = next(iter(targets))
            if j != k:
                rework.setdefault((k, j), {})[c["source_family"]] = source_accuracy(c["source_kind"])
    return order, rework


def sample_relations(n, observations, rng):
    pairs = {tuple(sorted(pair)) for pair in observations}
    choices = []
    for u, v in sorted(pairs):
        logs = [math.log(.8), math.log(.1), math.log(.1)]  # none / u->v / v->u
        for direction, pair in ((1, (u, v)), (2, (v, u))):
            for r in observations.get(pair, {}).values():
                for j in range(3):
                    logs[j] += math.log(r if j == direction else (1 - r) / 2)
        choices.append(((u, v), probabilities(logs)))
    # Constrained Gibbs, targeting the product of relation likelihoods given
    # acyclicity. Whole-graph rejection is unusable when sources disagree strongly.
    edges = set()
    for _ in range(30):
        scan = list(choices); rng.shuffle(scan)
        for (u, v), weights in scan:
            edges.discard((u, v)); edges.discard((v, u))
            allowed = [weights[0]]
            for edge in ((u, v), (v, u)):
                allowed.append(weights[len(allowed)] if topological(range(n), edges | {edge}) is not None else 0.)
            state = categorical([0, 1, 2], allowed, rng)
            if state:
                edges.add((u, v) if state == 1 else (v, u))
    return sorted(edges)


def simulate_case(nodes, edges, rework, rng, max_repeats=3):
    """Acyclic schedule plus explicit rework excursions; missing hours stay missing.

    Edges encode prerequisite completion. Conditional/standing activity inclusion
    is a first-version approximation, reported as such, not an inferred case mix.
    """
    order = topological(range(len(nodes)), edges)
    if order is None:
        raise ValueError("Base graph must be acyclic; put loops in rework")
    parents = {i: [u for u, v in edges if v == i] for i in range(len(nodes))}
    ends, events, visits = {}, [], Counter()
    for i in order:
        node = nodes[i]
        start = max((ends.get(p, 0.) for p in parents[i]), default=0.)
        if rng.random() > node.get("p_occurs", 1):
            ends[i] = start; continue
        duration = max(0., rng.lognormvariate(node["mu"], node["sigma"]))
        ends[i] = start + duration
        visits[i] += 1
        events.append({"node": i, "start": start, "end": ends[i], "duration": duration, "repeat": False})
        # Repeat the whole supported path from the rework destination through i.
        for u, v, probability in rework:
            if u != i or order.index(v) > order.index(u):
                continue
            ancestors = {u}
            changed = True
            while changed:
                old = len(ancestors)
                ancestors.update(p for q in list(ancestors) for p in parents[q])
                changed = len(ancestors) != old
            descendants = {v}
            for q in order:
                if any(p in descendants for p in parents[q]):
                    descendants.add(q)
            excursion = [q for q in order if q in ancestors & descendants]
            if v not in ancestors:
                continue
            for _ in range(max_repeats):
                if rng.random() >= probability:
                    break
                base = ends[i]
                local = {}
                for q in excursion:
                    if not visits[q]:
                        continue
                    begin = max([base] + [local[p] for p in parents[q] if p in local])
                    d = rng.lognormvariate(nodes[q]["mu"], nodes[q]["sigma"])
                    local[q] = begin + d; visits[q] += 1
                    events.append({"node": q, "start": begin, "end": local[q], "duration": d, "repeat": True})
                for q, end in local.items():
                    ends[q] = max(ends.get(q, 0.), end)
    cash, transactions, encounters = 0., set(), set()
    payer_hours = agency_hours = 0.
    payer_missing = agency_missing = 0
    agencies, unknown_agency_steps, agency_tasks = set(), 0, 0
    for e in events:
        i = e["node"]; node = nodes[i]
        actor = node["actor"]
        agency = actor not in {"applicant", "third_party"}
        if agency:
            agency_tasks += 1
            if actor == "unresolved_agency":
                unknown_agency_steps += 1
            else:
                agencies.add(actor)
        amount = node.get("fee")
        transaction = node.get("transaction_id") or f"step:{i}"
        if amount is not None and (transaction not in transactions or node.get("fee_per_visit", False)):
            cash += amount; transactions.add(transaction)
        if node.get("occasion") in {"counter", "site_visit", "hearing"}:
            # If absent, encounter identity is unknown: this is an upper-count proxy.
            encounter = node.get("encounter_id") or f"step:{i}"
            encounters.add((encounter, e["start"] if e["repeat"] else 0))
        for field, applies in (("applicant_hours", actor in {"applicant", "third_party"}),
                               ("agency_hours", agency)):
            param = node.get(field)
            if param is not None:
                hours = rng.lognormvariate(*param)
                if field == "applicant_hours":
                    payer_hours += hours
                else:
                    agency_hours += hours
            elif applies:
                if field == "applicant_hours":
                    payer_missing += 1
                else:
                    agency_missing += 1
    decision_times = [ends[i] for i in visits if nodes[i].get("is_decision")]
    return {"elapsed_to_decision_days": min(decision_times) if decision_times else None,
            "elapsed_to_closeout_days": max(ends.values(), default=0.),
            "documented_fees": cash, "step_executions": len(events),
            "distinct_steps_encountered": len(visits), "repeat_executions": sum(visits.values()) - len(visits),
            "agency_step_executions": agency_tasks, "resolved_agencies_involved": len(agencies),
            "unresolved_agency_executions": unknown_agency_steps,
            "encounter_upper_proxy": len(encounters),
            "applicant_hours": payer_hours if not payer_missing else None,
            "agency_hours": agency_hours if not agency_missing else None,
            "unmeasured_applicant_work_events": payer_missing,
            "unmeasured_agency_work_events": agency_missing}


def basic_rhat(chains):
    """Basic between/within-chain diagnostic; not a convergence guarantee."""
    m = len(chains); n = min(map(len, chains), default=0)
    if m < 2 or n < 2:
        return None
    means = [statistics.mean(c[:n]) for c in chains]
    W = statistics.mean(statistics.variance(c[:n]) for c in chains)
    B = n * statistics.variance(means)
    if W == 0:
        return 1.0 if B == 0 else None
    return math.sqrt(((n - 1) / n * W + B / n) / W)


def fit(evidence, config=Config()):
    posterior = StructurePosterior(evidence, config)
    draws, chains = posterior.sample()
    rng = random.Random(config.seed + 99991)
    timing_cache = {}
    group_summaries = {}

    def parameters(group):
        key = tuple(group)
        if key in group_summaries:
            return group_summaries[key]
        claims = [posterior.claims[i] for i in group]
        measurements = [m for c in claims for m in c.get("measurements", [])]
        timing_cache[key] = timing_grid(measurements, config)
        counts = Counter(c["name"] for c in claims)
        name = sorted(counts, key=lambda n: (-counts[n], n))[0]
        actor_weights, _ = posterior.actor_posterior(frozenset(group))
        fees = [c.get("fee", {}).get("amount") for c in claims if isinstance(c.get("fee"), dict)]
        fees = sorted({float(f) for f in fees if isinstance(f, (int, float)) and f >= 0})
        fee_claims = [{**c, "amount": c["fee"]["amount"]} for c in claims
                      if isinstance(c.get("fee"), dict) and isinstance(c["fee"].get("amount"), (int, float))]
        _, fw = categorical_field(fee_claims, "amount", fees)
        occasions = sorted({c["occasion"] for c in claims if c.get("occasion")})
        _, ow = categorical_field(claims, "occasion", occasions)
        labor = {}
        for field in ("applicant_hours", "agency_hours"):
            values = [m for m in measurements if m.get("field") == field and m.get("usable", True)]
            grid = timing_grid(values, config, field) if values else None
            labor[field] = grid if grid and grid["n_observations"] else None
        result = {"name": name, "actor_weights": actor_weights, "fees": fees, "fee_weights": fw,
                  "occasions": occasions, "occasion_weights": ow, "class": classify(name),
                  "measurements": measurements, "labor": labor,
                  "claims": [c["claim_id"] for c in claims]}
        group_summaries[key] = result
        return result

    # One representative posterior graph, not an independently thresholded set of marginals.
    representative = max(draws, key=lambda d: d["log_density"])
    model_acts, membership = [], {}
    for i, group in enumerate(representative["groups"]):
        p = parameters(group); grid = timing_cache[tuple(group)]
        med_draws = [math.exp(categorical(grid["states"], grid["weights"], rng)[0]) for _ in range(1000)]
        membership[i] = frozenset(group)
        model_acts.append({"id": f"B{i+1:02d}", "name": p["name"],
                           "actor": point_actor(posterior.actors, p["actor_weights"]),
                           "actor_posterior": dict(zip(posterior.actors, p["actor_weights"])),
                           "occasion": p["occasions"][max(range(len(p["occasions"])), key=p["occasion_weights"].__getitem__)] if p["occasions"] else None,
                           "timing": {"median_days": statistics.median(med_draws), "kind": "median",
                                      "median_ci90": summary(med_draws)["ci90"], "n_claims": grid["n_observations"],
                                      "prior_only": grid["n_observations"] == 0,
                                      "excluded": grid["excluded"], "grid_boundary_mass": grid["boundary_mass"]},
                           "fee": {"amount": p["fees"][max(range(len(p["fees"])), key=p["fee_weights"].__getitem__)]} if p["fees"] else None,
                           "scope_class": p["class"], "evidence": p["claims"]})
    relation_obs, rw_obs = relation_evidence(posterior.claims, representative["groups"])
    rep_edges = sample_relations(len(model_acts), relation_obs, rng)
    model = {"model_id": "bayes_process_v3", "source": "inferred", "activities": model_acts,
             "actors": posterior.actors,
             "edges": [{"from": f"B{u+1:02d}", "to": f"B{v+1:02d}", "type": "sequence"} for u, v in rep_edges] +
                      [{"from": f"B{u+1:02d}", "to": f"B{v+1:02d}", "type": "rework"} for u, v in sorted(rw_obs)]}
    case_draws, case_batches, median_elapsed, step_samples = [], [], [], {i: [] for i in membership}
    for d in draws:
        nodes = []
        for group in d["groups"]:
            p = parameters(group); grid = timing_cache[tuple(group)]
            mu, sigma = categorical(grid["states"], grid["weights"], rng)
            actor = categorical(posterior.actors, p["actor_weights"], rng)
            scope = p["class"]
            # Scope uncertainty is explicit and intentionally broad for legacy extractions.
            occurs = .05 if scope == "standing" else .15 if scope == "conditional" else .95
            node = {"name": p["name"], "mu": mu, "sigma": sigma, "actor": actor,
                    "p_occurs": occurs, "is_decision": scope == "decision",
                    "fee": categorical(p["fees"], p["fee_weights"], rng) if p["fees"] else None,
                    "occasion": categorical(p["occasions"], p["occasion_weights"], rng) if p["occasions"] else None}
            for field, labor_grid in p["labor"].items():
                node[field] = categorical(labor_grid["states"], labor_grid["weights"], rng) if labor_grid else None
            nodes.append(node)
            for i, members in membership.items():
                # Label-switching-safe reference: the cluster holding its first mention.
                if min(members) in group:
                    step_samples[i].append({"median": math.exp(mu), "case": rng.lognormvariate(mu, sigma), "actor": actor})
        order_obs, rework_obs = relation_evidence(posterior.claims, d["groups"])
        edges = sample_relations(len(nodes), order_obs, rng)
        # Undetected steps affect the count and sensitivity scenario, but have no
        # identified position/attributes. Do not silently invent a workflow for them.
        d["unseen_steps"] = d["n_steps"] - len(nodes)
        d["n_resolved_agencies"] = len({n["actor"] for n in nodes} - {"applicant", "third_party", "unresolved_agency"})
        d["n_unresolved_actor_steps"] = sum(n["actor"] == "unresolved_agency" for n in nodes)
        # Existence of a rework link is uncertain; trigger frequency is prior-only
        # unless the next extraction schema supplies a measured probability.
        rework = []
        for (u, v), sources in sorted(rework_obs.items()):
            odds = math.log(.2 / .8) + sum(math.log(r / (1-r)) for r in sources.values())
            if rng.random() < 1 / (1 + math.exp(-odds)):
                rework.append((u, v, rng.betavariate(1, 4)))
        cases = [simulate_case(nodes, edges, rework, rng) for _ in range(config.cases_per_draw)]
        case_draws.extend(cases)
        case_batches.append(cases)
        defined = [c["elapsed_to_decision_days"] for c in cases if c["elapsed_to_decision_days"] is not None]
        if defined:
            median_elapsed.append(statistics.median(defined))
    burden = summarize_burden(case_batches)
    for i, act in enumerate(model_acts):
        values = step_samples[i]
        act["timing"]["median_days"] = quantile([v["median"] for v in values], .5)
        act["timing"]["median_ci90"] = summary(v["median"] for v in values)["ci90"]
        act["timing"]["case_predictive_ci90"] = summary(v["case"] for v in values)["ci90"]
        act["reference_claim_presence"] = len(values) / len(draws)
    e2e = [c["elapsed_to_decision_days"] for c in case_draws if c["elapsed_to_decision_days"] is not None]
    model["process_timing"] = {"median_days": quantile(e2e, .5), "p90_days": quantile(e2e, .9),
                               "scope": "start of inferred included activities to first decision",
                               "conditional_on": "represented steps and a decision being reached; unseen-step burden unidentified",
                               "case_predictive_ci90": summary(e2e)["ci90"],
                               "population_median_ci90": summary(median_elapsed)["ci90"],
                               "population_median_note": "Conditional on a decision in each draw; interval also contains finite case-simulation error."}
    counts = Counter(d["n_steps"] for d in draws)
    coassignment = []
    for i in range(len(posterior.claims)):
        for j in range(i + 1, len(posterior.claims)):
            p = sum(any(i in group and j in group for group in d["groups"]) for d in draws) / len(draws)
            if p > .05:
                coassignment.append({"claims": [posterior.claims[i]["claim_id"], posterior.claims[j]["claim_id"]], "probability": p})
    result = {"schema": "bayes-process-posterior/3", "config": asdict(config), "model": model,
              "n_documents": len(posterior.documents), "n_source_families": len(posterior.sources),
              "n_claims": len(posterior.claims),
              "step_count": {**summary(d["n_steps"] for d in draws), "pmf": {str(n): c / len(draws) for n, c in sorted(counts.items())}},
              "represented_step_count": summary(len(d["groups"]) for d in draws),
              "unseen_step_count": summary(d["unseen_steps"] for d in draws),
              "resolved_agency_count": summary(d["n_resolved_agencies"] for d in draws),
              "unresolved_actor_steps": summary(d["n_unresolved_actor_steps"] for d in draws),
              "burden": burden, "coassignment": coassignment,
              "diagnostics": {"count_rhat_basic": basic_rhat(chains), "count_chain_means": [statistics.mean(c) for c in chains],
                              "represented_count_rhat_basic": basic_rhat([[len(d['groups']) for d in draws if d['chain'] == c] for c in range(config.chains)]),
                              "clutter_count_rhat_basic": basic_rhat([[len(d['clutter']) for d in draws if d['chain'] == c] for c in range(config.chains)]),
                              "n_draws": len(draws), "count_cap_mass": sum(d["n_steps"] == config.max_steps for d in draws) / len(draws),
                              "zero_detection_probability": posterior.q0,
                              "clutter_count": summary(len(d["clutter"]) for d in draws)},
              "limitations": ["modular/cut posterior: timing does not feed back into entity resolution",
                              "source reliability and disclosure priors are assumptions, not calibrated error rates",
                              "unknown steps counted but their routing and burden are unidentified",
                              "labor hours unavailable without explicit work-hour evidence",
                              "legacy scope classification and rework frequencies are prior-driven",
                              "no dynamic versions, joint case-selection correction, or learned staffing/queue model",
                              "graph ensemble uses sampled supported relations; absent relations may omit real dependencies"],
              "provenance": evidence.get("provenance", {})}
    return result, draws, case_draws


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sweeps", type=int, default=400)
    ap.add_argument("--burn", type=int, default=150)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--count-mean", type=float, default=20)
    a = ap.parse_args(argv)
    result, draws, cases = fit(json.loads(pathlib.Path(a.evidence).read_text()),
                              Config(sweeps=a.sweeps, burn=a.burn, chains=a.chains, seed=a.seed, count_mean=a.count_mean))
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for name, value in (("posterior.json", result), ("model.json", result["model"]),
                        ("draws.json", draws), ("case_draws.json", cases)):
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"step_count": result["step_count"], "diagnostics": result["diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
