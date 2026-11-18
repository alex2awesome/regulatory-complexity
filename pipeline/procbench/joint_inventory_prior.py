"""Optional finite *joint* inventory prior for V6's existing route vectors.

The external occupancy posterior may induce dependence between jurisdictions.
Replacing it by independent program-wise route weights loses that dependence.
This object preserves a finite joint support and supplies one exact Gibbs block.
It does not infer ordering, turn availability into case participation, or decide
whether the occupancy evidence is scientifically adequate.
"""
from __future__ import annotations

import math
from copy import deepcopy

import numpy as np
from scipy.special import logsumexp


class JointInventoryPrior:
    def __init__(self, declaration, programs):
        if declaration.get("schema_version") != "v6-joint-inventory-prior/1":
            raise ValueError("Unknown joint inventory prior contract")
        ids = [p["id"] for p in programs]
        if declaration.get("program_ids") != ids:
            raise ValueError("Joint inventory prior must cover all programs in declared model order")
        if (declaration.get("feedback_policy") != "downstream_evidence_updates_joint_inventory"
                or declaration.get("evidence_partition_reviewed") is not True
                or not isinstance(declaration.get("evidence_partition_note"), str)
                or not declaration["evidence_partition_note"].strip()
                or declaration.get("route_semantics_reviewed") is not True):
            raise ValueError("Declare reviewed evidence partition, route meaning, and structural feedback policy")
        # No opaque silent multiplication of two distinct priors.
        if any(route["prior_weight"] != 1. for p in programs for route in p["routes"]):
            raise ValueError("Joint weights replace marginal route priors; use unit per-route placeholder weights")
        hypotheses = declaration.get("hypotheses")
        if not isinstance(hypotheses, list) or not hypotheses:
            raise ValueError("Joint inventory prior needs explicit finite nonempty support")
        route_maps = [{r["id"]: i for i, r in enumerate(p["routes"])} for p in programs]
        names, states, weights = [], [], []
        for h in hypotheses:
            name, weight, routes = h.get("id"), h.get("prior_weight"), h.get("route_ids")
            if (not isinstance(name, str) or not name.strip() or name in names
                    or isinstance(weight, bool) or not isinstance(weight, (int, float))
                    or not math.isfinite(weight) or weight <= 0
                    or not isinstance(routes, list) or len(routes) != len(ids)):
                raise ValueError("Joint hypotheses need distinct names, positive finite weights and a complete route vector")
            try:
                state = tuple(mapping[r] for mapping, r in zip(route_maps, routes))
            except (KeyError, TypeError) as exc:
                raise ValueError("Joint hypothesis names an unsupported route") from exc
            if state in states:
                raise ValueError("Aggregate duplicate joint route vectors before supplying weights")
            names.append(name)
            weights.append(weight)
            states.append(state)
        self.names = names
        self.states = np.asarray(states, dtype=int)
        if any(set(self.states[:, pi]) != set(range(len(p["routes"]))) for pi, p in enumerate(programs)):
            raise ValueError("Joint prior must represent every declared program route; remove unsupported routes explicitly")
        weights = np.asarray(weights, dtype=float)
        self.probabilities = weights/weights.max()
        self.probabilities /= self.probabilities.sum()
        if np.any(self.probabilities == 0):
            raise ValueError("Joint inventory weights lose positive support in floating-point normalization")
        self.log_probabilities = np.log(self.probabilities)
        self.lookup = {s: i for i, s in enumerate(states)}
        self.declaration = deepcopy(declaration)

    def index(self, structure):
        value = np.asarray(structure)
        if (value.shape != (self.states.shape[1],)
                or not np.issubdtype(value.dtype, np.integer)):
            raise ValueError("Joint inventory route vector must have one integer index per program")
        key = tuple(value)
        if key not in self.lookup:
            raise ValueError("Route vector is outside the declared joint inventory support")
        return self.lookup[key]

    def draw_prior(self, rng):
        return self.states[rng.choice(len(self.states), p=self.probabilities)].copy()

    def conditional(self, model, continuous_state):
        """Evaluate each unique program/route factor once, then combine jointly.

        Conditional on continuous hierarchy coordinates the program likelihood
        factors are independent, but their structural prior need not factor.
        Missing support has zero mass, never a renormalized independent route.
        """
        likelihood = np.zeros(len(self.states))
        calls = 0
        for pi in range(self.states.shape[1]):
            for ri in np.unique(self.states[:, pi]):
                proposal = self.states[np.flatnonzero(self.states[:, pi] == ri)[0]]
                value = model.log_likelihood(continuous_state, proposal, _program_index=pi)
                likelihood[self.states[:, pi] == ri] += value
                calls += 1
        weights = self.log_probabilities + likelihood
        normalizer = logsumexp(weights)
        if not np.isfinite(normalizer):
            raise ValueError("No supported joint inventory has finite likelihood at this continuous state")
        return np.exp(weights-normalizer), likelihood, calls

    def update(self, model, continuous_state, rng):
        probabilities, likelihood, calls = self.conditional(model, continuous_state)
        i = rng.choice(len(self.states), p=probabilities)
        return self.states[i].copy(), float(likelihood[i]), calls


def empirical_joint_inventory(joint_presence, jurisdictions, step_ids):
    """Compress full aligned inventories without dropping any *supplied draws*.

    This is NOT a route compiler. Returned draw memberships allow attaching the
    same upstream hierarchy/identity draw after a downstream inventory update.
    Mapping available actions to executable case paths still requires review.
    """
    z = np.asarray(joint_presence)
    if (z.ndim != 4 or z.shape[2:] != (len(jurisdictions), len(step_ids))
            or min(z.shape) < 1 or not np.isin(z, [0, 1]).all()
            or len(set(jurisdictions)) != len(jurisdictions) or len(set(step_ids)) != len(step_ids)):
        raise ValueError("Need aligned chains x draws x jurisdictions x binary steps")
    flat = z.reshape(-1, z.shape[2]*z.shape[3])
    unique, inverse, counts = np.unique(flat, axis=0, return_inverse=True, return_counts=True)
    return dict(jurisdictions=list(jurisdictions), steps=list(step_ids),
                joint_inventories=unique.reshape(-1, z.shape[2], z.shape[3]),
                probabilities=counts/counts.sum(),
                upstream_draw_to_inventory=inverse.reshape(z.shape[:2]),
                chain_draw_shape=z.shape[:2], retained_mass=1.,
                retained_mass_scope="supplied_empirical_draw_multiset_not_continuous_posterior",
                route_semantics_reviewed=False)


def _inventory_memberships(upstream_draw_to_inventory, downstream_inventory):
    membership, selected = np.asarray(upstream_draw_to_inventory), np.asarray(downstream_inventory)
    if (membership.ndim != 2 or selected.ndim != 2 or not membership.size or not selected.size
            or not np.issubdtype(membership.dtype, np.integer)
            or not np.issubdtype(selected.dtype, np.integer)
            or np.any(membership < 0) or np.any(selected < 0)):
        raise ValueError("Need nonempty chains-by-draws integer inventory memberships")
    unique = np.unique(membership)
    if not np.array_equal(unique, np.arange(len(unique))) or np.any(selected >= len(unique)):
        raise ValueError("Inventory memberships must cover contiguous support and every downstream index")
    return membership, selected, np.bincount(membership.ravel(), minlength=len(unique))


def replay_upstream_indices(upstream_draw_to_inventory, downstream_inventory, rng):
    """Link each downstream draw to ONE aligned original upstream draw.

    Valid only when the new likelihood depends on upstream latent variables
    through the inventory, not on their other coordinates. Conditional on that
    inventory the empirical upstream conditional is uniform over its members.
    Apply these same returned indices to ALL upstream arrays (hierarchy,
    detection, identity, presence). Never resample each field independently.
    This is exact for the finite empirical prior, not its continuous population.
    """
    membership, selected, counts = _inventory_memberships(
        upstream_draw_to_inventory, downstream_inventory)
    ordered = np.argsort(membership.ravel(), kind="stable")
    starts = np.r_[0, np.cumsum(counts)[:-1]]
    positions = starts[selected] + rng.integers(0, counts[selected], size=selected.shape)
    return ordered[positions]


def empirical_bridge_report(upstream_draw_to_inventory, downstream_inventory):
    """Finite-support reweighting diagnostics, separate from MCMC convergence.

    Each upstream draw has posterior weight Q(h)/n(h); weight ESS ignores
    upstream autocorrelation and is only an upper bound on effective support.
    Even high support cannot certify adequate coverage of unseen inventories.
    """
    membership, selected, counts = _inventory_memberships(
        upstream_draw_to_inventory, downstream_inventory)
    posterior = np.bincount(selected.ravel(), minlength=len(counts))/selected.size
    prior = counts/membership.size
    positive = posterior > 0
    ess = float(1./np.sum(posterior**2/counts))
    return dict(upstream_draw_count=int(membership.size),
        supplied_joint_inventory_count=len(counts),
        downstream_visited_joint_inventory_count=int(positive.sum()),
        upstream_mass_on_unvisited_inventories=float(prior[~positive].sum()),
        maximum_reweighting_ratio=float(np.max(posterior/prior)),
        upstream_particle_weight_ess=ess,
        upstream_particle_weight_ess_fraction=ess/membership.size,
        qualification="Empirical support diagnostic, not MCMC ESS, no bound on unseen posterior mass or transportability; upstream serial dependence and finite-sample error remain.")
