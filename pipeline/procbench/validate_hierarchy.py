"""Independent generated-data checks, not the synthetic benchmark's hidden truth.

Exercises up/down agency propagation and source/total likelihoods with known
parameters. Kept separate from benchmark fitting and model selection.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import pathlib
import time

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .evidence_contract import VERSION
from .latent_gaussian import summary
from .run_hierarchical import write


def generated_evidence(seed=17, n_cases=10, with_totals=True):
    rng = np.random.default_rng(seed)
    ref = {"doc_id": "generated", "quote": "independent generated-data validation"}
    actors = [{"id": aid, "name": aid, "role": "agency", "aliases": [], "evidence": [ref]}
              for aid in ("slower_agency", "faster_agency")]
    # Multiple distinct observed tasks per agency are essential: many reports
    # about ONE task cannot identify an agency effect separately from that task.
    specs = [("slow_observed1", "slower_agency", "technical_review", "review", 25.),
             ("slow_observed2", "slower_agency", "technical_review", "review", 23.),
             ("slow_observed3", "slower_agency", "technical_review", "review", 24.),
             ("slow_held_out", "slower_agency", "technical_review", "review", 22.),
             ("fast_observed1", "faster_agency", "technical_review", "review", 2.),
             ("fast_observed2", "faster_agency", "technical_review", "review", 2.2),
             ("fast_observed3", "faster_agency", "technical_review", "review", 2.8),
             ("fast_held_out", "faster_agency", "technical_review", "review", 2.5),
             ("decide", "faster_agency", "decision", "decision", 1.)]
    activities = [{"id": aid, "name": aid, "actor_id": actor, "task_type": task,
                   "stage": stage, "scope": "core", "condition": None, "existence": "explicit",
                   "evidence": [ref], "notes": ""} for aid, actor, task, stage, _ in specs]
    relations = [{"source": specs[i][0], "target": specs[i + 1][0], "kind": "precedes",
                  "support": "explicit", "condition": None, "evidence": [ref]} for i in range(len(specs) - 1)]
    evidence = {"schema_version": VERSION, "program_id": "validation__generated", "actors": actors,
                "activities": activities, "relations": relations, "measurements": [], "ambiguities": [], "excluded": []}
    for case in range(n_cases):
        values = rng.lognormal(np.log([s[-1] for s in specs]), .3)
        for i in (*[i for i, s in enumerate(specs) if 'held_out' not in s[0]], -1):
            if i == -1 and not with_totals:
                continue
            value = values.sum() if i == -1 else values[i]
            # Independent reporting noise, with an explicit shared case identity.
            reported = value * np.exp(.15 * rng.standard_t(4))
            evidence['measurements'].append({"id": f"c{case}:m{i}", "metric": "elapsed",
                "scope": "process" if i == -1 else "step", "activity_ids": [] if i == -1 else [specs[i][0]],
                "start": "preparation_start" if i == -1 else "activity_start", "end": "decision" if i == -1 else "activity_end",
                "statistic": "individual", "value": float(reported), "lower": None, "upper": None,
                "unit": "calendar_days", "qualitative": False, "n": None, "case_id": f"case{case}",
                "cohort": None, "source_family": f"independent_source{case}", "doc_id": "generated",
                "quote": ref['quote'], "interpretation": "known simulated observation, not benchmark truth"})
    return evidence, {s[0]: s[-1] for s in specs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--warmup', type=int, default=500)
    ap.add_argument('--draws', type=int, default=500)
    ap.add_argument('--chains', type=int, default=4)
    ap.add_argument('--cases', type=int, default=10)
    ap.add_argument('--no-hierarchy', action='store_true')
    ap.add_argument('--no-totals', action='store_true')
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if (out / 'report.json').exists():
        raise ValueError('Use a fresh output directory')
    evidence, truth = generated_evidence(n_cases=args.cases, with_totals=not args.no_totals)
    cfg = Config(warmup=args.warmup, draws=args.draws, chains=args.chains, thin=1, max_unseen=0,
                 unseen_mean=0, population_size=64, report_sd=.15, source_bias_sd=.05,
                 use_hierarchy=not args.no_hierarchy)
    model = HierarchicalModel([evidence], cfg)
    started = time.monotonic()
    z, s, ll, calls = model.sample(lambda d: print(json.dumps(d), flush=True))
    report = model.report(z, s, ll)
    acts = report['programs'][evidence['program_id']]['model']['activities']
    comparison = {a['id']: {'true_median': truth[a['id']], 'estimated_median': a['timing']['median_days'],
                          'ci90': a['timing']['median_ci90'], 'held_out': 'held_out' in a['id']}
                  for a in acts}
    write(out / 'report.json', report)
    write(out / 'comparison.json', {'steps': comparison, 'config': asdict(cfg),
                                   'seconds': time.monotonic() - started,
                                   'caveat': 'parameter recovery check, not a coverage study or benchmark result'})
    np.savez_compressed(out / 'draws.npz', z=z, structure=s, log_likelihood=ll)
    print(json.dumps(comparison, indent=2), flush=True)


if __name__ == '__main__':
    main()
