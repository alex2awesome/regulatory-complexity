import math
from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from pipeline.procbench.bayes_preparation_measurement import Config,PreparationMeasurementModel
from pipeline.procbench.diagnose_process_reports import broad_probability,conditional_attributions
from test_preparation_measurement import inputs


def test_responsibilities_are_joint_conditional_probabilities_not_independent_case_weights():
    e,a,o,prep=inputs()
    cfg=Config(quadrature=1024,outcome_contrast_sd=0,source_sd=0)
    model=PreparationMeasurementModel([e],[a],[o],[prep],cfg)
    core=PreparationMeasurementModel([e],[a],[o],[prep],replace(cfg,contamination=0))
    z=np.zeros(model.layout.size)
    p=model.programs[0]
    z[p['clock'][0]]=2.
    par=model.parameters(p,z)
    rows=p['cases']['c1']
    def likelihood(node,replace_row=False):
        base=par['mu']+par['sigma']*node
        values=[(core if replace_row and i==0 else model).observation_probability(m,base,par) for i,m in enumerate(rows)]
        return norm.pdf(node)*np.exp(sum(values))
    normalizer=quad(likelihood,-12,12,epsabs=1e-15)[0]
    core_first=quad(lambda node:likelihood(node,True),-12,12,epsabs=1e-15)[0]
    expected=1-(1-cfg.contamination)*core_first/normalizer
    result=conditional_attributions(model,core,z)
    assert result[(e['program_id'],'m1')]==pytest.approx(expected,abs=1e-7)
    assert all(0<=value<=1 for value in result.values())


def test_zero_contamination_cannot_assign_a_report_to_a_nonexistent_component():
    assert broad_probability(np.array([-5.,-2]),np.array([-5.,-2]),0).tolist()==[0.,0.]
    assert broad_probability(math.log(.2),math.log(.1),.1)==pytest.approx(.55)
