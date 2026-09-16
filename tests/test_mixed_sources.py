import math

import numpy as np
import pytest
from scipy.stats import norm

from pipeline.procbench.validate_mixed_sources import ExactSourceModel
from pipeline.procbench.bayes_process_measurement import log_selection_weight


def test_learning_variability_includes_the_gaussian_scale_normalizer():
    model=ExactSourceModel(np.log([20.,30.,70.]),np.log([25.,35.]))
    rng=np.random.default_rng(458)
    for z in rng.normal(size=(20,3)):
        mu,sigma,kappa=model.parameters(z)
        reference=norm.logpdf(model.selected,mu,sigma).sum()+norm.logpdf(model.administrative,mu,sigma).sum()
        reference+=log_selection_weight((model.selected-mu)/sigma,kappa).sum()
        reference+=5*.5*math.log(2*math.pi)  # only this parameter-independent constant is omitted
        assert model.log_likelihood(z)==pytest.approx(reference,abs=1e-10)


def test_administrative_cases_do_not_receive_forum_ascertainment_weights():
    data=np.log([25.,40.,90.])
    admin=ExactSourceModel([],data)
    selected=ExactSourceModel(data,[])
    z=np.zeros(3)
    assert admin.log_likelihood(z)==pytest.approx(selected.log_likelihood(z))
    before=admin.log_likelihood(z)
    z[2]=2.
    assert admin.log_likelihood(z)==before
    assert selected.log_likelihood(z)!=pytest.approx(before)
