"""Refresh end-to-end metrics in the historical synthetic dashboard.

Uses a saved baseline_rescoring.json; never modifies original benchmark runs.
Structural metrics/alignments remain historical, explicitly labeled as such.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import re
import statistics


def refresh_results(results, predictions, rescoring):
    results, predictions = copy.deepcopy(results), copy.deepcopy(predictions)
    lookup = {(r["condition"], r["task"]): r["end_to_end"] for r in rescoring["rows"]}
    touched = set()
    for collection, condition, aggregate in (("runs", "oracle_docs", "oracle"),
                                              ("search_runs", "search", "search")):
        errors = []
        for row in results[collection]:
            key = (condition, row["task_id"])
            timing = lookup[key]
            touched.add(key)
            row["e2e_pred"] = timing["pred_median_days"]
            row["e2e_gold"] = timing["gold_median_days"]
            row["e2e_abs_log"] = timing["abs_log_ratio"]
            predictions[row["model_id"]][condition]["metrics"]["e2e"] = timing
            if row["e2e_pred"] and row["e2e_gold"]:
                errors.append(abs(math.log(row["e2e_pred"] / row["e2e_gold"])))
        results["medians"][aggregate]["e2e_abs_log"] = statistics.median(errors) if errors else None
    if touched != set(lookup):
        raise ValueError("Dashboard and rescored task sets differ")
    results["timing_scorer_version"] = rescoring["scorer_version"]
    results["timing_correction"] = (
        "2026-09-16: explicit process_timing.median_days, never a sum of step medians. "
        "Only end-to-end metrics refreshed; structural metrics/alignments remain historical. "
        "Oracle and search have different task sets, not a paired retrieval-effect estimate."
    )
    return results, predictions


def embed(html, script_id, data):
    pattern = re.compile(r'(<script id="' + re.escape(script_id) + r'" type="application/json">).*?(</script>)', re.S)
    payload = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    result, count = pattern.subn(lambda m: m[1] + payload + m[2], html)
    if count != 1:
        raise ValueError(f"Expected one {script_id} block, found {count}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rescoring", default="runs/bayes_v3_final/baseline_rescoring.json")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    data = root / "dashboard/data"
    results, predictions = refresh_results(
        json.loads((data / "synth_results.json").read_text()),
        json.loads((data / "synth_pred.json").read_text()),
        json.loads((root / args.rescoring).read_text()))
    outputs = []
    for filename in ("synthetic_processes.html", "synthetic_processes.standalone.html"):
        path = root / "dashboard/out" / filename
        html = embed(path.read_text(), "synth-results", results)
        outputs.append((path, embed(html, "synth-pred", predictions)))
    # Validate all inputs before rebuilding any generated artifacts.
    (data / "synth_results.json").write_text(json.dumps(results, indent=1) + "\n")
    (data / "synth_pred.json").write_text(json.dumps(predictions) + "\n")
    for path, html in outputs:
        path.write_text(html)
    print(f"Refreshed {len(results['runs'])} oracle and {len(results['search_runs'])} search timelines in both dashboards.")


if __name__ == "__main__":
    main()
