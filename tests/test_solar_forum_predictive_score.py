import numpy as np
import pytest

from pipeline.procbench.solar_panel.evaluate_forum_predictions import GRID, event_probability, valid_cdf


def test_common_cdf_interpolation_scores_mass_not_midpoint():
    cdf=(np.log1p(GRID)/np.log1p(GRID[-1])).tolist()
    assert valid_cdf(cdf)
    expected=(np.log1p(3)-np.log1p(1))/np.log1p(GRID[-1])
    assert event_probability(cdf,1,3)==pytest.approx(expected)
    assert event_probability(cdf,147,None)==pytest.approx(1-np.log1p(147)/np.log1p(GRID[-1]))
    assert event_probability(cdf,0,None)==1


def test_nonmonotone_cdf_and_unfrozen_tail_are_not_silently_repaired():
    cdf=(np.log1p(GRID)/np.log1p(GRID[-1])).tolist()
    invalid=cdf.copy(); invalid[5]=0
    assert not valid_cdf(invalid)
    with pytest.raises(ValueError,match='frozen grid'):
        event_probability(cdf,0,GRID[-1]+1)
