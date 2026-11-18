from dataclasses import asdict, replace
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.reconcile_evidence import digest, write
from pipeline.procbench.refine_visit_predictions import main, prepare_refinement


def saved_run(tmp_path, *, population_summary=False, selection=0., finite_cohort=False):
    data = dict(programs=[dict(id='P', routes=[dict(id='route', prior_weight=1.,
        operations=[dict(id='review', actor_id='A', actor_role='agency', task_type='review',
                         markers=['decision'], payer_work=False, agency_work=True)],
        blocks=[dict(id='review', operations=['review'])])], observations=[dict(
            id='time', case_id=None if population_summary else 'case', source_family='source',
            sampling='unselected', statistic='median' if population_summary else 'individual',
            lower=4., upper=9., operators=[dict(basis='whole_case_clock', start='process_start',
                                              end='initial_decision')], operator_weights=[1.])])])
    if finite_cohort:
        from test_cohort_quantiles import cohort_fixture
        data['programs'][0].update(observations=[],quantile_cohorts=[cohort_fixture()])
    cfg = Config(chains=1, draws=8, warmup=0, population_size=16, selection_sd=selection)
    model = VisitHierarchy(data, cfg)
    z = np.random.default_rng(78).normal(scale=.1, size=(1, 8, model.layout.size))
    structures = np.zeros((1, 8, 1), dtype=int)
    ll = np.array([[model.log_likelihood(zz, [0]) for zz in z[0]]])
    root, input_path = tmp_path / 'run', tmp_path / 'input.json'
    write(input_path, data)
    write(root / 'data.json', data)
    write(root / 'posterior.json', dict(numerically_usable=False))
    np.savez_compressed(root / 'draws.npz', z=z, structures=structures, log_likelihood=ll)
    write(root / 'manifest.json', dict(config=asdict(cfg), completed_utc='test',
        posterior_sha256=digest((root / 'posterior.json').read_bytes()),
        input_sha256={str(input_path): digest(input_path.read_bytes())}))
    return root


def test_refinement_preserves_joint_samples_and_individual_likelihood(tmp_path):
    root = saved_run(tmp_path)
    original, model, z, routes, ll, checks = prepare_refinement(root, 64)
    assert model.cfg == replace(Config(**original['config']), population_size=64)
    assert checks['saved_likelihood_checks'] == 8
    assert checks['saved_likelihood_max_difference'] == 0.
    with np.load(root / 'draws.npz') as raw:
        for actual, name in ((z, 'z'), (routes, 'structures'), (ll, 'log_likelihood')):
            np.testing.assert_array_equal(actual, raw[name])


@pytest.mark.parametrize('population_summary,selection', [(True, 0.), (False, .5)])
def test_refinement_rejects_population_likelihood_terms(tmp_path, population_summary, selection):
    root = saved_run(tmp_path, population_summary=population_summary, selection=selection)
    with pytest.raises(ValueError, match='Population integration'):
        prepare_refinement(root, 64)


def test_refinement_cannot_change_a_finite_cohort_target_without_refitting(tmp_path):
    root=saved_run(tmp_path,finite_cohort=True)
    with pytest.raises(ValueError,match='Population integration'):
        prepare_refinement(root,64)


@pytest.mark.parametrize('size', [8, 16, 17, 48])
def test_refinement_requires_larger_power_of_two_resolution(tmp_path, size):
    with pytest.raises(ValueError, match='power-of-two'):
        prepare_refinement(saved_run(tmp_path), size)


def test_refinement_rejects_changed_input_or_saved_data(tmp_path):
    root = saved_run(tmp_path)
    data = json.loads((root / 'data.json').read_text())
    data['programs'][0]['observations'][0]['lower'] = 5.
    write(root / 'data.json', data)
    with pytest.raises(ValueError, match='Saved data disagree'):
        prepare_refinement(root, 64)
    write(tmp_path / 'input.json', data)
    with pytest.raises(ValueError, match='original inference input changed'):
        prepare_refinement(root, 64)


def test_refinement_rejects_changed_report_or_likelihood(tmp_path):
    root = saved_run(tmp_path)
    with np.load(root / 'draws.npz') as raw:
        z, structures, ll = raw['z'], raw['structures'], raw['log_likelihood']
    np.savez_compressed(root / 'draws.npz', z=z, structures=structures, log_likelihood=ll + 1.)
    with pytest.raises(ValueError, match='Saved likelihood changed'):
        prepare_refinement(root, 64)
    write(root / 'posterior.json', dict(changed=True))
    with pytest.raises(ValueError, match='completed, unchanged'):
        prepare_refinement(root, 64)


def test_cli_preserves_failed_fit_and_draw_file_without_resampling(tmp_path):
    root = saved_run(tmp_path)
    previous = (root / 'posterior.json').read_bytes()
    out = tmp_path / 'refined'
    main(['--run', str(root), '--out', str(out), '--population-size', '64'])
    assert (root / 'posterior.json').read_bytes() == previous
    assert (root / 'draws.npz').read_bytes() == (out / 'draws.npz').read_bytes()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['mcmc_draws_added'] == 0
    assert manifest['prediction_resolution_only'] is True
    assert manifest['completed_utc']
    assert not json.loads((out / 'posterior.json').read_text())['numerically_usable']
    with pytest.raises(ValueError, match='fresh output'):
        main(['--run', str(root), '--out', str(out), '--population-size', '64'])
