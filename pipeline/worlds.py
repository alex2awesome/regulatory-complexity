"""Latent worlds: the synthetic stimuli of the looseness instrument.

A world spec (schemas/latent_world.schema.json) defines, for one judgment
predicate, a latent severity axis (or axes) with anchored descriptions, plus
realistic context fields. Cases are generated as SWEEPS — dense coverage of
the axis — because the instrument is psychophysics, not training: probes must
span the borderline region, they need not match reality's density. Realism
enters only at the weighting step (population_sample), whose distribution is
a placeholder prior until calibrated to real data.

Rendering (theta -> vignette) has two backends: an offline template renderer
(deterministic, for tests and dry runs) and an LLM renderer (prompt
06_render_vignette.md) for realistic inspector-notes prose. Vignettes must
never leak theta numerically.
"""

import json
import pathlib
import random


def load_world(path):
    return json.loads(pathlib.Path(path).read_text())


def sweep(world, n=40, jitter=0.0, seed=0):
    """Grid sweep over each latent axis (crossed with sampled context)."""
    rng = random.Random(seed)
    axes = world["axes"]
    cases = []
    for i in range(n):
        theta = {}
        for ax in axes:
            lo, hi = ax.get("range", [0.0, 1.0])
            t = lo + (hi - lo) * (i / max(n - 1, 1))
            if jitter:
                t = min(hi, max(lo, t + rng.gauss(0, jitter)))
            theta[ax["name"]] = round(t, 4)
        context = {
            f["name"]: rng.choice(f["values"])
            for f in world.get("context_fields", [])
        }
        cases.append({"case_id": f"{world['world_id']}_{i:04d}", "theta": theta, "context": context})
    return cases


def population_sample(world, n=1000, seed=0):
    """Sample thetas from the world's population prior (for band-mass weighting)."""
    rng = random.Random(seed)
    pop = world.get("population", {"distribution": "uniform"})
    dist = pop.get("distribution", "uniform")
    axis = world["axes"][0]
    lo, hi = axis.get("range", [0.0, 1.0])
    out = []
    for _ in range(n):
        if dist == "beta":
            t = rng.betavariate(pop.get("alpha", 2), pop.get("beta", 2))
        elif dist == "uniform":
            t = rng.random()
        else:
            raise ValueError(f"unknown population distribution: {dist}")
        out.append(lo + (hi - lo) * t)
    return out


def _bracketing_anchors(axis, t):
    anchors = sorted(axis["anchors"], key=lambda a: a["theta"])
    below = max((a for a in anchors if a["theta"] <= t), key=lambda a: a["theta"], default=anchors[0])
    above = min((a for a in anchors if a["theta"] >= t), key=lambda a: a["theta"], default=anchors[-1])
    return below, above


def template_render(world, case):
    """Deterministic offline renderer: nearest-anchor description + context.
    Crude by design — use the LLM renderer for realistic vignettes."""
    parts = []
    for ax in world["axes"]:
        t = case["theta"][ax["name"]]
        below, above = _bracketing_anchors(ax, t)
        nearest = below if abs(below["theta"] - t) <= abs(above["theta"] - t) else above
        parts.append(nearest["description"])
    ctx = "; ".join(f"{k}: {v}" for k, v in case["context"].items())
    return f"Unit context: {ctx}. Observed conditions: " + " ".join(parts)


def render_prompt_extra(world, case):
    """The `extra` block handed to the LLM renderer for one case."""
    blocks = []
    for ax in world["axes"]:
        t = case["theta"][ax["name"]]
        below, above = _bracketing_anchors(ax, t)
        frac = 0.0 if above["theta"] == below["theta"] else (t - below["theta"]) / (above["theta"] - below["theta"])
        blocks.append(
            f"Axis '{ax['name']}': the unit's true condition sits {frac:.0%} of the way between:\n"
            f"  LOWER anchor ({below['theta']}): {below['description']}\n"
            f"  UPPER anchor ({above['theta']}): {above['description']}"
        )
    ctx = json.dumps(case["context"])
    return "\n".join(blocks) + f"\nContext fields (weave in naturally): {ctx}"
