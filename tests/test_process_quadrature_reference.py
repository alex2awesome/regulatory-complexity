import numpy as np
import pytest

from pipeline.procbench.bayes_preparation_measurement import Config, PreparationMeasurementModel
from pipeline.procbench.check_process_quadrature import case_integral
from test_preparation_measurement import inputs


@pytest.mark.parametrize('known_outcome', ['approved', 'denied', 'unknown'])
def test_adaptive_case_integral_matches_joint_model_including_outcome_and_selection(known_outcome):
    e, a, o, prep = inputs()
    o['cases'][0]['outcome'] = known_outcome
    o['cases'][0]['initial_decision_status'] = 'completed'
    cfg = Config(quadrature=2048, selection_sd=1.5)
    model = PreparationMeasurementModel([e], [a], [o], [prep], cfg)
    p = model.programs[0]
    z = np.full(model.layout.size, .3)
    par = model.parameters(p, z)
    value, _ = case_integral(model, p, 'c1', par)
    reference, error = case_integral(model, p, 'c1', par, adaptive=True)
    assert value == pytest.approx(model.log_likelihood(z), abs=1e-9)
    assert reference == pytest.approx(value, abs=1e-6)
    assert error < 1e-6
