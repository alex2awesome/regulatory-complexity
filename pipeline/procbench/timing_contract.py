"""Declared timing estimands; equal files alone do not make equal targets."""

INITIAL_POPULATION_MEDIAN = dict(
    start='beginning_preparation_or_filing', end='initial_decision',
    unit='calendar_days', functional='population_median',
)
LEGACY_SUMMARY_MEDIAN = dict(
    start='beginning_preparation_or_filing', end='latest_recorded_decision',
    unit='calendar_days', functional='observed_finally_decided_uncensored_cohort_median',
)


def verify_declared_initial_target(manifest):
    """Old v5 manifests predate this field; their fixed implementation is known.

    Only the v5 comparator uses this fallback. New declared targets must agree;
    this function must not be used to guess the target of an arbitrary estimator.
    """
    current = manifest
    while 'timing_target' not in current and isinstance(current.get('base_manifest'), dict):
        current = current['base_manifest']
    target = current.get('timing_target', INITIAL_POPULATION_MEDIAN)
    if target != INITIAL_POPULATION_MEDIAN:
        raise ValueError('Declared estimator target differs from the v5 initial-decision target')
    return dict(target)
