import math

import pytest

from pipeline.priors import compare_models as comparison


def test_global_baseline_excludes_held_out_key(monkeypatch):
    groups = {("a", "task"): [(0., "s")], ("b", "task"): [(10., "s")]}

    def fake_gibbs(rest, families, **kwargs):
        assert len(rest) == 1
        return {}, {"m": {"family": [1., 1.]}, "tau2": [1., 1.]}, {}, {}

    monkeypatch.setattr(comparison.H, "gibbs", fake_gibbs)
    rows = comparison.loo(groups, lambda key: "family", draws=2, burn=0, min_anchors=1)
    # Leaking both keys into the global median would give error 5 rather than 10.
    assert [r["global"] for r in rows] == pytest.approx([10., 10.])


def test_no_training_keys_is_not_a_cross_validation_result():
    assert comparison.loo({("a", "task"): [(math.log(5), "s")]},
                          lambda key: "family", draws=2, burn=0, min_anchors=1) == []
