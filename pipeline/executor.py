"""Run a compiled rule (decision_tree.schema.json) on a case.

The central object is `reachable_outcomes`: objective predicates are evaluated
mechanically from the case facts; judgment/reference predicates (and objective
predicates with missing inputs) are INDETERMINATE, so both branches are
explored. The result is the set of outcomes a faithful reader could reach for
this case — the per-case identified set. |outcomes| > 1 means the rule does
not determine this case: the case is a discretion witness (or a schema gap,
if the indeterminacy came from a missing input — the two are distinguished
in the result).

No LLM appears anywhere in this module.
"""

from dataclasses import dataclass, field


class Indeterminate(Exception):
    pass


def eval_expr(expr, facts):
    """Minimal JsonLogic-style evaluator. Raises Indeterminate on missing vars."""
    if not isinstance(expr, dict):
        return expr
    if len(expr) != 1:
        raise ValueError(f"malformed expr: {expr!r}")
    op, args = next(iter(expr.items()))
    if op == "var":
        name = args[0] if isinstance(args, list) else args
        if name not in facts or facts[name] is None:
            raise Indeterminate(name)
        return facts[name]
    if op == "missing":
        names = args if isinstance(args, list) else [args]
        return [n for n in names if n not in facts or facts[n] is None]
    vals = [eval_expr(a, facts) for a in (args if isinstance(args, list) else [args])]
    if op == "==":  return vals[0] == vals[1]
    if op == "!=":  return vals[0] != vals[1]
    if op == "<":   return vals[0] < vals[1]
    if op == "<=":  return vals[0] <= vals[1]
    if op == ">":   return vals[0] > vals[1]
    if op == ">=":  return vals[0] >= vals[1]
    if op == "!":   return not vals[0]
    if op == "and": return all(vals)
    if op == "or":  return any(vals)
    if op == "in":  return vals[0] in vals[1]
    if op == "+":   return sum(vals)
    if op == "-":   return vals[0] - vals[1] if len(vals) == 2 else -vals[0]
    if op == "*":
        out = 1
        for v in vals: out *= v
        return out
    if op == "/":   return vals[0] / vals[1]
    if op == "if":  return vals[1] if vals[0] else vals[2]
    raise ValueError(f"unsupported op: {op}")


@dataclass
class Run:
    """Result of exploring one case through one compiled rule."""
    outcomes: set = field(default_factory=set)
    pivotal_judgment: set = field(default_factory=set)   # judgment/reference node ids whose branch mattered
    missing_inputs: set = field(default_factory=set)     # schema gaps encountered
    inputs_demanded: set = field(default_factory=set)    # every input a visited node asked for
    max_depth: int = 0

    @property
    def determinate(self):
        return len(self.outcomes) == 1

    @property
    def discretion_exposed(self):
        """Indeterminate because of judgment/reference nodes (not just missing data)."""
        return len(self.outcomes) > 1 and bool(self.pivotal_judgment)


def reachable_outcomes(tree, facts):
    """Memoized: a node's reachable-outcome set is path-independent given the
    facts, so the walk is O(nodes) even when dozens of judgment nodes are
    indeterminate (the naive both-branches recursion is exponential).

    A visited indeterminate node is PIVOTAL iff its two branches lead to
    different outcome sets — an indeterminate node whose branches converge
    doesn't contribute discretion."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    run = Run()
    memo = {}

    def branch_of(node):
        """Which branches apply: 'true'/'false' for a decided objective node,
        None for an indeterminate one (judgment/reference/missing input)."""
        pred = node["predicate"]
        if pred["type"] != "objective":
            return None
        try:
            return bool(eval_expr(pred["expr"], facts))
        except Indeterminate as e:
            run.missing_inputs.add(str(e))
            return None

    def score_state(node):
        """For a score node: (score interval [lo, hi], has_judgment_slack,
        reachable targets). Objective items add their points or nothing;
        judgment (or missing-input) items widen the interval by their points.
        Every threshold band the interval touches is reachable — the
        identified-set semantics of a point system."""
        lo = hi = 0.0
        slack = False
        for item in node["score"]["items"]:
            pts = item["points"]
            if item["type"] == "objective" and "expr" in item:
                try:
                    if bool(eval_expr(item["expr"], facts)):
                        lo += pts
                        hi += pts
                    continue
                except Indeterminate as e:
                    run.missing_inputs.add(str(e))
            hi += pts
            if item["type"] == "judgment":
                slack = True
        targets = [t["target"] for t in node["score"]["thresholds"]
                   if t["min"] <= hi and lo <= t.get("max", float("inf"))]
        return (lo, hi), slack, targets

    def out_set(node_id):
        if node_id in memo:
            return memo[node_id] if memo[node_id] is not None else set()  # cycle guard
        node = nodes.get(node_id)
        if node is None:
            return set()
        memo[node_id] = None
        if "outcome" in node:
            s = {node["outcome"]["label"]}
        elif "score" in node:
            _, _, targets = score_state(node)
            s = set()
            for t in targets:
                s |= out_set(t)
        else:
            val = branch_of(node)
            if val is None:
                s = out_set(node["if_true"]) | out_set(node["if_false"])
            else:
                s = set(out_set(node["if_true" if val else "if_false"]))
        memo[node_id] = s
        return s

    run.outcomes = set(out_set(tree["root"]))

    # reachability walk for inputs_demanded and pivotality
    seen, frontier = set(), [tree["root"]]
    while frontier:
        nid = frontier.pop()
        if nid in seen or nid not in nodes:
            continue
        seen.add(nid)
        node = nodes[nid]
        if "outcome" in node:
            continue
        if "score" in node:
            for item in node["score"]["items"]:
                run.inputs_demanded.update(item.get("inputs", []))
            _, slack, targets = score_state(node)
            frontier += targets
            if slack and len({frozenset(out_set(t)) for t in targets}) > 1:
                run.pivotal_judgment.add(nid)
            continue
        pred = node["predicate"]
        run.inputs_demanded.update(pred.get("inputs", []))
        val = branch_of(node)
        if val is None:
            frontier += [node["if_true"], node["if_false"]]
            if pred["type"] != "objective" and out_set(node["if_true"]) != out_set(node["if_false"]):
                run.pivotal_judgment.add(nid)
        else:
            frontier.append(node["if_true" if val else "if_false"])
    run.max_depth = len(seen)
    return run


def burden_of_run(tree, run, priors):
    """Effort vector for the inputs this run actually demanded.

    Lower bound on the rule's ask for this case: only inputs attached to
    visited nodes count (path-dependence). Fields sharing an `acquisition`
    event are charged ONCE per event (one site inspection observes many
    facts); fields without an event are charged individually.
    """
    fields = {f["name"]: f for f in tree["input_schema"]["fields"]}
    total = {"hours": 0.0, "dollars": 0.0, "wait_days": 0.0, "trips": 0.0, "n_sensitive": 0}
    events_charged = set()
    for name in sorted(run.inputs_demanded):
        f = fields.get(name)
        if f is None:
            continue
        if f.get("sensitive"):
            total["n_sensitive"] += 1
        event = f.get("acquisition")
        if event is not None:
            if event in events_charged:
                continue
            events_charged.add(event)
        cls = priors["classes"].get(f.get("provenance_class", "a"), {})
        override = f.get("burden_override", {})
        for k in ("hours", "dollars", "wait_days", "trips"):
            total[k] += override.get(k, cls.get(k, 0))
    return total
