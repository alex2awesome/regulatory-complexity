"""An exposed sensitivity constant must not change defaults or cohort semantics."""
from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from test_analytic_phase import phase_data, config
from test_cohort_quantiles import model_data as finite_cohort_data
from test_typical_range_reports import range_data


@pytest.mark.parametrize('floor',[0.,.25,.5,.75,1.])
def test_unknown_n_floor_is_used_by_both_targets_and_diagnostics(floor):
    model=VisitHierarchy(phase_data(),config(unknown_n_report_sd_floor=floor))
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==model.log_likelihood_reference(z,[0])
    report=model.source_support_report()
    assert report['unknown_n_report_sd_floor']==floor
    assert report['source_families']['source']['report_log_scales']==[max(.25,floor)]


def test_default_is_identical_and_narrower_assumption_changes_target():
    default=VisitHierarchy(phase_data(),config())
    explicit=VisitHierarchy(phase_data(),config(unknown_n_report_sd_floor=.5))
    narrower=VisitHierarchy(phase_data(),config(unknown_n_report_sd_floor=.25))
    z=np.zeros(default.layout.size)
    assert default.log_likelihood(z,[0])==explicit.log_likelihood(z,[0])
    assert narrower.log_likelihood(z,[0])>default.log_likelihood(z,[0])


def test_exact_histogram_does_not_use_report_floor():
    model=VisitHierarchy(phase_data(histogram=True),config())
    other=VisitHierarchy(phase_data(histogram=True),replace(model.cfg,unknown_n_report_sd_floor=3.))
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==other.log_likelihood(z,[0])


@pytest.mark.parametrize('make_data',[finite_cohort_data,range_data])
def test_known_n_and_subjective_range_contracts_do_not_use_unknown_n_floor(make_data):
    data=make_data()
    model=VisitHierarchy(data,Config(population_size=16))
    other=VisitHierarchy(data,replace(model.cfg,unknown_n_report_sd_floor=3.))
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==other.log_likelihood(z,[0])


@pytest.mark.parametrize('floor',[-1.,float('inf'),float('nan')])
def test_invalid_floor_rejected(floor):
    with pytest.raises(ValueError,match='Invalid hierarchy scales'):
        Config(unknown_n_report_sd_floor=floor)
