import json
import math

import pytest

from pipeline.procbench.refresh_synth_scores import embed, refresh_results


def test_timing_refresh_preserves_historical_structure_and_is_idempotent():
    results = {"runs": [{"task_id": "W__J__S", "model_id": "J__S", "precision": .75}],
               "search_runs": [], "medians": {"oracle": {"precision": .75}, "search": {}}}
    predictions = {"J__S": {"oracle_docs": {"metrics": {"precision": .75}}}}
    rescoring = {"scorer_version": "procbench-score/2", "rows": [
        {"condition": "oracle_docs", "task": "W__J__S", "end_to_end": {
            "pred_median_days": 10, "gold_median_days": 20, "abs_log_ratio": .6931}}]}
    updated, preds = refresh_results(results, predictions, rescoring)
    assert updated["runs"][0]["precision"] == .75
    assert updated["runs"][0]["e2e_pred"] == 10
    assert updated["medians"]["oracle"]["e2e_abs_log"] == pytest.approx(math.log(2))
    assert "e2e_pred" not in results["runs"][0]
    assert preds["J__S"]["oracle_docs"]["metrics"]["precision"] == .75
    assert refresh_results(updated, preds, rescoring) == (updated, preds)


def test_json_embedding_preserves_document_and_escapes_script_closures():
    html = 'before<script id="synth-results" type="application/json">{}</script>after'
    value = {"quote": "</script><script>untrusted</script>"}
    result = embed(html, "synth-results", value)
    assert result.count("</script>") == 1
    assert json.loads(result.split(">", 1)[1].split("</script>", 1)[0]) == value
    assert result.startswith("before") and result.endswith("after")
    with pytest.raises(ValueError, match="Expected one"):
        embed(html, "absent", {})
