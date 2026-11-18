"""Independent target and admission checks for uncertain jurisdiction units."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import types

import numpy as np
import pytest
from numpy.polynomial.hermite import hermgauss
from scipy.special import betaln, expit, xlog1py, xlogy

from pipeline.procbench.process_structure.occupancy import Config, Evidence, fit, verify_source_bindings
from pipeline.procbench.process_structure.prediction import leave_jurisdiction_readings_out


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "runs/process_structure_20260921/calfresh_phase2/reproducibility_snapshot"


def ref(name, locator=None, *, digest=None):
    return {
        "path": f"source-free/{name}.json",
        "sha256": digest or hashlib.sha256(name.encode()).hexdigest(),
        "locator": locator or f"$.{name}",
    }


def resolved_row(jurisdiction, step, detected):
    unit = f"fixed-{jurisdiction}"
    scope = ref(f"scope-{jurisdiction}", f"$.threads.{jurisdiction}")
    return {
        "unit_id": unit,
        "dependence_group_id": unit,
        "jurisdiction_id": jurisdiction,
        "step_id": step,
        "source_type": "forum",
        "detected": detected,
        "reviewed_scope": True,
        "identity_scope_id": f"episode:{jurisdiction}",
        "identity_scope_reviewed": True,
        "identity_scope_refs": [scope],
        "evidence_refs": [ref(f"fixed-{jurisdiction}-{step}")],
    }


def uncertain_unit(name="u", scope_locator="$.threads.u", outcomes=(True, False),
                   candidates=(('A', 3.0), ('B', 2.0)), *, shared_scope_digest=None):
    return {
        "unit_id": name,
        "dependence_group_id": name,
        "source_type": "forum",
        "identity_reviewed": True,
        "identity_scope_id": f"episode:{name}",
        "identity_scope_reviewed": True,
        "identity_scope_refs": [ref(
            f"scope-{name}", scope_locator, digest=shared_scope_digest)],
        "candidate_scope_complete": True,
        "assignment_prior_basis": "Source-free bounded two-county context.",
        "assignment_prior_kind": "reviewed_candidate_weights",
        "assignment_prior_refs": [ref(f"prior-{name}")],
        "candidates": [
            {"jurisdiction_id": jurisdiction, "prior_weight": weight}
            for jurisdiction, weight in candidates
        ],
        "reviewed_step_ids": ["s1", "s2"],
        "readings": [
            {
                "step_id": step,
                "detected": outcome,
                "reviewed_scope": True,
                "evidence_refs": [ref(f"reading-{name}-{step}")],
            }
            for step, outcome in zip(("s1", "s2"), outcomes)
        ],
    }


def fixture(*, identity=True):
    data = {
        "schema_version": "process-occupancy-evidence/2" if identity else "process-occupancy-evidence/1",
        "scope": "source-free two-county two-step identity fixture",
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Complete source-free checklists; no real claims.",
        "jurisdictions": ["A", "B"],
        "steps": ["s1", "s2"],
        "source_types": ["forum"],
        "source_models": {
            "forum": {"detection_beta": [2.0, 3.0], "false_positive_probability": 0.1}
        },
        "observations": [
            resolved_row("A", "s1", True),
            resolved_row("A", "s2", False),
            resolved_row("B", "s1", False),
            resolved_row("B", "s2", True),
        ],
        "known_presence": [],
    }
    if identity:
        data["uncertain_jurisdiction_units"] = [uncertain_unit()]
    return data


def test_identity_prior_normalization_cannot_silently_drop_a_candidate():
    data = fixture()
    data['uncertain_jurisdiction_units'] = [uncertain_unit(
        candidates=(('A', 1.e308), ('B', np.nextafter(0., 1.))))]
    with pytest.raises(ValueError, match='normalization underflow'):
        Evidence(data)
    data['uncertain_jurisdiction_units'] = [uncertain_unit(
        candidates=(('A', 1.e308), ('B', 1.e308)))]
    np.testing.assert_array_equal(Evidence(data).identity.priors, [[.5, .5]])


def test_explicit_reviewed_subset_does_not_turn_unread_new_steps_into_nondetections():
    data = fixture()
    unit = data['uncertain_jurisdiction_units'][0]
    unit.update(reading_scope_kind='reviewed_fixed_subset', step_scope_reviewed=True,
                step_scope_rationale='Only s1 was covered by this fixed source-free checklist.',
                step_scope_refs=[ref('fixed-checklist-scope')], reviewed_step_ids=['s1'])
    unit['readings'] = unit['readings'][:1]
    evidence = Evidence(data)
    assert evidence.identity.positive[0, 0, 0] == 1
    assert evidence.identity.positive[0, 1, 0] == 0
    assert evidence.identity.negative[0, 1, 0] == 0
    assert unit['step_scope_refs'][0] in evidence.identity.refs
    presence = np.array([[1, 0], [0, 1]])
    detection = np.array([[.6], [.4]])
    expected = np.array([[3 * .6, 2 * .1]]) / (3 * .6 + 2 * .1)
    np.testing.assert_allclose(evidence.identity.conditional_probabilities(presence, detection), expected)
    presence[:, 1] = 1 - presence[:, 1]
    detection[1] = .99
    np.testing.assert_allclose(evidence.identity.conditional_probabilities(presence, detection), expected)
    for key in ['step_scope_rationale', 'step_scope_refs', 'step_scope_reviewed']:
        broken = copy.deepcopy(data)
        del broken['uncertain_jurisdiction_units'][0][key]
        with pytest.raises(ValueError):
            Evidence(broken)
    broken = copy.deepcopy(data)
    broken['uncertain_jurisdiction_units'][0]['reading_scope_kind'] = 'complete_fixed_universe'
    with pytest.raises(ValueError, match='complete reviewed fixed step checklist'):
        Evidence(broken)


def test_partial_checklist_cannot_smuggle_readings_outside_its_declared_scope():
    data = fixture()
    unit = data['uncertain_jurisdiction_units'][0]
    unit.update(reading_scope_kind='reviewed_fixed_subset', step_scope_reviewed=True,
                step_scope_rationale='Fixed s1-only scope.',
                step_scope_refs=[ref('fixed-checklist-scope')], reviewed_step_ids=['s1'])
    unit['readings'] = unit['readings'][1:]
    with pytest.raises(ValueError, match='cover the complete reviewed scope'):
        Evidence(data)


def exact_joint_oracle(data, config, order=14):
    """Enumerate a,z; integrate shared step p exactly and Gaussian effects by GH."""
    evidence = Evidence(data)
    assert len(evidence.identity.units) == 1
    assert config.jurisdiction_scale_log_sd == 0
    nodes, weights = hermgauss(order)
    grids = np.meshgrid(*([np.sqrt(2.0) * nodes] * 4), indexing="ij")
    wg = np.meshgrid(*([weights] * 4), indexing="ij")
    alpha = np.stack(grids[:2], axis=-1).reshape(-1, 2)
    county = np.stack(grids[2:], axis=-1).reshape(-1, 2)
    quadrature_weight = np.prod(np.stack(wg, axis=-1), axis=-1).reshape(-1) / np.pi**2
    logits = (config.step_logit_sd * alpha[:, None, :]
              + config.jurisdiction_scale_median * county[:, :, None])
    q = expit(logits)

    prior_z = {}
    for bits in itertools.product((0, 1), repeat=4):
        z = np.array(bits, dtype=int).reshape(2, 2)
        probability = np.prod(np.where(z[None, :, :] == 1, q, 1-q), axis=(1, 2))
        prior_z[bits] = float(np.sum(quadrature_weight * probability))
    assert sum(prior_z.values()) == pytest.approx(1.0, abs=2e-12)

    alpha0, beta0 = evidence.a[:, 0], evidence.b[:, 0]
    false_positive = evidence.false_positive[0]
    masses, p_numerator = {}, np.zeros(2)
    for assignment in range(2):
        positive = evidence.identity.base_positive.copy()
        negative = evidence.identity.base_negative.copy()
        positive[assignment] += evidence.identity.positive[0]
        negative[assignment] += evidence.identity.negative[0]
        for bits, z_prior in prior_z.items():
            z = np.array(bits, dtype=int).reshape(2, 2)
            likelihood = 1.0
            conditional_p_mean = np.empty(2)
            for s in range(2):
                present = z[:, s].astype(bool)
                n1 = int(positive[present, s, 0].sum())
                n0 = int(negative[present, s, 0].sum())
                f1 = int(positive[~present, s, 0].sum())
                f0 = int(negative[~present, s, 0].sum())
                likelihood *= np.exp(
                    betaln(alpha0[s] + n1, beta0[s] + n0)
                    - betaln(alpha0[s], beta0[s])
                ) * false_positive**f1 * (1-false_positive)**f0
                conditional_p_mean[s] = ((alpha0[s] + n1)
                                          / (alpha0[s] + beta0[s] + n1 + n0))
            key = (assignment,) + bits
            mass = evidence.identity.priors[0, assignment] * z_prior * likelihood
            masses[key] = mass
            p_numerator += mass * conditional_p_mean
    normalizer = sum(masses.values())
    return ({key: value / normalizer for key, value in masses.items()},
            p_numerator / normalizer)


def test_identity_conditional_is_one_joint_assignment_across_all_steps():
    evidence = Evidence(fixture())
    z = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    p = np.array([[0.75], [0.6]])
    actual = evidence.identity.conditional_probabilities(z, p)[0]
    report = np.where(z[:, :, None], p, evidence.false_positive)
    likelihood = np.array([
        np.sum(xlogy(evidence.identity.positive[0], report[j])
               + xlog1py(evidence.identity.negative[0], -report[j]))
        for j in range(2)
    ])
    expected = evidence.identity.priors[0] * np.exp(likelihood-likelihood.max())
    expected /= expected.sum()
    np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-15)

    # Per-step assignments would produce four states; this contract has one
    # categorical draw for the complete two-step unit.
    draws = np.array([evidence.identity.sample([actual], np.random.default_rng(i))[0]
                      for i in range(100)])
    assert set(draws) <= {0, 1}


def test_assignment_rebuilds_counts_once_and_restores_the_previous_county():
    evidence = Evidence(fixture())
    base_positive = evidence.identity.base_positive.copy()
    base_negative = evidence.identity.base_negative.copy()
    evidence.identity.set_assignments(np.array([0], dtype=np.int32))
    np.testing.assert_array_equal(
        evidence.positive[0], base_positive[0] + evidence.identity.positive[0])
    np.testing.assert_array_equal(
        evidence.negative[0], base_negative[0] + evidence.identity.negative[0])
    evidence.identity.set_assignments(np.array([1], dtype=np.int32))
    np.testing.assert_array_equal(evidence.positive[0], base_positive[0])
    np.testing.assert_array_equal(evidence.negative[0], base_negative[0])
    np.testing.assert_array_equal(
        evidence.positive[1], base_positive[1] + evidence.identity.positive[0])
    np.testing.assert_array_equal(
        evidence.negative[1], base_negative[1] + evidence.identity.negative[0])


@pytest.mark.parametrize("mutation,match", [
    ("contract1", "contract /2"),
    ("missing_step", "complete reviewed fixed step checklist"),
    ("duplicate_step", "duplicate, unresolved or unreviewed"),
    ("missing_prior_refs", "evidence_refs"),
    ("unequal_symmetric", "symmetric identity prior"),
    ("boolean_weight", "finite and positive"),
])
def test_incomplete_or_unbound_identity_contract_fails_closed(mutation, match):
    data = fixture()
    unit = data["uncertain_jurisdiction_units"][0]
    if mutation == "contract1":
        data["schema_version"] = "process-occupancy-evidence/1"
    elif mutation == "missing_step":
        unit["readings"].pop()
    elif mutation == "duplicate_step":
        unit["readings"][1]["step_id"] = "s1"
    elif mutation == "missing_prior_refs":
        del unit["assignment_prior_refs"]
    elif mutation == "unequal_symmetric":
        unit["assignment_prior_kind"] = "symmetric_bounded_context"
    else:
        unit["candidates"][0]["prior_weight"] = True
    with pytest.raises((ValueError, TypeError), match=match):
        Evidence(data)


def test_canonical_episode_overlap_is_rejected_but_distinct_bulk_roots_are_allowed():
    digest = hashlib.sha256(b"one bulk fixture").hexdigest()
    data = fixture()
    first = uncertain_unit("u1", "$.threads[0]", shared_scope_digest=digest)
    overlap = uncertain_unit("u2", "$.threads[0].comments[2]", shared_scope_digest=digest)
    data["uncertain_jurisdiction_units"] = [first, overlap]
    with pytest.raises(ValueError, match="overlaps"):
        Evidence(data)

    distinct = uncertain_unit("u2", "$.threads[1]", shared_scope_digest=digest)
    data["uncertain_jurisdiction_units"] = [first, distinct]
    evidence = Evidence(data)
    assert len(evidence.identity.units) == 2


def test_identity_context_bytes_are_verified_and_old_holdout_fails_closed(tmp_path):
    source = tmp_path / "captured.json"
    source.write_text('{"source-free": true}\n')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    data = fixture()
    for row in data["observations"]:
        for key in ("evidence_refs", "identity_scope_refs"):
            for item in row[key]:
                item["path"], item["sha256"] = source.name, digest
    unit = data["uncertain_jurisdiction_units"][0]
    scope_source = tmp_path / 'reading_scope.json'
    scope_source.write_text('{"reviewed_steps": ["s1", "s2"]}\n')
    unit['step_scope_refs'] = [dict(path=scope_source.name, locator='$.reviewed_steps',
        sha256=hashlib.sha256(scope_source.read_bytes()).hexdigest())]
    for key in ("identity_scope_refs", "assignment_prior_refs"):
        for item in unit[key]:
            item["path"], item["sha256"] = source.name, digest
    for row in unit["readings"]:
        for item in row["evidence_refs"]:
            item["path"], item["sha256"] = source.name, digest
    Evidence(data)
    assert verify_source_bindings(data, tmp_path) == 2
    with pytest.raises(ValueError, match="Uncertain identity holdouts"):
        leave_jurisdiction_readings_out(data, "A", source_root=tmp_path)
    scope_source.write_text('{"reviewed_steps": ["s1"]}\n')
    with pytest.raises(ValueError, match="Changed source binding"):
        verify_source_bindings(data, tmp_path)


def test_two_county_two_step_sampler_matches_shared_beta_gaussian_oracle():
    data = fixture()
    config = Config(chains=4, warmup=1000, draws=4000, seed=2026092191,
                    step_logit_sd=0.8, jurisdiction_scale_median=0.6,
                    jurisdiction_scale_log_sd=0.0,
                    hierarchy_update="collapsed", hierarchy_block_size=0)
    expected, expected_p = exact_joint_oracle(data, config, order=14)
    result, arrays = fit(data, config)

    assignments = arrays["jurisdiction_assignment"].reshape(-1)
    presence = arrays["presence"].reshape(-1, 4)
    observed = Counter((int(a), *map(int, z)) for a, z in zip(assignments, presence))
    n = len(assignments)
    empirical = {key: observed[key] / n for key in expected}
    assert max(abs(empirical[key]-expected[key]) for key in expected) < 0.025
    assert sum(abs(empirical[key]-expected[key]) for key in expected) / 2 < 0.075
    np.testing.assert_allclose(arrays["detection"].mean(axis=(0, 1))[:, 0],
                               expected_p, rtol=0, atol=0.02)

    expected_assignment = np.array([
        sum(value for key, value in expected.items() if key[0] == assignment)
        for assignment in range(2)
    ])
    sampled_assignment = np.bincount(assignments, minlength=2) / n
    rb_assignment = arrays["jurisdiction_assignment_probability"].mean(axis=(0, 1))[0]
    np.testing.assert_allclose(sampled_assignment, expected_assignment, rtol=0, atol=0.02)
    np.testing.assert_allclose(rb_assignment, expected_assignment, rtol=0, atol=0.02)
    assert any(name.startswith("jurisdiction_assignment_indicator:u:")
               for name in result["diagnostics"])


def _load_archived_occupancy():
    """Load the frozen pre-identity module under an isolated package name."""
    package_paths = {
        "_occupancy_archive": ARCHIVE / "pipeline",
        "_occupancy_archive.procbench": ARCHIVE / "pipeline/procbench",
        "_occupancy_archive.procbench.process_structure": ARCHIVE / "pipeline/procbench/process_structure",
    }
    for name, path in package_paths.items():
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    name = "_occupancy_archive.procbench.process_structure.occupancy"
    spec = importlib.util.spec_from_file_location(
        name, ARCHIVE / "pipeline/procbench/process_structure/occupancy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_contract1_default_draws_are_identical_to_archived_preidentity_sampler():
    archived = _load_archived_occupancy()
    data = fixture(identity=False)
    kwargs = dict(chains=2, warmup=12, draws=16, seed=8123,
                  jurisdiction_scale_log_sd=0, hierarchy_update="collapsed",
                  hierarchy_block_size=1)
    current_result, current_arrays = fit(data, Config(**kwargs))
    old_result, old_arrays = archived.fit(data, archived.Config(**kwargs))
    assert current_result == old_result
    assert set(current_arrays) == set(old_arrays)
    for key in current_arrays:
        np.testing.assert_array_equal(current_arrays[key], old_arrays[key])


def test_identity_support_report_is_strict_json_serializable():
    """Report-only boundary; this does not change the frozen sampler target."""
    report = Evidence(fixture()).support_report()
    value = report["positive_only_opportunity_frame"]
    assert type(value) is bool
    assert json.loads(json.dumps(report, allow_nan=False)) == report
