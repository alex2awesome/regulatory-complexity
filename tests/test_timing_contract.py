import pytest

from pipeline.procbench.compare_process_measurement import main
from pipeline.procbench.timing_contract import INITIAL_POPULATION_MEDIAN, LEGACY_SUMMARY_MEDIAN, verify_declared_initial_target


def test_legacy_clock_mismatch_requires_explicit_acknowledgment_before_any_truth_read(tmp_path):
    with pytest.raises(ValueError, match='allow-legacy-clock-mismatch'):
        main(['--runs', str(tmp_path/'nonexistent_fit'), '--baseline-root', str(tmp_path/'no_baseline'),
              '--world', str(tmp_path/'no_world'), '--out', str(tmp_path/'output')])
    assert not (tmp_path/'output').exists()


def test_initial_target_is_preserved_through_unchanged_target_extensions():
    fit = dict(base_manifest=dict(timing_target=dict(INITIAL_POPULATION_MEDIAN)))
    assert verify_declared_initial_target(fit) == INITIAL_POPULATION_MEDIAN
    fit['base_manifest']['timing_target'] = dict(LEGACY_SUMMARY_MEDIAN)
    with pytest.raises(ValueError, match='Declared estimator target differs'):
        verify_declared_initial_target(fit)


def test_known_legacy_v5_manifest_fallback_does_not_mutate_it():
    old = dict(base_manifest=dict(config={'old': True}))
    target = verify_declared_initial_target(old)
    target['end'] = 'changed'
    assert 'timing_target' not in old['base_manifest']
    assert verify_declared_initial_target(old)['end'] == 'initial_decision'
