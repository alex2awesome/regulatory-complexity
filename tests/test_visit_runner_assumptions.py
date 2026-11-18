"""Configured mechanical experiments use the shared immutable V6 runner."""
import json

import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config
from pipeline.procbench.run_visit_hierarchy import SENSITIVITY_FIELDS, main
from test_analytic_phase import phase_data


def test_explicit_development_assumptions_are_saved_in_preflight(tmp_path, capsys):
    path = tmp_path / 'data.json'
    path.write_text(json.dumps(phase_data()))
    out = tmp_path / 'preflight'
    values = dict(elapsed_prior_median=20., location_sd=1., task_sd=0.,
                  report_sd=.20, contamination=0., unknown_n_report_sd_floor=.20,
                  agency_sd=.5, operation_sd=.25, source_sd=.3, common_case_sd=.1,
                  case_log_sd_median=.8, case_log_sd_prior=.5)
    argv = ['--data', str(path), '--out', str(out), '--preflight',
            '--observed-channels-only', '--population-integration', 'analytic_single_phase',
            '--population-size', '16']
    for key, value in values.items():
        argv += ['--' + key.replace('_', '-'), str(value)]
    main(argv)
    manifest = json.loads((out / 'manifest.json').read_text())
    assert {k: manifest['provenance']['config'][k] for k in values} == values
    assert not json.loads((out / 'preflight.json').read_text())['sampling_performed']
    capsys.readouterr()


@pytest.mark.parametrize('field', SENSITIVITY_FIELDS)
def test_no_prior_or_reporting_override_during_saved_draw_diagnostics(tmp_path, field):
    with pytest.raises(SystemExit):
        main(['--diagnose-run', str(tmp_path / 'not_opened'), '--out', str(tmp_path / 'out'),
              '--' + field.replace('_', '-'), str(getattr(Config(), field))])


def test_omitted_assumptions_retain_historical_config_defaults(tmp_path, capsys):
    path = tmp_path / 'data.json'
    path.write_text(json.dumps(phase_data()))
    out = tmp_path / 'preflight'
    main(['--data', str(path), '--out', str(out), '--preflight', '--population-size', '16'])
    cfg = json.loads((out / 'manifest.json').read_text())['provenance']['config']
    for field in SENSITIVITY_FIELDS:
        assert cfg[field] == getattr(Config(), field)
    capsys.readouterr()
